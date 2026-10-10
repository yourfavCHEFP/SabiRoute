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
