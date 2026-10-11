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


def test_unwired_active_health_checker_is_absent():
    import importlib.util

    import sabiroute.providers as providers

    assert importlib.util.find_spec("sabiroute.providers.healthcheck") is None
    assert not hasattr(providers, "ProviderHealthChecker")


class _Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


def test_cooldown_starts_at_failure_time_and_ends_at_boundary(monkeypatch):
    from datetime import UTC, datetime

    import sabiroute.routing.health as health_mod

    t0 = datetime(2026, 10, 11, 12, 0, 0, tzinfo=UTC)
    clock = _Clock(t0)
    monkeypatch.setattr(health_mod, "utc_now", clock)
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    for _ in range(3):
        health.mark_failure("m")
    assert health.deployments["m"].cooldown_until == t0 + timedelta(seconds=30)
    assert health.available("m") is False

    # One microsecond before expiry: still cooling down.
    clock.now = t0 + timedelta(seconds=30) - timedelta(microseconds=1)
    assert health.available("m") is False
    # Exactly at expiry: half-open reset grants one fresh attempt.
    clock.now = t0 + timedelta(seconds=30)
    assert health.available("m") is True
    assert health.deployments["m"].healthy is True
    assert health.deployments["m"].consecutive_failures == 0


def test_wall_clock_jump_forward_expires_cooldown(monkeypatch):
    # Documents the wall-clock contract: cooldowns follow datetime.now(UTC),
    # so a forward system-clock jump ends them early. Monotonic timing is
    # deliberately not used because observation timestamps are persisted.
    from datetime import UTC, datetime

    import sabiroute.routing.health as health_mod

    t0 = datetime(2026, 10, 11, 12, 0, 0, tzinfo=UTC)
    clock = _Clock(t0)
    monkeypatch.setattr(health_mod, "utc_now", clock)
    health = HealthRegistry(failure_threshold=1, cooldown_seconds=3600)

    health.mark_failure("m")
    assert health.available("m") is False
    clock.now = t0 + timedelta(hours=2)
    assert health.available("m") is True


def test_concurrent_marks_trip_cooldown_without_errors():
    import threading

    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)
    errors: list[BaseException] = []

    def mark_many():
        try:
            for _ in range(10):
                health.mark_failure("m")
                assert isinstance(health.available("m"), bool)
        except BaseException as exc:  # noqa: BLE001 - must not escape threads
            errors.append(exc)

    threads = [threading.Thread(target=mark_many) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert errors == []
    assert health.deployments["m"].healthy is False
    assert health.available("m") is False
