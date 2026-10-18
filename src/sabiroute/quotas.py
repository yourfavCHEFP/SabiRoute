"""Per-user daily token quotas for shared Free Pool inference (pilot).

Design notes (read before extending):

- This is metering, not billing. No charges, no payments, no plans.
- Only pilot-enrolled SabiChat users are metered, and only on marked
  shared-inference requests carrying trusted Phase 1 identity. Everyone
  else — unmarked traffic, non-pilot users, missing identity — follows the
  exact pre-quota path. There is deliberately no code path that grants
  unmetered shared inference to pilot members: no identity means no
  admission for enrolled traffic, and unenrolled traffic never enters.
- The daily allowance is an owner-approved constant (50,000 tokens, UTC
  calendar day). It is not configurable at runtime in this revision: a
  misconfigured knob that silently widens would be worse than a constant
  that requires a code change to move.
- Pilot membership is an explicit server-side set parsed from
  ``SABIROUTE_QUOTA_PILOT_USERS`` (comma-separated user IDs, default
  empty). Empty means nobody is metered — and pilot members are still
  subject to every pre-existing gate. Missing or unreadable quota state
  denies pilot admissions (fail closed).
- Reservation lifecycle mirrors the budget machinery: one atomic
  check-and-reserve per logical request, settle-once with actuals, release
  when nothing executed, hold estimates when provider usage is unknown.
  Crash recovery needs no worker: outstanding rows already carry estimates,
  and the UTC window bounds every hold to under 24 hours.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

_ONE_DAY = timedelta(days=1)

#: Owner-approved daily allowance per pilot user (tokens, UTC calendar day).
DAILY_TOKEN_QUOTA = 50_000

#: Stable denial reasons. Each becomes the response ``error.type`` and the
#: finalized usage event's ``failure_category``.
QUOTA_EXCEEDED = "quota_exceeded"
QUOTA_UNAVAILABLE = "quota_unavailable"
QUOTA_MAX_TOKENS_REQUIRED = "quota_max_tokens_required"


def quota_window_start(now: datetime) -> datetime:
    """Start of the UTC calendar day containing ``now`` (reset boundary)."""
    current = now.astimezone(UTC)
    return datetime(current.year, current.month, current.day, tzinfo=UTC)


def quota_reset_at(window_start: datetime) -> datetime:
    """Next reset instant for a window: exactly one UTC day later."""
    start = window_start.astimezone(UTC)
    return datetime(start.year, start.month, start.day, tzinfo=UTC) + _ONE_DAY


@dataclass(frozen=True, slots=True)
class QuotaPolicy:
    """Explicit pilot cohort for quota metering. Empty means nobody metered."""

    daily_tokens: int = DAILY_TOKEN_QUOTA
    pilot_users: frozenset[str] = frozenset()

    @classmethod
    def from_env(cls) -> QuotaPolicy:
        """Parse the pilot cohort from the environment (default: nobody)."""
        raw = os.environ.get("SABIROUTE_QUOTA_PILOT_USERS") or ""
        pilot = frozenset(part.strip() for part in raw.split(",") if part.strip())
        return cls(pilot_users=pilot)

    def covers(self, user_id: str | None) -> bool:
        """Whether this user is an enrolled pilot member (never trust input)."""
        return isinstance(user_id, str) and bool(user_id) and user_id in self.pilot_users


async def check_quota_admission(
    state: Any,
    store: Any,
    *,
    user_id: str,
    request_id: str,
    estimate: int,
    window_start: datetime,
    quota: int,
) -> str | None:
    """Atomically verify allowance and reserve, or return a denial reason.

    Returns ``None`` when admitted, otherwise ``QUOTA_EXCEEDED`` (no room)
    or ``QUOTA_UNAVAILABLE`` (state unreadable). Single transaction inside
    the store: never check-then-write. Fail-closed on every abnormal shape.
    """
    if store is None:
        return QUOTA_UNAVAILABLE
    executor = getattr(state, "store_executor", None)
    if executor is None:
        return QUOTA_UNAVAILABLE
    try:
        admitted = await executor.run(
            store.check_and_reserve_quota,
            user_id,
            request_id,
            estimate,
            window_start,
            quota,
        )
    except Exception:
        return QUOTA_UNAVAILABLE
    return None if admitted else QUOTA_EXCEEDED
