"""Residual branches of :mod:`sabiroute.security.auth`.

Three paths a healthy deployment never walks: a credential string that cannot
be UTF-8 encoded, the executor-less authentication path kept for states that
have no store executor, and administrative authentication when no secret has
been provisioned at all.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from sabiroute.security import auth as auth_module
from sabiroute.security.auth import (
    _constant_time_equal,
    require_admin_key,
    require_client_key,
)
from sabiroute.security.keys import ApiKeyRecord

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_constant_time_comparison_rejects_an_unencodable_string() -> None:
    # A lone surrogate cannot be UTF-8 encoded; the comparison must deny
    # rather than raise out of the dependency.
    assert _constant_time_equal("expected", "\ud800") is False


def _credentials(token: str = "presented") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _request(gateway: Any) -> Any:
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway=gateway)),
        state=SimpleNamespace(),
    )


def test_client_key_authenticates_synchronously_without_an_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = ApiKeyRecord(
        key_id="key-1",
        key_hash="hash",
        project_id="proj-1",
        name="test",
        created_at=NOW,
    )
    monkeypatch.setattr(
        auth_module, "authenticate_api_key", lambda store, presented: record
    )
    gateway = SimpleNamespace(key_store=object())

    resolved = asyncio.run(
        require_client_key(_request(gateway), _credentials())
    )

    assert resolved is record


def test_admin_authentication_is_unavailable_without_a_configured_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SABIROUTE_ADMIN_KEY", raising=False)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(require_admin_key(_credentials()))

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail["error"]["type"] == "authentication_unavailable"
