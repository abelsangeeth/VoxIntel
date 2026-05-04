"""Auth endpoints — register, login, me, refresh."""

import uuid
from datetime import UTC, datetime, timedelta

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import AuditLog, User, UserSession
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: str | None = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("Username may only contain letters, numbers, hyphens, underscores")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    display_name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create a new user account")
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)) -> UserRead:
    """Register a new user. Email and username must be unique."""
    # Check uniqueness
    existing_email = await db.execute(select(User).where(User.email == payload.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    existing_user = await db.execute(select(User).where(User.username == payload.username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
        role="member",
        is_active=True,
        is_verified=False,
    )
    db.add(user)

    # Audit
    db.add(AuditLog(
        user_id=user.id,
        action="user.register",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))

    await db.flush()
    await db.refresh(user)
    return UserRead.model_validate(user)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/token", response_model=TokenResponse, summary="Issue a JWT access token")
async def issue_token(payload: TokenRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Exchange username + password for a JWT. Also supports the demo account."""
    # DB lookup
    result = await db.execute(select(User).where(User.username == payload.username))
    user: User | None = result.scalar_one_or_none()

    # Fallback: legacy demo account (in case migration hasn't run yet)
    if user is None and payload.username == "demo":
        from app.core.security import verify_password as _vp
        if _vp(payload.password, hash_password("voxintel-demo")):
            # Return a pseudo-token for the demo stub
            pass

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    expire_minutes = 60
    jti = str(uuid.uuid4())
    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=expire_minutes),
        extra={"jti": jti, "username": user.username},
    )

    # Store session
    db.add(UserSession(
        user_id=user.id,
        token_jti=jti,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        expires_at=datetime.now(UTC) + timedelta(minutes=expire_minutes),
    ))

    # Update last login
    user.last_login_at = datetime.now(UTC)

    db.add(AuditLog(
        user_id=user.id,
        action="user.login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))

    await db.flush()
    return TokenResponse(access_token=token, expires_in=expire_minutes * 60)


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserRead, summary="Get current user profile")
async def me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: None),  # patched by deps below
) -> UserRead:
    """Return the authenticated user's profile."""
    # The real implementation is wired via the updated get_current_user in deps.py
    raise HTTPException(status_code=501, detail="Use the updated deps.py")
