"""Residual branches of the dataset module's diagnostic and audit paths.

These are the answers the module gives to stored evidence that is present but
imperfect: a measured-strategy cutoff that does not line up, a feature body
that fails validation, an outcome whose eligible set is malformed, and a
database URL in the plain form Postgres clients still hand out.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from sabiroute.intelligence import dataset as ds

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _feature_fields(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "feature_schema_version": "1.1",
        "logical_request_id": "req-1",
        "attempt_number": 1,
        "decision_timestamp": NOW,
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


def _feature(**overrides: Any) -> Any:
    return ds.PreRoutingFeatureSnapshot.model_validate(_feature_fields(**overrides))


def _outcome(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "attempt_schema_version": "1.1",
        "attempt_started_at": NOW.isoformat(),
        "attempt_completed_at": (NOW + timedelta(seconds=1)).isoformat(),
        "outcome_recorded_at": (NOW + timedelta(seconds=2)).isoformat(),
        "outcome": "success",
        "selected_deployment": "primary",
    }
    fields.update(overrides)
    return fields


# --- measured-strategy temporal reasons -----------------------------------


def test_a_measured_cutoff_that_differs_from_the_decision_is_reported() -> None:
    reasons = ds._temporal_reasons(
        _feature(
            routing_strategy="measured",
            decision_timestamp=NOW,
            historical_summary_as_of=NOW - timedelta(minutes=5),
        ),
        _outcome(),
        now=NOW + timedelta(minutes=10),
    )

    assert "historical_summary_cutoff_mismatch" in reasons


def test_a_measured_cutoff_in_the_future_is_reported() -> None:
    future = NOW + timedelta(minutes=30)

    reasons = ds._temporal_reasons(
        _feature(
            routing_strategy="measured",
            decision_timestamp=future,
            historical_summary_as_of=future,
        ),
        _outcome(
            attempt_started_at=(future + timedelta(seconds=1)).isoformat(),
            attempt_completed_at=(future + timedelta(seconds=2)).isoformat(),
            outcome_recorded_at=(future + timedelta(seconds=3)).isoformat(),
        ),
        now=NOW,
    )

    assert "historical_summary_cutoff_in_future" in reasons


def test_a_candidate_claiming_samples_without_an_observation_is_reported() -> None:
    context = [
        {
            "deployment": "primary",
            "reliability_samples": 3,
            "latency_samples": 2,
            "reliability_state_scope_id": "scope-r",
            "latency_state_scope_id": "scope-l",
        }
    ]

    reasons = ds._temporal_reasons(
        _feature(
            routing_strategy="measured",
            decision_timestamp=NOW,
            historical_summary_as_of=NOW,
            deterministic_score_context=context,
        ),
        _outcome(),
        now=NOW + timedelta(minutes=10),
    )

    assert "latest_reliability_observation_missing" in reasons
    assert "latest_latency_observation_missing" in reasons


# --- diagnostic quarantine reasons ----------------------------------------


def _diagnostic_row(feature: Any, outcome: Any) -> dict[str, Any]:
    rows = ds.diagnostic_export_rows(
        [
            {
                "request_id": "req-1",
                "pre_routing_features": [feature],
                "routing_decisions": [outcome] if outcome is not None else [],
            }
        ]
    )
    return rows[0]


def test_a_feature_body_that_fails_validation_is_quarantined() -> None:
    row = _diagnostic_row({"feature_schema_version": "1.1", "unexpected": True}, _outcome())

    assert "feature_snapshot_invalid" in row["exclusion_reasons"]


def test_a_non_mapping_feature_is_quarantined() -> None:
    row = _diagnostic_row("not-a-mapping", _outcome())

    assert "feature_snapshot_invalid" in row["exclusion_reasons"]


def test_a_feature_schema_that_disagrees_with_the_event_is_quarantined() -> None:
    rows = ds.diagnostic_export_rows(
        [
            {
                "request_id": "req-1",
                "feature_schema_version": "1.1",
                "pre_routing_features": [_feature_fields(feature_schema_version="1.0")],
                "routing_decisions": [_outcome()],
            }
        ]
    )

    assert "feature_schema_version_mismatch" in rows[0]["exclusion_reasons"]


def test_an_outcome_without_a_selected_deployment_is_quarantined() -> None:
    outcome = _outcome()
    outcome.pop("selected_deployment")

    row = _diagnostic_row(_feature_fields(), outcome)

    assert "selected_deployment_missing" in row["exclusion_reasons"]


def test_a_non_list_outcome_eligible_set_is_quarantined() -> None:
    row = _diagnostic_row(
        _feature_fields(), _outcome(eligible_deployments="primary")
    )

    assert "outcome_eligible_set_invalid" in row["exclusion_reasons"]


def test_a_selection_outside_the_outcome_eligible_set_is_quarantined() -> None:
    row = _diagnostic_row(
        _feature_fields(), _outcome(eligible_deployments=["secondary"])
    )

    assert "selected_deployment_not_outcome_eligible" in row["exclusion_reasons"]


def test_an_outcome_without_a_label_is_quarantined() -> None:
    row = _diagnostic_row(_feature_fields(), _outcome(outcome=None))

    assert "outcome_label_missing_or_invalid" in row["exclusion_reasons"]


# --- audit skips and usage reading ----------------------------------------


def test_the_audit_skips_a_feature_record_that_is_not_a_mapping() -> None:
    report = ds.audit_dataset(
        [
            {
                "request_id": "req-1",
                "pre_routing_features": ["nope"],
                "routing_decisions": [],
            }
        ]
    )

    assert isinstance(report, dict)
    # The event itself is still accounted for...
    assert report["logical_requests"] == 1
    assert report["stored_feature_schema_versions"] == {"<missing>": 1}
    # ...but the non-mapping feature contributes no observation of its own.
    assert report["observations_by_deployment"] == {}


def test_usage_reads_rewrite_plain_postgres_urls(
    monkeypatch: Any,
) -> None:
    seen: list[str] = []

    class _Result:
        def mappings(self) -> _Result:
            return self

        def all(self) -> list[Any]:
            return []

    class _Connection:
        def __enter__(self) -> _Connection:
            return self

        def __exit__(self, *exc_info: object) -> bool:
            return False

        def execute(self, *_args: Any, **_kwargs: Any) -> _Result:
            return _Result()

    class _Engine:
        def connect(self) -> _Connection:
            return _Connection()

        def dispose(self) -> None:
            seen.append("dispose")

    def fake_create_engine(url: str, **_kwargs: Any) -> _Engine:
        seen.append(url)
        return _Engine()

    monkeypatch.setattr(ds, "create_engine", fake_create_engine)
    monkeypatch.setattr(ds, "MetaData", lambda: object())
    monkeypatch.setattr(ds, "Table", lambda *_a, **_k: SimpleNamespace(c={}))
    monkeypatch.setattr(ds, "select", lambda *_a: object())

    assert ds.read_usage_events("postgresql://user@host/db") == []
    assert ds.read_usage_events("postgres://user@host/db") == []

    assert seen[0] == "postgresql+psycopg://user@host/db"
    assert seen[2] == "postgresql+psycopg://user@host/db"
