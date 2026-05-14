"""Structured request/response logging middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("oh_agent.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing for auditability."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        start = time.monotonic()
        response: Response = await call_next(request)
        elapsed = time.monotonic() - start
        logger.info(
            "%s %s → %d (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response
