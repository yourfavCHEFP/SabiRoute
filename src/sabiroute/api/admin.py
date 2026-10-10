from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from ..gateway import GatewayState
from ..security.auth import require_admin_key
from ..security.keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    ApiKeyRecord,
    ApiKeyStore,
    issue_api_key,
    revoke_api_key,
    rotate_api_key,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_key)],
)


class CreateApiKeyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiKeyRateLimitRequest(BaseModel):
    requests_per_minute: int = Field(ge=1, le=1_000_000)
    burst_capacity: int = Field(ge=1, le=1_000_000)


class ApiKeyBudgetRequest(BaseModel):
    daily_tokens: int | None = Field(default=None, ge=1)
    monthly_tokens: int | None = Field(default=None, ge=1)
    daily_cost_usd: Decimal | None = Field(default=None, gt=0)
    monthly_cost_usd: Decimal | None = Field(default=None, gt=0)


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
                    "message": "Key management is unavailable.",
                    "type": "key_store_unavailable",
                }
            },
        )
    return store


def _issued_response(record: ApiKeyRecord, plaintext: str) -> dict[str, Any]:
    """Return a newly issued credential exactly once, alongside non-secret metadata."""
    return {
        "id": record.key_id,
        "project_id": record.project_id,
        "name": record.name,
        "created_at": record.created_at,
        "api_key": plaintext,
    }


@router.get("/health")
async def deployment_health(request: Request) -> dict[str, Any]:
    return cast(dict[str, Any], _state(request).health.snapshot())


@router.get("/metrics")
async def metrics_snapshot(request: Request) -> dict[str, Any]:
    return cast(dict[str, Any], _state(request).metrics.snapshot())


@router.get("/latency")
async def latency_snapshot(request: Request) -> dict[str, Any]:
    return cast(dict[str, Any], _state(request).latency.snapshot())


@router.get("/errors")
async def error_snapshot(request: Request) -> dict[str, Any]:
    return cast(dict[str, Any], _state(request).errors.counts())


@router.get("/usage")
async def usage_snapshot(request: Request) -> dict[str, Any]:
    return cast(dict[str, Any], _state(request).usage.totals())


@router.post("/api-keys", status_code=201)
async def create_client_api_key(
    payload: CreateApiKeyRequest,
    request: Request,
) -> dict[str, Any]:
    record, plaintext = issue_api_key(
        _key_store(request),
        project_id=payload.project_id,
        name=payload.name,
        metadata=payload.metadata,
    )
    return _issued_response(record, plaintext)


@router.post("/api-keys/{key_id}/rotate", status_code=201)
async def rotate_client_api_key(key_id: str, request: Request) -> dict[str, Any]:
    rotated = rotate_api_key(_key_store(request), key_id)
    if rotated is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "API key not found or inactive.",
                    "type": "key_not_found",
                }
            },
        )
    record, plaintext = rotated
    return _issued_response(record, plaintext)


@router.post("/api-keys/{key_id}/revoke")
async def revoke_client_api_key(key_id: str, request: Request) -> dict[str, str]:
    if not revoke_api_key(_key_store(request), key_id):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "API key not found or inactive.",
                    "type": "key_not_found",
                }
            },
        )
    return {"id": key_id, "status": "revoked"}


@router.put("/api-keys/{key_id}/rate-limit")
async def set_client_rate_limit(
    key_id: str,
    payload: ApiKeyRateLimitRequest,
    request: Request,
) -> dict[str, Any]:
    store = _key_store(request)
    record = store.get(key_id)
    if record is None or record.revoked_at is not None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "API key not found or inactive.",
                    "type": "key_not_found",
                }
            },
        )
    limit = ApiKeyRateLimit(
        requests_per_minute=payload.requests_per_minute,
        burst_capacity=payload.burst_capacity,
    )
    if not store.set_rate_limit(key_id, limit):
        raise HTTPException(status_code=404, detail="API key not found or inactive.")
    return {
        "key_id": key_id,
        "project_id": record.project_id,
        "requests_per_minute": limit.requests_per_minute,
        "burst_capacity": limit.burst_capacity,
    }


@router.get("/api-keys/{key_id}/rate-limit")
async def get_client_rate_limit(key_id: str, request: Request) -> dict[str, Any]:
    store = _key_store(request)
    record = store.get(key_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "API key not found.", "type": "key_not_found"}},
        )
    limit = store.get_rate_limit(key_id)
    return {
        "key_id": key_id,
        "project_id": record.project_id,
        "requests_per_minute": limit.requests_per_minute if limit else None,
        "burst_capacity": limit.burst_capacity if limit else None,
    }


@router.delete("/api-keys/{key_id}/rate-limit")
async def clear_client_rate_limit(key_id: str, request: Request) -> dict[str, str]:
    store = _key_store(request)
    if not store.set_rate_limit(key_id, None):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "API key not found or inactive.",
                    "type": "key_not_found",
                }
            },
        )
    return {"key_id": key_id, "status": "rate_limit_removed"}


@router.get("/api-keys/{key_id}/usage")
async def client_usage_events(
    key_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=1_000_000),
) -> dict[str, Any]:
    store = _key_store(request)
    record = store.get(key_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "API key not found.", "type": "key_not_found"}},
        )
    events, total = store.list_usage_events(key_id, limit=limit, offset=offset)
    return {
        "key_id": key_id,
        "project_id": record.project_id,
        "limit": limit,
        "offset": offset,
        "total": total,
        "items": [
            {
                "request_id": event.request_id,
                "created_at": event.created_at,
                "requested_alias": event.requested_alias,
                "final_deployment": event.final_deployment,
                "final_status": event.final_status,
                "prompt_tokens": event.prompt_tokens,
                "completion_tokens": event.completion_tokens,
                "total_tokens": event.total_tokens,
                "failure_category": event.failure_category,
                "estimated_input_tokens": event.estimated_input_tokens,
                "reserved_tokens": event.reserved_tokens,
                "estimated_cost_usd": (
                    str(event.estimated_cost_usd) if event.estimated_cost_usd is not None else None
                ),
                "actual_cost_usd": (
                    str(event.actual_cost_usd) if event.actual_cost_usd is not None else None
                ),
                "feature_schema_version": event.feature_schema_version,
                "pre_routing_features": list(event.pre_routing_features),
                "routing_decisions": list(event.routing_decisions),
            }
            for event in events
        ],
    }


@router.put("/api-keys/{key_id}/budget")
async def set_client_budget(
    key_id: str,
    payload: ApiKeyBudgetRequest,
    request: Request,
) -> dict[str, Any]:
    try:
        budget = ApiKeyBudget(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not _key_store(request).set_budget(key_id, budget):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "API key not found or inactive.",
                    "type": "key_not_found",
                }
            },
        )
    return {"key_id": key_id, **_budget_payload(budget)}


@router.get("/api-keys/{key_id}/budget")
async def get_client_budget(key_id: str, request: Request) -> dict[str, Any]:
    store = _key_store(request)
    if store.get(key_id) is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    budget = store.get_budget(key_id)
    usage = store.get_budget_usage(key_id, datetime.now(UTC))
    return {
        "key_id": key_id,
        "budget": _budget_payload(budget) if budget else None,
        "usage": {
            period: {
                "tokens": int(values["tokens"]),
                "cost_usd": str(values["cost_usd"]),
            }
            for period, values in usage.items()
        },
    }


@router.delete("/api-keys/{key_id}/budget")
async def clear_client_budget(key_id: str, request: Request) -> dict[str, str]:
    if not _key_store(request).set_budget(key_id, None):
        raise HTTPException(status_code=404, detail="API key not found or inactive.")
    return {"key_id": key_id, "status": "budget_removed"}


def _budget_payload(budget: ApiKeyBudget) -> dict[str, Any]:
    return {
        "daily_tokens": budget.daily_tokens,
        "monthly_tokens": budget.monthly_tokens,
        "daily_cost_usd": str(budget.daily_cost_usd) if budget.daily_cost_usd is not None else None,
        "monthly_cost_usd": (
            str(budget.monthly_cost_usd) if budget.monthly_cost_usd is not None else None
        ),
    }
