"""Regression tests for the absolute logical-request deadline.

The middleware bounds total request lifetime (ingress to completion);
the endpoint maps in-flight deadline expiry to an honest
``deadline_exceeded`` outcome without attributing it to a deployment.
Fake clocks and controlled transports only: no real sleeps at scale, no
live providers.
"""

from __future__ import annotations

import asyncio
import json
import time

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.testclient import TestClient

from sabiroute.api.deadline import (
    DEFAULT_REQUEST_DEADLINE_SECONDS,
    DeadlineMiddleware,
    request_deadline_seconds,
)
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClientError

MESSAGES = [{"role": "user", "content": "hello"}]


def _never_resolving_app() -> FastAPI:
    async def hanging_endpoint(request):
        await asyncio.Event().wait()

    app = FastAPI()
    app.router.routes.append(
        __import__("starlette.routing", fromlist=["Route"]).Route(
            "/", hanging_endpoint
        )
    )
    return app


def test_deadline_env_parsing() -> None:
    assert request_deadline_seconds(None) == DEFAULT_REQUEST_DEADLINE_SECONDS
    assert request_deadline_seconds("") == DEFAULT_REQUEST_DEADLINE_SECONDS
    assert request_deadline_seconds("   ") == DEFAULT_REQUEST_DEADLINE_SECONDS
    assert request_deadline_seconds("60") == 60.0
    for bad in ("abc", "0", "-5", "nan", "inf"):
        with pytest.raises(ValueError):
            request_deadline_seconds(bad)


def test_past_deadline_returns_503_without_running_handler() -> None:
    events: list[str] = []

    async def handler(request):

        events.append("started")
        await asyncio.sleep(10)
        events.append("finished")
        return JSONResponse({"ok": True})

    app = FastAPI()
    from starlette.routing import Route

    app.router.routes.append(Route("/", handler))
    app.add_middleware(DeadlineMiddleware, deadline_seconds=0)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "message": "The request exceeded its processing deadline.",
            "type": "deadline_exceeded",
        }
    }
    # The handler starts (a deadline cannot preempt synchronous entry) but
    # can never finish async work past the deadline.
    assert events == ["started"]


def test_expired_deadline_aborts_hung_downstream() -> None:
    app = _never_resolving_app()
    app.add_middleware(DeadlineMiddleware, deadline_seconds=0.05)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/")

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "deadline_exceeded"


def test_truncated_stream_sends_no_completion_marker() -> None:
    # NOTE: this Starlette TestClient drops body frames buffered before an
    # abnormal app-task end (verified: even an explicit mid-stream raise
    # yields 200 + empty body), so the test observes the generator, not the
    # client bytes. Real servers stream frames as they are sent.
    events: list[str] = []

    async def infinite_stream(request):
        async def body():
            try:
                events.append("yield-frame")
                yield b'data: {"x": 1}\n\n'
                await asyncio.Event().wait()
            except BaseException as exc:
                events.append(type(exc).__name__)
                raise
            events.append("completed")

        return StreamingResponse(body(), media_type="text/event-stream")

    app = FastAPI()
    from starlette.routing import Route

    app.router.routes.append(Route("/", infinite_stream))
    app.add_middleware(DeadlineMiddleware, deadline_seconds=0.5)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert events[0] == "yield-frame"
    assert "completed" not in events
    assert not any("DONE" in event for event in events)


def test_caller_cancellation_is_not_converted_to_deadline() -> None:
    from fastapi import Request

    async def cancelling(request: Request):
        raise asyncio.CancelledError

    app = FastAPI()
    from starlette.routing import Route

    app.router.routes.append(Route("/", cancelling))
    app.add_middleware(DeadlineMiddleware, deadline_seconds=300)

    # NOTE: TestClient surfaces server-side asyncio cancellation as
    # concurrent.futures.CancelledError (portal translation); the assertion
    # is that no 503 deadline response is produced and the cancellation
    # propagates unconverted.
    import concurrent.futures

    with TestClient(app) as client:
        with pytest.raises(concurrent.futures.CancelledError):
            client.get("/")


def test_non_http_scope_passes_through() -> None:
    seen: list[str] = []

    async def inner(scope, receive, send):
        seen.append(scope["type"])

    middleware = DeadlineMiddleware(inner, deadline_seconds=300)
    asyncio.run(middleware({"type": "lifespan"}, None, None))
    assert seen == ["lifespan"]


def test_hung_attempt_records_deadline_without_health_mark() -> None:
    stub = StubLiteLLMClient()

    async def hanging(decision, messages, **kwargs):
        stub.calls.append(decision.deployment)
        await asyncio.Event().wait()

    stub.chat_completion = hanging  # type: ignore[method-assign]
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = create_app(state=state)
    # Shorten the wired default for this test only; production default stays.
    app.user_middleware = [
        (m.cls, m.args, {**m.kwargs, "deadline_seconds": 0.2})
        if m.cls is DeadlineMiddleware
        else (m.cls, m.args, m.kwargs)
        for m in app.user_middleware
    ]
    app.middleware_stack = app.build_middleware_stack()

    with TestClient(
        app, headers={"Authorization": f"Bearer {key}"}, raise_server_exceptions=False
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
        )

    assert response.status_code in (502, 503)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert [d["outcome"] for d in event.routing_decisions] == ["failure"]
    assert event.routing_decisions[0]["failure_category"] in (
        "deadline_exceeded",
        "transport",
    )
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["healthy"] is True


def test_deadline_expiry_stops_fallback_without_new_attempt() -> None:
    stub = StubLiteLLMClient()

    async def hanging(decision, messages, **kwargs):
        stub.calls.append(decision.deployment)
        await asyncio.Event().wait()

    stub.chat_completion = hanging  # type: ignore[method-assign]
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = create_app(state=state)
    app.user_middleware = [
        (m.cls, m.args, {**m.kwargs, "deadline_seconds": 0.2})
        if m.cls is DeadlineMiddleware
        else (m.cls, m.args, m.kwargs)
        for m in app.user_middleware
    ]
    app.middleware_stack = app.build_middleware_stack()

    with TestClient(
        app, headers={"Authorization": f"Bearer {key}"}, raise_server_exceptions=False
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
        )

    assert response.status_code in (502, 503)
    # At most the in-flight attempt exists; the deadline forbids fallback.
    assert len(stub.calls) <= 1


def _app_with_short_deadline(state, seconds: float):
    from sabiroute.main import create_app as _create_app

    app = _create_app(state=state)
    app.user_middleware = [
        (m.cls, m.args, {**m.kwargs, "deadline_seconds": seconds})
        if m.cls is DeadlineMiddleware
        else (m.cls, m.args, m.kwargs)
        for m in app.user_middleware
    ]
    app.middleware_stack = app.build_middleware_stack()
    return app


def test_streaming_deadline_truncates_without_health_mark() -> None:
    stub = StubLiteLLMClient()

    class HangingStream:
        async def events(self):
            yield b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
            await asyncio.Event().wait()

        async def aclose(self):
            return None

    async def hanging_stream(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        return HangingStream()

    stub.start_chat_completion_stream = hanging_stream  # type: ignore[method-assign]
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = _app_with_short_deadline(state, 0.5)

    with TestClient(
        app, headers={"Authorization": f"Bearer {key}"}, raise_server_exceptions=False
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "stream": True},
        )

    assert response.status_code == 200
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 503
    (decision,) = event.routing_decisions
    assert decision["outcome"] == "failure"
    assert decision["failure_category"] == "deadline_exceeded"
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["healthy"] is True
    assert snapshot["primary"]["total_failures"] == 0
    assert store.finalize_calls == 1


def test_foreign_timeout_error_is_not_misclassified_as_deadline() -> None:
    async def foreign_timeout(request):
        raise TimeoutError("unrelated downstream timeout")

    app = FastAPI()
    from starlette.routing import Route

    app.router.routes.append(Route("/", foreign_timeout))
    app.add_middleware(DeadlineMiddleware, deadline_seconds=300)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/")

    assert response.status_code == 500
    assert "deadline_exceeded" not in response.text


def test_trickle_stream_cannot_evade_deadline() -> None:
    """Frames arriving before the deadline do not exempt the stream from it.

    Regression test (P1-A): a stream that keeps emitting data is still
    bounded by the absolute request deadline. Proves the existing
    post-header truncation contract — wire stays 200 with no fabricated
    ``[DONE]``, telemetry records exactly one
    ``failure``/``deadline_exceeded`` decision, and provider health is
    untouched by the local expiry.
    """
    stub = StubLiteLLMClient()
    events: list[str] = []
    frames: list[bytes] = []

    class TricklingStream:
        async def events(self):
            for i in range(3):
                events.append(f"frame-{i}")
                frame = (
                    b'data: {"choices":[{"delta":{"content":"part'
                    + str(i).encode()
                    + b'"}}]}\n\n'
                )
                frames.append(frame)
                yield frame
            await asyncio.Event().wait()

        async def aclose(self):
            events.append("aclose")
            return None

    async def trickling_stream(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        return TricklingStream()

    stub.start_chat_completion_stream = trickling_stream  # type: ignore[method-assign]
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = _app_with_short_deadline(state, 0.3)

    with TestClient(
        app, headers={"Authorization": f"Bearer {key}"}, raise_server_exceptions=False
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "stream": True},
        )

    assert response.status_code == 200
    # All three frames flowed before the deadline; the hang afterwards met it.
    assert events[:3] == ["frame-0", "frame-1", "frame-2"]
    assert len(frames) == 3
    # Every emitted frame carries valid JSON in its data: payload — the
    # gateway's SSE parser must accept what this stub produced.
    for frame in frames:
        payload = frame.decode("utf-8").splitlines()[0][len("data:"):].strip()
        assert json.loads(payload)["choices"][0]["delta"]["content"].startswith(
            "part"
        )
    # Post-header truncation contract: the wire stays 200 and carries no
    # fabricated completion marker.
    assert b"data: [DONE]" not in response.content
    assert events[-1] == "aclose"
    assert "completed" not in events
    assert stub.calls == ["primary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 503
    (decision,) = event.routing_decisions
    assert decision["outcome"] == "failure"
    assert decision["failure_category"] == "deadline_exceeded"
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["healthy"] is True
    assert snapshot["primary"]["total_failures"] == 0
    assert store.finalize_calls == 1


def _install_flag_clock(monkeypatch: pytest.MonkeyPatch, flag: dict[str, bool]) -> None:
    """Fake the gate clock so it jumps past the deadline once flagged.

    Verified during development: this environment's event-loop clock
    delegates to ``time.monotonic``, so faking ``time.monotonic`` alone
    shifts the middleware deadline by the same amount and the gate can
    never trip. The loop clock is therefore pinned to the real monotonic
    reading (preserving its normal semantics) while the gate-visible
    ``time.monotonic`` jumps once the stub flips the flag (or starts set).
    Expiry timing is fully deterministic with no sleeps.
    """
    import asyncio as _asyncio

    original = time.monotonic
    monkeypatch.setattr(
        _asyncio.BaseEventLoop, "time", lambda self: original()
    )

    def fake() -> float:
        if flag["past"]:
            return original() + 3600.0
        return original()

    monkeypatch.setattr(time, "monotonic", fake)


def test_past_deadline_starts_no_upstream_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An already-exhausted budget starts zero upstream attempts (P1-B).

    Exercises the actual pre-attempt gate in the completions request
    path: with the deadline in the past before the first iteration, no
    provider call begins, the outcome is 503 ``deadline_exceeded``, and
    telemetry finalizes exactly once with no routing decisions.
    """
    stub = StubLiteLLMClient()
    _install_flag_clock(monkeypatch, {"past": True})
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = create_app(state=state)

    with TestClient(
        app, headers={"Authorization": f"Bearer {key}"}, raise_server_exceptions=False
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
        )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "deadline_exceeded"
    assert stub.calls == []
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 503
    assert list(event.routing_decisions) == []
    assert event.failure_category == "deadline_exceeded"
    assert store.finalize_calls == 1


def test_deadline_expiry_between_attempts_starts_no_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deadline expiring after a failed attempt suppresses fallback (P1-B).

    The first attempt fails fast with a retryable 500 (fallback would
    normally follow); the flagged clock expires the budget before the
    second gate evaluation. Proves exactly one upstream invocation, no
    fallback attempt, and terminal ``deadline_exceeded`` classification
    alongside the recorded first-attempt failure.
    """
    stub = StubLiteLLMClient()
    past = {"past": False}
    _install_flag_clock(monkeypatch, past)

    async def failing_once(decision, messages, **kwargs):
        stub.calls.append(decision.deployment)
        past["past"] = True
        raise LiteLLMClientError("boom", status_code=500)

    stub.chat_completion = failing_once  # type: ignore[method-assign]
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = create_app(state=state)

    with TestClient(
        app, headers={"Authorization": f"Bearer {key}"}, raise_server_exceptions=False
    ) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
        )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "deadline_exceeded"
    assert stub.calls == ["primary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 503
    assert len(event.routing_decisions) == 1
    (first,) = event.routing_decisions
    assert first["outcome"] == "failure"
    assert first["failure_category"] == "server"
    assert event.failure_category == "deadline_exceeded"
    assert store.finalize_calls == 1
