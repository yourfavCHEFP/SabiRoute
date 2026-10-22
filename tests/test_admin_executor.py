"""Admin-route coverage for the Mission 16B executor migration.

Every admin store operation now runs through
``GatewayState.store_executor``. These tests drive the HTTP admin routes
(never the store directly) so behavior preservation is proven on the real
request path, including across separate TestClient event loops.
"""

from __future__ import annotations

from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    make_config,
    provision_test_key,
)
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

MESSAGES = [{"role": "user", "content": "hello"}]
ADMIN_KEY = "test-admin-secret-distinct-from-client-key"


def _make_app(monkeypatch):
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", ADMIN_KEY)
    return state, create_app(state=state)


def _admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {ADMIN_KEY}"}


def test_admin_create_rotate_revoke_round_trip(monkeypatch):
    _, app = _make_app(monkeypatch)
    headers = _admin_headers()
    with TestClient(app) as client:
        created = client.post(
            "/admin/api-keys",
            json={"project_id": "project-a", "name": "key-a"},
            headers=headers,
        )
        assert created.status_code == 201
        body = created.json()
        assert body["project_id"] == "project-a"
        assert body["api_key"].startswith("sr_")
        key_id = body["id"]

        rotated = client.post(f"/admin/api-keys/{key_id}/rotate", headers=headers)
        assert rotated.status_code == 201
        new_body = rotated.json()
        assert new_body["id"] != key_id
        assert new_body["api_key"] != body["api_key"]

        # The old credential is revoked by rotation.
        stale = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {body['api_key']}"},
        )
        assert stale.status_code == 401

        revoked = client.post(
            f"/admin/api-keys/{new_body['id']}/revoke", headers=headers
        )
        assert revoked.status_code == 200
        assert revoked.json() == {"id": new_body["id"], "status": "revoked"}

        missing = client.post("/admin/api-keys/no-such-key/revoke", headers=headers)
        assert missing.status_code == 404


def test_admin_rate_limit_round_trip(monkeypatch):
    _, app = _make_app(monkeypatch)
    headers = _admin_headers()
    with TestClient(app) as client:
        key_id = client.post(
            "/admin/api-keys",
            json={"project_id": "project-b", "name": "key-b"},
            headers=headers,
        ).json()["id"]

        set_response = client.put(
            f"/admin/api-keys/{key_id}/rate-limit",
            json={"requests_per_minute": 60, "burst_capacity": 10},
            headers=headers,
        )
        assert set_response.status_code == 200
        assert set_response.json()["requests_per_minute"] == 60

        got = client.get(f"/admin/api-keys/{key_id}/rate-limit", headers=headers)
        assert got.status_code == 200
        assert got.json()["burst_capacity"] == 10

        cleared = client.delete(
            f"/admin/api-keys/{key_id}/rate-limit", headers=headers
        )
        assert cleared.status_code == 200
        assert cleared.json()["status"] == "rate_limit_removed"

        empty = client.get(f"/admin/api-keys/{key_id}/rate-limit", headers=headers)
        assert empty.json()["requests_per_minute"] is None

        unknown = client.get("/admin/api-keys/no-such-key/rate-limit", headers=headers)
        assert unknown.status_code == 404


def test_admin_budget_round_trip(monkeypatch):
    _, app = _make_app(monkeypatch)
    headers = _admin_headers()
    with TestClient(app) as client:
        key_id = client.post(
            "/admin/api-keys",
            json={"project_id": "project-c", "name": "key-c"},
            headers=headers,
        ).json()["id"]

        set_response = client.put(
            f"/admin/api-keys/{key_id}/budget",
            json={"daily_tokens": 1000, "monthly_tokens": None},
            headers=headers,
        )
        assert set_response.status_code == 200
        assert set_response.json()["daily_tokens"] == 1000

        got = client.get(f"/admin/api-keys/{key_id}/budget", headers=headers)
        assert got.status_code == 200
        assert got.json()["budget"]["daily_tokens"] == 1000
        usage = got.json()["usage"]
        assert usage["daily"]["tokens"] == 0
        assert usage["monthly"]["tokens"] == 0

        cleared = client.delete(f"/admin/api-keys/{key_id}/budget", headers=headers)
        assert cleared.status_code == 200
        assert cleared.json()["status"] == "budget_removed"

        unknown = client.get("/admin/api-keys/no-such-key/budget", headers=headers)
        assert unknown.status_code == 404


def test_admin_usage_lists_completed_request(monkeypatch):
    state, app = _make_app(monkeypatch)
    client_key = provision_test_key(state)
    headers = _admin_headers()
    with TestClient(app) as client:
        completion = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
            headers={"Authorization": f"Bearer {client_key}"},
        )
        assert completion.status_code == 200

        key_id = next(iter(state.key_store.records))
        usage = client.get(
            f"/admin/api-keys/{key_id}/usage", headers=headers, params={"limit": 50}
        )
        assert usage.status_code == 200
        body = usage.json()
        assert body["total"] == 1
        assert body["items"][0]["final_status"] == 200

        unknown = client.get(
            "/admin/api-keys/no-such-key/usage", headers=headers
        )
        assert unknown.status_code == 404


def test_admin_executor_usable_across_client_contexts(monkeypatch):
    """Separate TestClient portals use separate event loops; admin must work in both."""
    state, app = _make_app(monkeypatch)
    headers = _admin_headers()
    with TestClient(app) as first:
        key_id = first.post(
            "/admin/api-keys",
            json={"project_id": "project-d", "name": "key-d"},
            headers=headers,
        ).json()["id"]
    with TestClient(app) as second:
        got = second.get(f"/admin/api-keys/{key_id}/rate-limit", headers=headers)
        assert got.status_code == 200
        assert got.json()["key_id"] == key_id
    assert state.store_executor.in_use_count == 0
