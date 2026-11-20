# T3 — Telemetry evidence for failure and success paths — 2026-11-19

Task brief: `.superpowers/sdd/sabiroute-production-readiness-mobilization-prompt-2026-11-19/task-3-brief.md` (read — VERIFIED BY INSPECTION).
All commands ran from `/Users/airm2/My ML Hub/SabiRoute` with the project interpreter `./.venv/bin/python`. No live provider call, credential value, secret inspection, training, hosted CI, deployment, publication, or architecture change was used. Evidence labels are used literally: VERIFIED BY INSPECTION, VERIFIED BY RUNTIME, STATIC-ANALYSIS FINDING, INFERRED, UNVERIFIED.

## ACTION COMPLETED

**Files created (1):** this report, `artifacts/production-readiness/T3-telemetry-evidence-2026-11-19.md`.
**Files modified:** none. **Files deleted:** none. **Configuration changed:** none. **Dependencies changed:** none. **Production code changed:** none. **Tests added, edited, skipped, or weakened:** none.

**Git state changes:** none (forbidden). Commits: **none (forbidden)**. No commit, stage, push, PR, merge, rebase, reset, clean, stash, checkout, worktree, or history rewrite.

**Protected paths:** no protected path, `.env`, secret value, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, or `reports/provider_verification.json` was inspected for values or changed. No pre-existing untracked path was altered.

**Frozen state — VERIFIED BY RUNTIME (before write):**

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

The 131 untracked paths pre-existed this report; this report adds one new untracked file inside an already-untracked directory.

**Commands executed:** read-only inspection (`git rev-parse`, `git status`, `rg`, file reads), `pytest --collect-only` (one call), the single focused pytest run below, and a final post-write Git status check. No full suite rerun was needed; Task 2's separate full-gate evidence is not reproduced or upgraded here.

## WHY

The brief asks to close the Phase 07 Implemented limitation "no stored failure-metric evidence" by reusing Task 2's local stub failure-injection harness and proving that success and failure attempts produce telemetry records with decision-time linkage, and that an unlinked outcome is not silently accepted. The relevant tests and finalization gates already exist at exact locations; rewriting them would add noise without new evidence. This task therefore supplies an inspected and executed evidence chain only. Live-provider telemetry and live failure drills remain outside authorization, so no live-verified claim is made.

## RESULT

### Linkage verdict — VERIFIED BY INSPECTION + VERIFIED BY RUNTIME

**Proved for the persisted finalization gate and the read-only diagnostic export path.** This is not a claim that arbitrary callers bypassing those gates are covered.

1. **Persistence rejection of unlinked/mismatched outcomes.**
   - `src/sabiroute/security/keys.py:195-201`: every finalized outcome must carry at least one of `request_id` / `logical_request_id`, and every present identifier must equal `event.request_id`; otherwise `UsageEventValidationError("outcome logical request identifier differs")` is raised. `src/sabiroute/security/keys.py:202-210` also enforces sequential `fallback_attempt` and a non-null `success`/`failure` label.
   - `src/sabiroute/security/store.py:1503-1504` calls `validate_usage_event_finalization(event)` before SQL persistence; the in-memory double does the same at `tests/conftest.py:283-292`.
   - `tests/test_phase10.py:362-409` constructs four malformed variants, including `outcome | {"logical_request_id": "other"}` at line 401, and asserts `pytest.raises(UsageEventValidationError)` at lines 407-409. Lines 411-412 then query `store.list_usage_events(record.key_id, limit=10, offset=0)` and assert the row remains unfinalized (`final_status is None`). This test PASSED in the focused run.
   - `tests/test_phase10.py:322-359` rejects unpaired feature/outcome attempt counts and verifies no partial record is persisted; PASSED in the focused run.

2. **Read-only export quarantines unlinked outcomes instead of accepting them.**
   - `src/sabiroute/intelligence/dataset.py:524-535` checks linkage against the source outcome *before* `_safe_outcome` projects identifiers away: missing identifiers produce `outcome_request_id_unavailable`, mismatches produce `outcome_request_id_mismatch`. Lines 537-545 check `fallback_attempt`; lines 562-580 map those reasons to `request_attempt_linkage_status` of `mismatch` or `unverified`.
   - `tests/test_dataset.py:411-447` parametrizes four mutations (`mismatched_request_id`, `missing_request_ids`, `mismatched_attempt`, `missing_attempt`), asserts the exact exclusion reason and linkage status (lines 440-441), verifies identifiers are absent from the projected `post_execution_outcome` (lines 443-445), and asserts `DatasetExportBlocked` from `training_candidate_export` (lines 446-447). All four parameter cases PASSED in the focused run.

3. **Decision-time linkage fields observed on real gateway records.**
   - Success/failure attempts carry `logical_request_id`, `fallback_attempt`, `selected_deployment`, `decision_timestamp`, `attempt_started_at`, `attempt_completed_at`, `outcome_recorded_at`, `outcome`, `failure_category`, and `attempt_schema_version`: produced by `src/sabiroute/api/completions.py:2067-2154` and validated by `src/sabiroute/security/keys.py:175-263`.
   - Pre-routing snapshots are appended before provider execution (`src/sabiroute/api/completions.py:1544`, `tests/test_completions.py:206-229`) and are schema-validated by `src/sabiroute/intelligence/dataset.py:127-246`.

### Stored-record query evidence — VERIFIED BY INSPECTION + VERIFIED BY RUNTIME

No record was fabricated, re-typed, or replayed for this report. The queries below are the exact read-only assertions executed by the passing tests:

| Path | Exact query/assertion in test | Observed properties |
|---|---|---|
| Measured-policy failure then success | `tests/test_completions.py:138-177` — `usage_event = next(iter(store.usage_events.values()))`; `attempts = usage_event.routing_decisions`; `features = usage_event.pre_routing_features` | `[1, 2]` snapshot `attempt_number`s; schema `1.1`; `historical_summary_as_of == decision_timestamp`; no `content`/`outcome` keys in features; attempt outcomes `failure`, `success`; `fallback_attempt` 1 then 2; `started <= completed <= recorded`. |
| Provider exception (failure path) | `tests/test_completions.py:273-279` — `event = next(iter(store.usage_events.values()))`; `attempt = event.routing_decisions[0]` | HTTP 500; `final_status == 500`; `outcome == "failure"`; `failure_category == "provider_exception"`; ordered attempt/outcome timestamps. |
| Streaming success path | `tests/test_completions.py:339-345` — `event = next(iter(store.usage_events.values()))` | HTTP 200; `final_status == 200`; `outcome == "success"`; `pre_routing_features[0]["streaming"] is True`; ordered attempt/outcome timestamps. |
| Reconstructable mixed outcome | `tests/test_completions.py:1046-1066` — `(event,) = store.usage_events.values()` | `final_status == 200`; attempts sorted by `fallback_attempt` are `[1, 2]`; selected deployments `primary`, `secondary`; outcomes `failure`, `success`; first has non-null `failure_category`; all `logical_request_id == event.request_id`; all `attempt_schema_version == "1.1"`. |
| SQL store rejection | `tests/test_phase10.py:411-412` — `store.list_usage_events(record.key_id, limit=10, offset=0)` | After each rejected malformed finalization, `total == 1`, `final_status is None`, `pre_routing_features == ()`, `routing_decisions == ()`. |

### Focused test run — VERIFIED BY RUNTIME

Single focused run (collected 11 items; no full-suite rerun):

```
$ ./.venv/bin/python -m pytest -v tests/test_completions.py::test_measured_policy_scores_and_persists_each_fallback_decision tests/test_completions.py::test_unexpected_provider_exception_persists_attempt_timestamps_without_fallback tests/test_completions.py::test_streaming_returns_incremental_sse_and_records_telemetry tests/test_completions.py::test_request_lifecycle_reconstructable_from_persisted_telemetry tests/test_phase10.py::test_sql_finalization_rejects_mismatched_attempt_metadata tests/test_phase10.py::test_sql_finalization_rejects_unpaired_attempt_telemetry tests/test_phase10.py::test_sql_finalization_requires_complete_schema_1_1_timestamps tests/test_dataset.py::test_diagnostic_linkage_is_checked_before_safe_outcome_projection
============================= test session starts ==============================
platform darwin -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /Users/airm2/My ML Hub/SabiRoute/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/airm2/My ML Hub/SabiRoute
configfile: pyproject.toml
plugins: cov-7.1.0, asyncio-1.4.0, platformdirs-4.12.1, anyio-4.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 11 items

tests/test_completions.py::test_measured_policy_scores_and_persists_each_fallback_decision PASSED [ 9%]
tests/test_completions.py::test_unexpected_provider_exception_persists_attempt_timestamps_without_fallback PASSED [ 18%]
tests/test_completions.py::test_streaming_returns_incremental_sse_and_records_telemetry PASSED [ 27%]
tests/test_completions.py::test_request_lifecycle_reconstructable_from_persisted_telemetry PASSED [ 36%]
tests/test_phase10.py::test_sql_finalization_rejects_mismatched_attempt_metadata PASSED [ 45%]
tests/test_phase10.py::test_sql_finalization_rejects_unpaired_attempt_telemetry PASSED [ 54%]
tests/test_phase10.py::test_sql_finalization_requires_complete_schema_1_1_timestamps PASSED [ 63%]
tests/test_dataset.py::test_diagnostic_linkage_is_checked_before_safe_outcome_projection[mismatched_request_id-outcome_request_id_mismatch-mismatch] PASSED [ 72%]
tests/test_dataset.py::test_diagnostic_linkage_is_checked_before_safe_outcome_projection[missing_request_ids-outcome_request_id_unavailable-unverified] PASSED [ 81%]
tests/test_dataset.py::test_diagnostic_linkage_is_checked_before_safe_outcome_projection[mismatched_attempt-fallback_attempt_number_mismatch-mismatch] PASSED [ 90%]
tests/test_dataset.py::test_diagnostic_linkage_is_checked_before_safe_outcome_projection[missing_attempt-outcome_attempt_number_unavailable-unverified] PASSED [100%]

============================== 11 passed in 0.56s ==============================
EXIT_CODE=0
```

### Limits and self-review — VERIFIED BY INSPECTION

- No concrete production defect was found; per the evidence-only constraint, no source/test/config edit was made and no STOP condition was triggered.
- No new timestamp, label, outcome, cost, or selection propensity was invented. All field values cited above came from inspected code or passing test assertions; fixed timestamps in dataset tests are pre-existing repository fixtures.
- No training, ML selector integration, phase-status change, live provider call, hosted CI, deployment, or publication.
- This is local stub/test-double evidence only. It does not upgrade Phase 07 to Live-verified/Complete, and it does not prove real-provider telemetry behavior.
- Live provider metrics, real-service PG/Redis telemetry queries in this shell, and owner acceptance remain UNVERIFIED.

## ARCHITECTURAL POSITION

Pipeline position: `Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter → Routing Engine → Fallback → LiteLLM → Provider → Response`. This task inspects telemetry at the Routing Engine / Fallback / LiteLLM boundary and the storage/export boundary. SabiRoute continues to decide and record explainable attempts; LiteLLM is represented only by `StubLiteLLMClient`. No behavior changed in PostgreSQL, Redis, Telemetry, or Security. Phase 13 dataset rules remain untouched: `selection_propensity` is `None` in generated snapshots (`src/sabiroute/intelligence/dataset.py:243`), and exports remain diagnostic-only with `training_authorized: False` (`src/sabiroute/intelligence/dataset.py:650-663`).

## ROADMAP POSITION

Phase 07 Observability, currently `Implemented`. This task advances **local evidence** for the stored failure-metric limitation and prepares a future owner-authorized live drill; it does not complete Phase 07, upgrade Live-verified/Complete, or change any Phase 00–20 status. Phase 13 remains gated; no training or dataset-integrity gate was exercised beyond read-only export tests.

## DEPENDENCY IMPACT

No dependency added, removed, or changed; `uv.lock` untouched. No production component depends on this report. Task 4 and later evidence tasks may cite the exact test anchors and focused run above rather than rebuilding telemetry or linkage coverage.

## NEXT STEP

Owner decision on an authorized live-request telemetry drill; until then, keep Phase 07 at `Implemented` and preserve this local evidence chain.

## DO NOT TOUCH YET

Live provider accounts/credentials, training and all Phase 13 gates, hosted CI, deployment, publication, architecture, README phase table, source, config, tests, `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`, and all pre-existing untracked paths.

## CURRENT PROJECT STATUS

```
CURRENT GATE: Local evidence chain green at frozen HEAD 13d0377: focused telemetry/linkage run 11 passed, exit 0; tracked tree clean. Full five-gate results belong to Task 1/Task 2 reports and were not rerun here. Live-request telemetry, hosted CI, and owner release gates remain open.
CURRENT PHASE: Phase 07 Observability Implemented; Phase 02 Provider Expansion and Phase 13 ML Router In progress; no status upgraded by this task.
PROVEN: VERIFIED BY INSPECTION — finalization and diagnostic-export linkage checks at the cited file:line locations; stored-record queries in passing tests. VERIFIED BY RUNTIME — 11 focused tests passed with exit code 0; HEAD unchanged; tracked diff clean.
UNPROVEN: Live-provider success/failure telemetry; live stored failure metrics; real-service PG/Redis telemetry in this shell; production-readiness owner acceptance.
BLOCKED BY: Fresh owner authorization for live-request evidence, hosted CI, deployment, publication, and any phase-status upgrade; no technical blocker to local evidence work.
NEXT: Preserve this evidence and wait for the owner decision on an authorized live telemetry drill.
```

---

**Post-write self-check.** After this report was created, the executing agent rechecked `git rev-parse HEAD` → `13d0377927e8be5b088c4e5c5026a6aa2650a1aa`; `git status --short --untracked-files=no | wc -l` → `0`; no tracked file was modified. This report is the only file created by Task 3.
