"""Phase 12: persisted routing signals against a disposable Redis.

Opt-in only, via ``SABIROUTE_TEST_REDIS_URL``, following
``tests/test_rate_limit_redis.py``:

- unset -> every test skips cleanly (the default suite stays Redis-free);
- set -> tests run against that instance;
- unreachable -> tests fail clearly (never silent-pass);
- non-loopback host -> the fixture refuses (pytest.fail, never runs).

Safety: loopback-only targets, a unique key prefix per test, and per-test
cleanup that deletes only keys under that prefix (never FLUSHDB). No
credentials are written to code or output.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import pytest
from conftest import make_config
from redis import Redis

from sabiroute.gateway import build_gateway_state
from sabiroute.monitoring.latency import LatencyTracker
from sabiroute.monitoring.signals_store import RedisBackend
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.scoring import DeterministicScorer, ScoringSettings

TEST_URL_ENV = "SABIROUTE_TEST_REDIS_URL"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

pytestmark = pytest.mark.skipif(
    not os.environ.get(TEST_URL_ENV),
    reason=f"{TEST_URL_ENV} is not set; Redis persistence tests skipped",
)


def _checked_url() -> str:
    url = os.environ[TEST_URL_ENV]
    host = (urlparse(url).hostname or "").lower()
    if host not in LOOPBACK_HOSTS:
        pytest.fail(
            f"Refusing to run Redis persistence tests against non-loopback "
            f"host {host!r}; set {TEST_URL_ENV} to a 127.0.0.1/localhost URL."
        )
    return url


@pytest.fixture()
def redis_env():
    url = _checked_url()
    prefix = f"sabiroute:test-signals:{uuid.uuid4().hex}"
    clients: list[Redis] = []
    backends: list[RedisBackend] = []

    def make_client() -> Redis:
        client = Redis.from_url(url, decode_responses=True)
        client.ping()
        clients.append(client)
        return client

    def make_backend(*, ttl_seconds: int = 3600) -> RedisBackend:
        backend = RedisBackend(
            make_client(),
            ttl_seconds=ttl_seconds,
            key_prefix=prefix,
        )
        backends.append(backend)
        return backend

    try:
        yield prefix, make_client, make_backend
    finally:
        for backend in backends:
            backend.close()
        cleanup = Redis.from_url(url, decode_responses=True)
        try:
            leftovers = list(cleanup.scan_iter(match=f"{prefix}:*"))
            if leftovers:
                cleanup.delete(*leftovers)
            remaining = list(cleanup.scan_iter(match=f"{prefix}:*"))
            assert remaining == [], f"test keys leaked: {remaining}"
        finally:
            cleanup.close()
        for client in clients:
            try:
                client.close()
            except Exception:  # noqa: BLE001 - teardown must not mask failures
                pass


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


def test_observations_survive_a_simulated_restart(redis_env) -> None:
    _, _, make_backend = redis_env
    first_backend = make_backend()
    first_health = HealthRegistry(backend=first_backend)
    first_latency = LatencyTracker(backend=first_backend)
    _warm(first_health, first_latency, "fast", latency_ms=10.0)
    _warm(first_health, first_latency, "slow", latency_ms=100.0)

    assert first_backend.flush(timeout=5.0) is True
    assert first_backend.degraded is False

    # Simulated restart: a new backend instance and new registry objects.
    restarted_backend = make_backend()
    restarted_health = HealthRegistry(backend=restarted_backend)
    restarted_latency = LatencyTracker(backend=restarted_backend)

    assert restarted_health.scoring_observation("fast")[:2] == (5, 0)
    assert restarted_health.scoring_observation("slow")[:2] == (5, 0)
    assert restarted_latency.scoring_observation("fast")[:2] == (5, 10.0)
    assert restarted_latency.scoring_observation("slow")[:2] == (5, 100.0)


def test_scorer_engages_after_restart(redis_env) -> None:
    _, _, make_backend = redis_env
    first_backend = make_backend()
    first_health = HealthRegistry(backend=first_backend)
    first_latency = LatencyTracker(backend=first_backend)
    _warm(first_health, first_latency, "slow", latency_ms=100.0)
    _warm(first_health, first_latency, "fast", latency_ms=10.0)
    assert first_backend.flush(timeout=5.0) is True

    now = datetime.now(UTC)
    scorer = DeterministicScorer(
        ScoringSettings(minimum_samples=5, max_signal_age_seconds=3600)
    )
    restarted_backend = make_backend()
    ranking = scorer.rank(
        ["slow", "fast"],
        reliability=HealthRegistry(backend=restarted_backend),
        latency=LatencyTracker(backend=restarted_backend),
        now=now,
    )

    assert ranking.fallback_reason is None
    assert ranking.ranked_candidates == ("fast", "slow")


def test_ttl_expiry_drops_stale_signals(redis_env) -> None:
    prefix, make_client, make_backend = redis_env
    backend = make_backend(ttl_seconds=1)
    client = make_client()

    backend.append_health("m", datetime.now(UTC), True)
    assert backend.flush(timeout=5.0) is True

    key = f"{prefix}:health:m"
    assert client.exists(key) == 1
    pttl = client.pttl(key)
    assert 0 < pttl <= 1100

    time.sleep(1.2)

    assert client.exists(key) == 0
    assert backend.load_health() == {}


def test_observations_older_than_the_window_are_not_loaded(redis_env) -> None:
    _, _, make_backend = redis_env
    backend = make_backend(ttl_seconds=3600)
    stale = datetime.now(UTC) - timedelta(hours=2)

    backend.append_health("m", stale, True)
    backend.append_latency("m", stale, 12.0)
    assert backend.flush(timeout=5.0) is True

    assert backend.load_health() == {}
    assert backend.load_latency() == {}


def test_gateway_uses_redis_backend_when_redis_url_is_configured(
    redis_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, make_client, _ = redis_env
    monkeypatch.setenv("REDIS_URL", _checked_url())
    monkeypatch.delenv("REDIS_HOST", raising=False)
    model = f"wired-{uuid.uuid4().hex}"

    state = build_gateway_state(config=make_config())
    try:
        assert isinstance(state.health.backend, RedisBackend)
        assert state.health.backend is state.latency.backend

        state.health.mark_success(model)
        state.latency.record(model, 5.0)
        assert state.health.backend.flush(timeout=5.0) is True

        client = make_client()
        keys = list(client.scan_iter(match="sabiroute:signals:v1:*"))
        assert any(key.endswith(f":health:{model}") for key in keys)
        assert any(key.endswith(f":latency:{model}") for key in keys)

        # A second startup over the same store hydrates the observations.
        restarted = build_gateway_state(config=make_config())
        try:
            assert restarted.health.scoring_observation(model)[:2] == (1, 0)
            assert restarted.latency.scoring_observation(model)[:2] == (1, 5.0)
        finally:
            restarted.health.backend.close()
    finally:
        state.health.backend.close()
        cleanup = make_client()
        cleanup.delete(
            f"sabiroute:signals:v1:health:{model}",
            f"sabiroute:signals:v1:latency:{model}",
        )
