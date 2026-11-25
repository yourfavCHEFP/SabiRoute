# SabiRoute — Local Validation

**Purpose.** Everything here runs on one machine with no provider credentials and no spend. It
is the repeatable path that turns "it worked when I looked" into "here is the command and its
output". Read it before claiming any phase is verified.

**What this document is not.** Local validation never promotes a phase to Complete. "Complete"
requires live verification against real services (see
[architecture-decision-record.md](architecture-decision-record.md) §3–4). Passing everything
below proves the tree is internally consistent — not that it works against a provider.

**Rules of engagement.**

- Use `uv run` for every Python command. Never `pip`, never a system interpreter.
- Never commit a `.coverage` artefact or a scratch coverage config.
- Every number you report must name the command that produced it.
- Hung or skipped tests are reported as such, never as passes.

---

## 1. Baseline gates

These are the same six steps the CI workflow runs `[V]` (`.github/workflows/ci.yml`), in the
same order. Run them from the repository root.

```bash
uv sync --frozen
```

```bash
uv run pytest -q
```

```bash
uv run ruff check src tests scripts config
```

```bash
uv run mypy src
```

```bash
node --check web/app.js
```

```bash
docker build -t sabiroute:ci .
```

**Expected baseline** `[V]` on `feat/sabiroute-routing-foundation` @ `69985da`:

| Gate | Result |
|---|---|
| `pytest -q` | `1123 passed, 9 skipped` |
| `ruff check` | `All checks passed!` |
| `mypy src` | `Success: no issues found in 49 source files` |
| `node --check` | silent (exit 0) |
| `docker build` | succeeds |

If your count differs, do not adjust the expectation — find out why. A different count is
almost always a different checkout (see the worktree trap in §7).

### The nine skips are not failures

Nine tests are environment-gated and skip without a live service:

| Variable | Unlocks |
|---|---|
| `SABIROUTE_TEST_REDIS_URL` | rate-limit tests |
| `SABIROUTE_TEST_PG_URL` | PostgreSQL-backed store tests |

To include them, provide disposable services:

```bash
SABIROUTE_TEST_REDIS_URL=redis://localhost:6379/0 SABIROUTE_TEST_PG_URL=postgresql://postgres:postgres@localhost:5432/sabiroute_test uv run pytest -q
```

CI supplies Redis as a service, so those tests execute there instead of skipping. A skip that
becomes a pass is a real gain in coverage; a skip reported as a pass is a lie.

---

## 2. Coverage measurement

The default configuration excludes pragma-marked defensive lines. To see what is *actually*
unexecuted, including excluded regions, measure with a throwaway config that empties
`exclude_lines` — then delete it.

```bash
uv run pytest -q -p no:cacheprovider --cov=sabiroute
```

```bash
uv run coverage report
```

**Expected** `[V]`: `4641 statements, 0 missed, 100%`, with
`src/sabiroute/api/completions.py` at `784 0 100%`.

### Raw measurement — for audit only

Create `cov-raw.rc` outside the tracked tree, emptying `exclude_lines`, measure, and delete it.
The raw view on the same commit reports:

```
src/sabiroute/api/completions.py    800    15    98%   583-589, 781-787, 1455
TOTAL                              4686    17    99%
```

Fifteen excluded statements remain in `completions.py`, and they are **dead by construction**,
not unproven:

- **583–589 and 781–787** — the two in-flight barrier bodies. `_run_accounting` untracks on
  every exit path (success, exception, cancellation, self-cancelled shielded worker), so
  `in_flight` is already `None` when `finish` / `_cancelled_finish` are entered. The bodies are
  kept as defensive depth for a future overlapping accounting call site.
- **1455** — `if estimated_cost is None:`, unreachable behind a pre-check.

The two other raw misses are `if TYPE_CHECKING:` import lines
(`freepool/eligibility.py:27`, `main.py:32`). They are deliberately unexcluded: a pragma there
would buy a cleaner report and hide a real structural fact, which is the wrong trade.

Rationale and the full evidence table live in
[phase18-testing-evidence.md](phase18-testing-evidence.md).

---

## 3. Database validation (disposable PostgreSQL 16)

Schema is an ordered additive ledger (`SCHEMA_MIGRATIONS`) with no destructive change — see
ADR-006. Validate it against a **disposable** instance, never against anything you care about.

```bash
docker run --rm -d --name sabiroute-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
```

**Fresh init, then idempotent re-run.** Start the app twice against the same database; the
second start must be a no-op. The ledger rows record which revisions have applied.

**Key lifecycle verification:**

```bash
SABIROUTE_TEST_PG_URL=postgresql://postgres:postgres@localhost:5432/sabiroute_test uv run python scripts/verify_postgres.py
```

`verify_postgres.py` verifies connectivity and the API-key lifecycle (issue, use, revoke)
against a real engine `[V]`.

**Backup and restore.**

```bash
docker exec sabiroute-pg pg_dump -U postgres sabiroute_test > /tmp/sabiroute-backup.sql
```

Restore into a second empty instance and confirm the ledger replays identically. An additive
ledger is idempotent by design; this is the property being tested, not a formality.

```bash
docker rm -f sabiroute-pg
```

**What this does not prove.** Local PostgreSQL 16 is not managed PostgreSQL. Connection
pooling, TLS, failover, and provider-specific extensions are unverified. Gate E in the ADR
stays open after this passes.

---

## 4. Migration/ledger sanity

Before reporting any schema claim, confirm the ledger you think exists is the ledger in the
tree:

```bash
grep -nA8 "SCHEMA_MIGRATIONS" src/sabiroute/security/store.py
```

As of `69985da` `[V]` the revisions are `0001`, `0002`, `0003`, `0004`, `0006`. **`0005` is not
a table-adding revision** — it is the schema-group marker row
`0005-schema-groups:<core|full>`. Reading the gap as a missing migration is a mistake this
repository has already invited once; the comment block at `store.py` describes the grouping.

---

## 5. SabiChat browser smoke procedure

`tests/test_sabichat_web.py` proves serving, endpoint parity with the real route table, and
static safety properties (no secrets, no `innerHTML`, no persistent token storage, no direct
provider calls). Its docstring is explicit: *"Interactive browser behavior is covered by the
optional Playwright smoke procedure, not by this file."*

This section is that procedure. It is **optional**, manual, and not part of CI. There is no
automated browser suite in this repository `[V]`.

### Setup

```bash
uv run uvicorn sabiroute.main:app --reload --port 8000
```

The zero-build frontend is served from `web/` at `/app/` — plain HTML/CSS/vanilla JS, no build
step.

### Checklist

Walk these in one session against a running gateway, and record the outcome of each:

1. **Sign-in** — the SabiChat surface authenticates and lands on the conversation view.
2. **Send a message** — a request traverses the same numbered gateway path and a response
   renders.
3. **Conversation creation** — a new conversation appears and is selectable.
4. **Session-token lifetime** — the token is in memory only; **reloading signs you out**. That
   is the documented behaviour, not a bug.
5. **Allowlist denial** — a deployment outside the Free Chat allowlist is refused before
   execution, with a stable reason.

### Recording the result

State what you exercised and what you did not. "The UI works" without a checklist is a memory,
and memories decay. The last recorded session is summarised in
[architecture-decision-record.md](architecture-decision-record.md) §5.

**This never satisfies a phase gate.** A manual pass cannot detect a behavioural regression.

---

## 6. What local validation cannot prove

Every item below is a gate that stays open no matter how green the local run is:

- **Provider behaviour.** No credentials locally, none in CI. Fallback, rate-limit rejection,
  budget exhaustion, and provider failure have never been live-verified (Phase 05).
- **Alias liveness.** Three of fourteen aliases have runtime evidence; the rest are configured
  and dark.
- **Managed PostgreSQL.** See §3.
- **Staging or container orchestration.** The image builds; it has never been deployed.
- **Warm routing performance.** Benchmark output is synthetic.
- **Hosted CI.** The workflow has executed locally step-by-step; a hosted Actions run is
  unverified.

---

## 7. Traps

1. **Run the suite in the worktree that holds the branch you are validating.** A different
   checkout gives a different count, and the difference is not a regression.
2. **A skip is not a pass.** Report `1123 passed, 9 skipped` as exactly that.
3. **Do not leave a scratch coverage config behind.** `git status --short` must be clean of
   `cov-raw.rc` and `.coverage-*` before you commit.
4. **Verify Claude attribution by parsing trailers, never by grep:**
   `git log -1 --format='%(trailers:key=Co-Authored-By,valueonly)' <sha>`.
5. **`cooldown_until = None` means permanent removal, not a reset.** If a health test appears to
   need this reset to pass, the test is wrong.
