"""Lineage compatibility-state invariants (F-27 follow-up, isolated SQLite only).

Scope: documents the three-state identity model the admission path
(``rate_limit_key = identity.lineage_id or identity.key_id`` in
``api/completions.py``) assumes but cannot currently distinguish:

1. Legacy key: lineage_id IS NULL (pre-0006 row, never migrated).
2. Migrated key with valid lineage: lineage_id non-NULL AND a matching row
   exists in ``sabiroute_accounting_lineages``.
3. Migrated key with missing lineage: lineage_id non-NULL but NO matching
   row (legacy rotation, deleted row, crash between key insert and lineage
   insert). Admission currently treats this exactly like state 2.

These tests use throwaway ``tempfile`` SQLite databases only. They never
touch shared, production, or loopback-service databases, and they do not
modify any Terminal A-owned source file.

Labels: VERIFIED BY RUNTIME (fresh isolated run); historical states are
cited, not re-asserted.
"""

from __future__ import annotations

import tempfile

from sqlalchemy import text
from sqlalchemy.engine import Engine

from sabiroute.security.keys import issue_api_key, rotate_api_key
from sabiroute.security.store import (
    PostgresApiKeyStore,
    _connect,
    ensure_schema,
    get_lineage,
)


def _fresh_store() -> tuple[PostgresApiKeyStore, Engine]:
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    return store, eng


def test_fresh_key_has_backing_lineage_row() -> None:
    """State 2 invariant: a newly issued key resolves to an existing row."""
    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="k")
    assert rec.lineage_id is not None
    with eng.begin() as conn:
        assert get_lineage(conn, rec.lineage_id) is not None
    eng.dispose()


def test_legacy_key_is_null_not_missing() -> None:
    """State 1 invariant: an unmigrated legacy row carries NULL, not a dangling pointer."""
    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="k")
    with eng.begin() as conn:
        conn.execute(
            text("UPDATE sabiroute_api_keys SET lineage_id = NULL WHERE key_id = :k"),
            {"k": rec.key_id},
        )
    assert store.get(rec.key_id).lineage_id is None
    eng.dispose()


def test_rotated_legacy_key_has_backing_lineage_row() -> None:
    """State 3 regression: rotating a NULL-lineage legacy key must establish
    a backing lineage row atomically (fixed in Terminal A rotate path)."""
    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="k")
    with eng.begin() as conn:
        conn.execute(
            text("UPDATE sabiroute_api_keys SET lineage_id = NULL WHERE key_id = :k"),
            {"k": rec.key_id},
        )
    new, _ = rotate_api_key(store, rec.key_id)
    assert new is not None and new.lineage_id is not None
    with eng.begin() as conn:
        assert get_lineage(conn, new.lineage_id) is not None
    eng.dispose()
