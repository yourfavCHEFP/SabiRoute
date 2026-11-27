"""Refusals on the SabiChat auth and quota endpoints.

Two shapes of failure must stay apart. A rate-limited caller gets a retry
answer, not a credentials error. A quota summary that cannot be computed fails
closed with 503 and never reports zero usage, because reporting zero would
tell an exhausted caller they had budget left.

The quota tests go through the real executor against a store that returns the
malformed row, so the assertions cover the branch that actually rejects it.
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


class _Runner:
    async def run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)


def _policy(*, daily_tokens: int = 1000) -> Any:
    return SimpleNamespace(covers=lambda _user_id: True, daily_tokens=daily_tokens)


def _context(user_id: str = "user-1") -> Any:
    return SimpleNamespace(user=SimpleNamespace(user_id=user_id))


def _quota_request(usage: Any, *, daily_tokens: int = 1000) -> Any:
    store = SimpleNamespace(get_quota_usage=lambda *_args: usage)
    gateway = SimpleNamespace(
        quota_policy=_policy(daily_tokens=daily_tokens),
        key_store=store,
        store_executor=_Runner(),
    )
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway=gateway))
    )


def test_login_is_rate_limited_before_any_credential_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_module,
        "_service",
        lambda _request: SimpleNamespace(auth_limiter=_Limited()),
    )
    monkeypatch.setattr(chat_module, "_client_ip", lambda _request: "127.0.0.1")
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: SimpleNamespace())
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            chat_module.login(
                LoginRequest(email="user@example.com", password="secret"), request
            )
        )

    assert excinfo.value.status_code == 429


def test_quota_summary_fails_closed_without_a_key_store() -> None:
    gateway = SimpleNamespace(quota_policy=_policy(), key_store=None)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(gateway=gateway)))

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(chat_module.quota_summary(request, _context()))

    assert excinfo.value.status_code == 503


def test_quota_summary_fails_closed_on_a_malformed_usage_row() -> None:
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(chat_module.quota_summary(_quota_request({}), _context()))

    assert excinfo.value.status_code == 503


def test_quota_summary_fails_closed_on_non_integer_usage() -> None:
    usage = {"reserved_tokens": "5", "consumed_tokens": 1}

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(chat_module.quota_summary(_quota_request(usage), _context()))

    assert excinfo.value.status_code == 503


def test_quota_summary_fails_closed_on_an_invalid_quota() -> None:
    usage = {"reserved_tokens": 0, "consumed_tokens": 1}

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            chat_module.quota_summary(
                _quota_request(usage, daily_tokens=0), _context()
            )
        )

    assert excinfo.value.status_code == 503
