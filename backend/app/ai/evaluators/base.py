"""Shared evaluator plumbing — one pattern for every evaluator.

An evaluator is a pure function: structured resume data in, validated
Pydantic output out. ``run_evaluator`` owns everything the four evaluators
share (user-prompt composition, the ``call_ai`` invocation, output
validation, error wrapping), so each evaluator file only states its name,
prompt, schema, and focus.
"""

from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.provider import call_ai
from app.common.exceptions import AIEvaluationError

T = TypeVar("T", bound=BaseModel)


def compose_user_prompt(resume_data: dict[str, Any]) -> str:
    """Serialize the parsed resume as the evaluator's user prompt."""
    return (
        "RESUME DATA (JSON):\n"
        f"{json.dumps(resume_data, ensure_ascii=False, default=str)}"
    )


async def run_evaluator(
    *,
    name: str,
    system_prompt: str,
    response_model: type[T],
    resume_data: dict[str, Any],
) -> T:
    """Run one evaluator: prompt → AI call → validated output.

    Raises:
        AIEvaluationError: If the AI call fails or the output does not
            validate against ``response_model``.
    """
    result = await call_ai(
        system_prompt=system_prompt,
        user_prompt=compose_user_prompt(resume_data),
        response_model=response_model,
    )
    if not isinstance(result.data, response_model):
        raise AIEvaluationError(
            evaluator=name, reason="model returned no structured evaluation"
        )
    return result.data
