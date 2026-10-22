"""Measured, deterministic ranking of candidates already cleared by eligibility."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Protocol


class ReliabilitySource(Protocol):
    state_scope_id: str

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> tuple[int, int, datetime | None]: ...


class LatencySource(Protocol):
    state_scope_id: str

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> tuple[int, float | None, datetime | None]: ...


@dataclass(frozen=True, slots=True)
class ScoringSettings:
    policy_version: str = "deterministic-v1"
    reliability_weight: float = 0.7
    latency_weight: float = 0.3
    minimum_samples: int = 5
    max_signal_age_seconds: int = 3600

    def __post_init__(self) -> None:
        if not self.policy_version.strip():
            raise ValueError("Scoring policy version must not be empty.")
        if self.reliability_weight < 0 or self.latency_weight < 0:
            raise ValueError("Scoring weights cannot be negative.")
        if abs(self.reliability_weight + self.latency_weight - 1.0) > 1e-9:
            raise ValueError("Reliability and latency weights must sum to 1.")
        if self.minimum_samples < 1:
            raise ValueError("Scoring minimum_samples must be positive.")
        if self.max_signal_age_seconds < 1:
            raise ValueError("Scoring max_signal_age_seconds must be positive.")
        if not isfinite(self.reliability_weight) or not isfinite(self.latency_weight):
            raise ValueError("Scoring weights must be finite numbers.")

    @property
    def weights(self) -> dict[str, float]:
        return {
            "reliability": self.reliability_weight,
            "latency": self.latency_weight,
        }


@dataclass(frozen=True, slots=True)
class CandidateScore:
    deployment: str
    score: float | None
    success_rate: float | None
    reliability_samples: int
    average_latency_ms: float | None
    latency_normalized: float | None
    latency_samples: int
    latest_reliability_observation: datetime | None = None
    latest_latency_observation: datetime | None = None
    reliability_state_scope_id: str | None = None
    latency_state_scope_id: str | None = None


@dataclass(frozen=True, slots=True)
class RankingResult:
    ranked_candidates: tuple[str, ...]
    candidate_scores: tuple[CandidateScore, ...]
    policy_version: str
    weights: dict[str, float]
    fallback_reason: str | None


@dataclass(frozen=True, slots=True)
class _ObservedSignals:
    success_rate: float | None
    reliability_samples: int
    average_latency_ms: float | None
    latency_samples: int
    last_reliability_observation: datetime | None
    last_latency_observation: datetime | None
    reliability_state_scope_id: str | None
    latency_state_scope_id: str | None


class DeterministicScorer:
    """Ranks an already eligible ordered candidate set using fresh telemetry."""

    def __init__(self, settings: ScoringSettings | None = None) -> None:
        self.settings = settings or ScoringSettings()

    def rank(
        self,
        eligible_candidates: tuple[str, ...] | list[str],
        *,
        reliability: ReliabilitySource,
        latency: LatencySource,
        now: datetime | None = None,
    ) -> RankingResult:
        candidates = tuple(eligible_candidates)
        if not candidates:
            return RankingResult((), (), self.settings.policy_version, self.settings.weights, None)

        current_time = now if now is not None else datetime.now(UTC)
        if current_time.tzinfo is None:
            raise ValueError("Scoring as-of timestamp must be timezone-aware.")
        current_time = current_time.astimezone(UTC)
        observations = {
            name: self._observe(name, reliability, latency, current_time)
            for name in candidates
        }
        stale_before = current_time - timedelta(
            seconds=self.settings.max_signal_age_seconds
        )
        fallback_reasons: set[str] = set()
        for observation in observations.values():
            if observation.reliability_samples < self.settings.minimum_samples:
                fallback_reasons.add("insufficient_reliability_samples")
            if observation.latency_samples < self.settings.minimum_samples:
                fallback_reasons.add("insufficient_latency_samples")
            if (
                observation.last_reliability_observation is None
                or observation.last_reliability_observation < stale_before
                or observation.last_reliability_observation > current_time
                or observation.last_latency_observation is None
                or observation.last_latency_observation < stale_before
                or observation.last_latency_observation > current_time
            ):
                fallback_reasons.add("stale_or_missing_telemetry")

        if fallback_reasons:
            scores = tuple(
                CandidateScore(
                    deployment=name,
                    score=None,
                    success_rate=observations[name].success_rate,
                    reliability_samples=observations[name].reliability_samples,
                    average_latency_ms=observations[name].average_latency_ms,
                    latency_normalized=None,
                    latency_samples=observations[name].latency_samples,
                    latest_reliability_observation=(
                        observations[name].last_reliability_observation
                    ),
                    latest_latency_observation=observations[name].last_latency_observation,
                    reliability_state_scope_id=(
                        observations[name].reliability_state_scope_id
                    ),
                    latency_state_scope_id=observations[name].latency_state_scope_id,
                )
                for name in candidates
            )
            return RankingResult(
                ranked_candidates=candidates,
                candidate_scores=scores,
                policy_version=self.settings.policy_version,
                weights=self.settings.weights,
                fallback_reason=",".join(sorted(fallback_reasons)),
            )

        latency_values = [
            observations[name].average_latency_ms for name in candidates
        ]
        minimum_latency = min(value for value in latency_values if value is not None)
        maximum_latency = max(value for value in latency_values if value is not None)
        latency_range = maximum_latency - minimum_latency

        scores_by_name: dict[str, CandidateScore] = {}
        for name in candidates:
            observation = observations[name]
            assert observation.success_rate is not None
            assert observation.average_latency_ms is not None
            normalized_latency = (
                1.0
                if latency_range == 0
                else (maximum_latency - observation.average_latency_ms) / latency_range
            )
            score = (
                self.settings.reliability_weight * observation.success_rate
                + self.settings.latency_weight * normalized_latency
            )
            scores_by_name[name] = CandidateScore(
                deployment=name,
                score=score,
                success_rate=observation.success_rate,
                reliability_samples=observation.reliability_samples,
                average_latency_ms=observation.average_latency_ms,
                latency_normalized=normalized_latency,
                latency_samples=observation.latency_samples,
                latest_reliability_observation=observation.last_reliability_observation,
                latest_latency_observation=observation.last_latency_observation,
                reliability_state_scope_id=observation.reliability_state_scope_id,
                latency_state_scope_id=observation.latency_state_scope_id,
            )

        priority_index = {name: index for index, name in enumerate(candidates)}

        def deterministic_key(name: str) -> tuple[float, int]:
            score = scores_by_name[name].score
            assert score is not None
            return -score, priority_index[name]

        ranked = tuple(
            sorted(candidates, key=deterministic_key)
        )
        return RankingResult(
            ranked_candidates=ranked,
            candidate_scores=tuple(scores_by_name[name] for name in candidates),
            policy_version=self.settings.policy_version,
            weights=self.settings.weights,
            fallback_reason=None,
        )

    @staticmethod
    def _observe(
        deployment: str,
        reliability: ReliabilitySource,
        latency: LatencySource,
        as_of: datetime,
    ) -> _ObservedSignals:
        successes, failures, latest_outcome = reliability.scoring_observation(
            deployment, as_of
        )
        latency_samples, average_latency, latest_latency = latency.scoring_observation(
            deployment, as_of
        )
        if latest_outcome is not None and latest_outcome > as_of:
            successes = failures = 0
            latest_outcome = None
        if latest_latency is not None and latest_latency > as_of:
            latency_samples = 0
            average_latency = None
            latest_latency = None
        outcome_count = successes + failures
        success_rate = successes / outcome_count if outcome_count else None
        return _ObservedSignals(
            success_rate=success_rate,
            reliability_samples=outcome_count,
            average_latency_ms=average_latency,
            latency_samples=latency_samples,
            last_reliability_observation=latest_outcome,
            last_latency_observation=latest_latency,
            reliability_state_scope_id=reliability.state_scope_id,
            latency_state_scope_id=latency.state_scope_id,
        )
