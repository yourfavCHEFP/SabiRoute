"""I3 — the effective request.

A frozen value derived **once** per logical request. Re-derivation per attempt is
forbidden: two derivations of one request would split a single reservation across two
shapes, and the reservation is taken on the original.

The effective request is the **sole provider reader** after this point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes
from .errors import EffectiveRequestError


@dataclass(frozen=True, slots=True)
class EffectiveRequest:
    """The request the provider will actually see."""

    messages: tuple[dict[str, Any], ...]
    policy_id: str | None
    policy_version: int
    shrunk: bool

    def as_messages(self) -> list[dict[str, Any]]:
        return [dict(message) for message in self.messages]

    def byte_length(self) -> int:
        return len(canonical_bytes(list(self.messages)))


def derive_effective(
    original: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    *,
    policy_id: str | None,
    policy_version: int,
) -> EffectiveRequest:
    """Build an effective request from already-transformed messages.

    Enforces I3's **monotone-shrink** invariant: the effective request may never be
    larger than the original it replaces.
    """
    original_bytes = canonical_bytes(original)
    effective_bytes = canonical_bytes(messages)
    if len(effective_bytes) > len(original_bytes):
        raise EffectiveRequestError(
            "effective request expands the original; monotone-shrink violated"
        )
    return EffectiveRequest(
        messages=tuple(dict(message) for message in messages),
        policy_id=policy_id,
        policy_version=policy_version,
        shrunk=len(effective_bytes) < len(original_bytes),
    )
