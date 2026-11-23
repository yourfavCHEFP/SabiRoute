"""Phase 18: token-usage and cost accounting helpers.

The settlement tests exercise these paths through the HTTP surface. These
unit tests pin the helpers themselves, where a silent change (a dropped
total, a bool accepted as a token count, a wrong divisor) would otherwise
only surface as wrong money.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from sabiroute.api.completions import (
    _actual_cost,
    _actual_tokens,
    _record_usage,
    _safe_token_count,
    _sum_actual_tokens,
    _usage_object,
)
from sabiroute.monitoring.usage import UsageTracker
from sabiroute.providers.base import ProviderDeployment, ProviderInfo
from sabiroute.providers.registry import ProviderRegistry


def test_usage_object_prefers_the_top_level_usage() -> None:
    body = {
        "usage": {"prompt_tokens": 1},
        "error": {"usage": {"prompt_tokens": 99}},
    }

    assert _usage_object(body) == {"prompt_tokens": 1}


def test_usage_object_falls_back_to_error_usage() -> None:
    assert _usage_object({"error": {"usage": {"prompt_tokens": 2}}}) == {
        "prompt_tokens": 2
    }
    # A non-mapping top-level usage lets the error payload supply it.
    assert _usage_object(
        {"usage": "bad", "error": {"usage": {"prompt_tokens": 3}}}
    ) == {"prompt_tokens": 3}


@pytest.mark.parametrize(
    "body", [None, "not-a-body", {"usage": None}, {"usage": [1, 2]}, {}]
)
def test_usage_object_rejects_missing_or_malformed_usage(body: object) -> None:
    assert _usage_object(body) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [(5, 5), (0, 0), (True, None), (-1, None), (3.0, None), ("5", None), (None, None)],
)
def test_safe_token_count_accepts_only_non_negative_ints(
    value: object, expected: int | None
) -> None:
    # ``bool`` is an ``int`` subclass but must never count as tokens.
    assert _safe_token_count(value) == expected


def test_actual_tokens_reports_all_three_when_present() -> None:
    assert _actual_tokens(
        {"usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 9}}
    ) == (2, 3, 9)


def test_actual_tokens_synthesises_a_missing_total() -> None:
    assert _actual_tokens({"usage": {"prompt_tokens": 2, "completion_tokens": 3}}) == (
        2,
        3,
        5,
    )


def test_actual_tokens_does_not_invent_a_partial_total() -> None:
    # Total can only be derived when both parts are known.
    assert _actual_tokens({"usage": {"prompt_tokens": 2}}) == (2, None, None)
    assert _actual_tokens({"usage": {"completion_tokens": 4}}) == (None, 4, None)


@pytest.mark.parametrize("body", [{}, {"usage": {}}, {"usage": {"prompt_tokens": -1}}])
def test_actual_tokens_is_none_when_nothing_usable(body: object) -> None:
    assert _actual_tokens(body) is None


def test_sum_actual_tokens_adds_each_component_independently() -> None:
    parts = [(2, 3, None), (None, None, 7)]

    # Total comes from the part that reported one; it is not re-derived.
    assert _sum_actual_tokens(parts) == (2, 3, 7)


def test_sum_actual_tokens_synthesises_total_only_when_absent() -> None:
    assert _sum_actual_tokens([(2, None, None), (3, 4, None)]) == (5, 4, 9)
    assert _sum_actual_tokens([(1, 1, 5), (2, 2, None)]) == (3, 3, 5)


@pytest.mark.parametrize("parts", [[], [(None, None, None)]])
def test_sum_actual_tokens_of_nothing_is_empty(parts: list) -> None:
    assert _sum_actual_tokens(parts) == (None, None, None)


def test_record_usage_records_prompt_and_completion() -> None:
    usage = UsageTracker()
    state = SimpleNamespace(usage=usage)

    _record_usage(
        state, "a", {"usage": {"prompt_tokens": 3, "completion_tokens": 2}}
    )

    observed = [
        (r.model, r.prompt_tokens, r.completion_tokens, r.total_tokens)
        for r in usage.records
    ]
    assert observed == [("a", 3, 2, 5)]


def test_record_usage_defaults_a_missing_completion_to_zero() -> None:
    usage = UsageTracker()
    state = SimpleNamespace(usage=usage)

    _record_usage(state, "a", {"usage": {"prompt_tokens": 4}})

    assert usage.records[0].completion_tokens == 0
    assert usage.records[0].total_tokens == 4


def test_record_usage_accepts_error_usage_but_skips_unusable_bodies() -> None:
    usage = UsageTracker()
    state = SimpleNamespace(usage=usage)

    _record_usage(state, "skipped", {})
    _record_usage(state, "errored", {"error": {"usage": {"prompt_tokens": 7}}})

    assert [record.model for record in usage.records] == ["errored"]
    assert usage.records[0].prompt_tokens == 7


def _priced_state() -> SimpleNamespace:
    registry = ProviderRegistry(
        providers=[ProviderInfo(name="prov", display_name="Prov")],
        deployments=[
            ProviderDeployment(
                name="priced",
                provider="prov",
                model="prov/m",
                input_cost_per_million_tokens=Decimal("2"),
                output_cost_per_million_tokens=Decimal("6"),
            ),
            ProviderDeployment(name="unpriced", provider="prov", model="prov/n"),
        ],
    )
    return SimpleNamespace(registry=registry)


def test_actual_cost_computes_the_decimal_charge() -> None:
    cost = _actual_cost(_priced_state(), [("priced", (1000, 2000, 3000))], False)

    # (1000 * 2 + 2000 * 6) / 1_000_000
    assert cost == Decimal("0.014")


def test_actual_cost_sums_across_attempts() -> None:
    cost = _actual_cost(
        _priced_state(), [("priced", (1, 1, 2)), ("priced", (1, 1, 2))], False
    )

    assert cost == Decimal("0.000016")


@pytest.mark.parametrize(
    ("parts", "has_unknown_usage"),
    [
        ([("priced", (1000, 2000, 3000))], True),  # unknown usage
        ([], False),  # nothing to price
        ([("priced", (None, 1, 2))], False),  # missing prompt count
        ([("unpriced", (1, 1, 2))], False),  # deployment has no prices
    ],
)
def test_actual_cost_is_none_when_it_cannot_be_known(parts: list, has_unknown_usage: bool) -> None:
    assert _actual_cost(_priced_state(), parts, has_unknown_usage) is None
