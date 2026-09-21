"""
SQLAlchemy ORM models for per-user session history.

Each session belongs to exactly one authenticated user (column: user) so
different accounts can never see or touch each other's conversations.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="chat", nullable=False)
    title: Mapped[str] = mapped_column(String(300), default="New conversation", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en-IN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    messages: Mapped[list["SessionMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionMessage.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChatSession id={self.id} user={self.user!r} mode={self.mode}>"


class SessionMessage(Base):
    __tablename__ = "session_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SessionMessage id={self.id} role={self.role}>"