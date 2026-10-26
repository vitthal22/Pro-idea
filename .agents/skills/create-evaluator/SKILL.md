---
name: create-evaluator
description: Add a new AI evaluator to the resume analysis pipeline
---

## Prerequisites

- Understanding of Pydantic schemas and structured AI outputs
- Existing evaluator in `app/ai/evaluators/` to use as reference

## Steps

1. **Define the output Pydantic schema** in `app/schemas/evaluators.py`
   ```python
   class NewEvaluatorOutput(BaseModel):
       summary: str = Field(description="Overall assessment summary")
       critical_issues: list[CriticalIssue] = Field(description="Issues that must be fixed")
       strengths: list[str] = Field(description="What the resume does well")
       # Add evaluator-specific fields with descriptions
   ```
   - Use `Field(description=...)` for EVERY field — descriptions become part of the AI prompt
   - Use `Literal` for enum-like fields
   - Always include: summary, critical_issues, strengths

2. **Create the prompt file** in `app/ai/prompts/evaluators/<name>.py`
   ```python
   VERSION = "1.0.0"
   SYSTEM_PROMPT = """You are a [role description]...

   ## Output Format
   Return a JSON object with:
   - summary: Overall assessment
   - critical_issues: Array of {title, description, category, severity, improvement, recruiter_perspective}
   - strengths: Array of strings

   ## Rules
   - Be specific, not generic
   - Every criticism must include how to improve
   - Focus on [specific area]"""
   OUTPUT_SCHEMA = NewEvaluatorOutput  # The Pydantic model from step 1
   ```

3. **Create the evaluator function** in `app/ai/evaluators/<name>.py`
   ```python
   from app.ai.provider import call_ai
   from app.ai.prompts.evaluators.<name> import SYSTEM_PROMPT, OUTPUT_SCHEMA, VERSION
   from app.schemas.resume import ResumeStructuredData

   async def run_<name>_evaluator(
       resume_data: ResumeStructuredData,
       context: EvaluationContext,
   ) -> NewEvaluatorOutput:
       messages = [
           {"role": "system", "content": SYSTEM_PROMPT},
           {"role": "user", "content": f"Analyze this resume:\n\n{resume_data.model_dump_json()}"},
       ]

       result, usage = await call_ai(
           model=context.model,
           messages=messages,
           response_model=OUTPUT_SCHEMA,
       )

       return result
   ```

4. **Register in the orchestrator** (`app/ai/orchestrator.py`)
   - Add evaluator to the evaluator map
   - Set which analysis modes use this evaluator

5. **Write tests** in `tests/test_ai/evaluators/test_<name>.py`
   - Mock `app.ai.provider.call_ai()` to return a predefined Pydantic object
   - Test with sample resume data
   - Test validation failure handling

## Verification

- Run evaluator with a sample resume and verify output structure
- Check that the evaluator is included in the correct analysis modes
- Verify prompt version is tracked in analysis records

## Common Mistakes

- Forgetting `Field(description=...)` on schema fields (AI won't know what to put there)
- Not handling AI output validation failures gracefully
- Hardcoding the model name instead of using `context.model`
- Not registering the evaluator in the orchestrator
