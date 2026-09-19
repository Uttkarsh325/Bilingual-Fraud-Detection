# FraudGuard AI — Master Stepwise Agentic Development Plan
**Capstone Project:** Multilingual Financial Fraud & Scam-Pattern Advisory System  
**Academic Context:** B.Tech. CSE (Major Project - 1 / 7th Semester)  
**Document Purpose:** Master execution roadmap for agentic development, tracking completed phases (0, 1, 2) and defining stepwise milestones for subsequent phases (3 to 12).

---

## 1. System Architecture & Project Blueprint

```
                          MULTIMODAL USER INPUT
               +----------------+-------------+----------------+
               |                |             |                |
             TEXT           SCREENSHOT       URL         CALL RECORDING
               |                |             |                |
               |             [ OCR ]    [ URL ANALYZER ]    [ STT ]
               +----------------+-------------+----------------+
                                        |
                                        v
                          [ PREPROCESSING & NORMALIZATION ]
                                        |
                                        v
                            [ ML SCAM CLASSIFIER ]
                        (Baseline TF-IDF vs. Transformer)
                                        |
                            +-----------+-----------+
                            |                       |
                     Category & Score       Scam Indicators
                            |                       |
                            +-----------+-----------+
                                        |
                                        v
                            [ INTENT-AWARE RAG ]
                       (Curated RBI / NPCI / 1930 DB)
                                        |
                                        v
                          [ GROUNDED LLM EXPLANATION ]
                         (Strict Citation & Guardrails)
                                        |
                                        v
                          [ MULTILINGUAL DELIVERY ]
                         (English, Hindi, +1 Regional)
                                        |
                                        v
                             [ USER INTERFACE ]
                                        |
                                        v
                           [ FEEDBACK STORE & MLOPS ]
                        (SQLite + MLflow Retraining Gate)
```

---

## 2. Status of Completed Foundation (Phases 0, 1, and 2)

The foundational scaffolding of the project has been established as follows:

| Phase | Description | Key Modules / Files | Current Status |
|---|---|---|---|
| **Phase 0: Architecture & Contracts** | Core project structure, FastAPI application setup, Next.js UI boilerplate, Pydantic contracts, and Scam Taxonomy definitions. | `backend/core/models.py`<br>`backend/classification/taxonomy.py`<br>`backend/main.py`<br>`docker-compose.yml` | **COMPLETED** |
| **Phase 1: Knowledge Ingestion & Advisories** | Curated official regulatory advisories from RBI, NPCI, and National Cybercrime Reporting Portal. Ingestion chunker and embedder scripts. | `docs/advisories/*.txt`<br>`ingestion/chunker.py`<br>`ingestion/embedder.py`<br>`ingestion/ingest.py` | **COMPLETED** |
| **Phase 2: Baseline Classification & Graph Pipeline** | Keyword-based rule classifier, zero-shot NLI classifier fallback, LangGraph multi-node state graph (`memory_recall` $\to$ `classify` $\to$ `rag` $\to$ `memory_store`), and chat/voice routing. | `backend/classification/classifier.py`<br>`backend/api/pipeline.py`<br>`backend/api/routes.py`<br>`backend/memory/mem0_layer.py` | **COMPLETED** |

---

## 3. Stepwise Agentic Development Roadmap (Phase 3 through Phase 12)

Each subsequent phase is designed as an independent, testable milestone suitable for agentic code generation, automated testing, and verification.

---

### Phase 3: Trainable Baseline & Advanced ML Classifier
**Goal:** Deliver reproducible ML models trained on labeled fraud/benign datasets with side-by-side performance benchmarks (Academic requirement).

#### 3.1 Dataset Split & Taxonomy Alignment
- **Path:** `data/raw/`, `data/processed/`, `data/taxonomy.csv`
- **Actions:**
  - Create `data/taxonomy.csv` detailing the 10 scam classes + `benign`.
  - Assemble synthetic & curated real-world SMS/WhatsApp scam datasets with benign samples.
  - Implement `scripts/prepare_dataset.py` with stratified 70/15/15 train/val/test splits and deduplication.

#### 3.2 Baseline Classifier (TF-IDF + Linear Model)
- **Path:** `training/train_baseline.py`
- **Actions:**
  - Build Scikit-learn pipeline: Character + Word TF-IDF n-grams (`ngram_range=(1, 3)`).
  - Train Logistic Regression with balanced class weights / LinearSVC.
  - Export model to `models/baseline_tfidf.joblib`.
  - Compute Baseline metrics: Macro F1, Precision, Recall, and Confusion Matrix.

#### 3.3 Advanced Classifier (Transformer / Sentence-Transformers)
- **Path:** `training/train_advanced.py`
- **Actions:**
  - Train an embedding classifier using `sentence-transformers` (`all-MiniLM-L6-v2` or `paraphrase-multilingual-mpnet-base-v2`) with a PyTorch classification head.
  - Export model weights and tokenizer to `models/advanced_classifier/`.
- **Inference Integration:** Update `backend/classification/classifier.py` to load the advanced model with graceful fallback to baseline TF-IDF and keyword matching.

#### 3.4 Verification & Milestones
- Run `python -m training.train_baseline` and `python -m training.train_advanced`.
- Verify inference latency $< 100\text{ms}$ on CPU and generation of classification report.

---

### Phase 4: Production Grounded RAG & Provenance Layer
**Goal:** Ensure the RAG engine retrieves high-relevance regulatory passages and preserves strict provenance.

#### 4.1 Document Metadata & Provenance Enhancement
- **Path:** `ingestion/chunker.py`, `backend/rag/vector_store.py`
- **Actions:**
  - Add explicit provenance attributes to every chunk: `document_id`, `authority` (RBI, NPCI, MHA Cybercrime), `source_url`, `section_title`, and `effective_date`.
  - Support both Qdrant and local in-memory/FAISS fallback for offline testing without Docker.

#### 4.2 Query Reformulation & Relevance Scoring
- **Path:** `backend/rag/engine.py`
- **Actions:**
  - Inject the predicted scam category into query rewriting (e.g. converting *"got msg to update kyc or acc blocked"* $\to$ *"RBI customer liability guidelines for unauthorized electronic banking fake KYC"*).
  - Apply cosine similarity thresholds ($\ge 0.65$) to discard irrelevant chunks.

#### 4.3 Verification & Milestones
- Test retrieval on 5 representative queries: verify top-3 chunks are retrieved with accurate provenance citations.

---

### Phase 5: Anti-Hallucination Grounded Prompting & Advisory Output
**Goal:** Generate structured, plain-language advisory reports strictly bounded by retrieved evidence.

#### 5.1 Strict Evidence-First Prompt Engineering
- **Path:** `backend/rag/prompts.py`
- **Actions:**
  - Construct prompt with system guardrails:
    - User message/transcript.
    - Model classification category and confidence score.
    - Retrieved regulatory passages.
  - Require structured JSON / clear Markdown output sections:
    1. **Summary & Risk Verdict** (Low / Medium / High).
    2. **Detected Scam Indicators** (e.g., Urgency, Credential Demand, Suspicious Link).
    3. **Why It Is Suspicious** (Directly citing RBI/NPCI directives).
    4. **Actionable Checklist**:
       - What to do immediately (Call 1930, block card, notify bank within 72 hours under RBI zero-liability policy).
       - What NOT to do (Never enter UPI PIN to receive money, never share OTP).
    5. **Verified Citations** (Document name, section, source link).

#### 5.2 Verification & Milestones
- Execute mock queries; confirm zero unsupported legal claims and accurate emergency helpline citations (1930).

---

### Phase 6: Multilingual Advisory Engine (Hindi & Regional Delivery)
**Goal:** Deliver accessible fraud advisory in Hindi and an additional regional Indian language (Tamil/Bengali).

#### 6.1 Translation & Multilingual Generation
- **Path:** `backend/services/multilingual.py`
- **Actions:**
  - Implement translation pipeline using Sarvam AI Indic translation endpoint or open-source NLLB/IndicTrans2.
  - Implement bilingual generation mode: produce the advisory directly in Hindi/regional language while preserving safety-critical terms in English/Hinglish (e.g., "UPI PIN", "OTP", "1930 Helpline", "Bank Account").

#### 6.2 Verification & Milestones
- Verify Hindi advisory generation for a KYC scam message; validate clarity of precautions.

---

### Phase 7: Multimodal Extension 1 — Suspicious URL & Passive Domain Analyzer
**Goal:** Detect malicious phishing links and deceptive domains before passing into text analysis.

#### 7.1 Passive URL Feature Extractor
- **Path:** `backend/classification/url_analyzer.py`
- **Actions:**
  - Extract and inspect URLs without making network requests to dangerous hosts.
  - Detect heuristic indicators:
    - IP address used as hostname (e.g. `http://192.168.1.1/sbi`).
    - Brand impersonation (e.g. `sbi-kyc-update.com`, `paytm-refund-portal.in`).
    - Excessive subdomains or punycode/homoglyph characters.
    - Known shortening services (`bit.ly`, `tinyurl.com`, `is.gd`).
    - Suspicious top-level domains (`.xyz`, `.top`, `.tk`, `.club`).
  - Return `URLAnalysisResult` with detected risk signals.

#### 7.2 Verification & Milestones
- Run unit tests with benign URLs (`sbi.co.in`, `npci.org.in`) and phishing samples (`http://bit.ly/sbi-kyc-alert`).

---

### Phase 8: Multimodal Extension 2 — Screenshot OCR Pipeline
**Goal:** Extract text from screenshots of SMS, WhatsApp chats, and UPI payment requests.

#### 8.1 OCR Processing Service
- **Path:** `backend/services/ocr.py`, `backend/api/routes.py`
- **Actions:**
  - Implement `/ocr/analyze` endpoint accepting image uploads (`.png`, `.jpg`, `.jpeg`).
  - Use Tesseract OCR / easyOCR / Vision API with contrast preprocessing and grayscale conversion.
  - Feed extracted text directly into the classification and RAG pipeline.

#### 8.2 Verification & Milestones
- Test with sample screenshot images of scam SMS and verify accurate text extraction.

---

### Phase 9: Multimodal Extension 3 — Call-Recording Fraud Analysis & Timeline
**Goal:** Transcribe phone call recordings and build a time-indexed social engineering scam timeline.

#### 9.1 Audio Transcription & Timestamp Extraction
- **Path:** `backend/services/audio_pipeline.py`, `backend/api/routes.py`
- **Actions:**
  - Enhance `/voice/transcribe` to support longer audio recordings (`.wav`, `.mp3`).
  - Extract timestamped utterances using Sarvam STT / Whisper.

#### 9.2 Scam Indicator Timeline Builder
- **Path:** `backend/classification/timeline_builder.py`
- **Actions:**
  - Analyze utterances across time for progressive social engineering tactics:
    - `00:30` Impersonation (Claiming to be police / bank / telecom authority).
    - `01:15` Artificial Urgency (Threatening immediate account block or arrest).
    - `02:00` Action Request (Demanding OTP, payment, or remote software like AnyDesk).
  - Output structured scam timeline for visualization in the UI.

#### 9.3 Verification & Milestones
- Test with simulated call audio snippet and verify timeline output generation.

---

### Phase 10: Feedback Store & MLOps Automated Retraining Loop
**Goal:** Collect user corrections and enable a versioned, controlled retraining and re-indexing pipeline.

#### 10.1 Feedback Store
- **Path:** `backend/mlops/feedback.py`, `backend/api/routes.py`
- **Actions:**
  - Create SQLite / PostgreSQL feedback database table:
    - `session_id`, `input_type`, `raw_content`, `predicted_category`, `confidence`, `is_helpful`, `user_corrected_category`, `user_notes`, `created_at`.
  - Expose `/feedback` endpoint.

#### 10.2 Continuous Improvement Pipeline
- **Path:** `mlops/retrain_pipeline.py`
- **Actions:**
  - Script to extract verified feedback data and merge with versioned training dataset.
  - Retrain baseline & advanced classifiers.
  - **Evaluation Gate:** Validate retrained candidate model against frozen benchmark test set; reject deployment if F1 degrades.
  - Log experiments, parameters, and confusion matrix artifacts to MLflow.

#### 10.3 Verification & Milestones
- Submit mock feedback, run retraining script, and confirm evaluation gating logic.

---

### Phase 11: Academic Research Evaluation Suite & Ablation Studies
**Goal:** Generate formal benchmark metrics, confusion matrices, and ablation tables for the B.Tech project report.

#### 11.1 Benchmark Scripts
- **Path:** `evaluation/eval_classification.py`, `evaluation/eval_rag.py`, `evaluation/ablation_studies.py`
- **Actions:**
  - **Classifier Evaluation:** Compute Accuracy, Precision, Recall, Macro-F1 across all 10 taxonomy categories.
  - **RAG Groundedness Evaluation:** Measure citation faithfulness, retrieval precision@k, and hallucination reduction vs. ungrounded baseline LLM.
  - **Ablation Studies:**
    1. Full System (ML + RAG + LLM).
    2. Without RAG (Pure LLM hallucination analysis).
    3. Baseline ML (TF-IDF) vs. Advanced Transformer Classifier.
    4. Rule-based only vs. ML Classifier.
  - Output LaTeX tables and markdown reports for the final thesis.

#### 11.2 Verification & Milestones
- Execute full evaluation suite and verify markdown summary output in `evaluation/results/`.

---

### Phase 12: Full-Stack UI Polish, Final Demo & Viva Defense Kit
**Goal:** Deliver a responsive web application and examiner defense documentation.

#### 12.1 UI Multimodal Dashboard
- **Path:** `frontend/components/`, `frontend/app/`
- **Actions:**
  - Multi-tab input: **Text / Message**, **Screenshot OCR**, **Call Recording Audio**.
  - Visual output display: Risk Badge, Confidence Gauge, Scam Indicator chips, Plain-Language Explanation, Do's & Don'ts Checklist, Official Sources drawer.
  - Language toggle (English / Hindi / Regional).
  - Audio Call Scam Timeline widget.
  - Feedback action ("Helpful? Thumbs Up / Thumbs Down + Suggest Correction").

#### 12.2 Viva Defense Kit & Demo Script
- **Path:** `docs/VIVA_DEFENSE_GUIDE.md`
- **Actions:**
  - Document core examiner viva answers:
    - *Where is ML?* (Multi-class taxonomy classification + confidence scoring).
    - *Where is RAG?* (Curated RBI/NPCI/Cybercrime knowledge retrieval to prevent hallucination).
    - *Why an LLM?* (Natural language synthesis and contextual translation, not raw classification).
    - *Why MLOps?* (Adapting to evolving scam patterns via controlled retraining and validation gates).
  - Step-by-step 5-minute presentation script demonstrating 5 distinct fraud patterns.

---

## 4. Execution Sequence Summary

```
[Phase 0, 1, 2] -> Already Completed (Foundation & Baseline Scaffolding)
      │
      ├──> Step 1: Execute Phase 3 (Trainable Baseline & Advanced ML Models + Dataset Splits)
      │
      ├──> Step 2: Execute Phase 4 & 5 (Production RAG & Strict Anti-Hallucination Prompts)
      │
      ├──> Step 3: Execute Phase 6 (Multilingual Hindi/Regional Delivery)
      │
      ├──> Step 4: Execute Phase 7 & 8 (URL Analyzer & Screenshot OCR)
      │
      ├──> Step 5: Execute Phase 9 (Call Recording STT & Interactive Scam Timeline)
      │
      ├──> Step 6: Execute Phase 10 (Feedback Store & MLflow Retraining Loop)
      │
      ├──> Step 7: Execute Phase 11 (Evaluation Suite & Ablation Studies for Project Report)
      │
      └──> Step 8: Execute Phase 12 (Frontend UI Polish & Viva Defense Kit)
```
