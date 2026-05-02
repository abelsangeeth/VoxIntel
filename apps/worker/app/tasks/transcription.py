"""
Phase 1 — Transcription task.

Runs Faster-Whisper ASR on a diarized segment and writes Utterance rows.
"""

import asyncio
import uuid

import structlog
from celery import shared_task

from app.core.config import settings

logger = structlog.get_logger(__name__)


@shared_task(
    name="transcription.run_segment",
    bind=True,
    max_retries=3,
    default_retry_delay=20,
    acks_late=True,
)
def transcribe_segment(
    self,
    conversation_id: str,
    speaker_label: str,
    audio_path: str,
    start: float,
    end: float,
    sequence_number: int,
) -> dict:
    """
    Transcribe a single diarized segment using Faster-Whisper.

    Args:
        conversation_id:  UUID string of the parent Conversation.
        speaker_label:    e.g. "SPEAKER_00"
        audio_path:       Path to the full audio file.
        start / end:      Timestamps in seconds.
        sequence_number:  Ordering index within the conversation.
    """
    log = logger.bind(conversation_id=conversation_id, speaker=speaker_label)
    log.info("transcription.start", start=start, end=end)

    try:
        text, confidence, language = _transcribe(audio_path, start, end)
        asyncio.run(
            _persist_utterance(
                conversation_id,
                speaker_label,
                sequence_number,
                start,
                end,
                text,
                confidence,
                language,
            )
        )
        log.info("transcription.complete", chars=len(text))
        return {
            "conversation_id": conversation_id,
            "sequence_number": sequence_number,
            "text": text,
        }
    except Exception as exc:
        log.error("transcription.failed", error=str(exc))
        raise self.retry(exc=exc)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _transcribe(audio_path: str, start: float, end: float) -> tuple[str, float, str]:
    """Return (text, confidence, language) for the segment."""
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5, clip_timestamps=f"{start},{end}")
        text = " ".join(seg.text.strip() for seg in segments)
        avg_confidence = sum(
            seg.avg_logprob for seg in list(model.transcribe(audio_path)[0])
        ) / max(1, len(list(model.transcribe(audio_path)[0])))
        return text, float(avg_confidence), info.language
    except ImportError:
        return f"[stub transcript {start:.1f}–{end:.1f}s]", 0.9, "en"


async def _persist_utterance(
    conversation_id: str,
    speaker_label: str,
    sequence_number: int,
    start: float,
    end: float,
    text: str,
    confidence: float,
    language: str,
) -> None:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    # app/db is mounted from apps/api/app/db via docker-compose volume
    from app.db.models import Speaker, Utterance  # type: ignore[import]

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as session:
        result = await session.execute(
            select(Speaker).where(
                Speaker.conversation_id == uuid.UUID(conversation_id),
                Speaker.label == speaker_label,
            )
        )
        speaker = result.scalar_one_or_none()

        utterance = Utterance(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            speaker_id=speaker.id if speaker else None,
            sequence_number=sequence_number,
            start_time=start,
            end_time=end,
            text=text,
            confidence=confidence,
            language=language,
        )
        session.add(utterance)
        await session.commit()
    await engine.dispose()
