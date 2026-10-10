from __future__ import annotations

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.config.loader import DEFAULT_CONFIG_PATH, load_config
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.policies import PolicyRegistry


def test_runtime_route_files_reference_configured_deployments():
    config = load_config(DEFAULT_CONFIG_PATH)
    registry = registry_from_config(config)
    route_dir = DEFAULT_CONFIG_PATH.parent / "routes"

    policies = PolicyRegistry.from_directory(route_dir, registry)

    assert {policy.name for policy in policies.list()} == {
        "ultimate",
        "coding",
        "research",
        "reasoning",
        "fast",
        "cheap",
    }
    assert policies.get("fast").deployments == ["sabiroute-gemini", "sabiroute-openai"]
    assert policies.get("fast").max_attempts == 2
    assert policies.get("cheap").deployments == ["sabiroute-gemini"]
    assert policies.get("cheap").max_attempts == 1


def test_gateway_uses_runtime_route_files(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")

    state = build_gateway_state()

    assert state.policies.get("fast").deployments == [
        "sabiroute-gemini",
        "sabiroute-openai",
    ]
    assert state.policies.get("ultimate").max_attempts == 3


def test_runtime_virtual_model_preserves_ordinary_chat_fallback(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    client_stub = StubLiteLLMClient(failures={"sabiroute-gemini": 1})
    state = build_gateway_state(client=client_stub, key_store=InMemoryApiKeyStore())
    key = provision_test_key(state)

    with TestClient(create_app(state=state), headers={"Authorization": f"Bearer {key}"}) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "fast",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )

    assert response.status_code == 200
    assert client_stub.calls == [
        "sabiroute-gemini",
        "sabiroute-openai",
    ]


@pytest.mark.parametrize(
    "route_yaml, error",
    [
        ("name: broken\ndeployments: [missing-model]\nmax_attempts: 1\n", "Invalid deployment"),
        (
            "name: broken\ndeployments: [primary]\nstrategy: weighted\nmax_attempts: 1\n",
            "unsupported strategy",
        ),
        ("name: broken\ndeployments: [primary]\nmax_attempts: 2\n", "candidate count"),
    ],
)
def test_route_configuration_rejects_invalid_candidates_and_settings(
    tmp_path, route_yaml: str, error: str
):
    from conftest import make_config

    registry = registry_from_config(make_config())
    route_file = tmp_path / "broken.yaml"
    route_file.write_text(route_yaml, encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        PolicyRegistry.from_directory(tmp_path, registry)
