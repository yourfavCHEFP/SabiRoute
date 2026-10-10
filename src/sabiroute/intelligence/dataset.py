"""Content-free routing feature snapshots and read-only dataset utilities.

The feature and outcome schemas are intentionally separate. The database stores
one logical request with ordered pre-routing snapshots and ordered attempt
outcomes; exported rows are paired by attempt index without mixing their fields.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import MetaData, Table, create_engine, select

from ..security.budgets import UnsupportedBudgetRequest, estimate_input_tokens

FEATURE_SCHEMA_VERSION: Literal["1.1"] = "1.1"
_SENSITIVE_LABEL = re.compile(
    r"(?i)(sr_live_[a-z0-9_-]+|sk-[a-z0-9_-]+|(?:bearer|basic)\s+\S+|"
    r"authorization\s*[:=]\s*\S+|(?:x-)?api[_-]?key\s*[:=]\s*\S+|"
    r"(?:database|db|redis)[_-]?url\s*[:=]\s*\S+|"
    r"(?:postgres(?:ql)?|redis|mysql|mariadb|mongodb(?:\+srv)?|sqlite)://\S+)"
)
_SENSITIVE_FIELD = re.compile(
    r"(?i)^(?:authorization|api[_-]?key|access[_-]?token|password|secret|credential|"
    r"database[_-]?url|db[_-]?url|redis[_-]?url)$"
)


class HistoricalCandidateFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deployment: str = Field(min_length=1, max_length=256)
    score: float | None = None
    success_rate: float | None = Field(default=None, ge=0, le=1)
    reliability_samples: int = Field(default=0, ge=0)
    average_latency_ms: float | None = Field(default=None, ge=0)
    latency_normalized: float | None = Field(default=None, ge=0, le=1)
    latency_samples: int = Field(default=0, ge=0)
    latest_reliability_observation: datetime | None = None
    latest_latency_observation: datetime | None = None
    reliability_state_scope_id: str | None = Field(default=None, max_length=64)
    latency_state_scope_id: str | None = Field(default=None, max_length=64)


class PreRoutingFeatureSnapshot(BaseModel):
    """Allowlisted, versioned facts available before one provider attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_schema_version: Literal["1.0", "1.1"] = FEATURE_SCHEMA_VERSION
    logical_request_id: str = Field(min_length=1, max_length=36)
    attempt_number: int = Field(ge=1)
    decision_timestamp: datetime
    historical_summary_as_of: datetime | None = None
    request_type: str = Field(min_length=1, max_length=64)
    requested_alias: str | None = Field(default=None, max_length=256)
    routing_policy_id: str = Field(min_length=1, max_length=128)
    candidate_deployments: tuple[str, ...] = ()
    capability_eligible_deployments: tuple[str, ...] = ()
    health_eligible_deployments: tuple[str, ...] = ()
    capability_exclusions: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    unhealthy_deployments: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    streaming: bool | None = None
    tool_use: bool | None = None
    response_format_category: (
        Literal["none", "text", "json_object", "json_schema", "other"] | None
    ) = None
    multimodal: bool | None = None
    estimated_input_tokens: int | None = Field(default=None, ge=0)
    request_size_bytes: int | None = Field(default=None, ge=0)
    requested_max_output_tokens: int | None = Field(default=None, ge=0)
    context_size_requirement: int | None = Field(default=None, ge=0)
    routing_strategy: Literal["priority", "measured"]
    routing_strategy_version: str = Field(min_length=1, max_length=64)
    deterministic_score_context: tuple[HistoricalCandidateFeatures, ...] = ()
    deterministic_scoring_weights: dict[str, float] = Field(default_factory=dict)
    deterministic_scoring_fallback_reason: str | None = Field(default=None, max_length=128)
    selection_propensity: float | None = Field(default=None, gt=0, le=1)
    experiment_id: str | None = Field(default=None, max_length=128)

    @field_validator("requested_alias")
    @classmethod
    def redact_sensitive_alias(cls, value: str | None) -> str | None:
        if value is not None and _SENSITIVE_LABEL.search(value):
            return "[redacted]"
        return value


class PostExecutionOutcome(BaseModel):
    """Allowlisted labels/outcomes, never used as that attempt's features."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["success", "failure"] | None = None
    http_status: int | None = Field(default=None, ge=100, le=599)
    failure_category: str | None = Field(default=None, max_length=64)
    actual_latency_ms: float | None = Field(default=None, ge=0)
    provider_usage: dict[str, int | None] | None = None
    actual_cost_usd: str | None = Field(default=None, max_length=64)
    selected_deployment: str | None = Field(default=None, max_length=256)
    attempt_schema_version: Literal["1.1"] | None = None
    attempt_started_at: datetime | None = None
    attempt_completed_at: datetime | None = None
    outcome_recorded_at: datetime | None = None


def _safe_size(messages: list[dict[str, Any]], options: dict[str, Any]) -> int | None:
    """Measure request structure in memory and persist only the byte count."""
    try:
        payload = {
            "messages": messages,
            "tools": options.get("tools"),
            "response_format": options.get("response_format"),
        }
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError):
        return None


def make_pre_routing_snapshot(
    *,
    logical_request_id: str,
    attempt_number: int,
    decision_timestamp: datetime,
    requested_alias: str | None,
    request_type: str,
    routing_policy_id: str,
    routing_strategy: str,
    messages: list[dict[str, Any]],
    options: dict[str, Any],
    decision: Any,
) -> dict[str, Any]:
    """Build a schema-validated allowlist; request text is never returned."""
    explanation = decision.explanation
    scores = tuple(
        HistoricalCandidateFeatures(
            deployment=item.deployment,
            score=item.score,
            success_rate=item.success_rate,
            reliability_samples=item.reliability_samples,
            average_latency_ms=item.average_latency_ms,
            latency_normalized=item.latency_normalized,
            latency_samples=item.latency_samples,
            latest_reliability_observation=item.latest_reliability_observation,
            latest_latency_observation=item.latest_latency_observation,
            reliability_state_scope_id=item.reliability_state_scope_id,
            latency_state_scope_id=item.latency_state_scope_id,
        )
        for item in (explanation.candidate_scores if explanation is not None else ())
    )
    estimated_tokens: int | None
    try:
        estimated_tokens = estimate_input_tokens(messages)
    except UnsupportedBudgetRequest:
        estimated_tokens = None

    response_format = options.get("response_format")
    response_kind = response_format.get("type") if isinstance(response_format, dict) else None
    category: str | None
    if response_format is None:
        category = "none"
    elif response_kind == "text":
        category = "text"
    elif response_kind == "json_object":
        category = "json_object"
    elif response_kind == "json_schema":
        category = "json_schema"
    else:
        category = "other"

    max_output = options.get("max_tokens", options.get("max_completion_tokens"))
    if isinstance(max_output, bool) or not isinstance(max_output, int) or max_output < 0:
        max_output = None
    context_requirement = options.get("context_size_requirement")
    if (
        isinstance(context_requirement, bool)
        or not isinstance(context_requirement, int)
        or context_requirement < 0
    ):
        context_requirement = None
    tools = options.get("tools")
    tool_use = (isinstance(tools, list) and bool(tools)) or (
        options.get("tool_choice") not in (None, "none")
    )
    multimodal = any(
        isinstance(message.get("content"), list)
        and any(
            isinstance(part, dict)
            and part.get("type")
            in {"image", "image_url", "input_image", "input_audio", "audio", "video", "input_video"}
            for part in message["content"]
        )
        for message in messages
    )
    required = explanation.required_capabilities if explanation is not None else ()
    snapshot = PreRoutingFeatureSnapshot(
        logical_request_id=logical_request_id,
        attempt_number=attempt_number,
        decision_timestamp=decision_timestamp,
        historical_summary_as_of=(
            explanation.scoring_as_of if explanation is not None else None
        ),
        request_type=request_type,
        requested_alias=requested_alias,
        routing_policy_id=routing_policy_id,
        candidate_deployments=tuple(explanation.candidate_deployments) if explanation else (),
        capability_eligible_deployments=(
            tuple(explanation.capability_eligible_deployments) if explanation else ()
        ),
        health_eligible_deployments=tuple(explanation.eligible_deployments) if explanation else (),
        capability_exclusions=(
            {
                name: tuple(reasons)
                for name, reasons in explanation.capability_excluded_deployments.items()
            }
            if explanation
            else {}
        ),
        unhealthy_deployments=(tuple(explanation.unhealthy_deployments) if explanation else ()),
        required_capabilities=tuple(sorted(item.value for item in required)),
        streaming=options.get("stream") if isinstance(options.get("stream"), bool) else None,
        tool_use=tool_use,
        response_format_category=category,  # type: ignore[arg-type]
        multimodal=multimodal,
        estimated_input_tokens=estimated_tokens,
        request_size_bytes=_safe_size(messages, options),
        requested_max_output_tokens=max_output,
        context_size_requirement=context_requirement,
        routing_strategy=routing_strategy,  # type: ignore[arg-type]
        routing_strategy_version=(explanation.scoring_policy_version if explanation else "unknown"),
        deterministic_score_context=scores,
        deterministic_scoring_weights=(dict(explanation.scoring_weights) if explanation else {}),
        deterministic_scoring_fallback_reason=(
            explanation.scoring_fallback_reason if explanation else None
        ),
        selection_propensity=None,
        experiment_id=None,
    )
    return snapshot.model_dump(mode="json")


class DatasetExportBlocked(ValueError):
    """Raised when integrity or readiness gates reject a review export."""

    def __init__(self, readiness: dict[str, Any]) -> None:
        self.readiness = readiness
        blockers = ", ".join(readiness.get("blockers", ())) or "invalid attempt records"
        super().__init__(f"Dataset export is blocked: {blockers}")


def _safe_outcome(raw_outcome: Any) -> dict[str, Any] | None:
    if not isinstance(raw_outcome, dict):
        return None
    raw_usage = raw_outcome.get("usage")
    safe_usage = None
    if isinstance(raw_usage, dict):
        safe_usage = {
            key: value
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0
            else None
            for key, value in raw_usage.items()
            if key in {"prompt_tokens", "completion_tokens", "total_tokens"}
        }
    safe = {
        "outcome": raw_outcome.get("outcome"),
        "http_status": raw_outcome.get("http_status"),
        "failure_category": raw_outcome.get("failure_category"),
        "actual_latency_ms": raw_outcome.get("latency_ms"),
        "provider_usage": safe_usage,
        "actual_cost_usd": raw_outcome.get("actual_cost_usd"),
        "selected_deployment": raw_outcome.get("selected_deployment"),
        "attempt_schema_version": raw_outcome.get("attempt_schema_version"),
        "attempt_started_at": raw_outcome.get("attempt_started_at"),
        "attempt_completed_at": raw_outcome.get("attempt_completed_at"),
        "outcome_recorded_at": raw_outcome.get("outcome_recorded_at"),
    }
    try:
        return PostExecutionOutcome.model_validate(safe).model_dump(mode="json")
    except Exception:
        return None


def _contains_sensitive_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            _SENSITIVE_FIELD.fullmatch(str(key)) is not None
            or _SENSITIVE_LABEL.search(str(key)) is not None
            or _contains_sensitive_value(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_sensitive_value(item) for item in value)
    return isinstance(value, str) and _SENSITIVE_LABEL.search(value) is not None


def _redact_sensitive_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            "[redacted]"
            if _SENSITIVE_FIELD.fullmatch(str(key)) or _SENSITIVE_LABEL.search(str(key))
            else key:
            _redact_sensitive_values(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    if isinstance(value, str) and _SENSITIVE_LABEL.search(value):
        return "[redacted]"
    return value


def _parsed_aware_timestamp(value: Any) -> datetime | None:
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _temporal_reasons(
    feature: PreRoutingFeatureSnapshot,
    outcome: dict[str, Any],
    *,
    now: datetime,
) -> list[str]:
    reasons: list[str] = []
    if (
        feature.feature_schema_version != "1.1"
        or outcome.get("attempt_schema_version") != "1.1"
    ):
        reasons.append("temporal_provenance_unknown_for_schema")
        return reasons

    decision_at = _parsed_aware_timestamp(feature.decision_timestamp)
    if decision_at is None:
        reasons.append("decision_timestamp_missing_or_invalid")
    elif decision_at > now:
        reasons.append("decision_timestamp_in_future")

    if feature.routing_strategy == "measured":
        cutoff = _parsed_aware_timestamp(feature.historical_summary_as_of)
        if cutoff is None:
            reasons.append("historical_summary_cutoff_missing_or_invalid")
        elif decision_at is None or cutoff != decision_at:
            reasons.append("historical_summary_cutoff_mismatch")
        elif cutoff > now:
            reasons.append("historical_summary_cutoff_in_future")
        else:
            for candidate in feature.deterministic_score_context:
                if not candidate.reliability_state_scope_id:
                    reasons.append("reliability_state_scope_missing")
                if not candidate.latency_state_scope_id:
                    reasons.append("latency_state_scope_missing")
                for timestamp, samples, field in (
                    (
                        candidate.latest_reliability_observation,
                        candidate.reliability_samples,
                        "latest_reliability_observation",
                    ),
                    (
                        candidate.latest_latency_observation,
                        candidate.latency_samples,
                        "latest_latency_observation",
                    ),
                ):
                    if timestamp is None:
                        if samples:
                            reasons.append(f"{field}_missing")
                    elif timestamp.tzinfo is None or timestamp.astimezone(UTC) > cutoff:
                        reasons.append(f"{field}_not_valid_at_cutoff")

    timestamps = [
        _parsed_aware_timestamp(outcome.get(name))
        for name in ("attempt_started_at", "attempt_completed_at", "outcome_recorded_at")
    ]
    if any(timestamp is None for timestamp in timestamps):
        reasons.append("attempt_timestamps_incomplete_or_invalid")
    elif all(timestamp is not None for timestamp in timestamps):
        started_at, completed_at, recorded_at = timestamps
        assert started_at is not None and completed_at is not None and recorded_at is not None
        if not started_at <= completed_at <= recorded_at:
            reasons.append("attempt_timestamp_order_invalid")
        if decision_at is not None and started_at < decision_at:
            reasons.append("attempt_started_before_decision")
        if recorded_at > now:
            reasons.append("outcome_recorded_at_in_future")
    return list(dict.fromkeys(reasons))


def diagnostic_export_rows(events: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return allowlisted diagnostic rows with explicit quarantine reasons.

    This output is never a training dataset. Unmatched rows are retained as
    diagnostics and marked quarantined rather than paired or discarded.
    """
    output: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    for event in events:
        features = event.get("pre_routing_features") or []
        outcomes = event.get("routing_decisions") or []
        count = max(len(features), len(outcomes))
        for index in range(count):
            raw_feature = features[index] if index < len(features) else None
            raw_outcome = outcomes[index] if index < len(outcomes) else None
            reasons: list[str] = []
            sensitive_values_detected = _contains_sensitive_value(
                raw_feature
            ) or _contains_sensitive_value(raw_outcome)
            if sensitive_values_detected:
                reasons.append("sensitive_value_redacted")
            feature_model: PreRoutingFeatureSnapshot | None = None
            if raw_feature is None:
                reasons.append("feature_snapshot_missing")
            elif isinstance(raw_feature, dict):
                if raw_feature.get("feature_schema_version") is None:
                    reasons.append("feature_schema_version_missing")
                try:
                    feature_model = PreRoutingFeatureSnapshot.model_validate(raw_feature)
                except Exception:
                    reasons.append("feature_snapshot_invalid")
            else:
                reasons.append("feature_snapshot_invalid")

            safe_outcome = _safe_outcome(raw_outcome)
            if raw_outcome is None:
                reasons.append("outcome_missing")
            elif safe_outcome is None:
                reasons.append("outcome_invalid")

            feature = (
                feature_model.model_dump(mode="json") if feature_model is not None else None
            )
            raw_feature_schema = (
                raw_feature.get("feature_schema_version")
                if isinstance(raw_feature, dict)
                else None
            )
            feature_schema_version = (
                raw_feature_schema if raw_feature_schema in {"1.0", "1.1"} else None
            )
            if feature is not None and feature_schema_version is None:
                # Do not present Pydantic's current-schema default as stored
                # historical evidence when the source omitted its version.
                feature.pop("feature_schema_version", None)
            outcome = safe_outcome
            if feature is not None:
                feature = _redact_sensitive_values(feature)
            if outcome is not None:
                outcome = _redact_sensitive_values(outcome)
            eligibility_status = "unknown"
            temporal_status = "unavailable" if feature_model is None else "unknown"
            if feature_model is not None and outcome is not None:
                # `_safe_outcome` only returns a value for dictionary records.
                assert isinstance(raw_outcome, dict)
                if feature_model.logical_request_id != str(event.get("request_id", "")):
                    reasons.append("feature_request_id_mismatch")
                if feature_model.attempt_number != index + 1:
                    reasons.append("attempt_number_mismatch")
                event_schema = event.get("feature_schema_version")
                if (
                    event_schema is not None
                    and isinstance(raw_feature, dict)
                    and raw_feature.get("feature_schema_version") != event_schema
                ):
                    reasons.append("feature_schema_version_mismatch")

                selected = outcome.get("selected_deployment")
                if selected is None:
                    reasons.append("selected_deployment_missing")
                else:
                    eligibility_checks = (
                        (
                            feature_model.candidate_deployments,
                            "candidate_set_missing_or_empty",
                            "selected_deployment_not_candidate",
                        ),
                        (
                            feature_model.capability_eligible_deployments,
                            "capability_eligible_set_missing_or_empty",
                            "selected_deployment_not_capability_eligible",
                        ),
                        (
                            feature_model.health_eligible_deployments,
                            "eligible_set_missing_or_empty",
                            "selected_deployment_not_eligible",
                        ),
                    )
                    eligible_in_all_sets = True
                    for eligible, missing_reason, mismatch_reason in eligibility_checks:
                        if not eligible:
                            reasons.append(missing_reason)
                            eligible_in_all_sets = False
                        elif selected not in eligible:
                            reasons.append(mismatch_reason)
                            eligible_in_all_sets = False
                    outcome_eligible = raw_outcome.get("eligible_deployments")
                    if outcome_eligible is not None:
                        if not isinstance(outcome_eligible, (list, tuple)):
                            reasons.append("outcome_eligible_set_invalid")
                            eligible_in_all_sets = False
                        elif selected not in outcome_eligible:
                            reasons.append("selected_deployment_not_outcome_eligible")
                            eligible_in_all_sets = False
                    eligibility_status = (
                        "verified_eligible" if eligible_in_all_sets else "ineligible"
                    )
                if sensitive_values_detected:
                    eligibility_status = "unknown"

                if outcome.get("outcome") not in {"success", "failure"}:
                    reasons.append("outcome_label_missing_or_invalid")
                # Validate linkage on the source record before `_safe_outcome`
                # projects away identifiers. Never expose those identifiers in
                # diagnostic output; report only the verification result.
                outcome_ids = [
                    raw_outcome.get(name)
                    for name in ("request_id", "logical_request_id")
                    if raw_outcome.get(name) is not None
                ]
                if not outcome_ids:
                    reasons.append("outcome_request_id_unavailable")
                elif any(value != str(event.get("request_id", "")) for value in outcome_ids):
                    reasons.append("outcome_request_id_mismatch")

                attempt_number = raw_outcome.get("fallback_attempt")
                if attempt_number is None:
                    reasons.append("outcome_attempt_number_unavailable")
                elif (
                    isinstance(attempt_number, bool)
                    or not isinstance(attempt_number, int)
                    or attempt_number != index + 1
                ):
                    reasons.append("fallback_attempt_number_mismatch")

                temporal = _temporal_reasons(feature_model, outcome, now=now)
                if raw_feature_schema not in {"1.0", "1.1"}:
                    temporal.append("temporal_provenance_unknown_for_schema")
                reasons.extend(temporal)
                temporal_status = "verified" if not temporal else "incomplete_or_unknown"

            output.append(
                {
                    "logical_request_id": str(event.get("request_id", "")),
                    "attempt_index": index + 1,
                    "diagnostic_only": True,
                    "training_candidate": False,
                    "disposition": "quarantined" if reasons else "diagnostic_only",
                    "exclusion_reasons": list(dict.fromkeys(reasons)),
                    "eligibility_status": eligibility_status,
                    "request_attempt_linkage_status": (
                        "mismatch"
                        if any(
                            reason in reasons
                            for reason in (
                                "outcome_request_id_mismatch",
                                "fallback_attempt_number_mismatch",
                            )
                        )
                        else "unverified"
                        if any(
                            reason in reasons
                            for reason in (
                                "outcome_request_id_unavailable",
                                "outcome_attempt_number_unavailable",
                            )
                        )
                        else "verified"
                    ),
                    "temporal_provenance_status": temporal_status,
                    "feature_present": raw_feature is not None,
                    "outcome_present": raw_outcome is not None,
                    "feature_schema_version": feature_schema_version,
                    "outcome_schema_version": (
                        outcome.get("attempt_schema_version") if outcome else None
                    ),
                    "decision_timestamp": feature.get("decision_timestamp") if feature else None,
                    "attempt_started_at": outcome.get("attempt_started_at") if outcome else None,
                    "attempt_completed_at": (
                        outcome.get("attempt_completed_at") if outcome else None
                    ),
                    "outcome_recorded_at": outcome.get("outcome_recorded_at") if outcome else None,
                    "pre_routing_features": feature,
                    "post_execution_outcome": outcome,
                }
            )
    return output


def readiness_report(
    events: Sequence[dict[str, Any]], *, low_sample_threshold: int | None = None
) -> dict[str, Any]:
    """Build the read-only audit, split result, and Phase 13 readiness decision."""
    audit = audit_dataset(events, low_sample_threshold=low_sample_threshold)
    rows = diagnostic_export_rows(events)
    split_rows = [
        row
        for row in rows
        if row["disposition"] == "diagnostic_only"
        and row["eligibility_status"] == "verified_eligible"
        and row["temporal_provenance_status"] == "verified"
    ]
    try:
        training_rows, evaluation_rows = chronological_split(split_rows)
    except ValueError as exc:
        time_split = {
            "available": False,
            "reason": str(exc),
            "eligible_attempt_rows": len(split_rows),
            "excluded_attempt_rows": len(rows) - len(split_rows),
        }
    else:
        time_split = {
            "available": True,
            "method": (
                "chronological by logical_request_id on integrity-eligible, "
                "temporally verified attempts; grouped fallback attempts"
            ),
            "eligible_attempt_rows": len(split_rows),
            "excluded_attempt_rows": len(rows) - len(split_rows),
            "training_attempt_rows": len(training_rows),
            "evaluation_attempt_rows": len(evaluation_rows),
            "training_logical_requests": len(
                {row["logical_request_id"] for row in training_rows}
            ),
            "evaluation_logical_requests": len(
                {row["logical_request_id"] for row in evaluation_rows}
            ),
        }
    readiness = assess_phase13_readiness(audit, time_split)
    return {
        "audit": audit,
        "diagnostic_rows": rows,
        "time_split": time_split,
        "readiness": readiness,
    }


def diagnostic_export(
    events: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Build an explicitly diagnostic envelope, including quarantined rows."""
    result = readiness_report(events)
    return {
        "export_type": "sabiroute-diagnostic-only",
        "training_authorized": False,
        "readiness_status": result["readiness"]["status"],
        "readiness_blockers": result["readiness"]["blockers"],
        "integrity_issues": result["audit"]["integrity_checks"]["issues"],
        "timestamp_fields": result["audit"]["integrity_checks"]["timestamps"],
        "records": result["diagnostic_rows"],
    }


def training_candidate_export(
    events: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Return a review candidate only when every current readiness gate passes.

    The result is not authorization to train; it must receive human review.
    """
    result = readiness_report(events)
    readiness = result["readiness"]
    rows = result["diagnostic_rows"]
    if readiness["status"] != "READY_FOR_HUMAN_REVIEW" or any(
        row["disposition"] != "diagnostic_only"
        or row["eligibility_status"] != "verified_eligible"
        or row["temporal_provenance_status"] != "verified"
        for row in rows
    ):
        raise DatasetExportBlocked(readiness)

    record_fields = (
        "logical_request_id",
        "feature_schema_version",
        "outcome_schema_version",
        "decision_timestamp",
        "attempt_started_at",
        "attempt_completed_at",
        "outcome_recorded_at",
        "pre_routing_features",
        "post_execution_outcome",
    )
    return {
        "export_type": "sabiroute-training-candidate-for-human-review",
        "readiness_status": readiness["status"],
        "training_authorized": False,
        "human_review_required": True,
        "time_split": result["time_split"],
        "records": [
            {field: row[field] for field in record_fields}
            for row in rows
        ],
    }


def _write_json_export(payload: dict[str, Any], path: Path) -> None:
    """Write one JSON envelope with an explicit export type and safety status."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_training_candidate_export(
    events: Sequence[dict[str, Any]], path: Path
) -> dict[str, Any]:
    """Write only a readiness-gated human-review candidate export."""
    payload = training_candidate_export(events)
    _write_json_export(payload, path)
    return payload


def write_diagnostic_export(
    events: Sequence[dict[str, Any]], path: Path
) -> dict[str, Any]:
    """Write a diagnostic-only envelope; quarantined records remain visible."""
    payload = diagnostic_export(events)
    _write_json_export(payload, path)
    return payload


def chronological_split(
    rows: Sequence[dict[str, Any]], *, evaluation_fraction: float = 0.2
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split chronologically by logical request; fallback attempts stay grouped."""
    if not 0 < evaluation_fraction < 1:
        raise ValueError("evaluation_fraction must be between 0 and 1")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    times: dict[str, list[datetime]] = defaultdict(list)
    for row in rows:
        request_id = str(row.get("logical_request_id", ""))
        if not request_id:
            raise ValueError("Every exported row must have a logical_request_id")
        groups[request_id].append(dict(row))
        timestamp = row.get("decision_timestamp")
        if not timestamp:
            raise ValueError("Every exported row needs a decision timestamp for a time split")
        try:
            parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Every exported row needs a valid decision timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError(
                "Every exported row needs a timezone-aware decision timestamp for a time split"
            )
        times[request_id].append(parsed.astimezone(UTC))
    ordered = sorted(groups, key=lambda request_id: (min(times[request_id]), request_id))
    if len(ordered) < 2:
        raise ValueError("At least two logical requests are required for a time split")
    evaluation_count = max(1, int(len(ordered) * evaluation_fraction))
    desired_cutoff = len(ordered) - evaluation_count
    cutoff = 0
    for candidate_cutoff in range(desired_cutoff, 0, -1):
        latest_training = max(max(times[request_id]) for request_id in ordered[:candidate_cutoff])
        earliest_evaluation = min(
            min(times[request_id]) for request_id in ordered[candidate_cutoff:]
        )
        if latest_training <= earliest_evaluation:
            cutoff = candidate_cutoff
            break
    if cutoff == 0:
        raise ValueError(
            "Logical request groups overlap in time; no leakage-safe chronological split exists"
        )
    train_ids = set(ordered[:cutoff])
    train = [row for request_id in ordered[:cutoff] for row in groups[request_id]]
    evaluation = [row for request_id in ordered[cutoff:] for row in groups[request_id]]
    assert train_ids.isdisjoint({row["logical_request_id"] for row in evaluation})
    return train, evaluation


def audit_dataset(
    events: Sequence[dict[str, Any]], *, low_sample_threshold: int | None = None
) -> dict[str, Any]:
    """Summarize telemetry coverage and observational selection bias."""
    if low_sample_threshold is not None and low_sample_threshold < 1:
        raise ValueError("low_sample_threshold must be positive")
    feature_rows: list[dict[str, Any]] = []
    attempt_rows: list[dict[str, Any]] = []
    request_types: Counter[str] = Counter()
    schema_versions: Counter[str] = Counter()
    streaming: Counter[str] = Counter()
    capabilities: Counter[str] = Counter()
    failure_categories: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    daily: Counter[str] = Counter()
    weekly: Counter[str] = Counter()
    eligible_by_deployment: Counter[str] = Counter()
    eligible_requests_by_deployment: dict[str, set[str]] = defaultdict(set)
    jointly_eligible_pairs: Counter[str] = Counter()
    selected_by_deployment: Counter[str] = Counter()
    selected_requests_by_deployment: dict[str, set[str]] = defaultdict(set)
    attempts_per_request: Counter[int] = Counter()
    timestamps: list[datetime] = []
    missing: Counter[str] = Counter()
    labels_available = 0
    request_shapes: dict[str, Counter[str]] = {
        name: Counter() for name in ("tool_use", "response_format_category", "multimodal")
    }
    candidate_sizes: Counter[int] = Counter()
    eligible_sizes: Counter[int] = Counter()
    attempts_with_latency = attempts_with_usage = attempts_with_cost = 0
    attempts_with_timestamps = 0
    attempts_without_temporal_provenance = 0

    for event in events:
        features = event.get("pre_routing_features") or []
        outcomes = event.get("routing_decisions") or []
        schema_versions[str(event.get("feature_schema_version") or "<missing>")] += 1
        feature_rows.extend(item for item in features if isinstance(item, dict))
        attempts = max(len(features), len(outcomes))
        attempts_per_request[attempts] += 1
        for feature in features:
            if not isinstance(feature, dict):
                continue
            for field in request_shapes:
                value = feature.get(field)
                request_shapes[field][str(value) if value is not None else "unknown"] += 1
            candidate_sizes[len(feature.get("candidate_deployments") or [])] += 1
            eligible_sizes[len(feature.get("health_eligible_deployments") or [])] += 1
            request_types[str(feature.get("request_type") or "<missing>")] += 1
            streaming[
                str(feature.get("streaming") if feature.get("streaming") is not None else "unknown")
            ] += 1
            for capability in feature.get("required_capabilities") or []:
                capabilities[str(capability)] += 1
            request_id = str(event.get("request_id", ""))
            for deployment in set(feature.get("health_eligible_deployments") or []):
                eligible_by_deployment[deployment] += 1
                eligible_requests_by_deployment[deployment].add(request_id)
            eligible_names = sorted(set(feature.get("health_eligible_deployments") or []))
            for left_index, left in enumerate(eligible_names):
                for right in eligible_names[left_index + 1 :]:
                    jointly_eligible_pairs[f"{left}|{right}"] += 1
            parsed_timestamp = _parsed_aware_timestamp(feature.get("decision_timestamp"))
            if parsed_timestamp is not None:
                timestamps.append(parsed_timestamp)
                daily[parsed_timestamp.date().isoformat()] += 1
                iso = parsed_timestamp.isocalendar()
                weekly[f"{iso.year}-W{iso.week:02d}"] += 1
            for name in (
                "request_type",
                "requested_alias",
                "routing_policy_id",
                "streaming",
                "tool_use",
                "response_format_category",
                "multimodal",
                "estimated_input_tokens",
                "request_size_bytes",
                "requested_max_output_tokens",
                "context_size_requirement",
                "routing_strategy_version",
                "candidate_deployments",
                "capability_eligible_deployments",
                "health_eligible_deployments",
                "required_capabilities",
                "deterministic_score_context",
                "deterministic_scoring_weights",
                "deterministic_scoring_fallback_reason",
                "selection_propensity",
                "experiment_id",
            ):
                if feature.get(name) is None:
                    missing[name] += 1
        for outcome in outcomes:
            if not isinstance(outcome, dict):
                continue
            attempt_rows.append(outcome)
            deployment = str(outcome.get("selected_deployment") or "<missing>")
            selected_by_deployment[deployment] += 1
            selected_requests_by_deployment[deployment].add(str(event.get("request_id", "")))
            status = outcome.get("http_status")
            statuses[str(status) if status is not None else "unknown"] += 1
            category = outcome.get("failure_category")
            if category:
                failure_categories[str(category)] += 1
            if outcome.get("outcome") in {"success", "failure"}:
                labels_available += 1
            if outcome.get("latency_ms") is not None:
                attempts_with_latency += 1
            usage = outcome.get("usage")
            if isinstance(usage, dict) and any(
                isinstance(usage.get(name), int) and not isinstance(usage.get(name), bool)
                for name in ("prompt_tokens", "completion_tokens", "total_tokens")
            ):
                attempts_with_usage += 1
            if outcome.get("actual_cost_usd") is not None:
                attempts_with_cost += 1
            if outcome.get("attempt_schema_version") == "1.1" and all(
                outcome.get(name) is not None
                for name in (
                    "attempt_started_at",
                    "attempt_completed_at",
                    "outcome_recorded_at",
                )
            ):
                attempts_with_timestamps += 1
            else:
                attempts_without_temporal_provenance += 1

    total_requests = len(events)
    total_attempts = sum(
        max(
            len(event.get("pre_routing_features") or []),
            len(event.get("routing_decisions") or []),
        )
        for event in events
    )
    deployment_names = set(eligible_by_deployment) | set(selected_by_deployment)
    deployment_coverage: dict[str, Any] = {}
    for name in sorted(deployment_names):
        eligible_opportunities = eligible_by_deployment[name]
        eligible_request_count = len(eligible_requests_by_deployment[name])
        selected_count = selected_by_deployment[name]
        selection_rate = selected_count / eligible_opportunities if eligible_opportunities else None
        deployment_coverage[name] = {
            "eligible_requests": eligible_request_count,
            "eligible_decision_opportunities": eligible_opportunities,
            "eligible_share": (eligible_request_count / total_requests if total_requests else None),
            "selected_attempts": selected_count,
            "selected_share": selected_count / total_attempts if total_attempts else None,
            "selected_logical_requests": len(selected_requests_by_deployment[name]),
            "selected_request_share": (
                len(selected_requests_by_deployment[name]) / total_requests
                if total_requests
                else None
            ),
            "selection_rate_when_eligible": selection_rate,
            "outcome_observations": selected_count,
            "insufficient_evidence": (
                True
                if selected_count == 0
                else (
                    None if low_sample_threshold is None else selected_count < low_sample_threshold
                )
            ),
        }
    missingness = {
        name: {
            "missing": count,
            "total": len(feature_rows),
            "rate": count / len(feature_rows) if feature_rows else None,
        }
        for name, count in sorted(missing.items())
    }
    fallback_requests = sum(
        1
        for event in events
        if max(
            len(event.get("pre_routing_features") or []),
            len(event.get("routing_decisions") or []),
        )
        > 1
    )
    observed_rates = [
        data["selection_rate_when_eligible"]
        for data in deployment_coverage.values()
        if data["selection_rate_when_eligible"] is not None
    ]
    integrity_checks = _audit_integrity(events)
    timestamp_persistence = _timestamp_persistence_report(
        events,
        verified_attempts=integrity_checks["temporal_provenance"]["verified_attempts"],
    )
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "stored_feature_schema_versions": dict(schema_versions),
        "logical_requests": total_requests,
        "provider_attempts": total_attempts,
        "observations_by_deployment": dict(selected_by_deployment),
        "observations_by_request_type": dict(request_types),
        "success_failure_counts": dict(
            Counter(str(row.get("outcome") or "unknown") for row in attempt_rows)
        ),
        "failure_categories": dict(failure_categories),
        "explicit_timeout_attempts": sum(
            count for category, count in failure_categories.items()
            if "timeout" in category.lower()
        ),
        "transport_failures_not_inferred_as_timeouts": failure_categories.get("transport", 0),
        "http_status_counts": dict(statuses),
        "time_range": {
            "start": min(timestamps).isoformat() if timestamps else None,
            "end": max(timestamps).isoformat() if timestamps else None,
        },
        "daily_observations": dict(sorted(daily.items())),
        "weekly_observations": dict(sorted(weekly.items())),
        "feature_missingness": missingness,
        "request_shape_coverage": {
            **{name: dict(values) for name, values in request_shapes.items()},
            "candidate_set_sizes": dict(sorted(candidate_sizes.items())),
            "eligible_set_sizes": dict(sorted(eligible_sizes.items())),
        },
        "label_availability": {
            "attempts_with_outcome_label": labels_available,
            "attempts_without_outcome_label": max(0, total_attempts - labels_available),
        },
        "streaming_distribution": dict(streaming),
        "capability_distribution": dict(capabilities),
        "fallback_logical_requests": fallback_requests,
        "attempts_per_logical_request": {
            str(key): count for key, count in sorted(attempts_per_request.items())
        },
        "deployment_selection_and_eligibility": deployment_coverage,
        "eligibility_overlap": {
            "jointly_eligible_decision_opportunities": dict(jointly_eligible_pairs),
            "unselected_candidate_outcomes": "unobserved; no counterfactual labels created",
        },
        "outcome_availability": {
            "attempts_with_latency": attempts_with_latency,
            "attempts_with_provider_usage": attempts_with_usage,
            "attempts_with_actual_cost": attempts_with_cost,
            "outcome_schema_version": {
                "1.1": attempts_with_timestamps,
                "unavailable_or_legacy": attempts_without_temporal_provenance,
            },
            "attempts_with_event_timestamps": attempts_with_timestamps,
            "attempts_without_temporal_provenance": attempts_without_temporal_provenance,
            "timestamp_fields": timestamp_persistence,
            "explicit_timeout_count": sum(
                count for category, count in failure_categories.items()
                if "timeout" in category.lower()
            ),
            "generic_transport_failures_not_counted_as_timeouts": failure_categories.get(
                "transport", 0
            ),
            "outcome_timestamp": timestamp_persistence["outcome_recorded_at"],
        },
        "integrity_checks": integrity_checks | {"timestamps": timestamp_persistence},
        "selection_bias": {
            "historical_data_is_observational": True,
            "unselected_candidates_have_counterfactual_outcomes": False,
            "selection_imbalance_detected": (
                len(set(observed_rates)) > 1 if len(observed_rates) >= 2 else None
            ),
            "selection_rates_when_eligible": {
                name: data["selection_rate_when_eligible"]
                for name, data in deployment_coverage.items()
            },
            "offline_comparison_warning": (
                "Historical outcomes exist only for selected attempts; do not treat "
                "unselected candidates as failures or successes."
            ),
        },
        "telemetry_coverage": {
            "requests_with_feature_snapshot": sum(
                bool(event.get("pre_routing_features")) for event in events
            ),
            "requests_missing_feature_snapshot": sum(
                not bool(event.get("pre_routing_features")) for event in events
            ),
            "feature_fields_audited": len(missingness),
            "deployments_with_no_observed_outcomes": [
                name
                for name, data in deployment_coverage.items()
                if data["outcome_observations"] == 0
            ],
            "low_observation_threshold": low_sample_threshold,
            "sample_adequacy_threshold_configured": low_sample_threshold is not None,
        },
    }


def assess_phase13_readiness(
    audit: dict[str, Any], time_split: dict[str, Any]
) -> dict[str, Any]:
    """Summarize data-readiness blockers without imposing a sample-count threshold.

    A structurally clean report only advances the dataset to human review; it
    never authorizes model training by itself.
    """
    integrity = audit["integrity_checks"]
    temporal = integrity["temporal_provenance"]
    issues = integrity["issues"]
    outcomes = audit["success_failure_counts"]
    observed_outcomes = {name: count for name, count in outcomes.items() if count}
    outcome_variation = len(observed_outcomes) > 1
    unknown_temporal = temporal["unknown_or_unavailable_attempts"]
    blockers: list[str] = []

    if not integrity["valid"]:
        blockers.append("feature_outcome_integrity_failed")
    if unknown_temporal:
        blockers.append("temporal_provenance_incomplete")
    if not outcome_variation:
        blockers.append("no_outcome_variation")
    if not time_split.get("available", False):
        blockers.append("chronological_split_unavailable")

    status = "BLOCKED" if blockers else "READY_FOR_HUMAN_REVIEW"
    return {
        "status": status,
        "training_authorized": False,
        "interpretation": (
            "Passing structural checks advances the dataset to human review; "
            "it is not approval to train or evidence of model utility."
        ),
        "minimum_sample_threshold_applied": False,
        "blockers": blockers,
        "feature_outcome_pairing": {
            "integrity_valid": integrity["valid"],
            "issues": integrity["issues"],
            "provider_attempts": audit["provider_attempts"],
            "labeled_attempts": audit["label_availability"]["attempts_with_outcome_label"],
            "unlabeled_attempts": audit["label_availability"]["attempts_without_outcome_label"],
        },
        "request_attempt_consistency": {
            "unfinished_requests": issues.get("request_not_finalized", 0),
            "association_issues": {
                name: count
                for name, count in issues.items()
                if "request_id_mismatch" in name
                or name in {
                    "attempt_number_mismatch",
                    "fallback_attempt_number_mismatch",
                    "selected_deployment_not_eligible",
                    "duplicate_request_id",
                    "missing_request_id",
                }
            },
            "invalid_or_missing_records": {
                name: count
                for name, count in issues.items()
                if name.startswith("invalid_")
                or name.startswith("missing_")
                or name.startswith("outcome_without_")
                or name.startswith("outcome_with_")
            },
        },
        "schema_and_temporal_provenance": {
            "feature_schema_versions": audit["stored_feature_schema_versions"],
            "schema_compatibility_issues": {
                name: count
                for name, count in issues.items()
                if "schema" in name or name == "unsupported_attempt_schema_version"
            },
            "verified_attempts": temporal["verified_attempts"],
            "unknown_or_unavailable_attempts": unknown_temporal,
            "unavailable_attempts": temporal["unavailable_attempts"],
            "temporal_leakage_issues": {
                name: count
                for name, count in issues.items()
                if "cutoff" in name
                or "future_" in name
                or "_after_cutoff" in name
                or name in {
                    "attempt_timestamp_order",
                    "attempt_started_before_decision",
                    "out_of_order_decision_timestamp",
                    "decision_precedes_request_creation",
                }
            },
        },
        "observations_by_deployment": audit["observations_by_deployment"],
        "request_shape_coverage": audit["request_shape_coverage"],
        "eligible_candidate_overlap": audit["eligibility_overlap"],
        "time_coverage": {
            "range": audit["time_range"],
            "daily_observations": audit["daily_observations"],
            "weekly_observations": audit["weekly_observations"],
        },
        "outcome_variation": {
            "counts": outcomes,
            "distinct_observed_outcomes": len(observed_outcomes),
            "present": outcome_variation,
        },
        "chronological_split": time_split,
        "feature_missingness": audit["feature_missingness"],
        "selection_bias": audit["selection_bias"],
    }


def _timestamp_persistence_report(
    events: Sequence[dict[str, Any]], *, verified_attempts: int
) -> dict[str, dict[str, Any]]:
    """Report where timestamps are stored and whether their schema is auditable."""
    specs = {
        "decision_timestamp": (
            "pre_routing_features[i].decision_timestamp",
            "Time the router made the candidate decision; stored with that attempt's features.",
            "feature_schema_version",
        ),
        "attempt_started_at": (
            "routing_decisions[i].attempt_started_at",
            "Time recorded immediately before the provider call.",
            "attempt_schema_version",
        ),
        "attempt_completed_at": (
            "routing_decisions[i].attempt_completed_at",
            "Time recorded after the provider call returns or raises.",
            "attempt_schema_version",
        ),
        "outcome_recorded_at": (
            "routing_decisions[i].outcome_recorded_at",
            "Time the outcome object is assembled after the attempt; not the database commit time.",
            "attempt_schema_version",
        ),
    }
    counters: dict[str, Counter[str]] = {
        field: Counter() for field in specs
    }
    for event in events:
        features = event.get("pre_routing_features") or []
        outcomes = event.get("routing_decisions") or []
        for index in range(max(len(features), len(outcomes))):
            feature = features[index] if index < len(features) else None
            outcome = outcomes[index] if index < len(outcomes) else None
            for field, counter in counters.items():
                if field == "decision_timestamp":
                    record = feature
                    value = record.get(field) if isinstance(record, dict) else None
                    schema_version = (
                        record.get("feature_schema_version")
                        if isinstance(record, dict)
                        else None
                    )
                else:
                    record = outcome
                    value = record.get(field) if isinstance(record, dict) else None
                    schema_version = (
                        record.get("attempt_schema_version")
                        if isinstance(record, dict)
                        else None
                    )
                if not isinstance(record, dict):
                    counter["unavailable"] += 1
                    continue
                if value is None:
                    counter["missing"] += 1
                else:
                    counter["stored"] += 1
                    if _parsed_aware_timestamp(value) is None:
                        counter["invalid_or_timezone_unknown"] += 1
                if schema_version != "1.1":
                    counter["legacy_or_unknown_schema"] += 1

    result: dict[str, dict[str, Any]] = {}
    for field, (source, meaning, _) in specs.items():
        counts = counters[field]
        result[field] = {
            "source": source,
            "meaning": meaning,
            "stored": counts["stored"],
            "missing": counts["missing"],
            "unavailable": counts["unavailable"],
            "invalid_or_timezone_unknown": counts["invalid_or_timezone_unknown"],
            "legacy_or_unknown_schema": counts["legacy_or_unknown_schema"],
            "attempts_with_verified_temporal_provenance": verified_attempts,
        }
    return result


def _audit_integrity(events: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Check stored request/attempt pairings without exposing malformed values."""
    issues: Counter[str] = Counter()
    seen_ids: Counter[str] = Counter()
    now = datetime.now(UTC)
    checked_attempts = 0
    checked_outcome_attempts = 0
    provenance_unknown_attempts = 0
    provenance_unavailable_attempts = 0
    provenance_verified_attempts = 0
    for event in events:
        request_id = str(event.get("request_id") or "")
        if not request_id:
            issues["missing_request_id"] += 1
        seen_ids[request_id] += 1
        if "final_status" in event and event.get("final_status") is None:
            issues["request_not_finalized"] += 1
        features = event.get("pre_routing_features") or []
        outcomes = event.get("routing_decisions") or []
        event_schema_version = event.get("feature_schema_version")
        if len(features) != len(outcomes):
            issues["feature_outcome_count_mismatch"] += 1
        feature_provenance: dict[int, bool] = {}
        previous: datetime | None = None
        created_at = event.get("created_at")
        if created_at is not None:
            if not isinstance(created_at, datetime):
                try:
                    created_at = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                except ValueError:
                    created_at = None
                    issues["invalid_request_timestamp"] += 1
            if isinstance(created_at, datetime):
                if created_at.tzinfo is None:
                    issues["naive_request_timestamp"] += 1
                    created_at = created_at.replace(tzinfo=UTC)
                created_at = created_at.astimezone(UTC)
                if created_at > now:
                    issues["future_request_timestamp"] += 1
        for index, raw_feature in enumerate(features):
            checked_attempts += 1
            if not isinstance(raw_feature, dict):
                issues["invalid_feature_record"] += 1
                continue
            if raw_feature.get("feature_schema_version") is None:
                issues["missing_feature_schema_version"] += 1
            try:
                feature = PreRoutingFeatureSnapshot.model_validate(raw_feature)
            except Exception:
                issues["invalid_feature_schema"] += 1
                continue
            if (
                event_schema_version is not None
                and raw_feature.get("feature_schema_version") != event_schema_version
            ):
                issues["feature_schema_version_mismatch"] += 1
            if feature.logical_request_id != request_id:
                issues["feature_request_id_mismatch"] += 1
            if feature.attempt_number != index + 1:
                issues["attempt_number_mismatch"] += 1
            timestamp = feature.decision_timestamp
            decision_timestamp_aware = timestamp.tzinfo is not None
            if not decision_timestamp_aware:
                issues["naive_decision_timestamp"] += 1
                timestamp = timestamp.replace(tzinfo=UTC)
            timestamp = timestamp.astimezone(UTC)
            if timestamp > now:
                issues["future_decision_timestamp"] += 1
            if isinstance(created_at, datetime) and timestamp < created_at:
                issues["decision_precedes_request_creation"] += 1
            if previous is not None and timestamp < previous:
                issues["out_of_order_decision_timestamp"] += 1
            previous = timestamp
            if not feature.candidate_deployments:
                issues["empty_candidate_set"] += 1
            if not feature.health_eligible_deployments:
                issues["empty_eligible_set"] += 1
            if (
                feature.feature_schema_version == "1.1"
            ):
                provenance_ok = (
                    raw_feature.get("feature_schema_version") == "1.1"
                    and decision_timestamp_aware
                )
                if feature.routing_strategy == "measured":
                    as_of = feature.historical_summary_as_of
                    if as_of is None:
                        issues["missing_historical_summary_as_of"] += 1
                        provenance_ok = False
                    else:
                        if as_of.tzinfo is None:
                            issues["naive_historical_summary_as_of"] += 1
                            provenance_ok = False
                        as_of_utc = (
                            as_of.astimezone(UTC)
                            if as_of.tzinfo
                            else as_of.replace(tzinfo=UTC)
                        )
                        if as_of_utc != timestamp:
                            issues["historical_summary_cutoff_mismatch"] += 1
                            provenance_ok = False
                        if as_of_utc > now:
                            issues["future_historical_summary_as_of"] += 1
                            provenance_ok = False
                        for candidate in feature.deterministic_score_context:
                            if not candidate.reliability_state_scope_id:
                                issues["missing_reliability_state_scope_id"] += 1
                                provenance_ok = False
                            if not candidate.latency_state_scope_id:
                                issues["missing_latency_state_scope_id"] += 1
                                provenance_ok = False
                            for field_name in (
                                "latest_reliability_observation",
                                "latest_latency_observation",
                            ):
                                observed_at = getattr(candidate, field_name)
                                sample_count = (
                                    candidate.reliability_samples
                                    if field_name == "latest_reliability_observation"
                                    else candidate.latency_samples
                                )
                                if observed_at is None:
                                    if sample_count:
                                        issues[f"missing_{field_name}"] += 1
                                        provenance_ok = False
                                    continue
                                if observed_at.tzinfo is None:
                                    issues[f"naive_{field_name}"] += 1
                                    provenance_ok = False
                                    continue
                                if observed_at.astimezone(UTC) > as_of_utc:
                                    issues[f"{field_name}_after_cutoff"] += 1
                                    provenance_ok = False
                feature_provenance[index] = provenance_ok
        for index, outcome in enumerate(outcomes):
            checked_outcome_attempts += 1
            if not isinstance(outcome, dict):
                issues["invalid_outcome_record"] += 1
                continue
            if index >= len(features):
                issues["outcome_without_feature_snapshot"] += 1
                provenance_unknown_attempts += 1
                provenance_unavailable_attempts += 1
                continue
            if not isinstance(features[index], dict):
                issues["outcome_with_invalid_feature_snapshot"] += 1
                provenance_unknown_attempts += 1
                provenance_unavailable_attempts += 1
                continue
            feature = features[index]
            selected = outcome.get("selected_deployment")
            if selected is None:
                issues["missing_selected_deployment"] += 1
            else:
                if selected not in (feature.get("candidate_deployments") or []):
                    issues["selected_deployment_not_candidate"] += 1
                if selected not in (feature.get("capability_eligible_deployments") or []):
                    issues["selected_deployment_not_capability_eligible"] += 1
                if selected not in (feature.get("health_eligible_deployments") or []):
                    issues["selected_deployment_not_eligible"] += 1
                outcome_eligible = outcome.get("eligible_deployments")
                if outcome_eligible is not None:
                    if not isinstance(outcome_eligible, (list, tuple)):
                        issues["invalid_outcome_eligible_set"] += 1
                    elif selected not in outcome_eligible:
                        issues["selected_deployment_not_outcome_eligible"] += 1

            feature_version = feature.get("feature_schema_version")
            outcome_version = outcome.get("attempt_schema_version")
            schema_1_1_attempt = feature_version == "1.1" and outcome_version == "1.1"
            attempt_number = outcome.get("fallback_attempt")
            if attempt_number is None:
                if schema_1_1_attempt:
                    issues["missing_fallback_attempt_number"] += 1
            elif (
                isinstance(attempt_number, bool)
                or not isinstance(attempt_number, int)
            ):
                issues["invalid_fallback_attempt_number"] += 1
            elif attempt_number != index + 1:
                issues["fallback_attempt_number_mismatch"] += 1

            if outcome.get("request_id") not in (None, request_id):
                issues["outcome_request_id_mismatch"] += 1
            if outcome.get("logical_request_id") not in (None, request_id):
                issues["outcome_logical_request_id_mismatch"] += 1
            if schema_1_1_attempt and not any(
                outcome.get(name) is not None
                for name in ("request_id", "logical_request_id")
            ):
                issues["missing_outcome_request_identifier"] += 1
            if outcome.get("outcome") not in {"success", "failure"}:
                issues["invalid_outcome_label"] += 1
            if (
                feature_version != "1.1"
                or outcome_version != "1.1"
            ):
                if outcome_version not in (None, "1.0", "1.1"):
                    issues["unsupported_attempt_schema_version"] += 1
                provenance_unknown_attempts += 1
                continue
            names = ("attempt_started_at", "attempt_completed_at", "outcome_recorded_at")
            parsed: list[datetime] = []
            timestamps_valid = True
            for name in names:
                value = outcome.get(name)
                try:
                    item = value if isinstance(value, datetime) else datetime.fromisoformat(
                        str(value).replace("Z", "+00:00")
                    )
                except (TypeError, ValueError):
                    issues[f"missing_or_invalid_{name}"] += 1
                    timestamps_valid = False
                    continue
                if item.tzinfo is None:
                    issues[f"naive_{name}"] += 1
                    timestamps_valid = False
                    continue
                item = item.astimezone(UTC)
                if item > now:
                    issues[f"future_{name}"] += 1
                    timestamps_valid = False
                parsed.append(item)
            if len(parsed) == 3:
                started_at, completed_at, recorded_at = parsed
                if not started_at <= completed_at <= recorded_at:
                    issues["attempt_timestamp_order"] += 1
                    timestamps_valid = False
                if index < len(features) and isinstance(features[index], dict):
                    decision_value = features[index].get("decision_timestamp")
                    try:
                        decision_time = datetime.fromisoformat(
                            str(decision_value).replace("Z", "+00:00")
                        ).astimezone(UTC)
                    except (TypeError, ValueError):
                        decision_time = None
                    if decision_time is not None and started_at < decision_time:
                        issues["attempt_started_before_decision"] += 1
                        timestamps_valid = False
                if timestamps_valid and feature_provenance.get(index, False):
                    provenance_verified_attempts += 1
                else:
                    provenance_unknown_attempts += 1
        if len(features) > len(outcomes):
            provenance_unknown_attempts += len(features) - len(outcomes)
    for request_id, count in seen_ids.items():
        if request_id and count > 1:
            issues["duplicate_request_id"] += count - 1
    return {
        "valid": not issues,
        "checked_feature_attempts": checked_attempts,
        "checked_outcome_attempts": checked_outcome_attempts,
        "issues": dict(issues),
        "historical_summary_as_of_provenance": (
            "v1.1 cutoff/latest-observation timestamps auditable; aggregate source history "
            "cannot be reconstructed; v1.0 provenance unknown"
        ),
        "temporal_provenance": {
            "verified_attempts": provenance_verified_attempts,
            "unknown_or_unavailable_attempts": provenance_unknown_attempts,
            "unavailable_attempts": provenance_unavailable_attempts,
            "legacy_records_are_unknown": True,
        },
        "unselected_candidates_given_outcomes": False,
    }


def read_usage_events(database_url: str) -> list[dict[str, Any]]:
    """Read only the usage table; reflection and SELECT do not initialize schema."""
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    elif database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        metadata = MetaData()
        table = Table("sabiroute_request_usage", metadata, autoload_with=engine)
        fields = [
            name
            for name in (
                "request_id",
                "created_at",
                "final_status",
                "requested_alias",
                "routing_decisions",
                "feature_schema_version",
                "pre_routing_features",
            )
            if name in table.c
        ]
        with engine.connect() as connection:
            rows = connection.execute(select(*(table.c[name] for name in fields))).mappings().all()
        return [dict(row) for row in rows]
    finally:
        engine.dispose()
