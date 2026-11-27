"""Validation coverage for :mod:`sabiroute.config.models`.

Only the declaration-shape guard and the explicit policy-version path are
unreached elsewhere: pydantic does not validate defaults, so the version
validator only runs when a configuration actually names a version.
"""
from __future__ import annotations

import pytest

from sabiroute.config.models import DeploymentConfig, RoutingScoringConfig


def test_capabilities_must_be_a_mapping() -> None:
    with pytest.raises(ValueError, match="must map each capability"):
        DeploymentConfig(
            model_name="primary",
            litellm_params={"model": "gpt-4o-mini"},
            capabilities=["chat"],
        )


def test_an_explicit_null_capability_map_passes_through() -> None:
    config = DeploymentConfig(
        model_name="primary",
        litellm_params={"model": "gpt-4o-mini"},
        capabilities=None,
    )

    assert config.capabilities is None


def test_explicit_policy_version_is_kept_verbatim() -> None:
    config = RoutingScoringConfig(policy_version="deterministic-v2")

    assert config.policy_version == "deterministic-v2"


def test_blank_policy_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="policy_version must not be empty"):
        RoutingScoringConfig(policy_version="   ")
