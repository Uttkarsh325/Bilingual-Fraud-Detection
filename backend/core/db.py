"""
SQLAlchemy database setup — SQLite engine, session factory, and base class.

Used by the user auth layer. The DB file lives at backend/fraudguard.db
and is excluded from git.
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "fraudguard.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite + FastAPI threads
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a scoped DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist. Called once at app startup."""
    from core.user_model import User  # noqa: F401  (register model with Base)
    from core.session_model import ChatSession, SessionMessage  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)