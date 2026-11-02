"""R3 — BYOK-0 provider-identity boundary (regression suite).

Owner decision D-R3-1: caller-supplied provider credentials and provider
identity are not legitimate in this deployment model. The gateway owns
provider credentials. Probing fields must be **rejected explicitly** — not
silently stripped, not forwarded, and never able to reach the provider.

Owner decision D-R3-2: the boundary must behave identically for budgeted and
unbudgeted requests, streaming and non-streaming, and on retry/fallback paths.

This file exists because the original guard compared raw lowercased keys with
only ``-`` and ``_`` removed, so ``api.key``, ``"api key"``, ``"api_key "``,
``"\\tapi_key"`` and nested containers (``litellm_params``, ``extra_body``,
``kwargs``) were admitted with HTTP 200 and forwarded verbatim into the
outbound LiteLLM request body (see tests marked "regression").

Labels: VERIFIED BY RUNTIME (fresh local run, stub provider, no real calls).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClientError
from sabiroute.security.keys import ApiKeyBudget

MESSAGES = [{"role": "user", "content": "hello"}]

#: Distinctive marker so a leak is unmistakable in payload/response scans.
SECRET = "sk-R3-CANARY-9f3ab7"

#: Every shape a caller could use to try to supply provider credentials or
#: provider identity. Keys are the attacker's spelling; values are the probe.
FORBIDDEN_VARIANTS: dict[str, dict[str, Any]] = {
    # Canonical spellings.
    "api_key": {"api_key": SECRET},
    "api_base": {"api_base": "http://attacker.invalid"},
    "authorization": {"authorization": f"Bearer {SECRET}"},
    # Case / separator variants the original guard already caught.
    "API_KEY": {"API_KEY": SECRET},
    "ApiKey": {"ApiKey": SECRET},
    "Api-Key": {"Api-Key": SECRET},
    "Api_Key": {"Api_Key": SECRET},
    # Separator variants the original guard MISSED (regression).
    "api.key": {"api.key": SECRET},
    "api key": {"api key": SECRET},
    "api_key trailing space": {"api_key ": SECRET},
    "api_key leading space": {" api_key": SECRET},
    "api_key leading tab": {"\tapi_key": SECRET},
    "api‐key unicode hyphen": {"api‐key": SECRET},
    "author ization spaced": {"author ization": f"Bearer {SECRET}"},
    # Nested containers — a real LiteLLM call parameter shape (regression).
    "nested litellm_params": {"litellm_params": {"api_key": SECRET}},
    "nested extra_body": {"extra_body": {"api_key": SECRET}},
    "nested kwargs": {"kwargs": {"api_key": SECRET}},
    "nested extra_body api_base": {"extra_body": {"api_base": "http://attacker.invalid"}},
    "deeply nested": {"extra_body": {"outer": {"inner": {"api_key": SECRET}}}},
    "nested in list": {"extra_body": [{"api_key": SECRET}]},
    "nested authorization": {"litellm_params": {"authorization": f"Bearer {SECRET}"}},
}


class RecordingStub:
    """Provider double that records every kwarg forwarded to the provider.

    ``calls`` records one entry per attempted provider invocation so a
    rejected request can be proven to have made **zero** attempts.
    """

    def __init__(self, failures: int = 0) -> None:
        self.calls: list[str] = []
        self.forwarded: list[dict[str, Any]] = []
        #: The ``messages`` sequence as the client would serialize it. Recorded
        #: because message dicts travel to the provider verbatim
        #: (``litellm_client.chat_completion`` builds ``"messages": list(messages)``),
        #: so a credential key nested inside one is a credential channel.
        self.forwarded_messages: list[Any] = []
        self.failures_remaining = failures

    def _record(self, decision: Any, extra: dict[str, Any]) -> None:
        self.calls.append(decision.deployment)
        self.forwarded.append(dict(extra))
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise LiteLLMClientError("stub failure", status_code=500)

    async def chat_completion(
        self, decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        self.forwarded_messages.append(messages)
        self._record(decision, extra)
        return {
            "id": "chatcmpl-stub",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    async def start_chat_completion_stream(
        self, decision: Any, messages: Any, **extra: Any
    ) -> Any:
        self.forwarded_messages.append(messages)
        self._record(decision, extra)
        raise AssertionError("stream stub not used by rejection tests")


def make_client(
    *, stub: RecordingStub | None = None, budget: bool = False
) -> tuple[TestClient, Any, RecordingStub]:
    stub = stub or RecordingStub()
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    if budget:
        store = state.key_store
        # The store exposes ``records``; assert the precondition so a renamed
        # attribute can never silently turn this into an unbudgeted test.
        records = store.records
        assert records, "budget fixture requires at least one provisioned key"
        for record in records.values():
            store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1_000))
        assert store.budgets, "budget was not actually applied"
    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {key}"}
    )
    return client, state, stub


def _body(**extra: Any) -> dict[str, Any]:
    return {"model": "fast", "messages": MESSAGES, **extra}


def _assert_rejected(resp: Any, stub: RecordingStub, state: Any) -> None:
    """The full hard-deny contract, asserted in one place."""
    assert resp.status_code == 400, f"expected hard reject, got {resp.status_code}"
    assert resp.json()["error"]["type"] == "invalid_request_error"
    # D-R3-3: the probe value must never be echoed back.
    assert SECRET not in resp.text
    assert "attacker.invalid" not in resp.text
    # No provider invocation, no accounting, no reservation.
    assert stub.calls == [], "forbidden request reached the provider"
    assert stub.forwarded == [], "forbidden fields were forwarded to provider payload"
    store = state.key_store
    if isinstance(store, InMemoryApiKeyStore):
        assert store.usage_events == {}, "rejected request wrote a usage row"
        assert store.budget_usage == {}, "rejected request reserved budget"
        assert store.quota_reservations == {}, "rejected request took a rate/quota token"


@pytest.mark.parametrize("name", sorted(FORBIDDEN_VARIANTS))
def test_forbidden_provider_field_is_rejected_in_every_spelling(name: str) -> None:
    """Every spelling/nesting of a provider-credential field is hard-denied."""
    client, state, stub = make_client()
    resp = client.post("/v1/chat/completions", json=_body(**FORBIDDEN_VARIANTS[name]))
    _assert_rejected(resp, stub, state)


@pytest.mark.parametrize(
    "name",
    [
        "api.key",
        "api key",
        "api_key trailing space",
        "nested extra_body",
        "nested litellm_params",
    ],
)
def test_regression_separator_and_nesting_bypass_is_closed(name: str) -> None:
    """Regression for the confirmed bypass: these returned 200 and forwarded.

    Before the fix these shapes reached ``RecordingStub.forwarded`` verbatim,
    i.e. the caller's secret would have been placed in the outbound LiteLLM
    request body.
    """
    client, state, stub = make_client()
    resp = client.post("/v1/chat/completions", json=_body(**FORBIDDEN_VARIANTS[name]))
    assert resp.status_code == 400
    assert stub.forwarded == []


def test_valid_request_still_succeeds() -> None:
    client, state, stub = make_client()
    resp = client.post("/v1/chat/completions", json=_body())
    assert resp.status_code == 200
    assert stub.calls  # provider was reached for legitimate traffic


def test_unrelated_extra_field_still_forwarded_for_unbudgeted() -> None:
    """Guard must reject credential fields, not all passthrough fields.

    OpenAI-compatible passthrough of benign extras is an existing contract;
    the fix must not collaterally forbid it.
    """
    client, state, stub = make_client()
    resp = client.post("/v1/chat/completions", json=_body(top_p=0.5))
    assert resp.status_code == 200
    assert stub.forwarded and stub.forwarded[0].get("top_p") == 0.5


def test_streaming_request_rejected_before_stream_open() -> None:
    client, state, stub = make_client()
    resp = client.post(
        "/v1/chat/completions",
        json=_body(stream=True, **FORBIDDEN_VARIANTS["nested extra_body"]),
    )
    assert resp.status_code == 400
    assert stub.calls == []


def test_retry_and_fallback_paths_never_attempted() -> None:
    """D-R3-2: the boundary is enforced before the attempt loop.

    Stub is primed to fail so any attempt would be visible as a provider call
    or a fallback walk; a correct guard makes zero attempts.
    """
    client, state, stub = make_client(stub=RecordingStub(failures=5))
    resp = client.post(
        "/v1/chat/completions", json=_body(**FORBIDDEN_VARIANTS["api.key"])
    )
    assert resp.status_code == 400
    assert stub.calls == [], "guard must run before any retry/fallback attempt"


@pytest.mark.parametrize("field", ["api_key", "api.key", "nested extra_body"])
def test_budgeted_request_rejected(field: str) -> None:
    """D-R3-2: budgeted requests hit the same boundary."""
    client, state, stub = make_client(budget=True)
    resp = client.post("/v1/chat/completions", json=_body(**FORBIDDEN_VARIANTS[field]))
    assert resp.status_code == 400
    assert stub.calls == []


def test_forbidden_field_absent_from_outbound_payload_on_valid_request() -> None:
    """Belt-and-braces: a normal request forwards no credential-shaped key."""
    client, state, stub = make_client()
    resp = client.post("/v1/chat/completions", json=_body(top_p=0.2))
    assert resp.status_code == 200
    blob = json.dumps(stub.forwarded).lower()
    for needle in ("api_key", "api_base", "authorization", SECRET.lower()):
        assert needle not in blob


# ---------------------------------------------------------------------------
# Message-object credential channel (regression).
#
# The guard scanned ``payload.model_extra`` only. ``messages`` is typed
# ``list[dict[str, Any]]`` and is forwarded as ``"messages": list(messages)``
# in ``LiteLLMClient.chat_completion`` / ``start_chat_completion_stream``, so
# any key a caller adds to a message object is serialized into the outbound
# LiteLLM body exactly like a top-level extra. A credential placed there
# therefore had the same reach as one under ``extra_body``, but was never
# scanned. These cases pin the boundary over the whole request body.
# ---------------------------------------------------------------------------

#: Forbidden keys nested inside a message object rather than at the top level.
MESSAGE_NESTED_VARIANTS: dict[str, dict[str, Any]] = {
    "message api_key": {"role": "user", "content": "hello", "api_key": SECRET},
    "message api.key": {"role": "user", "content": "hello", "api.key": SECRET},
    "message API-KEY": {"role": "user", "content": "hello", "API-KEY": SECRET},
    "message api_base": {
        "role": "user",
        "content": "hello",
        "api_base": "http://attacker.invalid",
    },
    "message authorization": {
        "role": "user",
        "content": "hello",
        "authorization": f"Bearer {SECRET}",
    },
    "message provider": {"role": "user", "content": "hello", "provider": "openai"},
    "message nested mapping": {
        "role": "user",
        "content": "hello",
        "metadata": {"litellm_params": {"api_key": SECRET}},
    },
    "message multimodal part": {
        "role": "user",
        "content": [{"type": "text", "text": "hi", "api_key": SECRET}],
    },
    "second message": None,  # filled below: forbidden key in the second turn
}

_second_turn = {
    "role": "user",
    "content": "hello",
    "api_key": SECRET,
}
MESSAGE_NESTED_VARIANTS["second message"] = _second_turn


def _body_with_message(message: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {"model": "fast", "messages": [{"role": "system", "content": "s"}, message], **extra}


@pytest.mark.parametrize("name", sorted(MESSAGE_NESTED_VARIANTS))
def test_forbidden_field_nested_in_message_is_rejected(name: str) -> None:
    """D-R3-1: a credential key inside a message object is the same probe.

    Oracle is the provider boundary, not the status code alone: the stub must
    record zero invocations and no forwarded message sequence.
    """
    client, state, stub = make_client()
    resp = client.post(
        "/v1/chat/completions", json=_body_with_message(MESSAGE_NESTED_VARIANTS[name])
    )
    _assert_rejected(resp, stub, state)
    assert stub.forwarded_messages == [], "message body reached the provider"


@pytest.mark.parametrize("name", ["message api_key", "message nested mapping"])
def test_message_nested_field_rejected_on_streaming(name: str) -> None:
    """D-R3-2: streaming hits the same boundary, before the stream opens."""
    client, state, stub = make_client()
    resp = client.post(
        "/v1/chat/completions",
        json=_body_with_message(MESSAGE_NESTED_VARIANTS[name], stream=True),
    )
    assert resp.status_code == 400
    assert stub.calls == []
    assert stub.forwarded_messages == []


@pytest.mark.parametrize("name", ["message api_key", "message provider"])
def test_message_nested_field_rejected_on_budgeted_request(name: str) -> None:
    """D-R3-2: budgeted requests hit the same boundary."""
    client, state, stub = make_client(budget=True)
    resp = client.post(
        "/v1/chat/completions", json=_body_with_message(MESSAGE_NESTED_VARIANTS[name])
    )
    assert resp.status_code == 400
    assert stub.calls == []


def _wrap(value: Any, levels: int) -> Any:
    """Nest ``value`` under ``levels`` single-key mappings."""
    for index in range(levels):
        value = {f"layer{index}": value}
    return value


@pytest.mark.parametrize("levels", [1, 3, 5, 6, 7, 9])
def test_nesting_depth_cannot_evade_the_guard(levels: int) -> None:
    """A depth bound must fail *closed*, not open.

    ``_FORBIDDEN_SCAN_MAX_DEPTH`` exists so a hostile body cannot force an
    expensive walk. The original implementation returned ``False`` on
    exceeding it, which turned the bound itself into a bypass: wrapping the
    credential in enough mappings let it through unscanned while it was still
    serialized into the outbound provider body.
    """
    client, state, stub = make_client()
    resp = client.post(
        "/v1/chat/completions",
        json=_body(extra_body=_wrap({"api_key": SECRET}, levels)),
    )
    assert resp.status_code == 400, f"depth {levels} evaded the guard"
    assert stub.calls == []
    assert stub.forwarded == []
    assert SECRET not in resp.text


def test_message_content_discussing_api_keys_is_not_rejected() -> None:
    """Non-over-correction: only mapping *keys* are denied, never content.

    A prompt that talks about API keys, or a tool name containing the word,
    must pass — otherwise the fix would break ordinary use. This test fails
    if the boundary is ever widened to scan string values.
    """
    client, state, stub = make_client()
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "fast",
            "messages": [
                {
                    "role": "user",
                    "content": "How do I rotate an api_key and set authorization headers?",
                    "name": "provider_advisor",
                }
            ],
        },
    )
    assert resp.status_code == 200
    assert stub.calls, "legitimate request must still reach the provider"
