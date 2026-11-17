"""I8 — validation of the effective request.

Same caps as I1: 256 messages, 500k characters, 1 MiB of canonical bytes. A failure here
degrades to the original. It is **never** a 4xx: the message says "our optimiser rejected
your request" is a category that does not exist.
"""

from __future__ import annotations

from typing import Any

from .canonical import canonical_bytes
from .errors import ValidationFailure

MAX_MESSAGES = 256
MAX_CHARS = 500_000
MAX_BYTES = 1_048_576


def validate_effective(messages: list[dict[str, Any]]) -> None:
    """Raise ``ValidationFailure`` when the effective request breaks any cap."""
    if not messages:
        raise ValidationFailure("effective request is empty")
    if len(messages) > MAX_MESSAGES:
        raise ValidationFailure(f"effective request exceeds {MAX_MESSAGES} messages")

    characters = 0
    for message in messages:
        if not isinstance(message, dict):
            raise ValidationFailure("effective request contains a non-mapping message")
        role = message.get("role")
        if not isinstance(role, str) or not role:
            raise ValidationFailure("effective request contains a message with no role")
        content = message.get("content")
        if isinstance(content, str):
            characters += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    characters += len(block["text"])
    if characters > MAX_CHARS:
        raise ValidationFailure(f"effective request exceeds {MAX_CHARS} characters")

    if len(canonical_bytes(messages)) > MAX_BYTES:
        raise ValidationFailure(f"effective request exceeds {MAX_BYTES} canonical bytes")
