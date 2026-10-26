---
name: add-database-model
description: Add a new SQLAlchemy database model with migration
---

## Prerequisites

- PostgreSQL running and accessible
- Alembic configured

## Steps

1. **Create the model** in `app/models/<name>.py`
   ```python
   from sqlalchemy import Column, String, DateTime, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID, JSONB
   from sqlalchemy.orm import relationship
   import uuid
   from datetime import datetime

   from app.models.base import Base

   class NewModel(Base):
       __tablename__ = "new_models"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
       name = Column(String(255), nullable=False)
       data = Column(JSONB)
       status = Column(String(50), default="pending")
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

       # Relationships
       user = relationship("User", back_populates="new_models")
   ```

2. **Register the model** in `app/models/__init__.py` (if needed for Alembic autogenerate)

3. **Generate migration:**
   ```bash
   poetry run alembic revision --autogenerate -m "add new_models table"
   ```

4. **Review the generated migration** in `alembic/versions/`
   - Check column types are correct
   - Check foreign keys are correct
   - Verify up and downgrade functions

5. **Test the migration:**
   ```bash
   poetry run alembic upgrade head    # Apply
   poetry run alembic downgrade -1    # Rollback
   poetry run alembic upgrade head    # Re-apply
   ```

6. **Create Pydantic schema** in `app/schemas/<name>.py`
   ```python
   from pydantic import BaseModel
   from datetime import datetime
   from uuid import UUID

   class NewModelResponse(BaseModel):
       id: UUID
       name: str
       status: str
       created_at: datetime

       model_config = {"from_attributes": True}
   ```

7. **Add service methods** in `app/services/<name>.py` for CRUD operations

## Rules

- All primary keys are UUIDs
- All tables have created_at and updated_at
- Use JSONB for flexible/varying structures
- Use `relationship()` with `back_populates`, never `backref`
- Never use lazy loading in async — use `selectin` or `joinedload`

## Verification

- Migration applies and rolls back cleanly
- Model can be queried via SQLAlchemy
- Pydantic schema can serialize model instances
