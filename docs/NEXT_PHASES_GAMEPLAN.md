# FraudGuard AI — Next Phases Gameplan
**Document Purpose:** Detailed, step-by-step execution plan for all remaining phases (4 → 12), written after a thorough audit of the actual codebase against the master `AGENTIC_IMPLEMENTATION_PLAN.md`.  
**Last Updated:** 2026-09-21

---

## ✅ Completed Phases — Verified Against Codebase

| Phase | Status | Evidence |
|---|---|---|
| **Phase 0** — Architecture & Contracts | ✅ **COMPLETE** | `backend/core/models.py`, `backend/main.py`, `backend/classification/taxonomy.py`, `docker-compose.yml` exist with full Pydantic contracts and FastAPI app |
| **Phase 1** — Knowledge Ingestion & Advisories | ✅ **COMPLETE** | `docs/advisories/*.txt`, `ingestion/chunker.py`, `ingestion/embedder.py`, `ingestion/ingest.py` implemented |
| **Phase 2** — Baseline Classification & LangGraph Pipeline | ✅ **COMPLETE** | `backend/api/pipeline.py` has full 4-node LangGraph (`memory_recall → classify → rag → memory_store`), `backend/classification/classifier.py` has 3-tier system, `backend/memory/mem0_layer.py` exists |
| **Phase 3** — Trainable ML Classifiers | ✅ **COMPLETE** | `training/train_baseline.py` (TF-IDF + LogReg), `training/train_advanced.py` (FeatureUnion + XGBoost), `models/baseline_tfidf.joblib`, `models/advanced_xgboost.joblib`, `evaluation/advanced_metrics.json` (99.84% accuracy on 1,924 test samples), `evaluation/compare_classifiers.py` all done |

> [!IMPORTANT]
> **The project is fully complete through Phase 3.** The RAG engine (`backend/rag/engine.py`) and prompts (`backend/rag/prompts.py`) are also scaffolded as part of Phase 2, giving Phase 4 a strong head start. The Sarvam AI client (`backend/services/sarvam.py`) is fully implemented with STT/TTS/transliterate, giving Phase 6 a partial start.

---

## 🚀 Next Phases — Detailed Gameplan

---

### Phase 4: Production Grounded RAG & Provenance Layer
**Priority:** HIGH — Directly enables Phases 5 & 6  
**Estimated Effort:** 1–2 days  
**Goal:** Upgrade the existing RAG engine (`backend/rag/engine.py`) with richer provenance and cosine-threshold filtering.

#### What Already Exists
- `backend/rag/engine.py` — Full intent-aware RAG with query rewriting and re-ranking
- `backend/rag/vector_store.py` — Qdrant vector store with payload indexes for `source_type` and `scam_category`
- `ingestion/chunker.py` & `ingestion/embedder.py` — Chunking pipeline

#### Tasks

**4.1 — Enhance Chunk Provenance Metadata** (`ingestion/chunker.py`)
- Add these fields to every chunk's metadata dict before embedding:
  ```python
  {
    "document_id":    "rbi-upi-safety-2024",   # unique slug per document
    "authority":      "RBI",                    # RBI | NPCI | MHA_Cybercrime
    "source_url":     "https://rbi.org.in/...", # canonical URL
    "section_title":  "Customer Liability",     # H2/H3 heading from the doc
    "effective_date": "2024-01-15",             # YYYY-MM-DD
  }
  ```
- Update `ingestion/ingest.py` to pass these fields when calling the embedder.
- Re-run ingestion so all Qdrant vectors carry the enriched payload.

**4.2 — Add Cosine Similarity Threshold** (`backend/rag/engine.py`)
- In `_retrieve()`, filter out hits with `score < 0.65` before adding to results:
  ```python
  if score >= 0.65:
      results.append((doc, score))
  ```
- Add a `SIMILARITY_THRESHOLD = 0.65` class constant so it is easy to tune.

**4.3 — Category-Injected Query Rewriting** (`backend/rag/engine.py`)
- Modify `run()` to pass `scam_category` into `rewrite_queries()`.
- Update `rewrite_queries()` signature to accept `scam_category: str = "unknown"`.
- Update `QUERY_REWRITE_PROMPT` in `backend/rag/prompts.py` to include the scam category in the human message so the LLM can use it to write domain-specific sub-queries.

**4.4 — Verification**
- Write a `tests/test_rag_retrieval.py` script that calls `engine.run()` on 5 sample queries (one per major scam category) and asserts:
  - At least 1 retrieved source with `score >= 0.65`
  - Each source has `authority`, `source_url`, and `document_id` in metadata

---

### Phase 5: Anti-Hallucination Grounded Prompting & Structured Advisory Output
**Priority:** HIGH — Core academic differentiator  
**Estimated Effort:** 1 day  
**Goal:** Replace the current free-text LLM answer with a strictly structured JSON advisory output validated by Pydantic.

#### What Already Exists
- `backend/rag/prompts.py` — Basic `ANSWER_PROMPT` with source grounding guardrails
- `backend/core/models.py` — Pydantic models (will need new `AdvisoryReport` model)

#### Tasks

**5.1 — Add `AdvisoryReport` Pydantic Model** (`backend/core/models.py`)
```python
class RiskVerdict(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AdvisoryReport(BaseModel):
    summary: str                          # 2-3 sentence plain-language verdict
    risk_verdict: RiskVerdict
    detected_indicators: list[str]        # e.g. ["Urgency", "OTP Demand"]
    why_suspicious: str                   # Cites RBI/NPCI directives
    do_list: list[str]                    # "Call 1930 immediately"
    dont_list: list[str]                  # "Never share your UPI PIN"
    citations: list[RetrievedSource]      # Already defined in models.py
```

**5.2 — Rewrite `ANSWER_PROMPT`** (`backend/rag/prompts.py`)
- Instruct the LLM to output **only** a valid JSON object matching `AdvisoryReport`.
- Include a few-shot example JSON in the system prompt.
- Add explicit rule: *"If no relevant advisory passage exists, set why_suspicious to 'Insufficient evidence — please consult cybercrime.gov.in' and risk_verdict to 'low'."*
- Preserve the existing `context`, `memory_context`, `query`, `scam_category`, `scam_confidence`, and `risk_level` template variables.

**5.3 — Parse & Validate LLM Output** (`backend/rag/engine.py`)
- In `generate_answer()`, after the chain call, attempt `AdvisoryReport.model_validate_json(answer)`.
- On validation failure, fall back to a safe default `AdvisoryReport` with `risk_verdict=LOW` and emergency info.
- Return the `AdvisoryReport` object (not raw string) from `generate_answer()`.
- Update `run()` to embed the `AdvisoryReport` into `MessageMetadata`.

**5.4 — Update API Response** (`backend/core/models.py`, `backend/api/pipeline.py`)
- Add `advisory_report: Optional[AdvisoryReport]` to `MessageMetadata`.
- Serialize as JSON in the `ChatResponse` so the frontend can render structured sections.

**5.5 — Verification**
- Run 3 mock queries (phishing, OTP scam, benign message).
- Verify zero unsupported legal claims.
- Verify `citations` always references actual retrieved passage titles.
- Verify `do_list` always contains `"Call 1930"` for high-risk verdicts.

---

### Phase 6: Multilingual Advisory Engine (Hindi & Regional)
**Priority:** HIGH — Key academic requirement  
**Estimated Effort:** 1–2 days  
**Goal:** Deliver advisory responses in Hindi (and optionally Tamil/Bengali).

#### What Already Exists
- `backend/services/sarvam.py` — **Fully implemented** with `transcribe()`, `synthesize()`, `detect_language()`, and `transliterate()` methods
- `backend/api/routes.py` — `/voice/transcribe` and `/voice/synthesize` endpoints exist
- Sarvam speaker map covers: `en-IN`, `hi-IN`, `bn-IN`, `ta-IN`, `te-IN`, `mr-IN`, etc.

#### Tasks

**6.1 — Create `backend/services/multilingual.py`** (New File)
```python
# Responsibilities:
# 1. Detect the input language (call sarvam_client.detect_language(text))
# 2. If non-English detected, translate query to English for RAG retrieval
# 3. After advisory is generated (English), translate back to user's language
# 4. Preserve safety-critical terms in English: "UPI PIN", "OTP", "1930", "cybercrime.gov.in"

class MultilingualAdvisoryService:
    SAFETY_TERMS = ["UPI PIN", "OTP", "1930", "cybercrime.gov.in", "NPCI", "RBI"]
    
    async def translate(self, text: str, target_lang: str) -> str: ...
    async def process_bilingual(self, text: str, language: str) -> tuple[str, str]: 
        # Returns (english_query_for_rag, detected_language_code)
```

**6.2 — Integrate into LangGraph Pipeline** (`backend/api/pipeline.py`)
- Add a new `node_multilingual_preprocess` node **before** `node_classify`:
  - Detects language from user message
  - Stores `detected_language` in `PipelineState`
  - Sets `english_message` for downstream nodes to use
- Add a new `node_multilingual_postprocess` node **after** `node_rag`:
  - If `detected_language != "en-IN"`, translates `state["reply"]` to the detected language
  - Preserves safety terms

**6.3 — Update `PipelineState`** (`backend/api/pipeline.py`)
- Add `detected_language: str` and `english_message: str` fields.
- Update `node_classify` and `node_rag` to use `english_message` for processing.

**6.4 — Verification**
- Submit a Hindi KYC scam message: *"आपका KYC अपडेट करें या खाता बंद हो जाएगा"*
- Verify advisory is returned in Hindi.
- Verify safety terms (UPI PIN, 1930) are not translated.

---

### Phase 7: Multimodal Extension 1 — Suspicious URL Analyzer
**Priority:** MEDIUM  
**Estimated Effort:** 1 day  
**Goal:** Passive heuristic URL analysis without making live network calls to dangerous hosts.

#### Tasks

**7.1 — Create `backend/classification/url_analyzer.py`** (New File)
```python
from dataclasses import dataclass, field
import re, ipaddress
from urllib.parse import urlparse

BRAND_KEYWORDS = ["sbi", "paytm", "hdfc", "icici", "npci", "rbi", "irctc", "uidai"]
SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".club", ".buzz", ".gq", ".ml", ".cf"}
SHORTENERS = {"bit.ly", "tinyurl.com", "is.gd", "t.co", "ow.ly", "rb.gy", "tiny.cc"}

@dataclass
class URLAnalysisResult:
    url: str
    is_suspicious: bool
    risk_signals: list[str] = field(default_factory=list)
    risk_score: float = 0.0   # 0.0 to 1.0

def analyze_url(url: str) -> URLAnalysisResult:
    # Detectors to implement:
    # 1. IP-as-hostname check (re.match for IPv4 pattern in netloc)
    # 2. Brand impersonation (check if BRAND_KEYWORDS in domain but domain != official)
    # 3. Shortener detection (netloc in SHORTENERS)
    # 4. Suspicious TLD (os.path.splitext on domain)
    # 5. Excessive subdomains (netloc.count('.') > 3)
    # 6. Punycode / homoglyph (xn-- in netloc)
    # 7. Path contains credential-demand keywords: kyc, login, verify, update, otp
```

**7.2 — Integrate URL Extraction into `classify_text()`** (`backend/classification/classifier.py`)
- In `_extract_indicators()`, detect URLs via regex.
- For each URL found, call `analyze_url()` and merge `risk_signals` into the indicators list.

**7.3 — Add `/url/analyze` Endpoint** (`backend/api/routes.py`)
```python
class URLAnalyzeRequest(BaseModel):
    url: str

@router.post("/url/analyze", tags=["multimodal"])
async def analyze_url_endpoint(request: URLAnalyzeRequest): ...
```

**7.4 — Verification**
- Unit tests in `tests/test_url_analyzer.py`:
  - `https://sbi.co.in` → `is_suspicious=False`
  - `http://bit.ly/sbi-kyc-alert` → `is_suspicious=True`, `risk_signals` includes "shortener"
  - `http://192.168.1.1/sbi` → `is_suspicious=True`, `risk_signals` includes "ip_as_hostname"
  - `https://sbi-kyc-update.com` → `is_suspicious=True`, `risk_signals` includes "brand_impersonation"

---

### Phase 8: Multimodal Extension 2 — Screenshot OCR Pipeline
**Priority:** MEDIUM  
**Estimated Effort:** 1–2 days  
**Goal:** Extract text from uploaded screenshots (SMS/WhatsApp/UPI) and feed into the analysis pipeline.

#### Tasks

**8.1 — Install OCR Dependency**
- Add `easyocr` or `pytesseract` to `requirements.txt`.
- Recommended: `easyocr` (handles Hindi/regional scripts better).

**8.2 — Create `backend/services/ocr.py`** (New File)
```python
import easyocr
from PIL import Image, ImageFilter
import io

reader = easyocr.Reader(['en', 'hi'], gpu=False)  # Singleton

def preprocess_image(image_bytes: bytes) -> bytes:
    # Convert to grayscale, apply contrast enhancement
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def extract_text_from_image(image_bytes: bytes) -> str:
    processed = preprocess_image(image_bytes)
    results = reader.readtext(processed, detail=0, paragraph=True)
    return " ".join(results).strip()
```

**8.3 — Add `/ocr/analyze` Endpoint** (`backend/api/routes.py`)
```python
@router.post("/ocr/analyze", response_model=ChatResponse, tags=["multimodal"])
async def analyze_screenshot(
    image: UploadFile = File(...),
    session_id: str = Form(...),
    user_id: str = Form(...),
    language: Optional[str] = Form(default="en-IN"),
    current_user: str = Depends(get_current_user),
):
    image_bytes = await image.read()
    extracted_text = extract_text_from_image(image_bytes)
    if not extracted_text:
        raise HTTPException(400, "Could not extract text from image")
    
    request = ChatRequest(
        session_id=session_id, user_id=user_id,
        message=extracted_text, language=language
    )
    return await run_pipeline(request)
```

**8.4 — Verification**
- Save 2 test images (a benign bank SMS screenshot, a phishing SMS screenshot) in `tests/fixtures/`.
- Write `tests/test_ocr.py` asserting correct text extraction and non-empty pipeline response.

---

### Phase 9: Multimodal Extension 3 — Call Recording Analysis & Scam Timeline
**Priority:** MEDIUM  
**Estimated Effort:** 2–3 days  
**Goal:** Transcribe phone recordings and produce a time-indexed social engineering scam timeline.

#### Tasks

**9.1 — Enhance `/voice/transcribe` for Long Audio** (`backend/api/routes.py`)
- Current endpoint handles short clips only.
- Add chunking logic: split audio longer than 60s into 30s overlapping segments using `pydub`.
- Add `audio/mpeg` (`.mp3`) and `audio/wav` (`.wav`) to accepted MIME types alongside `audio/webm`.
- Collect per-segment transcripts with timestamps and concatenate.

**9.2 — Create `backend/services/audio_pipeline.py`** (New File)
```python
from pydub import AudioSegment
import io

CHUNK_MS = 30_000   # 30 second chunks
OVERLAP_MS = 2_000  # 2 second overlap for context continuity

def chunk_audio(audio_bytes: bytes, mime_type: str) -> list[tuple[int, bytes]]:
    """Returns list of (start_ms, chunk_bytes) tuples."""
    ...

async def transcribe_long_audio(audio_bytes: bytes, mime_type: str, lang: str) -> list[dict]:
    """Returns list of {start_ms, end_ms, text} utterances."""
    ...
```

**9.3 — Create `backend/classification/timeline_builder.py`** (New File)
```python
SOCIAL_ENGINEERING_STAGES = {
    "impersonation":    ["police", "cbi", "rbi", "trai", "bank officer", "customs"],
    "urgency":          ["immediately", "arrest", "blocked", "suspend", "today only"],
    "credential_steal": ["otp", "pin", "password", "anydesk", "teamviewer", "cvv"],
    "payment_demand":   ["transfer", "send money", "upi", "pay", "fine", "penalty"],
}

@dataclass
class TimelineEvent:
    timestamp_ms: int
    stage: str           # e.g. "impersonation"
    matched_terms: list[str]
    utterance: str

def build_scam_timeline(utterances: list[dict]) -> list[TimelineEvent]:
    """Scan timestamped utterances for social engineering stages."""
    ...
```

**9.4 — Add `/voice/analyze-recording` Endpoint** (`backend/api/routes.py`)
```python
@router.post("/voice/analyze-recording", tags=["multimodal"])
async def analyze_call_recording(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    user_id: str = Form(...),
    language_hint: Optional[str] = Form(default=None),
): ...
# Returns: {transcript, timeline: [TimelineEvent], scam_analysis: ChatResponse}
```

**9.5 — Verification**
- Create a simulated call audio in `tests/fixtures/call_scam_sample.wav`.
- Assert timeline has at least one event with stage `"impersonation"` or `"urgency"`.

---

### Phase 10: Feedback Store & MLOps Automated Retraining Loop
**Priority:** HIGH — Required for academic MLOps component  
**Estimated Effort:** 2 days  
**Goal:** Collect user corrections and enable a versioned, gated retraining pipeline.

#### Tasks

**10.1 — Create `backend/mlops/feedback.py`** (New File)
```python
import sqlite3
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

DB_PATH = Path(__file__).parent.parent.parent / "data" / "feedback.db"

class FeedbackRecord(BaseModel):
    session_id: str
    input_type: str           # "text" | "ocr" | "voice"
    raw_content: str
    predicted_category: str
    confidence: float
    is_helpful: bool
    user_corrected_category: Optional[str] = None
    user_notes: Optional[str] = None

def init_db() -> None:
    """Create feedback table if not exists."""
    ...

def save_feedback(record: FeedbackRecord) -> None: ...
def get_feedback_for_retraining(min_records: int = 20) -> list[FeedbackRecord]: ...
```

**10.2 — Add `/feedback` Endpoint** (`backend/api/routes.py`)
```python
class FeedbackRequest(BaseModel):
    session_id: str
    is_helpful: bool
    user_corrected_category: Optional[str] = None
    user_notes: Optional[str] = None

@router.post("/feedback", tags=["mlops"])
async def submit_feedback(request: FeedbackRequest): ...
```

**10.3 — Create `mlops/retrain_pipeline.py`** (New File)
```python
# Steps:
# 1. Load verified feedback records from feedback.db
# 2. Filter: only records where user_corrected_category is not None (explicit corrections)
# 3. Merge with existing training CSV (data/splits/train.csv)
# 4. Retrain BOTH baseline and advanced models
# 5. EVALUATION GATE: evaluate candidate on frozen test.csv
#    - If candidate macro_f1 < (current_best_f1 - 0.005): REJECT
#    - Else: ACCEPT → overwrite models/*.joblib
# 6. Log experiment to MLflow: parameters, metrics, confusion matrix artifact
```

**10.4 — MLflow Experiment Tracking Setup**
- Add `mlflow` to requirements.
- In `retrain_pipeline.py`, wrap training in `with mlflow.start_run()`.
- Log: `n_training_samples`, `n_feedback_samples`, `accuracy`, `macro_f1`, `confusion_matrix.png`.

**10.5 — Verification**
- Insert 5 mock feedback records directly into `feedback.db`.
- Run `python mlops/retrain_pipeline.py`.
- Verify MLflow UI shows the experiment run.
- Verify evaluation gate logic by injecting a deliberately bad model.

---

### Phase 11: Academic Research Evaluation Suite & Ablation Studies
**Priority:** HIGH — Required for B.Tech project report  
**Estimated Effort:** 1–2 days  
**Goal:** Generate formal benchmark metrics, LaTeX tables, and ablation results for the thesis.

#### What Already Exists
- `evaluation/compare_classifiers.py` — Head-to-head classifier comparison with Markdown + LaTeX output
- `evaluation/baseline_metrics.json` & `evaluation/advanced_metrics.json` — Pre-computed metrics

#### Tasks

**11.1 — Create `evaluation/eval_rag.py`** (New File)
- Define 10 ground-truth (query, expected_passage_title) pairs for retrieval testing.
- Compute:
  - **Precision@3**: fraction of top-3 retrieved chunks that are relevant
  - **Citation Faithfulness**: manually verified that cited titles match actual docs
  - **Hallucination Reduction**: compare structured advisory output vs. a raw LLM call without RAG context

**11.2 — Create `evaluation/ablation_studies.py`** (New File)
Ablation configurations:
| Config | ML | RAG | LLM Grounding |
|---|---|---|---|
| Full System | ✅ | ✅ | ✅ |
| No RAG | ✅ | ❌ | ❌ |
| Rule-only | ❌ | ✅ | ✅ |
| Baseline ML only | TF-IDF | ✅ | ✅ |

- Run each config on 20 fixed test queries and compute response quality scores (manual + automated).
- Output `evaluation/results/ablation_table.md` and `ablation_table.tex`.

**11.3 — Create `evaluation/eval_classification.py`** (New File)
- Full confusion matrix across all 11 classes (10 scam + benign).
- Per-class Precision/Recall/F1 tables.
- Output `evaluation/results/classification_report.md` with embedded LaTeX table.

**11.4 — Verification**
- Run `python evaluation/eval_classification.py` — confirm output in `evaluation/results/`.
- Run `python evaluation/ablation_studies.py` — confirm 4-row ablation table generates.

---

### Phase 12: Full-Stack UI Polish, Final Demo & Viva Defense Kit
**Priority:** HIGH — Public-facing demo and examiner submission  
**Estimated Effort:** 3–4 days  
**Goal:** Responsive multi-tab UI with all modalities + examiner viva documentation.

#### What Already Exists
- `frontend/` — Next.js + Tailwind project with chat, voice pages and core components
- `frontend/components/chat/` — `ChatWindow`, `ChatInput`, `MessageBubble`
- `frontend/components/ui/` — `ScamBadge`, `SourceCitations`, `LanguageSelector`
- `frontend/components/voice/` — `VoiceOrb`
- `frontend/app/api/` — Next.js API routes for chat, memory, and voice

#### Tasks

**12.1 — Multi-Tab Input Dashboard** (`frontend/app/page.tsx`)
- Add 3 tabs: **Text / Message** | **Screenshot OCR** | **Call Recording**
- Text tab: current `ChatInput` component
- Screenshot tab: drag-and-drop image uploader → calls `/api/ocr/analyze`
- Call Recording tab: file upload `.wav`/`.mp3` → calls `/api/voice/analyze-recording`

**12.2 — Structured Advisory Display** (`frontend/components/chat/MessageBubble.tsx`)
- Parse the new `AdvisoryReport` JSON from `metadata.advisory_report`.
- Render structured sections:
  - 🔴/🟡/🟢 **Risk Badge** (from `risk_verdict`)
  - 🚩 **Detected Indicators** (chip list from `detected_indicators`)
  - 💬 **Why Suspicious** (expandable text with citation footnotes)
  - ✅ **Do's Checklist** (green bullet list from `do_list`)
  - ❌ **Don'ts Checklist** (red bullet list from `dont_list`)
  - 📄 **Official Sources** (expandable drawer from `citations`)

**12.3 — Language Toggle** (`frontend/components/ui/LanguageSelector.tsx`)
- Wire the existing `LanguageSelector` component to the `language` field in chat requests.
- On language change, re-send last message to get a translated advisory.

**12.4 — Scam Timeline Widget** (New: `frontend/components/voice/ScamTimeline.tsx`)
- Render a vertical timeline (using Tailwind CSS) showing each `TimelineEvent`:
  - Timestamp badge
  - Stage label (Impersonation / Urgency / Credential Steal / Payment Demand)
  - Matched terms chips
  - Utterance snippet

**12.5 — Feedback Widget** (`frontend/components/chat/MessageBubble.tsx`)
- Add thumbs up / thumbs down buttons below each AI response.
- On thumbs down: show a small form asking for the correct category (dropdown of 11 classes).
- Call `POST /feedback` with the collected data.

**12.6 — Create `docs/VIVA_DEFENSE_GUIDE.md`**
Structure:
- **5-Minute Demo Script** (5 distinct fraud scenarios with expected inputs and outputs)
- **Common Examiner Questions & Answers:**
  - *Where is the ML?* — Multi-class 11-category taxonomy, 99.84% accuracy, baseline vs. advanced ablation
  - *Where is the RAG?* — Qdrant + RBI/NPCI advisory retrieval, cosine threshold 0.65, multi-query rewriting
  - *Why LLM?* — Structured advisory generation, not raw classification; strictly grounded by retrieved passages
  - *Where is MLOps?* — Feedback store, evaluation gate, MLflow experiment tracking
  - *Why Bilingual?* — Sarvam AI STT/TTS, Hindi advisory generation, safety-term preservation
- **Architecture Diagram** (from `AGENTIC_IMPLEMENTATION_PLAN.md`)

**12.7 — Verification**
- Run full local demo: submit a phishing SMS in Hindi → verify Hindi structured advisory with risk badge and citations renders correctly.
- Upload a scam screenshot → verify OCR extracts text and advisory is displayed.
- Upload a 30s call recording → verify timeline widget renders.

---

## 📋 Execution Priority Summary

```
[Phase 3 ✅ DONE]
      │
      ├──► Phase 4 (RAG Provenance)    ← Start here — 1 day
      │
      ├──► Phase 5 (Structured Output) ← Depends on Phase 4 — 1 day
      │
      ├──► Phase 6 (Multilingual)      ← Depends on Phase 5 — 1-2 days (Sarvam already coded)
      │
      ├──► Phase 7 (URL Analyzer)      ← Independent, can be done in parallel — 1 day
      │
      ├──► Phase 8 (OCR)               ← Independent — 1-2 days
      │
      ├──► Phase 9 (Call Recording)    ← Depends on Phase 8 — 2-3 days
      │
      ├──► Phase 10 (Feedback + MLOps) ← Independent — 2 days
      │
      ├──► Phase 11 (Evaluation Suite) ← Depends on Phases 4,5 — 1-2 days
      │
      └──► Phase 12 (UI + Viva Kit)    ← Depends on ALL — 3-4 days
```

**Total Estimated Remaining Effort: ~14–19 days** (sequential) or ~10–12 days (with parallel execution of independent phases).

---

## 🗂️ New Files to Create (Summary)

| File | Phase |
|---|---|
| `backend/services/multilingual.py` | 6 |
| `backend/classification/url_analyzer.py` | 7 |
| `backend/services/ocr.py` | 8 |
| `backend/services/audio_pipeline.py` | 9 |
| `backend/classification/timeline_builder.py` | 9 |
| `backend/mlops/__init__.py` | 10 |
| `backend/mlops/feedback.py` | 10 |
| `mlops/retrain_pipeline.py` | 10 |
| `evaluation/eval_rag.py` | 11 |
| `evaluation/eval_classification.py` | 11 |
| `evaluation/ablation_studies.py` | 11 |
| `evaluation/results/` (directory) | 11 |
| `frontend/components/voice/ScamTimeline.tsx` | 12 |
| `docs/VIVA_DEFENSE_GUIDE.md` | 12 |
| `tests/test_rag_retrieval.py` | 4 |
| `tests/test_url_analyzer.py` | 7 |
| `tests/test_ocr.py` | 8 |
| `tests/fixtures/` (directory with test images/audio) | 8, 9 |

## 🔧 Existing Files to Modify (Summary)

| File | Phase | Change |
|---|---|---|
| `ingestion/chunker.py` | 4 | Add `document_id`, `authority`, `source_url`, `section_title`, `effective_date` to chunk metadata |
| `backend/rag/engine.py` | 4, 5 | Add cosine threshold, inject scam category into query rewrite, parse `AdvisoryReport` |
| `backend/rag/prompts.py` | 4, 5 | Add scam category to query rewrite prompt; rewrite answer prompt for structured JSON output |
| `backend/core/models.py` | 5 | Add `AdvisoryReport`, `RiskVerdict` Pydantic models |
| `backend/api/pipeline.py` | 6 | Add multilingual pre/post-processing nodes to LangGraph |
| `backend/classification/classifier.py` | 7 | Integrate URL analysis into `_extract_indicators()` |
| `backend/api/routes.py` | 7, 8, 9, 10 | Add `/url/analyze`, `/ocr/analyze`, `/voice/analyze-recording`, `/feedback` endpoints |
| `frontend/app/page.tsx` | 12 | Add multi-tab input layout |
| `frontend/components/chat/MessageBubble.tsx` | 12 | Render structured `AdvisoryReport` sections + feedback widget |
