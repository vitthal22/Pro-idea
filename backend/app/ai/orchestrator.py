"""Evaluator registry — which evaluators exist and which run per mode.

Phase-2 note: execution (parallel gather, partial-failure handling) lives in
this module too once the pipeline is wired; today it only registers the
evaluators built in Phase 1 and maps the ``general`` mode. ``role_based``/
``jd_based``/``custom`` modes additionally need the Job Matcher evaluator
and are not wired yet (out of MVP scope for now).
"""

from typing import Any

from app.ai.evaluators.ats import run_ats_evaluator
from app.ai.evaluators.content_quality import run_content_quality_evaluator
from app.ai.evaluators.recruiter import run_recruiter_evaluator
from app.ai.evaluators.technical import run_technical_evaluator

GENERAL_EVALUATORS = [
    run_recruiter_evaluator,
    run_ats_evaluator,
    run_technical_evaluator,
    run_content_quality_evaluator,
]

_MODE_EVALUATORS: dict[str, list[Any]] = {
    "general": GENERAL_EVALUATORS,
}


def get_evaluators_for_mode(mode: str) -> list[Any]:
    """Evaluator functions to run for ``mode`` (empty for unwired modes)."""
    return _MODE_EVALUATORS.get(mode, [])
