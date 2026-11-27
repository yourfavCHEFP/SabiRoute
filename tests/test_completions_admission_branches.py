"""Admission denials and snapshot-failure exits in the completions handler.

Each test drives the real endpoint with a store double that answers one way
only, so the branch under test is the one that produces the response. The
store contract is the subject: a reservation that reports a changed budget or
unknown pricing must become a typed denial, not a silent admission.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from starlette.requests import Request

from sabiroute.api import completions as completions_module
from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.keys import ApiKeyBudget, ApiKeyIdentity, ApiKeyRecord, issue_api_key


def _harness(store: Any = None, client: Any = None) -> tuple[Any, Any, ApiKeyRecord]:
    store = store if store is not None else InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=client or StubLiteLLMClient(),
        key_store=store,
    )
    record, _secret = issue_api_key(store, project_id="proj-1", name="key")
    return state, store, record


def _request(state: Any, record: ApiKeyRecord) -> Request:
    app = create_app(state=state)
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
            "app": app,
            "state": {
                "api_identity": ApiKeyIdentity(key_id=record.key_id, project_id=record.project_id)
            },
        }
    )


def _payload(**extra: Any) -> ChatCompletionRequest:
    fields: dict[str, Any] = {
        "model": "primary",
        "messages": [{"role": "user", "content": "hello"}],
    }
    fields.update(extra)
    return ChatCompletionRequest.model_validate(fields)


def _body(response: Any) -> dict[str, Any]:
    return json.loads(response.body)


class _ChangedBudgetStore(InMemoryApiKeyStore):
    def reserve_budget(self, *_args: Any, **_kwargs: Any) -> str:
        return "budget_changed"


class _PricingUnknownStore(InMemoryApiKeyStore):
    def reserve_budget(self, *_args: Any, **_kwargs: Any) -> str:
        return "daily_pricing_unknown"


class _EmptyStream:
    async def events(self) -> Any:
        if False:  # pragma: no cover - unreachable, keeps this a generator
            yield b""

    async def aclose(self) -> None:
        return None


class _ExplodingStream:
    async def events(self) -> Any:
        raise RuntimeError("stream exploded")
        yield b""  # pragma: no cover - unreachable, makes this a generator

    async def aclose(self) -> None:
        return None


class _EmptyStreamClient:
    async def chat_completion(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("non-streaming path is not used here")

    async def start_chat_completion_stream(self, *_args: Any, **_kwargs: Any) -> Any:
        return _EmptyStream()


class _ExplodingStreamClient:
    async def chat_completion(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("non-streaming path is not used here")

    async def start_chat_completion_stream(self, *_args: Any, **_kwargs: Any) -> Any:
        return _ExplodingStream()


# --- budget admission -----------------------------------------------------


def test_a_budgeted_request_with_an_unestimable_parameter_is_refused() -> None:
    state, store, record = _harness()
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    response = asyncio.run(
        chat_completions(_payload(max_tokens=16, seed=7), _request(state, record))
    )

    assert response.status_code == 400
    assert _body(response)["error"]["type"] == "budget_request_unsupported"


def test_a_budget_change_during_admission_is_reported() -> None:
    state, store, record = _harness(store=_ChangedBudgetStore())
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    response = asyncio.run(chat_completions(_payload(max_tokens=16), _request(state, record)))

    assert response.status_code == 503
    assert _body(response)["error"]["message"] == ("Budget configuration changed during admission.")


def test_unknown_pricing_during_admission_is_reported() -> None:
    state, store, record = _harness(store=_PricingUnknownStore())
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    response = asyncio.run(chat_completions(_payload(max_tokens=16), _request(state, record)))

    assert response.status_code == 503
    assert _body(response)["error"]["type"] == "budget_pricing_unavailable"


# --- snapshot failures ----------------------------------------------------


def test_a_snapshot_that_cannot_be_built_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _store, record = _harness()

    def explode(**_kwargs: Any) -> Any:
        raise RuntimeError("cannot build")

    monkeypatch.setattr(completions_module, "make_pre_routing_snapshot", explode)

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 500
    assert _body(response)["error"]["type"] == "telemetry_integrity_error"


def test_a_snapshot_rejected_by_validation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sabiroute.security.keys import UsageEventValidationError

    state, _store, record = _harness()

    def reject(**_kwargs: Any) -> Any:
        raise UsageEventValidationError("invalid snapshot")

    monkeypatch.setattr(completions_module, "make_pre_routing_snapshot", reject)

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 500
    assert _body(response)["error"]["type"] == "telemetry_integrity_error"


def test_a_snapshot_the_store_refuses_stops_before_execution() -> None:
    state, store, record = _harness()
    store.append_pre_routing_feature_snapshot = lambda *_a, **_k: False  # type: ignore[assignment]

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 503
    assert _body(response)["error"]["type"] == "telemetry_store_unavailable"
    assert state.client.calls == []


# --- stream setup failures ------------------------------------------------


def test_a_stream_that_ends_before_its_first_event_fails_closed() -> None:
    state, _store, record = _harness(client=_EmptyStreamClient())

    response = asyncio.run(chat_completions(_payload(stream=True), _request(state, record)))

    assert response.status_code == 502
    assert _body(response)["error"]["type"] == "sabiroute_upstream_error"


def test_a_stream_that_fails_before_its_first_event_fails_closed() -> None:
    state, _store, record = _harness(client=_ExplodingStreamClient())

    response = asyncio.run(chat_completions(_payload(stream=True), _request(state, record)))

    assert response.status_code == 502
    assert _body(response)["error"]["type"] == "sabiroute_upstream_error"


class _UnreadableLimitStore(InMemoryApiKeyStore):
    def get_rate_limit(self, _key_id: str) -> Any:
        raise RuntimeError("rate-limit store lost")


def test_an_unreadable_rate_limit_fails_closed_before_execution() -> None:
    state, _store, record = _harness(store=_UnreadableLimitStore())

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 503
    assert _body(response)["error"]["type"] == "rate_limit_unavailable"


def test_a_snapshot_the_store_rejects_as_invalid_fails_closed() -> None:
    from sabiroute.security.keys import UsageEventValidationError

    state, store, record = _harness()

    def reject(*_args: Any, **_kwargs: Any) -> Any:
        raise UsageEventValidationError("snapshot rejected")

    store.append_pre_routing_feature_snapshot = reject  # type: ignore[assignment]

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 500
    assert _body(response)["error"]["type"] == "telemetry_integrity_error"


def test_a_usage_event_the_store_rejects_at_finalization_is_reported() -> None:
    from sabiroute.security.keys import UsageEventValidationError

    state, store, record = _harness()

    def reject(*_args: Any, **_kwargs: Any) -> Any:
        raise UsageEventValidationError("event rejected")

    store.finalize_usage_event = reject  # type: ignore[assignment]

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 500
    assert _body(response)["error"]["type"] == "telemetry_integrity_error"


def test_a_quota_settlement_failure_is_reported() -> None:
    from conftest import _make_free_chat_payload, _make_quota_and_budget_harness

    state, store, _stub, key_id, uid = _make_quota_and_budget_harness()

    def fail(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("settlement lost")

    store.settle_quota = fail  # type: ignore[assignment]
    record = store.records[key_id]
    payload = _make_free_chat_payload(uid)

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 503
    assert _body(response)["error"]["message"] == (
        "Quota reservation could not be reconciled."
    )
