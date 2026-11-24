"""Refusals on the SabiChat auth and quota endpoints.

Two shapes of failure must stay apart. A rate-limited caller gets a retry
answer, not a credentials error. A quota summary that cannot be computed
fails closed with 503 and never reports zero usage, because reporting zero
would tell an exhausted caller they had budget left.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from sabiroute.api import chat as chat_module
from sabiroute.api.chat import LoginRequest


class _Limited:
    def check(self, _key: str) -> float:
        return 7.0


class _Returns:
    def __init__(self, value: Any) -> None:
        self.value = value

    async def run(self, _func: Any, *_args: Any, **_kwargs: Any) -> Any:
        return self.value


def _request(state: Any) -> Any:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(gateway=state)))


def _context(user_id: str = "user-1") -> Any:
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


def _policy(*, daily_tokens: int = 1000) -> Any:
    return SimpleNamespace(covers=lambda _user_id: True, daily_tokens=daily_tokens)


def test_login_is_rate_limited_before_any_credential_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_module, "_service", lambda _request: SimpleNamespace(auth_limiter=_Limited())
    )
    monkeypatch.setattr(chat_module, "_client_ip", lambda _request: "127.0.0.1")
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: SimpleNamespace())

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            chat_module.login(
                LoginRequest(email="user@example.com", password="secret"),
                _request(SimpleNamespace()),
            )
        )

    assert excinfo.value.status_code == 429


def _summary(state: Any, usage: Any) -> Any:
    return asyncio.run(chat_module.quota_summary(_request(state), _context()))


def test_quota_summary_fails_closed_without_a_key_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = SimpleNamespace(quota_policy=_policy(), key_store=None)

    with pytest.raises(HTTPException) as excinfo:
        _summary(state, {})

    assert excinfo.value.status_code == 503


def test_quota_summary_fails_closed_on_a_malformed_usage_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = SimpleNamespace(quota_policy=_policy(), key_store=object())
    monkeypatch.setattr(chat_module, "_executor", lambda _request: _Returns({}))

    with pytest.raises(HTTPException) as excinfo:
        _summary(state, {})

    assert excinfo.value.status_code == 503


def test_quota_summary_fails_closed_on_non_integer_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = SimpleNamespace(quota_policy=_policy(), key_store=object())
    usage = {"reserved_tokens": "5", "consumed_tokens": 1}
    monkeypatch.setattr(chat_module, "_executor", lambda _request: _Returns(usage))

    with pytest.raises(HTTPException) as excinfo:
        _summary(state, usage)

    assert excinfo.value.status_code == 503


def test_quota_summary_fails_closed_on_an_invalid_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = SimpleNamespace(quota_policy=_policy(daily_tokens=0), key_store=object())
    usage = {"reserved_tokens": 0, "consumed_tokens": 1}
    monkeypatch.setattr(chat_module, "_executor", lambda _request: _Returns(usage))

    with pytest.raises(HTTPException) as excinfo:
        _summary(state, usage)

    assert excinfo.value.status_code == 503
