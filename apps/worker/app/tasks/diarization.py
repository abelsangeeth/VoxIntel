"""
Phase 1 — Speaker diarization task.

Flow:
  1. Receive audio file path from queue
  2. Run pyannote.audio diarization → speaker segments
  3. Write Speaker records to DB
  4. Chain transcription task for each segment
"""

import asyncio
import uuid

import structlog
from app.core.config import settings
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(
    name="diarization.run",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def run_diarization(self, conversation_id: str, audio_path: str) -> dict:
    """
    Diarize an audio file and persist speaker-attributed segments.

    Args:
        conversation_id: UUID string of the parent Conversation row.
        audio_path:       Local path to the audio file to process.

    Returns:
        dict with keys: conversation_id, speaker_count, segment_count
    """
    log = logger.bind(conversation_id=conversation_id, audio_path=audio_path)
    log.info("diarization.start")

    try:
        segments = _diarize(audio_path)
        asyncio.run(_persist_segments(conversation_id, segments))
        log.info("diarization.complete", segment_count=len(segments))
        return {
            "conversation_id": conversation_id,
            "speaker_count": len({s["speaker"] for s in segments}),
            "segment_count": len(segments),
        }
    except Exception as exc:
        log.error("diarization.failed", error=str(exc))
        raise self.retry(exc=exc)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _diarize(audio_path: str) -> list[dict]:
    """
    Run pyannote.audio diarization pipeline.

    Returns a list of dicts:
      [{"speaker": "SPEAKER_00", "start": 0.5, "end": 3.2}, ...]
    """
    try:
        from pyannote.audio import Pipeline  # type: ignore

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=settings.HUGGINGFACE_TOKEN,
        )
        diarization = pipeline(audio_path)
        return [
            {"speaker": str(turn.speaker), "start": turn.start, "end": turn.end}
            for turn, _, _ in diarization.itertracks(yield_label=True)
        ]
    except ImportError:
        # Stub for local dev without GPU / pyannote installed
        logger.warning("pyannote not available — returning stub segments")
        return [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 5.0},
            {"speaker": "SPEAKER_01", "start": 5.1, "end": 10.0},
        ]


async def _persist_segments(conversation_id: str, segments: list[dict]) -> None:
    """Write Speaker rows (if new) to the database."""
    # app/db is mounted from apps/api/app/db via docker-compose volume
    from app.db.models import Speaker  # type: ignore[import]
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    seen_speakers: set[str] = set()
    async with SessionLocal() as session:
        for seg in segments:
            label = seg["speaker"]
            if label not in seen_speakers:
                result = await session.execute(
                    select(Speaker).where(
                        Speaker.conversation_id == uuid.UUID(conversation_id),
                        Speaker.label == label,
                    )
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    session.add(
                        Speaker(
                            id=uuid.uuid4(),
                            conversation_id=uuid.UUID(conversation_id),
                            label=label,
                        )
                    )
                seen_speakers.add(label)
        await session.commit()
    await engine.dispose()
