"""B1 Stage B: schema-group boundary tests (isolated SQLite only)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text

from sabiroute.security.store import (
    CORE_TABLES,
    SABICHAT_PRODUCT_TABLES,
    _connect,
    applied_schema_revisions,
    ensure_schema,
    resolve_schema_groups,
)


def _tables(engine):
    return set(inspect(engine).get_table_names())


def test_mode_defaults_to_full_and_invalid_fails_before_ddl(monkeypatch):
    monkeypatch.delenv("SABIROUTE_SCHEMA_GROUPS", raising=False)
    assert resolve_schema_groups() == "full"
    monkeypatch.setenv("SABIROUTE_SCHEMA_GROUPS", "  ")
    assert resolve_schema_groups() == "full"
    monkeypatch.setenv("SABIROUTE_SCHEMA_GROUPS", "bogus")
    with pytest.raises(ValueError, match="must be 'core' or 'full'"):
        resolve_schema_groups()
    assert resolve_schema_groups("core") == "core"
    assert resolve_schema_groups("FULL") == "full"


def test_fresh_core_creates_nine_no_product_tables():
    engine = create_engine("sqlite:///:memory:")
    ensure_schema(engine, groups="core")
    tables = _tables(engine)
    assert {t.name for t in CORE_TABLES} <= tables
    assert not ({t.name for t in SABICHAT_PRODUCT_TABLES} & tables)
    engine.dispose()


def test_fresh_full_creates_all_thirteen():
    engine = create_engine("sqlite:///:memory:")
    ensure_schema(engine, groups="full")
    tables = _tables(engine)
    assert {t.name for t in CORE_TABLES} <= tables
    assert {t.name for t in SABICHAT_PRODUCT_TABLES} <= tables
    engine.dispose()


def test_legacy_full_recognized_data_untouched(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="full")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO sabiroute_schema_versions "
                "(revision, description, applied_at) VALUES "
                "('sentinel', 'legacy row', CURRENT_TIMESTAMP)"
            )
        )
    ensure_schema(engine, groups="full")
    revs = applied_schema_revisions(engine)
    assert "sentinel" in revs
    assert "0001-usage-source" in revs
    engine.dispose()


def test_core_to_full_upgrade(tmp_path):
    url = f"sqlite:///{tmp_path / 'upgrade.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="core")
    assert "sabichat_users" not in _tables(engine)
    ensure_schema(engine, groups="full")
    assert "sabichat_users" in _tables(engine)
    assert "sabichat_messages" in _tables(engine)
    engine.dispose()


def test_failed_init_retries_without_false_state(tmp_path, monkeypatch):
    from sabiroute.security import store as store_mod

    url = f"sqlite:///{tmp_path / 'retry.sqlite'}"
    engine = _connect(url, None)
    real = store_mod._migrate_usage_columns

    calls = {"n": 0}

    def _boom_once(connection, eng):
        if calls["n"] == 0:
            calls["n"] += 1
            raise RuntimeError("simulated migration failure")
        return real(connection, eng)

    monkeypatch.setattr(store_mod, "_migrate_usage_columns", _boom_once)
    with pytest.raises(RuntimeError, match="simulated migration failure"):
        ensure_schema(engine, groups="core")
    monkeypatch.undo()
    ensure_schema(engine, groups="core")
    assert "sabiroute_api_keys" in _tables(engine)
    assert "sabichat_users" not in _tables(engine)
    engine.dispose()


def test_core_marked_db_requesting_full_upgrades(tmp_path):
    url = f"sqlite:///{tmp_path / 'marked.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="core")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sabichat_users (x VARCHAR(8))"))
    tables = _tables(engine)
    assert "sabichat_users" in tables
    engine.dispose()


def test_quota_ledgers_preserved_across_core_ensure(tmp_path):
    url = f"sqlite:///{tmp_path / 'quota.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="core")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO sabichat_quota_windows "
                "(user_id, window_start, reserved_tokens, consumed_tokens, updated_at) "
                "VALUES ('u1', CURRENT_TIMESTAMP, 5, 2, CURRENT_TIMESTAMP)"
            )
        )
    # Re-running core must preserve the ledger row (no downgrade involved:
    # this database was never marked full).
    ensure_schema(engine, groups="core")
    with engine.connect() as conn:
        rows = list(conn.execute(text("SELECT * FROM sabichat_quota_windows")))
    assert len(rows) == 1
    engine.dispose()


def test_legacy_full_requested_core_refuses_without_changes(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy-core.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="full")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO sabichat_quota_windows "
                "(user_id, window_start, reserved_tokens, consumed_tokens, updated_at) "
                "VALUES ('u1', CURRENT_TIMESTAMP, 5, 2, CURRENT_TIMESTAMP)"
            )
        )
    with engine.connect() as conn:
        before_tables = set(inspect(conn).get_table_names())
        before_rows = list(conn.execute(text("SELECT * FROM sabichat_quota_windows")))
    with pytest.raises(ValueError, match="not applicable|downgrade"):
        ensure_schema(engine, groups="core")
    with engine.connect() as conn:
        assert set(inspect(conn).get_table_names()) == before_tables
        assert list(conn.execute(text("SELECT * FROM sabichat_quota_windows"))) == before_rows
    engine.dispose()


def test_full_marked_requested_core_refuses_without_downgrade(tmp_path):
    url = f"sqlite:///{tmp_path / 'full-core.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="full")
    with pytest.raises(ValueError, match="downgrade"):
        ensure_schema(engine, groups="core")
    # Nothing removed: all 13 tables still present.
    tables = set(inspect(engine).get_table_names())
    assert {t.name for t in CORE_TABLES} <= tables
    assert {t.name for t in SABICHAT_PRODUCT_TABLES} <= tables
    engine.dispose()


def test_core_state_with_unexpected_product_tables_detected(tmp_path):
    url = f"sqlite:///{tmp_path / 'mismatch.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="core")
    # Out-of-band DDL: product table appears without a full migration.
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sabichat_users (x VARCHAR(8))"))
    with pytest.raises(ValueError, match="[Uu]nexpected|not applicable"):
        ensure_schema(engine, groups="core")
    # Nothing deleted, no false state update.
    assert "sabichat_users" in set(inspect(engine).get_table_names())
    engine.dispose()


def test_missing_product_table_repaired_in_full_mode(tmp_path):
    url = f"sqlite:///{tmp_path / 'repair.sqlite'}"
    engine = _connect(url, None)
    ensure_schema(engine, groups="full")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE sabichat_messages"))
    assert "sabichat_messages" not in set(inspect(engine).get_table_names())
    ensure_schema(engine, groups="full")
    assert "sabichat_messages" in set(inspect(engine).get_table_names())
    engine.dispose()
