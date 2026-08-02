# Backend Setup

This backend uses FastAPI for HTTP routes, Pydantic for request and response
validation, and the Gemini API for AI analysis.

## 1. Create a virtual environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_gemini_api_key_here` with your actual Gemini API
key.

Load the variables into your shell:

```bash
set -a
source .env
set +a
```

Required variables:

- `GEMINI_API_KEY`: API key used by the backend to call Gemini.
- `GEMINI_MODEL`: Gemini model name. Defaults to `gemini-3.5-flash` in code if
  this variable is not set.
- `CORS_ORIGINS`: comma-separated frontend origins allowed to call the backend.

## 4. Run the backend locally

```bash
uvicorn backend.main:app --reload
```

The backend should run at:

```text
http://127.0.0.1:8000
```

## 5. Test GET /health

In a second terminal:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## 6. Test POST /analyze

The transcript must be long enough to pass request validation.

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Operator: Welcome to the quarterly earnings call. Management discussed revenue growth, margin pressure, cost discipline, product demand, customer adoption, operational efficiency, macroeconomic uncertainty, and future guidance. The leadership team explained that demand remains resilient in key markets while costs and foreign exchange remain areas to monitor. They also described new product opportunities and a cautious but constructive outlook for the next quarter."
  }'
```

Expected result:

- If `GEMINI_API_KEY` is valid, the backend should return JSON matching the
  `EarningsAnalysisResponse` schema.
- If `GEMINI_API_KEY` is missing, the backend should return an error explaining
  that the AI provider is not configured.
- If Gemini fails or returns invalid output, the backend should return a safe
  provider failure error.

## Request lifecycle

1. The client sends JSON to `POST /analyze`.
2. FastAPI validates the request body with `EarningsAnalysisRequest`.
3. The route calls the analysis service.
4. The analysis service builds the Version 1 prompt.
5. The analysis service calls the Gemini service.
6. The Gemini service calls the external Gemini API using `GEMINI_API_KEY`.
7. The Gemini response is parsed as JSON.
8. The parsed JSON is validated with `EarningsAnalysisResponse`.
9. FastAPI returns the final structured JSON response.
