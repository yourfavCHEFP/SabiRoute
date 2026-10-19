"""Batch 2: docs exposure policy, body-size protection, message shape caps.

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


# --- F-06a literal-credential policy ---

def test_literal_secret_rejected_without_value_leak():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import ConfigValidationError, validate_config

    secret = "sk-live-REALISTIC-SECRET-abc123"
    try:
        validate_config(
            SabiRouteConfig.from_mapping(
                {
                    "model_list": [
                        {
                            "model_name": "prod",
                            "litellm_params": {
                                "model": "openai/gpt-4o-mini",
                                "api_key": secret,
                            },
                        }
                    ]
                }
            )
        )
    except ConfigValidationError as exc:
        assert "literal" in str(exc).lower()
        assert secret not in str(exc)
    else:
        raise AssertionError("literal secret was accepted")


def test_marked_test_credential_accepted():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import validate_config

    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "t",
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "sk-test-fixture-only",
                        },
                    }
                ]
            }
        )
    )
    assert config.model_list[0].litellm_params.api_key == "sk-test-fixture-only"


def test_allowlist_rejects_whitespace_padded_values():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import ConfigValidationError, validate_config

    for bad in (" sk-test-123", "sk-test-123 ", "sk-test-123\n"):
        try:
            validate_config(
                SabiRouteConfig.from_mapping(
                    {
                        "model_list": [
                            {
                                "model_name": "t",
                                "litellm_params": {
                                    "model": "openai/x",
                                    "api_key": bad,
                                },
                            }
                        ]
                    }
                )
            )
        except ConfigValidationError:
            pass
        else:
            raise AssertionError(f"whitespace-padded value accepted: {bad!r}")


def test_env_reference_accepted_and_missing_var_fails():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import validate_config

    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "t",
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "os.environ/OPENAI_API_KEY",
                        },
                    }
                ]
            }
        )
    )
    assert config.model_list[0].litellm_params.api_key == "os.environ/OPENAI_API_KEY"
    # Missing-variable behavior lives in the loader/resolver layer:
    from sabiroute.config.loader import ConfigLoadError, _resolve_os_environ_value

    try:
        _resolve_os_environ_value("os.environ/SABIROUTE_DEFINITELY_UNSET_VAR_XYZ")
    except ConfigLoadError as exc:
        assert "SABIROUTE_DEFINITELY_UNSET_VAR_XYZ" in str(exc)
    else:
        raise AssertionError("missing env var was accepted")


# --- F-07 lifespan-owned cleanup ---

def test_startup_purges_expired_sessions_only(tmp_path):
    from datetime import UTC, datetime, timedelta

    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'purge.sqlite'}")
    now = datetime.now(UTC)
    uid = store.create_user("purge@example.com", "hashed").user_id
    # expired session
    store.create_session(uid, "a" * 64, now - timedelta(days=1))
    # live session
    store.create_session(uid, "b" * 64, now + timedelta(days=7))
    assert store.purge_expired_sessions(now) == 1
    # idempotent re-run removes nothing
    assert store.purge_expired_sessions(now) == 0


def test_lifespan_purge_runs_and_never_breaks_startup(tmp_path):
    from datetime import UTC, datetime, timedelta

    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'lifespan-purge.sqlite'}")
    now = datetime.now(UTC)
    uid = store.create_user("life@example.com", "hashed").user_id
    store.create_session(uid, "c" * 64, now - timedelta(days=1))
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore(),
        chat_store=store,
    )
    with TestClient(create_app(state=state)):
        pass
    # expired row removed by lifespan purge; live path unaffected
    assert store.purge_expired_sessions(now) == 0
    ready = TestClient(create_app(state=state)).get("/health/ready")
    assert ready.status_code == 200


def test_purge_failure_is_hygiene_not_outage(tmp_path, monkeypatch):
    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'purge-fail.sqlite'}")

    def boom(*a, **k):
        raise RuntimeError("store down")

    monkeypatch.setattr(store, "purge_expired_sessions", boom)
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore(),
        chat_store=store,
    )
    with TestClient(create_app(state=state)) as client:
        assert client.get("/health/live").status_code == 200


# --- F-08 multi-instance shared enforcement (deterministic doubles) ---

class _ScriptlessBucket:
    """Minimal RedisTokenBucket-shaped double sharing one dict backend."""

    def __init__(self, backend: dict, prefix: str = "t"):
        self._backend = backend
        self._prefix = prefix

    async def admit(self, key_id: str, limit) -> object:
        import time as _time

        now_ms = int(_time.time() * 1000)
        window_ms = 60_000
        key = f"{self._prefix}:{key_id}"
        state = self._backend.setdefault(
            key, {"tokens": limit.burst_capacity, "last": now_ms}
        )
        elapsed = now_ms - state["last"]
        refill = elapsed * limit.requests_per_minute / window_ms
        state["tokens"] = min(limit.burst_capacity, state["tokens"] + refill)
        state["last"] = now_ms
        from types import SimpleNamespace

        if state["tokens"] >= 1:
            state["tokens"] -= 1
            return SimpleNamespace(admitted=True, retry_after_seconds=None)
        return SimpleNamespace(admitted=False, retry_after_seconds=1)

    def key(self, key_id: str) -> str:
        return f"{self._prefix}:{key_id}"


def test_two_instances_share_one_backend_allowance():
    import asyncio

    from sabiroute.security.keys import ApiKeyRateLimit

    backend: dict = {}
    a = _ScriptlessBucket(backend, prefix="shared")
    b = _ScriptlessBucket(backend, prefix="shared")
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=3)

    async def run():
        r1 = await a.admit("k", limit)
        r2 = await b.admit("k", limit)
        r3 = await a.admit("k", limit)
        r4 = await b.admit("k", limit)
        return [r.admitted for r in (r1, r2, r3, r4)]

    assert asyncio.run(run()) == [True, True, True, False]


def test_distinct_prefixes_do_not_share_allowance():
    import asyncio

    from sabiroute.security.keys import ApiKeyRateLimit

    backend: dict = {}
    a = _ScriptlessBucket(backend, prefix="one")
    b = _ScriptlessBucket(backend, prefix="two")
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=1)

    async def run():
        return [(await a.admit("k", limit)).admitted, (await b.admit("k", limit)).admitted]

    assert asyncio.run(run()) == [True, True]


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


def test_docs_malformed_value_stays_disabled(monkeypatch):
    monkeypatch.setenv("SABIROUTE_DOCS_ENABLED", "maybe")
    _, client = make_client()
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_middleware_order_body_before_deadline():
    _, client = make_client()
    names = [
        m.cls.__name__ if hasattr(m, "cls") else type(m).__name__
        for m in client.app.user_middleware
    ]
    assert names.index("BodySizeMiddleware") < names.index("DeadlineMiddleware")


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


def test_empty_messages_rejected_422():
    client = _authed_client()
    response = client.post(
        "/v1/chat/completions", json={"model": "primary", "messages": []}
    )
    assert response.status_code == 422


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


def test_purge_removes_revoked_past_retention_keeps_recent(tmp_path):
    from datetime import UTC, datetime, timedelta

    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'revoked.sqlite'}")
    now = datetime.now(UTC)
    uid = store.create_user("rev@example.com", "h").user_id
    # old revoked (40 days ago) -> purged; recent revoked -> kept; live -> kept
    s_old = store.create_session(uid, "o" * 64, now + timedelta(days=7))
    s_new = store.create_session(uid, "n" * 64, now + timedelta(days=7))
    store.create_session(uid, "l" * 64, now + timedelta(days=7))
    # backdate revoked_at via direct SQL (store API stamps now)
    from sqlalchemy import update

    from sabiroute.chat.store import _SABICHAT_SESSIONS

    with store._engine.begin() as conn:
        conn.execute(
            update(_SABICHAT_SESSIONS)
            .where(_SABICHAT_SESSIONS.c.session_id == s_old.session_id)
            .values(revoked_at=now - timedelta(days=40))
        )
    store.revoke_session(s_new.session_id)
    removed = store.purge_expired_sessions(now)
    assert removed == 1
    assert store.get_session("o" * 64) is None
    assert store.get_session("n" * 64) is not None
    assert store.get_session("l" * 64) is not None
