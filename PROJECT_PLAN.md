# Project Plan — AI Resume Brutal Roaster

> Track incremental progress. Each module is independent enough to work on separately.
> Mark `[x]` when done, `[~]` when in progress.

---

## Status Legend

- `[ ]` — Not started
- `[~]` — In progress
- `[x]` — Done

---

## Module 1: Project Foundation

> **Goal:** Working FastAPI skeleton with database, auth, and middleware.
> **Depends on:** Nothing (first module).
> **Deliverable:** `poetry run uvicorn app.main:app --reload` works, endpoints respond, DB connects.

### M1.1 — Project Scaffolding

- [x] Create `backend/` directory with `pyproject.toml` via `poetry init`
- [x] Install all backend dependencies (see `AI_CONTEXT.md`)
- [x] Create `app/__init__.py`, `app/main.py` (bare FastAPI app)
- [x] Create `app/config.py` with `pydantic-settings` (reads `.env`)
- [x] Add `.env` and `.env.example` (copy from root `.env.example` to `backend/`)
- [x] Verify app starts: `poetry run uvicorn app.main:app --reload --port 8000`
- [x] Verify docs at `http://localhost:8000/docs` (Swagger UI)



### M1.2 — Docker Infrastructure

- [x] Copy/move `docker-compose.yml` into `backend/` (or keep at root, update paths) — kept at root
- [ ] Verify PostgreSQL container starts (`pg_isready` healthcheck) — blocked: Docker not installed
- [ ] Verify Redis container starts (`redis-cli ping` healthcheck) — blocked: Docker not installed
- [x] Verify `DATABASE_URL` connection string works with `asyncpg` — verified against local PostgreSQL 18.3 (`AIRoast`); a container is not required
- [x] Create `app/common/logging.py` (basic structured logging setup)



### M1.3 — Database Setup

- [~] Create `app/models/base.py` — done as `app/db/base.py`; `DeclarativeBase` only, no UUID/timestamp mixin yet
- [x] Initialize Alembic: created `alembic/` + `alembic.ini` by hand (not `alembic init`)
- [x] Configure `alembic.ini` + `alembic/env.py` for async PostgreSQL
- [x] Create first migration — revision `0001` creates `users` (not an empty baseline)
- [x] Verify: `upgrade head` + `downgrade -1` roundtrip verified; `alembic check` reports no model/DB drift



### M1.4 — Database Models

- [x] `app/models/user.py` — User (id, email, name, password_hash, tier, timestamps)
- [x] `app/models/resume.py` — Resume (id, user_id FK, file_path, original_name, file_size, mime_type, raw_text, structured_data JSONB, parsing_status, parsing_errors JSONB, timestamps, deleted_at)
- [x] `app/models/analysis.py` — Analysis (id, user_id FK, resume_id FK, analysis_type, target_role, job_description, custom_instructions, status, error_message, prompt_versions_used JSONB, ai_model_used, processing_time_ms, timestamps)
- [x] `app/models/analysis.py` — AnalysisResult (id, analysis_id UNIQUE FK, all feedback JSONB columns, scores, final_roast, final_report JSONB, timestamps)
- [ ] `app/models/prompt_version.py` — PromptVersion — **intentionally skipped**: ARCHITECTURE.md keeps prompt versions as file constants for the MVP (table is V2)
- [x] `app/models/analysis_usage.py` — AnalysisUsage (id, user_id FK, analysis_id FK, ai_model, prompt_tokens, completion_tokens, cost_usd)
- [x] Add relationships to User model (resumes, analyses) — `lazy="raise"`, load explicitly with `selectinload`
- [x] Add relationships to Resume model (user, analyses)
- [x] Add relationships to Analysis model (user, resume, result)
- [x] Generate migration: revision `0002` creates `resumes`, `analyses`, `analysis_results`, `analysis_usage`
- [x] Verify migration applies and rolls back cleanly — both verified, plus `alembic check`



### M1.5 — JWT Authentication

- [x] `app/common/security.py` — `hash_password()`, `verify_password()`, `create_access_token()`, `create_refresh_token()`, `decode_token()`
- [x] `app/common/exceptions.py` — `AppException` base, `AuthenticationError`, `AuthorizationError`, `NotFound`, `ValidationError`
- [x] `app/api/deps.py` — `get_db()` async generator, `get_current_user()` dependency
- [x] `app/api/schemas/auth.py` — `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`
- [x] `app/services/auth.py` — `register()`, `login()`, `refresh_token()` (+ `revoke()` for logout)
- [x] `app/api/v1/auth.py` — Router: `POST /register`, `POST /login`, `POST /refresh` (+ `/logout`, `/me`)
- [x] `app/api/v1/router.py` — Aggregate v1 router, include auth
- [x] `app/main.py` — Register v1 router, configure CORS (allow `localhost:3000`)
- [x] Test: register a user, login, get JWT, call protected endpoint — 30-test pytest suite + curl against `AIRoast`



### M1.6 — Middleware

- [~] `app/common/middleware.py` — Rate limiting — **updated 2026-10-29**: per-tier daily cap (free 3 / pro 50 from settings, by `users.tier`) enforced in the analysis service + login brute-force throttle via `LoginThrottle`; slowapi burst limiting itself stays deferred (meaningful per-IP limits need Redis for multi-worker)
- [x] Add `CORSMiddleware` to `app/main.py` — now registered via `common/middleware.py::setup_middleware` together with logging
- [x] Add request logging middleware — `http_request method/path/status/duration_ms` per request + `X-Process-Time` response header
- [x] Add global exception handler for `AppException` → structured JSON error response
- [x] Verify: 429 asserted for login throttling; **per-tier cap asserted** (`test_daily_cap_is_per_tier`); **CORS asserted** (`test_middleware.py`: configured origin allowed, preflight OK, unknown origin rejected)



### M1.7 — Error Handling

- [x] `app/common/exceptions.py` — Full exception hierarchy:
  - `ResumeParsingError(reason, file_path)`
  - `AIEvaluationError(evaluator, reason)`
  - `AnalysisFailed(stage, reason)`
  - `InvalidFileError(file_type, reason)`
- [x] Global handler in `app/main.py` catches `AppException` → returns `{ "error": { "code", "message", "details" } }`
- [x] Verify: raise custom exception → returns proper JSON, not HTML traceback — 401/409 asserted in `tests/test_api/test_auth.py`

---



## Module 2: Resume Upload & Extraction

> **Goal:** Upload PDF/DOCX, extract raw text, handle OCR fallback.
> **Depends on:** Module 1 (database, auth, storage).
> **Deliverable:** `POST /api/v1/resumes/upload` extracts text, stores Resume record with `raw_text` populated.



### M2.1 — File Storage

- [x] `app/storage/base.py` — `Storage` protocol: `save()`, `delete()`, `get_path()`
- [x] `app/storage/local_storage.py` — Local filesystem: `UPLOAD_DIR/{user_id}/{uuid}.{ext}`, traversal-guarded
- [x] `app/api/deps.py` — Add `get_storage()` dependency (returns `LocalStorage` instance)
- [x] Verify: save a file, get back path, file exists on disk — covered by `tests/test_services/test_storage.py`



### M2.2 — PDF Extraction

- [x] `app/document_processing/pdf.py` — `extract_pdf(file_path) -> str`
  - Use `pdfplumber` to extract text
  - Handle multi-page documents
  - Handle tables (best-effort text extraction)
  - Return cleaned text string
- [x] Test with sample PDF: valid text extraction — generated in-memory PDF fixture



### M2.3 — DOCX Extraction

- [x] `app/document_processing/docx.py` — `extract_docx(file_path) -> str`
  - Use `python-docx` to extract paragraphs + tables
  - Preserve section ordering
  - Return cleaned text string
- [x] Test with sample DOCX: valid text extraction — paragraphs + tables in document order



### M2.4 — OCR Fallback

- [ ] `app/document_processing/ocr.py` — `extract_ocr(file_path) -> str` — **V2**: pytesseract/pdf2image are V2 deps; low-quality text currently raises a clean 422
  - Use `pytesseract` + `pdf2image` (for PDF → images → text)
  - Handle image-based PDFs
  - Return cleaned text string
- [ ] ⚠️ Windows prerequisite: Tesseract in PATH, Poppler in PATH
- [ ] Test: image-based PDF → valid text via OCR



### M2.5 — Text Quality Check

- [x] `app/document_processing/quality.py` — `validate_text(text) -> TextQuality`
  - Check: > 100 words? printable char ratio > 60%? not garbled?
  - Return: `{ is_valid, word_count, printable_ratio, confidence }`
- [x] Test: valid text, empty text, garbled text, short text



### M2.6 — Extractor Router

- [~] `app/document_processing/extractor.py` — Main entry point: `extract_text(file_path, mime_type) -> ExtractedText` (OCR fallback deferred to V2)
  - Route: `application/pdf` → pdfplumber
  - Route: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` → python-docx
  - After extraction, run quality check
  - If quality low (empty/garbled) → fallback to OCR
  - If OCR also fails → raise `ResumeParsingError`
  - Return: `{ raw_text, extraction_method, quality }`
- [~] Test: PDF works, DOCX works, garbage input fails cleanly (OCR fallback untested — V2)



### M2.7 — Resume Service

- [x] `app/services/resume.py` — `upload()`, `get()`, `list()`, `delete()` on `ResumeService`
  - Upload: validate MIME (python-magic), validate size (10MB), save file, create DB record, extract text, update record
  - Get: fetch by ID, ensure user owns it
  - List: fetch all for user, ordered by created_at desc
  - Delete: remove file + DB record
- [x] Test: upload PDF → DB record created, `raw_text` populated



### M2.8 — Resume API Endpoints

- [x] `app/api/schemas/resumes.py` — `ResumeResponse`, `ResumeDetailResponse`, `ResumeListResponse`
- [x] `app/api/v1/resumes.py` — Router:
  - `POST /upload` (201) — multipart upload
  - `GET /` — list user's resumes
  - `GET /{resume_id}` — get resume details
  - `DELETE /{resume_id}` — delete resume
- [x] Include in `app/api/v1/router.py`
- [x] Test: upload file via API → 201, list shows it, get returns details, delete removes it

---



## Module 3: AI Infrastructure

> **Goal:** litellm wrapper, prompt system, structured output schemas.
> **Depends on:** Module 1 (nothing AI-specific depends on Module 2).
> **Deliverable:** `call_ai()` works, prompts load from files, Pydantic validates AI output.



### M3.1 — AI Provider Wrapper

- [x] `app/ai/provider.py` — `call_ai(model, messages, response_model, max_retries) -> (result, usage)` — **done, adapted (2026-10-29)**: async `litellm.acompletion`, config from `Settings`, retries with backoff, structured outputs via `response_model`, returns `AIResult` (content + parsed data + token usage)
- [x] Fallback chain: primary → fallback → emergency (per `FALLBACK_CHAIN` in architecture) — primary → `AI_FAST_MODEL`, env-tunable (`ai_fallback_enabled`); proven live when gemini-3.8-flash timeouts fell back to the fast model
- [x] Test: mock litellm, verify retry logic, verify usage tracking — `tests/test_ai/test_provider.py` (8 tests: success/usage, structured validation, retry, fallback, exhaustion, missing-key fail-fast, local provider, missing usage)

### M3.2 — Prompt Composition System

- [~] `app/ai/prompts/__init__.py` — `load_prompt(module_path) -> str` helper — **adapted**: prompts are versioned Python modules (`VERSION` + `SYSTEM_PROMPT`) imported directly, no string loader
- [~] `app/ai/prompts/base.py` — Base system prompt — **adapted**: each evaluator/parser/composer owns its `SYSTEM_PROMPT` in `app/ai/prompts/`; no shared base prompt
- [~] Define `ComposedPrompt` dataclass: `{ system: str, user: str, schema: type }` — **adapted**: system prompt + user prompt composed in `evaluators/base.py`; the schema is appended as JSON-schema instructions by `call_ai(response_model=...)`
- [x] `compose_prompt(evaluator, resume_data, mode, target_role?, job_description?, custom_instructions?) -> ComposedPrompt` function — **adapted (2026-10-29)**: `compose_user_prompt(resume_data, context)` appends TARGET ROLE / JOB DESCRIPTION / USER FOCUS blocks; mode weights per mode in scoring
- [x] Verify: compose a prompt, see it as string, validate structure — `tests/test_ai/test_evaluators.py::test_compose_user_prompt_serializes_resume_as_json`

### M3.3 — AI Output Schemas

- [x] `app/schemas/resume.py` — `StructuredResume` model — **done, adapted field names** (contact_info/experience/education/skills/certifications/projects/languages; all `Field(description=...)`)
- [x] `app/schemas/evaluators.py` — All evaluator output schemas — **done, adapted**: categorical ratings (`excellent|good|fair|poor|missing`) instead of raw numbers, per ARCHITECTURE §13; fields differ from this list by design (see file)
- [x] All use `Field(description=...)` for every field (becomes part of prompt) — descriptions double as prompt guidance
- [x] All use `Literal` for enum-like fields (not custom Enum classes) — `QualityRating` + impression/credibility Literals
- [x] Test: validate with mock data, validate with bad data (should fail) — `tests/test_ai/test_evaluators.py` (valid payloads ×4; invalid/numeric/over-length rejected — verified live 2026-10-29)

### M3.4 — Resume Parser

- [x] `app/ai/parser.py` — `parse_resume(raw_text) -> StructuredResume` — on `AI_FAST_MODEL`, truncates input at 15k chars (never the system prompt)
- [x] `app/ai/prompts/parser.py` — Parser prompt + output schema reference (`PARSER_RESPONSE_MODEL`)
- [x] Handle: missing fields → empty defaults, extra fields → ignored — extraction-only rules in the prompt; Pydantic ignores unknown keys
- [x] Test: mock AI returning valid JSON → `StructuredResume` object — `tests/test_ai/test_parser.py` (4 tests)

### M3.5 — Token/Cost Tracking

- [x] Add `track_usage(user_id, analysis_id, model, usage)` to `AnalysisUsage` table — **adapted**: the pipeline writes one `AnalysisUsageModel` row per AI call (evaluators + composer) directly
- [x] Integrate into `call_ai()` provider wrapper — `AIResult` carries prompt/completion tokens; `compose_roast` returns its usage too
- [x] Calculate cost: `prompt_tokens * price + completion_tokens * price` — **done (2026-10-29)**: `ai_input_price_per_m` / `ai_output_price_per_m` settings (null = unpriced); `_cost_usd()` computes per call; tested
- [x] Test: mock call_ai, verify usage record created — `tests/test_services/test_analysis.py` (5 usage rows for 4 evaluators + composer)

---



## Module 4: Core Evaluation Pipeline

> **Goal:** 5 evaluators (Recruiter, ATS, Technical, Content Quality, Job Matcher), orchestrator, aggregator.
> **Depends on:** Module 3 (AI infrastructure).
> **Deliverable:** Given `StructuredResume`, run all evaluators in parallel, get aggregated results.



### M4.1 — Evaluator Base Pattern

- [x] `app/ai/evaluators/base.py` — **done, adapted**: `run_evaluator()` (prompt → AI call → validated output + usage) and `compose_user_prompt()`; one evaluator = one file, one function, one prompt (registry in `orchestrator.py`)
- [x] Define evaluator function signature protocol: `async def evaluator(resume_data, context) -> EvaluationResult` — adapted: `async def evaluator(resume_data) -> tuple[OutputModel, AIResult]` (usage flows to `analysis_usage`)
- [x] Document the pattern (one evaluator = one file, one function, one prompt) — docstrings in `base.py` + each evaluator

### M4.2 — Recruiter Evaluator

- [x] `app/ai/prompts/evaluators/recruiter.py` — System prompt + output schema ref — VERSION + SYSTEM_PROMPT (six-second scan, credibility, red flags)
- [x] `app/ai/evaluators/recruiter.py` — `run_recruiter_evaluator(resume_data) -> RecruiterEvaluation` — via shared `run_evaluator`, validated against `RecruiterEvaluatorOutput`
- [x] Test: mock AI → valid RecruiterEvaluation returned — `tests/test_ai/test_evaluators.py` (mocked `call_ai`, valid + no-data cases)

### M4.3 — ATS Evaluator

- [x] `app/ai/prompts/evaluators/ats.py` — System prompt
- [x] `app/ai/evaluators/ats.py` — `run_ats_evaluator(resume_data) -> ATSEvaluation` — **adapted hybrid**: AI judges parse readiness/formatting/missing keywords; the deterministic half (sections, contact, bullets, dates) lives in `scoring.py`'s checks, which run on `StructuredResume` without AI
- [x] Test: mock AI → valid ATSEvaluation

### M4.4 — Technical Evaluator

- [x] `app/ai/prompts/evaluators/technical.py` — System prompt
- [x] `app/ai/evaluators/technical.py` — `run_technical_evaluator(resume_data) -> TechnicalEvaluation`
- [x] Test: mock AI → valid TechnicalEvaluation

### M4.5 — Content Quality Evaluator

- [x] `app/ai/prompts/evaluators/content_quality.py` — System prompt
- [x] `app/ai/evaluators/content_quality.py` — `run_content_quality_evaluator(resume_data) -> ContentQualityEvaluation`
- [x] Test: mock AI → valid ContentQualityEvaluation

### M4.6 — Job Matcher Evaluator

- [x] `app/ai/prompts/evaluators/job_matcher.py` — System prompt — fit-only-against-context rules; role context from `prompts/roles/` appended for known slugs
- [x] `app/ai/evaluators/job_matcher.py` — `run_job_matcher_evaluator(resume_data, context) -> JobMatchEvaluation` — fails fast without target_role/jd context (no fabricated fit)
- [x] Test: mock AI → valid JobMatchEvaluation — orchestrator + aggregator + scoring tests cover it

### M4.7 — AI Orchestrator

- [x] `app/ai/orchestrator.py` — `run_evaluation(resume_data, analysis) -> dict` — **done, adapted**: `run_evaluations(resume_data, mode) -> EvaluatorResults` (outputs + failed + usage), `asyncio.gather(return_exceptions=True)`
- [x] If one fails → store partial result, continue others — failure recorded in `failed` with reason; scoring renormalizes (never scores zero); proven live (survived a 500 + 503 from Gemini)
- [x] Collect all results, pass to aggregator — `aggregator.aggregate_results(outputs, failed_names)`
- [x] General mode → Recruiter + ATS + Technical + Content Quality
- [x] Role-based mode → all above + Job Matcher — `target_role` reaches every prompt; role context appended for known slugs; role_based weights (§13) applied
- [x] JD-based mode → all above + Job Matcher — `job_description` in context; required at creation
- [x] Custom mode → all above + custom instructions injection — context reaches evaluators; composer gets "USER FOCUS".
- [x] Test: mock all evaluators, verify parallel execution, verify failure handling — `tests/test_ai/test_orchestrator.py` (all-succeed, single-failure, all-fail, unknown mode)

### M4.8 — Result Aggregator

- [x] `app/ai/aggregator.py` — `aggregate_results(evaluator_results) -> AggregatedResults` — deterministic merge; severity buckets: red flags → critical; credibility flags/gaps/formatting/clarity → warnings; generic phrasing + missing keywords → suggestions
- [x] Collect all evaluator outputs
- [x] Deduplicate observations across evaluators — whitespace/punctuation-insensitive key, per bucket
- [x] Organize: Critical Issues → Warnings → Suggestions → Positive Notes
- [x] Both perspectives coexist (recruiter says X, technical says Y) — items carry `source`
- [x] Return `AggregatedResults` with: `critical_issues[]`, `warnings[]`, `suggestions[]`, `positive_notes[]`, `evaluator_summaries{}` — plus `failed_evaluators[]`
- [x] Test: two evaluators with overlapping findings → deduplicated output — `tests/test_ai/test_aggregator.py`

---



## Module 5: Scoring + Roast Generation

> **Goal:** Hybrid scoring (deterministic + AI), final roast synthesis.
> **Depends on:** Module 4 (evaluator results).
> **Deliverable:** Score 0-100 with breakdown, final roast text.



### M5.1 — Deterministic Scoring Components

- [x] `app/scoring/score_calculator.py` — **done, adapted**: lives in `app/ai/scoring.py` per ARCHITECTURE §13 (no separate `scoring/` package). 8 checks implemented (vs the 11 sketched): section completeness 0–5, bullet points 0–5, word count 0–3, contact info 0–2, date consistency 0–3, quantified achievements 0–5, action verbs 0–5, formatting quality 0–5. Keyword density + length-appropriateness deferred (need role/JD context)
- [x] Each returns `{ score: int, max: int, details: str }` — adapted: `DeterministicCheck(name, score, max, details)`
- [x] Test: valid resume → scores make sense; empty resume → low scores — `tests/test_ai/test_scoring.py`

### M5.2 — Hybrid Scoring Engine

- [x] `app/ai/scoring.py` — `calculate_scores(aggregated_results, evaluator_outputs, mode) -> ScoringResult` — **done, adapted signature**: `calculate_scores(resume, raw_text, evaluator_outputs, failed_evaluators, mode)`
- [x] Deterministic: 50% of total
- [x] AI-assessed: 50% of total (from evaluator summaries) — from evaluator categorical ratings mapped to fixed bands (excellent 94 / good 78.5 / fair 57 / poor 32 / missing 9.5)
- [x] Mode-specific weights (from architecture: Content Quality, Experience, Skills Alignment, ATS, Role Relevance) — `MODE_WEIGHTS` (general wired; role/JD pending)
- [x] Partial-failure weight renormalization — failed categories dropped, surviving weights renormalized to 100%; deterministic-only fallback when all AI fails
- [x] Return: `{ overall_score: 0-100, breakdown: {...}, methodology: {...} }` — `ScoringResult` in `app/schemas/report.py`
- [x] Test: same inputs → same scores (deterministic part reproducible) — `test_determinism_same_inputs_same_score` + renormalization tests

### M5.3 — Roast Compositor

- [x] `app/ai/composer.py` — `compose_roast(aggregated_results, scores, context) -> str` — **done, adapted**: returns `(roast, fallback_used, usage)`; 200–350 word prose, quotes findings, no invention
- [x] Load composer prompt from `app/ai/prompts/composer.py` — VERSION + SYSTEM_PROMPT (persona + rules)
- [x] Feed aggregated results + scores — compact JSON within token budget (8 items/list, 160 chars/item)
- [x] Handle failure: return raw aggregated results as fallback — deterministic template; pipeline marks the analysis `partial`
- [x] Test: mock AI → valid roast text returned — `tests/test_ai/test_composer.py` (AI path, failure fallback, empty-response fallback, template never raises)

### M5.4 — Analysis Results Schema

- [x] `app/schemas/report.py` — `FinalReport` model — **done, adapted**: `AggregatedResults` + `AnalysisResultPayload` (assembled in the API layer from `analysis_results` columns)
- [x] `app/schemas/scoring.py` — `ScoringResult`, `ScoreBreakdown`, `ScoreMethodology` — **done, adapted**: `ScoringResult`, `DeterministicCheck`, `CategoryScore` in `app/schemas/report.py`
- [x] Verify: `AnalysisResult` JSONB columns match these schemas — pipeline writes `model_dump()` outputs; the API reads them back (`tests/test_services/test_analysis.py` round-trips the columns)

---



## Module 6: Analysis Module

> **Goal:** Full analysis pipeline: create → extract → parse → evaluate → score → compose → return.
> **Depends on:** Modules 2, 3, 4, 5.
> **Deliverable:** `POST /api/v1/analyses` runs complete pipeline, returns structured roast.



### M6.1 — Analysis Service

- [x] `app/services/analysis.py` — `create_analysis(user_id, resume_id, mode, options) -> Analysis` — ownership/soft-delete check (404), mode validation (only `general` wired → 400), daily cap from `settings.rate_limit_free` (429), inserts `queued`, schedules `run_pipeline` via `asyncio.create_task` (fire-and-forget per ARCHITECTURE §11 MVP — client disconnects never lose work)
- [x] Pipeline steps — **done, adapted**: `extracting → parsing → evaluating → scoring → composing → completed | partial | failed`; extraction reads the already-stored `raw_text` (upload extracted it); stages commit so status polls see progress
  1. Fetch resume → extract text (M2.6) — text already stored at upload; missing text → clean `failed`
  2. Parse resume via AI → `StructuredResume` (M3.4) — stored into `resume.structured_data["parsed"]`
  3. Run evaluators via orchestrator (M4.7)
  4. Aggregate results (M4.8)
  5. Calculate scores (M5.2)
  6. Compose roast (M5.3) — deterministic fallback on failure
  7. Store results in `AnalysisResult` — plus one `analysis_usage` row per AI call
  8. Return final report — via `GET /analyses/{id}` (background pipeline, not the request)
- [x] Track `processing_time_ms`, `ai_model_used`, `prompt_versions_used` — all recorded on the analysis row
- [x] On failure: set status `FAILED`, store `error_message` — `failed` with clean message; never a traceback
- [x] Test: mock all AI calls, verify full pipeline runs end-to-end — `tests/test_services/test_analysis.py` (success/partial/failure/no-text/roast-fallback) + live HTTP E2E verified 2026-10-29

### M6.2 — Analysis API Endpoints

- [x] `app/api/schemas/analyses.py` — `AnalysisCreateRequest`, `AnalysisResponse`, `AnalysisStatusResponse`, `AnalysisListResponse`, `AnalysisResultResponse` — adapted names: `AnalysisCreatedResponse`, `AnalysisListItemResponse`, `AnalysisStatusResponse`, `AnalysisDetailResponse` (+ `AnalysisResultPayload`)
- [x] `app/api/v1/analyses.py` — Router:
  - `POST /` (201) — create analysis, returns analysis_id — **done, adapted**: **202** `{analysis_id, status: "queued"}` per ARCHITECTURE §10
  - `GET /{analysis_id}` — full result
  - `GET /{analysis_id}/status` — status only (fast)
  - `GET /` — list user's analyses — paginated (`limit`/`offset`)
- [x] Include in `app/api/v1/router.py`
- [x] Test: create analysis → 201, poll status → complete, get result → full data — `tests/test_api/test_analyses.py` (202/404/400/401/429/list/status/detail); live E2E polled `parsing → evaluating → composing → completed`

### M6.3 — SSE Streaming (MVP)

- [x] `app/api/v1/analyses.py` — Add `GET /{analysis_id}/stream` endpoint — **done (2026-10-29)**: `StreamingResponse` SSE; ownership checked before streaming; heartbeat comments every 15s; idempotent (terminal state replays instantly); the stream is a viewer, not the executor
  - Return `StreamingResponse(media_type="text/event-stream")` — done
  - Yield events: `status` per stage, then `complete` (with score) or `error`
  - Each event: `{ step, state }` / `{ analysis_id, status, overall_score }` (adapted shapes)
- [x] Test: connect via `httpx` SSE client, verify events received — `test_stream_replays_terminal_state_immediately` + live curl verification

### M6.4 — General Mode

- [x] Wire `AnalysisType.GENERAL` → evaluators: Recruiter, ATS, Technical, Content Quality — `orchestrator._MODE_EVALUATORS["general"]`
- [x] Test: create general analysis → runs 4 evaluators, no job matcher — orchestrator + API tests

### M6.5 — Role-Based Mode

- [x] Wire `AnalysisType.ROLE_BASED` → all evaluators + Job Matcher — done 2026-10-29; verified live (score 70.69, job_match_feedback persisted)
- [x] Add `target_role` to context → role-specific prompts from `app/ai/prompts/roles/` — `ROLE_CONTEXT_PROMPTS` registry; known slugs append role context, unknown roles pass as text
- [x] Create role prompt files: `frontend_dev.py`, `backend_dev.py`, `fullstack_dev.py`, `ai_engineer.py`, `data_scientist.py`, `devops.py` — all eight roles now exist (incl. software_engineer, product_manager)
- [x] Test: create role-based analysis → runs all 5 evaluators — orchestrator tests + `test_role_based_pipeline_passes_context_and_persists_job_match` + live run

---



## Module 7: Prompt Management & Versioning

> **Goal:** All prompts versioned, tracked, reproducible.
> **Depends on:** Module 3 (prompt composition).
> **Deliverable:** Prompts stored in DB, analysis records track which version was used.



### M7.1 — Prompt Versioning

- [~] `app/services/prompt_service.py` — `get_active_prompt(key) -> PromptVersion` — **intentionally skipped for MVP**: prompts are versioned file constants (`VERSION` in every prompt module); the `prompt_versions` DB table is V2 (per ARCHITECTURE + PROGRESS gotcha 21). Do not "fix" by adding the table.
- [~] `sync_prompts_to_db()` — On startup, sync prompt files to `prompt_versions` table — same: skipped by design
- [x] Record `prompt_versions_used` in Analysis when creating — the pipeline records all six prompt versions on every analysis row
- [x] Verify: same resume analyzed twice with same prompts → identical results (deterministic portion) — `tests/test_ai/test_scoring.py::test_determinism_same_inputs_same_score`; identical prompts recorded in `analyses.prompt_versions_used`

---



## Module 8: Testing Infrastructure

> **Goal:** pytest setup, fixtures, test coverage for core modules.
> **Depends on:** Modules 1-6 (test what exists).
> **Deliverable:** `poetry run pytest` passes, CI-ready.



### M8.1 — Test Setup

- [x] Create `tests/conftest.py` — event loop fixture, async DB session fixture, `AsyncClient` fixture, auth fixtures (register + login helper) — **done, adapted**: real-Postgres per-test transaction rollback (`create_savepoint`), `session_factory`/`db_session`/`client`/`auth_headers`/`email_factory` fixtures; migrations applied by a session fixture
- [x] Create `tests/fixtures/` — `sample.pdf`, `sample.docx`, `sample_image.pdf`, `mock_structured_resume.json`, `mock_evaluator_results.json` — **done, adapted**: fixtures are generated in code (`docx_bytes_factory`, `pdf_bytes_factory`) and mock payloads live in the test files — no binary fixture files needed

### M8.2 — Unit Tests

- [x] `tests/test_document_processing/test_extraction.py` — PDF, DOCX, OCR, quality — OCR portion V2
- [x] `tests/test_scoring/test_score_calculator.py` — Each deterministic check — **adapted path**: `tests/test_ai/test_scoring.py`
- [x] `tests/test_schemas/test_evaluators.py` — Pydantic validation with valid + invalid data — **adapted path**: validation coverage inside `tests/test_ai/test_evaluators.py`
- [x] `tests/test_ai/test_provider.py` — Mock litellm, verify retry + usage tracking
- [x] `tests/test_services/test_resume.py` — Upload, extract, CRUD — **adapted path**: `tests/test_services/test_storage.py` + `tests/test_api/test_resumes.py`
- [x] `tests/test_services/test_analysis.py` — Full pipeline (mocked AI)

### M8.3 — API Tests

- [x] `tests/test_api/test_auth.py` — Register, login, refresh, invalid credentials — plus throttle tests (`test_auth_throttle.py`) and non-blocking-auth tests
- [x] `tests/test_api/test_resumes.py` — Upload, list, get, delete, invalid file type
- [x] `tests/test_api/test_analyses.py` — Create, get, status, list

### M8.4 — Integration Tests

- [x] `tests/test_integration/test_full_pipeline.py` — Mark `@pytest.mark.integration` — **done (2026-10-29)**: opt-in via `RUN_INTEGRATION=1` + `GEMINI_API_KEY`; asserts completed/partial + score bounds + roast length + 5 usage rows
  - Real resume → real AI calls — models: `gemini-3.5-flash` / `flash-lite`
  - Verify: text extracted → structured resume → evaluators → scores → roast
- [x] Only run explicitly: `RUN_INTEGRATION=1 npm test --prefix backend` — skips silently otherwise (1 skipped in normal runs)

---



## Module 9: Frontend Foundation

> **Goal:** Next.js app running, auth flow working, layout structure in place.
> **Depends on:** Module 1 (backend auth endpoints available).
> **Deliverable:** User can register/login, sees dashboard layout.



### M9.1 — Next.js Scaffolding

- [x] `npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir` (Next 16.3.7, current @latest)
- [x] `npx shadcn@latest init` (radix base, nova preset — new shadcn v4 CLI)
- [x] Add shadcn components: button, card, input, label, textarea, select, badge, progress, tabs, skeleton, dialog, dropdown-menu, sonner
- [x] Add npm deps: `@tanstack/react-query`, `@tanstack/react-query-devtools`, `zustand`, `zod`, `react-dropzone`, `recharts`, `lucide-react`, `sonner`
- [x] Create `src/providers/app-providers.tsx` — `QueryClientProvider` wrapper
- [x] Wrap root layout with `<AppProviders>`



### M9.2 — API Client + Auth Store

- [x] `src/lib/api-client.ts` — Fetch wrapper: inject JWT header, handle 401 → refresh, base URL from env
- [x] `src/stores/auth-store.ts` — Zustand: `token`, `user`, `setAuth()`, `clearAuth()` (persist to localStorage)
- [x] `src/hooks/queries/use-auth.ts` — `useLogin()` mutation, `useRegister()` mutation (`useCurrentUser()` pending backend `/auth/me` contract)
- [x] Test: login → token stored → API calls include header → logout clears — backend auth curl/pytest verified; **browser walkthrough verified 2026-10-28/29** (login via UI, dashboard guard, logout)



### M9.3 — Landing Page

- [x] `src/app/page.tsx` — Hero section, features, CTA → dashboard button if logged in
- [x] `src/components/layout/Navbar.tsx` — Logo, nav links, auth buttons, logout (user dropdown deferred)



### M9.4 — Auth Pages

- [x] `src/app/(auth)/login/page.tsx` — Email + password form, redirect to `/dashboard` on success
- [x] `src/app/(auth)/register/page.tsx` — Name + email + password form, redirect to `/dashboard` on success
- [x] `src/components/auth/LoginForm.tsx` — Form validation with zod, error handling, loading state
- [x] `src/components/auth/RegisterForm.tsx`



### M9.5 — Dashboard Layout

- [x] `src/app/dashboard/layout.tsx` — Sidebar nav (Upload, History), main content area + client-side auth guard
- [x] `src/app/dashboard/page.tsx` — List of user's analyses (cards), status badges, timestamps
- [x] `src/hooks/queries/use-analyses.ts` — `useAnalyses()` query, `useAnalysis(id)` query
- [x] `src/components/analysis/AnalysisCard.tsx` — Title, status badge, date, actions (score shown once backend returns it)

---



## Module 10: Frontend Features

> **Goal:** Upload flow, analysis creation, results display with streaming.
> **Depends on:** Module 9 (frontend foundation) + Modules 2-6 (backend endpoints).
> **Deliverable:** Full user flow: upload → configure → view roast + scores.



### M10.1 — Resume Upload

- [x] `src/app/upload/page.tsx` — Multi-step wizard: Upload → Configure → Submit — **done, adapted (2026-10-29)**: single-step with auto-roast (user decision — confirm-step option was declined); glass dropzone + file chip + gradient CTA + toast hand-off
- [x] `src/components/upload/ResumeDropzone.tsx` — Drag-and-drop zone, file validation (PDF/DOCX, 10MB), progress indicator — react-dropzone; animated ember border on drag
- [x] `src/hooks/mutations/use-upload.ts` — `useUploadResume()` mutation
- [x] `src/types/resume.ts` — TypeScript types matching backend `ResumeResponse` (+ `ResumeListResponse`)
- [x] Test: upload file → success toast → resume ID stored for next step — curl-verified 201 flow; toast fires on roast start; browser rendering verified (IAB cannot set files)

### M10.2 — Analysis Configuration

- [x] `src/components/upload/ModeSelector.tsx` — **done, adapted (2026-10-29)**: inline 4-mode selector on the upload page (glass radio tiles with hints), default General — auto-roast kept, choosing a mode replaces the default
- [x] `src/components/upload/RoleSelector.tsx` — **adapted**: role dropdown (8 roles) shown for role_based
- [x] `src/components/upload/JdInput.tsx` — **adapted**: JD textarea (5000-char cap) shown for jd_based
- [x] `src/components/upload/CustomInstructions.tsx` — **adapted**: focus textarea (500-char cap) shown for custom
- [ ] `src/hooks/mutations/use-start-analysis.ts` — `useStartAnalysis()` mutation (POST to `/analyses`) — **done**: exists at `src/hooks/mutations/use-start-analysis.ts`
- [x] On submit → redirect to `/analysis/[id]` — upload success → `POST /analyses` → `router.push(/analysis/[id])`

### M10.3 — Analysis Result View

- [x] `src/app/analysis/[id]/page.tsx` — Full roast dashboard
- [x] `src/components/analysis/ScoreRing.tsx` — Circular score display (0-100), color-coded — **adapted path**: `score-ring.tsx` (animated SVG arc)
- [x] `src/components/analysis/ScoreBreakdown.tsx` — Bar chart or radar chart (recharts) showing sub-scores — **adapted**: `Breakdown` inside `RoastResult.tsx` (animated category bars + deterministic check list; radar chart not needed)
- [x] `src/components/analysis/FeedbackCard.tsx` — Evaluator summary with expand/collapse — **adapted**: "Expert verdicts" grid in `RoastResult.tsx`
- [x] `src/components/analysis/CriticalIssueList.tsx` — Issues with severity badges, improvement suggestions — **adapted**: `FindingsList` (critical/warnings/fix-these) in `RoastResult.tsx`
- [x] `src/components/analysis/RoastDisplay.tsx` — Final roast text (markdown-like formatting) — **adapted**: ember glass roast card in `RoastResult.tsx`
- [x] `src/app/analysis/[id]/loading.tsx` — Skeleton loading state — **adapted**: in-page skeleton branch (no separate loading.tsx)
- [x] `src/types/analysis.ts` — TypeScript types matching backend `AnalysisResultResponse`

### M10.4 — Streaming Display

- [x] `src/hooks/use-analysis-stream.ts` — Custom hook consuming SSE from `/analyses/{id}/stream` — **done (2026-10-29)**: fetch-based stream reader (EventSource cannot send JWT headers), parses status/complete/error events, aborts cleanly; wired into the result page with polling as automatic fallback (`useAnalysis(id, { poll: !streamActive })`)
- [x] `src/components/analysis/StreamingStatus.tsx` — Pipeline step progress (Extracting → Parsing → Evaluating → Scoring → Composing → Done) — **adapted**: `StageProgress.tsx` (animated flame, spring ember progress bar, per-stage check/spinner)
- [x] Show animated progress bar with step labels
- [x] On `complete` event → refetch full analysis result, show results — polling refetches and the page transitions without reload (browser-verified)

### M10.5 — Analysis History

- [x] `src/app/dashboard/page.tsx` — Table/card list of all analyses — **done, adapted**: Overview bento (stats + latest roast + recent roasts) and a dedicated `/history` page with Roasts/Resumes tabs
- [x] Status badges: Queued, Processing, Complete, Failed — lowercase statuses matching the backend (queued/…/completed/partial/failed)
- [x] Quick view: resume name, mode, score, date — `AnalysisCard` (mode, score ring, status, date)
- [x] Click → navigate to `/analysis/[id]`

### M10.6 — Error & Empty States

- [x] `src/components/shared/ErrorState.tsx` — Retry button, error message
- [x] `src/components/shared/EmptyState.tsx` — No analyses yet, CTA to upload
- [~] `src/components/shared/Loader.tsx` — Full-page or inline loader — **adapted**: skeleton branches + `StageProgress` cover loading; no separate Loader component
- [x] Toast notifications for success/error via `sonner` — Toaster mounted; roast-start toast live

---



## Module 11: Polish & Deploy

> **Goal:** Production-ready, Dockerfile, deployed.
> **Depends on:** All previous modules.
> **Deliverable:** Live deployment.



### M11.1 — Docker Production

- [ ] `backend/Dockerfile` — Multi-stage build (build → runtime)
- [ ] `frontend/Dockerfile` — Multi-stage build (build → nginx or standalone)
- [ ] Root `docker-compose.yml` — Add app service (backend + frontend) alongside postgres + redis
- [ ] Production `.env` template



### M11.2 — Deployment

- [ ] Deploy backend: Railway / Render / Fly.io
- [ ] Deploy frontend: Vercel
- [ ] Set environment variables in deployment platforms
- [ ] Verify: CORS works, API calls from frontend succeed



### M11.3 — Final Polish

- [ ] Loading states on all async pages
- [ ] Error boundaries on key routes
- [ ] 404 page
- [ ] Responsive design pass (mobile upload flow)
- [ ] README.md with setup instructions

---



## Dependency Graph

```
Module 1 (Foundation)
    ├── Module 2 (Resume Upload)
    │       └── Module 6 (Analysis Service) ──┐
    ├── Module 3 (AI Infrastructure)          │
    │       ├── Module 4 (Evaluators) ──┐     │
    │       │       └── Module 5 (Scoring)──┘ │
    │       └── Module 7 (Prompt Versioning)  │
    └── Module 8 (Tests)                      │
                                              │
Module 9 (Frontend Foundation) ──────────────►│
    └── Module 10 (Frontend Features) ────────┘
        └── Module 11 (Polish & Deploy)
```

---



## Suggested Work Order


| Sprint   | Modules                                        | Days (est.) |
| -------- | ---------------------------------------------- | ----------- |
| Sprint 1 | M1 (Foundation)                                | 3-4         |
| Sprint 2 | M2 (Resume Upload) + M3 (AI Infra)             | 4-5         |
| Sprint 3 | M4 (Evaluators) + M5 (Scoring)                 | 5-6         |
| Sprint 4 | M6 (Analysis Service) + M7 (Prompt Versioning) | 3-4         |
| Sprint 5 | M8 (Tests) + M9 (Frontend Foundation)          | 4-5         |
| Sprint 6 | M10 (Frontend Features)                        | 5-6         |
| Sprint 7 | M11 (Polish & Deploy)                          | 2-3         |


**Total estimated: 26-33 working days** (varies by pace and scope).

---

*Plan created from ARCHITECTURE.md v2.0. Update status checkboxes as work progresses.*