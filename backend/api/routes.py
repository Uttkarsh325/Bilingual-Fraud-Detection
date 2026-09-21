"""
FastAPI route definitions — chat, voice, memory, and health endpoints.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from classification.classifier import classify_text
from core.auth import get_current_user
from core.logging import logger
from core.models import (
    ChatRequest,
    ChatResponse,
    ScamClassification,
    SynthesizeRequest,
    SynthesizeResponse,
    TranscribeResponse,
    UserMemory,
)
from api.pipeline import run_pipeline
from memory.mem0_layer import get_memory_layer
from services.sarvam import sarvam_client
from services.s3 import get_s3

router = APIRouter()


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "FraudGuard AI Backend"}


# ─── Direct ML Classification ────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    text: str


@router.post("/classify", response_model=ScamClassification, tags=["classification"])
async def classify_message(request: ClassifyRequest) -> ScamClassification:
    """
    Direct ML Scam Classification endpoint.
    Runs the trained model (TF-IDF / XGBoost) on CPU in <1ms and returns
    the predicted scam category, confidence score, risk level, and detected indicators.
    """
    return classify_text(request.text)


@router.get("/taxonomy", tags=["classification"])
async def get_taxonomy():
    """Returns the full scam taxonomy definitions and risk levels."""
    from classification.taxonomy import SCAM_TAXONOMY
    return [
        {
            "category": defn.category,
            "label": defn.label,
            "risk_level": defn.risk_level,
            "description": defn.description,
            "keywords": defn.keywords,
        }
        for defn in SCAM_TAXONOMY
    ]


# ─── Chat ─────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
) -> ChatResponse:
    """
    Main conversational endpoint.
    Runs the full LangGraph pipeline:
      memory recall → scam classify → intent-aware RAG → memory store → respond.
    """
    # Allow the auth token user_id to override the request body user_id
    # so the server is always the source of truth in a real deployment.
    if current_user != "anonymous":
        request = request.model_copy(update={"user_id": current_user})

    logger.info(
        "chat.request",
        session=request.session_id,
        user=request.user_id,
        lang=request.language,
        msg_len=len(request.message),
    )

    response = await run_pipeline(request)
    logger.info("chat.response", session=request.session_id, reply_len=len(response.reply))
    return response


# ─── Voice — Transcribe ───────────────────────────────────────────────────────

@router.post("/voice/transcribe", response_model=TranscribeResponse, tags=["voice"])
async def transcribe_audio(
    audio: UploadFile = File(..., description="WebM/WAV audio file"),
    session_id: str = Form(...),
    user_id: str = Form(...),
    language_hint: Optional[str] = Form(default=None),
    current_user: str = Depends(get_current_user),
) -> TranscribeResponse:
    """
    Transcribe an audio file to text using Sarvam AI's STT.
    Optionally uploads the audio to S3 for audit purposes.
    """
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file received",
        )

    # Upload to S3 for audit (non-blocking; errors are swallowed)
    try:
        s3 = get_s3()
        s3.upload_audio(audio_bytes, session_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("voice.s3_upload_failed", error=str(exc))

    try:
        result = await sarvam_client.transcribe(
            audio_bytes=audio_bytes,
            language_code=language_hint,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("voice.transcribe_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Speech-to-text service is temporarily unavailable. Please try again or type your message instead.",
        ) from exc

    return TranscribeResponse(
        transcript=result["transcript"],
        language_detected=result["language_detected"],
        confidence=result["confidence"],
    )


# ─── Voice — Synthesize ───────────────────────────────────────────────────────

@router.post("/voice/synthesize", response_model=SynthesizeResponse, tags=["voice"])
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: str = Depends(get_current_user),
) -> SynthesizeResponse:
    """
    Convert text to speech using Sarvam AI's TTS.
    Returns a pre-signed S3 URL to the generated audio.
    """
    try:
        audio_bytes = await sarvam_client.synthesize(
            text=request.text,
            language_code=request.language_code,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("tts.synthesize_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Text-to-speech service is temporarily unavailable. Please try again later.",
        ) from exc

    # Store in S3 and return presigned URL
    try:
        s3 = get_s3()
        key = s3.upload_audio(audio_bytes, request.session_id)
        audio_url = s3.presign_url(key, expires_in=3600)
    except Exception as exc:  # noqa: BLE001
        logger.warning("tts.s3_failed", error=str(exc))
        # Fallback: return base64 data URL
        import base64
        b64 = base64.b64encode(audio_bytes).decode()
        audio_url = f"data:audio/wav;base64,{b64}"

    return SynthesizeResponse(audio_url=audio_url)


# ─── Memory ───────────────────────────────────────────────────────────────────

@router.get("/memory/{user_id}", response_model=UserMemory, tags=["memory"])
async def get_user_memory(
    user_id: str,
    current_user: str = Depends(get_current_user),
) -> UserMemory:
    """Return a summary of stored memory for a user."""
    mem = get_memory_layer()
    all_memories = mem.get_all(user_id)

    # Extract derived fields from stored memory
    languages = [m.get("metadata", {}).get("language") for m in all_memories if m.get("metadata", {}).get("language")]
    scam_types = list({
        m.get("metadata", {}).get("scam_category")
        for m in all_memories
        if m.get("metadata", {}).get("scam_category")
        and m.get("metadata", {}).get("scam_category") != "unknown"
    })

    from core.models import ScamCategory
    valid_scam_types = []
    for st in scam_types:
        try:
            valid_scam_types.append(ScamCategory(st))
        except ValueError:
            pass

    return UserMemory(
        user_id=user_id,
        preferred_language=languages[-1] if languages else "en-IN",
        reported_scam_types=valid_scam_types,
        session_count=len(all_memories),
        raw_memories=all_memories[:10],  # Return last 10 for UI display
    )


@router.delete("/memory/{user_id}", tags=["memory"])
async def clear_user_memory(
    user_id: str,
    current_user: str = Depends(get_current_user),
) -> dict:
    """Clear all stored memory for a user (GDPR / user-initiated reset)."""
    mem = get_memory_layer()
    mem.delete_all(user_id)
    return {"status": "cleared", "user_id": user_id}
