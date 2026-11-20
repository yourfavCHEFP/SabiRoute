# Task 4 — Phase 13 read-only re-audit (2026-11-19)

Scope: frozen HEAD `13d0377927e8be5b088c4e5c5026a6aa2650a1aa`; branch observed as `sec/deps-nov`. Endpoint values are withheld throughout: `<LOOPBACK_HOST>`, `<DISPOSABLE_PORT>`, and `<TEMP_DIR>` replace values that existed only inside this task's disposable `/tmp` cluster. No `.env` value was inspected or printed.

## ACTION COMPLETED

- **Files created (only repository file):** `artifacts/production-readiness/T4-phase13-reaudit-2026-11-19.md` (this report).
- **Files modified/deleted in the repository:** none. Tracked-tree check after teardown: `git diff --stat -- .` produced no output; `git status --short --untracked-files=no | wc -l` produced `0`.
- **Git state changes:** none — no commit, staging, push, PR, merge, rebase, reset, clean, stash, checkout, or worktree operation.
- **Commands executed (read-only repository checks):**
  - `git -C "/Users/airm2/My ML Hub/SabiRoute" rev-parse HEAD` → `13d0377927e8be5b088c4e5c5026a6aa2650a1aa`
  - `git -C "/Users/airm2/My ML Hub/SabiRoute" status --short --branch | head -5` → `## sec/deps-nov` followed by pre-existing untracked paths.
  - `grep -nE '13\.[1-5]|Phase 13' README.md ...` → README lines 337, 352–374: Phase 13 `In progress`; 13.1 implemented; 13.2 in progress; 13.3/13.4/13.5 blocked; `No model has been trained or deployed.`
- **Files inspected, not modified:** `docs/phase13-data-foundation.md`, `src/sabiroute/intelligence/dataset.py`, `scripts/audit_routing_dataset.py`, `README.md`, `OFFICIAL_SABIROUTE_ENGINEERING_TEAM_MOBILIZATION_ORDER.md`, and `.superpowers/sdd/sabiroute-production-readiness-mobilization-prompt-2026-11-19/task-4-brief.md`.
- **Disposable infrastructure created and removed:** two private `/tmp` directories (`mktemp -d /tmp/sabiroute-t4-reaudit-pg-XXXXXX`); the first failed initialization and the second ran PostgreSQL 17.10 (Homebrew) on a dynamically selected non-default loopback port, with a private Unix socket directory. Neither used owner defaults `5432`/`5433`, owner sockets, owner data, or owner credentials. No data was seeded.
- **Configuration changed:** none.

## WHY

Phase 13 must remain gated by dataset integrity, not by project optimism. The task requires a fresh read-only re-audit where a real dataset is available, explicit confirmation or `UNVERIFIED` marking of five data criteria, reaffirmation of five sub-gate statuses, and an unchanged `training_authorized` value. No training, invented records, timestamps, labels, costs, propensities, phase upgrade, live provider call, or service mutation was authorized.

## RESULT

### 1. Documentary baseline — `VERIFIED BY INSPECTION` (not a fresh run)

`docs/phase13-data-foundation.md` records a historical, success-only audit: 7 logical requests, 6 provider attempts, 5 requests with feature snapshots, 6 labeled outcomes, 1 feature/outcome count mismatch, 1 outcome without a feature snapshot, 2 attempts with verifiable schema-`1.1` temporal provenance, 4 attempts with legacy/unavailable provenance, and no chronological split or outcome variation. It explicitly says all six recorded provider attempts were successful, that the unmatched historical attempt has no decision timestamp, and that no historical records were repaired. This is documentary evidence only; it is not treated as a fresh runtime result.

### 2. Read-only audit tool — `VERIFIED BY INSPECTION` / `STATIC-ANALYSIS FINDING`

`scripts/audit_routing_dataset.py` reads `DATABASE_URL` (environment overriding `.env`), calls `read_usage_events()`, and prints `readiness_report()`. `read_usage_events()` reflects and selects from `sabiroute_request_usage` only; it does not initialize schema or write rows. `assess_phase13_readiness()` hard-codes `training_authorized: False` and blocks on `feature_outcome_integrity_failed`, `temporal_provenance_incomplete`, `no_outcome_variation`, and `chronological_split_unavailable`. `chronological_split()` groups by logical request and requires a valid timezone-aware decision timestamp; it raises when fewer than two groups exist or groups overlap in time. `diagnostic_export_rows()` quarantines unmatched, malformed, ineligible, or provenance-deficient rows with explicit exclusion reasons while retaining them as diagnostic-only, never training data.

### 3. Dataset availability on fresh disposable PostgreSQL — `VERIFIED BY RUNTIME`

First attempt (no service started):

```text
initdb: error: invalid locale settings; check LANG and LC_* environment variables
pg_ctl: directory "<TEMP_DIR>/data" is not a database cluster directory
```

**Error triage:** (1) error: invalid inherited locale; (2) likely cause: shell `LANG`/`LC_*` not usable by `initdb` — `INFERRED`; (3) evidence: quoted `initdb` output — `VERIFIED BY RUNTIME`; (4) scope: first disposable `/tmp` directory only, no repository file; (5) safest fix: retry with explicit `LC_ALL=C LANG=C` in a new `/tmp` directory. This was done; no unrelated component was changed.

Second attempt (fresh directory, explicit C locale), with `<DISPOSABLE_PORT>` dynamically selected and endpoint values withheld:

```sh
DIR=$(mktemp -d /tmp/sabiroute-t4-reaudit-pg-XXXXXX)
PORT=$("$REPO/.venv/bin/python" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
LC_ALL=C LANG=C /opt/homebrew/bin/initdb -D "$DIR/data" -U postgres -A trust --no-instructions
LC_ALL=C LANG=C /opt/homebrew/bin/pg_ctl -D "$DIR/data" -o "-c listen_addresses=127.0.0.1 -c port=$PORT -c unix_socket_directories=$DIR/socket -c fsync=off" -l "$DIR/postgres.log" -w start
/opt/homebrew/bin/pg_isready -h 127.0.0.1 -p "$PORT"
/opt/homebrew/bin/psql -h 127.0.0.1 -p "$PORT" -U postgres -d postgres -Atqc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
/opt/homebrew/bin/psql -h 127.0.0.1 -p "$PORT" -U postgres -d postgres -Atqc "SELECT to_regclass('public.sabiroute_request_usage')"
```

Sanitized output:

```text
PG_VERSION=postgres (PostgreSQL) 17.10 (Homebrew)
INITDB=syncing data to disk ... ok
START=waiting for server to start.... done
server started
READY=<LOOPBACK_HOST>:<DISPOSABLE_PORT> - accepting connections
PUBLIC_TABLE_COUNT=0
USAGE_TABLE=[]
```

**Finding:** no real dataset existed on the fresh disposable endpoint: the `public` schema contained zero tables and `sabiroute_request_usage` did not exist. No data was seeded. `VERIFIED BY RUNTIME`.

### 4. Diagnostic-only audit invocation — retained failure excerpt — `VERIFIED BY RUNTIME`

This invocation was a **diagnostic-only safety check**, not the acceptance audit. The endpoint had already been shown dataset-free (`PUBLIC_TABLE_COUNT=0`, `USAGE_TABLE=[]`), so no readiness conclusion can be drawn from the invocation. It was run solely to capture the existing read-only tool's behavior against a safe private endpoint and to document any exact failure rather than guessing at one. All five fresh data criteria remain `UNVERIFIED` and the verdict remains `ML NOT DONE`. The script was invoked from the disposable directory (so its internal `.env` lookup did not read the repository `.env`) with an explicit environment-only connection value:

```sh
cd "$DIR"
PYTHONPATH="$REPO/src" DATABASE_URL="postgresql://postgres@<LOOPBACK_HOST>:<DISPOSABLE_PORT>/postgres" \
  "$REPO/.venv/bin/python" "$REPO/scripts/audit_routing_dataset.py"
```

**Retention disclosure:** only an excerpt of the 99-line traceback was retained in this session. The complete original traceback is not available here; it is not reconstructed below. Host, port, and temporary-directory values are redacted. The retained head and tail are shown verbatim as retained excerpts; the intervening SQLAlchemy frames are not represented.

```text
Traceback (most recent call last):
  File "/Users/airm2/My ML Hub/SabiRoute/scripts/audit_routing_dataset.py", line 102, in <module>
    main()
  File "/Users/airm2/My ML Hub/SabiRoute/scripts/audit_routing_dataset.py", line 51, in main
    events = read_usage_events(str(database_url))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/airm2/My ML Hub/SabiRoute/src/sabiroute/intelligence/dataset.py", line 1542, in read_usage_events
    table = Table("sabiroute_request_usage", metadata, autoload_with=engine)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  [... intervening SQLAlchemy frames were not retained and are not reconstructed ...]
  File "/Users/airm2/My ML Hub/SabiRoute/.venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 759, in initialize
    self.server_version_info = self._get_server_version_info(
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/airm2/My ML Hub/SabiRoute/.venv/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/base.py", line 4073, in _get_server_version_info
    m = re.match(
        ^^^^^^^^^
  File "/Users/airm2/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none/lib/python3.11/re/__init__.py", line 166, in match
    return _compile(pattern, flags).match(string)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot use a string pattern on a bytes-like object
EXIT_CODE=1
```

**Error triage:** (1) error: `TypeError` during SQLAlchemy PostgreSQL dialect initialization, before `autoload_with` completed; (2) likely cause: installed SQLAlchemy/psycopg interaction returned bytes where a string regex was expected — `INFERRED`, not root-caused because dependency changes and broader investigation were out of scope; (3) evidence: retained traceback excerpt with observed exit code — `VERIFIED BY RUNTIME`; (4) scope: this diagnostic invocation only; it did not reach the dataset query and did not mutate data; (5) safest fix: leave dependencies untouched under this task and record the failure; investigate compatibility separately with owner authorization. No fresh numeric audit result was produced.

### 5. Five data criteria

| Criterion | Fresh status | Evidence and meaning |
|---|---|---|
| Pair integrity | `UNVERIFIED` | Fresh audit stopped before querying; historical document reports 1 count mismatch and 1 outcome without a snapshot. Tool logic quarantines such rows (`STATIC-ANALYSIS FINDING`). |
| Temporal provenance | `UNVERIFIED` | Fresh audit produced no report. Historical document reports only 2 schema-`1.1` verified attempts versus 4 legacy/unavailable, with no invented provenance (`VERIFIED BY INSPECTION` of document). |
| Outcome variation | `UNVERIFIED` | Fresh audit produced no counts. Historical document says all six attempts succeeded, so no variation was observed (`VERIFIED BY INSPECTION` of document). |
| Chronological split feasibility | `UNVERIFIED` | Fresh audit produced no split. Historical document says unavailable because the unmatched attempt has no decision timestamp; tool requires valid timestamps and at least two non-overlapping groups (`STATIC-ANALYSIS FINDING`). |
| Exclusions | `UNVERIFIED` for live rows; `STATIC-ANALYSIS FINDING` for mechanism | No live rows existed to classify. Code retains unmatched/malformed/ineligible/provenance-deficient rows as quarantined diagnostics with explicit reasons; no training candidate or candidate export is written while readiness is `BLOCKED`. |

### 6. Five sub-gates reaffirmed — `VERIFIED BY INSPECTION`

- **13.1 data foundation:** Implemented — schema `1.1` snapshots, read-only audit, and committed implementation `71271fc`.
- **13.2 target/labels/provenance/audit:** In progress — live sub-gate passed historically; aggregate integrity acceptance did not pass.
- **13.3 training and evaluation:** BLOCKED — integrity mismatch, incomplete provenance, no outcome variation, no defensible chronological split.
- **13.4 guarded inference:** BLOCKED pending a valid trained artifact.
- **13.5 ML selector integration:** BLOCKED pending validated inference.
- **Verdict: `ML NOT DONE`.** `training_authorized` remains `False`/unchanged; no training command ran and no model artifact was created (`VERIFIED BY INSPECTION` of code and `VERIFIED BY RUNTIME` absence of training actions in this task).

### 7. Teardown proof — `VERIFIED BY RUNTIME`

Exact commands actually run (endpoint/port redacted in output only; `$DIR` and `$PORT` were set inside the same shell):

```sh
/opt/homebrew/bin/pg_ctl -D "$DIR/data" -m fast -w stop
rm -rf /tmp/sabiroute-t4-reaudit-pg-XfCmNu /tmp/sabiroute-t4-reaudit-pg-3u5aJz
echo "removed=$? dirs=$(ls -d /tmp/sabiroute-t4-reaudit-pg-* 2>/dev/null | wc -l | tr -d ' ')"
/opt/homebrew/bin/pg_isready -h 127.0.0.1 -p "$PORT"
```

Exact retained output, in the same order:

```text
--- STOP ACTIVE CLUSTER ---
waiting for server to shut down.... done
server stopped
--- REMOVE TEMP DIRS ---
(eval):12: no matches found: /tmp/sabiroute-t4-reaudit-pg-*
removed=0 dirs=0
--- POST-TEARDOWN PROBE ---
<LOOPBACK_HOST>:<DISPOSABLE_PORT> - no response
--- REPO TRACKED STATE ---
tracked_diff_lines=0
```

`removed=0` is the exit status of the `rm -rf` command captured immediately afterward. The `dirs=0` count came from `ls -d /tmp/sabiroute-t4-reaudit-pg-* 2>/dev/null | wc -l | tr -d ' '`; the stale `zsh` glob message appeared because no matching directory remained. The final `pg_isready` probe reported no response at the former disposable endpoint. These outputs together prove both `/tmp` clusters were deleted and no disposable service remained. No owner PostgreSQL socket, port, data directory, or process was contacted. No endpoint value appears in this report.

## ARCHITECTURAL POSITION

This task only observes the evidence path: Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter → Routing Engine → Fallback → LiteLLM → Provider → Response. It changes no routing stage. PostgreSQL was contacted only through a private disposable cluster and read-only reflection/SELECT intent; the audit failed before its SELECT. Redis was not contacted. Telemetry remains observational and selection-biased: outcomes exist only for selected deployments. Security is unchanged: no credential, key, `.env` value, prompt, completion, or identity was exposed. Future intelligence remains gated by deterministic-first, leakage-safe data; ML must not route to unhealthy deployments and cannot bypass eligibility or deterministic fallback.

## ROADMAP POSITION

Phase 13 only. This is a read-only verification and gate-maintenance action: it reaffirms 13.1 implemented, 13.2 in progress, and 13.3–13.5 blocked. It advances no phase, upgrades no status, and does not open training.

## DEPENDENCY IMPACT

No existing component depends on this report to execute. Phase 13.3 training, 13.4 guarded inference, and 13.5 selector integration all remain blocked by it. The audit script's dependency/runtime incompatibility is a separate finding for a future authorized dependency investigation; it was not changed here. Deterministic-v1 routing, capability/health filtering, fallback, provider execution, budgets, and admin behavior are untouched.

## NEXT STEP

With explicit owner authorization, investigate the SQLAlchemy/psycopg runtime incompatibility and re-run the read-only audit against an authorized real dataset; do not seed or synthesize records.

## DO NOT TOUCH YET

No commits, pushes, PRs, branches, merges, rebases, resets, cleans, stashes, checkouts, or worktrees. No source, config, tests, `uv.lock`, `.env`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, or `reports/provider_verification.json` changes. No owner PostgreSQL/Redis service, port `5432`/`5433`/`6379`, live provider call, training job, model artifact, phase-status upgrade, `training_authorized` change, invented timestamp/label/cost/propensity, or historical-record repair. Empty placeholders and zero-byte files remain untouched.

## CURRENT PROJECT STATUS

```text
CURRENT GATE: Task 4 re-audit completed with no fresh numeric audit result; no dataset existed on the disposable endpoint and the audit invocation failed during SQLAlchemy dialect initialization. ML NOT DONE; training_authorized unchanged.
CURRENT PHASE: 13 — ML-assisted routing; 13.1 implemented, 13.2 in progress, 13.3 BLOCKED, 13.4 BLOCKED, 13.5 BLOCKED.
PROVEN: Frozen HEAD verified; historical documentary counts read; audit tool's read-only/blocking logic inspected; disposable PostgreSQL reachable but dataset-free; diagnostic audit failure excerpt and exit code captured; both /tmp clusters removed; tracked tree clean; no Git state change.
UNPROVEN: Fresh pair integrity, temporal provenance, outcome variation, chronological-split feasibility, and live-row exclusions; no real dataset was available, so these remain UNVERIFIED rather than failed or passed.
BLOCKED BY: No authorized real dataset on the disposable endpoint; SQLAlchemy/psycopg runtime TypeError before the SELECT; historical integrity mismatch, incomplete temporal provenance, no outcome variation, unavailable chronological split.
NEXT: Obtain owner authorization to investigate the audit-runtime incompatibility and repeat the read-only audit against an authorized real dataset.
```

## FIX REPORT

Scope: fix round 1/5 changed only `artifacts/production-readiness/T4-phase13-reaudit-2026-11-19.md`. No source, config, test, protected-path, or Git change; no service was started; no new investigation was performed.

Covering command and exact output:

```sh
cd "/Users/airm2/My ML Hub/SabiRoute" && git diff --check; echo "exit_code=$?"
```

```text
exit_code=0
```

`git diff --check` produced no stdout or stderr; only the captured `exit_code=0` line appeared. The report is an untracked artifact, so this command verifies the tracked tree remains whitespace-clean; the covering artifact for the fix is this report itself. No test suite was run because this was a documentation-only change.

Changes made:
1. Replaced the “sanitized output … otherwise verbatim” claim with an explicit retention disclosure: only an excerpt of the 99-line traceback was retained; the complete original is unavailable and is not reconstructed. Removed the placeholder line implying omitted frames were accounted for as a verbatim record.
2. Relabeled the invocation “Diagnostic-only audit invocation” and explained that it was a safety check after the endpoint was confirmed dataset-free, not an acceptance audit; no readiness conclusion was drawn from it. All five fresh criteria remain `UNVERIFIED` and the verdict remains `ML NOT DONE`.
3. Added the exact teardown deletion/probe commands and their retained output, including `removed=0`, `dirs=0`, the stale `zsh` glob message, and the no-response final probe. These replace the previous indirect teardown presentation.
4. Corrected the `PROVEN` line from “exact audit failure captured” to “diagnostic audit failure excerpt and exit code captured.”
