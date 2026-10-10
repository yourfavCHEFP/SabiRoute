from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect

from sabiroute.capabilities import Capability
from sabiroute.intelligence.dataset import (
    FEATURE_SCHEMA_VERSION,
    DatasetExportBlocked,
    PreRoutingFeatureSnapshot,
    assess_phase13_readiness,
    audit_dataset,
    chronological_split,
    diagnostic_export,
    diagnostic_export_rows,
    make_pre_routing_snapshot,
    read_usage_events,
    readiness_report,
    training_candidate_export,
    write_diagnostic_export,
    write_training_candidate_export,
)
from sabiroute.security.store import PostgresApiKeyStore


def _decision(deployment: str = "provider-a") -> SimpleNamespace:
    score = SimpleNamespace(
        deployment=deployment,
        score=0.8,
        success_rate=1.0,
        reliability_samples=5,
        average_latency_ms=120.0,
        latency_normalized=0.75,
        latency_samples=5,
        latest_reliability_observation=None,
        latest_latency_observation=None,
        reliability_state_scope_id=None,
        latency_state_scope_id=None,
    )
    explanation = SimpleNamespace(
        candidate_scores=(score,),
        required_capabilities=(Capability.CHAT,),
        candidate_deployments=("provider-a", "provider-b"),
        capability_eligible_deployments=("provider-a", "provider-b"),
        eligible_deployments=("provider-a", "provider-b"),
        capability_excluded_deployments={},
        unhealthy_deployments=(),
        scoring_policy_version="deterministic-v1",
        scoring_as_of=datetime(2026, 1, 1, tzinfo=UTC),
        scoring_weights={"reliability": 0.7, "latency": 0.3},
        scoring_fallback_reason=None,
    )
    return SimpleNamespace(explanation=explanation)


def _feature(request_id: str, attempt: int, timestamp: str) -> dict[str, object]:
    return {
        "feature_schema_version": "1.0",
        "logical_request_id": request_id,
        "attempt_number": attempt,
        "decision_timestamp": timestamp,
        "request_type": "chat",
        "requested_alias": "research",
        "routing_policy_id": "research",
        "candidate_deployments": ["provider-a", "provider-b"],
        "capability_eligible_deployments": ["provider-a", "provider-b"],
        "health_eligible_deployments": ["provider-a", "provider-b"],
        "required_capabilities": ["chat"],
        "streaming": False,
        "tool_use": False,
        "response_format_category": "none",
        "multimodal": False,
        "estimated_input_tokens": 33,
        "request_size_bytes": 129,
        "requested_max_output_tokens": 128,
        "context_size_requirement": None,
        "routing_strategy": "measured",
        "routing_strategy_version": "deterministic-v1",
        "deterministic_score_context": [],
        "selection_propensity": None,
        "experiment_id": None,
    }


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _versioned_attempt_event(
    request_id: str, observations: list[tuple[str, str]]
) -> dict[str, object]:
    """Create isolated synthetic telemetry for readiness unit tests only."""
    features = []
    outcomes = []
    for attempt_number, (timestamp, outcome) in enumerate(observations, start=1):
        features.append(
            _feature(request_id, attempt_number, timestamp)
            | {
                "feature_schema_version": "1.1",
                "historical_summary_as_of": timestamp,
            }
        )
        day = timestamp[:10]
        outcomes.append(
            {
                "request_id": request_id,
                "logical_request_id": request_id,
                "fallback_attempt": attempt_number,
                "selected_deployment": "provider-a",
                "outcome": outcome,
                "attempt_schema_version": "1.1",
                "attempt_started_at": f"{day}T00:00:00.001000+00:00",
                "attempt_completed_at": f"{day}T00:00:00.500000+00:00",
                "outcome_recorded_at": f"{day}T00:00:00.501000+00:00",
            }
        )
    return {
        "request_id": request_id,
        "feature_schema_version": "1.1",
        "pre_routing_features": features,
        "routing_decisions": outcomes,
    }


def test_snapshot_is_versioned_allowlisted_and_content_free() -> None:
    snapshot = make_pre_routing_snapshot(
        logical_request_id="00000000-0000-0000-0000-000000000001",
        attempt_number=1,
        decision_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        requested_alias="research",
        request_type="chat",
        routing_policy_id="research",
        routing_strategy="measured",
        messages=[{"role": "user", "content": "do-not-persist-this-prompt"}],
        options={"stream": False, "max_tokens": 128, "api_key": "sk-sensitive"},
        decision=_decision(),
    )
    encoded = json.dumps(snapshot)
    assert snapshot["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert snapshot["historical_summary_as_of"] == snapshot["decision_timestamp"]
    assert "do-not-persist-this-prompt" not in encoded
    assert "sk-sensitive" not in encoded
    assert "api_key" not in encoded
    assert "outcome" not in snapshot
    assert "actual_latency_ms" not in snapshot
    assert snapshot["estimated_input_tokens"] is not None


def test_snapshot_redacts_secret_like_requested_alias() -> None:
    feature = PreRoutingFeatureSnapshot.model_validate(
        _feature("logical-1", 1, "2026-01-01T00:00:00+00:00")
        | {"requested_alias": "sr_live_abc123secret"}
    )
    assert feature.requested_alias == "[redacted]"


def test_schema_version_is_enforced_and_extra_fields_rejected() -> None:
    base = _feature("logical-1", 1, "2026-01-01T00:00:00+00:00")
    with pytest.raises(ValidationError):
        PreRoutingFeatureSnapshot.model_validate(base | {"feature_schema_version": "2.0"})
    with pytest.raises(ValidationError):
        PreRoutingFeatureSnapshot.model_validate(base | {"prompt": "secret"})


def test_export_separates_features_from_outcomes_and_omits_secrets() -> None:
    rows = diagnostic_export_rows(
        [
            {
                "request_id": "logical-1",
                "key_id": "do-not-export-key-id",
                "project_id": "do-not-export-project",
                "pre_routing_features": [_feature("logical-1", 1, "2026-01-01T00:00:00+00:00")],
                "routing_decisions": [
                    {
                        "selected_deployment": "provider-a",
                        "outcome": "success",
                        "http_status": 200,
                        "failure_category": None,
                        "latency_ms": 123.0,
                        "usage": {"prompt_tokens": 20, "completion_tokens": 10, "secret": "omit"},
                        "actual_cost_usd": None,
                        "prompt": "omit this prompt",
                        "api_key": "omit this credential",
                    }
                ],
            }
        ]
    )
    rendered = json.dumps(rows)
    assert rows[0]["pre_routing_features"] is not None
    assert rows[0]["post_execution_outcome"]["outcome"] == "success"
    assert '"prompt":' not in rendered
    assert "api_key" not in rendered
    assert "do-not-export-key-id" not in rendered
    assert "do-not-export-project" not in rendered
    assert "secret" not in rendered


def test_time_split_keeps_fallback_attempts_in_same_logical_group() -> None:
    rows = [
        {
            "logical_request_id": "r1",
            "decision_timestamp": "2026-01-01T00:00:00+00:00",
            "attempt": 1,
        },
        {
            "logical_request_id": "r1",
            "decision_timestamp": "2026-01-01T00:00:01+00:00",
            "attempt": 2,
        },
        {
            "logical_request_id": "r2",
            "decision_timestamp": "2026-01-02T00:00:00+00:00",
            "attempt": 1,
        },
        {
            "logical_request_id": "r3",
            "decision_timestamp": "2026-01-03T00:00:00+00:00",
            "attempt": 1,
        },
    ]
    train, evaluation = chronological_split(rows, evaluation_fraction=0.34)
    train_ids = {row["logical_request_id"] for row in train}
    evaluation_ids = {row["logical_request_id"] for row in evaluation}
    assert train_ids.isdisjoint(evaluation_ids)
    assert {row["logical_request_id"] for row in train} == {"r1", "r2"}
    assert {row["logical_request_id"] for row in evaluation} == {"r3"}
    assert len([row for row in train if row["logical_request_id"] == "r1"]) == 2


def test_time_split_requires_multiple_logical_requests() -> None:
    with pytest.raises(ValueError, match="At least two"):
        chronological_split(
            [
                {
                    "logical_request_id": "only",
                    "decision_timestamp": "2026-01-01T00:00:00+00:00",
                }
            ]
        )


def test_time_split_rejects_naive_decision_timestamps() -> None:
    with pytest.raises(ValueError, match="timezone-aware decision timestamp"):
        chronological_split(
            [
                {
                    "logical_request_id": "r1",
                    "decision_timestamp": "2026-01-01T00:00:00",
                },
                {
                    "logical_request_id": "r2",
                    "decision_timestamp": "2026-01-02T00:00:00+00:00",
                },
            ]
        )


def test_time_split_moves_overlapping_fallback_group_to_evaluation() -> None:
    rows = [
        {"logical_request_id": "r1", "decision_timestamp": "2026-01-01T00:00:00+00:00"},
        {
            "logical_request_id": "r2",
            "decision_timestamp": "2026-01-02T00:00:00+00:00",
            "attempt": 1,
        },
        {
            "logical_request_id": "r2",
            "decision_timestamp": "2026-01-04T00:00:00+00:00",
            "attempt": 2,
        },
        {"logical_request_id": "r3", "decision_timestamp": "2026-01-03T00:00:00+00:00"},
    ]
    train, evaluation = chronological_split(rows, evaluation_fraction=0.25)
    assert {row["logical_request_id"] for row in train} == {"r1"}
    assert {row["logical_request_id"] for row in evaluation} == {"r2", "r3"}


def test_time_split_rejects_request_groups_that_prevent_a_safe_boundary() -> None:
    rows = [
        {"logical_request_id": "r1", "decision_timestamp": "2026-01-01T00:00:00+00:00"},
        {"logical_request_id": "r1", "decision_timestamp": "2026-01-03T00:00:00+00:00"},
        {"logical_request_id": "r2", "decision_timestamp": "2026-01-02T00:00:00+00:00"},
    ]
    with pytest.raises(ValueError, match="overlap in time"):
        chronological_split(rows, evaluation_fraction=0.5)


def test_audit_counts_observations_fallback_missingness_and_selection_bias() -> None:
    events = [
        {
            "request_id": "r1",
            "pre_routing_features": [
                _feature("r1", 1, "2026-01-01T00:00:00+00:00"),
                _feature("r1", 2, "2026-01-01T00:00:02+00:00"),
            ],
            "routing_decisions": [
                {
                    "selected_deployment": "provider-a",
                    "outcome": "failure",
                    "http_status": 503,
                    "failure_category": "server",
                },
                {"selected_deployment": "provider-b", "outcome": "success", "http_status": 200},
            ],
        },
        {
            "request_id": "r2",
            "pre_routing_features": [
                _feature("r2", 1, "2026-01-02T00:00:00+00:00")
                | {"health_eligible_deployments": ["provider-a", "provider-b"], "streaming": None}
            ],
            "routing_decisions": [
                {"selected_deployment": "provider-a", "outcome": "success", "http_status": 200}
            ],
        },
    ]
    report = audit_dataset(events)
    assert report["logical_requests"] == 2
    assert report["provider_attempts"] == 3
    assert report["fallback_logical_requests"] == 1
    assert report["success_failure_counts"] == {"failure": 1, "success": 2}
    assert report["failure_categories"] == {"server": 1}
    assert report["feature_missingness"]["streaming"]["missing"] == 1
    assert report["selection_bias"]["historical_data_is_observational"] is True
    assert report["selection_bias"]["unselected_candidates_have_counterfactual_outcomes"] is False
    assert report["deployment_selection_and_eligibility"]["provider-b"]["eligible_requests"] == 2
    assert report["deployment_selection_and_eligibility"]["provider-a"]["selected_attempts"] == 2
    assert report["integrity_checks"]["valid"] is True
    assert report["request_shape_coverage"]["candidate_set_sizes"] == {2: 3}
    assert report["eligibility_overlap"]["jointly_eligible_decision_opportunities"] == {
        "provider-a|provider-b": 3
    }
    assert report["outcome_availability"]["outcome_timestamp"] == report[
        "integrity_checks"
    ]["timestamps"]["outcome_recorded_at"]


def test_audit_flags_snapshot_attempt_and_selected_deployment_mismatches() -> None:
    feature = _feature("r1", 2, "2026-01-01T00:00:00+00:00")
    event = {
        "request_id": "r1",
        "pre_routing_features": [feature],
        "routing_decisions": [
            {
                "selected_deployment": "not-eligible",
                "fallback_attempt": 2,
                "outcome": "success",
            }
        ],
    }

    integrity = audit_dataset([event])["integrity_checks"]

    assert integrity["valid"] is False
    assert integrity["issues"] == {
        "attempt_number_mismatch": 1,
        "fallback_attempt_number_mismatch": 1,
        "selected_deployment_not_candidate": 1,
        "selected_deployment_not_capability_eligible": 1,
        "selected_deployment_not_eligible": 1,
    }
    assert integrity["unselected_candidates_given_outcomes"] is False


@pytest.mark.parametrize(
    ("field", "issue", "reason"),
    [
        (
            "candidate_deployments",
            "selected_deployment_not_candidate",
            "selected_deployment_not_candidate",
        ),
        (
            "capability_eligible_deployments",
            "selected_deployment_not_capability_eligible",
            "selected_deployment_not_capability_eligible",
        ),
        (
            "health_eligible_deployments",
            "selected_deployment_not_eligible",
            "selected_deployment_not_eligible",
        ),
    ],
)
def test_audit_and_candidate_export_require_all_eligibility_sets(
    field: str, issue: str, reason: str
) -> None:
    event = _versioned_attempt_event(
        "eligibility-check", [("2026-01-01T00:00:00+00:00", "success")]
    )
    event["pre_routing_features"][0][field] = ["provider-b"]  # type: ignore[index]

    audit = audit_dataset([event])
    row = diagnostic_export_rows([event])[0]

    assert audit["integrity_checks"]["valid"] is False
    assert audit["integrity_checks"]["issues"][issue] == 1
    assert reason in row["exclusion_reasons"]
    assert row["eligibility_status"] == "ineligible"
    with pytest.raises(DatasetExportBlocked):
        training_candidate_export([event])


@pytest.mark.parametrize(
    ("mutation", "reason", "linkage_status"),
    [
        ("mismatched_request_id", "outcome_request_id_mismatch", "mismatch"),
        ("missing_request_ids", "outcome_request_id_unavailable", "unverified"),
        ("mismatched_attempt", "fallback_attempt_number_mismatch", "mismatch"),
        ("missing_attempt", "outcome_attempt_number_unavailable", "unverified"),
    ],
)
def test_diagnostic_linkage_is_checked_before_safe_outcome_projection(
    mutation: str, reason: str, linkage_status: str
) -> None:
    event = _versioned_attempt_event(
        "linkage-check", [("2026-01-01T00:00:00+00:00", "success")]
    )
    outcome = event["routing_decisions"][0]  # type: ignore[index]
    if mutation == "mismatched_request_id":
        outcome["request_id"] = "different-request"  # type: ignore[index]
    elif mutation == "missing_request_ids":
        outcome.pop("request_id")  # type: ignore[union-attr]
        outcome.pop("logical_request_id")  # type: ignore[union-attr]
    elif mutation == "mismatched_attempt":
        outcome["fallback_attempt"] = 2  # type: ignore[index]
    else:
        outcome.pop("fallback_attempt")  # type: ignore[union-attr]

    row = diagnostic_export_rows([event])[0]
    rendered = json.dumps(row)

    assert reason in row["exclusion_reasons"]
    assert row["request_attempt_linkage_status"] == linkage_status
    assert "different-request" not in rendered
    assert "request_id" not in row["post_execution_outcome"]
    assert "logical_request_id" not in row["post_execution_outcome"]
    assert "fallback_attempt" not in row["post_execution_outcome"]
    with pytest.raises(DatasetExportBlocked):
        training_candidate_export([event])


def test_audit_flags_future_snapshot_and_missing_attempt_label() -> None:
    report = audit_dataset(
        [
            {
                "request_id": "r1",
                "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                "feature_schema_version": "1.0",
                "pre_routing_features": [
                    _feature("r1", 1, "2099-01-01T00:00:00+00:00")
                ],
                "routing_decisions": [
                    {
                        "selected_deployment": "provider-a",
                        "fallback_attempt": 1,
                        "outcome": None,
                    }
                ],
            }
        ]
    )

    assert report["integrity_checks"]["issues"] == {
        "future_decision_timestamp": 1,
        "invalid_outcome_label": 1,
    }


def test_audit_counts_only_explicit_timeout_categories() -> None:
    events = []
    for request_id, category in (("timeout", "timeout"), ("transport", "transport")):
        events.append(
            {
                "request_id": request_id,
                "pre_routing_features": [
                    _feature(request_id, 1, "2026-01-01T00:00:00+00:00")
                ],
                "routing_decisions": [
                    {
                        "selected_deployment": "provider-a",
                        "fallback_attempt": 1,
                        "outcome": "failure",
                        "failure_category": category,
                    }
                ],
            }
        )

    report = audit_dataset(events)

    assert report["outcome_availability"]["explicit_timeout_count"] == 1
    assert report["outcome_availability"][
        "generic_transport_failures_not_counted_as_timeouts"
    ] == 1


def test_audit_reports_latency_usage_cost_and_schema_gaps() -> None:
    report = audit_dataset(
        [
            {
                "request_id": "r1",
                "pre_routing_features": [
                    _feature("r1", 1, "2026-01-01T00:00:00+00:00")
                ],
                "routing_decisions": [
                    {
                        "selected_deployment": "provider-a",
                        "fallback_attempt": 1,
                        "outcome": "success",
                        "latency_ms": 42.0,
                        "usage": {"prompt_tokens": 5, "completion_tokens": 7},
                        "actual_cost_usd": "0.001",
                    }
                ],
            }
        ]
    )

    assert report["outcome_availability"]["attempts_with_latency"] == 1
    assert report["outcome_availability"]["attempts_with_provider_usage"] == 1
    assert report["outcome_availability"]["attempts_with_actual_cost"] == 1
    assert report["outcome_availability"]["outcome_schema_version"] == {
        "1.1": 0,
        "unavailable_or_legacy": 1,
    }


def test_empty_dataset_does_not_claim_selection_balance_or_missingness_rate() -> None:
    report = audit_dataset([])
    assert report["selection_bias"]["selection_imbalance_detected"] is None
    assert report["feature_missingness"] == {}
    assert report["logical_requests"] == 0
    assert report["provider_attempts"] == 0


def test_phase13_readiness_reports_current_blockers_without_row_threshold() -> None:
    event = {
        "request_id": "legacy-request",
        "pre_routing_features": [
            _feature("legacy-request", 1, "2026-01-01T00:00:00+00:00")
        ],
        "routing_decisions": [
            {"selected_deployment": "provider-a", "outcome": "success"}
        ],
    }
    audit = audit_dataset([event])
    rows = diagnostic_export_rows([event])
    try:
        train, evaluation = chronological_split(rows)
    except ValueError as exc:
        split = {"available": False, "reason": str(exc)}
    else:
        split = {"available": True, "training": len(train), "evaluation": len(evaluation)}

    readiness = assess_phase13_readiness(audit, split)

    assert readiness["status"] == "BLOCKED"
    assert readiness["training_authorized"] is False
    assert readiness["minimum_sample_threshold_applied"] is False
    assert readiness["blockers"] == [
        "temporal_provenance_incomplete",
        "no_outcome_variation",
        "chronological_split_unavailable",
    ]
    assert readiness["observations_by_deployment"] == {"provider-a": 1}


def test_missing_feature_schema_is_not_inferred_as_current_schema() -> None:
    event = _versioned_attempt_event(
        "schema-missing", [("2026-01-01T00:00:00+00:00", "success")]
    )
    event.pop("feature_schema_version")
    event["pre_routing_features"][0].pop("feature_schema_version")  # type: ignore[index]

    row = diagnostic_export_rows([event])[0]
    integrity = audit_dataset([event])["integrity_checks"]

    assert row["feature_schema_version"] is None
    assert "feature_schema_version" not in row["pre_routing_features"]
    assert "feature_schema_version_missing" in row["exclusion_reasons"]
    assert row["temporal_provenance_status"] == "incomplete_or_unknown"
    assert integrity["valid"] is False
    assert integrity["issues"]["missing_feature_schema_version"] == 1
    assert integrity["temporal_provenance"]["verified_attempts"] == 0
    with pytest.raises(DatasetExportBlocked):
        training_candidate_export([event])


def test_legacy_quarantined_records_do_not_claim_chronological_split() -> None:
    events = []
    for request_id, outcome, timestamp in (
        ("legacy-a", "success", "2026-01-01T00:00:00+00:00"),
        ("legacy-b", "failure", "2026-01-02T00:00:00+00:00"),
    ):
        events.append(
            {
                "request_id": request_id,
                "feature_schema_version": "1.0",
                "pre_routing_features": [_feature(request_id, 1, timestamp)],
                "routing_decisions": [
                    {
                        "request_id": request_id,
                        "logical_request_id": request_id,
                        "fallback_attempt": 1,
                        "selected_deployment": "provider-a",
                        "outcome": outcome,
                    }
                ],
            }
        )

    report = readiness_report(events)

    assert all(row["disposition"] == "quarantined" for row in report["diagnostic_rows"])
    assert report["time_split"]["available"] is False
    assert report["time_split"]["eligible_attempt_rows"] == 0
    assert report["time_split"]["excluded_attempt_rows"] == 2
    assert "temporal_provenance_incomplete" in report["readiness"]["blockers"]
    assert "chronological_split_unavailable" in report["readiness"]["blockers"]


def test_audit_time_coverage_ignores_naive_timestamps_without_crashing() -> None:
    events = [
        {
            "request_id": "aware-time",
            "pre_routing_features": [
                _feature("aware-time", 1, "2026-01-01T00:00:00+00:00")
            ],
            "routing_decisions": [],
        },
        {
            "request_id": "naive-time",
            "pre_routing_features": [
                _feature("naive-time", 1, "2026-01-02T00:00:00")
            ],
            "routing_decisions": [],
        },
    ]

    report = audit_dataset(events)

    assert report["time_range"] == {
        "start": "2026-01-01T00:00:00+00:00",
        "end": "2026-01-01T00:00:00+00:00",
    }
    assert report["daily_observations"] == {"2026-01-01": 1}
    assert report["integrity_checks"]["issues"]["naive_decision_timestamp"] == 1


def test_naive_priority_decision_timestamp_is_not_counted_as_verified_provenance() -> None:
    event = _versioned_attempt_event(
        "naive-priority", [("2026-01-01T00:00:00+00:00", "success")]
    )
    feature = event["pre_routing_features"][0]
    feature["routing_strategy"] = "priority"
    feature["decision_timestamp"] = "2026-01-01T00:00:00"

    report = readiness_report([event])
    integrity = report["audit"]["integrity_checks"]
    row = report["diagnostic_rows"][0]

    assert integrity["issues"]["naive_decision_timestamp"] == 1
    assert integrity["temporal_provenance"]["verified_attempts"] == 0
    assert integrity["temporal_provenance"]["unknown_or_unavailable_attempts"] == 1
    assert row["temporal_provenance_status"] == "incomplete_or_unknown"
    assert row["disposition"] == "quarantined"
    assert report["readiness"]["training_authorized"] is False


def test_phase13_invalid_integrity_is_reported_as_a_structural_blocker() -> None:
    event = {
        "request_id": "unmatched",
        "feature_schema_version": "1.1",
        "pre_routing_features": [],
        "routing_decisions": [
            {
                "request_id": "unmatched",
                "logical_request_id": "unmatched",
                "selected_deployment": "provider-a",
                "outcome": "success",
                "fallback_attempt": 1,
                "attempt_schema_version": "1.1",
                "attempt_started_at": "2026-01-01T00:00:00.001000+00:00",
                "attempt_completed_at": "2026-01-01T00:00:00.500000+00:00",
                "outcome_recorded_at": "2026-01-01T00:00:00.501000+00:00",
            }
        ],
    }
    audit = audit_dataset([event])
    readiness = assess_phase13_readiness(audit, {"available": False, "reason": "missing"})

    assert readiness["status"] == "BLOCKED"
    assert "feature_outcome_integrity_failed" in readiness["blockers"]
    assert readiness["request_attempt_consistency"]["invalid_or_missing_records"][
        "outcome_without_feature_snapshot"
    ] == 1
    assert readiness["training_authorized"] is False


def test_phase13_valid_temporal_data_with_only_successes_lacks_target_variation() -> None:
    events = [
        _versioned_attempt_event(
            f"success-{day}",
            [(f"2026-01-0{day}T00:00:00+00:00", "success")],
        )
        for day in (1, 2)
    ]
    audit = audit_dataset(events)
    rows = diagnostic_export_rows(events)
    train, evaluation = chronological_split(rows)
    readiness = assess_phase13_readiness(
        audit,
        {"available": True, "training_rows": len(train), "evaluation_rows": len(evaluation)},
    )

    assert audit["integrity_checks"]["valid"] is True
    assert readiness["schema_and_temporal_provenance"]["verified_attempts"] == 2
    assert readiness["outcome_variation"]["present"] is False
    assert readiness["blockers"] == ["no_outcome_variation"]
    assert readiness["training_authorized"] is False


def test_phase13_varied_labels_without_safe_time_boundary_remain_blocked() -> None:
    events = [
        _versioned_attempt_event(
            "fallback-request",
            [
                ("2026-01-01T00:00:00+00:00", "success"),
                ("2026-01-04T00:00:00+00:00", "failure"),
            ],
        ),
        _versioned_attempt_event(
            "middle-request", [("2026-01-02T00:00:00+00:00", "success")]
        ),
        _versioned_attempt_event(
            "later-request", [("2026-01-03T00:00:00+00:00", "failure")]
        ),
    ]
    audit = audit_dataset(events)
    rows = diagnostic_export_rows(events)
    with pytest.raises(ValueError, match="overlap in time") as error:
        chronological_split(rows)
    readiness = assess_phase13_readiness(
        audit,
        {"available": False, "reason": str(error.value)},
    )

    assert audit["integrity_checks"]["valid"] is True
    assert readiness["outcome_variation"]["present"] is True
    assert readiness["schema_and_temporal_provenance"]["verified_attempts"] == 4
    assert readiness["blockers"] == ["chronological_split_unavailable"]
    assert readiness["training_authorized"] is False


def test_phase13_structural_screen_only_advances_to_human_review() -> None:
    events: list[dict[str, object]] = []
    for index, outcome in enumerate(("success", "failure"), start=1):
        request_id = f"request-{index}"
        decision_time = f"2026-01-0{index}T00:00:00+00:00"
        feature = _feature(request_id, 1, decision_time) | {
            "feature_schema_version": "1.1",
            "historical_summary_as_of": decision_time,
        }
        events.append(
            {
                "request_id": request_id,
                "feature_schema_version": "1.1",
                "pre_routing_features": [feature],
                "routing_decisions": [
                    {
                        "request_id": request_id,
                        "logical_request_id": request_id,
                        "fallback_attempt": 1,
                        "selected_deployment": "provider-a",
                        "outcome": outcome,
                        "attempt_schema_version": "1.1",
                        "attempt_started_at": f"2026-01-0{index}T00:00:00.001000+00:00",
                        "attempt_completed_at": f"2026-01-0{index}T00:00:00.500000+00:00",
                        "outcome_recorded_at": f"2026-01-0{index}T00:00:00.501000+00:00",
                    }
                ],
            }
        )
    audit = audit_dataset(events)
    rows = diagnostic_export_rows(events)
    train, evaluation = chronological_split(rows)
    split = {"available": True, "training": len(train), "evaluation": len(evaluation)}

    readiness = assess_phase13_readiness(audit, split)

    assert readiness["status"] == "READY_FOR_HUMAN_REVIEW"
    assert readiness["blockers"] == []
    assert readiness["training_authorized"] is False
    assert readiness["outcome_variation"]["present"] is True
    assert readiness["status"] == "READY_FOR_HUMAN_REVIEW"
    assert (
        readiness["selection_bias"]["unselected_candidates_have_counterfactual_outcomes"]
        is False
    )
    assert readiness["eligible_candidate_overlap"]["jointly_eligible_decision_opportunities"]


def test_diagnostic_export_is_explicit_and_omits_unapproved_fields(tmp_path: Path) -> None:
    event = {
        "request_id": "r1",
        "pre_routing_features": [_feature("r1", 1, "2026-01-01T00:00:00+00:00")],
        "routing_decisions": [{"selected_deployment": "provider-a", "outcome": "success"}],
        "api_key": "never-export",
    }
    payload = diagnostic_export([event])
    destination = tmp_path / "diagnostic.json"
    write_diagnostic_export([event], destination)
    content = destination.read_text(encoding="utf-8")
    assert payload["export_type"] == "sabiroute-diagnostic-only"
    assert payload["training_authorized"] is False
    assert content.count("never-export") == 0
    decoded = json.loads(content)
    assert decoded["export_type"] == "sabiroute-diagnostic-only"
    assert decoded["records"][0]["diagnostic_only"] is True
    assert decoded["records"][0]["training_candidate"] is False


def test_diagnostic_export_redacts_secret_like_labels_and_quarantines_row() -> None:
    event = _versioned_attempt_event(
        "secret-label", [("2026-01-01T00:00:00+00:00", "success")]
    )
    feature = event["pre_routing_features"][0]  # type: ignore[index]
    outcome = event["routing_decisions"][0]  # type: ignore[index]
    feature["capability_exclusions"] = {  # type: ignore[index]
        "Authorization": ["Bearer authorization-token"],
        "provider-a": [
            "Authorization: Bearer header-token",
            "api_key=sr_live_api-key",
            "DATABASE_URL=postgresql://user:password@db.example:5432/sabiroute",
        ],
    }
    outcome["failure_category"] = "api_key=sk-provider-secret"  # type: ignore[index]

    row = diagnostic_export_rows([event])[0]
    rendered = json.dumps(row)

    for secret in (
        "authorization-token",
        "header-token",
        "sr_live_api-key",
        "user:password@db.example",
        "sk-provider-secret",
    ):
        assert secret not in rendered
    assert "[redacted]" in rendered
    assert row["eligibility_status"] == "unknown"
    assert row["disposition"] == "quarantined"
    assert "sensitive_value_redacted" in row["exclusion_reasons"]


def test_candidate_export_cannot_accept_caller_supplied_readiness(tmp_path: Path) -> None:
    event = {
        "request_id": "blocked",
        "pre_routing_features": [],
        "routing_decisions": [{"selected_deployment": "provider-a", "outcome": "success"}],
    }
    forged_assessment = {
        "readiness": {"status": "READY_FOR_HUMAN_REVIEW", "blockers": []},
        "diagnostic_rows": [],
        "time_split": {"available": True},
    }
    destination = tmp_path / "forged.json"

    with pytest.raises(TypeError):
        training_candidate_export([event], assessment=forged_assessment)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        write_training_candidate_export(  # type: ignore[call-arg]
            [event], destination, assessment=forged_assessment
        )
    assert not destination.exists()


def test_valid_candidate_export_requires_human_review_and_never_authorizes_training() -> None:
    events = [
        _versioned_attempt_event("r1", [("2026-01-01T00:00:00+00:00", "success")]),
        _versioned_attempt_event("r2", [("2026-01-02T00:00:00+00:00", "failure")]),
    ]

    payload = training_candidate_export(events)

    assert payload["export_type"] == "sabiroute-training-candidate-for-human-review"
    assert payload["readiness_status"] == "READY_FOR_HUMAN_REVIEW"
    assert payload["human_review_required"] is True
    assert payload["training_authorized"] is False
    assert len(payload["records"]) == 2
    assert "diagnostic_only" not in payload["records"][0]


def test_export_writer_outputs_candidate_json_only_after_gates_pass(tmp_path: Path) -> None:
    events = [
        _versioned_attempt_event("r1", [("2026-01-01T00:00:00+00:00", "success")]),
        _versioned_attempt_event("r2", [("2026-01-02T00:00:00+00:00", "failure")]),
    ]
    destination = tmp_path / "candidate.json"

    write_training_candidate_export(events, destination)

    decoded = json.loads(destination.read_text(encoding="utf-8"))
    assert decoded["training_authorized"] is False
    assert decoded["readiness_status"] == "READY_FOR_HUMAN_REVIEW"
    assert len(decoded["records"]) == 2


def test_blocked_candidate_export_writes_no_file_and_diagnostic_quarantines_unmatched(
    tmp_path: Path,
) -> None:
    event = {
        "request_id": "unmatched",
        "feature_schema_version": "1.1",
        "pre_routing_features": [],
        "routing_decisions": [
            {
                "selected_deployment": "provider-a",
                "outcome": "success",
                "attempt_schema_version": "1.1",
                "attempt_started_at": "2026-01-01T00:00:00.001000+00:00",
                "attempt_completed_at": "2026-01-01T00:00:00.500000+00:00",
                "outcome_recorded_at": "2026-01-01T00:00:00.501000+00:00",
            }
        ],
    }
    destination = tmp_path / "blocked" / "candidate.json"

    with pytest.raises(DatasetExportBlocked) as error:
        write_training_candidate_export([event], destination)
    diagnostic = diagnostic_export([event])

    assert "feature_outcome_integrity_failed" in error.value.readiness["blockers"]
    assert not destination.exists()
    assert diagnostic["training_authorized"] is False
    assert diagnostic["records"][0]["disposition"] == "quarantined"
    assert diagnostic["records"][0]["exclusion_reasons"] == [
        "feature_snapshot_missing"
    ]


def test_diagnostic_rows_quarantine_feature_without_matching_outcome() -> None:
    rows = diagnostic_export_rows(
        [
            {
                "request_id": "r1",
                "pre_routing_features": [_feature("r1", 1, "2026-01-01T00:00:00+00:00")],
                "routing_decisions": [],
            }
        ]
    )

    assert rows[0]["feature_present"] is True
    assert rows[0]["outcome_present"] is False
    assert rows[0]["disposition"] == "quarantined"
    assert "outcome_missing" in rows[0]["exclusion_reasons"]


def test_diagnostic_export_quarantines_selected_deployment_outside_eligible_set() -> None:
    event = {
        "request_id": "ineligible",
        "feature_schema_version": "1.1",
        "pre_routing_features": [
            _feature("ineligible", 1, "2026-01-01T00:00:00+00:00")
            | {
                "feature_schema_version": "1.1",
                "historical_summary_as_of": "2026-01-01T00:00:00+00:00",
                "health_eligible_deployments": ["provider-a"],
            }
        ],
        "routing_decisions": [
            {
                "selected_deployment": "provider-b",
                "outcome": "success",
                "fallback_attempt": 1,
                "attempt_schema_version": "1.1",
                "attempt_started_at": "2026-01-01T00:00:00.001000+00:00",
                "attempt_completed_at": "2026-01-01T00:00:00.500000+00:00",
                "outcome_recorded_at": "2026-01-01T00:00:00.501000+00:00",
            }
        ],
    }

    row = diagnostic_export_rows([event])[0]

    assert row["eligibility_status"] == "ineligible"
    assert row["disposition"] == "quarantined"
    assert "selected_deployment_not_eligible" in row["exclusion_reasons"]


def test_incomplete_temporal_provenance_is_visible_and_blocks_candidate_export() -> None:
    event = _versioned_attempt_event(
        "incomplete", [("2026-01-01T00:00:00+00:00", "success")]
    )
    event["routing_decisions"][0]["outcome_recorded_at"] = None  # type: ignore[index]

    row = diagnostic_export_rows([event])[0]

    assert row["temporal_provenance_status"] == "incomplete_or_unknown"
    assert "attempt_timestamps_incomplete_or_invalid" in row["exclusion_reasons"]
    with pytest.raises(DatasetExportBlocked):
        training_candidate_export([event])


def test_temporal_export_preserves_attempt_timestamps_and_legacy_is_unknown() -> None:
    feature = _feature("r1", 1, "2026-01-01T00:00:00+00:00")
    feature.update(
        feature_schema_version="1.1",
        historical_summary_as_of="2026-01-01T00:00:00+00:00",
    )
    attempt = {
        "request_id": "r1",
        "logical_request_id": "r1",
        "selected_deployment": "provider-a",
        "outcome": "success",
        "fallback_attempt": 1,
        "attempt_schema_version": "1.1",
        "attempt_started_at": "2026-01-01T00:00:00.001000+00:00",
        "attempt_completed_at": "2026-01-01T00:00:00.500000+00:00",
        "outcome_recorded_at": "2026-01-01T00:00:00.501000+00:00",
    }
    event = {
        "request_id": "r1",
        "feature_schema_version": "1.1",
        "pre_routing_features": [feature],
        "routing_decisions": [attempt],
    }

    row = diagnostic_export_rows([event])[0]
    audit = audit_dataset([event])

    assert row["outcome_schema_version"] == "1.1"
    assert _timestamp(row["attempt_started_at"]) == _timestamp(attempt["attempt_started_at"])
    assert _timestamp(row["attempt_completed_at"]) == _timestamp(attempt["attempt_completed_at"])
    assert _timestamp(row["outcome_recorded_at"]) == _timestamp(attempt["outcome_recorded_at"])
    assert audit["integrity_checks"]["valid"] is True
    assert audit["integrity_checks"]["temporal_provenance"]["verified_attempts"] == 1
    timestamp_summary = audit["integrity_checks"]["timestamps"]
    assert audit["outcome_availability"]["outcome_timestamp"] == timestamp_summary[
        "outcome_recorded_at"
    ]
    assert timestamp_summary["attempt_started_at"]["stored"] == 1
    assert (
        timestamp_summary["attempt_started_at"][
            "attempts_with_verified_temporal_provenance"
        ]
        == 1
    )

    legacy = {
        "request_id": "legacy",
        "pre_routing_features": [_feature("legacy", 1, "2026-01-01T00:00:00+00:00")],
        "routing_decisions": [{"selected_deployment": "provider-a", "outcome": "success"}],
    }
    legacy_audit = audit_dataset([legacy])
    assert legacy_audit["integrity_checks"]["temporal_provenance"][
        "unknown_or_unavailable_attempts"
    ] == 1


def test_audit_counts_attempt_without_feature_as_unavailable_and_invalid() -> None:
    event = {
        "request_id": "unmatched-attempt",
        "feature_schema_version": "1.1",
        "pre_routing_features": [],
        "routing_decisions": [
            {
                "request_id": "unmatched-attempt",
                "logical_request_id": "unmatched-attempt",
                "selected_deployment": "provider-a",
                "outcome": "success",
                "fallback_attempt": 1,
                "attempt_schema_version": "1.1",
                "attempt_started_at": "2026-01-01T00:00:00.001000+00:00",
                "attempt_completed_at": "2026-01-01T00:00:00.500000+00:00",
                "outcome_recorded_at": "2026-01-01T00:00:00.501000+00:00",
            }
        ],
    }

    integrity = audit_dataset([event])["integrity_checks"]

    assert integrity["valid"] is False
    assert integrity["checked_feature_attempts"] == 0
    assert integrity["checked_outcome_attempts"] == 1
    assert integrity["issues"]["feature_outcome_count_mismatch"] == 1
    assert integrity["issues"]["outcome_without_feature_snapshot"] == 1
    assert integrity["temporal_provenance"]["verified_attempts"] == 0
    assert integrity["temporal_provenance"]["unavailable_attempts"] == 1
    assert integrity["temporal_provenance"]["unknown_or_unavailable_attempts"] == 1


def test_audit_flags_persisted_request_that_was_never_finalized() -> None:
    event = {
        "request_id": "unfinished-request",
        "final_status": None,
        "pre_routing_features": [],
        "routing_decisions": [],
    }

    integrity = audit_dataset([event])["integrity_checks"]

    assert integrity["valid"] is False
    assert integrity["issues"]["request_not_finalized"] == 1


def test_store_additively_migrates_feature_columns_on_existing_usage_table() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE sabiroute_request_usage (request_id VARCHAR(36) PRIMARY KEY)"
        )
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    columns = {column["name"] for column in inspect(engine).get_columns("sabiroute_request_usage")}
    store.close()
    assert {"feature_schema_version", "pre_routing_features"} <= columns


def test_read_only_database_reader_does_not_initialize_or_change_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "existing.sqlite"
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE sabiroute_request_usage "
            "(request_id TEXT PRIMARY KEY, created_at TEXT, routing_decisions JSON, "
            "feature_schema_version TEXT, pre_routing_features JSON)"
        )
        connection.exec_driver_sql(
            "INSERT INTO sabiroute_request_usage VALUES "
            "('r1', '2026-01-01T00:00:00+00:00', '[]', '1.0', '[]')"
        )
    before = inspect(engine).get_table_names()
    engine.dispose()

    rows = read_usage_events(database_url)

    after_engine = create_engine(database_url)
    after = inspect(after_engine).get_table_names()
    after_engine.dispose()
    assert len(rows) == 1
    assert rows[0]["request_id"] == "r1"
    assert before == after == ["sabiroute_request_usage"]
