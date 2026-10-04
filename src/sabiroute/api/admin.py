from fastapi import APIRouter

from ..monitoring.errors import ErrorTracker
from ..monitoring.latency import LatencyTracker
from ..monitoring.metrics import Metrics
from ..monitoring.usage import UsageTracker
from ..routing.health import HealthRegistry

router = APIRouter(prefix="/admin", tags=["admin"])


metrics = Metrics()
latency = LatencyTracker()
errors = ErrorTracker()
usage = UsageTracker()
health_registry = HealthRegistry()


@router.get("/health")
async def deployment_health() -> dict:
    return health_registry.snapshot()


@router.get("/metrics")
async def metrics_snapshot() -> dict:
    return metrics.snapshot()


@router.get("/latency")
async def latency_snapshot() -> dict:
    return latency.snapshot()


@router.get("/errors")
async def error_snapshot() -> dict:
    return errors.counts()


@router.get("/usage")
async def usage_snapshot() -> dict:
    return usage.totals()
