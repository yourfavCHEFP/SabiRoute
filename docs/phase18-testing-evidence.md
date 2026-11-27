# Phase 18 — Testing & Regression: current evidence

Recorded 2026-11-24 on `feat/sabiroute-routing-foundation`.
Roadmap phase status is unchanged. This document records evidence, not a promotion.

## Verification basis (VERIFIED BY RUNTIME)

| gate | command | result |
|---|---|---|
| tests | `uv run pytest -q` | 1123 passed, 9 skipped |
| coverage | `uv run pytest -q --cov=sabiroute` | 4641 statements, 0 missed, 100% |
| lint | `uv run ruff check src tests scripts config` | clean |
| types | `uv run mypy src` | clean, 49 source files |
| whitespace | `git diff --check` | clean |

The nine skips are environment-gated on `SABIROUTE_TEST_REDIS_URL` /
`SABIROUTE_TEST_PG_URL`; none is a contract skip.

An earlier revision of this document recorded "1123 passed" while the suite then
collected 1125 tests and passed 1116. That figure was corrected to 1116 at the
time. Eight further tests for the in-flight interleavings described below have
since been added, so the suite now really reports 1123 passed of 1132 collected.
`scripts/test_models.py` and `scripts/test_providers.py` hold 3 further tests
that `testpaths = ["tests"]` excludes.

## What the 100% does and does not mean

Coverage reports 100%, but the figure is not produced by execution alone.
15 statements in `api/completions.py` carry `# pragma: no cover`. All 15 are
unexecuted lines, and they are measured rather than argued: running the suite
against a coverage config with `exclude_lines` emptied reports 800 statements in
the file and names exactly them — the two barrier bodies below plus the
`estimated_cost is None` branch.

This coverage figure is a measurement, not a claim about evidence quality. An
excluded branch that later becomes reachable will not appear in any coverage
report. Two regions are still excluded, and both are named below.

- the barrier bodies in `finish` and in the cancelled finalize. Each loop waits
  on another accounting worker's completion event, so the only way into its body
  is a cancellation arriving mid-wait while that worker is still in flight — the
  interleaving these tests never produced. It is now dead by construction rather
  than merely unreached: `_run_accounting` untracks on every exit path (success,
  exception, cancellation, and self-cancelled shielded worker), so `in_flight` is
  already `None` whenever either finish runs. The five statements per loop are
  kept — and excluded — as the barrier a future overlapping accounting call site
  would need, with the invariant recorded at both sites.
- the `estimated_cost is None` branch inside the retry loop. This one is not
  merely unreached — it cannot run. `estimated_cost` is computed once, before
  admission, and never reassigned, and a cost budget over candidates without
  pricing already answers 503 there, so no input reaches the branch. It is kept
  as the floor the cost arithmetic below it requires; the reason is recorded at
  the site so a later reader does not mistake it for an unproven path.

Further branches that were previously excluded here are now exercised by real
tests and no longer carry a pragma: a retry whose spend cannot be priced from the
provider's usage report, and a retry whose remaining budget floors to zero
output tokens. Both are reachable only on a route with a second candidate — a
single-alias request has no second attempt to refuse — so
`tests/test_completions_cost_caps.py` drives them through a registered
two-deployment route and asserts that exactly one upstream call happened.

The other two are the cancelled-attempt handlers reached only when cancellation
lands *inside* an attempt, holding an open stream: the close that fails while
the request is being finalized (it must not replace the recorded outcome) and
the reserved budget that becomes unknown usage once its deadline passed.
`test_a_cancelled_attempt_past_its_deadline_closes_the_stream_and_holds_the_budget`
(`tests/test_completions_freepool_and_stream.py`) cancels after the published
deadline elapses and asserts the deadline is still what telemetry records. A
cancellation that lands in the response generator instead is a different,
already-covered handler — it records "during streaming" — which is why the
sweep in the cancellation matrix could not reach these by cancelling offsets
alone.

A third group is the cancelled-request path, which finalizes telemetry like the
normal one and therefore meets the same store refusals. Two tests cancel while
admission is inside the store and let finalization fail — once as a validation
rejection, once as an outage — asserting the caller still gets a typed 503 and
that the store's own message is not echoed back. The rest make the *worker*
cancel itself, one cleanup step at a time: the quota release, the budget
release, and each of those on the pre-dispatch snapshot-failure path, including
the successful release that clears the flag. A worker that ends itself cancelled
re-raises on every await, so each of these is the same hazard as the shield-loop
bug one layer down, and each is now proven to end the request rather than stall
it.

The six re-raises beside the shielded cleanups were the last group recorded here
as unproven, and they are now exercised rather than argued. A store method that
runs on the worker thread cannot cancel the task, but it can raise
`asyncio.CancelledError`, which leaves the shielded worker ending itself
cancelled; from there each cleanup step is driven separately: the quota
settlement and the finalize in `finish`, the finalize on the cancelled path, the
budget release and the quota release in full compensation, and the quota release
that follows a cancelled budget reservation. Where the raised error is not a
cancellation, the release is recorded as `quota_cleanup_failed` and the caller
still receives its 499 — asserted, because that refusal is the one outcome the
invariant tolerates. Each of these tests would have hung the request before the
shield-loop guard, which is why they are assertions about completion and not
only about line coverage.

What that sweep also settled is why the two barrier bodies are unreachable:
`_run_accounting` untracks the in-flight worker on every path out, including the
self-cancelled one, so neither finish ever finds a barrier to wait on. The
barriers stay as defensive depth for a future overlapping call site, documented
at both sites and excluded here; nothing else in the file is excluded.

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
- No claim that the excluded branches are exercised. They are not: they are now
  only the two barrier bodies and the `estimated_cost is None` branch, and all
  fifteen lines are listed above by function and by measurement.
- No claim that the exclusion list is unreachable code. Both remaining regions
  are argued dead by construction — an invariant on `_run_accounting`'s exit
  paths, and a pre-check plus a value that is never reassigned — and each
  argument is recorded at its site, not only here.
- Coverage percentage is a proxy. The cancellation tests exist for the
  invariant, not the number.
