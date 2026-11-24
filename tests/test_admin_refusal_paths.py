"""Refusal paths for the admin API.

Every branch here is a refusal the admin surface must return rather than
silently succeed: missing accounting, a key that cannot be rotated, a limit or
budget that the store declined to write, and an unbuildable budget. The
endpoint coroutines are called directly with a stand-in application state so
the assertions are about the HTTP outcome, not about routing.
"""
from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from sabiroute.api import admin as admin_module
from sabiroute.api.admin import ApiKeyBudgetRequest, ApiKeyRateLimitRequest


class _NullExecutor:
    async def run(self, _func: Any, *_args: Any, **_kwargs: Any) -> None:
        return None


class _FalseExecutor:
    async def run(self, _func: Any, *_args: Any, **_kwargs: Any) -> bool:
        return False


class _CallThroughExecutor:
    async def run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)


def _store(*, writes: bool = False) -> Any:
    """A key store whose writes succeed or refuse, per the case under test."""
    return SimpleNamespace(
        get=lambda _key_id: SimpleNamespace(revoked_at=None),
        set_rate_limit=lambda _key_id, _limit: writes,
        set_budget=lambda _key_id, _budget: writes,
    )


def _request(state: Any) -> Any:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(gateway=state)))


def _status_of(call: Any) -> int:
    with pytest.raises(HTTPException) as excinfo:
        call()
    return excinfo.value.status_code


def test_key_store_helper_refuses_when_accounting_is_unavailable() -> None:
    request = _request(SimpleNamespace(key_store=None))

    assert _status_of(lambda: admin_module._key_store(request)) == 503


def test_rotation_reports_a_key_that_cannot_be_rotated() -> None:
    state = SimpleNamespace(key_store=object(), store_executor=_NullExecutor())
    request = _request(state)

    status = _status_of(
        lambda: asyncio.run(admin_module.rotate_client_api_key("key-1", request))
    )

    assert status == 404


def test_rate_limit_is_refused_for_an_unknown_key() -> None:
    store = SimpleNamespace(get=lambda _key_id: None)
    state = SimpleNamespace(key_store=store, store_executor=_CallThroughExecutor())
    payload = ApiKeyRateLimitRequest(requests_per_minute=10, burst_capacity=10)

    status = _status_of(
        lambda: asyncio.run(
            admin_module.set_client_rate_limit("key-1", payload, _request(state))
        )
    )

    assert status == 404


def test_rate_limit_is_refused_when_the_store_declines_to_write() -> None:
    store = SimpleNamespace(
        get=lambda _key_id: SimpleNamespace(revoked_at=None),
        set_rate_limit=lambda _key_id, _limit: False,
    )
    state = SimpleNamespace(key_store=store, store_executor=_CallThroughExecutor())
    payload = ApiKeyRateLimitRequest(requests_per_minute=10, burst_capacity=10)

    status = _status_of(
        lambda: asyncio.run(
            admin_module.set_client_rate_limit("key-1", payload, _request(state))
        )
    )

    assert status == 404


def test_clearing_a_rate_limit_is_refused_for_an_unknown_key() -> None:
    state = SimpleNamespace(key_store=_store(), store_executor=_FalseExecutor())

    status = _status_of(
        lambda: asyncio.run(
            admin_module.clear_client_rate_limit("key-1", _request(state))
        )
    )

    assert status == 404


def test_an_unbuildable_budget_is_rejected_before_any_write() -> None:
    state = SimpleNamespace(key_store=_store(writes=True), store_executor=_FalseExecutor())
    # model_construct bypasses the request model's own constraints so the
    # value reaches ApiKeyBudget, which is what this test is about.
    payload = ApiKeyBudgetRequest.model_construct(daily_tokens=0)

    status = _status_of(
        lambda: asyncio.run(
            admin_module.set_client_budget("key-1", payload, _request(state))
        )
    )

    assert status == 422


def test_a_budget_is_refused_when_the_store_declines_to_write() -> None:
    state = SimpleNamespace(key_store=_store(), store_executor=_FalseExecutor())
    payload = ApiKeyBudgetRequest(daily_tokens=100)

    status = _status_of(
        lambda: asyncio.run(
            admin_module.set_client_budget("key-1", payload, _request(state))
        )
    )

    assert status == 404


def test_clearing_a_budget_is_refused_for_an_unknown_key() -> None:
    state = SimpleNamespace(key_store=_store(), store_executor=_FalseExecutor())

    status = _status_of(
        lambda: asyncio.run(admin_module.clear_client_budget("key-1", _request(state)))
    )

    assert status == 404


class _AwaitingExecutor:
    """Runs the delegated call, awaiting it when it is a coroutine."""

    async def run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result


def test_reconcile_refuses_a_key_without_a_lineage() -> None:
    store = SimpleNamespace(get=lambda _key_id: SimpleNamespace(lineage_id=None))
    state = SimpleNamespace(key_store=store, store_executor=_AwaitingExecutor())

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(admin_module.reconcile_client_lineage("key-1", _request(state)))

    assert excinfo.value.status_code >= 400
    assert "lineage" in str(excinfo.value.detail)


def test_reconcile_refuses_when_the_store_exposes_no_engine() -> None:
    store = SimpleNamespace(get=lambda _key_id: SimpleNamespace(lineage_id="lineage-1"))
    state = SimpleNamespace(key_store=store, store_executor=_AwaitingExecutor())

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(admin_module.reconcile_client_lineage("key-1", _request(state)))

    assert excinfo.value.status_code >= 400
    assert "unavailable" in str(excinfo.value.detail)
