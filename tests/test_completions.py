from __future__ import annotations

from conftest import StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state, empty_gateway_state
from sabiroute.main import create_app, main

MESSAGES = [{"role": "user", "content": "hello"}]


def make_client(stub: StubLiteLLMClient):
    state = build_gateway_state(config=make_config(), client=stub)
    app = create_app(state=state)
    return TestClient(app), state


def test_success_returns_body_and_routing_headers():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "primary"
    assert response.json()["model"] == "primary"
    assert stub.calls == ["primary"]

    assert state.metrics.snapshot()["requests_total"] == 1
    assert state.metrics.snapshot()["requests_successful"] == 1
    assert state.usage.totals()["primary"] == 5
    assert state.health.snapshot()["primary"]["healthy"] is True


def test_alias_request_does_not_fan_out():
    stub = StubLiteLLMClient(failures={"primary": 5})
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert response.json()["error"]["attempts"] == ["primary"]
    assert stub.calls == ["primary"]


def test_policy_request_falls_back_to_next_deployment():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert response.headers["X-SabiRoute-Attempt"] == "2"
    assert stub.calls == ["primary", "secondary"]

    snapshot = state.health.snapshot()
    assert snapshot["primary"]["total_failures"] == 1
    assert snapshot["secondary"]["healthy"] is True


def test_policy_alias_normalization():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "SabiRoute_Fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"


def test_non_retryable_client_error_stops_retrying():
    stub = StubLiteLLMClient(failures={"primary": 3}, failure_status=400)
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ultimate", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary"]


def test_unknown_model_returns_available_list():
    stub = StubLiteLLMClient()
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "nope", "messages": MESSAGES},
    )

    assert response.status_code == 404
    assert "primary" in response.json()["error"]["available_models"]


def test_streaming_rejected_explicitly():
    stub = StubLiteLLMClient()
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 400
    assert "Streaming" in response.json()["error"]["message"]


def test_empty_registry_returns_503_with_startup_error():
    state = empty_gateway_state()
    state.startup_error = "config not found"
    app = create_app(state=state)

    with TestClient(app) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
        )

    assert response.status_code == 503
    assert "config not found" in response.json()["error"]["message"]


def test_extras_pass_through_to_client():
    stub = StubLiteLLMClient()
    captured: dict = {}
    original = stub.chat_completion

    async def capture(decision, messages, **extra):
        captured.update(extra)
        return await original(decision, messages, **extra)

    stub.chat_completion = capture  # type: ignore[method-assign]
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "primary",
            "messages": MESSAGES,
            "temperature": 0.2,
            "top_p": 0.9,
        },
    )

    assert response.status_code == 200
    assert captured["temperature"] == 0.2
    assert captured["top_p"] == 0.9


def test_console_entry_point_exists():
    assert callable(main)
