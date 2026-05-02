"""FastAPI shared dependencies — auth, rate-limiting guard, etc."""

from app.core.security import decode_access_token
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

# ── JWT bearer ───────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer),
    api_key: str | None = Security(_api_key_header),
) -> str:
    """
    Accepts either:
      - Authorization: Bearer <jwt>
      - X-API-Key: <raw-token-used-as-api-key>

    Returns the subject string (user-id / service-name) embedded in the token.
    Raises 401 on missing / invalid credentials.
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

    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return subject


# Convenience alias so routes can use `Depends(auth)` for brevity
auth = Depends(get_current_user)
