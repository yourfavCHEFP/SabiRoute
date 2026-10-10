"""Shared gateway application state wiring config, routing, and monitoring."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from redis.asyncio import Redis

from .config.loader import load_config
from .config.models import SabiRouteConfig
from .monitoring.errors import ErrorTracker
from .monitoring.latency import LatencyTracker
from .monitoring.metrics import Metrics
from .monitoring.usage import UsageTracker
from .providers.litellm_client import LiteLLMClient
from .providers.registry import ProviderRegistry, registry_from_config
from .routing.fallback import FallbackEngine
from .routing.health import HealthRegistry
from .routing.policies import PolicyRegistry
from .routing.router import Router
from .routing.scoring import ScoringSettings
from .security.keys import ApiKeyStore
from .security.rate_limit import RedisTokenBucket
from .security.store import PostgresApiKeyStore

DEFAULT_PROXY_URL = "http://127.0.0.1:4000"
DEFAULT_ROUTES_PATH = Path(__file__).resolve().parents[2] / "config" / "routes"


@dataclass
class GatewayState:
    """Single shared state object for the API layer.

    Every component that must observe the same traffic (router, health
    registry, metrics, admin endpoints) reads from one instance of this
    class instead of constructing its own.
    """

    config: SabiRouteConfig
    registry: ProviderRegistry
    policies: PolicyRegistry
    router: Router
    health: HealthRegistry
    metrics: Metrics
    latency: LatencyTracker
    errors: ErrorTracker
    usage: UsageTracker
    client: LiteLLMClient
    startup_error: str | None = None
    key_store: ApiKeyStore | None = None
    rate_limiter: RedisTokenBucket | None = None


def build_gateway_state(
    config_path: str | Path | None = None,
    *,
    config: SabiRouteConfig | None = None,
    client: LiteLLMClient | None = None,
    key_store: ApiKeyStore | None = None,
    rate_limiter: RedisTokenBucket | None = None,
) -> GatewayState:
    """Build gateway state from configuration.

    The config path defaults to ``SABIROUTE_CONFIG_PATH`` or the repo's
    ``config/config.yaml``. Pass ``config`` directly to skip file loading
    (used by tests and embedders), and ``client`` to inject a custom
    LiteLLM boundary client, and ``key_store`` to inject SabiRoute-owned key
    persistence (tests/embedders). When omitted, ``DATABASE_URL`` selects the
    PostgreSQL-backed store. Pass ``rate_limiter`` to inject Redis admission;
    otherwise it is configured from ``REDIS_URL`` or ``REDIS_HOST``.
    """

    load_runtime_routes = config is None
    if config is None:
        path = config_path or os.environ.get("SABIROUTE_CONFIG_PATH")
        config = load_config(path)

    registry = registry_from_config(config)
    if load_runtime_routes:
        routes_path = os.environ.get("SABIROUTE_ROUTES_PATH", str(DEFAULT_ROUTES_PATH))
        policies = PolicyRegistry.from_directory(routes_path, registry)
    else:
        # Explicitly injected configs are used by tests and embedders; keep
        # their policy defaults independent of the repository's production routes.
        policies = PolicyRegistry()
    health = HealthRegistry()
    metrics = Metrics()
    latency = LatencyTracker()
    errors = ErrorTracker()
    usage = UsageTracker()

    router = Router(
        registry,
        health=health,
        policies=policies,
        fallback=FallbackEngine(health),
        scoring_settings=ScoringSettings(
            policy_version=config.routing_scoring.policy_version,
            reliability_weight=config.routing_scoring.reliability_weight,
            latency_weight=config.routing_scoring.latency_weight,
            minimum_samples=config.routing_scoring.minimum_samples,
            max_signal_age_seconds=config.routing_scoring.max_signal_age_seconds,
        ),
        latency=latency,
    )

    if client is None:
        client = LiteLLMClient(
            base_url=os.environ.get("SABIROUTE_LITELLM_URL", DEFAULT_PROXY_URL),
            api_key=os.environ.get("LITELLM_MASTER_KEY") or None,
            timeout_seconds=float(config.litellm_settings.request_timeout),
        )

    if key_store is None:
        database_url = os.environ.get("DATABASE_URL")
        key_store = PostgresApiKeyStore(database_url) if database_url else None

    if rate_limiter is None:
        redis_url = os.environ.get("REDIS_URL")
        redis_host = os.environ.get("REDIS_HOST")
        if redis_url:
            redis_client = Redis.from_url(redis_url, decode_responses=True)
            rate_limiter = RedisTokenBucket(redis_client)
        elif redis_host:
            redis_client = Redis(
                host=redis_host,
                port=int(os.environ.get("REDIS_PORT", "6379")),
                password=os.environ.get("REDIS_PASSWORD") or None,
                db=int(os.environ.get("REDIS_DB", "0")),
                decode_responses=True,
            )
            rate_limiter = RedisTokenBucket(redis_client)

    return GatewayState(
        config=config,
        registry=registry,
        policies=policies,
        router=router,
        health=health,
        metrics=metrics,
        latency=latency,
        errors=errors,
        usage=usage,
        client=client,
        key_store=key_store,
        rate_limiter=rate_limiter,
    )


def empty_gateway_state(*, client: LiteLLMClient | None = None) -> GatewayState:
    """Degraded state with no deployments, used when startup fails."""

    config = SabiRouteConfig()
    registry = ProviderRegistry()
    policies = PolicyRegistry()
    health = HealthRegistry()
    latency = LatencyTracker()

    router = Router(
        registry,
        health=health,
        policies=policies,
        fallback=FallbackEngine(health),
        latency=latency,
    )

    return GatewayState(
        config=config,
        registry=registry,
        policies=policies,
        router=router,
        health=health,
        metrics=Metrics(),
        latency=latency,
        errors=ErrorTracker(),
        usage=UsageTracker(),
        client=client or LiteLLMClient(),
        key_store=None,
        rate_limiter=None,
    )
