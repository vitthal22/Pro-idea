# Skills — Reusable Task Instructions

> Follow these step-by-step instructions when performing common development tasks.
> Each skill is a self-contained procedure that any AI assistant can follow.

---

## Skill 1: Create a New API Endpoint

```
1. Define the Pydantic request/response schemas in app/api/schemas/<module>.py
2. Create the router function in app/api/v1/<module>.py
3. Add response_model and status_code to the decorator
4. Inject dependencies (db, current_user) via function parameters
5. Call the appropriate service method (not business logic in the router)
6. Register the router in app/api/v1/router.py if it's a new module
7. Write tests in tests/test_api/test_<module>.py
```

**Template:**
```python
@router.post("/", response_model=SomeResponse, status_code=201)
async def create_thing(
    payload: SomeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SomeResponse:
    service = ThingService(db)
    result = await service.create(payload, current_user)
    return result
```

---

## Skill 2: Create a New AI Evaluator

```
1. Define the output Pydantic schema in app/schemas/evaluators.py
   - Use Field(description=...) for every field (becomes part of the prompt)
   - Use Literal for enum-like fields
   - Always include: summary, critical_issues, strengths

2. Create the prompt file in app/ai/prompts/evaluators/<name>.py
   - Export: SYSTEM_PROMPT (str), OUTPUT_SCHEMA (Pydantic model), VERSION (str)
   - System prompt should define the evaluator's role and expertise

3. Create the evaluator function in app/ai/evaluators/<name>.py
   - Function signature: async def run_<name>_evaluator(resume_data, context) -> <Schema>
   - Load prompt from the prompts module
   - Call AI via app.ai.provider.call_ai()
   - Validate output with Pydantic
   - Return structured result

4. Register the evaluator in app/ai/orchestrator.py
   - Add to the evaluator map for relevant analysis modes

5. Write tests in tests/test_ai/evaluators/test_<name>.py
   - Mock the AI provider call
   - Test with valid structured resume data
   - Test AI output validation failure handling
```

---

## Skill 3: Create a New Prompt

```
1. Create file in app/ai/prompts/<category>/<name>.py
2. Export these constants:
   - VERSION: str = "1.0.0"
   - SYSTEM_PROMPT: str = """..."""
   - USER_PROMPT_TEMPLATE: str = """..."""
3. System prompt should include:
   - Role definition ("You are a...")
   - Output format instructions
   - Constraints and rules
   - Tone guidance (for roast evaluators)
4. User prompt template should use .format() or f-string placeholders
5. Add prompt composition logic in app/ai/prompts/__init__.py
```

**Prompt writing rules:**
- Never tell the AI to "make up" data — it works with what's provided
- Always specify the output format explicitly
- Always include examples of good/bad output in the system prompt
- Use delimiters for user-provided data to prevent injection
- Keep system prompts under 2000 words

---

## Skill 4: Add a New Analysis Mode

```
1. Add the mode to the AnalysisType enum in app/schemas/analyses.py
2. Create mode configuration in app/ai/prompts/modes/<mode>.py
   - Define which evaluators run for this mode
   - Define scoring category weights
   - Define any mode-specific prompt fragments
3. Update the orchestrator (app/ai/orchestrator.py) to route to the right evaluators
4. Update the scoring engine (app/ai/scoring.py) with mode-specific weights
5. Add API request validation in app/api/schemas/analyses.py
6. Write integration tests for the new mode
```

---

## Skill 5: Add a New Database Model

```
1. Create the model in app/models/<name>.py
   - Inherit from app.models.base.Base
   - Use UUID primary key
   - Add created_at and updated_at timestamps
   - Define relationships with back_populates
2. Create Alembic migration: poetry run alembic revision --autogenerate -m "add <name> table"
3. Review the generated migration in alembic/versions/
4. Add Pydantic schema in app/schemas/<name>.py with model_config = {"from_attributes": True}
5. Add repository/service methods in app/services/<name>.py
6. Write tests
```

---

## Skill 6: Debug AI Pipeline Issues

```
1. Check the analysis record status — what step failed?
2. Check prompt_versions_used in the analysis record — correct prompts loaded?
3. Check analysis_usage for token counts — did the call complete?
4. Add logging at the evaluator level:
   - Log the composed prompt (system + user messages)
   - Log the raw AI response before parsing
   - Log the Pydantic validation result
5. Common issues:
   - AI returns invalid JSON → check response_format / schema compatibility
   - AI returns incomplete output → increase max_tokens or simplify schema
   - AI returns wrong structure → improve prompt with examples
   - Rate limiting → check litellm retry config
   - Token limit exceeded → truncate resume data, not the prompt
```

---

## Skill 7: Write Tests for This Project

```
1. Unit tests (fast, mocked AI):
   - Mock app.ai.provider.call_ai() to return predefined Pydantic objects
   - Test evaluator logic with mock AI responses
   - Test scoring engine with known inputs
   - Test prompt composition with sample data

2. API tests (httpx + AsyncClient):
   - Use the test client fixture from conftest.py
   - Test all response codes (200, 201, 400, 401, 404)
   - Test request validation (invalid payloads)
   - Test auth (missing token, expired token)

3. Integration tests (real AI, marked):
   - @pytest.mark.integration
   - Use a test OpenAI key or a cheap model
   - Test full pipeline with a sample resume
   - Verify output structure matches Pydantic schema

4. Fixture files go in tests/fixtures/
   - sample.pdf, sample.docx, sample.txt
   - Never use real user resumes in tests
```

---

## Skill 8: Update Pydantic Schemas Without Breaking API

```
1. Read the existing schema in app/api/schemas/<module>.py or app/schemas/
2. Check all usages of the schema across the codebase
3. For adding new optional fields:
   - Add field with default value: new_field: str | None = None
   - This is backward-compatible
4. For removing fields:
   - First deprecate (add a comment, don't remove yet)
   - Remove after ensuring no consumers depend on it
5. For changing field types:
   - This is a breaking change — version the schema or update all consumers
6. Always run: poetry run ruff check . && poetry run mypy app/ && poetry run pytest
```

---

## Skill 9: Add a New Role Context for Role-Based Analysis

```
1. Create app/ai/prompts/roles/<role_name>.py
2. Export:
   - ROLE_KEY: str = "frontend_dev"  (matches API enum)
   - ROLE_DISPLAY_NAME: str = "Frontend Developer"
   - ROLE_CONTEXT_PROMPT: str = """..."""
3. The context prompt should include:
   - Key skills expected for this role
   - Common project types
   - Technology stack expectations
   - Red flags (e.g., "no frontend projects for a frontend role")
   - What recruiters look for in this role
4. Register in app/ai/prompts/roles/__init__.py (role registry)
5. Add to the role enum in app/api/schemas/analyses.py
```

---

## Skill 10: Handle a Failing AI Provider

```
1. Check if the issue is rate limiting:
   - Look for 429 errors in logs
   - Solution: increase retry delay or switch to fallback model
2. Check if the issue is API key:
   - Verify .env has the correct key
   - Check if the key has credits remaining
3. Check if the issue is model-specific:
   - Some models don't support structured output (response_format)
   - Solution: switch to a model that supports it, or parse manually
4. Check if the issue is prompt length:
   - Token limit exceeded → truncate the resume data
   - Keep the system prompt intact, trim the user message
5. Fallback chain: primary → fallback → emergency (degraded quality)
6. Log everything: which model was called, what failed, what was tried
```
