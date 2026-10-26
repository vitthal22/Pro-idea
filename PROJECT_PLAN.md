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
- [~] Verify: `upgrade head` verified; `downgrade -1` roundtrip not exercised yet



### M1.4 — Database Models

- [x] `app/models/user.py` — User (id, email, name, password_hash, tier, timestamps)
- [ ] `app/models/resume.py` — Resume (id, user_id FK, file_path, original_name, file_size, mime_type, raw_text, structured_data JSONB, parsing_status, parsing_errors JSONB, timestamps)
- [ ] `app/models/analysis.py` — Analysis (id, user_id FK, resume_id FK, analysis_type, target_role, job_description, custom_instructions, status, error_message, prompt_versions_used JSONB, ai_model_used, processing_time_ms, timestamps)
- [ ] `app/models/analysis.py` — AnalysisResult (id, analysis_id UNIQUE FK, all feedback JSONB columns, scores, final_roast, final_report JSONB, timestamps)
- [ ] `app/models/prompt_version.py` — PromptVersion (id, prompt_key, version, content, schema_hash)
- [ ] `app/models/analysis_usage.py` — AnalysisUsage (id, user_id FK, analysis_id FK, ai_model, tokens, cost_usd)
- [ ] Add relationships to User model (resumes list, analyses list)
- [ ] Add relationships to Resume model (user, analyses list)
- [ ] Add relationships to Analysis model (user, resume, result)
- [~] Generate migration: revision `0001` covers `users` only; the rest arrive with their models
- [~] Verify migration applies (verified) and rolls back (not exercised yet)



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

- [ ] `app/common/middleware.py` — Rate limiting with `slowapi` (3/day free, 50/day pro)
- [x] Add `CORSMiddleware` to `app/main.py`
- [ ] Add request logging middleware
- [x] Add global exception handler for `AppException` → structured JSON error response
- [~] Verify: CORS configured (headers not explicitly asserted); no 429 yet — rate limiting not implemented



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

- [ ] `app/storage/base_storage.py` — Abstract base: `save()`, `delete()`, `get_path()`
- [ ] `app/storage/local_storage.py` — Local filesystem: `uploads/{user_id}/{uuid}.{ext}`
- [ ] `app/api/deps.py` — Add `get_storage()` dependency (returns `LocalStorage` instance)
- [ ] Verify: save a file, get back path, file exists on disk



### M2.2 — PDF Extraction

- [ ] `app/document_processing/pdf.py` — `extract_pdf(file_path) -> str`
  - Use `pdfplumber` to extract text
  - Handle multi-page documents
  - Handle tables (best-effort text extraction)
  - Return cleaned text string
- [ ] Test with sample PDF: valid text extraction



### M2.3 — DOCX Extraction

- [ ] `app/document_processing/docx.py` — `extract_docx(file_path) -> str`
  - Use `python-docx` to extract paragraphs + tables
  - Preserve section ordering
  - Return cleaned text string
- [ ] Test with sample DOCX: valid text extraction



### M2.4 — OCR Fallback

- [ ] `app/document_processing/ocr.py` — `extract_ocr(file_path) -> str`
  - Use `pytesseract` + `pdf2image` (for PDF → images → text)
  - Handle image-based PDFs
  - Return cleaned text string
- [ ] ⚠️ Windows prerequisite: Tesseract in PATH, Poppler in PATH
- [ ] Test: image-based PDF → valid text via OCR



### M2.5 — Text Quality Check

- [ ] `app/document_processing/quality.py` — `validate_text(text) -> TextQualityResult`
  - Check: > 100 words? printable char ratio > 60%? not garbled?
  - Return: `{ is_valid, word_count, printable_ratio, confidence }`
- [ ] Test: valid text, empty text, garbled text, short text



### M2.6 — Extractor Router

- [ ] `app/document_processing/extractor.py` — Main entry point: `extract_text(file_path, mime_type) -> ExtractedText`
  - Route: `application/pdf` → pdfplumber
  - Route: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` → python-docx
  - After extraction, run quality check
  - If quality low (empty/garbled) → fallback to OCR
  - If OCR also fails → raise `ResumeParsingError`
  - Return: `{ raw_text, extraction_method, quality }`
- [ ] Test: PDF works, DOCX works, OCR fallback triggers, garbage input fails cleanly



### M2.7 — Resume Service

- [ ] `app/services/resume.py` — `upload_resume()`, `get_resume()`, `list_resumes()`, `delete_resume()`
  - Upload: validate MIME (python-magic), validate size (10MB), save file, create DB record, extract text, update record
  - Get: fetch by ID, ensure user owns it
  - List: fetch all for user, ordered by created_at desc
  - Delete: remove file + DB record
- [ ] Test: upload PDF → DB record created, `raw_text` populated



### M2.8 — Resume API Endpoints

- [ ] `app/api/schemas/resumes.py` — `ResumeUploadResponse`, `ResumeResponse`, `ResumeListResponse`
- [ ] `app/api/v1/resumes.py` — Router:
  - `POST /upload` (201) — multipart upload
  - `GET /` — list user's resumes
  - `GET /{resume_id}` — get resume details
  - `DELETE /{resume_id}` — delete resume
- [ ] Include in `app/api/v1/router.py`
- [ ] Test: upload file via API → 201, list shows it, get returns details, delete removes it

---



## Module 3: AI Infrastructure

> **Goal:** litellm wrapper, prompt system, structured output schemas.
> **Depends on:** Module 1 (nothing AI-specific depends on Module 2).
> **Deliverable:** `call_ai()` works, prompts load from files, Pydantic validates AI output.



### M3.1 — AI Provider Wrapper

- [ ] `app/ai/provider.py` — `call_ai(model, messages, response_model, max_retries) -> (result, usage)`
  - Wraps `litellm.acompletion()`
  - Handles retries (exponential backoff)
  - Handles rate limits (litellm built-in)
  - Returns structured Pydantic result + token usage dict
  - Logs model, tokens, cost
- [ ] Fallback chain: primary → fallback → emergency (per `FALLBACK_CHAIN` in architecture)
- [ ] Test: mock litellm, verify retry logic, verify usage tracking



### M3.2 — Prompt Composition System

- [ ] `app/ai/prompts/__init__.py` — `load_prompt(module_path) -> str` helper
- [ ] `app/ai/prompts/base.py` — Base system prompt (the "you are an expert resume analyst" context)
- [ ] Define `ComposedPrompt` dataclass: `{ system: str, user: str, schema: type }`
- [ ] `compose_prompt(evaluator, resume_data, mode, target_role?, job_description?, custom_instructions?) -> ComposedPrompt` function
- [ ] Verify: compose a prompt, see it as string, validate structure



### M3.3 — AI Output Schemas

- [ ] `app/schemas/resume.py` — `StructuredResume` model (all fields: contact_info, summary, experience[], education[], skills[], certifications[], projects[], languages[], etc.)
- [ ] `app/schemas/evaluators.py` — All evaluator output schemas:
  - `CriticalIssue` (title, description, category, severity, improvement, recruiter_perspective)
  - `RecruiterEvaluation` (summary, first_impression, critical_issues[], strengths[], hire_recommendation)
  - `ATSEvaluation` (summary, keyword_analysis, ats_score, section_completeness, formatting_issues[])
  - `TechnicalEvaluation` (summary, tech_stack_assessment, relevance_score, gaps[], strengths[])
  - `ContentQualityEvaluation` (summary, writing_quality, generic_language_issues[], quantification_score)
  - `JobMatchEvaluation` (summary, match_score, alignment{}, gaps[], recommendations[])
- [ ] All use `Field(description=...)` for every field (becomes part of prompt)
- [ ] All use `Literal` for enum-like fields (not custom Enum classes)
- [ ] Test: validate with mock data, validate with bad data (should fail)



### M3.4 — Resume Parser

- [ ] `app/ai/parser.py` — `parse_resume(raw_text) -> StructuredResume`
  - Compose parser prompt from `app/ai/prompts/parser.py`
  - Call AI via `call_ai()` with `StructuredResume` as response_model
  - Return parsed resume
- [ ] `app/ai/prompts/parser.py` — Parser prompt + output schema reference
- [ ] Handle: missing fields → empty defaults, extra fields → ignored
- [ ] Test: mock AI returning valid JSON → `StructuredResume` object



### M3.5 — Token/Cost Tracking

- [ ] Add `track_usage(user_id, analysis_id, model, usage)` to `AnalysisUsage` table
- [ ] Integrate into `call_ai()` provider wrapper
- [ ] Calculate cost: `prompt_tokens * price + completion_tokens * price`
- [ ] Test: mock call_ai, verify usage record created

---



## Module 4: Core Evaluation Pipeline

> **Goal:** 5 evaluators (Recruiter, ATS, Technical, Content Quality, Job Matcher), orchestrator, aggregator.
> **Depends on:** Module 3 (AI infrastructure).
> **Deliverable:** Given `StructuredResume`, run all evaluators in parallel, get aggregated results.



### M4.1 — Evaluator Base Pattern

- [ ] `app/ai/evaluators/base.py` — Define `EvaluationContext` dataclass (model, mode, target_role?, job_description?, custom_instructions?)
- [ ] Define evaluator function signature protocol: `async def evaluator(resume_data, context) -> EvaluationResult`
- [ ] Document the pattern (one evaluator = one file, one function, one prompt)



### M4.2 — Recruiter Evaluator

- [ ] `app/ai/prompts/evaluators/recruiter.py` — System prompt + output schema ref
- [ ] `app/ai/evaluators/recruiter.py` — `run_recruiter_evaluator(resume_data, context) -> RecruiterEvaluation`
  - Loads prompt, composes messages, calls AI, validates output
- [ ] Test: mock AI → valid RecruiterEvaluation returned



### M4.3 — ATS Evaluator

- [ ] `app/ai/prompts/evaluators/ats.py` — System prompt
- [ ] `app/ai/evaluators/ats.py` — `run_ats_evaluator(resume_data, context) -> ATSEvaluation`
  - Hybrid: mostly deterministic keyword matching + AI for overall impression
- [ ] Test: mock AI → valid ATSEvaluation



### M4.4 — Technical Evaluator

- [ ] `app/ai/prompts/evaluators/technical.py` — System prompt
- [ ] `app/ai/evaluators/technical.py` — `run_technical_evaluator(resume_data, context) -> TechnicalEvaluation`
- [ ] Test: mock AI → valid TechnicalEvaluation



### M4.5 — Content Quality Evaluator

- [ ] `app/ai/prompts/evaluators/content_quality.py` — System prompt
- [ ] `app/ai/evaluators/content_quality.py` — `run_content_quality_evaluator(resume_data, context) -> ContentQualityEvaluation`
- [ ] Test: mock AI → valid ContentQualityEvaluation



### M4.6 — Job Matcher Evaluator

- [ ] `app/ai/prompts/evaluators/job_matcher.py` — System prompt
- [ ] `app/ai/evaluators/job_matcher.py` — `run_job_matcher_evaluator(resume_data, context) -> JobMatchEvaluation`
- [ ] Test: mock AI → valid JobMatchEvaluation



### M4.7 — AI Orchestrator

- [ ] `app/ai/orchestrator.py` — `run_evaluation(resume_data, analysis) -> dict`
  - Determine which evaluators to run based on `analysis_type`
  - Run evaluators in parallel via `asyncio.gather(return_exceptions=True)`
  - If one fails → store partial result, continue others
  - Collect all results, pass to aggregator
- [ ] General mode → Recruiter + ATS + Technical + Content Quality
- [ ] Role-based mode → all above + Job Matcher
- [ ] JD-based mode → all above + Job Matcher
- [ ] Custom mode → all above + custom instructions injection
- [ ] Test: mock all evaluators, verify parallel execution, verify failure handling



### M4.8 — Result Aggregator

- [ ] `app/ai/aggregator.py` — `aggregate_results(evaluator_results) -> AggregatedResults`
  - Collect all evaluator outputs
  - Deduplicate observations across evaluators
  - Organize: Critical Issues → Warnings → Suggestions → Positive Notes
  - Both perspectives coexist (recruiter says X, technical says Y)
- [ ] Return `AggregatedResults` with: `critical_issues[]`, `warnings[]`, `suggestions[]`, `positive_notes[]`, `evaluator_summaries{}`
- [ ] Test: two evaluators with overlapping findings → deduplicated output

---



## Module 5: Scoring + Roast Generation

> **Goal:** Hybrid scoring (deterministic + AI), final roast synthesis.
> **Depends on:** Module 4 (evaluator results).
> **Deliverable:** Score 0-100 with breakdown, final roast text.



### M5.1 — Deterministic Scoring Components

- [ ] `app/scoring/score_calculator.py` — Individual checks:
  - `score_section_completeness(structured_resume) -> 0-5`
  - `score_bullet_points(structured_resume) -> 0-5`
  - `score_word_count(structured_resume) -> 0-3`
  - `score_keyword_density(structured_resume, context) -> 0-5`
  - `score_formatting(structured_resume) -> 0-5`
  - `score_contact_info(structured_resume) -> 0-2`
  - `score_date_consistency(structured_resume) -> 0-3`
  - `score_quantified_achievements(structured_resume) -> 0-5`
  - `score_action_verbs(structured_resume) -> 0-5`
  - `score_redundancy(structured_resume) -> 0-5`
  - `score_length_appropriateness(structured_resume) -> 0-5`
- [ ] Each returns `{ score: int, max: int, details: str }`
- [ ] Test: valid resume → scores make sense; empty resume → low scores



### M5.2 — Hybrid Scoring Engine

- [ ] `app/ai/scoring.py` — `calculate_scores(aggregated_results, evaluator_outputs, mode) -> ScoringResult`
  - Deterministic: 50% of total
  - AI-assessed: 50% of total (from evaluator summaries)
  - Mode-specific weights (from architecture: Content Quality, Experience, Skills Alignment, ATS, Role Relevance)
- [ ] Return: `{ overall_score: 0-100, breakdown: {...}, methodology: {...} }`
- [ ] Test: same inputs → same scores (deterministic part reproducible)



### M5.3 — Roast Compositor

- [ ] `app/ai/composer.py` — `compose_roast(aggregated_results, scores, context) -> str`
  - Load composer prompt from `app/ai/prompts/composer.py`
  - Feed aggregated results + scores
  - AI synthesizes constructive roast
  - Handle failure: return raw aggregated results as fallback
- [ ] `app/ai/prompts/composer.py` — Composer prompt (tone: brutally honest + constructive)
- [ ] Test: mock AI → valid roast text returned



### M5.4 — Analysis Results Schema

- [ ] `app/schemas/report.py` — `FinalReport` model (overall_score, breakdown, critical_issues[], warnings[], suggestions[], positive_notes[], final_roast, metadata)
- [ ] `app/schemas/scoring.py` — `ScoringResult`, `ScoreBreakdown`, `ScoreMethodology`
- [ ] Verify: `AnalysisResult` JSONB columns match these schemas

---



## Module 6: Analysis Module

> **Goal:** Full analysis pipeline: create → extract → parse → evaluate → score → compose → return.
> **Depends on:** Modules 2, 3, 4, 5.
> **Deliverable:** `POST /api/v1/analyses` runs complete pipeline, returns structured roast.



### M6.1 — Analysis Service

- [ ] `app/services/analysis.py` — `create_analysis(user_id, resume_id, mode, options) -> Analysis`
  - Create DB record with status `QUEUED`
  - Trigger pipeline (sync for MVP)
  - Update status through: `EXTRACTING` → `PARSING` → `EVALUATING` → `SCORING` → `COMPOSING` → `COMPLETE`
  - On failure: set status `FAILED`, store `error_message`
- [ ] Pipeline steps:
  1. Fetch resume → extract text (M2.6)
  2. Parse resume via AI → `StructuredResume` (M3.4)
  3. Run evaluators via orchestrator (M4.7)
  4. Aggregate results (M4.8)
  5. Calculate scores (M5.2)
  6. Compose roast (M5.3)
  7. Store results in `AnalysisResult`
  8. Return final report
- [ ] Track `processing_time_ms`, `ai_model_used`, `prompt_versions_used`
- [ ] Test: mock all AI calls, verify full pipeline runs end-to-end



### M6.2 — Analysis API Endpoints

- [ ] `app/api/schemas/analyses.py` — `AnalysisCreateRequest`, `AnalysisResponse`, `AnalysisStatusResponse`, `AnalysisListResponse`, `AnalysisResultResponse`
- [ ] `app/api/v1/analyses.py` — Router:
  - `POST /` (201) — create analysis, returns analysis_id
  - `GET /{analysis_id}` — full result
  - `GET /{analysis_id}/status` — status only (fast)
  - `GET /` — list user's analyses
- [ ] Include in `app/api/v1/router.py`
- [ ] Test: create analysis → 201, poll status → complete, get result → full data



### M6.3 — SSE Streaming (MVP)

- [ ] `app/api/v1/analyses.py` — Add `GET /{analysis_id}/stream` endpoint
  - Return `StreamingResponse(media_type="text/event-stream")`
  - Yield events: `extraction`, `parsing`, `evaluation`, `scoring`, `composition`, `complete`
  - Each event: `{ step, status, progress?, data? }`
- [ ] Test: connect via `httpx` SSE client, verify events received



### M6.4 — General Mode

- [ ] Wire `AnalysisType.GENERAL` → evaluators: Recruiter, ATS, Technical, Content Quality
- [ ] Test: create general analysis → runs 4 evaluators, no job matcher



### M6.5 — Role-Based Mode

- [ ] Wire `AnalysisType.ROLE_BASED` → all evaluators + Job Matcher
- [ ] Add `target_role` to context → role-specific prompts from `app/ai/prompts/roles/`
- [ ] Create role prompt files: `frontend_dev.py`, `backend_dev.py`, `fullstack_dev.py`, `ai_engineer.py`, `data_scientist.py`, `devops.py`
- [ ] Test: create role-based analysis → runs all 5 evaluators

---



## Module 7: Prompt Management & Versioning

> **Goal:** All prompts versioned, tracked, reproducible.
> **Depends on:** Module 3 (prompt composition).
> **Deliverable:** Prompts stored in DB, analysis records track which version was used.



### M7.1 — Prompt Versioning

- [ ] `app/services/prompt_service.py` — `get_active_prompt(key) -> PromptVersion`
- [ ] `sync_prompts_to_db()` — On startup, sync prompt files to `prompt_versions` table
- [ ] Record `prompt_versions_used` in Analysis when creating
- [ ] Verify: same resume analyzed twice with same prompts → identical results (deterministic portion)

---



## Module 8: Testing Infrastructure

> **Goal:** pytest setup, fixtures, test coverage for core modules.
> **Depends on:** Modules 1-6 (test what exists).
> **Deliverable:** `poetry run pytest` passes, CI-ready.



### M8.1 — Test Setup

- [ ] Create `tests/conftest.py` — event loop fixture, async DB session fixture, `AsyncClient` fixture, auth fixtures (register + login helper)
- [ ] Create `tests/fixtures/` — `sample.pdf`, `sample.docx`, `sample_image.pdf`, `mock_structured_resume.json`, `mock_evaluator_results.json`



### M8.2 — Unit Tests

- [ ] `tests/test_document_processing/test_extractor.py` — PDF, DOCX, OCR, quality
- [ ] `tests/test_scoring/test_score_calculator.py` — Each deterministic check
- [ ] `tests/test_schemas/test_evaluators.py` — Pydantic validation with valid + invalid data
- [ ] `tests/test_ai/test_provider.py` — Mock litellm, verify retry + usage tracking
- [ ] `tests/test_services/test_resume.py` — Upload, extract, CRUD
- [ ] `tests/test_services/test_analysis.py` — Full pipeline (mocked AI)



### M8.3 — API Tests

- [ ] `tests/test_api/test_auth.py` — Register, login, refresh, invalid credentials
- [ ] `tests/test_api/test_resumes.py` — Upload, list, get, delete, invalid file type
- [ ] `tests/test_api/test_analyses.py` — Create, get, status, list



### M8.4 — Integration Tests

- [ ] `tests/test_integration/test_full_pipeline.py` — Mark `@pytest.mark.integration`
  - Real resume → real AI calls (use `gpt-4o-mini` to save cost)
  - Verify: text extracted → structured resume → evaluators → scores → roast
- [ ] Only run explicitly: `poetry run pytest -m integration`

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
- [ ] Test: login → token stored → API calls include header → logout clears — backend auth now exists and is curl/pytest verified; the browser walkthrough has not been run



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

- [ ] `src/app/upload/page.tsx` — Multi-step wizard: Upload → Configure → Submit
- [ ] `src/components/upload/ResumeDropzone.tsx` — Drag-and-drop zone, file validation (PDF/DOCX, 10MB), progress indicator
- [ ] `src/hooks/mutations/use-upload.ts` — `useUploadResume()` mutation
- [ ] `src/types/resume.ts` — TypeScript types matching backend `ResumeResponse`
- [ ] Test: upload file → success toast → resume ID stored for next step



### M10.2 — Analysis Configuration

- [ ] `src/components/upload/ModeSelector.tsx` — Radio/tabs: General, Role-Based, JD-Based (disabled for V1?), Custom
- [ ] `src/components/upload/RoleSelector.tsx` — Shown if role-based: dropdown of roles (Frontend Dev, Backend Dev, etc.)
- [ ] `src/components/upload/JdInput.tsx` — Shown if JD-based: textarea for job description
- [ ] `src/components/upload/CustomInstructions.tsx` — Shown if custom: textarea for focus areas
- [ ] `src/hooks/mutations/use-start-analysis.ts` — `useStartAnalysis()` mutation (POST to `/analyses`)
- [ ] On submit → redirect to `/analysis/[id]`



### M10.3 — Analysis Result View

- [ ] `src/app/analysis/[id]/page.tsx` — Full roast dashboard
- [ ] `src/components/analysis/ScoreRing.tsx` — Circular score display (0-100), color-coded
- [ ] `src/components/analysis/ScoreBreakdown.tsx` — Bar chart or radar chart (recharts) showing sub-scores
- [ ] `src/components/analysis/FeedbackCard.tsx` — Evaluator summary with expand/collapse
- [ ] `src/components/analysis/CriticalIssueList.tsx` — Issues with severity badges, improvement suggestions
- [ ] `src/components/analysis/RoastDisplay.tsx` — Final roast text (markdown-like formatting)
- [ ] `src/app/analysis/[id]/loading.tsx` — Skeleton loading state
- [ ] `src/types/analysis.ts` — TypeScript types matching backend `AnalysisResultResponse`



### M10.4 — Streaming Display

- [ ] `src/hooks/use-sse.ts` — Custom hook consuming SSE from `/analyses/{id}/stream`
- [ ] `src/components/analysis/StreamingStatus.tsx` — Pipeline step progress (Extracting → Parsing → Evaluating → Scoring → Composing → Done)
- [ ] Show animated progress bar with step labels
- [ ] On `complete` event → refetch full analysis result, show results



### M10.5 — Analysis History

- [ ] `src/app/dashboard/page.tsx` — Table/card list of all analyses
- [ ] Status badges: Queued, Processing, Complete, Failed
- [ ] Quick view: resume name, mode, score, date
- [ ] Click → navigate to `/analysis/[id]`



### M10.6 — Error & Empty States

- [ ] `src/components/shared/ErrorState.tsx` — Retry button, error message
- [ ] `src/components/shared/EmptyState.tsx` — No analyses yet, CTA to upload
- [ ] `src/components/shared/Loader.tsx` — Full-page or inline loader
- [ ] Toast notifications for success/error via `sonner`

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