"""I6 — capability preservation.

Reuses the existing ``Capability`` enum. **No new enum is introduced.** If a transform
would drop a capability the request requires, the transform hard-fails to the original:
eligibility was decided on the original, so a later transform must not invalidate it.
"""

from __future__ import annotations

from typing import Any

from ..capabilities import Capability
from .errors import CapabilityLoss

_MULTIMODAL_CAPABILITIES = frozenset({Capability.VISION, Capability.MULTIMODAL})


def _has_non_text_content(message: dict[str, Any]) -> bool:
    content = message.get("content")
    if isinstance(content, list):
        return any(
            isinstance(block, dict) and block.get("type") not in (None, "text") for block in content
        )
    return False


def _has_tool_calls(message: dict[str, Any]) -> bool:
    calls = message.get("tool_calls")
    return isinstance(calls, list) and bool(calls)


def check_capability_preservation(
    original: list[dict[str, Any]],
    effective: list[dict[str, Any]],
    required: frozenset[Capability],
) -> None:
    """Raise ``CapabilityLoss`` if the transform dropped a required capability."""
    if not required:
        return

    kept = {id(message) for message in effective}
    dropped = [message for message in original if id(message) not in kept]
    if not dropped:
        return

    if required & _MULTIMODAL_CAPABILITIES:
        if any(_has_non_text_content(message) for message in dropped):
            raise CapabilityLoss("transform would drop multimodal content the request requires")

    if Capability.TOOL_USE in required:
        if any(_has_tool_calls(message) for message in dropped):
            raise CapabilityLoss("transform would drop a tool call the request requires")
