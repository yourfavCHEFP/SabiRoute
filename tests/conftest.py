from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from threading import RLock
from typing import Any

import pytest

from sabiroute.config.models import SabiRouteConfig
from sabiroute.config.validation import validate_config
from sabiroute.providers.litellm_client import LiteLLMClientError
from sabiroute.security.keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    ApiKeyRecord,
    RequestUsageEvent,
    issue_api_key,
    validate_pre_routing_feature_snapshot,
    validate_usage_event_finalization,
)


class InMemoryApiKeyStore:
    """Small transactional test double; production uses PostgresApiKeyStore."""

    def __init__(self) -> None:
        self.records: dict[str, ApiKeyRecord] = {}
        self.rate_limits: dict[str, ApiKeyRateLimit] = {}
        self.budgets: dict[str, ApiKeyBudget] = {}
        self.budget_usage: dict[tuple[str, str], tuple[int, Decimal | None]] = {}
        self.usage_events: dict[str, RequestUsageEvent] = {}
        self.finalize_calls = 0
        self.fail_usage_writes = False
        self.fail_feature_snapshot_writes = False
        self.fail_finalize_usage_writes = False
        self.shared_inference: bool | None = None
        self.shared_inference_by: str | None = None
        self.fail_policy_reads = False
        self.fail_quota_reads = False
        self.quota_windows: dict[tuple[str, str], tuple[int, int]] = {}
        self.quota_reservations: dict[tuple[str, str], list] = {}
        self._lock = RLock()

    def create(self, record: ApiKeyRecord) -> None:
        with self._lock:
            self.records[record.key_id] = record

    def get(self, key_id: str) -> ApiKeyRecord | None:
        with self._lock:
            return self.records.get(key_id)

    def revoke(self, key_id: str, at: datetime) -> bool:
        with self._lock:
            record = self.records.get(key_id)
            if record is None or record.revoked_at is not None:
                return False
            self.records[key_id] = replace(record, revoked_at=at)
            return True

    def rotate(self, old_key_id: str, new_record: ApiKeyRecord, at: datetime) -> bool:
        with self._lock:
            if not self.revoke(old_key_id, at):
                return False
            self.create(new_record)
            old_limit = self.rate_limits.get(old_key_id)
            if old_limit is not None:
                self.rate_limits[new_record.key_id] = old_limit
            old_budget = self.budgets.get(old_key_id)
            if old_budget is not None:
                self.budgets[new_record.key_id] = old_budget
            return True

    def get_rate_limit(self, key_id: str) -> ApiKeyRateLimit | None:
        with self._lock:
            return self.rate_limits.get(key_id)

    def set_rate_limit(self, key_id: str, limit: ApiKeyRateLimit | None) -> bool:
        with self._lock:
            record = self.records.get(key_id)
            if record is None or record.revoked_at is not None:
                return False
            if limit is None:
                self.rate_limits.pop(key_id, None)
            else:
                self.rate_limits[key_id] = limit
            return True

    def get_shared_inference(self) -> bool | None:
        with self._lock:
            if self.fail_policy_reads:
                raise RuntimeError("test policy store unavailable")
            return self.shared_inference

    def set_shared_inference(self, enabled: bool, actor: str) -> None:
        with self._lock:
            if self.fail_policy_reads:
                raise RuntimeError("test policy store unavailable")
            self.shared_inference = enabled
            self.shared_inference_by = actor

    def shared_inference_status(self) -> dict[str, object]:
        with self._lock:
            if self.fail_policy_reads:
                raise RuntimeError("test policy store unavailable")
            value = self.shared_inference
            return {
                "enabled": value is True,
                "configured": isinstance(value, bool),
                "updated_at": None,
                "updated_by": self.shared_inference_by,
            }

    # -- per-user quota ledger (mirrors the SQL store contract) -------------

    def check_and_reserve_quota(
        self,
        user_id: str,
        request_id: str,
        estimate: int,
        window_start: object,
        quota: int,
    ) -> bool:
        with self._lock:
            if self.fail_policy_reads or self.fail_quota_reads:
                raise RuntimeError("test quota store unavailable")
            if estimate < 1 or quota < 1:
                return False
            key = (user_id, str(window_start))
            reserved, consumed = self.quota_windows.get(key, (0, 0))
            if (user_id, request_id) in self.quota_reservations:
                return True
            if reserved + consumed + estimate > quota:
                return False
            self.quota_windows[key] = (reserved + estimate, consumed)
            self.quota_reservations[(user_id, request_id)] = [estimate, "reserved", key]
            return True

    def settle_quota(
        self, user_id: str, request_id: str, actual_tokens: int | None
    ) -> None:
        with self._lock:
            if self.fail_policy_reads or self.fail_quota_reads:
                raise RuntimeError("test quota store unavailable")
            record = self.quota_reservations.get((user_id, request_id))
            if record is None or record[1] != "reserved":
                return
            estimate, _, window_key = record
            settled = actual_tokens if actual_tokens is not None else estimate
            record[1] = "settled"
            reserved, consumed = self.quota_windows[window_key]
            self.quota_windows[window_key] = (reserved - estimate, consumed + settled)

    def release_quota(self, user_id: str, request_id: str) -> None:
        with self._lock:
            if self.fail_policy_reads or self.fail_quota_reads:
                raise RuntimeError("test quota store unavailable")
            record = self.quota_reservations.get((user_id, request_id))
            if record is None or record[1] != "reserved":
                return
            estimate, _, window_key = record
            record[1] = "released"
            reserved, consumed = self.quota_windows[window_key]
            self.quota_windows[window_key] = (reserved - estimate, consumed)

    def get_quota_usage(self, user_id: str, window_start: object) -> dict[str, int]:
        with self._lock:
            if self.fail_policy_reads or self.fail_quota_reads:
                raise RuntimeError("test quota store unavailable")
            reserved, consumed = self.quota_windows.get((user_id, str(window_start)), (0, 0))
            return {"reserved_tokens": reserved, "consumed_tokens": consumed}

    def get_budget(self, key_id: str) -> ApiKeyBudget | None:
        with self._lock:
            return self.budgets.get(key_id)

    def set_budget(self, key_id: str, budget: ApiKeyBudget | None) -> bool:
        with self._lock:
            record = self.records.get(key_id)
            if record is None or record.revoked_at is not None:
                return False
            if budget is None:
                self.budgets.pop(key_id, None)
            else:
                self.budgets[key_id] = budget
            return True

    def get_budget_usage(self, key_id: str, now: datetime) -> dict[str, dict[str, Any]]:
        tokens = sum(
            amount
            for (saved_key, _), (amount, _) in self.budget_usage.items()
            if saved_key == key_id
        )
        costs = [
            cost
            for (saved_key, _), (_, cost) in self.budget_usage.items()
            if saved_key == key_id and cost is not None
        ]
        total_cost = sum(costs, Decimal(0))
        return {
            "daily": {"tokens": tokens, "cost_usd": total_cost},
            "monthly": {"tokens": tokens, "cost_usd": total_cost},
        }

    def reserve_budget(
        self,
        key_id: str,
        request_id: str,
        estimated_tokens: int,
        estimated_cost_usd: Decimal | None,
        now: datetime,
    ) -> str | None:
        with self._lock:
            budget = self.budgets.get(key_id)
            if budget is None:
                return None
            current = sum(
                amount
                for (saved_key, _), (amount, _) in self.budget_usage.items()
                if saved_key == key_id
            )
            limits = [value for value in (budget.daily_tokens, budget.monthly_tokens) if value]
            if limits and current + estimated_tokens > min(limits):
                return "daily_tokens_exceeded"
            if (
                budget.daily_cost_usd is not None or budget.monthly_cost_usd is not None
            ) and estimated_cost_usd is None:
                return "daily_pricing_unknown"
            self.budget_usage[(key_id, request_id)] = (estimated_tokens, estimated_cost_usd)
            return None

    def reconcile_budget(
        self,
        key_id: str,
        request_id: str,
        actual_tokens: int | None,
        actual_cost_usd: Decimal | None,
    ) -> None:
        with self._lock:
            old = self.budget_usage.get((key_id, request_id))
            if old is not None:
                self.budget_usage[(key_id, request_id)] = (
                    actual_tokens if actual_tokens is not None else old[0],
                    actual_cost_usd if actual_cost_usd is not None else old[1],
                )

    def release_budget(self, key_id: str, request_id: str) -> None:
        with self._lock:
            self.budget_usage.pop((key_id, request_id), None)

    def create_usage_event(self, event: RequestUsageEvent) -> None:
        with self._lock:
            if self.fail_usage_writes:
                raise RuntimeError("test usage store unavailable")
            if event.request_id in self.usage_events:
                raise ValueError("duplicate test request ID")
            self.usage_events[event.request_id] = event

    def append_pre_routing_feature_snapshot(
        self, request_id: str, snapshot: Mapping[str, Any]
    ) -> bool:
        with self._lock:
            if self.fail_usage_writes or self.fail_feature_snapshot_writes:
                raise RuntimeError("test usage store unavailable")
            existing = self.usage_events.get(request_id)
            if existing is None or existing.final_status is not None:
                return False
            validate_pre_routing_feature_snapshot(
                request_id,
                len(existing.pre_routing_features) + 1,
                snapshot,
                existing.feature_schema_version,
            )
            self.usage_events[request_id] = replace(
                existing,
                feature_schema_version=str(snapshot.get("feature_schema_version")),
                pre_routing_features=existing.pre_routing_features + (dict(snapshot),),
            )
            return True

    def finalize_usage_event(self, event: RequestUsageEvent) -> bool:
        with self._lock:
            self.finalize_calls += 1
            if self.fail_usage_writes or self.fail_finalize_usage_writes:
                raise RuntimeError("test usage store unavailable")
            existing = self.usage_events.get(event.request_id)
            if existing is None or existing.final_status is not None:
                return False
            validate_usage_event_finalization(event)
            self.usage_events[event.request_id] = event
            return True

    def list_usage_events(
        self, key_id: str, *, limit: int, offset: int
    ) -> tuple[list[RequestUsageEvent], int]:
        with self._lock:
            rows = sorted(
                (event for event in self.usage_events.values() if event.key_id == key_id),
                key=lambda event: (event.created_at, event.request_id),
                reverse=True,
            )
            return rows[offset : offset + limit], len(rows)


def enable_shared_inference(state: Any) -> Any:
    """Explicitly enable the kill-switch, mirroring an operator action.

    Shared inference starts disabled; harnesses that exercise the Free Chat
    path must opt in, or admissions fail closed by design.
    """
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.shared_inference = True
    return state


def provision_test_key(state: Any, *, project_id: str = "project-test") -> str:
    store = state.key_store
    if not isinstance(store, InMemoryApiKeyStore):
        store = InMemoryApiKeyStore()
        state.key_store = store
    _, plaintext = issue_api_key(store, project_id=project_id, name="test key")
    return plaintext


def make_config() -> SabiRouteConfig:
    """Build a small in-memory config covering the credential shapes."""

    return validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "primary",
                        "capabilities": {"chat": True, "streaming": True},
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "os.environ/OPENAI_API_KEY",
                        },
                    },
                    {
                        "model_name": "secondary",
                        "capabilities": {"chat": True, "streaming": True},
                        "litellm_params": {
                            "model": "groq/llama-3.1-8b-instant",
                            "api_key": "os.environ/GROQ_API_KEY",
                        },
                    },
                    {
                        "model_name": "cloudy",
                        "capabilities": {"chat": True},
                        "litellm_params": {
                            "model": "cloudflare/@cf/meta/llama-3.3-70b",
                            "api_key": "os.environ/CLOUDFLARE_API_KEY",
                            "account_id": "os.environ/CLOUDFLARE_ACCOUNT_ID",
                        },
                    },
                    {
                        "model_name": "literal-key",
                        "capabilities": {"chat": True},
                        "litellm_params": {
                            "model": "together/meta-llama/Llama-3-70b",
                            "api_key": "sk-literal-test",
                        },
                    },
                ]
            }
        )
    )


class StubLiteLLMClient:
    """Test double for the LiteLLM proxy client.

    Fails the first N calls per deployment, then succeeds.
    """

    def __init__(
        self,
        failures: dict[str, int] | None = None,
        failure_status: int = 500,
    ) -> None:
        self.failures_remaining = dict(failures or {})
        self.failure_status = failure_status
        self.calls: list[str] = []

    async def chat_completion(
        self,
        decision: Any,
        messages: Any,
        **extra: Any,
    ) -> dict[str, Any]:
        self.calls.append(decision.deployment)

        remaining = self.failures_remaining.get(decision.deployment, 0)
        if remaining > 0:
            self.failures_remaining[decision.deployment] = remaining - 1
            raise LiteLLMClientError(
                f"stub failure for {decision.deployment}",
                status_code=self.failure_status,
            )

        return {
            "id": "chatcmpl-stub",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    async def start_chat_completion_stream(
        self,
        decision: Any,
        messages: Any,
        **extra: Any,
    ):
        self.calls.append(decision.deployment)
        remaining = self.failures_remaining.get(decision.deployment, 0)
        if remaining > 0:
            self.failures_remaining[decision.deployment] = remaining - 1
            raise LiteLLMClientError(
                f"stub failure for {decision.deployment}",
                status_code=self.failure_status,
            )

        class Stream:
            async def events(self):
                yield b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
                yield b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
                yield (
                    b'data: {"choices":[],"usage":{"prompt_tokens":3,'
                    b'"completion_tokens":2,"total_tokens":5}}\n\n'
                )
                yield b"data: [DONE]\n\n"

            async def aclose(self):
                return None

        return Stream()


@pytest.fixture
def config() -> SabiRouteConfig:
    return make_config()


_ISOLATED_RUNTIME_ENV_VARS = (
    "DATABASE_URL",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_PORT",
    "REDIS_URL",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_DB",
    "REDIS_PASSWORD",
    "SABIROUTE_ADMIN_KEY",
    "LITELLM_MASTER_KEY",
    "LITELLM_SALT_KEY",
    "SABIROUTE_LITELLM_URL",
    "SABIROUTE_CONFIG_PATH",
    "SABIROUTE_ROUTES_PATH",
    "SABIROUTE_REQUEST_DEADLINE_SECONDS",
    "SABIROUTE_FREEPOOL_ENABLED",
    "SABIROUTE_FREEPOOL_DEPLOYMENTS",
    "SABIROUTE_QUOTA_PILOT_USERS",
)


@pytest.fixture(autouse=True)
def _isolate_runtime_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> Any:
    """Keep tests hermetic against the developer's local repository .env.

    Redirects ``DEFAULT_ENV_PATH`` to an empty per-test ``.env`` file so
    ``_load_environment_file()`` exercises its normal ``load_dotenv`` path
    without falling through to ``find_dotenv(usecwd=True)`` (which would
    read the repository root ``.env``) and clears runtime service/secret
    variables unless a test sets them explicitly. Restores ``os.environ``
    on teardown even if ``load_dotenv`` mutated it outside ``monkeypatch``.
    """
    import os

    import sabiroute.config.loader as config_loader

    snapshot = dict(os.environ)
    isolated_env = tmp_path / ".env"
    isolated_env.write_text("", encoding="utf-8")
    monkeypatch.setattr(config_loader, "DEFAULT_ENV_PATH", isolated_env)
    for var in _ISOLATED_RUNTIME_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(snapshot)


def _make_direct_completion_request(state: Any) -> Any:
    from types import SimpleNamespace

    from sabiroute.security.keys import ApiKeyIdentity

    key_id = next(iter(state.key_store.records))
    record = state.key_store.records[key_id]
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway=state)),
        state=SimpleNamespace(
            api_identity=ApiKeyIdentity(
                key_id=record.key_id, project_id=record.project_id
            ),
            sabiroute_deadline_at=None,
        ),
    )


def test_accounting_success_and_exception_clear_in_flight() -> None:
    """Success and worker exceptions clear in-flight tracking without hanging finish()."""
    from fastapi.testclient import TestClient

    from sabiroute.gateway import build_gateway_state
    from sabiroute.main import create_app

    stub = StubLiteLLMClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=stub, key_store=store)
    key = provision_test_key(state)
    key_id = next(iter(store.records))
    store.set_budget(key_id, ApiKeyBudget(daily_tokens=1000))
    app = create_app(state=state)
    headers = {"Authorization": f"Bearer {key}"}

    with TestClient(app, headers=headers) as client:
        ok = client.post(
            "/v1/chat/completions",
            json={
                "model": "primary",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 16,
            },
        )
        assert ok.status_code == 200
        assert state.store_executor.in_use_count == 0
        assert store.finalize_calls == 1

        # Now force a worker exception inside _run_accounting("snapshot", ...):
        # must untrack, release the held budget reservation, and return 503
        # without hanging in snapshot_persistence_failure() / finish().
        store.fail_feature_snapshot_writes = True
        failed = client.post(
            "/v1/chat/completions",
            json={
                "model": "primary",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 16,
            },
        )
        assert failed.status_code == 503
        assert failed.json()["error"]["type"] == "telemetry_store_unavailable"
        assert state.store_executor.in_use_count == 0
        # Only the first (successful) request holds reconciled budget usage;
        # the second request's budget reservation was released on snapshot error.
        assert len(store.budget_usage) == 1


def test_running_worker_cancellation_waits_before_cleanup() -> None:
    """Cancelling while a reservation worker runs waits for it before releasing."""
    import asyncio
    import threading

    from sabiroute.api.completions import ChatCompletionRequest, chat_completions
    from sabiroute.gateway import build_gateway_state

    stub = StubLiteLLMClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=stub, key_store=store)
    provision_test_key(state)
    key_id = next(iter(store.records))
    store.set_budget(key_id, ApiKeyBudget(daily_tokens=1000))

    entered = threading.Event()
    release_gate = threading.Event()
    order: list[str] = []
    orig_reserve = store.reserve_budget
    orig_release = store.release_budget

    def gated_reserve(
        k_id: str,
        req_id: str,
        est_tokens: int,
        est_cost: Decimal | None,
        now: datetime,
    ) -> str | None:
        order.append("reserve_enter")
        entered.set()
        assert release_gate.wait(timeout=5.0)
        result = orig_reserve(k_id, req_id, est_tokens, est_cost, now)
        order.append("reserve_exit")
        return result

    def tracked_release(k_id: str, req_id: str) -> None:
        order.append("release_budget")
        orig_release(k_id, req_id)

    store.reserve_budget = gated_reserve  # type: ignore[method-assign]
    store.release_budget = tracked_release  # type: ignore[method-assign]
    request = _make_direct_completion_request(state)

    async def run_scenario() -> None:
        task = asyncio.create_task(
            chat_completions(
                ChatCompletionRequest(
                    model="primary",
                    messages=[{"role": "user", "content": "hello"}],
                    max_tokens=16,
                ),
                request,
            )
        )
        assert await asyncio.to_thread(entered.wait, 5.0)
        # Cancel while the worker thread is still blocked inside gated_reserve.
        task.cancel()
        await asyncio.sleep(0)
        # Cleanup must NOT have raced ahead while gated_reserve is still running.
        assert order == ["reserve_enter"]
        assert not task.done()
        assert store.finalize_calls == 0

        # Let the worker finish committing the reservation; cleanup must now
        # observe and release it, then finalize as 499 client_cancelled.
        release_gate.set()
        response = await task
        assert response.status_code == 499
        assert order == ["reserve_enter", "reserve_exit", "release_budget"]
        assert store.budget_usage == {}
        assert store.finalize_calls == 1
        event = next(iter(store.usage_events.values()))
        assert event.final_status == 499
        assert event.failure_category == "client_cancelled"
        assert state.store_executor.in_use_count == 0
        assert stub.calls == []

    asyncio.run(run_scenario())


def test_queued_worker_cancellation_does_not_hang_or_leak() -> None:
    """Cancelling while queued in the executor semaphore starts nothing and does not hang."""
    import asyncio
    import threading

    from sabiroute.api.completions import ChatCompletionRequest, chat_completions
    from sabiroute.gateway import build_gateway_state
    from sabiroute.security.store_executor import BoundedStoreExecutor

    stub = StubLiteLLMClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=stub, key_store=store)
    state.store_executor = BoundedStoreExecutor(max_concurrency=1)
    provision_test_key(state)
    key_id = next(iter(store.records))
    store.set_budget(key_id, ApiKeyBudget(daily_tokens=1000))

    holder_entered = threading.Event()
    holder_release = threading.Event()
    queued_reserve_ran = False
    orig_create_event = store.create_usage_event
    orig_reserve = store.reserve_budget

    def create_then_saturate(event: RequestUsageEvent) -> None:
        orig_create_event(event)

    def gated_reserve(
        k_id: str,
        req_id: str,
        est_tokens: int,
        est_cost: Decimal | None,
        now: datetime,
    ) -> str | None:
        nonlocal queued_reserve_ran
        queued_reserve_ran = True
        return orig_reserve(k_id, req_id, est_tokens, est_cost, now)

    store.create_usage_event = create_then_saturate  # type: ignore[method-assign]
    store.reserve_budget = gated_reserve  # type: ignore[method-assign]

    # Hold the single executor slot when get_budget finishes so _run_accounting("budget_reserve")
    # queues on the semaphore.
    orig_get_budget = store.get_budget
    blocker_task: asyncio.Task[Any] | None = None

    async def run_scenario() -> None:
        nonlocal blocker_task
        loop = asyncio.get_running_loop()
        budget_read_entered = asyncio.Event()
        budget_read_release = threading.Event()

        def get_budget_and_signal(k_id: str) -> ApiKeyBudget | None:
            result = orig_get_budget(k_id)
            loop.call_soon_threadsafe(budget_read_entered.set)
            assert budget_read_release.wait(timeout=5.0)
            return result

        store.get_budget = get_budget_and_signal  # type: ignore[method-assign]

        def hold_slot() -> None:
            holder_entered.set()
            assert holder_release.wait(timeout=5.0)

        request = _make_direct_completion_request(state)
        task = asyncio.create_task(
            chat_completions(
                ChatCompletionRequest(
                    model="primary",
                    messages=[{"role": "user", "content": "hello"}],
                    max_tokens=16,
                ),
                request,
            )
        )
        await budget_read_entered.wait()
        # Queue blocker_task while get_budget still holds the sole executor slot
        # so FIFO handoff grants the slot to hold_slot before budget_reserve.
        blocker_task = asyncio.create_task(state.store_executor.run(hold_slot))
        while not state.store_executor._semaphore._waiters:
            await asyncio.sleep(0)
        budget_read_release.set()
        assert await asyncio.to_thread(holder_entered.wait, 5.0)
        while not state.store_executor._semaphore._waiters:
            await asyncio.sleep(0)

        # Cancel task while budget_reserve is queued on the semaphore.
        task.cancel()
        await asyncio.sleep(0)
        assert queued_reserve_ran is False

        # Release the blocker so cleanup (release_budget no-op + finalize) can run.
        holder_release.set()
        await blocker_task
        response = await task
        assert response.status_code == 499
        assert queued_reserve_ran is False
        assert store.budget_usage == {}
        assert store.finalize_calls == 1
        assert state.store_executor.in_use_count == 0

    asyncio.run(run_scenario())


def _make_quota_and_budget_harness() -> tuple[
    Any, InMemoryApiKeyStore, StubLiteLLMClient, str, str
]:
    from sabiroute.freepool.eligibility import FreePoolPolicy
    from sabiroute.gateway import build_gateway_state
    from sabiroute.quotas import QuotaPolicy

    uid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    stub = StubLiteLLMClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=store,
        free_pool=FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"})),
        quota_policy=QuotaPolicy(pilot_users=frozenset({uid})),
    )
    record, _ = issue_api_key(store, project_id="sabichat-service", name="sabichat-service")
    state.sabichat_service_key_id = record.key_id
    enable_shared_inference(state)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))
    return state, store, stub, record.key_id, uid


def _make_free_chat_payload(uid: str) -> Any:
    from sabiroute.api.completions import ChatCompletionRequest
    from sabiroute.security.keys import SABI_USER_ID_FIELD

    return ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
            "sabi_route_free_chat": True,
            SABI_USER_ID_FIELD: uid,
        }
    )


def test_repeated_cancellation_during_budget_cleanup_completes_quota_and_finalizes() -> None:
    """Repeated cancellation during budget_cleanup still runs quota_cleanup and finalizes once."""
    import asyncio
    import threading
    from datetime import UTC

    from sabiroute.api.completions import chat_completions
    from sabiroute.quotas import quota_window_start

    def run_pre_dispatch_case(cancel_during_cleanup: bool) -> None:
        state, store, stub, _, uid = _make_quota_and_budget_harness()
        request = _make_direct_completion_request(state)
        snapshot_entered = threading.Event()
        snapshot_gate = threading.Event()
        release_budget_entered = threading.Event()
        release_budget_gate = threading.Event()
        order: list[str] = []

        orig_quota_reserve = store.check_and_reserve_quota
        orig_budget_reserve = store.reserve_budget
        orig_snapshot = store.append_pre_routing_feature_snapshot
        orig_release_budget = store.release_budget
        orig_release_quota = store.release_quota
        orig_finalize = store.finalize_usage_event

        def tracked_quota_reserve(*args: Any, **kwargs: Any) -> bool:
            order.append("quota_reserve")
            return orig_quota_reserve(*args, **kwargs)

        def tracked_budget_reserve(*args: Any, **kwargs: Any) -> str | None:
            order.append("budget_reserve")
            return orig_budget_reserve(*args, **kwargs)

        def gated_snapshot(req_id: str, snap: Mapping[str, Any]) -> bool:
            order.append("snapshot_enter")
            snapshot_entered.set()
            assert snapshot_gate.wait(timeout=5.0)
            res = orig_snapshot(req_id, snap)
            order.append("snapshot_exit")
            return res

        def gated_release_budget(k_id: str, req_id: str) -> None:
            order.append("release_budget_enter")
            release_budget_entered.set()
            assert release_budget_gate.wait(timeout=5.0)
            orig_release_budget(k_id, req_id)
            order.append("release_budget_exit")

        def tracked_release_quota(u_id: str, req_id: str) -> None:
            order.append("release_quota")
            orig_release_quota(u_id, req_id)

        def tracked_finalize(ev: RequestUsageEvent) -> bool:
            order.append("finalize")
            return orig_finalize(ev)

        store.check_and_reserve_quota = tracked_quota_reserve  # type: ignore[method-assign]
        store.reserve_budget = tracked_budget_reserve  # type: ignore[method-assign]
        store.append_pre_routing_feature_snapshot = gated_snapshot  # type: ignore[method-assign]
        store.release_budget = gated_release_budget  # type: ignore[method-assign]
        store.release_quota = tracked_release_quota  # type: ignore[method-assign]
        store.finalize_usage_event = tracked_finalize  # type: ignore[method-assign]

        async def run_pre_dispatch() -> None:
            task = asyncio.create_task(
                chat_completions(_make_free_chat_payload(uid), request)
            )
            assert await asyncio.to_thread(snapshot_entered.wait, 5.0)
            # First cancellation while snapshot worker is running.
            task.cancel()
            snapshot_gate.set()

            assert await asyncio.to_thread(release_budget_entered.wait, 5.0)
            if cancel_during_cleanup:
                # Second and third cancellations while budget_cleanup is in flight.
                task.cancel()
                await asyncio.sleep(0)
                task.cancel()
                await asyncio.sleep(0)
            release_budget_gate.set()

            response = await task
            assert response.status_code == 499
            assert order == [
                "quota_reserve",
                "budget_reserve",
                "snapshot_enter",
                "snapshot_exit",
                "release_budget_enter",
                "release_budget_exit",
                "release_quota",
                "finalize",
            ]
            assert store.budget_usage == {}
            window = quota_window_start(datetime.now(UTC))
            assert store.get_quota_usage(uid, window) == {
                "reserved_tokens": 0,
                "consumed_tokens": 0,
            }
            assert store.finalize_calls == 1
            event = next(iter(store.usage_events.values()))
            assert event.final_status == 499
            assert event.failure_category == "client_cancelled"
            assert event.reserved_tokens is None
            assert state.store_executor.in_use_count == 0
            assert stub.calls == []

        asyncio.run(run_pre_dispatch())

    # Part 1: Pre-dispatch snapshot cancellation with both quota & budget held,
    # tested under single cancellation and then under repeated cancellation
    # during budget_cleanup.
    for cancel_flag in (False, True):
        run_pre_dispatch_case(cancel_flag)

    # Part 2: Post-dispatch provider cancellation with both quota & budget held,
    # receiving repeated cancellation during finish()'s budget_cleanup.
    state, store, stub, key_id, uid = _make_quota_and_budget_harness()
    request = _make_direct_completion_request(state)
    provider_entered = asyncio.Event()
    reconcile_entered = threading.Event()
    reconcile_gate = threading.Event()
    post_order: list[str] = []

    orig_reconcile = store.reconcile_budget
    orig_settle_quota = store.settle_quota
    orig_finalize = store.finalize_usage_event

    async def hanging_provider(decision: Any, messages: Any, **extra: Any) -> dict[str, Any]:
        stub.calls.append(decision.deployment)
        provider_entered.set()
        await asyncio.Event().wait()
        return {}

    def gated_reconcile(
        k_id: str, req_id: str, actual_tokens: int | None, actual_cost: Decimal | None
    ) -> None:
        post_order.append("reconcile_budget_enter")
        reconcile_entered.set()
        assert reconcile_gate.wait(timeout=5.0)
        orig_reconcile(k_id, req_id, actual_tokens, actual_cost)
        post_order.append("reconcile_budget_exit")

    def tracked_settle_quota(u_id: str, req_id: str, actual_tokens: int | None) -> None:
        post_order.append("settle_quota")
        orig_settle_quota(u_id, req_id, actual_tokens)

    def tracked_post_finalize(ev: RequestUsageEvent) -> bool:
        post_order.append("finalize")
        return orig_finalize(ev)

    stub.chat_completion = hanging_provider  # type: ignore[method-assign]
    store.reconcile_budget = gated_reconcile  # type: ignore[method-assign]
    store.settle_quota = tracked_settle_quota  # type: ignore[method-assign]
    store.finalize_usage_event = tracked_post_finalize  # type: ignore[method-assign]

    async def run_post_dispatch() -> None:
        task = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid), request)
        )
        await provider_entered.wait()
        # First cancellation interrupts the upstream provider call.
        task.cancel()
        assert await asyncio.to_thread(reconcile_entered.wait, 5.0)
        # Second cancellation while finish() is running budget_cleanup.
        task.cancel()
        await asyncio.sleep(0)
        reconcile_gate.set()

        with pytest.raises(asyncio.CancelledError):
            await task

        assert post_order == [
            "reconcile_budget_enter",
            "reconcile_budget_exit",
            "settle_quota",
            "finalize",
        ]
        window = quota_window_start(datetime.now(UTC))
        assert store.get_quota_usage(uid, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 71,
        }
        assert len(store.budget_usage) == 1
        assert store.finalize_calls == 1
        event = next(iter(store.usage_events.values()))
        assert event.final_status == 499
        assert event.failure_category == "client_cancelled"
        assert state.store_executor.in_use_count == 0

    asyncio.run(run_post_dispatch())


def test_budget_cleanup_failure_under_cancellation_attempts_quota_and_preserves_flag() -> None:
    """Failed budget_cleanup under cancel still attempts quota_cleanup and keeps flag."""
    import asyncio
    import threading
    from datetime import UTC

    from sabiroute.api.completions import chat_completions
    from sabiroute.quotas import quota_window_start

    # Case A: Pre-dispatch snapshot cancellation where release_budget raises
    # an exception while also receiving a second cancellation.
    state, store, stub, key_id, uid = _make_quota_and_budget_harness()
    request = _make_direct_completion_request(state)
    snapshot_entered = threading.Event()
    snapshot_gate = threading.Event()
    release_budget_entered = threading.Event()
    release_budget_gate = threading.Event()
    order: list[str] = []

    orig_snapshot = store.append_pre_routing_feature_snapshot
    orig_release_quota = store.release_quota
    orig_finalize = store.finalize_usage_event

    def gated_snapshot(req_id: str, snap: Mapping[str, Any]) -> bool:
        order.append("snapshot_enter")
        snapshot_entered.set()
        assert snapshot_gate.wait(timeout=5.0)
        res = orig_snapshot(req_id, snap)
        order.append("snapshot_exit")
        return res

    def failing_release_budget(k_id: str, req_id: str) -> None:
        order.append("release_budget_enter")
        release_budget_entered.set()
        assert release_budget_gate.wait(timeout=5.0)
        order.append("release_budget_fail")
        raise RuntimeError("simulated budget release failure")

    def tracked_release_quota(u_id: str, req_id: str) -> None:
        order.append("release_quota")
        orig_release_quota(u_id, req_id)

    def tracked_finalize(ev: RequestUsageEvent) -> bool:
        order.append("finalize")
        return orig_finalize(ev)

    store.append_pre_routing_feature_snapshot = gated_snapshot  # type: ignore[method-assign]
    store.release_budget = failing_release_budget  # type: ignore[method-assign]
    store.release_quota = tracked_release_quota  # type: ignore[method-assign]
    store.finalize_usage_event = tracked_finalize  # type: ignore[method-assign]

    async def run_failing_pre_dispatch() -> None:
        task = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid), request)
        )
        assert await asyncio.to_thread(snapshot_entered.wait, 5.0)
        task.cancel()
        snapshot_gate.set()

        assert await asyncio.to_thread(release_budget_entered.wait, 5.0)
        # Second cancellation while failing release_budget is in flight.
        task.cancel()
        await asyncio.sleep(0)
        release_budget_gate.set()

        response = await task
        assert response.status_code == 499
        assert order == [
            "snapshot_enter",
            "snapshot_exit",
            "release_budget_enter",
            "release_budget_fail",
            "release_quota",
            "finalize",
        ]
        # Quota cleanup still ran and released the quota reservation.
        window = quota_window_start(datetime.now(UTC))
        assert store.get_quota_usage(uid, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 0,
        }
        # Budget release failed, so the store reservation remains held and
        # budget_reserved was NOT falsely cleared (final_event.reserved_tokens == 71).
        assert len(store.budget_usage) == 1
        assert store.finalize_calls == 1
        event = next(iter(store.usage_events.values()))
        assert event.final_status == 499
        assert event.failure_category == "client_cancelled"
        assert event.reserved_tokens == 71
        assert state.store_executor.in_use_count == 0
        assert stub.calls == []

    asyncio.run(run_failing_pre_dispatch())

    # Case B: Cancellation during budget_reserve after worker committed, where
    # release_budget raises an exception under a second cancellation.
    state2, store2, _, _, uid2 = _make_quota_and_budget_harness()
    request2 = _make_direct_completion_request(state2)
    reserve_entered = threading.Event()
    reserve_gate = threading.Event()
    release_entered2 = threading.Event()
    release_gate2 = threading.Event()
    order2: list[str] = []

    orig_reserve2 = store2.reserve_budget
    orig_release_quota2 = store2.release_quota
    orig_finalize2 = store2.finalize_usage_event

    def gated_reserve2(
        k_id: str,
        req_id: str,
        est_tokens: int,
        est_cost: Decimal | None,
        now: datetime,
    ) -> str | None:
        order2.append("budget_reserve_enter")
        reserve_entered.set()
        assert reserve_gate.wait(timeout=5.0)
        res = orig_reserve2(k_id, req_id, est_tokens, est_cost, now)
        order2.append("budget_reserve_exit")
        return res

    def failing_release2(k_id: str, req_id: str) -> None:
        order2.append("release_budget_enter")
        release_entered2.set()
        assert release_gate2.wait(timeout=5.0)
        order2.append("release_budget_fail")
        raise RuntimeError("simulated admission budget release failure")

    def tracked_release_quota2(u_id: str, req_id: str) -> None:
        order2.append("release_quota")
        orig_release_quota2(u_id, req_id)

    def tracked_finalize2(ev: RequestUsageEvent) -> bool:
        order2.append("finalize")
        return orig_finalize2(ev)

    store2.reserve_budget = gated_reserve2  # type: ignore[method-assign]
    store2.release_budget = failing_release2  # type: ignore[method-assign]
    store2.release_quota = tracked_release_quota2  # type: ignore[method-assign]
    store2.finalize_usage_event = tracked_finalize2  # type: ignore[method-assign]

    async def run_failing_admission_cleanup() -> None:
        task = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid2), request2)
        )
        assert await asyncio.to_thread(reserve_entered.wait, 5.0)
        task.cancel()
        reserve_gate.set()

        assert await asyncio.to_thread(release_entered2.wait, 5.0)
        task.cancel()
        await asyncio.sleep(0)
        release_gate2.set()

        response = await task
        assert response.status_code == 499
        assert order2 == [
            "budget_reserve_enter",
            "budget_reserve_exit",
            "release_budget_enter",
            "release_budget_fail",
            "release_quota",
            "finalize",
        ]
        window = quota_window_start(datetime.now(UTC))
        assert store2.get_quota_usage(uid2, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 0,
        }
        assert len(store2.budget_usage) == 1
        assert store2.finalize_calls == 1
        event2 = next(iter(store2.usage_events.values()))
        assert event2.reserved_tokens == 71

    asyncio.run(run_failing_admission_cleanup())


def test_budget_reserve_cancellation_with_quota_held_preserves_order() -> None:
    """Cancelling during budget_reserve when quota is held preserves exact cleanup order."""
    import asyncio
    import threading
    from datetime import UTC

    from sabiroute.api.completions import chat_completions
    from sabiroute.quotas import quota_window_start

    state, store, stub, _, uid = _make_quota_and_budget_harness()
    request = _make_direct_completion_request(state)
    budget_reserve_entered = threading.Event()
    budget_reserve_gate = threading.Event()
    release_budget_entered = threading.Event()
    release_budget_gate = threading.Event()
    order: list[str] = []

    orig_quota_reserve = store.check_and_reserve_quota
    orig_budget_reserve = store.reserve_budget
    orig_release_budget = store.release_budget
    orig_release_quota = store.release_quota
    orig_finalize = store.finalize_usage_event

    def tracked_quota_reserve(*args: Any, **kwargs: Any) -> bool:
        order.append("quota_reserve")
        return orig_quota_reserve(*args, **kwargs)

    def gated_budget_reserve(
        k_id: str,
        req_id: str,
        est_tokens: int,
        est_cost: Decimal | None,
        now: datetime,
    ) -> str | None:
        order.append("budget_reserve_enter")
        budget_reserve_entered.set()
        assert budget_reserve_gate.wait(timeout=5.0)
        res = orig_budget_reserve(k_id, req_id, est_tokens, est_cost, now)
        order.append("budget_reserve_exit")
        return res

    def gated_release_budget(k_id: str, req_id: str) -> None:
        order.append("release_budget_enter")
        release_budget_entered.set()
        assert release_budget_gate.wait(timeout=5.0)
        orig_release_budget(k_id, req_id)
        order.append("release_budget_exit")

    def tracked_release_quota(u_id: str, req_id: str) -> None:
        order.append("release_quota")
        orig_release_quota(u_id, req_id)

    def tracked_finalize(ev: RequestUsageEvent) -> bool:
        order.append("finalize")
        return orig_finalize(ev)

    store.check_and_reserve_quota = tracked_quota_reserve  # type: ignore[method-assign]
    store.reserve_budget = gated_budget_reserve  # type: ignore[method-assign]
    store.release_budget = gated_release_budget  # type: ignore[method-assign]
    store.release_quota = tracked_release_quota  # type: ignore[method-assign]
    store.finalize_usage_event = tracked_finalize  # type: ignore[method-assign]

    async def run_scenario() -> None:
        task = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid), request)
        )
        assert await asyncio.to_thread(budget_reserve_entered.wait, 5.0)
        # First cancel while budget_reserve worker is still running.
        task.cancel()
        await asyncio.sleep(0)
        assert order == ["quota_reserve", "budget_reserve_enter"]
        assert not task.done()

        budget_reserve_gate.set()
        assert await asyncio.to_thread(release_budget_entered.wait, 5.0)
        # Second cancel while release_budget cleanup is in flight.
        task.cancel()
        await asyncio.sleep(0)
        release_budget_gate.set()

        response = await task
        assert response.status_code == 499
        assert order == [
            "quota_reserve",
            "budget_reserve_enter",
            "budget_reserve_exit",
            "release_budget_enter",
            "release_budget_exit",
            "release_quota",
            "finalize",
        ]
        assert store.budget_usage == {}
        window = quota_window_start(datetime.now(UTC))
        assert store.get_quota_usage(uid, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 0,
        }
        assert store.finalize_calls == 1
        event = next(iter(store.usage_events.values()))
        assert event.final_status == 499
        assert event.failure_category == "client_cancelled"
        assert event.reserved_tokens is None
        assert state.store_executor.in_use_count == 0
        assert stub.calls == []

    asyncio.run(run_scenario())


def test_worker_closed_loop_fallback_does_not_set_event_off_thread_or_mask_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Closed-loop fallback clears in_flight without calling Event.set off-thread."""
    import asyncio
    import json
    import threading

    from sabiroute.api.completions import ChatCompletionRequest, chat_completions
    from sabiroute.gateway import build_gateway_state

    stub = StubLiteLLMClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=stub, key_store=store)
    provision_test_key(state)
    key_id = next(iter(store.records))
    store.set_budget(key_id, ApiKeyBudget(daily_tokens=1000))
    request = _make_direct_completion_request(state)

    off_thread_event_sets: list[str] = []
    closed_loop_fallback_triggered = 0
    orig_event_set = asyncio.Event.set

    def guarded_event_set(self: asyncio.Event) -> None:
        if threading.current_thread().name == "sabiroute-store-worker":
            off_thread_event_sets.append(threading.current_thread().name)
        orig_event_set(self)

    monkeypatch.setattr(asyncio.Event, "set", guarded_event_set)

    # Create a closed event loop with a pending waiter future to prove that if
    # done.set() were called on the worker thread during the closed-loop
    # fallback, it would raise a secondary RuntimeError("Event loop is closed")
    # and mask the worker's return value or exception.
    closed_loop = asyncio.new_event_loop()
    closed_waiter = closed_loop.create_future()
    closed_loop.close()

    fail_reserve = False
    orig_reserve = store.reserve_budget

    def reserve_with_failing_Flag(
        k_id: str,
        req_id: str,
        est_tokens: int,
        est_cost: Decimal | None,
        now: datetime,
    ) -> str | None:
        if fail_reserve:
            raise ValueError("original reserve_budget failure")
        return orig_reserve(k_id, req_id, est_tokens, est_cost, now)

    store.reserve_budget = reserve_with_failing_Flag  # type: ignore[method-assign]

    async def run_scenario() -> None:
        nonlocal closed_loop_fallback_triggered, fail_reserve
        loop = asyncio.get_running_loop()
        orig_call_soon_threadsafe = loop.call_soon_threadsafe

        def intercept_untrack(callback: Any, *args: Any, **kwargs: Any) -> Any:
            nonlocal closed_loop_fallback_triggered
            if (
                getattr(callback, "__name__", "") == "_untrack"
                and args
                and args[0] == "budget_reserve"
            ):
                done_event = args[1]
                # Attach the closed-loop waiter before triggering the fallback;
                # remove it before returning to the event loop so normal loop-thread
                # cleanup after store_executor.run() stays clean.
                done_event._waiters.append(closed_waiter)
                closed_loop_fallback_triggered += 1

                def remove_closed_waiter() -> None:
                    if closed_waiter in done_event._waiters:
                        done_event._waiters.remove(closed_waiter)

                orig_call_soon_threadsafe(remove_closed_waiter)
                raise RuntimeError("Event loop is closed")
            return orig_call_soon_threadsafe(callback, *args, **kwargs)

        monkeypatch.setattr(loop, "call_soon_threadsafe", intercept_untrack)

        # 1. Normal return value is preserved when _untrack fallback runs.
        ok_resp = await chat_completions(
            ChatCompletionRequest(
                model="primary",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=16,
            ),
            request,
        )
        assert ok_resp.status_code == 200
        assert closed_loop_fallback_triggered == 1
        assert off_thread_event_sets == []

        # 2. Original worker exception is preserved (not masked by closed loop)
        # and finish() does not hang on in_flight.
        fail_reserve = True
        err_resp = await chat_completions(
            ChatCompletionRequest(
                model="primary",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=16,
            ),
            request,
        )
        assert err_resp.status_code == 503
        err_payload = json.loads(bytes(err_resp.body).decode("utf-8"))
        assert err_payload["error"]["type"] == "budget_store_unavailable"
        assert closed_loop_fallback_triggered == 2
        assert off_thread_event_sets == []
        assert state.store_executor.in_use_count == 0

    asyncio.run(run_scenario())


def test_shared_inference_check_cancellation_compensates_and_finalizes() -> None:
    """Cancellation during per-attempt shared-inference check compensates and finalizes."""
    import asyncio
    import threading
    from datetime import UTC

    from sabiroute.api.completions import chat_completions
    from sabiroute.quotas import quota_window_start

    state, store, stub, _, uid = _make_quota_and_budget_harness()
    request = _make_direct_completion_request(state)
    check_entered = threading.Event()
    check_gate = threading.Event()
    order: list[str] = []
    shared_calls = 0

    orig_quota_reserve = store.check_and_reserve_quota
    orig_budget_reserve = store.reserve_budget
    orig_get_shared = store.get_shared_inference
    orig_release_budget = store.release_budget
    orig_release_quota = store.release_quota
    orig_finalize = store.finalize_usage_event

    def tracked_quota_reserve(*args: Any, **kwargs: Any) -> bool:
        order.append("quota_reserve")
        return orig_quota_reserve(*args, **kwargs)

    def tracked_budget_reserve(*args: Any, **kwargs: Any) -> str | None:
        order.append("budget_reserve")
        return orig_budget_reserve(*args, **kwargs)

    def gated_get_shared_inference() -> bool | None:
        nonlocal shared_calls
        shared_calls += 1
        if shared_calls == 1:
            return orig_get_shared()
        order.append("shared_inference_enter")
        check_entered.set()
        assert check_gate.wait(timeout=5.0)
        res = orig_get_shared()
        order.append("shared_inference_exit")
        return res

    def tracked_release_budget(k_id: str, req_id: str) -> None:
        order.append("release_budget")
        orig_release_budget(k_id, req_id)

    def tracked_release_quota(u_id: str, req_id: str) -> None:
        order.append("release_quota")
        orig_release_quota(u_id, req_id)

    def tracked_finalize(ev: RequestUsageEvent) -> bool:
        order.append("finalize")
        return orig_finalize(ev)

    store.check_and_reserve_quota = tracked_quota_reserve  # type: ignore[method-assign]
    store.reserve_budget = tracked_budget_reserve  # type: ignore[method-assign]
    store.get_shared_inference = gated_get_shared_inference  # type: ignore[method-assign]
    store.release_budget = tracked_release_budget  # type: ignore[method-assign]
    store.release_quota = tracked_release_quota  # type: ignore[method-assign]
    store.finalize_usage_event = tracked_finalize  # type: ignore[method-assign]

    async def run_scenario() -> None:
        task = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid), request)
        )
        assert await asyncio.to_thread(check_entered.wait, 5.0)
        # Cancel while per-attempt shared_inference_check worker is in flight
        # after quota_reserve and budget_reserve have committed.
        task.cancel()
        await asyncio.sleep(0)
        assert order == [
            "quota_reserve",
            "budget_reserve",
            "shared_inference_enter",
        ]
        assert not task.done()

        check_gate.set()
        response = await task
        assert response.status_code == 499
        assert order == [
            "quota_reserve",
            "budget_reserve",
            "shared_inference_enter",
            "shared_inference_exit",
            "release_budget",
            "release_quota",
            "finalize",
        ]
        assert store.budget_usage == {}
        window = quota_window_start(datetime.now(UTC))
        assert store.get_quota_usage(uid, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 0,
        }
        assert store.finalize_calls == 1
        event = next(iter(store.usage_events.values()))
        assert event.final_status == 499
        assert event.failure_category == "client_cancelled"
        assert event.reserved_tokens is None
        assert state.store_executor.in_use_count == 0
        assert stub.calls == []

    asyncio.run(run_scenario())


def test_second_attempt_snapshot_cancellation_preserves_first_attempt_accounting() -> None:
    """Cancelling on Attempt 2 after Attempt 1 failed reconciles and attributes Attempt 1."""
    import asyncio
    import threading
    from datetime import UTC

    from sabiroute.api.completions import ChatCompletionRequest, chat_completions
    from sabiroute.freepool.eligibility import FreePoolPolicy
    from sabiroute.gateway import build_gateway_state
    from sabiroute.quotas import QuotaPolicy, quota_window_start
    from sabiroute.routing.policies import RoutingPolicy
    from sabiroute.security.keys import (
        SABI_USER_ID_FIELD,
        validate_usage_event_finalization,
    )

    uid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    stub = StubLiteLLMClient()

    async def fail_primary_with_usage(
        decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        stub.calls.append(decision.deployment)
        if decision.deployment == "primary":
            raise LiteLLMClientError(
                "stub failure for primary",
                status_code=500,
                response_body={
                    "usage": {
                        "prompt_tokens": 3,
                        "completion_tokens": 0,
                        "total_tokens": 3,
                    }
                },
            )
        return {
            "id": "chatcmpl-stub",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    stub.chat_completion = fail_primary_with_usage  # type: ignore[method-assign]
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=store,
        free_pool=FreePoolPolicy(
            enabled=True, eligible_deployments=frozenset({"primary", "secondary"})
        ),
        quota_policy=QuotaPolicy(pilot_users=frozenset({uid})),
    )
    state.policies.register(
        RoutingPolicy(
            name="fast",
            deployments=["primary", "secondary"],
            strategy="priority",
            max_attempts=2,
        )
    )
    record, _ = issue_api_key(
        store, project_id="sabichat-service", name="sabichat-service"
    )
    state.sabichat_service_key_id = record.key_id
    enable_shared_inference(state)
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))
    request = _make_direct_completion_request(state)

    snapshot2_entered = threading.Event()
    snapshot2_gate = threading.Event()
    order: list[str] = []
    snapshot_calls = 0

    orig_quota_reserve = store.check_and_reserve_quota
    orig_budget_reserve = store.reserve_budget
    orig_snapshot = store.append_pre_routing_feature_snapshot
    orig_reconcile = store.reconcile_budget
    orig_release_budget = store.release_budget
    orig_settle_quota = store.settle_quota
    orig_release_quota = store.release_quota
    orig_finalize = store.finalize_usage_event

    def tracked_quota_reserve(*args: Any, **kwargs: Any) -> bool:
        order.append("quota_reserve")
        return orig_quota_reserve(*args, **kwargs)

    def tracked_budget_reserve(*args: Any, **kwargs: Any) -> str | None:
        order.append("budget_reserve")
        return orig_budget_reserve(*args, **kwargs)

    def gated_snapshot(req_id: str, snap: Mapping[str, Any]) -> bool:
        nonlocal snapshot_calls
        snapshot_calls += 1
        if snapshot_calls == 1:
            order.append("snapshot_1")
            return orig_snapshot(req_id, snap)
        order.append("snapshot_2_enter")
        snapshot2_entered.set()
        assert snapshot2_gate.wait(timeout=5.0)
        res = orig_snapshot(req_id, snap)
        order.append("snapshot_2_exit")
        return res

    def tracked_reconcile(
        k_id: str, req_id: str, actual_tokens: int | None, actual_cost: Decimal | None
    ) -> None:
        order.append("reconcile_budget")
        orig_reconcile(k_id, req_id, actual_tokens, actual_cost)

    def tracked_release_budget(k_id: str, req_id: str) -> None:
        order.append("release_budget")
        orig_release_budget(k_id, req_id)

    def tracked_settle_quota(u_id: str, req_id: str, actual_tokens: int | None) -> None:
        order.append("settle_quota")
        orig_settle_quota(u_id, req_id, actual_tokens)

    def tracked_release_quota(u_id: str, req_id: str) -> None:
        order.append("release_quota")
        orig_release_quota(u_id, req_id)

    def tracked_finalize(ev: RequestUsageEvent) -> bool:
        order.append("finalize")
        return orig_finalize(ev)

    store.check_and_reserve_quota = tracked_quota_reserve  # type: ignore[method-assign]
    store.reserve_budget = tracked_budget_reserve  # type: ignore[method-assign]
    store.append_pre_routing_feature_snapshot = gated_snapshot  # type: ignore[method-assign]
    store.reconcile_budget = tracked_reconcile  # type: ignore[method-assign]
    store.release_budget = tracked_release_budget  # type: ignore[method-assign]
    store.settle_quota = tracked_settle_quota  # type: ignore[method-assign]
    store.release_quota = tracked_release_quota  # type: ignore[method-assign]
    store.finalize_usage_event = tracked_finalize  # type: ignore[method-assign]

    payload = ChatCompletionRequest.model_validate(
        {
            "model": "fast",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
            "sabi_route_free_chat": True,
            SABI_USER_ID_FIELD: uid,
        }
    )

    async def run_scenario() -> None:
        task = asyncio.create_task(chat_completions(payload, request))
        assert await asyncio.to_thread(snapshot2_entered.wait, 5.0)
        assert stub.calls == ["primary"]

        # Cancel during Attempt 2's pre-routing feature snapshot write.
        task.cancel()
        await asyncio.sleep(0)
        assert order == [
            "quota_reserve",
            "budget_reserve",
            "snapshot_1",
            "snapshot_2_enter",
        ]
        snapshot2_gate.set()

        with pytest.raises(asyncio.CancelledError):
            await task

        assert order == [
            "quota_reserve",
            "budget_reserve",
            "snapshot_1",
            "snapshot_2_enter",
            "snapshot_2_exit",
            "reconcile_budget",
            "settle_quota",
            "finalize",
        ]
        assert "release_budget" not in order
        assert "release_quota" not in order
        window = quota_window_start(datetime.now(UTC))
        assert store.get_quota_usage(uid, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 3,
        }
        assert len(store.budget_usage) == 1
        assert store.finalize_calls == 1
        event = next(iter(store.usage_events.values()))
        validate_usage_event_finalization(event)
        assert event.final_status == 499
        assert event.final_deployment == "primary"
        assert event.failure_category == "client_cancelled"
        assert event.total_tokens == 3
        assert len(event.pre_routing_features) == 1
        assert len(event.routing_decisions) == 1
        assert event.routing_decisions[0]["selected_deployment"] == "primary"
        assert state.store_executor.in_use_count == 0

    asyncio.run(run_scenario())


def test_queued_cleanup_repeated_cancellation_preserves_fifo_and_post_spawn_window() -> None:
    """Queued cleanup preserves FIFO order under repeated cancel; post-spawn window is tracked."""
    import asyncio
    import threading
    from datetime import UTC

    from sabiroute.api.completions import chat_completions
    from sabiroute.quotas import quota_window_start
    from sabiroute.security.store_executor import BoundedStoreExecutor

    # Part 1: Queued cleanup operation (shield_cancellation=True) under repeated
    # cancellation preserves its FIFO queue position and executes once.
    state, store, stub, _, uid = _make_quota_and_budget_harness()
    state.store_executor = BoundedStoreExecutor(max_concurrency=1)
    request = _make_direct_completion_request(state)

    snapshot_entered = asyncio.Event()
    snapshot_release = threading.Event()
    holder_entered = threading.Event()
    holder_release = threading.Event()
    order: list[str] = []

    orig_snapshot = store.append_pre_routing_feature_snapshot
    orig_release_budget = store.release_budget
    orig_release_quota = store.release_quota
    orig_finalize = store.finalize_usage_event

    async def run_queued_cleanup_fifo() -> None:
        loop = asyncio.get_running_loop()

        def gated_snapshot(req_id: str, snap: Mapping[str, Any]) -> bool:
            order.append("snapshot_enter")
            loop.call_soon_threadsafe(snapshot_entered.set)
            assert snapshot_release.wait(timeout=5.0)
            res = orig_snapshot(req_id, snap)
            order.append("snapshot_exit")
            return res

        def hold_slot() -> None:
            order.append("holder_enter")
            holder_entered.set()
            assert holder_release.wait(timeout=5.0)
            order.append("holder_exit")

        def late_worker() -> str:
            order.append("late_worker")
            return "late"

        def tracked_release_budget(k_id: str, req_id: str) -> None:
            order.append("release_budget")
            orig_release_budget(k_id, req_id)

        def tracked_release_quota(u_id: str, req_id: str) -> None:
            order.append("release_quota")
            orig_release_quota(u_id, req_id)

        def tracked_finalize(ev: RequestUsageEvent) -> bool:
            order.append("finalize")
            return orig_finalize(ev)

        store.append_pre_routing_feature_snapshot = gated_snapshot  # type: ignore[method-assign]
        store.release_budget = tracked_release_budget  # type: ignore[method-assign]
        store.release_quota = tracked_release_quota  # type: ignore[method-assign]
        store.finalize_usage_event = tracked_finalize  # type: ignore[method-assign]

        task = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid), request)
        )
        await snapshot_entered.wait()

        # Queue blocker_task while snapshot holds the sole executor slot so
        # hold_slot acquires the slot next, forcing budget_cleanup to queue.
        blocker_task = asyncio.create_task(state.store_executor.run(hold_slot))
        while not state.store_executor._semaphore._waiters:
            await asyncio.sleep(0)

        # First cancel interrupts snapshot; release snapshot so hold_slot starts
        # and budget_cleanup queues at FIFO index 0.
        task.cancel()
        snapshot_release.set()
        assert await asyncio.to_thread(holder_entered.wait, 5.0)
        while not state.store_executor._semaphore._waiters:
            await asyncio.sleep(0)

        cleanup_waiter = state.store_executor._semaphore._waiters[0]
        # Enqueue a second waiter behind budget_cleanup.
        late_task = asyncio.create_task(state.store_executor.run(late_worker))
        while len(state.store_executor._semaphore._waiters) < 2:
            await asyncio.sleep(0)

        # Deliver repeated cancellations to the request task while budget_cleanup
        # is queued on the semaphore.
        for _ in range(3):
            task.cancel()
            await asyncio.sleep(0)

        # The shielded cleanup waiter never left _waiters and kept FIFO index 0.
        assert len(state.store_executor._semaphore._waiters) == 2
        assert state.store_executor._semaphore._waiters[0] is cleanup_waiter

        holder_release.set()
        await blocker_task
        response = await task
        assert await late_task == "late"

        assert response.status_code == 499
        assert order == [
            "snapshot_enter",
            "snapshot_exit",
            "holder_enter",
            "holder_exit",
            "release_budget",
            "late_worker",
            "release_quota",
            "finalize",
        ]
        assert store.budget_usage == {}
        window = quota_window_start(datetime.now(UTC))
        assert store.get_quota_usage(uid, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 0,
        }
        assert store.finalize_calls == 1
        assert state.store_executor.in_use_count == 0
        assert stub.calls == []

    asyncio.run(run_queued_cleanup_fifo())

    # Part 2: Post-spawn / pre-first-instruction cancellation window (F-17.1.2-05).
    # Cancel the caller on the event loop right when _on_worker_spawned fires
    # (after Thread.start(), before reserve_budget executes its body).
    state2, store2, stub2, _, uid2 = _make_quota_and_budget_harness()
    request2 = _make_direct_completion_request(state2)
    allow_worker_body = threading.Event()
    reserve_body_ran = False
    order2: list[str] = []

    orig_reserve2 = store2.reserve_budget
    orig_release_budget2 = store2.release_budget
    orig_release_quota2 = store2.release_quota
    orig_finalize2 = store2.finalize_usage_event
    orig_executor_run = state2.store_executor.run

    def gated_reserve_body(
        k_id: str,
        req_id: str,
        est_tokens: int,
        est_cost: Decimal | None,
        now: datetime,
    ) -> str | None:
        nonlocal reserve_body_ran
        assert allow_worker_body.wait(timeout=5.0)
        reserve_body_ran = True
        order2.append("budget_reserve_body")
        return orig_reserve2(k_id, req_id, est_tokens, est_cost, now)

    def tracked_release_budget2(k_id: str, req_id: str) -> None:
        order2.append("release_budget")
        orig_release_budget2(k_id, req_id)

    def tracked_release_quota2(u_id: str, req_id: str) -> None:
        order2.append("release_quota")
        orig_release_quota2(u_id, req_id)

    def tracked_finalize2(ev: RequestUsageEvent) -> bool:
        order2.append("finalize")
        return orig_finalize2(ev)

    store2.reserve_budget = gated_reserve_body  # type: ignore[method-assign]
    store2.release_budget = tracked_release_budget2  # type: ignore[method-assign]
    store2.release_quota = tracked_release_quota2  # type: ignore[method-assign]
    store2.finalize_usage_event = tracked_finalize2  # type: ignore[method-assign]

    async def run_post_spawn_window() -> None:
        spawned_budget_reserve = asyncio.Event()
        accounting_calls = 0

        async def intercept_executor_run(
            func: Any, /, *args: Any, **kwargs: Any
        ) -> Any:
            nonlocal accounting_calls
            orig_hook = getattr(func, "_on_worker_spawned", None)
            if callable(orig_hook):
                accounting_calls += 1
                # Tracked call #2 is budget_reserve (after quota_reserve).
                if accounting_calls == 2:

                    def hooked_on_spawned() -> None:
                        orig_hook()
                        spawned_budget_reserve.set()

                    func._on_worker_spawned = hooked_on_spawned
            return await orig_executor_run(func, *args, **kwargs)

        state2.store_executor.run = intercept_executor_run  # type: ignore[method-assign]

        task2 = asyncio.create_task(
            chat_completions(_make_free_chat_payload(uid2), request2)
        )
        await spawned_budget_reserve.wait()
        # Cancel immediately after worker thread spawn, BEFORE reserve_budget
        # has executed its body on the worker thread.
        assert reserve_body_ran is False
        task2.cancel()
        await asyncio.sleep(0)
        assert reserve_body_ran is False
        assert not task2.done()

        allow_worker_body.set()
        response2 = await task2
        assert response2.status_code == 499
        assert reserve_body_ran is True
        assert order2 == [
            "budget_reserve_body",
            "release_budget",
            "release_quota",
            "finalize",
        ]
        assert store2.budget_usage == {}
        window = quota_window_start(datetime.now(UTC))
        assert store2.get_quota_usage(uid2, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 0,
        }
        assert store2.finalize_calls == 1
        assert state2.store_executor.in_use_count == 0
        assert stub2.calls == []

    asyncio.run(run_post_spawn_window())


def test_explicit_dotenv_file_loading_is_preserved_and_isolated(
    tmp_path: Any,
) -> None:
    """Explicit .env loading works via DEFAULT_ENV_PATH without leaking across tests."""
    import os

    import sabiroute.config.loader as config_loader
    from sabiroute.config.loader import load_raw_config

    assert "REDIS_URL" not in os.environ
    assert "DATABASE_URL" not in os.environ

    # Write to the isolated per-test DEFAULT_ENV_PATH provided by the fixture.
    config_loader.DEFAULT_ENV_PATH.write_text(
        "OPENAI_API_KEY=sk-from-isolated-dotenv\n"
        "REDIS_URL=redis://127.0.0.1:6379/9\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "model_list:\n"
        "  - model_name: openai-test\n"
        "    litellm_params:\n"
        "      model: openai/gpt-4o-mini\n"
        "      api_key: os.environ/OPENAI_API_KEY\n",
        encoding="utf-8",
    )

    raw = load_raw_config(config_file, resolve_env=True)
    assert raw["model_list"][0]["litellm_params"]["api_key"] == "sk-from-isolated-dotenv"
    assert os.environ.get("REDIS_URL") == "redis://127.0.0.1:6379/9"


def pytest_collectstart(collector: pytest.Collector) -> None:
    if isinstance(collector, pytest.Module):
        name = collector.path.name
        if name == "test_deadline.py":
            for fn in (
                test_accounting_success_and_exception_clear_in_flight,
                test_running_worker_cancellation_waits_before_cleanup,
                test_queued_worker_cancellation_does_not_hang_or_leak,
                test_repeated_cancellation_during_budget_cleanup_completes_quota_and_finalizes,
                test_budget_cleanup_failure_under_cancellation_attempts_quota_and_preserves_flag,
                test_budget_reserve_cancellation_with_quota_held_preserves_order,
                test_worker_closed_loop_fallback_does_not_set_event_off_thread_or_mask_outcome,
                test_shared_inference_check_cancellation_compensates_and_finalizes,
                test_second_attempt_snapshot_cancellation_preserves_first_attempt_accounting,
                test_queued_cleanup_repeated_cancellation_preserves_fifo_and_post_spawn_window,
            ):
                setattr(collector.obj, fn.__name__, fn)
        elif name == "test_loader.py":
            collector.obj.test_explicit_dotenv_file_loading_is_preserved_and_isolated = (
                test_explicit_dotenv_file_loading_is_preserved_and_isolated
            )
