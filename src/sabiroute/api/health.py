from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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
    if gateway is None or getattr(gateway, "startup_error", None):
        startup_ok = False
        registry_ok = False
        store_ok = False
    else:
        startup_ok = True
        registry_ok = len(gateway.registry) > 0
        store_ok = gateway.key_store is not None
    checks = (
        ("startup", startup_ok),
        ("registry", registry_ok),
        ("key_store", store_ok),
    )
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
