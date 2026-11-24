"""Guard-path coverage for the routing layer.

Health availability without a cooldown, an observation for a deployment that
was never registered, the strategy-name rejection, and the ``route`` alias are
the four branches that the behavioural routing tests never take.
"""
from __future__ import annotations

import pytest
from conftest import make_config

from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.health import DeploymentHealth, HealthRegistry
from sabiroute.routing.router import Router


def _router() -> Router:
    return Router(registry_from_config(make_config()), health=HealthRegistry())


def test_unhealthy_deployment_without_a_cooldown_is_unavailable() -> None:
    state = DeploymentHealth(model_name="primary", healthy=False, cooldown_until=None)

    assert state.is_available() is False


def test_scoring_observation_for_an_unknown_deployment_is_empty() -> None:
    assert HealthRegistry().scoring_observation("never-registered") == (0, 0, None)


def test_unsupported_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported routing strategy"):
        _router().choose_deployment(["primary"], strategy="vibes")


def test_route_delegates_to_choose_deployment() -> None:
    decision = _router().route(["primary"])

    assert decision.deployment == "primary"
