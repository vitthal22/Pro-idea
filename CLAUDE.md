# Claude Code Context

> Claude Code: Read this file first, then read the referenced files for full project context.

## Project

**AI Resume Brutal Roaster** — An AI-powered resume analysis tool with a multi-evaluator pipeline that delivers brutally honest, constructive feedback.

## Quick Start

0. Read `PROGRESS.md` FIRST — current state (done/doing/blocked/issues), run commands, file map. Update it at the end of every session, automatically, without being reminded.
1. Read `AI_CONTEXT.md` for project overview, tech stack, and architecture
2. Read `CONVENTIONS.md` for coding rules and standards
3. Read `SKILLS.md` for step-by-step task instructions
4. Read `ARCHITECTURE.md` for the complete architecture blueprint (15 sections)

## Tech Stack (Summary)

- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL + SQLAlchemy 2.0 (async)
- **AI:** litellm (OpenAI/Anthropic provider abstraction)
- **Validation:** Pydantic v2
- **PDF/DOCX:** pdfplumber + python-docx
- **Auth:** JWT (PyJWT + pwdlib — access token in memory, refresh in HttpOnly cookie)

## Key Rules

- Read `PROGRESS.md` first; update it every session (see `AGENTS.md` Session Protocol)
- Review your own code before claiming done: no dead code, honest naming, no duplicated logic, constants before use
- Security bar: logout must revoke (denylist), no account enumeration, deliberate cookie flags, verify success AND failure with real requests
- External stores behind Protocol + config-selected factory (`user_store`, `denylist_store`) — swap via `.env`, not code edits
- Follow `CONVENTIONS.md` for all coding decisions
- Use Pydantic schemas for ALL data validation — never validate manually
- Use type hints EVERYWHERE — this is a typed Python project
- Never hardcode prompts — always load from `app/ai/prompts/`
- Never call AI providers directly — use `app.ai.provider.call_ai()`
- Put business logic in services, not routers
- Use `app/common/exceptions.py` for custom exceptions
- Write tests for new features — mock AI calls in unit tests

## Running

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000
poetry run pytest
```

## Current Phase

Phase 1: Foundation — Project setup, database, authentication.
