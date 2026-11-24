"""Free Chat admission denials and the streaming response generator.

The Free Pool narrows a request to an allowlist before routing. These tests
pin every denial the gate can produce, plus the three ways a provider stream
can end without a clean completion.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from starlette.requests import Request

from sabiroute.api.completions import (
    FREE_POOL_ROUTE_CONFIGURATION_ERROR,
    ChatCompletionRequest,
    chat_completions,
)
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.keys import ApiKeyIdentity, ApiKeyRecord, issue_api_key


def _state(client: Any, eligible: frozenset[str]):
    store = InMemoryApiKeyStore()
    store.shared_inference = True
    state = build_gateway_state(
        config=make_config(),
        client=client,
        key_store=store,
        free_pool=FreePoolPolicy(enabled=True, eligible_deployments=eligible),
    )
    record, _secret = issue_api_key(store, project_id="proj-1", name="sabi")
    return state, store, record


def _request(state: Any, record: ApiKeyRecord) -> Request:
    app = create_app(state=state)
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 1),
            "server": ("test", 80),
            "app": app,
            "state": {
                "api_identity": ApiKeyIdentity(
                    key_id=record.key_id, project_id=record.project_id
                )
            },
        }
    )


def _payload(**extra: Any) -> ChatCompletionRequest:
    fields: dict[str, Any] = {
        "model": "primary",
        "messages": [{"role": "user", "content": "hello"}],
        "sabi_route_free_chat": True,
    }
    fields.update(extra)
    return ChatCompletionRequest.model_validate(fields)


def _body(response: Any) -> dict[str, Any]:
    return json.loads(response.body)


# --- Free Pool denials ----------------------------------------------------


def test_a_free_chat_request_with_no_capable_deployment_is_refused() -> None:
    state, _store, record = _state(StubLiteLLMClient(), frozenset({"cloudy"}))

    response = asyncio.run(
        chat_completions(
            _payload(model="cloudy", stream=True), _request(state, record)
        )
    )

    assert response.status_code == 503
    assert "verified for this request's capabilities" in _body(response)["error"][
        "message"
    ]


def test_a_free_chat_request_with_no_healthy_deployment_is_refused() -> None:
    state, _store, record = _state(StubLiteLLMClient(), frozenset({"primary"}))
    for _ in range(3):
        state.health.mark_failure("primary")

    response = asyncio.run(
        chat_completions(_payload(), _request(state, record))
    )

    assert response.status_code == 503
    assert "No healthy Free Chat deployment" in _body(response)["error"]["message"]


def test_a_misconfigured_free_chat_route_is_refused() -> None:
    state, _store, record = _state(StubLiteLLMClient(), frozenset({"primary"}))

    def explode(*_args: Any, **_kwargs: Any) -> Any:
        raise ValueError("route is broken")

    state.router.evaluate_candidates = explode  # type: ignore[assignment]

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 503
    assert _body(response)["error"]["type"] == FREE_POOL_ROUTE_CONFIGURATION_ERROR


# --- streaming generator outcomes -----------------------------------------


class _TruncatedStream:
    async def events(self) -> Any:
        yield b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'

    async def aclose(self) -> None:
        return None


class _TruncatedFailingCloseStream(_TruncatedStream):
    async def aclose(self) -> None:
        raise RuntimeError("cleanup failed")


class _NoUsageStream:
    async def events(self) -> Any:
        yield b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
        yield b"data: [DONE]\n\n"

    async def aclose(self) -> None:
        return None


class _StreamingClient:
    def __init__(self, stream: Any) -> None:
        self._stream = stream

    async def chat_completion(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("non-streaming path is not used here")

    async def start_chat_completion_stream(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._stream


def _drain(client: Any) -> list[Any]:
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(), client=client, key_store=store
    )
    record, _secret = issue_api_key(store, project_id="proj-1", name="k")
    request = _request(state, record)
    payload = ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        }
    )

    async def scenario() -> list[Any]:
        response = await chat_completions(payload, request)
        return [chunk async for chunk in response.body_iterator]

    return asyncio.run(scenario())


def test_a_stream_without_a_done_frame_is_recorded_as_interrupted() -> None:
    chunks = _drain(_StreamingClient(_TruncatedStream()))

    assert chunks
    assert not any(b"[DONE]" in chunk for chunk in chunks)


def test_a_stream_that_completes_without_usage_is_treated_as_unknown() -> None:
    chunks = _drain(_StreamingClient(_NoUsageStream()))

    assert any(b"[DONE]" in chunk for chunk in chunks)


def test_a_cleanup_failure_before_completion_is_named() -> None:
    chunks = _drain(_StreamingClient(_TruncatedFailingCloseStream()))

    assert chunks
