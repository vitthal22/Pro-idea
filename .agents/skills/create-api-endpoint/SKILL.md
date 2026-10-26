---
name: create-api-endpoint
description: Add a new API endpoint to the FastAPI backend
---

## Prerequisites

- Understanding of FastAPI route decorators and dependency injection
- Existing module in `app/api/v1/` or readiness to create one

## Steps

1. **Define request/response schemas** in `app/api/schemas/<module>.py`
   - Use Pydantic BaseModel with Field descriptions
   - API response schemas need `model_config = {"from_attributes": True}`

2. **Create the router** in `app/api/v1/<module>.py`
   ```python
   from fastapi import APIRouter, Depends
   router = APIRouter(prefix="/<module>", tags=["<module>"])
   ```

3. **Add the endpoint function**
   - Always specify `response_model` and `status_code` in the decorator
   - Use `201` for creation endpoints
   - Inject dependencies via function parameters:
     - `db: AsyncSession = Depends(get_db)` for database
     - `current_user: User = Depends(get_current_user)` for auth

4. **Call the service layer** — never put business logic in the router
   ```python
   service = SomeService(db)
   result = await service.do_something(payload, current_user)
   ```

5. **Register the router** in `app/api/v1/router.py` if it's a new module
   ```python
   from app.api.v1.<module> import router as <module>_router
   api_router.include_router(<module>_router)
   ```

6. **Write tests** in `tests/test_api/test_<module>.py`
   - Use `httpx.AsyncClient` for API testing
   - Test success (200/201), validation errors (422), auth (401), not found (404)

## Verification

- Run `poetry run ruff check .` — no lint errors
- Run `poetry run pytest tests/test_api/test_<module>.py` — all tests pass
- Check auto-generated docs at `http://localhost:8000/docs`

## Common Mistakes

- Putting business logic in the router (move to service layer)
- Missing `response_model` (FastAPI won't validate response shape)
- Not registering the router (endpoint won't be accessible)
- Hardcoding status codes without using HTTPException for errors
