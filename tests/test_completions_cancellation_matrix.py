"""Cancellation swept across the whole request, not at one chosen instant.

The handler's accounting layer has different cleanup code for every await it
can be cancelled at: the attempt, the snapshot write, the finalize, the
budget release and the quota release. Rather than pick one instant per
branch, these tests cancel at a range of offsets into the request and assert
the same invariant every time: whatever the schedule, no reservation is left
held and at most one usage event is finalized.

The store is slowed deliberately so that each accounting call spends real
time in a worker thread; that is what gives the sweep something to land on.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from starlette.requests import Request

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.quotas import QuotaPolicy
from sabiroute.security.keys import (
    SABI_USER_ID_FIELD,
    ApiKeyBudget,
    ApiKeyIdentity,
    issue_api_key,
)

UID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
SLOW = 0.002


class _SlowStore(InMemoryApiKeyStore):
    """Every accounting call spends time in its worker thread.

    Successful holds and their cleanups are counted here so the invariant is
    expressed directly: a hold that was taken must be released or settled.
    """

    def __init__(self) -> None:
        super().__init__()
        self.budget_holds = 0
        self.budget_cleanups = 0
        self.quota_holds = 0
        self.quota_cleanups = 0

    def _delay(self) -> None:
        time.sleep(SLOW)

    def check_and_reserve_quota(self, *a: Any, **k: Any) -> Any:
        self._delay()
        result = super().check_and_reserve_quota(*a, **k)
        if result:
            self.quota_holds += 1
        return result

    def release_quota(self, *a: Any, **k: Any) -> Any:
        self._delay()
        self.quota_cleanups += 1
        return super().release_quota(*a, **k)

    def settle_quota(self, *a: Any, **k: Any) -> Any:
        self._delay()
        self.quota_cleanups += 1
        return super().settle_quota(*a, **k)

    def reserve_budget(self, *a: Any, **k: Any) -> Any:
        self._delay()
        result = super().reserve_budget(*a, **k)
        if result is None:
            self.budget_holds += 1
        return result

    def release_budget(self, *a: Any, **k: Any) -> Any:
        self._delay()
        self.budget_cleanups += 1
        return super().release_budget(*a, **k)

    def reconcile_budget(self, *a: Any, **k: Any) -> Any:
        self._delay()
        self.budget_cleanups += 1
        return super().reconcile_budget(*a, **k)

    def get_shared_inference(self) -> Any:
        self._delay()
        return super().get_shared_inference()

    def append_pre_routing_feature_snapshot(self, *a: Any, **k: Any) -> Any:
        self._delay()
        return super().append_pre_routing_feature_snapshot(*a, **k)

    def finalize_usage_event(self, *a: Any, **k: Any) -> Any:
        self._delay()
        return super().finalize_usage_event(*a, **k)


class _SlowClient(StubLiteLLMClient):
    async def chat_completion(self, *a: Any, **k: Any) -> Any:
        await asyncio.sleep(SLOW * 2)
        return await super().chat_completion(*a, **k)


def _request(state: Any, record: Any) -> Request:
    app = create_app(state=state)
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 1),
            "server": ("test", 80),
            "app": app,
            "state": {
                "api_identity": ApiKeyIdentity(key_id=record.key_id, project_id=record.project_id)
            },
        }
    )


def _budget_case() -> tuple[Any, Any, ChatCompletionRequest]:
    store = _SlowStore()
    state = build_gateway_state(config=make_config(), client=_SlowClient(), key_store=store)
    record, _secret = issue_api_key(store, project_id="proj-1", name="key")
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))
    payload = ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
        }
    )
    return state, record, payload


def _quota_case() -> tuple[Any, Any, ChatCompletionRequest]:
    store = _SlowStore()
    state = build_gateway_state(
        config=make_config(),
        client=_SlowClient(),
        key_store=store,
        free_pool=FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"})),
        quota_policy=QuotaPolicy(pilot_users=frozenset({UID})),
    )
    record, _secret = issue_api_key(store, project_id="sabichat-service", name="service")
    state.sabichat_service_key_id = record.key_id
    store.shared_inference = True
    payload = ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
            "sabi_route_free_chat": True,
            SABI_USER_ID_FIELD: UID,
        }
    )
    return state, record, payload


def _assert_invariants(store: _SlowStore) -> None:
    # A hold that was taken must have been released or settled exactly once;
    # never twice, and never left behind.
    assert store.budget_holds == store.budget_cleanups
    assert store.quota_holds == store.quota_cleanups
    assert store.finalize_calls <= 1


def _run_case(maker: Any, delay: float, cancels: int) -> None:
    state, record, payload = maker()
    store = state.key_store

    async def scenario() -> None:
        task = asyncio.create_task(chat_completions(payload, _request(state, record)))
        await asyncio.sleep(delay)
        for _ in range(cancels):
            task.cancel()
            await asyncio.sleep(SLOW / 2)
        await asyncio.gather(task, return_exceptions=True)

    asyncio.run(scenario())
    _assert_invariants(store)


@pytest.mark.parametrize("delay", [0.0, 0.001, 0.003, 0.005, 0.008, 0.012, 0.02])
def test_budget_cancellation_at_any_offset_leaves_no_hold(delay: float) -> None:
    _run_case(_budget_case, delay, cancels=1)


@pytest.mark.parametrize("delay", [0.0, 0.001, 0.003, 0.005, 0.008, 0.012, 0.02])
def test_quota_cancellation_at_any_offset_leaves_no_hold(delay: float) -> None:
    _run_case(_quota_case, delay, cancels=1)


@pytest.mark.parametrize("delay", [0.0, 0.002, 0.004, 0.006, 0.01])
def test_repeated_cancellation_at_any_offset_leaves_no_hold(delay: float) -> None:
    _run_case(_budget_case, delay, cancels=3)
    _run_case(_quota_case, delay, cancels=3)


@pytest.mark.parametrize("delay", [0.002, 0.006, 0.012])
def test_a_burst_of_cancellations_is_still_compensated(delay: float) -> None:
    # Ten cancellations in quick succession, more than the shield's re-wait
    # loop would see from a single client disconnection.
    _run_case(_budget_case, delay, cancels=10)
    _run_case(_quota_case, delay, cancels=10)
