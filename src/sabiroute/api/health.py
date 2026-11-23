"""Unauthenticated health probes.

``/health`` and ``/health/live`` are static liveness answers. ``/health/ready``
proves the process can actually serve: startup succeeded, deployments are
configured, request accounting is available, and the database schema still
matches. Two Phase 17 hardening rules apply to it:

* F-08 — the response is a bare verdict. Component names and whether rate
  limiting is configured are not disclosed to an unauthenticated caller.
* F-09 — the database schema re-checks are cached briefly, so repeated
  unauthenticated probes cannot drive repeated database work.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..security.store import (
    check_sabichat_schema,
    check_schema,
    check_shared_inference_schema,
)

router = APIRouter(tags=["health"])

#: How long a successful schema re-check is trusted before the next probe
#: re-runs it. Short enough that a schema change is noticed quickly, long
#: enough that a probe loop cannot become a database query loop.
READINESS_SCHEMA_CACHE_SECONDS = 5.0

#: Indirection so tests can advance the cache clock without sleeping.
_monotonic = time.monotonic


class SchemaCheckCache:
    """Short-TTL cache for the readiness database schema re-check.

    Only a *successful* check is cached. A failed check is re-probed on the
    next request so a transient database fault cannot hold readiness down for
    the TTL; the amplification F-09 names is the healthy steady state, where
    every unauthenticated request would otherwise run three schema queries.
    """

    __slots__ = ("ttl_seconds", "_checked_at", "_failures")

    def __init__(self, ttl_seconds: float = READINESS_SCHEMA_CACHE_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._checked_at: float | None = None
        self._failures: frozenset[str] = frozenset()

    def failures(self) -> frozenset[str] | None:
        """Return the cached failure set, or ``None`` when a check is due."""
        if self._checked_at is None:
            return None
        if (_monotonic() - self._checked_at) >= self.ttl_seconds:
            return None
        return self._failures

    def record(self, failures: set[str]) -> None:
        """Store a check outcome; failures are deliberately not cached."""
        if failures:
            self.clear()
            return
        self._checked_at = _monotonic()
        self._failures = frozenset()

    def clear(self) -> None:
        self._checked_at = None
        self._failures = frozenset()


def _cache(request: Request) -> SchemaCheckCache:
    cache = getattr(request.app.state, "readiness_schema_cache", None)
    if not isinstance(cache, SchemaCheckCache):
        cache = SchemaCheckCache()
        request.app.state.readiness_schema_cache = cache
    return cache


def _schema_failures(request: Request, gateway: Any) -> frozenset[str]:
    """Return the failing schema groups, re-checking only when the cache expires."""
    cache = _cache(request)
    cached = cache.failures()
    if cached is not None:
        return cached
    failures: set[str] = set()
    # Read-only schema re-check (defensive; startup already validated).
    # A transient failure here is response-local: mutating shared gateway
    # state would make one failed probe permanently poison readiness.
    try:
        if gateway.key_store is not None and hasattr(gateway.key_store, "_engine"):
            check_schema(gateway.key_store._engine)
            check_shared_inference_schema(gateway.key_store._engine)
    except Exception:
        failures.add("key_store")
    try:
        if gateway.chat_store is not None and hasattr(gateway.chat_store, "_engine"):
            check_sabichat_schema(gateway.chat_store._engine)
    except Exception:
        failures.add("chat_store")
    cache.record(failures)
    return frozenset(failures)


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "sabiroute",
    }


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {
        "status": "alive",
    }


@router.get("/health/ready")
async def readiness(request: Request) -> JSONResponse:
    """Readiness: core request path can serve traffic.

    The body is deliberately a bare verdict. The component breakdown and the
    rate-limiter configuration are not disclosed to an unauthenticated caller
    (F-08); operators read deployment health from the authenticated
    ``/admin/health`` endpoint instead.
    """
    gateway = getattr(request.app.state, "gateway", None)
    if gateway is None or getattr(gateway, "startup_error", None):
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    if len(gateway.registry) == 0:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    if gateway.key_store is None:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    if _schema_failures(request, gateway):
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})
