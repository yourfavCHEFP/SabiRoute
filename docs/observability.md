# Observability (Phase 07)

SabiRoute records four runtime signals for every routed request and exposes
them through the admin API. This document describes what is recorded, where,
what is readable, and — importantly — what the trackers do **not** do.

Evidence basis: live-provider telemetry was exercised on 2026-11-23 with three
real completions through a real LiteLLM proxy to three real providers
(`sabiroute-groq`, `sabiroute-cloudflare`, `sabiroute-openrouter`). See
`artifacts/sprint-4/PHASE07-LIVE-TELEMETRY-2026-11-23.md` for the captured
values. The success path is **VERIFIED BY RUNTIME**; live *failure*
categorisation is unit-tested but was not triggered by that run (all three
calls returned HTTP 200).

## The four trackers

All four are plain in-memory objects, constructed once and held on
`GatewayState` (`src/sabiroute/gateway.py`). Every component that must observe
traffic reads the same instance.

| Tracker | Module | Keyed by | Records |
|---|---|---|---|
| `Metrics` | `monitoring/metrics.py` | deployment | `requests_total`, `requests_successful`, `requests_failed`, `requests_rate_limited`, `requests_by_model` |
| `LatencyTracker` | `monitoring/latency.py` | deployment | per-attempt `samples`, `average_ms`, `last_ms` (plus a timestamped observation series used by measured scoring) |
| `ErrorTracker` | `monitoring/errors.py` | category | `ErrorRecord(category, model, message, timestamp)`; `counts()` aggregates by category |
| `UsageTracker` | `monitoring/usage.py` | deployment | `UsageRecord(model, prompt_tokens, completion_tokens, total_tokens)`; `totals()` sums `total_tokens` per model |

Keys are **deployment aliases** (e.g. `sabiroute-groq`), not upstream model
ids — the same identifier SabiRoute routes on and returns in the
`X-SabiRoute-Deployment` response header.

## Where recording happens

All writes are in `src/sabiroute/api/completions.py`:

- `metrics.record_request(deployment)` — once per attempt, at attempt start.
- On provider success: `metrics.record_success()`, `latency.record(...)`,
  `health.mark_success(...)`, and `usage.record(...)` populated from the
  response's `usage` object (`_record_usage`).
- On a `LiteLLMClientError`: `metrics.record_failure()`,
  `health.mark_failure(...)`, `errors.record(category, deployment, message)`,
  `latency.record(...)`. The category comes from `_error_category`:
  `auth` (401/403), `rate_limit` (429), `server` (5xx), `client` (other 4xx),
  `timeout`, or `transport`.
- `metrics.record_rate_limited()` — an authenticated request rejected by the
  rate limiter before provider routing.
- Streaming has the same success/failure recording, plus `stream_interrupted`
  and `deadline_exceeded` categories.

A request that fails **before** the attempt loop (e.g. rejected by the
body/credential guard, or a store failure) is accounted for in the durable
usage event but does not increment `requests_total`; this is deliberate —
`requests_total` counts provider attempts.

## Admin endpoints

The telemetry endpoints live under the `/admin` router and require the
environment-provisioned admin secret `SABIROUTE_ADMIN_KEY` as a bearer token
(`security/auth.py::require_admin_key`). They are **not** the same as the
public unauthenticated `/health`.

| Method & path | Returns |
|---|---|
| `GET /admin/metrics` | `Metrics.snapshot()` |
| `GET /admin/latency` | `LatencyTracker.snapshot()` |
| `GET /admin/errors` | `ErrorTracker.counts()` — category → count |
| `GET /admin/usage` | `UsageTracker.totals()` — deployment → total tokens |
| `GET /admin/health` | `HealthRegistry.snapshot()` — passive health/cooldown state |

Public, unauthenticated liveness/readiness is separate: `GET /health`,
`GET /health/live`, `GET /health/ready`.

Admin authentication fails closed with a typed `503`
(`authentication_unavailable`) when `SABIROUTE_ADMIN_KEY` is unset, and refuses
a secret that starts with `sr_live_` or equals `LITELLM_MASTER_KEY`, so a
client credential can never be used as the admin credential.

## What this telemetry is not

- **In-memory, per process.** Restarting SabiRoute resets every counter and
  sample. There is no persistence or export yet; these snapshot endpoints are
  the only read surface. Durable per-request accounting is a *separate* system
  (the usage-event store) and is not the same data.
- **Counts only on `/admin/errors`.** `ErrorRecord.message` is stored (and
  redacted with `redact_secrets`) but not exposed by the endpoint today; it is
  a latent channel, noted in the code at the recording site.
- **Passive health.** `HealthRegistry` reflects observed success/failure and a
  cooldown; there is no active provider health checker wired (Phase 06 gap).
- **No content-quality signal.** A `200` whose `content` is empty because a
  reasoning model spent the whole `max_tokens` budget on reasoning
  (`finish_reason == "length"`) is recorded as a *successful execution* — it
  is, for telemetry purposes. Content quality/truncation is not a Phase 07
  concern and is not counted as an error.

## Reproducing the live evidence

`scripts/phase07_live_telemetry.py` starts a LiteLLM proxy from the
repository's own `config/config.yaml` routes, builds real gateway state, makes
one real request per alias (capped at three), then reads the admin endpoints
back and asserts the invariants. It prints JSON plus a human-readable table and
never prints a credential value.

```bash
PYTHONPATH="$PWD/src" \
SABIROUTE_ENV_FILE=/path/to/.env \
/path/to/.venv/bin/python scripts/phase07_live_telemetry.py
```

`--self-check` re-evaluates the captured 2026-11-23 run through the same
assertion logic with **zero network calls**, so the evaluator can be
regression-tested without spend.

Exit codes: `0` pass, `1` invariant failure or no usable completion, `3`
environment problem (missing credential, proxy would not start).
