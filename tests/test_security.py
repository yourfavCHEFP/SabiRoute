from __future__ import annotations

from dataclasses import asdict

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClient
from sabiroute.routing.router import RouteDecision
from sabiroute.security.keys import issue_api_key
from sabiroute.security.store import PostgresApiKeyStore

MESSAGES = [{"role": "user", "content": "hello"}]


def _client_with_store():
    stub = StubLiteLLMClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=stub, key_store=store)
    return TestClient(create_app(state=state)), state, store, stub


def _admin_headers(key: str = "test-admin-bootstrap-secret") -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def test_valid_key_authenticates_completion_and_key_hash_only_is_stored():
    client, state, store, stub = _client_with_store()
    record, secret = issue_api_key(store, project_id="project-a", name="primary")

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
        headers={"Authorization": f"Bearer {secret}"},
    )

    assert response.status_code == 200
    assert stub.calls == ["primary"]
    assert state.key_store is store
    assert store.get(record.key_id) == record
    assert secret not in repr(asdict(record))
    assert record.key_hash != secret
    assert state.usage.totals()["primary"] == 5


def test_missing_malformed_invalid_and_revoked_keys_share_response():
    client, _, store, _ = _client_with_store()
    _, revoked_secret = issue_api_key(store, project_id="project-a", name="revoked")
    revoked_id = next(key for key, row in store.records.items() if row.key_hash)
    assert store.revoke(revoked_id, store.get(revoked_id).created_at)

    headers = [
        {},
        {"Authorization": "Basic not-a-bearer"},
        {"Authorization": "Bearer malformed"},
        {
            "Authorization": (
                "Bearer sr_live_000000000000000000000000_"
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            )
        },
        {"Authorization": f"Bearer {revoked_secret}"},
    ]
    responses = [
        client.post(
            "/v1/chat/completions", json={"model": "primary", "messages": MESSAGES}, headers=h
        )
        for h in headers
    ]

    assert all(response.status_code == 401 for response in responses)
    assert all(response.json() == responses[0].json() for response in responses)
    assert responses[0].json()["detail"]["error"]["message"] == "Invalid bearer credential."
    assert revoked_secret not in responses[-1].text


def test_completion_and_admin_are_protected_but_health_is_public(monkeypatch):
    client, state, _, _ = _client_with_store()
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "separate-admin-bootstrap-secret")

    completion = client.post(
        "/v1/chat/completions", json={"model": "primary", "messages": MESSAGES}
    )
    admin = client.get("/admin/health")
    public_health = client.get("/health")
    public_liveness = client.get("/health/live")

    assert completion.status_code == 401
    assert admin.status_code == 401
    assert public_health.status_code == 200
    assert public_liveness.status_code == 200
    assert state.metrics.snapshot()["requests_total"] == 0


def test_key_creation_discloses_secret_once_and_rotation_revokes_old_key(monkeypatch, caplog):
    client, state, store, stub = _client_with_store()
    admin_secret = "separate-admin-bootstrap-secret"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", admin_secret)
    admin_headers = _admin_headers(admin_secret)

    created = client.post(
        "/admin/api-keys",
        json={"project_id": "project-a", "name": "production", "metadata": {"tier": "standard"}},
        headers=admin_headers,
    )
    assert created.status_code == 201
    body = created.json()
    old_secret = body["api_key"]
    old_record = store.get(body["id"])
    assert old_record is not None
    assert old_secret not in repr(asdict(old_record))
    assert old_secret not in str(state.metrics.snapshot())

    rotated = client.post(f"/admin/api-keys/{body['id']}/rotate", headers=admin_headers)
    assert rotated.status_code == 201
    new_secret = rotated.json()["api_key"]
    assert new_secret != old_secret
    assert rotated.json()["project_id"] == "project-a"
    assert store.get(body["id"]).revoked_at is not None

    old_attempt = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
        headers={"Authorization": f"Bearer {old_secret}"},
    )
    new_attempt = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
        headers={"Authorization": f"Bearer {new_secret}"},
    )
    assert old_attempt.status_code == 401
    assert new_attempt.status_code == 200
    assert stub.calls == ["primary"]

    later_response = client.get("/admin/metrics", headers=admin_headers)
    assert later_response.status_code == 200
    assert old_secret not in later_response.text
    assert new_secret not in later_response.text
    assert old_secret not in caplog.text
    assert new_secret not in caplog.text
    assert old_secret not in later_response.json().__repr__()
    assert state.errors.counts() == {}


def test_key_revocation_disables_key_without_echoing_it(monkeypatch):
    client, _, store, _ = _client_with_store()
    admin_secret = "separate-admin-bootstrap-secret"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", admin_secret)
    created = client.post(
        "/admin/api-keys",
        json={"project_id": "project-a", "name": "revocable"},
        headers=_admin_headers(admin_secret),
    )
    secret = created.json()["api_key"]
    result = client.post(
        f"/admin/api-keys/{created.json()['id']}/revoke",
        headers=_admin_headers(admin_secret),
    )
    assert result.status_code == 200
    assert secret not in result.text
    assert store.get(created.json()["id"]).revoked_at is not None


def test_admin_secret_cannot_equal_litellm_master_key(monkeypatch):
    client, _, _, _ = _client_with_store()
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "shared-internal-secret")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "shared-internal-secret")

    response = client.get("/admin/health", headers=_admin_headers("shared-internal-secret"))

    assert response.status_code == 503
    assert (
        response.json()["detail"]["error"]["message"]
        == "Administrative authentication is unavailable."
    )
    assert "shared-internal-secret" not in response.text


def test_admin_secret_cannot_use_client_key_namespace(monkeypatch):
    client, _, _, _ = _client_with_store()
    client_namespace_secret = "sr_live_admin-namespace-secret"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", client_namespace_secret)

    response = client.get(
        "/admin/health",
        headers=_admin_headers(client_namespace_secret),
    )

    assert response.status_code == 503
    assert client_namespace_secret not in response.text


def test_injected_store_prevents_database_connection(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/sabiroute")
    store = InMemoryApiKeyStore()

    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=store,
    )

    assert state.key_store is store


def test_sql_store_persists_hash_and_supports_atomic_rotation_and_revocation():
    engine = create_engine("sqlite:///:memory:")
    store = PostgresApiKeyStore("sqlite:///:memory:", engine=engine)
    old_record, old_secret = issue_api_key(store, project_id="project-pg", name="smoke")

    loaded = store.get(old_record.key_id)
    assert loaded is not None
    assert loaded.key_hash == old_record.key_hash
    assert loaded.project_id == "project-pg"
    assert loaded.name == "smoke"
    assert old_secret not in repr(asdict(loaded))

    from sabiroute.security.keys import rotate_api_key

    rotated = rotate_api_key(store, old_record.key_id)
    assert rotated is not None
    new_record, new_secret = rotated
    assert new_secret != old_secret
    assert store.get(old_record.key_id).revoked_at is not None
    assert store.get(new_record.key_id).revoked_at is None
    assert old_secret not in repr(asdict(store.get(new_record.key_id)))

    assert store.revoke(new_record.key_id, new_record.created_at)
    assert store.get(new_record.key_id).revoked_at is not None
    store.close()


@pytest.mark.asyncio
async def test_litellm_boundary_sends_internal_master_key_not_client_key(monkeypatch):
    import sabiroute.providers.litellm_client as boundary

    internal_key = "internal-litellm-master-test"
    client_key = "sr_live_client-secret-must-not-be-forwarded"
    monkeypatch.setenv("LITELLM_MASTER_KEY", internal_key)
    captured: dict[str, object] = {}

    class Response:
        status_code = 200
        is_error = False

        @staticmethod
        def json():
            return {"choices": []}

    class FakeAsyncClient:
        def __init__(self, *, timeout, headers):
            captured["headers"] = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json):
            captured["payload"] = json
            return Response()

    monkeypatch.setattr(boundary.httpx, "AsyncClient", FakeAsyncClient)
    proxy_client = LiteLLMClient(api_key=internal_key)
    await proxy_client.chat_completion(
        RouteDecision(deployment="deployment-a", provider="openai"),
        MESSAGES,
    )

    assert captured["headers"] == {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {internal_key}",
    }
    assert client_key not in repr(captured)
    assert internal_key not in repr(captured["payload"])
