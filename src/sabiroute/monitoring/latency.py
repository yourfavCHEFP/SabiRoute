from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LatencyTracker:
    samples: dict[str, list[float]] = field(default_factory=dict)

    def record(self, model: str, latency_ms: float) -> None:
        self.samples.setdefault(model, []).append(latency_ms)

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
