"""Health-check endpoint."""

import time

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    version: str


@router.get("", response_model=HealthResponse, summary="Service health check")
async def health_check() -> HealthResponse:
    """Returns 200 when the API is reachable and ready to serve traffic."""
    return HealthResponse(
        status="ok",
        uptime_seconds=round(time.time() - _START_TIME, 2),
        version="0.1.0",
    )
