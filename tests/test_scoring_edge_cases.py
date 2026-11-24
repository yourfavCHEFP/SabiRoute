"""Coverage for the defensive branches of :mod:`sabiroute.routing.scoring`.

The behavioural path is already pinned by ``test_scoring.py``. This module
covers what that file cannot reach through the real trackers: configuration
rejections, the empty candidate set, a naive cutoff, and telemetry timestamps
dated after the cutoff. The trackers filter future observations upstream, so
the scorer's own guard only runs when a source hands one back directly.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from sabiroute.routing.scoring import DeterministicScorer, ScoringSettings

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class _Reliability:
    def __init__(
        self, observations: dict[str, tuple[int, int, datetime | None]]
    ) -> None:
        self.observations = observations
        self.state_scope_id = "rel-scope"

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> tuple[int, int, datetime | None]:
        return self.observations.get(deployment, (0, 0, None))


class _Latency:
    def __init__(
        self, observations: dict[str, tuple[int, float | None, datetime | None]]
    ) -> None:
        self.observations = observations
        self.state_scope_id = "lat-scope"

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> tuple[int, float | None, datetime | None]:
        return self.observations.get(deployment, (0, None, None))


class _ExplodingSource:
    state_scope_id = "exploding"

    def scoring_observation(
        self, deployment: str, as_of: datetime | None = None
    ) -> Any:
        raise AssertionError("no source may be consulted for an empty candidate set")


def test_empty_candidate_set_returns_an_empty_ranking() -> None:
    scorer = DeterministicScorer()

    ranking = scorer.rank(
        [], reliability=_ExplodingSource(), latency=_ExplodingSource(), now=NOW
    )

    assert ranking.ranked_candidates == ()
    assert ranking.candidate_scores == ()
    assert ranking.fallback_reason is None
    assert ranking.policy_version == "deterministic-v1"
    assert ranking.weights == {"reliability": 0.7, "latency": 0.3}


def test_blank_policy_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="policy version must not be empty"):
        ScoringSettings(policy_version="   ")


def test_minimum_samples_below_one_is_rejected() -> None:
    with pytest.raises(ValueError, match="minimum_samples must be positive"):
        ScoringSettings(minimum_samples=0)


def test_max_signal_age_below_one_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_signal_age_seconds must be positive"):
        ScoringSettings(max_signal_age_seconds=0)


def test_non_finite_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        ScoringSettings(
            reliability_weight=float("nan"), latency_weight=float("nan")
        )


def test_naive_as_of_timestamp_is_rejected() -> None:
    scorer = DeterministicScorer()

    with pytest.raises(ValueError, match="timezone-aware"):
        scorer.rank(
            ["a"],
            reliability=_Reliability({}),
            latency=_Latency({}),
            now=datetime(2026, 1, 1, 12, 0),
        )


def test_reliability_observation_after_the_cutoff_is_discarded() -> None:
    future = NOW + timedelta(minutes=5)
    scorer = DeterministicScorer(ScoringSettings(minimum_samples=1))

    ranking = scorer.rank(
        ["a"],
        reliability=_Reliability({"a": (9, 1, future)}),
        latency=_Latency({"a": (9, 25.0, NOW)}),
        now=NOW,
    )

    score = ranking.candidate_scores[0]
    assert score.reliability_samples == 0
    assert score.success_rate is None
    assert score.latest_reliability_observation is None
    assert score.score is None
    assert "insufficient_reliability_samples" in (ranking.fallback_reason or "")


def test_latency_observation_after_the_cutoff_is_discarded() -> None:
    future = NOW + timedelta(minutes=5)
    scorer = DeterministicScorer(ScoringSettings(minimum_samples=1))

    ranking = scorer.rank(
        ["a"],
        reliability=_Reliability({"a": (9, 1, NOW)}),
        latency=_Latency({"a": (9, 25.0, future)}),
        now=NOW,
    )

    score = ranking.candidate_scores[0]
    assert score.latency_samples == 0
    assert score.average_latency_ms is None
    assert score.latest_latency_observation is None
    assert score.score is None
    assert "insufficient_latency_samples" in (ranking.fallback_reason or "")


def test_fallback_reasons_are_deduplicated_and_sorted() -> None:
    scorer = DeterministicScorer(ScoringSettings(minimum_samples=5))

    ranking = scorer.rank(
        ["short-reliability", "short-latency"],
        reliability=_Reliability(
            {"short-reliability": (1, 0, NOW), "short-latency": (50, 0, NOW)}
        ),
        latency=_Latency(
            {"short-reliability": (50, 10.0, NOW), "short-latency": (1, 10.0, NOW)}
        ),
        now=NOW,
    )

    assert ranking.fallback_reason == (
        "insufficient_latency_samples,insufficient_reliability_samples"
    )
    assert all(item.score is None for item in ranking.candidate_scores)
