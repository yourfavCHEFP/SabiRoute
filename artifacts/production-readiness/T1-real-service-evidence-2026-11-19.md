# Task 1 — Real-service gates on disposable infrastructure

Date: 2026-11-19
Frozen HEAD (VERIFIED BY RUNTIME): `13d0377927e8be5b088c4e5c5026a6aa2650a1aa`
Branch observed (VERIFIED BY RUNTIME): `sec/deps-nov`
Git actions: none (forbidden). No staging, commit, push, merge, rebase, reset, clean, stash, checkout, or worktree creation.
Endpoint values: withheld. `SABIROUTE_TEST_REDIS_URL` and `SABIROUTE_TEST_PG_URL` were composed only in each command's environment and never written to a file, report, commit, or output. No credentials were used or printed.

Evidence labels used: VERIFIED BY INSPECTION, VERIFIED BY RUNTIME, STATIC-ANALYSIS FINDING, INFERRED, UNVERIFIED.

---

## ACTION COMPLETED

- FILE CREATED (VERIFIED BY RUNTIME): `artifacts/production-readiness/T1-real-service-evidence-2026-11-19.md` (this report). It is the only file created inside the repository.
- FILES MODIFIED / DELETED INSIDE REPOSITORY (VERIFIED BY RUNTIME): none.
- FILES CREATED OUTSIDE REPOSITORY (VERIFIED BY RUNTIME): a fresh `/tmp/sabiroute-t1-20261119.j1IVsr` tree containing only disposable PostgreSQL data/logs and Redis working files/logs; removed after teardown.
- SERVICES STARTED (VERIFIED BY RUNTIME): one fresh PostgreSQL cluster with a fresh `initdb` data directory and a disposable database whose name ends in `_test`; one Redis server with persistence disabled and no AOF. Both were bound to loopback, non-owner ports. Port numbers and database name are withheld here.
- TEST COMMANDS EXECUTED (VERIFIED BY RUNTIME): one diagnostic full-suite attempt, one corrected full-suite run, one explicitly targeted real-service control-suite run, and collection-only counts used for skip accounting.
- RESIDUE ACTIONS (VERIFIED BY RUNTIME): scanned Redis for the test key prefix; counted PostgreSQL test-tagged rows before cleanup; deleted only test-created rows in the disposable database; recounted to zero.
- TEARDOWN (VERIFIED BY RUNTIME): PostgreSQL stopped, Redis shut down without saving, both ports confirmed not listening, both processes confirmed absent, and the temporary directory confirmed absent.
- CONFIGURATION CHANGED (VERIFIED BY RUNTIME): none in the repository. `PGCLIENTENCODING=UTF8` was used in the corrected test command environment only, to avoid a SQL_ASCII client-encoding artifact in the disposable cluster.

Command shapes (values withheld; no endpoint values reproduced):

```sh
# disposable service preparation
mktemp -d /tmp/sabiroute-t1-20261119.XXXXXX
initdb -D <PG_DATA_DIR> --username=postgres --auth-local=trust --auth-host=trust --no-instructions
pg_ctl -D <PG_DATA_DIR> -l <PG_LOG> -o "<loopback bind options>" -w start
createdb <DISPOSABLE_DB_NAME>
redis-server <loopback bind options> --save '' --appendonly no --dir <TMP_DIR> --daemonize yes --pidfile <TMP_DIR>/redis.pid --logfile <TMP_DIR>/redis.log

# diagnostic full-suite attempt (first run; SQL_ASCII client artifact)
env SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q

# authoritative full-suite run (single allowed repeat, with command-environment encoding fix)
env PGCLIENTENCODING=UTF8 SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q -rs

# explicitly targeted real-service control suite
env PGCLIENTENCODING=UTF8 SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q -rs tests/test_r3_real_service_controls.py

# residue checks
redis-cli <loopback options> --scan --pattern 'sabiroute:test*' | wc -l
redis-cli <loopback options> dbsize
psql <disposable database options> -c "select ... from sabichat_quota_windows ..."
psql <disposable database options> -c "delete ... where user_id like 'pgrace-%' or user_id like 'r3ctl%' ..."

# teardown
pg_ctl -D <PG_DATA_DIR> -m fast -w stop
redis-cli <loopback options> shutdown nosave
rm -rf <TMP_DIR>
```

---

## WHY

The repository's default suite skipped nine real-service tests because `SABIROUTE_TEST_REDIS_URL` and `SABIROUTE_TEST_PG_URL` were unset. A green default run therefore proved nothing about the real Redis Lua bucket or the real PostgreSQL quota ledger. This task converts those skips into runtime evidence using infrastructure that is disposable by construction, loopback-only, and fully removable, without touching owner Redis, owner PostgreSQL sockets, owner data directories, credentials, source, tests, configuration, dependencies, or protected paths.

---

## RESULT

### 1. Service identity (VERIFIED BY RUNTIME)

```text
postgres (PostgreSQL) 17.10 (Homebrew)
initdb (PostgreSQL) 17.10 (Homebrew)
psql (PostgreSQL) 17.10 (Homebrew)
Redis server v=8.10.2 sha=00000000:1 malloc=libc bits=64 build=764b3e45065a66fb
```

Port-availability check before startup reported both assigned loopback ports free. Endpoint values and port numbers are withheld.

Initial setup incident (VERIFIED BY RUNTIME, resolved): the inherited `LANG`/`LC_*` environment was invalid; `initdb` first failed with `invalid locale settings`, then the server start failed with `postmaster became multithreaded during startup / Set the LC_ALL environment variable to a valid locale`. Both were resolved by setting `LC_ALL=C LANG=C` in the disposable service-start commands. No repository file was changed.

### 2. Diagnostic full-suite attempt (VERIFIED BY RUNTIME)

The first run used the disposable services but inherited the cluster's SQL_ASCII client encoding. Four PostgreSQL tests failed before reaching their assertions because SQLAlchemy received the server-version string as bytes. Exact final output:

```text
=========================== short test summary info ============================
SKIPPED [1] tests/test_r6_registration_digest_conformance.py:570: awaiting authorised ledger instantiation
FAILED tests/test_r3_real_service_controls.py::test_real_pg_same_request_id_under_two_tenants_is_independent
FAILED tests/test_shared_inference.py::test_pg_policy_round_trip_and_null_fail_closed
FAILED tests/test_user_quotas.py::test_pg_concurrent_last_allowance_single_winner
FAILED tests/test_user_quotas.py::test_pg_migration_records_0004 - TypeError:...
4 failed, 871 passed, 1 skipped in 28.77s
FULL_SUITE_EXIT=1
```

The decisive traceback frame was `TypeError: cannot use a string pattern on a bytes-like object` with `string = b'PostgreSQL 17.10 (Homebrew) ...'`. STATIC-ANALYSIS FINDING: the failure is in disposable-service encoding handling, not in the repository's routing, quota, or rate-limit logic. Safest fix applied: `PGCLIENTENCODING=UTF8` in the command environment only.

### 3. Authoritative full suite (VERIFIED BY RUNTIME)

Command shape: `env PGCLIENTENCODING=UTF8 SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q -rs`

Exact output:

```text
........................................................................ [ 8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 41%]
........................................................................ [ 49%]
........................................................................ [ 57%]
......................................................s................. [ 65%]
........................................................................ [ 73%]
........................................................................ [ 82%]
........................................................................ [ 90%]
........................................................................ [ 98%]
............ [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/test_r6_registration_digest_conformance.py:570: awaiting authorised ledger instantiation
875 passed, 1 skipped in 27.53s
FULL_SUITE_EXIT=0
```

### 4. Real-service control suite (VERIFIED BY RUNTIME)

Command shape: `env PGCLIENTENCODING=UTF8 SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q -rs tests/test_r3_real_service_controls.py`

Exact output:

```text
........................... [100%]
27 passed in 0.51s
CONTROL_SUITE_EXIT=0
```

This proves the control suite ran rather than skipped: all 27 control tests passed, including `test_real_redis_per_key_isolation_matches_fake_redis_model` and `test_real_pg_same_request_id_under_two_tenants_is_independent`, which are the two opt-in real-service controls (VERIFIED BY RUNTIME). No `SKIPPED` line appeared for this file.

### 5. Skip accounting (VERIFIED BY RUNTIME + VERIFIED BY INSPECTION)

Baseline without env vars: `866 passed, 10 skipped` = 876 collected tests. Authoritative run: `875 passed, 1 skipped` = 876 collected tests. The nine converted skips are:

| Category | Count | Tests | Evidence |
|---|---:|---|---|
| Redis integration, shipped suite | 4 | `tests/test_rate_limit_redis.py` (module-level `skipif`) | VERIFIED BY INSPECTION of `tests/test_rate_limit_redis.py:35`; VERIFIED BY RUNTIME via green full suite |
| Redis real-service control | 1 | `tests/test_r3_real_service_controls.py::test_real_redis_per_key_isolation_matches_fake_redis_model` | VERIFIED BY INSPECTION of `tests/test_r3_real_service_controls.py:371`; VERIFIED BY RUNTIME via targeted control suite |
| PostgreSQL integration, shipped suites | 3 | `tests/test_user_quotas.py::test_pg_concurrent_last_allowance_single_winner`; `tests/test_user_quotas.py::test_pg_migration_records_0004`; `tests/test_shared_inference.py::test_pg_policy_round_trip_and_null_fail_closed` | VERIFIED BY INSPECTION of each opt-in guard; VERIFIED BY RUNTIME via green full suite |
| PostgreSQL real-service control | 1 | `tests/test_r3_real_service_controls.py::test_real_pg_same_request_id_under_two_tenants_is_independent` | VERIFIED BY INSPECTION of `tests/test_r3_real_service_controls.py:435`; VERIFIED BY RUNTIME via targeted control suite |
| **Converted total** | **9** | — | VERIFIED BY RUNTIME |

Remaining skip (VERIFIED BY RUNTIME — exact output above): 1 skip, `tests/test_r6_registration_digest_conformance.py:570: awaiting authorised ledger instantiation`. It is unrelated to real services and remains deliberately blocked pending authorised ledger instantiation; no ledger was fabricated and no authorization was assumed.

### 6. Residue verification (VERIFIED BY RUNTIME)

Exact output:

```text
REDIS_TEST_PREFIX_KEY_COUNT=0
REDIS_DBSIZE=0
--- PG_TAGGED_ROWS_BEFORE ---
quota_windows|1
quota_reservations|5
shared_inference_policy|1
--- PG_CLEANUP ---
--- PG_ROWS_AFTER ---
quota_windows|0
quota_reservations|0
shared_inference_policy|0
REDIS_DBSIZE_AFTER=0
```

`PG_CLEANUP` is empty because `psql -q` suppresses command tags; the following count query is the evidence that deletion succeeded. Only test-created rows in the disposable database were deleted. No Redis key with the test prefix existed before cleanup, and Redis held no keys at all.

### 7. Teardown proof (VERIFIED BY RUNTIME)

Exact output:

```text
waiting for server to shut down.... done
server stopped
PG_STOP_EXIT=0
REDIS_SHUTDOWN_EXIT=0
REDIS_PORT_LISTENING=false
POSTGRES_PORT_LISTENING=false
REDIS_PROCESS_PRESENT=false
POSTGRES_PROCESS_PRESENT=false
TEMP_DIR_ABSENT=true
```

Both disposable services are stopped, neither assigned port is listening, neither process is present, and the fresh `/tmp` tree is absent. No owner service, owner socket, owner data directory, or pre-existing untracked path was touched (VERIFIED BY RUNTIME).

---

## ARCHITECTURAL POSITION

No production code was changed. The exercised path is the test harness around `sabiroute.security.rate_limit.RedisTokenBucket` and `sabiroute.security.store.PostgresApiKeyStore` (VERIFIED BY INSPECTION). Pipeline effect:

```text
Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter
       → Routing Engine → Fallback → LiteLLM → Provider → Response
```

- Authentication / policy: no routing or policy behavior changed; evidence only.
- Classification / capability / health / routing / fallback / LiteLLM / provider: untouched; no provider calls were made.
- PostgreSQL: only the disposable `_test` database was created, migrated by the store under test, written to, cleaned, and dropped with the cluster.
- Redis: only the disposable non-persistent instance was used; zero keys remained before teardown.
- Telemetry: no telemetry configuration changed; no routing telemetry was emitted by provider calls.
- Security: real Redis per-key bucket isolation and real PostgreSQL tenant isolation were exercised; no credentials were handled or printed.
- Future intelligence: no training, no dataset creation, no scoring change; Phase 13 gates remain closed.

---

## ROADMAP POSITION

This action advances the production-readiness Task 1 gate, not a Phase 00–20 roadmap status (VERIFIED BY INSPECTION of the task brief). It supplies Phase 19-style CI/CD evidence for existing Phase 17/R3 security controls; it does not mark any phase live-verified or complete. No roadmap number was renumbered and no status was inflated.

---

## DEPENDENCY IMPACT

No code, configuration, `pyproject.toml`, `uv.lock`, or installed-package state was changed (VERIFIED BY RUNTIME). The evidence is reusable by future gate-closure work that needs to cite real Redis/PostgreSQL execution, but it is bound to this disposable run and does not substitute for hosted CI or production verification. The remaining R6 registration-ledger skip continues to depend on separate, explicit authorization for ledger instantiation (VERIFIED BY INSPECTION).

---

## NEXT STEP

Present the exact run evidence to the owner and await the next gate decision. Do not re-run the full suite merely to re-confirm this gate.

---

## DO NOT TOUCH YET

- Owner Redis, owner PostgreSQL sockets/data directories, ports `6379`, `5432`, `5433`, `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, and `reports/provider_verification.json`.
- Source, tests, configuration, the nine zero-byte placeholder files, `security/`, `intelligence/`, and `routing/` implementations.
- ML routing, reinforcement learning, dashboards, Go rewrite, enterprise control plane, cloud deployment, native IDE extensions, autonomous agents, training, hosted CI, and provider calls with live credentials.
- R6 registration-ledger instantiation without explicit authorization.

---

## CURRENT PROJECT STATUS

```text
CURRENT GATE: Task 1 real-service gates on disposable infrastructure passed with endpoint values withheld; broader production-readiness closure remains open.
CURRENT PHASE: Roadmap phase statuses unchanged from frozen HEAD; this is Phase 19-style evidence for existing R3/Phase 17 controls.
PROVEN: 875 passed, 1 skipped, exit 0; targeted controls 27 passed, exit 0; zero Redis keys; zero PostgreSQL test rows; services stopped and temp directory absent.
UNPROVEN: production/live request paths, hosted CI, owner infrastructure, live provider execution, and authorised R6 ledger instantiation.
BLOCKED BY: one registration-ledger authorization skip and owner decision on the next tranche; no infrastructure blocker remains for Task 1.
NEXT: owner review of this evidence and decision on the next gate; no code change.
```
