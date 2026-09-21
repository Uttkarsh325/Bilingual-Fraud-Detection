"""
JWT auth + password hashing for FraudGuard AI.

Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib only, no extra deps)
using a per-user random salt and 240k iterations — the same KDF Django uses.

Users are stored in SQLite via SQLAlchemy (see core.user_model).
"""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.db import get_db
from core.user_model import User
from .config import settings

_bearer = HTTPBearer(auto_error=False)

_PBKDF2_ALGO = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 240_000


class TokenData(BaseModel):
    user_id: str
    exp: Optional[datetime] = None


# ─── Password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return "{}${}${}${}".format(
        _PBKDF2_ALGO,
        _PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_b64, hash_b64 = stored.split("$")
        if algo != _PBKDF2_ALGO:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(derived, expected)
    except Exception:  # noqa: BLE001 — malformed/invalid hash, never crash
        return False


# ─── User store helpers ────────────────────────────────────────────────────────

def create_user(db: Session, username: str, password: str) -> User:
    """Create a new user. Raises ValueError if the username is taken."""
    existing = db.query(User).filter(User.username == username).first()
    if existing is not None:
        raise ValueError("Username already registered")

    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ─── JWT ───────────────────────────────────────────────────────────────────────

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
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ─── FastAPI dependency ────────────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """
    Dependency — returns the authenticated username.
    Rejects requests without a valid Bearer token (401).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    data = decode_token(credentials.credentials)
    return data.user_id