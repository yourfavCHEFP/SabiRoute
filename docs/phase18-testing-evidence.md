# Phase 18 — Testing & Regression: current evidence

Recorded 2026-11-24 on `feat/sabiroute-routing-foundation`.
Roadmap phase status is unchanged. This document records evidence, not a promotion.

## Verification basis (VERIFIED BY RUNTIME)

| gate | command | result |
|---|---|---|
| tests | `uv run pytest -q` | 1077 passed, 9 skipped |
| coverage | `uv run pytest -q --cov=sabiroute --cov-report=term-missing` | 4655 statements, 54 missed, 99% |
| lint | `uv run ruff check src tests scripts config` | clean |
| types | `uv run mypy src` | clean, 49 source files |
| whitespace | `git diff --check` | clean |

The nine skips are environment-gated on `SABIROUTE_TEST_REDIS_URL` /
`SABIROUTE_TEST_PG_URL`; none is a contract skip.

Coverage is measured as a union across the whole suite. Per-file coverage runs
report every other module as largely missed and are not a valid measure here.

## Module coverage

Every module is at 100% except `api/completions.py` at 93%.

The authoritative residual list is the output of
`uv run coverage report --show-missing`, filtered to that file. It is not
reproduced here because it changes with every commit; the groups below are the
durable description.

## Named residual — `api/completions.py` (54 statements)

### 1. Cancellation interleavings not exercised

The accounting layer absorbs more than one cancellation: while `finish` waits
for an in-flight worker, inside `_compensate_all` when a release is itself
cancelled, inside `_cancelled_finish`, inside `snapshot_persistence_failure`,
and during quota/budget release.

**Tested** (`tests/test_completions_cancellation.py`): one cancellation landing
while a reservation worker is mid-call, and a second landing while the handler
waits for it. The assertions are the invariants, not the lines: a cancelled
request leaves no quota reservation held, leaves no budget hold behind, and
finalizes exactly once.

**Not tested**: a third cancellation during compensation, cancellation during
snapshot persistence, and cancellation during stream cleanup. If a leak exists
in one of those schedules, this suite will not find it.

### 2. Cost-cap branches that cannot be reached

Three monetary-cap statements on the second loop iteration cannot be reached
while a budget is reserved: for a cost budget the token retry gate answers
first whenever the failed attempt reports usage. A fourth is preceded by the
pricing pre-check that returns 503 before the loop.

Closing them would require disabling the gate above them, which would assert a
schedule the code cannot produce. They are recorded as defensive, not as gaps.

**Tested** (`tests/test_completions_cost_caps.py`): an unpriced routed
deployment stops the retry even when an estimate exists, and an input cost that
already exhausts the budget admits nothing.

### 3. Quota-estimator refusal

Capability classification refuses a multimodal payload before the quota gate is
reached, so the estimator's refusal cannot be driven without a deployment that
declares that capability. Unverified.

### 4. Defensive attribute guard

One guard sits behind an `isinstance(..., dict)` check on the same expression,
so no input currently reaches it. Recorded rather than contrived.

## What this document does not claim

- No phase status change.
- No claim that cancellation safety is fully verified. The two tested invariants
  are named above, and the untested interleavings are named beside them.
- Coverage percentage is a proxy. The value of the cancellation tests is the
  invariant they assert, not the lines they colour.
