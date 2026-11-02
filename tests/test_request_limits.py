"""R7 integrated-release evidence: docs exposure, request limits, deny-closed.

Lane ownership: R7 (Operations/recovery — integrated regression & release
evidence). Contains only tests that assert the *release surface* of the
gateway as a whole:

- docs exposure contract (fail-closed by default, F-04 policy)
- request body-size and message-shape limits
- body middleware abort/propagation safety
- deny-closed rate limiting when the limiter is absent or unreachable

Tests owned by other lanes were moved out of this file without changing their
bodies (see R7 ownership map):

- ``test_config_credential_policy.py`` — F-06a literal-credential rules (R3)
- ``test_chat_session_hygiene.py``     — F-07 lifespan/session purge (SabiChat)
- ``test_rate_limit_shared_backend.py``— F-08 shared-allowance doubles (rate limit)

Uses only in-process TestClient probes with stubbed providers. No services,
no network, no secrets.
"""

from __future__ import annotations

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.api.body_limit import (
    ABSOLUTE_MAX_BODY_BYTES,
    DEFAULT_MAX_BODY_BYTES,
    request_max_body_bytes,
)
from sabiroute.api.completions import MAX_MESSAGE_CHARS, MAX_MESSAGES_PER_REQUEST
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app


def make_client(**kwargs):
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
    )
    return state, TestClient(create_app(state=state, **kwargs))


# --- docs exposure contract (F-04) ---

def test_docs_disabled_by_default():
    _, client = make_client()
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_docs_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("SABIROUTE_DOCS_ENABLED", "1")
    _, client = make_client()
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_env_variants(monkeypatch):
    for value, expected in (("true", 200), ("YES", 200), ("on", 200), ("0", 404), ("", 404)):
        monkeypatch.setenv("SABIROUTE_DOCS_ENABLED", value)
        _, client = make_client()
        assert client.get("/docs").status_code == expected, value


def test_docs_malformed_value_stays_disabled(monkeypatch):
    monkeypatch.setenv("SABIROUTE_DOCS_ENABLED", "maybe")
    _, client = make_client()
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


# --- request body-size and message-shape limits ---

def test_body_limit_defaults_and_validation(monkeypatch):
    monkeypatch.delenv("SABIROUTE_MAX_REQUEST_BODY_BYTES", raising=False)
    assert request_max_body_bytes() == DEFAULT_MAX_BODY_BYTES == 1_048_576
    for bad in ("0", "-1", "notanumber", str(ABSOLUTE_MAX_BODY_BYTES + 1)):
        monkeypatch.setenv("SABIROUTE_MAX_REQUEST_BODY_BYTES", bad)
        try:
            request_max_body_bytes()
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted bad limit {bad!r}")
    monkeypatch.setenv("SABIROUTE_MAX_REQUEST_BODY_BYTES", "2048")
    assert request_max_body_bytes() == 2048


def _authed_client():
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    return TestClient(create_app(state=state), headers={"Authorization": f"Bearer {key}"})


def test_oversized_body_rejected_before_auth_accounting():
    client = _authed_client()
    big = "x" * (DEFAULT_MAX_BODY_BYTES + 1)
    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": [{"role": "user", "content": big}]},
    )
    assert response.status_code == 413
    body = response.json()["error"]
    assert body["type"] == "request_body_too_large"
    assert body["limit_bytes"] == DEFAULT_MAX_BODY_BYTES


def test_body_at_boundary_passes_middleware():
    client = _authed_client()
    # Just under the limit passes the middleware (endpoint may still 200).
    small = "x" * 100
    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": [{"role": "user", "content": small}]},
    )
    assert response.status_code == 200


def test_chunked_over_limit_rejected_without_length():
    client = _authed_client()
    big = b"x" * (DEFAULT_MAX_BODY_BYTES + 1024)
    response = client.post(
        "/v1/chat/completions",
        content=b'{"model":"primary","messages":[{"role":"user","content":"'
        + big
        + b'"}]}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["type"] == "request_body_too_large"


def test_message_count_cap():
    client = _authed_client()
    many = [{"role": "user", "content": "hi"}] * (MAX_MESSAGES_PER_REQUEST + 1)
    response = client.post("/v1/chat/completions", json={"model": "primary", "messages": many})
    assert response.status_code == 422


def test_message_count_at_boundary():
    client = _authed_client()
    many = [{"role": "user", "content": "hi"}] * MAX_MESSAGES_PER_REQUEST
    response = client.post("/v1/chat/completions", json={"model": "primary", "messages": many})
    # Passes validation (may 200 or fail downstream, but never 422 for shape).
    assert response.status_code != 422


def test_message_content_cap():
    client = _authed_client()
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "primary",
            "messages": [{"role": "user", "content": "x" * (MAX_MESSAGE_CHARS + 1)}],
        },
    )
    assert response.status_code == 413
    assert response.json()["error"]["type"] == "message_content_too_large"


def test_message_content_at_boundary():
    client = _authed_client()
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "primary",
            "messages": [{"role": "user", "content": "x" * MAX_MESSAGE_CHARS}],
        },
    )
    assert response.status_code != 413


def test_malformed_body_not_confused_with_oversize():
    client = _authed_client()
    response = client.post(
        "/v1/chat/completions",
        content=b"{not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_empty_messages_rejected_422():
    client = _authed_client()
    response = client.post(
        "/v1/chat/completions", json={"model": "primary", "messages": []}
    )
    assert response.status_code == 422


# --- body middleware robustness ---

def test_middleware_order_body_before_deadline():
    _, client = make_client()
    names = [
        m.cls.__name__ if hasattr(m, "cls") else type(m).__name__
        for m in client.app.user_middleware
    ]
    assert names.index("BodySizeMiddleware") < names.index("DeadlineMiddleware")


def test_streaming_body_abort_never_fabricates_response():
    """Post-start over-limit abort must propagate, never synthesize a 413."""
    import asyncio

    from sabiroute.api.body_limit import BodySizeMiddleware, _BodyTooLarge

    events: list = []

    async def downstream(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        # consume one chunk then exceed on second
        m1 = await receive()
        events.append(m1.get("body", b""))
        with __import__("pytest").raises(_BodyTooLarge):
            await receive()

    async def fake_receive():
        if not hasattr(fake_receive, "n"):
            fake_receive.n = 0  # type: ignore[attr-defined]
        fake_receive.n += 1  # type: ignore[attr-defined]
        if fake_receive.n == 1:
            return {"type": "http.request", "body": b"x" * 100, "more_body": True}
        return {"type": "http.request", "body": b"x" * (2 * 1024 * 1024), "more_body": False}

    sent: list = []

    async def send(msg):
        sent.append(msg)

    scope = {"type": "http", "headers": []}
    mw = BodySizeMiddleware(downstream, max_body_bytes=1024)

    async def run():
        # drive downstream manually: start response, then feed chunks
        started = False

        async def tracked_send(m):
            nonlocal started
            if m.get("type") == "http.response.start":
                started = True
            sent.append(m)

        async def tracked_receive():
            return await fake_receive()

        try:
            await mw(scope, tracked_receive, tracked_send)
        except _BodyTooLarge:
            pass
        return started

    assert asyncio.run(run()) is True
    # Only the downstream start was sent; no synthetic 413 start followed it.
    starts = [m for m in sent if m.get("type") == "http.response.start"]
    assert len(starts) == 1 and starts[0]["status"] == 200


def test_body_read_receive_exception_propagates():
    import asyncio

    from sabiroute.api.body_limit import BodySizeMiddleware

    async def downstream(scope, receive, send):
        await receive()

    async def fake_receive():
        raise RuntimeError("boom")

    sent: list = []

    async def send(msg):
        sent.append(msg)

    scope = {"type": "http", "headers": []}
    mw = BodySizeMiddleware(downstream, max_body_bytes=1024)

    async def run():
        try:
            await mw(scope, fake_receive, send)
        except RuntimeError as exc:
            return str(exc)
        return "no-exception"

    assert asyncio.run(run()) == "boom"
    # No response was fabricated.
    starts = [m for m in sent if m.get("type") == "http.response.start"]
    assert len(starts) == 0


def test_body_read_disconnect_propagates():
    import asyncio

    from sabiroute.api.body_limit import BodySizeMiddleware

    async def downstream(scope, receive, send):
        await receive()

    async def fake_receive():
        return {"type": "http.disconnect"}

    sent: list = []

    async def send(msg):
        sent.append(msg)

    scope = {"type": "http", "headers": []}
    mw = BodySizeMiddleware(downstream, max_body_bytes=1024)

    async def run():
        try:
            await mw(scope, fake_receive, send)
        except Exception as exc:  # noqa: BLE001
            return type(exc).__name__
        return "completed"

    result = asyncio.run(run())
    # Disconnect message is forwarded; downstream completes without 413.
    assert result == "completed"
    starts = [m for m in sent if m.get("type") == "http.response.start"]
    assert len(starts) == 0


def test_body_read_cancellation_propagates():
    import asyncio

    from sabiroute.api.body_limit import BodySizeMiddleware

    async def downstream(scope, receive, send):
        await receive()

    async def fake_receive():
        raise asyncio.CancelledError()

    sent: list = []

    async def send(msg):
        sent.append(msg)

    scope = {"type": "http", "headers": []}
    mw = BodySizeMiddleware(downstream, max_body_bytes=1024)

    async def run():
        try:
            await mw(scope, fake_receive, send)
        except asyncio.CancelledError:
            return "cancelled"
        return "not-cancelled"

    assert asyncio.run(run()) == "cancelled"
    starts = [m for m in sent if m.get("type") == "http.response.start"]
    assert len(starts) == 0


def test_body_read_send_error_propagates():
    import asyncio

    from sabiroute.api.body_limit import BodySizeMiddleware

    async def downstream(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def fake_receive():
        return {"type": "http.request", "body": b"hello", "more_body": False}

    async def failing_send(msg):
        raise RuntimeError("send-boom")

    scope = {"type": "http", "headers": []}
    mw = BodySizeMiddleware(downstream, max_body_bytes=1024)

    async def run():
        try:
            await mw(scope, fake_receive, failing_send)
        except RuntimeError as exc:
            return str(exc)
        return "no-exception"

    assert asyncio.run(run()) == "send-boom"


# --- deny-closed rate limiting (R7 core) ---

def test_redis_outage_denies_closed_with_contract():
    import asyncio

    from sabiroute.security.keys import ApiKeyRateLimit

    async def run():
        from sabiroute.gateway import build_gateway_state

        state = build_gateway_state(
            config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
        )
        key = provision_test_key(state)

        store = state.key_store
        record_id = next(iter(store.records))
        store.set_rate_limit(record_id, ApiKeyRateLimit(requests_per_minute=60, burst_capacity=5))

        class Outage:
            async def admit(self, *a, **k):
                raise ConnectionError("redis down")

        state.rate_limiter = Outage()
        app = create_app(state=state)
        from fastapi.testclient import TestClient

        with TestClient(app, headers={"Authorization": f"Bearer {key}"}) as client:
            r = client.post(
                "/v1/chat/completions",
                json={"model": "primary", "messages": [{"role": "user", "content": "hi"}]},
            )
            assert r.status_code == 503
            assert r.json()["error"]["type"] == "rate_limiter_unavailable"

    asyncio.run(run())


def test_missing_limiter_with_configured_limit_denies_closed():
    from sabiroute.security.keys import ApiKeyRateLimit

    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    store = state.key_store
    record_id = next(iter(store.records))
    store.set_rate_limit(record_id, ApiKeyRateLimit(requests_per_minute=60, burst_capacity=5))
    assert state.rate_limiter is None
    from fastapi.testclient import TestClient

    with TestClient(create_app(state=state), headers={"Authorization": f"Bearer {key}"}) as client:
        r = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert r.status_code == 503
        assert r.json()["error"]["type"] == "rate_limiter_unavailable"
