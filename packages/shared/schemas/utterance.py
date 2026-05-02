"""Utterance Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UtteranceCreate(BaseModel):
    conversation_id: uuid.UUID
    speaker_id: Optional[uuid.UUID] = None
    sequence_number: int
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None


class UtteranceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    speaker_id: Optional[uuid.UUID]
    sequence_number: int
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float]
    language: Optional[str]
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    intent: Optional[str]
    created_at: datetime
