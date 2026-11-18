# R7 D1/D2 CONTROLLED-REPLAY RECORD — 2026-11-18

**Authority:** Row D, Tranches D1 and D2. **Status:** D1 LOCAL REPLAY EVIDENCED · D2 FRESH LOCAL CHECK PASS · D3 OUT OF SCOPE.

**Repository state:** branch `sec/deps-nov`, HEAD `fb7583b75b868c55da254c154eacde2e144c012e`.
**Interpreter:** `/Users/airm2/My ML Hub/SabiRoute/.venv/bin/python` (Python 3.11.15, pytest 9.1.1).
**Boundaries:** no live provider, managed service, GitHub workflow run, deploy, flag change, ledger change, push, stage, or commit. No file other than this record was created or edited.

---

## 1. D1 E1–E8 evidence table

Evidence labels follow `CLAUDE.md`. "PASS" below means the named local test or runtime command passed; it does not mean a full D1 E2E harness now exists.

| ID | Status | Coverage class | Exact test / runtime evidence | Command output summary | Remaining gap |
|---|---|---|---|---|---|
| E1 | PASS | Stub-provider call-site replay | `tests/test_r6_request_transform.py::test_call_site_is_reached_and_disabled_default_sends_identical_bytes` | `200`; `len(stub.sent) == 1`; `stub.sent[0] == messages`; canonical bytes identical | None at local scope |
| E2 | PASS | Stub-provider call-site replay | `tests/test_r6_request_transform.py::test_call_site_honours_an_enabled_policy_from_config` | `200`; `len(stub.sent[0]) < len(messages)`; canonical bytes of sent messages `<=` original | None at local scope |
| E3 | PASS | Local transform-level replay, not stub-provider E2E | `tests/test_r6_request_transform.py::test_r64_tool_span_is_contiguous_and_atomic`; `tests/test_r6_request_transform.py::test_r64_never_splits_a_tool_exchange` | `tool_spans(...) == [(0, 1)]`; assistant/tool call IDs retained together | No stub-provider byte capture for a tool-exchange request |
| E4 | PASS | Local transform-level replay, not stub-provider E2E | `tests/test_r6_request_transform.py::test_r64_protects_everything_up_to_the_last_cache_breakpoint`; `tests/test_r6_request_transform.py::test_r64_never_rewrites_a_cached_prefix` | Protected indices include the cache breakpoint; original first/breakpoint message objects survive compression | No stub-provider byte capture for a cached-prefix request |
| E5 | PASS | Pipeline-level replay, not stub-provider E2E | `tests/test_r6_request_transform.py::test_b5_capability_loss_degrades_to_the_original` | Canonical bytes unchanged; `BypassReason.CAPABILITY_LOSS`, whose literal value is `capability_loss` | No stub-provider byte capture; capability-loss reason is asserted as enum, not from a provider response |
| E6 | PASS | Pipeline-level replay, not stub-provider E2E | `tests/test_r6_request_transform.py::test_b5_an_exception_inside_the_transform_leaves_the_original_intact` | Canonical bytes unchanged; `bypass.reason is BypassReason.TRANSFORM_ERROR`; `record.fallback_reason == "transform_error"` | No stub-provider byte capture |
| E7 | NOT RUN | Partial helper test only | `tests/test_r6_request_transform.py::test_i9_does_not_swallow_cancelled_error` passed, but no scenario-level test exists | `CancelledError` propagates from `fail_to_original` | No test injects `CancelledError` into `sabiroute.request_transform.run` or the call site, and no test asserts that no original fallback reaches the provider. D1 cancellation scenario is therefore NOT RUN, not PASS. |
| E8 | PASS | Fresh process-startup runtime evidence | `tests/test_r6_request_transform.py::test_invalid_optimization_config_fails_startup` plus the fresh subprocess command in §3 | Invalid `policy.max_ratio=4.0` makes the process exit `1` with `ConfigValidationError` during startup, before any request | The committed test constructs gateway state in-process; only the ad-hoc command below exercises a real process exit |

**E1–E8 verdict:** six scenarios PASS at local replay scope (E1/E2 full stub-provider; E3–E6 transform/pipeline-level; E8 process startup), one scenario NOT RUN at scenario level (E7). The D1 exit gate "E1–E8 pass under controlled replay with exact captured bytes" is **not** fully met: E3–E6 lack stub-provider byte capture and E7 has no scenario-level test.

---

## 2. Focused test commands and outputs

### 2.1 Whole R6 request-transform module

Command:

```bash
cd "/Users/airm2/My ML Hub/SabiRoute" && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_r6_request_transform.py
```

Output:

```text
................................................................. [100%]
65 passed in 0.45s
```

### 2.2 E1–E8 mapped tests, explicit node IDs

Command:

```bash
cd "/Users/airm2/My ML Hub/SabiRoute" && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider -vv tests/test_r6_request_transform.py::test_call_site_is_reached_and_disabled_default_sends_identical_bytes tests/test_r6_request_transform.py::test_call_site_honours_an_enabled_policy_from_config tests/test_r6_request_transform.py::test_r64_tool_span_is_contiguous_and_atomic tests/test_r6_request_transform.py::test_r64_never_splits_a_tool_exchange tests/test_r6_request_transform.py::test_r64_protects_everything_up_to_the_last_cache_breakpoint tests/test_r6_request_transform.py::test_r64_never_rewrites_a_cached_prefix tests/test_r6_request_transform.py::test_b5_capability_loss_degrades_to_the_original tests/test_r6_request_transform.py::test_b5_an_exception_inside_the_transform_leaves_the_original_intact tests/test_r6_request_transform.py::test_i9_does_not_swallow_cancelled_error tests/test_r6_request_transform.py::test_invalid_optimization_config_fails_startup
```

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /Users/airm2/My ML Hub/SabiRoute/.venv/bin/python
rootdir: /Users/airm2/My ML Hub/SabiRoute
configfile: pyproject.toml
plugins: cov-7.1.0, asyncio-1.4.0, platformdirs-4.12.1, anyio-4.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 10 items

tests/test_r6_request_transform.py::test_call_site_is_reached_and_disabled_default_sends_identical_bytes PASSED [ 10%]
tests/test_r6_request_transform.py::test_call_site_honours_an_enabled_policy_from_config PASSED [ 20%]
tests/test_r6_request_transform.py::test_r64_tool_span_is_contiguous_and_atomic PASSED [ 30%]
tests/test_r6_request_transform.py::test_r64_never_splits_a_tool_exchange PASSED [ 40%]
tests/test_r6_request_transform.py::test_r64_protects_everything_up_to_the_last_cache_breakpoint PASSED [ 50%]
tests/test_r6_request_transform.py::test_r64_never_rewrites_a_cached_prefix PASSED [ 60%]
tests/test_r6_request_transform.py::test_b5_capability_loss_degrades_to_the_original PASSED [ 70%]
tests/test_r6_request_transform.py::test_b5_an_exception_inside_the_transform_leaves_the_original_intact PASSED [ 80%]
tests/test_r6_request_transform.py::test_i9_does_not_swallow_cancelled_error PASSED [ 90%]
tests/test_r6_request_transform.py::test_invalid_optimization_config_fails_startup PASSED [100%]

============================== 10 passed in 0.34s ==============================
```

**STATIC-ANALYSIS FINDING:** the only stub-provider capture class in this module is `_CapturingClient` at `tests/test_r6_request_transform.py:746-757`; it is used by the E1 and E2 call-site tests. The E3–E6 tests exercise transform or pipeline functions directly. This is why E3–E6 are marked local replay rather than stub-provider E2E.

---

## 3. E8 fresh process-startup evidence

The committed test `test_invalid_optimization_config_fails_startup` passes, but it calls `build_gateway_state` in-process. To close E8 at process scope, the following command fed the repository config plus an invalid optimization override through `/dev/stdin`; it created no file. `DATABASE_URL`, `REDIS_URL`, `REDIS_HOST` and `LITELLM_MASTER_KEY` were unset so no service or credential path could be contacted.

Command:

```bash
cd "/Users/airm2/My ML Hub/SabiRoute" && env -u DATABASE_URL -u REDIS_URL -u REDIS_HOST -u LITELLM_MASTER_KEY PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -c 'from pathlib import Path; import sys; sys.stdout.write(Path("config/config.yaml").read_text()); sys.stdout.write("\noptimization:\n  policy:\n    max_ratio: 4.0\n")' | env -u DATABASE_URL -u REDIS_URL -u REDIS_HOST -u LITELLM_MASTER_KEY SABIROUTE_CONFIG_PATH=/dev/stdin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -c 'from sabiroute.gateway import build_gateway_state; build_gateway_state()' 2>&1; rc=$?; printf 'EXIT_STATUS=%s\n' "$rc"
```

Output summary:

```text
  File "/Users/airm2/My ML Hub/SabiRoute/src/sabiroute/gateway.py", line 202, in build_gateway_state
    optimization = load_optimization_settings(
  File "/Users/airm2/My ML Hub/SabiRoute/src/sabiroute/config/validation.py", line 196, in load_optimization_settings
    raise ConfigValidationError(f"invalid optimization settings: {exc}") from exc
sabiroute.config.validation.ConfigValidationError: invalid optimization settings: 1 validation error for OptimizationSettings
policy.max_ratio
  Value error, max_ratio must be between 0.25 and 1.0 [type=value_error, input_value=4.0, input_type=float]
EXIT_STATUS=1
```

Two earlier diagnostic attempts failed on unrelated config prerequisites (`model_list must contain at least one deployment`, then default-route deployment/schema checks). Those attempts are not E8 evidence; the final command above isolated the invalid policy and failed at `gateway.py:202` before serving any request.

---

## 4. D2 fresh disposable local PostgreSQL check

**HISTORICAL EVIDENCE:** `artifacts/sprint-phoenix-2/R6.6-R7D2-EXECUTION-RECORD.md` (2026-11-17, HEAD `6f972f8`) records `D2_CHECK_OK` and `D2_CLEANUP_OK` against database `r7_d2_check_phoenix_20261117`. It is cited, not treated as a fresh run.

**VERIFIED BY RUNTIME:** a fresh check was run on 2026-11-18 at HEAD `fb7583b`. It used a newly initialized PostgreSQL 17.10 cluster on an ephemeral port, a disposable database, and Unix socket inside the temporary cluster. No default port 5432, shared server, managed PostgreSQL, credential, or repository database was used.

Final command:

```bash
set -u
ROOT="/Users/airm2/My ML Hub/SabiRoute"
LOCALE=en_US.UTF-8
CLUSTER=$(mktemp -d /tmp/r7-d2-pg-XXXXXX)
PORT=$("$ROOT/.venv/bin/python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
DB="r7_d2_check_phoenix_20261118_${PORT}"
cleanup() {
  if [ -f "$CLUSTER/postmaster.pid" ]; then
    env LANG="$LOCALE" LC_ALL="$LOCALE" /opt/homebrew/bin/pg_ctl -D "$CLUSTER" -m immediate -w stop >/dev/null 2>&1 || true
  fi
  rm -rf "$CLUSTER"
}
trap cleanup EXIT
fail() {
  printf 'COMMAND_FAILED: %s\n' "$*"
  if [ -f "$CLUSTER/server.log" ]; then
    "$ROOT/.venv/bin/python" -c 'import sys; from pathlib import Path; sys.stdout.write(Path(sys.argv[1]).read_text(errors="replace"))' "$CLUSTER/server.log"
  fi
  exit 1
}
run() {
  "$@" || fail "$@"
}
run env LANG="$LOCALE" LC_ALL="$LOCALE" /opt/homebrew/bin/initdb -D "$CLUSTER" --auth-local=trust --auth-host=trust --no-instructions
run env LANG="$LOCALE" LC_ALL="$LOCALE" /opt/homebrew/bin/pg_ctl -D "$CLUSTER" -o "-p $PORT -h 127.0.0.1 -k $CLUSTER -c listen_addresses=127.0.0.1" -l "$CLUSTER/server.log" -w start
run env LANG="$LOCALE" LC_ALL="$LOCALE" /opt/homebrew/bin/createdb -h 127.0.0.1 -p "$PORT" -U airm2 "$DB"
run env LANG="$LOCALE" LC_ALL="$LOCALE" PGHOST=127.0.0.1 PGPORT="$PORT" PGUSER=airm2 PGDATABASE="$DB" PYTHONDONTWRITEBYTECODE=1 "$ROOT/.venv/bin/python" "$ROOT/artifacts/sprint-phoenix-2/R7-D2-check_backup_restore.py"
printf 'D2_FRESH_CHECK_OK port=%s database=%s locale=%s\n' "$PORT" "$DB" "$LOCALE"
run env LANG="$LOCALE" LC_ALL="$LOCALE" /opt/homebrew/bin/pg_ctl -D "$CLUSTER" -m fast -w stop
trap - EXIT
rm -rf "$CLUSTER"
printf 'D2_CLEANUP_OK\n'
```

Output summary:

```text
The database cluster will be initialized with locale "en_US.UTF-8".
The default database encoding has accordingly been set to "UTF8".
...
syncing data to disk ... ok
waiting for server to start.... done
server started
D2_FRESH_CHECK_OK port=56386 database=r7_d2_check_phoenix_20261118_56386 locale=en_US.UTF-8
waiting for server to shut down.... done
server stopped
D2_CLEANUP_OK
```

The sentinel was created before backup, dropped after backup, and recovered by `pg_restore --clean --if-exists`. The cluster and backup file were removed; no database remains on port 56386.

Failed attempts before the final command, recorded for honesty:

| Attempt | Signal | Disposition |
|---|---|---|
| 1 | `initdb: error: invalid locale settings`; later commands failed with connection refused; an unconditional `D2_FRESH_CHECK_OK` marker was printed | Marker invalid; disregarded. Trap removed the temporary cluster. |
| 2 | `initdb` succeeded with `LANG=C`; `pg_ctl: could not start server` | Server process inherited invalid locale; no check ran. Trap removed the temporary cluster. |
| 3 | Server started under `LANG=C`, but check reported `restore did not recover sentinel: [(b'sentinel',)]` | `SQL_ASCII` made `text` return as `bytes`; sentinel was restored but the fixture expected `str`. No file was edited; rerun with UTF-8. |
| 4 | Final `en_US.UTF-8` run above | `D2_FRESH_CHECK_OK`, `server stopped`, `D2_CLEANUP_OK` |

---

## 5. Scope compliance

- **ACTION COMPLETED:** created only `artifacts/sprint-phoenix-2/R7-D1-D2-CONTROLLED-REPLAY-RECORD.md`. No scorecard, D1, D2, D3, workflow, source, config, dependency, or `.github/**` file was edited. No staging, commit, push, branch switch, or worktree was used.
- **WHY:** the inherited R7 state said D1 was defined but not run and D2 had only an older record. This record closes the locally executable portion without claiming coverage that does not exist.
- **RESULT:** 65 focused tests passed; 10 E-mapped node IDs passed; E8 failed startup as expected with exit status 1; fresh D2 disposable check passed and was torn down. E7 remains NOT RUN at scenario level. No full 839-test suite was rerun in this lane.
- **ARCHITECTURAL POSITION:** D1 evidence targets the request-transform stage between SabiRoute Auth/Policy and the Routing Engine, before Fallback and LiteLLM. D2 exercises only a disposable local PostgreSQL backup/restore path. PostgreSQL, Redis, Telemetry, Security and future intelligence behaviour in the product were not changed.
- **ROADMAP POSITION:** advances R7 Tranche D1/D2 evidence. It does not start R9–R20. R6.6 remains `L1/L2 REPLAY PASS · MUTATION MATRIX OPEN`.
- **DEPENDENCY IMPACT:** none in code. The parent agent can reference this dated record from the scorecard; no component depends on it at runtime.
- **NEXT STEP:** decide whether to add a committed scenario-level cancellation test for E7 and stub-provider byte capture for E3–E6, or accept the narrower local replay evidence recorded here.
- **DO NOT TOUCH YET:** `.github/**`, `R7-D3-GITHUB-WORKFLOW.yml`, the scorecard, source code, `uv.lock`, `.env`, `.mcp.json`, `.claude/**`, `reports/provider_verification.json`, managed services, live provider credentials, and R9–R20.
- **STATE DISCREPANCY:** `git ls-files artifacts/sprint-phoenix-2` currently lists `R7-D3-GITHUB-WORKFLOW.yml` as tracked, despite the inherited note that it is untracked. It remains under `artifacts/`, outside `.github/workflows/`, was not modified, and is OUT OF SCOPE.

```text
CURRENT GATE: R7 D1/D2 local evidence recorded; D1 exit gate not fully met; R6.6 mutation matrix open
CURRENT PHASE: R7 Tranche D1/D2
PROVEN: 65 focused tests passed; 10 E-mapped tests passed; E8 process exit 1; fresh D2 disposable PG check passed and cleaned up
UNPROVEN: E7 scenario-level cancellation; stub-provider byte capture for E3-E6; pinned SHA-256 corpus; full suite in this lane
BLOCKED BY: no committed E7 scenario test; no single E1-E8 stub-provider harness; no R6.6 mutation-matrix evidence
NEXT: owner decision on adding E7/stub-provider tests versus accepting narrow local replay evidence
```

---

## 6. Residual blockers

1. E7 is NOT RUN at scenario level; the passing `fail_to_original` helper test is not equivalent to cancellation during the wired transform.
2. E3–E6 have transform/pipeline-level evidence only; they do not satisfy the D1 precondition that a stub provider captures exact bytes.
3. The D1 pinned corpus SHA-256 precondition is not evidenced; these tests use inline fixtures.
4. R6.6 mutation matrix remains open per `R6.6-R7D2-EXECUTION-RECORD.md:27-29`.
5. The full repository suite (`839 passed, 10 skipped` historically) was not rerun in this lane; only the focused module was run.
6. No commit was made. Any commit, push, `.github/**` change, or R9–R20 work still requires the owner's separate decision.

---

## 7. Dated addendum — 2026-11-18, local D1 gaps closed

The §1/§6 findings remain as the record of the first pass. This addendum supersedes only their
status, not their history.

Five tests were added to `tests/test_r6_request_transform.py` with a pinned inline corpus and
SHA-256 constants: `test_d1_e3_tool_exchange_captures_pinned_original_bytes_at_stub`,
`test_d1_e4_cached_prefix_captures_pinned_original_bytes_at_stub`,
`test_d1_e5_capability_loss_sends_pinned_original_bytes_to_stub`,
`test_d1_e6_transform_error_sends_pinned_original_bytes_to_stub`, and
`test_d1_e7_cancellation_inside_transform_reaches_no_stub_provider`. TDD RED was observed for all
five (`5 failed`, `NotImplementedError: D1 corpus pin helper not implemented`), and GREEN was
reached after test-local helpers and production capability wiring.

The E5 RED that mattered was substantive: before the fix the wired call site produced
`BypassReason.NOT_BYPASSED`; after adding
`required_capabilities=classification.required_capabilities` to the `run_transform(...)` call in
`src/sabiroute/api/completions.py:1379`, it produced `BypassReason.CAPABILITY_LOSS` and sent pinned
original bytes. No routing order, policy, fallback, or telemetry behavior changed; independent
code review found no issue.

Fresh gates after the fix: `844 passed, 10 skipped`; `ruff check src tests scripts config` clean;
`mypy src` clean over 61 files; `git diff --check` clean; report manifest 13/13 OK. The ten skips
remain environment/authorization-gated.

**Updated verdict:** R7 D1 `E1–E8 PASS AT LOCAL CONTROLLED-REPLAY SCOPE` — pinned corpus, canonical
provider-bound payload capture for E1–E6 (test-side encoding, not observed HTTP wire bytes),
cancellation raised inside the real transform at E7 with zero provider calls, and E8 process
startup. Budget/quota reservation cleanup on cancellation is outside D1's stated scenario and is
not claimed here. This is not live-provider evidence and does not close R7's external gates (managed
PG/TLS, managed backup/restore, compose E2E, hosted GH run, staging). R6.6 mutation matrix and
R6.7 rollout remain open. D3 remains tracked under `artifacts/`, inert and uninstalled.
