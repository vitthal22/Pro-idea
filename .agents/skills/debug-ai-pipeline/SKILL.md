---
name: debug-ai-pipeline
description: Debug failures in the AI evaluation pipeline
---

## Prerequisites

- An analysis that failed or produced unexpected results
- Access to database and application logs

## Debugging Steps

### 1. Check Analysis Status
Look at the `analyses` table for the failed analysis:
```sql
SELECT status, error_message, prompt_versions_used, ai_model_used
FROM analyses WHERE id = '<analysis_id>';
```
Note which step it failed at: extracting, parsing, evaluating, aggregating, scoring, composing.

### 2. Check Prompt Versions
```sql
SELECT prompt_versions_used FROM analyses WHERE id = '<analysis_id>';
```
Verify the correct prompt versions were loaded. If versions are missing, the prompt module may not be exporting VERSION correctly.

### 3. Check Token Usage
```sql
SELECT ai_model, prompt_tokens, completion_tokens, cost_usd
FROM analysis_usage WHERE analysis_id = '<analysis_id>';
```
- Zero tokens = AI call never happened (check network/auth)
- Very high tokens = prompt too long (truncate resume data)
- Normal tokens but bad output = prompt quality issue

### 4. Add Logging at Evaluator Level
Temporarily add logging to the failing evaluator:
```python
import logging
logger = logging.getLogger(__name__)

async def run_failing_evaluator(resume_data, context):
    logger.info(f"Starting evaluator with model: {context.model}")
    logger.info(f"Resume data length: {len(resume_data.model_dump_json())}")

    messages = [...]
    logger.info(f"System prompt length: {len(messages[0]['content'])}")

    result, usage = await call_ai(model=context.model, messages=messages, response_model=OUTPUT_SCHEMA)
    logger.info(f"AI response received, tokens: {usage}")

    return result
```

### 5. Common Issues and Fixes

| Symptom | Likely Cause | Fix |
|---|---|---|
| Invalid JSON from AI | Schema too complex or model doesn't support structured output | Simplify schema or switch model |
| Incomplete output | max_tokens too low | Increase token limit |
| Wrong structure | Prompt doesn't clearly specify format | Add output format examples to prompt |
| Rate limiting (429) | Too many parallel requests | Add delay between evaluator calls or reduce concurrency |
| Token limit exceeded | Resume data too long | Truncate raw text, keep structured data |
| Empty evaluator result | AI returned empty response | Check for empty content in response handling |
| Timeout | AI provider slow | Increase timeout or use faster model |

### 6. Retry Strategy
- Extraction failures: retry once, then try OCR
- Parsing failures: retry once with stricter prompt
- Evaluator failures: retry up to 3 times with backoff (1s, 2s, 4s)
- If all retries fail: skip evaluator, note in results, continue pipeline

## Verification

After fixing, re-run the analysis and verify:
- All evaluators complete successfully
- Output validates against Pydantic schema
- Scoring produces meaningful results
- Final roast is generated
