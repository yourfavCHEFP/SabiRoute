# Final audit prompt — Phase 18 test tranche (SabiRoute)

You are auditing a completed body of test work in the repository at
`/Users/airm2/My ML Hub/SabiRoute` (quote the path; it contains spaces).
You have read-only intent: do not modify source, tests or documentation, do not
commit, do not push, do not rebase or merge. Report findings only.

## Context you must not take on trust

The branch is `feat/sabiroute-routing-foundation`. It is **diverged from origin**
and nothing in this tranche has been pushed. Do not attempt to reconcile it.

The work under audit raised test coverage of the SabiRoute package and consists
of these new or modified test files plus one document:

- `tests/test_completions_helpers.py`
- `tests/test_completions_admission_branches.py`
- `tests/test_completions_freepool_and_stream.py`
- `tests/test_completions_cost_caps.py`
- `tests/test_completions_cancellation.py`
- `tests/test_completions_cancellation_matrix.py`
- `tests/test_completions_reachable_edges.py`
- `tests/test_completions_cleanup_failures.py`
- `tests/test_dataset_integrity_branches.py`
- `tests/test_dataset_residual_branches.py`
- `tests/test_auth_dependencies.py`
- `docs/phase18-testing-evidence.md`

## Claims to falsify

Treat every one as a hypothesis. Attempt to disprove it before accepting it.

1. **Coverage claim.** The package reports 100%: 4593 statements, 0 missed.
   Reproduce with:
   ```
   uv run pytest -q --cov=sabiroute --cov-report=term-missing
   ```
   Report the exact totals. Then audit the exclusions: 62 statements in
   `api/completions.py` carry `# pragma: no cover`. List every pragma with its
   line number and the code it excludes. Confirm that each sits on a defensive
   branch (cancellation handler, cost-cap guard, stream/deadline branch) and
   flag any pragma that excludes ordinary request logic. Before the pragmas the
   file measured 4655 statements; confirm the 62-statement difference and say
   how many of those were already covered (claimed: 16).

2. **Unreachability claim (the 41 cancellation statements).** The `except
   asyncio.CancelledError: raise` and re-wait lines in `finish`,
   `_compensate_all`, `_cancelled_finish`, `snapshot_persistence_failure` and the
   quota-cleanup paths are said to be shielded by `shield_cancellation=True` and
   therefore not reachable by any cancellation schedule. Removing the pragmas
   from a scratch copy (outside the repository) and experimenting is allowed;
   changing this repository is not.
   Try to disprove this. Write a scratch script **outside** the repository (for
   example under `/tmp`) that drives `chat_completions` with different
   cancellation patterns (offsets, repeated cancels, cancels inside a blocked
   store call, cancels during cleanup) and check whether the missing-line count
   can be moved. Report the best count you can reach and the schedules you tried.
   Do not add your scratch work to the repository.

3. **Arithmetic claim (1 statement).** One cost-cap line is said to be
   unreachable because a monetary budget cannot reach the loop without a
   non-`None` estimate: the pricing pre-check returns 503 first. Read the
   handler and confirm or refute the ordering.

4. **Test quality.** For each new test file, identify any test that would still
   pass if the branch it names were removed or broken. Specifically check that:
   - the cancellation tests assert invariants (no lease left held, at most one
     finalize) rather than merely completing without exception;
   - the cost-cap tests assert the number of provider calls where the break is
     the subject;
   - no test asserts a status code that an unrelated guard would also produce.

5. **Flakiness.** Run the cancellation files five times:
   ```
   for i in 1 2 3 4 5; do uv run pytest -q tests/test_completions_cancellation.py tests/test_completions_cancellation_matrix.py tests/test_completions_cleanup_failures.py || echo "RUN $i FAILED"; done
   ```
   Report any failure and whether it looks like scheduling or behaviour.

6. **Hygiene.** Confirm: `uv run ruff check src tests scripts config` is clean;
   `uv run mypy src` is clean; `git diff --check` is clean; no `.env`, `uv.lock`,
   `.github/**`, `.mcp.json`, `.claude/**`, `brag-output/**` or
   `reports/provider_verification.json` was modified in this tranche; no secret
   literal was added to a test file; no commit was amended, reset or rewritten.

7. **Evidence honesty.** Compare `docs/phase18-testing-evidence.md` against what
   the code and tests actually do. Flag any sentence in that document that
   overstates what is proven, and any claim of "unreachable" that your own
   experiment contradicts.

## Output format

For each numbered claim: `PASS`, `FAIL`, or `UNVERIFIABLE`, with the command you
ran and a short excerpt of output. Then a section **Weak tests** listing any test
that could pass without exercising its branch, and a section **Overclaims**
listing any documentation statement you could not substantiate.

End with a one-word verdict: `CLEAN` or `NOT CLEAN`.
