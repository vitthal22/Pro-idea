"""Unit tests for the AI provider wrapper (litellm fully mocked — no real API)."""

from types import SimpleNamespace
from typing import Any

import litellm
import pytest
from pydantic import BaseModel

from app.ai import provider as provider_module
from app.ai.provider import AIResult, call_ai
from app.common.exceptions import AIEvaluationError
from app.config import settings


class _Verdict(BaseModel):
    verdict: str


def _fake_response(
    content: str, prompt_tokens: int = 10, completion_tokens: int = 5
) -> Any:
    """A litellm-shaped response built from SimpleNamespace records."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


@pytest.fixture(autouse=True)
def _provider_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deterministic provider settings; no key is ever sent anywhere."""
    monkeypatch.setattr(provider_module, "RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "ai_model", "gemini/gemini-test-model")
    monkeypatch.setattr(settings, "ai_fast_model", "gemini/gemini-test-fast")
    monkeypatch.setattr(settings, "ai_timeout", 5.0)
    monkeypatch.setattr(settings, "ai_max_tokens", 256)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")


async def test_success_returns_content_and_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_acompletion(**kwargs: Any):
        calls.append(kwargs)
        return _fake_response("roast incoming")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_ai(system_prompt="be honest", user_prompt="resume text")

    assert isinstance(result, AIResult)
    assert result.content == "roast incoming"
    assert result.model == "gemini/gemini-test-model"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5
    assert result.fallback_used is False
    assert result.data is None
    assert len(calls) == 1
    assert calls[0]["model"] == "gemini/gemini-test-model"
    assert calls[0]["api_key"] == "test-key"
    assert calls[0]["timeout"] == 5.0
    assert calls[0]["max_tokens"] == 256
    assert calls[0]["messages"][0] == {"role": "system", "content": "be honest"}
    assert calls[0]["messages"][1] == {"role": "user", "content": "resume text"}


async def test_structured_output_is_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_acompletion(**kwargs: Any):
        calls.append(kwargs)
        return _fake_response('{"verdict": "roast-worthy"}')

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_ai(system_prompt="s", user_prompt="u", response_model=_Verdict)

    assert result.data is not None
    assert result.data.verdict == "roast-worthy"
    # The JSON-schema instruction must be appended to the system prompt
    assert '"verdict"' in calls[0]["messages"][0]["content"]


async def test_invalid_structured_output_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_acompletion(**kwargs: Any):
        calls.append(kwargs)
        if len(calls) < 3:
            return _fake_response("definitely not json")
        return _fake_response('{"verdict": "fine"}')

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_ai(
        system_prompt="s", user_prompt="u", response_model=_Verdict, max_retries=2
    )

    assert result.data is not None
    assert result.data.verdict == "fine"
    # attempt 1: primary + fallback both unusable; attempt 2: primary ok
    assert len(calls) == 3


async def test_fallback_model_used_when_primary_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_acompletion(**kwargs: Any):
        calls.append(kwargs)
        if kwargs["model"] == "gemini/gemini-test-model":
            raise RuntimeError("primary is down")
        return _fake_response("from the fast model")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_ai(system_prompt="s", user_prompt="u")

    assert result.content == "from the fast model"
    assert result.model == "gemini/gemini-test-fast"
    assert result.fallback_used is True
    assert len(calls) == 2


async def test_raises_after_all_attempts_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_acompletion(**kwargs: Any):
        calls.append(kwargs)
        raise RuntimeError("provider down")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    with pytest.raises(AIEvaluationError) as excinfo:
        await call_ai(system_prompt="s", user_prompt="u", max_retries=2)

    assert "provider down" in str(excinfo.value)
    # (2 retries + 1 attempts) × 2 models in the fallback chain
    assert len(calls) == 6


async def test_missing_api_key_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", None)
    called = False

    async def fake_acompletion(**kwargs: Any):
        nonlocal called
        called = True
        return _fake_response("should not happen")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    with pytest.raises(AIEvaluationError) as excinfo:
        await call_ai(system_prompt="s", user_prompt="u")

    assert "GEMINI_API_KEY" in str(excinfo.value)
    assert called is False


async def test_local_provider_needs_no_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_model", "ollama/llama3")
    monkeypatch.setattr(settings, "ai_fast_model", "ollama/llama3-fast")
    monkeypatch.setattr(settings, "gemini_api_key", None)

    async def fake_acompletion(**kwargs: Any):
        assert kwargs["api_key"] is None
        return _fake_response("local answer")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_ai(system_prompt="s", user_prompt="u")

    assert result.content == "local answer"


async def test_missing_usage_defaults_to_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_acompletion(**kwargs: Any):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
        )

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_ai(system_prompt="s", user_prompt="u")

    assert result.prompt_tokens == 0
    assert result.completion_tokens == 0
