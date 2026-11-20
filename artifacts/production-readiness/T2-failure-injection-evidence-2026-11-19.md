# T2 — Local failure injection and fallback evidence — 2026-11-19

Task brief: `.superpowers/sdd/sabiroute-production-readiness-mobilization-prompt-2026-11-19/task-2-brief.md` (read — VERIFIED BY INSPECTION).
All commands ran from `/Users/airm2/My ML Hub/SabiRoute` with the project interpreter `./.venv/bin/python` or `uv`. No live provider, credential, training, hosted CI, deployment, publication, or architecture change was used.
Evidence labels are used literally: VERIFIED BY INSPECTION, VERIFIED BY RUNTIME, STATIC-ANALYSIS FINDING, INFERRED, UNVERIFIED.

## ACTION COMPLETED

**Files created (1):** this report, `artifacts/production-readiness/T2-failure-injection-evidence-2026-11-19.md`.
**Files modified:** none. **Files deleted:** none. **Configuration changed:** none. **Dependencies changed:** none. **Production code changed:** none. **Tests added or weakened:** none.
**Git state changes:** none (forbidden). Commits: **none (forbidden)**. No commit, stage, push, PR, merge, rebase, reset, clean, stash, checkout, worktree, or history rewrite.
**Protected paths:** no protected path, `.env`, secret value, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, or `reports/provider_verification.json` was inspected for values or changed. No pre-existing untracked path was altered.
**Frozen state — VERIFIED BY RUNTIME:**

```
$ git rev-parse HEAD
13d0377927e8be5b088c4e5c5026a6aa2650a1aa
$ git rev-parse --abbrev-ref HEAD
sec/deps-nov
$ git status --short --untracked-files=no | wc -l
 0
$ git status --short | wc -l
 131
```

The 131 untracked paths pre-existed this report; the report adds one new untracked path.

**Commands executed:** read-only inspection (`git rev-parse`, `git status`, `rg`, `find`, file reads), the focused pytest command below, the five full gates below, and the post-write state check near the end of this report.

## WHY

The brief asks to close the Phase 05 limitation "no live failure-injection evidence" using a local stub. Controller scope limits edits to `tests/test_completions.py` and `tests/test_health.py`, plus `src/sabiroute/api/completions.py` only if a newly written RED test proves a production defect. The prior 8-task tranche already documented and tested all four required properties; duplicating those tests or editing production code would add noise without evidence. Live-provider failure injection remains outside authorization, so this task provides **local stub-driven** evidence only and does not claim live-provider closure.

## RESULT

### RED/GREEN verdict

**No RED needed — prior coverage exact.** No new test was written because each required property already has an exact passing test and an exact file:line citation (matrix below). No production defect was observed; therefore no production fix, GREEN transition, or source edit was made. This is a coverage-ruled outcome, not a skipped verification: all cited tests were executed in the focused run.

### Coverage matrix — VERIFIED BY INSPECTION + VERIFIED BY RUNTIME

| # | Required property | Exact existing evidence | Focused run | Verdict |
|---|---|---|---|---|
| 1 | Retryable failure: attempt count, deterministic fallback, explainable decision | `tests/test_completions.py:92` `test_policy_request_falls_back_to_next_deployment` asserts 200 from `secondary`, `X-SabiRoute-Attempt == "2"`, `stub.calls == ["primary", "secondary"]`, and recorded health state; `tests/test_completions.py:111` `test_measured_policy_scores_and_persists_each_fallback_decision` asserts `fallback_attempt` 1/2, `scoring_policy_version == "deterministic-v1"`, eligible deployments, candidate scores, attempt outcomes, and ordered attempt timestamps; `tests/test_completions.py:1041` `test_request_lifecycle_reconstructable_from_persisted_telemetry` reconstructs the entire decision from persisted telemetry. | 60 passed | Covered; no new test |
| 2 | Cooldown entry and recovery | `tests/test_completions.py:1005` `test_sustained_failure_cools_down_and_recovers` asserts three primary calls then cooldown skipping, unhealthy state at `tests/test_completions.py:1024`, and explicit cooldown-expiry retry at `tests/test_completions.py:1026-1038`; `tests/test_health.py:12` `test_failures_trip_cooldown` and `tests/test_health.py:23` `test_half_open_reset_after_cooldown_expiry` cover registry entry/half-open reset; `tests/test_health.py:99` `test_cooldown_starts_at_failure_time_and_ends_at_boundary` covers exact timing. | 60 passed | Covered; no new test |
| 3 | Non-retryable failure must not be retried | `tests/test_completions.py:294` `test_non_retryable_client_error_stops_retrying` injects a 400 with three remaining failures and asserts `stub.calls == ["primary"]`; `tests/test_completions.py:617` `test_exhausted_attempts_omit_upstream_error_detail` and `tests/test_completions.py:851` / `tests/test_completions.py:893` assert no retry for malformed upstream bodies. | 60 passed | Covered; no new test |
| 4 | Transient health/readiness failure recovers without sticky startup error | `tests/test_admin.py:97` `test_readiness_recovers_after_transient_schema_check_failure` injects one `check_schema` failure, asserts first `GET /health/ready` is 503 and second is 200 with `key_store == "ok"`. A successful second probe also implies no sticky `startup_error`: `src/sabiroute/api/health.py:41` skips checks only when `startup_error` is set and `src/sabiroute/api/health.py:56-58` marks readiness failed when it is set. `src/sabiroute/api/health.py:43-44` explicitly documents the response-local contract. | 60 passed (explicit selector) | Covered; no new test |

**Controller-note discrepancy — VERIFIED BY INSPECTION:** the controller message stated the transient readiness recovery test was in `tests/test_health.py`. It is actually `tests/test_admin.py:97`, matching the prior-tranche plan `docs/superpowers/plans/2026-11-18-s1-s18-local-gap-closure.md:165-193`. It was run by exact selector; no out-of-scope file was edited.

**Prior-tranche ledger — VERIFIED BY INSPECTION:** `docs/controlled-failure-injection.md:28-30` gives the local reproduction scope and commands; its scenario matrix cites `test_policy_request_falls_back_to_next_deployment`, `test_measured_policy_scores_and_persists_each_fallback_decision` (line 36), `test_non_retryable_client_error_stops_retrying` (line 41), `test_sustained_failure_cools_down_and_recovers`, and `test_request_lifecycle_reconstructable_from_persisted_telemetry` (lines 53-54). The current SDD ledger at `.superpowers/sdd/sabiroute-production-readiness-mobilization-prompt-2026-11-19/progress.md:44` ruled that prior coverage is cited rather than duplicated, and its line 76 fixed this task's edit scope.

**Execution boundary — STATIC-ANALYSIS FINDING:** `src/sabiroute/api/completions.py:1643-1646` retries only when status is `None`, `>= 500`, or in `RETRYABLE_STATUS_CODES`; a non-retryable 400 breaks the loop. The fallback loop and explainable attempt telemetry are already implemented; no production change was needed. `docs/controlled-failure-injection.md:19-26` states the important limit: one SabiRoute attempt equals one SabiRoute-to-proxy request, **not** one provider attempt; downstream proxy retries remain UNVERIFIED.

### Focused test — VERIFIED BY RUNTIME

```
$ ./.venv/bin/python -m pytest tests/test_completions.py tests/test_health.py tests/test_admin.py::test_readiness_recovers_after_transient_schema_check_failure -q
............................................................ [100%]
60 passed in 0.84s
EXIT_CODE=0
```

### Full gates (each run once) — VERIFIED BY RUNTIME

**Gate 1 — `./.venv/bin/python -m pytest -q`, exit code 0.** Exact output:

```
........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 41%]
........................................................................ [ 49%]
..ss.................................................................... [ 57%]
......................................................s................. [ 65%]
........................................................................ [ 73%]
.........................ssss........................................... [ 82%]
........................................................................ [ 90%]
...............................s........................................ [ 98%]
..........ss [100%]
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
866 passed, 10 skipped in 22.59s
GATE1_EXIT=0
```

This run had no Redis/PostgreSQL test URLs set in this task's shell; all ten skips are environment/authorization gates. Task 1's separate 875 passed / 1 skipped run is documented in `artifacts/production-readiness/T1-real-service-evidence-2026-11-19.md` using disposable services and is not reproduced here. The different counts are an environment difference, not a regression claim; no phase or gate status is upgraded from either count.

**Gate 2 — `uv run ruff check src tests scripts config`, exit code 0.** Exact output:

```
All checks passed!
GATE2_EXIT=0
```

**Gate 3 — `uv run mypy src`, exit code 0.** Exact output:

```
Success: no issues found in 61 source files
GATE3_EXIT=0
```

**Gate 4 — `shasum -c REPORTS-MANIFEST.sha256`, exit code 0.** Exact output:

```
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
GATE4_EXIT=0
```

**Gate 5 — `git diff --check`, exit code 0.** Exact output: no stdout or stderr; `GATE5_EXIT=0`.

### Limits and self-review — VERIFIED BY INSPECTION

- No live provider call, credential value, or secret was used or printed; all injected failures use `StubLiteLLMClient` and local test doubles.
- No test was weakened, deleted, skipped by this task, or added redundantly; no production file was modified.
- No git state change; HEAD remains frozen at `13d0377`.
- No phase status changed. Local stub evidence does **not** equal live failure-injection evidence; real-provider failure drills remain blocked pending owner authorization.
- Proxy-side retry behavior and provider-level failure semantics remain UNVERIFIED.

## ARCHITECTURAL POSITION

Pipeline position: `Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter → Routing Engine → Fallback → LiteLLM → Provider → Response`. This task only verifies the Health Filter / Routing Engine / Fallback / LiteLLM boundary with local doubles. SabiRoute continues to decide; LiteLLM continues to execute. No behavioral change was made to PostgreSQL, Redis, Telemetry, or Security. Telemetry explainability was inspected and exercised through persisted routing-decision attempts, not modified.

## ROADMAP POSITION

Phase 05 (Fallback Engine), currently `Implemented`. This task advances local **evidence** for the documented limitation and prepares a future owner-authorized live failure drill; it does not complete Phase 05, upgrade `Live-verified`/`Complete`, or change any Phase 00–20 status. Phase 13 remains gated; nothing here touches training or dataset integrity.

## DEPENDENCY IMPACT

No dependency added, removed, or changed; `uv.lock` untouched. Task 3 may cite the exact tests and report above as existing local evidence rather than rebuilding a harness. No production component depends on this report; it is evidence only.

## NEXT STEP

Owner decision on an authorized live-provider failure-injection drill; until then, keep Phase 05 at `Implemented` and preserve the local stub evidence chain.

## DO NOT TOUCH YET

Live provider accounts/credentials, training and Phase 13 gates, hosted CI, deployment, publication, architecture, README phase table, `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`, and all pre-existing untracked paths. Do not rewire health checking, fallback, or retry logic without a new RED test and owner authorization.

## CURRENT PROJECT STATUS

```
CURRENT GATE: Local five-gate baseline green at frozen HEAD 13d0377 under this task's shell (pytest 866 passed / 10 skipped exit 0; Ruff exit 0; mypy 61 files exit 0; manifest 13 OK exit 0; git diff --check exit 0). Local stub failure-injection coverage is documented; live-provider failure injection, hosted CI, and owner release gates remain open.
CURRENT PHASE: Phase 02 Provider Expansion and Phase 13 ML Router In progress; Phase 05 Fallback Engine Implemented; no status upgraded by this task.
PROVEN: VERIFIED BY INSPECTION — four required properties already covered at exact test file:line citations; no production defect found. VERIFIED BY RUNTIME — focused 60 passed exit 0; five full gates green as recorded above; HEAD unchanged; tracked diff clean.
UNPROVEN: Live-provider failure injection; live fallback on real provider errors; downstream LiteLLM proxy retry behavior; real-service Redis/PG paths in this shell; production-readiness owner acceptance.
BLOCKED BY: Fresh owner authorization for live-provider drills, hosted CI, deployment, publication, and any phase-status upgrade; no technical blocker to local evidence work.
NEXT: Preserve this evidence and wait for the owner decision on an authorized live failure drill; Task 3 may cite the exact local tests above.
```

---

**Post-write self-check — VERIFIED BY RUNTIME:** after this report was created, `git rev-parse HEAD` → `13d0377927e8be5b088c4e5c5026a6aa2650a1aa`; `git status --short --untracked-files=no | wc -l` → ` 0`; `git status --short | wc -l` → ` 131`. The count is unchanged because Git collapses the already-untracked `artifacts/production-readiness/` directory into one status line; this report is the single new file inside that directory. No tracked file was modified.
