"""Absolute logical-request deadline enforced at the ASGI boundary."""

from __future__ import annotations

import asyncio
import logging
import math
import os
from typing import Any

from fastapi.responses import JSONResponse

DEFAULT_REQUEST_DEADLINE_SECONDS = 300.0
DEADLINE_ENV_VAR = "SABIROUTE_REQUEST_DEADLINE_SECONDS"

logger = logging.getLogger(__name__)


def request_deadline_seconds(raw: str | None = None) -> float:
    """Resolve the total request deadline in seconds.

    Unset or blank means the default. Anything else must be a finite
    positive number; invalid values fail loudly at startup instead of
    silently becoming a different budget.
    """
    value = raw if raw is not None else os.environ.get(DEADLINE_ENV_VAR)
    if value is None or not value.strip():
        return DEFAULT_REQUEST_DEADLINE_SECONDS
    try:
        parsed = float(value)
    except ValueError:
        raise ValueError(
            f"{DEADLINE_ENV_VAR} must be a number of seconds, got {value!r}."
        ) from None
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(
            f"{DEADLINE_ENV_VAR} must be a finite positive number of seconds, "
            f"got {value!r}."
        )
    return parsed


class DeadlineMiddleware:
    """Bound total request lifetime, including streamed response bodies.

    An in-endpoint timeout cannot cover body iteration: Starlette invokes
    the response (headers, then body) after the endpoint returns. This
    middleware wraps the whole downstream ASGI call, so the deadline
    encloses dependencies, handler execution, header sending, streaming,
    and generator-tail finalization.

    Pre-header expiry returns 503 ``deadline_exceeded``. Post-header
    expiry aborts the body without fabricating completion markers.
    Caller cancellation (``CancelledError``) always propagates untouched
    and is never converted into a deadline response.
    """

    def __init__(
        self, app: Any, deadline_seconds: float = DEFAULT_REQUEST_DEADLINE_SECONDS
    ) -> None:
        self.app = app
        self.deadline_seconds = deadline_seconds

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        started = False
        deadline_at = asyncio.get_running_loop().time() + self.deadline_seconds
        # Publish the deadline where endpoint code can read it. A timeout
        # raised by this middleware arrives downstream as CancelledError,
        # which is otherwise indistinguishable from a caller disconnect;
        # comparing against the published instant tells them apart.
        scope.setdefault("state", {})["sabiroute_deadline_at"] = deadline_at

        async def send_wrapper(message: Any) -> None:
            nonlocal started
            if message.get("type") == "http.response.start":
                started = True
            await send(message)

        try:
            async with asyncio.timeout_at(deadline_at):
                await self.app(scope, receive, send_wrapper)
        except TimeoutError:
            # The deadline fired. Caller cancellation arrives as
            # CancelledError and is deliberately not caught here.
            # Guard against misclassifying a foreign TimeoutError raised
            # by downstream code before our own deadline passed.
            if asyncio.get_running_loop().time() < deadline_at:
                raise
            if started:
                logger.warning("Request deadline exceeded after response started; aborting body.")
                return
            expired = JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "message": "The request exceeded its processing deadline.",
                        "type": "deadline_exceeded",
                    }
                },
            )
            await expired(scope, receive, send)
