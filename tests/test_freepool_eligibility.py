"""Sprint 1: Free Pool eligibility contract for Free Chat requests.

Proves that Free Chat only uses explicitly mapped, eligible deployments;
that denial happens before any LiteLLM call; that fallback cannot bypass the
allowlist; and that the existing non-Free-Pool path is unchanged.
"""

from __future__ import annotations

import pytest
from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    enable_shared_inference,
    make_config,
    provision_test_key,
)
from fastapi.testclient import TestClient

from sabiroute.capabilities import Capability
from sabiroute.freepool.eligibility import (
    FREE_POOL_NO_CAPABLE_DEPLOYMENT,
    FREE_POOL_NO_HEALTHY_DEPLOYMENT,
    FREE_POOL_UNMAPPED_DEPLOYMENT,
    FreePoolDecision,
    FreePoolPolicy,
    deny_reason_for_evaluation,
    evaluate_free_pool,
)
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

MESSAGES = [{"role": "user", "content": "hello"}]

ENABLED = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
DISABLED = FreePoolPolicy()


def make_free_client(stub, *, policy=ENABLED):
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore(), free_pool=policy
    )
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    return TestClient(app, headers={"Authorization": f"Bearer {key}"}), state


def free_body(model="primary", **extra):
    return {"model": model, "messages": MESSAGES, "sabi_route_free_chat": True, **extra}


def single_usage_event(state):
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    events = list(store.usage_events.values())
    assert len(events) == 1
    return events[0]


# --- Pure contract --------------------------------------------------------


def test_disabled_policy_passes_candidates_through():
    decision = evaluate_free_pool(["primary", "ghost"], DISABLED)

    assert decision == FreePoolDecision(
        allowed=True, reason=None, eligible_candidates=("primary", "ghost")
    )


def test_enabled_policy_keeps_only_mapped_aliases_in_order():
    decision = evaluate_free_pool(["secondary", "primary", "ghost"], ENABLED)

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.eligible_candidates == ("primary",)


def test_unknown_or_unmapped_deployment_is_denied():
    decision = evaluate_free_pool(["ghost", "secondary"], ENABLED)

    assert decision.allowed is False
    assert decision.reason == FREE_POOL_UNMAPPED_DEPLOYMENT
    assert decision.eligible_candidates == ()


def test_empty_candidates_are_denied_when_enabled():
    decision = evaluate_free_pool([], ENABLED)

    assert decision.allowed is False
    assert decision.reason == FREE_POOL_UNMAPPED_DEPLOYMENT


def test_policy_from_mapping_requires_explicit_values():
    policy = FreePoolPolicy.from_mapping(
        {"enabled": True, "eligible_deployments": ["primary", " secondary "]}
    )

    assert policy.enabled is True
    assert policy.eligible_deployments == frozenset({"primary", "secondary"})

    with pytest.raises(ValueError):
        FreePoolPolicy.from_mapping({"enabled": True})
    with pytest.raises(ValueError):
        FreePoolPolicy.from_mapping({"enabled": "yes", "eligible_deployments": []})
    with pytest.raises(ValueError):
        FreePoolPolicy.from_mapping({"enabled": True, "eligible_deployments": [" "]})
    with pytest.raises(TypeError):
        FreePoolPolicy.from_mapping(["primary"])


def test_deny_reason_prefers_capability_over_health():
    stub = StubLiteLLMClient()
    _, state = make_free_client(stub)

    no_capable = state.router.evaluate_candidates(
        ["primary"], required_capabilities=[Capability.VISION]
    )
    assert deny_reason_for_evaluation(no_capable) == FREE_POOL_NO_CAPABLE_DEPLOYMENT

    for _ in range(3):
        state.health.mark_failure("primary")
    unhealthy = state.router.evaluate_candidates(["primary"])
    assert deny_reason_for_evaluation(unhealthy) == FREE_POOL_NO_HEALTHY_DEPLOYMENT

    healthy = state.router.evaluate_candidates(["secondary"])
    assert deny_reason_for_evaluation(healthy) is None


def test_policy_parsed_from_environment(monkeypatch):
    monkeypatch.setenv("SABIROUTE_FREEPOOL_ENABLED", "1")
    monkeypatch.setenv("SABIROUTE_FREEPOOL_DEPLOYMENTS", "primary, secondary,,")
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
    )

    assert state.free_pool.enabled is True
    assert state.free_pool.eligible_deployments == frozenset({"primary", "secondary"})


def test_policy_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SABIROUTE_FREEPOOL_ENABLED", raising=False)
    monkeypatch.delenv("SABIROUTE_FREEPOOL_DEPLOYMENTS", raising=False)
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
    )

    assert state.free_pool == FreePoolPolicy()


# --- Request path ---------------------------------------------------------


def test_allowed_free_chat_request_reaches_litellm_once():
    stub = StubLiteLLMClient()
    client, _ = make_free_client(stub)

    response = client.post("/v1/chat/completions", json=free_body("primary"))

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "primary"
    assert stub.calls == ["primary"]


def test_unmapped_free_chat_request_denied_before_litellm():
    stub = StubLiteLLMClient()
    client, state = make_free_client(stub)

    response = client.post("/v1/chat/completions", json=free_body("secondary"))

    assert response.status_code == 403
    assert response.json()["error"]["type"] == FREE_POOL_UNMAPPED_DEPLOYMENT
    assert stub.calls == []

    event = single_usage_event(state)
    assert event.final_status == 403
    assert event.failure_category == FREE_POOL_UNMAPPED_DEPLOYMENT


def test_unhealthy_allowlisted_deployment_denied_before_litellm():
    stub = StubLiteLLMClient()
    client, state = make_free_client(stub)
    for _ in range(3):
        state.health.mark_failure("primary")

    response = client.post("/v1/chat/completions", json=free_body("primary"))

    assert response.status_code == 503
    assert response.json()["error"]["type"] == FREE_POOL_NO_HEALTHY_DEPLOYMENT
    assert stub.calls == []

    event = single_usage_event(state)
    assert event.final_status == 503
    assert event.failure_category == FREE_POOL_NO_HEALTHY_DEPLOYMENT


def test_marked_request_fails_closed_when_policy_disabled():
    stub = StubLiteLLMClient()
    client, state = make_free_client(stub, policy=DISABLED)

    response = client.post("/v1/chat/completions", json=free_body("primary"))

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "free_pool_unavailable"
    assert stub.calls == []

    event = single_usage_event(state)
    assert event.failure_category == "free_pool_unavailable"


def test_fallback_cannot_leave_the_allowlist():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, _ = make_free_client(stub)

    response = client.post("/v1/chat/completions", json=free_body("fast"))

    assert response.status_code == 502
    assert stub.calls == ["primary"]
    assert "secondary" not in stub.calls


def test_unmarked_request_ignores_the_allowlist():
    stub = StubLiteLLMClient()
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
    client, _ = make_free_client(stub, policy=policy)

    response = client.post(
        "/v1/chat/completions", json={"model": "secondary", "messages": MESSAGES}
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert stub.calls == ["secondary"]
