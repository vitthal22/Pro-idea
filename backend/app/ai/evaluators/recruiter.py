"""Recruiter evaluator — six-second-screen lens on the resume."""

from __future__ import annotations

from typing import Any

from app.ai.evaluators.base import run_evaluator
from app.ai.prompts.evaluators.recruiter import SYSTEM_PROMPT
from app.ai.provider import AIResult
from app.schemas.evaluators import RecruiterEvaluatorOutput


async def run_recruiter_evaluator(
    resume_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[RecruiterEvaluatorOutput, AIResult]:
    """Screen the resume the way a recruiter's six-second scan would."""
    return await run_evaluator(
        name="recruiter",
        system_prompt=SYSTEM_PROMPT,
        response_model=RecruiterEvaluatorOutput,
        resume_data=resume_data,
        context=context,
    )
