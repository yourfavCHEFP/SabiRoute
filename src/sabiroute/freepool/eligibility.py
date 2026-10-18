"""Free Pool eligibility contract for Free Chat requests.

Design notes (read before extending):

- Catalogue metadata is **not** runtime proof. A model listed in the Free Pool
  catalogue is not thereby configured, healthy, or usable here. Admission
  requires an explicit mapping to a configured deployment alias, and that
  mapping is the ``eligible_deployments`` allowlist — nothing else.
- This module never ranks, scores, executes, or retries. Candidate filtering
  reuses ``Router.evaluate_candidates`` at the call site, and selection reuses
  ``Router.choose_deployment`` inside the existing attempt loop. There is
  exactly one routing engine.
- Unknown, unmapped, stale, or ineligible names fail to intersect with the
  allowlist and are denied. They are never silently admitted.
- Enforcement is disabled by default (``FreePoolPolicy.enabled is False``).
  A disabled gateway fails closed on marked requests so OFF is never
  mistaken for production-ready Free Chat.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..routing.router import CandidateEvaluation

#: Request-body marker selecting Free Chat mode. Declared alongside the
#: existing ``sabi_route_request_type`` field; popped before provider
#: execution so it is never forwarded to LiteLLM.
FREE_CHAT_MARKER = "sabi_route_free_chat"

#: Stable denial reasons. Each becomes the response ``error.type`` and the
#: finalized usage event's ``failure_category``.
FREE_POOL_UNAVAILABLE = "free_pool_unavailable"
#: Stable reason when the shared-inference kill-switch denies admission.
SHARED_INFERENCE_DISABLED = "shared_inference_disabled"
FREE_POOL_UNMAPPED_DEPLOYMENT = "free_pool_unmapped_deployment"
FREE_POOL_NO_CAPABLE_DEPLOYMENT = "free_pool_no_capable_deployment"
FREE_POOL_NO_HEALTHY_DEPLOYMENT = "free_pool_no_healthy_deployment"
FREE_POOL_ROUTE_CONFIGURATION_ERROR = "free_pool_route_configuration_error"


@dataclass(frozen=True, slots=True)
class FreePoolPolicy:
    """Explicit Free Pool allowlist. Disabled by default."""

    enabled: bool = False
    eligible_deployments: frozenset[str] = frozenset()

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> FreePoolPolicy:
        """Build a policy from an explicit mapping (config/env/test fixtures).

        Raises ``ValueError``/``TypeError`` on anything but an explicit
        boolean flag and an explicit list of non-empty alias strings.
        """
        if not isinstance(mapping, dict):
            raise TypeError("Free Pool policy mapping must be a dict.")
        try:
            enabled = mapping["enabled"]
            eligible = mapping["eligible_deployments"]
        except KeyError as exc:
            raise ValueError(f"Free Pool policy is missing {exc}.") from exc
        if not isinstance(enabled, bool):
            raise ValueError("Free Pool policy 'enabled' must be a boolean.")
        if not isinstance(eligible, list) or not all(
            isinstance(name, str) and name.strip() for name in eligible
        ):
            raise ValueError(
                "Free Pool policy 'eligible_deployments' must be a list of "
                "non-empty deployment alias strings."
            )
        return cls(
            enabled=enabled,
            eligible_deployments=frozenset(name.strip() for name in eligible),
        )


@dataclass(frozen=True, slots=True)
class FreePoolDecision:
    """Typed allow/deny outcome for one Free Chat request."""

    allowed: bool
    reason: str | None
    eligible_candidates: tuple[str, ...]


def evaluate_free_pool(
    candidates: Iterable[str],
    policy: FreePoolPolicy,
) -> FreePoolDecision:
    """Intersect requested candidates with the explicit allowlist.

    Pure function: no router, no I/O. When the policy is disabled the
    candidates pass through unchanged (the call site fails closed on marked
    requests before consulting this function). When enabled, only explicitly
    mapped aliases survive; an empty intersection is denied, never widened.
    """
    requested = tuple(candidates)
    if not policy.enabled:
        return FreePoolDecision(
            allowed=True, reason=None, eligible_candidates=requested
        )
    eligible = tuple(name for name in requested if name in policy.eligible_deployments)
    if not eligible:
        return FreePoolDecision(
            allowed=False,
            reason=FREE_POOL_UNMAPPED_DEPLOYMENT,
            eligible_candidates=(),
        )
    return FreePoolDecision(
        allowed=True, reason=None, eligible_candidates=eligible
    )


def deny_reason_for_evaluation(evaluation: CandidateEvaluation) -> str | None:
    """Map a router evaluation over the allowlisted subset to a denial reason.

    Returns ``None`` when at least one allowlisted deployment is capable and
    healthy. Mirrors the order of ``Router.evaluate_candidates``: capability
    eligibility first, then health.
    """
    if not evaluation.capability_eligible_deployments:
        return FREE_POOL_NO_CAPABLE_DEPLOYMENT
    if not evaluation.available_deployments:
        return FREE_POOL_NO_HEALTHY_DEPLOYMENT
    return None


async def shared_inference_denial(state: Any, store: Any) -> str | None:
    """Decide whether shared inference may proceed right now.

    Returns ``None`` when an administrator explicitly enabled it, otherwise
    the stable ``SHARED_INFERENCE_DISABLED`` denial reason. Fail-closed on
    every abnormal shape: missing store, unreadable record, non-boolean
    value, or a store exception all deny. Read-through on every call — no
    cached enabled state exists anywhere, so a disable takes effect on the
    next admission or attempt on every instance sharing the database.
    """
    if store is None:
        return SHARED_INFERENCE_DISABLED
    executor = getattr(state, "store_executor", None)
    if executor is None:
        return SHARED_INFERENCE_DISABLED
    try:
        allowed = await executor.run(store.get_shared_inference)
    except Exception:
        return SHARED_INFERENCE_DISABLED
    return None if allowed is True else SHARED_INFERENCE_DISABLED
