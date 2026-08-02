# PROJECT_RULES.md

## Project Philosophy

This project is being built as a portfolio-quality AI application.

The objective is to learn software engineering, AI application development, financial document analysis, backend development, frontend development, API design, and product thinking.

The project should prioritize:

* Clean architecture
* Maintainability
* Simplicity
* Security
* Learning value

The project should not prioritize:

* Maximum feature count
* Premature optimization
* Unnecessary complexity
* Trendy frameworks without clear benefits

---

# Engineering Principles

1. Explain architectural decisions before implementing them.

2. Prefer simple solutions over complex solutions.

3. Avoid overengineering.

4. Every module should have a single responsibility.

5. Code should be understandable by a first-year Computer Science student.

6. Favor readability over cleverness.

7. Build for future extensibility without introducing unnecessary abstractions.

---

# Technology Stack

Frontend:

* React
* Tailwind CSS

Backend:

* FastAPI
* Python

AI:

* Gemini API (initially)

Deployment:

* Vercel (Frontend)
* Render or Railway (Backend)

---

# Forbidden Technologies For Version 1

Do NOT introduce:

* LangChain
* LangGraph
* CrewAI
* AutoGen
* Pinecone
* Weaviate
* ChromaDB
* Vector databases
* RAG pipelines
* Fine-tuning
* Multi-agent systems
* User authentication
* Databases
* Stock market APIs

These technologies may be considered in future versions if justified.

---

# Coding Standards

* Use descriptive variable names.
* Use type hints where possible.
* Use Pydantic models for request and response validation.
* Keep functions small and focused.
* Avoid duplicate logic.
* Separate API routes from business logic.
* Separate prompts from backend services.
* Use environment variables for secrets.

---

# Security Rules

* Never hardcode API keys.
* Never commit secrets to GitHub.
* Store secrets in .env files.
* Validate all user inputs.
* Handle API failures gracefully.
* Return meaningful error messages.

---

# Development Workflow

Before implementing a feature:

1. Understand the requirement.
2. Identify tradeoffs.
3. Propose a design.
4. Explain why the design was chosen.
5. Implement.
6. Test.

Do not immediately generate large amounts of code without discussion.

---

# AI Agent Instructions

Any AI coding assistant working on this repository must:

1. Read ARCHITECTURE.md.
2. Follow the existing folder structure.
3. Follow the existing API contracts.
4. Avoid introducing unnecessary dependencies.
5. Avoid changing project architecture without justification.
6. Explain tradeoffs before major changes.

The architecture is owned by the human developer. AI assistants should assist implementation, not redesign the project without approval.
