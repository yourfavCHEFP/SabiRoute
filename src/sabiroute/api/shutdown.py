"""Shared-inference kill-switch: admin disable/enable/status.

Separate router module (rather than extending ``api/admin.py``) so the
uncommitted Sprint 16B admin changes stay isolated and committable on their
own. Same conventions: router-wide ``require_admin_key``, ``{"error":
{...}}`` response shapes, store access via ``BoundedStoreExecutor``.

Policy: shared inference starts disabled and stays disabled unless an
administrator explicitly enables it; any missing, invalid, or unreadable
control state denies new admissions (fail closed). Disabling takes effect
on the next admission or attempt read-through — in-flight attempts are
never cancelled by the switch (documented limitation).
"""

from __future__ import annotations

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from ..gateway import GatewayState
from ..security.auth import require_admin_key
from ..security.keys import ApiKeyStore

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_key)],
)


class SharedInferenceRequest(BaseModel):
    """Kill-switch change request. No secrets, no content, no credentials."""

    model_config = ConfigDict(str_strip_whitespace=True)

    enabled: StrictBool
    reason: str | None = Field(default=None, max_length=280)


def _state(request: Request) -> GatewayState:
    """Read the shared gateway state from the running application."""
    return cast(GatewayState, request.app.state.gateway)


def _key_store(request: Request) -> ApiKeyStore:
    store = _state(request).key_store
    if store is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Shared-inference state is unavailable.",
                    "type": "shared_inference_unavailable",
                }
            },
        )
    return store


@router.get("/shared-inference")
async def shared_inference_status(request: Request) -> dict[str, Any]:
    """Report the kill-switch state (safe snapshot only, no secrets)."""
    store = _key_store(request)
    try:
        return await _state(request).store_executor.run(store.shared_inference_status)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Shared-inference state is unavailable.",
                    "type": "shared_inference_unavailable",
                }
            },
        ) from exc


@router.put("/shared-inference")
async def set_shared_inference(
    payload: SharedInferenceRequest, request: Request
) -> dict[str, Any]:
    """Explicitly disable or re-enable shared inference. No redeploy needed.

    Re-enabling requires this same explicit action; a restart never flips
    the persisted state. The change is audited via a structured log line
    carrying actor, action, reason length, and outcome — never secrets or
    conversation content.
    """
    store = _key_store(request)
    try:
        await _state(request).store_executor.run(
            store.set_shared_inference, payload.enabled, "admin"
        )
        status: dict[str, Any] = await _state(request).store_executor.run(
            store.shared_inference_status
        )
    except Exception as exc:
        logger.error("Shared-inference control change failed.")
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Shared-inference state is unavailable.",
                    "type": "shared_inference_unavailable",
                }
            },
        ) from exc
    logger.info(
        "Shared inference %s by admin (reason chars: %d).",
        "enabled" if payload.enabled else "disabled",
        len(payload.reason or ""),
    )
    return status
