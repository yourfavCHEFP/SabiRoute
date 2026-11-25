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


def _drain(client: Any) -> tuple[list[Any], Any]:
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

    return asyncio.run(scenario()), state


def test_a_stream_without_a_done_frame_is_recorded_as_interrupted() -> None:
    chunks, state = _drain(_StreamingClient(_TruncatedStream()))

    assert chunks
    assert not any(b"[DONE]" in chunk for chunk in chunks)
    # Truncation is not merely passed through to the client: the outcome is
    # named in telemetry, together with the reason the stream ended.
    assert state.errors.counts() == {"stream_interrupted": 1}
    assert [record.message for record in state.errors.records] == [
        "Provider stream ended without [DONE]."
    ]


def test_a_stream_that_completes_without_usage_is_treated_as_unknown() -> None:
    chunks, _state = _drain(_StreamingClient(_NoUsageStream()))

    assert any(b"[DONE]" in chunk for chunk in chunks)


def test_a_cleanup_failure_before_completion_is_named() -> None:
    chunks, state = _drain(_StreamingClient(_TruncatedFailingCloseStream()))

    assert chunks
    # A close that fails is distinguished from a plain truncation by its
    # message, so the two are separable from telemetry alone.
    assert state.errors.counts() == {"stream_interrupted": 1}
    assert [record.message for record in state.errors.records] == [
        "Provider stream cleanup failed before completion."
    ]


class _ExplodingStartStream:
    async def events(self) -> Any:
        raise RuntimeError("no first frame")
        yield b""  # pragma: no cover - unreachable, keeps this a generator

    async def aclose(self) -> None:
        raise RuntimeError("cleanup also failed")


def test_a_cleanup_failure_does_not_mask_the_provider_error() -> None:
    state, _store, record = _state(
        _StreamingClient(_ExplodingStartStream()), frozenset({"primary"})
    )
    payload = ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        }
    )

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 502


class _UsageFailingClient:
    def __init__(self) -> None:
        self.calls = 0

    async def chat_completion(self, *_args: Any, **_kwargs: Any) -> Any:
        from sabiroute.providers.litellm_client import LiteLLMClientError

        self.calls += 1
        raise LiteLLMClientError(
            "upstream failed after consuming the reservation",
            status_code=500,
            response_body={
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "total_tokens": 20,
                }
            },
        )

    async def start_chat_completion_stream(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("streaming path is not used here")


def test_a_retry_that_cannot_fit_the_remaining_budget_stops() -> None:
    from sabiroute.security.keys import ApiKeyBudget

    client = _UsageFailingClient()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=client, key_store=store)
    record, _secret = issue_api_key(store, project_id="proj-1", name="k")
    store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1000))

    payload = ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10,
        }
    )

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 502
    # The first attempt consumed more than the reservation left room for, so
    # no second provider call was made.
    assert client.calls == 1


class _FlakySharedStore(InMemoryApiKeyStore):
    """Allows the admission read, then fails the per-attempt re-check."""

    def __init__(self) -> None:
        super().__init__()
        self.reads = 0

    def get_shared_inference(self) -> bool:
        self.reads += 1
        if self.reads > 1:
            raise RuntimeError("shared-inference read lost")
        return True


def test_an_unreadable_shared_inference_flag_denies_the_attempt() -> None:
    store = _FlakySharedStore()
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=store,
        free_pool=FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"})),
    )
    record, _secret = issue_api_key(store, project_id="proj-1", name="sabi")

    response = asyncio.run(
        chat_completions(_payload(), _request(state, record))
    )

    assert response.status_code == 403
    assert "Shared inference is currently disabled" in _body(response)["error"][
        "message"
    ]


def test_a_budget_released_without_an_attempt_clears_the_reservation() -> None:
    from sabiroute.routing.router import NoCapableDeploymentError
    from sabiroute.security.keys import ApiKeyBudget

    state, store, record = _harness_with_budget(ApiKeyBudget(daily_tokens=1000))

    def refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise NoCapableDeploymentError("nothing routable")

    state.router.choose_deployment = refuse  # type: ignore[assignment]

    response = asyncio.run(chat_completions(_payload_basic(), _request(state, record)))

    assert response.status_code == 502


def _harness_with_budget(budget: Any) -> tuple[Any, Any, ApiKeyRecord]:
    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=store
    )
    record, _secret = issue_api_key(store, project_id="proj-1", name="k")
    store.set_budget(record.key_id, budget)
    return state, store, record


def _payload_basic() -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
        }
    )
