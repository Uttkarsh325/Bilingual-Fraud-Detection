"""
FastAPI routes for per-user session history.

Sessions are keyed by the authenticated username, so each account only ever
sees and mutates its own conversations. Transcripts are stored in SQLite via
core.session_model.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.db import get_db
from core.logging import logger
from core.models import (
    SessionCreate,
    SessionDetail,
    SessionMessageIn,
    SessionMessageOut,
    SessionSummary,
    SessionUpdate,
)
from core.session_model import ChatSession, SessionMessage

router = APIRouter()

_TITLE_LIMIT = 80


def _iso(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _session_summary(session: ChatSession) -> SessionSummary:
    return SessionSummary(
        session_id=session.id,
        mode=session.mode,
        title=session.title,
        language=session.language,
        created_at=_iso(session.created_at),
        updated_at=_iso(session.updated_at),
        message_count=len(session.messages),
    )


def _get_owned_session(db: Session, user: str, session_id: str) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user != user:
        raise HTTPException(status_code=403, detail="Session belongs to another user")
    return session


def _load_metadata(raw: str) -> dict:
    try:
        return json.loads(raw or "{}")
    except Exception:  # noqa: BLE001
        return {}


def store_chat_turn(
    db: Session,
    user: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
    metadata: Optional[dict] = None,
    language: str = "en-IN",
    mode: str = "chat",
) -> None:
    """
    Persist one user → assistant turn. Called by the /chat endpoint so every
    completed analysis is recorded automatically for chat and voice mode.
    Never raises — chat must succeed even if persistence fails.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        session = ChatSession(
            id=session_id,
            user=user,
            mode=mode,
            language=language,
            title=(user_message.strip()[:_TITLE_LIMIT] or "New conversation"),
        )
        db.add(session)
        db.flush()
    else:
        if session.user != user:
            return
        if session.title == "New conversation":
            session.title = user_message.strip()[:_TITLE_LIMIT] or "New conversation"

    db.add(
        SessionMessage(
            session_id=session.id,
            role="user",
            content=user_message,
            metadata_json="{}",
        )
    )
    db.add(
        SessionMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_message,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        )
    )
    try:
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("sessions.store_failed", error=str(exc))


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.get("/sessions", response_model=list[SessionSummary], tags=["sessions"])
async def list_sessions(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """List the authenticated user's sessions, most recent first."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user == current_user)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [_session_summary(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetail, tags=["sessions"])
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Return the full transcript of one owned session."""
    session = _get_owned_session(db, current_user, session_id)
    messages = [
        SessionMessageOut(
            role=m.role,
            content=m.content,
            metadata=_load_metadata(m.metadata_json),
            created_at=_iso(m.created_at),
        )
        for m in session.messages
    ]
    return SessionDetail(
        session_id=session.id,
        mode=session.mode,
        title=session.title,
        language=session.language,
        created_at=_iso(session.created_at),
        updated_at=_iso(session.updated_at),
        message_count=len(messages),
        messages=messages,
    )


@router.post("/sessions", response_model=SessionSummary, tags=["sessions"])
async def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Create an empty session (idempotent)."""
    existing = db.query(ChatSession).filter(ChatSession.id == payload.session_id).first()
    if existing is not None:
        if existing.user != current_user:
            raise HTTPException(status_code=403, detail="Session belongs to another user")
        return _session_summary(existing)

    session = ChatSession(
        id=payload.session_id,
        user=current_user,
        mode=payload.mode or "chat",
        title=payload.title or "New conversation",
        language=payload.language or "en-IN",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_summary(session)


@router.put("/sessions/{session_id}", response_model=SessionSummary, tags=["sessions"])
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Update a session's title / language."""
    session = _get_owned_session(db, current_user, session_id)
    if payload.title is not None:
        session.title = payload.title[:300]
    if payload.language is not None:
        session.language = payload.language
    db.commit()
    db.refresh(session)
    return _session_summary(session)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=SessionSummary,
    tags=["sessions"],
)
async def append_message(
    session_id: str,
    payload: SessionMessageIn,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Append a single message. Creates the session on first use."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        session = ChatSession(
            id=session_id,
            user=current_user,
            mode="chat",
            title=(
                payload.content.strip()[:_TITLE_LIMIT]
                if payload.role == "user"
                else "New conversation"
            )
            or "New conversation",
        )
        db.add(session)
        db.flush()
    else:
        if session.user != current_user:
            raise HTTPException(status_code=403, detail="Session belongs to another user")
        if session.title == "New conversation" and payload.role == "user":
            session.title = payload.content.strip()[:_TITLE_LIMIT] or "New conversation"

    db.add(
        SessionMessage(
            session_id=session.id,
            role=payload.role,
            content=payload.content,
            metadata_json=json.dumps(payload.metadata or {}, ensure_ascii=False),
        )
    )
    db.commit()
    db.refresh(session)
    return _session_summary(session)


@router.delete("/sessions/{session_id}", tags=["sessions"])
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> dict:
    """Delete one owned session and its messages."""
    session = _get_owned_session(db, current_user, session_id)
    db.delete(session)
    db.commit()
    return {"status": "deleted", "session_id": session_id}