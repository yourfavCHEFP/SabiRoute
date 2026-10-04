from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoutingPolicy:
    name: str
    deployments: list[str] = field(default_factory=list)
    strategy: str = "priority"
    max_attempts: int = 2


DEFAULT_POLICIES = {
    "ultimate": RoutingPolicy(
        name="ultimate",
        strategy="priority",
        max_attempts=3,
    ),
    "coding": RoutingPolicy(
        name="coding",
        strategy="priority",
        max_attempts=3,
    ),
    "reasoning": RoutingPolicy(
        name="reasoning",
        strategy="priority",
        max_attempts=3,
    ),
    "research": RoutingPolicy(
        name="research",
        strategy="priority",
        max_attempts=3,
    ),
    "fast": RoutingPolicy(
        name="fast",
        strategy="priority",
        max_attempts=2,
    ),
    "cheap": RoutingPolicy(
        name="cheap",
        strategy="priority",
        max_attempts=2,
    ),
}


class PolicyRegistry:
    def __init__(
        self,
        policies: dict[str, RoutingPolicy] | None = None,
    ) -> None:
        self._policies = policies or DEFAULT_POLICIES.copy()

    def get(self, name: str) -> RoutingPolicy:
        try:
            return self._policies[name]
        except KeyError as exc:
            raise ValueError(f"Unknown routing policy: {name}") from exc

    def register(self, policy: RoutingPolicy) -> None:
        self._policies[policy.name] = policy

    def list(self) -> list[RoutingPolicy]:
        return list(self._policies.values())
