"""Durable observation backends for routing health and latency signals.

Phase 12 defect: ``HealthRegistry`` and ``LatencyTracker`` keep their
observations in process memory, so a restarted gateway starts cold and cannot
satisfy ``routing_scoring.minimum_samples`` inside its first requests. Measured
routing therefore falls back to configured priority order and never engages in
production. The fix is to carry the same observations across restarts, not to
lower the sample threshold.

``SignalsBackend`` is the narrow seam:

* ``InMemoryBackend`` is the default. It keeps today's process-local semantics;
  a fresh instance starts empty, so omitting a backend changes nothing.
* ``RedisBackend`` persists observations in sorted sets whose keys expire after
  ``max_signal_age_seconds``, so a cold process inherits signals that are still
  fresh and stale signals disappear on their own.

Failure policy: this store is telemetry. A Redis outage must degrade routing to
the in-process behaviour, never fail a request. Writes are queued to a bounded
background writer (the registry write path is synchronous and runs inside async
request handlers, so it must never block the event loop), and reads return an
empty result after recording the degradation. Nothing here raises on a store
failure.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from redis import Redis

from ..security.redaction import redact_secrets

logger = logging.getLogger(__name__)

DEFAULT_KEY_PREFIX = "sabiroute:signals:v1"
DEFAULT_MAX_OBSERVATIONS_PER_MODEL = 1000
DEFAULT_WRITER_QUEUE_CAPACITY = 10000
MAX_RECORDED_ERROR_CHARS = 200

#: One queued observation: (kind, model, observed_at, value).
_PendingWrite = tuple[str, str, datetime, float]


class SignalsBackend(Protocol):
    """Storage seam behind health and latency observations."""

    @property
    def degraded(self) -> bool:
        """True once a store failure has been observed this process."""
        ...

    def append_health(self, model: str, observed_at: datetime, success: bool) -> None:
        """Record one provider attempt outcome. Never raises on store failure."""
        ...

    def append_latency(self, model: str, observed_at: datetime, latency_ms: float) -> None:
        """Record one attempt latency sample. Never raises on store failure."""
        ...

    def load_health(self) -> dict[str, list[tuple[datetime, bool]]]:
        """Return stored outcomes per model, newest window only."""
        ...

    def load_latency(self) -> dict[str, list[tuple[datetime, float]]]:
        """Return stored latency samples per model, newest window only."""
        ...

    def flush(self, timeout: float | None = None) -> bool:
        """Wait for queued writes to drain; True when nothing remains."""
        ...

    def close(self) -> None:
        """Drain, stop the writer, and release the client if owned."""
        ...


class InMemoryBackend:
    """Process-local store; the default and the Redis-less fallback.

    A fresh instance starts empty, so a registry that receives no backend (or
    this one) behaves byte-for-byte like it did before persistence existed.
    Sharing one instance between two registry objects is how the tests simulate
    a restart without a server.
    """

    def __init__(self) -> None:
        self._health: dict[str, list[tuple[datetime, bool]]] = {}
        self._latency: dict[str, list[tuple[datetime, float]]] = {}
        self._lock = threading.Lock()

    @property
    def degraded(self) -> bool:
        return False

    def append_health(self, model: str, observed_at: datetime, success: bool) -> None:
        with self._lock:
            self._health.setdefault(model, []).append((observed_at, success))

    def append_latency(self, model: str, observed_at: datetime, latency_ms: float) -> None:
        with self._lock:
            self._latency.setdefault(model, []).append((observed_at, latency_ms))

    def load_health(self) -> dict[str, list[tuple[datetime, bool]]]:
        with self._lock:
            return {model: list(events) for model, events in self._health.items()}

    def load_latency(self) -> dict[str, list[tuple[datetime, float]]]:
        with self._lock:
            return {model: list(events) for model, events in self._latency.items()}

    def flush(self, timeout: float | None = None) -> bool:
        return True

    def close(self) -> None:
        return None


class RedisBackend:
    """Sorted-set persistence with a TTL derived from ``max_signal_age_seconds``.

    Each deployment gets one sorted set per signal kind, scored by observation
    timestamp. Writes prune members older than the freshness window, cap the set
    at ``max_observations_per_model``, and refresh the key TTL, so an idle
    deployment's key vanishes on its own rather than accumulating forever.

    Appends are queued to a bounded background writer; the caller never waits on
    Redis and never sees its exceptions. If the queue fills, the oldest pending
    observation is dropped and counted, because telemetry loss is preferable to
    memory growth or request latency.
    """

    def __init__(
        self,
        client: Redis,
        *,
        ttl_seconds: int,
        key_prefix: str = DEFAULT_KEY_PREFIX,
        max_observations_per_model: int = DEFAULT_MAX_OBSERVATIONS_PER_MODEL,
        queue_capacity: int = DEFAULT_WRITER_QUEUE_CAPACITY,
    ) -> None:
        if ttl_seconds < 1:
            raise ValueError("Signals TTL must be positive.")
        if max_observations_per_model < 1:
            raise ValueError("Signals observation cap must be positive.")
        if queue_capacity < 1:
            raise ValueError("Signals writer queue capacity must be positive.")
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix.rstrip(":")
        self._max_observations = max_observations_per_model
        self._queue_capacity = queue_capacity
        self._condition = threading.Condition()
        self._state_lock = threading.Lock()
        self._queue: deque[_PendingWrite] = deque()
        self._pending = 0
        self._closed = False
        self._degraded = False
        self._last_error: str | None = None
        self._dropped = 0
        self._writer = threading.Thread(
            target=self._run,
            name="sabiroute-signals-writer",
            daemon=True,
        )
        self._writer.start()

    @property
    def degraded(self) -> bool:
        return self._degraded

    @property
    def last_error(self) -> str | None:
        """Redacted description of the most recent store failure."""
        return self._last_error

    @property
    def dropped_observations(self) -> int:
        """Observations discarded because the writer queue was full."""
        return self._dropped

    @property
    def pending_observations(self) -> int:
        """Observations queued or in flight (test/diagnostic seam)."""
        return self._pending

    def append_health(self, model: str, observed_at: datetime, success: bool) -> None:
        self._enqueue("health", model, observed_at, 1.0 if success else 0.0)

    def append_latency(self, model: str, observed_at: datetime, latency_ms: float) -> None:
        self._enqueue("latency", model, observed_at, float(latency_ms))

    def load_health(self) -> dict[str, list[tuple[datetime, bool]]]:
        return {
            model: [(observed_at, value >= 0.5) for observed_at, value in observations]
            for model, observations in self._load("health").items()
        }

    def load_latency(self) -> dict[str, list[tuple[datetime, float]]]:
        return self._load("latency")

    def flush(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._condition:
            while self._pending:
                if not self._writer.is_alive():
                    return False
                if deadline is None:
                    self._condition.wait(timeout=0.5)
                    continue
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(timeout=remaining)
        return True

    def close(self) -> None:
        self.flush(timeout=2.0)
        with self._condition:
            self._closed = True
            self._condition.notify_all()
        self._writer.join(timeout=2.0)
        try:
            self._client.close()
        except Exception as exc:  # noqa: BLE001 - teardown must not raise
            self._record_failure(exc)

    def _enqueue(self, kind: str, model: str, observed_at: datetime, value: float) -> None:
        with self._condition:
            if self._closed:
                return
            if self._pending >= self._queue_capacity:
                self._queue.popleft()
                self._pending -= 1
                self._dropped += 1
            self._queue.append((kind, model, observed_at, value))
            self._pending += 1
            self._condition.notify()

    def _run(self) -> None:
        while True:
            with self._condition:
                while not self._queue and not self._closed:
                    self._condition.wait(timeout=0.5)
                if not self._queue and self._closed:
                    return
                batch = list(self._queue)
                self._queue.clear()
            try:
                self._write_batch(batch)
            except Exception as exc:  # noqa: BLE001 - degrade, never crash
                self._record_failure(exc)
            finally:
                with self._condition:
                    self._pending -= len(batch)
                    if self._pending < 0:
                        self._pending = 0
                    self._condition.notify_all()

    def _write_batch(self, batch: list[_PendingWrite]) -> None:
        cutoff = f"({time.time() - self._ttl_seconds}"
        pipeline = self._client.pipeline(transaction=False)
        for kind, model, observed_at, value in batch:
            key = self._key(kind, model)
            member = json.dumps(
                {
                    "t": observed_at.isoformat(),
                    "v": value,
                    "n": uuid4().hex,
                }
            )
            pipeline.zadd(key, {member: observed_at.timestamp()})
            pipeline.zremrangebyscore(key, "-inf", cutoff)
            pipeline.zremrangebyrank(key, 0, -(self._max_observations + 1))
            pipeline.expire(key, self._ttl_seconds)
        pipeline.execute()

    def _load(self, kind: str) -> dict[str, list[tuple[datetime, float]]]:
        try:
            cutoff = f"({time.time() - self._ttl_seconds}"
            base = f"{self._key_prefix}:{kind}:"
            loaded: dict[str, list[tuple[datetime, float]]] = {}
            for raw_key in self._client.scan_iter(match=f"{base}*", count=200):
                key = _as_text(raw_key)
                model = key[len(base) :] if key.startswith(base) else key.rsplit(":", 1)[-1]
                observations: list[tuple[datetime, float]] = []
                for raw_member in self._client.zrangebyscore(key, cutoff, "+inf"):
                    parsed = _parse_observation(raw_member)
                    if parsed is not None:
                        observations.append(parsed)
                if observations:
                    loaded[model] = sorted(observations, key=lambda item: item[0])
            return loaded
        except Exception as exc:  # noqa: BLE001 - degrade, never crash
            self._record_failure(exc)
            return {}

    def _key(self, kind: str, model: str) -> str:
        return f"{self._key_prefix}:{kind}:{model}"

    def _record_failure(self, exc: BaseException) -> None:
        message = redact_secrets(exc)
        if len(message) > MAX_RECORDED_ERROR_CHARS:
            message = f"{message[:MAX_RECORDED_ERROR_CHARS]}..."
        with self._state_lock:
            first_failure = not self._degraded
            self._degraded = True
            self._last_error = message
        if first_failure:
            logger.warning(
                "Signals backend degraded; routing continues on in-process "
                "observations: %s",
                message,
            )


def _as_text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def _parse_observation(raw_member: object) -> tuple[datetime, float] | None:
    try:
        payload = json.loads(_as_text(raw_member))
        observed_at = datetime.fromisoformat(str(payload["t"]))
        value = float(payload["v"])
    except (TypeError, ValueError, KeyError):
        return None
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    return observed_at, value
