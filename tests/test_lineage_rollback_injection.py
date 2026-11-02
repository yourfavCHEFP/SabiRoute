"""F-27 rollback / failure-injection proof (isolated SQLite only).

Proves the missing invariant: a deterministic failure during a
lineage-sensitive mutation leaves NO partial lineage/accounting state,
and a subsequent retry succeeds deterministically.

Failure seam (single, bounded, documented): the module-level
``insert`` symbol in ``sabiroute.security.store`` is monkeypatched so
that an INSERT targeting ``_ACCOUNTING_LINEAGES`` raises
``RuntimeError("injected lineage-write failure")`` while every other
table delegates to the real ``sqlalchemy.insert``. This simulates the
lineage-row write failing *after* the key-row write has begun inside
the same transaction -- the exact crash boundary the rollback logic
must survive. No timing sleeps, no randomness, no concurrency.

Storage isolation: throwaway ``tempfile`` SQLite databases only. No
Redis, no shared/production infrastructure.

Labels: VERIFIED BY RUNTIME (fresh isolated run recorded in handoff).
"""

from __future__ import annotations

import tempfile

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

import sabiroute.security.store as store_module
from sabiroute.security.keys import (
    _new_key_record,
    issue_api_key,
    rotate_api_key,
)
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
    return PostgresApiKeyStore(url, engine=eng), eng


def _counts(eng: Engine) -> tuple[int, int]:
    with eng.connect() as conn:
        n_keys = conn.execute(text("SELECT COUNT(*) FROM sabiroute_api_keys")).scalar()
        n_lin = conn.execute(
            text("SELECT COUNT(*) FROM sabiroute_accounting_lineages")
        ).scalar()
    assert isinstance(n_keys, int) and isinstance(n_lin, int)
    return n_keys, n_lin


def _fail_lineage_insert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bounded seam: only the lineage-table INSERT raises; all else is real."""
    real_insert = store_module.insert

    def failing_insert(table=None, *args, **kwargs):  # type: ignore[no-untyped-def]
        if table is store_module._ACCOUNTING_LINEAGES:
            raise RuntimeError("injected lineage-write failure")
        return real_insert(table, *args, **kwargs)

    monkeypatch.setattr(store_module, "insert", failing_insert)


def test_create_rollback_on_lineage_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A. Record valid pre-state (one live key + its lineage row).
    B. Inject lineage-write failure. C. Run real ``store.create``.
    D. Assert controlled failure. E/F. Re-read: no partial key row,
    no partial lineage row, baseline untouched. G. Retry succeeds."""
    store, eng = _fresh_store()
    base, _ = issue_api_key(store, project_id="p", name="base")
    k0, l0 = _counts(eng)
    assert (k0, l0) == (1, 1)

    victim, _ = _new_key_record(project_id="p", name="victim")
    _fail_lineage_insert(monkeypatch)
    with pytest.raises(RuntimeError, match="injected lineage-write failure"):
        store.create(victim)

    assert store.get(victim.key_id) is None
    with eng.connect() as conn:
        assert get_lineage(conn, victim.lineage_id) is None
        assert get_lineage(conn, base.lineage_id) is not None
    assert _counts(eng) == (k0, l0)
    live_base = store.get(base.key_id)
    assert live_base is not None and live_base.revoked_at is None

    monkeypatch.undo()
    store.create(victim)
    got = store.get(victim.key_id)
    assert got is not None and got.revoked_at is None
    with eng.connect() as conn:
        assert get_lineage(conn, victim.lineage_id) is not None
    assert _counts(eng) == (k0 + 1, l0 + 1)
    eng.dispose()


def test_rotate_rollback_on_lineage_backstop_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy (NULL-lineage) rotation exercises the same-transaction
    lineage backstop -- the newest lineage mutation path. Inject failure
    at that boundary: rotation must fail, the original key must remain
    active with NULL lineage, no partial replacement may survive, and a
    retry must establish valid lineage preserving rotation semantics."""
    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="legacy")
    with eng.begin() as conn:
        conn.execute(
            text("UPDATE sabiroute_api_keys SET lineage_id = NULL WHERE key_id = :k"),
            {"k": rec.key_id},
        )
    k0, l0 = _counts(eng)

    _fail_lineage_insert(monkeypatch)
    with pytest.raises(RuntimeError, match="injected lineage-write failure"):
        rotate_api_key(store, rec.key_id)

    old = store.get(rec.key_id)
    assert old is not None
    assert old.revoked_at is None
    assert old.lineage_id is None
    assert _counts(eng) == (k0, l0)
    with eng.connect() as conn:
        assert conn.execute(
            text("SELECT COUNT(*) FROM sabiroute_api_keys WHERE revoked_at IS NOT NULL")
        ).scalar() == 0

    monkeypatch.undo()
    out = rotate_api_key(store, rec.key_id)
    assert out is not None
    new, _ = out
    assert new.lineage_id is not None
    with eng.connect() as conn:
        assert get_lineage(conn, new.lineage_id) is not None
    assert store.get(rec.key_id) is not None
    assert store.get(rec.key_id).revoked_at is not None  # type: ignore[union-attr]
    live_new = store.get(new.key_id)
    assert live_new is not None and live_new.revoked_at is None
    eng.dispose()
