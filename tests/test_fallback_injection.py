"""Fallback failure-injection tests using in-process mocks (no live providers)."""

from __future__ import annotations

import asyncio

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app


def _client(stub: StubLiteLLMClient):
    state = build_gateway_state(config=make_config(), client=stub, key_store=InMemoryApiKeyStore())
    key = provision_test_key(state)
    client = TestClient(create_app(state=state), headers={"Authorization": f"Bearer {key}"})
    return client, state, stub


def test_retryable_primary_failure_falls_back():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state, _ = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert response.headers["X-SabiRoute-Attempt"] == "2"
    assert stub.calls == ["primary", "secondary"]


def test_non_retryable_400_does_not_fallback():
    stub = StubLiteLLMClient(failures={"primary": 1}, failure_status=400)
    client, state, _ = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary"]


def test_all_deployments_fail_terminal_error():
    stub = StubLiteLLMClient(failures={"primary": 1, "secondary": 1})
    client, state, _ = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary", "secondary"]
    assert response.json()["error"]["attempts"] == ["primary", "secondary"]


def test_deadline_expired_prevents_invocation(monkeypatch):
    import sabiroute.api.completions as mod

    monkeypatch.setattr(mod, "_deadline_expired", lambda request: True)
    stub = StubLiteLLMClient()
    client, state, _ = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "deadline_exceeded"
    assert stub.calls == []


def test_cancellation_propagates_no_fallback():
    import pytest
    from test_completions import make_direct_request

    from sabiroute.api.completions import ChatCompletionRequest, chat_completions

    stub = StubLiteLLMClient()

    async def cancelled_completion(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        raise asyncio.CancelledError

    stub.chat_completion = cancelled_completion  # type: ignore[method-assign]
    state = build_gateway_state(config=make_config(), client=stub, key_store=InMemoryApiKeyStore())
    provision_test_key(state)
    request = make_direct_request(state)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            chat_completions(
                ChatCompletionRequest(model="fast", messages=[{"role": "user", "content": "hi"}]),
                request,
            )
        )

    # Exactly one attempt, on primary; no fallback to secondary.
    assert stub.calls == ["primary"]
    # Cancellation must not poison deployment health: no failure recorded.
    assert state.health.snapshot()["primary"]["total_failures"] == 0
    # Telemetry records the cancelled attempt with the expected category.
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 499
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["failure_category"] == "client_cancelled"
    assert event.routing_decisions[0]["outcome"] == "failure"


def test_cooldown_excludes_failed_deployment():
    # failure_threshold is 3; fail primary three times to trip cooldown.
    stub = StubLiteLLMClient(failures={"primary": 3})
    client, state, _ = _client(stub)

    for _ in range(3):
        r = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert r.status_code == 200

    before = len(stub.calls)
    fourth = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert fourth.status_code == 200
    # primary is in cooldown and must not be invoked.
    assert "primary" not in stub.calls[before:]
