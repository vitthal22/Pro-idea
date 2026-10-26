---
name: create-prompt
description: Create a new versioned prompt for the AI pipeline
---

## Prerequisites

- Understanding of prompt engineering for structured outputs
- Existing prompt in `app/ai/prompts/` to use as reference

## Steps

1. **Create the prompt file** in `app/ai/prompts/<category>/<name>.py`
   - Categories: `evaluators/`, `roles/`, `modes/`, root level for parser/composer

2. **Export these required constants:**
   ```python
   VERSION = "1.0.0"  # Semantic versioning
   SYSTEM_PROMPT = """..."""
   USER_PROMPT_TEMPLATE = """..."""
   ```

3. **Write the system prompt:**
   - Start with role definition: "You are a [specific role with expertise]..."
   - Define the output format explicitly
   - List constraints and rules
   - Include 1-2 examples of expected output quality
   - Set the tone (for roast evaluators: "Be brutally honest but constructive")
   - Keep under 2000 words

4. **Write the user prompt template:**
   - Use `{placeholder}` syntax for dynamic data
   - Structure clearly with sections
   - Use delimiters for user-provided data:
     ```
     === RESUME DATA START ===
     {resume_data}
     === RESUME DATA END ===
     ```

5. **Compose the full prompt** in `app/ai/prompts/__init__.py`
   - Add a composition function that combines system + user prompt parts
   - Support mode-specific and role-specific prompt fragments

6. **Track versions** in the database
   - When analysis is created, store which prompt version was used
   - Enable reproduction of past results

## Prompt Writing Rules

- Never tell the AI to "make up" data — work with what's provided
- Always specify the output format (JSON schema or field descriptions)
- Use concrete examples, not abstract instructions
- Separate instructions from data with clear delimiters
- Include error handling instructions: "If information is missing, state 'Not provided' rather than guessing"
- For roast prompts: "Every criticism must explain: what's wrong, why it matters, how a recruiter sees it, how to fix it"

## Verification

- Test the prompt with a sample resume and verify output matches the expected schema
- Check that the prompt version is correct
- Verify the prompt is loadable from the prompts module (not hardcoded elsewhere)

## Common Mistakes

- Writing prompts that are too long (>2000 words) — AI performance degrades
- Not including output format instructions — AI returns unstructured text
- Hardcoding prompts in evaluator code instead of the prompts module
- Not versioning prompts — impossible to reproduce past results
- Forgetting delimiters for user data — prompt injection risk
