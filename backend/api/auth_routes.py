"""
Authentication endpoints — register, login, and current-user information.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
)
from core.config import settings
from core.db import get_db
from core.user_model import User

router = APIRouter(prefix="/auth", tags=["auth"])


class CredentialsRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    expires_in: Optional[int] = None


class UserInfo(BaseModel):
    user_id: int
    username: str
    created_at: str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: CredentialsRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Create a new account and return a JWT (auto-login)."""
    username = request.username.strip()
    try:
        user = create_user(db, username, request.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    token = create_access_token(user.username)
    return AuthResponse(
        access_token=token,
        username=user.username,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: CredentialsRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Authenticate credentials and return a JWT."""
    user = authenticate_user(db, request.username.strip(), request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.username)
    return AuthResponse(
        access_token=token,
        username=user.username,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=UserInfo)
async def me(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserInfo:
    """Return details for the currently authenticated user."""
    user = db.query(User).filter(User.username == current_user).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return UserInfo(
        user_id=user.id,
        username=user.username,
        created_at=user.created_at.isoformat(),
    )