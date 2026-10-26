# AGENTS.md — AI Resume Brutal Roaster

> This file is loaded into every OpenCode session for this project.
> It defines behavior that must hold **automatically** — no user reminding needed.

---

## Read first

Before writing any code, read these (in order):

0. `PROGRESS.md` — **current project state**: what's done, in progress, blocked, known issues, how to run, file map. This is the session entry point — read it before anything else and never rescan the whole repo to "figure out the state".
1. `AI_CONTEXT.md` — project overview, tech stack, architecture
2. `CONVENTIONS.md` — coding rules and standards (mandatory)
3. `PROJECT_PLAN.md` — implementation roadmap and module dependencies

Existing `CLAUDE.md` also applies (OpenCode reads it as a fallback), but this file takes precedence.

---

## Anti-hallucination rules (NON-NEGOTIABLE)

These exist because assistants routinely invent facts, APIs, file paths, and test results. Do not do that here.

### 1. Never assert something you have not verified in this session

- **File contents** — read the file before editing or quoting it. Never reconstruct from memory.
- **APIs / library behavior** — if unsure whether a function exists or how it behaves, check the source or docs; do not guess and present a guess as fact.
- **Command results** — a command's output is what it is. Do not summarize a command as "passed" without seeing its output.
- **Environment facts** — what is installed, what is configured — verify with a command, do not assume from the project docs.

### 2. Say "I don't know" instead of inventing

If a fact is not in the context you actually have, say so. A correct "I don't know" is always preferred over a confident wrong answer.

### 3. Verify before claiming success

- After writing code: run the relevant check (`ruff`, `mypy`, `pytest`) and **report the actual output**.
- If a check fails, say it failed. Do not describe it as passing.
- If a command is not available (e.g. `poetry` not installed), say so — do not narrate a fictional run.

### 4. Distinguish invented from real

When referencing a file path, function name, endpoint, or library API, it must correspond to something that exists in the repo or a documented dependency. Never propose a path like `app/services/foo.py` unless you have created it or confirmed it exists.

### 5. When the answer depends on external reality, say so

Examples: "Poetry is not installed on this machine" or "PostgreSQL is not running" are statements of observed fact. "The app is running on port 8000" is only true if you verified it in this session.

---

## Code standards

Follow `CONVENTIONS.md` exactly:

- **Type hints everywhere** — use `X | None`, never `Optional[X]`.
- **Pydantic v2** for all validation; `Field(description=...)` on AI schemas.
- **Ruff** formatting: 4-space indent, 88-char lines, double quotes, trailing commas.
- **Module boundaries** — routers = HTTP only; services = business logic; models = DB only; AI code = no HTTP/DB.
- **Never call AI providers directly** — always `app.ai.provider.call_ai()`.
- **Never hardcode prompts** — always load from `app/ai/prompts/`.
- **One logical change per commit.**

---

## Environment-portable code (NON-NEGOTIABLE)

Write code that runs **identically on local, dev, and prod**. Never write code that only works in one environment and "happens to work" elsewhere.

### 1. Never hardcode environment-specific values

- **No hardcoded ports, hosts, URLs, or paths.** Read them from config (`app/config.py`, pydantic-settings) or environment variables.
- **No hardcoded secrets.** API keys, JWT secrets, and DB credentials come from the environment — never from source.
- **No hardcoded model names.** `AI_MODEL` / `AI_FAST_MODEL` come from config; the provider is selected via `AI_PROVIDER`.

### 2. Configuration is the single source of truth

- One config object (`Settings`) loaded from `.env` / environment, injected where needed.
- Different environments differ **only** in their `.env` values — the code is the same.
- Use sensible defaults for local dev (e.g. `localhost:5432`), but never assume; let the env override.

### 3. Abstractions over concrete services

- **Storage:** always go through the `storage/` abstraction (local filesystem MVP, swappable to S3/R2 later). Never touch the filesystem directly in business logic.
- **AI:** always `app.ai.provider.call_ai()`. Never import `litellm` directly — swapping providers is a one-line env change.
- **Database:** use the async session via `get_db()`; never open a raw connection in services.

### 4. Environment detection is for behavior, not for code paths

- If you must branch on environment (e.g. enable debug logging), do it via `APP_ENV` from config — not by sniffing `os.name`, hostname, or "is this my laptop".
- **Never** write `if env == "local": do_X else: do_Y` for core logic. That's how prod breaks.

### 5. Paths and filesystems are relative to the app, not the cwd

- Resolve upload/storage paths relative to a configured `UPLOAD_DIR`, not `os.getcwd()`.
- Docker and local runs should produce identical file layouts.

### 6. Make it easy to verify portability

- After writing code, ask: "Does this break if `DATABASE_URL`, `REDIS_URL`, or `APP_ENV` changes?" If the answer is yes, it's not portable.
- Run `ruff check .` + `mypy app/` + `pytest` after every change — these catch env-specific assumptions (e.g. missing env vars) before prod.

---

## Resource & resilience (NON-NEGOTIABLE)

This project runs on **free/local AI models** with **limited CPU and memory**. Code must not break the live environment under load, and heavy tasks must never take the app down mid-request.

### 1. Free/local models only

- `AI_MODEL` / `AI_FAST_MODEL` come from config. The provider is selected via `AI_PROVIDER` — swapping providers is a **one-line env change**.
- Never hardcode a paid model name as the only option. Always configure a **fallback chain**: primary → fallback → emergency (degraded quality, still works).
- If a provider is unavailable or rate-limited, the fallback chain kicks in automatically. Never let a single provider failure crash a request.

### 2. Never block the event loop

FastAPI is async. Heavy **synchronous** work must never run inline in a request:

- **PDF/DOCX/OCR extraction** → run in a thread pool: `await asyncio.to_thread(extract_text, path)` or `loop.run_in_executor(None, ...)`.
- **AI calls** are already async via `call_ai()` — never wrap them in `asyncio.run` or call sync litellm.
- If you are tempted to write `time.sleep(...)` or a CPU-bound loop inside an `async def` handler, you are blocking the loop. Redo it.

### 3. Heavy work off the request path

The analysis pipeline is long (extract → parse → evaluate → score → compose). A client must **never wait for the full pipeline**:

- `POST /api/v1/analyses` returns **immediately** with an `analysis_id` (status `QUEUED`).
- Processing happens async. The client polls `GET /{id}/status` or streams `GET /{id}/stream` (SSE).
- Never make a request synchronous end-to-end. If a handler runs the whole pipeline, it will time out under load.

### 4. Graceful degradation under failure

- If an AI evaluator fails after retries → **skip it**, store a partial result, continue the others. Never let one failing evaluator abort the whole analysis.
- If the AI provider is entirely unavailable → return a degraded result with deterministic scores only (no AI feedback), status `PARTIAL`, not a 500.
- If OCR/extraction fails → raise `ResumeParsingError` and return a clean 4xx, not a raw traceback.
- **Never let raw Python tracebacks reach the API response.**

### 5. Resource limits

- Enforce `MAX_FILE_SIZE_MB` on upload. Reject oversized files before reading them into memory.
- Cap `max_tokens` on every AI call. Truncate the **resume data**, never the system prompt, when input exceeds the model's window.
- Stream large responses; never buffer a multi-MB AI response in memory before returning.
- Close file handles and DB sessions deterministically — DB sessions come from `get_db()` (auto-closed), and uploaded temp files are deleted after extraction.

### 6. Verify under constraint

- After writing code, ask: "Does this hold if the machine is CPU-constrained, the AI provider is slow, and 100 requests hit at once?" If the answer is no, it is not ready.
- Run `pytest` with mocked slow/failed AI providers — the pipeline must still complete or degrade, never hang.

---

## Timeout handling (NON-NEGOTIABLE)

If a client disconnects or hits a timeout (e.g. 1 minute), the work must **not** be lost. The server keeps going, and the result is still retrievable.

### 1. Never abort work when the client disconnects

- If the HTTP client times out or disconnects mid-request, the server must **continue** the background job to completion.
- The result is stored in the database. The client can poll and pick it up later.
- **Never** tie job completion to the request lifecycle — `BackgroundTasks` that finish the work are fine, but the durable state must be written regardless of whether anyone is still listening.

### 2. Distinguish fast endpoints from long endpoints

- **Fast endpoints** (auth, resume CRUD, status polls) must respond in well under 1 minute. If they don't, that's a bug — fix it, don't hide it.
- **Long endpoints** (full analysis pipeline) are allowed to take longer, but they must **never** be synchronous end-to-end. They return immediately with an ID; the client polls or streams.

### 3. Bound every external call

- **AI calls** — set a `timeout` on every `call_ai()` invocation. If it exceeds the limit, fail fast and fall back to the next model in the chain. Never hang a request on a slow provider.
- **Database calls** — use a reasonable connection/pool timeout. If the DB is slow, fail fast with a clean 5xx, not a hang.
- **Extraction** — bound the time spent on OCR/pdfplumber. If it exceeds a limit, return a clean `ResumeParsingError` (4xx), not a timeout.

### 4. Timeouts must degrade, not crash

- A timeout on one evaluator → skip it, store partial results, continue.
- A timeout on the whole provider → fall back to the emergency model or deterministic-only scoring.
- A timeout on the client side → the job still completes and is stored; the next poll returns the result.
- **Never** let a timeout produce a raw traceback or a half-written result.

### 5. Optimize aggressively, but correctly

- Cache where it's safe (parsed resume data, role context prompts).
- Run independent evaluators in parallel (`asyncio.gather`).
- Truncate resume data, not system prompts, when input is large.
- Prefer the fast model (`AI_FAST_MODEL`) for parsing and simple checks; reserve the heavy model for scoring and composition.
- But **never** trade correctness for speed in a way that produces wrong results — a fast wrong answer is worse than a slow right one.

---

## Testing

- **pytest + pytest-asyncio**, real PostgreSQL (never SQLite).
- Mock AI calls in unit tests — never hit real APIs.
- Test success **and** failure paths: validation errors, 401/403/404, ownership checks, empty/garbage input.
- Report actual test output. Do not summarize results you have not observed.

---

## Session protocol (NON-NEGOTIABLE)

Every session, without being asked or reminded:

1. **Read `PROGRESS.md` first** — it is the authoritative snapshot of the project state (done / in progress / blocked / known issues / run commands / file map).
2. **Do the work.**
3. **Update `PROGRESS.md` before finishing** — refresh the status snapshot, move items between done/in-progress/blocked, add newly discovered gotchas to the issues list, add new file paths to the file map. Do this even for small changes.
4. **Record what was verified** — list the commands you ran and their actual outcomes. Never write "it works" into `PROGRESS.md` unless you ran the check in that session.
5. If the user's request contradicts something in `PROGRESS.md`, trust the code you actually read, and fix `PROGRESS.md` — the tracker is a cache, the repo is the truth.

## Code quality (NON-NEGOTIABLE)

The code must be smart and easy to read. Before finishing any change:

### 1. Review your own code first
- Re-read every file you touched before claiming done. Fix naming, ordering, and duplication on the spot.
- Run `npm run check` (or the relevant side) and report the ACTUAL output. A failing check is reported as failing.

### 2. No dead code, no laziness
- No unused imports, variables, aliases, or "temp" files. If you create a helper, use it; if you stop using one, delete it.
- Define constants BEFORE the functions that use them. No hidden function-local imports unless a circular import forces it (and say why in a comment).
- No copy-pasted logic — extract one well-named function and reuse it (e.g. cookie handling lives in ONE place, not repeated per endpoint).

### 3. Naming must be honest
- Names state what things ARE or DO: `set_refresh_cookie`, `get_user_repository`, `AuthSession`. No vague `handle_stuff`, `data2`, `do_work`.
- One concept, one name, everywhere (frontend and backend): `refresh_token`, `access_token`, `analysis_type`.

### 4. Security code is held to a higher bar
- **Logout must actually invalidate the session** (denylist/revocation), not just delete a client-side artifact. Test the revoked token explicitly.
- Same error message for "unknown email" and "wrong password" (no account enumeration).
- Cookie flags deliberate: HttpOnly, SameSite=Lax, Secure in prod, path-scoped. Never extend cookie scope "to make it easier".
- Secrets/JWT config only from Settings/env — never hardcoded.
- Every auth endpoint verified with a real request (success AND failure) before claiming done.

### 5. Seam discipline for future infrastructure
- External stores (users, denylist, cache) sit behind a Protocol + factory selected by config (`user_store`, `denylist_store`). Swapping memory → postgres/redis must be a `.env` change plus ONE new implementation file — zero edits to services/routers.

### 6. No extra code
- Implement what was asked, completely — nothing half-wired, nothing speculative. No feature flags, abstractions, or "flexibility" for hypothetical future needs beyond rule 5.

## Working style

- Prefer the smallest correct change. Do not refactor unrelated code.
- Do not create documentation files (`.md`) unless explicitly asked.
- Do not commit unless explicitly asked.
- When a task is multi-step, use the todo list.