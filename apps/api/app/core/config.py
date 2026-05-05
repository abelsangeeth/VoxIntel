"""Application settings — loaded from environment variables / .env file."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_BASE_URL: str = "https://voxintel-production.up.railway.app"
    # Comma-separated origins — override via CORS_ORIGINS env var in Railway/Vercel.
    # e.g. CORS_ORIGINS="https://my-app.vercel.app,https://custom.domain.com"
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8000",
        "https://voxintel-production.up.railway.app",
        # Vercel production + all preview deployments
        "https://vox-intel.vercel.app",
        "https://vox-intel-git-main-abelsangeeth.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Allow CORS_ORIGINS to be set as a comma-separated string in env."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://voxintel:voxintel@localhost:5432/voxintel"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_asyncpg_driver(cls, v: str) -> str:
        """Convert postgres:// or postgresql:// → postgresql+asyncpg:// for async SQLAlchemy."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "insecure-dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── LLM ───────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ── Vector store ──────────────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "voxintel_docs"

    # ── ASR / Diarization ─────────────────────────────────────────────────
    HUGGINGFACE_TOKEN: str = ""
    ASSEMBLY_AI_API_KEY: str = ""

    # ── Audio storage ─────────────────────────────────────────────────────
    AUDIO_UPLOAD_DIR: str = "/tmp/audio"

    # ── Integrations ──────────────────────────────────────────────────────
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    ZOOM_WEBHOOK_SECRET_TOKEN: str = ""
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_SUMMARY_CHANNEL: str = "#voxintel-summaries"

    # ── Webhooks ──────────────────────────────────────────────────────────
    WEBHOOK_URL: str = ""  # Generic webhook fired after session summarization

    # ── Observability ─────────────────────────────────────────────────────
    SENTRY_DSN: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
