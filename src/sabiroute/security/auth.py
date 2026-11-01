"""Authentication dependencies for client and administrative API boundaries."""

from __future__ import annotations

import hmac
import os
from typing import cast

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .keys import ApiKeyIdentity, ApiKeyRecord, ApiKeyStore, authenticate_api_key
from .store_executor import BoundedStoreExecutor

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


def _executor(request: Request) -> BoundedStoreExecutor | None:
    state = getattr(request.app.state, "gateway", None)
    executor = getattr(state, "store_executor", None)
    return executor if isinstance(executor, BoundedStoreExecutor) else None


async def require_client_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> ApiKeyRecord:
    """Require an active SabiRoute client API key for request execution."""
    store = _store(request)
    presented = _credentials(credentials)
    executor = _executor(request)
    try:
        if executor is None:
            # States without an executor keep exact synchronous behavior.
            record = authenticate_api_key(store, presented)
        else:
            record = await executor.run(authenticate_api_key, store, presented)
    except Exception:  # noqa: BLE001 - a store fault must deny, never escape
        # R3-S5 fail-closed: a credential-store fault denies the request with
        # the established typed 503, exactly as the missing-store case above
        # and the accounting path's ``usage_store_unavailable`` do.
        #
        # R3-S3: an exception escaping here becomes an unhandled 500 whose
        # full traceback the ASGI server logs, and a store driver failure
        # carries the DSN (password included) in its message. Handling it here
        # keeps that text out of the log, and ``from None`` stops the original
        # exception leaking through exception chaining.
        raise _unavailable(
            "Authentication is unavailable.", "authentication_unavailable"
        ) from None
    if record is None:
        raise _unauthorized()
    request.state.api_identity = ApiKeyIdentity(
        key_id=record.key_id,
        project_id=record.project_id,
        lineage_id=record.lineage_id,
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
