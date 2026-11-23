from __future__ import annotations

from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    make_config,
    provision_test_key,
)
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

MESSAGES = [{"role": "user", "content": "hello"}]


def test_admin_reflects_live_request_traffic(monkeypatch):
    stub = StubLiteLLMClient(failures={"primary": 1})
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    client_key = provision_test_key(state)
    admin_key = "test-admin-secret-distinct-from-client-key"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", admin_key)
    app = create_app(state=state)

    with TestClient(app) as client:
        completion = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {client_key}"},
        )
        assert completion.status_code == 200

        admin_headers = {"Authorization": f"Bearer {admin_key}"}
        health = client.get("/admin/health", headers=admin_headers).json()
        metrics = client.get("/admin/metrics", headers=admin_headers).json()
        latency = client.get("/admin/latency", headers=admin_headers).json()
        errors = client.get("/admin/errors", headers=admin_headers).json()
        usage = client.get("/admin/usage", headers=admin_headers).json()
        key_usage = client.get(
            f"/admin/api-keys/{next(iter(state.key_store.records))}/usage",
            headers=admin_headers,
        ).json()

    assert health["primary"]["total_failures"] == 1
    assert health["secondary"]["total_successes"] == 1

    assert metrics["requests_total"] == 2
    assert metrics["requests_failed"] == 1
    assert metrics["requests_by_model"]["primary"] == 1

    assert "primary" in latency
    assert errors == {"server": 1}
    assert usage["secondary"] == 5
    route_attempts = key_usage["items"][0]["routing_decisions"]
    assert [item["outcome"] for item in route_attempts] == ["failure", "success"]
    assert all("scoring_policy_version" in item for item in route_attempts)


def test_liveness_endpoints(monkeypatch):
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    provision_test_key(state)
    monkeypatch.delenv("SABIROUTE_ADMIN_KEY", raising=False)
    app = create_app(state=state)

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "service": "sabiroute"}
        assert client.get("/health/live").json() == {"status": "alive"}


def test_readiness_reports_ready_when_request_path_is_servable():
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    provision_test_key(state)
    app = create_app(state=state)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    # F-08: component names and whether rate limiting is configured are not
    # disclosed to an unauthenticated caller. The verdict is the whole body.
    assert set(body) == {"status"}


def test_readiness_recovers_after_transient_schema_check_failure(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    import sabiroute.api.health as health_module
    from sabiroute.security.store import ensure_schema

    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    provision_test_key(state)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    ensure_schema(engine, groups="full")
    state.key_store._engine = engine

    calls = 0

    def fail_once(_engine):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("transient schema check failure")

    monkeypatch.setattr(health_module, "check_schema", fail_once)
    app = create_app(state=state)
    client = TestClient(app)

    first = client.get("/health/ready")
    second = client.get("/health/ready")

    assert first.status_code == 503
    assert second.status_code == 200
    # F-08: the recovery is observable from the status code alone.
    assert second.json() == {"status": "ready"}


def test_readiness_fails_when_startup_is_degraded():
    from sabiroute.gateway import empty_gateway_state

    app = create_app(state=empty_gateway_state())

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    # F-08: which component failed is not disclosed to an anonymous caller.
    assert set(body) == {"status"}
