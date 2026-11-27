"""Sprint 3: SabiChat backend — identity, sessions, ownership, gateway chat.

Conventions: stubbed LiteLLM execution (deterministic, no provider keys),
sqlite-file SabiChat persistence (real SQL), InMemory gateway key store.
Live PostgreSQL and live providers are NOT used here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, enable_shared_inference, make_config
from fastapi.testclient import TestClient

from sabiroute.api.chat import _PUBLIC_GATEWAY_MESSAGES, _public_gateway_error
from sabiroute.chat.passwords import (
    dummy_verify,
    hash_password,
    verify_password,
)
from sabiroute.chat.store import SabiChatStore, digest_token
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

PASSWORD = "correct-horse-battery-99"
MESSAGES = [{"role": "user", "content": "hello"}]


def make_chat_client(stub, tmp_path, *, eligible=("primary",)):
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset(eligible))
    chat_store = SabiChatStore(f"sqlite:///{tmp_path / 'chat.sqlite'}")
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
        chat_store=chat_store,
    )
    enable_shared_inference(state)
    app = create_app(state=state)
    return TestClient(app), state


def register(client, email="ada@example.com", password=PASSWORD):
    return client.post("/v1/auth/register", json={"email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def service_secret_absent(client, state, responses):
    """The server-held service key must never appear in API responses."""
    del state  # silence unused warning; responses carry the evidence
    for response in responses:
        assert "sr_live_" not in response.text


# --- authentication ------------------------------------------------------


def test_register_issues_session_and_stores_hash_not_plaintext(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)

    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["token"]
    expires = datetime.fromisoformat(body["expires_at"])
    assert timedelta(days=6) < expires - datetime.now(UTC) < timedelta(days=8)

    chat_store = state.chat_store
    assert isinstance(chat_store, SabiChatStore)
    user = chat_store.get_user_by_email("ada@example.com")
    assert user is not None
    assert user.password_hash.startswith("pbkdf2-sha256$")
    assert PASSWORD not in user.password_hash

    me = client.get("/v1/auth/me", headers=auth_headers(body["token"]))
    assert me.status_code == 200
    assert me.json()["user_id"] == body["user_id"]
    assert "token" not in me.json()
    assert "password_hash" not in me.text


def test_duplicate_registration_fails_generically(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    assert register(client).status_code == 201

    second = register(client)

    assert second.status_code == 400
    assert second.json()["detail"]["error"]["type"] == "registration_failed"
    assert "token" not in second.json()


def test_invalid_email_and_short_password_rejected(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)

    assert register(client, email="not-an-email").status_code == 400
    short = register(client, email="b@example.com", password="too-short")
    assert short.status_code == 400
    assert short.json()["detail"]["error"]["type"] == "invalid_password"


def test_login_round_trip_and_generic_failures(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    assert register(client).status_code == 201

    ok = client.post(
        "/v1/auth/login", json={"email": "ada@example.com", "password": PASSWORD}
    )
    assert ok.status_code == 200
    assert ok.json()["token"]

    unknown = client.post(
        "/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    wrong = client.post(
        "/v1/auth/login", json={"email": "ada@example.com", "password": "wrong-password-xyz"}
    )
    assert unknown.status_code == 401
    assert wrong.status_code == 401
    # Generic: identical shape whether the account exists or not.
    assert unknown.json() == wrong.json()
    assert unknown.json()["detail"]["error"]["type"] == "invalid_credentials"


def test_disabled_user_cannot_login(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)
    body = register(client).json()

    chat_store = state.chat_store
    assert isinstance(chat_store, SabiChatStore)
    assert chat_store.disable_user(body["user_id"]) is True

    denied = client.post(
        "/v1/auth/login", json={"email": "ada@example.com", "password": PASSWORD}
    )
    assert denied.status_code == 401
    assert denied.json()["detail"]["error"]["type"] == "invalid_credentials"


def test_auth_endpoints_resolve_password_executor(tmp_path):
    """The chat auth path resolves PBKDF2 work to password_executor."""
    from unittest.mock import patch

    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)

    seen: list[str] = []
    real_password_executor = state.password_executor
    real_store_executor = state.store_executor

    async def _spy_password_run(func, /, *args, **kwargs):
        seen.append(getattr(func, "__name__", type(func).__name__))
        return await real_password_executor.run(func, *args, **kwargs)

    async def _spy_store_run(func, /, *args, **kwargs):
        name = getattr(func, "__name__", type(func).__name__)
        assert name not in {"hash_password", "verify_password", "dummy_verify"}, (
            f"PBKDF2 helper {name} ran on the database executor"
        )
        return await real_store_executor.run(func, *args, **kwargs)

    with (
        patch.object(state, "password_executor", autospec=False),
        patch.object(state, "store_executor", autospec=False),
    ):
        state.password_executor.run = _spy_password_run  # type: ignore[method-assign]
        state.store_executor.run = _spy_store_run  # type: ignore[method-assign]
        assert register(client).status_code == 201
        assert "hash_password" in seen
        seen.clear()
        ok = client.post(
            "/v1/auth/login", json={"email": "ada@example.com", "password": PASSWORD}
        )
        assert ok.status_code == 200
        assert "verify_password" in seen
        seen.clear()
        unknown = client.post(
            "/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
        )
        assert unknown.status_code == 401
        assert "dummy_verify" in seen


def test_logout_revokes_session(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)

    assert client.post("/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/v1/auth/me", headers=headers).status_code == 401
    assert client.post("/v1/auth/logout", headers=headers).status_code == 401


def test_expired_session_rejected(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)
    body = register(client).json()

    chat_store = state.chat_store
    assert isinstance(chat_store, SabiChatStore)
    user = chat_store.get_user(body["user_id"])
    assert user is not None
    expired = chat_store.create_session(
        user.user_id, digest_token("expired-token"), datetime.now(UTC) - timedelta(seconds=1)
    )
    assert expired.expires_at <= datetime.now(UTC)

    response = client.get("/v1/auth/me", headers=auth_headers("expired-token"))
    assert response.status_code == 401


def test_malformed_credentials_rejected(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    register(client)

    assert client.get("/v1/auth/me").status_code == 401
    nonsense = client.get("/v1/auth/me", headers={"Authorization": "Bearer nonsense"})
    assert nonsense.status_code == 401
    assert client.get("/v1/auth/me", headers={"Authorization": "Token abc"}).status_code == 401


def test_auth_rate_limit(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)

    statuses = [
        register(client, email=f"user{i}@example.com").status_code for i in range(11)
    ]
    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429
    limited = register(client, email="user11@example.com")
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers


def test_password_primitives():
    stored = hash_password(PASSWORD)
    assert verify_password(PASSWORD, stored) is True
    assert verify_password("wrong-password-xyz", stored) is False
    assert verify_password(PASSWORD, "not-a-hash") is False
    assert verify_password(PASSWORD, "pbkdf2-sha256$abc$00$00") is False
    assert dummy_verify(PASSWORD) is None


# --- authorization -------------------------------------------------------


def test_unauthenticated_requests_denied(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)

    assert client.get("/v1/conversations").status_code == 401
    assert client.post("/v1/conversations", json={}).status_code == 401
    assert client.get("/v1/conversations/anything").status_code == 401
    assert (
        client.post(
            "/v1/conversations/anything/messages", json={"content": "hi hello world"}
        ).status_code
        == 401
    )
    assert stub.calls == []


def test_cross_user_conversations_isolated(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    token_a = register(client, email="a@example.com").json()["token"]
    token_b = register(client, email="b@example.com").json()["token"]

    created = client.post(
        "/v1/conversations", json={"title": "A private"}, headers=auth_headers(token_a)
    )
    assert created.status_code == 201
    conversation_id = created.json()["conversation_id"]

    assert (
        client.get(
            f"/v1/conversations/{conversation_id}", headers=auth_headers(token_b)
        ).status_code
        == 404
    )
    forbidden_post = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "intruder message here"},
        headers=auth_headers(token_b),
    )
    assert forbidden_post.status_code == 404
    assert stub.calls == []

    mine = client.get("/v1/conversations", headers=auth_headers(token_a)).json()
    theirs = client.get("/v1/conversations", headers=auth_headers(token_b)).json()
    assert mine["total"] == 1
    assert theirs["total"] == 0

    guessed = client.get(
        "/v1/conversations/00000000-0000-4000-8000-000000000000",
        headers=auth_headers(token_a),
    )
    assert guessed.status_code == 404
    assert guessed.json()["detail"]["error"]["type"] == "not_found"


def test_conversation_pagination_bounds(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)

    assert client.get("/v1/conversations?limit=0", headers=headers).status_code == 422
    assert client.get("/v1/conversations?limit=51", headers=headers).status_code == 422


# --- gateway integration -------------------------------------------------


def test_chat_success_persists_both_messages(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello there gateway", "model": "primary"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"]["content"] == "ok"
    assert body["deployment"] == "primary"
    assert stub.calls == ["primary"]
    service_secret_absent(client, state, [response])

    history = client.get(f"/v1/conversations/{conversation_id}", headers=headers).json()
    assert [item["role"] for item in history["messages"]] == ["user", "assistant"]
    assert history["messages"][1]["deployment"] == "primary"


def test_chat_default_model_routes(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello with default model"},
        headers=headers,
    )

    assert response.status_code == 200
    assert stub.calls[0] == "primary"


def test_chat_attributes_free_pool_usage(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )
    assert (
        client.post(
            f"/v1/conversations/{conversation_id}/messages",
            json={"content": "hello attribution check", "model": "primary"},
            headers=headers,
        ).status_code
        == 200
    )

    key_store = state.key_store
    assert isinstance(key_store, InMemoryApiKeyStore)
    (event,) = list(key_store.usage_events.values())
    assert event.usage_source == "free_pool"


def test_chat_free_pool_denial_mapped_and_recorded(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path, eligible=("primary",))
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello denied model", "model": "secondary"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["type"] == "free_pool_unmapped_deployment"
    assert stub.calls == []
    service_secret_absent(client, state, [response])

    history = client.get(f"/v1/conversations/{conversation_id}", headers=headers).json()
    assert [item["role"] for item in history["messages"]] == ["user", "assistant"]
    failed = history["messages"][1]
    assert failed["content"] == ""
    assert failed["error_type"] == "free_pool_unmapped_deployment"


def test_chat_gateway_failure_mapped_safely(tmp_path):
    stub = StubLiteLLMClient(failures={"primary": 5})
    client, state = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello failing provider", "model": "primary"},
        headers=headers,
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"]["type"] == "gateway_error"
    assert "primary" not in response.text
    service_secret_absent(client, state, [response])


def test_client_marker_cannot_influence_attribution(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )

    # Unknown fields are ignored: the server forces the marker itself.
    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={
            "content": "hello spoof attempt here",
            "model": "primary",
            "sabi_route_free_chat": False,
        },
        headers=headers,
    )

    assert response.status_code == 200
    key_store = state.key_store
    assert isinstance(key_store, InMemoryApiKeyStore)
    (event,) = list(key_store.usage_events.values())
    assert event.usage_source == "free_pool"


def test_invalid_message_content_never_reaches_gateway(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_chat_client(stub, tmp_path)
    token = register(client).json()["token"]
    headers = auth_headers(token)
    conversation_id = (
        client.post("/v1/conversations", json={}, headers=headers).json()["conversation_id"]
    )

    blank = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "   "},
        headers=headers,
    )
    assert blank.status_code == 400
    oversize = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "x" * 8001},
        headers=headers,
    )
    assert oversize.status_code == 422
    assert stub.calls == []


def test_public_gateway_error_mapping():
    for error_type in _PUBLIC_GATEWAY_MESSAGES:
        status, kind, message = _public_gateway_error(500, error_type)
        assert kind == error_type
        assert message
        # 400 is an established public status (see the generic fallback
        # below); mapped entries may use it for malformed requests.
        assert status in (400, 403, 429, 503)
    assert _public_gateway_error(418, "mystery")[0] == 502
    assert _public_gateway_error(404, "mystery")[0] == 404


def test_chat_unavailable_without_store(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    stub = StubLiteLLMClient()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=FreePoolPolicy(),
    )
    assert state.chat_store is None
    app = create_app(state=state)
    client = TestClient(app)

    response = client.post(
        "/v1/auth/register", json={"email": "a@example.com", "password": PASSWORD}
    )
    assert response.status_code == 503


# --- persistence ---------------------------------------------------------


def test_chat_tables_created_and_revision_recorded(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'sabichat.sqlite'}"
    store = SabiChatStore(database_url)
    try:
        from sabiroute.security.store import PostgresApiKeyStore as KeyStore

        key_store = KeyStore(database_url)
        try:
            assert key_store.applied_revisions()[:4] == [
                "0001-usage-source",
                "0002-sabichat-backend",
                "0003-shared-inference-switch",
                "0004-user-quota-ledger",
            ]
        finally:
            key_store.close()

        user = store.create_user("c@example.com", hash_password(PASSWORD))
        session = store.create_session(
            user.user_id, digest_token("tok"), datetime.now(UTC) + timedelta(days=1)
        )
        assert store.get_session(digest_token("tok")) == session
        conversation = store.create_conversation(user.user_id, " hello ")
        assert store.get_conversation(conversation.conversation_id, user.user_id) == conversation
        assert store.get_conversation(conversation.conversation_id, "someone-else") is None
        message = store.create_message(conversation.conversation_id, "user", "hi")
        assert store.list_messages(conversation.conversation_id, limit=10) == [message]
        assert store.purge_expired_sessions() == 0
        assert store.revoke_user_sessions(user.user_id) == 1
        assert store.get_session(digest_token("tok")) is not None
    finally:
        store.close()


def test_purge_expired_sessions(tmp_path):
    store = SabiChatStore(f"sqlite:///{tmp_path / 'purge.sqlite'}")
    try:
        user = store.create_user("d@example.com", hash_password(PASSWORD))
        store.create_session(
            user.user_id, digest_token("old"), datetime.now(UTC) - timedelta(hours=1)
        )
        store.create_session(
            user.user_id, digest_token("new"), datetime.now(UTC) + timedelta(days=1)
        )
        assert store.purge_expired_sessions() == 1
        assert store.get_session(digest_token("new")) is not None
        assert store.get_session(digest_token("old")) is None
    finally:
        store.close()


def test_the_store_requires_a_database_url() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL is required for SabiChat"):
        SabiChatStore("")
