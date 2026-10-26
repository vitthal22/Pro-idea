"""Declarative base for all ORM models.

Alembic autogenerate reads ``Base.metadata``, so every model module must be
imported before metadata is inspected (see ``app/models/__init__.py``).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class shared by every SQLAlchemy model."""
