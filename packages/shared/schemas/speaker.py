"""Speaker Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class SpeakerCreate(BaseModel):
    conversation_id: uuid.UUID
    label: str
    display_name: Optional[str] = None


class SpeakerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    label: str
    display_name: Optional[str]
    created_at: datetime
