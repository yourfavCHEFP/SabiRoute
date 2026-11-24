"""Session refusal in the SabiChat bearer dependency.

A bearer token that resolves to no user, or to a disabled one, must be
rejected exactly like an unknown session. Anything weaker would let a disabled
account keep a working session until the token expired.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from sabiroute.api import chat as chat_module


class _Executor:
    async def run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)


def _request() -> Any:
    """Only a bearer credential matters here; the resolvers are patched."""
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))


def _store(user: Any) -> Any:
    session = SimpleNamespace(
        user_id="user-1",
        revoked_at=None,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    return SimpleNamespace(
        get_session=lambda _token_hash: session,
        get_user=lambda _user_id: user,
    )


def _credentials() -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")


def test_a_session_whose_user_is_gone_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store(None))
    monkeypatch.setattr(chat_module, "_executor", lambda _request: _Executor())
    request = _request()

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            chat_module.require_chat_session(request, credentials=_credentials())
        )

    assert excinfo.value.status_code == 401


def test_a_session_whose_user_is_disabled_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disabled = SimpleNamespace(
        user_id="user-1", disabled_at=datetime.now(UTC) - timedelta(hours=1)
    )
    monkeypatch.setattr(chat_module, "_chat_store", lambda _request: _store(disabled))
    monkeypatch.setattr(chat_module, "_executor", lambda _request: _Executor())
    request = _request()

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            chat_module.require_chat_session(request, credentials=_credentials())
        )

    assert excinfo.value.status_code == 401
