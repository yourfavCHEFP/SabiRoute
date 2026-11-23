# Phase 06 and Phase 10 — completion evidence

**Date:** 2026-11-23. Both phases moved to Complete on live evidence, not on
argument. This file records what was actually observed and, just as importantly,
what standard the evidence meets.

---

## Phase 06 — health lifecycle, live

**Verdict: PASS.** Reproduce with:

```
SABIROUTE_ENV_FILE=/path/to/.env \
PYTHONPATH=/path/to/SabiRoute-claude-fix/src \
  /path/to/.venv/bin/python scripts/phase06_health_cooldown_live.py
```

Five real requests through a real LiteLLM Proxy to real providers. Primary is
`openai/gpt-6-luna` (real 429, no credits); secondary is
`nvidia_nim/nvidia/nemotron-3.5-bolt-e4b` (real success). No stub.

| Step | HTTP | Content | primary failures | healthy | available | cooldown_until |
|---|---|---|---|---|---|---|
| failure_1 | 200 | OK | 1 | true | true | — |
| failure_2 | 200 | OK | 2 | true | true | — |
| failure_3 | 200 | OK | 3 | **false** | **false** | set |
| while_cooling_down | 200 | OK | **3 (frozen)** | false | false | set |
| after_cooldown_expired | 200 | OK | **4** | — | **true** | cleared |

All six checks passed: `threshold_tripped`, `unavailable_during_cooldown`,
`skipped_while_cooling_down`, `traffic_flowed_during_cooldown`,
`half_open_recovery`, `retried_after_recovery`.

**Why the 4th row is the load-bearing one.** A health system that counts
failures but never removes a deployment has changed nothing. The observable
proof is that `primary_failures` stays frozen at 3 — the deployment is not
attempted at all — while the request still returns 200 from the secondary. That
is cooldown doing its job rather than merely recording disappointment.

**The 5th row proves recovery.** Expiring the deadline re-admits the deployment
(`primary_failures` rises to 4), so cooldown is a pause, not an eviction.

**A trap this run depends on.** Recovery is reached by setting `cooldown_until`
to an *expired* timestamp. Setting it to `None` on an unhealthy deployment makes
it permanently unavailable — `is_available()` returns False for a None deadline.
Anyone "simplifying" that line turns a 30-second cooldown into a dead deployment.

**What Phase 06 Complete now rests on:** implemented (`routing/health.py`),
unit-tested (`tests/test_health.py`), **and live-verified** on a real request
path including the cooldown trip and recovery, which were previously only
unit-tested. The architecture decision to use passive rather than active probing
is recorded separately in `docs/routing.md` (amendment 2026-11-23).

---

## Phase 10 — budgets and rate limits, against real services

**Verdict: PASS by integration tests against real PostgreSQL and Redis.**

The blocker was never code. It was that `SABIROUTE_TEST_REDIS_URL` was unset, so
five real-Redis tests skipped, and the suite had never been run with both
service endpoints present.

It is not necessary to point tests at the live gateway Redis. A disposable
instance is sufficient:

```
redis-server --port 6399 --save '' --appendonly no --daemonize yes \
  --dir /tmp/sabiroute-phase10-redis
```

Then run the suite with `SABIROUTE_TEST_REDIS_URL=redis://127.0.0.1:6399/0` and
`SABIROUTE_TEST_PG_URL` set. Shut it down with `redis-cli -p 6399 shutdown nosave`.

| Configuration | Result |
|---|---|
| No test services | 866 passed, 10 skipped |
| `SABIROUTE_TEST_PG_URL` only | 870 passed, 6 skipped |
| PG + disposable Redis | **875 passed, 1 skipped** |

The single remaining skip is the known contract skip at
`tests/test_r6_registration_digest_conformance.py:570`.

**The specific claims Phase 10 needed are asserted, not adjacent:**

- `tests/test_phase10.py:125` — a rate-limited response carries
  `Retry-After: 1`.
- `tests/test_phase10.py:767` — a **budget** denial does *not* carry
  `Retry-After`, while a rate-limit denial does. That distinction matters: it is
  wrong to tell a client to retry when the reason is an exhausted budget.
- `tests/test_user_quotas.py:334,572` — quota 429s carry `Retry-After`, and the
  header is absent where it should be.
- All five previously-skipped Redis tests now execute and pass.

**Honest limit on the claim.** This is integration-test evidence through the
real ASGI app against real PostgreSQL and real Redis. It is not a manual
production run with a live client across a real billing period. The repository's
definition of live-verified is "exercised on a documented real request path",
which this meets; a reader who reserves "live" for production traffic should
read this as the strongest form of test evidence rather than as operational
experience.

---

## Phase board after this change

| Phase | Status |
|---|---|
| 05 Fallback Engine | Complete — real 429 drove a real fallback |
| 06 Health Monitoring | Complete — live cooldown trip, skip, and recovery |
| 10 Budgets & Rate Limits | Complete — 429 + Retry-After against real PG/Redis |
| 02 Provider Expansion | In progress — 4 of 14, six blocked on money |
| 11 Routing Intelligence | In progress — chat evidence for 4, nothing else tested |
