from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..security.store import (
    check_sabichat_schema,
    check_schema,
    check_shared_inference_schema,
)

router = APIRouter(tags=["health"])


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

    Liveness answers "is the process up"; readiness answers "can this
    instance serve requests": startup succeeded, deployments are
    configured, and request accounting is available. The rate limiter is
    reported informationally only: probing Redis on every readiness check
    would add latency and failure surface to the probe itself.
    """

    gateway = getattr(request.app.state, "gateway", None)
    schema_failures: set[str] = set()
    if gateway is not None and getattr(gateway, "startup_error", None) is None:
        # Read-only schema re-check (defensive; startup already validated).
        # A transient failure here is response-local: mutating shared gateway
        # state would make one failed probe permanently poison readiness.
        try:
            if gateway.key_store is not None and hasattr(gateway.key_store, "_engine"):
                check_schema(gateway.key_store._engine)
                check_shared_inference_schema(gateway.key_store._engine)
        except Exception:
            schema_failures.add("key_store")
        try:
            if gateway.chat_store is not None and hasattr(gateway.chat_store, "_engine"):
                check_sabichat_schema(gateway.chat_store._engine)
        except Exception:
            schema_failures.add("chat_store")
    if gateway is None or getattr(gateway, "startup_error", None):
        startup_ok = False
        registry_ok = False
        store_ok = False
    else:
        startup_ok = True
        registry_ok = len(gateway.registry) > 0
        store_ok = gateway.key_store is not None and "key_store" not in schema_failures
    checks: tuple[tuple[str, bool], ...] = (
        ("startup", startup_ok),
        ("registry", registry_ok),
        ("key_store", store_ok),
    )
    if "chat_store" in schema_failures:
        checks += (("chat_store", False),)
    failing = [name for name, ok in checks if not ok]
    components = {name: ("ok" if ok else "failed") for name, ok in checks}
    components["rate_limiter"] = (
        "configured"
        if gateway is not None
        and getattr(gateway, "rate_limiter", None) is not None
        else "absent"
    )
    if failing:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "failing": failing,
                "components": components,
            },
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "components": components},
    )
