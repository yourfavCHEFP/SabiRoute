"""The four failure outcomes of the chat send path.

A gateway that is unavailable, slow, or unreachable must each produce a
distinct status, and the two upstream failures must also record an assistant
message carrying the failure type so the conversation history explains the gap
instead of silently ending. A malformed upstream body is not a failure: it
yields an empty reply rather than an exception.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from sabiroute.api import chat as chat_module
from sabiroute.api.chat import (
    ChatServiceUnavailable,
    ChatUpstreamTimeout,
    ChatUpstreamTransport,
    PostMessageRequest,
)


class _Admit:
    def check(self, _key: str) -> None:
        return None


class _Limited:
    def check(self, _key: str) -> float:
        return 3.0


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []

    async def run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((func, args, kwargs))
        return func(*args, **kwargs)


def _message(**overrides: Any) -> Any:
    fields = {
        "message_id": "m1",
        "role": "assistant",
        "content": "",
        "created_at": datetime.now(UTC),
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def _store() -> Any:
    return SimpleNamespace(
        get_conversation=lambda cid, _uid: SimpleNamespace(
            conversation_id=cid, title="t"
        ),
        create_message=lambda _cid, role, content, **_kwargs: _message(
            role=role, content=content
        ),
        list_messages=lambda _cid, limit=None: [],
        touch_conversation=lambda _cid, _uid: None,
    )


def _context() -> Any:
    return SimpleNamespace(
        user=SimpleNamespace(user_id="user-1"),
        session=SimpleNamespace(session_id="session-1"),
    )


def _call(*, complete: Any, limiter: Any = None, recorder: Any = None) -> Any:
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    return asyncio.run(
        chat_module.post_message(
            "conversation-1",
            PostMessageRequest(content="hello"),
            request,
            context=_context(),
        )
    )


def test_a_rate_limited_send_is_refused_before_any_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Limited(), complete=None),
    )

    with pytest.raises(HTTPException) as excinfo:
        _call(complete=None, limiter=_Limited(), recorder=recorder)

    assert excinfo.value.status_code == 429
    assert recorder.calls == []


def test_an_unavailable_gateway_is_a_503(monkeypatch: pytest.MonkeyPatch) -> None:
    async def unavailable(*_args: Any, **_kwargs: Any) -> Any:
        raise ChatServiceUnavailable("no key")

    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Admit(), complete=unavailable),
    )

    with pytest.raises(HTTPException) as excinfo:
        _call(complete=unavailable, recorder=recorder)

    assert excinfo.value.status_code == 503


def test_an_upstream_timeout_is_a_504_and_is_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def slow(*_args: Any, **_kwargs: Any) -> Any:
        raise ChatUpstreamTimeout("slow")

    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Admit(), complete=slow),
    )

    with pytest.raises(HTTPException) as excinfo:
        _call(complete=slow, recorder=recorder)

    assert excinfo.value.status_code == 504
    assert any(
        kwargs.get("error_type") == "gateway_timeout"
        for _func, _args, kwargs in recorder.calls
    )


def test_an_unreachable_gateway_is_a_502_and_is_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def broken(*_args: Any, **_kwargs: Any) -> Any:
        raise ChatUpstreamTransport("broken")

    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Admit(), complete=broken),
    )

    with pytest.raises(HTTPException) as excinfo:
        _call(complete=broken, recorder=recorder)

    assert excinfo.value.status_code == 502
    assert any(
        kwargs.get("error_type") == "gateway_transport"
        for _func, _args, kwargs in recorder.calls
    )


def test_a_malformed_upstream_body_becomes_an_empty_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def empty(*_args: Any, **_kwargs: Any) -> Any:
        return 200, {}, None, {}

    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Admit(), complete=empty),
    )

    _call(complete=empty, recorder=recorder)

    assistant_writes = [
        args
        for _func, args, kwargs in recorder.calls
        if len(args) > 1 and args[1] == "assistant" and "error_type" not in kwargs
    ]
    assert assistant_writes
    assert assistant_writes[0][2] == ""


def test_a_non_mapping_upstream_body_is_treated_as_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def listed(*_args: Any, **_kwargs: Any) -> Any:
        return 200, {}, None, []

    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Admit(), complete=listed),
    )

    _call(complete=listed, recorder=recorder)

    assistant_writes = [
        args
        for _func, args, kwargs in recorder.calls
        if len(args) > 1 and args[1] == "assistant" and "error_type" not in kwargs
    ]
    assert assistant_writes[0][2] == ""


def test_a_non_string_content_becomes_an_empty_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def numeric(*_args: Any, **_kwargs: Any) -> Any:
        return 200, {}, None, {"choices": [{"message": {"content": 123}}]}

    recorder = _Recorder()
    monkeypatch.setattr(chat_module, "_executor", lambda _request: recorder)
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store())
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(chat_limiter=_Admit(), complete=numeric),
    )

    _call(complete=numeric, recorder=recorder)

    assistant_writes = [
        args
        for _func, args, kwargs in recorder.calls
        if len(args) > 1 and args[1] == "assistant" and "error_type" not in kwargs
    ]
    assert assistant_writes[0][2] == ""
