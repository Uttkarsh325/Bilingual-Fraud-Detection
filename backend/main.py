"""
FraudGuard AI — FastAPI application entry point.

Startup sequence:
  1. Configure structured logging
  2. Load settings
  3. Ensure Qdrant collection exists
  4. Mount API routes
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import configure_logging, logger
from api.routes import router
from api.auth_routes import router as auth_router
from api.sessions_routes import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────
    configure_logging()
    logger.info("startup.begin", app=settings.app_name)

    # Ensure the SQLite user store exists
    try:
        from core.db import init_db
        init_db()
        logger.info("startup.db_ready")
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup.db_failed", error=str(exc))

    # Ensure the Qdrant advisory collection exists
    try:
        from rag.vector_store import ensure_collection
        ensure_collection()
        logger.info("startup.qdrant_ready")
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup.qdrant_unavailable", error=str(exc))

    # Warm up the embedding model (download on first run)
    try:
        from rag.embeddings import get_embeddings
        get_embeddings()
        logger.info("startup.embeddings_ready")
    except Exception as exc:  # noqa: BLE001
        logger.warning("startup.embeddings_failed", error=str(exc))

    logger.info("startup.complete", host=settings.backend_host, port=settings.backend_port)
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("shutdown.complete")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Multilingual Financial Fraud & Scam-Pattern Advisory System. "
        "Powered by Sarvam AI, LangGraph, Qdrant, mem0, and an open-source LLM."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(router)
app.include_router(sessions_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level="info",
    )
