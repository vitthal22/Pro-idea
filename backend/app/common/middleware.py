"""Cross-cutting HTTP middleware: request logging + CORS.

Registered once via ``setup_middleware(app)`` — main.py stays declarative.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.common.logging import app_logger
from app.config import settings


async def _log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Log method, path, status, and duration for every request.

    Also sets ``X-Process-Time`` so clients and tests can observe latency.
    """
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Process-Time"] = f"{duration_ms:.0f}"
    app_logger.info(
        "http_request method=%s path=%s status=%d duration_ms=%.0f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


def setup_middleware(app: FastAPI) -> None:
    """Attach CORS (explicit origins only) and request logging."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(_log_requests)
