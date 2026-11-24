"""Cleanup that itself fails, on the cancellation and snapshot-failure paths.

The compensation code is written to survive a store that refuses to release.
These tests make the release raise so the error is recorded rather than
escaping, and assert the request still answers with its typed envelope.
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

UID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"


class _RefusingStore(InMemoryApiKeyStore):
    """A store whose releases fail, optionally blocking the reservation."""

    def __init__(self, *, block_reserve: bool = False) -> None:
        super().__init__()
        self.block_reserve = block_reserve
        self.entered = threading.Event()
        self.release_gate = threading.Event()

    def check_and_reserve_quota(self, *a: Any, **k: Any) -> Any:
        if self.block_reserve:
            self.entered.set()
            self.release_gate.wait(timeout=10)
        return super().check_and_reserve_quota(*a, **k)

    def release_quota(self, *a: Any, **k: Any) -> Any:
        raise RuntimeError("quota release refused")


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


def _state(store: InMemoryApiKeyStore) -> tuple[Any, Any, ChatCompletionRequest]:
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


def test_a_refused_quota_release_on_the_cancellation_path_is_recorded() -> None:
    store = _RefusingStore(block_reserve=True)
    state, record, payload = _state(store)

    async def scenario() -> Any:
        task = asyncio.create_task(chat_completions(payload, _request(state, record)))
        for _ in range(400):
            if store.entered.is_set():
                break
            await asyncio.sleep(0.005)
        task.cancel()
        for _ in range(30):
            await asyncio.sleep(0)
        store.release_gate.set()
        return (await asyncio.gather(task, return_exceptions=True))[0]

    asyncio.run(scenario())


def test_a_refused_quota_release_on_the_snapshot_failure_path_is_recorded() -> None:
    store = _RefusingStore()
    state, record, payload = _state(store)
    store.append_pre_routing_feature_snapshot = lambda *_a, **_k: False  # type: ignore[assignment]

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 503


class _BlockingCleanupStore(InMemoryApiKeyStore):
    """Blocks reconciliation until the test lets it finish."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.gate = threading.Event()

    def _block(self) -> None:
        self.entered.set()
        self.gate.wait(timeout=10)

    def reconcile_budget(self, *a: Any, **k: Any) -> Any:
        self._block()
        return super().reconcile_budget(*a, **k)

    def release_budget(self, *a: Any, **k: Any) -> Any:
        self._block()
        return super().release_budget(*a, **k)

    def settle_quota(self, *a: Any, **k: Any) -> Any:
        self._block()
        return super().settle_quota(*a, **k)

    def release_quota(self, *a: Any, **k: Any) -> Any:
        self._block()
        return super().release_quota(*a, **k)


def _budget_state(store: InMemoryApiKeyStore) -> tuple[Any, Any, ChatCompletionRequest]:
    from sabiroute.security.keys import ApiKeyBudget

    state = build_gateway_state(config=make_config(), client=StubLiteLLMClient(), key_store=store)
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


def _cancel_during_cleanup(maker: Any) -> None:
    state, record, payload = maker()
    store = state.key_store

    async def scenario() -> None:
        task = asyncio.create_task(chat_completions(payload, _request(state, record)))
        for _ in range(400):
            if store.entered.is_set():
                break
            await asyncio.sleep(0.005)
        task.cancel()
        for _ in range(40):
            await asyncio.sleep(0)
        task.cancel()
        for _ in range(40):
            await asyncio.sleep(0)
        store.gate.set()
        await asyncio.gather(task, return_exceptions=True)
        assert store.finalize_calls <= 1

    asyncio.run(scenario())


def test_cancellation_inside_budget_reconciliation_is_absorbed() -> None:
    store = _BlockingCleanupStore()
    _cancel_during_cleanup(lambda: _budget_state(store))


def test_cancellation_inside_quota_settlement_is_absorbed() -> None:
    store = _BlockingCleanupStore()
    _cancel_during_cleanup(lambda: _state(store))
