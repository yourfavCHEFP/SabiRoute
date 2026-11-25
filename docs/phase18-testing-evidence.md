# Phase 18 — Testing & Regression: current evidence

Recorded 2026-11-24 on `feat/sabiroute-routing-foundation`.
Roadmap phase status is unchanged. This document records evidence, not a promotion.

## Verification basis (VERIFIED BY RUNTIME)

| gate | command | result |
|---|---|---|
| tests | `uv run pytest -q` | 1106 passed, 9 skipped |
| coverage | `uv run pytest -q --cov=sabiroute` | 4597 statements, 0 missed, 100% |
| lint | `uv run ruff check src tests scripts config` | clean |
| types | `uv run mypy src` | clean, 49 source files |
| whitespace | `git diff --check` | clean |

The nine skips are environment-gated on `SABIROUTE_TEST_REDIS_URL` /
`SABIROUTE_TEST_PG_URL`; none is a contract skip.

An earlier revision of this document recorded "1123 passed". That figure did not
reproduce: a plain `uv run pytest -q` collects 1115 tests, of which 1106 pass and
9 skip. `scripts/test_models.py` and `scripts/test_providers.py` hold 3 further
tests that `testpaths = ["tests"]` excludes, so even counting them reaches 1109,
not 1123. The recorded number is corrected here rather than explained away.

## What the 100% does and does not mean

Coverage reports 100%, but the figure is not produced by execution alone.
58 statements in `api/completions.py` carry `# pragma: no cover`. Of those, 42
are branches this suite does not reach and 16 are covered statements inside the
same blocks that block-level exclusion also removed.

This coverage figure is a measurement, not a claim about evidence quality. An
excluded branch that later becomes reachable will not appear in any coverage
report. The excluded regions are:

- cancellation handlers that run behind `shield_cancellation=True`. A sweep
  cancelling at seven offsets, three times in succession, and ten times in a
  burst, on both the budget and quota paths, did not reach them
  (`tests/test_completions_cancellation_matrix.py`). This is a record of what
  the sweep did not reach; it is not proof the handlers are unreachable.
- the `estimated_cost is None` branch inside the retry loop, which the pricing
  pre-check answers with a 503 before the loop is entered.
- the stream-cleanup and deadline-with-reservation branches.

Two branches that were previously excluded here are now exercised by real tests
and no longer carry a pragma: a retry whose spend cannot be priced from the
provider's usage report, and a retry whose remaining budget floors to zero
output tokens. Both are reachable only on a route with a second candidate — a
single-alias request has no second attempt to refuse — so
`tests/test_completions_cost_caps.py` drives them through a registered
two-deployment route and asserts that exactly one upstream call happened.

## What is tested rather than excluded

The cancellation tests assert invariants, not lines: a cancelled request leaves
no quota reservation held, leaves no budget hold behind, and finalizes at most
once. The matrix counts a cleanup only after the store call returns, so a
reconciliation that was attempted and refused does not satisfy the invariant.
`tests/test_completions_cleanup_failures.py` proves the compensation handlers
survive a store that refuses to release, and asserts that the refusal is
recorded and does not replace the response the caller was owed.

## What this document does not claim

- No phase status change.
- No claim that the excluded branches are exercised. They are not.
- No claim that the exclusion list is unreachable code. Reachability was argued
  for two branches and those two are now tested; the rest rests on the
  pre-check and on the sweep above, which is evidence about what the tests did,
  not about what the code permits.
- Coverage percentage is a proxy. The cancellation tests exist for the
  invariant, not the number.
