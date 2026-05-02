"""Worker settings — mirrors the API config for DB/Redis access."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://voxintel:voxintel@localhost:5432/voxintel"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "voxintel_docs"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    HUGGINGFACE_TOKEN: str = ""
    ASSEMBLY_AI_API_KEY: str = ""

    SLACK_BOT_TOKEN: str = ""
    SLACK_SUMMARY_CHANNEL: str = "#voxintel-summaries"

    WEBHOOK_URL: str = ""

    AUDIO_UPLOAD_DIR: str = "/tmp/audio"

    LOG_LEVEL: str = "INFO"


settings = WorkerSettings()
