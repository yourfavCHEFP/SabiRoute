# R8 EXECUTIONER RECORD — stable SHA 1d91f73

**Issued:** 2026-11-17
**Stable SHA:** `1d91f73b1c551d1b259c1cf1a44c3e18203b8222`
**Branch:** `sec/deps-nov`
**Evidence labels:** `[VERIFIED BY INSPECTION]` for git state; `[VERIFIED BY RUNTIME]` for gate output.
**Verdict:** `GATES GREEN · T1/T8 NOT ISSUED · OWNER GREEN NOT ISSUED · R8 NOT ACCEPTED`

---

## 0. Preconditions `[VERIFIED BY INSPECTION]`

| Check | Observed value |
|---|---|
| `git rev-parse HEAD` | `1d91f73b1c551d1b259c1cf1a44c3e18203b8222` |
| `git rev-parse --abbrev-ref HEAD` | `sec/deps-nov` |
| `git diff --quiet && git diff --cached --quiet` | clean tracked tree (`TRACKED_TREE_CLEAN`) |
| `./.venv/bin/python --version` | `Python 3.11.15` |
| `./.venv/bin/python -m ruff --version` | `ruff 0.16.9` |
| `./.venv/bin/python -m mypy --version` | `mypy 2.3.1 (compiled: yes)` |
| `REPORTS-MANIFEST.sha256` | present |

The requested `pytest -q` gate was executed as `./.venv/bin/python -m pytest -q` to use the project
interpreter explicitly. Ruff and mypy were likewise invoked through `./.venv/bin/python -m` for the
same reason.

---

## 1. Gate 1 — pytest `[VERIFIED BY RUNTIME]`

**Requested:** `pytest -q`
**Executed:** `./.venv/bin/python -m pytest -q`
**Exit code:** `0`

Exact output:

```text
........................................................................ [ 8%]
........................................................................ [ 16%]
........................................................................ [ 25%]
........................................................................ [ 33%]
........................................................................ [ 42%]
...........................................................ss........... [ 50%]
........................................................................ [ 59%]
................................s....................................... [ 67%]
......................................................................ss [ 76%]
ss...................................................................... [ 84%]
........................................................................ [ 93%]
....s..................................................ss [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/test_r3_real_service_controls.py:373: SABIROUTE_TEST_REDIS_URL is not set; real Redis control skipped
SKIPPED [1] tests/test_r3_real_service_controls.py:437: SABIROUTE_TEST_PG_URL is not set; real PostgreSQL control skipped
SKIPPED [1] tests/test_r6_registration_digest_conformance.py:570: awaiting authorised ledger instantiation
SKIPPED [1] tests/test_rate_limit_redis.py:81: SABIROUTE_TEST_REDIS_URL is not set; Redis integration tests skipped
SKIPPED [1] tests/test_rate_limit_redis.py:92: SABIROUTE_TEST_REDIS_URL is not set; Redis integration tests skipped
SKIPPED [1] tests/test_rate_limit_redis.py:103: SABIROUTE_TEST_REDIS_URL is not set; Redis integration tests skipped
SKIPPED [1] tests/test_rate_limit_redis.py:114: SABIROUTE_TEST_REDIS_URL is not set; Redis integration tests skipped
SKIPPED [1] tests/test_shared_inference.py:462: SABIROUTE_TEST_PG_URL is not set; PostgreSQL integration tests skipped
SKIPPED [1] tests/test_user_quotas.py:584: SABIROUTE_TEST_PG_URL is not set; PostgreSQL integration tests skipped
SKIPPED [1] tests/test_user_quotas.py:614: SABIROUTE_TEST_PG_URL is not set; PostgreSQL integration tests skipped
839 passed, 10 skipped in 22.02s
```

Skips are disclosed, not hidden. Eight are environment-gated on `SABIROUTE_TEST_REDIS_URL` or
`SABIROUTE_TEST_PG_URL`; one is the registration-ledger skip at
`tests/test_r6_registration_digest_conformance.py:570`; one is recorded by the conformance suite.

---

## 2. Gate 2 — ruff `[VERIFIED BY RUNTIME]`

**Requested and executed:** `./.venv/bin/python -m ruff check src tests scripts config`
**Exit code:** `0`

Exact output:

```text
All checks passed!
```

---

## 3. Gate 3 — mypy `[VERIFIED BY RUNTIME]`

**Requested and executed:** `./.venv/bin/python -m mypy src`
**Exit code:** `0`

Exact output:

```text
Success: no issues found in 61 source files
```

---

## 4. Gate 4 — report manifest `[VERIFIED BY RUNTIME]`

**Requested and executed:** `shasum -a 256 -c REPORTS-MANIFEST.sha256`
**Exit code:** `0`

Exact output:

```text
reports/audit-acceptance-and-disposition.md: OK
reports/implementation_12h.md: OK
reports/mission-c-evidence-audit-2026-10-26.md: OK
reports/mission-runlog-2026-10-26T095838.md: OK
reports/mobilization-reconciliation-2026-10-26.md: OK
reports/my_scorecard.md: OK
reports/part-i-sprints-1-8-overnight-report-2026-10-26.md: OK
reports/pre-roadmap-audit.md: OK
reports/provider_verification.json: OK
reports/r02-kill-switch-remediation.md: OK
reports/reconciliation-plan.md: OK
reports/remediation-roadmap-and-gates.md: OK
reports/sprint-02b-unattended-core.md: OK
```

---

## 5. Gate 5 — diff check `[VERIFIED BY RUNTIME]`

**Requested and executed:** `git diff --check`
**Exit code:** `0`
**Exact output:** no output.

---

## 6. Scope exclusions

No deployment, provider call, managed service, registration ledger, flag change, `training_authorized`
change, workflow run, stage, commit, push, PR, merge, rebase, reset, checkout, dashboard edit, scorecard
edit, or R8 badge was performed in this lane. No live credential was read or printed. The tracked tree
was clean before the gates and remains clean apart from this untracked record.

---

## 7. Remaining findings for fresh T1/T8

1. The six R8 verdicts have **not** been re-read against their source reports in this lane. Fresh T1/T8
   must do that from the tree and cite report and line for each verdict.
2. The dashboard/scorecard conflict is recorded in `artifacts/sprint-phoenix-2/R8-BUILD-MAP.md` §0 and
   must be verified, not silently edited.
3. `R6.6` remains `L1/L2 REPLAY PASS · MUTATION MATRIX OPEN` per the committed execution record.
4. `R7 D1` remains defined but not run; `R7 D3` remains written, inert, and untracked.
5. No T1/T8 verdict and no owner green exist at this time.

---

## 8. Handoff

`SHA: 1d91f73b1c551d1b259c1cf1a44c3e18203b8222 · GATES: GREEN · T1/T8: PENDING · OWNER GREEN: NOT ISSUED · COMMITTED: NONE · STAGED: NONE · PUSHED: NONE · R8: AWAITING T1/T8`

---

## 9. Dated correction — F1 skip breakdown (2026-11-18)

Authority: owner row `R8-W1`, recorded in
`artifacts/sprint-phoenix-2/R8-OWNER-DISPOSITION-UNTRACEABLE-VERDICTS.md`.
Finding corrected: `artifacts/sprint-phoenix-2/T1-T8-REVIEW-RECORD.md:116-120`.

The narrative in §1 saying “Eight are environment-gated … one is the registration-ledger skip …
one is recorded by the conformance suite” is inaccurate. It remains visible above as history and is
not erased.

Correct breakdown of the 10 skips:

- 9 environment-gated skips: 2 R3 real-service controls, 4 `test_rate_limit_redis.py` skips,
  1 `test_shared_inference.py` PostgreSQL skip, and 2 `test_user_quotas.py` PostgreSQL skips.
- 1 registration-ledger skip at `tests/test_r6_registration_digest_conformance.py:570`, which is
  itself the conformance-suite skip.

The aggregate `839 passed, 10 skipped` was and remains correct. Only the breakdown was wrong.

`F1: CORRECTED BY DATED NOTE · ORIGINAL TEXT PRESERVED · NO GATE OUTPUT CHANGED`
