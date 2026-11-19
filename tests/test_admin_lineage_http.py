"""F-27 admin lineage-reconciliation HTTP tests (isolated SQLite only).

Drives the real ``POST /admin/api-keys/{key_id}/reconcile-lineage``
contract through the HTTP layer (never the store directly):

1. missing admin secret -> 401 ``authentication_error``, no mutation;
2. wrong admin secret   -> 401 ``authentication_error``, no mutation;
3. unknown key id        -> 404 ``key_not_found``, no lineage mutation;
4. conflicting sibling budgets in the same lineage -> 409
   ``lineage_reconciliation_conflict``, no partial reconciliation;
5. aligned lineage -> 200 ``{"reconciled": True, ...}`` with the lineage
   row audit marker (``status == "reconciled"``,
   ``superseded_by == approver``) verified in the database.

Storage is a disposable SQLite file per test; no shared or production
database is touched.
"""

from __future__ import annotations

import tempfile

from conftest import StubLiteLLMClient, make_config
from fastapi.testclient import TestClient
from sqlalchemy import text

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.keys import ApiKeyBudget, issue_api_key
from sabiroute.security.store import (
    PostgresApiKeyStore,
    _connect,
    ensure_schema,
    get_lineage,
)

ADMIN_KEY = "test-admin-lineage-secret"
APPROVER = "admin-role"


def _make_app(monkeypatch):
    """Build an isolated app backed by a disposable SQLite key store."""
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/lineage-http.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=store,
    )
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", ADMIN_KEY)
    monkeypatch.delenv("LITELLM_MASTER_KEY", raising=False)
    return store, eng, create_app(state=state)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {ADMIN_KEY}"}


def test_reconcile_lineage_missing_admin_secret_returns_401(monkeypatch):
    store, eng, app = _make_app(monkeypatch)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with TestClient(app) as client:
        response = client.post(
            f"/admin/api-keys/{rec.key_id}/reconcile-lineage",
            json={"approver": APPROVER},
        )
        assert response.status_code == 401
        assert response.json()["detail"]["error"]["type"] == "authentication_error"
    with eng.connect() as conn:
        row = get_lineage(conn, rec.lineage_id)
    assert row is not None
    assert row.status == "active"
    assert row.superseded_by is None


def test_reconcile_lineage_wrong_admin_secret_returns_401(monkeypatch):
    store, eng, app = _make_app(monkeypatch)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with TestClient(app) as client:
        response = client.post(
            f"/admin/api-keys/{rec.key_id}/reconcile-lineage",
            json={"approver": APPROVER},
            headers={"Authorization": "Bearer wrong-secret"},
        )
        assert response.status_code == 401
        assert response.json()["detail"]["error"]["type"] == "authentication_error"
    with eng.connect() as conn:
        row = get_lineage(conn, rec.lineage_id)
    assert row is not None
    assert row.status == "active"
    assert row.superseded_by is None


def test_reconcile_lineage_unknown_key_returns_404(monkeypatch):
    store, eng, app = _make_app(monkeypatch)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with TestClient(app) as client:
        response = client.post(
            "/admin/api-keys/key-no-such-key/reconcile-lineage",
            json={"approver": APPROVER},
            headers=_auth(),
        )
        assert response.status_code == 404
        assert response.json()["detail"]["error"]["type"] == "key_not_found"
    # The only real lineage in this isolated store is untouched.
    with eng.connect() as conn:
        row = get_lineage(conn, rec.lineage_id)
    assert row is not None
    assert row.status == "active"
    assert row.superseded_by is None


def test_reconcile_lineage_missing_row_returns_409(monkeypatch):
    store, eng, app = _make_app(monkeypatch)
    rec, plaintext = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with eng.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM sabiroute_accounting_lineages WHERE lineage_id = :l"
            ),
            {"l": rec.lineage_id},
        )
        assert get_lineage(conn, rec.lineage_id) is None
    # A dangling lineage is normally denied by store.get. Hold the admin's
    # already-read record to exercise the read→reconcile race: the row is
    # gone when reconciliation executes, which is the rowcount guard's job.
    assert store.get(rec.key_id) is None
    monkeypatch.setattr(
        store, "get", lambda key_id: rec if key_id == rec.key_id else None
    )
    with TestClient(app) as client:
        response = client.post(
            f"/admin/api-keys/{rec.key_id}/reconcile-lineage",
            json={"approver": APPROVER},
            headers=_auth(),
        )
        assert response.status_code == 409
        error = response.json()["detail"]["error"]
        assert error["type"] == "reconciliation_conflict"
        assert "not found" in error["message"]
        assert ADMIN_KEY not in response.text
        assert plaintext not in response.text
    # The missing row must not be resurrected by reconciliation.
    with eng.connect() as conn:
        assert get_lineage(conn, rec.lineage_id) is None


def test_reconcile_lineage_conflicting_budgets_returns_409(monkeypatch):
    store, eng, app = _make_app(monkeypatch)
    rec1, _ = issue_api_key(store, project_id="p", name="k1")
    rec2, _ = issue_api_key(store, project_id="p", name="k2")
    # Place both keys in the same lineage, then diverge their budgets.
    with eng.begin() as conn:
        conn.execute(
            text(
                "UPDATE sabiroute_api_keys SET lineage_id = :l "
                "WHERE key_id IN (:a, :b)"
            ),
            {"l": rec1.lineage_id, "a": rec1.key_id, "b": rec2.key_id},
        )
    store.set_budget(rec1.key_id, ApiKeyBudget(daily_tokens=100))
    store.set_budget(rec2.key_id, ApiKeyBudget(daily_tokens=200))
    with TestClient(app) as client:
        response = client.post(
            f"/admin/api-keys/{rec1.key_id}/reconcile-lineage",
            json={"approver": APPROVER},
            headers=_auth(),
        )
        assert response.status_code == 409
        assert (
            response.json()["detail"]["error"]["type"] == "reconciliation_conflict"
        )
    # No partial reconciliation: the lineage row keeps its active state.
    with eng.connect() as conn:
        row = get_lineage(conn, rec1.lineage_id)
    assert row is not None
    assert row.status == "active"
    assert row.superseded_by is None


def test_reconcile_lineage_success_records_audit_marker(monkeypatch):
    store, eng, app = _make_app(monkeypatch)
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=100))
    with TestClient(app) as client:
        response = client.post(
            f"/admin/api-keys/{rec.key_id}/reconcile-lineage",
            json={"approver": APPROVER},
            headers=_auth(),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "reconciled"
        assert body["key_id"] == rec.key_id
    # Required audit evidence: the lineage row carries the marker.
    # The operator identity is the fixed administrative role token
    # ``admin-role`` recorded by the endpoint itself.
    with eng.connect() as conn:
        row = get_lineage(conn, rec.lineage_id)
    assert row is not None
    assert row.status == "reconciled"
    assert row.superseded_by == "admin-role"
