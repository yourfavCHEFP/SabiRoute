"""Attempt-timestamp refusals and quarantine marking in the dataset module.

An attempt whose timestamps are out of order, or that claims to have started
before the routing decision it informs, cannot be used as training evidence.
The diagnostic export must say so explicitly and keep the row as quarantined
diagnostics rather than pairing it or dropping it silently.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from sabiroute.intelligence import dataset as ds

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _snapshot(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "logical_request_id": "req-1",
        "attempt_number": 1,
        "decision_timestamp": NOW,
        "requested_alias": "fast",
        "request_type": "chat",
        "routing_policy_id": "policy",
        "routing_strategy": "priority",
        "messages": [{"role": "user", "content": "hi"}],
        "options": {},
        "decision": SimpleNamespace(explanation=None),
    }
    fields.update(overrides)
    return ds.make_pre_routing_snapshot(**fields)


def _feature(**overrides: Any) -> Any:
    return ds.PreRoutingFeatureSnapshot.model_validate(_snapshot(**overrides))


def _outcome(started: datetime, completed: datetime, recorded: datetime) -> dict[str, Any]:
    return {
        "attempt_schema_version": "1.1",
        "attempt_started_at": started.isoformat(),
        "attempt_completed_at": completed.isoformat(),
        "outcome_recorded_at": recorded.isoformat(),
    }


def test_an_attempt_that_completes_before_it_starts_is_reported() -> None:
    reasons = ds._temporal_reasons(
        _feature(),
        _outcome(NOW + timedelta(minutes=2), NOW + timedelta(minutes=1), NOW),
        now=NOW + timedelta(minutes=5),
    )

    assert "attempt_timestamp_order_invalid" in reasons


def test_an_attempt_that_starts_before_the_decision_is_reported() -> None:
    reasons = ds._temporal_reasons(
        _feature(decision_timestamp=NOW + timedelta(minutes=2)),
        _outcome(
            NOW + timedelta(minutes=1),
            NOW + timedelta(minutes=3),
            NOW + timedelta(minutes=4),
        ),
        now=NOW + timedelta(minutes=5),
    )

    assert "attempt_started_before_decision" in reasons


def test_an_outcome_recorded_after_the_cutoff_is_reported() -> None:
    reasons = ds._temporal_reasons(
        _feature(decision_timestamp=NOW - timedelta(minutes=2)),
        _outcome(
            NOW - timedelta(minutes=1),
            NOW,
            NOW + timedelta(minutes=10),
        ),
        now=NOW,
    )

    assert "outcome_recorded_at_in_future" in reasons


def test_an_event_with_no_attempts_produces_no_rows() -> None:
    rows = ds.diagnostic_export_rows(
        [{"request_id": "req-1", "pre_routing_features": [], "routing_decisions": []}]
    )

    assert rows == []


def test_a_missing_feature_snapshot_is_quarantined() -> None:
    rows = ds.diagnostic_export_rows(
        [{"request_id": "req-1", "pre_routing_features": [None], "routing_decisions": []}]
    )

    assert len(rows) == 1
    assert "feature_snapshot_missing" in str(rows[0])
    assert "outcome_missing" in str(rows[0])


def test_an_invalid_outcome_is_quarantined() -> None:
    rows = ds.diagnostic_export_rows(
        [
            {
                "request_id": "req-1",
                "pre_routing_features": [_snapshot()],
                "routing_decisions": [{"http_status": 999}],
            }
        ]
    )

    assert len(rows) == 1
    assert "outcome_invalid" in str(rows[0])
