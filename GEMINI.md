# AI Resume Brutal Roaster — Project Context

> Antigravity: Read this first, then load Skills from `.agents/skills/`.
> Read `PROGRESS.md` FIRST for current state (done/doing/blocked/issues) and update it at the end of every session — automatically, without being reminded.

## Project

AI-powered resume analysis tool with a multi-evaluator pipeline delivering brutally honest, constructive feedback. Users upload a resume, select an analysis mode, and get a structured roast with scores, issues, and improvements.

## Tech Stack

- **Python 3.11** | **FastAPI 0.115+** | **SQLAlchemy 2.0 (async)** | **PostgreSQL 16+**
- **Alembic** (migrations) | **Pydantic v2** (validation) | **litellm** (AI provider)
- **pdfplumber** (PDF) | **python-docx** (DOCX) | **pytesseract** (OCR)
- **Poetry** (deps) | **pytest** (tests) | **slowapi** (rate limiting)
- **Docker** (PostgreSQL + Redis infrastructure only during dev)

## Architecture

**Modular Monolith.** Single deployable, clean module boundaries.

```
app/
├── api/                  # HTTP layer
├── models/               # SQLAlchemy ORM
├── schemas/              # Pydantic (domain + AI)
├── services/             # Business logic
├── document_processing/  # PDF, DOCX (OCR handler is V2)
├── ai/                   # Provider, evaluators, prompts, scoring
│   ├── provider.py       # litellm wrapper
│   ├── orchestrator.py   # Pipeline coordinator
│   ├── scoring.py        # Hybrid scoring: deterministic + AI ratings
│   ├── evaluators/       # Recruiter, ATS, Technical, Content, JobMatch
│   └── prompts/          # All prompts (versioned)
├── storage/              # File storage abstraction
└── common/               # Exceptions, dependencies, middleware
```

## Key Rules

0. **Read `PROGRESS.md` first** and update it every session; review your own code (no dead code, honest naming, no duplication) and verify security paths with real requests — see `AGENTS.md` Code Quality + Session Protocol
1. **Never hardcode prompts** — load from `app/ai/prompts/`
2. **Never call AI directly** — use `app.ai.provider.call_ai()`
3. **Pydantic everywhere** — all data validation
4. **Type hints required** — no exceptions
5. **Business logic in services** — routers only handle HTTP
6. **Tests for new features** — mock AI calls in unit tests
7. **UUIDs for all IDs** — native PostgreSQL type
8. **JSONB for AI outputs** — enforced with Pydantic

## Analysis Modes

| Mode | Evaluators |
|---|---|
| `general` | Recruiter + ATS + Technical + Content Quality |
| `role_based` | All above + Job Matcher |
| `jd_based` | All above + Job Matcher (JD comparison) |
| `custom` | All above + custom instructions |

## How to Run

```bash
poetry install
docker compose up -d postgres redis
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000
poetry run pytest
```

## Skills Available

Load from `.agents/skills/` when performing tasks:

- `create-api-endpoint` — Add a new API endpoint
- `create-evaluator` — Add a new AI evaluator
- `create-prompt` — Create a new versioned prompt
- `add-analysis-mode` — Add a new analysis mode
- `add-database-model` — Add a new database model
- `debug-ai-pipeline` — Debug AI pipeline failures
- `write-tests` — Write tests for this project
- `add-role-context` — Add a new job role context
