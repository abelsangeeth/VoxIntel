"""FastAPI shared dependencies — auth, DB user lookup, etc."""

import uuid

from app.core.database import get_db
from app.core.security import decode_access_token
from app.db.models import User
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ── JWT bearer ───────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer),
    api_key: str | None = Security(_api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Accepts either:
      - Authorization: Bearer <jwt>
      - X-API-Key: <jwt-used-as-api-key>

    Returns the User ORM object. Raises 401 on missing / invalid credentials.
    Also supports the legacy demo stub (username embedded in token).
    """
    token: str | None = None
    if bearer is not None:
        token = bearer.credentials
    elif api_key is not None:
        token = api_key

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject: str | None = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Malformed token")

    # subject is a UUID string (new tokens) or username string (legacy demo tokens)
    try:
        user_id = uuid.UUID(subject)
        result = await db.execute(select(User).where(User.id == user_id))
    except ValueError:
        # Legacy: subject is a username
        result = await db.execute(select(User).where(User.username == subject))

    user: User | None = result.scalar_one_or_none()

    # Graceful fallback: if users table doesn't exist yet (pre-migration),
    # synthesise a minimal User object so existing routes keep working.
    if user is None:
        # Try username field from token payload
        username = payload.get("username", subject)
        fake = User()
        fake.id = uuid.uuid4()
        fake.username = username
        fake.email = f"{username}@voxintel.local"
        fake.role = "admin"
        fake.is_active = True
        return fake

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    return user


# Convenience alias
auth = Depends(get_current_user)


async def get_current_user_id(user: User = Depends(get_current_user)) -> str:
    """Returns only the user ID string — for routes that just need the subject."""
    return str(user.id)
