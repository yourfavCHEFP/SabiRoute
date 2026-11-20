# SabiRoute end-to-end deadline: design (not implemented)

Status: design candidate. No code changed. Implementing it alters routing
timing policy and needs explicit owner approval plus the tests below.

## A. Lifecycle

- Start: `time.monotonic()` captured when the logical request is admitted
  (after auth/admission, before candidate selection), stored on the
  request scope alongside `request_id`.
- One total budget per logical request (value: owner decision; see §D).
- Before every attempt (including the first), compute
  `remaining = deadline - monotonic_now()`; if `remaining <= 0`, stop —
  no new attempt begins, including no first attempt.
- On expiry: return 503 (not 502: nothing was necessarily attempted and
  nothing failed upstream) with a distinct `deadline_exceeded` category;
  finalize telemetry normally (attempts recorded so far + expiry marker);
  reconcile/release budget by the existing rules.
- Cleanup: close the in-flight HTTP session, abort the SSE generator,
  release budget reservation — reusing the existing cancellation cleanup
  paths, not new ones.

## B. Nested timeout ownership

| Limit | Owner | Enforceable from SabiRoute? |
|---|---|---|
| Total logical-request deadline | SabiRoute (new) | Yes — gate before each attempt |
| Per-attempt timeout | SabiRoute `LiteLLMClient` (120s default) | Yes — but must be ≤ remaining budget or it is meaningless; clamp or skip attempt when smaller |
| HTTP connect/read | httpx (inside per-attempt) | Config only |
| Proxy timeout | proxy config (120 repo / 10 drill) | Advisory to SabiRoute; observed, not controlled |
| Provider SDK timeout | proxy deployment | Not visible; unknown |
| Retry delay/backoff | proxy internals | Not controllable; measured ~1–2s gaps |
| Client cancellation | caller | Observed via `CancelledError`; never conflated |
| Deadline expiry | SabiRoute (new) | Internal signal, distinct category |

A per-attempt timeout is not a deadline: three 10s proxy attempts plus
backoff measured 37–38s wall-clock against a single logical request.

## C. Cancellation and error semantics (preserved)

- `asyncio.CancelledError` stays provider-failure-free; deadline expiry
  gets its own `deadline_exceeded` category (never `client_cancelled`).
- `timeout` vs `transport` distinction unchanged.
- Expired-deadline attempts do not mark health (no attempt ran); timed-out
  attempts keep current retryable-failure health handling.
- Unknown usage stays null; no zeroes invented on expiry.
- Finalization runs exactly once on every expiry path (same `finish()`
  discipline as today).
- Malformed-200 no-retry contract unchanged.
- Cancelling the local HTTP wait does not prove upstream work stopped:
  the deadline bounds SabiRoute waiting, never claims remote undo.

## D. Budget models (no hardcoded value)

- Model 1 — fixed total (e.g., owner-set seconds): simplest; worst case =
  deadline regardless of attempt count. Requires owner to pick the number.
- Model 2 — derived: `attempts_allowed × (per-attempt timeout + retry
  slack)` from live config: adapts to policy but inherits proxy-timeout
  assumptions; needs the proxy timeout as an input, currently 120s repo
  default (10s in drills — never mix drill numbers into prod math).
- Model 3 — per-policy budgets: different totals for interactive
  (`fast`) vs background routes. Most expressive, most config surface.
- Owner decisions required: the numeric budget(s); whether streaming
  responses (long-lived by nature) are exempt or bounded separately;
  whether `Retry-After`/backoff advice shortens the deadline.

## E. Regression-test strategy (fake clocks, controlled transports)

1. Deadline already past at admission → no attempt, 503, finalized.
2. Deadline expires mid-attempt (fake clock advance) → stop, no further
   attempt, `deadline_exceeded`.
3. Expiry between fallback attempts → second attempt never starts.
4. Caller cancel during wait → `client_cancelled`, not `deadline_exceeded`.
5. Retry/backoff longer than remaining → attempt skipped.
6. Unknown usage on expiry stays null (no fabricated tokens/cost).
7. Finalize-once counter unchanged on all expiry paths.
8. Malformed-200 tests still pass unmodified.
9. Cancellation never marks health (existing test still passes).

## F. Telemetry/ML notes

No schema change proposed. Deadline expiry adds one categorical value to
existing fields; attempt latency remains SabiRoute-attempt latency (proxy
internals still opaque). Dataset gates untouched; this design creates no
training data and changes no eligibility.
