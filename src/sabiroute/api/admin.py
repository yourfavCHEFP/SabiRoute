from __future__ import annotations

from fastapi import APIRouter, Request

from ..gateway import GatewayState

router = APIRouter(prefix="/admin", tags=["admin"])


def _state(request: Request) -> GatewayState:
    """Read the shared gateway state from the running application."""

    return request.app.state.gateway


@router.get("/health")
async def deployment_health(request: Request) -> dict:
    return _state(request).health.snapshot()


@router.get("/metrics")
async def metrics_snapshot(request: Request) -> dict:
    return _state(request).metrics.snapshot()


@router.get("/latency")
async def latency_snapshot(request: Request) -> dict:
    return _state(request).latency.snapshot()


@router.get("/errors")
async def error_snapshot(request: Request) -> dict:
    return _state(request).errors.counts()


@router.get("/usage")
async def usage_snapshot(request: Request) -> dict:
    return _state(request).usage.totals()
