"""
Central configuration — reads from environment / .env file.
All other modules import `settings` from here.
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Resolve .env relative to this file: backend/core/config.py → ../../.env
_ENV_FILE = str(Path(__file__).resolve().parent.parent.parent / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "FraudGuard AI"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # ── Auth ─────────────────────────────────────────────────────────────────
    jwt_secret: str = Field(default="change_me_in_production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # ── Sarvam AI ────────────────────────────────────────────────────────────
    sarvam_api_key: str = Field(default="")
    sarvam_api_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_speaker: str = "amit"

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = "groq"          # groq | ollama
    groq_api_key: str = Field(default="")
    groq_model: str = "openai/gpt-oss-20b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # ── Qdrant ───────────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = Field(default="")
    qdrant_collection_name: str = "fraud_advisories"

    # ── mem0 ─────────────────────────────────────────────────────────────────
    mem0_api_key: str = Field(default="")
    mem0_provider: str = "local"        # local | mem0ai

    # ── AWS S3 ───────────────────────────────────────────────────────────────
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    aws_region: str = "ap-south-1"
    s3_bucket_name: str = "fraud-advisory-store"

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
