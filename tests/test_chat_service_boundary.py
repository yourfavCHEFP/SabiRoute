"""Service-level branches of the SabiChat backend.

The service key is provisioned once and cached in memory, with a re-check
after the lock is taken so two concurrent first requests do not both mint a
key. The upstream call has three outcomes that must stay distinct: a timeout,
a transport failure, and a response whose body is not JSON. These tests stop
at the service boundary; the endpoints are covered separately.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from sabiroute.api.chat import (
    ChatServiceUnavailable,
    ChatUpstreamTimeout,
    ChatUpstreamTransport,
    SabiChatService,
)


class _Executor:
    async def run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)


_UNSET = object()


def _service(*, plaintext: str | None = None, key_store: Any = _UNSET) -> Any:
    store = object() if key_store is _UNSET else key_store
    state = SimpleNamespace(key_store=store, store_executor=_Executor())
    service = SabiChatService(state)
    service._service_plaintext = plaintext
    return service


def test_service_headers_return_the_cached_bearer_token() -> None:
    service = _service(plaintext="abc123")

    headers = asyncio.run(service.service_headers())

    assert headers == {"Authorization": "Bearer abc123"}


def test_service_headers_refuse_without_a_key_store() -> None:
    service = _service(key_store=None)

    with pytest.raises(ChatServiceUnavailable):
        asyncio.run(service.service_headers())


class _CachingLock:
    """Simulates a concurrent request that minted the key first."""

    def __init__(self, service: Any) -> None:
        self._service = service

    async def __aenter__(self) -> _CachingLock:
        self._service._service_plaintext = "provisioned-by-the-winner"
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


def test_service_headers_recheck_the_cache_after_acquiring_the_lock() -> None:
    service = _service()
    service._key_lock = _CachingLock(service)

    headers = asyncio.run(service.service_headers())

    assert headers == {"Authorization": "Bearer provisioned-by-the-winner"}


class _FailingClient:
    def __init__(self, error: Exception | None) -> None:
        self._error = error

    def __call__(self, *args: Any, **kwargs: Any) -> _FailingClient:
        return self

    async def __aenter__(self) -> _FailingClient:
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False

    async def post(self, *args: Any, **kwargs: Any) -> Any:
        assert self._error is not None
        raise self._error


def test_an_upstream_timeout_is_reported_as_a_chat_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _FailingClient(httpx.ReadTimeout("slow")))
    service = _service(plaintext="k")

    with pytest.raises(ChatUpstreamTimeout):
        asyncio.run(service.complete(None, "m", [], user_id="u"))


def test_an_upstream_transport_error_is_reported_as_such(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx, "AsyncClient", _FailingClient(httpx.ConnectError("refused"))
    )
    service = _service(plaintext="k")

    with pytest.raises(ChatUpstreamTransport):
        asyncio.run(service.complete(None, "m", [], user_id="u"))


class _BadJSONResponse:
    status_code = 200
    headers: dict[str, str] = {}

    def json(self) -> Any:
        raise ValueError("no body")


class _BadJSONClient(_FailingClient):
    async def post(self, *args: Any, **kwargs: Any) -> Any:
        return _BadJSONResponse()


def test_an_unparseable_upstream_body_becomes_an_empty_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _BadJSONClient(None))
    service = _service(plaintext="k")

    status_code, _headers, _deployment, body = asyncio.run(
        service.complete(None, "m", [], user_id="u")
    )

    assert status_code == 200
    assert body == {}


class _ListJSONResponse:
    status_code = 200
    headers: dict[str, str] = {}

    def json(self) -> Any:
        return []


class _ListJSONClient(_FailingClient):
    async def post(self, *args: Any, **kwargs: Any) -> Any:
        return _ListJSONResponse()


def test_a_non_mapping_upstream_body_is_normalised_to_an_empty_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _ListJSONClient(None))
    service = _service(plaintext="k")

    status_code, _headers, _deployment, body = asyncio.run(
        service.complete(None, "m", [], user_id="u")
    )

    assert status_code == 200
    assert body == {}
