// ─── Message Types ─────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  scam_classification?: ScamClassification;
  retrieved_sources?: RetrievedSource[];
  intent?: DetectedIntent;
  language_detected?: string;
  processing_time_ms?: number;
  audio_url?: string;        // TTS audio for this response
}

// ─── Scam Classification ───────────────────────────────────────────────────────

export type RiskLevel = "high" | "medium" | "low" | "safe";

export type ScamCategory =
  | "upi_collect_scam"
  | "phishing_link"
  | "voice_phishing"
  | "lottery_prize"
  | "job_offer_scam"
  | "loan_scam"
  | "sim_swap"
  | "investment_scam"
  | "otp_scam"
  | "fake_refund"
  | "unknown";

export interface ScamClassification {
  category: ScamCategory;
  confidence: number;          // 0–1
  risk_level: RiskLevel;
  label_display: string;       // Human-readable label
  indicators: string[];        // Key phrases / signals detected
}

// ─── Intent Detection ──────────────────────────────────────────────────────────

export type IntentType =
  | "verify_message"
  | "get_guidance"
  | "report_incident"
  | "general_query"
  | "follow_up";

export interface DetectedIntent {
  type: IntentType;
  confidence: number;
  rewritten_query: string;     // The query as understood by the RAG engine
}

// ─── RAG Sources ───────────────────────────────────────────────────────────────

export interface RetrievedSource {
  id: string;
  title: string;
  snippet: string;
  source_url?: string;
  source_type: "rbi_advisory" | "npci_advisory" | "cybercrime_faq" | "scam_pattern";
  relevance_score: number;
}

// ─── API Request / Response ───────────────────────────────────────────────────

export interface ChatRequest {
  session_id: string;
  user_id: string;
  message: string;
  language?: string;           // ISO 639-1 or BCP-47, e.g. "hi", "en", "ta"
  mode?: "chat" | "voice";
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  metadata: MessageMetadata;
  audio_url?: string;          // Pre-signed S3 URL if TTS was requested
}

export interface VoiceTranscribeRequest {
  session_id: string;
  user_id: string;
  audio_blob: Blob;
  language_hint?: string;
}

export interface VoiceTranscribeResponse {
  transcript: string;
  language_detected: string;
  confidence: number;
}

// ─── Memory ───────────────────────────────────────────────────────────────────

export interface UserMemory {
  user_id: string;
  preferred_language: string;
  reported_scam_types: ScamCategory[];
  session_count: number;
  last_active: string;
}

// ─── Session History ──────────────────────────────────────────────────────────

export type SessionMode = "chat" | "voice";

export interface SessionSummary {
  session_id: string;
  mode: SessionMode;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SessionMessageRecord {
  role: MessageRole;
  content: string;
  metadata: MessageMetadata;
  created_at: string;
}

export interface SessionDetail extends SessionSummary {
  messages: SessionMessageRecord[];
}

// ─── Translation ─────────────────────────────────────────────────────────────

export interface TranslateResponse {
  translated_text: string;
  target: string;
}

// ─── UI State ─────────────────────────────────────────────────────────────────

export interface ConversationState {
  sessionId: string;
  userId: string;
  messages: ChatMessage[];
  isLoading: boolean;
  isRecording: boolean;
  isSpeaking: boolean;
  selectedLanguage: SupportedLanguage;
  error: string | null;
}

export interface SupportedLanguage {
  code: string;        // BCP-47 e.g. "hi-IN"
  name: string;        // "Hindi"
  nativeName: string;  // "हिन्दी"
  sarvamCode: string;  // Sarvam AI language code
}

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { code: "en-IN", name: "English", nativeName: "English", sarvamCode: "en-IN" },
  { code: "hi-IN", name: "Hindi", nativeName: "हिन्दी", sarvamCode: "hi-IN" },
  { code: "bn-IN", name: "Bengali", nativeName: "বাংলা", sarvamCode: "bn-IN" },
  { code: "ta-IN", name: "Tamil", nativeName: "தமிழ்", sarvamCode: "ta-IN" },
  { code: "te-IN", name: "Telugu", nativeName: "తెలుగు", sarvamCode: "te-IN" },
  { code: "mr-IN", name: "Marathi", nativeName: "मराठी", sarvamCode: "mr-IN" },
  { code: "gu-IN", name: "Gujarati", nativeName: "ગુજરાતી", sarvamCode: "gu-IN" },
  { code: "kn-IN", name: "Kannada", nativeName: "ಕನ್ನಡ", sarvamCode: "kn-IN" },
  { code: "ml-IN", name: "Malayalam", nativeName: "മലയാളം", sarvamCode: "ml-IN" },
  { code: "pa-IN", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ", sarvamCode: "pa-IN" },
];

export const SCAM_CATEGORY_LABELS: Record<ScamCategory, string> = {
  upi_collect_scam: "UPI Collect Scam",
  phishing_link: "Phishing Link",
  voice_phishing: "Voice Phishing (Vishing)",
  lottery_prize: "Lottery / Prize Fraud",
  job_offer_scam: "Fake Job Offer",
  loan_scam: "Fake Loan Scam",
  sim_swap: "SIM Swap Fraud",
  investment_scam: "Investment / Crypto Scam",
  otp_scam: "OTP Fraud",
  fake_refund: "Fake Refund Scam",
  unknown: "Unknown / Review Needed",
};

export const RISK_COLORS: Record<RiskLevel, string> = {
  high: "text-red-400",
  medium: "text-amber-400",
  low: "text-yellow-400",
  safe: "text-green-400",
};
