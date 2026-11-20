# S1–S18 Local Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close every locally fixable S1–S18 gap with evidence, tests, and honest gate reporting, without opening an owner or external gate.

**Architecture:** The work is a coordinated closure tranche, not a product feature. Evidence and documentation tasks establish a current-HEAD crosswalk and correct stale claims. Bounded test-first changes fix readiness recovery, lineage reconciliation, redaction documentation, and admin executor boundary behavior. The routing pipeline, deterministic-v1 formula, LiteLLM boundary, and all external gates remain unchanged.

**Tech Stack:** Python 3.x, FastAPI, SQLAlchemy, pytest, Ruff, mypy, uv, `./.venv/bin/python`, shell-based evidence artifacts.

**Spec:** `docs/superpowers/specs/2026-11-18-s1-s18-local-gap-closure-design.md`

**Execution method already supplied by owner:** subagent-driven execution in this session; fresh implementer and fresh reviewer per task.

## Global Constraints

- Current branch is `sec/deps-nov`; HEAD at planning is `4294eb701d366562feed2a1a15bb1a8b41e0acbe`.
- Do not push, merge, rebase, reset, clean, stash, amend, or rewrite history.
- Do not modify `main`.
- Stage only explicitly listed paths; inspect the complete staged diff; never use `git add .` or `git add -A`.
- Protected paths: `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`.
- Never read or print `.env` values or live credentials; report credential variable names and set/empty status only.
- Use `uv` and `./.venv/bin/python`; never hand-edit `uv.lock`.
- No live provider call, credential change, spend authorization, managed service, hosted CI, staging, production deploy, D3 installation, R6.6 mutation execution, R6.7 rollout, registration ledger, `training_authorized` change, dashboard UI, or zero-byte placeholder edit.
- Preserve every pre-existing untracked file.
- Use repository evidence labels: `VERIFIED BY INSPECTION`, `VERIFIED BY RUNTIME`, `STATIC-ANALYSIS FINDING`, `INFERRED`, `UNVERIFIED`.
- Behavior changes must be RED → GREEN → REFACTOR with a failing test observed first.
- Every commit message ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

- **Stale status laundering:** a document row must never convert historical or offline evidence into owner acceptance; Task 1 pins a gate column for every S1–S18 row.
- **Readiness fail-open regression:** a transient post-startup schema check must not permanently null stores or mask a real startup failure; Task 4 pins 503-then-recovery after one transient failure.
- **False lineage reconciliation:** a zero-row lineage update must not be reported as reconciled; Task 5 pins both direct-store and HTTP 409 behavior.
- **Redaction overclaim:** residual pattern-based redaction gaps must be documented as residual, not claimed eliminated; Task 6 pins the known boundaries.
- **Admin executor slot/cancellation leak:** store faults must produce stable typed 503 without secret text, and cancellation must not leak an executor slot; Task 7 pins both.

---

### Task 1: S1/S2 evidence baseline

**Files:**
- Create: `artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md`
- Create: `artifacts/sprint-phoenix-2/S2-BASELINE-ADDENDUM.md`

**Interfaces:**
- Consumes: scout evidence in `reports/`, `docs/build-map.md`, `REPORTS-PROVENANCE.md`, `reports/my_scorecard.md`, and gate artifacts under `artifacts/sprint-phoenix-2/`.
- Produces: a current-HEAD crosswalk with 18 sprint rows and a baseline addendum. No code interface.

- [ ] **Step 1: Create the S1–S18 crosswalk**

Use columns: `Sprint | Verified state | Evidence anchor | Remaining gate | Evidence label`. Include exactly S1 through S18. Every row must retain its open gate where one exists. Do not write `DONE` for any sprint.

- [ ] **Step 2: Verify crosswalk anchors**

Open every cited file and line/section. Replace any anchor that does not support the claim.

- [ ] **Step 3: Re-run the baseline gates**

Run in order:
```bash
./.venv/bin/python -m pytest -q
uv run ruff check src tests scripts config
uv run mypy src
git diff --check
shasum -c REPORTS-MANIFEST.sha256
```
Record exact commands, exit codes, pass/skip counts, skip reasons, and branch/HEAD/worktree state in the addendum.

- [ ] **Step 4: Verify no gate upgrade**
```bash
rg -n 'DONE|COMPLETE|training_authorized=true|live.*PASS' artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md
```
Expected: no unqualified completion or gated-status claim.

- [ ] **Step 5: Commit**
```bash
git add artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md artifacts/sprint-phoenix-2/S2-BASELINE-ADDENDUM.md
git commit -m "docs(s1-s18): add current-head crosswalk and baseline" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: S3/S5/S8/S16 documentation corrections

**Files:**
- Modify: `docs/providers.md:9-25`
- Modify: `docs/failure-injection-runbook.md:9-12,70-79`
- Modify: `README.md:603-611`

**Interfaces:**
- Consumes: `artifacts/sprint-phoenix-2/R2-LIVE-PROVIDER-MATRIX-GATE.md`, `src/sabiroute/quotas.py:78-110`, `src/sabiroute/api/completions.py:1168-1189`, `tests/test_user_quotas.py`.
- Produces: corrected documentation only; no public API change.

- [ ] **Step 1: Add provider contract gap note**

In `docs/providers.md`, add an explicit note or column naming untested contract dimensions: provider-reported usage, tool calls, context limits, authentication translation, and live response shape. Keep R2 `BLOCKED — NOT DONE`.

- [ ] **Step 2: Correct failure-injection runbook**

Replace references to nonexistent `routing/fallback.py`, `FallbackEngine`, and `providers/healthcheck.py` with the real completion retry loop, `routing/health.py` passive cooldown, and `tests/test_fallback_injection.py`. Do not claim live failure injection is complete.

- [ ] **Step 3: Correct quota enforcement wording**

Change `README.md:611` so “runtime quota enforcement” is no longer listed as unimplemented. State that it is implemented and tested for the opt-in pilot cohort, 50,000-token UTC day, fail-closed on unavailable state. Keep catalogue mapping, provider-terms validation, shared inference, and provider-side quota discovery unimplemented.

- [ ] **Step 4: Verify changed lines**
```bash
git diff --check
rg -n 'FallbackEngine|providers/healthcheck|runtime quota enforcement' docs/failure-injection-runbook.md README.md
```
Expected: `git diff --check` clean; no stale names; quota line reflects implemented scope.

- [ ] **Step 5: Commit**
```bash
git add docs/providers.md docs/failure-injection-runbook.md README.md
git commit -m "docs: correct provider, failure, and quota status" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: S9/S13/S17/S18 evidence documents

**Files:**
- Create: `artifacts/sprint-phoenix-2/CD1-CD6-FINAL-REPORT.md`
- Create: `docs/incident-response-runbook.md`
- Create: `artifacts/sprint-phoenix-2/COMPETITIVE-EVIDENCE-MATRIX-DRAFT.md`
- Modify: `docs/phase13-data-foundation.md:140-156`
- Modify: `docs/deployment.md:127-143`

**Interfaces:**
- Consumes: `docs/compression-discovery-packet.md`, `docs/phase13-data-foundation.md`, `README.md:358`, `reports/pre-roadmap-audit.md:116-127`, checklist S13–S18 rows.
- Produces: evidence documents only; no acceptance gate upgraded.

- [ ] **Step 1: Compile CD1–CD6 report**

Write the report from the existing discovery packet. State explicitly: Sprint 9 design acceptance, T8 review, and owner implementation authorization remain open.

- [ ] **Step 2: Correct Phase 13.1 commit line**

Change only the statement that snapshot/audit work is “not yet isolated in a Phase 13 commit” so it says the work is committed as `71271fc`. Preserve integrity FAILED, readiness BLOCKED, and `training_authorized: false`.

- [ ] **Step 3: Add incident-response runbook**

Create a narrow runbook covering readiness 503, startup/schema failure, auth/store 503, Redis 503, provider-failure classification, rollback, evidence capture, and secret redaction. Label it local-only and not production verification. Link it from `docs/deployment.md` under startup/shutdown/rollback.

- [ ] **Step 4: Add competitive evidence matrix draft**

Build only from existing anchors. List evidence status and untested dimensions. Do not add competitor-performance rankings or treat the OmniRoute benchmark as done.

- [ ] **Step 5: Verify no gate upgrade**
```bash
rg -n 'training_authorized.*true|OMNIROUTE.*PASS|Sprint 9.*DONE|T8.*accepted' artifacts/sprint-phoenix-2/CD1-CD6-FINAL-REPORT.md artifacts/sprint-phoenix-2/COMPETITIVE-EVIDENCE-MATRIX-DRAFT.md docs/phase13-data-foundation.md docs/incident-response-runbook.md
```
Expected: no unqualified acceptance claim.

- [ ] **Step 6: Commit**
```bash
git add artifacts/sprint-phoenix-2/CD1-CD6-FINAL-REPORT.md artifacts/sprint-phoenix-2/COMPETITIVE-EVIDENCE-MATRIX-DRAFT.md docs/incident-response-runbook.md docs/phase13-data-foundation.md docs/deployment.md
git commit -m "docs: compile s9-s18 evidence and correct phase 13 record" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: S6-F3 readiness recovery

**Files:**
- Test: `tests/test_admin.py`
- Modify only if RED proves the defect: `src/sabiroute/api/health.py:39-57`

**Interfaces:**
- Consumes: `readiness(request: Request) -> JSONResponse` in `src/sabiroute/api/health.py`; `gateway.startup_error`, `gateway.key_store`, `gateway.chat_store`; schema checks `check_schema`, `check_shared_inference_schema`, `check_sabichat_schema`.
- Produces: a readiness endpoint that can recover from one transient post-startup schema-check failure without masking a real startup failure.

- [ ] **Step 1: Write RED test**

Add `test_readiness_recovers_after_transient_schema_check_failure` to `tests/test_admin.py`. Build a servable gateway with `build_gateway_state(...)`, patch `sabiroute.api.health.check_schema` to raise once on the first readiness call, then return normally. Assert first `GET /health/ready` is 503 and second is 200 with `body["components"]["key_store"] == "ok"`.

- [ ] **Step 2: Run focused test**
```bash
./.venv/bin/python -m pytest tests/test_admin.py::test_readiness_recovers_after_transient_schema_check_failure -q
```
Expected: FAIL because the first check permanently sets `startup_error` and nulls stores.

- [ ] **Step 3: Implement minimal fix**

In `readiness`, make the post-startup schema-check failure response-local only: do not set `gateway.startup_error`; do not null `key_store` or `chat_store`; set a local `schema_ok = False` and include the affected component in this response's failing list. Preserve fail-closed behavior when `gateway.startup_error` was set at startup.

- [ ] **Step 4: Run focused and readiness suites**
```bash
./.venv/bin/python -m pytest tests/test_admin.py -q
```
Expected: PASS with no stale sticky-readiness behavior.

- [ ] **Step 5: Independent review**

Review specifically for masked schema failures, mutation of shared state, and secret leakage in the failure response.

- [ ] **Step 6: Commit**
```bash
git add tests/test_admin.py src/sabiroute/api/health.py
git commit -m "fix(health): recover from transient readiness check failure" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: S6-F5 lineage reconciliation rowcount

**Files:**
- Test: `tests/test_accounting_lineage.py`
- Test: `tests/test_admin_lineage_http.py`
- Modify only if RED proves the defect: `src/sabiroute/security/store.py:695-700`

**Interfaces:**
- Consumes: `reconcile_lineage_budgets(connection: Any, lineage_id: str, keep_key_id: str, approver: str) -> None`.
- Produces: `ValueError` when the lineage row to update does not exist, mapped by the existing admin handler to a typed 409 response.

- [ ] **Step 1: Write RED direct-store test**

Add `test_reconcile_missing_lineage_row_fails` to `tests/test_accounting_lineage.py`. Create a key/budget, delete the lineage row, then call `reconcile_lineage_budgets(...)` inside `pytest.raises(ValueError, match="not found")`.

- [ ] **Step 2: Write RED HTTP test**

Add a test in `tests/test_admin_lineage_http.py` that calls the existing reconcile endpoint for a missing lineage and asserts HTTP 409 with a stable error code and no credential text.

- [ ] **Step 3: Run focused tests**
```bash
./.venv/bin/python -m pytest tests/test_accounting_lineage.py tests/test_admin_lineage_http.py -q
```
Expected: FAIL because `connection.execute(update(...))` currently ignores rowcount.

- [ ] **Step 4: Implement minimal fix**

In `reconcile_lineage_budgets`, capture the `CursorResult` from the update and raise `ValueError("Lineage ... not found for reconciliation.")` when `rowcount == 0`. Do not change budget validation or lineage semantics.

- [ ] **Step 5: Run focused suites**
```bash
./.venv/bin/python -m pytest tests/test_accounting_lineage.py tests/test_admin_lineage_http.py -q
```
Expected: PASS.

- [ ] **Step 6: Independent review**

Review for accidental data deletion, changed approval semantics, and secret text in HTTP responses.

- [ ] **Step 7: Commit**
```bash
git add tests/test_accounting_lineage.py tests/test_admin_lineage_http.py src/sabiroute/security/store.py
git commit -m "fix(lineage): fail reconciliation on missing row" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: S6-F6 redaction boundary tests

**Files:**
- Test: `tests/test_r3_secret_leakage.py`

**Interfaces:**
- Consumes: `redact_secrets(value: object) -> str` from `src/sabiroute/security/redaction.py`.
- Produces: tests only; no redaction policy change.

- [ ] **Step 1: Add residual-boundary tests**

Add parametrized tests pinning documented behavior:
- known carriers are masked: URI userinfo password, Bearer token, `sr_live_`/`sr_test_`, `sk-...`;
- a bare password in prose is not claimed masked;
- an unencoded `@` inside a password is a documented residual boundary.

- [ ] **Step 2: Run focused tests**
```bash
./.venv/bin/python -m pytest tests/test_r3_secret_leakage.py -q
```
Expected: PASS. If a known carrier is not masked, fix the implementation before proceeding; this is a RED-proven defect, not a documentation choice.

- [ ] **Step 3: Verify no overclaim**
```bash
rg -n 'all secrets|zero leak|guarantee' tests/test_r3_secret_leakage.py
```
Expected: no claim of total elimination.

- [ ] **Step 4: Commit**
```bash
git add tests/test_r3_secret_leakage.py
git commit -m "test(security): pin redaction residual boundaries" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: S16 admin executor boundary tests

**Files:**
- Test: `tests/test_admin_executor.py`
- Modify only if RED proves the defect: `src/sabiroute/api/admin.py:104-388`

**Interfaces:**
- Consumes: `BoundedStoreExecutor.run(...)` and admin endpoints under test in `tests/test_admin_executor.py`.
- Produces: stable typed 503 `key_store_unavailable` on executor faults, no credential/exception text in response, and no executor slot leak on cancellation.

- [ ] **Step 1: Write RED store-failure test**

Add `test_admin_store_fault_returns_typed_503_without_secret_text`. Patch the executor `run` to raise `RuntimeError("postgresql://user:secret@host/db")`. Call the relevant admin key endpoint and assert 503, stable code `key_store_unavailable`, and that `secret` is absent from body.

- [ ] **Step 2: Write RED cancellation test**

Add `test_admin_cancelled_request_does_not_leak_executor_slot`. Queue a blocking store call, cancel the request, then assert `in_use_count` returns to its pre-request value.

- [ ] **Step 3: Run focused tests**
```bash
./.venv/bin/python -m pytest tests/test_admin_executor.py -q
```
Expected: FAIL where faults escape or slots leak; PASS already-covered behavior.

- [ ] **Step 4: Implement minimal fix only for observed RED failures**

In the affected admin endpoint(s), catch executor/store faults and return typed 503 through the existing error helper without interpolating exception text. Ensure cancellation releases the executor slot in a `finally` path. Do not change key lifecycle semantics.

- [ ] **Step 5: Run focused suite and independent review**
```bash
./.venv/bin/python -m pytest tests/test_admin_executor.py -q
```
Review specifically for secret text, changed admin semantics, and slot accounting.

- [ ] **Step 6: Commit**
```bash
git add tests/test_admin_executor.py src/sabiroute/api/admin.py
git commit -m "fix(admin): harden executor fault and cancellation handling" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Final verification and honest gate report

**Files:**
- None. Review-only task; commit only if review requires a fix.

**Interfaces:**
- Consumes: all tasks above.
- Produces: final verification output, whole-branch review result, and external-gate report.

- [ ] **Step 1: Run full gates**
```bash
./.venv/bin/python -m pytest -q
uv run ruff check src tests scripts config
uv run mypy src
git diff --check
shasum -c REPORTS-MANIFEST.sha256
```
Expected: zero failures, no lint/type errors, clean diff, manifest OK. Record exact counts.

- [ ] **Step 2: Verify no prohibited path or gate change**
```bash
git diff --name-only
```
Expected: only files listed in Tasks 1–7. No protected paths, placeholders, live-provider matrix, CI, D3, rollout, registration ledger, or `training_authorized` change.

- [ ] **Step 3: Independent whole-branch review**

Use a fresh reviewer on the complete diff. Require explicit findings or no findings; do not accept “looks good” without evidence.

- [ ] **Step 4: Apply review fixes with individual test cycles**

If findings exist, write or update a failing test for each behavior finding before fixing. Stage and commit only the files each fix touches.

- [ ] **Step 5: Report**

Report ACTION COMPLETED / WHY / RESULT / ARCHITECTURAL POSITION / ROADMAP POSITION / DEPENDENCY IMPACT / NEXT STEP / DO NOT TOUCH YET / CURRENT PROJECT STATUS. State plainly that S1–S18 as a whole remains open where owner/external gates remain closed.
