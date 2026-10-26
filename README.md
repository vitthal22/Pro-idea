# AI Resume Brutal Roaster

An AI-powered resume analysis tool with a multi-evaluator pipeline that delivers brutally honest, constructive feedback. Upload a resume, pick an analysis mode, and get a structured "roast" with scores, critical issues, warnings, and actionable improvements.

> **Not** a simple "paste resume, get ChatGPT response" tool. This is a multi-evaluator AI pipeline with structured outputs, hybrid scoring, and proper engineering.

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
| Auth | PyJWT + pwdlib[bcrypt] | JWT + password hashing |
| Rate Limiting | slowapi | — |
| Package Manager | Poetry | — |
| Testing | pytest + pytest-asyncio | Real PostgreSQL test DB |
| Linting | Ruff | — |
| Type Checking | mypy | — |
| Frontend | Next.js 15, TypeScript, Tailwind v4, shadcn/ui | — |

---

## Prerequisites

Install these tools before starting. Click each to install:

| Tool | Why needed | Install command |
|---|---|---|
| **Python 3.11** | Backend language + all Python deps | `winget install Python.Python.3.11` |
| **Poetry** | Python dependency manager | `pip install poetry` |
| **Docker Desktop** | PostgreSQL + pgvector + Redis | `winget install Docker.DockerDesktop` |
| **Node.js 18+** | Frontend (Next.js) | `winget install OpenJS.NodeJS` |
| **Tesseract OCR** | PDF OCR fallback | `winget install Tesseract.Tesseract-OCR` |
| **Poppler** | pdf2image needs `pdftoppm` | `winget install Uvlnatives.Poppler` |

> **Windows note:** The `python.exe` that ships with Windows is a Store stub. Install a real Python 3.11 via winget and be sure to check **"Add Python to PATH"** during install — that replaces the stub.

### Verify installs

```bash
python --version   # 3.11.x
poetry --version   # 1.x
docker --version   # 24.x
node --version     # 18+ / 22
npm --version
```

---

## Setup

### 1. Backend

```bash
cd backend
poetry install
cp .env.example .env      # edit with your API keys and secrets
```

Edit `backend/.env`. The database pieces (this repo's local values):

```env
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=AIRoast
# Optional — wins over the DB_* parts when set. Percent-encode special characters
# in the URL (a `@` in the password becomes `%40`):
DATABASE_URL=postgresql+asyncpg://postgres:your-postgres-password@localhost:5432/AIRoast
USER_STORE=postgres

OPENAI_API_KEY=sk-your-key-here      # or ANTHROPIC_API_KEY
JWT_SECRET_KEY=change-this-to-a-random-string-at-least-32-chars
```

### 2. Infrastructure (PostgreSQL + Redis)

```bash
docker compose up -d postgres redis
```

Already running PostgreSQL locally (no Docker)? Create the database once and skip
compose — the app only reads `DB_*` / `DATABASE_URL`:

```bash
createdb -U postgres AIRoast
```

### 3. Database

```bash
cd backend
poetry run alembic upgrade head     # or, from the repo root: npm run db:migrate --prefix backend
```

This creates the `users` table. The backend seeds the demo account on startup
(idempotent), so no manual insert is needed.

### Demo login

Login is **email + password only** — no OTP, no email verification, no confirmation
step. The seeded account:

| Field | Value |
|---|---|
| Email | `demo@airoast.dev` |
| Password | `Demo@12345` |

Override it per environment with `DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD` / `DEMO_USER_NAME`
in `backend/.env`; leave them blank to skip seeding. Restart the backend and it logs
`Demo user created` (first run) or `Demo user already exists` (later runs).

### 4. Run the backend

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

### 5. Tests

```bash
cd backend && poetry run pytest      # or, from the repo root: npm test --prefix backend
```

The suite runs against the **same PostgreSQL** as the app (`DB_*` must be reachable)
and applies migrations itself. Each test runs inside a transaction that is rolled
back, so no test rows survive — the seeded demo user and your dev data stay as they are.

Open http://localhost:8000/docs for the Swagger UI.

### 6. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project layout

```
app/                    # FastAPI modular monolith
├── api/                # HTTP layer (routers, schemas, deps)
├── models/             # SQLAlchemy 2.0 ORM
├── schemas/            # Pydantic v2 (API + AI outputs)
├── services/           # Business logic
├── document_processing/# PDF/DOCX/OCR extraction
├── ai/                 # litellm wrapper, evaluators, prompts, scoring
├── storage/            # File storage abstraction
└── common/             # Exceptions, security, middleware, logging
frontend/               # Next.js 15 App Router + TypeScript
tests/                  # pytest (unit, API, integration)
```

---

## How to Run

```bash
# Install dependencies
poetry install

# Start infrastructure (PostgreSQL + Redis) — skip if using a local Postgres
docker compose up -d postgres redis

# Apply migrations (creates the users table)
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

## Analysis Modes

| Mode | Evaluators Used | Description |
|---|---|---|
| `general` | Recruiter + ATS + Technical + Content Quality | Analyze resume as a whole |
| `role_based` | All above + Job Matcher (role context) | Analyze for a specific job role |
| `jd_based` | All above + Job Matcher (JD comparison) | Compare against a job description |
| `custom` | All above + custom instruction injection | User-provided focus areas |

---

## Current Phase

**Phase 1: Foundation** — Project setup, database, authentication.

See `PROJECT_PLAN.md` for the full implementation roadmap (11 modules).

---

## AI Context

This project uses an **AI context file** (`AI_CONTEXT.md`) as the single source of truth for any AI assistant working on it. Read that first before writing code.

- `AI_CONTEXT.md` — project overview, tech stack, architecture
- `CONVENTIONS.md` — coding rules and standards
- `SKILLS.md` — step-by-step task instructions
- `ARCHITECTURE.md` — complete architecture blueprint
- `PROJECT_PLAN.md` — incremental implementation plan
- `AGENTS.md` — anti-hallucination rules loaded automatically every session