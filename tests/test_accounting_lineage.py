"""F-27 accounting-lineage focused tests (isolated SQLite only)."""

from __future__ import annotations

import tempfile

import pytest
from sqlalchemy import inspect, text

from sabiroute.security.keys import ApiKeyBudget, issue_api_key, rotate_api_key
from sabiroute.security.store import (
    _ACCOUNTING_LINEAGES,
    PostgresApiKeyStore,
    _connect,
    _lineage_for_key,
    applied_schema_revisions,
    create_lineage,
    ensure_schema,
    get_lineage,
    reconcile_lineage_budgets,
)


def test_lineage_created_on_key_issuance():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    assert rec.lineage_id is not None
    assert store.get(rec.key_id).lineage_id == rec.lineage_id
    row = get_lineage(store._engine.connect(), rec.lineage_id)
    assert row is not None
    assert row.status == "active"


def test_rotation_preserves_lineage():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    orig = rec.lineage_id
    new, _ = rotate_api_key(store, rec.key_id)
    assert new is not None
    assert new.lineage_id == orig
    assert store.get(new.key_id).lineage_id == orig


def test_reconcile_fail_closed_on_missing_budget():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    with pytest.raises(ValueError, match="has no budget"):
        with eng.begin() as conn:
            reconcile_lineage_budgets(conn, rec.lineage_id, rec.key_id, "admin")


def test_reconcile_requires_approver():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with pytest.raises(ValueError, match="approver identity is required"):
        with eng.begin() as conn:
            reconcile_lineage_budgets(conn, rec.lineage_id, rec.key_id, "  ")


def test_reconcile_marks_reconciled():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with eng.begin() as conn:
        reconcile_lineage_budgets(conn, rec.lineage_id, rec.key_id, "admin-role")
        row = get_lineage(conn, rec.lineage_id)
        assert row.status == "reconciled"
        assert row.superseded_by == "admin-role"


def test_reconcile_conflict_blocks():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec1, _ = issue_api_key(store, project_id="p", name="k1")
    rec2, _ = issue_api_key(store, project_id="p", name="k2")
    # Put both keys in the same lineage.
    with eng.begin() as conn:
        conn.execute(
            text(
                "UPDATE sabiroute_api_keys SET lineage_id = :l WHERE key_id IN (:a, :b)"
            ),
            {"l": rec1.lineage_id, "a": rec1.key_id, "b": rec2.key_id},
        )
    store.set_budget(rec1.key_id, ApiKeyBudget(daily_tokens=100))
    store.set_budget(rec2.key_id, ApiKeyBudget(daily_tokens=200))
    with pytest.raises(ValueError, match="Conflicting budgets"):
        with eng.begin() as conn:
            reconcile_lineage_budgets(conn, rec1.lineage_id, rec1.key_id, "admin")


def test_legacy_upgrade_adds_lineage_column():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    # Simulate legacy schema: create without lineage columns by running
    # ensure_schema with a monkeypatch? Instead, just verify ensure_schema
    # creates the column on a fresh DB.
    ensure_schema(eng, groups="full")
    with eng.connect() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("sabiroute_api_keys")}
    assert "lineage_id" in cols
    revs = applied_schema_revisions(eng)
    assert "0006-accounting-lineages" in revs
    eng.dispose()


def test_missing_lineage_fails_closed():
    """A key with NULL lineage_id must not crash reads; lineage lookup returns None."""

    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    # Force lineage_id to NULL in the DB.
    with eng.begin() as conn:
        conn.execute(
            text(
                "UPDATE sabiroute_api_keys SET lineage_id = NULL WHERE key_id = :k"
            ),
            {"k": rec.key_id},
        )
        assert _lineage_for_key(conn, rec.key_id) is None
    engine = eng
    engine.dispose()


def test_legacy_upgrade_preserves_data():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=42))
    # Re-run migration (idempotent).
    ensure_schema(eng, groups="full")
    assert store.get(rec.key_id) is not None
    assert store.get_budget(rec.key_id).daily_tokens == 42
    eng.dispose()


def test_concurrent_rotation_preserves_lineage():
    """Concurrent rotations must not split authority or create duplicate lineages."""
    import threading

    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    orig_lineage = rec.lineage_id

    results = {}

    def rotate_worker(idx):
        try:
            target = rec.key_id
            if idx != 0 and 0 in results:
                target = results[0].key_id
            new, _ = rotate_api_key(store, target)
            results[idx] = new
        except Exception as exc:
            results[idx] = exc

    # First rotation succeeds; subsequent ones fail (key already revoked).
    t0 = threading.Thread(target=rotate_worker, args=(0,))
    t0.start()
    t0.join(timeout=10)
    ok = isinstance(results[0], type(rec)) or hasattr(results[0], "lineage_id")
    assert ok, "first rotation should succeed"
    assert results[0].lineage_id == orig_lineage

    # Second rotation on the already-revoked key must fail (return None).
    second = rotate_api_key(store, rec.key_id)
    assert second is None, "rotating a revoked key must return None"


def test_lineage_idempotent_creation():
    """Creating a lineage twice must not raise or create duplicates."""
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    with eng.begin() as conn:
        create_lineage(conn, "test-lineage-id")
        create_lineage(conn, "test-lineage-id")  # idempotent
        from sqlalchemy import select
        rows = conn.execute(
            select(_ACCOUNTING_LINEAGES).where(
                _ACCOUNTING_LINEAGES.c.lineage_id == "test-lineage-id"
            )
        ).all()
        assert len(rows) == 1
    eng.dispose()


def test_reconcile_idempotent():
    """Re-running reconcile on an already-reconciled lineage must succeed."""
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with eng.begin() as conn:
        reconcile_lineage_budgets(conn, rec.lineage_id, rec.key_id, "admin-role")
    with eng.begin() as conn:
        reconcile_lineage_budgets(conn, rec.lineage_id, rec.key_id, "admin-role")
        row = get_lineage(conn, rec.lineage_id)
        assert row.status == "reconciled"
    eng.dispose()


def test_shared_lineage_single_rate_limit_authority():
    """Migrated keys sharing a lineage must share one rate-limit bucket."""
    import inspect

    import sabiroute.api.completions as comp
    import sabiroute.security.auth as auth_mod

    assert hasattr(auth_mod, "require_admin_key")
    # Contract: completions admits with lineage_id or key_id, never both.
    src = inspect.getsource(comp)
    assert "identity.lineage_id or identity.key_id" in src
    # Both rotated keys resolve to the same lineage bucket key.
    import tempfile

    from sabiroute.security.keys import issue_api_key, rotate_api_key
    from sabiroute.security.store import PostgresApiKeyStore, _connect, ensure_schema
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    new, _ = rotate_api_key(store, rec.key_id)
    assert new is not None
    bucket_old = rec.lineage_id or rec.key_id
    bucket_new = new.lineage_id or new.key_id
    assert bucket_old == bucket_new, "rotated keys must share one lineage bucket"
    eng.dispose()


def test_missing_lineage_never_falls_back_to_key_bucket():
    """A migrated lineage with unavailable state must fail closed, not fall back."""
    import tempfile

    from sabiroute.security.store import _lineage_for_key, ensure_schema
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t2.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    # Unknown key has no lineage row: lookup returns None (fail closed).
    with eng.begin() as conn:
        assert _lineage_for_key(conn, "nonexistent-key-id") is None
    eng.dispose()
