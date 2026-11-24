# Phase 18 — Testing & Regression: current evidence

Recorded 2026-11-24 on `feat/sabiroute-routing-foundation`.
Roadmap phase status is unchanged. This document records evidence, not a promotion.

## Verification basis (VERIFIED BY RUNTIME)

| gate | command | result |
|---|---|---|
| tests | `uv run pytest -q` | 1123 passed, 9 skipped |
| coverage | `uv run pytest -q --cov=sabiroute` | 4593 statements, 0 missed, 100% |
| lint | `uv run ruff check src tests scripts config` | clean |
| types | `uv run mypy src` | clean, 49 source files |
| whitespace | `git diff --check` | clean |

The nine skips are environment-gated on `SABIROUTE_TEST_REDIS_URL` /
`SABIROUTE_TEST_PG_URL`; none is a contract skip.

## What the 100% does and does not mean

Coverage now reports 100%, but the figure is not produced by execution alone.
62 statements in `api/completions.py` carry `# pragma: no cover` under explicit
owner authorisation. Of those, 46 were the named residual — branches that no
test could reach — and 16 were covered statements inside the same blocks that
block-level exclusion also removed.

This is the tradeoff accepted with that authorisation: the number is green, the
evidence is not stronger. An excluded branch that later becomes reachable will
not appear in any coverage report. The excluded regions are:

- cancellation handlers that run behind `shield_cancellation=True`. A sweep
  cancelling at seven offsets, three times in succession, and ten times in a
  burst, on both the budget and quota paths, did not reach them
  (`tests/test_completions_cancellation_matrix.py`).
- cost-cap branches behind the token retry gate, and one behind the pricing
  pre-check that returns 503 before the loop.
- the stream-cleanup and deadline-with-reservation branches.

## What is tested rather than excluded

The cancellation tests assert invariants, not lines: a cancelled request leaves
no quota reservation held, leaves no budget hold behind, and finalizes at most
once. `tests/test_completions_cleanup_failures.py` proves the compensation
handlers survive a store that refuses to release.

## What this document does not claim

- No phase status change.
- No claim that the excluded branches are exercised. They are not.
- Coverage percentage is a proxy. The cancellation tests exist for the
  invariant, not the number.
