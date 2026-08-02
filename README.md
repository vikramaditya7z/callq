# CallQ

> AI-powered earnings call intelligence for investors.

CallQ transforms lengthy earnings call transcripts into structured investor insights using Google's Gemini API. Built with React, FastAPI, and TypeScript, it delivers executive summaries, business risks, opportunities, management outlook, and key themes through a clean, production-ready web application.

**Live Demo**  
https://callq-nine.vercel.app

---

## Features

- AI-powered transcript analysis
- Structured investor insights
- Executive summaries
- Risks & opportunities extraction
- Management outlook
- Theme identification
- Responsive React interface
- Production deployment on Vercel & Render

---

## Tech Stack

| Frontend | Backend | AI | Deployment |
|----------|----------|----|------------|
| React + TypeScript | FastAPI + Python | Gemini API | Vercel + Render |

---

## Architecture

```
React
   │
FastAPI
   │
Gemini API
   │
Structured Validation
   │
Investor Insights
```

---

## Local Setup

```bash
git clone https://github.com/vikramaditya7z/callq.git

cd callq

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

# Add your Gemini API key

set -a
source .env
set +a

uvicorn backend.main:app --reload
```

Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## API

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/analyze` | Analyze an earnings call transcript |

---

## Roadmap

- Financial metric extraction
- Quarter-over-quarter comparison
- Interactive dashboards
- PDF research reports
- Multi-document analysis

---

## License

MIT
