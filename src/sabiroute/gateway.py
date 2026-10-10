"""Shared gateway application state wiring config, routing, and monitoring."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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


def build_gateway_state(
    config_path: str | Path | None = None,
    *,
    config: SabiRouteConfig | None = None,
    client: LiteLLMClient | None = None,
) -> GatewayState:
    """Build gateway state from configuration.

    The config path defaults to ``SABIROUTE_CONFIG_PATH`` or the repo's
    ``config/config.yaml``. Pass ``config`` directly to skip file loading
    (used by tests and embedders), and ``client`` to inject a custom
    LiteLLM boundary client.
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
    )
