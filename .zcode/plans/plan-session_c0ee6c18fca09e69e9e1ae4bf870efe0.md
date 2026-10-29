# Plan: Upload → Automatic Brutal Roast — executed PHASE BY PHASE

**Execution mode (user-requested):** one phase at a time. After each phase I report the results and **wait for your go-ahead** before starting the next. Phase order below; nothing later runs until you say so.

## Locked decisions (user-confirmed)
- Auto-roast after upload (frontend auto-starts a `general` analysis → progress/result page).
- Keep `.env` as-is: `gemini-2.5-flash` primary / `gemini-2.5-flash-lite` fast (real key present).
- Progress via 2s status polling (SSE later). Statuses lowercase: `queued → extracting → parsing → evaluating → scoring → composing → completed | partial | failed`.

## Phase 0 — Live AI smoke test (first, alone)
One-off script with the real key: plain call on the primary model, structured-output call on the fast model. Confirms key + both models work before anything is built. Report exact provider errors if any.

## Phase 1 — Evaluator layer
Categorical-rating evaluator schemas in `app/schemas/evaluators.py` (AI never returns raw numbers); prompts `prompts/evaluators/{recruiter,ats,technical,content_quality}.py`; four evaluator functions in `app/ai/evaluators/` (ATS partly deterministic). Remove `culture_fit` evaluator + prompt and superseded `communication.py`/`technical_fit.py`. Mocked tests.

## Phase 2 — Pipeline brain
Rewrite `orchestrator.py` (parallel evaluators, skip-and-flag on failure); new `aggregator.py` (dedupe → critical/warnings/suggestions/positives); rewrite `scoring.py` (50% deterministic checks / 50% AI categorical ratings → fixed ranges, mode weights, renormalization on partial failure); new `composer.py` + `prompts/composer.py` (roast text, deterministic fallback). Mocked tests incl. determinism + partial-failure renormalization.

## Phase 3 — Analysis service + API
`app/services/analysis.py` (ownership check, type validation, daily cap → 429, insert `queued`, `asyncio.create_task(run_pipeline)`, stage transitions, usage rows persisted, `completed/partial/failed` semantics) + `app/api/schemas/analyses.py` + `app/api/v1/analyses.py` (`POST /analyses` → 202, `GET /analyses`, `GET /{id}`, `GET /{id}/status`). Tests: API + pipeline (mocked AI).

## Phase 4 — Frontend
Real analysis types (lowercase statuses) + `useStartAnalysis` + fixed `use-analyses.ts`; upload page auto-starts the roast → new `/analysis/[id]` page (polling progress, score, breakdown, issues, final roast card, failed/partial states); dashboard "Recent roasts" via fixed `AnalysisCard`. eslint/tsc/build.

## Phase 5 — Full verification + tracker
Backend checks + full pytest (AI mocked) → live end-to-end with the real key (upload → auto-roast → result page, DB rows verified) → `PROGRESS.md` update. No commits.

**Out of scope:** SSE, role_based/jd_based/custom modes, rerun endpoint, slowapi per-tier limits, OCR, prompt_versions table.