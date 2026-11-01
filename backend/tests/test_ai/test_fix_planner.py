"""Unit tests for the fix planner (call_ai mocked — no real API)."""

from typing import Any

import pytest

from app.ai import fix_planner as fix_planner_module
from app.ai.fix_planner import plan_fixes
from app.ai.provider import AIResult
from app.common.exceptions import AIEvaluationError
from app.schemas.evaluators import JobMatchEvaluatorOutput
from app.schemas.report import AggregatedResults, FixPlanReport, ReportItem

_RESUME_DATA: dict[str, Any] = {
    "contact_info": {"name": "Jane Doe", "email": "jane@example.com"},
    "experience": [
        {
            "job_title": "Backend Developer",
            "company": "Acme",
            "start_date": "Jan 2022",
            "bullet_points": ["Improved API performance by 20%"],
        }
    ],
    "skills": ["Python", "FastAPI"],
}

_FIX_PLAN_PAYLOAD: dict[str, Any] = {
    "intro": "Fix the unverified metrics first, then sharpen the opener.",
    "fixes": [
        {
            "issue": "Unverified, duplicated performance claims",
            "severity": "critical",
            "before": "Improved API performance by 20%",
            "after": (
                "Cut checkout API p99 latency 200ms to 140ms (-30%) at "
                "40k requests/day by adding Redis caching"
            ),
            "why": "A real measurement pair and system scale are verifiable.",
        },
        {
            "issue": "Generic opener",
            "severity": "enhancement",
            "before": "Hardworking developer seeking growth",
            "after": "Backend developer: FastAPI + Postgres at 40k req/day",
            "why": "Leads with the stack and scale instead of adjectives.",
        },
    ],
}

_JOB_MATCH = JobMatchEvaluatorOutput(
    summary="Decent backend fit; missing the posting's data emphasis.",
    match_rating="fair",
    matched_skills=["Python", "FastAPI"],
    missing_skills=["PostgreSQL tuning", "Kafka pipelines"],
    alignment_findings=["Resume shows FastAPI but the posting wants Django too"],
    recommendations=["Quantify database work with real query-scale numbers"],
)


def _aggregated() -> AggregatedResults:
    return AggregatedResults(
        critical_issues=[
            ReportItem(
                text="Unverified '20%' metrics across employers",
                source="recruiter",
            )
        ],
        warnings=[
            ReportItem(text="Generic opener with no stack or scale", source="ats")
        ],
        suggestions=[],
        positive_notes=["Real API latency work exists somewhere"],
        evaluator_summaries={"recruiter": "Needs proof."},
        failed_evaluators=[],
    )


async def test_plan_fixes_returns_structured_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_ai(**kwargs: Any) -> AIResult:
        captured.update(kwargs)
        return AIResult(
            content="ok",
            model="gemini/gemini-3.5-flash",
            prompt_tokens=900,
            completion_tokens=300,
            data=FixPlanReport.model_validate(_FIX_PLAN_PAYLOAD),
        )

    monkeypatch.setattr(fix_planner_module, "call_ai", fake_call_ai)

    plan, usage = await plan_fixes(
        _aggregated(),
        _RESUME_DATA,
        job_match=_JOB_MATCH,
        context={
            "target_role": None,
            "job_description": "Build data pipelines with Kafka and Postgres.",
            "custom_instructions": "Focus on my API work",
        },
    )

    assert isinstance(plan, FixPlanReport)
    assert plan.fixes[0].severity == "critical"
    assert plan.fixes[0].after.startswith("Cut checkout API")
    assert usage is not None and usage.prompt_tokens == 900

    prompt = captured["user_prompt"]
    assert "Unverified '20%' metrics" in prompt  # finding text
    assert "Improved API performance by 20%" in prompt  # verbatim resume data
    assert "JOB MATCH ANALYSIS" in prompt
    assert "Kafka pipelines" in prompt  # missing skill reached the prompt
    assert "JOB DESCRIPTION:" in prompt
    assert "Focus on my API work" in prompt
    assert captured["response_model"] is FixPlanReport


async def test_plan_fixes_omits_job_match_block_without_matcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_ai(**kwargs: Any) -> AIResult:
        captured.update(kwargs)
        return AIResult(
            content="ok",
            model="m",
            prompt_tokens=10,
            completion_tokens=10,
            data=FixPlanReport.model_validate(_FIX_PLAN_PAYLOAD),
        )

    monkeypatch.setattr(fix_planner_module, "call_ai", fake_call_ai)

    plan, usage = await plan_fixes(_aggregated(), _RESUME_DATA)

    assert plan is not None
    assert usage is not None
    assert "JOB MATCH ANALYSIS" not in captured["user_prompt"]


async def test_plan_fixes_returns_none_on_ai_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs: Any) -> AIResult:
        raise AIEvaluationError(evaluator="fix_planner", reason="provider down")

    monkeypatch.setattr(fix_planner_module, "call_ai", fake_call_ai)

    plan, usage = await plan_fixes(_aggregated(), _RESUME_DATA)

    assert plan is None
    assert usage is None


async def test_plan_fixes_returns_none_on_unstructured_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call_ai(**kwargs: Any) -> AIResult:
        return AIResult(content="   ", model="m", prompt_tokens=5, completion_tokens=5)

    monkeypatch.setattr(fix_planner_module, "call_ai", fake_call_ai)

    plan, usage = await plan_fixes(_aggregated(), _RESUME_DATA)

    assert plan is None
    assert usage is None
