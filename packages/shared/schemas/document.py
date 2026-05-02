"""Document Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    status: str
    tags: Dict[str, Any] = {}
    chunk_count: Optional[int]
    token_count: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
