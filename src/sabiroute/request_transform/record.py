"""I4 — transformation metadata.

Scalars only. **This record never carries message text.** It is a frozen tuple, read-only
to the API layer, and it is the only place a transformation is described.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TransformationRecord:
    """What was done to one request. Counts and hashes only — never text."""

    policy_id: str | None
    policy_version: int
    strategy: str
    original_count: int
    effective_count: int
    original_sha256: str
    effective_sha256: str
    fallback_reason: str | None
    bypass_reason: str | None

    def to_dict(self) -> dict[str, object]:
        """Serialise to scalars only. Used by tests to prove no text leaks."""
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "strategy": self.strategy,
            "original_count": self.original_count,
            "effective_count": self.effective_count,
            "original_sha256": self.original_sha256,
            "effective_sha256": self.effective_sha256,
            "fallback_reason": self.fallback_reason,
            "bypass_reason": self.bypass_reason,
        }
