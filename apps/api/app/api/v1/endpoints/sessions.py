"""Session endpoints — Phase 1.

Improvements over stub:
  - POST /sessions/{id}/audio   → saves file locally + enqueues diarization
  - GET  /sessions/{id}/transcript/stream → real SSE from DB polling
  - GET  /sessions/{id}/rag     → answer a question via RAG
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models import Conversation, Utterance, Speaker
from packages.shared.schemas.conversation import ConversationCreate, ConversationRead

logger = structlog.get_logger(__name__)
router = APIRouter()

AUDIO_UPLOAD_DIR = Path(os.getenv("AUDIO_UPLOAD_DIR", "/tmp/audio"))
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/ogg", "audio/webm", "audio/mp4", "audio/flac",
    "audio/aac", "audio/m4a", "application/octet-stream",
}


# ── Create session ─────────────────────────────────────────────────────────────

@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> ConversationRead:
    """Create a new conversation session."""
    conversation = Conversation(
        id=uuid.uuid4(),
        title=payload.title,
        external_id=payload.external_id,
        source=payload.source,
        metadata_=payload.metadata or {},
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return ConversationRead.model_validate(conversation)


# ── Get session ────────────────────────────────────────────────────────────────

@router.get("/{session_id}", response_model=ConversationRead)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> ConversationRead:
    """Retrieve a session by ID."""
    result = await db.get(Conversation, session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return ConversationRead.model_validate(result)


# ── Upload audio ───────────────────────────────────────────────────────────────

@router.post("/{session_id}/audio", status_code=status.HTTP_202_ACCEPTED)
async def upload_audio(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    context_doc: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """
    Upload an audio file for async diarization + transcription.

    Optionally include a context_doc (.txt / .pdf) to inject as RAG context.
    Returns 202 immediately; processing happens in the worker.
    """
    conv = await db.get(Conversation, session_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate content type (accept octet-stream for curl uploads without explicit type)
    ct = file.content_type or "application/octet-stream"
    if not (ct.startswith("audio/") or ct == "application/octet-stream"):
        raise HTTPException(
            status_code=422,
            detail=f"Expected audio file, got: {ct}",
        )

    # Persist audio bytes
    session_dir = AUDIO_UPLOAD_DIR / str(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    audio_path = session_dir / (file.filename or f"{uuid.uuid4()}.audio")
    contents = await file.read()
    audio_path.write_bytes(contents)

    # Optionally persist context document
    context_path: Path | None = None
    if context_doc and context_doc.filename:
        context_path = session_dir / context_doc.filename
        context_path.write_bytes(await context_doc.read())

    # Mark session as processing
    conv.status = "processing"
    await db.flush()

    # Enqueue diarization job
    try:
        from app.tasks_proxy import run_diarization_task

        run_diarization_task.delay(str(session_id), str(audio_path))
        logger.info("audio.queued", session_id=str(session_id), path=str(audio_path))
    except Exception as exc:
        logger.error("audio.queue_failed", error=str(exc))

    return {
        "session_id": str(session_id),
        "audio_filename": file.filename,
        "context_doc": context_doc.filename if context_doc else None,
        "audio_path": str(audio_path),
        "status": "queued",
    }


# ── SSE transcript stream ──────────────────────────────────────────────────────

@router.get("/{session_id}/transcript/stream")
async def stream_transcript(
    session_id: uuid.UUID,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Server-Sent Events stream — delivers new utterances as they are written to the DB.
    Polls every 2 seconds; sends a keep-alive ping every 10 s when idle.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        last_seq = -1
        idle_ticks = 0
        while True:
            result = await db.execute(
                select(Utterance, Speaker)
                .outerjoin(Speaker, Utterance.speaker_id == Speaker.id)
                .where(
                    Utterance.conversation_id == session_id,
                    Utterance.sequence_number > last_seq,
                )
                .order_by(Utterance.sequence_number)
                .limit(20)
            )
            rows = result.all()
            if rows:
                idle_ticks = 0
                for utt, spk in rows:
                    last_seq = utt.sequence_number
                    speaker_label = (
                        spk.display_name or spk.label if spk else "Unknown"
                    )
                    event_data = json.dumps(
                        {
                            "type": "utterance",
                            "seq": utt.sequence_number,
                            "speaker": speaker_label,
                            "start": utt.start_time,
                            "end": utt.end_time,
                            "text": utt.text,
                            "sentiment": utt.sentiment_label,
                            "intent": utt.intent,
                        }
                    )
                    yield f"data: {event_data}\n\n"
            else:
                idle_ticks += 1
                if idle_ticks % 5 == 0:  # every ~10 s
                    yield f"data: {json.dumps({'type': 'ping', 'session_id': str(session_id)})}\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── RAG query ──────────────────────────────────────────────────────────────────

@router.post("/{session_id}/rag")
async def rag_query(
    session_id: uuid.UUID,
    question: str = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """
    Ask a question grounded in the knowledge-base documents.
    Dispatches to the worker's rag.query Celery task and waits up to 30s.
    """
    conv = await db.get(Conversation, session_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        from app.tasks_proxy import _celery

        result = _celery.send_task(
            "rag.query",
            args=[str(session_id), question],
        ).get(timeout=30)
        return result
    except Exception as exc:
        logger.warning("rag.query_fallback", error=str(exc))
        return {
            "conversation_id": str(session_id),
            "answer": "RAG worker not reachable in this environment.",
            "sources": [],
        }
