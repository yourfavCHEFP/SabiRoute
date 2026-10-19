"""Phase 2: per-user daily token quotas for pilot shared inference.

Proves atomic admission, idempotent settlement, conservative unknown-usage
handling, pilot isolation, and unchanged behavior for everyone else.
Providers stubbed; SQLite covers logic, disposable PostgreSQL covers real
row locking (opt-in, skipped without SABIROUTE_TEST_PG_URL).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    enable_shared_inference,
    make_config,
    provision_test_key,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.quotas import (
    DAILY_TOKEN_QUOTA,
    QUOTA_EXCEEDED,
    QUOTA_MAX_TOKENS_REQUIRED,
    QUOTA_UNAVAILABLE,
    QuotaPolicy,
    quota_reset_at,
    quota_window_start,
)
from sabiroute.security.keys import SABI_USER_ID_FIELD, issue_api_key
from sabiroute.security.store import PostgresApiKeyStore

MESSAGES = [{"role": "user", "content": "hello"}]
UID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OTHER_UID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

PG_URL_ENV = "SABIROUTE_TEST_PG_URL"


def make_quota_client(stub, *, eligible=("primary",), pilot=(UID,)):
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset(eligible))
    quota = QuotaPolicy(pilot_users=frozenset(pilot))
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=store,
        free_pool=policy,
        quota_policy=quota,
    )
    record, plaintext = issue_api_key(
        store, project_id="sabichat-service", name="sabichat-service"
    )
    state.sabichat_service_key_id = record.key_id
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    return (
        TestClient(app, headers={"Authorization": f"Bearer {key}"}),
        TestClient(app, headers={"Authorization": f"Bearer {plaintext}"}),
        state,
        app,
    )


def marked(model="primary", max_tokens=500, **extra):
    return {
        "model": model,
        "messages": MESSAGES,
        "sabi_route_free_chat": True,
        "max_tokens": max_tokens,
        SABI_USER_ID_FIELD: UID,
        **extra,
    }


def quota_events(state):
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    return store.quota_reservations


# --- policy units -----------------------------------------------------------


def test_daily_quota_is_owner_approved_value():
    assert DAILY_TOKEN_QUOTA == 50_000


def test_window_boundaries_utc():
    assert quota_window_start(datetime(2026, 3, 14, 23, 59, 59, tzinfo=UTC)) == datetime(
        2026, 3, 14, tzinfo=UTC
    )
    assert quota_window_start(datetime(2026, 3, 15, 0, 0, 0, tzinfo=UTC)) == datetime(
        2026, 3, 15, tzinfo=UTC
    )
    assert quota_window_start(datetime(2026, 12, 31, 12, 0, 0, tzinfo=UTC)) == datetime(
        2026, 12, 31, tzinfo=UTC
    )
    assert quota_reset_at(datetime(2026, 3, 14, tzinfo=UTC)) == datetime(
        2026, 3, 15, tzinfo=UTC
    )


def test_policy_defaults_to_nobody(monkeypatch):
    monkeypatch.delenv("SABIROUTE_QUOTA_PILOT_USERS", raising=False)
    policy = QuotaPolicy.from_env()
    assert policy.pilot_users == frozenset()
    assert policy.daily_tokens == DAILY_TOKEN_QUOTA
    assert policy.covers(UID) is False
    assert policy.covers(None) is False
    assert policy.covers("") is False


def test_policy_parses_pilot_cohort(monkeypatch):
    monkeypatch.setenv("SABIROUTE_QUOTA_PILOT_USERS", f" {UID} ,,{OTHER_UID} ")
    policy = QuotaPolicy.from_env()
    assert policy.pilot_users == frozenset({UID, OTHER_UID})
    assert policy.covers(UID) is True


# --- store-level admission ----------------------------------------------------


def test_boundary_exact_fit_then_denied(tmp_path):
    store = PostgresApiKeyStore(f"sqlite:///{tmp_path / 'boundary.sqlite'}")
    try:
        window = quota_window_start(datetime.now(UTC))
        assert store.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
        assert store.check_and_reserve_quota(UID, "r2", 40, window, 100) is True
        assert store.check_and_reserve_quota(UID, "r3", 1, window, 100) is False
        usage = store.get_quota_usage(UID, window)
        assert usage == {"reserved_tokens": 100, "consumed_tokens": 0}
    finally:
        store.close()


def test_duplicate_admission_is_noop_success(tmp_path):
    store = PostgresApiKeyStore(f"sqlite:///{tmp_path / 'dedupe.sqlite'}")
    try:
        window = quota_window_start(datetime.now(UTC))
        assert store.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
        assert store.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
        assert store.get_quota_usage(UID, window)["reserved_tokens"] == 60
    finally:
        store.close()


def test_settle_release_idempotent(tmp_path):
    store = PostgresApiKeyStore(f"sqlite:///{tmp_path / 'settle.sqlite'}")
    try:
        window = quota_window_start(datetime.now(UTC))
        assert store.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
        store.settle_quota(UID, "r1", 40)
        store.settle_quota(UID, "r1", 40)
        assert store.get_quota_usage(UID, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 40,
        }
        store.release_quota(UID, "r1")
        assert store.get_quota_usage(UID, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 40,
        }
        assert store.check_and_reserve_quota(UID, "r2", 10, window, 100) is True
        store.release_quota(UID, "r2")
        store.release_quota(UID, "r2")
        assert store.get_quota_usage(UID, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 40,
        }
        store.settle_quota(UID, "missing", 10)
        assert store.get_quota_usage(UID, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 40,
        }
    finally:
        store.close()


def test_unknown_usage_holds_estimate(tmp_path):
    store = PostgresApiKeyStore(f"sqlite:///{tmp_path / 'hold.sqlite'}")
    try:
        window = quota_window_start(datetime.now(UTC))
        assert store.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
        store.settle_quota(UID, "r1", None)
        assert store.get_quota_usage(UID, window) == {
            "reserved_tokens": 0,
            "consumed_tokens": 60,
        }
    finally:
        store.close()


def test_restart_keeps_held_reservation(tmp_path):
    url = f"sqlite:///{tmp_path / 'restart.sqlite'}"
    window = quota_window_start(datetime.now(UTC))
    first = PostgresApiKeyStore(url)
    try:
        assert first.check_and_reserve_quota(UID, "r1", 60, window, 100) is True
    finally:
        first.close()
    second = PostgresApiKeyStore(url)
    try:
        assert second.applied_revisions()[-1] == "0004-user-quota-ledger"
        assert second.get_quota_usage(UID, window) == {
            "reserved_tokens": 60,
            "consumed_tokens": 0,
        }
        assert second.check_and_reserve_quota(UID, "r2", 41, window, 100) is False
        assert second.check_and_reserve_quota(UID, "r2", 40, window, 100) is True
    finally:
        second.close()


def test_sequential_exact_fit_then_denied(tmp_path):
    # SQLite ignores SELECT ... FOR UPDATE, so true concurrency Proving
    # happens on PostgreSQL below; this test pins the exact-fit arithmetic
    # deterministically on any backend.
    store = PostgresApiKeyStore(f"sqlite:///{tmp_path / 'race.sqlite'}")
    try:
        window = quota_window_start(datetime.now(UTC))
        results = [
            store.check_and_reserve_quota(UID, f"r{index}", 10000, window, 50000)
            for index in range(8)
        ]
        assert results == [True] * 5 + [False] * 3
        usage = store.get_quota_usage(UID, window)
        assert usage == {"reserved_tokens": 50000, "consumed_tokens": 0}
    finally:
        store.close()


# --- request-path admission -----------------------------------------------------


def test_exhaustion_denies_before_dispatch():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)

    response = service.post("/v1/chat/completions", json=marked(max_tokens=60000))

    assert response.status_code == 429
    body = response.json()["error"]
    assert body["type"] == QUOTA_EXCEEDED
    assert "reset_at" in body
    assert stub.calls == []

    event = single_finalized(state)
    assert event.final_status == 429
    assert event.failure_category == QUOTA_EXCEEDED
    assert event.usage_source == "free_pool"


def test_max_tokens_required_for_metered_requests():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)

    body = marked()
    del body["max_tokens"]
    response = service.post("/v1/chat/completions", json=body)

    assert response.status_code == 400
    assert response.json()["error"]["type"] == QUOTA_MAX_TOKENS_REQUIRED
    assert stub.calls == []


def test_pilot_ineligible_proceeds_unmetered():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub, pilot=("someone-else",))

    body = marked()
    body[SABI_USER_ID_FIELD] = UID
    response = service.post("/v1/chat/completions", json=body)

    assert response.status_code == 200
    assert stub.calls == ["primary"]
    assert quota_events(state) == {}


def test_spoofed_identity_consumes_nothing():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)
    ordinary = provision_test_key(state)
    spoof = TestClient(app, headers={"Authorization": f"Bearer {ordinary}"})

    response = spoof.post("/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: UID}))

    assert response.status_code == 200
    assert "X-SabiRoute-User" not in response.headers
    assert quota_events(state) == {}
    event = single_finalized(state)
    assert event.usage_source == "free_pool"


def single_finalized(state):
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    events = list(store.usage_events.values())
    assert len(events) == 1
    return events[0]


def test_quota_store_failure_denies_with_503():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_quota_reads = True

    response = service.post("/v1/chat/completions", json=marked())

    assert response.status_code == 503
    assert response.json()["error"]["type"] == QUOTA_UNAVAILABLE
    assert stub.calls == []


def test_exhaustion_retry_after_matches_reset():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)

    before = datetime.now(UTC)
    response = service.post("/v1/chat/completions", json=marked(max_tokens=60000))

    assert response.status_code == 429
    body = response.json()["error"]
    assert body["type"] == QUOTA_EXCEEDED
    retry_after = response.headers.get("retry-after")
    assert retry_after is not None and retry_after.isdigit()
    seconds = int(retry_after)
    reset_at = datetime.fromisoformat(body["reset_at"])
    window_seconds = (reset_at - before).total_seconds()
    assert 0 <= seconds <= window_seconds
    assert seconds >= window_seconds - 5
    assert stub.calls == []


def test_quota_unavailable_carries_no_retry_after():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_quota_reads = True

    response = service.post("/v1/chat/completions", json=marked())

    assert response.status_code == 503
    assert response.json()["error"]["type"] == QUOTA_UNAVAILABLE
    assert "retry-after" not in response.headers
    assert stub.calls == []


def test_retry_uses_single_allowance():
    stub = StubLiteLLMClient(failures={"primary": 1})
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary", "secondary"}))
    quota = QuotaPolicy(pilot_users=frozenset({UID}))
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=store,
        free_pool=policy,
        quota_policy=quota,
    )
    record, plaintext = issue_api_key(
        store, project_id="sabichat-service", name="sabichat-service"
    )
    state.sabichat_service_key_id = record.key_id
    enable_shared_inference(state)
    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {plaintext}"}
    )

    body = marked(model="fast")
    response = client.post("/v1/chat/completions", json=body)

    assert response.status_code == 200
    assert stub.calls == ["primary", "secondary"]
    assert len(store.quota_reservations) == 1
    event = single_finalized(state)
    assert event.usage_source == "free_pool"


def test_provider_failure_holds_estimate():
    stub = StubLiteLLMClient(failures={"primary": 5})
    client, service, state, app = make_quota_client(stub)

    response = service.post("/v1/chat/completions", json=marked())

    assert response.status_code == 502
    usage = store_quota_usage(state)
    assert usage["reserved_tokens"] == 0
    assert usage["consumed_tokens"] > 0


def store_quota_usage(state):
    from sabiroute.quotas import quota_window_start

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    window = quota_window_start(datetime.now(UTC))
    return store.get_quota_usage(UID, window)


def test_streaming_settles_actuals():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)

    body = marked()
    body["stream"] = True
    response = service.post("/v1/chat/completions", json=body)

    assert response.status_code == 200
    usage = store_quota_usage(state)
    assert usage == {"reserved_tokens": 0, "consumed_tokens": 5}


def test_byok_and_local_traffic_unaffected():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)

    plain = client.post("/v1/chat/completions", json={"model": "primary", "messages": MESSAGES})
    assert plain.status_code == 200
    assert quota_events(state) == {}
    event = single_finalized(state)
    assert event.usage_source == "unknown"


def test_denied_request_source_reflects_gate_decision():
    stub = StubLiteLLMClient()
    client, service, state, app = make_quota_client(stub)

    response = service.post("/v1/chat/completions", json=marked(max_tokens=60000))

    assert response.status_code == 429
    event = single_finalized(state)
    assert event.usage_source == "free_pool"
    assert event.failure_category == QUOTA_EXCEEDED


def test_fresh_database_includes_quota_tables(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'quota-fresh.sqlite'}"
    store = PostgresApiKeyStore(database_url)
    try:
        assert store.applied_revisions()[-1] == "0004-user-quota-ledger"
        window = quota_window_start(datetime.now(UTC))
        assert store.check_and_reserve_quota(UID, "r1", 10, window, 50000) is True
        assert store.get_quota_usage(UID, window) == {
            "reserved_tokens": 10,
            "consumed_tokens": 0,
        }
    finally:
        store.close()


def test_legacy_database_upgrades_with_quota_tables(tmp_path):
    from sqlalchemy import text as sa_text

    database_url = f"sqlite:///{tmp_path / 'quota-legacy.sqlite'}"
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            sa_text(
                "CREATE TABLE sabiroute_api_keys (key_id VARCHAR(24) PRIMARY KEY,"
                " key_hash VARCHAR(64) NOT NULL, project_id VARCHAR(128) NOT NULL,"
                " name VARCHAR(128) NOT NULL, created_at DATETIME NOT NULL,"
                " revoked_at DATETIME, metadata_json JSON NOT NULL)"
            )
        )
        connection.execute(
            sa_text(
                "INSERT INTO sabiroute_api_keys (key_id, key_hash, project_id,"
                " name, created_at, metadata_json) VALUES"
                " ('legacykey00000000000001', 'abc', 'legacy', 'legacy',"
                " '2026-01-02 03:04:05.000000', '{}')"
            )
        )
    engine.dispose()
    store = PostgresApiKeyStore(database_url)
    try:
        assert store.applied_revisions()[-1] == "0004-user-quota-ledger"
        assert store.get("legacykey00000000000001") is not None
        window = quota_window_start(datetime.now(UTC))
        assert store.check_and_reserve_quota(UID, "r1", 10, window, 50000) is True
    finally:
        store.close()


def test_pg_concurrent_last_allowance_single_winner():
    import os
    import threading

    url = os.environ.get(PG_URL_ENV)
    if not url:
        pytest.skip(f"{PG_URL_ENV} is not set; PostgreSQL integration tests skipped")
    store = PostgresApiKeyStore(url)
    try:
        window = quota_window_start(datetime.now(UTC))
        tag = f"pgrace-{os.getpid()}"
        results: list = [None] * 8

        def attempt(index):
            results[index] = store.check_and_reserve_quota(
                tag, f"{tag}-r{index}", 10000, window, 50000
            )

        threads = [threading.Thread(target=attempt, args=(index,)) for index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert sum(1 for admitted in results if admitted) == 5
        assert sum(1 for admitted in results if not admitted) == 3
        usage = store.get_quota_usage(tag, window)
        assert usage["reserved_tokens"] + usage["consumed_tokens"] <= 50000
    finally:
        store.close()


def test_pg_migration_records_0004():
    import os

    url = os.environ.get(PG_URL_ENV)
    if not url:
        pytest.skip(f"{PG_URL_ENV} is not set; PostgreSQL integration tests skipped")
    store = PostgresApiKeyStore(url)
    try:
        assert store.applied_revisions()[-1] == "0004-user-quota-ledger"
    finally:
        store.close()
