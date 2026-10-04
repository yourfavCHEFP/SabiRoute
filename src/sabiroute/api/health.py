from fastapi import APIRouter

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
