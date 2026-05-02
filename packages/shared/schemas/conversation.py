"""Conversation Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str
    source: str = "upload"
    external_id: str | None = None
    metadata: dict[str, Any] | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str
    external_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    ended_at: datetime | None
