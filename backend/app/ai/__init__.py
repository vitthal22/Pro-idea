"""AI Resume Roaster — provider wrapper, parser, and evaluator registry.

Public API:
- ``call_ai()`` — async AI call with timeout, retries, and fallback chain
- ``AIResult`` — the result of one AI call (content, parsed data, usage)
- ``parse_resume()`` — raw resume text → ``StructuredResume``
- ``get_evaluators_for_mode()`` — evaluator functions per analysis mode

Prompts live in ``app/ai/prompts/`` and are never hardcoded elsewhere.
"""

from __future__ import annotations

from app.ai.orchestrator import get_evaluators_for_mode  # noqa: F401
from app.ai.parser import parse_resume  # noqa: F401
from app.ai.provider import AIResult, call_ai  # noqa: F401

__all__ = ["AIResult", "call_ai", "get_evaluators_for_mode", "parse_resume"]
