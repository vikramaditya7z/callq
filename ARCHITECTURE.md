# CallQ Architecture

## Current Release

CallQ V1.5 is a single-transcript earnings-call analysis application. It
turns one raw earnings-call transcript into a structured investor-insight
response. It does not use a database, authentication, market-data APIs,
multi-document analysis, or persistent user data.

## Request Flow

```text
Transcript input
  -> React + TypeScript frontend
  -> POST /analyze
  -> FastAPI analysis route
  -> analysis service and V1 prompt
  -> Gemini structured-output API
  -> Gemini response schema + Pydantic validation
  -> JSON API response
  -> V1 insight grid + V1.5 insight components
```

The frontend calls `/api/analyze` by default. During local development, Vite
proxies `/api` to FastAPI at `http://127.0.0.1:8000`; deployments can supply
`VITE_API_BASE_URL`.

## Backend

- `backend/main.py` creates the FastAPI application, configures CORS from
  `CORS_ORIGINS`, and registers the health and analysis routers.
- `backend/api/health.py` exposes `GET /health`, returning `{"status":"ok"}`.
- `backend/api/analysis.py` exposes `POST /analyze`. It validates the request,
  delegates analysis to the service layer, and maps missing AI configuration to
  HTTP 500 and provider/validation failures to HTTP 502.
- `backend/services/analysis_service.py` builds the V1 analysis prompt, calls
  Gemini, and validates the returned object as `EarningsAnalysisResponse`.
- `backend/services/gemini_service.py` sends the prompt and JSON schema to the
  Gemini `generateContent` endpoint using `GEMINI_API_KEY` and `GEMINI_MODEL`.
- `backend/prompts/analysis_prompt.py` contains the V1.5 structured-output
  instructions.
- `backend/models/analysis.py` contains the request and response Pydantic
  models. `backend/services/gemini_schemas.py` supplies the matching Gemini
  response schema.

### Request Contract

`POST /analyze` accepts a JSON object with one field:

```json
{
  "transcript": "Raw earnings-call transcript text"
}
```

The transcript is trimmed, must contain readable text, and must be between
200 and 100,000 characters. Additional request fields are rejected.

### V1.5 Response Contract

`POST /analyze` returns the following required top-level fields. Additional
response fields are not permitted.

```json
{
  "executive_summary": ["string"],
  "positives": ["string"],
  "negatives": ["string"],
  "risks": ["string"],
  "opportunities": ["string"],
  "management_outlook": "string",
  "themes": ["string"],
  "financial_metrics": [
    {
      "name": "string",
      "value": "string",
      "change": "string or null",
      "period": "string or null"
    }
  ],
  "guidance": [
    {
      "metric": "string",
      "value": "string",
      "period": "string",
      "context": "string or null"
    }
  ],
  "management_signals": {
    "overall_tone": "string",
    "positive_signals": ["string"],
    "watch_signals": ["string"]
  }
}
```

The seven original insight fields each require at least one non-blank string.
`financial_metrics` and `guidance` may be empty when the transcript contains
no supported items. Management signal lists may be empty, but the
`management_signals` object is always present.

## Frontend

- `frontend/src/App.tsx` owns transcript, loading, result, and error state.
- `frontend/src/services/api.ts` posts the transcript and converts API failures
  to a user-facing error message.
- `frontend/src/types/insights.ts` mirrors the backend V1.5 response contract.
- `frontend/src/components/InsightsGrid.tsx` renders the seven original insight
  sections.
- `frontend/src/components/V15Insights.tsx` renders financial metrics,
  management guidance, and management signals when those sections contain
  displayable content.

## Technology

- Frontend: React 18, TypeScript, Vite
- Backend: Python, FastAPI, Pydantic v2
- AI provider: Google Gemini structured output
- Deployment targets documented by the project: Vercel frontend and Render
  backend

## V1.5 Boundary

V1.5 is limited to one submitted transcript and transcript-grounded analysis.
Future work should extend the documented response contract deliberately rather
than change the existing fields incompatibly.
