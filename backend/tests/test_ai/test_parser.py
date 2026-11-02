"""Unit tests for the AI resume parser (call_ai mocked — no real API)."""

import json
from typing import Any

import pytest

from app.ai import parser as parser_module
from app.ai.parser import (
    _USER_PROMPT_PREFIX,
    MAX_RESUME_CHARS,
    parse_resume,
)
from app.ai.prompts.parser import PARSER_SYSTEM_PROMPT
from app.ai.provider import AIResult
from app.common.exceptions import AIEvaluationError
from app.config import settings
from app.schemas.resume import StructuredResume

_PAYLOAD: dict[str, Any] = {
    "contact_info": {"name": "Vitthal Gupta", "email": "vitthal@example.com"},
    "experience": [
        {
            "job_title": "Backend Developer",
            "company": "Acme",
            "bullet_points": ["Built APIs", "Cut latency 40%"],
        }
    ],
    "skills": ["Python", "FastAPI", "PostgreSQL"],
}


def _ai_result(data: StructuredResume | None) -> AIResult:
    content = json.dumps(_PAYLOAD) if data is not None else ""
    return AIResult(content=content, model="test-model", data=data)


def _capture_call_ai(
    monkeypatch: pytest.MonkeyPatch, data: StructuredResume | None
) -> dict[str, Any]:
    """Patch parser.call_ai with a fake that records its kwargs."""
    captured: dict[str, Any] = {}

    async def fake_call_ai(**kwargs: Any):
        captured.update(kwargs)
        return _ai_result(data)

    monkeypatch.setattr(parser_module, "call_ai", fake_call_ai)
    return captured


async def test_parse_resume_returns_structured_resume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_call_ai(monkeypatch, StructuredResume.model_validate(_PAYLOAD))

    resume = await parse_resume("Vitthal Gupta — Backend Developer at Acme…")

    assert isinstance(resume, StructuredResume)
    assert resume.contact_info.name == "Vitthal Gupta"
    assert resume.experience[0].company == "Acme"
    assert resume.skills == ["Python", "FastAPI", "PostgreSQL"]
    assert captured["response_model"] is StructuredResume
    assert captured["system_prompt"] == PARSER_SYSTEM_PROMPT


async def test_parse_resume_truncates_long_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_call_ai(monkeypatch, StructuredResume.model_validate(_PAYLOAD))

    await parse_resume("x" * (MAX_RESUME_CHARS + 5_000))

    assert captured["user_prompt"] == _USER_PROMPT_PREFIX + "x" * MAX_RESUME_CHARS


async def test_parse_resume_uses_fast_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_call_ai(monkeypatch, StructuredResume.model_validate(_PAYLOAD))

    await parse_resume("short resume")

    assert captured["model"] == settings.ai_fast_model


async def test_parse_resume_raises_when_no_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _capture_call_ai(monkeypatch, None)

    with pytest.raises(AIEvaluationError):
        await parse_resume("some resume text")
