from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Metrics:
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    requests_rate_limited: int = 0
    _by_model: dict[str, int] = field(default_factory=dict)

    def record_request(self, model: str) -> None:
        self.requests_total += 1
        self._by_model[model] = self._by_model.get(model, 0) + 1

    def record_success(self) -> None:
        self.requests_successful += 1

    def record_failure(self) -> None:
        self.requests_failed += 1

    def record_rate_limited(self) -> None:
        """Count one authenticated client request rejected before provider routing."""
        self.requests_rate_limited += 1

    def snapshot(self) -> dict[str, int | dict[str, int]]:
        return {
            "requests_total": self.requests_total,
            "requests_successful": self.requests_successful,
            "requests_failed": self.requests_failed,
            "requests_rate_limited": self.requests_rate_limited,
            "requests_by_model": dict(self._by_model),
        }
