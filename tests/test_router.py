from __future__ import annotations

import pytest
from conftest import make_config

from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.router import Router


@pytest.fixture
def router():
    registry = registry_from_config(make_config())
    health = HealthRegistry()
    return Router(registry, health=health), health


def test_first_candidate_chosen(router):
    routing, _ = router

    decision = routing.choose_deployment(["primary", "secondary"])

    assert decision.deployment == "primary"
    assert decision.provider == "openai"


def test_unhealthy_candidate_skipped(router):
    routing, health = router

    for _ in range(3):
        health.mark_failure("primary")

    decision = routing.choose_deployment(["primary", "secondary"])

    assert decision.deployment == "secondary"


def test_attempted_candidates_excluded(router):
    routing, _ = router

    decision = routing.choose_deployment(
        ["primary", "secondary"],
        attempted=["primary"],
    )

    assert decision.deployment == "secondary"


def test_last_resort_uses_unhealthy_candidates(router):
    routing, health = router

    for name in ("primary", "secondary"):
        for _ in range(3):
            health.mark_failure(name)

    decision = routing.choose_deployment(["primary", "secondary"])

    assert decision.deployment == "primary"


def test_unknown_candidate_rejected(router):
    routing, _ = router

    with pytest.raises(KeyError):
        routing.choose_deployment(["does-not-exist"])


def test_empty_candidates_rejected(router):
    routing, _ = router

    with pytest.raises(ValueError):
        routing.choose_deployment([])
