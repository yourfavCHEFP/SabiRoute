"""Authentication dependencies for client and administrative API boundaries."""

from __future__ import annotations

import hmac
import os
from typing import cast

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .keys import ApiKeyIdentity, ApiKeyRecord, ApiKeyStore, authenticate_api_key

_bearer = HTTPBearer(auto_error=False)
_bearer_dependency = Depends(_bearer)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "error": {
                "message": "Invalid bearer credential.",
                "type": "authentication_error",
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def _unavailable(message: str, error_type: str) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={"error": {"message": message, "type": error_type}},
    )


def _constant_time_equal(left: str, right: str) -> bool:
    try:
        return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
    except UnicodeEncodeError:
        return False


def _store(request: Request) -> ApiKeyStore:
    state = getattr(request.app.state, "gateway", None)
    store = getattr(state, "key_store", None)
    if store is None:
        raise _unavailable("Authentication is unavailable.", "authentication_unavailable")
    return cast(ApiKeyStore, store)


def _credentials(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise _unauthorized()
    return credentials.credentials


async def require_client_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> ApiKeyRecord:
    """Require an active SabiRoute client API key for request execution."""
    record = authenticate_api_key(_store(request), _credentials(credentials))
    if record is None:
        raise _unauthorized()
    request.state.api_identity = ApiKeyIdentity(
        key_id=record.key_id,
        project_id=record.project_id,
    )
    return record


async def require_admin_key(
    credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> None:
    """Require the separate, environment-provisioned administrative secret."""
    expected = os.environ.get("SABIROUTE_ADMIN_KEY")
    if not expected:
        raise _unavailable(
            "Administrative authentication is unavailable.",
            "authentication_unavailable",
        )
    internal_key = os.environ.get("LITELLM_MASTER_KEY")
    if expected.startswith("sr_live_") or (
        internal_key and _constant_time_equal(expected, internal_key)
    ):
        raise _unavailable(
            "Administrative authentication is unavailable.",
            "authentication_unavailable",
        )
    supplied = _credentials(credentials)
    if not _constant_time_equal(expected, supplied):
        raise _unauthorized()
