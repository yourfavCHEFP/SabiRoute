"""Behavioural tests for :mod:`sabiroute.monitoring.latency`."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sabiroute.monitoring.latency import LatencyTracker


def test_average_is_none_before_any_sample() -> None:
    assert LatencyTracker().average("model-a") is None


def test_average_is_the_mean_of_recorded_samples() -> None:
    tracker = LatencyTracker()
    tracker.record("model-a", 100.0)
    tracker.record("model-a", 300.0)

    assert tracker.average("model-a") == 200.0


def test_snapshot_is_empty_without_samples() -> None:
    assert LatencyTracker().snapshot() == {}


def test_snapshot_reports_count_average_and_last() -> None:
    tracker = LatencyTracker()
    tracker.record("model-a", 10.0)
    tracker.record("model-a", 30.0)

    assert tracker.snapshot() == {
        "model-a": {"samples": 2, "average_ms": 20.0, "last_ms": 30.0}
    }


def test_scoring_observation_is_empty_for_an_unknown_model() -> None:
    assert LatencyTracker().scoring_observation("absent") == (0, None, None)


def test_scoring_observation_reports_count_average_and_latest() -> None:
    tracker = LatencyTracker()
    tracker.record("model-a", 40.0)
    tracker.record("model-a", 60.0)

    count, average, latest = tracker.scoring_observation("model-a")

    assert count == 2
    assert average == 50.0
    assert latest is not None


def test_scoring_observation_honours_an_as_of_cutoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sabiroute.monitoring import latency as latency_module

    base = datetime.now(UTC)

    class _Clock:
        current = base

        @classmethod
        def now(cls, tz: object) -> datetime:
            return cls.current

    monkeypatch.setattr(latency_module, "datetime", _Clock)
    tracker = latency_module.LatencyTracker()
    tracker.record("model-a", 10.0)
    _Clock.current = base + timedelta(seconds=5)
    tracker.record("model-a", 1000.0)

    count, average, latest = tracker.scoring_observation("model-a", as_of=base)

    assert count == 1
    assert average == 10.0
    assert latest == base


def test_scoring_observation_excludes_everything_after_a_past_cutoff() -> None:
    tracker = LatencyTracker()
    tracker.record("model-a", 10.0)

    count, average, latest = tracker.scoring_observation(
        "model-a", as_of=datetime.now(UTC) - timedelta(days=1)
    )

    assert (count, average, latest) == (0, None, None)
