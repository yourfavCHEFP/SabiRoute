"""Client API-key primitives. Plaintext keys are returned only at issuance."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol

_KEY_PATTERN = re.compile(r"^sr_live_([a-f0-9]{24})_([A-Za-z0-9_-]{43})$")


@dataclass(frozen=True, slots=True)
class ApiKeyRecord:
    """Persistable, non-secret client key metadata and one-way digest."""

    key_id: str
    key_hash: str
    project_id: str
    name: str
    created_at: datetime
    revoked_at: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ApiKeyIdentity:
    """Trusted request identity derived only after successful key validation."""

    key_id: str
    project_id: str


@dataclass(frozen=True, slots=True)
class ApiKeyRateLimit:
    """Per-key token-bucket refill rate and maximum burst, in requests."""

    requests_per_minute: int
    burst_capacity: int

    def __post_init__(self) -> None:
        if self.requests_per_minute < 1 or self.burst_capacity < 1:
            raise ValueError("Rate limits and burst capacity must be positive integers.")


@dataclass(frozen=True, slots=True)
class ApiKeyBudget:
    """Optional per-key daily and monthly token/USD ceilings."""

    daily_tokens: int | None = None
    monthly_tokens: int | None = None
    daily_cost_usd: Decimal | None = None
    monthly_cost_usd: Decimal | None = None

    def __post_init__(self) -> None:
        if all(
            value is None
            for value in (
                self.daily_tokens,
                self.monthly_tokens,
                self.daily_cost_usd,
                self.monthly_cost_usd,
            )
        ):
            raise ValueError("At least one budget limit must be configured.")
        if any(
            value is not None and value < 1 for value in (self.daily_tokens, self.monthly_tokens)
        ):
            raise ValueError("Token budgets must be positive integers.")
        if any(
            value is not None and value <= 0
            for value in (self.daily_cost_usd, self.monthly_cost_usd)
        ):
            raise ValueError("Monetary budgets must be positive.")


@dataclass(frozen=True, slots=True)
class RequestUsageEvent:
    """One durable accounting row for one authenticated client request."""

    request_id: str
    key_id: str
    project_id: str
    created_at: datetime
    requested_alias: str | None
    final_deployment: str | None = None
    final_status: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    failure_category: str | None = None
    estimated_input_tokens: int | None = None
    reserved_tokens: int | None = None
    actual_cost_usd: Decimal | None = None
    estimated_cost_usd: Decimal | None = None
    routing_decisions: tuple[dict[str, Any], ...] = ()
    feature_schema_version: str | None = "1.0"
    pre_routing_features: tuple[dict[str, Any], ...] = ()


class UsageEventValidationError(ValueError):
    """Raised when a finalized request contains inconsistent attempt telemetry."""


def _aware_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate_usage_event_finalization(event: RequestUsageEvent) -> None:
    """Validate the request/attempt contract before persisting final telemetry.

    An in-progress admission row may have no attempts. Once attempts are
    finalized, every feature snapshot must have exactly one corresponding
    outcome, with matching logical request, sequential attempt number, and an
    eligible selected deployment.
    """
    if not isinstance(event.request_id, str) or not event.request_id:
        raise UsageEventValidationError("finalized request requires a request identifier")
    if (
        isinstance(event.final_status, bool)
        or not isinstance(event.final_status, int)
        or not 100 <= event.final_status <= 599
    ):
        raise UsageEventValidationError("finalized request requires an HTTP final_status")

    features = event.pre_routing_features
    outcomes = event.routing_decisions
    if len(features) != len(outcomes):
        raise UsageEventValidationError("feature/outcome attempt counts differ")
    if not features:
        return

    if not event.final_deployment:
        raise UsageEventValidationError("attempted request requires a final_deployment")

    for index, (feature, outcome) in enumerate(zip(features, outcomes, strict=True), start=1):
        if not isinstance(feature, Mapping):
            raise UsageEventValidationError("feature snapshot must be an object")
        if feature.get("logical_request_id") != event.request_id:
            raise UsageEventValidationError("feature logical request identifier differs")
        attempt_number = feature.get("attempt_number")
        if (
            isinstance(attempt_number, bool)
            or not isinstance(attempt_number, int)
            or attempt_number != index
        ):
            raise UsageEventValidationError("feature attempt number is not sequential")
        if (
            event.feature_schema_version is not None
            and feature.get("feature_schema_version") != event.feature_schema_version
        ):
            raise UsageEventValidationError("feature schema version differs from request schema")

        if not isinstance(outcome, Mapping):
            raise UsageEventValidationError("attempt outcome must be an object")
        outcome_ids = [
            outcome.get(name)
            for name in ("request_id", "logical_request_id")
            if outcome.get(name) is not None
        ]
        if not outcome_ids or any(value != event.request_id for value in outcome_ids):
            raise UsageEventValidationError("outcome logical request identifier differs")
        fallback_attempt = outcome.get("fallback_attempt")
        if (
            isinstance(fallback_attempt, bool)
            or not isinstance(fallback_attempt, int)
            or fallback_attempt != index
        ):
            raise UsageEventValidationError("outcome attempt number is not sequential")
        if outcome.get("outcome") not in {"success", "failure"}:
            raise UsageEventValidationError("attempt outcome label is missing or invalid")

        selected = outcome.get("selected_deployment")
        if not isinstance(selected, str) or not selected:
            raise UsageEventValidationError("attempt outcome requires selected_deployment")
        for field in (
            "candidate_deployments",
            "capability_eligible_deployments",
            "health_eligible_deployments",
        ):
            candidates = feature.get(field)
            if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
                raise UsageEventValidationError(f"feature snapshot requires {field}")
            if selected not in candidates:
                raise UsageEventValidationError(f"selected deployment was not in {field}")
        outcome_eligible = outcome.get("eligible_deployments")
        if outcome_eligible is not None:
            if not isinstance(outcome_eligible, Sequence) or isinstance(
                outcome_eligible, (str, bytes)
            ):
                raise UsageEventValidationError("outcome eligible_deployments must be a list")
            if selected not in outcome_eligible:
                raise UsageEventValidationError(
                    "outcome selected deployment is outside its eligible set"
                )

        if (
            feature.get("feature_schema_version") == "1.1"
            or outcome.get("attempt_schema_version") == "1.1"
        ):
            if (
                feature.get("feature_schema_version") != "1.1"
                or outcome.get("attempt_schema_version") != "1.1"
            ):
                raise UsageEventValidationError("feature and outcome schema versions disagree")
            decision_at = _aware_timestamp(feature.get("decision_timestamp"))
            started_at = _aware_timestamp(outcome.get("attempt_started_at"))
            completed_at = _aware_timestamp(outcome.get("attempt_completed_at"))
            recorded_at = _aware_timestamp(outcome.get("outcome_recorded_at"))
            if None in (decision_at, started_at, completed_at, recorded_at):
                raise UsageEventValidationError(
                    "schema 1.1 attempt requires timezone-aware provenance timestamps"
                )
            assert decision_at is not None
            assert started_at is not None
            assert completed_at is not None
            assert recorded_at is not None
            if not decision_at <= started_at <= completed_at <= recorded_at:
                raise UsageEventValidationError("attempt provenance timestamps are out of order")

    if outcomes[-1].get("selected_deployment") != event.final_deployment:
        raise UsageEventValidationError(
            "final_deployment differs from the last selected deployment"
        )


def validate_pre_routing_feature_snapshot(
    request_id: str,
    attempt_number: int,
    snapshot: Mapping[str, Any],
    existing_schema_version: str | None,
) -> None:
    """Validate one decision snapshot before it is durably appended."""
    if snapshot.get("logical_request_id") != request_id:
        raise UsageEventValidationError("feature logical request identifier differs")
    saved_attempt_number = snapshot.get("attempt_number")
    if (
        isinstance(saved_attempt_number, bool)
        or not isinstance(saved_attempt_number, int)
        or saved_attempt_number != attempt_number
    ):
        raise UsageEventValidationError("feature attempt number is not sequential")
    schema_version = snapshot.get("feature_schema_version")
    if schema_version not in {"1.0", "1.1"}:
        raise UsageEventValidationError("unsupported feature schema version")
    if existing_schema_version is not None and schema_version != existing_schema_version:
        raise UsageEventValidationError("feature schema version differs from request schema")
    for field in (
        "candidate_deployments",
        "capability_eligible_deployments",
        "health_eligible_deployments",
    ):
        candidates = snapshot.get(field)
        if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
            raise UsageEventValidationError(f"feature snapshot requires {field}")
    if schema_version == "1.1" and _aware_timestamp(snapshot.get("decision_timestamp")) is None:
        raise UsageEventValidationError(
            "schema 1.1 feature requires a timezone-aware decision timestamp"
        )


class ApiKeyStore(Protocol):
    """Persistence contract used by the key lifecycle and auth boundary."""

    def create(self, record: ApiKeyRecord) -> None: ...

    def get(self, key_id: str) -> ApiKeyRecord | None: ...

    def revoke(self, key_id: str, at: datetime) -> bool: ...

    def rotate(self, old_key_id: str, new_record: ApiKeyRecord, at: datetime) -> bool: ...

    def get_rate_limit(self, key_id: str) -> ApiKeyRateLimit | None: ...

    def set_rate_limit(self, key_id: str, limit: ApiKeyRateLimit | None) -> bool: ...

    def get_budget(self, key_id: str) -> ApiKeyBudget | None: ...

    def set_budget(self, key_id: str, budget: ApiKeyBudget | None) -> bool: ...

    def get_budget_usage(self, key_id: str, now: datetime) -> dict[str, dict[str, Any]]: ...

    def reserve_budget(
        self,
        key_id: str,
        request_id: str,
        estimated_tokens: int,
        estimated_cost_usd: Decimal | None,
        now: datetime,
    ) -> str | None: ...

    def reconcile_budget(
        self,
        key_id: str,
        request_id: str,
        actual_tokens: int | None,
        actual_cost_usd: Decimal | None,
    ) -> None: ...

    def release_budget(self, key_id: str, request_id: str) -> None: ...

    def create_usage_event(self, event: RequestUsageEvent) -> None: ...

    def append_pre_routing_feature_snapshot(
        self, request_id: str, snapshot: Mapping[str, Any]
    ) -> bool: ...

    def finalize_usage_event(self, event: RequestUsageEvent) -> bool: ...

    def list_usage_events(
        self, key_id: str, *, limit: int, offset: int
    ) -> tuple[list[RequestUsageEvent], int]: ...


def _new_key_record(
    *, project_id: str, name: str, metadata: dict[str, Any] | None = None
) -> tuple[ApiKeyRecord, str]:
    key_id = secrets.token_hex(12)
    secret = secrets.token_urlsafe(32)
    plaintext = f"sr_live_{key_id}_{secret}"
    record = ApiKeyRecord(
        key_id=key_id,
        key_hash=hashlib.sha256(plaintext.encode("utf-8")).hexdigest(),
        project_id=project_id,
        name=name,
        created_at=datetime.now(UTC),
        metadata=metadata or {},
    )
    return record, plaintext


def issue_api_key(
    store: ApiKeyStore,
    *,
    project_id: str,
    name: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[ApiKeyRecord, str]:
    """Create a random key and persist only its SHA-256 digest."""
    record, plaintext = _new_key_record(project_id=project_id, name=name, metadata=metadata)
    store.create(record)
    return record, plaintext


def rotate_api_key(store: ApiKeyStore, old_key_id: str) -> tuple[ApiKeyRecord, str] | None:
    """Atomically revoke a key and issue its replacement, if it is active."""
    old_record = store.get(old_key_id)
    if old_record is None or old_record.revoked_at is not None:
        return None

    new_record, plaintext = _new_key_record(
        project_id=old_record.project_id,
        name=old_record.name,
        metadata=old_record.metadata,
    )
    if not store.rotate(old_key_id, new_record, datetime.now(UTC)):
        return None
    return new_record, plaintext


def revoke_api_key(store: ApiKeyStore, key_id: str) -> bool:
    """Revoke a key without returning or logging any credential material."""
    return store.revoke(key_id, datetime.now(UTC))


def authenticate_api_key(store: ApiKeyStore, plaintext: str) -> ApiKeyRecord | None:
    """Validate format, identifier, revocation state, and one-way digest."""
    match = _KEY_PATTERN.fullmatch(plaintext)
    if match is None:
        return None

    key_id = match.group(1)
    record = store.get(key_id)
    if record is None or record.revoked_at is not None:
        return None

    presented_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(record.key_hash, presented_hash):
        return None
    return record
