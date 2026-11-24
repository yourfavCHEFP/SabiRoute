"""Pure helper branches inside the completions handler.

These decide what telemetry is reported when usage is partial or absent, and
what a malformed SSE frame contributes. They are separated from the endpoint
because each is a self-contained answer to a malformed input.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from sabiroute.api.completions import (
    _actual_cost,
    _actual_tokens,
    _record_usage,
    _sse_usage,
    _sum_actual_tokens,
)


class _UsageRecorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def record(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


def test_usage_with_no_readable_token_counts_records_nothing() -> None:
    recorder = _UsageRecorder()
    state = SimpleNamespace(usage=recorder)

    _record_usage(
        state,
        "primary",
        {"usage": {"prompt_tokens": "unknown", "completion_tokens": False}},
    )

    assert recorder.calls == []


def test_actual_tokens_with_no_usable_field_returns_none() -> None:
    assert _actual_tokens({"usage": {"prompt_tokens": None}}) is None


def test_summing_derives_a_total_from_known_parts() -> None:
    assert _sum_actual_tokens([(1, 2, None)]) == (1, 2, 3)


def test_a_malformed_sse_frame_contributes_no_usage() -> None:
    assert _sse_usage(b"data: not-json\n\n") is None


def test_cost_is_unavailable_when_a_token_count_is_missing() -> None:
    assert _actual_cost(object(), [("primary", (None, 5, 6))], False) is None
