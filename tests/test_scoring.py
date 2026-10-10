from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from conftest import make_config

from sabiroute.capabilities import Capability, DeploymentCapabilities
from sabiroute.config.models import SabiRouteConfig
from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.router import NoHealthyDeploymentError, Router
from sabiroute.routing.scoring import DeterministicScorer, ScoringSettings
from sabiroute.security.keys import RequestUsageEvent, issue_api_key
from sabiroute.security.store import PostgresApiKeyStore


class FixedSignals:
    def __init__(self, observations):
        self.observations = observations
        self.state_scope_id = str(uuid4())

    def scoring_observation(self, deployment, as_of=None):
        return self.observations.get(deployment, (0, 0, None))


class FixedLatencies:
    def __init__(self, observations):
        self.observations = observations
        self.state_scope_id = str(uuid4())

    def scoring_observation(self, deployment, as_of=None):
        return self.observations.get(deployment, (0, None, None))


def test_tracker_observations_after_as_of_are_excluded_from_scores() -> None:
    as_of = datetime(2026, 1, 1, tzinfo=UTC)
    health = HealthRegistry()
    latency = LatencyTracker()
    health.mark_success("a")
    latency.record("a", 12.0)
    scorer, _ = _scorer(minimum_samples=1)

    ranking = scorer.rank(["a"], reliability=health, latency=latency, now=as_of)

    score = ranking.candidate_scores[0]
    assert score.reliability_samples == 0
    assert score.latency_samples == 0
    assert score.latest_reliability_observation is None
    assert score.latest_latency_observation is None
    assert ranking.fallback_reason is not None


def test_router_passes_and_exposes_the_identical_scoring_cutoff() -> None:
    registry = registry_from_config(make_config())
    health = HealthRegistry()
    latency = LatencyTracker()
    routing = Router(registry, health=health, latency=latency)
    observed: dict[str, datetime] = {}
    original_rank = routing.scorer.rank

    def capture_rank(candidates, **kwargs):
        observed["scorer"] = kwargs["now"]
        return original_rank(candidates, **kwargs)

    routing.scorer.rank = capture_rank  # type: ignore[method-assign]
    decision = routing.choose_deployment(["primary"], strategy="measured")

    assert decision.explanation is not None
    assert decision.explanation.scoring_as_of == observed["scorer"]


def _scorer(**overrides):
    settings = ScoringSettings(**overrides)
    return DeterministicScorer(settings), settings


def _fresh_observations(now: datetime, latency_by_name: dict[str, float]):
    reliability = FixedSignals(
        {
            name: (successes, failures, now)
            for name, successes, failures in ((name, 5, 0) for name in latency_by_name)
        }
    )
    latency = FixedLatencies({name: (5, value, now) for name, value in latency_by_name.items()})
    return reliability, latency


def test_scoring_is_deterministic_and_preserves_priority_for_ties() -> None:
    now = datetime.now(UTC)
    reliability, latency = _fresh_observations(now, {"a": 10.0, "b": 10.0})
    scorer, _ = _scorer(minimum_samples=5)

    first = scorer.rank(["b", "a"], reliability=reliability, latency=latency, now=now)
    second = scorer.rank(["b", "a"], reliability=reliability, latency=latency, now=now)

    assert first == second
    assert first.ranked_candidates == ("b", "a")
    assert first.fallback_reason is None
    assert all(item.score == 1.0 for item in first.candidate_scores)


def test_reliability_weight_can_improve_a_candidate_ranking() -> None:
    now = datetime.now(UTC)
    reliability = FixedSignals({"reliable": (10, 0, now), "fast": (8, 2, now)})
    latency = FixedLatencies({"reliable": (10, 100.0, now), "fast": (10, 10.0, now)})
    scorer, _ = _scorer(
        reliability_weight=1.0,
        latency_weight=0.0,
        minimum_samples=5,
    )

    ranking = scorer.rank(["fast", "reliable"], reliability=reliability, latency=latency, now=now)

    assert ranking.ranked_candidates == ("reliable", "fast")


def test_latency_normalization_and_weight_are_explainable() -> None:
    now = datetime.now(UTC)
    reliability, latency = _fresh_observations(now, {"slow": 100.0, "quick": 20.0})
    scorer, _ = _scorer(
        reliability_weight=0.0,
        latency_weight=1.0,
        minimum_samples=5,
    )

    ranking = scorer.rank(["slow", "quick"], reliability=reliability, latency=latency, now=now)
    scores = {item.deployment: item for item in ranking.candidate_scores}

    assert ranking.ranked_candidates == ("quick", "slow")
    assert scores["quick"].latency_normalized == 1.0
    assert scores["slow"].latency_normalized == 0.0


def test_insufficient_or_stale_telemetry_falls_back_to_priority() -> None:
    now = datetime.now(UTC)
    old = now - timedelta(hours=2)
    reliability = FixedSignals({"a": (20, 0, old), "b": (20, 0, old)})
    latency = FixedLatencies({"a": (20, 12.0, old), "b": (20, 8.0, old)})
    scorer, _ = _scorer(max_signal_age_seconds=3600, minimum_samples=5)

    ranking = scorer.rank(["a", "b"], reliability=reliability, latency=latency, now=now)

    assert ranking.ranked_candidates == ("a", "b")
    assert ranking.fallback_reason == "stale_or_missing_telemetry"
    assert all(item.score is None for item in ranking.candidate_scores)


def test_each_scoring_signal_must_be_fresh() -> None:
    now = datetime.now(UTC)
    old = now - timedelta(hours=2)
    reliability = FixedSignals({"a": (20, 0, now), "b": (20, 0, now)})
    latency = FixedLatencies({"a": (20, 12.0, old), "b": (20, 8.0, now)})
    scorer, _ = _scorer(max_signal_age_seconds=3600, minimum_samples=5)

    ranking = scorer.rank(["a", "b"], reliability=reliability, latency=latency, now=now)

    assert ranking.ranked_candidates == ("a", "b")
    assert ranking.fallback_reason == "stale_or_missing_telemetry"


def test_missing_telemetry_does_not_crash_or_penalize_cold_start() -> None:
    now = datetime.now(UTC)
    scorer, _ = _scorer()

    ranking = scorer.rank(
        ["new", "known"],
        reliability=FixedSignals({}),
        latency=FixedLatencies({}),
        now=now,
    )

    assert ranking.ranked_candidates == ("new", "known")
    assert ranking.fallback_reason is not None
    assert ranking.candidate_scores[0].score is None


def test_weights_must_be_valid_and_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        ScoringSettings(reliability_weight=0.5, latency_weight=0.4)
    with pytest.raises(ValueError, match="negative"):
        ScoringSettings(reliability_weight=1.1, latency_weight=-0.1)


def test_scoring_weights_are_validated_in_project_configuration() -> None:
    raw = make_config().model_dump(mode="python")
    raw["routing_scoring"]["reliability_weight"] = 0.6
    raw["routing_scoring"]["latency_weight"] = 0.6

    with pytest.raises(ValueError, match="sum to 1"):
        SabiRouteConfig.from_mapping(raw)


def test_router_scores_only_healthy_capable_candidates() -> None:
    registry = registry_from_config(make_config())
    registry._deployments["primary"] = replace(
        registry.get("primary"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT}),
            unsupported=frozenset({Capability.CODING}),
        ),
    )
    registry._deployments["secondary"] = replace(
        registry.get("secondary"),
        capabilities=DeploymentCapabilities(
            supported=frozenset({Capability.CHAT, Capability.CODING}),
        ),
    )
    health = HealthRegistry()
    latency = LatencyTracker()
    for _ in range(5):
        health.mark_success("secondary")
        latency.record("secondary", 20)
    for _ in range(health.failure_threshold):
        health.mark_failure("cloudy")
    routing = Router(registry, health=health, latency=latency)

    decision = routing.choose_deployment(
        ["primary", "secondary", "cloudy"],
        required_capabilities={Capability.CHAT, Capability.CODING},
        strategy="measured",
    )

    assert decision.deployment == "secondary"
    assert decision.explanation is not None
    assert decision.explanation.eligible_deployments == ("secondary",)
    assert tuple(score.deployment for score in decision.explanation.candidate_scores) == (
        "secondary",
    )
    assert decision.explanation.scoring_policy_version == "deterministic-v1"


def test_measured_fallback_never_reintroduces_unhealthy_candidate() -> None:
    registry = registry_from_config(make_config())
    health = HealthRegistry()
    for _ in range(health.failure_threshold):
        health.mark_failure("primary")
    routing = Router(registry, health=health)

    with pytest.raises(NoHealthyDeploymentError):
        routing.choose_deployment(
            ["primary"],
            strategy="measured",
        )


def test_routing_decision_telemetry_persists_across_store_restart(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'routing-decisions.sqlite'}"
    store = PostgresApiKeyStore(database_url)
    record, _ = issue_api_key(store, project_id="project-test", name="test")
    request_id = "00000000-0000-0000-0000-000000000012"
    event = RequestUsageEvent(
        request_id=request_id,
        key_id=record.key_id,
        project_id=record.project_id,
        created_at=datetime.now(UTC),
        requested_alias="fast",
        pre_routing_features=(
            {
                "feature_schema_version": "1.0",
                "logical_request_id": request_id,
                "attempt_number": 1,
                "decision_timestamp": datetime.now(UTC).isoformat(),
                "request_type": "chat",
                "requested_alias": "fast",
                "routing_policy_id": "fast",
                "candidate_deployments": ["primary", "secondary"],
                "capability_eligible_deployments": ["primary", "secondary"],
                "health_eligible_deployments": ["secondary"],
                "required_capabilities": ["chat"],
                "streaming": False,
                "tool_use": False,
                "response_format_category": "none",
                "multimodal": False,
                "estimated_input_tokens": 12,
                "request_size_bytes": 40,
                "requested_max_output_tokens": 20,
                "context_size_requirement": None,
                "routing_strategy": "measured",
                "routing_strategy_version": "deterministic-v1",
                "deterministic_score_context": [],
                "selection_propensity": None,
                "experiment_id": None,
            },
        ),
    )
    store.create_usage_event(event)
    decision = {
        "logical_request_id": request_id,
        "request_type": "chat",
        "candidate_deployments": ["primary", "secondary"],
        "eligible_deployments": ["secondary"],
        "selected_deployment": "secondary",
        "scoring_policy_version": "deterministic-v1",
        "candidate_scores": [{"deployment": "secondary", "score": 0.9}],
        "decision_timestamp": datetime.now(UTC).isoformat(),
        "fallback_attempt": 1,
        "outcome": "success",
        "latency_ms": 18.2,
        "usage": {"total_tokens": 12},
        "actual_cost_usd": None,
    }
    finalized = replace(
        event,
        final_deployment="secondary",
        final_status=200,
        routing_decisions=(decision,),
    )
    assert store.finalize_usage_event(finalized)
    store.close()

    reopened = PostgresApiKeyStore(database_url)
    rows, total = reopened.list_usage_events(record.key_id, limit=10, offset=0)
    reopened.close()

    assert total == 1
    assert rows[0].routing_decisions == (decision,)
    assert rows[0].feature_schema_version == "1.0"
    assert rows[0].pre_routing_features[0]["logical_request_id"] == request_id
