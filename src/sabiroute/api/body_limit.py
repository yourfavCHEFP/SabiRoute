"""Bound total inbound request body size at the ASGI boundary.

Reads ``Content-Length`` when present and rejects oversized bodies with
413 before routing, auth accounting, or provider dispatch. Chunked bodies
without a length are measured while streaming and aborted at the limit.
Limits are operator-configurable; invalid values fail loudly at startup.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi.responses import JSONResponse

DEFAULT_MAX_BODY_BYTES = 1_048_576  # 1 MiB
BODY_ENV_VAR = "SABIROUTE_MAX_REQUEST_BODY_BYTES"
ABSOLUTE_MAX_BODY_BYTES = 16_777_216  # 16 MiB hard ceiling


def request_max_body_bytes(raw: str | None = None) -> int:
    """Resolve the inbound body limit in bytes.

    Unset or blank means the default. Anything else must be a positive
    integer within the absolute ceiling; invalid values fail loudly at
    startup instead of silently becoming a different limit.
    """
    value = raw if raw is not None else os.environ.get(BODY_ENV_VAR)
    if value is None or not value.strip():
        return DEFAULT_MAX_BODY_BYTES
    try:
        parsed = int(value.strip())
    except ValueError:
        raise ValueError(
            f"{BODY_ENV_VAR} must be an integer number of bytes, got {value!r}."
        ) from None
    if parsed < 1 or parsed > ABSOLUTE_MAX_BODY_BYTES:
        raise ValueError(
            f"{BODY_ENV_VAR} must be between 1 and {ABSOLUTE_MAX_BODY_BYTES}, "
            f"got {value!r}."
        )
    return parsed


def _too_large(limit: int) -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content={
            "error": {
                "message": f"Request body exceeds the {limit}-byte limit.",
                "type": "request_body_too_large",
                "limit_bytes": limit,
            }
        },
    )


class BodySizeMiddleware:
    """Reject oversized request bodies before downstream handling."""

    def __init__(
        self, app: Any, max_body_bytes: int = DEFAULT_MAX_BODY_BYTES
    ) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Any, receive: Any, send: Any) -> Any:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        declared = headers.get("content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_body_bytes:
                    response = _too_large(self.max_body_bytes)
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass  # malformed length: measure the actual body instead

        seen = 0
        limit = self.max_body_bytes

        async def bounded_receive() -> Any:
            nonlocal seen
            message = await receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                seen += len(chunk)
                if seen > limit:
                    raise _BodyTooLarge(limit)
            return message

        started = False

        async def _send_limited(message: Any) -> None:
            nonlocal started
            if message.get("type") == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, bounded_receive, _send_limited)
        except _BodyTooLarge as exc:
            if started:
                # Headers already sent: abort the body without fabricating
                # a second response (mirrors DeadlineMiddleware post-header
                # behavior — never convert into a synthetic response).
                raise
            response = _too_large(exc.limit)
            await response(scope, receive, send)


class _BodyTooLarge(Exception):
    def __init__(self, limit: int) -> None:
        super().__init__(f"body exceeds {limit} bytes")
        self.limit = limit
