"""Chat outer/inner timeout precedence (P1-C, deterministic, offline).

Proves the effective timeout layering when the outer SabiChat gateway
call reaches the inner in-process completions request:

- The outer ``INTERNAL_TIMEOUT_SECONDS`` (120.0, asserted unchanged)
  does **not** bound the in-process ASGI call: probed offline with the
  installed httpx 0.28.1, ``httpx.Timeout(0.3)`` did not interrupt a
  hanging ``ASGITransport`` app within 30s. The inner completions
  deadline is therefore the effective bound for a hung provider reached
  through chat. (Observed consequence, mapping unchanged:
  ``ChatUpstreamTimeout`` / 504 ``gateway_timeout`` is unreachable for
  hangs on this path; it remains the mapping for genuine httpx
  timeouts and transport errors.)
- An expired inner deadline budget surfaces through the public gateway
  mapping as 503 ``gateway_error``, persists an assistant message
  carrying that public type, starts zero upstream attempts, and
  finalizes inner telemetry as ``deadline_exceeded`` (never fabricated
  success, never attributed to provider health).
- A fast upstream failure keeps its own mapping (502 ``gateway_error``)
  with a ``server`` inner classification — proving the timeout mapping
  is specific to timeouts.

Hang-vs-timeout races are deliberately not asserted: with one shared
middleware stack the outer and inner budgets differ by microseconds, so
a hanging stub under a short shared deadline would race by
epsilon. The flag-clock gate test below determines the inner outcome
without any race or sleep.

Controlled fixtures only: flag-controlled gate clock, fast-failing (or
idle) stubs, sqlite-file chat persistence, in-memory gateway store. No
real waits at production durations, no providers, no network.
"""

from __future__ import annotations

import time

import pytest
from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    enable_shared_inference,
    make_config,
)
from fastapi.testclient import TestClient

import sabiroute.api.chat as chat_module
from sabiroute.chat.store import SabiChatStore
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app


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


def register_and_conversation(client):
    response = client.post(
        "/v1/auth/register",
        json={"email": "ada@example.com", "password": "correct-horse-battery-99"},
    )
    assert response.status_code == 201
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/v1/conversations", json={}, headers=headers)
    assert response.status_code == 201
    return headers, response.json()["conversation_id"]


def _install_past_gate_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expire the completions gate clock while keeping the loop clock real.

    Same verified constraint as the deadline gate tests: this
    environment's event-loop clock delegates to ``time.monotonic``, so
    the loop clock is pinned to the real reading (normal semantics)
    while gate-visible ``time.monotonic`` reports past-deadline. The
    outer chat path never reads this clock, so only the inner
    completions gate is affected — deterministically, with no sleeps.
    """
    import asyncio as _asyncio

    original = time.monotonic
    monkeypatch.setattr(_asyncio.BaseEventLoop, "time", lambda self: original())
    monkeypatch.setattr(time, "monotonic", lambda: original() + 3600.0)


def test_inner_deadline_expiry_maps_through_chat(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """An expired inner budget maps through chat without upstream work."""
    # The outer timeout value is asserted, never changed by this task.
    assert chat_module.INTERNAL_TIMEOUT_SECONDS == 120.0
    _install_past_gate_clock(monkeypatch)

    stub = StubLiteLLMClient()
    client, state = make_chat_client(stub, tmp_path)
    headers, conversation_id = register_and_conversation(client)

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello world, please respond"},
        headers=headers,
    )

    # 1 + 2. The inner gate expiry (503 deadline_exceeded) is not a mapped
    # message, so the public gateway mapping yields 503 gateway_error
    # (verified in _public_gateway_error: unmapped 503 stays
    # 503/gateway_error). No upstream attempt begins.
    assert response.status_code == 503
    assert response.json()["detail"]["error"]["type"] == "gateway_error"
    assert stub.calls == []

    # 3. An assistant message is persisted carrying the public error type.
    chat_store = state.chat_store
    assert isinstance(chat_store, SabiChatStore)
    history = chat_store.list_messages(conversation_id, limit=10)
    assistant_rows = [m for m in history if m.role == "assistant"]
    assert assistant_rows, "expected a persisted assistant message on timeout"
    assert assistant_rows[-1].content == ""
    assert assistant_rows[-1].error_type == "gateway_error"

    # 4 + 5. Inner telemetry records the deadline expiry with zero
    # decisions (not success, not provider failure, not caller
    # cancellation): the inner request completes before the outer
    # returns, so no polling is needed. Health is untouched.
    key_store = state.key_store
    assert isinstance(key_store, InMemoryApiKeyStore)
    event = next(iter(key_store.usage_events.values()))
    assert event.final_status == 503
    assert event.failure_category == "deadline_exceeded"
    assert list(event.routing_decisions) == []
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["healthy"] is True
    assert key_store.finalize_calls == 1


def test_upstream_failure_maps_distinctly_from_timeout(tmp_path) -> None:
    """Fast upstream failure is a 502 gateway_error, not a timeout.

    Companion to the precedence test: proves the timeout mapping above
    is specific to timeouts by showing the transport/upstream path keeps
    its own status, error code, persisted marker, and inner
    ``server`` classification. (The chat Free Pool gate narrows inner
    candidates to the eligible allowlist, so only ``primary`` is
    attempted here.)
    """
    stub = StubLiteLLMClient(failures={"primary": 1}, failure_status=500)
    client, state = make_chat_client(stub, tmp_path)
    headers, conversation_id = register_and_conversation(client)

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello world, please respond"},
        headers=headers,
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"]["type"] == "gateway_error"
    assert stub.calls == ["primary"]

    chat_store = state.chat_store
    assert isinstance(chat_store, SabiChatStore)
    history = chat_store.list_messages(conversation_id, limit=10)
    assistant_rows = [m for m in history if m.role == "assistant"]
    assert assistant_rows, "expected a persisted assistant message on failure"
    assert assistant_rows[-1].error_type == "gateway_error"

    key_store = state.key_store
    assert isinstance(key_store, InMemoryApiKeyStore)
    event = next(iter(key_store.usage_events.values()))
    assert event.final_status == 502
    assert event.failure_category == "server"
    assert [d["outcome"] for d in event.routing_decisions] == ["failure"]
