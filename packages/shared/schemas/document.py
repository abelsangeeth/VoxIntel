"""Document Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    status: str
    tags: dict[str, Any] = {}
    chunk_count: int | None
    token_count: int | None
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None
