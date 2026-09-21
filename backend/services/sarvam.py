"""
Sarvam AI integration — STT, TTS, and Indic language text understanding.

Docs: https://docs.sarvam.ai/
All calls are async via httpx.
"""
import base64
import os
import shutil
import subprocess
import tempfile
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from core.config import settings
from core.logging import logger


def normalize_audio(
    data: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> tuple[bytes, str, str]:
    """
    Normalise arbitrary browser audio into a canonical 16 kHz mono WAV.

    Real MediaRecorder captures (WebM/Opus fragments, Safari's .mp4) sometimes
    carry non-standard metadata that downstream decoders reject. Re-muxing via
    ffmpeg gives Sarvam a clean, universally decodable payload.

    Falls back to the original bytes (pass-through) when ffmpeg is unavailable.
    Returns (audio_bytes, filename, content_type).
    """
    if shutil.which("ffmpeg") is None or not data:
        return data, filename or "audio.wav", content_type or "audio/wav"

    try:
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "in")
            dst = os.path.join(td, "out.wav")
            with open(src, "wb") as f:
                f.write(data)
            proc = subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", src,
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                    dst,
                ],
                capture_output=True,
                timeout=30,
            )
            if proc.returncode != 0:
                logger.warning("sarvam.normalize_failed", err=proc.stderr.decode()[:200])
                return data, filename or "audio.wav", content_type or "audio/wav"
            with open(dst, "rb") as f:
                return f.read(), "audio.wav", "audio/wav"
    except Exception as exc:  # noqa: BLE001
        logger.warning("sarvam.normalize_error", error=str(exc))
        return data, filename or "audio.wav", content_type or "audio/wav"


def _retryable_stt(exc: BaseException) -> bool:
    """
    Retry only transient failures (5xx, rate limits, network timeouts).
    4xx errors mean the audio/key is bad — retrying is pointless and slow.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return isinstance(
        exc, (httpx.TimeoutException, httpx.TransportError, httpx.ConnectError)
    )


# Sarvam's `bulbul:v3` TTS uses a set of base speakers that work across all
# supported languages. Map our supported BCP-47 codes to a base speaker for
# natural variety and fall back to a neutral default speaker for unmapped ones.
LANG_TO_SPEAKER: dict[str, str] = {
    "en-IN": "simran",
    "hi-IN": "kabir",
    "bn-IN": "roopa",
    "ta-IN": "kavya",
    "te-IN": "varun",
    "mr-IN": "shubh",
    "gu-IN": "ishita",
    "kn-IN": "aditya",
    "pa-IN": "pooja",
}


def resolve_speaker(language_code: str) -> str:
    """Pick the best Sarvam speaker for a BCP-47 language code."""
    if language_code in LANG_TO_SPEAKER:
        return LANG_TO_SPEAKER[language_code]
    base = language_code.split("-")[0].lower() if language_code else ""
    for code, speaker in LANG_TO_SPEAKER.items():
        if code.split("-")[0].lower() == base:
            return speaker
    return settings.sarvam_speaker


class SarvamClient:
    """Thin async wrapper around Sarvam AI's REST API."""

    def __init__(self) -> None:
        self._base = settings.sarvam_api_base_url
        # Auth header only — Content-Type is set per-request to match the endpoint
        self._auth_headers = {
            "api-subscription-key": settings.sarvam_api_key,
        }
        # JSON endpoints also need Content-Type
        self._json_headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json",
        }

    # ── Speech-to-Text ────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=4),
        retry=retry_if_exception(_retryable_stt),
    )
    async def transcribe(
        self,
        audio_bytes: bytes,
        language_code: Optional[str] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """
        Convert speech audio to text using multipart upload.

        Args:
            audio_bytes:  Raw audio payload as captured by the browser.
            language_code: Optional BCP-47 hint, e.g. "en-IN".
            filename:     Original file name from the upload (preserved so
                          Sarvam's decoder sees the true container — e.g.
                          .webm/.mp4 from a MediaRecorder, not a fake .wav).
            content_type: Original MIME type of the upload.

        Returns:
            {
                "transcript": str,
                "language_code": str,
                "confidence": float
            }
        """
        # Sarvam STT expects multipart/form-data, NOT base64 JSON.
        # httpx sets Content-Type + boundary automatically when files= is used.
        files = {
            "file": (
                filename or "audio.wav",
                audio_bytes,
                content_type or "audio/wav",
            )
        }
        data: dict = {"model": settings.sarvam_stt_model}
        if language_code:
            data["language_code"] = language_code

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base}/speech-to-text",
                headers=self._auth_headers,   # no Content-Type here — httpx sets it
                files=files,
                data=data,
            )
            resp.raise_for_status()
            result = resp.json()

        logger.info("sarvam.transcribe", language=result.get("language_code"))
        return {
            "transcript": result.get("transcript", ""),
            "language_detected": result.get("language_code", language_code or "en-IN"),
            "confidence": result.get("confidence", 1.0),
        }

    # ── Text-to-Speech ────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def synthesize(
        self,
        text: str,
        language_code: str = "hi-IN",
        speaker: Optional[str] = None,
    ) -> bytes:
        """
        Convert text to speech audio (WAV bytes).

        Args:
            text:          Text to synthesize (max 500 chars per chunk).
            language_code: BCP-47 language, e.g. "hi-IN", "en-IN".
            speaker:       Sarvam voice name; defaults to the best match for
                           `language_code` (see resolve_speaker).

        Returns:
            Raw WAV audio bytes.
        """
        payload = {
            "inputs": [text[:500]],
            "target_language_code": language_code,
            "speaker": speaker or resolve_speaker(language_code),
            "model": settings.sarvam_tts_model,
            "enable_preprocessing": True,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base}/text-to-speech",
                headers=self._json_headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # Sarvam returns base64-encoded audio in audios[0]
        audio_b64 = data.get("audios", [""])[0]
        audio_bytes = base64.b64decode(audio_b64)
        logger.info("sarvam.synthesize", lang=language_code, bytes=len(audio_bytes))
        return audio_bytes

    # ── Language Detection ────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def detect_language(self, text: str) -> str:
        """
        Detect the language of a text snippet.
        Returns a BCP-47 language code, e.g. "hi-IN".
        """
        payload = {"input": text, "model": "sarvam-2b"}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self._base}/text-lid",
                headers=self._json_headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        lang = data.get("language_code", "en-IN")
        logger.info("sarvam.detect_language", result=lang)
        return lang

    # ── Transliterate (script conversion) ─────────────────────────────────────

    async def transliterate(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        """Transliterate text between scripts (e.g. Roman Hindi → Devanagari)."""
        payload = {
            "input": text,
            "source_language_code": source_lang,
            "target_language_code": target_lang,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self._base}/transliterate",
                headers=self._json_headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("transliterated_text", text)


# Singleton
sarvam_client = SarvamClient()
