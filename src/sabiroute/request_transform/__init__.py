"""R6.2-R6.5 — the request-transform pipeline.

Ships **dark**: ``OptimizationPolicy.enabled`` defaults to ``False``, so ``run`` returns the
original request untouched. Nothing in this package is imported by the request path until
that flag is flipped by the owner.

See ``artifacts/sprint-phoenix/R6.1-FOUNDATION-CONTRACT.md`` for the I1-I9 contracts.
"""

from __future__ import annotations

from .bypass import BypassDecision, BypassReason, evaluate_bypass
from .canonical import canonical_bytes, is_canonical, within_budget, within_byte_budget
from .capability import check_capability_preservation
from .compression import compress, protected_indices, tool_spans
from .effective import EffectiveRequest, derive_effective
from .errors import (
    CanonicalisationError,
    CapabilityLoss,
    EffectiveRequestError,
    TransformError,
    ValidationFailure,
)
from .frozen import FrozenOriginal
from .guard import fail_to_original
from .pipeline import TransformOutcome, default_token_counter, run
from .record import TransformationRecord
from .validation import MAX_BYTES, MAX_CHARS, MAX_MESSAGES, validate_effective

__all__ = [
    "MAX_BYTES",
    "MAX_CHARS",
    "MAX_MESSAGES",
    "BypassDecision",
    "BypassReason",
    "CanonicalisationError",
    "CapabilityLoss",
    "EffectiveRequest",
    "EffectiveRequestError",
    "FrozenOriginal",
    "TransformError",
    "TransformOutcome",
    "TransformationRecord",
    "ValidationFailure",
    "canonical_bytes",
    "check_capability_preservation",
    "compress",
    "default_token_counter",
    "derive_effective",
    "evaluate_bypass",
    "fail_to_original",
    "is_canonical",
    "protected_indices",
    "run",
    "tool_spans",
    "validate_effective",
    "within_budget",
    "within_byte_budget",
]
