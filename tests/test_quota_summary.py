"""Quota-summary endpoint: authenticated per-user daily Free Pool meter read.

Covers GET /v1/chat/quota-summary only. Quota admission/settlement behavior
is covered by tests/test_user_quotas.py; this file covers the read path.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.chat.store import SabiChatStore, digest_token
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.quotas import (
    DAILY_TOKEN_QUOTA,
    QuotaPolicy,
    quota_reset_at,
    quota_window_start,
)

PASSWORD = "correct-horse-battery-99"
SUMMARY_PATH = "/v1/chat/quota-summary"


def make_summary_client(stub, tmp_path, *, pilot=()):
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
    chat_store = SabiChatStore(f"sqlite:///{tmp_path / 'quota-summary.sqlite'}")
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
        chat_store=chat_store,
        quota_policy=QuotaPolicy(pilot_users=frozenset(pilot)),
    )
    app = create_app(state=state)
    return TestClient(app), state


def register(client, email="meter@example.com"):
    response = client.post(
        "/v1/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_enrolled_returns_aggregate_and_reset(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)
    state.quota_policy = QuotaPolicy(pilot_users=frozenset({body["user_id"]}))

    window = quota_window_start(datetime.now(UTC))
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    assert store.check_and_reserve_quota(body["user_id"], "r-1", 10000, window, 50000) is True
    store.settle_quota(body["user_id"], "r-1", 4000)

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 200
    payload = response.json()
    assert payload["enrolled"] is True
    assert payload["used_tokens"] == 4000
    assert payload["quota_tokens"] == DAILY_TOKEN_QUOTA == 50_000
    assert payload["remaining_tokens"] == 46_000
    assert payload["window_start"] == window.isoformat()
    assert payload["reset_at"] == quota_reset_at(window).isoformat()


def test_reserved_included_in_used(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)
    state.quota_policy = QuotaPolicy(pilot_users=frozenset({body["user_id"]}))

    window = quota_window_start(datetime.now(UTC))
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    assert store.check_and_reserve_quota(body["user_id"], "r-hold", 7000, window, 50000) is True
    # No settle: the 7000 stays reserved (in-flight).

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 200
    assert response.json()["used_tokens"] == 7000


def test_unenrolled_returns_only_enrolled_false(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_summary_client(stub, tmp_path)
    body = register(client)

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 200
    assert response.json() == {"enrolled": False}


def test_missing_policy_returns_503_quota_unavailable(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)
    state.quota_policy = None

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 503
    error = response.json()["detail"]["error"]
    assert error["type"] == "quota_unavailable"
    assert "reset_at" not in error


def test_spoofed_user_id_cannot_read_other(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    victim = register(client, email="victim@example.com")
    attacker = register(client, email="attacker@example.com")
    state.quota_policy = QuotaPolicy(
        pilot_users=frozenset({victim["user_id"], attacker["user_id"]})
    )

    window = quota_window_start(datetime.now(UTC))
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    assert store.check_and_reserve_quota(victim["user_id"], "r-v", 20000, window, 50000) is True
    store.settle_quota(victim["user_id"], "r-v", 20000)

    # Query/body user IDs are not part of the contract; even if supplied they
    # must be ignored and the caller's own aggregate returned.
    response = client.get(
        f"{SUMMARY_PATH}?user_id={victim['user_id']}",
        headers=auth_headers(attacker["token"]),
    )
    assert response.status_code == 200
    assert response.json()["used_tokens"] == 0

    response = client.request(
        "GET",
        SUMMARY_PATH,
        headers=auth_headers(attacker["token"]),
        json={"user_id": victim["user_id"]},
    )
    assert response.status_code == 200
    assert response.json()["used_tokens"] == 0


def test_unauthenticated_rejected(tmp_path):
    stub = StubLiteLLMClient()
    client, _ = make_summary_client(stub, tmp_path)

    assert client.get(SUMMARY_PATH).status_code == 401
    response = client.get(SUMMARY_PATH, headers={"Authorization": "Bearer nonsense"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["type"] == "invalid_session"


def test_expired_and_revoked_rejected(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)

    chat_store = state.chat_store
    assert isinstance(chat_store, SabiChatStore)
    chat_store.create_session(
        body["user_id"], digest_token("expired-token"), datetime.now(UTC) - timedelta(seconds=1)
    )
    assert client.get(SUMMARY_PATH, headers=auth_headers("expired-token")).status_code == 401

    assert client.post("/v1/auth/logout", headers=auth_headers(body["token"])).status_code == 200
    assert client.get(SUMMARY_PATH, headers=auth_headers(body["token"])).status_code == 401


def test_store_failure_returns_503_quota_unavailable(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)
    state.quota_policy = QuotaPolicy(pilot_users=frozenset({body["user_id"]}))

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_quota_reads = True

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 503
    error = response.json()["detail"]["error"]
    assert error["type"] == "quota_unavailable"
    assert "reset_at" not in error


def test_missing_row_returns_genuine_zero_summary(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)
    state.quota_policy = QuotaPolicy(pilot_users=frozenset({body["user_id"]}))

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 200
    payload = response.json()
    assert payload["enrolled"] is True
    assert payload["used_tokens"] == 0
    assert payload["remaining_tokens"] == 50_000


def test_midnight_boundary_selects_current_window(tmp_path):
    stub = StubLiteLLMClient()
    client, state = make_summary_client(stub, tmp_path)
    body = register(client)
    state.quota_policy = QuotaPolicy(pilot_users=frozenset({body["user_id"]}))

    now = datetime.now(UTC)
    today = quota_window_start(now)
    yesterday = today - timedelta(days=1)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    assert store.check_and_reserve_quota(body["user_id"], "r-old", 30000, yesterday, 50000) is True
    store.settle_quota(body["user_id"], "r-old", 30000)

    response = client.get(SUMMARY_PATH, headers=auth_headers(body["token"]))

    assert response.status_code == 200
    payload = response.json()
    assert payload["used_tokens"] == 0
    assert payload["window_start"] == today.isoformat()
    assert payload["reset_at"] == quota_reset_at(today).isoformat()
