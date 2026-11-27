"""Behavioural tests for the SabiRoute -> LiteLLM boundary client."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from sabiroute.providers import litellm_client as client_module
from sabiroute.providers.litellm_client import (
    LiteLLMClient,
    LiteLLMClientError,
    LiteLLMStream,
)

DECISION = SimpleNamespace(deployment="fast")
MESSAGES = [{"role": "user", "content": "hi"}]


class _Response:
    def __init__(
        self,
        *,
        body: Any = None,
        text: str = "",
        status_code: int = 200,
        content_type: str = "application/json",
        lines: list[str] | None = None,
    ) -> None:
        self._body = body
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self._lines = lines or []
        self.closed = False

    def json(self) -> Any:
        if self._body is None:
            raise ValueError("not json")
        return self._body

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    async def aiter_lines(self) -> Any:
        for line in self._lines:
            yield line

    async def aread(self) -> bytes:
        return self.text.encode()

    async def aclose(self) -> None:
        self.closed = True


class _Client:
    def __init__(self, response: _Response, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.posted: tuple[str, Any] | None = None
        self.closed = False

    async def __aenter__(self) -> _Client:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def post(self, url: str, json: Any = None) -> _Response:
        self.posted = (url, json)
        if self.error is not None:
            raise self.error
        return self.response

    def build_request(self, method: str, url: str, json: Any = None) -> Any:
        return SimpleNamespace(method=method, url=url, json=json)

    async def send(self, request: Any, stream: bool = False) -> _Response:
        if self.error is not None:
            raise self.error
        return self.response

    async def aclose(self) -> None:
        self.closed = True


def _install(monkeypatch: pytest.MonkeyPatch, client: _Client) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    def factory(**kwargs: Any) -> _Client:
        seen.update(kwargs)
        return client

    monkeypatch.setattr(client_module.httpx, "AsyncClient", factory)
    return seen


def test_completion_posts_alias_messages_and_auth_header(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _Response(body={"choices": [{"message": {"content": "ok"}}]})
    client = _Client(response)
    seen = _install(monkeypatch, client)

    result = asyncio.run(
        LiteLLMClient(base_url="http://gw:4000/", api_key="secret").chat_completion(
            DECISION, MESSAGES, temperature=0.2, max_tokens=16
        )
    )

    assert result["choices"][0]["message"]["content"] == "ok"
    url, payload = client.posted  # type: ignore[misc]
    assert url == "http://gw:4000/v1/chat/completions"
    assert payload["model"] == "fast"
    assert payload["messages"] == MESSAGES
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 16
    assert seen["headers"]["Authorization"] == "Bearer secret"


def test_completion_omits_auth_header_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _Client(_Response(body={}))
    seen = _install(monkeypatch, client)

    asyncio.run(LiteLLMClient().chat_completion(DECISION, MESSAGES))

    assert "Authorization" not in seen["headers"]


def test_timeout_is_reported_as_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _Client(_Response(body={}), error=httpx.TimeoutException("slow")))

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().chat_completion(DECISION, MESSAGES))

    assert excinfo.value.timed_out is True


def test_transport_error_is_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _Client(_Response(body={}), error=httpx.ConnectError("refused")))

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().chat_completion(DECISION, MESSAGES))

    assert "transport error" in str(excinfo.value)


def test_http_error_carries_status_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    body = {"error": {"message": "rate limited"}}
    _install(monkeypatch, _Client(_Response(body=body, status_code=429)))

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().chat_completion(DECISION, MESSAGES))

    assert excinfo.value.status_code == 429
    assert excinfo.value.response_body == body


def test_non_object_response_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _Client(_Response(body=["not", "an", "object"])))

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().chat_completion(DECISION, MESSAGES))

    assert "non-object" in str(excinfo.value)


def test_stream_returns_an_open_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _Response(content_type="text/event-stream", lines=["data: hi", ""])
    client = _Client(response)
    _install(monkeypatch, client)

    stream = asyncio.run(
        LiteLLMClient(api_key="secret").start_chat_completion_stream(DECISION, MESSAGES)
    )

    assert isinstance(stream, LiteLLMStream)
    assert stream.response is response


def test_stream_rejects_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _Client(_Response(body={"error": "boom"}, status_code=500))
    _install(monkeypatch, client)

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().start_chat_completion_stream(DECISION, MESSAGES))

    assert excinfo.value.status_code == 500
    assert client.closed is True


def test_stream_rejects_a_non_sse_response(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _Client(_Response(body={}, content_type="application/json"))
    _install(monkeypatch, client)

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().start_chat_completion_stream(DECISION, MESSAGES))

    assert "did not return an event stream" in str(excinfo.value)


def test_stream_events_group_lines_into_frames() -> None:
    response = _Response(lines=["data: a", "", "data: b", ""])
    client = _Client(response)
    stream = LiteLLMStream(client, response)  # type: ignore[arg-type]

    frames = asyncio.run(_collect(stream))

    assert frames == [b"data: a\n\n", b"data: b\n\n"]


def test_stream_events_flush_a_trailing_frame() -> None:
    response = _Response(lines=["data: tail"])
    stream = LiteLLMStream(_Client(response), response)  # type: ignore[arg-type]

    assert asyncio.run(_collect(stream)) == [b"data: tail\n\n"]


def test_stream_aclose_closes_both_handles() -> None:
    response = _Response(lines=[])
    client = _Client(response)
    stream = LiteLLMStream(client, response)  # type: ignore[arg-type]

    asyncio.run(stream.aclose())

    assert response.closed is True
    assert client.closed is True


async def _collect(stream: LiteLLMStream) -> list[bytes]:
    return [frame async for frame in stream.events()]


def test_stream_timeout_is_reported_and_closes_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _Client(_Response(), error=httpx.TimeoutException("slow"))
    _install(monkeypatch, client)

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().start_chat_completion_stream(DECISION, MESSAGES))

    assert excinfo.value.timed_out is True
    assert client.closed is True


def test_stream_transport_error_is_reported_and_closes_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _Client(_Response(), error=httpx.ConnectError("refused"))
    _install(monkeypatch, client)

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().start_chat_completion_stream(DECISION, MESSAGES))

    assert "stream transport error" in str(excinfo.value)
    assert client.closed is True


class _CapturingClient(_Client):
    """Records the request the client builds, including its JSON body."""

    def __init__(self, response: _Response) -> None:
        super().__init__(response)
        self.request: Any = None

    def build_request(self, method: str, url: str, json: Any = None) -> Any:
        request = super().build_request(method, url, json=json)
        self.request = request
        return request


def test_an_error_body_that_is_not_json_is_reported_as_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A gateway that dies before it can serialise anything returns HTML or a
    # bare traceback; the reference detail must still reach the caller.
    _install(
        monkeypatch,
        _Client(_Response(text="upstream exploded", status_code=502)),
    )

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().chat_completion(DECISION, MESSAGES))

    assert excinfo.value.status_code == 502
    assert excinfo.value.response_body == "upstream exploded"
    assert "upstream exploded" in str(excinfo.value)


def test_stream_forwards_temperature_and_max_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _Response(content_type="text/event-stream", lines=["data: hi", ""])
    client = _CapturingClient(response)
    _install(monkeypatch, client)

    asyncio.run(
        LiteLLMClient().start_chat_completion_stream(
            DECISION, MESSAGES, temperature=0.1, max_tokens=32
        )
    )

    assert client.request.json["temperature"] == 0.1
    assert client.request.json["max_tokens"] == 32
    assert client.request.json["stream"] is True


def test_stream_http_error_with_a_non_json_body_keeps_the_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _Client(_Response(text="gateway exploded", status_code=502))
    _install(monkeypatch, client)

    with pytest.raises(LiteLLMClientError) as excinfo:
        asyncio.run(LiteLLMClient().start_chat_completion_stream(DECISION, MESSAGES))

    assert excinfo.value.status_code == 502
    assert excinfo.value.response_body == "gateway exploded"
    assert client.closed is True
