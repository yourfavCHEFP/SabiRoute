from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..capabilities import Capability
from ..providers.registry import ProviderRegistry


@dataclass(frozen=True)
class RoutingPolicy:
    name: str
    deployments: list[str] = field(default_factory=list)
    strategy: str = "priority"
    max_attempts: int = 2
    required_capabilities: frozenset[Capability] = frozenset()


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

    @classmethod
    def from_directory(
        cls,
        directory: str | Path,
        registry: ProviderRegistry,
    ) -> PolicyRegistry:
        """Load ordered virtual-model routes and validate them against deployments."""
        route_dir = Path(directory)
        if not route_dir.is_dir():
            raise ValueError(f"Route configuration directory does not exist: {route_dir}")

        policies: dict[str, RoutingPolicy] = {}
        for path in sorted(route_dir.glob("*.yaml")):
            with path.open("r", encoding="utf-8") as stream:
                raw: Any = yaml.safe_load(stream)
            if not isinstance(raw, dict):
                raise ValueError(f"Route file must contain a YAML mapping: {path}")

            name = raw.get("name", path.stem)
            candidates = raw.get("deployments")
            strategy = raw.get("strategy", "priority")
            max_attempts = raw.get("max_attempts", 1)
            raw_requirements = raw.get("required_capabilities", [])
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"Route name must be a non-empty string: {path}")
            name = name.strip().lower()
            if name in policies:
                raise ValueError(f"Duplicate route name: {name}")
            if not isinstance(candidates, list) or not candidates:
                raise ValueError(f"Route {name!r} must define at least one deployment.")
            if any(not isinstance(item, str) or not item.strip() for item in candidates):
                raise ValueError(f"Route {name!r} contains an invalid deployment name.")
            if len(set(candidates)) != len(candidates):
                raise ValueError(f"Route {name!r} contains duplicate deployments.")
            try:
                validated = registry.validate_candidates(candidates)
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Invalid deployment in route {name!r}: {exc}") from exc
            if strategy not in {"priority", "measured"}:
                raise ValueError(f"Route {name!r} uses unsupported strategy {strategy!r}.")
            if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
                raise ValueError(f"Route {name!r} max_attempts must be an integer.")
            if max_attempts < 1 or max_attempts > len(validated):
                raise ValueError(
                    f"Route {name!r} max_attempts must be between 1 and its candidate count."
                )
            if not isinstance(raw_requirements, list):
                raise ValueError(f"Route {name!r} required_capabilities must be a list.")
            try:
                requirements = [Capability(value) for value in raw_requirements]
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Route {name!r} contains an unknown required capability."
                ) from exc
            if len(requirements) != len(set(requirements)):
                raise ValueError(f"Route {name!r} repeats a required capability.")

            policies[name] = RoutingPolicy(
                name=name,
                deployments=validated,
                strategy=strategy,
                max_attempts=max_attempts,
                required_capabilities=frozenset(requirements),
            )

        if not policies:
            raise ValueError(f"No route YAML files found in {route_dir}")
        return cls(policies)
