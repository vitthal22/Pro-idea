# PROGRESS — Project Tracker

> **Purpose:** The single file any AI assistant (or human) reads FIRST to know
> the current state of this project — without rescanning the whole repo.
> Kept up to date at the end of every session (see the rule in `AGENTS.md`).

---

## 1. Status snapshot

**Last updated:** 2026-10-29
**Phase:** **MVP complete + "2026 Hiring Panel" roast overhaul (v2 prompts) live-verified (2026-10-30).** All four analysis modes, SSE streaming, ops middleware, and the scorecard/reality-check UI are done. Prompts bumped to v2.0.0: 20-year-principal-recruiter persona, harsh calibration anchors, 2026-market red flags; composer returns a structured `RoastReport` (headline verdict, 5-second impression, poison points, 3-market rejection analysis + prose). Score bands recalibrated (88/72/50/26/5 — a generic resume now lands ~58-66 instead of 77) with blunt verdict labels. Verified live on the user's own resume: 77 → 66.44 "Needs work" with real defect findings (bracket placeholders, 2026 date). Core agenda: no remaining gaps — only infra/deploy (skipped) and V2 items. The startup-seeded demo account is now on an unlimited `demo` tier (exempt from the per-tier daily analysis cap); accounts predating the tier are reconciled automatically at startup.
**One-liner:** A user uploads a resume and gets a brutally honest AI roast — 4 expert evaluators, hybrid 50/50 scoring, and a narrative roast — in a modern dark-first UI with analytics, all persisted in Postgres (`AIRoast`) with token usage and prompt versions tracked.
**Plan progress (PROJECT_PLAN.md, checkboxes):** **206/236 done (87%), 10 partial, 20 pending** — synced 2026-10-29 after the modes/SSE/ops session. Remaining pending are all intentional scope-outs: Docker/Redis infra + deploy (M11, user-skipped), OCR (V2), prompt_versions DB table (V2 by design), slowapi burst limiting (needs Redis for multi-worker), frontend_dev coverage of the 4 remaining analysis modes is done — nothing left on the core agenda.

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
| Test suite | `backend/tests/`: auth (repository/AuthService/API/seed/throttle/non-blocking), schema, storage, extraction, resumes API, AI provider/parser — real PostgreSQL, per-test transaction rollback + temp upload dir, migrations applied by a session fixture | `pytest` → `78 passed in 52.77s` (2026-10-28); `mypy app/ tests/` clean (56 files); ruff + format clean on every touched file |
| Full DB schema | `resumes`, `analyses`, `analysis_results`, `analysis_usage` models + relationships (`lazy="raise"`); migration `0002` | `alembic check` → “No new upgrade operations detected”; 6 FKs all `ON DELETE CASCADE`; indexes + `uq_analysis_results_analysis_id` verified via asyncpg; downgrade/upgrade roundtrip OK; 5 schema tests (JSONB/Numeric round-trip, unique result, FK violation, cascade, no lazy IO) |
| Resume upload (Module 2) | `storage/` (protocol + `LocalStorage` under `UPLOAD_DIR`), `document_processing/` (pdfplumber, python-docx in document order, quality gate, extractor router), `ResumeService` (chunked size cap, libmagic + OOXML check, `asyncio.to_thread` extraction, soft delete) | Live server: upload `201` → `parsing_status: completed`, 151 words, table row preserved; list → total 1; get `200`; delete `204`, file gone from disk, row soft-deleted; get after delete `404`. Low-quality uploads return 422 with `PARSING_FAILED` error code; record kept with `parsing_status: failed` in DB (test limitation due to transaction savepoint mechanics). Frontend: upload page fixed (removed explicit `Content-Type` header), dashboard/profile pages now include Sidebar component for navigation. |
| Resume API | `POST /api/v1/resumes/upload` (201), `GET /api/v1/resumes`, `GET /{id}`, `DELETE /{id}` (204) | pytest: 24 Module-2 tests incl. ownership 404, 400 invalid/empty/oversized, 422 low-quality (API returns 422 + error code, DB `parsing_status` sees `pending` due to transaction savepoint mechanics), 401 unauthenticated |
| Upload 422 fix (frontend) | `api-client.ts` no longer forces `Content-Type: application/json` on `FormData` bodies (it stripped the multipart boundary → backend saw no `file` field → 422); upload page: file input is now wired to a `<label htmlFor>` (it was `hidden` with no click handler, so no file could ever be picked), file is read via a **`ref`** (it was read from `e.target`, which is the `<form>` on submit, so `.files` is always `undefined`), `useState` hooks moved **above** the early returns (rules-of-hooks violation), `uploading`/`uploadError` state replaces the fake `isPending` spinner, failures now render on the page instead of `console.error`, navigation via `router.push`; `parseErrorResponse` now also maps FastAPI's `{detail}` shapes (string + `RequestValidationError` array) so 422s show a real message | Reproduced the exact 422 with curl: forced JSON header on multipart → `422 {"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required"}]}`; correct multipart → `201` for a DOCX **and** a PDF (≥100 extracted words, `parsing_status: completed`); user's own `vitthal gupta resume.pdf` (174 KB) is in the DB as `completed`; `npm run lint` → 0 errors (upload/page clean), `npx tsc --noEmit` clean, `npm run build` → ✅ `/upload` route generated |
| Login throttling (M1.6) | `LoginThrottle` protocol + `InMemoryLoginThrottle` sliding window; 429 after `LOGIN_RATE_LIMIT_PER_HOUR` failures per email+client; success resets; seam ready for Redis | TDD (tests written first): 6 tests — block after N, correct password blocked, reset on success, per-account isolation, window pruning; `RateLimitError` → 429 `RATE_LIMITED` |
| bcrypt off the event loop | `AuthService.register/login` call `hash_password`/`verify_password` via `asyncio.to_thread` | TDD: concurrency test fails on the old code (2 ticks vs ≥12 expected) and passes after (≥12 ticks during a 250 ms verify) |
| Frontend scaffold | Next.js 16.3.7 + Tailwind v4 + shadcn (radix/nova) + TanStack Query + Zustand + Zod | `npm run build` ✅ (6 routes), `npm run lint` ✅ |
| Frontend auth UI | Landing, `/login`, `/register` (zod validation), dashboard (guarded), api-client with JWT + one-shot 401 refresh, `credentials: "include"` for cookies | Build/lint pass; live test pending backend running |
| npm workflow | Root + backend `package.json` scripts; backend has a project-local `.venv` (like node_modules); `concurrently` runs both servers with one command | `npm run dev` verified: backend `/health` `{"status":"ok"}` + frontend `HTTP 200`; `npm run check` passes both sides |
| AI provider wrapper (M3.1, rewritten 2026-10-28) | `app/ai/provider.py`: async `litellm.acompletion` (never blocks the loop), config from `Settings` (`ai_timeout`/`ai_max_retries`/`ai_fallback_enabled`/`ai_max_tokens` + per-provider key fields), JSON-schema structured outputs via `response_model`, retries with backoff (invalid output counts as a failure), fallback chain primary→fast model, `AIResult` carries content + parsed data + token usage, fail-fast with clear error when a hosted provider has no key. Broken `_provider_impl.py`/`_fallback_provider.py` deleted; `culture_fit` evaluator now validates against `RecruiterEvaluatorOutput` instead of silently defaulting garbage | `ruff check .` + `ruff format --check .` clean (70 files), `mypy app/ tests/` clean (56 files), `pytest tests/test_ai` → 12 passed (mocked litellm), full suite `pytest` → **78 passed** |
| AI resume parser (M3.4) | `app/schemas/resume.py` (`StructuredResume` + ContactInfo/Experience/Education/Project/Certification, all `Field(description=...)`), `app/ai/prompts/parser.py` (extraction-only rules, no invention), `app/ai/parser.py` (`parse_resume` on `AI_FAST_MODEL`, truncates input at 15k chars, never the system prompt) | `tests/test_ai/test_parser.py` → 4 passed (mocked `call_ai`): structured round-trip, truncation, fast-model choice, error on missing data |
| Prompt files repaired | `prompts/evaluators/communication.py`, `technical_fit.py`, `prompts/roles/product_manager.py`, `software_engineer.py` were single-line garbage (`\"\"\"…\n` escaped) that ruff couldn't parse; all rewritten as valid Python | `ruff format --check .` parses and passes; pre-existing issue #29 fully resolved |
| Upload live re-verification (2026-10-28) | Full flow on live server: login → upload DOCX `201` (`parsing_status: completed`, 122 words) → list → get `200` → delete `204` → get-after-delete `404`; undersized fixture (68 words) correctly rejected `422 PARSING_FAILED too_few_words` by the quality gate | curl against live uvicorn; test records deleted afterwards |
| Frontend upload UI (M10.1 partial) | `ResumeDropzone` (react-dropzone: drag&drop, PDF/DOCX + 10 MB client validation), `useUploadResume` mutation hook, upload page rewritten on both; shared `EmptyState`/`ErrorState` components extracted | `npm run lint` 0 errors (14 pre-existing warnings in untouched files), `tsc --noEmit` clean, `npm run build` ✅ all 7 routes |
| Frontend dashboard on real data | Dashboard now lists **resumes** (`useResumes` → `GET /resumes`) with parsing-status badges + upload CTA — it previously called the nonexistent `/analyses` endpoint and always errored. Browser-verified: login as demo → dashboard shows 15 real rows (Parsed/Failed/Processing badges) → `/upload` renders dropzone | Live browser walkthrough 2026-10-28 (IAB): login redirect, dashboard rows, upload page all verified; actual file-set via browser unsupported (IAB limitation) — the multipart POST itself is curl-verified |
| 2026 Hiring Panel — roast v2 (2026-10-30) | Prompts bumped to v2.0.0 across all 5 evaluators + composer: 20-year principal-recruiter persona, AI-slop-era calibration anchors ("excellent = top decile with P99/SLIs/eval-pass-rate/cost evidence; when torn, pick the harsher"), 2026 red flags (AI-generic phrasing, stack-stuffing). Composer now returns a **structured `RoastReport`** (headline_verdict, verdict_summary, five_second_impression, poison_points ≤5, exactly 3 MarketVerdicts, prose roast) via `response_model`; deterministic fallback fills every field. Score bands recalibrated 88/72/50/26/5 + `score_verdict` labels (Interview-ready / Needs work / Will get screened out / Instant-reject pile). API: `reality_check` + `score_verdict` on the detail response (JSONB — no migration). UI: **Resume Performance Scorecard** (ring + weighted category cards incl. locked Job Match + benchmark line + verdict) and **Unfiltered Recruiter Reality Check** (Zero-Sugarcoating badge, headline, 5-second impression quote, Fatal Poison Points, 3-market rejection cards with missing-signal chips). Verified: backend 136 passed + 1 skipped, ruff/mypy clean; frontend tsc/lint/build green; **live before/after on the user's own resume: 77 → 66.44 "Needs work"** with the panel catching real defects v1 missed (bracket placeholders, 2026 future date, word-joining errors) — screenshots of scorecard + reality check + market cards taken. |

| UI consistency pass — one container everywhere (2026-10-30) | User complained that page switches visibly shifted the content edges (every page declared its own width: analysis `max-w-2xl`, history `max-w-3xl`, dashboard/analytics `max-w-4xl`, upload `max-w-xl`) and that Analytics had dead space on the right on wide screens. Fix: the app shell `(app)/layout.tsx` now owns ONE constant container — `<main className="mx-auto w-full max-w-6xl flex-1 p-4 md:p-8">` — and every page dropped its own `mx-auto max-w-*` wrapper (inner `max-w-md` status cards kept; they center inside the container). Auth pages: the glass-card wrapper changed from `w-fit` (content-dependent width) to `w-full max-w-sm`, identical on login and register. Landing audited visually — marketing width hierarchy (hero 3xl / bento 5xl / navbar+footer 6xl) is intentional and evenly padded; no change. | `npx tsc --noEmit` clean, `npm run lint` clean, `npm run build` ✅ 9 routes; live browser walkthrough at 1600×900 with screenshots: landing, register, login, dashboard, analytics, upload, profile, result all fill the same container — Analytics charts now stretch full width (the complaint), result scorecard uses the space; 390px mobile re-check: no overflow, tiles stack, hamburger nav intact |

| Scorecard squeeze fix (2026-10-30) | User screenshot showed "Weight 20%" overlapping the JOB MATCH card on the result page. Measured live geometry: at 1024–1280 CSS px viewports the scorecard's `lg:grid-cols-[auto_1fr]` gave the ring column a fixed ~320px (the `max-w-xs` verdict paragraph), squeezing the 2-col category grid to ~126–160px cards — below the label's min-content width, so the `Weight X%` span spilled out of its card. (The user's screenshot itself was the STALE pre-container build — content box measured exactly 672 CSS px = the old `max-w-2xl` at their 125% Windows scaling; a reload picks up the new layout.) Fix in `RoastResult.tsx`: the ring stacks above the cards until `xl` (`xl:grid-cols-[auto_minmax(0,1fr)]`), the weight span is `shrink-0 whitespace-nowrap`, and the label span gets `min-w-0` so the label wraps instead. | tsc/lint clean, build ✅; measured at 1920: ATS card 913–1246, weight right edge 1230 (inside), JOB MATCH starts 1258; screenshots at 1536 and 1100 confirm no overlap at any width |

| Role dropdown unreadable in dark mode (2026-10-30) | User screenshot: the upload page's native `<select>` popup rendered white (OS light theme) with light-gray option text — unreadable. Two fixes: (1) the role dropdown now uses the shadcn `Select` (Radix) instead of a native `<select>` — a fully themed popup in both themes, consistent with the rest of the form controls; (2) `globals.css` sets `color-scheme: light` on `:root` and `color-scheme: dark` on `.dark`, so any remaining native controls (scrollbars, autofill, native popups) follow the app theme instead of the OS. | tsc/lint clean, build ✅; browser screenshots with the popup open in dark mode (dark popup, ember highlight + checkmark on the selected role) and light mode (white popup, dark text) — both fully readable |

| Demo tier — unlimited analyses (2026-10-30) | `TIER_DEMO = "demo"` constant on the user model; `UserRepository.create` gained a `tier` param and a new `update_tier` method (protocol + in-memory + postgres); the seeder creates the demo account on the demo tier and **reconciles pre-existing accounts** at startup; `_enforce_daily_cap` returns early for the demo tier (no DB roundtrip). The API already passes `current_user.tier`, so no endpoint changes. | `npm run check:backend` → ruff + format clean (104 files), mypy clean (79 files); `npm test --prefix backend` → **141 passed + 1 skipped** (5 new: create-with-tier, update_tier persists/unknown-id, seed upgrade of an existing free-tier demo account, cap bypass with `rate_limit_free=0`); live: the running dev server auto-reloaded and its startup seeder moved `demo@airoast.dev` to `tier='demo'` (asyncpg row check + `/me` returns `"tier":"demo"`) |

| Status-clarity + completed-only report gating (2026-10-30) | User reported "partial" reading as "partially reviewed / still working", then explicitly requested: **only a fully `completed` analysis may show the report** — a partial one (an evaluator failed) must never render the roast; opening it shows an error card with "Try roasting again" instead. Fix: shared `StatusBadge` (`components/shared/status-badge.tsx`) — pulsing "In progress" for the 6 running statuses, "Ready", amber "Incomplete" with tooltip, "Failed" — used in `AnalysisCard` (History), the dashboard `LatestRoastCard` (button: "Watch live" / "View roast" / "View status"), and the Analytics `ActivityFeed` (badge for everything except `completed`; running titles not clickable). Result page: running → `StageProgress`; failed/partial → "The roast burned" / "The roast didn't finish" card with retry; **only `completed` renders `RoastResult`** (its `status` prop, partial-banner logic, and the ATS locked-branch were removed as unreachable for completed analyses); completed-without-result shows a retry card instead of a blank page. Also removed the dead `JobMatchCard` (+ imports). Backend untouched: `partial` rows stay in the DB (debug/analytics) but the UI never serves them as reports. | `npx tsc --noEmit` clean, `npm run lint` 0 errors/0 warnings, `npm run build` ✅ 9 routes; live browser: the user's partial analysis URL → "The roast didn't finish" card (screenshot), a completed URL → full scorecard, History shows "Incomplete"/"Ready" badges with tooltips; live demo-tier check: the day's 4th analysis accepted (202) where a free user would hit the 3/day cap |

| Modes + SSE + ops session (2026-10-29, "go for it" batch) | **Analysis modes end-to-end**: Job Matcher evaluator (fails fast without context), `context` flows to every evaluator prompt (TARGET ROLE / JOB DESCRIPTION / USER FOCUS), 8 role context prompts + registry, role_based/jd_based/custom wired in the orchestrator with §13 mode weights, service validates mode context (400s), composer takes USER FOCUS, job_match_feedback persisted + exposed via API. **Frontend**: 4-mode selector on upload (glass tiles), role dropdown / JD textarea / custom-focus textarea, Job Match result card. **SSE**: `GET /analyses/{id}/stream` (heartbeats, idempotent replay) + fetch-based `use-analysis-stream` hook (EventSource can't send JWTs); result page uses SSE with polling fallback. **Ops**: `common/middleware.py` (request logging + X-Process-Time + CORS via setup_middleware), CORS asserted (origin/preflight/reject), per-tier daily cap by `users.tier`. **Phase D**: opt-in integration test (`RUN_INTEGRATION=1`, marker registered) + `cost_usd` from `ai_input/output_price_per_m` settings. **Found+fixed live**: pipeline never passed `mode` to `calculate_scores` (role_based ran general weights) — regression test added. Verified: ruff/mypy clean (101 files), **135 passed + 1 skipped** (integration opt-in), tsc/lint/build green, live role_based run on port 8010 (job match_rating "good", role_relevance from matcher, correct weights) + SSE replay via curl; test rows cleaned. |

| Roast pipeline final verification (Phase 5, 2026-10-29) | Full-stack pass. Backend: ruff + format clean (90 files), mypy clean, `pytest` → **119 passed ×5 consecutive runs** after fixing the third unscoped-select flake (`test_full_chain_persists_and_roundtrips` grabbed any `analysis_usage` row — now scoped by analysis id). Frontend: `tsc` clean, lint 0 errors, build ✅. **Browser E2E with screenshot**: login via UI → roast started via API → `/analysis/[id]` showed `StageProgress` live (4 stages done, "Writing the roast" active) → the page transitioned to the full result **without reload** via 2s polling (score 69, full roast catching timeline inflation + ghost skills + missing contact info, findings lists, breakdown) → dashboard showed "Recent roasts (1)" with score badge linking to the result. All test rows cleaned afterwards (analyses/usage back to 0; only the demo user's pre-existing data remains). |
| UI overhaul Phases 1–5 (2026-10-29) | **Ember design system** (`globals.css` rewritten): dark-first warm layered surfaces, ember `oklch` accent, gradient/glow/glass/shimmer utilities, full chart palette; light theme = warm paper. `next-themes` wired (dark default, class attribute, `suppressHydrationWarning`) + `ThemeToggle`. **Consistency fix**: all app pages moved into the `(app)` route group with one shell layout (auth guard + sticky sidebar / mobile hamburger+Sheet) — per-page sidebars and the top-gap quirk deleted; shared `PageHeader`. New Sidebar (Overview/Roasts/Analytics + ember New-roast CTA + Profile + toggle). Components: animated `ScoreRing` (SVG sweep, band colors), `StatTile`, `ResumeRow`, restyled `AnalysisCard` (score chip + hover lift). Overview = bento (stats, latest-roast card, gradient CTA tile, recent lists, stagger animations). History = Roasts/Resumes tabs. Upload = ember dropzone (drag wiggle/glow), file chip, gradient CTA, sonner toast on hand-off. Roast experience = pulsing glow + flame, spring ember progress bar, per-stage check/spinner. Result = 140px ring card, ember glass roast card, staggered findings, animated category bars, amber partial banner. Landing = glass navbar, radial-glow hero with gradient headline, CSS product mock (browser chrome + ring + roast excerpt), features bento, 3-step how-it-works, CTA panel; auth pages glassed. Analytics = 4 stat tiles + score-trend area chart + distribution bar chart + activity feed (shadcn ChartContainer, no backend changes). Deps added: `framer-motion`; shadcn `sheet` + `chart`. Verified: `tsc`/lint clean, build ✅ (9 routes), **browser walkthrough with screenshots** — landing/login/dashboard/analytics/result in dark + light, mobile 390px sheet nav; auth-glass wrapper width fixed during walkthrough. |

---

## 3. In progress / next up

- [x] **bcrypt off the event loop** — `AuthService` now hashes/verifies via `asyncio.to_thread`; regression test asserts the loop keeps ticking during a 250 ms verify.
- [x] **Module 3 core (2026-10-28)** — `call_ai()` reworked (async, Settings, fallback, usage, structured outputs); `StructuredResume` + parser built; 12 new mocked AI tests.
- [x] **AI live-verified (2026-10-29, roast-pipeline Phase 0)** — real `GEMINI_API_KEY` works. Google retired `gemini-2.5-flash`/`-lite` for new accounts (404 "no longer available"), and `gemini-3.8-flash` hangs at connection (>90s). Final `.env`: `AI_MODEL=gemini/gemini-3.5-flash` (~6s) + `AI_FAST_MODEL=gemini/gemini-3.5-flash-lite` (~1s, structured output verified). The fallback chain proved itself live: 3.8-flash timeouts were caught by the fast model every time.
- [x] **Roast pipeline Phase 1 done (2026-10-29) — evaluator layer** — `app/schemas/evaluators.py` rewritten to categorical outputs (AI never returns raw numbers; `QualityRating` Literal + `max_length` caps). Shared `app/ai/evaluators/base.py` (`run_evaluator` pattern). Four evaluators (`recruiter`, `ats`, `technical`, `content_quality`) + versioned prompts; `orchestrator.py` registry; removed `culture_fit` and superseded prompts; added missing `__init__.py` files under `app/ai/`.
- [x] **Roast pipeline Phase 2 done (2026-10-29) — the pipeline brain** — `orchestrator.run_evaluations()` runs evaluators via `asyncio.gather(return_exceptions=True)`: one failure is recorded and skipped, never aborting the rest (evaluators return `(output, AIResult)` for usage tracking). Deterministic `aggregator.py` (severity buckets + whitespace-insensitive dedupe); rewritten `scoring.py` (8 deterministic checks 50% + AI categorical ratings 50% → fixed bands; §13 weights; renormalization on partial failure; deterministic-only fallback); `composer.py` + prompt (roast prose, deterministic template fallback); `app/schemas/report.py` (AggregatedResults, ScoringResult). Live brain E2E: 4 evaluators on real Gemini (survived 500+503 via retries), 318-word roast.
- [x] **Roast pipeline Phase 3 done (2026-10-29) — analysis service + API** — `app/services/analysis.py`: `create_analysis` (mode wired → 400, ownership/soft-delete → 404, daily cap → 429) inserts `queued` + schedules `run_pipeline` fire-and-forget in **its own session** (injectable factory; tests run it inside the test transaction per gotcha 14) through `extracting → parsing → evaluating → scoring → composing → completed | partial | failed`, never raises; stores parsed data in `resume.structured_data["parsed"]`, `analysis_results` row, one `analysis_usage` row per AI call, prompt versions/model/processing time. `compose_roast` returns usage (3-tuple). API: `POST /analyses` → **202** `{analysis_id, status:"queued"}`, `GET /analyses` (paginated), `GET /{id}` (full result), `GET /{id}/status` (poll); `pytest` → **119 passed**. **Live HTTP E2E**: 202 → `parsing → evaluating → composing → completed` (166s) → score 69.42, roast that caught the test resume's timeline inflation; 5 usage rows + 6 prompt versions verified in DB.
- [x] **Roast pipeline Phase 4 done (2026-10-29) — frontend auto-roast flow** — `types/analysis.ts` rewritten to the real Phase-3 contract (lowercase statuses, `AnalysisDetail`/`AnalysisResultPayload`/`ScoringBreakdown`, `RUNNING_STATUSES` + `isRunningStatus`). New `useStartAnalysis` mutation; `useAnalyses`/`useAnalysis` rewritten (`useAnalysis` **polls every 2s while the pipeline runs, stops at terminal status**). Upload page auto-roasts: upload success → `POST /analyses` → redirect to `/analysis/[id]` (button reflects Uploading → Starting the roast → done; start failures shown inline). New `/analysis/[id]` page (Next 16 `use(params)`): skeleton → `StageProgress` (5 live stages, done/active styling) while running; failed → error + "Try roasting again" (starts a new analysis); completed/partial → `RoastResult` (score header, partial banner, roast card, critical/warnings/suggestions/positives lists with sources, score breakdown with AI category bars + deterministic check list, expert verdicts). `AnalysisCard` fixed (lowercase statuses + score badge); dashboard gained "Recent roasts" section (top 5, silently hidden while the endpoint errors). Checks: `tsc --noEmit` clean, `npm run lint` 0 errors (14 pre-existing warnings in untouched files), `npm run build` ✅ — `/analysis/[id]` generated as dynamic route.
- [x] **Roast pipeline Phase 5 done (2026-10-29) — final verification** — see the Phase 5 row in section 2. The MVP roast flow is complete end-to-end and browser-verified.
- [ ] **Next candidates (no strict order)** — SSE streaming (`GET /analyses/{id}/stream`, polling works today); `role_based` mode + Job Matcher evaluator + role prompt wiring; per-tier slowapi limits + request-logging middleware (rest of M1.6); rerun endpoint; layout polish (standalone pages `/analysis`, `/upload`, `/profile` render the Sidebar with a large top gap on wide screens).
- [ ] **M2.4 OCR** (image-only PDFs) stays V2: pytesseract/pdf2image are not installed; low-quality extraction currently returns a clean 422.
- [ ] Resume text is extracted **synchronously on upload** (bounded by the 10 MB cap). If resumes get large/slow, move extraction to a background job and poll `parsing_status`.
- [ ] `RedisTokenDenylist`: protocol + factory seam are ready; logout revocation is still in-memory and returns after a backend restart (documented, by design).

---

## 4. Blocked / waiting

| Item | Blocker | Unblock path |
|---|---|---|
| PostgreSQL (M1.2–M1.4) | Not blocked anymore — a **local** PostgreSQL 18.3 serves `AIRoast`; Docker is still absent but not required | Docker install optional (`docker compose up -d postgres redis`) |
| Rate limiting (M1.6) | Needs Redis for meaningful limits | Install Docker (or point `REDIS_URL` at any Redis) |
| OCR fallback (M2.4) | pytesseract + pdf2image + Tesseract/Poppler are V2 deps and not installed | Add deps + binaries, then implement `document_processing/ocr.py` |
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
16. **bcrypt must stay off the event loop** — measured 258–271 ms per hash/verify. `AuthService` wraps both in `asyncio.to_thread`; `tests/test_services/test_auth_nonblocking.py` fails if that regresses. Never call the sync hashers directly from a request path, and do not lower the bcrypt cost to hide it.
17. **Multi-worker auth state needs Redis** — both `InMemoryTokenDenylist` and `InMemoryLoginThrottle` are per process. Today the backend runs a single uvicorn worker, so revocation and throttling are consistent; with two workers, a logout/throttle in one process does not affect the other. Redis implementations are required before scaling workers.
18. **GitHub push 403 on this machine** — Windows Credential Manager holds a `git:https://github.com` credential for **vitthal-blip**, but the repo belongs to **vitthal22**, so plain `git push` fails with `Permission to vitthal22/Pro-idea.git denied to vitthal-blip`. The remote is now scoped to the right account (`https://vitthal22@github.com/vitthal22/Pro-idea.git`) and pushes work. To remove the stale entry: `cmdkey /delete:LegacyGeneric:target=git:https://github.com` (run in cmd.exe). The repo is **public**; blank out `DEMO_USER_*` before any public deployment so the documented demo login cannot be used.
19. **`node_modules/` is gitignored from the root now** — 488 files were briefly tracked in the first local commit; it was amended before the first push, so nothing leaked to GitHub. Keep Node deps at the root ignored.
20. **libmagic reports DOCX as `application/octet-stream` on this machine** — detected MIME alone would reject every Word upload. `ResumeService._detect_mime_type` therefore accepts `octet-stream`/`zip` **only** when the archive really contains `word/document.xml`; never fall back to the filename extension.
21. **`prompt_versions` table is intentionally absent** — ARCHITECTURE.md keeps prompt versions as file constants for the MVP; `PROJECT_PLAN.md` still lists it as a V2 item. Do not “fix” this by adding the table.
22. **Relationships use `lazy="raise"`** — accessing `user.resumes`, `resume.analyses`, `analysis.result` without `selectinload` raises instead of silently emitting IO in async code. Load them explicitly.
23. **Uploads are rooted at `backend/uploads`** — `LocalStorage` resolves `UPLOAD_DIR` against the backend package, never the process cwd. Tests override `get_storage` with a temp dir so the real `uploads/` stays empty.
24. **Never set `Content-Type` on a `FormData` request** — `api-client.ts` only applies `application/json` when the body is *not* `FormData`. Overriding the header drops the multipart boundary and FastAPI returns `422 "Field required: file"` even though the file was sent. This was the cause of the upload-page 422 (2026-10-27).
25. **Quality gate: `MIN_WORDS = 100`** (`document_processing/quality.py`) — a syntactically valid resume under 100 words returns `422 PARSING_FAILED` with reason `low_quality:too_few_words:N`. Not a client bug; the upload page now shows this message inline instead of swallowing it.
26. **Hooks must precede early returns in page components** — `upload/page.tsx` declared `useState` after `isPending`/`isError` returns, which crashes when the query settles. Keep all hooks at the top of the component.
27. **In a form `onSubmit`, `e.target` is the `<form>`, not the input** — `(e.target as HTMLInputElement).files` is always `undefined` there (HTMLFormElement has no `files`). Read the file from a `useRef<HTMLInputElement>` (or `new FormData(e.currentTarget)` with `name="file"` on the input). This produced the misleading "Please choose a PDF or DOCX file first" while "Selected: …" was already on screen.
28. **The stored PDFs in `backend/uploads/…/*.pdf` are 25-byte fixtures** (`%PDF-1.4 fake pdf content`) from earlier manual tests — pdfplumber raises `PdfminerException: No /Root object!` on them. They are not evidence of a broken pipeline.
29. **~~Pre-existing lint/format drift~~ RESOLVED (2026-10-28)** — the drifted `app/ai/*` and `app/schemas/evaluators.py` files were reformatted, and the four unparseable prompt files (escaped `\"\"\"` garbage) were rewritten as valid Python. `ruff check .` and `ruff format --check .` are now clean across the whole backend.
30. **The cascade schema test asserts per-user rows, not empty tables** (fixed 2026-10-28) — `test_deleting_user_cascades_through_children` used to `count(*)` whole tables and only passed on a pristine DB; the dev DB holds real demo uploads, so it failed with "15 == 0". It now counts only the deleted user's rows. Keep that pattern for any new test in the shared dev DB. **Third instance fixed 2026-10-29**: `test_full_chain_persists_and_roundtrips` also had an unscoped `select(AnalysisUsageModel)` and went flaky once the pipeline wrote real usage rows — always scope test queries by the row the test created (`analysis_id`, `user_id`, unique file name).
31. **In-app-browser file upload is unsupported** — ZCode's IAB cannot set file inputs, so UI upload tests verify rendering only; use curl for the multipart POST itself.
32. **Standalone-page top-gap quirk FIXED (2026-10-29)** — all app pages now live in the `(app)` route group with one shell layout; per-page sidebars are gone.
33. **Zombie port on 8000 — RESOLVED 2026-10-30** — a leaked socket from Oct-26-era orphaned python processes kept serving stale code on 8000 (dead PIDs, "process not found", health still 200). Fix: `powershell Get-Process python*` → `taskkill //PID <pid> //F` every stale python (some dated days back), after which the port freed. **Caution:** stale servers serve OLD code — a browser pointed at them silently renders outdated behavior; when pages look wrong, verify which process owns the API port first.
34. **Next.js dev overlay blocks Playwright clicks** near the bottom-left corner (portal covers the point). Click such elements via `locator.evaluate((el) => el.click())` instead.
35. **The UI only ever shows reports for `completed` analyses** (user decision, 2026-10-30) — `partial` (an evaluator failed or the composer fell back) is terminal in the DB and the row stays stored, but the frontend treats it like `failed`: lists badge it "Incomplete" (amber) and the result page shows "The roast didn't finish" + retry instead of the report. Do not "helpfully" re-enable partial reports — the earlier banner approach ("Partial report, but final") was explicitly rejected by the user ("partial is fake for me"). Backend semantics unchanged: `partial` still means "stored, degraded result"; only the presentation is gated. If partial reports are ever wanted back, it is a one-branch change in `analysis/[id]/page.tsx`.
32. **Standalone pages have a top-gap layout quirk** — `/analysis/[id]`, `/upload`, `/profile` render `Sidebar` + content without a proper flex row wrapper, so the content starts far down on wide screens (visible in the Phase 5 screenshot). Cosmetic only; fix alongside dashboard-layout consolidation in the polish pass.

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
│   └── versions/
│       ├── 0001_create_users_table.py        # users + unique email index
│       └── 0002_create_analysis_tables.py    # resumes, analyses, results, usage
└── app/
    ├── main.py               # FastAPI app, CORS, AppException handler, /health, lifespan
    ├── config.py             # Settings (pydantic-settings) — single source of truth; database_dsn
    ├── db/
    │   ├── base.py           # DeclarativeBase
    │   ├── session.py        # async engine + session factory + dispose_engine
    │   └── seed.py           # seed_demo_user() — idempotent seeding + demo-tier reconciliation
    ├── models/
    │   ├── user.py           # UserModel (users table) + TIER_DEMO constant + relationships
    │   ├── resume.py         # ResumeModel (soft delete via deleted_at)
    │   ├── analysis.py       # AnalysisModel + AnalysisResultModel
    │   └── analysis_usage.py # AnalysisUsageModel (tokens/cost)
    ├── storage/
    │   ├── base.py           # Storage protocol (save/delete/get_path)
    │   └── local_storage.py  # LocalStorage under UPLOAD_DIR, traversal-guarded
    ├── document_processing/
    │   ├── pdf.py            # extract_pdf (pdfplumber)
    │   ├── docx.py           # extract_docx (paragraphs + tables, document order)
    │   ├── quality.py        # validate_text → TextQuality (words, printable ratio)
    │   ├── cleaning.py       # shared whitespace cleanup
    │   └── extractor.py      # extract_text router + quality gate
    ├── common/
    │   ├── exceptions.py     # AppException hierarchy (auth/parsing/AI/analysis)
    │   ├── logging.py        # setup_logging() + app_logger
    │   └── security.py       # bcrypt hash/verify, JWT create/decode
    ├── ai/
    │   ├── provider.py       # call_ai(): async litellm, retries, fallback chain,
    │   │                     #   structured outputs (response_model), AIResult + usage
    │   ├── parser.py         # parse_resume(): raw text → StructuredResume (fast model)
    │   ├── orchestrator.py   # evaluator registry/mode map (still placeholder — Module 4)
    │   ├── scoring.py        # mode weights (still placeholder — Module 4/5)
    │   ├── evaluators/
    │   │   └── culture_fit.py  # run_culture_fit_evaluator (validates vs schema)
    │   └── prompts/
    │       ├── parser.py             # PARSER_SYSTEM_PROMPT + response model ref
    │       ├── evaluators/           # culture_fit, communication, technical_fit
    │       └── roles/                # software_engineer, product_manager
    ├── schemas/
    │   ├── resume.py         # StructuredResume + sub-models (AI parser contract)
    │   └── evaluators.py     # Recruiter/ATS/Technical/ContentQuality evaluator outputs
    ├── api/
    │   ├── deps.py           # get_db (AsyncSession), get_user_repo, get_auth_service, get_current_user, cookie helpers
    │   ├── schemas/auth.py   # RegisterRequest, LoginRequest, TokenResponse, UserResponse
    │   ├── schemas/resumes.py# ResumeResponse, ResumeDetailResponse, ResumeListResponse
    │   └── v1/
    │       ├── router.py     # aggregates v1 routers
    │       ├── auth.py       # register/login/refresh/logout/me (HTTP + cookies only)
    │       └── resumes.py    # upload/list/get/delete
    └── services/
        ├── auth.py           # AuthService: register/login/refresh/revoke → AuthSession
        ├── resume.py         # ResumeService: upload/extract/list/get/soft delete
        ├── login_throttle.py # LoginThrottle protocol + in-memory sliding window
        ├── token_denylist.py # TokenDenylist protocol + in-memory impl (logout revocation)
        └── user_repository.py# Protocol + InMemoryUserRepository + PostgresUserRepository + factory
└── tests/                    # pytest (real Postgres, per-test rollback)
    ├── conftest.py           # migrations + transactional fixtures + HTTP client + email factory
    ├── test_ai/test_provider.py  # call_ai: success/usage/structured/retry/fallback/no-key (mocked litellm)
    ├── test_ai/test_parser.py    # parse_resume: round-trip/truncate/fast-model/error (mocked call_ai)
    ├── test_services/test_user_repository.py
    ├── test_services/test_auth_service.py
    ├── test_api/test_auth.py # 201/409/401/204, cookie flags, revoked-token replay
    ├── test_api/test_auth_throttle.py
    ├── test_api/test_resumes.py # upload/list/get/delete, ownership, 400/422
    ├── test_document_processing/test_extraction.py # PDF/DOCX/quality failures
    ├── test_services/test_storage.py            # layout, delete, traversal guard
    ├── test_services/test_auth_nonblocking.py   # bcrypt stays off the event loop
    ├── test_db/test_seed.py  # demo seeding: creates + hashes, idempotent, skip when unconfigured
    └── test_db/test_schema.py# constraints, JSONB round-trip, FK cascade, lazy guard
frontend/
├── package.json              # Next 16, TanStack Query, Zustand, Zod, recharts...
└── src/
    ├── app/                  # page.tsx (landing), (auth)/login|register, dashboard/, upload/, profile/
    ├── components/           # ui/ (shadcn), auth/ (forms), layout/ (Navbar, Sidebar),
    │                         #   upload/ResumeDropzone, shared/ (ErrorState, EmptyState),
    │                         #   analysis/AnalysisCard (unused until /analyses exists)
    ├── hooks/queries/        # use-auth.ts, use-resumes.ts, use-analyses.ts (analyses endpoints pending);
    │                         #   hooks/mutations/use-upload.ts
    ├── lib/api-client.ts     # fetch wrapper: JWT header, 401→refresh→retry, credentials:include
    ├── providers/            # AppProviders (QueryClientProvider)
    ├── stores/auth-store.ts  # Zustand persisted auth state
    └── types/                # api.ts, resume.ts (ResumeResponse + ResumeListResponse), analysis.ts
```

---

## 8. Update protocol (for the AI assistant)

At the end of **every** session (or user request):

1. Re-read this file first.
2. Do the work.
3. Update sections 1–5 (snapshot, done, next, blocked, issues) to reflect reality.
4. Add any new file paths to section 7.
5. Report what was verified (command + actual output), not what is assumed.
