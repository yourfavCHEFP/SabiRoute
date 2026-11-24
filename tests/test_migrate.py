"""Behavioural tests for :mod:`sabiroute.migrate`.

Two contracts are covered:

* ``_database_url()`` -- environment-variable precedence, and a non-zero
  exit with a stderr diagnostic when no URL is configured.
* ``main()`` -- dialect routing: PostgreSQL takes a transaction-scoped
  advisory lock and migrates inside that transaction, SQLite applies the
  schema directly, every failure path returns 1 with a stderr diagnostic,
  and success prints the applied groups and returns 0.

The module is also the only supported entry point for schema changes, so
the ``__main__`` guard surfacing ``main()``'s return code as the process
exit status is asserted as well.
"""
from __future__ import annotations

import runpy
from typing import Any

import pytest

import sabiroute.migrate as migrate


class _RecordingConnection:
    """Stand-in for a SQLAlchemy connection that records statements."""

    def __init__(self) -> None:
        self.executed: list[tuple[str, Any]] = []

    def execute(self, statement: Any, params: Any = None) -> None:
        self.executed.append((str(statement), params))


class _RecordingTransaction:
    """Context manager recording whether it was entered and exited."""

    def __init__(self, connection: _RecordingConnection) -> None:
        self._connection = connection
        self.entered = False
        self.exited = False

    def __enter__(self) -> _RecordingConnection:
        self.entered = True
        return self._connection

    def __exit__(self, *exc_info: object) -> bool:
        self.exited = True
        return False


class _Dialect:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeEngine:
    def __init__(self, dialect_name: str) -> None:
        self.dialect = _Dialect(dialect_name)
        self.connection = _RecordingConnection()
        self.transaction: _RecordingTransaction | None = None

    def begin(self) -> _RecordingTransaction:
        self.transaction = _RecordingTransaction(self.connection)
        return self.transaction


def _install_engine(
    monkeypatch: pytest.MonkeyPatch, engine: _FakeEngine
) -> list[tuple[str, Any]]:
    """Point ``migrate._connect`` at *engine* and record how it was called."""
    opened: list[tuple[str, Any]] = []

    def fake_connect(url: str, engine_arg: Any) -> _FakeEngine:
        opened.append((url, engine_arg))
        return engine

    monkeypatch.setattr(migrate, "_connect", fake_connect)
    return opened


def _forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("this schema helper must not be called on this path")


# --- _database_url: environment precedence -------------------------------


def test_database_url_prefers_primary_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://primary")
    monkeypatch.setenv("SABIROUTE_DATABASE_URL", "postgresql://fallback")

    assert migrate._database_url() == "postgresql://primary"


def test_database_url_falls_back_to_sabiroute_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SABIROUTE_DATABASE_URL", "postgresql://fallback")

    assert migrate._database_url() == "postgresql://fallback"


def test_database_url_treats_empty_primary_variable_as_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("SABIROUTE_DATABASE_URL", "postgresql://fallback")

    assert migrate._database_url() == "postgresql://fallback"


def test_missing_database_url_exits_two_with_diagnostic(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SABIROUTE_DATABASE_URL", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        migrate._database_url()

    assert excinfo.value.code == 2
    assert "DATABASE_URL is required" in capsys.readouterr().err


# --- main(): SQLite path -------------------------------------------------


def test_main_applies_schema_directly_on_sqlite(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    engine = _FakeEngine("sqlite")
    opened = _install_engine(monkeypatch, engine)
    applied: list[tuple[Any, tuple[str, ...]]] = []

    def fake_ensure_schema(target: Any, *, groups: tuple[str, ...]) -> None:
        applied.append((target, groups))

    monkeypatch.setattr(migrate, "ensure_schema", fake_ensure_schema)
    monkeypatch.setattr(migrate, "ensure_schema_in_connection", _forbidden)
    monkeypatch.setattr(migrate, "resolve_schema_groups", lambda: ("core",))

    assert migrate.main() == 0

    assert opened == [("sqlite:///tmp.db", None)]
    assert applied == [(engine, ("core",))]
    assert engine.transaction is None
    assert capsys.readouterr().out == "Migrations applied (groups=('core',)).\n"


def test_main_skips_advisory_lock_on_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    engine = _FakeEngine("sqlite")
    _install_engine(monkeypatch, engine)
    monkeypatch.setattr(migrate, "ensure_schema", lambda target, *, groups: None)
    monkeypatch.setattr(migrate, "resolve_schema_groups", lambda: ("core",))

    assert migrate.main() == 0

    assert engine.connection.executed == []


def test_main_returns_one_when_sqlite_migration_raises(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    engine = _FakeEngine("sqlite")
    _install_engine(monkeypatch, engine)

    def exploding_ensure_schema(target: Any, *, groups: tuple[str, ...]) -> None:
        raise OSError("disk I/O error")

    monkeypatch.setattr(migrate, "ensure_schema", exploding_ensure_schema)
    monkeypatch.setattr(migrate, "resolve_schema_groups", lambda: ("core",))

    assert migrate.main() == 1

    captured = capsys.readouterr()
    assert "Migration failed: disk I/O error" in captured.err
    assert "Migrations applied" not in captured.out


# --- main(): PostgreSQL path --------------------------------------------


def test_main_locks_and_migrates_inside_one_transaction_on_postgresql(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://db")
    engine = _FakeEngine("postgresql")
    _install_engine(monkeypatch, engine)
    locked: list[tuple[Any, Any, tuple[str, ...]]] = []

    def fake_ensure_schema_in_connection(
        connection: Any, target: Any, *, groups: tuple[str, ...]
    ) -> None:
        locked.append((connection, target, groups))

    monkeypatch.setattr(
        migrate, "ensure_schema_in_connection", fake_ensure_schema_in_connection
    )
    monkeypatch.setattr(migrate, "ensure_schema", _forbidden)
    monkeypatch.setattr(migrate, "resolve_schema_groups", lambda: ("core", "full"))

    assert migrate.main() == 0

    transaction = engine.transaction
    assert transaction is not None
    assert transaction.entered is True
    assert transaction.exited is True
    assert locked == [(engine.connection, engine, ("core", "full"))]

    statements = engine.connection.executed
    assert len(statements) == 2

    timeout_statement, timeout_params = statements[0]
    assert "lock_timeout" in timeout_statement
    assert f"'{migrate.LOCK_TIMEOUT_SECONDS}s'" in timeout_statement
    assert timeout_params is None

    lock_statement, lock_params = statements[1]
    assert "pg_advisory_xact_lock" in lock_statement
    assert lock_params == {"key": migrate.SABIROUTE_MIGRATION_LOCK_KEY}

    assert "groups=('core', 'full')" in capsys.readouterr().out


def test_main_reports_resolution_error_before_touching_database(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    engine = _FakeEngine("sqlite")
    _install_engine(monkeypatch, engine)

    def bad_groups() -> tuple[str, ...]:
        raise ValueError("unknown schema group: 'nope'")

    monkeypatch.setattr(migrate, "resolve_schema_groups", bad_groups)
    monkeypatch.setattr(migrate, "ensure_schema", _forbidden)
    monkeypatch.setattr(migrate, "ensure_schema_in_connection", _forbidden)

    assert migrate.main() == 1

    assert engine.transaction is None
    assert "Migration failed: unknown schema group: 'nope'" in capsys.readouterr().err


def test_main_returns_one_when_postgres_migration_raises(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://db")
    engine = _FakeEngine("postgresql")
    _install_engine(monkeypatch, engine)

    def deadlocking(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("deadlock detected")

    monkeypatch.setattr(migrate, "ensure_schema_in_connection", deadlocking)
    monkeypatch.setattr(migrate, "resolve_schema_groups", lambda: ("full",))

    assert migrate.main() == 1

    transaction = engine.transaction
    assert transaction is not None
    assert transaction.exited is True
    captured = capsys.readouterr()
    assert "Migration failed: deadlock detected" in captured.err
    assert "Migrations applied" not in captured.out


# --- module entry point -------------------------------------------------


def test_running_the_module_exits_with_the_main_return_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SABIROUTE_DATABASE_URL", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("sabiroute.migrate", run_name="__main__")

    assert excinfo.value.code == 2
