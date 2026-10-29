"""Unit tests for orchestrator execution (AI fully mocked)."""

from typing import Any

import pytest

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
    JobMatchEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)

RESUME: dict[str, Any] = {"contact_info": {"name": "Jane Doe"}}

CONTEXT: dict[str, Any] = {
    "target_role": "backend_dev",
    "job_description": None,
    "custom_instructions": None,
    "role_slug": "backend_dev",
}

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
    JobMatchEvaluatorOutput: {
        "summary": "Strong backend fit.",
        "match_rating": "good",
        "matched_skills": ["Python", "PostgreSQL"],
        "missing_skills": ["Kubernetes operations"],
        "recommendations": ["Quantify API scale"],
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
    assert set(get_evaluators_for_mode("jd_based")) == {
        "recruiter",
        "ats",
        "technical",
        "content_quality",
        "job_matcher",
    }
    assert get_evaluators_for_mode("made_up") == {}
    assert set(get_evaluators_for_mode("general")) == {
        "recruiter",
        "ats",
        "technical",
        "content_quality",
    }


async def test_role_based_runs_job_matcher_with_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_call_ai_dispatch(monkeypatch, fail_for=None)
    captured: list[dict[str, Any]] = []

    async def capture_user_prompt(**kwargs: Any):
        captured.append(kwargs)
        model = kwargs["response_model"]
        return AIResult(
            content="json",
            model="test-model",
            data=model.model_validate(_PAYLOADS[model]),
        )

    monkeypatch.setattr(evaluator_base, "call_ai", capture_user_prompt)

    results = await run_evaluations(RESUME, "role_based", CONTEXT)

    assert "job_matcher" in results.outputs
    assert results.failed == {}
    # Every evaluator's user prompt carries the role context.
    assert len(captured) == 5
    assert all("TARGET ROLE" in c["user_prompt"] for c in captured)
    assert all("backend_dev" in c["user_prompt"] for c in captured)


async def test_job_matcher_fails_fast_without_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """role_based without target_role/jd context fails only the matcher."""
    _patch_call_ai_dispatch(monkeypatch, fail_for=None)

    results = await run_evaluations(RESUME, "role_based", context=None)

    assert set(results.failed) == {"job_matcher"}
    assert len(results.outputs) == 4
