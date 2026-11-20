# Task 5 — Local CI completeness

Date: 2026-11-19
Frozen HEAD (VERIFIED BY RUNTIME): `13d0377927e8be5b088c4e5c5026a6aa2650a1aa`
Branch observed (VERIFIED BY RUNTIME): `sec/deps-nov`
Git actions: none (forbidden). No commit, staging, push, PR, merge, rebase, reset, clean, stash, checkout, or worktree creation.
Endpoint values: withheld. `SABIROUTE_TEST_REDIS_URL` and `SABIROUTE_TEST_PG_URL` were composed only inside the one shell command's environment and were never written to a file, report, commit, or printed output. Report placeholders are `<REDIS_URL>` and `<PG_URL>`. No credentials or owner infrastructure were used.

Evidence labels used: VERIFIED BY INSPECTION, VERIFIED BY RUNTIME, STATIC-ANALYSIS FINDING, INFERRED, UNVERIFIED.

---

## ACTION COMPLETED

- FILE CREATED (VERIFIED BY RUNTIME): `artifacts/production-readiness/T5-local-ci-evidence-2026-11-19.md` (this report). It is the only repository file created.
- FILES MODIFIED / DELETED INSIDE REPOSITORY (VERIFIED BY RUNTIME): none.
- WORKFLOW READ (VERIFIED BY INSPECTION): `.github/workflows/ci.yml`, read-only; no edit.
- LOCAL CHECKS EXECUTED ONCE EACH (VERIFIED BY RUNTIME): full pytest suite with fresh disposable Redis/PostgreSQL in the command environment, Ruff, mypy, `node --check web/app.js`, and the workflow's `docker build -t sabiroute:ci .` command.
- DISPOSABLE INFRASTRUCTURE (VERIFIED BY RUNTIME): fresh `/tmp` tree, fresh PostgreSQL cluster with a fresh `initdb` data directory and a fresh `_test` database, and a fresh non-persistent Redis server, both bound to loopback on dynamically selected non-owner ports (never 6379, 5432, or 5433; PostgreSQL used a private `/tmp` socket directory). Ports and database name are withheld.
- TEARDOWN (VERIFIED BY RUNTIME): PostgreSQL stopped, Redis shut down without saving, both ports confirmed not listening, both processes confirmed absent, and the service temp directory confirmed absent.
- POST-RUN STATE (VERIFIED BY RUNTIME): HEAD unchanged; tracked diff empty; zero disposable Redis/PG processes remained.
- CONFIGURATION / DEPENDENCY CHANGES (VERIFIED BY RUNTIME): none in the repository. `PGCLIENTENCODING=UTF8` was used in the pytest command environment only, matching the Task 1 encoding fix. No `uv.lock`, `.env`, source, test, or configuration edit occurred.

Command shapes (endpoint values withheld; exact local outputs are in RESULT):

```sh
# disposable service preparation, one shell; dynamic nonstandard loopback ports
mktemp -d /tmp/sabiroute-t5-20261119.XXXXXX
mktemp -d /tmp/sabiroute-t5-outputs.XXXXXX
initdb -D <TMP_DIR>/pgdata --username=postgres --auth-local=trust --auth-host=trust --no-instructions
pg_ctl -D <TMP_DIR>/pgdata -l <TMP_DIR>/pg.log -o "<loopback bind options>" -w start
createdb <DISPOSABLE_DB_NAME>
redis-server <loopback bind options> --save '' --appendonly no --dir <TMP_DIR> --daemonize yes --pidfile <TMP_DIR>/redis.pid --logfile <TMP_DIR>/redis.log

# local-equivalent checks, each run once
env PGCLIENTENCODING=UTF8 SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q
uv run ruff check src tests scripts config
uv run mypy src
node --check web/app.js
docker build -t sabiroute:ci .

# teardown
pg_ctl -D <TMP_DIR>/pgdata -m fast -w stop
redis-cli <loopback options> shutdown nosave
rm -rf <TMP_DIR>
```

---

## WHY

The workflow defines six runnable checks after checkout and locked dependency setup. A passing local default suite alone does not prove the Redis/PostgreSQL gated tests ran, and a read-only workflow inspection cannot prove the commands succeed on this frozen tree. This task reproduces each reproducible check locally, converts the environment-gated skips with fresh disposable services, and records the one step that cannot run because the local Docker daemon is unavailable. Hosted GitHub Actions remains outside this task's authority.

---

## RESULT

### 1. Workflow-to-local equivalence (VERIFIED BY INSPECTION + VERIFIED BY RUNTIME)

| Workflow step (`.github/workflows/ci.yml`) | Local equivalent command | Result |
|---|---|---|
| `Check out repository` (`actions/checkout@v4`) | No local equivalent; operating on the frozen checked-out tree at `13d0377` | Not applicable locally; HEAD verified, exit `0` from `git rev-parse HEAD` (VERIFIED BY RUNTIME) |
| `Set up uv` (`astral-sh/setup-uv@v5`, Python 3.11) | No local equivalent run; `uv` and `./.venv/bin/python` already present | Hosted action UNVERIFIED; local tools confirmed available (VERIFIED BY RUNTIME) |
| `Install dependencies (locked)` — `uv sync --frozen` | Not re-run: this evidence task forbids dependency/environment mutation; existing locked `.venv` used | Hosted step UNVERIFIED; no dependency state changed (VERIFIED BY RUNTIME) |
| `Run test suite` — `uv run pytest -q` | `env PGCLIENTENCODING=UTF8 SABIROUTE_TEST_REDIS_URL=<REDIS_URL> SABIROUTE_TEST_PG_URL=<PG_URL> ./.venv/bin/python -m pytest -q` | PASS — `875 passed, 1 skipped in 35.35s`, exit `0` (VERIFIED BY RUNTIME). Local invocation uses the project interpreter explicit per repository protocol; the workflow's Redis service URL was substituted with a disposable one. |
| `Ruff check` — `uv run ruff check src tests scripts config` | Same command | PASS — `All checks passed!`, exit `0` (VERIFIED BY RUNTIME) |
| `Mypy` — `uv run mypy src` | Same command | PASS — `Success: no issues found in 61 source files`, exit `0` (VERIFIED BY RUNTIME) |
| `Frontend syntax check` — `node --check web/app.js` | Same command | PASS — no output, exit `0` (VERIFIED BY RUNTIME) |
| `Build application container` — `docker build -t sabiroute:ci .` | Same command, local Docker only, never pushed | FAIL locally / UNVERIFIED — Docker daemon unavailable; exact error below, exit `1` (VERIFIED BY RUNTIME) |

Hosted GitHub Actions, workflow dispatch, push, PR, hosted build, deployment, and registry actions: UNVERIFIED and not attempted (VERIFIED BY RUNTIME from the absence of such commands in this task). No workflow file was edited (VERIFIED BY INSPECTION + VERIFIED BY RUNTIME).

### 2. Disposable service setup (VERIFIED BY RUNTIME)

Readiness markers: `SERVICE_SETUP redis_ping_exit=0 pg_isready_exit=0`.

One non-fatal harness warning appeared while reading the Redis PID file:

```text
(eval):79: no such file or directory: <TMP_DIR>/redis.pid
```

The server itself was reachable (`redis-cli ping` exit `0`) and teardown subsequently proved the process was absent and the port was closed. STATIC-ANALYSIS FINDING: the warning is in this task's transient PID-file read, not in repository code or CI behavior. No blind retry was performed.

### 3. Full suite — single authoritative run (VERIFIED BY RUNTIME)

Exact output (endpoint-free by scan; only the skip reason is reproduced):

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
875 passed, 1 skipped in 35.35s
PYTEST_EXIT=0
```

Skip accounting (VERIFIED BY RUNTIME + VERIFIED BY INSPECTION of Task 1 evidence): 876 collected; no-service baseline `866 passed / 10 skipped`; this run `875 passed / 1 skipped`. Nine environment-gated tests were converted from skips to passes by the disposable Redis/PostgreSQL environment (4 shipped Redis integration, 1 Redis real-service control, 3 shipped PostgreSQL integration, 1 PostgreSQL real-service control). The single remaining skip is the deliberate R6 registration-ledger authorization gate at `tests/test_r6_registration_digest_conformance.py:570`; no ledger was fabricated.

### 4. Static checks and frontend syntax (VERIFIED BY RUNTIME)

```text
=== RUFF OUTPUT ===
All checks passed!
RUFF_EXIT=0

=== MYPY OUTPUT ===
Success: no issues found in 61 source files
MYPY_EXIT=0

=== NODE OUTPUT ===
NODE_EXIT=0
```

`node --check web/app.js` emitted no stdout or stderr. The mypy count is reported exactly as observed on this tree.

### 5. Container build blocker (VERIFIED BY RUNTIME)

Command: `docker build -t sabiroute:ci .` (local Docker only; no push).

Exact output:

```text
ERROR: Cannot connect to the Docker daemon at unix:///Users/airm2/.docker/run/docker.sock. Is the docker daemon running?
DOCKER_EXIT=1
```

Error triage (STATIC-ANALYSIS FINDING unless stated):
1. Error: Docker client could not connect to its local daemon socket; build never started.
2. Likely cause: Docker daemon is not running in this environment.
3. Evidence: exact stderr above, exit `1`; no build steps were emitted.
4. Scope: container-build step only. All Python, frontend, and real-service test steps completed and passed; no repository file changed.
5. Safest fix: owner starts the local Docker daemon, then a separately authorized rerun of the same local command. Starting a daemon, retrying blindly, pushing an image, or invoking hosted CI is outside this task. Container build therefore remains UNVERIFIED.

### 6. Teardown proof (VERIFIED BY RUNTIME)

Exact output:

```text
PG_STOP_EXIT=0
REDIS_SHUTDOWN_EXIT=0
REDIS_PORT_LISTENING=false
POSTGRES_PORT_LISTENING=false
REDIS_PROCESS_PRESENT=false
POSTGRES_PROCESS_PRESENT=false
TEMP_DIR_ABSENT=true
```

Post-run independent check (VERIFIED BY RUNTIME): `HEAD=13d0377927e8be5b088c4e5c5026a6aa2650a1aa`, `TRACKED_DIFF_LINES=0`, `SERVICE_TEMP_DIRS=0`, `REDIS_T5_PROCESSES=0`, `PG_T5_PROCESSES=0`. No owner service, owner socket, owner data directory, pre-existing untracked path, or `.env` value was touched.

---

## ARCHITECTURAL POSITION

No production code changed. The exercised path is the repository's CI-equivalent test and static-check surface around the existing gateway (VERIFIED BY INSPECTION). Pipeline:

```text
Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter
       → Routing Engine → Fallback → LiteLLM → Provider → Response
```

- Authentication / policy: real Redis and PostgreSQL gated tests executed; no policy or authentication behavior changed.
- Classification / capability / health / routing / fallback / LiteLLM / provider: untouched; no provider call was made.
- PostgreSQL: a fresh disposable `_test` database was created, exercised, stopped with its cluster, and removed with the `/tmp` tree.
- Redis: a fresh non-persistent loopback instance was used and shut down without saving.
- Telemetry: no telemetry configuration or emitted routing telemetry changed.
- Security: no credentials were used, read, or printed; no protected path was edited; hosted actions remained unauthorized.
- Future intelligence: no dataset, training, scoring change, or phase-status upgrade occurred.

---

## ROADMAP POSITION

This is production-readiness Task 5 evidence, not a Phase 00–20 status change (VERIFIED BY INSPECTION of the task brief). It supplies Phase 19-style local-CI evidence for the frozen tree; it does not make hosted CI live-verified, does not complete Phase 19, and does not upgrade any phase status. Phase 13 remains in progress with 13.3 BLOCKED and `training_authorized` unchanged (VERIFIED BY INSPECTION of prior readiness reports).

---

## DEPENDENCY IMPACT

No `pyproject.toml`, `uv.lock`, installed-package state, source, test, or configuration was changed (VERIFIED BY RUNTIME). `uv run` used the existing environment without a frozen sync; no dependency drift was introduced. Later gate-closure work may cite these local results, but they do not substitute for a hosted CI run, a successful container build, or owner release acceptance. The container-build step remains dependent on an authorized local daemon start or a separately authorized hosted run.

---

## NEXT STEP

Report the local results and the Docker-daemon blocker to the owner; await an explicit decision on starting local Docker for a separate build rerun or authorizing a hosted CI run. No repository change is proposed here.

---

## DO NOT TOUCH YET

- `.github/workflows/ci.yml` and all other protected paths: `.github/**`, `.env`, `uv.lock`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`.
- Source, tests, configuration, zero-byte placeholders, and all security, intelligence, and routing implementations.
- Owner Redis (port 6379), owner PostgreSQL (ports 5432/5433 and owner sockets), owner data directories, and any pre-existing untracked path.
- Workflow dispatch, push, PR, hosted Actions, registry push, deployment, publication, live provider calls, live request drills, architecture changes, training, and phase-status upgrades.
- R6 registration-ledger instantiation without explicit authorization.

---

## CURRENT PROJECT STATUS

```text
CURRENT GATE: Task 5 local CI equivalence complete for five runnable steps at frozen HEAD 13d0377 (pytest 875 passed / 1 skipped exit 0 with disposable services; Ruff exit 0; mypy 61 files exit 0; node --check exit 0). Container build blocked locally by unavailable Docker daemon, exit 1; hosted Actions UNVERIFIED. Production-readiness closure remains open.
CURRENT PHASE: Roadmap statuses unchanged from frozen HEAD; Phase 13 in progress with 13.3 BLOCKED. Task 5 is Phase 19-style evidence only, not a phase advance.
PROVEN: VERIFIED BY RUNTIME — HEAD unchanged; tracked diff empty; one full suite converted nine service skips to passes; static checks green; exact Docker error captured; services stopped, ports closed, processes absent, temp service directory absent. VERIFIED BY INSPECTION — workflow steps and no protected-path edit.
UNPROVEN: Hosted GitHub Actions, container build success, hosted build image, live-provider paths, production rollout, owner release acceptance, and authorized R6 ledger instantiation.
BLOCKED BY: Local Docker daemon unavailable for container build; fresh owner authorization required for hosted CI, push, deployment, publication, live drills, training, and any phase-status upgrade. No technical blocker remains for the local test/lint/type/frontend steps.
NEXT: Owner decision on the container-build blocker and hosted CI; no code change.
```
