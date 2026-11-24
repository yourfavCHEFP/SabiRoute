"""Pairing checks inside the diagnostic export.

A feature snapshot and its outcome are only usable together if they agree on
which request and attempt they describe, and if the selected deployment is
actually present in every eligibility set the decision recorded. Each
disagreement is recorded as a named reason rather than a silent drop.
"""
from __future__ import annotations

from datetime import UTC, datetime
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


def _rows(feature: dict[str, Any], outcome: dict[str, Any]) -> list[dict[str, Any]]:
    return ds.diagnostic_export_rows(
        [
            {
                "request_id": "req-1",
                "pre_routing_features": [feature],
                "routing_decisions": [outcome],
            }
        ]
    )


def _outcome(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "outcome": "success",
        "http_status": 200,
        "selected_deployment": "primary",
        "attempt_schema_version": "1.1",
        "eligible_deployments": ["primary"],
    }
    fields.update(overrides)
    return fields


def test_a_feature_for_another_request_is_quarantined() -> None:
    rows = _rows(_snapshot(logical_request_id="other"), _outcome())

    assert "feature_request_id_mismatch" in str(rows[0])


def test_a_feature_for_another_attempt_is_quarantined() -> None:
    rows = _rows(_snapshot(attempt_number=2), _outcome())

    assert "attempt_number_mismatch" in str(rows[0])


def test_empty_eligibility_sets_are_reported_individually() -> None:
    rows = _rows(_snapshot(), _outcome())

    record = str(rows[0])
    assert "candidate_set_missing_or_empty" in record
    assert "capability_eligible_set_missing_or_empty" in record
    assert "eligible_set_missing_or_empty" in record


def test_a_selection_outside_the_candidate_set_is_reported() -> None:
    feature = _snapshot()
    feature["candidate_deployments"] = ["other"]
    feature["capability_eligible_deployments"] = ["other"]
    feature["health_eligible_deployments"] = ["other"]

    rows = _rows(feature, _outcome())

    assert "selected_deployment_not_candidate" in str(rows[0])
