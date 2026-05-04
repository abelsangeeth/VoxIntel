"""VoxIntel API — application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.database import engine
from app.db.models import Base

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", env=settings.ENV)
    # Create tables if they don't exist (migrations handle prod)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database connected")
    except Exception as exc:  # noqa: BLE001
        logger.warning("database unavailable at startup", error=str(exc))
    yield
    logger.info("shutdown")
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title="VoxIntel API",
        description="Real-time conversational intelligence — RAG-powered meeting analytics.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────
    application.include_router(v1_router, prefix="/v1")

    # ── Prometheus metrics ────────────────────────────────────────────────
    Instrumentator().instrument(application).expose(application, endpoint="/metrics")

    return application


app = create_app()
