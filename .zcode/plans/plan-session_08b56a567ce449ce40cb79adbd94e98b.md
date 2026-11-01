## Multi-model cascade + per-tier model chains (config-driven, zero hardcoding)

Every model name lives in `.env` — the code contains no model names, it only walks the configured list. `AI_MODEL_CHAIN` (comma-separated, priority order) defines the cascade; `AI_MODEL_CHAIN_FREE` / `AI_MODEL_CHAIN_PRO` map user tiers to their own lists for the future payment release.

Runtime flow: pipeline resolves the user's tier → config gives that tier's list → `call_ai` tries model #1 → on **429/quota** it advances to the next model immediately (no pointless retries against a "retry in 9h" error) → on **transient** errors (500/503/timeout) it retries the same model with backoff first → only fails when the whole list fails.

### 1. Generalized model chain — `app/ai/provider.py` + `config.py`

- New settings: `ai_model_chain: str | None`, `ai_model_chain_free: str | None`, `ai_model_chain_pro: str | None` (comma-separated; all default `None`).
- New helper `resolve_model_chain(tier) -> list[str]`: `free` → `ai_model_chain_free` or default; `pro`/`demo` → `ai_model_chain_pro` or default; default = `ai_model_chain` or the legacy `[AI_MODEL, AI_FAST_MODEL]` pair (fully backward compatible). `ai_fallback_enabled=False` still pins the chain to its head.
- `call_ai` gains `chain: list[str] | None = None` (explicit override; an explicit `model` param still heads the chain).
- **Rate-limit fast-advance**: on `litellm.RateLimitError`, skip that model's remaining retries and move to the next model. Transient errors keep the existing backoff behavior.

### 2. Pipeline threading — tier-aware chains

- `_execute_pipeline` resolves the owner's tier once via `get_user_repository(session).get_by_id(...)` (no migration) and computes `chain = resolve_model_chain(tier)`.
- `chain` threads through `parse_resume`, `run_evaluations` → `run_evaluator`, `compose_roast`, `plan_fixes` (each gains `chain: list[str] | None = None`, passed to `call_ai`). Existing call sites unaffected (default `None`).

### 3. Configuration shipped (`.env` + `.env.example`)

- `AI_MODEL_CHAIN=gemini/gemini-3.5-flash,gemini/gemini-3.5-flash-lite` — today's proven pair, so live behavior is unchanged until quota forces the step-down (which now works mid-pipeline).
- Comments document the known 2026 free-tier candidates (3.5-flash ≈ $0.90/1M in, 3.6-flash ≈ $1.50/1M, 3.5-flash-lite) and warn that **3.8-flash hangs on this machine — do not add without testing** (PROGRESS gotcha). At implementation time I'll query the read-only models-list endpoint with your key to confirm exactly which IDs it can use before finalizing those comments.
- `AI_MODEL_CHAIN_FREE` / `AI_MODEL_CHAIN_PRO` shipped unset with a comment — when payments launch, setting them is the whole rollout.

### 4. Tests

- `tests/test_ai/test_provider.py`: chain resolution (default, `ai_model_chain`, tier overrides, fallback-disabled); **rate-limit fast-advance** — primary raises litellm's real `RateLimitError`, a counting fake proves only ONE primary attempt happened before the fallback served; explicit `chain` override.
- `tests/test_services/test_analysis.py`: pipeline passes the tier-derived chain down (captured by the existing seams). No existing assertions change.

### 5. Verification

- Backend: `npm run check:backend` + `npm test --prefix backend` (actual output reported).
- Live: query the models-list endpoint (read-only, no quota) to confirm the key's usable IDs; then a small `call_ai` script with the primary quota-dead — expected: immediate advance to flash-lite, result served. No full roast (daily quota).
- Frontend: no changes (model names already flow into `analysis_usage.ai_model` / `ai_model_used`).

### Out of scope (seams ready)

API-key rotation, other providers (no keys configured), enforcing paid tiers — when payments ship, `AI_MODEL_CHAIN_FREE`/`PRO` + `users.tier` already carry the policy.