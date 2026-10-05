from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


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
        health.last_success = utc_now()
        health.cooldown_until = None

    def mark_failure(self, model_name: str) -> None:
        self.register(model_name)

        health = self.deployments[model_name]

        health.total_failures += 1
        health.consecutive_failures += 1
        health.last_failure = utc_now()

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

    def snapshot(self) -> dict[str, dict]:
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
