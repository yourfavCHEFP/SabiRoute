"""Behavioural tests for :mod:`sabiroute.config.validation`."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from sabiroute.config.validation import ConfigValidationError, validate_config


def _deployment(
    name: str = "d1",
    model: str = "openai/gpt-4o-mini",
    api_key: Any = "os.environ/OPENAI_API_KEY",
) -> Any:
    params = SimpleNamespace(model=model, api_key=api_key)
    return SimpleNamespace(model_name=name, litellm_params=params)


def _config(deployments: list[Any] | None = None, timeout: float = 30.0) -> Any:
    return SimpleNamespace(
        model_list=[_deployment()] if deployments is None else deployments,
        litellm_settings=SimpleNamespace(request_timeout=timeout),
    )


def test_empty_model_list_is_rejected() -> None:
    with pytest.raises(ConfigValidationError) as excinfo:
        validate_config(_config(deployments=[]))

    assert "at least one deployment" in str(excinfo.value)


def test_blank_model_name_is_rejected() -> None:
    with pytest.raises(ConfigValidationError) as excinfo:
        validate_config(_config(deployments=[_deployment(name="  ")]))

    assert "non-empty model_name" in str(excinfo.value)


def test_duplicate_model_name_is_rejected() -> None:
    with pytest.raises(ConfigValidationError) as excinfo:
        validate_config(_config(deployments=[_deployment(), _deployment()]))

    assert "Duplicate model_name" in str(excinfo.value)


def test_empty_litellm_model_is_rejected() -> None:
    with pytest.raises(ConfigValidationError) as excinfo:
        validate_config(_config(deployments=[_deployment(model="  ")]))

    assert "empty LiteLLM model" in str(excinfo.value)


def test_environment_reference_passes_through() -> None:
    config = _config()

    assert validate_config(config) is config


def test_malformed_environment_reference_is_rejected() -> None:
    for bad in ("os.environ/lower-case", "os.environ/1LEADING", "os.environ/"):
        with pytest.raises(ConfigValidationError) as excinfo:
            validate_config(_config(deployments=[_deployment(api_key=bad)]))
        assert "Invalid environment reference" in str(excinfo.value)


def test_literal_api_key_is_rejected_without_echoing_it() -> None:
    secret = "sk-live-do-not-ship"

    with pytest.raises(ConfigValidationError) as excinfo:
        validate_config(_config(deployments=[_deployment(api_key=secret)]))

    message = str(excinfo.value)
    assert "embeds a literal" in message
    assert secret not in message


def test_marked_test_credentials_are_accepted() -> None:
    for credential in ("sk-test-abc", "sk-test_abc", "sk-literal-test"):
        config = _config(deployments=[_deployment(api_key=credential)])
        assert validate_config(config) is config


def test_padded_credential_is_not_treated_as_a_test_credential() -> None:
    with pytest.raises(ConfigValidationError):
        validate_config(_config(deployments=[_deployment(api_key=" sk-test-abc ")]))


def test_none_api_key_is_permitted() -> None:
    config = _config(deployments=[_deployment(api_key=None)])

    assert validate_config(config) is config


def test_non_positive_request_timeout_is_rejected() -> None:
    for timeout in (0, -1.5):
        with pytest.raises(ConfigValidationError) as excinfo:
            validate_config(_config(timeout=timeout))
        assert "request_timeout" in str(excinfo.value)
