"""Sprint 2: versioned migrations and usage-source attribution.

Proves revision 0001-usage-source applies to fresh databases, upgrades a
representative legacy schema without losing rows, re-runs idempotently, keeps
legacy rows "unknown" (never backfilled), and carries the source end to end
from admission through the admin usage output.
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
from sqlalchemy import create_engine, text

from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.keys import (
    RequestUsageEvent,
    UsageEventValidationError,
    issue_api_key,
    validate_usage_event_finalization,
)
from sabiroute.security.store import SCHEMA_MIGRATIONS, PostgresApiKeyStore

MESSAGES = [{"role": "user", "content": "hello"}]

LEGACY_USAGE_DDL = """
CREATE TABLE sabiroute_request_usage (
    request_id VARCHAR(36) NOT NULL PRIMARY KEY,
    key_id VARCHAR(24) NOT NULL,
    project_id VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL,
    requested_alias VARCHAR(256),
    final_deployment VARCHAR(256),
    final_status INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    failure_category VARCHAR(64),
    estimated_input_tokens INTEGER,
    reserved_tokens INTEGER,
    estimated_cost_usd NUMERIC(20, 10),
    actual_cost_usd NUMERIC(20, 10),
    routing_decisions JSON NOT NULL,
    feature_schema_version VARCHAR(16),
    pre_routing_features JSON NOT NULL
)
"""


def test_fresh_database_records_revision_and_round_trips_source(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'fresh.sqlite'}"
    store = PostgresApiKeyStore(database_url)
    try:
        assert store.applied_revisions() == [
            "0001-usage-source",
            "0002-sabichat-backend",
            "0003-shared-inference-switch",
            "0004-user-quota-ledger",
        ]

        record, _ = issue_api_key(store, project_id="src-test", name="src")
        event = RequestUsageEvent(
            request_id="11111111-1111-4111-8111-111111111111",
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="primary",
            usage_source="free_pool",
        )
        store.create_usage_event(event)

        events, total = store.list_usage_events(record.key_id, limit=10, offset=0)
        assert total == 1
        assert events[0].usage_source == "free_pool"
    finally:
        store.close()


def test_legacy_schema_upgrades_without_losing_rows_and_stays_unknown(tmp_path):
    database_path = tmp_path / "legacy.sqlite"
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(LEGACY_USAGE_DDL))
        connection.execute(
            text(
                "INSERT INTO sabiroute_request_usage "
                "(request_id, key_id, project_id, created_at, requested_alias, "
                "final_status, routing_decisions, feature_schema_version, "
                "pre_routing_features) VALUES "
                "('22222222-2222-4222-8222-222222222222', 'legacykey00000000000001', "
                "'legacy-project', '2026-01-02 03:04:05.000000', 'primary', "
                "200, '[]', '1.0', '[]')"
            )
        )
    engine.dispose()

    store = PostgresApiKeyStore(database_url)
    try:
        assert store.applied_revisions() == [
            "0001-usage-source",
            "0002-sabichat-backend",
            "0003-shared-inference-switch",
            "0004-user-quota-ledger",
        ]

        events, total = store.list_usage_events("legacykey00000000000001", limit=10, offset=0)
        assert total == 1
        assert events[0].request_id == "22222222-2222-4222-8222-222222222222"
        assert events[0].requested_alias == "primary"
        assert events[0].final_status == 200
        # Legacy rows are never backfilled: NULL reads as "unknown".
        assert events[0].usage_source == "unknown"
    finally:
        store.close()


def test_migrations_rerun_idempotently(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'rerun.sqlite'}"
    first = PostgresApiKeyStore(database_url)
    first.close()

    second = PostgresApiKeyStore(database_url)
    try:
        assert second.applied_revisions() == [
            "0001-usage-source",
            "0002-sabichat-backend",
            "0003-shared-inference-switch",
            "0004-user-quota-ledger",
        ]
        assert [revision for revision, _ in SCHEMA_MIGRATIONS] == [
            "0001-usage-source",
            "0002-sabichat-backend",
            "0003-shared-inference-switch",
            "0004-user-quota-ledger",
        ]
    finally:
        second.close()


def test_finalize_rejects_unknown_usage_source():
    event = RequestUsageEvent(
        request_id="33333333-3333-4333-8333-333333333333",
        key_id="key00000000000000000001",
        project_id="project-test",
        created_at=datetime.now(UTC),
        requested_alias="primary",
        final_status=200,
        usage_source="free",
    )

    with pytest.raises(UsageEventValidationError, match="usage_source"):
        validate_usage_event_finalization(event)


def test_denied_marked_request_stays_unknown():
    stub = StubLiteLLMClient()
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
    )
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {key}"})

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "secondary",
            "messages": MESSAGES,
            "sabi_route_free_chat": True,
        },
    )

    assert response.status_code == 403
    assert stub.calls == []
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    (event,) = list(store.usage_events.values())
    assert event.failure_category == "free_pool_unmapped_deployment"
    # Denied requests never received Free Pool service: source stays unknown.
    assert event.usage_source == "unknown"


def test_disabled_marked_request_stays_unknown():
    stub = StubLiteLLMClient()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=FreePoolPolicy(),
    )
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {key}"})

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, "sabi_route_free_chat": True},
    )

    assert response.status_code == 503
    assert stub.calls == []
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    (event,) = list(store.usage_events.values())
    assert event.failure_category == "free_pool_unavailable"
    assert event.usage_source == "unknown"


def test_truthy_string_marker_does_not_activate_free_chat():
    stub = StubLiteLLMClient()
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
    )
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {key}"})

    # Only exact JSON true activates; a truthy string is an ordinary request.
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "secondary",
            "messages": MESSAGES,
            "sabi_route_free_chat": "yes",
        },
    )

    assert response.status_code == 200
    assert stub.calls == ["secondary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    (event,) = list(store.usage_events.values())
    assert event.usage_source == "unknown"


def test_marker_like_alias_is_an_unknown_model():
    stub = StubLiteLLMClient()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=FreePoolPolicy(
            enabled=True, eligible_deployments=frozenset({"primary"})
        ),
    )
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {key}"})

    response = client.post(
        "/v1/chat/completions",
        json={"model": "sabi_route_free_chat", "messages": MESSAGES},
    )

    assert response.status_code == 404
    assert stub.calls == []


def test_retry_and_fallback_preserve_free_pool_source():
    stub = StubLiteLLMClient(failures={"primary": 1})
    policy = FreePoolPolicy(
        enabled=True, eligible_deployments=frozenset({"primary", "secondary"})
    )
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
    )
    enable_shared_inference(state)
    key = provision_test_key(state)
    app = create_app(state=state)
    client = TestClient(app, headers={"Authorization": f"Bearer {key}"})

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "sabi_route_free_chat": True},
    )

    assert response.status_code == 200
    assert stub.calls == ["primary", "secondary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    (event,) = list(store.usage_events.values())
    assert event.usage_source == "free_pool"
    assert len(event.routing_decisions) == 2


def test_finalize_updates_source_on_sql_database(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'source-update.sqlite'}"
    store = PostgresApiKeyStore(database_url)
    try:
        record, _ = issue_api_key(store, project_id="src-update", name="src")
        event = RequestUsageEvent(
            request_id="44444444-4444-4444-8444-444444444444",
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="primary",
        )
        store.create_usage_event(event)

        from dataclasses import replace as dc_replace

        finalized = dc_replace(event, final_deployment="primary", final_status=200)
        assert store.finalize_usage_event(finalized) is True
        events, _ = store.list_usage_events(record.key_id, limit=10, offset=0)
        assert events[0].usage_source == "unknown"

        second = RequestUsageEvent(
            request_id="55555555-5555-4555-8555-555555555555",
            key_id=record.key_id,
            project_id=record.project_id,
            created_at=datetime.now(UTC),
            requested_alias="primary",
        )
        store.create_usage_event(second)
        allowed = dc_replace(
            second,
            final_deployment="primary",
            final_status=200,
            usage_source="free_pool",
        )
        assert store.finalize_usage_event(allowed) is True
        events, total = store.list_usage_events(record.key_id, limit=10, offset=0)
        assert total == 2
        by_id = {item.request_id: item.usage_source for item in events}
        assert by_id == {
            "44444444-4444-4444-8444-444444444444": "unknown",
            "55555555-5555-4555-8555-555555555555": "free_pool",
        }
    finally:
        store.close()


def test_failed_migration_surfaces_and_recovers(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration-failure.sqlite'}"

    def _boom(self) -> None:
        raise RuntimeError("simulated migration failure")

    monkeypatch.setattr(PostgresApiKeyStore, "_migrate_usage_columns", _boom)
    with pytest.raises(RuntimeError, match="simulated migration failure"):
        PostgresApiKeyStore(database_url)

    monkeypatch.undo()
    store = PostgresApiKeyStore(database_url)
    try:
        assert store.applied_revisions() == [
            "0001-usage-source",
            "0002-sabichat-backend",
            "0003-shared-inference-switch",
            "0004-user-quota-ledger",
        ]
    finally:
        store.close()


def test_request_path_tags_source_and_admin_reports_it(monkeypatch):
    stub = StubLiteLLMClient()
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
    )
    enable_shared_inference(state)
    client_key = provision_test_key(state)
    admin_key = "test-admin-secret-distinct-from-client-key"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", admin_key)
    app = create_app(state=state)

    with TestClient(app) as client:
        free = client.post(
            "/v1/chat/completions",
            json={
                "model": "primary",
                "messages": MESSAGES,
                "sabi_route_free_chat": True,
            },
            headers={"Authorization": f"Bearer {client_key}"},
        )
        assert free.status_code == 200

        paid_style = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {client_key}"},
        )
        assert paid_style.status_code == 200

        key_id = next(iter(state.key_store.records))
        key_usage = client.get(
            f"/admin/api-keys/{key_id}/usage",
            headers={"Authorization": f"Bearer {admin_key}"},
        ).json()

    # Both requests name the same alias; the source multiset distinguishes them.
    assert len(key_usage["items"]) == 2
    assert sorted(item["usage_source"] for item in key_usage["items"]) == [
        "free_pool",
        "unknown",
    ]
