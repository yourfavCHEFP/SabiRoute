# S1–S18 local gap closure — short design

**Date:** 2026-11-18
**Status:** APPROVED 2026-11-18
**Execution plan:** `docs/superpowers/plans/2026-11-18-s1-s18-local-gap-closure.md`
**Scope:** every locally fixable gap found in the S1–S18 scout; no owner or external gate is opened.

## Intent

S1–S18 is not complete. The repository already contains substantial verified implementation, but several acceptance records, documents, and small test/hardening gaps remain. Close those local gaps without converting configuration, local tests, or historical evidence into false completion claims.

## Goals

1. Record the current-HEAD evidence crosswalk and baseline at `sec/deps-nov` / `4294eb70`.
2. Correct stale documentation that contradicts current code or gate records.
3. Compile the CD1–CD6 and competitive-evidence reports that are already supported by existing artifacts.
4. Add bounded tests for the identified S6 and S16 residuals; change production code only where a RED test proves a defect.
5. Re-run the full local gate set and commit only explicitly assigned files.

## Non-goals

- No live provider call, credential read, spend authorization, or provider matrix completion.
- No managed PostgreSQL/TLS, managed backup/restore, hosted GitHub Actions, staging, or production deployment.
- No D3 workflow installation, R6.6 mutation execution, R6.7 rollout, registration ledger, or `training_authorized` change.
- No ML training, selector implementation, or filling zero-byte placeholders.
- No modification of protected paths or pre-existing untracked files.
- No claim that S1–S18 as a whole becomes DONE.

## Constraints

- Repository protocol evidence labels remain mandatory.
- Current branch is `sec/deps-nov`, HEAD `4294eb70`; no push, merge, rebase, reset, or history rewrite.
- Use `uv` and `./.venv/bin/python`; never hand-edit `uv.lock`.
- Behavior changes use TDD RED → GREEN → REFACTOR.
- Fresh local baseline for this design: `844 passed, 10 skipped`; Ruff clean; mypy clean over 61 files; report manifest `13 OK`; `git diff --check` clean.

## Evidence base

All executioners returned before implementation. `[VERIFIED BY RUNTIME]` at exact HEAD `4294eb70`: the five local gates above are green. `[VERIFIED BY INSPECTION]`: the deterministic request path is wired from FastAPI ingress through auth/admission, deterministic classification, capability and passive-health filters, routing, bounded fallback, the LiteLLM client boundary, response normalization, and durable telemetry. Live-provider matrix, live failure/budget/rate-limit paths, managed operations, hosted CI, staging, and ML routing are outside the proven scope. A separate register records 19 owner gates with no status upgraded; all remain closed.

Implementation sequencing from the closure map: create the S1 crosswalk first, then establish the S2 baseline before any test or behavior edits. S6-F3 readiness recovery and S16 admin-executor fixes are high-risk and require RED proof plus review; F5 is a bounded rowcount assertion; F6 is tests-only.

## Approaches considered

1. **Evidence-first local closure (chosen).** Close all locally provable docs/evidence gaps and bounded test/hardening gaps, then verify and commit. Cost: more review work; benefit: maximum honest progress tonight without opening external gates.
2. **Ledger only.** Produce the crosswalk and gate register, change no tests or behavior. Cost: leaves known local defects open.
3. **Gate requests first.** Request all owner/external authorizations. Cost: requires credentials, spend, managed infrastructure, and deployment authority; cannot be completed in this session.

## Design

### Tranche A — evidence and documentation

- Add a current-HEAD S1–S18 acceptance crosswalk under `artifacts/sprint-phoenix-2/`, citing each sprint criterion, current evidence, and remaining gate.
- Add an S2 baseline addendum recording branch, HEAD, worktree state, fresh gate outputs, and skip reasons.
- Extend the provider documentation with an explicit column/note for contract dimensions not tested offline: provider-reported usage, tool calls, context limits, auth translation, and live response shape. Do not change R2 status.
- Correct `docs/failure-injection-runbook.md` to name the actual completion path and passive health module; do not create or reference nonexistent `FallbackEngine` or `providers/healthcheck.py`.
- Correct `README.md` runtime-enforcement wording so it reflects the implemented quota gate and its tests.
- Add the CD1–CD6 final report from the existing discovery packet; mark Sprint 9 formal acceptance still owner/T8 gated.
- Correct the Phase 13.1 line to state that the snapshot/audit work is committed as `71271fc`; leave integrity, readiness, and training verdicts unchanged.
- Add a narrow incident-response runbook and link it from deployment documentation, explicitly labelled local-only and not production verification.
- Add an evidence-cited competitive matrix draft with no competitor-performance claim; keep the OmniRoute benchmark gated.

### Tranche B — bounded tests and hardening

- S6 F3: add a RED test for bounded readiness recovery after a transient schema-check failure following successful startup. Any production change must preserve fail-closed startup and must not mask a real schema failure.
- S6 F5: add a RED test proving lineage reconciliation detects zero-row updates; add the minimal rowcount assertion only after RED.
- S6 F6: add tests pinning the documented residual boundaries of pattern-based redaction. Do not claim total secret elimination and do not change redaction policy without a failing test.
- S16: add admin executor store-failure `503` and cancellation tests. Change production code only if a test exposes a defect.
- Each behavior change receives independent code review before verification.

### Verification and closure

Run full pytest, Ruff, mypy, `git diff --check`, report manifest verification, and an independent review of the complete diff. Inspect the complete staged diff. Stage only explicitly assigned files. Commit locally; do not push.

## Residual gates

Live providers and credentials, managed PG/TLS, managed backup/restore, hosted CI, staging, production deployment, `.github/**`, D3 installation, R6.6 mutation execution, R6.7 rollout, registration ledger, `training_authorized`, dashboard UI, full provider matrix, and S13–S15 ML gates remain open. They are reported, not closed.

## Builder discretion

Choose exact artifact filenames to match neighboring conventions. Keep all new claims labelled to their evidence and keep every gated item in the open-gate register. No behavior beyond the tests named above.
