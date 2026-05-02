"""Celery application — entry point for the async worker."""

from celery import Celery
from app.core.config import settings

app = Celery(
    "voxintel_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.diarization",
        "app.tasks.transcription",
        "app.tasks.rag",
        "app.tasks.analytics",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_connection_retry_on_startup=True,  # suppress Celery 6.x deprecation warning
)
