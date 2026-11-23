"""Phase 18: health-as-telemetry and deterministic scoring edge cases.

``HealthRegistry`` cooldown transitions already have coverage. These tests
cover the parts that do not: ``HealthRegistry.scoring_observation`` (the
reliability source that feeds measured routing), the read-only
``DeploymentHealth.is_available`` contract, the snapshot key set, and the
scoring settings / ranking edge cases.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.routing.health import DeploymentHealth, HealthRegistry
from sabiroute.routing.scoring import DeterministicScorer, ScoringSettings


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def test_scoring_observation_of_an_unknown_deployment_is_empty() -> None:
    assert HealthRegistry().scoring_observation("never-seen") == (0, 0, None)


def test_scoring_observation_counts_outcomes_and_reports_latest(monkeypatch) -> None:
    import sabiroute.routing.health as health_mod

    t0 = datetime(2026, 10, 11, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(seconds=10)
    clock = _Clock(t0)
    monkeypatch.setattr(health_mod, "utc_now", clock)
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    health.mark_success("m")
    clock.now = t1
    health.mark_failure("m")

    assert health.scoring_observation("m") == (1, 1, t1)
    # As-of is an inclusive cutoff over the observation timestamps.
    assert health.scoring_observation("m", as_of=t0) == (1, 0, t0)
    assert health.scoring_observation("m", as_of=t1) == (1, 1, t1)
    assert health.scoring_observation("m", as_of=t0 - timedelta(seconds=1)) == (
        0,
        0,
        None,
    )


def test_is_available_false_without_a_deadline_is_permanent_removal() -> None:
    # ``cooldown_until is None`` while unhealthy means removed, not
    # "no cooldown": there is no timestamp at which it becomes available.
    removed = DeploymentHealth(model_name="gone", healthy=False, cooldown_until=None)

    assert removed.is_available() is False


def test_is_available_does_not_reset_an_expired_cooldown() -> None:
    expired = DeploymentHealth(
        model_name="expired",
        healthy=False,
        consecutive_failures=3,
        cooldown_until=datetime.now(UTC) - timedelta(seconds=5),
    )
    deadline = expired.cooldown_until

    # Advisory read: reports availability but must not perform the
    # half-open reset that ``HealthRegistry.available`` performs.
    assert expired.is_available() is True
    assert expired.healthy is False
    assert expired.consecutive_failures == 3
    assert expired.cooldown_until == deadline


def test_is_available_healthy_without_cooldown() -> None:
    assert DeploymentHealth(model_name="ok").is_available() is True


def test_snapshot_exposes_the_documented_keys() -> None:
    health = HealthRegistry()
    health.mark_success("m")

    assert set(health.snapshot()["m"]) == {
        "healthy",
        "available",
        "consecutive_failures",
        "total_successes",
        "total_failures",
        "last_success",
        "last_failure",
        "cooldown_until",
    }


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"policy_version": "  "}, "policy version must not be empty"),
        ({"reliability_weight": -0.1, "latency_weight": 1.1}, "cannot be negative"),
        ({"reliability_weight": 0.5, "latency_weight": 0.4}, "must sum to 1"),
        ({"minimum_samples": 0}, "minimum_samples must be positive"),
        ({"max_signal_age_seconds": 0}, "max_signal_age_seconds must be positive"),
        (
            {"reliability_weight": float("nan"), "latency_weight": float("nan")},
            "must be finite",
        ),
    ],
)
def test_scoring_settings_rejects_invalid_values(
    kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        ScoringSettings(**kwargs)  # type: ignore[arg-type]


def test_rank_of_no_candidates_is_empty() -> None:
    result = DeterministicScorer().rank(
        [], reliability=HealthRegistry(), latency=LatencyTracker()
    )

    assert result.ranked_candidates == ()
    assert result.candidate_scores == ()
    assert result.fallback_reason is None
    assert result.policy_version == "deterministic-v1"


def test_rank_rejects_a_naive_as_of() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        DeterministicScorer().rank(
            ["a"],
            reliability=HealthRegistry(),
            latency=LatencyTracker(),
            now=datetime(2026, 1, 1),  # noqa: DTZ001 - naive on purpose
        )


def test_rank_of_a_single_candidate_normalises_latency_to_one() -> None:
    health = HealthRegistry()
    latency = LatencyTracker()
    for _ in range(5):
        health.mark_success("a")
        latency.record("a", 250.0)

    result = DeterministicScorer().rank(
        ["a"], reliability=health, latency=latency, now=datetime.now(UTC)
    )

    assert result.fallback_reason is None
    only = result.candidate_scores[0]
    # A zero-width latency range normalises to 1.0 rather than dividing by
    # zero, so a lone candidate scores its own success rate weighted in.
    assert only.latency_normalized == 1.0
    assert only.score == pytest.approx(1.0)


def test_rank_uses_fresh_reliability_and_latency_together() -> None:
    health = HealthRegistry()
    latency = LatencyTracker()
    for _ in range(5):
        health.mark_success("a")
        latency.record("a", 100.0)
    for _ in range(4):
        health.mark_success("b")
    health.mark_failure("b")
    for _ in range(5):
        latency.record("b", 200.0)

    result = DeterministicScorer().rank(
        ["a", "b"], reliability=health, latency=latency, now=datetime.now(UTC)
    )

    assert result.fallback_reason is None
    assert result.ranked_candidates == ("a", "b")
    scores = {score.deployment: score for score in result.candidate_scores}
    assert scores["a"].success_rate == 1.0
    assert scores["a"].latency_normalized == 1.0
    assert scores["a"].score == pytest.approx(1.0)
    assert scores["b"].success_rate == 0.8
    assert scores["b"].latency_normalized == 0.0
    # 0.7 * 0.8 + 0.3 * 0.0
    assert scores["b"].score == pytest.approx(0.56)
    assert scores["a"].reliability_samples == 5
    assert scores["b"].latency_samples == 5


def test_rank_treats_observations_after_the_cutoff_as_absent() -> None:
    health = HealthRegistry()
    latency = LatencyTracker()
    for _ in range(5):
        health.mark_success("a")
        latency.record("a", 100.0)

    # Cutoff before any observation exists: the signals must be treated as
    # missing, not as the newest values.
    result = DeterministicScorer().rank(
        ["a"],
        reliability=health,
        latency=latency,
        now=datetime(2020, 1, 1, tzinfo=UTC),
    )

    assert result.fallback_reason is not None
    assert "insufficient_reliability_samples" in result.fallback_reason
    assert "insufficient_latency_samples" in result.fallback_reason
    assert "stale_or_missing_telemetry" in result.fallback_reason
    assert result.ranked_candidates == ("a",)
    assert result.candidate_scores[0].score is None
