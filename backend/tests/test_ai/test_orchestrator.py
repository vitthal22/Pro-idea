"""Unit tests for orchestrator execution (AI fully mocked)."""

from typing import Any

import pytest

from app.ai import orchestrator as orchestrator_module
from app.ai.evaluators import base as evaluator_base
from app.ai.orchestrator import (
    EvaluatorResults,
    get_evaluators_for_mode,
    run_evaluations,
)
from app.ai.provider import AIResult
from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)

RESUME: dict[str, Any] = {"contact_info": {"name": "Jane Doe"}}

# Valid payload per evaluator, keyed by its output model.
_PAYLOADS: dict[type, dict[str, Any]] = {
    RecruiterEvaluatorOutput: {
        "summary": "Solid.",
        "first_impression": "average",
        "first_impression_reason": "Generic opener.",
        "experience_relevance_rating": "good",
        "credibility_rating": "high",
        "red_flags": [],
        "would_shortlist": True,
        "would_shortlist_reason": "Relevant experience",
    },
    ATSEvaluatorOutput: {
        "summary": "Parseable.",
        "ats_readiness_rating": "fair",
    },
    TechnicalEvaluatorOutput: {
        "summary": "Evidenced.",
        "technical_depth_rating": "good",
    },
    ContentQualityEvaluatorOutput: {
        "summary": "Generic.",
        "writing_quality_rating": "fair",
        "quantification_rating": "poor",
    },
}


def _patch_call_ai_dispatch(monkeypatch: pytest.MonkeyPatch, fail_for: type | None):
    """Fake call_ai: answers per response_model; raises for ``fail_for``."""

    async def fake_call_ai(**kwargs: Any):
        model = kwargs["response_model"]
        if fail_for is not None and model is fail_for:
            raise RuntimeError("simulated AI outage")
        return AIResult(
            content="json",
            model="test-model",
            data=model.model_validate(_PAYLOADS[model]),
        )

    monkeypatch.setattr(evaluator_base, "call_ai", fake_call_ai)


async def test_all_evaluators_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_call_ai_dispatch(monkeypatch, fail_for=None)

    results = await run_evaluations(RESUME, "general")

    assert set(results.outputs) == {"recruiter", "ats", "technical", "content_quality"}
    assert results.failed == {}
    assert len(results.usage) == 4
    assert all(usage.model == "test-model" for usage in results.usage)


async def test_single_failure_does_not_abort_the_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_call_ai_dispatch(monkeypatch, fail_for=TechnicalEvaluatorOutput)

    results = await run_evaluations(RESUME, "general")

    assert set(results.outputs) == {"recruiter", "ats", "content_quality"}
    assert set(results.failed) == {"technical"}
    assert "simulated AI outage" in results.failed["technical"]
    assert len(results.usage) == 3


async def test_all_failures_yield_empty_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Fail everything: dispatch raises for every model.
    async def fake_call_ai(**kwargs: Any):
        raise RuntimeError("total outage")

    monkeypatch.setattr(evaluator_base, "call_ai", fake_call_ai)

    results = await run_evaluations(RESUME, "general")

    assert results.outputs == {}
    assert set(results.failed) == {"recruiter", "ats", "technical", "content_quality"}
    assert isinstance(results, EvaluatorResults)
    assert set(results.failed_names) == set(results.failed)


def test_unknown_mode_returns_no_evaluators() -> None:
    assert get_evaluators_for_mode("jd_based") == {}
    assert get_evaluators_for_mode("general") == orchestrator_module.EVALUATOR_MAP
