# Mission C Evidence Audit — 2026-10-26

Audit of claims in `reports/mobilization-reconciliation-2026-10-26.md` for the
Mission C working-tree changes. Evidence labels follow the repository's evidence
standard: VERIFIED = direct code/test output; PARTIALLY VERIFIED = some direct
evidence, gaps remain; UNVERIFIED = no direct evidence found; OWNER DECISION
REQUIRED = cannot be resolved by engineering alone.

No application code, tests, configuration, or protected paths were changed by
this audit. Only this report was added.

## 1. BYOK-0 rejection of caller-controlled `api_key`, `api_base`, `authorization`

- Claim assessed: rejected top-level `api_key`/`api_base`/`authorization` (incl.
  camelCase and kebab-case variants) after auth, before request_id/accounting.
- Evidence present: `src/sabiroute/api/completions.py` lines 248-270 show the guard
  placed after identity/store checks and before `request_id = str(uuid4())`.
  Forbidden set includes `api_key`, `apiKey`, `api-key`, `api_base`, `apiBase`,
  `api-base`, `authorization`. Tests `test_byok0_*` (8 tests, all passing in the
  focused run).
- Classification: VERIFIED.
- Discrepancy/missing: none for the in-memory path. No live-provider or
  managed-PostgreSQL evidence, but the guard is pure request parsing and does
  not depend on either.
- Next verification step: none required beyond the existing 8 tests; optional
  property test for arbitrary forbidden aliases (not currently in scope).

## 2. Rejection occurs before accounting writes and provider execution

- Claim assessed: rejected requests leave no usage row, reservation, snapshot,
  rate token, or provider call.
- Evidence present: guard returns before `request_id` creation and before
  `store.create_usage_event`, `quota_reservations`, rate limiter, and the
  LiteLLM client call. Tests assert `stub.calls == []`, `store.usage_events == {}`,
  `store.budget_usage == {}`, `store.quota_reservations == {}` for each variant.
- Classification: VERIFIED for the in-memory store path exercised by tests.
- Discrepancy/missing: no test asserts absence of a Redis rate-limit token
  consumption on rejection (Redis is env-gated and not configured in this run).
  The code path returns before the rate limiter is reached, so this is a
  code-inspection conclusion, not a runtime observation.
- Next verification step: optional Redis-enabled run of `test_byok0_*` to
  confirm no token consumption (env: `SABIROUTE_TEST_REDIS_URL`).

## 3. Read-only schema validation at startup and failure behavior

- Claim assessed: `build_gateway_state` runs `check_schema`,
  `check_shared_inference_schema`, `check_sabichat_schema` on the engines; an
  incompatible schema fails startup; injected state is validated in lifespan.
- Evidence present: `src/sabiroute/gateway.py` lines 195-202 (read-only checks,
  no mutation). `src/sabiroute/main.py` lifespan validates injected state and
  on failure sets `startup_error` and nulls `key_store`/`chat_store`.
  `tests/test_schema_validators.py` (12 tests) + migration-path tests (74 total
  in the focused run) pass.
- Classification: PARTIALLY VERIFIED. Code and unit tests confirm the read-only
  behavior and failure path on SQLite. No managed-PostgreSQL or cross-host
  evidence.
- Discrepancy/missing: the reconciliation report's "74 passed" figure aggregates
  `test_schema_validators.py` + `test_dataset.py` + `test_usage_source.py`;
  re-run this session gave 123 passed across those four files (including
  `test_completions.py`). The subset counts are consistent (12 + 74 = 86 for
  schema/migration files; 123 includes 37 completions tests). No contradiction,
  but the report's grouping should be read carefully.
- Next verification step: disposable PostgreSQL run (`SABIROUTE_TEST_PG_URL`) of
  `test_schema_validators.py` and `test_shared_inference.py`.

## 4. Migration concurrency strategy and unresolved acceptance gate

- Claim assessed: connection-scoped `_acquire_migration_lock` uses a PostgreSQL
  advisory transaction lock (`pg_advisory_xact_lock`); no-op on other dialects.
- Evidence present: `src/sabiroute/security/store.py` lines 261-274 implement the
  lock with `SET LOCAL lock_timeout = '30s'` on PostgreSQL only. `ensure_schema`
  acquires it inside `engine.begin()`. Tests pass on SQLite (no-op path).
- Classification: OWNER DECISION REQUIRED for acceptance. The implementation
  exists and is unit-tested on SQLite; owner acceptance of the concurrency
  strategy is explicitly NOT granted per the mission state and reconciliation
  report.
- Discrepancy/missing: no live cross-process/cross-host contention evidence.
  Phase 3 accounting continuity remains blocked by this gate.
- Next verification step: owner decision; then disposable multi-process PG test
  if accepted.

## 5. Focused and full test results, including environment-gated skips

- Claim assessed: suite 425 passed / 7 skipped; ruff/mypy/diff clean.
- Evidence present: this session re-ran `pytest -q` → 425 passed, 7 skipped in
  16.70s (4 Redis-gated: `SABIROUTE_TEST_REDIS_URL` unset; 3 PG-gated:
  `SABIROUTE_TEST_PG_URL` unset). `ruff check src tests scripts config` → all
  checks passed. `mypy src` → 47 files, no issues. `git diff --check` → clean.
- Classification: VERIFIED.
- Discrepancy/missing: none. Counts match the reconciliation report exactly.

## 6. Previously reported snapshot-filtered test timeout

- Claim assessed: a snapshot-filtered completions test run timed out; cause not
  established.
- Evidence present: this session ran `tests/test_completions.py` in 0.76s with
  all tests passing, including `test_current_attempt_outcome_is_not_in_its_own_feature_snapshot`,
  `test_feature_snapshot_is_durable_before_provider_execution`, and
  `test_snapshot_persistence_failure_prevents_provider_execution`. No hang
  reproduced; no timeout artifact found.
- Classification: UNVERIFIED (the original timeout claim). Current evidence
  shows the tests pass quickly; the root cause of the earlier timeout was never
  established and remains unknown.
- Discrepancy/missing: the reconciliation report states the timeout as a
  historical claim and does not assert a root cause. This audit agrees: do not
  treat the timeout as a current defect.
- Next verification step: if the timeout recurs, capture the exact command,
  environment, and stack trace before drawing conclusions.

## 7. Repository divergence and uncommitted changes

- Claim assessed: local ahead of origin by 2 commits, behind by 3; 10 tracked
  modifications; untracked `tests/test_schema_validators.py` and prior artifacts.
- Evidence present: `git status --short` shows 10 tracked modifications
  (`completions.py`, `health.py`, `chat/store.py`, `gateway.py`, `main.py`,
  `security/store.py`, `conftest.py`, `test_completions.py`, `test_dataset.py`,
  `test_usage_source.py`) plus untracked files including `tests/test_schema_validators.py`.
  HEAD `b360ffc` on `feat/sabiroute-routing-foundation`.
- Classification: PARTIALLY VERIFIED. Working-tree state verified by direct
  inspection this session. The ahead/behind commit counts (2 ahead, 3 behind)
  were reported in the reconciliation report and not re-verified against the
  remote this session (no fetch performed, per the no-push/no-fetch constraint).
- Discrepancy/missing: remote divergence counts rely on the prior report; an
  owner decision on reconciliation is still required.
- Next verification step: owner-authorized `git fetch` (no merge) to confirm
  ahead/behind counts.

## Summary

Mission C's code-level claims (BYOK-0 guard, read-only schema validation, advisory
lock implementation, test counts) are supported by direct code inspection and
passing tests this session. Owner acceptance, live/managed-database evidence, and
the original timeout's root cause remain unresolved. No runtime behavior or
acceptance status was changed by this audit.
