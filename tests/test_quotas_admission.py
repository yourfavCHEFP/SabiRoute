"""Behavioural tests for :mod:`sabiroute.quotas` admission.

The admission helper is the only quota code path that decides whether a
pilot request proceeds, so its contract is: reserve atomically through the
bounded store executor, admit only on an explicit reservation, and deny with
a stable reason on every abnormal shape (missing store, missing executor,
raised error, refused reservation).
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from sabiroute.quotas import (
    DAILY_TOKEN_QUOTA,
    QUOTA_EXCEEDED,
    QUOTA_UNAVAILABLE,
    QuotaPolicy,
    check_quota_admission,
    quota_reset_at,
    quota_window_start,
)

WINDOW = datetime(2026, 11, 24, tzinfo=UTC)


class _RecordingExecutor:
    """Stand-in for BoundedStoreExecutor that records the dispatched call."""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[Any, tuple[Any, ...]]] = []
        self._result = result
        self._error = error

    async def run(self, func: Any, *args: Any) -> Any:
        self.calls.append((func, args))
        if self._error is not None:
            raise self._error
        return self._result


class _Store:
    def __init__(self) -> None:
        self.invocations: list[tuple[Any, ...]] = []

    def check_and_reserve_quota(self, *args: Any) -> bool:
        self.invocations.append(args)
        return True


def _admit(state: Any, store: Any, **overrides: Any) -> str | None:
    params: dict[str, Any] = {
        "user_id": "user-1",
        "request_id": "req-1",
        "estimate": 128,
        "window_start": WINDOW,
        "quota": DAILY_TOKEN_QUOTA,
    }
    params.update(overrides)
    return asyncio.run(check_quota_admission(state, store, **params))


def test_admission_denies_when_store_is_missing() -> None:
    state = SimpleNamespace(store_executor=_RecordingExecutor(result=True))

    assert _admit(state, None) == QUOTA_UNAVAILABLE


def test_admission_denies_when_executor_is_missing() -> None:
    assert _admit(SimpleNamespace(), _Store()) == QUOTA_UNAVAILABLE


def test_admission_reserves_through_the_executor_and_admits() -> None:
    executor = _RecordingExecutor(result=True)
    store = _Store()

    assert _admit(SimpleNamespace(store_executor=executor), store) is None

    assert len(executor.calls) == 1
    dispatched, args = executor.calls[0]
    assert dispatched == store.check_and_reserve_quota
    assert args == ("user-1", "req-1", 128, WINDOW, DAILY_TOKEN_QUOTA)


def test_admission_reports_exceeded_when_reservation_is_refused() -> None:
    executor = _RecordingExecutor(result=False)

    assert _admit(SimpleNamespace(store_executor=executor), _Store()) == QUOTA_EXCEEDED


def test_admission_denies_when_reservation_raises() -> None:
    executor = _RecordingExecutor(error=RuntimeError("database is down"))

    assert _admit(SimpleNamespace(store_executor=executor), _Store()) == QUOTA_UNAVAILABLE


def test_admission_treats_missing_state_attribute_as_unavailable() -> None:
    assert _admit(object(), _Store()) == QUOTA_UNAVAILABLE


# --- window and policy helpers ------------------------------------------


def test_window_start_truncates_to_utc_midnight() -> None:
    moment = datetime(2026, 11, 24, 23, 59, 59, 999999, tzinfo=UTC)

    assert quota_window_start(moment) == datetime(2026, 11, 24, tzinfo=UTC)


def test_window_start_converts_offsets_before_truncating() -> None:
    # 02:30+02:00 on the 25th is 00:30 UTC on the 25th, not the 24th.
    moment = datetime(2026, 11, 25, 2, 30, tzinfo=timezone(timedelta(hours=2)))

    assert quota_window_start(moment) == datetime(2026, 11, 25, tzinfo=UTC)


def test_reset_is_exactly_one_day_after_window_start() -> None:
    start = datetime(2026, 11, 24, tzinfo=UTC)

    assert quota_reset_at(start) == datetime(2026, 11, 25, tzinfo=UTC)


def test_reset_normalises_a_non_midnight_start() -> None:
    start = datetime(2026, 11, 24, 13, 45, tzinfo=UTC)

    assert quota_reset_at(start) == datetime(2026, 11, 25, tzinfo=UTC)


def test_reset_crosses_a_month_boundary() -> None:
    start = datetime(2026, 11, 30, tzinfo=UTC)

    assert quota_reset_at(start) == datetime(2026, 12, 1, tzinfo=UTC)


def test_policy_from_env_defaults_to_nobody(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SABIROUTE_QUOTA_PILOT_USERS", raising=False)

    policy = QuotaPolicy.from_env()

    assert policy.pilot_users == frozenset()
    assert policy.daily_tokens == DAILY_TOKEN_QUOTA


def test_policy_from_env_parses_and_trims_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SABIROUTE_QUOTA_PILOT_USERS", " user-a , user-b ,, ")

    assert QuotaPolicy.from_env().pilot_users == frozenset({"user-a", "user-b"})


def test_policy_from_env_treats_empty_string_as_nobody(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SABIROUTE_QUOTA_PILOT_USERS", "")

    assert QuotaPolicy.from_env().pilot_users == frozenset()


def test_covers_only_enrolled_string_ids() -> None:
    policy = QuotaPolicy(pilot_users=frozenset({"user-a"}))

    assert policy.covers("user-a") is True
    assert policy.covers("user-b") is False
    assert policy.covers(None) is False
    assert policy.covers("") is False
