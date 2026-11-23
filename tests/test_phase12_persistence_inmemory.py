"""Phase 12: persisted routing signals, in-process backend.

No external service is required. These tests prove the backend seam preserves
today's behaviour, that observations survive a simulated restart, that a store
failure degrades instead of raising, and that the scorer engages with a warmed
registry where a cold process still falls back to configured priority.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from conftest import make_config

from sabiroute.gateway import build_gateway_state
from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.monitoring.signals_store import InMemoryBackend, RedisBackend
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.scoring import DeterministicScorer, ScoringSettings


def _scorer() -> DeterministicScorer:
    return DeterministicScorer(
        ScoringSettings(minimum_samples=5, max_signal_age_seconds=3600)
    )


def _warm(
    health: HealthRegistry,
    latency: LatencyTracker,
    model: str,
    *,
    samples: int = 5,
    latency_ms: float = 10.0,
) -> None:
    for _ in range(samples):
        health.mark_success(model)
        latency.record(model, latency_ms)


class _FailingRedis:
    """Minimal client double whose every operation fails like an outage."""

    def scan_iter(self, **kwargs: object) -> object:
        raise ConnectionError("connection refused")

    def pipeline(self, transaction: bool = False) -> object:
        raise ConnectionError("connection refused")

    def close(self) -> None:
        return None


def test_default_registries_use_the_in_memory_backend() -> None:
    health = HealthRegistry()
    latency = LatencyTracker()

    assert isinstance(health.backend, InMemoryBackend)
    assert isinstance(latency.backend, InMemoryBackend)
    assert health.backend.degraded is False
    assert latency.backend.degraded is False


def test_in_memory_backend_preserves_existing_behaviour(monkeypatch) -> None:
    import sabiroute.routing.health as health_mod

    frozen = datetime(2026, 11, 23, 12, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(health_mod, "utc_now", lambda: frozen)

    plain_health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)
    backed_health = HealthRegistry(
        failure_threshold=3,
        cooldown_seconds=30,
        backend=InMemoryBackend(),
    )
    plain_latency = LatencyTracker()
    backed_latency = LatencyTracker(backend=InMemoryBackend())

    for registry in (plain_health, backed_health):
        registry.mark_failure("m")
        registry.mark_failure("m")
        registry.mark_success("m")
        registry.mark_failure("m")
    for tracker in (plain_latency, backed_latency):
        tracker.record("m", 12.0)
        tracker.record("m", 18.0)

    assert plain_health.snapshot() == backed_health.snapshot()
    assert plain_health.scoring_observation("m") == backed_health.scoring_observation("m")
    assert plain_health.scoring_observation("never-seen") == (0, 0, None)
    assert backed_health.scoring_observation("never-seen") == (0, 0, None)
    assert plain_latency.snapshot() == backed_latency.snapshot()
    assert plain_latency.average("m") == backed_latency.average("m")
    assert (
        plain_latency.scoring_observation("m")[:2]
        == backed_latency.scoring_observation("m")[:2]
    )


def test_observations_survive_a_simulated_restart() -> None:
    backend = InMemoryBackend()
    first_health = HealthRegistry(backend=backend)
    first_latency = LatencyTracker(backend=backend)
    _warm(first_health, first_latency, "fast", latency_ms=10.0)
    _warm(first_health, first_latency, "slow", latency_ms=100.0)

    # Simulated restart: brand-new registry objects over the same store.
    restarted_health = HealthRegistry(backend=backend)
    restarted_latency = LatencyTracker(backend=backend)

    assert restarted_health.scoring_observation("fast")[:2] == (5, 0)
    assert restarted_health.scoring_observation("slow")[:2] == (5, 0)
    assert restarted_latency.scoring_observation("fast")[:2] == (5, 10.0)
    assert restarted_latency.scoring_observation("slow")[:2] == (5, 100.0)
    assert restarted_latency.average("fast") == 10.0


def test_scorer_engages_after_restart_where_a_cold_process_cannot() -> None:
    backend = InMemoryBackend()
    first_health = HealthRegistry(backend=backend)
    first_latency = LatencyTracker(backend=backend)
    _warm(first_health, first_latency, "slow", latency_ms=100.0)
    _warm(first_health, first_latency, "fast", latency_ms=10.0)

    now = datetime.now(UTC)
    cold = _scorer().rank(
        ["slow", "fast"],
        reliability=HealthRegistry(),
        latency=LatencyTracker(),
        now=now,
    )
    assert cold.fallback_reason is not None
    assert cold.ranked_candidates == ("slow", "fast")

    restarted = _scorer().rank(
        ["slow", "fast"],
        reliability=HealthRegistry(backend=backend),
        latency=LatencyTracker(backend=backend),
        now=now,
    )
    assert restarted.fallback_reason is None
    assert restarted.ranked_candidates == ("fast", "slow")
    assert all(score.score is not None for score in restarted.candidate_scores)


def test_restart_does_not_restore_cooldown_state() -> None:
    backend = InMemoryBackend()
    first = HealthRegistry(backend=backend, failure_threshold=3, cooldown_seconds=30)
    for _ in range(3):
        first.mark_failure("m")
    assert first.available("m") is False

    restarted = HealthRegistry(
        backend=backend,
        failure_threshold=3,
        cooldown_seconds=30,
    )

    # Observations are inherited; the cooldown is deliberately not.
    assert restarted.scoring_observation("m")[:2] == (0, 3)
    assert restarted.available("m") is True
    assert restarted.deployments["m"].consecutive_failures == 0


def test_store_failure_degrades_to_in_memory_without_raising() -> None:
    backend = RedisBackend(_FailingRedis(), ttl_seconds=60)  # type: ignore[arg-type]
    health = HealthRegistry(backend=backend)
    latency = LatencyTracker(backend=backend)

    health.mark_success("m")
    health.mark_failure("m")
    latency.record("m", 12.0)

    assert backend.flush(timeout=5.0) is True
    assert backend.degraded is True
    assert backend.last_error is not None
    assert health.scoring_observation("m")[:2] == (1, 1)
    assert latency.scoring_observation("m")[:2] == (1, 12.0)
    assert backend.load_health() == {}
    assert backend.load_latency() == {}
    backend.close()


def test_gateway_uses_in_memory_backend_without_redis_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("REDIS_HOST", raising=False)

    state = build_gateway_state(config=make_config())

    assert isinstance(state.health.backend, InMemoryBackend)
    assert state.health.backend is state.latency.backend
