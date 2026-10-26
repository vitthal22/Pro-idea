# PROGRESS — Project Tracker

> **Purpose:** The single file any AI assistant (or human) reads FIRST to know
> the current state of this project — without rescanning the whole repo.
> Kept up to date at the end of every session (see the rule in `AGENTS.md`).

---

## 1. Status snapshot

**Last updated:** 2026-10-26
**Phase:** Foundation + Auth COMPLETE, now **persisted in PostgreSQL** (local `AIRoast` DB) — full session lifecycle works: register, login, refresh (rotation), logout (denylist revocation), /me, frontend session restore.
**One-liner:** Auth runs against real Postgres (`USER_STORE=postgres`) via Alembic-migrated `users` table; a demo account is seeded at startup; login is email+password only (no OTP).
**Plan progress (PROJECT_PLAN.md, checkboxes):** 47/223 items complete, 5 partial. Module 1 "Project Foundation" 28/45 complete + 5 partial; Module 9 "Frontend Foundation" 19/20; Modules 2–8 and 10+ not started. Auth (M1.5) and error handling (M1.7) are done; rate limiting + request logging (M1.6) and the remaining DB models (M1.4) are not.

---

## 2. Done (verified with real output)

| Area | What exists | Verification |
|---|---|---|
| Backend scaffold | `backend/app` (FastAPI + pydantic-settings config + logging) | `uvicorn` boots; `/health` → `{"status":"ok"}` |
| Backend auth (reviewed) | `/auth/register` (201+tokens), `/auth/login`, `/auth/refresh` (rotation), `/auth/logout` (204, denylist revoke), `/auth/me`; consistent `TokenResponse` everywhere | curl-verified: 201 register, 409 duplicate, 200 login, 401 bad password, `Token has been revoked` on replayed refresh after logout, 204 logout, cookie deleted |
| Token revocation | `TokenDenylist` protocol + in-memory impl (`token_denylist.py`); tokens carry `jti`; logout revokes, refresh refuses revoked tokens | Explicit stolen-token replay test → 401 revoked |
| Frontend session | `useCurrentUser` query restores profile via `/me` on reload (works when DB arrives); `useLogout`; typed `AuthError` with per-kind messages; single-request register | build + lint pass |
| Auth security | bcrypt hashing (pwdlib `PasswordHash([BcryptHasher()])`), JWT access 1h + refresh 7d with `jti`, HttpOnly SameSite=Lax cookie path-scoped to `/api/v1/auth`, no account enumeration | Cookie flags in `deps.py`; verified in jar |
| Error handling | `AppException` hierarchy → global handler returns `{"error":{"code","message","details"}}` | 401/409 responses verified as structured JSON |
| User store | `UserRepository` protocol + `InMemoryUserRepository` (tests) + `PostgresUserRepository` (real DB); selected by `USER_STORE` | mypy clean; both paths verified |
| Database | `app/db/base.py`, `app/db/session.py` (async engine, pool pre-ping, 10s connect timeout), `get_db()` yields `AsyncSession`; Alembic 0001 creates `users` | `alembic upgrade head` → `MIGRATIONS: ['0001']`; columns/indexes verified via asyncpg |
| Demo seed | `app/db/seed.py` + startup lifespan: creates `demo@airoast.dev` from `DEMO_USER_*` env, idempotent, logs and continues if DB unreachable | Run 1: `Demo user created: demo@airoast.dev`; run 2 after restart: `Demo user already exists`; login still 200 after restart |
| DB-backed auth | login 200 (demo), wrong password 401, `/me` 200, register 201, duplicate 409, bcrypt hash `$2b$12$` in DB, no plaintext | curl against `AIRoast`; rows inspected via asyncpg |
| Test suite | `backend/tests/`: repository (6), AuthService (9), auth API (14), demo seeding (3) — real PostgreSQL, per-test transaction rollback, migrations applied by a session fixture | `pytest` → `30 passed in 7.85s`; mutation check (dropping `.lower()` in `normalize_email`) → `2 failed, 4 passed`; after 30 tests the dev DB still holds only `demo@airoast.dev`; `mypy app/ tests/` clean; ruff clean |
| Frontend scaffold | Next.js 16.3.7 + Tailwind v4 + shadcn (radix/nova) + TanStack Query + Zustand + Zod | `npm run build` ✅ (6 routes), `npm run lint` ✅ |
| Frontend auth UI | Landing, `/login`, `/register` (zod validation), dashboard (guarded), api-client with JWT + one-shot 401 refresh, `credentials: "include"` for cookies | Build/lint pass; live test pending backend running |
| npm workflow | Root + backend `package.json` scripts; backend has a project-local `.venv` (like node_modules); `concurrently` runs both servers with one command | `npm run dev` verified: backend `/health` `{"status":"ok"}` + frontend `HTTP 200`; `npm run check` passes both sides |

---

## 3. In progress / next up

- [ ] **Next fix (correctness under load): bcrypt runs on the event loop.** `AuthService` calls sync `hash_password`/`verify_password` inside `async def`; measured 258–271 ms per call, ~3.7 logins/sec per worker, and every other request on that worker stalls for the duration. Fix = `await asyncio.to_thread(...)` at the service boundary + a test that concurrent requests are not blocked.
- [ ] Then **Module 1.6** (Redis denylist + rate limiting), then the remaining DB models (M1.4) and Module 2 (resume upload).
- [ ] `RedisTokenDenylist`: protocol + factory seam are ready; logout revocation is still in-memory and returns after a backend restart (documented, by design).
- [ ] Later tables (`resumes`, `analyses`, `analysis_results`) get their own Alembic revisions; only `users` exists today.

---

## 4. Blocked / waiting

| Item | Blocker | Unblock path |
|---|---|---|
| PostgreSQL (M1.2–M1.4) | Not blocked anymore — a **local** PostgreSQL 18.3 serves `AIRoast`; Docker is still absent but not required | Docker install optional (`docker compose up -d postgres redis`) |
| Rate limiting (M1.6) | Needs Redis for meaningful limits | Install Docker |
| Live frontend↔backend auth test | Nothing blocking — both run locally | Run backend + frontend (commands below), register via UI |

---

## 5. Known issues / gotchas (read before coding)

1. **Poetry is only needed for setup** — daily work uses `npm run ...` from the repo root, which calls `backend/.venv` directly. The old cached pypoetry env was deleted; if someone runs `poetry install` without the `virtualenvs.in-project` config, poetry creates envs elsewhere again (`backend/poetry.toml` pins `in-project = true`).
2. **Use `http://localhost:3000`, not `127.0.0.1:3000`** — Next dev listens on IPv6; `curl` against `127.0.0.1` may show connection refused (IPv6/IPv4 mismatch), browsers on `localhost` are fine.
3. **pwdlib API** — `PasswordHash.recommended()` requires argon2 (not installed); this project uses `PasswordHash([BcryptHasher()])` per the `pwdlib[bcrypt]` spec. Don't "fix" it back.
3. **pwdlib API** — `PasswordHash.recommended()` requires argon2 (not installed); this project uses `PasswordHash([BcryptHasher()])` per the `pwdlib[bcrypt]` spec. Don't "fix" it back.
4. **zod v4 on frontend** — top-level `z.email()` exists, but `.min()` must chain on `z.string()`.
5. **shadcn v4 CLI** — new flags (`--base radix --preset nova`); no `base-color`; `form` component doesn't exist in the new registry (auth forms use plain state + zod).
6. **Cookie path** — refresh cookie is scoped to `/api/v1/auth` deliberately. If you add logout, delete the cookie on that path.
7. **CORS** — backend allows `http://localhost:3000` with credentials; frontend uses `credentials: "include"`. Keep both in sync.
8. **In-memory stores are volatile** — users AND revoked tokens vanish on backend restart until Postgres/Redis land. Expected; don't file as a bug.
9. **Test scripts: strip CR from cookie jars** — curl cookie jars on Windows have `\r` line endings; when extracting a token use `| tr -d '\r\n'`, or you'll send a broken header and get a misleading 401.
10. **Alembic and `%` in the DSN** — `config.set_main_option("sqlalchemy.url", ...)` raises `ValueError: invalid interpolation syntax` on a URL-encoded password (`%40`). `alembic/env.py` therefore builds the engine straight from `settings.database_dsn`; keep it that way.
11. **`alembic/` vs the `alembic` package** — the script directory shares the installed package's name, so ruff's isort must be told `known-third-party = ["alembic"]` (configured in `pyproject.toml`). Runtime imports still resolve to the installed package.
12. **Database is `AIRoast`** (verified in `pg_database`), not `resume_roaster` as older docs/AI_CONTEXT say, and not `AIRoastt`. `backend/.env` ends with an override block (`DB_*`, `DATABASE_URL`, `USER_STORE=postgres`, `DEMO_USER_*`) — last value wins in pydantic-settings.
13. **Postgres password contains `@`** — in `DATABASE_URL` it must be percent-encoded (`@` → `%40`); the `DB_PASSWORD` part stays literal because `database_dsn` applies `quote_plus`.
14. **Tests reuse the dev database by design** (user's choice, 2026-10-26) — no separate test DB. Isolation comes from `tests/conftest.py`: one connection per test, outer transaction + `join_transaction_mode="create_savepoint"`, rolled back at teardown, so repositories' `commit()` never escapes. Never add a fixture that opens its own engine/session outside that transaction, or it will leave rows in `AIRoast`. The suite also runs `alembic upgrade head` once at session start.
15. **`docker-compose.yml` would collide with the local server** — it maps port 5432 and defines `POSTGRES_DB=resume_roaster` / `postgres:postgres`. Since a local PostgreSQL already owns 5432 with `AIRoast` and the password in `backend/.env`, do not start the compose postgres service on this machine; migrations and auth use the local server via `DB_*`.
16. **bcrypt blocks the event loop (measured 2026-10-26)** — `verify_password` ≈ 271 ms, `hash_password` ≈ 258 ms on this machine, called synchronously inside `AuthService.login/register` (`async def`). One login therefore stalls the whole worker (~3.7 logins/sec ceiling) — health checks, SSE streams and other requests included. Use `await asyncio.to_thread(...)`; do not lower the bcrypt cost to hide it.
17. **Multi-worker logout needs Redis** — `InMemoryTokenDenylist` is per process. Today the backend runs a single uvicorn worker, so revocation is consistent; add a second worker and a logout in one process leaves the refresh token valid in the other. `RedisTokenDenylist` becomes mandatory before scaling workers.
18. **Pre-existing lint/format drift (not from this session)** — `ruff check .` flags `I001` in `app/ai/evaluators/culture_fit.py`, and `ruff format --check .` wants to reformat `app/ai/evaluators/culture_fit.py`, `app/ai/orchestrator.py`, `app/ai/prompts/evaluators/culture_fit.py`, `app/ai/scoring.py`, `app/schemas/evaluators.py`. All newly added/edited files pass both.

---

## 6. How to run locally

Everything runs through npm from the **repo root** — same workflow as Node projects:

```bash
npm run dev              # backend (8000) + frontend (3000) together, one terminal
npm run dev:backend      # backend only
npm run dev:frontend     # frontend only

npm run check            # lint + typecheck + build (both sides)
npm run check:backend    # ruff + mypy
npm run check:frontend   # eslint + next build

npm run setup            # one-time (fresh machine): install everything
npm run db:migrate --prefix backend   # apply migrations (users table)
npm test --prefix backend             # pytest (needs the Postgres in DB_*) — applies migrations itself
```

Then open **http://localhost:3000** (use localhost, not 127.0.0.1) and http://localhost:8000/docs for the API.
Stop with `Ctrl+C` in the terminal.

The backend scripts live in `backend/package.json` and use `backend/.venv` directly — poetry/PATH never involved. `backend/.venv` is to Python what `node_modules` is to Node.

**Frontend** (terminal 2):

```bash
cd frontend
npm run dev
# http://localhost:3000
```

**Checks before you claim done:**

```bash
cd backend  && poetry run ruff check . && poetry run mypy app/
cd frontend && npm run lint && npm run build
```

**Try the auth flow via UI:** open `http://localhost:3000/register`, create an account → you land on the dashboard.

---

## 7. File map (what lives where)

```
package.json                # root scripts: npm run dev / check / setup
backend/
├── package.json            # backend scripts (use .venv directly, no poetry needed)
├── .venv/                  # project-local Python env (like node_modules; gitignored)
├── poetry.toml             # pins virtualenvs.in-project = true
├── pyproject.toml            # deps + ruff/mypy config (B008 exempt for Depends)
├── .env / .env.example       # config; USER_STORE=postgres, DB_*, DEMO_USER_*
├── alembic.ini               # Alembic config (URL comes from settings, not here)
├── alembic/
│   ├── env.py                # async env; engine built from settings.database_dsn
│   └── versions/0001_create_users_table.py   # users table + unique email index
└── app/
    ├── main.py               # FastAPI app, CORS, AppException handler, /health, lifespan
    ├── config.py             # Settings (pydantic-settings) — single source of truth; database_dsn
    ├── db/
    │   ├── base.py           # DeclarativeBase
    │   ├── session.py        # async engine + session factory + dispose_engine
    │   └── seed.py           # seed_demo_user() — idempotent startup seeding
    ├── models/
    │   └── user.py           # UserModel (users table) — storage only
    ├── common/
    │   ├── exceptions.py     # AppException hierarchy (auth/parsing/AI/analysis)
    │   ├── logging.py        # setup_logging() + app_logger
    │   └── security.py       # bcrypt hash/verify, JWT create/decode
    ├── api/
    │   ├── deps.py           # get_db (AsyncSession), get_user_repo, get_auth_service, get_current_user, cookie helpers
    │   ├── schemas/auth.py   # RegisterRequest, LoginRequest, TokenResponse, UserResponse
    │   └── v1/
    │       ├── router.py     # aggregates v1 routers
    │       └── auth.py       # register/login/refresh/logout/me (HTTP + cookies only)
    └── services/
        ├── auth.py           # AuthService: register/login/refresh/revoke → AuthSession
        ├── token_denylist.py # TokenDenylist protocol + in-memory impl (logout revocation)
        └── user_repository.py# Protocol + InMemoryUserRepository + PostgresUserRepository + factory
└── tests/                    # pytest (real Postgres, per-test rollback)
    ├── conftest.py           # migrations + transactional fixtures + HTTP client + email factory
    ├── test_services/test_user_repository.py
    ├── test_services/test_auth_service.py
    ├── test_api/test_auth.py # 201/409/401/204, cookie flags, revoked-token replay
    └── test_db/test_seed.py  # demo seeding: creates + hashes, idempotent, skip when unconfigured
frontend/
├── package.json              # Next 16, TanStack Query, Zustand, Zod, recharts...
└── src/
    ├── app/                  # page.tsx (landing), (auth)/login|register, dashboard/, upload/
    ├── components/           # ui/ (shadcn), auth/ (forms), layout/Navbar, analysis/AnalysisCard
    ├── hooks/queries/        # use-auth.ts (register/login/logout/me + AuthError), use-analyses.ts; use-mounted.ts
    ├── lib/api-client.ts     # fetch wrapper: JWT header, 401→refresh→retry, credentials:include
    ├── providers/            # AppProviders (QueryClientProvider)
    ├── stores/auth-store.ts  # Zustand persisted auth state
    └── types/                # api.ts, resume.ts, analysis.ts (mirror backend schemas)
```

---

## 8. Update protocol (for the AI assistant)

At the end of **every** session (or user request):

1. Re-read this file first.
2. Do the work.
3. Update sections 1–5 (snapshot, done, next, blocked, issues) to reflect reality.
4. Add any new file paths to section 7.
5. Report what was verified (command + actual output), not what is assumed.
