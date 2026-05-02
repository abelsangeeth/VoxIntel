"""Utterance Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UtteranceCreate(BaseModel):
    conversation_id: uuid.UUID
    speaker_id: uuid.UUID | None = None
    sequence_number: int
    start_time: float
    end_time: float
    text: str
    confidence: float | None = None
    language: str | None = None


class UtteranceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    speaker_id: uuid.UUID | None
    sequence_number: int
    start_time: float
    end_time: float
    text: str
    confidence: float | None
    language: str | None
    sentiment_label: str | None
    sentiment_score: float | None
    intent: str | None
    created_at: datetime
