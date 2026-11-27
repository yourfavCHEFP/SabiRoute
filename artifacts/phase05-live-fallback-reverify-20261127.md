# Phase 05 — Live Failure-Injection Re-Verification

**Date:** 2026-11-27
**Branch:** `docs/phase06-reverify` (off `origin/main`)
**Verdict:** **PASS** — a real provider failure on the primary deployment caused SabiRoute to
fail over to a real secondary provider, which answered with real content.

This closes the scorecard gap for Phase 05: *"no live failure-injection; fallback has never
stepped to a second provider against real services."*

---

## What was run

```
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
PYTHONPATH="/Users/airm2/.sabiroute-main/src" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" \
scripts/phase05_real_provider_failure.py
```

`scripts/phase05_real_provider_failure.py` (320 lines) contains **no stub anywhere in the
request path**. It:

1. Starts its own LiteLLM proxy on a free port, from a per-run temporary config.
2. Builds a real SabiRoute gateway state over `LiteLLMClient`, with an in-memory key store.
3. Issues one completion through the real application (`create_app(state=...)`).
4. Reads the live `HealthRegistry` snapshot after the call.
5. **Checks the premise before the claim** — if the primary answered, it refuses to score a
   fallback and exits 2 (`PREMISE_NOT_MET`). This is the property that makes the result
   meaningful: a "fallback worked" claim is worthless if nothing failed.

Both legs are real HTTPS calls to real providers carrying real credentials.

---

## Result — VERIFIED BY RUNTIME

```json
{
  "verdict": "PASS",
  "status": 200,
  "elapsed_ms": 4427.3,
  "content_preview": "OK",
  "checks": {
    "status_200": true,
    "non_empty_text": true,
    "primary_recorded_failure": true,
    "secondary_recorded_success": true,
    "primary_never_succeeded": true
  }
}
```

Exit code: **0**.

The response body corroborates the failover independently of the health counters — the
served model is named:

```json
"model": "secondary"
```

### Health registry snapshot (live, post-call)

| deployment | total_failures | total_successes | consecutive_failures | last_success | available |
|---|---:|---:|---:|---|---|
| `primary` | **5** | **0** | 1 | `null` | true |
| `secondary` | 0 | **6** | 0 | `2026-11-27 19:08:02Z` | true |

`primary` never succeeded once (`total_successes: 0`, `last_success: null`) and `secondary`
served every successful response. The fallback was driven by a genuine upstream failure, not
by a scheduled or injected code path.

### Unit/test corroboration

```
tests/test_fallback_injection.py tests/test_proxy_attempt_census.py
16 passed in 5.92s   (rc=0)
```

---

## What this PASS does NOT establish

Recorded deliberately, because the structural point is easy to lose inside a green result.

The harness **supplies its own two-deployment topology** — `primary` and `secondary` are
deployments it writes into its own temporary proxy config. It does not run against
`config/config.yaml`.

In the shipped catalog, every one of the 14 aliases has **exactly one deployment**.
`registry_from_config` binds `ProviderDeployment.name = model_entry.model_name` at
`src/sabiroute/providers/registry.py:165`, and `ProviderRegistry.register` raises
`ValueError(f"Deployment already registered: {name}")` at `src/sabiroute/providers/registry.py:44`
over a `dict[str, ProviderDeployment]`. LiteLLM-style same-alias fallback is therefore not
reachable from the current configuration.

So, precisely:

- **PROVEN:** the fallback mechanism is correct end to end on the real request path, against
  real providers, under a real upstream failure.
- **NOT PROVEN:** that any *configured* alias currently has a valid failover target. None does.

This is a configuration/design gap, not a Phase 05 code defect.

---

## Counter arithmetic — explained (was UNVERIFIED, now resolved)

`primary` reports `consecutive_failures: 1` alongside `total_failures: 5` and
`total_successes: 0`. The two numbers measure different things, by design:

- `total_failures` / `total_successes` are **hydrated from persisted signals** on startup.
  `HealthRegistry.__post_init__` replays `backend.load_health()` and adds the counts
  (`src/sabiroute/routing/health.py:51-72`). With Redis configured, `gateway.py:179` builds the
  registry over `RedisBackend`, so the totals carry observations from earlier runs — including
  the earlier Phase 05 runs against the same Redis.
- `consecutive_failures` is **deliberately not restored**. The comment at
  `src/sabiroute/routing/health.py:47-50` states it plainly: *"Cooldown state (healthy /
  consecutive_failures / cooldown_until) is deliberately not restored: a restart still grants
  one fresh failure budget."* It therefore counts this process only — 1.

So `5 failures / 0 successes / 1 consecutive` is correct: four historical failures replayed
from Redis plus this run's single failure, with the streak counter scoped to the process.
No defect, and nothing to fix. Status: **VERIFIED BY INSPECTION**.

---

## Architectural position

Proves the **Routing Engine → Fallback** hop of the pipeline under real failure:
`Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter →
Routing Engine → **Fallback** → LiteLLM → Provider → Response`.

No PostgreSQL, Redis, or telemetry state was written (in-memory key store, process-local
health trackers).

## Roadmap position

Phase 05 — moves from *Implemented* to **Complete** (implemented + tested + live-verified),
carrying the documented single-deployment limitation above.

## Next

Phase 07's recorded gap is *"capture an admin metrics snapshot under induced failure."* This
harness now induces exactly that failure and exposes live health counters alongside it, so
the instrument for 07 already exists.
