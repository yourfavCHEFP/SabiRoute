"""I7 — the explicit bypass.

Immutable per request, evaluated **once**, default-off. A malformed caller signal is
**ignored** in favour of the operator default; it never errors. This is the same
strict-marker discipline the existing code uses for its own request markers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class BypassReason(StrEnum):
    """Why a request was or was not transformed. A policy enum, not a boolean."""

    NOT_BYPASSED = "not_bypassed"
    POLICY_DISABLED = "policy_disabled"
    CALLER_SIGNAL = "caller_signal"
    MALFORMED_SIGNAL = "malformed_signal"
    CAPABILITY_LOSS = "capability_loss"
    VALIDATION_FAILURE = "validation_failure"
    TRANSFORM_ERROR = "transform_error"

@dataclass(frozen=True, slots=True)
class BypassDecision:
    """One decision, correlated to one request."""

    bypassed: bool
    reason: BypassReason
    request_id: str

def evaluate_bypass(
    *,
    policy_enabled: bool,
    caller_signal: Any,
    request_id: str,
) -> BypassDecision:
    """Decide once whether this request is transformed.

    ``caller_signal`` is only honoured when it is exactly ``True``. Anything else that is
    not ``None`` is malformed and is ignored in favour of the operator default.
    """
    if not policy_enabled:
        return BypassDecision(True, BypassReason.POLICY_DISABLED, request_id)

    if caller_signal is None:
        return BypassDecision(False, BypassReason.NOT_BYPASSED, request_id)

    if caller_signal is True:
        return BypassDecision(True, BypassReason.CALLER_SIGNAL, request_id)

    # Malformed: ignore the signal, keep the operator default (transform).
    return BypassDecision(False, BypassReason.MALFORMED_SIGNAL, request_id)
