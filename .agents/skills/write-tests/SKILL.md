---
name: write-tests
description: Write tests for the AI Resume Roaster project
---

## Prerequisites

- pytest and pytest-asyncio installed
- Test fixtures in `tests/conftest.py`

## Test Types

### Unit Tests (Fast, Mocked AI)

For testing individual functions without hitting real AI APIs.

```python
# tests/test_ai/evaluators/test_recruiter.py
import pytest
from unittest.mock import AsyncMock, patch
from app.ai.evaluators.recruiter import run_recruiter_evaluator
from app.schemas.evaluators import RecruiterEvaluation
from app.schemas.resume import ResumeStructuredData

@pytest.mark.asyncio
async def test_recruiter_evaluator_returns_valid_structure():
    """Test that evaluator returns properly structured output."""
    mock_resume = ResumeStructuredData(...)  # Use fixture

    mock_result = RecruiterEvaluation(
        summary="Test summary",
        first_impression="Test impression",
        critical_issues=[],
        strengths=["Good skills section"],
        hire_recommendation="maybe",
    )

    with patch("app.ai.evaluators.recruiter.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = (mock_result, TokenUsage(prompt_tokens=100, completion_tokens=200))
        result = await run_recruiter_evaluator(mock_resume, test_context)

    assert isinstance(result, RecruiterEvaluation)
    assert result.summary == "Test summary"
    assert result.hire_recommendation == "maybe"
```

### API Tests (httpx AsyncClient)

For testing HTTP endpoints.

```python
# tests/test_api/test_resumes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_resume_success(client: AsyncClient, auth_headers: dict):
    """Test successful resume upload."""
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = await client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["parsing_status"] == "pending"

@pytest.mark.asyncio
async def test_upload_resume_no_auth(client: AsyncClient):
    """Test upload without authentication returns 401."""
    response = await client.post("/api/v1/resumes/upload")
    assert response.status_code == 401
```

### Integration Tests (Real AI)

For testing the full pipeline with actual AI calls.

```python
# tests/test_ai/test_pipeline.py
import pytest

@pytest.mark.integration
async def test_full_pipeline_with_sample_resume():
    """Test complete analysis pipeline with real AI."""
    # Use a cheap model for testing
    result = await run_full_pipeline(
        resume_path="tests/fixtures/sample.pdf",
        analysis_type="general",
        model="gpt-4o-mini",
    )
    assert result.status == "completed"
    assert result.scores.overall > 0
    assert len(result.critical_issues) >= 0
```

## Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture
def sample_resume_data():
    """Pre-built ResumeStructuredData for unit tests."""
    return ResumeStructuredData(...)

@pytest.fixture
def test_context():
    """EvaluationContext for testing."""
    return EvaluationContext(model="gpt-4o", analysis_type="general")
```

## Rules

- Test file names: `test_<module>.py`
- Test function names: `test_<what_is_being_tested>`
- Always mock AI calls in unit tests — never hit real APIs
- Use `@pytest.mark.integration` for tests that need real AI
- Put shared fixtures in `conftest.py`
- Test both success and failure paths
- Sample files go in `tests/fixtures/` — never use real user resumes

## Running Tests

```bash
poetry run pytest                           # All tests
poetry run pytest tests/test_api/           # API tests only
poetry run pytest -m "not integration"      # Skip integration tests
poetry run pytest tests/test_ai/test_pipeline.py -m integration  # Integration only
```
