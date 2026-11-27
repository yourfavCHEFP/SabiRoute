"""Phase 1: trusted SabiChat identity propagation (no quotas, no charges).

Proves the gateway accepts a canonical user ID only on the authenticated
SabiChat service path, strips it everywhere else, never forwards it to
LiteLLM, and changes no routing/attribution behavior. Providers stubbed.
"""

from __future__ import annotations

import pytest
from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    enable_shared_inference,
    make_config,
    provision_test_key,
)
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.keys import SABI_USER_ID_FIELD, issue_api_key

MESSAGES = [{"role": "user", "content": "hello"}]
UID_A = "11111111-1111-4111-8111-111111111111"
UID_B = "22222222-2222-4222-8222-222222222222"


def make_service_state(stub, *, eligible=("primary",)):
    """Gateway state plus a provisioned SabiChat service credential.

    Mirrors exactly what ``SabiChatService`` establishes after issuance:
    the plaintext stays server-side and the key ID is published on state
    for the provenance check.
    """
    from sabiroute.freepool.eligibility import FreePoolPolicy

    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset(eligible))
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=store, free_pool=policy
    )
    record, plaintext = issue_api_key(
        store, project_id="sabichat-service", name="sabichat-service"
    )
    state.sabichat_service_key_id = record.key_id
    # Shared inference must be explicitly enabled for marked requests to
    # proceed; the kill-switch default-off behavior is asserted elsewhere.
    enable_shared_inference(state)
    return state, plaintext


def gateway_client(state, plaintext):
    app = create_app(state=state)
    return TestClient(app, headers={"Authorization": f"Bearer {plaintext}"})


def marked(model="primary", **extra):
    return {
        "model": model,
        "messages": MESSAGES,
        "sabi_route_free_chat": True,
        **extra,
    }


# --- AC-01 valid authenticated identity ------------------------------------


def test_service_identity_accepted_and_attested():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    client = gateway_client(state, plaintext)

    response = client.post(
        "/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: UID_A})
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-User"] == UID_A
    assert stub.calls == ["primary"]


def test_distinct_users_yield_distinct_identities():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    client = gateway_client(state, plaintext)

    first = client.post("/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: UID_A}))
    second = client.post("/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: UID_B}))

    assert first.headers["X-SabiRoute-User"] == UID_A
    assert second.headers["X-SabiRoute-User"] == UID_B


def test_concurrent_requests_keep_their_own_identity():
    import asyncio

    import httpx

    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    app = create_app(state=state)

    async def one(uid):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://internal"
        ) as async_client:
            return await async_client.post(
                "/v1/chat/completions",
                json=marked(**{SABI_USER_ID_FIELD: uid}),
                headers={"Authorization": f"Bearer {plaintext}"},
            )

    async def both():
        return await asyncio.gather(one(UID_A), one(UID_B))

    first, second = asyncio.run(both())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["X-SabiRoute-User"] == UID_A
    assert second.headers["X-SabiRoute-User"] == UID_B


# --- AC-02 spoof resistance --------------------------------------------------


def test_ordinary_key_forged_field_ignored():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    ordinary = provision_test_key(state)
    client = gateway_client(state, ordinary)

    response = client.post(
        "/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: "mallory"})
    )

    assert response.status_code == 200
    assert "X-SabiRoute-User" not in response.headers
    assert stub.calls == ["primary"]


def test_forged_headers_ignored():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    ordinary = provision_test_key(state)
    app = create_app(state=state)
    client = TestClient(
        app,
        headers={
            "Authorization": f"Bearer {ordinary}",
            "X-SabiChat-User": "mallory",
            "X-Sabi-User-Id": "mallory",
        },
    )

    response = client.post("/v1/chat/completions", json=marked())

    assert response.status_code == 200
    assert "X-SabiRoute-User" not in response.headers


def test_nested_metadata_spoof_ignored():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    ordinary = provision_test_key(state)
    client = gateway_client(state, ordinary)

    body = marked()
    body["metadata"] = {SABI_USER_ID_FIELD: "mallory"}
    body["extra_body"] = {SABI_USER_ID_FIELD: "mallory"}
    response = client.post("/v1/chat/completions", json=body)

    assert response.status_code == 200
    assert "X-SabiRoute-User" not in response.headers


def test_unmarked_service_request_ignores_field():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    client = gateway_client(state, plaintext)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, SABI_USER_ID_FIELD: UID_A},
    )

    assert response.status_code == 200
    assert "X-SabiRoute-User" not in response.headers


def test_unmarked_ordinary_request_ignores_field():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    ordinary = provision_test_key(state)
    client = gateway_client(state, ordinary)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, SABI_USER_ID_FIELD: UID_A},
    )

    assert response.status_code == 200
    assert "X-SabiRoute-User" not in response.headers


# --- AC-05 service-path integrity --------------------------------------------


def test_missing_field_on_service_path_rejected():
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    client = gateway_client(state, plaintext)

    response = client.post("/v1/chat/completions", json=marked())

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "internal_identity_error"
    assert stub.calls == []


@pytest.mark.parametrize("bad", ["", "x" * 129, 123, ["uid"], {"uid": 1}])
def test_invalid_field_on_service_path_rejected(bad):
    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    client = gateway_client(state, plaintext)

    response = client.post("/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: bad}))

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "internal_identity_error"
    assert stub.calls == []


def test_unauthenticated_gets_no_identity():
    stub = StubLiteLLMClient()
    state, _ = make_service_state(stub)
    app = create_app(state=state)
    client = TestClient(app)

    response = client.post("/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: UID_A}))

    assert response.status_code == 401
    assert "X-SabiRoute-User" not in response.headers
    assert stub.calls == []


# --- retry, provider boundary, attribution -------------------------------------


def test_retry_preserves_identity():
    stub = StubLiteLLMClient(failures={"primary": 1})
    state, plaintext = make_service_state(stub, eligible=("primary", "secondary"))
    client = gateway_client(state, plaintext)

    response = client.post(
        "/v1/chat/completions",
        json=marked(model="fast", **{SABI_USER_ID_FIELD: UID_A}),
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-User"] == UID_A
    assert stub.calls == ["primary", "secondary"]


class RecordingStub(StubLiteLLMClient):
    def __init__(self):
        super().__init__()
        self.forwarded: list[dict] = []

    async def chat_completion(self, decision, messages, **extra):
        self.forwarded.append(dict(extra))
        return await super().chat_completion(decision, messages, **extra)


def test_provider_payload_excludes_identity():
    stub = RecordingStub()
    state, plaintext = make_service_state(stub)
    client = gateway_client(state, plaintext)

    response = client.post("/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: UID_A}))

    assert response.status_code == 200
    assert stub.forwarded
    for kwargs in stub.forwarded:
        assert SABI_USER_ID_FIELD not in kwargs
        assert not any("user_id" in key for key in kwargs)


def test_usage_source_invariance(caplog):
    import logging

    stub = StubLiteLLMClient()
    state, plaintext = make_service_state(stub)
    ordinary = provision_test_key(state)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)

    with caplog.at_level(logging.INFO):
        forged = gateway_client(state, ordinary).post(
            "/v1/chat/completions", json=marked(**{SABI_USER_ID_FIELD: "mallory"})
        )
        assert forged.status_code == 200
        plain = gateway_client(state, ordinary).post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
        )
        assert plain.status_code == 200
    events = list(store.usage_events.values())
    assert sorted(event.usage_source for event in events) == ["free_pool", "unknown"]
    assert plaintext not in caplog.text


