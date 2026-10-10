from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..capabilities import Capability, RequestType
from ..monitoring.latency import LatencyTracker
from ..providers.registry import ProviderRegistry
from .fallback import FallbackEngine
from .health import HealthRegistry
from .policies import PolicyRegistry
from .scoring import CandidateScore, DeterministicScorer, ScoringSettings


@dataclass(frozen=True, slots=True)
class RouteExplanation:
    """Internal route eligibility and deterministic-selection explanation."""

    request_type: RequestType | None
    required_capabilities: tuple[Capability, ...]
    candidate_deployments: tuple[str, ...]
    capability_eligible_deployments: tuple[str, ...]
    capability_excluded_deployments: dict[str, tuple[str, ...]]
    unhealthy_deployments: tuple[str, ...]
    eligible_deployments: tuple[str, ...]
    ranked_candidates: tuple[str, ...]
    candidate_scores: tuple[CandidateScore, ...]
    scoring_policy_version: str
    scoring_weights: dict[str, float]
    scoring_fallback_reason: str | None
    scoring_as_of: datetime | None
    selected_deployment: str
    selection_reason: str


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Selected deployment choice returned by the router."""

    deployment: str
    provider: str
    reason: str = "priority"
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    explanation: RouteExplanation | None = None


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    """Ordered capability and health filtering result for one routing request."""

    candidate_deployments: tuple[str, ...]
    capability_eligible_deployments: tuple[str, ...]
    capability_excluded_deployments: dict[str, tuple[str, ...]]
    unhealthy_deployments: tuple[str, ...]
    remaining_deployments: tuple[str, ...]
    available_deployments: tuple[str, ...]


class NoCapableDeploymentError(ValueError):
    """No configured candidate has every required capability verified."""


class NoHealthyDeploymentError(ValueError):
    """Capable candidates exist, but all are unhealthy or cooling down."""


class NoRemainingDeploymentError(ValueError):
    """All capable candidates have already been attempted."""


class Router:
    """Simple routing layer used by SabiRoute before LiteLLM proxy execution."""

    def __init__(
        self,
        registry: ProviderRegistry,
        health: HealthRegistry | None = None,
        policies: PolicyRegistry | None = None,
        fallback: FallbackEngine | None = None,
        scoring_settings: ScoringSettings | None = None,
        latency: LatencyTracker | None = None,
    ) -> None:
        self.registry = registry
        self.health = health or HealthRegistry()
        self.policies = policies or PolicyRegistry()
        self.fallback = fallback or FallbackEngine(self.health)
        self.scorer = DeterministicScorer(scoring_settings)
        self.latency = latency or LatencyTracker()

    def choose_deployment(
        self,
        candidates: Iterable[str],
        *,
        policy_name: str | None = None,
        attempted: Iterable[str] | None = None,
        required_capabilities: Iterable[Capability] = (),
        request_type: RequestType | None = None,
        strategy: str = "priority",
        scoring_as_of: datetime | None = None,
    ) -> RouteDecision:
        evaluation = self.evaluate_candidates(
            candidates,
            required_capabilities=required_capabilities,
            attempted=attempted,
        )
        if not evaluation.capability_eligible_deployments:
            raise NoCapableDeploymentError(
                "No configured deployment satisfies the required capabilities."
            )
        if not evaluation.remaining_deployments:
            raise NoRemainingDeploymentError(
                "Every capable deployment has already been attempted."
            )
        if not evaluation.available_deployments:
            raise NoHealthyDeploymentError(
                "No healthy deployment satisfies the required capabilities."
            )

        if strategy not in {"priority", "measured"}:
            raise ValueError(f"Unsupported routing strategy: {strategy}")
        ranking = None
        as_of = None
        if strategy == "measured":
            as_of = scoring_as_of if scoring_as_of is not None else datetime.now(UTC)
            ranking = self.scorer.rank(
                evaluation.available_deployments,
                reliability=self.health,
                latency=self.latency,
                now=as_of,
            )
        ranked_candidates = (
            ranking.ranked_candidates if ranking is not None else evaluation.available_deployments
        )
        chosen = ranked_candidates[0]
        deployment = self.registry.get(chosen)
        required = tuple(sorted(set(required_capabilities), key=lambda item: item.value))
        selection_reason = (
            "highest measured deterministic score; configured order breaks ties"
            if ranking is not None and ranking.fallback_reason is None
            else "configured priority order (cold start, stale telemetry, or priority strategy)"
        )
        scoring_policy_version = (
            ranking.policy_version if ranking is not None else "priority-v1"
        )
        explanation = RouteExplanation(
            request_type=request_type,
            required_capabilities=required,
            candidate_deployments=evaluation.candidate_deployments,
            capability_eligible_deployments=evaluation.capability_eligible_deployments,
            capability_excluded_deployments=evaluation.capability_excluded_deployments,
            unhealthy_deployments=evaluation.unhealthy_deployments,
            eligible_deployments=evaluation.available_deployments,
            ranked_candidates=ranked_candidates,
            candidate_scores=ranking.candidate_scores if ranking else (),
            scoring_policy_version=scoring_policy_version,
            scoring_weights=ranking.weights if ranking else {},
            scoring_fallback_reason=ranking.fallback_reason if ranking else "priority_strategy",
            scoring_as_of=as_of,
            selected_deployment=chosen,
            selection_reason=selection_reason,
        )

        return RouteDecision(
            deployment=chosen,
            provider=deployment.provider,
            reason=f"policy:{policy_name or 'default'}",
            priority=0,
            metadata={
                "policy": policy_name or "default",
                "selection_reason": explanation.selection_reason,
                "scoring_policy_version": explanation.scoring_policy_version,
                "ranked_candidates": explanation.ranked_candidates,
            },
            explanation=explanation,
        )

    def evaluate_candidates(
        self,
        candidates: Iterable[str],
        *,
        required_capabilities: Iterable[Capability] = (),
        attempted: Iterable[str] | None = None,
    ) -> CandidateEvaluation:
        """Filter in order: explicit capabilities, then health, then attempts."""
        candidate_list = list(candidates)
        if not candidate_list:
            raise ValueError("At least one routing candidate is required.")
        validated = self.registry.validate_candidates(candidate_list)
        required = frozenset(required_capabilities)
        attempted_set = {
            item.strip() for item in (attempted or ()) if item and item.strip()
        }

        capability_eligible: list[str] = []
        excluded: dict[str, tuple[str, ...]] = {}
        for name in validated:
            profile = self.registry.get(name).capabilities
            unsupported, unknown = profile.missing_requirements(required)
            if unsupported or unknown:
                reasons = [
                    f"unsupported:{item.value}"
                    for item in sorted(unsupported, key=lambda capability: capability.value)
                ]
                reasons.extend(
                    f"unknown:{item.value}"
                    for item in sorted(unknown, key=lambda capability: capability.value)
                )
                excluded[name] = tuple(reasons)
            else:
                capability_eligible.append(name)

        unhealthy: list[str] = []
        available: list[str] = []
        remaining: list[str] = []
        for name in capability_eligible:
            if name in attempted_set:
                continue
            remaining.append(name)
            if self.health.available(name):
                available.append(name)
            else:
                unhealthy.append(name)

        return CandidateEvaluation(
            candidate_deployments=tuple(validated),
            capability_eligible_deployments=tuple(capability_eligible),
            capability_excluded_deployments=excluded,
            unhealthy_deployments=tuple(unhealthy),
            remaining_deployments=tuple(remaining),
            available_deployments=tuple(available),
        )

    def route(
        self,
        candidates: Iterable[str],
        *,
        policy_name: str | None = None,
        attempted: Iterable[str] | None = None,
        required_capabilities: Iterable[Capability] = (),
        request_type: RequestType | None = None,
        strategy: str = "priority",
    ) -> RouteDecision:
        return self.choose_deployment(
            candidates,
            policy_name=policy_name,
            attempted=attempted,
            required_capabilities=required_capabilities,
            request_type=request_type,
            strategy=strategy,
        )


__all__ = [
    "CandidateEvaluation",
    "NoCapableDeploymentError",
    "NoHealthyDeploymentError",
    "NoRemainingDeploymentError",
    "RouteDecision",
    "RouteExplanation",
    "Router",
]
