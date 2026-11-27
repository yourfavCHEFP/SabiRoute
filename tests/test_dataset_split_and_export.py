"""Chronological splitting and export writing.

The split is the leakage barrier for Phase 13. Every row must be attributable
to a logical request and carry a timezone-aware decision timestamp, fallback
attempts must stay grouped with their request, and when the groups overlap in
time no leakage-safe split exists at all. Each of those is a refusal that
protects the training set from future information.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from sabiroute.intelligence import dataset as ds

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _row(request_id: str, moment: datetime) -> dict[str, Any]:
    return {"logical_request_id": request_id, "decision_timestamp": moment.isoformat()}


def test_evaluation_fraction_must_be_a_proper_fraction() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        ds.chronological_split([], evaluation_fraction=0.0)


def test_every_row_needs_a_logical_request_id() -> None:
    with pytest.raises(ValueError, match="logical_request_id"):
        ds.chronological_split([{"decision_timestamp": NOW.isoformat()}])


def test_every_row_needs_a_decision_timestamp() -> None:
    with pytest.raises(ValueError, match="decision timestamp"):
        ds.chronological_split([{"logical_request_id": "r1"}])


def test_a_decision_timestamp_must_parse() -> None:
    with pytest.raises(ValueError, match="valid decision timestamp"):
        ds.chronological_split(
            [{"logical_request_id": "r1", "decision_timestamp": "not a time"}]
        )


def test_a_decision_timestamp_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ds.chronological_split(
            [{"logical_request_id": "r1", "decision_timestamp": "2026-01-01T12:00:00"}]
        )


def test_two_logical_requests_are_required() -> None:
    with pytest.raises(ValueError, match="At least two"):
        ds.chronological_split([_row("r1", NOW)])


def test_earlier_requests_land_in_the_training_split() -> None:
    rows = [_row("r1", NOW), _row("r2", NOW + timedelta(hours=1))]

    train, evaluation = ds.chronological_split(rows, evaluation_fraction=0.5)

    assert [row["logical_request_id"] for row in train] == ["r1"]
    assert [row["logical_request_id"] for row in evaluation] == ["r2"]


def test_groups_that_overlap_in_time_cannot_be_split() -> None:
    rows = [
        _row("r1", NOW),
        _row("r1", NOW + timedelta(hours=3)),
        _row("r2", NOW + timedelta(hours=1)),
    ]

    with pytest.raises(ValueError, match="overlap"):
        ds.chronological_split(rows, evaluation_fraction=0.5)


def test_a_non_positive_audit_threshold_is_rejected() -> None:
    with pytest.raises(ValueError, match="low_sample_threshold"):
        ds.audit_dataset([], low_sample_threshold=0)


def test_an_export_creates_parents_and_ends_with_a_newline(tmp_path: Any) -> None:
    path = tmp_path / "nested" / "export.json"

    ds._write_json_export({"export_type": "diagnostic"}, path)

    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == {"export_type": "diagnostic"}
