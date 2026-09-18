"""
Sarvam AI integration — STT, TTS, and Indic language text understanding.

Docs: https://docs.sarvam.ai/
All calls are async via httpx.
"""
import base64
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.logging import logger


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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def transcribe(
        self,
        audio_bytes: bytes,
        language_code: Optional[str] = None,
    ) -> dict:
        """
        Convert speech audio (WebM/WAV/MP3) to text using multipart upload.

        Returns:
            {
                "transcript": str,
                "language_code": str,
                "confidence": float
            }
        """
        # Sarvam STT expects multipart/form-data, NOT base64 JSON.
        # httpx sets Content-Type + boundary automatically when files= is used.
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
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
