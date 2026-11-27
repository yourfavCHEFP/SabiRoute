# Phase 07 — Admin Telemetry Under Induced Failure

**Date:** 2026-11-27
**Branch:** `docs/phase06-reverify` (off `origin/main`)
**Verdict:** **PASS** — a real provider failure was observable through SabiRoute's
administrative telemetry surfaces.
**Raw snapshot:** `artifacts/phase07-metrics-under-failure-20261127.json`

This closes the scorecard gap for Phase 07: *"no stored failure-metric evidence; trackers are
process-local and reset on restart"* → next action *"capture an admin metrics snapshot under
induced failure"*.

It is the companion to `artifacts/sprint-4/PHASE07-LIVE-TELEMETRY-2026-11-23.md`, which proves
the **success** path. Neither record subsumes the other.

---

## Why a second harness

`scripts/phase07_live_telemetry.py` deliberately never fails: it drives one alias per request
with no cross-alias fallback, so every request it issues succeeds. A success path cannot
produce `requests_failed`, an error classification, or a failure-side latency sample.

`scripts/phase07_metrics_under_failure.py` supplies the one thing that harness cannot — a real
failure. It imports `phase05_real_provider_failure` for the proxy plumbing, gateway builder and
env loading rather than copying them, so the two phases cannot drift into testing different
things (`phase06_health_cooldown_live.py` reuses Phase 05 the same way).

Both harnesses share the premise discipline: if the primary provider answers, the run reports
`PREMISE_NOT_MET` (exit 2) and refuses to score any telemetry claim.

---

## What was run

```
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
PYTHONPATH="/Users/airm2/.sabiroute-main/src" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/phase07_metrics_under_failure.py
```

The chain contains no stub:

```
TestClient -> SabiRoute ASGI app -> LiteLLMClient -> LiteLLM Proxy
           -> primary   (real provider, really fails)
           -> secondary (real provider, really answers)
```

`/admin/{metrics,errors,latency,usage}` is read **before and after** the request, with a
per-run administrative secret (`SABIROUTE_ADMIN_KEY`) that is neither a client key prefix nor
the proxy master key. A baseline failure on any surface exits 3 rather than passing.

---

## Result — VERIFIED BY RUNTIME

```json
{ "verdict": "PASS", "status": 200, "served_model": "secondary" }
```

All nine checks passed:

| check | value |
|---|---|
| `status_200` | true |
| `non_empty_text` | true |
| `primary_recorded_failure` | true |
| `secondary_recorded_success` | true |
| `metrics_counted_the_request` | true |
| `metrics_counted_a_failure` | true |
| `metrics_counted_a_success` | true |
| `error_tracker_recorded_failure` | true |
| `latency_tracker_recorded_deployment` | true |

### Delta across the one completion

| surface | observed |
|---|---|
| `metrics.requests_total` | **+2** |
| `metrics.requests_failed` | **+1** |
| `metrics.requests_successful` | **+1** |
| `metrics.requests_by_model` | `{"primary": 1, "secondary": 1}` |
| `errors` | `{"rate_limit": 1}` |
| `latency` | samples for `primary` **and** `secondary` |

Two requests for one client call is correct, not a miscount: `record_request` is called per
**deployment attempt**, so a failover is one client request and two routing attempts.

`errors: {"rate_limit": 1}` is the substantive part. The failure was not merely counted — it
was **classified** as a rate limit, which is a retryable class, which is why fallback fired.
This is consistent with Phase 02's standing finding that the OpenAI leg refuses with 429.

### Corroborating tests

```
tests/test_admin.py                                              5 passed
tests/test_phase18_request_guard_and_telemetry.py               40 passed
tests/test_fallback_injection.py + test_proxy_attempt_census.py 16 passed
```

---

## What this PASS does NOT establish

**Durability is unchanged.** `Metrics`, `ErrorTracker` and `UsageTracker` are in-process
dataclasses; they still reset on restart. `monitoring/signals_store.py` persists health/latency
*signals* over a pluggable backend (`InMemoryBackend`, `RedisBackend`), but it does not persist
these counters. This harness stores the snapshot as a file — that is **stored evidence**, not
persistence, and the harness prints the same caveat in its own output.

If durable counters are considered part of Phase 07 rather than a separate concern, this phase
stays *In progress* and the remaining work is a persistence design change, which would need its
own approval.

---

## Cross-reference: Phase 05 counter arithmetic (resolved)

The Phase 05 record flagged `consecutive_failures: 1` alongside `total_failures: 5` as
UNVERIFIED. It is now resolved, and it is not a defect:

- `total_failures` / `total_successes` are **hydrated from persisted signals** at startup
  (`src/sabiroute/routing/health.py:51-72`), and `gateway.py:179` builds the registry over
  `RedisBackend` when Redis is configured — so those totals include earlier runs.
- `consecutive_failures` is **deliberately not restored** (`src/sabiroute/routing/health.py:47-50`):
  a restart grants one fresh failure budget, so the streak counts this process only.

Separately, this run shows why attempt-level and request-level numbers differ: two
`record_request` calls per failover mean one client request produces two routing attempts.

## Durability — settled as accepted design, not fixed

The counters are in-process and still reset on restart. That is **already the documented
behaviour**, not an oversight: `docs/observability.md:80-83` states that restarting SabiRoute
resets every counter, that there is no persistence or export yet, and that durable
per-request accounting is a *separate* system (the usage-event store). Persistent
health/latency *signals* live in `monitoring/signals_store.py`.

Making these counters durable would duplicate the usage-event store and is an architectural
change requiring its own approval, so it is recorded here as accepted design rather than
implemented in this phase.

---

## Roadmap position

Phase 07 — moves to **Complete**: implemented, tested, live-verified on both the success path
(2026-11-23) and the failure path (2026-11-27), with the in-process durability limit recorded.

## Next

Phase 02 remains the structural blocker (8 of 14 aliases cash-blocked) and the earliest phase
that unblocks others: 11 (capability evidence), 12 (real telemetry), 13 (dataset coverage).
