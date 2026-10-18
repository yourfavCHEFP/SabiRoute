"""Shared gateway application state wiring config, routing, and monitoring."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from redis.asyncio import Redis

from .chat.store import SabiChatStore
from .config.loader import load_config
from .config.models import SabiRouteConfig
from .freepool.eligibility import FreePoolPolicy
from .monitoring.errors import ErrorTracker
from .monitoring.latency import LatencyTracker
from .monitoring.metrics import Metrics
from .monitoring.usage import UsageTracker
from .providers.litellm_client import LiteLLMClient
from .providers.registry import ProviderRegistry, registry_from_config
from .quotas import QuotaPolicy
from .routing.health import HealthRegistry
from .routing.policies import PolicyRegistry
from .routing.router import Router
from .routing.scoring import ScoringSettings
from .security.keys import ApiKeyStore
from .security.rate_limit import RedisTokenBucket
from .security.store import PostgresApiKeyStore
from .security.store_executor import BoundedStoreExecutor

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
    free_pool: FreePoolPolicy = field(default_factory=FreePoolPolicy)
    chat_store: SabiChatStore | None = None
    # Key ID of the server-held SabiChat service credential, set by the chat
    # backend after provisioning. Only a request bearing this key may
    # establish trusted SabiChat user identity. Never sourced from config,
    # environment, or client input.
    sabichat_service_key_id: str | None = None
    # Per-user quota policy for pilot shared inference. Empty pilot cohort
    # by default: nobody is metered until deliberately configured.
    quota_policy: QuotaPolicy = field(default_factory=QuotaPolicy)
    store_executor: BoundedStoreExecutor = field(
        default_factory=BoundedStoreExecutor
    )
    # Dedicated executor for PBKDF2 password hashing (registration, login
    # verification, and dummy verification). Password hashing is
    # CPU-intensive (tens of milliseconds per call at 600k iterations) and
    # must never occupy slots on the database executor: saturating the
    # store executor with hashing work would stall request accounting
    # behind logins.
    password_executor: BoundedStoreExecutor = field(
        default_factory=lambda: BoundedStoreExecutor(max_concurrency=4)
    )


def build_gateway_state(
    config_path: str | Path | None = None,
    *,
    config: SabiRouteConfig | None = None,
    client: LiteLLMClient | None = None,
    key_store: ApiKeyStore | None = None,
    rate_limiter: RedisTokenBucket | None = None,
    free_pool: FreePoolPolicy | None = None,
    chat_store: SabiChatStore | None = None,
    quota_policy: QuotaPolicy | None = None,
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
        # Blank means unset: an empty SABIROUTE_ROUTES_PATH must select the
        # repository default, not the process working directory.
        routes_path = (os.environ.get("SABIROUTE_ROUTES_PATH") or "").strip() or str(
            DEFAULT_ROUTES_PATH
        )
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
        # Blank means unset: an empty SABIROUTE_LITELLM_URL must select the
        # default proxy URL, not an empty base URL. Non-blank values,
        # including invalid ones, pass through unchanged.
        client = LiteLLMClient(
            base_url=(os.environ.get("SABIROUTE_LITELLM_URL") or "").strip()
            or DEFAULT_PROXY_URL,
            api_key=os.environ.get("LITELLM_MASTER_KEY") or None,
            timeout_seconds=float(config.litellm_settings.request_timeout),
        )

    # Captured before auto-creation below: an explicitly injected key store
    # signals a test/embedding context that manages its own stores, which must
    # not trigger a surprise database connection for the chat store either.
    stores_managed_by_caller = key_store is not None or chat_store is not None

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
            # Blank means unset for numeric options too: int("") would crash
            # startup even though no value was really provided. Non-blank
            # invalid values still raise loudly instead of becoming defaults.
            redis_port = (os.environ.get("REDIS_PORT") or "").strip() or "6379"
            redis_db = (os.environ.get("REDIS_DB") or "").strip() or "0"
            redis_client = Redis(
                host=redis_host,
                port=int(redis_port),
                password=os.environ.get("REDIS_PASSWORD") or None,
                db=int(redis_db),
                decode_responses=True,
            )
            rate_limiter = RedisTokenBucket(redis_client)

    if free_pool is None:
        free_pool = _free_pool_from_env()

    if quota_policy is None:
        quota_policy = QuotaPolicy.from_env()

    if chat_store is None and not stores_managed_by_caller:
        # Neither store was injected, so this is a real deployment (or a
        # storeless test): both stores come from the environment together.
        database_url = os.environ.get("DATABASE_URL")
        chat_store = SabiChatStore(database_url) if database_url else None

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
        free_pool=free_pool,
        chat_store=chat_store,
        quota_policy=quota_policy,
    )


def _free_pool_from_env() -> FreePoolPolicy:
    """Build the Free Pool policy from the environment. Disabled by default.

    ``SABIROUTE_FREEPOOL_ENABLED`` accepts ``1``/``true``/``yes``/``on``
    (case-insensitive); anything else, including unset, means disabled.
    ``SABIROUTE_FREEPOOL_DEPLOYMENTS`` is a comma-separated allowlist of
    configured deployment aliases. Blank entries are ignored.
    """
    raw_enabled = (os.environ.get("SABIROUTE_FREEPOOL_ENABLED") or "").strip().lower()
    enabled = raw_enabled in {"1", "true", "yes", "on"}
    raw_deployments = os.environ.get("SABIROUTE_FREEPOOL_DEPLOYMENTS") or ""
    eligible = frozenset(
        part.strip() for part in raw_deployments.split(",") if part.strip()
    )
    return FreePoolPolicy(enabled=enabled, eligible_deployments=eligible)


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
