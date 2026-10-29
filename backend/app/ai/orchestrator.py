"""Evaluator registry and parallel execution.

``run_evaluations`` is the pipeline's evaluation stage: it runs every
evaluator for the mode concurrently and never lets one failure abort the
rest — a failing evaluator is recorded in ``failed`` and the pipeline
continues with the survivors (scores renormalize; see ``scoring.py``).

Mode wiring: only ``general`` runs today. ``role_based``/``jd_based``/
``custom`` additionally need the Job Matcher evaluator and are unwired
until that lands.
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
from app.ai.evaluators.recruiter import run_recruiter_evaluator
from app.ai.evaluators.technical import run_technical_evaluator
from app.ai.provider import AIResult

logger = logging.getLogger("app.ai.orchestrator")

EvaluatorFn = Callable[[dict[str, Any]], Awaitable[tuple[BaseModel, AIResult]]]

EVALUATOR_MAP: dict[str, EvaluatorFn] = {
    "recruiter": run_recruiter_evaluator,
    "ats": run_ats_evaluator,
    "technical": run_technical_evaluator,
    "content_quality": run_content_quality_evaluator,
}

_MODE_EVALUATORS: dict[str, dict[str, EvaluatorFn]] = {
    "general": EVALUATOR_MAP,
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


async def run_evaluations(resume_data: dict[str, Any], mode: str) -> EvaluatorResults:
    """Run all evaluators for ``mode`` in parallel; failures never abort.

    Args:
        resume_data: Parsed resume (``StructuredResume.model_dump()``).
        mode: Analysis mode — must be a wired one (``general``).

    Returns:
        Surviving outputs, failed evaluators with reasons, and per-call
        token usage.
    """
    evaluators = get_evaluators_for_mode(mode)
    results = EvaluatorResults()
    if not evaluators:
        return results

    outcomes = await asyncio.gather(
        *(fn(resume_data) for fn in evaluators.values()),
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
