# Plan: "2026 Hiring Panel" — brutal prompt v2, score recalibration, scorecard UI

**Grounding:** 2026 market research — 80% of hiring managers can spot AI-written resumes; the reject signals are exactly generic praise/buzzword stuffing; the winners' vocabulary is verifiable specificity (P99/SLIs, eval pass rates, cost-per-inference, RAGAS/LangSmith, incident retros). The reference screenshots map to data we can produce with ONE structured composer call. No DB migration needed (final_report is JSONB). **Locked:** "2026 Hiring Panel" persona; calibration excellent=88 / good=72 / fair=50 / poor=26 / missing=5.

## Phase 1 — Prompt overhaul v2.0.0
1. **Evaluator prompts v2** (recruiter, ats, technical, content_quality, job_matcher — all `VERSION = "2.0.0"`): add the hiring-panel persona (20-year principal recruiter, has read 10k+ resumes through the AI-slop era), **calibration anchors** ("excellent = top-decile: quantified system-scale impact (P99/SLIs, eval pass rates, cost/token savings); good = concrete specifics with some metrics; fair = competent but generic duties; poor = buzzword-only claims; **when torn between two ratings, pick the harsher one**"), and 2026-market red flags (AI-generic phrasing, stack-stuffing without scale, no eval/telemetry/cost signals on AI-era claims).
2. **Composer v2 → structured `RoastReport`** (new schema, `response_model=`): `headline_verdict` (one punchy line, e.g. "Junior task-executor posing as an AI engineer"), `verdict_summary`, `five_second_impression` (first-person recruiter quote — why you get passed over), `poison_points[]` (fatal flaws, ≤1 sentence each), `market_analysis[]` (exactly 3: "Product Tech & Tier-1", "Service & Consulting", "2026 AI-Era Market"; each `{ verdict, analysis, missing_signals[] }`), and `roast` (the narrative prose — kept). Same single AI call, bigger schema. Deterministic fallback template extended to fill every field. Prompt version bumped; JSONB stores it — **no migration**.

## Phase 2 — Score recalibration + verdict labels
3. `_RATING_MIDPOINT` → excellent 88 / good 72 / fair 50 / poor 26 / missing 5 (determinism preserved; tests updated to new bands).
4. Score **verdict labels** (new helper, exposed in API + UI): ≥80 "Interview-ready", 65–79 "Needs work", 45–64 "Will get screened out", <45 "Instant-reject pile" + one-line explanation (feeds the scorecard subtitle like the reference's "Needs Work / Moderate ATS compatibility…").

## Phase 3 — Backend plumbing
5. `RoastReport` schema in `app/schemas/report.py`; pipeline stores it in `final_report` (alongside existing keys); `AnalysisDetailResponse` gains `reality_check: RoastReport | None`; legacy analyses without it render the old layout gracefully.
6. Scorecard payload: `score_verdict` (label + line) added to the detail response; category cards computed frontend-side from existing `breakdown` (ATS ← ats_compatibility, Impact & Language ← content_quality, Completeness ← deterministic section_completeness %, Job Match ← job_match or "locked" when absent).

## Phase 4 — Result page redesign (reference layout, Ember theme)
7. **Scorecard header**: ring (animated, unchanged) + 4 weighted category cards (weight %, score, mini progress bar; Job Match shows "— / 100, Paste a job description to unlock" when absent) + verdict label + benchmark line ("Benchmark: senior engineering cohort, 2026 market").
8. **Unfiltered Recruiter Reality Check** section: flame mark + "Zero-Sugarcoating" badge, `headline_verdict` as the section H2, verdict summary paragraph, **5-Second Recruiter First Impression** quote block, **Fatal Application Poison Points** (red ✕ items), **Rejection Probability Across 3 Markets** cards (verdict chip color-coded + analysis + MISSING SIGNALS chips). Existing roast card, findings, breakdown, expert verdicts stay below.
9. Upload page copy mentions the harsher panel ("Zero sugarcoating by default").

## Phase 5 — Verification
10. Tests: composer v2 schema (mocked, incl. fallback filling every field), calibration values, API field. Full backend chain + frontend build.
11. **Live before/after**: run the SAME resume (your vitthal gupta resume.pdf) — old score 77 vs new run; screenshot old layout memory vs new scorecard + reality check; confirm the score lands meaningfully lower and the verdicts read like the reference. Sync `PROJECT_PLAN.md` + `PROGRESS.md`. No commits.

**Honest expectation-setting:** prompts change tone and calibration — measured via the live before/after run; the structural harshness comes from the recalibrated bands, which is deterministic.