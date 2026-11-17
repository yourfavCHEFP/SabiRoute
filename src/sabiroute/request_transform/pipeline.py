"""The request-transform pipeline — I1 through I9 in contract order.

The order is not incidental. ``R6.1-FOUNDATION-CONTRACT.md`` §3 requirement 4 says
**policy and capability checks precede transformation**, so the bypass decision is taken
before any message is touched, and the capability check is taken against the transformed
list *before* it is copied into an ``EffectiveRequest``.

Two invariants this module exists to enforce:

* **I3 — one effective request per logical request.** ``run`` is called once per request,
  never per attempt. The reservation at ``:1244`` is taken on the original; I3's
  monotone-shrink bound then guarantees the provider never sees more than was reserved.
* **I9 — fail-to-original.** Every failure path returns the original messages unchanged.
  Nothing here raises to the caller. ``CancelledError`` is not caught (``guard.py``).

**Identity note.** ``derive_effective`` copies each dict (``tuple(dict(m) for m in ...)``),
so after that copy the ``id()``-based dropped-message detection in ``capability.py`` can no
longer see anything as dropped. ``check_capability_preservation`` is therefore called on
the post-compression list, where ``compress`` has preserved object identity, and before
the copy. Calling it after ``derive_effective`` would silently disable I6.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from ..capabilities import Capability
from ..config.validation import OptimizationPolicy
from ..security.budgets import UnsupportedBudgetRequest, estimate_input_tokens
from .bypass import BypassDecision, BypassReason, evaluate_bypass
from .canonical import canonical_bytes, within_budget, within_byte_budget
from .capability import check_capability_preservation
from .compression import compress
from .effective import EffectiveRequest, derive_effective
from .errors import CapabilityLoss, TransformError, ValidationFailure
from .frozen import FrozenOriginal
from .guard import fail_to_original
from .record import TransformationRecord
from .validation import validate_effective

DEFAULT_STRATEGY = "whole_message_removal"


def default_token_counter(messages: list[dict[str, Any]]) -> int | None:
    """Adapt the repository's single estimator to the ``TokenCounter`` protocol.

    ``estimate_input_tokens`` *raises* on unsupported shapes (multimodal, custom message
    structures) rather than guessing. Here that becomes ``None``, which makes
    ``compression.compress`` skip entirely. That is deliberate: an unmeasurable request is
    left alone rather than compressed against an unknown baseline.
    """
    try:
        return estimate_input_tokens(messages)
    except UnsupportedBudgetRequest:
        return None


def _sha256(messages: list[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_bytes(messages)).hexdigest()


@dataclass(frozen=True, slots=True)
class TransformOutcome:
    """What the provider should receive, and what we should record about it."""

    messages: list[dict[str, Any]]
    effective: EffectiveRequest | None
    record: TransformationRecord | None
    bypass: BypassDecision


def _untouched_outcome(
    original: list[dict[str, Any]],
    bypass: BypassDecision,
    *,
    policy: OptimizationPolicy,
    fallback_reason: str | None = None,
) -> TransformOutcome:
    """The original, unchanged. Used by every bypass and every failure path."""
    record = TransformationRecord(
        policy_id=None,
        policy_version=policy.version,
        strategy=policy.strategy,
        original_count=len(original),
        effective_count=len(original),
        original_sha256=_sha256(original),
        effective_sha256=_sha256(original),
        fallback_reason=fallback_reason,
        bypass_reason=str(bypass.reason),
    )
    return TransformOutcome(
        messages=original,
        effective=None,
        record=record,
        bypass=bypass,
    )


def run(
    *,
    messages: list[dict[str, Any]],
    policy: OptimizationPolicy,
    required_capabilities: frozenset[Capability] = frozenset(),
    request_id: str,
    caller_signal: Any = None,
    logger: logging.Logger,
) -> TransformOutcome:
    """Run the pipeline once for one logical request.

    Never raises. Returns the original messages on any failure, with the reason recorded.
    """
    # D1: open the latency bracket before bypass and freeze. §4 calls the I2 budget a
    # *synchronous event-loop stall*; both are inline costs on the same request, so a
    # bracket that opened after them measured less than the docstring promises.
    started = time.perf_counter()

    # --- I7: bypass, evaluated once, before anything is touched -----------------
    bypass = evaluate_bypass(
        policy_enabled=policy.enabled,
        caller_signal=caller_signal,
        request_id=request_id,
    )
    if bypass.bypassed:
        # B5: with enabled=false the bytes are byte-identical to the pre-R6 path.
        return _untouched_outcome(messages, bypass, policy=policy)

    # --- I1: the immutable original --------------------------------------------
    try:
        original = FrozenOriginal.freeze(messages).as_messages()
    except Exception:  # noqa: BLE001 - degrade boundary
        logger.warning(
            "request transform could not freeze the original (request_id=%s); passing "
            "the request through untouched",
            request_id,
        )
        return _untouched_outcome(
            messages,
            BypassDecision(True, BypassReason.TRANSFORM_ERROR, request_id),
            policy=policy,
            fallback_reason="freeze_failed",
        )

    def _transform() -> TransformOutcome:
        # D1: ``started`` was taken at the top of ``run`` so the ceiling spans bypass,
        # freeze, and the transform body — all inline work on this one request.

        # --- I2: canonical form ------------------------------------------------
        # The invariant is "the canonical bytes are never longer than the input's
        # DEFAULT JSON" (canonical.py:8). The baseline must therefore be the default
        # encoding, not the canonical one: comparing canonical to itself reduces to
        # len(x) <= len(x) and can never fire. See R6.1-REVIEW-RECORD.md [M] 6.
        original_bytes = canonical_bytes(original)
        default_json = json.dumps(original, ensure_ascii=False).encode("utf-8")
        if not within_budget(default_json, original_bytes):
            raise TransformError("canonical form expanded the original")

        # --- R6.4: compression -------------------------------------------------
        compressed = compress(
            original,
            max_ratio=policy.max_ratio,
            count_tokens=default_token_counter,
        )

        # --- D1: the byte budget ------------------------------------------------
        # Configurable, and deliberately looser than I3's monotone-shrink, so it binds
        # only if that invariant is ever relaxed. See canonical.within_byte_budget.
        if not within_byte_budget(
            original_bytes, canonical_bytes(compressed), policy.byte_budget_ratio
        ):
            raise TransformError("transform output exceeded the byte budget")

        # --- I6: capability preservation, BEFORE the dict copy in I3 -----------
        # compress() preserves object identity; derive_effective() does not.
        check_capability_preservation(original, compressed, required_capabilities)

        # --- I3: the effective request -----------------------------------------
        effective = derive_effective(
            original,
            compressed,
            policy_id=None,
            policy_version=policy.version,
        )
        effective_messages = effective.as_messages()

        # --- I8: validation ----------------------------------------------------
        validate_effective(effective_messages)

        # --- I4: the record ----------------------------------------------------
        record = TransformationRecord(
            policy_id=None,
            policy_version=policy.version,
            strategy=policy.strategy,
            original_count=len(original),
            effective_count=len(effective_messages),
            original_sha256=_sha256(original),
            effective_sha256=_sha256(effective_messages),
            fallback_reason=None,
            bypass_reason=str(bypass.reason),
        )
        # --- D1: the latency ceiling --------------------------------------------
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > policy.latency_budget_ms:
            raise TransformError("transform exceeded the latency budget")

        return TransformOutcome(
            messages=effective_messages,
            effective=effective,
            record=record,
            bypass=bypass,
        )

    # --- I9: fail-to-original ---------------------------------------------------
    # The transform runs exactly once. The exception is captured so the degrade can be
    # classified without re-running anything: a second run would double the work and
    # could produce a different outcome than the one that failed.
    captured: list[Exception] = []

    def _attempt() -> TransformOutcome:
        try:
            return _transform()
        except Exception as exc:  # noqa: BLE001 - captured, then re-raised to the guard
            captured.append(exc)
            raise

    untouched = _untouched_outcome(messages, bypass, policy=policy)
    outcome = fail_to_original(
        _attempt,
        untouched,
        logger=logger,
        request_id=request_id,
        reason="transform_failed",
    )
    if outcome is not untouched:
        return outcome

    # The guard degraded. Classify from the captured exception — never "unknown error".
    reason = classify_failure(captured[0] if captured else None)
    return _untouched_outcome(
        messages,
        BypassDecision(True, reason, request_id),
        policy=policy,
        fallback_reason=str(reason),
    )


def classify_failure(error: BaseException | None) -> BypassReason:
    """Map a transform failure onto the bypass enum. ``None`` is not expected.

    A failure that reaches the guard must never be recorded as an unclassified error;
    ``TRANSFORM_ERROR`` is the terminal fallback, not the default answer.
    """
    if isinstance(error, CapabilityLoss):
        return BypassReason.CAPABILITY_LOSS
    if isinstance(error, ValidationFailure):
        return BypassReason.VALIDATION_FAILURE
    return BypassReason.TRANSFORM_ERROR
