from __future__ import annotations

from collections.abc import Iterable

from .health import HealthRegistry


class FallbackEngine:
    def __init__(self, health: HealthRegistry) -> None:
        self.health = health

    def available_candidates(
        self,
        candidates: Iterable[str],
    ) -> list[str]:
        return [
            model_name for model_name in candidates if self.health.available(model_name)
        ]

    def next_candidate(
        self,
        candidates: Iterable[str],
        attempted: set[str],
    ) -> str | None:
        for candidate in candidates:
            if candidate in attempted:
                continue

            if self.health.available(candidate):
                return candidate

        return None
