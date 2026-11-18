# Failure-Injection Runbook — SabiRoute

**Status:** documentation only. No code changes. Authored during the 2026-10-26
five-hour mobilization. Exercises the deterministic fallback, retry, and cooldown
paths that are currently unit-tested but lack live failure-injection evidence
(Phase 01/05 gap).

## Scope

- `src/sabiroute/api/completions.py` — completion retry/fallback loop
- `src/sabiroute/routing/health.py` — passive cooldown
- `tests/test_fallback_injection.py` — in-process failure-injection coverage

## Preconditions

- Local gateway running with at least two configured deployments for one model
  (e.g. `primary`, `secondary`).
- A stub LiteLLM client or a provider that can be forced to fail on demand.
- `SABIROUTE_TEST_REDIS_URL` / `SABIROUTE_TEST_PG_URL` optional for
  persistence-gated paths.

## Scenarios

### 1. Retryable provider failure → fallback to next deployment

1. Configure model `fast` with deployments `primary`, `secondary`.
2. Force `primary` to return a retryable error (timeout or 5xx).
3. Send `POST /v1/chat/completions` with `{"model": "fast", ...}`.
4. Expected: response succeeds via `secondary`; telemetry records the failed
   attempt on `primary` and the successful attempt on `secondary`.
5. Evidence: inspect usage events / attempt log for both attempts.

### 2. Non-retryable failure → no fallback

1. Force `primary` to return a non-retryable error (auth failure, 4xx).
2. Expected: no retry and no attempt on `secondary`. SabiRoute does not
   return the upstream status to the client: the terminal response is HTTP
   502 `sabiroute_upstream_error` with `failure_category` set to the classified
   category (e.g. `"client"` for HTTP 400).
3. Evidence: single attempt recorded.

### 3. Cooldown after repeated failures

1. Force `primary` to fail repeatedly (>= cooldown threshold).
2. Expected: `primary` enters cooldown; subsequent requests route to
   `secondary` only; `primary` excluded from candidate set while cooling.
3. Evidence: health state shows cooldown expiry; request routing skips
   `primary`.

### 4. Cooldown recovery

1. After scenario 3, wait for cooldown expiry (or advance test clock).
2. Expected: `primary` re-enters candidate set; next request may route to it.
3. Evidence: health state cleared; routing includes `primary`.

### 5. All deployments exhausted

1. Force every deployment for a model to fail.
2. Expected: request fails with a classified provider error (not an unexplained
   global error); no silent success.
3. Evidence: error type matches failure classification (§7 of CLAUDE.md).

## Failure classification reference

Distinguish: model unavailable · route unavailable · provider unavailable ·
account/credit problem · authentication failure · rate limit · timeout ·
network failure · configuration error · LiteLLM execution failure ·
SabiRoute failure.

## Limitations

- Live failure-injection evidence is **not** yet captured in this repository.
  This runbook defines the procedure; executing it requires a provider or stub
  capable of deterministic failure injection and is gated on environment
  availability. No claim of completion is made.
- In-process retry, fallback, and passive-cooldown paths are covered by
  `tests/test_fallback_injection.py`; this is not live failure-injection evidence.
- The live path is the retry loop in `src/sabiroute/api/completions.py` with
 cooldown state from `src/sabiroute/routing/health.py`; no active provider health
 checker is wired.

## Evidence to capture when run

- Exact command, environment, and provider/stub version.
- Request/response payloads (sanitized, no secrets).
- Telemetry attempt records and health-state transitions.
- Pass/fail per scenario with timestamps.
