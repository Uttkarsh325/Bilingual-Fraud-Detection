"""
Persistent memory layer built on mem0.

mem0 stores:
  - User's preferred language
  - Previously reported scam types
  - Prior advisory outcomes / key facts from past sessions
  - Session count

This context is injected into every new query to personalise the advisory.
"""
from typing import Optional
from functools import lru_cache

from core.config import settings
from core.logging import logger


class MemoryLayer:
    """
    Thin wrapper around mem0's Memory class.
    Falls back gracefully if mem0 is unavailable.
    """

    def __init__(self) -> None:
        self._mem = self._init_mem0()

    def _init_mem0(self):
        try:
            from mem0 import Memory

            llm_config = {
                "provider": "groq",
                "config": {
                    "model": settings.groq_model,
                    "api_key": settings.groq_api_key,
                },
            }
            embedder_config = {
                "provider": "huggingface",
                "config": {
                    "model": settings.embedding_model,
                },
            }

            if settings.mem0_provider == "mem0ai" and settings.mem0_api_key:
                # Cloud-backed mem0
                config = {
                    "vector_store": {
                        "provider": "mem0ai",
                        "config": {"api_key": settings.mem0_api_key},
                    },
                    "llm": llm_config,
                    "embedder": embedder_config,
                }
            else:
                # Local mode — uses Qdrant as the memory store
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "url": settings.qdrant_url or None,
                            "api_key": settings.qdrant_api_key or None,
                            "collection_name": "fraudguard_memory",
                            "embedding_model_dims": settings.embedding_dim,
                            "on_disk": False,
                        },
                    },
                    "llm": llm_config,
                    "embedder": embedder_config,
                }
            mem = Memory.from_config(config)
            logger.info("mem0.initialized", provider=settings.mem0_provider)
            return mem
        except Exception as exc:  # noqa: BLE001
            logger.warning("mem0.init_failed", error=str(exc))
            return None

    # ── Store ─────────────────────────────────────────────────────────────────

    def add(self, user_id: str, messages: list[dict], metadata: Optional[dict] = None) -> None:
        """
        Persist a conversation turn to memory.

        Args:
            user_id:  Unique user identifier.
            messages: List of {"role": "user"|"assistant", "content": str}.
            metadata: Optional extra facts (language, scam_category, etc.).

        Note: `infer=False` keeps write-time purely DB-side (no LLM extraction),
        which is both faster and respects low-rate-limit LLM keys. The structured
        facts (language, scam_category, risk_level) travel in `metadata` and are
        surfaced back through build_context_string().
        """
        if self._mem is None:
            return
        try:
            # Trim long replies to keep payloads small.
            trimmed = [
                {
                    "role": msg.get("role", "user"),
                    "content": str(msg.get("content", ""))[:1200],
                }
                for msg in messages
            ]
            self._mem.add(
                messages=trimmed,
                user_id=user_id,
                metadata=metadata or {},
                infer=False,
            )
            logger.info("mem0.add", user_id=user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mem0.add_failed", error=str(exc))

    # ── Recall ────────────────────────────────────────────────────────────────

    def search(self, user_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve the most relevant memory entries for a user + query.

        Returns:
            List of memory dicts with keys: id, memory, created_at, metadata.
        """
        if self._mem is None:
            return []
        try:
            results = self._mem.search(
                query=query,
                filters={"user_id": user_id},
                top_k=top_k,
            )
            memories = results if isinstance(results, list) else results.get("results", [])
            # mem0 v2 may nest results under an "entities"/"results" key
            if isinstance(memories, dict):
                memories = memories.get("results", [])
            logger.info("mem0.search", user_id=user_id, found=len(memories))
            return memories
        except Exception as exc:  # noqa: BLE001
            logger.warning("mem0.search_failed", error=str(exc))
            return []

    def get_all(self, user_id: str) -> list[dict]:
        """Return all stored memories for a user."""
        if self._mem is None:
            return []
        try:
            results = self._mem.get_all(filters={"user_id": user_id})
            memories = results if isinstance(results, list) else results.get("results", [])
            if isinstance(memories, dict):
                memories = memories.get("results", [])
            return memories
        except Exception as exc:  # noqa: BLE001
            logger.warning("mem0.get_all_failed", error=str(exc))
            return []

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete_all(self, user_id: str) -> None:
        """Wipe all memory for a user (GDPR / reset)."""
        if self._mem is None:
            return
        try:
            self._mem.delete_all(user_id=user_id)
            logger.info("mem0.delete_all", user_id=user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mem0.delete_failed", error=str(exc))

    # ── Summarise for prompt injection ────────────────────────────────────────

    def build_context_string(self, user_id: str, query: str) -> str:
        """
        Returns a concise natural-language summary of relevant memories
        suitable for injection into the LLM prompt.
        """
        memories = self.search(user_id=user_id, query=query, top_k=5)
        if not memories:
            return ""

        lines = ["Relevant context from this user's past interactions:"]
        for m in memories:
            meta = m.get("metadata") or {}
            parts = []
            text = m.get("memory", m.get("text", ""))
            if text:
                parts.append(text)
            if meta.get("scam_category") and meta.get("scam_category") != "unknown":
                parts.append(f"(previous report: {meta['scam_category']})")
            if meta.get("language"):
                parts.append(f"(language: {meta['language']})")
            if parts:
                lines.append(f"- {' '.join(parts)}")

        return "\n".join(lines)


@lru_cache(maxsize=1)
def get_memory_layer() -> MemoryLayer:
    return MemoryLayer()
