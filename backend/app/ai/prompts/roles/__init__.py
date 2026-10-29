"""Role context prompts for role-based analysis.

``ROLE_CONTEXT_PROMPTS`` maps the slug stored in ``analyses.target_role``
to the role's system-prompt context. The Job Matcher evaluator appends the
matching context to its own system prompt. A target_role that is not in
this map is passed through as plain text — no fabricated context.
"""

from app.ai.prompts.roles.ai_engineer import SYSTEM_PROMPT as AI_ENGINEER
from app.ai.prompts.roles.backend_dev import SYSTEM_PROMPT as BACKEND_DEV
from app.ai.prompts.roles.data_scientist import SYSTEM_PROMPT as DATA_SCIENTIST
from app.ai.prompts.roles.devops import SYSTEM_PROMPT as DEVOPS
from app.ai.prompts.roles.frontend_dev import SYSTEM_PROMPT as FRONTEND_DEV
from app.ai.prompts.roles.fullstack_dev import SYSTEM_PROMPT as FULLSTACK_DEV
from app.ai.prompts.roles.product_manager import SYSTEM_PROMPT as PRODUCT_MANAGER
from app.ai.prompts.roles.software_engineer import SYSTEM_PROMPT as SOFTWARE_ENGINEER

ROLE_CONTEXT_PROMPTS: dict[str, str] = {
    "software_engineer": SOFTWARE_ENGINEER,
    "product_manager": PRODUCT_MANAGER,
    "frontend_dev": FRONTEND_DEV,
    "backend_dev": BACKEND_DEV,
    "fullstack_dev": FULLSTACK_DEV,
    "ai_engineer": AI_ENGINEER,
    "data_scientist": DATA_SCIENTIST,
    "devops": DEVOPS,
}


def get_role_context(role_slug: str | None) -> str | None:
    """Role context prompt for ``role_slug``, or None for unknown/absent."""
    if not role_slug:
        return None
    return ROLE_CONTEXT_PROMPTS.get(role_slug)
