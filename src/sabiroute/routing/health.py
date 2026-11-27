from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class DeploymentHealth:
    model_name: str
    healthy: bool = True
    consecutive_failures: int = 0
    total_successes: int = 0
    total_failures: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    cooldown_until: datetime | None = None
    scoring_events: list[tuple[datetime, bool]] = field(default_factory=list, repr=False)

    def is_available(self) -> bool:
        if not self.healthy:
            if self.cooldown_until is None:
                return False

            if utc_now() < self.cooldown_until:
                return False

        return True


@dataclass
class HealthRegistry:
    deployments: dict[str, DeploymentHealth] = field(default_factory=dict)
    failure_threshold: int = 3
    cooldown_seconds: int = 30
    state_scope_id: str = field(default_factory=lambda: str(uuid4()))

    def register(self, model_name: str) -> None:
        self.deployments.setdefault(
            model_name,
            DeploymentHealth(model_name=model_name),
        )

    def mark_success(self, model_name: str) -> None:
        self.register(model_name)

        health = self.deployments[model_name]

        health.healthy = True
        health.consecutive_failures = 0
        health.total_successes += 1
        observed_at = utc_now()
        health.last_success = observed_at
        health.scoring_events.append((observed_at, True))
        health.cooldown_until = None

    def mark_failure(self, model_name: str) -> None:
        self.register(model_name)

        health = self.deployments[model_name]

        health.total_failures += 1
        health.consecutive_failures += 1
        observed_at = utc_now()
        health.last_failure = observed_at
        health.scoring_events.append((observed_at, False))

        if health.consecutive_failures >= self.failure_threshold:
            health.healthy = False
            health.cooldown_until = utc_now() + timedelta(seconds=self.cooldown_seconds)

    def available(self, model_name: str) -> bool:
        self.register(model_name)

        health = self.deployments[model_name]

        if not health.is_available():
            return False

        if not health.healthy:
            # Cooldown expired: enter half-open state and grant a fresh
            # failure budget instead of re-tripping on the first error.
            health.healthy = True
            health.consecutive_failures = 0
            health.cooldown_until = None

        return True

    def scoring_observation(
        self, model_name: str, as_of: datetime | None = None
    ) -> tuple[int, int, datetime | None]:
        health = self.deployments.get(model_name)
        if health is None:
            return 0, 0, None
        events = health.scoring_events
        if as_of is not None:
            events = [event for event in events if event[0] <= as_of]
        successes = sum(1 for _, success in events if success)
        failures = len(events) - successes
        observed = [timestamp for timestamp, _ in events]
        return (
            successes,
            failures,
            max(observed) if observed else None,
        )

    def snapshot(self) -> dict[str, dict[str, bool | int | datetime | None]]:
        return {
            name: {
                "healthy": health.healthy,
                "available": health.is_available(),
                "consecutive_failures": health.consecutive_failures,
                "total_successes": health.total_successes,
                "total_failures": health.total_failures,
                "last_success": health.last_success,
                "last_failure": health.last_failure,
                "cooldown_until": health.cooldown_until,
            }
            for name, health in self.deployments.items()
        }
