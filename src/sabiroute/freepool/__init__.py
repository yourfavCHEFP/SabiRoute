"""Free Pool eligibility for Free Chat requests.

Free Pool is the controlled catalogue of provider/model deployments that a
shared Free Chat request may use. Catalogue metadata (published allowances,
access arrangements, verification status) is informational and lives outside
the request path. This package enforces the runtime side only: an explicit
allowlist of configured deployment aliases, evaluated through the existing
routing engine. SabiRoute decides; LiteLLM executes.
"""

from .eligibility import (
    FREE_CHAT_MARKER,
    FREE_POOL_NO_CAPABLE_DEPLOYMENT,
    FREE_POOL_NO_HEALTHY_DEPLOYMENT,
    FREE_POOL_ROUTE_CONFIGURATION_ERROR,
    FREE_POOL_UNAVAILABLE,
    FREE_POOL_UNMAPPED_DEPLOYMENT,
    SHARED_INFERENCE_DISABLED,
    FreePoolDecision,
    FreePoolPolicy,
    deny_reason_for_evaluation,
    evaluate_free_pool,
    shared_inference_denial,
)

__all__ = [
    "FREE_CHAT_MARKER",
    "FREE_POOL_NO_CAPABLE_DEPLOYMENT",
    "FREE_POOL_NO_HEALTHY_DEPLOYMENT",
    "FREE_POOL_ROUTE_CONFIGURATION_ERROR",
    "FREE_POOL_UNAVAILABLE",
    "FREE_POOL_UNMAPPED_DEPLOYMENT",
    "SHARED_INFERENCE_DISABLED",
    "FreePoolDecision",
    "FreePoolPolicy",
    "deny_reason_for_evaluation",
    "evaluate_free_pool",
    "shared_inference_denial",
]
