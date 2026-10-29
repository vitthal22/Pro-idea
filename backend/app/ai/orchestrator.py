"""Evaluator registry and parallel execution.

``run_evaluations`` is the pipeline's evaluation stage: it runs every
evaluator for the mode concurrently and never lets one failure abort the
rest — a failing evaluator is recorded in ``failed`` and the pipeline
continues with the survivors (scores renormalize; see ``scoring.py``).

Mode wiring (ARCHITECTURE §4 Step 5, MVP):
- ``general``    → Recruiter + ATS + Technical + Content Quality
- ``role_based`` → all above + Job Matcher (requires ``target_role``)
- ``jd_based``   → all above + Job Matcher (requires ``job_description``)
- ``custom``     → general set; ``custom_instructions`` flow into every
  evaluator prompt and the composer as "additional focus"

``context`` carries ``target_role`` / ``job_description`` /
``custom_instructions`` and is appended to every evaluator's user prompt.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from app.ai.evaluators.ats import run_ats_evaluator
from app.ai.evaluators.content_quality import run_content_quality_evaluator
from app.ai.evaluators.job_matcher import run_job_matcher_evaluator
from app.ai.evaluators.recruiter import run_recruiter_evaluator
from app.ai.evaluators.technical import run_technical_evaluator
from app.ai.provider import AIResult

logger = logging.getLogger("app.ai.orchestrator")

EvaluatorFn = Callable[
    [dict[str, Any], dict[str, Any] | None],
    Awaitable[tuple[BaseModel, AIResult]],
]

_GENERAL_EVALUATORS: dict[str, EvaluatorFn] = {
    "recruiter": run_recruiter_evaluator,
    "ats": run_ats_evaluator,
    "technical": run_technical_evaluator,
    "content_quality": run_content_quality_evaluator,
}

_MODE_EVALUATORS: dict[str, dict[str, EvaluatorFn]] = {
    "general": _GENERAL_EVALUATORS,
    "role_based": {
        **_GENERAL_EVALUATORS,
        "job_matcher": run_job_matcher_evaluator,
    },
    "jd_based": {
        **_GENERAL_EVALUATORS,
        "job_matcher": run_job_matcher_evaluator,
    },
    # custom runs the general set; custom_instructions reach every
    # evaluator via the analysis context (no extra evaluator).
    "custom": _GENERAL_EVALUATORS,
}


@dataclass(slots=True)
class EvaluatorResults:
    """Outcome of one evaluation stage.

    ``outputs`` maps surviving evaluator names to their validated outputs;
    ``failed`` maps failed names to reasons (a failed evaluator is never
    scored as zero downstream — it is dropped and weights renormalize);
    ``usage`` carries one ``AIResult`` per successful AI call for cost
    tracking.
    """

    outputs: dict[str, BaseModel] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)
    usage: list[AIResult] = field(default_factory=list)

    @property
    def failed_names(self) -> list[str]:
        return list(self.failed)


def get_evaluators_for_mode(mode: str) -> dict[str, EvaluatorFn]:
    """Evaluator functions to run for ``mode`` (empty for unwired modes)."""
    return _MODE_EVALUATORS.get(mode, {})


async def run_evaluations(
    resume_data: dict[str, Any],
    mode: str,
    context: dict[str, Any] | None = None,
) -> EvaluatorResults:
    """Run all evaluators for ``mode`` in parallel; failures never abort.

    Args:
        resume_data: Parsed resume (``StructuredResume.model_dump()``).
        mode: Analysis mode — must be a wired one.
        context: Analysis context (``target_role`` / ``job_description`` /
            ``custom_instructions``) forwarded to every evaluator.

    Returns:
        Surviving outputs, failed evaluators with reasons, and per-call
        token usage.
    """
    evaluators = get_evaluators_for_mode(mode)
    results = EvaluatorResults()
    if not evaluators:
        return results

    outcomes = await asyncio.gather(
        *(fn(resume_data, context) for fn in evaluators.values()),
        return_exceptions=True,
    )
    for name, outcome in zip(evaluators, outcomes, strict=True):
        if isinstance(outcome, BaseException):
            results.failed[name] = str(outcome)
            logger.warning("Evaluator '%s' failed: %s", name, outcome)
            continue
        output, usage = outcome
        results.outputs[name] = output
        results.usage.append(usage)
    return results
