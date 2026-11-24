"""Behavioural tests for :mod:`sabiroute.security.budgets`.

Covers the byte-based input estimate (including its fail-closed guards) and
the worst-case cost quote, whose contract is: any deployment that cannot be
priced makes the whole quote unknown, and the quote is the maximum across
candidates rather than the cheapest.
"""
from __future__ import annotations

import json
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from sabiroute.security.budgets import (
    UnsupportedBudgetRequest,
    estimate_input_tokens,
    estimated_cost_usd,
)


def _deployment(input_price: Any, output_price: Any) -> Any:
    """Structural stand-in for ProviderDeployment -- only prices are read."""
    return SimpleNamespace(
        input_cost_per_million_tokens=input_price,
        output_cost_per_million_tokens=output_price,
    )


def _expected_estimate(messages: list[dict[str, Any]]) -> int:
    serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))
    return len(serialized.encode("utf-8")) + len(messages) * 16 + 4


# --- estimate_input_tokens ----------------------------------------------


def test_estimate_matches_documented_byte_upper_bound() -> None:
    messages = [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "hello there"},
    ]

    assert estimate_input_tokens(messages) == _expected_estimate(messages)


def test_estimate_counts_utf8_bytes_not_characters() -> None:
    messages = [{"role": "user", "content": "é"}]
    serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))

    assert estimate_input_tokens(messages) == len(serialized.encode("utf-8")) + 16 + 4
    assert len("é".encode("utf-8")) == 2


def test_estimate_rejects_empty_message_list() -> None:
    with pytest.raises(UnsupportedBudgetRequest) as excinfo:
        estimate_input_tokens([])

    assert "At least one message is required." in str(excinfo.value)


def test_estimate_rejects_multimodal_content() -> None:
    messages = [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]

    with pytest.raises(UnsupportedBudgetRequest) as excinfo:
        estimate_input_tokens(messages)

    assert "text-only messages" in str(excinfo.value)


def test_estimate_rejects_non_dict_message() -> None:
    with pytest.raises(UnsupportedBudgetRequest) as excinfo:
        estimate_input_tokens(["hello"])

    assert "text-only messages" in str(excinfo.value)


def test_estimate_rejects_nested_metadata_field() -> None:
    messages = [{"role": "user", "content": "hi", "meta": {"nested": 1}}]

    with pytest.raises(UnsupportedBudgetRequest) as excinfo:
        estimate_input_tokens(messages)

    assert "scalar text metadata" in str(excinfo.value)


def test_estimate_rejects_scalar_metadata_that_still_cannot_serialize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The serialization guard must fail closed even past the scalar checks."""
    messages = [{"role": "user", "content": "hi"}]

    def exploding_dumps(*args: Any, **kwargs: Any) -> str:
        raise TypeError("not serializable")

    monkeypatch.setattr("sabiroute.security.budgets.json.dumps", exploding_dumps)

    with pytest.raises(UnsupportedBudgetRequest) as excinfo:
        estimate_input_tokens(messages)

    assert "cannot be safely estimated" in str(excinfo.value)


# --- estimated_cost_usd -------------------------------------------------


def test_cost_quotes_the_most_expensive_candidate() -> None:
    deployments = [_deployment("2", "10"), _deployment("1", "1")]

    # (1_000_000 in @ 2/M) + (1_000 out @ 10/M) = 2 + 0.01
    assert estimated_cost_usd(deployments, 1_000_000, 1_000) == Decimal("2.01")


def test_cost_returns_zero_for_zero_tokens() -> None:
    assert estimated_cost_usd([_deployment("3", "7")], 0, 0) == Decimal("0")


def test_cost_is_unknown_when_any_price_is_missing() -> None:
    deployments = [_deployment("2", "10"), _deployment(None, "1")]

    assert estimated_cost_usd(deployments, 10, 10) is None


def test_cost_is_unknown_when_output_price_is_missing() -> None:
    assert estimated_cost_usd([_deployment("2", None)], 10, 10) is None


def test_cost_is_unknown_when_price_cannot_be_parsed() -> None:
    assert estimated_cost_usd([_deployment("not-a-number", "1")], 10, 10) is None


def test_cost_is_unknown_when_price_is_not_finite() -> None:
    assert estimated_cost_usd([_deployment("Infinity", "1")], 10, 10) is None


def test_cost_is_unknown_when_price_is_negative() -> None:
    assert estimated_cost_usd([_deployment("-1", "1")], 10, 10) is None


def test_cost_is_unknown_without_deployments() -> None:
    assert estimated_cost_usd([], 10, 10) is None
