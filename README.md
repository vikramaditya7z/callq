# AI Earnings Call Analyzer

AI Earnings Call Analyzer is a portfolio-quality full-stack application that
turns earnings call transcripts into structured investor insights.

Version 1 focuses on a single-document workflow: a user pastes an earnings call
transcript, the FastAPI backend sends a structured prompt to Gemini, and the
React frontend displays the resulting analysis.

## Motivation

Earnings calls contain useful information, but they are long, dense, and hard to
scan quickly. This project demonstrates how an AI application can convert raw
financial text into a consistent research format while preserving clean software
architecture, validation, and deployment readiness.

## Features

- Paste an earnings call transcript into a clean React interface.
- Analyze the transcript with a FastAPI backend.
- Use Gemini structured output for AI-generated analysis.
- Validate AI output with Pydantic before returning it to the frontend.
- Display seven Version 1 analysis sections:
  - Executive Summary
  - Positives
  - Negatives
  - Risks
  - Opportunities
  - Management Outlook
  - Themes
- Show loading, error, retry, and empty-result states in the frontend.

## Tech Stack

Frontend:

- React
- TypeScript
- Vite
- CSS

Backend:

- Python
- FastAPI
- Pydantic
- Uvicorn

AI:

- Gemini GenerateContent REST API

Deployment targets:

- Vercel for the frontend
- Render for the backend

## High-Level Architecture

```text
React frontend
  |
  | POST /analyze
  v
FastAPI backend
  |
  v
Analysis service
  |
  v
Prompt builder
  |
  v
Gemini service
  |
  v
Pydantic response validation
  |
  v
Structured JSON response
```

## Folder Structure

```text
.
|-- ARCHITECTURE.md
|-- PROJECT_RULES.md
|-- README.md
|-- requirements.txt
|-- backend/
|   |-- api/
|   |   |-- analysis.py
|   |   `-- health.py
|   |-- models/
|   |   `-- analysis.py
|   |-- prompts/
|   |   `-- analysis_prompt.py
|   |-- services/
|   |   |-- analysis_service.py
|   |   |-- gemini_schemas.py
|   |   `-- gemini_service.py
|   |-- utils/
|   `-- main.py
`-- frontend/
    |-- index.html
    |-- package.json
    |-- src/
    |   |-- components/
    |   |-- services/
    |   |-- types/
    |   |-- App.tsx
    |   |-- main.tsx
    |   `-- styles.css
    `-- vite.config.ts
```

## Backend Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your Gemini API key.

Load environment variables:

```bash
set -a
source .env
set +a
```

Run the backend:

```bash
uvicorn backend.main:app --reload
```

The backend runs locally at:

```text
http://127.0.0.1:8000
```

## Frontend Setup

From the frontend folder:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs locally at:

```text
http://127.0.0.1:5173
```

During local development, Vite proxies `/api` requests to the FastAPI backend at
`http://127.0.0.1:8000`.

## Environment Variables

The example environment file is [.env.example](.env.example).

Backend variables:

- `GEMINI_API_KEY`: required Gemini API key.
- `GEMINI_MODEL`: optional Gemini model name. The backend defaults to
  `gemini-3.5-flash`.
- `CORS_ORIGINS`: comma-separated frontend origins allowed to call the backend.
  Use the Vercel frontend URL in production.

Frontend variables:

- `VITE_API_BASE_URL`: production backend URL used by the Vercel frontend.

Never commit a real `.env` file or API key.

## Local Development

Use two terminals.

Terminal 1: backend

```bash
source .venv/bin/activate
set -a
source .env
set +a
uvicorn backend.main:app --reload
```

Terminal 2: frontend

```bash
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## API Endpoints

### GET /health

Checks that the backend is running.

Example:

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{"status":"ok"}
```

### POST /analyze

Analyzes one earnings call transcript.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Operator: Welcome to the quarterly earnings call. Management discussed revenue growth, margin pressure, cost discipline, product demand, customer adoption, operational efficiency, macroeconomic uncertainty, and future guidance. The leadership team explained that demand remains resilient in key markets while costs and foreign exchange remain areas to monitor. They also described new product opportunities and a cautious but constructive outlook for the next quarter."
  }'
```

Example response:

```json
{
  "executive_summary": [
    "Management discussed revenue growth, operating discipline, and market uncertainty."
  ],
  "positives": [
    "Demand remained resilient in key markets."
  ],
  "negatives": [
    "Management referenced margin pressure from costs and foreign exchange."
  ],
  "risks": [
    "Macroeconomic uncertainty may affect near-term performance."
  ],
  "opportunities": [
    "New product initiatives may support future growth."
  ],
  "management_outlook": "Management sounded cautiously constructive while acknowledging external uncertainty.",
  "themes": [
    "Revenue growth",
    "Margin pressure",
    "Cost discipline",
    "Market uncertainty"
  ]
}
```

Actual output depends on the transcript and Gemini response, but it must match
the Version 1 schema.

## Deployment

### Frontend: Vercel

Recommended settings:

- Root directory: `frontend`
- Install command: `npm install`
- Build command: `npm run build`
- Output directory: `dist`

Required Vercel environment variable:

- `VITE_API_BASE_URL`: deployed Render backend URL, for example
  `https://your-backend.onrender.com`

### Backend: Render

Recommended settings:

- Root directory: project root
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

Required Render environment variables:

- `GEMINI_API_KEY`
- `CORS_ORIGINS`

Optional Render environment variables:

- `GEMINI_MODEL`

## Screenshots

Screenshots will be added after deployment.

## Future Roadmap

Version 2:

- Sentiment analysis
- Theme analysis
- Confidence indicators
- Keyword analysis

Version 3:

- Quarter-over-quarter comparison
- Theme evolution
- Risk changes
- Tone comparison

Version 4:

- Cross-company analysis
- Competitive analysis
- Comparative insights

Version 5:

- Multi-document research assistant
- Investment thesis generation
- Bull case and bear case
- Full research reports

## Final Review Notes

Architectural strengths:

- Clear route, service, prompt, model, and provider boundaries.
- Pydantic validation protects the frontend from malformed AI output.
- Gemini-specific details are isolated in a dedicated service.
- Frontend state is simple and owned by `App`.
- The project avoids Version 1 overengineering such as auth, databases, vector
  stores, RAG, and state management libraries.

Remaining weaknesses:

- The backend does not yet include automated tests.
- Error logging should eventually use structured logging.
- The frontend currently depends on a single backend URL.
- Long transcript handling is limited by request size and model context.

These are future improvements and are intentionally not implemented in Version 1.

## License

MIT License.
