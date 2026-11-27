"""Coverage and bias summary from :func:`audit_dataset`.

The audit is what tells an operator whether the telemetry can support a
routing decision at all. Two properties matter most: a failure category that
merely contains the word "timeout" is counted as an explicit timeout while a
transport failure is never promoted to one, and a deployment with no observed
selection is reported as insufficient evidence rather than as a zero rate.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from sabiroute.intelligence import dataset as ds

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _feature(**overrides: Any) -> dict[str, Any]:
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


def _outcome(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "outcome": "success",
        "http_status": 200,
        "selected_deployment": "primary",
        "latency_ms": 120.0,
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "actual_cost_usd": "0.001",
        "attempt_schema_version": "1.1",
        "attempt_started_at": (NOW + timedelta(seconds=1)).isoformat(),
        "attempt_completed_at": (NOW + timedelta(seconds=2)).isoformat(),
        "outcome_recorded_at": (NOW + timedelta(seconds=3)).isoformat(),
    }
    fields.update(overrides)
    return fields


def _event(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "request_id": "req-1",
        "feature_schema_version": "1.1",
        "pre_routing_features": [_feature()],
        "routing_decisions": [_outcome()],
    }
    fields.update(overrides)
    return fields


def test_observed_attempts_are_attributed_to_the_selected_deployment() -> None:
    summary = ds.audit_dataset([_event()])

    assert summary["logical_requests"] == 1
    assert summary["provider_attempts"] == 1
    assert summary["observations_by_deployment"] == {"primary": 1}
    assert summary["deployment_selection_and_eligibility"]["primary"]["selected_attempts"] == 1


def test_attempts_carrying_latency_usage_and_cost_are_counted() -> None:
    summary = ds.audit_dataset([_event()])

    assert summary["label_availability"]["attempts_with_outcome_label"] == 1
    coverage = summary["deployment_selection_and_eligibility"]["primary"]
    assert coverage["outcome_observations"] == 1


def test_an_explicit_timeout_category_is_counted_separately() -> None:
    summary = ds.audit_dataset([_event(routing_decisions=[_outcome(failure_category="timeout")])])

    assert summary["explicit_timeout_attempts"] == 1


def test_a_transport_failure_is_not_promoted_to_a_timeout() -> None:
    summary = ds.audit_dataset(
        [_event(routing_decisions=[_outcome(failure_category="transport")])]
    )

    assert summary["explicit_timeout_attempts"] == 0
    assert summary["transport_failures_not_inferred_as_timeouts"] == 1


def test_a_deployment_with_no_observations_is_flagged_as_insufficient() -> None:
    summary = ds.audit_dataset([_event()], low_sample_threshold=10)

    coverage = summary["deployment_selection_and_eligibility"]["primary"]
    assert coverage["insufficient_evidence"] is True


def test_non_mapping_outcomes_are_skipped_without_failing_the_audit() -> None:
    summary = ds.audit_dataset([_event(routing_decisions=[None])])

    assert summary["observations_by_deployment"] == {}


def test_an_empty_audit_reports_no_rates() -> None:
    summary = ds.audit_dataset([])

    assert summary["logical_requests"] == 0
    assert summary["time_range"] == {"start": None, "end": None}
