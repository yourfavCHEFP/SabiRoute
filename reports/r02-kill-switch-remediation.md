# R-02 Emergency Kill-Switch — Mission Report

## 1. Authorization and scope

Owner-authorized: (a) read-only 16B verification, (b) narrow ignore-rule
review, (c) R-02 implementation with tests. NOT authorized: 16B commit,
other remediation, commit/push/deploy, paid resources, live inference,
production access, Sprint 6. No security skill was available in this
environment (`security-guidance` probe: unknown skill); review is manual
against the actual code. Nothing below claims a scanner ran.

## 2. Baseline

`/Users/airm2/My ML Hub/SabiRoute`, `feat/sabiroute-routing-foundation` @
`c50a349b723633fa933e49eb2ff4619f57a198ab`, upstream in sync (0/0), nothing
staged. 11 tracked files modified + untracked additions, all preserved;
`git diff --check` clean throughout. HEAD matches the expected SHA —
proceeded.

## 3. Sprint 16B verification (read-only; files byte-unchanged by R-02)

Paths: `src/sabiroute/api/admin.py` (tracked diff, +35/−15) and untracked
`tests/test_admin_executor.py` (5 tests). `store_executor.py` and
`tests/test_store_executor.py` are committed at HEAD (verified via
`git ls-files` + `git show --stat HEAD`: 438 insertions, 5 files, pushed).

- Isolation: every hunk wraps a sync store call in
  `store_executor.run(...)` across create/rotate/revoke/rate-limit
  (get/set/clear)/usage/budget (get/set/clear). Zero R-02 traces in the
  file (verified by grep). No routing, provider, fallback, health, or
  authorization change (router-level `require_admin_key` untouched).
  The diff additionally carries one Sprint 2 line (`usage_source` in the
  usage-items payload) — see commit recommendation.
- Tests run: `test_admin_executor.py` 5 passed exit 0 (HTTP-level round
  trips: key lifecycle, rate-limit, budget, usage listing, cross-context
  executor); `test_admin.py` + `test_security.py` 14 passed exit 0.
- Coverage: success paths + cross-context use. Missing: admin-level store-
  failure (503) and cancellation paths (executor-level cancellation is
  unit-tested; admin 404 semantics unchanged and still tested).
- Risks: none introduced; same executor semantics as committed 16A.

**16B VERIFIED — OWNER COMMIT DECISION REQUIRED** (never committed here).
Commit recommendation: `admin.py` as one commit with a message covering
both the 16B executor migration and the Sprint 2 `usage_source` exposure
(they share the file; splitting via `add -p` is possible but fiddly), or
two picked hunks if the owner prefers. `tests/test_admin_executor.py` rides
with it. Do not amend HEAD or the Sprint 1–5 file set in the same commit.

## 4. Report durability / ignore-rule review

`git check-ignore -v`: all five planning reports were ignored by
`.gitignore:20` (`reports/`). Sensitivity scan of `reports/` (key formats,
bearer/token/password/credential patterns): zero hits; the only absolute
paths are 3 occurrences of the repo checkout path. Excluded deliberately:
`brag-output/`, `artifacts/`, screenshots, drill configs (working material,
possible local paths), `provider_verification.json` (state unchanged:
still ignored+untracked, as before).

Change made (narrow, reversible, unstaged, uncommitted): `reports/` →
`reports/*` plus `!` exceptions for exactly the five planning reports
(`audit-acceptance-and-disposition.md`, `remediation-roadmap-and-gates.md`,
`pre-roadmap-audit.md`, `implementation_12h.md`, `my_scorecard.md`).
Verified: the five appear as individual untracked candidates, nothing
staged, tracked files unaffected. Caveat recorded in the rule comment:
scrub checkout-local paths before any future push (no push authorized or
performed here).

## 5. Architecture trace and state authority

Request path re-traced in code: Free Chat marker → Free Pool gate (policy
→ allowlist → capability/health → budget) → attempt loop → LiteLLM.
SabiChat forces the marker server-side; direct clients may set it, which
*opts into* shared-inference policy — so marker-present is exactly the
shared-inference class (no BYOK mechanism exists to confuse it with).
Admin boundary (`require_admin_key`, separate env secret) and response
conventions (`{"error": {...}}` + typed reasons) reused as-is.

State authority chosen: **database-backed control record, read-through on
every admission and every attempt, no cache anywhere.** Rationale: env-only
cannot satisfy no-redeploy disable (invariant 4); in-memory cannot satisfy
restart-must-not-re-enable (invariant 5) or multi-instance propagation;
the existing ledger gives ordering/idempotence for free. Propagation bound:
disable lands no later than the next admission/attempt read on every
instance sharing the database; in-flight attempts finish (invariant 9,
documented in code and report).

## 6. Design decisions

- Deny with 403 `shared_inference_disabled` (policy refusal, not server
  error), checked before the rollout-policy gate so incident messaging is
  singular; the switch never grants allowlist/policy/budget/attribution
  outcomes (invariant 11/12: allowlist evaluation still runs when enabled).
- Fail-closed on: absent record, NULL/non-boolean value, store None,
  executor missing, any read exception, startup without a readable store.
- Per-attempt re-check (not just admission) so mid-flight disable stops
  fallback; loop exit finalizes usage/budget through the existing
  `finish()` path with real token/cost totals.
- Admin: separate `api/shutdown.py` router (protects 16B committability),
  same auth dependency and error shapes; `StrictBool` + 280-char reason;
  status exposes only enabled/configured/updated_at/updated_by; audit via
  structured log line (actor "admin" — the shared secret carries no
  identity — action, reason length, outcome).
- Unmarked (developer/BYOK-shaped) traffic never consults the switch.

## 7. Files changed and purpose

- `security/store.py`: `sabiroute_shared_inference_policy` table,
  revision `0003-shared-inference-switch`, `get/set/status` methods.
- `security/keys.py`: the three methods added to the `ApiKeyStore`
  Protocol (mypy-required; both implementations conform).
- `freepool/eligibility.py` + `__init__.py`: `SHARED_INFERENCE_DISABLED`
  reason + `shared_inference_denial()` read-through helper, exported.
- `api/completions.py`: admission check (first inside the Free Chat gate)
  + per-attempt re-check with `finish()` reconciliation.
- `api/shutdown.py` (new): admin GET/PUT, no 16B contact.
- `api/main.py`: mount shutdown router. (Name `main.py` here means
  `src/sabiroute/main.py`.)
- `tests/conftest.py`: double gains policy state + `fail_policy_reads`
  + `enable_shared_inference()` harness helper (mirrors operator action).
- `tests/test_shared_inference.py` (new, ~20 tests).
- Existing fixtures in `test_freepool_eligibility.py`,
  `test_usage_source.py`, `test_sabichat.py` now enable the switch
  explicitly (the new fail-closed default otherwise denies them — intended
  semantic change, documented).
- Revision-list assertions updated to `[0001, 0002, 0003]`.
- `.gitignore`: narrow report-tracking adjustment ( §4).

16B files (`admin.py`, `test_admin_executor.py`): untouched by R-02
implementation (verified by grep: zero R-02 traces).

## 8. Migration details

Additive-only: new table via `create_all` on fresh DBs; existing DBs gain
it the same way (no column migration needed — new tables need none);
revision recorded in order by the existing ledger runner; re-runs no-op.
Rollback: ignore the table (no rows elsewhere depend on it). Downgrade
beyond ignoring is out of scope by design. No production access performed.

## 9. Test commands, exit codes, results

- `pytest tests/test_shared_inference.py` → 17 passed, 1 PG-opt-in skipped,
  exit 0. With disposable PostgreSQL 16.15 (loopback, temp creds, removed
  after): 18 passed, exit 0 (round-trip, audit metadata, NULL fail-closed).
- `pytest -q` (full) → **325 passed, 5 skipped** (4 Redis-gated + 1 PG
  opt-in), exit 0.
- `ruff check src tests scripts config` → clean, exit 0 (3 auto-fixed
  import-sort + 2 manual E501 + 1 F401 + Protocol/mypy fixes found and
  repaired mid-mission, not hidden).
- `mypy src` → 0 issues across 45 files. `git diff --check` → clean.
  `node --check web/app.js` → pass (frontend untouched).
- Mid-mission regression honestly caught and repaired: the fail-closed
  default denied 15 pre-existing Free Chat tests; harnesses now enable the
  switch explicitly via `enable_shared_inference()`.

## 10. Failure/authorization/concurrency/propagation evidence

- Disabled/absent/NULL/unreadable → 403 before dispatch, 0 stub calls,
  `failure_category=shared_inference_disabled`, source stays `unknown`.
- Enabled + eligible → 200 with `free_pool` attribution preserved.
- Mid-flight disable (deterministic router-hook test) stops fallback:
  403, secondary never attempted.
- Read-through proven: enable→allow→disable→deny sequence green; no cache
  exists in code (single read path, verified by inspection).
- Admin: disable/enable round-trip, idempotent repeats, 401 without/wrong
  credential (incl. the 503-without-admin-secret fail-closed subtlety,
  asserted), 422 on non-bool, 503 without store, status shape
  secret-scanned.
- Multi-instance: by construction (shared DB, no cache), NOT TESTED —
  stated limitation. Single-process concurrency covered by existing
  executor semantics; no new threads/locks introduced.
- Identical-write convergence: PASS (`test_concurrent_identical_writes_converge`,
  10 threads, one row, correct value/metadata). Conflicting enable/disable
  writes and true concurrent admission/disable races: NOT PROVEN
  (last-writer-wins is code-inspected upsert semantics only; no test forces
  the interleaving).

## 11. Validation split

Unit: helper contract, mapping, validation (mocked). SQLite: full request
paths, SQL NULL, ledger 0003, idempotent reruns, threaded identical-write
convergence. PostgreSQL: policy round-trip/metadata/NULL + ledger on
disposable PG 16.15 (opt-in test). Multi-instance, conflicting-write, and
true-concurrency admission races: NOT TESTED (design arguments only).
Unknowns: managed PG/TLS, GH Actions run, full-stack compose-up.
Read-only review focused run: 34 passed, 1 skipped (PG opt-in), exit 0 —
recorded separately; the full suite remains 328 passed, 5 skipped as
previously reported (not re-run for this documentation edit).

## 12. Risks, limitations, unverified requirements

- In-flight requests finish after disable (documented, inherent).
- Single shared secret means audit actor is always "admin" (no per-operator
  identity exists anywhere in the system — pre-existing).
- Reason field is admin-supplied free text (length-capped, never secrets).
- No per-user quota interaction (R-01 explicitly out of scope).
- Reports now visible as untracked candidates; push-time path scrub still
  required (noted in rule comment).

## 13. Acceptance checklist

- Shared inference starts disabled without established state: PASS
  (absent/NULL/unreadable/store-less all deny; tested).
- Startup DB failure cannot enable: PASS — composed evidence: fail-closed
  helper unit tests, 503-before-any-gate behavior without a store
  (`test_missing_store_never_enables_shared_inference`,
  `test_admin_mutation_without_store_is_503`), and the existing
  degraded-startup path (startup exceptions yield `startup_error` with
  completions 503, covered by the readiness regression tests).
- Admin disable/enable without redeploy: PASS. Explicit re-enable, no
  restart flip: PARTIAL — persistence of the row is implemented and tested,
  but no test restarts the process to exercise the re-read; the re-read uses
  the identical read-through code path (code-inspected).
- Audit without secrets/content: PASS (metadata + log line, scanned).
- AuthN/Z gating: PASS (401s, 503s asserted).
- Gate before dispatch + no fallback bypass: PASS (0-call + mid-flight tests).
- No eligibility/budget/attribution override: PASS (existing suites green).
- BYOK/local unaffected: PASS (unmarked path test + no BYOK mechanism).
- Distinguishability ambiguity: NONE FOUND (marker defines the class).
- Migration safety: PASS (additive, ledger-ordered, idempotent).
- Admin/status secrets: PASS (shape + scan assertions).
- Stale-enabled window: BOUNDED (per-admission/per-attempt reads; no
  cache) — multi-instance propagation NOT TESTED: acknowledged limitation,
  not a failure.
- 16B untouched by R-02: PASS (grep-verified).

## 14. Repository state and next action

Branch `feat/sabiroute-routing-foundation` @ `c50a349`, upstream in sync.
Nothing staged, nothing committed, nothing pushed, nothing deployed.
`git diff --check` clean. R-02 files additive except `completions.py`
(admission + loop checks), `keys.py` (Protocol), `store.py` (table/ledger/
methods), `main.py` (mount), `conftest.py` (double), fixtures (explicit
enablement), revision assertions (0003).

Scorecard: no automatic increase. Recommended: Free Pool eligibility row
evidence gains "kill-switch enforced (fail-closed, per-attempt re-checks)"
at the same 60% (capability proven, but quotas/catalogue still gate it) —
owner to confirm; all other rows held.

Next action (owner approval required): review this report, decide the 16B
commit shape, then authorize R-01 quota design. No further implementation
without that approval.

## 15. Continuation pass (same tree, no behavior change to prior scope)

- Admin auth for both verbs: router-wide `require_admin_key` (shared
  bearer + env secret + constant-time compare) covers GET and PUT
  identically; DeadlineMiddleware wraps all routes uniformly with no auth
  interference. New tests: valid client credential rejected on both verbs
  (401 — independent secrets proven independent); audit log line asserted
  via caplog (action + actor present, reason text and key material absent).
- Actor accuracy: `updated_by` is always the literal `"admin"` — accurate
  because no per-operator identity exists in the system (shared secret);
  asserted in tests; documented as a limitation, not a defect.
- Concurrency: 10 parallel identical upserts converge to one row with
  correct value/metadata (sqlite, threads). Multi-instance propagation
  remains by-construction (shared DB, zero cache) and NOT TESTED — standing
  limitation, unchanged.
- BYOK/allowlist/default-off: re-verified green (unmarked + policy-off
  tests in the full run).
- Battery: new tests 20/21 file-local (1 PG opt-in skip); full suite **328
  passed, 5 skipped** (4 Redis + 1 PG opt-in), exit 0; ruff/mypy (45
  files)/diff-check/node all clean, exit 0.
- 16B re-verified untouched (zero R-02 traces, same +35/−15); `.gitignore`
  change stands uncommitted with nothing staged.
- Scorecard: no change (confirmation only; 60% Free Pool evidence note
  remains owner-to-confirm).
