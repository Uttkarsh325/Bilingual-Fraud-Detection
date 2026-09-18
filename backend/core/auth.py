"""
Minimal JWT auth for demo purposes.
In production, replace with a proper identity provider.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings

_bearer = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    user_id: str
    exp: Optional[datetime] = None


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise ValueError("Missing sub")
        return TokenData(user_id=user_id)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """
    Dependency — returns user_id.
    For demo: if no token is supplied, returns 'anonymous'.
    In production, make this strict.
    """
    if credentials is None:
        return "anonymous"
    data = decode_token(credentials.credentials)
    return data.user_id
