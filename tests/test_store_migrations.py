"""Migration and URL-convention coverage for :mod:`sabiroute.security.store`.

These are paths a normal request never takes: engine URL rewriting before the
driver sees it, the additive column migrations that run against both dialects,
and the two public wrappers that must acquire the PostgreSQL advisory lock
before touching a schema.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
import sqlalchemy

from sabiroute.security import store as store_module
from sabiroute.security.store import (
    _acquire_migration_lock,
    _assert_no_product_tables,
    _connect,
    _group_tables,
    _lineage_for_key,
    _migrate_lineage_columns,
    _migrate_usage_columns,
    apply_schema_migrations,
    migrate_usage_columns,
)


class _Connection:
    def __init__(self, dialect: str = "postgresql") -> None:
        self.dialect = SimpleNamespace(name=dialect)
        self.driver_sql: list[str] = []
        self.executed: list[tuple[str, Any]] = []

    def exec_driver_sql(self, statement: str) -> None:
        self.driver_sql.append(statement)

    def execute(self, statement: Any, params: Any = None) -> Any:
        self.executed.append((str(statement), params))
        return SimpleNamespace(first=lambda: None)


class _Beginning:
    def __init__(self, connection: _Connection) -> None:
        self._connection = connection

    def __enter__(self) -> _Connection:
        return self._connection

    def __exit__(self, *exc_info: object) -> bool:
        return False


class _Engine:
    def __init__(self, dialect: str = "postgresql") -> None:
        self.dialect = SimpleNamespace(name=dialect)
        self.connection = _Connection(dialect)

    def begin(self) -> _Beginning:
        return _Beginning(self.connection)


def _fake_inspect(columns: list[dict[str, str]], tables: set[str]) -> Any:
    def inspect_(_connection: Any) -> Any:
        return SimpleNamespace(
            get_columns=lambda name: list(columns),
            get_table_names=lambda: set(tables),
        )

    return inspect_


def test_connect_rewrites_plain_postgres_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    def fake_create_engine(url: str, **_kwargs: Any) -> object:
        captured.append(url)
        return object()

    monkeypatch.setattr(store_module, "create_engine", fake_create_engine)

    _connect("postgresql://user@host/db", None)
    _connect("postgres://user@host/db", None)

    assert captured == [
        "postgresql+psycopg://user@host/db",
        "postgresql+psycopg://user@host/db",
    ]


def test_migrate_lineage_columns_adds_the_column_on_postgres(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sqlalchemy, "inspect", _fake_inspect([], set()))
    connection = _Connection("postgresql")

    _migrate_lineage_columns(connection, _Engine("postgresql"))

    assert len(connection.driver_sql) == 2
    assert all("ADD COLUMN IF NOT EXISTS" in sql for sql in connection.driver_sql)
    assert all("lineage_id VARCHAR(36)" in sql for sql in connection.driver_sql)


def test_migrate_usage_columns_adds_missing_columns_on_postgres(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sqlalchemy, "inspect", _fake_inspect([], set()))
    connection = _Connection("postgresql")

    _migrate_usage_columns(connection, _Engine("postgresql"))

    assert connection.driver_sql
    assert all("ADD COLUMN IF NOT EXISTS" in sql for sql in connection.driver_sql)


def test_migrate_usage_columns_wrapper_locks_before_migrating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        store_module, "_acquire_migration_lock", lambda c, e: calls.append("lock")
    )
    monkeypatch.setattr(
        store_module, "_migrate_usage_columns", lambda c, e: calls.append("usage")
    )
    monkeypatch.setattr(
        store_module, "_migrate_lineage_columns", lambda c, e: calls.append("lineage")
    )

    migrate_usage_columns(_Engine())

    assert calls == ["lock", "usage", "lineage"]


def test_apply_schema_migrations_locks_before_recording(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        store_module, "_acquire_migration_lock", lambda c, e: calls.append("lock")
    )
    monkeypatch.setattr(
        store_module, "_apply_schema_migrations", lambda c: calls.append("revisions")
    )

    apply_schema_migrations(_Engine())

    assert calls == ["lock", "revisions"]


def test_unknown_schema_group_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown schema group"):
        _group_tables("nope")


def test_core_database_rejects_sabichat_product_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sqlalchemy, "inspect", _fake_inspect([], {"chat_sessions"}))
    monkeypatch.setattr(
        store_module, "sabichat_product_table_names", lambda: {"chat_sessions"}
    )

    with pytest.raises(ValueError, match="Unexpected SabiChat product tables"):
        _assert_no_product_tables(_Connection())


def test_lineage_lookup_swallows_connection_failures() -> None:
    class _BrokenConnection:
        dialect = SimpleNamespace(name="postgresql")

        def execute(self, *_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("connection lost")

    assert _lineage_for_key(_BrokenConnection(), "key-1") is None


def test_migration_lock_falls_back_to_the_connection_dialect() -> None:
    connection = _Connection("postgresql")
    engine = SimpleNamespace(dialect=SimpleNamespace(name=None))

    _acquire_migration_lock(connection, engine)

    assert len(connection.executed) == 2
    assert "lock_timeout" in connection.executed[0][0]
    assert "pg_advisory_xact_lock" in connection.executed[1][0]
    assert connection.executed[1][1] is not None
