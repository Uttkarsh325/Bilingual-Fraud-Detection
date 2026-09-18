# FraudGuard AI — Multilingual Financial Fraud & Scam-Pattern Advisory System

A production-grade, multilingual conversational AI that helps users identify and understand
financial scams and fraudulent messages through **text and voice**, in Hindi, English, and
other Indian languages.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Next.js Web App (port 3000)             │
│         Chat UI  +  Voice-Call UI  +  API Routes         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│            FastAPI Orchestration Service (port 8000)     │
│                                                          │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │  Sarvam AI  │  │ LangGraph  │  │   mem0 Memory    │  │
│  │  STT / TTS  │  │  Pipeline  │  │   Layer          │  │
│  └─────────────┘  └─────┬──────┘  └──────────────────┘  │
│                         │                                │
│              ┌──────────▼──────────┐                     │
│              │  Intent-Aware RAG   │                     │
│              │  Engine             │                     │
│              │  (query rewriting   │                     │
│              │   + re-ranking)     │                     │
│              └──────────┬──────────┘                     │
│                         │                                │
│   ┌─────────────────────▼────────┐  ┌────────────────┐  │
│   │    Qdrant Vector Store       │  │  Scam Classify │  │
│   │  (RBI/NPCI advisories,       │  │  Module        │  │
│   │   cybercrime FAQs, patterns) │  └────────────────┘  │
│   └──────────────────────────────┘                      │
│                                                          │
│   ┌──────────────────────────────┐                      │
│   │  Open-Source LLM             │                      │
│   │  (GPT-OSS-20B / Qwen via     │                      │
│   │   Groq or local Ollama)      │                      │
│   └──────────────────────────────┘                      │
│                                                          │
│   ┌──────────────────────────────┐                      │
│   │  AWS S3 Storage              │                      │
│   │  (docs, audio, embeddings)   │                      │
│   └──────────────────────────────┘                      │
└──────────────────────────────────────────────────────────┘
```

---

## Quick Start (Local Dev)

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- A [Sarvam AI API key](https://sarvam.ai)
- A [Groq API key](https://groq.com) **or** Ollama running locally

### 1. Clone & configure
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Start Qdrant
```bash
docker compose up qdrant -d
```

### 3. Ingest advisory documents
```bash
cd ingestion
pip install -r requirements.txt
python ingest.py --source ../docs/advisories
```

### 4. Start the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Project Structure

```
.
├── frontend/           # Next.js 14 (App Router) web application
│   ├── app/            # Pages, layouts, API routes
│   ├── components/     # Chat, Voice, UI components
│   └── lib/            # API client, hooks, types
│
├── backend/            # FastAPI orchestration service
│   ├── api/            # Route handlers
│   ├── core/           # Config, auth, logging
│   ├── services/       # Sarvam AI, LLM, S3, mem0
│   ├── rag/            # Intent-aware RAG engine
│   ├── memory/         # mem0 memory layer
│   └── classification/ # Scam taxonomy classifier
│
├── ingestion/          # Data ingestion pipeline
│   ├── ingest.py       # Main ingestion script
│   ├── chunker.py      # Document chunking
│   ├── embedder.py     # Embedding + Qdrant upsert
│   └── s3_uploader.py  # Upload raw docs to S3
│
├── docs/
│   └── advisories/     # Place RBI/NPCI PDF advisories here
│
├── docker-compose.yml
└── .env.example
```

---

## Modules

| Module | Description |
|--------|-------------|
| **Sarvam AI** | Multilingual STT, TTS, Indic text understanding |
| **Intent-Aware RAG** | Query rewriting → intent classification → multi-stage retrieval → re-ranking |
| **Qdrant** | Vector store for RBI/NPCI advisories and scam patterns |
| **mem0** | Persistent per-user memory: language preference, prior incidents, session history |
| **Scam Classifier** | Maps message/intent to scam taxonomy with confidence score |
| **LLM** | Open-source instruct model (Llama 3.1 / Mistral) for grounded, cited answers |
| **AWS S3** | Cloud storage for source docs, audio artifacts, embedding backups |

---

## Scam Taxonomy

| Category | Examples |
|----------|---------|
| `upi_collect_scam` | Fake collect requests, QR code scams |
| `phishing_link` | Fake refund/KYC/reward links |
| `voice_phishing` | Impersonating bank officials, TRAI warnings |
| `lottery_prize` | Fake prize/lottery notifications |
| `job_offer_scam` | Fake work-from-home / part-time job offers |
| `loan_scam` | Fake instant loan apps |
| `sim_swap` | SIM card swap fraud |
| `investment_scam` | Ponzi / crypto investment fraud |
| `otp_scam` | Social engineering to extract OTP |
| `unknown` | Unclassified / needs review |

---

## Evaluation Metrics

- Intent classification accuracy
- Retrieval groundedness (answers traceable to cited advisory)
- Voice interaction latency & transcription accuracy (WER)
- Multi-turn conversation quality improvement with memory vs. stateless baseline

---

## Team

| Name | Enrollment No. |
|------|---------------|
| Uttkarsh Thakur | 9923103196 |
| Ayush Singh | 9923103193 |

**Supervisor:** Mr. Twinkle Tyagi  
**Institution:** Jaypee Institute of Information Technology, Noida (Sector 128)  
**Program:** B.Tech CSE — 4th Year, 7th Semester (2026-2027)
