"""
LangGraph orchestration pipeline.

Nodes in the graph:
  memory_recall → classify → rag → memory_store → respond

Each node receives and returns a shared State dict.
"""
import asyncio
from typing import TypedDict, Optional, Any

from langgraph.graph import StateGraph, END, START

from core.logging import logger
from core.models import ChatRequest, ChatResponse, MessageMetadata, ScamClassification
from classification.classifier import classify_text
from memory.mem0_layer import get_memory_layer
from rag.engine import get_rag_engine


# ─── Shared Pipeline State ────────────────────────────────────────────────────

class PipelineState(TypedDict):
    # Input
    session_id: str
    user_id: str
    message: str
    language: str

    # Intermediate
    memory_context: str
    scam_result: Optional[dict]

    # Output
    reply: str
    metadata: Optional[MessageMetadata]
    error: Optional[str]


# ─── Node Implementations ─────────────────────────────────────────────────────

async def node_memory_recall(state: PipelineState) -> PipelineState:
    """Recall relevant memories for this user + message."""
    try:
        mem = get_memory_layer()
        ctx = mem.build_context_string(
            user_id=state["user_id"],
            query=state["message"],
        )
        return {**state, "memory_context": ctx}
    except Exception as exc:  # noqa: BLE001
        logger.warning("pipeline.memory_recall_error", error=str(exc))
        return {**state, "memory_context": ""}


async def node_classify(state: PipelineState) -> PipelineState:
    """Run the scam classifier against the user's message."""
    try:
        # classify_text can trigger CPU-bound ML inference — run in a thread
        # so the async event loop is never blocked.
        result: ScamClassification = await asyncio.to_thread(
            classify_text, state["message"]
        )
        scam_dict = {
            "category": result.category.value,
            "confidence": result.confidence,
            "risk_level": result.risk_level.value,
            "label_display": result.label_display,
            "indicators": result.indicators,
        }
        return {**state, "scam_result": scam_dict}
    except Exception as exc:  # noqa: BLE001
        logger.warning("pipeline.classify_error", error=str(exc))
        return {**state, "scam_result": None}


async def node_rag(state: PipelineState) -> PipelineState:
    """Run the intent-aware RAG engine to generate a grounded answer."""
    try:
        engine = get_rag_engine()
        reply, metadata = await engine.run(
            query=state["message"],
            memory_context=state.get("memory_context", ""),
            scam_result=state.get("scam_result"),
            language=state.get("language", "en-IN"),
        )

        # Attach scam classification to metadata
        if state.get("scam_result"):
            sc = state["scam_result"]
            from core.models import ScamClassification, ScamCategory, RiskLevel
            metadata.scam_classification = ScamClassification(
                category=ScamCategory(sc["category"]),
                confidence=sc["confidence"],
                risk_level=RiskLevel(sc["risk_level"]),
                label_display=sc["label_display"],
                indicators=sc.get("indicators", []),
            )
        metadata.language_detected = state.get("language", "en-IN")

        return {**state, "reply": reply, "metadata": metadata}
    except Exception as exc:  # noqa: BLE001
        logger.error("pipeline.rag_error", error=str(exc))
        return {
            **state,
            "reply": (
                "I'm having trouble analysing your message right now. "
                "If you believe this is a scam, please report it at cybercrime.gov.in "
                "or call the national helpline 1930."
            ),
            "metadata": MessageMetadata(),
            "error": str(exc),
        }


async def node_memory_store(state: PipelineState) -> PipelineState:
    """Persist this turn to the user's memory."""
    try:
        mem = get_memory_layer()
        messages = [
            {"role": "user", "content": state["message"]},
            {"role": "assistant", "content": state["reply"]},
        ]
        extra_meta: dict[str, Any] = {"language": state.get("language", "en-IN")}
        if sc := state.get("scam_result"):
            extra_meta["scam_category"] = sc.get("category")
            extra_meta["risk_level"] = sc.get("risk_level")

        mem.add(
            user_id=state["user_id"],
            messages=messages,
            metadata=extra_meta,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("pipeline.memory_store_error", error=str(exc))

    return state


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_pipeline() -> Any:
    graph = StateGraph(PipelineState)

    graph.add_node("memory_recall", node_memory_recall)
    graph.add_node("classify", node_classify)
    graph.add_node("rag", node_rag)
    graph.add_node("memory_store", node_memory_store)

    graph.add_edge(START, "memory_recall")
    graph.add_edge("memory_recall", "classify")
    graph.add_edge("classify", "rag")
    graph.add_edge("rag", "memory_store")
    graph.add_edge("memory_store", END)

    return graph.compile()


# Singleton compiled graph
_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


# ─── Language auto-detection (script-based fallback) ────────────────────────
# If a message is written in an Indic script but no explicit `language` was
# sent, mirror the message's language so the answer comes back in it. Pure
# script detection — deterministic and zero-latency vs. an external detector.

_SCRIPT_LANGUAGE_MAP = [
    (r"[\u0900-\u097F]", "hi-IN"),  # Devanagari (Hindi, Marathi)
    (r"[\u0980-\u09FF]", "bn-IN"),  # Bengali
    (r"[\u0A00-\u0A7F]", "pa-IN"),  # Gurmukhi (Punjabi)
    (r"[\u0A80-\u0AFF]", "gu-IN"),  # Gujarati
    (r"[\u0B80-\u0BFF]", "ta-IN"),  # Tamil
    (r"[\u0C00-\u0C7F]", "te-IN"),  # Telugu
    (r"[\u0C80-\u0CFF]", "kn-IN"),  # Kannada
    (r"[\u0D00-\u0D7F]", "ml-IN"),  # Malayalam
]


def _detect_script_language(message: str) -> Optional[str]:
    import re

    for pattern, language in _SCRIPT_LANGUAGE_MAP:
        if re.search(pattern, message):
            return language
    return None


# ─── Public Helper ────────────────────────────────────────────────────────────

async def run_pipeline(request: ChatRequest) -> ChatResponse:
    pipeline = get_pipeline()

    requested_language = (request.language or "en-IN").lower()
    if requested_language in ("", "en-in", "unknown"):
        script_lang = _detect_script_language(request.message)
        if script_lang:
            requested_language = script_lang

    initial_state: PipelineState = {
        "session_id": request.session_id,
        "user_id": request.user_id,
        "message": request.message,
        "language": requested_language,
        "memory_context": "",
        "scam_result": None,
        "reply": "",
        "metadata": None,
        "error": None,
    }

    final_state = await pipeline.ainvoke(initial_state)

    return ChatResponse(
        session_id=request.session_id,
        reply=final_state["reply"],
        metadata=final_state["metadata"] or MessageMetadata(),
    )
