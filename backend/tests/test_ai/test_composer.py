"""Unit tests for the roast composer (call_ai mocked — no real API)."""

import pytest

from app.ai import composer as composer_module
from app.ai.composer import compose_roast
from app.ai.provider import AIResult
from app.common.exceptions import AIEvaluationError
from app.schemas.report import AggregatedResults, ReportItem, ScoringResult


def _aggregated() -> AggregatedResults:
    return AggregatedResults(
        critical_issues=[
            ReportItem(text="Nine-month gap unexplained", source="recruiter")
        ],
        warnings=[
            ReportItem(text="Kubernetes claimed but never used", source="technical")
        ],
        suggestions=[
            ReportItem(text="Rewrite the generic opener", source="content_quality")
        ],
        positive_notes=["API latency work quantified"],
        evaluator_summaries={"recruiter": "Solid."},
        failed_evaluators=[],
    )


def _scoring() -> ScoringResult:
    return ScoringResult(
        overall_score=58.4,
        deterministic_score=61.3,
        ai_score=55.5,
        methodology={"ai_partial": False, "failed_evaluators": []},
    )


async def test_compose_roast_returns_ai_prose(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    async def fake_call_ai(**kwargs):
        captured.update(kwargs)
        return AIResult(
            content=" Your biggest problem is that nine-month gap.  ",
            model="gemini/gemini-3.5-flash",
            prompt_tokens=100,
            completion_tokens=50,
        )

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    roast, fallback, usage = await compose_roast(_aggregated(), _scoring())

    assert fallback is False
    assert roast == "Your biggest problem is that nine-month gap."
    # The composer's input carries the score and the findings.
    assert '"overall_score": 58.4' in captured["user_prompt"]
    assert "Nine-month gap unexplained" in captured["user_prompt"]


async def test_compose_roast_falls_back_on_ai_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs):
        raise AIEvaluationError(evaluator="composer", reason="provider down")

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    roast, fallback, usage = await compose_roast(_aggregated(), _scoring())

    assert fallback is True
    # The fallback is a deterministic template of the same findings.
    assert "58.4/100" in roast
    assert "Nine-month gap unexplained" in roast
    assert "API latency work quantified" in roast


async def test_compose_roast_falls_back_on_empty_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs):
        return AIResult(content="   ", model="m")

    monkeypatch.setattr(composer_module, "call_ai", fake_call_ai)

    roast, fallback, usage = await compose_roast(_aggregated(), _scoring())

    assert fallback is True
    assert "58.4/100" in roast


def test_fallback_never_raises() -> None:
    # Direct call — the template must build even from empty findings.
    empty = AggregatedResults()
    roast = composer_module._fallback_roast(empty, _scoring())
    assert "58.4/100" in roast
    assert "unavailable" in roast
