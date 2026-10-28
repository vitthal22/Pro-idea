"""AI Resume Roaster — provider wrapper and prompt library.

Public API:
- ``call_ai()`` — async AI call with timeout, retries, and fallback chain
- ``AIResult`` — the result of one AI call (content, parsed data, usage)

Evaluators live in ``app/ai/evaluators/``, prompts in ``app/ai/prompts/``.
"""

from __future__ import annotations

# Import the evaluator package so its evaluators are registered and
# imported (and therefore syntax/type checked) with the app package.
from app.ai.evaluators import culture_fit  # noqa: F401
from app.ai.provider import AIResult, call_ai  # noqa: F401 (re-exported)

__all__ = ["AIResult", "call_ai"]
