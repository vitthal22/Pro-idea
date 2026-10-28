"""Resume parser: raw resume text → ``StructuredResume`` via the AI layer.

Parsing is a "simple check" in pipeline terms, so it runs on
``AI_FAST_MODEL`` (config), never the heavy model.
"""

from __future__ import annotations

import logging

from app.ai.prompts.parser import PARSER_RESPONSE_MODEL, PARSER_SYSTEM_PROMPT
from app.ai.provider import call_ai
from app.common.exceptions import AIEvaluationError
from app.config import settings
from app.schemas.resume import StructuredResume

logger = logging.getLogger("app.ai.parser")

# Cap the resume text fed to the model — truncate the input, never the
# system prompt (resource rules). A page of dense text is ~3k chars, so
# this covers multi-page resumes with headroom.
MAX_RESUME_CHARS = 15_000

_USER_PROMPT_PREFIX = "Extract the structured data from this resume:\n\n"


async def parse_resume(raw_text: str) -> StructuredResume:
    """Parse raw resume text into a ``StructuredResume``.

    Args:
        raw_text: The extracted resume text (from ``document_processing``).

    Returns:
        The structured resume. Fields the resume does not mention stay
        null/empty.

    Raises:
        AIEvaluationError: If the AI call fails or the output does not
            validate against the ``StructuredResume`` schema.
    """
    truncated = raw_text[:MAX_RESUME_CHARS]
    if len(raw_text) > MAX_RESUME_CHARS:
        logger.warning(
            "Resume text truncated for parsing (%d → %d chars)",
            len(raw_text),
            MAX_RESUME_CHARS,
        )

    result = await call_ai(
        system_prompt=PARSER_SYSTEM_PROMPT,
        user_prompt=f"{_USER_PROMPT_PREFIX}{truncated}",
        response_model=PARSER_RESPONSE_MODEL,
        model=settings.ai_fast_model,
    )

    if not isinstance(result.data, StructuredResume):
        raise AIEvaluationError(
            evaluator="resume_parser",
            reason="model returned no structured resume",
        )
    return result.data
