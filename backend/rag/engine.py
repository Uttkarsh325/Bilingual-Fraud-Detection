"""
Intent-Aware RAG Engine.

Pipeline per query turn:
  1. Intent classification  — what does the user REALLY want?
  2. Query rewriting        — expand into 2-3 retrieval sub-queries
  3. Multi-query retrieval  — fetch top-k from Qdrant per sub-query
  4. Re-ranking             — deduplicate + score by relevance
  5. Answer generation      — grounded LLM response with citations
"""
import json
import time
import uuid
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from core.config import settings
from core.logging import logger
from core.models import (
    DetectedIntent,
    IntentType,
    RetrievedSource,
    SourceType,
    MessageMetadata,
)
from rag.prompts import INTENT_PROMPT, QUERY_REWRITE_PROMPT, ANSWER_PROMPT
from rag.vector_store import get_vector_store
from services.llm import get_llm


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_json(text: str, fallback: dict) -> dict:
    """Parse JSON from LLM output, stripping markdown fences if needed."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def _doc_to_source(doc: Document, score: float) -> RetrievedSource:
    meta = doc.metadata or {}
    raw_type = meta.get("source_type", "rbi_advisory")
    try:
        source_type = SourceType(raw_type)
    except ValueError:
        source_type = SourceType.RBI_ADVISORY
    return RetrievedSource(
        id=meta.get("id", str(uuid.uuid4())),
        title=meta.get("title", "Advisory Document"),
        snippet=doc.page_content[:300],
        source_url=meta.get("source_url"),
        source_type=source_type,
        relevance_score=round(score, 3),
    )


# ── Main Engine Class ─────────────────────────────────────────────────────────

class IntentAwareRAGEngine:
    """
    Orchestrates intent detection → query rewriting → retrieval → generation.
    """

    TOP_K_PER_QUERY = 4
    MAX_SOURCES = 6

    def __init__(self) -> None:
        self._llm = get_llm()
        self._vs = get_vector_store()
        self._str_parser = StrOutputParser()

    # ── Step 1: Intent Classification ─────────────────────────────────────────

    async def classify_intent(self, query: str) -> DetectedIntent:
        chain = INTENT_PROMPT | self._llm | self._str_parser
        raw = await chain.ainvoke({"query": query})
        parsed = _safe_json(
            raw,
            {
                "intent_type": "general_query",
                "confidence": 0.5,
                "rewritten_query": query,
            },
        )
        return DetectedIntent(
            type=IntentType(parsed.get("intent_type", "general_query")),
            confidence=float(parsed.get("confidence", 0.5)),
            rewritten_query=parsed.get("rewritten_query", query),
        )

    # ── Step 2: Query Rewriting ────────────────────────────────────────────────

    async def rewrite_queries(self, query: str, intent_type: IntentType) -> list[str]:
        chain = QUERY_REWRITE_PROMPT | self._llm | self._str_parser
        raw = await chain.ainvoke({"query": query, "intent_type": intent_type.value})
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            queries = json.loads(raw)
            if isinstance(queries, list):
                return [str(q) for q in queries[:3]]
        except json.JSONDecodeError:
            pass
        return [query]

    # ── Step 3: Multi-Query Retrieval ─────────────────────────────────────────

    def _retrieve(self, queries: list[str]) -> list[tuple[Document, float]]:
        """
        Run each sub-query against Qdrant.
        Returns (doc, score) pairs, deduplicated by page_content.
        """
        seen: set[str] = set()
        results: list[tuple[Document, float]] = []

        for q in queries:
            try:
                hits = self._vs.similarity_search_with_score(q, k=self.TOP_K_PER_QUERY)
                for doc, score in hits:
                    key = doc.page_content[:120]
                    if key not in seen:
                        seen.add(key)
                        results.append((doc, score))
            except Exception as exc:  # noqa: BLE001
                logger.warning("rag.retrieval_error", query=q, error=str(exc))

        return results

    # ── Step 4: Re-Ranking ────────────────────────────────────────────────────

    def _rerank(
        self,
        results: list[tuple[Document, float]],
        intent: DetectedIntent,
    ) -> list[tuple[Document, float]]:
        """
        Simple score-based re-ranking:
        - Boost by intent-type alignment (source_type metadata match)
        - Sort descending by adjusted score
        - Cap at MAX_SOURCES
        """
        INTENT_BOOST = {
            IntentType.REPORT_INCIDENT: {"cybercrime_faq": 0.15},
            IntentType.VERIFY_MESSAGE: {"rbi_advisory": 0.1, "npci_advisory": 0.1},
            IntentType.GET_GUIDANCE: {"scam_pattern": 0.1},
        }
        boosts = INTENT_BOOST.get(intent.type, {})

        adjusted: list[tuple[Document, float]] = []
        for doc, score in results:
            src_type = doc.metadata.get("source_type", "")
            bonus = boosts.get(src_type, 0.0)
            adjusted.append((doc, score + bonus))

        adjusted.sort(key=lambda x: x[1], reverse=True)
        return adjusted[: self.MAX_SOURCES]

    # ── Step 5: Answer Generation ─────────────────────────────────────────────

    async def generate_answer(
        self,
        query: str,
        intent: DetectedIntent,
        sources: list[tuple[Document, float]],
        memory_context: str,
        scam_category: str,
        scam_confidence: float,
        risk_level: str,
    ) -> str:
        context_parts = []
        for i, (doc, score) in enumerate(sources, 1):
            title = doc.metadata.get("title", f"Document {i}")
            context_parts.append(f"[{i}] **{title}** (relevance: {score:.2f})\n{doc.page_content}")
        context = "\n\n".join(context_parts) if context_parts else "No specific advisory found."

        chain = ANSWER_PROMPT | self._llm | self._str_parser
        answer = await chain.ainvoke(
            {
                "context": context,
                "memory_context": memory_context or "No prior interactions.",
                "query": intent.rewritten_query,
                "intent_type": intent.type.value,
                "scam_category": scam_category,
                "scam_confidence": scam_confidence,
                "risk_level": risk_level,
            }
        )
        return answer.strip()

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    async def run(
        self,
        query: str,
        memory_context: str = "",
        scam_result: Optional[dict] = None,
    ) -> tuple[str, MessageMetadata]:
        """
        Run the full intent-aware RAG pipeline.

        Returns:
            (answer_text, MessageMetadata)
        """
        t0 = time.monotonic()

        # 1. Intent
        intent = await self.classify_intent(query)
        logger.info("rag.intent", type=intent.type, confidence=intent.confidence)

        # 2. Query rewriting
        sub_queries = await self.rewrite_queries(intent.rewritten_query, intent.type)
        logger.info("rag.queries", count=len(sub_queries))

        # 3. Retrieval
        raw_results = self._retrieve(sub_queries)

        # 4. Re-ranking
        ranked = self._rerank(raw_results, intent)

        # 5. Build sources list for response metadata
        sources = [_doc_to_source(doc, score) for doc, score in ranked]

        # 6. Scam classification data (passed in from classifier module)
        sc = scam_result or {}
        scam_category = sc.get("category", "unknown")
        scam_confidence = sc.get("confidence", 0.0)
        risk_level = sc.get("risk_level", "low")

        # 7. Generate answer
        answer = await self.generate_answer(
            query=query,
            intent=intent,
            sources=ranked,
            memory_context=memory_context,
            scam_category=scam_category,
            scam_confidence=scam_confidence,
            risk_level=risk_level,
        )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info("rag.complete", ms=elapsed_ms, sources=len(sources))

        metadata = MessageMetadata(
            intent=intent,
            retrieved_sources=sources,
            processing_time_ms=elapsed_ms,
        )
        return answer, metadata


# Singleton
_engine: Optional[IntentAwareRAGEngine] = None


def get_rag_engine() -> IntentAwareRAGEngine:
    global _engine
    if _engine is None:
        _engine = IntentAwareRAGEngine()
    return _engine
