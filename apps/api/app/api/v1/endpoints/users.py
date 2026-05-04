"""Users endpoints — profile management, listing (admin only)."""

import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.models import User
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    display_name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    is_verified: bool
    preferences: dict
    last_login_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    preferences: dict | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserRead, summary="Get your profile")
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, summary="Update your profile")
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.preferences is not None:
        current_user.preferences = payload.preferences
    await db.flush()
    await db.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT, summary="Change password")
async def change_password(
    payload: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=422, detail="New password must be at least 8 characters")
    current_user.hashed_password = hash_password(payload.new_password)
    await db.flush()


@router.get("", response_model=list[UserRead], summary="List all users (admin only)")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserRead]:
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserRead, summary="Get a user by ID (admin only)")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if current_user.role not in ("admin", "owner") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)
