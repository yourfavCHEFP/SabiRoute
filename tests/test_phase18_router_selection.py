"""Phase 18: deterministic selection and its explanation contract.

These tests pin behaviour of ``Router`` that no existing test exercises:
the ``route()`` delegate, the ``RouteDecision`` labelling, the error
*precedence* between "nothing left" and "nothing healthy", the strategy
guard, capability-exclusion reason ordering, and attempted-list
normalisation. They assert the code as it currently is.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from conftest import make_config

from sabiroute.capabilities import Capability, DeploymentCapabilities
from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.providers.base import ProviderDeployment, ProviderInfo
from sabiroute.providers.registry import ProviderRegistry, registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.router import (
    NoHealthyDeploymentError,
    NoRemainingDeploymentError,
    Router,
)


def _router(
    *, health: HealthRegistry | None = None, latency: LatencyTracker | None = None
) -> Router:
    return Router(
        registry_from_config(make_config()),
        health=health or HealthRegistry(),
        latency=latency or LatencyTracker(),
    )


def test_route_delegates_and_labels_the_policy() -> None:
    decision = _router().route(["primary", "secondary"], policy_name="fast")

    assert decision.deployment == "primary"
    assert decision.provider == "openai"
    assert decision.reason == "policy:fast"
    assert decision.priority == 0
    assert decision.metadata == {
        "policy": "fast",
        "selection_reason": (
            "configured priority order "
            "(cold start, stale telemetry, or priority strategy)"
        ),
        "scoring_policy_version": "priority-v1",
        "ranked_candidates": ("primary", "secondary"),
    }
    assert decision.explanation is not None
    assert decision.explanation.selected_deployment == "primary"


def test_route_without_a_policy_name_labels_default() -> None:
    decision = _router().route(["primary"])

    assert decision.reason == "policy:default"
    assert decision.metadata["policy"] == "default"


def test_priority_strategy_explains_its_fallback() -> None:
    decision = _router().choose_deployment(["primary", "secondary"])
    explanation = decision.explanation

    assert explanation is not None
    assert explanation.scoring_policy_version == "priority-v1"
    assert explanation.scoring_fallback_reason == "priority_strategy"
    assert explanation.scoring_weights == {}
    assert explanation.candidate_scores == ()
    assert explanation.scoring_as_of is None
    assert explanation.ranked_candidates == ("primary", "secondary")
    assert explanation.eligible_deployments == ("primary", "secondary")


def test_measured_strategy_selects_lowest_latency_with_explanation() -> None:
    health = HealthRegistry()
    latency = LatencyTracker()
    for _ in range(5):
        health.mark_success("primary")
        health.mark_success("secondary")
    for _ in range(5):
        latency.record("primary", 300.0)
        latency.record("secondary", 100.0)

    as_of = datetime.now(UTC)
    decision = _router(health=health, latency=latency).choose_deployment(
        ["primary", "secondary"], strategy="measured", scoring_as_of=as_of
    )
    explanation = decision.explanation

    assert decision.deployment == "secondary"
    assert explanation is not None
    assert explanation.scoring_policy_version == "deterministic-v1"
    assert explanation.scoring_fallback_reason is None
    assert explanation.scoring_as_of == as_of
    assert explanation.ranked_candidates == ("secondary", "primary")
    assert explanation.selection_reason == (
        "highest measured deterministic score; configured order breaks ties"
    )
    scores = {score.deployment: score for score in explanation.candidate_scores}
    assert scores["secondary"].score == pytest.approx(1.0)
    assert scores["primary"].score == pytest.approx(0.7)


def test_measured_strategy_rejects_a_naive_as_of_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _router().choose_deployment(
            ["primary"],
            strategy="measured",
            scoring_as_of=datetime(2026, 1, 1),  # noqa: DTZ001 - naive on purpose
        )


def test_unsupported_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported routing strategy: bogus"):
        _router().choose_deployment(["primary"], strategy="bogus")


def test_exhausted_attempts_outrank_health_in_error_precedence() -> None:
    # Both candidates capable and healthy: with every one attempted the
    # router reports "nothing left", not "nothing healthy".
    with pytest.raises(NoRemainingDeploymentError):
        _router().choose_deployment(
            ["primary", "secondary"], attempted=["primary", "secondary"]
        )


def test_attempted_but_unhealthy_remaining_reports_no_healthy() -> None:
    health = HealthRegistry()
    routing = _router(health=health)
    for _ in range(health.failure_threshold):
        health.mark_failure("secondary")

    # primary is attempted; secondary is remaining but unhealthy, so the
    # remaining set is non-empty and availability is the failing check.
    with pytest.raises(NoHealthyDeploymentError):
        routing.choose_deployment(["primary", "secondary"], attempted=["primary"])


def test_attempted_entries_are_normalised() -> None:
    routing = _router()

    evaluation = routing.evaluate_candidates(
        ["primary", "secondary"],
        attempted=[" primary ", "", "   ", "not-a-candidate"],
    )

    assert evaluation.remaining_deployments == ("secondary",)
    assert evaluation.available_deployments == ("secondary",)


def test_candidate_order_is_preserved_and_duplicates_collapsed() -> None:
    evaluation = _router().evaluate_candidates(["secondary", "primary", "secondary"])

    assert evaluation.candidate_deployments == ("secondary", "primary")
    assert evaluation.capability_eligible_deployments == ("secondary", "primary")


def test_capability_exclusion_lists_unsupported_before_unknown() -> None:
    deployment = ProviderDeployment(
        name="p1",
        provider="prov",
        model="prov/model",
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT}),
            unsupported=frozenset({Capability.VISION}),
        ),
    )
    registry = ProviderRegistry(
        providers=[ProviderInfo(name="prov", display_name="Prov")],
        deployments=[deployment],
    )
    routing = Router(registry, health=HealthRegistry())

    evaluation = routing.evaluate_candidates(
        ["p1"],
        required_capabilities={Capability.CHAT, Capability.REASONING, Capability.VISION},
    )

    # ``unsupported`` entries are emitted first, then ``unknown`` entries,
    # each group ordered by capability value.
    assert evaluation.capability_excluded_deployments["p1"] == (
        "unsupported:vision",
        "unknown:reasoning",
    )
    assert evaluation.capability_eligible_deployments == ()
