"""I1 — the immutable original request.

The original is snapshotted **structurally**: nested dicts become read-only mappings and
lists become tuples. A caller cannot mutate the snapshot through the object it was built
from, because nothing mutable is retained. ``as_messages`` hands back a fresh deep copy,
so a mutation of *that* cannot reach back into the snapshot either.

The pre-existing client shallow-copies; this replaces that with a deep freeze.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


def _freeze(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return value
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value

def _thaw(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value

@dataclass(frozen=True, slots=True)
class FrozenOriginal:
    """A deep-frozen snapshot of the messages as received."""

    _messages: tuple[Any, ...]

    @classmethod
    def freeze(cls, messages: list[dict[str, Any]]) -> FrozenOriginal:
        if not isinstance(messages, list):
            raise TypeError("messages must be a list of mappings")
        for message in messages:
            if not isinstance(message, dict):
                raise TypeError("every message must be a mapping")
        # copy.deepcopy first so the caller's objects are never referenced.
        snapshot = _freeze(copy.deepcopy(messages))
        return cls(_messages=snapshot)

    def as_messages(self) -> list[dict[str, Any]]:
        """Return a fresh deep copy. Mutating it cannot affect this snapshot."""
        thawed = _thaw(self._messages)
        return copy.deepcopy(thawed)

    def __len__(self) -> int:
        return len(self._messages)
