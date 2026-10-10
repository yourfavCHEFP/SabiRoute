from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from sqlalchemy import create_engine
from starlette.requests import Request

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.routing.policies import RoutingPolicy
from sabiroute.security.budgets import estimate_input_tokens
from sabiroute.security.keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    RequestUsageEvent,
    UsageEventValidationError,
    issue_api_key,
    rotate_api_key,
)
from sabiroute.security.rate_limit import RedisTokenBucket
from sabiroute.security.store import PostgresApiKeyStore

MESSAGES = [{"role": "user", "content": "hello"}]


class AtomicMemoryRedis:
    """Atomic bucket test double using the same refill/burst contract as Redis Lua."""

    def __init__(self) -> None:
        self.now_ms = 0
        self.buckets: dict[str, tuple[float, int]] = {}

    async def eval(
        self,
        script: str,
        numkeys: int,
        key: str,
        requests_per_minute: int,
        burst_capacity: int,
    ) -> list[int]:
        tokens, last_ms = self.buckets.get(key, (float(burst_capacity), self.now_ms))
        now_ms = max(self.now_ms, last_ms)
        tokens = min(
            float(burst_capacity),
            tokens + (now_ms - last_ms) * requests_per_minute / 60_000,
        )
        admitted = int(tokens >= 1)
        if admitted:
            tokens -= 1
        self.buckets[key] = (tokens, now_ms)
        retry_ms = 0 if admitted else int((1 - tokens) * 60_000 / requests_per_minute + 0.999999999)
        return [admitted, retry_ms]

    async def aclose(self) -> None:
        return None


class FailedRedis:
    async def eval(self, *args: object) -> list[int]:
        raise ConnectionError("redis unavailable")

    async def aclose(self) -> None:
        return None


def _state(
    *,
    failures: dict[str, int] | None = None,
    redis: object | None = None,
) -> tuple[object, InMemoryApiKeyStore, StubLiteLLMClient, str]:
    store = InMemoryApiKeyStore()
    stub = StubLiteLLMClient(failures=failures)
    redis_client = redis or AtomicMemoryRedis()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=store,
        rate_limiter=RedisTokenBucket(cast(Redis, redis_client)),
    )
    state.policies.register(
        RoutingPolicy(
            name="fast",
            deployments=["primary", "secondary"],
            strategy="priority",
            max_attempts=2,
        )
    )
    _, secret = issue_api_key(store, project_id="project-shared", name="client")
    return state, store, stub, secret


def test_one_client_request_consumes_one_bucket_token_across_fallback(monkeypatch) -> None:
    state, store, stub, secret = _state(failures={"primary": 1})
    record = next(iter(store.records.values()))
    store.set_rate_limit(record.key_id, ApiKeyRateLimit(requests_per_minute=60, burst_capacity=1))
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "separate-phase10-admin")

    with TestClient(create_app(state=state)) as client:
        first = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {secret}"},
        )
        second = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert first.status_code == 200
    assert first.headers["X-SabiRoute-Attempt"] == "2"
    assert first.headers["X-SabiRoute-Request-ID"]
    assert second.status_code == 429
    assert second.json()["error"]["type"] == "rate_limit_exceeded"
    assert second.headers["Retry-After"] == "1"
    assert second.headers["X-SabiRoute-Request-ID"]
    assert stub.calls == ["primary", "secondary"]
    assert state.metrics.snapshot()["requests_total"] == 2
    assert state.metrics.snapshot()["requests_rate_limited"] == 1

    events = list(store.usage_events.values())
    assert len(events) == 2
    successful = next(event for event in events if event.final_status == 200)
    limited = next(event for event in events if event.final_status == 429)
    assert successful.key_id == record.key_id
    assert successful.project_id == record.project_id
    assert successful.final_deployment == "secondary"
    assert successful.total_tokens == 5
    assert limited.failure_category == "rate_limited"
    assert limited.total_tokens is None


def test_configured_rate_limit_fails_closed_when_redis_is_unavailable() -> None:
    state, store, stub, secret = _state(redis=FailedRedis())
    record = next(iter(store.records.values()))
    store.set_rate_limit(record.key_id, ApiKeyRateLimit(requests_per_minute=10, burst_capacity=2))

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "rate_limiter_unavailable"
    assert stub.calls == []
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 503
    assert event.failure_category == "redis_unavailable"


def test_usage_store_failure_rejects_before_provider_execution() -> None:
    state, store, stub, secret = _state()
    store.fail_usage_writes = True

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "usage_store_unavailable"
    assert stub.calls == []
    assert store.usage_events == {}


def test_authenticated_request_without_trusted_identity_fails_closed() -> None:
    state, store, stub, _ = _state()
    app = create_app(state=state)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/chat/completions",
        "raw_path": b"/v1/chat/completions",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
        "app": app,
    }

    response = asyncio.run(
        chat_completions(
            ChatCompletionRequest(model="primary", messages=MESSAGES),
            Request(scope),
        )
    )

    assert response.status_code == 500
    assert json.loads(response.body)["error"]["type"] == "request_identity_unavailable"
    assert store.usage_events == {}
    assert stub.calls == []


def test_admin_can_set_limits_and_page_key_scoped_usage_without_secrets(monkeypatch) -> None:
    state, store, _, first_secret = _state()
    first_record = next(iter(store.records.values()))
    _, second_secret = issue_api_key(store, project_id=first_record.project_id, name="other client")
    admin_secret = "separate-phase10-admin"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", admin_secret)

    with TestClient(create_app(state=state)) as client:
        first_response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {first_secret}"},
        )
        second_response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {second_secret}"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_secret}"}
        set_response = client.put(
            f"/admin/api-keys/{first_record.key_id}/rate-limit",
            json={"requests_per_minute": 120, "burst_capacity": 5},
            headers=admin_headers,
        )
        limit_response = client.get(
            f"/admin/api-keys/{first_record.key_id}/rate-limit",
            headers=admin_headers,
        )
        clear_response = client.delete(
            f"/admin/api-keys/{first_record.key_id}/rate-limit",
            headers=admin_headers,
        )
        cleared_limit_response = client.get(
            f"/admin/api-keys/{first_record.key_id}/rate-limit",
            headers=admin_headers,
        )
        usage_response = client.get(
            f"/admin/api-keys/{first_record.key_id}/usage?limit=1&offset=0",
            headers=admin_headers,
        )
        oversized_page = client.get(
            f"/admin/api-keys/{first_record.key_id}/usage?limit=101",
            headers=admin_headers,
        )

    assert first_response.status_code == second_response.status_code == 200
    assert set_response.status_code == 200
    assert set_response.json()["requests_per_minute"] == 120
    assert limit_response.json()["burst_capacity"] == 5
    assert clear_response.status_code == 200
    assert cleared_limit_response.json()["requests_per_minute"] is None
    assert usage_response.status_code == 200
    assert usage_response.json()["total"] == 1
    assert len(usage_response.json()["items"]) == 1
    assert usage_response.json()["items"][0]["request_id"] == first_response.headers[
        "X-SabiRoute-Request-ID"
    ]
    assert oversized_page.status_code == 422
    assert first_secret not in usage_response.text
    assert second_secret not in usage_response.text
    assert "key_hash" not in usage_response.text
    assert "api_key" not in usage_response.text


def test_sql_store_persists_limits_usage_and_rotation_atomically() -> None:
    engine = create_engine("sqlite:///:memory:")
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    try:
        old_record, old_secret = issue_api_key(store, project_id="project-pg", name="sql")
        limit = ApiKeyRateLimit(requests_per_minute=30, burst_capacity=4)
        assert store.set_rate_limit(old_record.key_id, limit)
        assert store.get_rate_limit(old_record.key_id) == limit
        budget = ApiKeyBudget(daily_tokens=100, monthly_tokens=1000)
        assert store.set_budget(old_record.key_id, budget)
        assert store.get_budget(old_record.key_id) == budget

        event = RequestUsageEvent(
            request_id="e870b7b7-bbd6-4705-9ab9-220f2a4e5b10",
            key_id=old_record.key_id,
            project_id=old_record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="fast",
        )
        store.create_usage_event(event)
        final = replace(
            event,
            final_deployment="deployment-a",
            final_status=200,
            prompt_tokens=12,
            completion_tokens=8,
            total_tokens=20,
        )
        assert store.finalize_usage_event(final) is True
        assert store.finalize_usage_event(final) is False
        page, total = store.list_usage_events(old_record.key_id, limit=1, offset=0)
        assert total == 1
        assert page[0].request_id == event.request_id
        assert page[0].total_tokens == 20
        assert old_secret not in repr(page)

        rotated = rotate_api_key(store, old_record.key_id)
        assert rotated is not None
        new_record, _ = rotated
        assert store.get_rate_limit(new_record.key_id) == limit
        assert store.get_rate_limit(old_record.key_id) == limit
        assert store.get_budget(new_record.key_id) == budget
    finally:
        store.close()


def test_sql_finalization_rejects_unpaired_attempt_telemetry() -> None:
    engine = create_engine("sqlite:///:memory:")
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    try:
        record, _ = issue_api_key(store, project_id="project-integrity", name="integrity")
        request_id = "00000000-0000-0000-0000-000000000021"
        event = RequestUsageEvent(
            request_id=request_id,
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="test",
        )
        store.create_usage_event(event)
        malformed = replace(
            event,
            final_deployment="deployment-a",
            final_status=200,
            pre_routing_features=(
                {
                    "feature_schema_version": "1.0",
                    "logical_request_id": request_id,
                    "attempt_number": 1,
                    "health_eligible_deployments": ["deployment-a"],
                },
            ),
        )

        with pytest.raises(UsageEventValidationError, match="attempt counts differ"):
            store.finalize_usage_event(malformed)

        rows, total = store.list_usage_events(record.key_id, limit=10, offset=0)
        assert total == 1
        assert rows[0].final_status is None
        assert rows[0].pre_routing_features == ()
        assert rows[0].routing_decisions == ()
    finally:
        store.close()


def test_sql_finalization_rejects_mismatched_attempt_metadata() -> None:
    engine = create_engine("sqlite:///:memory:")
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    try:
        record, _ = issue_api_key(store, project_id="project-integrity", name="integrity")
        request_id = "00000000-0000-0000-0000-000000000022"
        event = RequestUsageEvent(
            request_id=request_id,
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="test",
        )
        store.create_usage_event(event)
        now = datetime.now(UTC)
        feature = {
            "feature_schema_version": "1.0",
            "logical_request_id": request_id,
            "attempt_number": 1,
            "decision_timestamp": now.isoformat(),
            "candidate_deployments": ["deployment-a"],
            "capability_eligible_deployments": ["deployment-a"],
            "health_eligible_deployments": ["deployment-a"],
        }
        outcome = {
            "logical_request_id": request_id,
            "fallback_attempt": 1,
            "selected_deployment": "deployment-a",
            "eligible_deployments": ["deployment-a"],
            "outcome": "success",
        }
        valid = replace(
            event,
            final_deployment="deployment-a",
            final_status=200,
            pre_routing_features=(feature,),
            routing_decisions=(outcome,),
        )
        malformed_variants = (
            replace(valid, routing_decisions=(outcome | {"logical_request_id": "other"},)),
            replace(valid, routing_decisions=(outcome | {"fallback_attempt": 2},)),
            replace(valid, routing_decisions=(outcome | {"selected_deployment": "deployment-b"},)),
            replace(valid, routing_decisions=(outcome | {"outcome": None},)),
        )

        for malformed in malformed_variants:
            with pytest.raises(UsageEventValidationError):
                store.finalize_usage_event(malformed)

        rows, _ = store.list_usage_events(record.key_id, limit=10, offset=0)
        assert rows[0].final_status is None
    finally:
        store.close()


def test_sql_finalization_requires_complete_schema_1_1_timestamps() -> None:
    engine = create_engine("sqlite:///:memory:")
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    try:
        record, _ = issue_api_key(store, project_id="project-integrity", name="integrity")
        request_id = "00000000-0000-0000-0000-000000000023"
        event = RequestUsageEvent(
            request_id=request_id,
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="test",
            feature_schema_version="1.1",
        )
        store.create_usage_event(event)
        decision_at = datetime.now(UTC)
        started_at = decision_at.replace(microsecond=min(decision_at.microsecond + 1, 999999))
        completed_at = started_at
        recorded_at = completed_at
        feature = {
            "feature_schema_version": "1.1",
            "logical_request_id": request_id,
            "attempt_number": 1,
            "decision_timestamp": decision_at.isoformat(),
            "candidate_deployments": ["deployment-a"],
            "capability_eligible_deployments": ["deployment-a"],
            "health_eligible_deployments": ["deployment-a"],
        }
        outcome = {
            "request_id": request_id,
            "logical_request_id": request_id,
            "fallback_attempt": 1,
            "selected_deployment": "deployment-a",
            "eligible_deployments": ["deployment-a"],
            "outcome": "success",
            "attempt_schema_version": "1.1",
            "attempt_started_at": started_at.isoformat(),
            "attempt_completed_at": completed_at.isoformat(),
            "outcome_recorded_at": recorded_at.isoformat(),
        }
        malformed = replace(
            event,
            final_deployment="deployment-a",
            final_status=200,
            pre_routing_features=(feature,),
            routing_decisions=(outcome | {"outcome_recorded_at": None},),
        )

        with pytest.raises(
            UsageEventValidationError, match="timezone-aware provenance timestamps"
        ):
            store.finalize_usage_event(malformed)
    finally:
        store.close()


def test_sql_store_persists_pre_routing_snapshot_before_finalization() -> None:
    engine = create_engine("sqlite:///:memory:")
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    try:
        record, _ = issue_api_key(store, project_id="project-snapshot", name="snapshot")
        request_id = "00000000-0000-0000-0000-000000000024"
        event = RequestUsageEvent(
            request_id=request_id,
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="test",
            feature_schema_version=None,
        )
        store.create_usage_event(event)
        snapshot = {
            "feature_schema_version": "1.1",
            "logical_request_id": request_id,
            "attempt_number": 1,
            "decision_timestamp": datetime.now(UTC).isoformat(),
            "candidate_deployments": ["deployment-a"],
            "capability_eligible_deployments": ["deployment-a"],
            "health_eligible_deployments": ["deployment-a"],
        }

        assert store.append_pre_routing_feature_snapshot(request_id, snapshot) is True
        rows, total = store.list_usage_events(record.key_id, limit=10, offset=0)

        assert total == 1
        assert rows[0].final_status is None
        assert rows[0].feature_schema_version == "1.1"
        assert rows[0].pre_routing_features == (snapshot,)
        assert rows[0].routing_decisions == ()
        with pytest.raises(UsageEventValidationError, match="not sequential"):
            store.append_pre_routing_feature_snapshot(request_id, snapshot)

        after_rejection, _ = store.list_usage_events(record.key_id, limit=10, offset=0)
        assert after_rejection[0].pre_routing_features == (snapshot,)
    finally:
        store.close()


def test_sql_budget_reservations_enforce_daily_monthly_windows_and_reconcile(
    tmp_path,
) -> None:
    database_path = tmp_path / "phase10-budget.sqlite"
    database_url = f"sqlite:///{database_path}"
    store = PostgresApiKeyStore(database_url)
    record, _ = issue_api_key(store, project_id="budget-sql", name="budget")
    assert store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=100, monthly_tokens=150))
    march_first = datetime(2026, 3, 1, 10, tzinfo=UTC)
    assert store.reserve_budget(record.key_id, "request-1", 100, None, march_first) is None
    store.reconcile_budget(record.key_id, "request-1", 60, None)
    assert store.reserve_budget(record.key_id, "request-2", 40, None, march_first) is None
    assert store.reserve_budget(record.key_id, "request-3", 1, None, march_first) == (
        "daily_tokens_exceeded"
    )
    next_day = datetime(2026, 3, 2, 10, tzinfo=UTC)
    assert store.reserve_budget(record.key_id, "request-4", 50, None, next_day) is None
    assert store.reserve_budget(record.key_id, "request-5", 1, None, next_day) == (
        "monthly_tokens_exceeded"
    )
    next_month = datetime(2026, 4, 1, 10, tzinfo=UTC)
    assert store.reserve_budget(record.key_id, "request-6", 80, None, next_month) is None
    usage = store.get_budget_usage(record.key_id, next_month)
    assert usage["daily"]["tokens"] == 80
    assert usage["monthly"]["tokens"] == 80
    store.close()

    reopened = PostgresApiKeyStore(database_url)
    assert reopened.get_budget(record.key_id) == ApiKeyBudget(
        daily_tokens=100,
        monthly_tokens=150,
    )
    assert reopened.reserve_budget(record.key_id, "request-7", 20, None, next_month) is None
    reopened.close()


def test_token_budget_reserves_once_for_fallback_and_reconciles_actual(monkeypatch) -> None:
    state, store, stub, secret = _state(failures={"primary": 1})
    record = next(iter(store.records.values()))
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000, monthly_tokens=1000))
    # The failing attempt explicitly reports zero use, so the same reservation
    # is safe to reuse for the fallback deployment.
    async def failing_then_success(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        if decision.deployment == "primary":
            from sabiroute.providers.litellm_client import LiteLLMClientError

            raise LiteLLMClientError(
                "provider rejected before execution",
                status_code=500,
                response_body={"usage": {"prompt_tokens": 0, "completion_tokens": 0}},
            )
        return {
            "id": "completion",
            "choices": [],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    stub.chat_completion = failing_then_success
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "budget-admin")
    body = {"model": "fast", "messages": MESSAGES, "max_tokens": 20}
    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {secret}"},
        )

    event = next(iter(store.usage_events.values()))
    assert response.status_code == 200
    assert stub.calls == ["primary", "secondary"]
    assert event.estimated_input_tokens == estimate_input_tokens(MESSAGES)
    assert event.reserved_tokens == event.estimated_input_tokens + 20
    assert event.total_tokens == 5
    assert state.metrics.snapshot()["requests_total"] == 2
    assert store.budget_usage[(record.key_id, event.request_id)][0] == 5


def test_budget_rejects_missing_cap_multimodal_and_daily_overage() -> None:
    state, store, stub, secret = _state()
    record = next(iter(store.records.values()))
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=50))

    with TestClient(create_app(state=state)) as client:
        no_cap = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {secret}"},
        )
        multimodal = client.post(
            "/v1/chat/completions",
            json={
                "model": "primary",
                "messages": [{"role": "user", "content": [{"type": "image_url"}]}],
                "max_tokens": 5,
            },
            headers={"Authorization": f"Bearer {secret}"},
        )
        over = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "max_tokens": 5},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert no_cap.status_code == 400
    assert no_cap.json()["error"]["type"] == "budget_output_cap_required"
    assert multimodal.status_code == 400
    assert multimodal.json()["error"]["type"] == "budget_request_unsupported"
    assert over.status_code == 429
    assert over.json()["error"]["type"] == "budget_exceeded"
    assert stub.calls == []


def test_monetary_budget_requires_explicit_pricing_and_records_actual(monkeypatch) -> None:
    state, store, stub, secret = _state()
    record = next(iter(store.records.values()))
    store.set_budget(record.key_id, ApiKeyBudget(daily_cost_usd=Decimal("0.001")))
    with TestClient(create_app(state=state)) as client:
        unknown = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "max_tokens": 10},
            headers={"Authorization": f"Bearer {secret}"},
        )
    assert unknown.status_code == 503
    assert unknown.json()["error"]["type"] == "budget_pricing_unavailable"
    assert stub.calls == []

    deployment = state.registry.get("primary")
    state.registry._deployments["primary"] = replace(
        deployment,
        input_cost_per_million_tokens=Decimal("1"),
        output_cost_per_million_tokens=Decimal("2"),
    )
    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "max_tokens": 10},
            headers={"Authorization": f"Bearer {secret}"},
        )
    event = list(store.usage_events.values())[-1]
    assert response.status_code == 200
    assert event.estimated_cost_usd is not None
    assert event.actual_cost_usd == Decimal("0.000007")


def test_budgeted_fallback_stops_when_failed_attempt_usage_is_unknown() -> None:
    state, store, stub, secret = _state(failures={"primary": 1})
    record = next(iter(store.records.values()))
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES, "max_tokens": 20},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 502
    assert stub.calls == ["primary"]
    event = next(iter(store.usage_events.values()))
    assert event.total_tokens is None
    assert event.reserved_tokens == event.estimated_input_tokens + 20
    assert store.budget_usage[(record.key_id, event.request_id)][0] == event.reserved_tokens


def test_budget_reservation_store_failure_fails_before_provider_execution() -> None:
    state, store, stub, secret = _state()
    record = next(iter(store.records.values()))
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    def unavailable(*args, **kwargs):
        raise ConnectionError("database unavailable")

    store.reserve_budget = unavailable
    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "max_tokens": 10},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "budget_store_unavailable"
    assert stub.calls == []


def test_missing_actual_usage_keeps_estimate_and_does_not_fabricate(monkeypatch) -> None:
    state, store, stub, secret = _state()
    record = next(iter(store.records.values()))
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    async def no_usage(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        return {"id": "completion", "choices": []}

    stub.chat_completion = no_usage
    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "max_tokens": 10},
            headers={"Authorization": f"Bearer {secret}"},
        )

    event = next(iter(store.usage_events.values()))
    assert response.status_code == 200
    assert event.total_tokens is None
    assert event.prompt_tokens is None
    assert event.completion_tokens is None
    assert store.budget_usage[(record.key_id, event.request_id)][0] == event.reserved_tokens


def test_admin_budget_lifecycle_is_protected_and_inspectable(monkeypatch) -> None:
    state, store, _, _ = _state()
    record = next(iter(store.records.values()))
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "budget-admin-secret")
    headers = {"Authorization": "Bearer budget-admin-secret"}
    with TestClient(create_app(state=state)) as client:
        denied = client.get(f"/admin/api-keys/{record.key_id}/budget")
        created = client.put(
            f"/admin/api-keys/{record.key_id}/budget",
            headers=headers,
            json={"daily_tokens": 1000, "monthly_cost_usd": "2.50"},
        )
        inspected = client.get(f"/admin/api-keys/{record.key_id}/budget", headers=headers)
        removed = client.delete(f"/admin/api-keys/{record.key_id}/budget", headers=headers)

    assert denied.status_code == 401
    assert created.status_code == 200
    assert inspected.json()["budget"]["daily_tokens"] == 1000
    assert inspected.json()["budget"]["monthly_cost_usd"] == "2.50"
    assert removed.status_code == 200
    assert store.get_budget(record.key_id) is None
