"""Auth endpoints — token issuance (Phase 4)."""

from datetime import timedelta

from app.core.security import create_access_token, hash_password, verify_password
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# In production this would be a DB lookup.  For the developer sandbox we
# accept a single hard-coded service account so the API can be tested
# without standing up a full user management system.
# Passwords are hashed at module load time (avoids storing pre-computed hashes).
# ---------------------------------------------------------------------------
_DEMO_USERS: dict[str, str] = {
    "demo": hash_password("voxintel-demo"),
}


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/token", response_model=TokenResponse, summary="Issue a JWT access token")
async def issue_token(payload: TokenRequest) -> TokenResponse:
    """
    Exchange username + password for a short-lived JWT.

    For the developer sandbox the only valid credentials are:
      username: demo  /  password: voxintel-demo
    """
    hashed = _DEMO_USERS.get(payload.username)
    if hashed is None or not verify_password(payload.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    expire_minutes = 60
    token = create_access_token(
        subject=payload.username,
        expires_delta=timedelta(minutes=expire_minutes),
    )
    return TokenResponse(
        access_token=token,
        expires_in=expire_minutes * 60,
    )
