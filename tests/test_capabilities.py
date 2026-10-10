from __future__ import annotations

from dataclasses import replace

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.capabilities import (
    Capability,
    DeploymentCapabilities,
    RequestType,
    classify_request,
)
from sabiroute.config.models import SabiRouteConfig
from sabiroute.config.validation import validate_config
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.policies import RoutingPolicy
from sabiroute.routing.router import (
    NoCapableDeploymentError,
    NoHealthyDeploymentError,
    NoRemainingDeploymentError,
    Router,
)


def _capability_router() -> tuple[Router, HealthRegistry]:
    registry = registry_from_config(make_config())
    registry._deployments["primary"] = replace(
        registry.get("primary"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT}),
            unsupported=frozenset({Capability.CODING, Capability.VISION}),
        ),
    )
    registry._deployments["secondary"] = replace(
        registry.get("secondary"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT, Capability.CODING, Capability.TOOL_USE}),
            unsupported=frozenset({Capability.VISION}),
        ),
    )
    registry._deployments["cloudy"] = replace(
        registry.get("cloudy"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT}),
            unsupported=frozenset({Capability.CODING}),
        ),
    )
    registry._deployments["literal-key"] = replace(
        registry.get("literal-key"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT, Capability.CODING}),
        ),
    )
    health = HealthRegistry()
    return Router(registry, health=health), health


def test_classifier_is_deterministic_and_uses_request_facts_only() -> None:
    messages = [{"role": "user", "content": "write code"}]
    first = classify_request(explicit_type=None, options={}, messages=messages)
    second = classify_request(explicit_type=None, options={}, messages=messages)
    coding = classify_request(
        explicit_type=RequestType.CODING_AGENT,
        options={
            "tools": [{"type": "function", "function": {"name": "run"}}],
            "response_format": {"type": "json_object"},
        },
        messages=[{"role": "user", "content": "please execute"}],
    )

    assert first == second
    assert first.request_type is RequestType.CHAT
    assert first.required_capabilities == frozenset()
    assert coding.request_type is RequestType.CODING_AGENT
    assert coding.tool_use_required is True
    assert coding.structured_output_required is True
    assert coding.required_capabilities == frozenset(
        {
            Capability.CHAT,
            Capability.CODING,
            Capability.TOOL_USE,
            Capability.STRUCTURED_OUTPUT,
            Capability.JSON,
        }
    )


def test_classifier_derives_streaming_and_visual_content_requirements() -> None:
    classified = classify_request(
        explicit_type=None,
        options={"stream": True},
        messages=[
            {
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": "opaque"}}],
            }
        ],
    )

    assert classified.streaming_required is True
    assert classified.vision_required is True
    assert classified.multimodal_required is True
    assert {
        Capability.STREAMING,
        Capability.VISION,
        Capability.MULTIMODAL,
    } <= classified.required_capabilities


def test_classifier_does_not_assume_unknown_content_part_is_multimodal() -> None:
    classified = classify_request(
        explicit_type=None,
        options={},
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": "hello"}, {"type": "vendor_extension"}],
            }
        ],
    )

    assert classified.multimodal_required is False
    assert classified.vision_required is False
    assert Capability.MULTIMODAL not in classified.required_capabilities


def test_capability_filter_selects_supported_candidate_and_explains_exclusion() -> None:
    routing, _ = _capability_router()
    requirements = {Capability.CHAT, Capability.CODING}

    decision = routing.choose_deployment(
        ["primary", "secondary", "cloudy"],
        required_capabilities=requirements,
        request_type=RequestType.CODING_AGENT,
    )

    assert decision.deployment == "secondary"
    assert decision.explanation is not None
    assert decision.explanation.candidate_deployments == ("primary", "secondary", "cloudy")
    assert decision.explanation.capability_eligible_deployments == ("secondary",)
    assert decision.explanation.capability_excluded_deployments == {
        "primary": ("unsupported:coding",),
        "cloudy": ("unsupported:coding",),
    }
    assert decision.explanation.request_type is RequestType.CODING_AGENT
    assert decision.explanation.required_capabilities == (
        Capability.CHAT,
        Capability.CODING,
    )


def test_explicit_chat_request_selects_chat_verified_deployment() -> None:
    routing, _ = _capability_router()
    classified = classify_request(
        explicit_type=RequestType.CHAT,
        options={},
        messages=[{"role": "user", "content": "hello"}],
    )

    decision = routing.choose_deployment(
        ["primary", "secondary"],
        required_capabilities=classified.required_capabilities,
        request_type=classified.request_type,
    )

    assert decision.deployment == "primary"


def test_unknown_capability_is_excluded_without_inference() -> None:
    routing, _ = _capability_router()
    evaluation = routing.evaluate_candidates(
        ["primary"], required_capabilities={Capability.CHAT, Capability.REASONING}
    )

    assert evaluation.capability_eligible_deployments == ()
    assert evaluation.capability_excluded_deployments["primary"] == ("unknown:reasoning",)
    with pytest.raises(NoCapableDeploymentError):
        routing.choose_deployment(
            ["primary"], required_capabilities={Capability.CHAT, Capability.REASONING}
        )


def test_unhealthy_capable_deployment_is_skipped_after_capability_filter() -> None:
    routing, health = _capability_router()
    for _ in range(health.failure_threshold):
        health.mark_failure("secondary")

    decision = routing.choose_deployment(
        ["primary", "secondary"],
        required_capabilities={Capability.CHAT},
    )

    assert decision.deployment == "primary"
    assert decision.explanation is not None
    assert decision.explanation.unhealthy_deployments == ("secondary",)


def test_fallback_remains_inside_capability_eligible_set() -> None:
    routing, _ = _capability_router()
    required = {Capability.CHAT, Capability.CODING}
    candidates = ["primary", "secondary", "cloudy", "literal-key"]
    first = routing.choose_deployment(
        candidates, required_capabilities=required
    )
    second = routing.choose_deployment(
        candidates,
        required_capabilities=required,
        attempted=[first.deployment],
    )

    assert (first.deployment, second.deployment) == ("secondary", "literal-key")
    with pytest.raises(NoRemainingDeploymentError):
        routing.choose_deployment(
            candidates,
            required_capabilities=required,
            attempted=["secondary", "literal-key"],
        )


def test_no_healthy_capable_deployment_has_distinct_error() -> None:
    routing, health = _capability_router()
    for name in ("primary", "secondary"):
        for _ in range(health.failure_threshold):
            health.mark_failure(name)

    with pytest.raises(NoHealthyDeploymentError):
        routing.choose_deployment(
            ["primary", "secondary"], required_capabilities={Capability.CHAT}
        )


def test_api_enforces_capabilities_on_initial_route_and_fallback(monkeypatch) -> None:
    client_stub = StubLiteLLMClient(failures={"secondary": 1})
    state = build_gateway_state(
        config=make_config(), client=client_stub, key_store=InMemoryApiKeyStore()
    )
    registry = state.registry
    registry._deployments["primary"] = replace(
        registry.get("primary"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT}),
            unsupported=frozenset({Capability.CODING}),
        ),
    )
    registry._deployments["secondary"] = replace(
        registry.get("secondary"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT, Capability.CODING}),
        ),
    )
    registry._deployments["cloudy"] = replace(
        registry.get("cloudy"),
        capabilities=DeploymentCapabilities(supported=frozenset({Capability.CHAT})),
    )
    registry._deployments["literal-key"] = replace(
        registry.get("literal-key"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT, Capability.CODING}),
        ),
    )
    state.policies.register(
        RoutingPolicy(
            name="coding",
            deployments=["primary", "secondary", "cloudy", "literal-key"],
            max_attempts=4,
            required_capabilities=frozenset({Capability.CODING}),
        )
    )
    key = provision_test_key(state)
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "phase11-admin")

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "coding",
                "sabi_route_request_type": "coding_agent",
                "messages": [{"role": "user", "content": "do the task"}],
            },
        )

    assert response.status_code == 200
    assert client_stub.calls == ["secondary", "literal-key"]
    assert response.headers["X-SabiRoute-Deployment"] == "literal-key"
    assert "capability_excluded_deployments" not in response.text
    assert "selection_reason" not in response.text


def test_current_unannotated_config_stays_unknown_and_fails_explicitly() -> None:
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore()
    )
    for name in ("primary", "secondary", "cloudy", "literal-key"):
        state.registry._deployments[name] = replace(
            state.registry.get(name), capabilities=DeploymentCapabilities()
        )
    key = provision_test_key(state)

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "primary",
                "messages": [{"role": "user", "content": "hi"}],
                "sabi_route_request_type": "coding_agent",
            },
        )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "no_capable_deployment"
    assert "primary" not in response.text


def test_config_rejects_unknown_capability_and_accepts_unknown_state() -> None:
    base = make_config().model_dump(mode="python")
    base["model_list"][0]["capabilities"] = {"unknown-capability": True}
    with pytest.raises(ValueError):
        SabiRouteConfig.from_mapping(base)

    base = make_config().model_dump(mode="python")
    base["model_list"][0]["capabilities"] = {"chat": 1}
    with pytest.raises(ValueError):
        SabiRouteConfig.from_mapping(base)

    base = make_config().model_dump(mode="python")
    base["model_list"][0]["capabilities"] = {
        "chat": "unknown",
        "coding": True,
        "vision": False,
    }
    config = validate_config(SabiRouteConfig.from_mapping(base))
    profile = registry_from_config(config).get("primary").capabilities
    assert profile.supported == frozenset({Capability.CODING})
    assert profile.unsupported == frozenset({Capability.VISION})
    assert profile.missing_requirements({Capability.CHAT})[1] == frozenset({Capability.CHAT})
