"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.common.exceptions import AppException
from app.common.logging import app_logger, setup_logging
from app.config import settings
from app.db.seed import seed_demo_user
from app.db.session import dispose_engine

setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Seed the demo account on startup and close the pool on shutdown."""
    await seed_demo_user()
    yield
    await dispose_engine()


app = FastAPI(
    title="AI Resume Brutal Roaster",
    version="0.1.0",
    description=(
        "AI-powered resume analysis with a multi-evaluator pipeline that "
        "delivers brutally honest, constructive feedback."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convert AppException into structured JSON — no raw tracebacks."""
    app_logger.warning(
        "app_exception",
        extra={
            "code": exc.code,
            "path": request.url.path,
            "details": exc.details,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness probe — no auth, no DB."""
    return {"status": "ok"}


app.include_router(api_v1_router, prefix="/api")
