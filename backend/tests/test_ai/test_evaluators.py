"""Unit tests for the four evaluators (call_ai mocked — no real API)."""

from typing import Any

import pytest
from pydantic import BaseModel

from app.ai.evaluators import ats, content_quality, recruiter, technical
from app.ai.evaluators import base as evaluator_base
from app.ai.evaluators.base import compose_user_prompt
from app.ai.provider import AIResult
from app.common.exceptions import AIEvaluationError
from app.schemas.evaluators import (
    ATSEvaluatorOutput,
    ContentQualityEvaluatorOutput,
    RecruiterEvaluatorOutput,
    TechnicalEvaluatorOutput,
)

RESUME: dict[str, Any] = {
    "contact_info": {"name": "Jane Doe"},
    "skills": ["Python", "SQL"],
}

# (evaluator function, its output model, a valid mock payload for the model)
_CASES: list[tuple[Any, type[BaseModel], dict[str, Any]]] = [
    (
        recruiter.run_recruiter_evaluator,
        RecruiterEvaluatorOutput,
        {
            "summary": "Solid mid-level resume.",
            "first_impression": "average",
            "first_impression_reason": "Clear layout but generic summary.",
            "experience_relevance_rating": "good",
            "experience_relevance_findings": ["Two relevant roles since 2021"],
            "credibility_rating": "medium",
            "credibility_flags": ["Seniority jump without supporting detail"],
            "red_flags": ["Nine-month gap left unexplained"],
            "would_shortlist": True,
            "would_shortlist_reason": "Relevant recent experience",
        },
    ),
    (
        ats.run_ats_evaluator,
        ATSEvaluatorOutput,
        {
            "summary": "Mostly parseable.",
            "ats_readiness_rating": "fair",
            "formatting_issues": ["Two-column layout near the header"],
            "missing_keywords": ["CI/CD", "unit testing"],
        },
    ),
    (
        technical.run_technical_evaluator,
        TechnicalEvaluatorOutput,
        {
            "summary": "Backend skills evidenced.",
            "technical_depth_rating": "good",
            "identified_stack": ["FastAPI", "PostgreSQL"],
            "gaps": ["Kubernetes listed but never used"],
            "strengths": ["API latency work quantified"],
        },
    ),
    (
        content_quality.run_content_quality_evaluator,
        ContentQualityEvaluatorOutput,
        {
            "summary": "Clear but generic.",
            "writing_quality_rating": "fair",
            "generic_language_issues": ["'passionate team player'"],
            "quantification_rating": "poor",
            "clarity_findings": ["Two overlapping roles dated 2021"],
        },
    ),
]


def _patch_call_ai(
    monkeypatch: pytest.MonkeyPatch, model: type[BaseModel], payload: dict[str, Any]
) -> None:
    """Patch base.call_ai so it returns a validated instance of ``model``."""

    async def fake_call_ai(**kwargs: Any):
        return AIResult(
            content=str(payload), model="test-model", data=model.model_validate(payload)
        )

    monkeypatch.setattr(evaluator_base, "call_ai", fake_call_ai)


@pytest.mark.parametrize(
    "evaluator,model,payload",
    _CASES,
    ids=["recruiter", "ats", "technical", "content_quality"],
)
async def test_evaluator_returns_validated_output(
    monkeypatch: pytest.MonkeyPatch,
    evaluator: Any,
    model: type[BaseModel],
    payload: dict[str, Any],
) -> None:
    _patch_call_ai(monkeypatch, model, payload)

    output, usage = await evaluator(RESUME)

    assert isinstance(output, model)
    assert usage.model == "test-model"


@pytest.mark.parametrize(
    "evaluator,model,payload",
    _CASES,
    ids=["recruiter", "ats", "technical", "content_quality"],
)
async def test_evaluator_raises_when_ai_returns_no_data(
    monkeypatch: pytest.MonkeyPatch,
    evaluator: Any,
    model: type[BaseModel],
    payload: dict[str, Any],
) -> None:
    async def fake_call_ai(**kwargs: Any):
        return AIResult(content="", model="test-model", data=None)

    monkeypatch.setattr(evaluator_base, "call_ai", fake_call_ai)

    with pytest.raises(AIEvaluationError):
        await evaluator(RESUME)


def test_compose_user_prompt_serializes_resume_as_json() -> None:
    prompt = compose_user_prompt({"name": "Jane", "skills": ["Python"]})

    assert prompt.startswith("RESUME DATA (JSON):")
    assert '"name": "Jane"' in prompt
    assert '"Python"' in prompt
