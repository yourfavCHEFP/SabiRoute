# S2 Baseline Addendum — frozen at `4294eb7`

**Purpose:** record the current-HEAD acceptance baseline for Task 1 of the S1–S18 local gap closure plan.
**Evidence labels:** `[VERIFIED BY RUNTIME]` for executed gates, `[VERIFIED BY INSPECTION]` for repository state read from Git, and `[INFERRED]` only where explicitly marked.

## 1. Repository state before the gates

`[VERIFIED BY INSPECTION]` git state observed immediately before the five gate commands:

| Field | Value |
|---|---|
| Branch | `sec/deps-nov` |
| HEAD | `4294eb701d366562feed2a1a15bb1a8b41e0acbe` |
| Worktree root | `/Users/airm2/My ML Hub/SabiRoute` |
| `git status --porcelain` line count | 129 pre-existing untracked paths |
| Tracked changes | 0 |
| Staged changes | 0 |
| `git diff --check` | clean |

`git worktree list` output:

```text
/Users/airm2/My ML Hub/SabiRoute 4294eb7 [sec/deps-nov]
/private/tmp/sabiroute-batch2/wt 0cb053d (detached HEAD) prunable
/private/tmp/sabiroute-p2-f06a/wt f09aaa9 [feat/sabiroute-f06a-p3-liteLLm-pin] prunable
/Users/airm2/My ML Hub/.sabiroute-docs-pub e43150c [docs/community-governance-publication]
/Users/airm2/My ML Hub/.sabiroute-reqflow 59095e0 [docs/publish-request-flow-diagram]
/Users/airm2/My ML Hub/sabiroute-release-20261020 e4ddc8d (detached HEAD)
```

After the gates, `git status --porcelain` still reported 129 lines; tracked changes remained 0 and staged changes remained 0. The five commands did not alter any tracked or staged repository file.

## 2. Gate result summary

All five commands were run in the exact order required by the Task 1 brief, in one shell invocation rooted at `/Users/airm2/My ML Hub/SabiRoute`.

| Order | Exact command | Exit code | Result |
|---:|---|---:|---|
| 1 | `./.venv/bin/python -m pytest -q` | 0 | `844 passed, 10 skipped in 44.29s` |
| 2 | `uv run ruff check src tests scripts config` | 0 | `All checks passed!` |
| 3 | `uv run mypy src` | 0 | `Success: no issues found in 61 source files` |
| 4 | `git diff --check` | 0 | No output; clean |
| 5 | `shasum -c REPORTS-MANIFEST.sha256` | 0 | 13 artifacts each reported `OK` |

`[VERIFIED BY RUNTIME]` the observed values match the approved baseline recorded in `docs/superpowers/specs/2026-11-18-s1-s18-local-gap-closure-design.md:35` and the Task 1 brief: 844 passed / 10 skipped, Ruff clean, mypy clean over 61 files, manifest 13 OK, and diff clean. No numerical reconciliation or baseline override was needed.

## 3. Exact command transcript

```text
=== REPO STATE ===
sec/deps-nov
4294eb701d366562feed2a1a15bb1a8b41e0acbe
/Users/airm2/My ML Hub/SabiRoute
/Users/airm2/My ML Hub/SabiRoute 4294eb7 [sec/deps-nov]
/private/tmp/sabiroute-batch2/wt 0cb053d (detached HEAD) prunable
/private/tmp/sabiroute-p2-f06a/wt f09aaa9 [feat/sabiroute-f06a-p3-liteLLm-pin] prunable
/Users/airm2/My ML Hub/.sabiroute-docs-pub e43150c [docs/community-governance-publication]
/Users/airm2/My ML Hub/.sabiroute-reqflow 59095e0 [docs/publish-request-flow-diagram]
/Users/airm2/My ML Hub/sabiroute-release-20261020 e4ddc8d (detached HEAD)
=== GATE 1: ./.venv/bin/python -m pytest -q ===
........................................................................ [ 8%]
........................................................................ [ 16%]
........................................................................ [ 25%]
........................................................................ [ 33%]
........................................................................ [ 42%]
...........................................................ss........... [ 50%]
........................................................................ [ 59%]
................................s....................................... [ 67%]
........................................................................ [ 75%]
...ssss................................................................. [ 84%]
........................................................................ [ 92%]
.........s..................................................ss [100%]
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
844 passed, 10 skipped in 44.29s
EXIT_CODE=0
=== GATE 2: uv run ruff check src tests scripts config ===
All checks passed!
EXIT_CODE=0
=== GATE 3: uv run mypy src ===
Success: no issues found in 61 source files
EXIT_CODE=0
=== GATE 4: git diff --check ===
EXIT_CODE=0
=== GATE 5: shasum -c REPORTS-MANIFEST.sha256 ===
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
EXIT_CODE=0
=== GATE SUMMARY: 0 0 0 0 0 ===
```

## 4. Exact skip reasons observed

`[VERIFIED BY RUNTIME]` all ten skip reasons are quoted verbatim from the pytest short summary above. Counts by class: five `SABIROUTE_TEST_REDIS_URL` environment gates, four `SABIROUTE_TEST_PG_URL` environment gates, one authorization gate awaiting ledger instantiation.

| Count | Exact reason |
|---:|---|
| 1 | `SABIROUTE_TEST_REDIS_URL is not set; real Redis control skipped` |
| 1 | `SABIROUTE_TEST_PG_URL is not set; real PostgreSQL control skipped` |
| 1 | `awaiting authorised ledger instantiation` |
| 4 | `SABIROUTE_TEST_REDIS_URL is not set; Redis integration tests skipped` |
| 1 | `SABIROUTE_TEST_PG_URL is not set; PostgreSQL integration tests skipped` |
| 2 | `SABIROUTE_TEST_PG_URL is not set; PostgreSQL integration tests skipped` |

The two PostgreSQL quota skips and the shared-inference PostgreSQL skip use the same literal reason as the PostgreSQL integration skip; the table keeps their source counts separate. No skip was a contract failure and no skip was silently reclassified.

## 5. Evidence limits

- `[VERIFIED BY INSPECTION]` the report manifest proves byte consistency of 13 attested artifacts only. Per `REPORTS-PROVENANCE.md:56-74`, it does not prove evidence validity, ownership or approval, or release readiness.
- `[VERIFIED BY INSPECTION]` no live provider call, credential read, spend authorization, managed service, hosted CI run, staging or production action was performed.
- `[INFERRED]` this baseline supports local regression comparison at this exact HEAD only; it does not close any S1–S18 sprint gate by itself.
- `[VERIFIED BY INSPECTION]` the frozen crosswalk is `artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md`; Task 8 consumes it as the Task 1 baseline and must not rewrite it into a completion claim.
