"""Thin proxy so the API can enqueue Celery tasks without importing the worker app directly.

The _celery instance is shared across all proxy calls so the result backend
is correctly configured for .get() calls on synchronous task results.
"""

import os

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _make_celery():
    from celery import Celery

    app = Celery(
        broker=_REDIS_URL,
        backend=_REDIS_URL,  # must match worker so .get() can retrieve results
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        broker_connection_retry_on_startup=True,
    )
    return app


# Singleton — reuse across requests
_celery = _make_celery()

# Named task signatures for enqueue-and-forget calls
summarize_session_task = _celery.signature("analytics.summarize_session")
ingest_document_task = _celery.signature("rag.ingest_document")
run_diarization_task = _celery.signature("diarization.run")
analyze_utterance_task = _celery.signature("analytics.analyze_utterance")
