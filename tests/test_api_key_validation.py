"""Rejection-path coverage for :mod:`sabiroute.security.keys`.

Every branch here is a refusal: a nonsensical rate limit or budget, a digest
mismatch, or one field of the request/attempt telemetry contract that does not
line up with the rest. Each is pinned individually because each is the only
thing standing between a malformed usage row and the database.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from sabiroute.security.keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    ApiKeyRecord,
    RequestUsageEvent,
    UsageEventValidationError,
    _aware_timestamp,
    authenticate_api_key,
    validate_pre_routing_feature_snapshot,
    validate_usage_event_finalization,
)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _event(**overrides: object) -> RequestUsageEvent:
    fields: dict[str, object] = {
        "request_id": "req-1",
        "key_id": "key-1",
        "project_id": "proj-1",
        "created_at": NOW,
        "requested_alias": "fast",
        "final_status": 200,
        "final_deployment": "primary",
    }
    fields.update(overrides)
    return RequestUsageEvent(**fields)  # type: ignore[arg-type]


def _feature(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "logical_request_id": "req-1",
        "attempt_number": 1,
        "feature_schema_version": "1.0",
        "candidate_deployments": ["primary"],
        "capability_eligible_deployments": ["primary"],
        "health_eligible_deployments": ["primary"],
    }
    fields.update(overrides)
    return fields


def _outcome(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "request_id": "req-1",
        "logical_request_id": "req-1",
        "fallback_attempt": 1,
        "outcome": "success",
        "selected_deployment": "primary",
        "eligible_deployments": ["primary"],
    }
    fields.update(overrides)
    return fields


def _attempted_event(**overrides: object) -> RequestUsageEvent:
    fields: dict[str, object] = {
        "pre_routing_features": (_feature(),),
        "routing_decisions": (_outcome(),),
    }
    fields.update(overrides)
    return _event(**fields)


# --- limits ---------------------------------------------------------------


def test_rate_limit_must_be_positive() -> None:
    with pytest.raises(ValueError, match="must be positive integers"):
        ApiKeyRateLimit(requests_per_minute=0, burst_capacity=1)


def test_budget_requires_at_least_one_limit() -> None:
    with pytest.raises(ValueError, match="At least one budget limit"):
        ApiKeyBudget()


def test_token_budget_must_be_positive() -> None:
    with pytest.raises(ValueError, match="Token budgets must be positive"):
        ApiKeyBudget(daily_tokens=0)


def test_monetary_budget_must_be_positive() -> None:
    with pytest.raises(ValueError, match="Monetary budgets must be positive"):
        ApiKeyBudget(daily_cost_usd=Decimal("0"))


# --- timestamps -----------------------------------------------------------


def test_aware_timestamp_accepts_datetimes_and_iso_strings() -> None:
    assert _aware_timestamp(NOW) is NOW
    assert _aware_timestamp("2026-01-01T12:00:00Z") == NOW


def test_aware_timestamp_rejects_unparseable_strings() -> None:
    assert _aware_timestamp("not a timestamp") is None


# --- finalization ---------------------------------------------------------


def test_finalization_requires_a_request_identifier() -> None:
    with pytest.raises(UsageEventValidationError, match="request identifier"):
        validate_usage_event_finalization(_attempted_event(request_id=""))


def test_finalization_requires_a_valid_http_status() -> None:
    with pytest.raises(UsageEventValidationError, match="HTTP final_status"):
        validate_usage_event_finalization(_attempted_event(final_status=True))


def test_attempted_request_requires_a_final_deployment() -> None:
    with pytest.raises(UsageEventValidationError, match="requires a final_deployment"):
        validate_usage_event_finalization(_attempted_event(final_deployment=None))


def test_feature_snapshot_must_be_an_object() -> None:
    with pytest.raises(UsageEventValidationError, match="feature snapshot must be"):
        validate_usage_event_finalization(
            _attempted_event(pre_routing_features=(None,))
        )


def test_feature_logical_request_identifier_must_match() -> None:
    with pytest.raises(UsageEventValidationError, match="logical request identifier"):
        validate_usage_event_finalization(
            _attempted_event(pre_routing_features=(_feature(logical_request_id="other"),))
        )


def test_feature_attempt_number_must_be_sequential() -> None:
    with pytest.raises(UsageEventValidationError, match="attempt number is not sequential"):
        validate_usage_event_finalization(
            _attempted_event(pre_routing_features=(_feature(attempt_number=2),))
        )


def test_feature_schema_version_must_match_the_request() -> None:
    with pytest.raises(UsageEventValidationError, match="schema version differs"):
        validate_usage_event_finalization(
            _attempted_event(
                pre_routing_features=(_feature(feature_schema_version="1.1"),)
            )
        )


def test_outcome_must_be_an_object() -> None:
    with pytest.raises(UsageEventValidationError, match="attempt outcome must be"):
        validate_usage_event_finalization(_attempted_event(routing_decisions=(None,)))


def test_outcome_requires_a_selected_deployment() -> None:
    with pytest.raises(UsageEventValidationError, match="requires selected_deployment"):
        validate_usage_event_finalization(
            _attempted_event(routing_decisions=(_outcome(selected_deployment=""),))
        )


def test_feature_requires_candidate_lists() -> None:
    with pytest.raises(UsageEventValidationError, match="requires candidate_deployments"):
        validate_usage_event_finalization(
            _attempted_event(
                pre_routing_features=(_feature(candidate_deployments=None),)
            )
        )


def test_outcome_eligible_deployments_must_be_a_list() -> None:
    with pytest.raises(UsageEventValidationError, match="eligible_deployments must be"):
        validate_usage_event_finalization(
            _attempted_event(routing_decisions=(_outcome(eligible_deployments="primary"),))
        )


def test_selected_deployment_must_be_in_the_eligible_set() -> None:
    with pytest.raises(UsageEventValidationError, match="outside its eligible set"):
        validate_usage_event_finalization(
            _attempted_event(
                routing_decisions=(_outcome(eligible_deployments=["secondary"]),)
            )
        )


def test_schema_versions_must_agree() -> None:
    with pytest.raises(UsageEventValidationError, match="schema versions disagree"):
        validate_usage_event_finalization(
            _attempted_event(
                feature_schema_version="1.1",
                pre_routing_features=(_feature(feature_schema_version="1.1"),),
            )
        )


def test_provenance_timestamps_must_be_ordered() -> None:
    later = NOW + timedelta(minutes=5)
    with pytest.raises(UsageEventValidationError, match="timestamps are out of order"):
        validate_usage_event_finalization(
            _attempted_event(
                feature_schema_version="1.1",
                pre_routing_features=(
                    _feature(
                        feature_schema_version="1.1",
                        decision_timestamp=NOW + timedelta(minutes=1),
                    ),
                ),
                routing_decisions=(
                    _outcome(
                        attempt_schema_version="1.1",
                        attempt_started_at=NOW,
                        attempt_completed_at=later,
                        outcome_recorded_at=later,
                    ),
                ),
            )
        )


def test_final_deployment_must_match_the_last_attempt() -> None:
    with pytest.raises(UsageEventValidationError, match="differs from the last selected"):
        validate_usage_event_finalization(
            _attempted_event(
                pre_routing_features=(
                    _feature(
                        candidate_deployments=["primary", "secondary"],
                        capability_eligible_deployments=["primary", "secondary"],
                        health_eligible_deployments=["primary", "secondary"],
                    ),
                ),
                routing_decisions=(
                    _outcome(
                        selected_deployment="secondary",
                        eligible_deployments=["primary", "secondary"],
                    ),
                ),
            )
        )


# --- feature snapshot -----------------------------------------------------


def _snapshot(**overrides: object) -> dict[str, object]:
    return _feature(**overrides)


def test_snapshot_logical_request_identifier_must_match() -> None:
    with pytest.raises(UsageEventValidationError, match="logical request identifier"):
        validate_pre_routing_feature_snapshot(
            "req-1", 1, _snapshot(logical_request_id="other"), None
        )


def test_snapshot_schema_version_must_be_supported() -> None:
    with pytest.raises(UsageEventValidationError, match="unsupported feature schema"):
        validate_pre_routing_feature_snapshot(
            "req-1", 1, _snapshot(feature_schema_version="2.0"), None
        )


def test_snapshot_schema_version_must_match_existing() -> None:
    with pytest.raises(UsageEventValidationError, match="schema version differs"):
        validate_pre_routing_feature_snapshot(
            "req-1", 1, _snapshot(feature_schema_version="1.0"), "1.1"
        )


def test_snapshot_requires_candidate_lists() -> None:
    with pytest.raises(UsageEventValidationError, match="requires candidate_deployments"):
        validate_pre_routing_feature_snapshot(
            "req-1", 1, _snapshot(candidate_deployments=None), None
        )


def test_schema_1_1_snapshot_requires_a_decision_timestamp() -> None:
    with pytest.raises(UsageEventValidationError, match="decision timestamp"):
        validate_pre_routing_feature_snapshot(
            "req-1", 1, _snapshot(feature_schema_version="1.1"), None
        )


# --- authentication -------------------------------------------------------


class _RecordStore:
    def __init__(self, record: ApiKeyRecord | None) -> None:
        self._record = record

    def get(self, key_id: str) -> ApiKeyRecord | None:
        return self._record


def test_digest_mismatch_is_rejected() -> None:
    key_id = "a" * 24
    plaintext = f"sr_live_{key_id}_{'b' * 43}"
    record = ApiKeyRecord(
        key_id=key_id,
        key_hash="wrong-digest",
        project_id="proj-1",
        name="test",
        created_at=NOW,
    )

    assert authenticate_api_key(_RecordStore(record), plaintext) is None
