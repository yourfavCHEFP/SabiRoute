from __future__ import annotations

from datetime import timedelta

from sabiroute.routing.health import HealthRegistry, utc_now


def _trip(health: HealthRegistry, name: str = "m") -> None:
    for _ in range(health.failure_threshold):
        health.mark_failure(name)


def test_failures_trip_cooldown():
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    _trip(health)

    state = health.deployments["m"]
    assert state.healthy is False
    assert state.cooldown_until is not None
    assert health.available("m") is False


def test_half_open_reset_after_cooldown_expiry():
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    _trip(health)

    state = health.deployments["m"]
    state.cooldown_until = utc_now() - timedelta(seconds=1)

    assert health.available("m") is True
    assert state.healthy is True
    assert state.consecutive_failures == 0
    assert state.cooldown_until is None


def test_single_failure_after_recovery_does_not_retrip():
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    _trip(health)

    state = health.deployments["m"]
    state.cooldown_until = utc_now() - timedelta(seconds=1)
    assert health.available("m") is True

    health.mark_failure("m")

    assert health.deployments["m"].healthy is True
    assert health.available("m") is True


def test_mark_success_resets_failure_state():
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    health.mark_failure("m")
    health.mark_failure("m")
    health.mark_success("m")

    state = health.deployments["m"]
    assert state.healthy is True
    assert state.consecutive_failures == 0
    assert state.total_failures == 2
    assert state.total_successes == 1


def test_snapshot_is_read_only():
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    _trip(health)

    state = health.deployments["m"]
    state.cooldown_until = utc_now() - timedelta(seconds=1)

    snapshot = health.snapshot()

    assert snapshot["m"]["available"] is True
    # snapshot must not perform the half-open reset
    assert state.consecutive_failures == 3
    assert state.healthy is False
