"""Every integrity issue :func:`_audit_integrity` can record.

The audit's job is to name the defect rather than to raise or to trust the
record. Each test drives one stored shape into one issue key so that a
regression in any single check is visible as itself, not as a changed total.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sabiroute.intelligence import dataset as ds

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _event(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "request_id": "req-1",
        "created_at": NOW.isoformat(),
        "pre_routing_features": [],
        "routing_decisions": [],
    }
    fields.update(overrides)
    return fields


def _feature(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "feature_schema_version": "1.1",
        "logical_request_id": "req-1",
        "attempt_number": 1,
        "decision_timestamp": NOW.isoformat(),
        "request_type": "chat",
        "routing_policy_id": "policy",
        "routing_strategy": "priority",
        "routing_strategy_version": "v1",
        "candidate_deployments": ["primary"],
        "capability_eligible_deployments": ["primary"],
        "health_eligible_deployments": ["primary"],
    }
    fields.update(overrides)
    return fields


def _outcome(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "attempt_schema_version": "1.1",
        "attempt_started_at": NOW.isoformat(),
        "attempt_completed_at": (NOW + timedelta(seconds=1)).isoformat(),
        "outcome_recorded_at": (NOW + timedelta(seconds=2)).isoformat(),
        "outcome": "success",
        "selected_deployment": "primary",
        "fallback_attempt": 1,
        "request_id": "req-1",
        "logical_request_id": "req-1",
    }
    fields.update(overrides)
    return fields


def _issues(event: dict[str, Any]) -> dict[str, int]:
    return ds._audit_integrity([event])["issues"]


# --- request-level checks -------------------------------------------------


def test_a_record_without_a_request_id_is_reported() -> None:
    assert _issues(_event(request_id=""))["missing_request_id"] == 1


def test_an_unparseable_request_timestamp_is_reported() -> None:
    assert _issues(_event(created_at="not-a-date"))["invalid_request_timestamp"] == 1


def test_a_naive_request_timestamp_is_reported() -> None:
    issues = _issues(_event(created_at=datetime(2026, 1, 1, 12, 0)))

    assert issues["naive_request_timestamp"] == 1


def test_a_future_request_timestamp_is_reported() -> None:
    issues = _issues(_event(created_at=(datetime.now(UTC) + timedelta(days=1)).isoformat()))

    assert issues["future_request_timestamp"] == 1


def test_a_feature_record_that_is_not_a_mapping_is_reported() -> None:
    assert _issues(_event(pre_routing_features=[123]))["invalid_feature_record"] == 1


def test_a_feature_record_that_fails_schema_validation_is_reported() -> None:
    issues = _issues(
        _event(pre_routing_features=[{"feature_schema_version": "1.1", "bogus": 1}])
    )

    assert issues["invalid_feature_schema"] == 1


def test_a_feature_schema_that_disagrees_with_the_event_is_reported() -> None:
    event = _event(
        feature_schema_version="1.1",
        pre_routing_features=[_feature(feature_schema_version="1.0")],
    )

    assert _issues(event)["feature_schema_version_mismatch"] == 1


def test_a_feature_bound_to_another_request_is_reported() -> None:
    issues = _issues(_event(pre_routing_features=[_feature(logical_request_id="other")]))

    assert issues["feature_request_id_mismatch"] == 1


def test_a_decision_before_the_request_was_created_is_reported() -> None:
    event = _event(
        created_at=(NOW + timedelta(minutes=5)).isoformat(),
        pre_routing_features=[_feature(decision_timestamp=NOW.isoformat())],
    )

    assert _issues(event)["decision_precedes_request_creation"] == 1


def test_out_of_order_decision_timestamps_are_reported() -> None:
    event = _event(
        pre_routing_features=[
            _feature(attempt_number=1, decision_timestamp=NOW.isoformat()),
            _feature(
                attempt_number=2,
                decision_timestamp=(NOW - timedelta(minutes=1)).isoformat(),
            ),
        ]
    )

    assert _issues(event)["out_of_order_decision_timestamp"] == 1


# --- measured-strategy provenance -----------------------------------------


def _measured(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "routing_strategy": "measured",
        "historical_summary_as_of": NOW.isoformat(),
    }
    fields.update(overrides)
    return fields


def test_a_measured_attempt_without_a_cutoff_is_reported() -> None:
    feature = _feature(**_measured(historical_summary_as_of=None))

    assert _issues(_event(pre_routing_features=[feature]))[
        "missing_historical_summary_as_of"
    ] == 1


def test_a_naive_measured_cutoff_is_reported() -> None:
    feature = _feature(
        **_measured(historical_summary_as_of=datetime(2026, 1, 1, 12, 0))
    )

    assert _issues(_event(pre_routing_features=[feature]))[
        "naive_historical_summary_as_of"
    ] == 1


def test_a_measured_cutoff_that_differs_from_the_decision_is_reported() -> None:
    feature = _feature(
        **_measured(
            decision_timestamp=NOW.isoformat(),
            historical_summary_as_of=(NOW - timedelta(minutes=5)).isoformat(),
        )
    )

    assert _issues(_event(pre_routing_features=[feature]))[
        "historical_summary_cutoff_mismatch"
    ] == 1


def test_a_future_measured_cutoff_is_reported() -> None:
    future = datetime.now(UTC) + timedelta(minutes=30)
    feature = _feature(
        **_measured(
            decision_timestamp=future.isoformat(),
            historical_summary_as_of=future.isoformat(),
        )
    )

    assert _issues(_event(pre_routing_features=[feature]))[
        "future_historical_summary_as_of"
    ] == 1


def test_a_measured_candidate_with_samples_but_no_observation_is_reported() -> None:
    feature = _feature(
        **_measured(
            deterministic_score_context=[
                {
                    "deployment": "primary",
                    "reliability_samples": 2,
                    "latency_samples": 3,
                    "reliability_state_scope_id": "scope-r",
                    "latency_state_scope_id": "scope-l",
                }
            ]
        )
    )

    issues = _issues(_event(pre_routing_features=[feature]))

    assert issues["missing_latest_reliability_observation"] == 1
    assert issues["missing_latest_latency_observation"] == 1


# --- outcome-level checks -------------------------------------------------


def test_an_outcome_paired_with_a_non_mapping_feature_is_reported() -> None:
    event = _event(pre_routing_features=["bad"], routing_decisions=[_outcome()])

    issues = _issues(event)

    assert issues["outcome_with_invalid_feature_snapshot"] == 1


def test_an_outcome_without_a_selection_is_reported() -> None:
    outcome = _outcome()
    outcome.pop("selected_deployment")
    event = _event(pre_routing_features=[_feature()], routing_decisions=[outcome])

    assert _issues(event)["missing_selected_deployment"] == 1


def test_a_non_list_outcome_eligible_set_is_reported() -> None:
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[_outcome(eligible_deployments="primary")],
    )

    assert _issues(event)["invalid_outcome_eligible_set"] == 1


def test_a_selection_outside_the_outcome_eligible_set_is_reported() -> None:
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[_outcome(eligible_deployments=["secondary"])],
    )

    assert _issues(event)["selected_deployment_not_outcome_eligible"] == 1


def test_a_boolean_attempt_number_is_reported() -> None:
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[_outcome(fallback_attempt=True)],
    )

    assert _issues(event)["invalid_fallback_attempt_number"] == 1


def test_an_outcome_bound_to_another_logical_request_is_reported() -> None:
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[_outcome(logical_request_id="other")],
    )

    assert _issues(event)["outcome_logical_request_id_mismatch"] == 1


def test_an_unknown_attempt_schema_is_reported() -> None:
    event = _event(
        pre_routing_features=[_feature(feature_schema_version="1.0")],
        routing_decisions=[_outcome(attempt_schema_version="9.9")],
    )

    assert _issues(event)["unsupported_attempt_schema_version"] == 1


def test_a_naive_attempt_timestamp_is_reported() -> None:
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[
            _outcome(attempt_started_at=datetime(2026, 1, 1, 12, 0))
        ],
    )

    assert _issues(event)["naive_attempt_started_at"] == 1


def test_a_future_attempt_timestamp_is_reported() -> None:
    future = datetime.now(UTC) + timedelta(days=1)
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[
            _outcome(
                attempt_started_at=future.isoformat(),
                attempt_completed_at=(future + timedelta(seconds=1)).isoformat(),
                outcome_recorded_at=(future + timedelta(seconds=2)).isoformat(),
            )
        ],
    )

    assert _issues(event)["future_attempt_started_at"] == 1


def test_out_of_order_attempt_timestamps_are_reported() -> None:
    event = _event(
        pre_routing_features=[_feature()],
        routing_decisions=[
            _outcome(
                attempt_started_at=(NOW + timedelta(minutes=2)).isoformat(),
                attempt_completed_at=(NOW + timedelta(minutes=1)).isoformat(),
                outcome_recorded_at=(NOW + timedelta(minutes=3)).isoformat(),
            )
        ],
    )

    assert _issues(event)["attempt_timestamp_order"] == 1


def test_an_attempt_that_started_before_the_decision_is_reported() -> None:
    event = _event(
        pre_routing_features=[
            _feature(decision_timestamp=(NOW + timedelta(minutes=10)).isoformat())
        ],
        routing_decisions=[
            _outcome(
                attempt_started_at=NOW.isoformat(),
                attempt_completed_at=(NOW + timedelta(minutes=1)).isoformat(),
                outcome_recorded_at=(NOW + timedelta(minutes=2)).isoformat(),
            )
        ],
    )

    assert _issues(event)["attempt_started_before_decision"] == 1


def test_an_unparseable_decision_timestamp_is_not_trusted_for_ordering() -> None:
    event = _event(
        pre_routing_features=[_feature(decision_timestamp="not-a-date")],
        routing_decisions=[_outcome()],
    )

    issues = _issues(event)

    # The feature itself is unreadable, so it is reported as such and the
    # outcome's ordering check cannot manufacture a verdict from it.
    assert issues["invalid_feature_schema"] == 1
    assert "attempt_started_before_decision" not in issues


def test_a_duplicate_request_id_is_counted() -> None:
    events = [_event(), _event()]

    assert ds._audit_integrity(events)["issues"]["duplicate_request_id"] == 1
