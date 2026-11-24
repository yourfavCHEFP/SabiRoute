"""ASGI-boundary coverage for :mod:`sabiroute.api.body_limit`.

The declared-length rejection is already pinned elsewhere; what follows covers
the paths that only run for hostile or unusual clients: a malformed
``Content-Length`` that must be ignored in favour of measuring the actual body,
and a streaming body that overflows the limit. The overflow has two outcomes
that must stay distinct: a 413 when nothing has been sent yet, and a propagated
``_BodyTooLarge`` once the response has started, because a second response
cannot be fabricated mid-stream.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from sabiroute.api.body_limit import BodySizeMiddleware, _BodyTooLarge


def _scope(
    *,
    headers: tuple[tuple[bytes, bytes], ...] = (),
    scope_type: str = "http",
) -> dict[str, Any]:
    return {
        "type": scope_type,
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/chat/completions",
        "raw_path": b"/v1/chat/completions",
        "query_string": b"",
        "root_path": "",
        "headers": list(headers),
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }


def _drive(
    middleware: BodySizeMiddleware,
    scope: dict[str, Any],
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sent: list[dict[str, Any]] = []
    queue = list(messages)

    async def receive() -> dict[str, Any]:
        if not queue:
            return {"type": "http.disconnect"}
        return queue.pop(0)

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    asyncio.run(middleware(scope, receive, send))
    return sent


def _error(captured: list[dict[str, Any]]) -> dict[str, Any]:
    body = next(
        message["body"]
        for message in captured
        if message["type"] == "http.response.body"
    )
    return json.loads(body)["error"]


def test_declared_length_over_the_limit_is_rejected_without_touching_the_app() -> None:
    invoked: list[bool] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        invoked.append(True)

    middleware = BodySizeMiddleware(app, max_body_bytes=1024)
    sent = _drive(
        middleware,
        _scope(headers=((b"content-length", b"2048"),)),
        [{"type": "http.request", "body": b"x", "more_body": False}],
    )

    assert invoked == []
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
    error = _error(sent)
    assert error["type"] == "request_body_too_large"
    assert error["limit_bytes"] == 1024


def test_malformed_content_length_is_ignored_and_the_body_measured() -> None:
    seen: list[bytes] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        message = await receive()
        seen.append(message["body"])
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = BodySizeMiddleware(app, max_body_bytes=1024)
    sent = _drive(
        middleware,
        _scope(headers=((b"content-length", b"not-a-number"),)),
        [{"type": "http.request", "body": b"hello", "more_body": False}],
    )

    assert seen == [b"hello"]
    assert sent[0]["status"] == 200


def test_streaming_overflow_before_headers_sent_becomes_a_413() -> None:
    async def app(scope: Any, receive: Any, send: Any) -> None:
        await receive()
        await receive()

    middleware = BodySizeMiddleware(app, max_body_bytes=10)
    sent = _drive(
        middleware,
        _scope(),
        [
            {"type": "http.request", "body": b"12345678", "more_body": True},
            {"type": "http.request", "body": b"12345678", "more_body": False},
        ],
    )

    assert sent[0]["status"] == 413
    assert _error(sent)["limit_bytes"] == 10


def test_streaming_overflow_after_headers_sent_propagates() -> None:
    async def app(scope: Any, receive: Any, send: Any) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await receive()

    middleware = BodySizeMiddleware(app, max_body_bytes=5)

    with pytest.raises(_BodyTooLarge):
        _drive(
            middleware,
            _scope(),
            [{"type": "http.request", "body": b"0123456789", "more_body": False}],
        )


def test_non_http_scope_is_passed_through_unchanged() -> None:
    captured: list[str] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured.append(scope["type"])

    middleware = BodySizeMiddleware(app, max_body_bytes=1)

    async def receive() -> dict[str, Any]:
        return {"type": "lifespan.startup"}

    async def send(message: dict[str, Any]) -> None:
        return None

    asyncio.run(middleware(_scope(scope_type="lifespan"), receive, send))

    assert captured == ["lifespan"]
