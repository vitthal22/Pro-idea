"""ORM models.

Import every model module here so ``Base.metadata`` is complete for
Alembic autogenerate and table creation.
"""

from app.models.user import UserModel

__all__ = ["UserModel"]
