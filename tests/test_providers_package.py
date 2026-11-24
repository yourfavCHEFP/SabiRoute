"""Behavioural tests for the lazy attribute surface of :mod:`sabiroute.providers`."""
from __future__ import annotations

import pytest

import sabiroute.providers as providers


def test_client_class_is_resolved_lazily() -> None:
    from sabiroute.providers.litellm_client import LiteLLMClient

    assert providers.LiteLLMClient is LiteLLMClient


def test_client_error_is_resolved_lazily() -> None:
    from sabiroute.providers.litellm_client import LiteLLMClientError

    assert providers.LiteLLMClientError is LiteLLMClientError


def test_unknown_attribute_raises_attribute_error() -> None:
    with pytest.raises(AttributeError) as excinfo:
        providers.DoesNotExist  # noqa: B018

    assert "has no attribute" in str(excinfo.value)
