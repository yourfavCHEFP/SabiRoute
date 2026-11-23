# Phase 07 — Live-Provider Telemetry Evidence

- **Date:** 2026-11-23
- **Repository:** `SabiRoute` (worktree of commit `117082f`)
- **Scope:** Close the recorded Phase 07 gap — *"live-provider telemetry
  remains UNVERIFIED."*
- **Harness:** `scripts/phase07_live_telemetry.py`
- **Doc:** `docs/observability.md`

## Claim under test

A real completion to a real provider, driven through the real SabiRoute ASGI
app, produces telemetry that lands in the `metrics` / `latency` / `errors` /
`usage` trackers and reads back through the admin endpoints with the numbers
you would expect.

Path under test (no stub):

```
TestClient -> SabiRoute ASGI app -> LiteLLMClient -> LiteLLM Proxy
           -> real provider HTTPS -> real response
```

The proxy was started by the harness from a config derived from the
repository's own `config/config.yaml` routes, with retries forced to zero.

## Spend

Exactly **three** real requests (the ceiling), one per alias, `max_tokens=32`,
sequential, no proxy retries, no cross-alias fallback. Observed billed tokens
across the three calls: 110 + 44 + 35 = **189**.

Credentials (names and state only — values never read into output):

| alias | credential variables | state |
|---|---|---|
| `sabiroute-groq` | `GROQ_API_KEY` | set |
| `sabiroute-cloudflare` | `CLOUDFLARE_API_KEY`, `CLOUDFLARE_ACCOUNT_ID` | set, set |
| `sabiroute-openrouter` | `OPENROUTER_API_KEY` | set |

## Command

```bash
cd "/Users/airm2/My ML Hub/SabiRoute/.claude/worktrees/agent-a0ab5022271717867"
PYTHONPATH="$PWD/src" \
SABIROUTE_ENV_FILE="/Users/airm2/My ML Hub/SabiRoute/.env" \
"/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python" scripts/phase07_live_telemetry.py
```

Admin auth used a per-run generated `SABIROUTE_ADMIN_KEY` (value not printed).

## Real telemetry read back from the admin endpoints

`GET /admin/metrics` — **before**: all zero, `requests_by_model {}`.
**After:**

```
requests_total 3
requests_successful 3
requests_failed 0
requests_rate_limited 0
requests_by_model {'sabiroute-groq': 1, 'sabiroute-cloudflare': 1, 'sabiroute-openrouter': 1}
```

`GET /admin/latency` — **before** `{}`. **After:**

```
sabiroute-groq        samples=1 average_ms=1363.6 last_ms=1363.6
sabiroute-cloudflare  samples=1 average_ms=1399.7 last_ms=1399.7
sabiroute-openrouter  samples=1 average_ms=9087.7 last_ms=9087.7
```

`GET /admin/usage` — **before** `{}`. **After:**

```
sabiroute-groq        110
sabiroute-cloudflare  44
sabiroute-openrouter  35
```

`GET /admin/errors` — **before** `{}`; **after** `{}` (consistent with zero
failed attempts).

`GET /admin/health` — all three deployments `healthy=true`,
`total_successes=1`, `total_failures=0`, `cooldown_until=null`.

## Per-request outcome (as the gateway recorded it)

| alias | HTTP | gateway outcome | content | elapsed_ms | prompt | compl | total | finish_reason |
|---|---|---|---|---|---|---|---|---|
| `sabiroute-groq` | 200 | success | empty_truncated | 1377.5 | 78 | 32 | 110 | length |
| `sabiroute-cloudflare` | 200 | success | non_empty (`OK`) | 1402.7 | 42 | 2 | 44 | — |
| `sabiroute-openrouter` | 200 | success | empty_truncated | 9090.1 | 7 | 28 | 35 | length |

Both empty-content responses are reasoning models (`gpt-oss-120b`,
`gemini-3.8-flash`) that spent the 32-token budget on reasoning
(`reasoning_tokens` present) and hit `finish_reason=length` before emitting
final content. The provider call itself succeeded, with real usage; the gateway
correctly recorded a success.

## Invariant evaluation

```json
{
  "deltas": {"metrics_requests_total": 3, "metrics_requests_successful": 3,
              "metrics_requests_failed": 0, "errors_records": 0},
  "checks": {
    "request_count_rose_by_attempts": true,
    "success_count_matches": true,
    "failure_count_matches": true,
    "latency_recorded_for_every_attempt": true,
    "errors_categorised_per_failure": true,
    "usage_recorded_with_real_tokens": true
  },
  "usage_proven": true,
  "verdict": "PASS"
}
```

The first execution of the harness reported `ASSERTION_FAILED`. That was a
**harness defect, not a system failure**: the harness had classified a `200`
with empty `content` as a failure, so its success/failure counts disagreed with
the gateway's (which correctly counted three successes). The classification
was corrected to use the gateway's definition (HTTP 200 = successful
execution), and the corrected evaluator was run against the captured values
with zero network calls:

```bash
PYTHONPATH="$PWD/src" /Users/airm2/My ML Hub/SabiRoute/.venv/bin/python \
  scripts/phase07_live_telemetry.py --self-check
# exit 0; evaluation.verdict = "PASS"
```

No additional provider calls were made to obtain this clean result — the spend
ceiling is three requests and it was already reached.

## What this proves, and what it does not

**Proven (VERIFIED BY RUNTIME):**
- Real requests through the real ASGI app increment `metrics` per deployment.
- Per-deployment `latency` is recorded with positive, plausible values.
- `usage` carries real token counts returned by the providers.
- The error surface is consistent with what happened (empty, because all three
  succeeded).
- All four admin endpoints are reachable with the admin secret and return the
  live values.

**Not proven by this run:**
- Live **failure** categorisation (`auth`/`rate_limit`/`server`/`timeout`/
  `transport`). No request failed, so that branch was not exercised live; it
  remains covered by unit tests only. It is explicitly not claimed here.
- Persistence across restart: the trackers are in-memory and reset. Documented
  in `docs/observability.md`.

## Defects in `src/**`

None found. The gateway recorded exactly what the responses contained. The one
non-obvious behaviour — a `200` with truncated/empty content being counted as a
success — is correct for telemetry (the execution succeeded and was billed) and
is a content-quality question, not an observability bug.

## Verdict

Phase 07's recorded gap was "live-provider telemetry UNVERIFIED". That gap is
now closed for the **success path**: real provider traffic produced real
metrics, latency and usage telemetry that read back correctly through the admin
endpoints. Live failure categorisation was not triggered by this run and should
not be upgraded on the strength of it.
