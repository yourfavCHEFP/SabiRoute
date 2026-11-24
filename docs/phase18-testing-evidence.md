# Phase 18 — Testing & Regression: current evidence

Recorded 2026-11-24 on `feat/sabiroute-routing-foundation`.
Roadmap phase status is unchanged. This document records evidence, not a promotion.

## Verification basis (VERIFIED BY RUNTIME)

| gate | command | result |
|---|---|---|
| tests | `uv run pytest -q` | 1123 passed, 9 skipped |
| coverage | `uv run pytest -q --cov=sabiroute` | 4655 statements, 46 missed, 99% |
| lint | `uv run ruff check src tests scripts config` | clean |
| types | `uv run mypy src` | clean, 49 source files |
| whitespace | `git diff --check` | clean |

The nine skips are environment-gated on `SABIROUTE_TEST_REDIS_URL` /
`SABIROUTE_TEST_PG_URL`; none is a contract skip.

## Module coverage

Every module is at 100% except `api/completions.py` at 94% (46 statements).

## The 46 statements in `api/completions.py`

### A. Cancellation handlers the shield prevents from firing (41 statements)

These are the `except asyncio.CancelledError: raise` and re-wait lines inside
`finish`, `_compensate_all`, `_cancelled_finish`, `snapshot_persistence_failure`
and the quota-cleanup paths. Every accounting call on these paths runs with
`shield_cancellation=True`, which re-waits the cancellation instead of
propagating it.

**Evidence that they are not reachable by cancellation schedule
(VERIFIED BY RUNTIME):** `tests/test_completions_cancellation_matrix.py`
cancels the request at seven offsets, three times in succession, and ten times
in a burst, on both the budget and quota paths. None of those schedules moves
the missing count. The invariant assertions pass, which is the point of the
tests; the lines stay uncovered, which is the point of this note.

**Covered on these paths instead:** a store that refuses a release
(`tests/test_completions_cleanup_failures.py`) exercises the `except Exception`
compensation handlers around them.

### B. Cost-cap branches (3 statements)

- One is arithmetically unreachable: the cost block runs only when a monetary
  budget exists, and the pricing pre-check returns 503 before the loop when no
  estimate can be produced.
- Two sit behind the token retry gate, which answers first for every budget
  shape tested, including a combined token+cost budget.

Two cost-cap branches **are** covered (`tests/test_completions_cost_caps.py`).

### C. Stream cleanup and deadline (2 statements)

The stream-cleanup failure path and the deadline-with-reservation branch.
Not driven; no attempt is claimed.

## What this document does not claim

- No phase status change.
- No claim of 100% coverage. The 46 statements are named by group above.
- Coverage percentage is a proxy. The cancellation tests exist to assert
  invariants (no hold left behind, at most one finalize), not to colour lines.
