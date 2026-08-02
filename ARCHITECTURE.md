# ARCHITECTURE.md

## Project Name

CallQ

---

# Vision

Build an AI-powered financial analysis tool that transforms earnings call transcripts into structured investor insights.

The long-term vision is to evolve into an AI-native investment research assistant capable of analyzing multiple financial documents and generating investment research reports.

---

# Version 1 Goal

Given an earnings call transcript, generate:

* Executive Summary
* Key Positives
* Key Negatives
* Risks Mentioned
* Opportunities Mentioned
* Management Outlook
* Major Themes

Version 1 focuses on single-document analysis.

---

# User Flow

User submits transcript

↓

Backend receives transcript

↓

Transcript is cleaned and validated

↓

Prompt is generated

↓

Gemini API analyzes transcript

↓

Structured JSON is returned

↓

Frontend displays insights

---

# System Architecture

Frontend (React)

↓

Backend API (FastAPI)

↓

Analysis Service

↓

Gemini API

---

# Backend Structure

backend/

├── api/

├── services/

├── prompts/

├── models/

├── utils/

└── main.py

---

## api/

Purpose:

Handle HTTP requests and responses.

Responsibilities:

* Route definitions
* Request validation
* Response handling

Business logic should not live here.

---

## services/

Purpose:

Core application logic.

Responsibilities:

* Transcript processing
* Analysis workflows
* Gemini API integration

This is the primary business logic layer.

---

## prompts/

Purpose:

Store AI prompts.

Responsibilities:

* Prompt templates
* Prompt versioning
* Structured output instructions

Prompt logic should not be hardcoded inside API routes.

---

## models/

Purpose:

Data schemas.

Responsibilities:

* Request models
* Response models
* Validation models

Use Pydantic.

---

## utils/

Purpose:

Reusable helper functions.

Examples:

* Text cleaning
* File parsing
* Logging helpers

---

# Frontend Structure

frontend/

├── components/

├── pages/

├── services/

├── hooks/

└── App.jsx

---

## components/

Reusable UI components.

Examples:

* SummaryCard
* ThemeCard
* RiskCard

---

## pages/

Application pages.

Examples:

* HomePage
* ResultsPage

---

## services/

Frontend API communication.

Responsibilities:

* Calling backend endpoints
* Handling API responses

---

## hooks/

Custom React hooks.

Used when shared frontend logic becomes necessary.

---

# API Design

## Health Check

GET /health

Purpose:

Verify backend is running.

---

## Analyze Transcript

POST /analyze

Purpose:

Analyze an earnings call transcript.

Input:

Transcript text.

Output:

Structured analysis JSON.

---

# Output Schema

{
"executive_summary": [],
"positives": [],
"negatives": [],
"risks": [],
"opportunities": [],
"management_outlook": "",
"themes": []
}

This schema is considered the Version 1 contract.

Future versions should extend this schema rather than replace it.

---

# Future Roadmap

Version 2

* Sentiment Analysis
* Theme Analysis
* Confidence Indicators
* Keyword Analysis

Version 3

* Quarter-over-Quarter Comparison
* Theme Evolution
* Risk Changes
* Tone Comparison

Version 4

* Cross-Company Analysis
* Competitive Analysis
* Comparative Insights

Version 5

* Multi-Document Research Assistant
* Investment Thesis Generation
* Bull Case
* Bear Case
* Research Reports

---

# Non-Goals For Version 1

Version 1 should NOT include:

* Databases
* Authentication
* Vector Databases
* RAG
* Agent Frameworks
* Fine-Tuning
* Stock Market Data
* Portfolio Tracking

The objective is a focused AI analysis application.

---

# Success Criteria

Version 1 is complete when:

1. User can submit a transcript.
2. Backend processes the transcript successfully.
3. Gemini returns structured insights.
4. Frontend displays results clearly.
5. Application is deployed publicly.
6. Source code is documented and portfolio-ready.
