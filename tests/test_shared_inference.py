"""R-02: emergency shared-inference kill-switch.

Proves fail-closed admission (before any provider dispatch), per-attempt
re-checks that fallback cannot bypass, admin-only mutation with safe
status, and read-through semantics (no cached enabled state). Providers
are stubbed; no live inference. SQLite covers SQL paths; PostgreSQL runs
only under SABIROUTE_TEST_PG_URL (see the opt-in test at the end).
"""

from __future__ import annotations

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from sabiroute.freepool.eligibility import (
    SHARED_INFERENCE_DISABLED,
    FreePoolPolicy,
    shared_inference_denial,
)
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.store import PostgresApiKeyStore

MESSAGES = [{"role": "user", "content": "hello"}]
ADMIN_KEY = "test-admin-secret-for-shared-inference"

ENABLED_POLICY = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))


def make_client(stub, *, policy=ENABLED_POLICY, monkeypatch=None):
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore(), free_pool=policy
    )
    key = provision_test_key(state)
    if monkeypatch is not None:
        monkeypatch.setenv("SABIROUTE_ADMIN_KEY", ADMIN_KEY)
    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {key}"})
    return client, state


def free_body(model="primary"):
    return {"model": model, "messages": MESSAGES, "sabi_route_free_chat": True}


def admin_headers():
    return {"Authorization": f"Bearer {ADMIN_KEY}"}


def single_usage_event(state):
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    events = list(store.usage_events.values())
    assert len(events) == 1
    return events[0]


# --- admission and safety -------------------------------------------------


def test_absent_control_record_denies_before_dispatch():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)

    response = client.post("/v1/chat/completions", json=free_body())

    assert response.status_code == 403
    assert response.json()["error"]["type"] == SHARED_INFERENCE_DISABLED
    assert stub.calls == []

    event = single_usage_event(state)
    assert event.final_status == 403
    assert event.failure_category == SHARED_INFERENCE_DISABLED
    assert event.usage_source == "unknown"


def test_explicit_disable_denies_before_dispatch():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.shared_inference = False

    response = client.post("/v1/chat/completions", json=free_body())

    assert response.status_code == 403
    assert response.json()["error"]["type"] == SHARED_INFERENCE_DISABLED
    assert stub.calls == []


def test_enabled_permits_otherwise_eligible_request():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.shared_inference = True

    response = client.post("/v1/chat/completions", json=free_body())

    assert response.status_code == 200
    assert stub.calls == ["primary"]

    event = single_usage_event(state)
    assert event.usage_source == "free_pool"


def test_control_read_failure_denies():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_policy_reads = True

    response = client.post("/v1/chat/completions", json=free_body())

    assert response.status_code == 403
    assert response.json()["error"]["type"] == SHARED_INFERENCE_DISABLED
    assert stub.calls == []


def test_missing_store_never_enables_shared_inference(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    stub = StubLiteLLMClient()
    state = build_gateway_state(
        config=make_config(), client=stub, free_pool=ENABLED_POLICY
    )
    assert state.key_store is None
    key_client = TestClient(create_app(state=state))

    # No client key can authenticate without a store (the auth dependency
    # fails 503 before any gate runs); the denial helper itself fail-closes.
    import asyncio

    assert asyncio.run(shared_inference_denial(state, None)) == SHARED_INFERENCE_DISABLED
    assert key_client.post("/v1/chat/completions", json=free_body()).status_code == 503
    assert stub.calls == []


def test_unmarked_traffic_unaffected_by_switch():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.shared_inference = False

    response = client.post("/v1/chat/completions", json={"model": "primary", "messages": MESSAGES})

    assert response.status_code == 200
    assert stub.calls == ["primary"]


def test_policy_off_still_denies_with_policy_reason():
    stub = StubLiteLLMClient()
    client, state = make_client(stub, policy=FreePoolPolicy())
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.shared_inference = True

    response = client.post("/v1/chat/completions", json=free_body())

    # The kill-switch cannot grant what the rollout policy forbids.
    assert response.status_code == 503
    assert response.json()["error"]["type"] == "free_pool_unavailable"
    assert stub.calls == []


def test_midflight_disable_stops_fallback(monkeypatch):
    stub = StubLiteLLMClient(failures={"primary": 1})
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary", "secondary"}))
    client, state = make_client(stub, policy=policy)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.shared_inference = True

    original_choose = state.router.choose_deployment

    def flipping_choose(*args, **kwargs):
        decision = original_choose(*args, **kwargs)
        store.shared_inference = False
        return decision

    monkeypatch.setattr(state.router, "choose_deployment", flipping_choose)
    response = client.post("/v1/chat/completions", json={**free_body(), "model": "fast"})

    assert response.status_code == 403
    assert response.json()["error"]["type"] == SHARED_INFERENCE_DISABLED
    assert stub.calls == ["primary"]

    event = single_usage_event(state)
    assert event.failure_category == SHARED_INFERENCE_DISABLED


def test_null_policy_value_denies_on_sqlite(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'null-policy.sqlite'}"
    store = PostgresApiKeyStore(database_url)
    try:
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO sabiroute_shared_inference_policy"
                    " (id, enabled, updated_at, updated_by)"
                    " VALUES ('shared', NULL, CURRENT_TIMESTAMP, 'admin')"
                )
            )
        engine.dispose()
        assert store.get_shared_inference() is None
    finally:
        store.close()


# --- helper unit contract -------------------------------------------------


class _FakeExecutorState:
    def __init__(self, value=None, fail=False):
        self._value = value
        self._fail = fail
        self.store_executor = self

    async def run(self, func, *args, **kwargs):
        if self._fail:
            raise RuntimeError("unavailable")
        return self._value


class _StubStore:
    """Shape-only store: the fake executor never calls the method, but the
    helper resolves the bound method before dispatch, so it must exist."""

    def get_shared_inference(self):  # pragma: no cover - dispatch shape only
        raise AssertionError("fake executor must not call the store")


def test_denial_helper_reads_through():
    import asyncio

    store = _StubStore()
    assert asyncio.run(shared_inference_denial(_FakeExecutorState(True), store)) is None
    assert (
        asyncio.run(shared_inference_denial(_FakeExecutorState(False), store))
        == SHARED_INFERENCE_DISABLED
    )
    assert (
        asyncio.run(shared_inference_denial(_FakeExecutorState(None), store))
        == SHARED_INFERENCE_DISABLED
    )
    assert (
        asyncio.run(shared_inference_denial(_FakeExecutorState("yes"), store))
        == SHARED_INFERENCE_DISABLED
    )
    assert (
        asyncio.run(shared_inference_denial(_FakeExecutorState(fail=True), store))
        == SHARED_INFERENCE_DISABLED
    )


# --- administrative controls ----------------------------------------------


def test_admin_disable_enable_status_round_trip(monkeypatch):
    stub = StubLiteLLMClient()
    client, state = make_client(stub, monkeypatch=monkeypatch)

    initial = client.get("/admin/shared-inference", headers=admin_headers()).json()
    assert initial == {
        "enabled": False,
        "configured": False,
        "updated_at": None,
        "updated_by": None,
    }

    disabled = client.put(
        "/admin/shared-inference",
        json={"enabled": False, "reason": "incident drill"},
        headers=admin_headers(),
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False
    assert disabled.json()["updated_by"] == "admin"

    denied = client.post("/v1/chat/completions", json=free_body())
    assert denied.status_code == 403

    enabled = client.put(
        "/admin/shared-inference", json={"enabled": True}, headers=admin_headers()
    )
    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True

    allowed = client.post("/v1/chat/completions", json=free_body())
    assert allowed.status_code == 200
    assert stub.calls == ["primary"]


def test_admin_mutation_requires_authentication(monkeypatch):
    # Admin auth must be available first: without SABIROUTE_ADMIN_KEY the
    # boundary fail-closes with 503, which would mask the 401 contract.
    stub = StubLiteLLMClient()
    client, _ = make_client(stub, monkeypatch=monkeypatch)

    assert client.put("/admin/shared-inference", json={"enabled": True}).status_code == 401
    assert client.get("/admin/shared-inference").status_code == 401
    assert (
        client.put(
            "/admin/shared-inference",
            json={"enabled": True},
            headers={"Authorization": "Bearer wrong"},
        ).status_code
        == 401
    )


def test_client_credential_rejected_on_admin_boundary(monkeypatch):
    # A valid client key must not satisfy the admin boundary: the secrets
    # are independent and compared independently.
    stub = StubLiteLLMClient()
    client, state = make_client(stub, monkeypatch=monkeypatch)
    client_key = provision_test_key(state)
    client_headers = {"Authorization": f"Bearer {client_key}"}

    assert (
        client.put(
            "/admin/shared-inference", json={"enabled": True}, headers=client_headers
        ).status_code
        == 401
    )
    assert client.get("/admin/shared-inference", headers=client_headers).status_code == 401


def test_audit_log_records_action_without_sensitive_values(monkeypatch, caplog):
    import logging

    stub = StubLiteLLMClient()
    client, _ = make_client(stub, monkeypatch=monkeypatch)

    with caplog.at_level(logging.INFO, logger="sabiroute.api.shutdown"):
        response = client.put(
            "/admin/shared-inference",
            json={"enabled": False, "reason": "incident drill number nine"},
            headers=admin_headers(),
        )
    assert response.status_code == 200
    records = [r for r in caplog.records if r.name == "sabiroute.api.shutdown"]
    assert len(records) == 1
    rendered = records[0].getMessage()
    assert "disabled" in rendered and "admin" in rendered
    assert "incident drill number nine" not in rendered
    assert "sr_live_" not in rendered


def test_concurrent_identical_writes_converge(tmp_path):
    import asyncio

    database_url = f"sqlite:///{tmp_path / 'concurrent.sqlite'}"
    store = PostgresApiKeyStore(database_url)
    try:

        async def one(value: bool) -> None:
            await asyncio.to_thread(store.set_shared_inference, value, "admin")

        asyncio.run(_gather_writes(one))
        assert store.get_shared_inference() is True
        status = store.shared_inference_status()
        assert status["enabled"] is True and status["updated_by"] == "admin"
    finally:
        store.close()


async def _gather_writes(one):
    import asyncio

    await asyncio.gather(*[one(True) for _ in range(10)])


def test_admin_mutation_without_store_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", ADMIN_KEY)
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), free_pool=ENABLED_POLICY
    )
    client = TestClient(create_app(state=state))

    response = client.put(
        "/admin/shared-inference", json={"enabled": True}, headers=admin_headers()
    )
    assert response.status_code == 503
    assert response.json()["detail"]["error"]["type"] == "shared_inference_unavailable"


def test_repeated_operations_are_idempotent(monkeypatch):
    stub = StubLiteLLMClient()
    client, _ = make_client(stub, monkeypatch=monkeypatch)

    for _ in range(2):
        response = client.put(
            "/admin/shared-inference", json={"enabled": True}, headers=admin_headers()
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is True


def test_status_and_errors_carry_no_secrets(monkeypatch):
    stub = StubLiteLLMClient()
    client, _ = make_client(stub, monkeypatch=monkeypatch)

    status = client.get("/admin/shared-inference", headers=admin_headers())
    assert set(status.json()) == {"enabled", "configured", "updated_at", "updated_by"}
    for response in (status,):
        lowered = response.text.lower()
        for needle in ("api_key", "bearer", "token", "password", "secret", "credential"):
            assert needle not in lowered, needle


def test_invalid_admin_body_rejected(monkeypatch):
    stub = StubLiteLLMClient()
    client, _ = make_client(stub, monkeypatch=monkeypatch)

    assert (
        client.put(
            "/admin/shared-inference", json={"enabled": "yes"}, headers=admin_headers()
        ).status_code
        == 422
    )
    assert (
        client.put("/admin/shared-inference", json={}, headers=admin_headers()).status_code
        == 422
    )


def test_no_cached_enabled_state_across_flip(monkeypatch):
    stub = StubLiteLLMClient()
    client, state = make_client(stub, monkeypatch=monkeypatch)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)

    client.put("/admin/shared-inference", json={"enabled": True}, headers=admin_headers())
    assert client.post("/v1/chat/completions", json=free_body()).status_code == 200
    client.put("/admin/shared-inference", json={"enabled": False}, headers=admin_headers())
    denied = client.post("/v1/chat/completions", json=free_body())
    assert denied.status_code == 403
    assert stub.calls == ["primary"]


# --- opt-in PostgreSQL -----------------------------------------------------

PG_URL_ENV = "SABIROUTE_TEST_PG_URL"


def _pg_url():
    import os

    return os.environ.get(PG_URL_ENV)


def test_pg_policy_round_trip_and_null_fail_closed():

    url = _pg_url()
    if not url:
        pytest.skip(f"{PG_URL_ENV} is not set; PostgreSQL integration tests skipped")
    # Opt-in disposable database only: this test writes and NULLs the single
    # policy row. Never point SABIROUTE_TEST_PG_URL at a real database.
    store = PostgresApiKeyStore(url)
    try:
        assert store.get_shared_inference() is None
        store.set_shared_inference(True, "admin")
        assert store.get_shared_inference() is True
        status = store.shared_inference_status()
        assert status["enabled"] is True and status["updated_by"] == "admin"
        engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE sabiroute_shared_inference_policy SET enabled = NULL")
            )
        engine.dispose()
        assert store.get_shared_inference() is None
    finally:
        store.close()
