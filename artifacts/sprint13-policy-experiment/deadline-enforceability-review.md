# Deadline enforceability review (audit, not implemented)

Status: findings + corrected design. No code changed. This document
supersedes the numeric derivation in `deadline-policy-decision.md` where
they conflict; the decision doc's categories, streaming rules, and test
strategy stand except as noted below.

## 1. Source-grounded findings

- `LiteLLMClient` builds `httpx.Timeout(timeout_seconds)` with the scalar
  form (installed httpx 0.28.1, `_config.py:86-131`). A scalar fans out to
  **four independent per-operation ceilings**: connect, read, write, pool
  (120s each at the 120s default).
- Consequence 1: a non-streaming attempt is bounded not by 120s but by up
  to ~120s connect + ~120s write + ~120s read in the adversarial case.
- Consequence 2: for streamed responses each chunk read carries its own
  read window, so a slow-but-steady stream is effectively unbounded by
  `httpx.Timeout` (it bounds inactivity, not total duration).
- No absolute-timeout mechanism (`asyncio.timeout`/`timeout_at`/
  `wait_for`) exists anywhere in `src/sabiroute/`; no total-deadline
  symbol exists in `completions.py` (verified by search).
- Status taxonomy: 504 is never emitted; 503 means unavailable,
  502 upstream-error, 499 caller cancel. `asyncio.CancelledError` never
  enters provider-failure accounting.

## 2. Formula verdict: NOT enforceable as specified

`total = max_attempts × (per-attempt timeout + 10s slack)` treats the
120s scalar as a per-attempt wall-clock bound. It is not one (§1). The
260s/390s derived values are therefore **not bounds** — adversarial
single attempts can exceed them, and trickling streams ignore them
entirely. The gate-before-attempt check in the decision doc remains
valid and necessary, but it bounds attempt *starts*, not elapsed time.
Do not adopt the formula without the enforcement mechanism in §3.

## 3. Recommended enforceable design

Wrap the post-admission request scope (attempt loop + streaming
generator drive + finalization) in a single `asyncio.timeout_at`
deadline computed from a monotonic start. Per-operation httpx timeouts
stay as the inner layer; the absolute timeout is the outer bound, so
worst case = deadline + bounded synchronous cleanup. Keep the
before-every-attempt remaining-budget gate as the graceful path (clean
503 + finalized telemetry) and the absolute timeout as the backstop
(interrupts a hung await that ignores per-operation limits).

- Start point: endpoint entry (true ingress), not post-admission.
  Rationale: auth/admission are SabiRoute-owned work (Redis I/O bounded
  at ~5s) and should be inside the budget; the difference is small and
  the semantics ("no logical request lives past N") are cleaner.
- No client-supplied deadlines (unauthenticated timing input rejected
  as before).
- Remote caveat preserved: expiring the local wait cancels local work;
  it never proves upstream execution stopped.

## 4. Streaming and status decisions

- Pre-first-byte expiry: 503 `deadline_exceeded`, no attempt starts.
- Post-first-byte expiry: terminate iteration, end without `[DONE]`,
  finalize failure/`deadline_exceeded`. Never emit a new status after
  headers; never synthesize success.
- Status choice: **503**, not 504. 504 is unused in this codebase and
  would mint a new client-visible contract; 503 already means
  "cannot complete" and matches the existing unavailable family.
  Disconnect stays `client_cancelled`; malformed-200, health, usage-null
  rules unchanged.

## 5. Numeric policy (proposed, awaiting approval)

With true enforcement (§3), the number becomes a real bound. Proposed:
**300s default total** — covers a full adversarial single attempt plus a
fallback plus finalization slack, sits below common 600s client
timeouts, and is short enough to matter. Streaming responses: exempt
post-first-byte (governed by 120s read-inactivity + a future explicit
idle policy, owner decision). Per-policy derivation (Model B) is
withdrawn as primary: it inherited the false per-attempt premise; keep
the formula only as documentation of how 300s relates to policy depths.

## 6. Regression tests (append to the D.2 §E list)

- Absolute timeout fires mid-hung-await (fake clock + `timeout_at`
  semantics asserted via controlled hanging transport, bounded 0.5s
  client timeouts as in existing census tests — no real sleeps at scale).
- Slow-trickle stream exceeding the deadline is terminated (chunk feeder
  with scripted delays under a short test deadline).
- Gate-before-attempt still prevents starts (existing planned tests).
- All nine D.2 §E cases unchanged.

## 7. Unknowns and approvals needed

Unknown: provider-side time behavior; exact backoff magnitudes; live
413/429 interplay. Approvals: 300s default (or alternate), streaming
exemption rule, `asyncio.timeout_at` mechanism choice, any proxy change,
implementation + push. The D.3 decision doc's model comparison is
superseded on numerics only; its categories, streaming rules (modulo
§4's 503 rationale), and test strategy are confirmed.
