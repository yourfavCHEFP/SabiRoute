"""Behavioural tests for :mod:`sabiroute.providers.registry`."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from sabiroute.providers.registry import (
    ProviderRegistry,
    _environment_reference_name,
    _model_dump,
    _provider_from_model,
    registry_from_config,
)


def _deployment(name: str, provider: str = "openai", **extra: Any) -> Any:
    return SimpleNamespace(name=name, provider=provider, **extra)


def _provider(name: str) -> Any:
    return SimpleNamespace(name=name)


def _registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register_provider(_provider("openai"))
    return registry


def test_provider_names_are_normalised_and_unique() -> None:
    registry = _registry()

    assert registry.has_provider(" OpenAI ") is True

    with pytest.raises(ValueError) as excinfo:
        registry.register_provider(_provider("OPENAI"))

    assert "already registered" in str(excinfo.value)


def test_empty_provider_name_is_rejected() -> None:
    with pytest.raises(ValueError) as excinfo:
        ProviderRegistry().register_provider(_provider("   "))

    assert "cannot be empty" in str(excinfo.value)


def test_deployment_requires_a_registered_provider() -> None:
    registry = _registry()

    with pytest.raises(ValueError) as excinfo:
        registry.register(_deployment("d1", provider="anthropic"))

    assert "is not registered" in str(excinfo.value)


def test_deployment_rejects_blank_name_and_duplicates() -> None:
    registry = _registry()

    with pytest.raises(ValueError):
        registry.register(_deployment("  "))

    registry.register(_deployment("d1"))

    with pytest.raises(ValueError) as excinfo:
        registry.register(_deployment("d1"))

    assert "already registered" in str(excinfo.value)


def test_lookup_and_membership() -> None:
    registry = _registry()
    deployment = _deployment("d1")
    registry.register(deployment)

    assert registry.get("  d1 ") is deployment
    assert registry.has_deployment("d1") is True
    assert registry.list_deployments() == [deployment]
    assert len(registry) == 1
    assert list(registry) == [deployment]

    with pytest.raises(KeyError):
        registry.get("absent")
    with pytest.raises(KeyError):
        registry.get_provider("absent")


def test_provider_deployments_filters_by_provider() -> None:
    registry = _registry()
    registry.register_provider(_provider("anthropic"))
    registry.register(_deployment("a", provider="openai"))
    registry.register(_deployment("b", provider=" Anthropic "))

    assert [d.name for d in registry.provider_deployments("ANTHROPIC")] == ["b"]


def test_validate_candidates_preserves_order_and_drops_repeats() -> None:
    registry = _registry()
    registry.register(_deployment("a"))
    registry.register(_deployment("b"))

    assert registry.validate_candidates(["b", "a", "b"]) == ["b", "a"]


def test_validate_candidates_rejects_blank_and_unknown() -> None:
    registry = _registry()
    registry.register(_deployment("a"))

    with pytest.raises(ValueError) as excinfo:
        registry.validate_candidates(["a", " "])

    assert "cannot be empty" in str(excinfo.value)

    with pytest.raises(KeyError):
        registry.validate_candidates(["ghost"])


def test_provider_from_model_requires_a_prefix() -> None:
    assert _provider_from_model("openai/gpt-4o-mini") == "openai"

    with pytest.raises(ValueError) as excinfo:
        _provider_from_model("gpt-4o-mini")

    assert "expected 'provider/model'" in str(excinfo.value)


def test_environment_reference_name_extraction() -> None:
    assert _environment_reference_name("os.environ/OPENAI_API_KEY") == "OPENAI_API_KEY"
    assert _environment_reference_name("os.environ/   ") is None
    assert _environment_reference_name("literal-key") is None
    assert _environment_reference_name(None) is None


def test_model_dump_accepts_models_and_mappings_and_rejects_others() -> None:
    class _WithDump:
        def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
            return {"model": "openai/x"}

    assert _model_dump(_WithDump()) == {"model": "openai/x"}
    assert _model_dump({"a": 1}) == {"a": 1}

    with pytest.raises(TypeError):
        _model_dump(object())


def _entry(
    name: str,
    model: str,
    *,
    api_key: Any = "os.environ/OPENAI_API_KEY",
    capabilities: dict[str, Any] | None = None,
) -> Any:
    params = {"model": model, "api_key": api_key, "api_base": "http://x", "seed": 1}

    class _Params:
        def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
            return dict(params)

    _Params.model = model  # type: ignore[attr-defined]

    return SimpleNamespace(
        model_name=name,
        litellm_params=_Params(),
        input_cost_per_million_tokens=None,
        output_cost_per_million_tokens=None,
        capabilities=capabilities,
    )


def test_registry_from_config_builds_providers_and_deployments() -> None:
    config = SimpleNamespace(model_list=[_entry("d1", "openai/gpt-4o-mini")])

    registry = registry_from_config(config)

    deployment = registry.get("d1")
    assert deployment.provider == "openai"
    assert deployment.api_key_env == "OPENAI_API_KEY"
    assert deployment.api_key is None
    assert [p.name for p in registry.list_providers()] == ["openai"]


def test_registry_from_config_keeps_literal_keys_and_metadata() -> None:
    config = SimpleNamespace(
        model_list=[_entry("d1", "openai/gpt-4o-mini", api_key="sk-literal-test")]
    )

    deployment = registry_from_config(config).get("d1")

    assert deployment.api_key == "sk-literal-test"
    assert deployment.api_key_env is None
    assert deployment.metadata == {"seed": 1}


def test_registry_from_config_derives_capability_declarations() -> None:
    from sabiroute.capabilities import Capability

    config = SimpleNamespace(
        model_list=[
            _entry(
                "d1",
                "openai/gpt-4o-mini",
                capabilities={
                    Capability.CHAT: True,
                    Capability.VISION: False,
                    Capability.JSON: "unknown",
                },
            )
        ]
    )

    deployment = registry_from_config(config).get("d1")

    assert deployment.capabilities.supported == frozenset({Capability.CHAT})
    assert deployment.capabilities.unsupported == frozenset({Capability.VISION})


def test_registry_from_config_rejects_a_model_without_a_provider() -> None:
    config = SimpleNamespace(model_list=[_entry("d1", "gpt-4o-mini")])

    with pytest.raises(ValueError) as excinfo:
        registry_from_config(config)

    assert "expected 'provider/model'" in str(excinfo.value)


def test_registry_from_config_rejects_an_empty_model() -> None:
    config = SimpleNamespace(model_list=[_entry("d1", "   ")])

    with pytest.raises(ValueError) as excinfo:
        registry_from_config(config)

    assert "has no LiteLLM model" in str(excinfo.value)
