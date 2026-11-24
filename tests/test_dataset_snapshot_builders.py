"""Snapshot construction and outcome normalisation in the dataset module.

Three things here decide whether a stored row can be trusted later: the byte
measurement must never fail a request, an unsupported payload must record an
unknown token count rather than a guessed one, and an outcome that does not
satisfy its schema must be dropped instead of stored half-built.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

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


def test_an_unmeasurable_request_records_no_size() -> None:
    assert ds._safe_size([{"content": {1, 2}}], {}) is None


def test_a_measurement_counts_bytes_of_the_structure() -> None:
    size = ds._safe_size([{"role": "user", "content": "hi"}], {})

    assert isinstance(size, int)
    assert size > 0


def test_an_unsupported_payload_records_no_token_estimate() -> None:
    multimodal = [
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "x"}}]}
    ]

    snapshot = _snapshot(messages=multimodal)

    assert snapshot["multimodal"] is True
    assert snapshot["estimated_input_tokens"] is None


@pytest.mark.parametrize(
    ("response_format", "expected"),
    [
        ({"type": "text"}, "text"),
        ({"type": "json_object"}, "json_object"),
        ({"type": "json_schema"}, "json_schema"),
        ({"type": "audio"}, "other"),
    ],
)
def test_the_response_format_category_is_classified(
    response_format: dict[str, Any], expected: str
) -> None:
    snapshot = _snapshot(options={"response_format": response_format})

    assert snapshot["response_format_category"] == expected


def test_an_outcome_that_fails_its_schema_is_dropped() -> None:
    assert ds._safe_outcome({"http_status": 999}) is None


def test_a_decision_timestamp_after_the_cutoff_is_reported() -> None:
    future = NOW + timedelta(minutes=5)
    feature = ds.PreRoutingFeatureSnapshot.model_validate(
        _snapshot(decision_timestamp=future)
    )

    reasons = ds._temporal_reasons(feature, {"attempt_schema_version": "1.1"}, now=NOW)

    assert "decision_timestamp_in_future" in reasons


def test_a_measured_snapshot_without_a_cutoff_is_reported() -> None:
    feature = ds.PreRoutingFeatureSnapshot.model_validate(
        _snapshot(routing_strategy="measured")
    )

    reasons = ds._temporal_reasons(feature, {"attempt_schema_version": "1.1"}, now=NOW)

    assert "historical_summary_cutoff_missing_or_invalid" in reasons
