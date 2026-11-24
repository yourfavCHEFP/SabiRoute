"""Boundary coverage for :mod:`sabiroute.providers.base`.

Pins the two behaviours the LiteLLM call boundary depends on: a value that is
not an ``os.environ/`` reference passes through untouched, and a reference is
resolved when the call is built rather than when the deployment is described.
``api_base`` is covered separately from ``api_key`` because a deployment may
carry one without the other, and a missing variable must fail loudly instead of
dispatching with an empty credential.
"""
from __future__ import annotations

from typing import Any

import pytest

from sabiroute.providers.base import (
    MissingCredentialError,
    ProviderDeployment,
    _resolve_env_reference,
)


@pytest.mark.parametrize("value", ["plain-value", None, 7])
def test_values_that_are_not_environment_references_pass_through(value: Any) -> None:
    resolved = _resolve_env_reference(value)

    assert resolved == value


def test_missing_environment_variable_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_PROVIDER_KEY", raising=False)

    with pytest.raises(MissingCredentialError, match="TEST_PROVIDER_KEY"):
        _resolve_env_reference("os.environ/TEST_PROVIDER_KEY")


def test_api_base_reference_is_resolved_at_the_call_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_PROVIDER_BASE", "https://gateway.internal/v1")
    deployment = ProviderDeployment(
        name="a",
        provider="openai",
        model="gpt-x",
        api_base="os.environ/TEST_PROVIDER_BASE",
    )

    params = deployment.as_litellm_params()

    assert params["api_base"] == "https://gateway.internal/v1"
    assert params["api_base"] != deployment.api_base
    assert params["model"] == "gpt-x"
    assert "api_key" not in params


def test_literal_api_base_is_passed_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_PROVIDER_BASE", raising=False)
    deployment = ProviderDeployment(
        name="a",
        provider="openai",
        model="gpt-x",
        api_base="https://literal.example/v1",
    )

    assert deployment.as_litellm_params()["api_base"] == "https://literal.example/v1"
