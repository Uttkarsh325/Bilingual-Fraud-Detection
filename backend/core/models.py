"""
Shared Pydantic request/response models used across the API.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ─── Scam Taxonomy ────────────────────────────────────────────────────────────

class ScamCategory(str, Enum):
    UPI_COLLECT_SCAM = "upi_collect_scam"
    PHISHING_LINK = "phishing_link"
    VOICE_PHISHING = "voice_phishing"
    LOTTERY_PRIZE = "lottery_prize"
    JOB_OFFER_SCAM = "job_offer_scam"
    LOAN_SCAM = "loan_scam"
    SIM_SWAP = "sim_swap"
    INVESTMENT_SCAM = "investment_scam"
    OTP_SCAM = "otp_scam"
    FAKE_REFUND = "fake_refund"
    BENIGN = "benign"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


class ScamClassification(BaseModel):
    category: ScamCategory
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    label_display: str
    indicators: list[str] = Field(default_factory=list)


# ─── Intent ───────────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    VERIFY_MESSAGE = "verify_message"
    GET_GUIDANCE = "get_guidance"
    REPORT_INCIDENT = "report_incident"
    GENERAL_QUERY = "general_query"
    FOLLOW_UP = "follow_up"


class DetectedIntent(BaseModel):
    type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    rewritten_query: str


# ─── RAG Sources ─────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    RBI_ADVISORY = "rbi_advisory"
    NPCI_ADVISORY = "npci_advisory"
    CYBERCRIME_FAQ = "cybercrime_faq"
    SCAM_PATTERN = "scam_pattern"


class RetrievedSource(BaseModel):
    id: str
    title: str
    snippet: str
    source_url: Optional[str] = None
    source_type: SourceType
    relevance_score: float = Field(ge=0.0, le=1.0)


# ─── Chat API ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    language: Optional[str] = "en-IN"
    mode: Optional[str] = "chat"


class MessageMetadata(BaseModel):
    scam_classification: Optional[ScamClassification] = None
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    intent: Optional[DetectedIntent] = None
    language_detected: Optional[str] = None
    processing_time_ms: Optional[int] = None
    audio_url: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: MessageMetadata


# ─── Voice API ───────────────────────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    transcript: str
    language_detected: str
    confidence: float


class SynthesizeRequest(BaseModel):
    text: str
    language_code: str
    session_id: str


class SynthesizeResponse(BaseModel):
    audio_url: str


# ─── Memory API ──────────────────────────────────────────────────────────────

class UserMemory(BaseModel):
    user_id: str
    preferred_language: str = "en-IN"
    reported_scam_types: list[ScamCategory] = Field(default_factory=list)
    session_count: int = 0
    last_active: Optional[str] = None
    raw_memories: list[dict] = Field(default_factory=list)


# ─── Session History API ─────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    session_id: str
    mode: Optional[str] = "chat"
    language: Optional[str] = "en-IN"
    title: Optional[str] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None


class SessionMessageIn(BaseModel):
    role: str
    content: str
    metadata: Optional[dict] = None


class SessionMessageOut(BaseModel):
    role: str
    content: str
    metadata: dict = Field(default_factory=dict)
    created_at: str


class SessionSummary(BaseModel):
    session_id: str
    mode: str = "chat"
    title: str
    language: str = "en-IN"
    created_at: str
    updated_at: str
    message_count: int = 0


class SessionDetail(SessionSummary):
    messages: list[SessionMessageOut] = Field(default_factory=list)


# ─── Translation API ─────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str
    target: str = "en-IN"  # BCP-47 code to translate INTO


class TranslateResponse(BaseModel):
    translated_text: str
    target: str
