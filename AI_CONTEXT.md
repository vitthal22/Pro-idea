# AI Resume Brutal Roaster — AI Context

> **This file is the single source of truth for any AI assistant working on this project.**
> Read this first before writing any code.

---

## Project Summary

An AI-powered resume analysis tool that delivers brutally honest, constructive feedback. Users upload a resume, select an analysis mode, and receive a structured "roast" with scores, critical issues, warnings, suggestions, and actionable improvements.

**Not** a simple "paste resume, get ChatGPT response" tool. This is a multi-evaluator AI pipeline with structured outputs, hybrid scoring, and proper engineering.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11 |
| Web Framework | FastAPI | 0.115+ |
| ORM | SQLAlchemy 2.0 | (async) |
| Migrations | Alembic | 1.13+ |
| Database | PostgreSQL + pgvector | 16+ |
| Validation | Pydantic v2 | 2.9+ |
| AI Provider | litellm | — |
| PDF Extraction | pdfplumber | — |
| DOCX Extraction | python-docx | 1.1+ |
| OCR | pytesseract + pdf2image | — |
| Auth | PyJWT + pwdlib[bcrypt] | JWT + password hashing (replaces unmaintained python-jose/passlib) |
| Rate Limiting | slowapi | — |
| Package Manager | Poetry | — |
| Testing | pytest + pytest-asyncio | Real PostgreSQL test DB (never SQLite) |
| Linting | Ruff | — |
| Type Checking | mypy | — |
| Docker | PostgreSQL + pgvector + Redis | Infrastructure only (dev) |

---

## Architecture Pattern

**Modular Monolith** — Clean module boundaries, single deployable unit.

```
app/
├── api/                  # HTTP layer (routers, request/response schemas)
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic schemas (domain + AI outputs)
├── services/             # Business logic
├── document_processing/  # File extraction (OCR handler is V2)
├── ai/                   # AI provider, evaluators, prompts, scoring
│                         #   scoring.py = deterministic checks + hybrid engine
│                         #   + mode weights (no separate scoring/ package)
├── storage/              # File storage abstraction
└── common/               # Shared utilities, exceptions, middleware
```

See `ARCHITECTURE.md` for the complete architecture blueprint.

---

## Key Design Decisions

1. **Evaluators, not agents** — Structured prompt → structured output functions. No autonomous loops for MVP.
2. **Hybrid scoring** — 50% deterministic + 50% AI-derived. Reproducible and explainable.
3. **Pydantic everywhere** — API validation, AI outputs, database serialization. One schema, multiple uses.
4. **litellm for AI** — Switch from OpenAI to Anthropic by changing one env var.
5. **pdfplumber for PDFs** — Good extraction, BSD license (safe for any use).
6. **Synchronous MVP** — SSE stream endpoint (`GET /analyses/{id}/stream`) + status poll fallback. arq queue for V2 (firm choice, not Celery).
7. **Docker infrastructure only** — PostgreSQL + Redis in Docker during dev. App runs locally with uvicorn.

---

## Analysis Modes

| Mode | Evaluators Used | Description |
|---|---|---|
| `general` | Recruiter + ATS + Technical + Content Quality | Analyze resume as a whole |
| `role_based` | All above + Job Matcher (role context) | Analyze for a specific job role |
| `jd_based` | All above + Job Matcher (JD comparison) | Compare against a job description |
| `custom` | All above + custom instruction injection | User-provided focus areas |

---

## Database Overview

```
users → resumes → analyses → analysis_results
                    ↓
              analysis_usage (cost tracking)

prompt_versions table: V2 only. MVP tracks prompt versions as file
constants (PROMPT_VERSION) recorded in analyses.prompt_versions_used JSONB.
```

All IDs are UUIDs (`gen_random_uuid()`, pgcrypto enabled in migration 1).
Timestamps are UTC `TIMESTAMPTZ`. All child FKs use ON DELETE CASCADE.

---

## Environment Variables

```
# .env.example
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resume_roaster
REDIS_URL=redis://localhost:6379/0
AI_PROVIDER=openai
AI_MODEL=gpt-4o
AI_FAST_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=
JWT_SECRET_KEY=change-this-to-a-random-string-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=7
STORAGE_BACKEND=local
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
APP_ENV=development
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_FREE=3
RATE_LIMIT_PRO=50
LOGIN_RATE_LIMIT_PER_HOUR=10
LOG_LEVEL=INFO

# V2 only:
# R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY
# R2_BUCKET_NAME / R2_ENDPOINT_URL
```

---

## How to Run

```bash
# Install dependencies
poetry install

# Start infrastructure (PostgreSQL + Redis)
docker compose up -d postgres redis

# Set up database
poetry run alembic upgrade head

# Run development server
poetry run uvicorn app.main:app --reload --port 8000

# Run tests
poetry run pytest

# Lint
poetry run ruff check .

# Type check
poetry run mypy app/
```

---

## Current Phase

**Phase 1: Foundation** — Project setup, database, authentication.

See `ARCHITECTURE.md` Section 17 for the full implementation plan.

---

## Backend and Frontend Structure

### Backend (`backend/`)
FastAPI modular monolith (`app/` package) strictly following module boundaries:
- **`api/`** — HTTP layer only: routers, request/response schemas, dependency injection
- **`models/`** — SQLAlchemy 2.0 ORM, async PostgreSQL, relationships
- **`schemas/`** — Pydantic v2: API contracts + AI output schemas (all `Field(description=...)`)
- **`services/`** — Business logic: auth, resumes, analyses orchestration
- **`document_processing/`** — PDF/DOCX/OCR extraction pipeline (pdfplumber → python-docx → pytesseract fallback)
- **`ai/`** — AI layer: `litellm` wrapper (`call_ai()`), orchestrator, parser, aggregator, composer, evaluators (prompt-based, not agents), prompts (versioned, never hardcoded), roles, modes; **`ai/scoring.py`** holds the hybrid scoring engine: deterministic checks (50%) + AI-assessed categorical ratings (50%), mode-specific weights, partial-failure weight renormalization
- **`storage/`** — Abstract storage interface (local S3-migratable, MVP local filesystem)
- **`common/`** — Exceptions, security (JWT/bcrypt), middleware, logging

Key conventions: type hints everywhere, `X | None` syntax, Ruff formatting (4-space indent, 88-char lines), double quotes, trailing commas. One Pydantic schema library across the stack. Evaluators are pure functions: structured in → structured out. No autonomous agents for MVP.

### Frontend (`frontend/`)
Next.js 15 App Router (`src/app/`), TypeScript, Tailwind CSS v4 + shadcn/ui components:
- **`src/app/`** — Page routes: landing, auth (login/register), dashboard, upload wizard, analysis result view with streaming steps
- **`src/components/`** — shadcn/ui primitives (button, card, input, progress, skeleton, dialog, etc.), layout, auth forms, upload UX, analysis display (score rings, feedback cards, roast view), shared helpers
- **`src/hooks/`** — TanStack Query hooks: `useAnalyses`, `useAnalysis(id)`, `useResumes`, `useLogin`, `useUpload`, `useStartAnalysis`; plus SSE streaming hook
- **`src/lib/`** — API client (fetch wrapper with JWT injection), TanStack Query config, utility functions (`cn()`)
- **`src/stores/`** — Zustand store: auth token + user persistence (client state only; server state in TanStack Query)
- **`src/types/`** — TypeScript mirrors of backend Pydantic responses (`resume.ts`, `analysis.ts`, `api.ts`)
- **`src/providers/`** — Root `AppProviders` wrapping `QueryClientProvider`

Data flow: `component → TanStack Query hook → api-client.ts → FastAPI`. Auth token stored in Zustand; server-side rate limiting via slowapi. UI states (loading, error, empty) handled with shadcn patterns + `sonner` toasts.

### Installed Dependencies

**Backend** (`pyproject.toml` / Poetry):
`fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic`, `pydantic-settings`, `litellm`, `python-multipart`, `pdfplumber`, `python-docx`, `python-magic` (Linux/macOS) / `python-magic-bin` (Windows — same `import magic` API), `pwdlib[bcrypt]`, `pyjwt`, `slowapi`, `redis`, `arq`
V2 only: `boto3` (R2), `pytesseract` + `pdf2image` (OCR), pgvector + llama-index packages (RAG)
Dev: `pytest`, `pytest-asyncio`, `pytest-mock`, `httpx`, `ruff`, `mypy`

**Frontend** (npm):
`next`, `react`, `react-dom`, `typescript`, `@types/*`, `tailwindcss` v4, `shadcn/ui` (CLI + radix components), `@tanstack/react-query`, `@tanstack/react-query-devtools`, `zustand`, `zod`, `react-dropzone`, `recharts`, `lucide-react`, `sonner`

### How They Connect
- Upload: Frontend `POST /api/v1/resumes/upload` (multipart) → Backend stores file, creates Resume record, returns `resume_id`
- Analysis: Frontend `POST /api/v1/analyses` (mode, target_role, instructions) → Backend creates Analysis record, runs synchronous pipeline (extraction → AI parsing → parallel evaluators → aggregation → scoring → roast compositing) → returns streaming SSE steps or final result → Frontend TanStack Query refetches `/analyses/:id` or consumes SSE stream
- Auth: Frontend login → access token held in Zustand (memory only) + refresh token in HttpOnly, SameSite=Lax cookie → every API call includes `Authorization: Bearer <token>` header → Backend `get_current_user` dependency validates token → `api-client.ts` auto-refreshes once on 401 via the cookie

---

## When Working on This Project

1. **Read `CONVENTIONS.md`** before writing code.
2. **Read `ARCHITECTURE.md`** if you need deep system understanding.
3. **Follow module structure** — no business logic in routers, no HTTP in services.
4. **Use Pydantic schemas** for all data validation.
5. **Use type hints** everywhere.
6. **Write tests** for new features.
7. **Never hardcode prompts** — load from `app/ai/prompts/`.
8. **Never call AI providers directly** — use `app.ai.provider.call_ai()`.
