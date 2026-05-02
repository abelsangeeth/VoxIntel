"""Speaker Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SpeakerCreate(BaseModel):
    conversation_id: uuid.UUID
    label: str
    display_name: str | None = None


class SpeakerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    label: str
    display_name: str | None
    created_at: datetime
