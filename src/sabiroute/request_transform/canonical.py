"""I2 — the canonical representation.

One defined form for comparison and hashing: UTF-8 JSON, keys in insertion order,
compact separators, no ASCII escaping. The form is:

* **deterministic** — the same messages always produce the same bytes;
* **idempotent** — canonicalising the parsed canonical form reproduces it exactly;
* **non-expanding** — the canonical bytes are never longer than the input's default JSON.

Anything that cannot be canonicalised raises ``CanonicalisationError``, which I9 degrades
to the original. It is never surfaced as a 4xx.
"""

from __future__ import annotations

import json
from typing import Any

from .errors import CanonicalisationError


def canonical_bytes(messages: Any) -> bytes:
    """Return the canonical UTF-8 bytes of ``messages``."""
    if not isinstance(messages, (list, tuple)):
        raise CanonicalisationError("messages must be a sequence")
    try:
        # Parse once so a canonical round-trip is genuinely idempotent.
        structure = json.loads(json.dumps(list(messages), ensure_ascii=False, default=_strict))
    except (TypeError, ValueError) as exc:
        raise CanonicalisationError(f"messages are not JSON-representable: {exc}") from exc
    return json.dumps(
        structure,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")

def _strict(value: Any) -> Any:
    raise CanonicalisationError(f"unsupported value type: {type(value).__name__}")

def is_canonical(messages: Any) -> bool:
    """True when re-canonicalising the parsed form reproduces the same bytes."""
    first = canonical_bytes(messages)
    second = canonical_bytes(json.loads(first))
    return first == second

def within_budget(original: bytes, canonical: bytes) -> bool:
    """The canonical form must never expand (I2 limits: output <= input)."""
    return len(canonical) <= len(original)
