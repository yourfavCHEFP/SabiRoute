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
        self.fail_usage_writes = False
        self.fail_feature_snapshot_writes = False
        self.fail_finalize_usage_writes = False
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
