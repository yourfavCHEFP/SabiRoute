from __future__ import annotations

from conftest import StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

MESSAGES = [{"role": "user", "content": "hello"}]


def test_admin_reflects_live_request_traffic():
    stub = StubLiteLLMClient(failures={"primary": 1})
    state = build_gateway_state(config=make_config(), client=stub)
    app = create_app(state=state)

    with TestClient(app) as client:
        completion = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
        )
        assert completion.status_code == 200

        health = client.get("/admin/health").json()
        metrics = client.get("/admin/metrics").json()
        latency = client.get("/admin/latency").json()
        errors = client.get("/admin/errors").json()
        usage = client.get("/admin/usage").json()

    assert health["primary"]["total_failures"] == 1
    assert health["secondary"]["total_successes"] == 1

    assert metrics["requests_total"] == 2
    assert metrics["requests_failed"] == 1
    assert metrics["requests_by_model"]["primary"] == 1

    assert "primary" in latency
    assert errors == {"server": 1}
    assert usage["secondary"] == 5


def test_liveness_endpoints():
    state = build_gateway_state(config=make_config(), client=StubLiteLLMClient())
    app = create_app(state=state)

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "service": "sabiroute"}
        assert client.get("/health/live").json() == {"status": "alive"}
