"""Shared evaluator plumbing — one pattern for every evaluator.

An evaluator is a pure function: structured resume data in, validated
Pydantic output out. ``run_evaluator`` owns everything the evaluators
share (context composition, the ``call_ai`` invocation, output
validation, error wrapping), so each evaluator file only states its name,
prompt, schema, and focus.
"""

from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.provider import AIResult, call_ai
from app.common.exceptions import AIEvaluationError

T = TypeVar("T", bound=BaseModel)

# Context keys appended to the user prompt when present in the analysis
# context (role_based / jd_based / custom modes).
_CONTEXT_LABELS: dict[str, str] = {
    "target_role": "TARGET ROLE",
    "job_description": "JOB DESCRIPTION",
    "custom_instructions": "ADDITIONAL FOCUS (user's own words)",
}

_MAX_CONTEXT_CHARS = 4000  # cap per context block; truncate input, not instructions


def compose_context_lines(context: dict[str, Any] | None) -> list[str]:
    """Render the analysis context as labelled prompt blocks."""
    if not context:
        return []
    lines: list[str] = []
    for key, label in _CONTEXT_LABELS.items():
        value = context.get(key)
        if not value:
            continue
        text = str(value).strip()[:_MAX_CONTEXT_CHARS]
        lines.append(f"{label}:\n{text}")
    return lines


def compose_user_prompt(
    resume_data: dict[str, Any], context: dict[str, Any] | None = None
) -> str:
    """Serialize the parsed resume (plus analysis context) as the user prompt."""
    prompt = (
        "RESUME DATA (JSON):\n"
        f"{json.dumps(resume_data, ensure_ascii=False, default=str)}"
    )
    context_lines = compose_context_lines(context)
    if context_lines:
        prompt += "\n\nANALYSIS CONTEXT:\n" + "\n\n".join(context_lines)
    return prompt


async def run_evaluator(
    *,
    name: str,
    system_prompt: str,
    response_model: type[T],
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[T, AIResult]:
    """Run one evaluator: prompt → AI call → validated output + usage.

    Args:
        name: Evaluator name for logs/errors (e.g. ``"recruiter"``).
        system_prompt: The evaluator's own system prompt.
        response_model: Schema the output must validate against.
        resume_data: Parsed resume (``StructuredResume.model_dump()``).
        context: Optional analysis context (``target_role``,
            ``job_description``, ``custom_instructions``) appended to the
            user prompt for role/JD/custom modes.

    Returns:
        The validated evaluator output and the underlying ``AIResult``
        (token usage is recorded per AI call by the pipeline).

    Raises:
        AIEvaluationError: If the AI call fails or the output does not
            validate against ``response_model``.
    """
    result = await call_ai(
        system_prompt=system_prompt,
        user_prompt=compose_user_prompt(resume_data, context),
        response_model=response_model,
    )
    if not isinstance(result.data, response_model):
        raise AIEvaluationError(
            evaluator=name, reason="model returned no structured evaluation"
        )
    return result.data, result
