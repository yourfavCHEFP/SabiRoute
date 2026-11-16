"""R6.4 — the compression reimplementation.

``litellm.compress()`` is **rejected** and is not imported. Its retrieval-tool injection,
ASCII-only tokenizer, 70/30 line split, foreign token counter and hard-coded trigger make
it unusable here. Two of its ideas are genuinely right and are reimplemented:

1. **Protected indices** — system messages, the last user message, the last assistant
   message, and *every message up to and including the last Anthropic ``cache_control``
   breakpoint*. The cache rule is load-bearing: rewriting a row inside a cached prefix
   turns the next request's cache *read* into a cache *write*, which makes compression
   **more** expensive than not compressing at all.
2. **Atomic tool-exchange spans** — a tool call and its results are removed together or
   not at all, so pairing is never broken.

Four explicit decisions (work order §B3):

* **Granularity — whole messages.** Sub-message truncation can split a JSON body or a tool
  payload. Whole-message removal is atomic and reversible. The "a constraint buried in a
  dropped message is deleted with it" risk is mitigated by the protected set below.
* **Truncation safety — no partial content rewriting, ever.** Content is never edited, so
  valid JSON and intact tool calls are guaranteed by construction rather than by a check.
* **Token accounting — one estimator.** The repository's own
  ``security.budgets.estimate_input_tokens`` is used and injected, so reservation and
  "tokens saved" cannot disagree. When it fails closed (e.g. multimodal), compression is
  **skipped** rather than guessed.
* **Bypass surface — a policy enum plus request correlation**, not "protected indices
  only". See ``bypass.py``.
"""

from __future__ import annotations

from typing import Any, Protocol


class TokenCounter(Protocol):
    def __call__(self, messages: list[dict[str, Any]]) -> int | None: ...

def _has_cache_control(message: dict[str, Any]) -> bool:
    if "cache_control" in message:
        return True
    content = message.get("content")
    if isinstance(content, list):
        return any(
            isinstance(block, dict) and "cache_control" in block for block in content
        )
    return False

def protected_indices(messages: list[dict[str, Any]]) -> frozenset[int]:
    """Indices that must never be removed."""
    protected: set[int] = set()

    for index, message in enumerate(messages):
        if message.get("role") == "system":
            protected.add(index)

    last_user = max(
        (i for i, m in enumerate(messages) if m.get("role") == "user"), default=None
    )
    last_assistant = max(
        (i for i, m in enumerate(messages) if m.get("role") == "assistant"), default=None
    )
    if last_user is not None:
        protected.add(last_user)
    if last_assistant is not None:
        protected.add(last_assistant)

    # Every message up to and including the last cache_control breakpoint.
    last_breakpoint = max(
        (i for i, m in enumerate(messages) if _has_cache_control(m)), default=None
    )
    if last_breakpoint is not None:
        protected.update(range(last_breakpoint + 1))

    return frozenset(protected)

def tool_spans(messages: list[dict[str, Any]]) -> list[tuple[int, ...]]:
    """Contiguous spans of an assistant tool call and the results answering it."""
    spans: list[tuple[int, ...]] = []
    index = 0
    while index < len(messages):
        calls = messages[index].get("tool_calls")
        if isinstance(calls, list) and calls:
            call_ids = {
                call.get("id") for call in calls if isinstance(call, dict)
            }
            span = [index]
            following = index + 1
            while following < len(messages) and messages[following].get("role") == "tool":
                if messages[following].get("tool_call_id") in call_ids:
                    span.append(following)
                    following += 1
                else:
                    break
            spans.append(tuple(span))
            index = following
        else:
            index += 1
    return spans

def compress(
    messages: list[dict[str, Any]],
    *,
    max_ratio: float | None,
    count_tokens: TokenCounter,
) -> list[dict[str, Any]]:
    """Return the messages to send. ``max_ratio`` is an owner slot; ``None`` means off."""
    if max_ratio is None:
        return list(messages)

    baseline = count_tokens(messages)
    if baseline is None or baseline <= 0:
        # The estimator failed closed. Skipping is the only honest option.
        return list(messages)

    target = baseline * max_ratio
    protected = protected_indices(messages)

    atomic_of: dict[int, tuple[int, ...]] = {}
    for span in tool_spans(messages):
        for member in span:
            atomic_of[member] = span

    removed: set[int] = set()

    def current_tokens() -> int:
        kept = [m for i, m in enumerate(messages) if i not in removed]
        return count_tokens(kept) or 0

    if current_tokens() <= target:
        return list(messages)

    for index in range(len(messages)):  # oldest first
        if current_tokens() <= target:
            break
        if index in protected or index in removed:
            continue
        members = atomic_of.get(index)
        if members is not None:
            if any(member in protected for member in members):
                continue
            if len(removed) + len(members) >= len(messages):
                continue
            removed.update(members)
        else:
            removed.add(index)

    result = [m for i, m in enumerate(messages) if i not in removed]
    if not result:
        return list(messages)
    return result
