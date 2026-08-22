# CallQ

> AI-powered financial research platform that transforms earnings call transcripts into structured investor intelligence.

CallQ helps investors, analysts, and researchers quickly digest complex earnings call commentary. By parsing raw transcripts, CallQ surfaces key takeaways, extracts historical financial metrics and future guidance, and identifies qualitative management signals.

**Live Demo**  
https://callq-nine.vercel.app

---

## Current V1.5 Capabilities

CallQ currently analyzes a single earnings call transcript per request, providing a structured, multidimensional dashboard:

* **Executive Summary**: High-level key takeaways and core business performance.
* **Themes**: Major recurring subjects and focus areas during the call.
* **Positives & Negatives**: Balanced extraction of positive developments and operational headwinds.
* **Risks & Opportunities**: Stated or implied operational, financial, and strategic risks alongside future growth vectors.
* **Management Outlook**: A consolidated summary of the executive team's forward-looking guidance and tone.
* **Financial Metrics**: Explicitly reported historical numbers (e.g., revenue, gross margins, cash flow, growth rates) with their comparative periods and year-over-year changes.
* **Management Guidance**: Explicit forward-looking management targets, ranges, periods, and context.
* **Management Signals**: Qualitative mapping of overall management tone, positive signals, and watch signals.

---

## Tech Stack

* **Frontend**: React (v18) + TypeScript + Vite
* **Backend**: FastAPI + Python (v3.9+) + Pydantic (v2)
* **AI Engine**: Google Gemini API (Structured Output Mode)
* **Deployment**: Vercel (Frontend) + Render (Backend)

---

## Architecture Overview

```text
React/TypeScript Frontend
          │
          ▼
    POST /analyze
          │
          ▼
    FastAPI Route
          │
          ▼
   Analysis Service
          │
          ▼
     Gemini API (Structured Output)
          │
          ▼
   Pydantic Validation (EarningsAnalysisResponse)
          │
          ▼
React Component Rendering (V1.5 Insights)
```

---

## Local Setup

### 1. Backend Setup

From the root directory:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY

# Load env variables and start backend
set -a
source .env
set +a
uvicorn backend.main:app --reload
```

The backend server runs locally at `http://127.0.0.1:8000`.

### 2. Frontend Setup

From the `frontend` directory:

```bash
npm install
npm run dev
```

The frontend server runs locally at `http://localhost:5173`.

---

## Current Status

* **Release Version**: V1.5 (Released)
* **Scope**: Analysis of a single raw transcript submission.
* **Error Handling**: Controlled API mappings returning 502/500 errors to avoid raw application failures.

---

## Future Roadmap

The following iterations represent future plans and are not yet active in the current V1.5 release:

* **V2: AI Investment Analyst** — Deep investor interpretation, valuation checks, and context-aware financial reasoning.
* **V3: Company Intelligence** — Multi-quarter comparative dashboards and historical trending across multiple earnings calls.
* **V4: Multi-Source Intelligence** — Integration of SEC filings (10-K, 10-Q) and investor slide decks alongside transcripts.
* **V5: Continuous Intelligence & Alerts** — Automated monitoring of company updates, news feeds, and social sentiment with customized notifications.
* **V6: AI Investment Research Advisor** — Multi-company benchmarking, industry sector analysis, and conversational portfolio assistants.

---

## License

MIT
