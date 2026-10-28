"""AI orchestrator - coordinates evaluator execution for analysis modes."""

from typing import Any

from app.ai.evaluators.culture_fit import run_culture_fit_evaluator

EVALUATOR_MAP: dict[str, Any] = {
    "culture_fit": run_culture_fit_evaluator,
}

DEFAULT_EVALUATORS: list[str] = ["culture_fit"]

MODE_EVALUATORS: dict[str, list[str]] = {
    "general": ["culture_fit"],
    "role_based": ["culture_fit"],
    "jd_based": ["culture_fit"],
    "custom": ["culture_fit"],
}


def get_evaluator(evaluator_name: str) -> Any | None:
    """Get an evaluator function by name."""
    return EVALUATOR_MAP.get(evaluator_name)


def get_evaluators_for_mode(mode: str) -> list[Any]:
    """Get all evaluator functions for a given analysis mode."""
    evaluator_names = MODE_EVALUATORS.get(mode, DEFAULT_EVALUATORS)
    return [get_evaluator(name) for name in evaluator_names if get_evaluator(name)]


def get_all_evaluators() -> list[Any]:
    """Get all registered evaluator functions."""
    return [func for func in EVALUATOR_MAP.values() if func is not None]
