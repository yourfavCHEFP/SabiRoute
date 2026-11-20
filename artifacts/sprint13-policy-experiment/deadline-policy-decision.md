# Deadline policy decision (specification, not implemented)

Status: proposal awaiting owner approval. No code changed. Numeric values
below are recommendations flagged as such — none are adopted.

## 1. Verified architectural findings

- One logical request (`request_id`, `completions.py:206`) can perform up
  to `max_attempts` SabiRoute attempts (default 2; ultimate/coding/
  reasoning/research 3; route files default 1) via the loop at
  `completions.py:538`. Every exit path is a terminal `return finish()`
  or re-raise; finalization runs exactly once (tested).
- Per-attempt timeout: SabiRoute client default 120s; proxy repo default
  120s (10s drill-only). No total deadline exists anywhere in the path.
- Cancellation propagates as `asyncio.CancelledError`, finalized as
  `client_cancelled`, never touching provider-failure accounting.
- Drill measurements (pinned digest, in `results.json`): retryable proxy
  failures cost 3/2/1 stub requests under unset/r1/r0; 401 never retried;
  429 never drilled (labeled unmeasured in `retry-policy-operational-
  limits.md`); hang/delay ≈10s per proxy attempt plus ~1–2s gaps.

## 2. Recommended model: B (derived remaining-time budget)

Deadline = `max_attempts × (per-attempt timeout + 10s slack)`, computed
from live config at admission with a monotonic clock, re-checked before
every attempt (including the first). At today's 120s timeout: `fast`/
`cheap` → 260s; three-attempt policies → 390s. Rationale: adapts per
policy, inputs are live config (only the 10s slack is a new constant),
worst case is computable per route. Model A (one fixed total) is the
fallback if simplicity wins — proposed range 180–300s, with the caveat
that 180s can truncate three-attempt policies mid-sequence. Model C
(external deadline in) is rejected: no caller supplies one, and it adds
unauthenticated timing input to a security-sensitive path.

## 3. Proposed numeric default (AWAITING APPROVAL)

Model B formula with 10s slack, evaluated against live config at runtime
— i.e., no hardcoded seconds. If a single fallback number is required
for operations docs: 300s (covers a full 120s attempt + one fallback +
slack; three-attempt policies rely on the derived 390s instead).

## 4. Streaming and cancellation decisions

- Pre-first-byte (open fails or deadline passes first): 503
  `deadline_exceeded`, no attempt starts — status still changeable.
- Post-first-byte: status sent; stop yielding, end **without** `[DONE]`
  (truncation signals incompleteness), finalize failure /
  `deadline_exceeded`. Never synthesize success; never promise a 503
  after headers.
- Disconnect/caller cancel → `client_cancelled` (existing paths
  untouched); deadline expiry is a separate category. Neither proves
  remote execution stopped — the deadline bounds SabiRoute waiting only.

## 5. Retry recommendation and trade-offs

**r1 + deadline (Option C)** as the production candidate: halves
worst-case upstream executions vs defaults (measured 2 vs 3 per proxy
inbound) while absorbing single transient blips; deadline caps the
stacked worst case (e.g., fast: 2 attempts × 2 proxy tries). r0 remains
defensible if provider-relations dominate (same-provider 429 hammering
is the sharpest cost of proxy-level retries). 429 proxy behavior is
unmeasured — close it in the lab before finalizing. Uniform `num_retries`
only; status-selective proxy retries do not exist in the pinned version.

## 6. Regression tests required (`tests/test_completions.py` unless noted)

1. Past deadline at admission → no attempt, 503, finalized.
2. Expiry mid-attempt (fake monotonic advance) → stop, no further attempt.
3. Expiry between fallbacks → second attempt never starts.
4. Remaining < needle time → attempt skipped (backoff-overflow rule).
5. Cancel during wait → `client_cancelled`, never `deadline_exceeded`.
6. Pre-stream expiry → 503, no stream started.
7. Post-stream-start expiry → truncated end, failure/`deadline_exceeded`.
8. Disconnect mid-stream → `client_cancelled` (existing tests stand).
9. Finalize-once counter unchanged on all expiry paths.
10. Unknown usage stays null on expiry.
11. Malformed-200, bounded-fallback, health tests pass unmodified.
12. r1 drill re-run (lab, authorized separately) confirms 2× counts.

Fake monotonic clock at the completions boundary; controlled hung/reset
transports; zero sleep-based assertions.

## 7. Likely implementation files (future, approved separately)

`api/completions.py` (deadline capture/gate/finish paths),
`gateway.py` + config models (budget plumbing: new optional setting),
`tests/test_completions.py`, failure-injection matrix doc row. No scoring,
policy, schema, gate, or public-API changes.

## 8. Uncertainty and approvals needed

Unknown: openai-constant value in-image (behaviorally covered),
429 proxy count, multi-fallback configs, live/billing truth. Approvals:
model choice, numeric budget/slack, streaming truncation rule, r1 vs r0,
429-closing drill, any implementation or proxy config change, pushes.
