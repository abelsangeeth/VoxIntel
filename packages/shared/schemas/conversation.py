"""Conversation Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str
    source: str = "upload"
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str
    external_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime]
