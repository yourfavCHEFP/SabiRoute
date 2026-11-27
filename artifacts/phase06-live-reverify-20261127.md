# Phase 06 — live re-verification

**Date:** 2026-11-27. **Verdict: PASS.**

## Why this run exists

The 2026-11-27 audit scorecard recorded Phase 06 as **Implemented** rather than
Complete, citing "recovery untested live" and naming the next action: *drive a
real cooldown → recovery transition with live traffic*.

The design docs already said otherwise — `docs/routing.md` (amendment
2026-11-23, owner accepted passive-only) and `CLAUDE.md:315` both record Phase 06
as closed. That left a three-way contradiction: design docs said closed, the
completion evidence of 2026-11-23 said PASS, and the scorecard said not-live.

This file resolves it by re-running the live repro on current `main`.

## Command

```
cd /path/to/SabiRoute
SABIROUTE_ENV_FILE=/path/to/.env \
PYTHONPATH=/path/to/SabiRoute/src \
  /path/to/.venv/bin/python scripts/phase06_health_cooldown_live.py
```

Exit code `0`. No stub in the path: a real LiteLLM Proxy is started on a free
port, the primary deployment fails with a real 429 (no-credit key), and the
secondary returns a real completion.

## Result

`threshold=3`, `cooldown_seconds=30`.

| Step | HTTP | Content | primary_failures | healthy | available | cooldown_until |
|---|---|---|---|---|---|---|
| failure_1 | 200 | OK | 1 | true | true | — |
| failure_2 | 200 | OK | 2 | true | true | — |
| failure_3 | 200 | OK | 3 | **false** | **false** | set |
| while_cooling_down | 200 | OK | **3 (frozen)** | false | false | set |
| after_cooldown_expired | 200 | OK | **4** | — | **true** | cleared |

All six checks passed: `threshold_tripped`, `unavailable_during_cooldown`,
`skipped_while_cooling_down`, `traffic_flowed_during_cooldown`,
`half_open_recovery`, `retried_after_recovery`.

## Why `while_cooling_down` is the load-bearing row

A health system that counts failures but never removes a deployment has changed
nothing. The observable proof is that `primary_failures` stays frozen at 3 —
the deployment is not attempted at all (`primary_attempted: false`) — while the
request still returns 200 from the secondary. Then the expired deadline moves
the counter to 4, proving the deployment was re-admitted rather than abandoned.

## Unit-level confirmation

`tests/test_health.py` + `tests/test_router.py` → **16 passed** on the same
tree. The state machine is covered independently of the live run.

## What this settles

- The scorecard's stated next action for Phase 06 is satisfied: a real cooldown
  → recovery transition was driven with live traffic.
- Phase 06 is **Complete**, consistent with `CLAUDE.md:315` and the
  `docs/routing.md` amendment of 2026-11-23.
- The scorecard's "Implemented but not live" roll-up of 8 phases should now be
  7 (05, 07, 10, 11, 12, 14, 18 — 06 removed).

## Honest limits

- **The harness supplies its own topology.** `primary` and `secondary` are
  deployments the script writes into a temporary LiteLLM proxy config; it does
  not run against the aliases in `config/config.yaml`. This proves the cooldown
  lifecycle on the real request path, not that any specific configured alias
  has a second candidate to fail over to. Main's 14 aliases each carry a single
  deployment, so deployment-level fallback is still not available by config
  alone.
- One run, one environment. `threshold` and `cooldown_seconds` are the defaults
  (3 / 30s), not tuned production values.
- The primary failure is a real 429 from an exhausted account, which is a
  narrower failure mode than timeout, connection reset, or 5xx.

## Trap worth preserving

Setting `cooldown_until = None` on an unhealthy deployment makes it
**permanently unavailable** — `is_available()` returns `False` when the deadline
is `None`. Only an *expired* deadline re-enters the half-open path. The harness
sets `now - 1s` for exactly this reason, and anyone "simplifying" that line turns
a 30-second cooldown into a dead deployment.
