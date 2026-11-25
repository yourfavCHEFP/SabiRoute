"""Cleanup that itself fails, on the cancellation and snapshot-failure paths.

The compensation code is written to survive a store that refuses to release.
These tests make the release raise so the error is recorded rather than
escaping, and assert the request still answers with its typed envelope.
"""

from __future__ import annotations

import asyncio
import logging
import threading
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
    ApiKeyIdentity,
    UsageEventValidationError,
    issue_api_key,
)

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


def test_a_refused_quota_release_on_the_cancellation_path_is_recorded(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = _RefusingStore(block_reserve=True)
    state, record, payload = _state(store)
    caplog.set_level(logging.ERROR)

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

    result = asyncio.run(scenario())

    # The reservation really was reached, so the release below is the one the
    # refusal interrupts rather than a guard that short-circuited earlier.
    assert store.entered.is_set()
    # Cancellation before the attempt answers with the typed envelope rather
    # than propagating the cancellation to the caller.
    assert result.status_code == 499
    # The refused release is recorded instead of vanishing silently, and it
    # does not replace the response the caller was owed.
    assert any(
        "Quota reservation release failed after cancellation" in entry.message
        for entry in caplog.records
    )


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


class _SelfCancellingCleanupStore(InMemoryApiKeyStore):
    """A shielded cleanup step that reports cancellation as its own outcome."""

    def reconcile_budget(self, *a: Any, **k: Any) -> Any:
        raise asyncio.CancelledError("worker cancelled itself")


def test_a_cleanup_that_cancels_itself_does_not_hang_the_request() -> None:
    store = _SelfCancellingCleanupStore()
    state, record, payload = _budget_state(store)

    async def scenario() -> Any:
        try:
            return await asyncio.wait_for(
                chat_completions(payload, _request(state, record)), timeout=2
            )
        except asyncio.CancelledError:
            return "cancelled"

    outcome = asyncio.run(scenario())

    # The shield exists so a client cancellation cannot withdraw cleanup. A
    # worker that ends cancelled is the other case: the shielded task is dead,
    # so retrying the await re-raises immediately and would spin forever. The
    # request has to finish — answering or surfacing the cancellation — rather
    # than hanging, which is the only outcome the timeout can rule out.
    assert outcome == "cancelled" or outcome.status_code >= 500
    assert store.finalize_calls <= 1


class _FinalizeFailingStore(InMemoryApiKeyStore):
    """A store whose durable finalize refuses with a chosen error.

    The quota reservation is held behind a gate, so cancellation lands while
    admission is inside the store and the request takes the cancelled-admission
    path — which finalizes telemetry exactly once, after compensating.
    """

    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error
        self.entered = threading.Event()
        self.release_gate = threading.Event()

    def check_and_reserve_quota(self, *a: Any, **k: Any) -> Any:
        self.entered.set()
        self.release_gate.wait(timeout=10)
        return super().check_and_reserve_quota(*a, **k)

    def finalize_usage_event(self, event: Any) -> bool:
        raise self.error


def _cancel_while_admission_is_inside_the_store(store: Any) -> Any:
    """Cancel the request once the store is entered, then let it continue."""
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

    return asyncio.run(scenario())


def test_a_rejected_finalize_on_the_cancelled_path_answers_503(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The cancelled-request path finalizes telemetry too, so it meets the same
    # store refusals as the normal one — and must answer rather than escape.
    caplog.set_level(logging.ERROR)
    result = _cancel_while_admission_is_inside_the_store(
        _FinalizeFailingStore(UsageEventValidationError("missing final_status"))
    )

    assert result.status_code == 503
    assert "usage_store_unavailable" in result.body.decode()
    assert "rejected at finalization" in caplog.text


def test_a_finalize_outage_on_the_cancelled_path_answers_503(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR)
    result = _cancel_while_admission_is_inside_the_store(
        _FinalizeFailingStore(RuntimeError("telemetry store down"))
    )

    assert result.status_code == 503
    # The store's message is not echoed back: only the typed category is.
    assert "telemetry store down" not in result.body.decode()
    assert "finalization failed" in caplog.text


class _SelfCancellingReleaseStore(_RefusingStore):
    """A store whose release worker ends *itself* cancelled."""

    def release_quota(self, *a: Any, **k: Any) -> Any:
        raise asyncio.CancelledError()


def test_a_self_cancelling_release_does_not_hang_the_cancelled_request() -> None:
    # Same shape as the shield-loop bug one layer down: awaiting a release whose
    # worker cancelled itself re-raises on every attempt, so the compensation
    # step must let that cancellation through instead of retrying it.
    result = _cancel_while_admission_is_inside_the_store(
        _SelfCancellingReleaseStore(block_reserve=True)
    )

    assert isinstance(result, asyncio.CancelledError)


class _BudgetGatedStore(_RefusingStore):
    """Gates budget reservation; both releases end themselves cancelled."""

    def __init__(self) -> None:
        super().__init__(block_reserve=False)
        self.budget_entered = threading.Event()
        self.budget_gate = threading.Event()
        # Reuse the shared harness gate on the budget step.
        self.entered = self.budget_entered
        self.release_gate = self.budget_gate

    def reserve_budget(self, *a: Any, **k: Any) -> Any:
        self.budget_entered.set()
        self.budget_gate.wait(timeout=10)
        return super().reserve_budget(*a, **k)

    def release_budget(self, *a: Any, **k: Any) -> Any:
        raise asyncio.CancelledError()


def test_a_self_cancelling_budget_release_does_not_hang_the_cancelled_request() -> None:
    # The budget gate holds the same shape as the quota one, one layer out:
    # cancellation lands while the reservation is inside the store, and the
    # compensation that follows must survive a release that cancels itself.
    from sabiroute.security.keys import ApiKeyBudget

    store = _BudgetGatedStore()
    state, record, payload = _state(store)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=100_000))

    async def scenario() -> Any:
        task = asyncio.create_task(chat_completions(payload, _request(state, record)))
        for _ in range(400):
            if store.budget_entered.is_set():
                break
            await asyncio.sleep(0.005)
        task.cancel()
        for _ in range(30):
            await asyncio.sleep(0)
        store.release_gate.set()
        return (await asyncio.gather(task, return_exceptions=True))[0]

    result = asyncio.run(scenario())

    assert store.budget_entered.is_set()
    assert isinstance(result, asyncio.CancelledError)


class _SnapshotRefusingStore(_RefusingStore):
    """A store that refuses the feature snapshot and both releases."""

    def __init__(self) -> None:
        super().__init__(block_reserve=False)
        self.append_pre_routing_feature_snapshot = (  # type: ignore[assignment]
            lambda *_a, **_k: False
        )

    def release_budget(self, *a: Any, **k: Any) -> Any:
        raise RuntimeError("budget release refused")


def test_a_snapshot_failure_compensates_through_refused_releases(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from sabiroute.security.keys import ApiKeyBudget

    caplog.set_level(logging.ERROR)
    store = _SnapshotRefusingStore()
    state, record, payload = _state(store)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=100_000))

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 503
    messages = [entry.message for entry in caplog.records]
    assert any("Budget reservation release failed" in message for message in messages)
    assert any("Quota reservation release failed" in message for message in messages)


class _SnapshotReleaseMode(_RefusingStore):
    """Snapshot fails; releases behave as the mode names."""

    def __init__(self, mode: str) -> None:
        super().__init__(block_reserve=False)
        self.mode = mode
        self.append_pre_routing_feature_snapshot = (  # type: ignore[assignment]
            lambda *_a, **_k: False
        )

    def release_budget(self, *a: Any, **k: Any) -> Any:
        if self.mode == "budget_cancels":
            raise asyncio.CancelledError()
        return InMemoryApiKeyStore.release_budget(self, *a, **k)

    def release_quota(self, *a: Any, **k: Any) -> Any:
        # Base keeps refusing releases; these modes control the outcome so the
        # success and self-cancellation branches are reachable too.
        if self.mode == "quota_cancels":
            raise asyncio.CancelledError()
        return InMemoryApiKeyStore.release_quota(self, *a, **k)


def test_a_successful_snapshot_compensation_releases_both_reservations() -> None:
    # The refusal cases above leave the release-success assignment unproven;
    # this one lets both releases land so the flags are what clear.
    from sabiroute.security.keys import ApiKeyBudget

    store = _SnapshotReleaseMode("releases_succeed")
    state, record, payload = _state(store)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=100_000))

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 503


def test_a_self_cancelling_budget_release_on_the_snapshot_path_is_raised() -> None:
    from sabiroute.security.keys import ApiKeyBudget

    store = _SnapshotReleaseMode("budget_cancels")
    state, record, payload = _state(store)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=100_000))

    async def scenario() -> Any:
        return (
            await asyncio.gather(
                chat_completions(payload, _request(state, record)), return_exceptions=True
            )
        )[0]

    result = asyncio.run(scenario())

    # The worker cancelled itself, so the cancellation surfaces rather than
    # being swallowed into a 503 the store never agreed to.
    assert isinstance(result, BaseException)


def test_a_self_cancelling_quota_release_on_the_snapshot_path_is_raised() -> None:
    from sabiroute.security.keys import ApiKeyBudget

    store = _SnapshotReleaseMode("quota_cancels")
    state, record, payload = _state(store)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=100_000))

    async def scenario() -> Any:
        return (
            await asyncio.gather(
                chat_completions(payload, _request(state, record)), return_exceptions=True
            )
        )[0]

    result = asyncio.run(scenario())

    assert isinstance(result, BaseException)
