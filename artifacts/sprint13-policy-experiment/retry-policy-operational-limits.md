# Retry policy: operational limits (measured 2026-10-12/13)

Scope: pinned proxy `ghcr.io/berriai/litellm:main-latest@sha256:de5b05…`
(arm64), drill configs in this directory, 10s proxy timeout. Evidence:
`results.json`, stub logs. Nothing here describes production traffic.

## Measured per-inbound-proxy-request stub counts

| Scenario | base (unset) | num_retries: 1 | num_retries: 0 |
|---|---|---|---|
| success | 1 | 1 | 1 |
| 401 | 1, no retry | 1, no retry | 1, no retry |
| 500 | 3 | 2 | 1 |
| reset | 3 | 2 | 1 |
| malformed-200 | 3 | 2 | 1 |
| hang | 3 (~37s) | 2 (~25s) | 1 (~13s) |
| delay12 | 3 (~38s) | 2 (~27s) | 1 (~13s) |
| 429 (`Retry-After: 2`) | 3 (~7s) | 2 (~7s) | 1 (~2s) |

429 was measured 2026-10-13 in `../sprint13-429-drill/results.json`: 3/2/1
stub requests across base/r1/r0 with ~2.3–2.7s inter-retry gaps,
consistent with honoring the stub's `Retry-After: 2` header. SabiRoute
treats upstream 429 as retryable (unit-tested).

Inter-retry gaps measured ~10–12s (≈10s timeout + backoff/overhead).
Proxy log corroboration (base): "Retried: 2 times, Max Retries: 2".

## Scenario maxima vs policy bounds (observed, not theoretical)

- Per proxy inbound: base ≤3, r1 ≤2, r0 =1 stub requests (for tested classes).
- Stacked with SabiRoute `max_attempts` (1–3 by policy): worst observed
  shape is attempts × per-attempt proxy retries (e.g., 2×3=6 for `fast`).
- 401 is the only tested class with zero retries in every variant.

## Why num_retries: 1 is not thereby production-correct

It halves worst-case executions in these tests, but production correctness
needs: live-provider confirmation, cost/billing analysis, and latency-budget
fit — none established here. The
pinned version offers no selective per-status retry knob (uniform
`num_retries` only); do not claim status-selective proxy retries exist.

## What remains unknown

Real provider executions/billing; other proxy versions; multi-fallback
configs; SabiRoute→drill-proxy live link; cancellation in-drill. A stub
count is evidence of requests reaching the stub — nothing more.
