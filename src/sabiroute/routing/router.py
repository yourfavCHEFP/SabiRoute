from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ..providers.registry import ProviderRegistry
from .fallback import FallbackEngine
from .health import HealthRegistry
from .policies import PolicyRegistry


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Selected deployment choice returned by the router."""

    deployment: str
    provider: str
    reason: str = "priority"
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class Router:
    """Simple routing layer used by SabiRoute before LiteLLM proxy execution."""

    def __init__(
        self,
        registry: ProviderRegistry,
        health: HealthRegistry | None = None,
        policies: PolicyRegistry | None = None,
        fallback: FallbackEngine | None = None,
    ) -> None:
        self.registry = registry
        self.health = health or HealthRegistry()
        self.policies = policies or PolicyRegistry()
        self.fallback = fallback or FallbackEngine(self.health)

    def choose_deployment(
        self,
        candidates: Iterable[str],
        *,
        policy_name: str | None = None,
        attempted: Iterable[str] | None = None,
    ) -> RouteDecision:
        candidate_list = list(candidates)
        if not candidate_list:
            raise ValueError("At least one routing candidate is required.")

        validated = self.registry.validate_candidates(candidate_list)
        attempted_set = {
            item.strip() for item in (attempted or ()) if item and item.strip()
        }

        available = [
            name
            for name in validated
            if name not in attempted_set and self.health.available(name)
        ]
        if not available:
            available = [name for name in validated if name not in attempted_set]
        if not available:
            raise ValueError("No routing candidates are available for this request.")

        chosen = available[0]
        deployment = self.registry.get(chosen)

        return RouteDecision(
            deployment=chosen,
            provider=deployment.provider,
            reason=f"policy:{policy_name or 'default'}",
            priority=0,
            metadata={"policy": policy_name or "default"},
        )

    def route(
        self,
        candidates: Iterable[str],
        *,
        policy_name: str | None = None,
        attempted: Iterable[str] | None = None,
    ) -> RouteDecision:
        return self.choose_deployment(
            candidates,
            policy_name=policy_name,
            attempted=attempted,
        )


__all__ = ["RouteDecision", "Router"]
