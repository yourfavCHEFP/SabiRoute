"""Cancellation safety for the accounting reservations.

These are the only tests in the suite that cancel the endpoint at a chosen
instant. They exist to prove two invariants that the handler's comments
describe but nothing else exercises:

1. a request cancelled while a quota reservation is being written does not
   leave that reservation held;
2. a request cancelled while a budget reservation is being written does not
   leave the hold behind.

Both cancel twice: once while the store worker is still running, and again
while the handler is waiting for that worker. That second cancellation is
the schedule the handler's re-wait loop exists for.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from starlette.requests import Request

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.quotas import QuotaPolicy
from sabiroute.security.keys import SABI_USER_ID_FIELD, ApiKeyIdentity, issue_api_key

UID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class _BlockingStore(InMemoryApiKeyStore):
    """Blocks one store call until the test releases it, and counts releases."""

    def __init__(self, *, block: str) -> None:
        super().__init__()
        self._block = block
        self.worker_entered = threading.Event()
        self.worker_release = threading.Event()
        self.release_calls = 0

    def _block_once(self) -> None:
        self.worker_entered.set()
        self.worker_release.wait(timeout=10)

    def check_and_reserve_quota(self, *args: Any, **kwargs: Any) -> bool:
        if self._block == "quota":
            self._block_once()
        return super().check_and_reserve_quota(*args, **kwargs)

    def reserve_budget(self, *args: Any, **kwargs: Any) -> Any:
        if self._block == "budget":
            self._block_once()
        return super().reserve_budget(*args, **kwargs)

    def release_quota(self, *args: Any, **kwargs: Any) -> None:
        self.release_calls += 1
        return super().release_quota(*args, **kwargs)


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


def _quota_state(store: _BlockingStore) -> tuple[Any, Any]:
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=store,
        free_pool=FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"})),
        quota_policy=QuotaPolicy(pilot_users=frozenset({UID})),
    )
    record, _secret = issue_api_key(store, project_id="sabichat-service", name="service")
    state.sabichat_service_key_id = record.key_id
    store.shared_inference = True
    return state, record


def _quota_payload() -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
            "sabi_route_free_chat": True,
            SABI_USER_ID_FIELD: UID,
        }
    )


def _budget_state(store: _BlockingStore) -> tuple[Any, Any]:
    from sabiroute.security.keys import ApiKeyBudget

    state = build_gateway_state(config=make_config(), client=StubLiteLLMClient(), key_store=store)
    record, _secret = issue_api_key(store, project_id="proj-1", name="key")
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))
    return state, record


def _budget_payload() -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
        }
    )


async def _cancel_while_the_worker_runs(task: asyncio.Task[Any], store: Any) -> Any:
    """Cancel twice around a blocked store worker, then let the worker finish."""
    for _ in range(500):
        if store.worker_entered.is_set():
            break
        await asyncio.sleep(0.01)
    assert store.worker_entered.is_set(), "the store worker never started"

    task.cancel()
    # Let the handler observe the first cancellation and enter its wait loop.
    for _ in range(50):
        await asyncio.sleep(0)

    task.cancel()
    for _ in range(50):
        await asyncio.sleep(0)

    store.worker_release.set()
    return (await asyncio.gather(task, return_exceptions=True))[0]


def test_a_cancelled_quota_reservation_is_released() -> None:
    store = _BlockingStore(block="quota")
    state, record = _quota_state(store)

    async def scenario() -> Any:
        task = asyncio.create_task(chat_completions(_quota_payload(), _request(state, record)))
        return await _cancel_while_the_worker_runs(task, store)

    asyncio.run(scenario())

    held = [r for r in store.quota_reservations.values() if r[1] == "reserved"]
    assert held == []
    assert store.release_calls >= 1
    assert store.finalize_calls == 1


def test_a_cancelled_budget_reservation_is_released() -> None:
    store = _BlockingStore(block="budget")
    state, record = _budget_state(store)

    async def scenario() -> Any:
        task = asyncio.create_task(chat_completions(_budget_payload(), _request(state, record)))
        return await _cancel_while_the_worker_runs(task, store)

    asyncio.run(scenario())

    assert store.budget_usage == {}
    assert store.finalize_calls == 1
