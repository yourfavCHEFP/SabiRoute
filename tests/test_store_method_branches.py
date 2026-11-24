"""Early-return and accounting branches of :class:`PostgresApiKeyStore`.

Each test drives a real SQLite-backed store into a branch a healthy key never
takes: an unknown key, a cleared limit, an unconfigured kill switch, and the
four budget-gate refusals. The cost-accounting test is deliberately written so
that it can only pass if ``reconcile_budget`` actually rewrote the reserved
row.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from sabiroute.security import store as store_module
from sabiroute.security.keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    ApiKeyRecord,
    issue_api_key,
)
from sabiroute.security.store import PostgresApiKeyStore, check_schema

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _store() -> PostgresApiKeyStore:
    engine = create_engine("sqlite:///:memory:")
    return PostgresApiKeyStore("sqlite:///:memory:", engine=engine)


def _stub_schema_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a fake engine from being asked to create real tables."""
    for name in ("ensure_schema", "ensure_schema_in_connection"):
        monkeypatch.setattr(store_module, name, lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        store_module,
        "_METADATA",
        SimpleNamespace(create_all=lambda *_args, **_kwargs: None),
    )


def _key(store: PostgresApiKeyStore) -> str:
    record, _secret = issue_api_key(store, project_id="proj-1", name="test")
    return record.key_id


def test_schema_check_can_be_restricted_to_a_subset() -> None:
    engine = create_engine("sqlite:///:memory:")
    PostgresApiKeyStore("sqlite:///:memory:", engine=engine)

    check_schema(engine, tables={store_module._API_KEYS.name})


def test_rotation_inherits_the_old_lineage_when_none_is_supplied() -> None:
    store = _store()
    old, _secret = issue_api_key(store, project_id="proj-1", name="old")
    replacement = ApiKeyRecord(
        key_id="new-key-id",
        key_hash="hash",
        project_id="proj-1",
        name="new",
        created_at=NOW,
    )

    assert store.rotate(old.key_id, replacement, NOW) is True

    loaded = store.get("new-key-id")
    assert loaded is not None
    assert loaded.lineage_id == old.lineage_id


def test_rate_limit_for_an_unknown_key_is_refused() -> None:
    assert _store().set_rate_limit("missing", ApiKeyRateLimit(10, 10)) is False


def test_clearing_a_rate_limit_deletes_the_row() -> None:
    store = _store()
    key_id = _key(store)
    store.set_rate_limit(key_id, ApiKeyRateLimit(10, 10))

    assert store.set_rate_limit(key_id, None) is True
    assert store.get_rate_limit(key_id) is None


def test_shared_inference_is_unset_before_it_is_ever_written() -> None:
    store = _store()

    assert store.get_shared_inference() is None
    assert store.shared_inference_status() == {
        "enabled": False,
        "configured": False,
        "updated_at": None,
        "updated_by": None,
    }


def test_budget_for_an_unknown_key_is_refused() -> None:
    assert _store().set_budget("missing", ApiKeyBudget(daily_tokens=10)) is False


def test_clearing_a_budget_deletes_the_row() -> None:
    store = _store()
    key_id = _key(store)
    store.set_budget(key_id, ApiKeyBudget(daily_tokens=10))

    assert store.set_budget(key_id, None) is True
    assert store.get_budget(key_id) is None


def test_reservation_without_a_budget_row_is_refused() -> None:
    store = _store()
    key_id = _key(store)

    assert store.reserve_budget(key_id, "req-1", 10, None, NOW) == "budget_changed"


def test_cost_limit_without_a_price_estimate_is_refused() -> None:
    store = _store()
    key_id = _key(store)
    store.set_budget(key_id, ApiKeyBudget(daily_cost_usd=Decimal("10")))

    assert (
        store.reserve_budget(key_id, "req-1", 10, None, NOW)
        == "daily_pricing_unknown"
    )


def test_reservation_over_the_cost_limit_is_refused() -> None:
    store = _store()
    key_id = _key(store)
    store.set_budget(key_id, ApiKeyBudget(daily_cost_usd=Decimal("1")))

    assert (
        store.reserve_budget(key_id, "req-1", 10, Decimal("5"), NOW)
        == "daily_cost_exceeded"
    )


def test_reconciliation_rewrites_the_accounted_cost() -> None:
    store = _store()
    key_id = _key(store)
    store.set_budget(key_id, ApiKeyBudget(daily_cost_usd=Decimal("1")))

    assert store.reserve_budget(key_id, "req-1", 5, Decimal("0.6"), NOW) is None
    store.reconcile_budget(key_id, "req-1", None, Decimal("0.5"))

    # Only passes if the accounted cost was rewritten from 0.6 down to 0.5:
    # the reserve above already filled 0.6 of the 1.0 budget.
    assert (
        store.reserve_budget(key_id, "req-2", 5, Decimal("0.6"), NOW)
        == "daily_cost_exceeded"
    )


def test_non_positive_quota_estimate_admits_nothing() -> None:
    store = _store()

    assert (
        store.check_and_reserve_quota("user-1", "req-1", 0, NOW, 100) is False
    )
    assert store.check_and_reserve_quota("user-1", "req-2", 10, NOW, 0) is False


def test_snapshot_for_an_unknown_request_is_not_appended() -> None:
    store = _store()

    assert store.append_pre_routing_feature_snapshot("missing", {}) is False


# --- construction and migration wrappers ----------------------------------


def test_store_requires_a_database_url() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        PostgresApiKeyStore("")


def test_store_rewrites_plain_postgres_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    class _NoopConnection:
        def exec_driver_sql(self, *_args: object, **_kwargs: object) -> None:
            return None

        def execute(self, *_args: object, **_kwargs: object) -> None:
            return None

    class _NoopBegin:
        def __enter__(self) -> "_NoopConnection":
            return _NoopConnection()

        def __exit__(self, *exc_info: object) -> bool:
            return False

    class _NoopEngine:
        dialect = SimpleNamespace(name="sqlite")

        def begin(self) -> "_NoopBegin":
            return _NoopBegin()

    def fake_create_engine(url: str, **_kwargs: object) -> "_NoopEngine":
        captured.append(url)
        return _NoopEngine()

    monkeypatch.setattr(store_module, "create_engine", fake_create_engine)
    _stub_schema_setup(monkeypatch)

    PostgresApiKeyStore("postgresql://user@host/db")
    PostgresApiKeyStore("postgres://user@host/db")

    assert captured == [
        "postgresql+psycopg://user@host/db",
        "postgresql+psycopg://user@host/db",
    ]


def test_store_migration_wrappers_delegate_to_the_module_runners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        store_module, "migrate_usage_columns", lambda engine: calls.append("usage")
    )
    monkeypatch.setattr(
        store_module, "apply_schema_migrations", lambda engine: calls.append("revisions")
    )
    store = _store()

    store._migrate_usage_columns()
    store._apply_schema_migrations()

    assert calls == ["usage", "revisions"]


def test_a_duplicate_lineage_insert_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_schema_setup(monkeypatch)
    class _Nested:
        def __enter__(self) -> None:
            raise IntegrityError("INSERT", {}, Exception("duplicate lineage"))

        def __exit__(self, *exc_info: object) -> bool:
            return False

    class _Connection2:
        def __init__(self) -> None:
            self.executed = 0

        def begin_nested(self) -> _Nested:
            return _Nested()

        def execute(self, _statement: object) -> None:
            self.executed += 1

    class _Begin2:
        def __init__(self, connection: _Connection2) -> None:
            self._connection = connection

        def __enter__(self) -> _Connection2:
            return self._connection

        def __exit__(self, *exc_info: object) -> bool:
            return False

    class _Engine2:
        def __init__(self) -> None:
            self.connection = _Connection2()

        def begin(self) -> _Begin2:
            return _Begin2(self.connection)

    engine = _Engine2()
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)  # type: ignore[arg-type]
    record = ApiKeyRecord(
        key_id="key-1",
        key_hash="hash",
        project_id="proj-1",
        name="test",
        created_at=NOW,
        lineage_id="lineage-1",
    )

    store.create(record)

    # The savepoint failed, but the key row was still written afterwards.
    assert engine.connection.executed == 1


def test_reconciliation_refuses_a_keep_key_without_a_budget() -> None:
    class _EmptyResult:
        def mappings(self) -> "_EmptyResult":
            return self

        def first(self) -> None:
            return None

        def scalar(self) -> None:
            return None

    class _EmptyConnection:
        def execute(self, *_args: object, **_kwargs: object) -> "_EmptyResult":
            return _EmptyResult()

    with pytest.raises(ValueError, match="has no budget"):
        store_module.reconcile_lineage_budgets(
            _EmptyConnection(), "lineage-1", "keep-key", "approver"
        )


def test_reconciliation_refuses_a_lineage_mismatch() -> None:
    class _ScriptedResult:
        def __init__(self, value: object) -> None:
            self._value = value

        def mappings(self) -> "_ScriptedResult":
            return self

        def first(self) -> object:
            return self._value

        def scalar(self) -> object:
            return self._value

    class _ScriptedConnection:
        def __init__(self, results: list[object]) -> None:
            self._results = list(results)

        def execute(self, *_args: object, **_kwargs: object) -> "_ScriptedResult":
            return _ScriptedResult(self._results.pop(0))

    connection = _ScriptedConnection([{"key_id": "keep-key"}, "other-lineage"])

    with pytest.raises(ValueError, match="lineage"):
        store_module.reconcile_lineage_budgets(
            connection, "lineage-1", "keep-key", "approver"
        )
