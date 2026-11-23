from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from .signals_store import InMemoryBackend, SignalsBackend


@dataclass
class LatencyTracker:
    samples: dict[str, list[float]] = field(default_factory=dict)
    _totals: dict[str, float] = field(default_factory=dict, repr=False)
    _last_observed: dict[str, datetime] = field(default_factory=dict, repr=False)
    _observations: dict[str, list[tuple[datetime, float]]] = field(
        default_factory=dict, repr=False
    )
    state_scope_id: str = field(default_factory=lambda: str(uuid4()))
    backend: SignalsBackend = field(
        default_factory=InMemoryBackend, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        # Hydrate samples that survived a restart so a cold process does not
        # need ``minimum_samples`` fresh requests before measured routing can
        # engage.
        for model, observations in self.backend.load_latency().items():
            if not observations:
                continue
            ordered = sorted(observations, key=lambda item: item[0])
            self._observations.setdefault(model, []).extend(ordered)
            values = [value for _, value in ordered]
            self.samples.setdefault(model, []).extend(values)
            self._totals[model] = self._totals.get(model, 0.0) + sum(values)
            self._last_observed[model] = ordered[-1][0]

    def record(self, model: str, latency_ms: float) -> None:
        observed_at = datetime.now(UTC)
        self.samples.setdefault(model, []).append(latency_ms)
        self._totals[model] = self._totals.get(model, 0.0) + latency_ms
        self._last_observed[model] = observed_at
        self._observations.setdefault(model, []).append((observed_at, latency_ms))
        self.backend.append_latency(model, observed_at, latency_ms)

    def scoring_observation(
        self, model: str, as_of: datetime | None = None
    ) -> tuple[int, float | None, datetime | None]:
        observations = self._observations.get(model, ())
        if as_of is not None:
            observations = [item for item in observations if item[0] <= as_of]
        values = [value for _, value in observations]
        count = len(values)
        average = sum(values) / count if count else None
        latest = max((timestamp for timestamp, _ in observations), default=None)
        return count, average, latest

    def average(self, model: str) -> float | None:
        values = self.samples.get(model)

        if not values:
            return None

        return sum(values) / len(values)

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        return {
            model: {
                "samples": len(values),
                "average_ms": sum(values) / len(values),
                "last_ms": values[-1],
            }
            for model, values in self.samples.items()
            if values
        }
