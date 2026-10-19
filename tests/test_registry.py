from __future__ import annotations

import pytest
from conftest import make_config

from sabiroute.providers.base import MissingCredentialError
from sabiroute.providers.registry import registry_from_config


def test_env_references_kept_as_names():
    registry = registry_from_config(make_config())

    primary = registry.get("primary")
    assert primary.api_key_env == "OPENAI_API_KEY"
    assert primary.api_key is None

    literal = registry.get("literal-key")
    assert literal.api_key_env is None
    assert literal.api_key == "sk-literal-test"


def test_as_litellm_params_resolves_real_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-key")

    registry = registry_from_config(make_config())
    params = registry.get("primary").as_litellm_params()

    assert params["api_key"] == "sk-real-key"
    assert params["model"] == "openai/gpt-4o-mini"


def test_as_litellm_params_missing_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    registry = registry_from_config(make_config())

    with pytest.raises(MissingCredentialError):
        registry.get("primary").as_litellm_params()


def test_metadata_env_references_resolved(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_API_KEY", "cf-key")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "cf-account")

    registry = registry_from_config(make_config())
    params = registry.get("cloudy").as_litellm_params()

    assert params["api_key"] == "cf-key"
    assert params["account_id"] == "cf-account"


def test_literal_key_passthrough():
    registry = registry_from_config(make_config())
    params = registry.get("literal-key").as_litellm_params()

    assert params["api_key"] == "sk-literal-test"
