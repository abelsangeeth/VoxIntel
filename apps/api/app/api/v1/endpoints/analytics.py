"""Analytics endpoints — Phase 3.

Endpoints:
  POST /sessions/{session_id}/end         → mark session done, trigger summary job
  GET  /sessions/{session_id}/summary     → fetch generated summary
  GET  /sessions/{session_id}/utterances  → paginated utterance list with analytics
"""

import uuid

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models import Conversation, SessionSummary, Utterance
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.schemas.utterance import UtteranceRead

router = APIRouter()


# ── Pydantic response models ──────────────────────────────────────────────────

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict


class SummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    summary_text: str
    action_items: list
    top_intents: list
    sentiment_arc: list
    webhook_sent: bool
    created_at: datetime


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/{session_id}/end",
    status_code=status.HTTP_202_ACCEPTED,
    summary="End a session and trigger analytics",
)
async def end_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> dict:
    """
    Mark a conversation as ended and enqueue the summarisation + analytics job.
    The response returns immediately; the summary is generated asynchronously.
    """
    conv = await db.get(Conversation, session_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if conv.status == "ended":
        raise HTTPException(status_code=409, detail="Session already ended")

    from datetime import datetime

    conv.status = "ended"
    conv.ended_at = datetime.now(UTC)
    await db.flush()

    # Enqueue async summarisation via Celery
    try:
        from app.tasks_proxy import summarize_session_task

        summarize_session_task.delay(str(session_id))
    except Exception:
        pass  # Worker may not be running in dev; summary queued best-effort

    return {"session_id": str(session_id), "status": "ended", "summary": "queued"}


@router.get(
    "/{session_id}/summary",
    response_model=SummaryRead,
    summary="Get the generated session summary",
)
async def get_summary(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> SummaryRead:
    """Retrieve the auto-generated meeting minutes and action items."""
    result = await db.execute(
        select(SessionSummary).where(SessionSummary.conversation_id == session_id)
    )
    summary = result.scalar_one_or_none()
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="Summary not yet available. Trigger /end first and wait for processing.",
        )
    return SummaryRead.model_validate(summary)


@router.get(
    "/{session_id}/utterances",
    response_model=list[UtteranceRead],
    summary="List utterances with sentiment and intent",
)
async def list_utterances(
    session_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
) -> list[UtteranceRead]:
    """Return paginated utterances for a session, including analytics fields."""
    conv = await db.get(Conversation, session_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Utterance)
        .where(Utterance.conversation_id == session_id)
        .order_by(Utterance.sequence_number)
        .offset(offset)
        .limit(limit)
    )
    utterances = result.scalars().all()
    return [UtteranceRead.model_validate(u) for u in utterances]
