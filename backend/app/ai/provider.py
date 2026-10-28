"""AI provider wrapper — the only module that talks to a model provider.

Routers, services, and evaluators must go through ``call_ai()`` — never
import litellm directly. Provider, model names, API keys, timeouts, and
token caps all come from ``Settings`` (env), so swapping providers is a
one-line ``.env`` change.

Behaviour:

- Async end to end (``litellm.acompletion``) — never blocks the event loop.
- Every call has a hard timeout and a ``max_tokens`` cap.
- Fallback chain: primary model → fast model (enabled via config).
- Retries with exponential backoff; an invalid structured output counts as
  a failed attempt.
- Structured outputs: pass ``response_model`` to get a validated Pydantic
  instance back in ``AIResult.data``.
- Token usage is returned on every result so the pipeline can record it
  in ``analysis_usage``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.common.exceptions import AIEvaluationError
from app.config import settings

logger = logging.getLogger("app.ai.provider")

T = TypeVar("T", bound=BaseModel)

# Settings field holding the API key for each litellm provider prefix.
# Providers absent from this map (e.g. ollama) need no key.
_PROVIDER_API_KEY_FIELD: dict[str, str] = {
    "gemini": "gemini_api_key",
    "google": "gemini_api_key",
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
}

# Seconds before the first retry; doubles on each further attempt.
RETRY_BACKOFF_SECONDS = 0.5

_JSON_INSTRUCTION = (
    "Respond with ONLY a single JSON object that validates against this "
    "JSON schema. No prose, no explanations, no markdown formatting:\n"
)


@dataclass(slots=True)
class AIResult:
    """One successful AI call: raw text, optional parsed data, and usage."""

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    fallback_used: bool = False
    data: Any = None  # populated when response_model is passed


def _api_key_for_model(model: str) -> str | None:
    """API key for the provider routing ``model`` (None for local providers).

    Raises ``AIEvaluationError`` early when a hosted provider has no key
    configured, so the caller gets a clear reason instead of a provider 401.
    """
    prefix = model.split("/", 1)[0] if "/" in model else settings.ai_provider
    field = _PROVIDER_API_KEY_FIELD.get(prefix)
    if field is None:
        return None
    key = getattr(settings, field)
    if not key:
        raise AIEvaluationError(
            evaluator="AI provider",
            reason=f"Provider '{prefix}' is configured but {field.upper()} is not set",
        )
    return key


def _strip_markdown_fences(text: str) -> str:
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text.strip(), re.DOTALL)
    return fenced.group(1) if fenced else text.strip()


def _extract_json_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object found in ``text`` (models add prose)."""
    cleaned = _strip_markdown_fences(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("AI response was JSON but not an object")
    return parsed


def _validate_structured(content: str, response_model: type[T]) -> T:
    """Validate the model's text output against ``response_model``."""
    try:
        return response_model.model_validate(_extract_json_object(content))
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise ValueError(
            f"AI output did not match {response_model.__name__}: {exc}"
        ) from exc


def _extract_content(response: Any) -> str:
    message = response.choices[0].message
    content = message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("AI response contained no text content")
    return content


def _extract_usage(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    return int(prompt_tokens), int(completion_tokens)


async def _complete(
    *, model: str, system_prompt: str, user_prompt: str, timeout: float
) -> Any:
    """One litellm call. litellm is imported lazily — its import is heavy."""
    import litellm

    return await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        timeout=timeout,
        max_tokens=settings.ai_max_tokens,
        api_key=_api_key_for_model(model),
        num_retries=0,  # retry policy is owned by call_ai()
    )


async def call_ai(
    *,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T] | None = None,
    model: str | None = None,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> AIResult:
    """Call the AI model with timeout, retries, and a fallback chain.

    Args:
        system_prompt: Instructions for the model.
        user_prompt: The input (e.g. resume data) to evaluate.
        response_model: When given, the output is parsed as JSON and
            validated against this Pydantic model (``AIResult.data``).
        model: Override model name (defaults to ``settings.ai_model``).
        timeout: Override per-call timeout in seconds.
        max_retries: Override retry count for the primary model.

    Returns:
        ``AIResult`` with the raw text, token usage, and parsed data.

    Raises:
        AIEvaluationError: If every attempt on every model in the chain
            fails (network, timeout, or invalid structured output).
    """
    primary_model = model or settings.ai_model
    chain = [primary_model]
    if (
        settings.ai_fallback_enabled
        and settings.ai_fast_model
        and settings.ai_fast_model != primary_model
    ):
        chain.append(settings.ai_fast_model)

    effective_timeout = timeout if timeout is not None else settings.ai_timeout
    retries = max_retries if max_retries is not None else settings.ai_max_retries

    system = system_prompt
    if response_model is not None:
        system = (
            f"{system_prompt}\n\n{_JSON_INSTRUCTION}"
            f"{json.dumps(response_model.model_json_schema())}"
        )

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        if attempt > 0:
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
        for chain_model in chain:
            started = time.monotonic()
            try:
                response = await _complete(
                    model=chain_model,
                    system_prompt=system,
                    user_prompt=user_prompt,
                    timeout=effective_timeout,
                )
                content = _extract_content(response)
                prompt_tokens, completion_tokens = _extract_usage(response)
                data = (
                    _validate_structured(content, response_model)
                    if response_model is not None
                    else None
                )
            except Exception as exc:  # noqa: BLE001 — any failure means "try next"
                last_error = exc
                logger.warning(
                    "AI call failed (model=%s, attempt=%d/%d): %s",
                    chain_model,
                    attempt + 1,
                    retries + 1,
                    exc,
                )
                continue
            logger.info(
                "AI call ok (model=%s, attempt=%d, elapsed=%.2fs, "
                "tokens in=%d out=%d, fallback=%s)",
                chain_model,
                attempt + 1,
                time.monotonic() - started,
                prompt_tokens,
                completion_tokens,
                chain_model != primary_model,
            )
            return AIResult(
                content=content,
                model=chain_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                fallback_used=chain_model != primary_model,
                data=data,
            )

    raise AIEvaluationError(
        evaluator="AI provider",
        reason=str(last_error) if last_error else "AI provider unavailable",
    )
