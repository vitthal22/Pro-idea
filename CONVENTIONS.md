# Coding Conventions & Rules

> All AI assistants and developers must follow these rules when writing code for this project.

---

## 1. Python Style

### Formatting
- **Formatter/Linter:** Ruff (replaces Black + isort + flake8)
- **Indent:** 4 spaces (no tabs)
- **Line length:** 88 characters (Ruff default)
- **Quotes:** Double quotes for strings
- **Trailing commas:** Yes, on multi-line structures

### Naming Conventions
```
Variables/Functions  → snake_case          (e.g., resume_data, parse_resume)
Classes              → PascalCase          (e.g., ResumeParser, RecruiterEvaluator)
Constants            → UPPER_SNAKE_CASE    (e.g., MAX_FILE_SIZE, JWT_ALGORITHM)
Private methods      → _leading_underscore (e.g., _validate_input)
Files/Modules        → snake_case          (e.g., resume.py, content_quality.py)
API endpoints        → kebab-case in URLs  (e.g., /api/v1/analyses/:id/status)
Database columns     → snake_case          (e.g., created_at, user_id)
JSON fields          → snake_case          (e.g., analysis_type, target_role)
```

### Type Hints
**Required everywhere.** No exceptions.

```python
# ✅ Correct
async def get_resume(resume_id: UUID, db: AsyncSession) -> Resume | None:
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return result.scalar_one_or_none()

# ❌ Wrong
async def get_resume(resume_id, db):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return result.scalar_one_or_none()
```

Use `X | None` instead of `Optional[X]` (Python 3.10+ syntax).

---

## 2. Project Structure Rules

### Module Boundaries
```
Router (api/)        → HTTP concerns ONLY
                       Request parsing, response formatting, status codes
                       NO business logic here

Service (services/)  → Business logic
                       Orchestration, validation rules, data transformation
                       NO HTTP concerns here

Model (models/)      → Database schema ONLY
                       SQLAlchemy table definitions, relationships
                       NO business logic here

Schema (schemas/)    → Data contracts
                       Pydantic models for API, AI outputs, domain objects
                       NO database or HTTP logic here

AI (ai/)             → AI-specific code
                       Providers, evaluators, prompts, scoring
                       NO HTTP or database logic here
```

### File Organization
- **One class per file** for services and evaluators
- **Related schemas can share a file** (e.g., all evaluator output schemas in `schemas/evaluators.py`)
- **Prompts are separate files** — never inline in evaluator code
- **Tests mirror source structure** — `app/ai/evaluators/recruiter.py` → `tests/test_ai/evaluators/test_recruiter.py`

---

## 3. Import Ordering

```python
# 1. Standard library
import asyncio
from uuid import UUID

# 2. Third-party packages
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application
from app.api.deps import get_db, get_current_user
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse
from app.services.resume import ResumeService
```

Ruff handles this automatically. Don't manually sort imports.

---

## 4. FastAPI Conventions

### Router Organization
```python
# app/api/v1/resumes.py
from fastapi import APIRouter, Depends, UploadFile

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeResponse:
    ...
```

### Dependency Injection
- Use `Depends()` for database sessions, auth, services
- Create dependencies in `api/deps.py`
- Never instantiate services inside routers — inject them

### Response Models
- Always specify `response_model` on endpoints
- Always use `status_code` for creation endpoints (201)
- Return Pydantic models, not dicts

### Error Handling
```python
# Use HTTPException for API errors
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail={"code": "RESUME_NOT_FOUND", "message": "Resume not found"}
)

# Use custom exceptions for business logic
from app.common.exceptions import ResumeParsingError

raise ResumeParsingError(reason="empty_text", file_path=file_path)
```

---

## 5. Database Conventions

### SQLAlchemy Models
```python
# app/models/resume.py
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    raw_text = Column(Text)
    structured_data = Column(JSONB)
    parsing_status = Column(String(50), default="pending")
    parsing_errors = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resumes")
    analyses = relationship("Analysis", back_populates="resume")
```

### Rules
- All primary keys are UUIDs
- Use `DateTime` with `default=datetime.utcnow` (not `func.now()`)
- Foreign keys always have `ForeignKey` constraint
- JSONB for flexible/varying structures (AI outputs, config)
- String for fixed-value fields (status, type enums)
- Never use `relationship` lazy loading in async — always `selectin` or `joinedload`

### Migrations
- Always create a migration for schema changes: `poetry run alembic revision --autogenerate -m "description"`
- Never edit migration files manually after creation
- Test migrations up AND down: `poetry run alembic upgrade head && poetry run alembic downgrade -1`

---

## 6. Pydantic Schema Conventions

### API Schemas (Request/Response)
```python
# app/api/schemas/resumes.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class ResumeResponse(BaseModel):
    id: UUID
    original_name: str
    file_size: int
    mime_type: str
    parsing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}  # enables ORM mode
```

### AI Output Schemas
```python
# app/schemas/evaluators.py
from pydantic import BaseModel, Field
from typing import Literal

class CriticalIssue(BaseModel):
    title: str = Field(description="Short issue title")
    description: str = Field(description="Detailed explanation")
    category: Literal["content", "formatting", "skills", "experience", "ats"]
    severity: Literal["critical", "warning", "suggestion"]
    improvement: str = Field(description="How to fix this")
    recruiter_perspective: str = Field(description="How a recruiter sees this")

class RecruiterEvaluation(BaseModel):
    summary: str
    first_impression: str
    critical_issues: list[CriticalIssue]
    strengths: list[str]
    hire_recommendation: Literal["strong_yes", "yes", "maybe", "no", "strong_no"]
```

### Rules
- Always use `Field(description=...)` for AI schemas — descriptions become part of the prompt
- Always use `Literal` for enums — not custom enum classes for AI outputs
- Always use `list[X]` syntax (not `List[X]`)
- AI schemas go in `app/schemas/`, API schemas go in `app/api/schemas/`

---

## 7. AI Code Conventions

### Never Call AI Providers Directly
```python
# ✅ Correct — go through provider abstraction
from app.ai.provider import call_ai
from app.schemas.evaluators import RecruiterEvaluation

result, usage = await call_ai(
    model="gpt-4o",
    messages=messages,
    response_model=RecruiterEvaluation,
)

# ❌ Wrong — direct litellm call
import litellm
response = await litellm.acompletion(model="gpt-4o", messages=messages)
```

### Never Hardcode Prompts
```python
# ✅ Correct — load from prompts module
from app.ai.prompts.evaluators.recruiter import RECRUITER_SYSTEM_PROMPT

# ❌ Wrong — inline prompt
system_prompt = "You are a senior recruiter with 10 years of experience..."
```

### Structured Output Validation
```python
# Always validate AI output with Pydantic
from app.schemas.evaluators import RecruiterEvaluation

try:
    result = RecruiterEvaluation.model_validate_json(ai_response)
except ValidationError as e:
    # Handle invalid AI output — retry or fallback
    logger.warning(f"AI output validation failed: {e}")
    # Retry with stricter prompt or fallback
```

### Evaluator Pattern
Every evaluator follows this pattern:
```python
# app/ai/evaluators/recruiter.py
from app.ai.provider import call_ai
from app.ai.prompts.evaluators.recruiter import RECRUITER_SYSTEM_PROMPT, RECRUITER_OUTPUT_SCHEMA
from app.schemas.resume import ResumeStructuredData

async def run_recruiter_evaluator(
    resume_data: ResumeStructuredData,
    context: EvaluationContext,
) -> RecruiterEvaluation:
    """Evaluate resume from recruiter perspective."""
    messages = [
        {"role": "system", "content": RECRUITER_SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(resume_data, context)},
    ]

    result, usage = await call_ai(
        model=context.model,
        messages=messages,
        response_model=RECRUITER_OUTPUT_SCHEMA,
    )

    return result
```

---

## 8. Error Handling Conventions

### Custom Exceptions
```python
# app/common/exceptions.py

class AppException(Exception):
    """Base exception for the application."""
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}

class ResumeParsingError(AppException):
    """Raised when resume text extraction fails."""
    def __init__(self, reason: str, file_path: str):
        super().__init__(
            code="PARSING_FAILED",
            message=f"Could not parse resume: {reason}",
            details={"reason": reason, "file_path": file_path},
        )

class AIEvaluationError(AppException):
    """Raised when an AI evaluator fails after retries."""
    def __init__(self, evaluator: str, reason: str):
        super().__init__(
            code="AI_EVALUATION_FAILED",
            message=f"Evaluator '{evaluator}' failed: {reason}",
            details={"evaluator": evaluator, "reason": reason},
        )
```

### Rules
- Never catch `Exception` broadly — catch specific exceptions
- Always log errors with context before re-raising
- AI failures should degrade gracefully (skip evaluator, note in results)
- Never let raw Python tracebacks reach the API response

---

## 9. Testing Conventions

### Framework
- **pytest** with **pytest-asyncio** for async tests
- **httpx** for testing FastAPI endpoints
- Fixtures in `conftest.py`, not in individual test files

### Test Structure
```python
# tests/test_api/test_resumes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_resume(client: AsyncClient, auth_headers: dict):
    """Test resume upload with valid PDF."""
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = await client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert response.status_code == 201
    data = response.json()
    assert data["parsing_status"] == "pending"
    assert "id" in data
```

### Rules
- Test file names: `test_<module>.py`
- Test function names: `test_<what_is_being_tested>`
- Use fixtures for shared setup (database, auth, test data)
- Test both success and failure paths
- Mock AI calls in unit tests — don't hit real APIs
- Integration tests can use real APIs (mark with `@pytest.mark.integration`)

---

## 10. Git Conventions

### Branch Naming
```
main                    # Production-ready code
develop                 # Integration branch
feature/resume-upload   # Feature branches
fix/parsing-error       # Bug fixes
refactor/evaluator-pipeline  # Refactoring
```

### Commit Messages
```
feat: add resume upload endpoint
fix: handle empty PDF extraction
refactor: extract evaluator base class
test: add recruiter evaluator unit tests
docs: update architecture blueprint
chore: update dependencies
```

### Rules
- One logical change per commit
- Never commit `.env` files or secrets
- Never commit `uploads/` directory
- Always run `ruff check .` and `pytest` before committing
