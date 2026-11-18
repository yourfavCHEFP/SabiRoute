# My Scorecard — 12-Hour Product Integration Mission

Percentages are architectural estimates (acceptance criteria met), not coverage
or elapsed time. A percentage rises only when acceptance criteria are met.
"Prev est." is the previous *accepted* checkpoint score (Sprint 1 close:
Free Pool 40%, routing 72%, gateway 80%); deltas are measured from there.
Each capability has exactly one authoritative row — no duplicate or
intermediate entries. Evidence levels: code-inspected < unit-tested <
integration-tested < live-provider-tested.

| Workstream | Prev est. | New est. | Delta (pp) | Evidence | Remains | Level | Next milestone (cost) |
|---|---|---|---|---|---|---|---|
| Core gateway / LiteLLM execution | 80% | 80% | 0 | Re-verified this turn; suite 308 passed / 4 skipped; ruff/mypy/diff clean | Live failure-injection evidence (pre-existing gap) | Integration-tested | Failure-injection runbook (medium) |
| Routing reliability & governance | 72% | 72% | 0 | Unchanged this sprint; fallback-confinement test green in final run | Capability evidence for most deployments (pre-existing) | Integration-tested | Catalogue↔registry mapping endpoint (low) |
| Free Pool runtime eligibility | 60% | 70% | +10 | Quota enforcement closed this closeout: 50,000-token UTC-day admission boundary, 429 quota_exceeded with window-derived Retry-After, 503 fail-closed, single-reservation retries, spoof-resistant identity; PG 17 race (8 threads, 5/8 admitted, total within limit, observed in `/tmp/pgverify/server.log`); full suite 393 passed / 4 skipped (PG-enabled, reported; targeted quota/header tests directly observed) | Catalogue mapping data, live-provider proof | Integration-tested (stub; disposable PG 17) | Catalogue mapping endpoint (low) |
| SabiChat identity/backend | 0% | 75% | +75 | Prior 65% evidence stands; added quota-summary endpoint (10/10 tests: auth, spoof-resistance, fail-closed 503, midnight boundary), PG 17 migration/idempotence/isolation/restart-persistence proof, cross-account read/write probes denied 404; full suite 393 passed / 4 skipped (PG-enabled, reported; 389 passed / 8 skipped SQLite default, reported) | Per-user keys, Redis limits, live-provider proof, managed-PG validation, prod hardening | Integration-tested (stub; disposable PG 17) | Staging deploy + managed-PG test (high) |
| SabiChat frontend | 0% | 65% | +65 | Prior MVP evidence stands; added daily usage meter (loading/ready/unavailable/stale, progressbar + ARIA, reduced-motion), 429 exhaustion UX with exact draft restore, account-switch isolation fix proven in real Chrome (marker + draft gone at logout, zero residue for second account); 9/9 web tests; console clean | Automated browser suite, full mobile/a11y passes, reload persistence decision | Browser-smoke-tested (manual) + static tests | Staging deploy + live-PG test (high) |
| Production deployment & operations | 45% | 55% | +10 | Reconciled this turn: image + smoke + compose re-verified green, suite 308 passed; local PG 16 gate stands (19/19) | GH Actions run, managed-PG + backup test, compose-up E2E, image slimming | Integration-tested (local PG 16 + container) | Managed-PG validation (high) |
| End-to-end verified product path | 25% | 40% | +15 | Real browser drove register→chat→reply→sign-out on stub backend (manual smoke); API-level attribution proven in tests | Automated browser E2E, live provider, staging smoke test | Browser-smoke-tested (manual, stub) | Sprint 5 staging smoke test (high) |

Sprint 4 checkpoint: frontend MVP COMPLETE (re-verified). 7/7 static tests,
31/31 UI tests, final suite 299 passed / 4 skipped (env-gated Redis);
ruff/mypy/`git diff --check` clean; `node --check` passes. Second browser
session confirmed: per-conversation isolation both directions (server-DB
cross-checked), single-render + pending-clear, double-submit guard probe,
revocation → expiry UI, empty web storage, zero console errors. Deltas held:
frontend 0% → 50% (+50), end-to-end 25% → 40% (+15); all other rows held.
Risks: none introduced; no automated browser suite, no mobile/a11y passes,
live-PostgreSQL and live-provider paths unproven. No commit created.

Sprint 5 checkpoint: deployment foundation COMPLETE (not production).
Image builds + smokes green (non-root, healthy, /app served); CI valid;
compose defined + config-valid; docs match; suite 308 passed. Delta:
deployment 10% → 45% (+35), scored on built + locally verified artifacts,
not config alone. Risks: GH Actions never ran here; managed-PG migration and backup/restore
untested (local disposable PG 16 gate passed: 19/19); full-stack compose up
not run; 2.71 GB image. No commit created. Next: managed-PG validation +
staging deploy (high cost).

SabiChat acceptance closeout (2026-10-16, branch
feat/sabiroute-routing-foundation @ c7756c7, no commit created).
Account-isolation fix (`web/app.js` showAuth teardown) proven in real Chrome:
marker + draft + banner gone at logout, zero residue for the second account
(DOM snapshots observed in `.playwright-cli/`); backend read/write probes denied 404.
Quota enforcement proven on the 50,000-token UTC-day boundary with
window-derived `Retry-After` on 429 and fail-closed 503; meter, exhaustion UX
(exact draft restore), and summary endpoint (10/10) verified in-browser and in
tests. Disposable local PostgreSQL 17.10 gate (server log observed at
`/tmp/pgverify/server.log`): fresh migration (0001–0004), idempotent re-run,
user/window isolation, 8-thread race admitting exactly 5/8 within limit (savepoint +
`SELECT ... FOR UPDATE`), restart persistence, fail-closed store failure.
Full suite with PG enabled (reported): 393 passed / 4 skipped (Redis-gated
only; 389 passed / 8 skipped SQLite-only default, reported). Deltas: Free Pool
60% → 70% (+10), SabiChat identity 0% → 75% (+75), frontend 0% → 65% (+65), all
measured from the Sprint 1 accepted baseline per this file's convention.
Risks remaining: managed-PG/TLS + backup/restore, GH Actions run,
automated browser suite, live-provider proof.
SabiChat Retry-After forwarding CLOSED 2026-10-16: `SabiChatService.complete`
now returns gateway headers and the message endpoint propagates the
standard HTTP `Retry-After` header (window-derived positive integer seconds
until 00:00:00 UTC) on `429 quota_exceeded` only (never invented;
`503 quota_unavailable` carries no `Retry-After` header across
`/v1/chat/completions`, `/v1/conversations/{id}/messages`, and
`/v1/chat/quota-summary`). Directly observed via
`test_exhaustion_retry_after_matches_reset`,
`test_quota_unavailable_carries_no_retry_after`, and
`test_chat_exhaustion_forwards_retry_after` (`3 passed`) plus live `TestClient`
429/503 header inspection confirming standard `Retry-After` header emission
(note: the earlier `gw-Retry-After=56982` / `sabi-Retry-After=56982` notation
was a probe stdout prefix for the standard `Retry-After` header, not a custom
header name); full-suite aggregate count is 393 passed / 4 skipped (PG17,
reported).
No pilot activation, no quota/billing changes, no production-readiness claim.

Mobilization reconciliation (2026-10-26, Africa/Lagos): suite re-run 425 passed / 7 skipped (env-gated Redis 4 + PG 3); ruff/mypy/diff clean; BYOK-0 8/8; schema validators 12/12; migration-path 74/74. Git diverged (ahead 2, behind 3) — reported, not reconciled. Phase 2/3 and BYOK-0 owner gates unchanged. Full detail: reports/mobilization-reconciliation-2026-10-26.md.
---

## R1–R8 Integration Lane — 2026-10-29 (branch `feat/sabiroute-routing-foundation` @ `b360ffc`)

Evidence levels: code-inspected < unit-tested < integration-tested <
live-provider-tested. Only fresh (this-lane) evidence advances a row; all
other figures are cited historical reports, not re-runs.

| Workstream | Prev (2026-10-26) | Now | Delta | Fresh evidence (this lane) | Level | Blocker |
|---|---|---|---|---|---|---|
| B0 manifest/provenance (R1) | 425/7 + hash OK | manifest re-verified 13/13, `git diff --check` clean | 0 | `shasum -c REPORTS-MANIFEST.sha256` 13/13 OK, exit 0 (fresh) | Historical + fresh hash check | A0/S2: ADR tracked by the R1/R4 reconciliation commit on `sec/deps-nov` (landing with this change — canonical status effective on commit, not by text edit); per-report authorship beyond filenames unresolved |
| Provider compatibility (R2) | contracts offline | unchanged | 0 | `test_provider_harness.py` 6/6 fresh; 14 aliases mapped to `litellm_params.model`, 19 model YAMLs (inspected) | Unit-tested (mocked) | Live matrix: 0 live calls (unauthorized); 1 historical 0/1 AUTH_FAIL (2026-10-10); gate recorded in `artifacts/sprint-phoenix-2/R2-LIVE-PROVIDER-MATRIX-GATE.md` |
| Core security/DB safety (R3/B1/B3) | BYOK-0 9/9 (fresh subset) | **R3 VERIFIED COMPLETE 2026-11-01** (Terminal D) — one security defect found and fixed; full R3 package proven | +1 defect fix; +30 tests | R3 package (`test_r3_byok_boundary`, `test_r3_db_isolation`, `test_r3_secret_leakage`, `test_r3_real_service_controls`, `test_r3_off_loop_boundary`) **129 passed / 0 failed / 0 skipped** against real disposable PostgreSQL 17.10 + Redis 6399, 3 consecutive runs, post-run residue 0 PG rows / 0 Redis keys; with services unset 127 passed / 2 skipped (opt-in skips named, never silent). **Defect fixed:** a credential-store fault during authentication escaped as an unhandled 500 (measured before/after) — an ASGI traceback would publish the DSN; now typed 503 `authentication_unavailable`, no canary in body or logs, zero provider calls. **Off-loop boundary** (`BoundedStoreExecutor`) proven on the completion path by thread identity plus responsiveness, both mutation-verified RED with the boundary replaced by an on-loop executor; the threaded file ran 20/20 green over 20 consecutive runs. Steady state: BYOK-0 13/13 (spellings, nesting, message-nested, depth, streaming, budgeted, retry/fallback); leakage 22/22; isolation 20/20; real-service controls 27/27. Full suite 665 passed with services / 656 passed + 9 skipped without; `ruff` clean; `mypy src` clean (49 files); `git diff --check` clean. Current BYOK guard placement is `completions.py:337-345` (this row previously cited `:256`) | Integration-tested (real disposable PG/Redis, loopback plaintext; mutation-verified) | No R3 blocker. Explicitly NOT proven: managed PostgreSQL, TLS/off-host transport, multi-instance Redis, live-provider behaviour (0 live calls made), browser/web-surface security. Deferred hardening: `append_pre_routing_feature_snapshot` remains `request_id`-scoped (server-generated `uuid4`, never client-settable) |
| F-27 lineage (R4) | 14 lineage tests (historical) | 14/14 fresh + 3-state defect pinned + 4 isolated PG/Redis probes | +defect pin | `test_accounting_lineage.py` 14 passed fresh; new `test_lineage_compat_state.py` 2 passed + 1 xfail (legacy-rotation defect pin); isolated Redis 6399: shared-bucket PASS + cutover semantics DOCUMENTED; isolated PG 55439: crash-no-fabricate DOCUMENTED + reconcile-idempotent DOCUMENTED | Integration-tested (isolated disposable PG/Redis; SQLite) | None for F-27 — D8 formally closed/complete 2026-10-31 (ADR D8; § F-27 formal closure); D6/A6 integrated acceptance closed by owner green R8-G1 (2026-11-18, stable SHA `1d91f73`). Non-blocking residuals: Q2 archival policy, Q3 TTL soak, dangling-lineage auth-denial telemetry |
| Reliability (R5) | scoped PASS (historical) | offline suites re-greened fresh | 0 | fallback+recovery+schema 37/37; request-limits+deployment 39+1 skip; BYOK-0 included above — all fresh, isolated | Unit-tested | Live failure-injection (env-gated); scoped R15 manifest reconstructed in `artifacts/sprint-phoenix-2/R5-SCOPED-R15-MANIFEST.md` with 75/75 focused offline tests verified |
| Compression discovery (R6) | not started | R6.1–R6.5 pipeline implemented in `src/sabiroute/request_transform/`; R6.6 L1/L2 controlled replay PASS, mutation matrix OPEN | +pipeline + I9 guard; +R6.6 replay | `68bde1f` (14 files: I1–I9 contracts, R6.4 compression, R6.5 capabilities, R6.1–R6.5 tests), `4080bf5` (I9 call-site guard wired into `api/completions.py` + `gateway.py`); `ac859fd` (R6.1 owner decisions); `artifacts/sprint-phoenix-2/R6.6-R7D2-EXECUTION-RECORD.md` (839 passed / 10 skipped, ruff/mypy clean over 61 files, manifest 13/13 at replay). R6.0 document-level closure: `d115073` | Implementation + unit tests + controlled replay (not mutation-validated) | R6.6 I1–I9 source-mutation matrix OPEN; R6.7 staged rollout not executed; Track A / T8 / Sprint 9 authorisation not re-verified here |
| Operations/recovery (R7) | partial | Redis outage branches proven covered; D2 local disposable-PG backup/restore check PASS; D1 E1–E8 local controlled replay PASS | +D2 local check +D1 replay + capability wiring fix | `test_redis_outage_denies_closed_with_contract` + `test_missing_limiter...` inspected (503 `rate_limiter_unavailable`); rollout/rollback docs reconciled; `artifacts/sprint-phoenix-2/R6.6-R7D2-EXECUTION-RECORD.md` §2 — sentinel recovered via local `pg_dump`/`pg_restore`, disposable DB and backup removed (`D2_CHECK_OK`, `D2_CLEANUP_OK`); `artifacts/sprint-phoenix-2/R7-D1-D2-CONTROLLED-REPLAY-RECORD.md` + 2026-11-18 addendum — E1–E8 local controlled replay PASS with pinned corpus SHA-256, canonical provider-bound payload capture for E3–E6 (test-side, not HTTP wire bytes), cancellation inside transform at E7, and E8 process startup | Unit-tested + local disposable-PG check + controlled replay | Managed-PG/TLS, managed backup/restore, compose E2E, hosted GH run, staging; D3 tracked but inert under `artifacts/` and not installed in `.github/workflows/`; R6.6 mutation matrix still open |
| A6 integrated acceptance (R8) | BLOCKED | **DONE — OWNER GREEN R8-G1 (2026-11-18)** at stable SHA `1d91f73`; fresh T1/T8 re-review PASS in `artifacts/sprint-phoenix-2/T1-T8-REREVIEW-RECORD.md`. Six legacy badges remain `UNTRACEABLE / WITHDRAWN` under R8-W1. | +R8 closed | Full suite fresh @ HEAD `524a017` + 141-file dirty tree: **656 passed / 0 failed / 9 skipped** (services unset) and **665 passed / 0 failed / 0 skipped** against disposable PostgreSQL 17.10 (port 55440, db `r8_acceptance_test`) + Redis 8.10.2 (port 6421); post-run residue 0 Redis keys, both instances torn down, default 5432/6379 never touched. The two recorded failures (`/app/` 404 + `/docs` 404) **no longer reproduce**: `main.py` now mounts `/app` (:173) and keeps docs **fail-closed** behind `SABIROUTE_DOCS_ENABLED` (:134–148) — the `/docs` 404 was F-04 intended policy, so this is test/impl realignment, not an F-04 policy change; covered by `test_mount_does_not_shadow_api` (`/app/` 200, `/docs` 404 default / 200 when enabled); `test_sabichat_web.py` **9 passed**. Static gates: `ruff` clean, `mypy src` clean (49 files), `git diff --check` clean. Tree byte-identical before/after (141 dirty / 0 staged) | Integration-tested + independently re-reviewed | None — owner green recorded in R8-G1 |

Full-suite manifest note: 504 collect (31 HEAD-tracked + 6 untracked test
files); HEAD-tracked = 30 files + `conftest.py`. The "18-file" D6 token is
the agreed baseline package, not the current file count — full-suite sign-off
remains conditional on the criterion matrix. No push, no deployment, no
shared/production-DB mutation in this lane. Isolated infra (Redis 6399,
PG 55439) torn down after probes; default 6379/5432 untouched.

---

## F-27 formal closure — 2026-10-31 (branch `feat/sabiroute-routing-foundation` @ `b360ffc`)

**Status: F-27 — CLOSED / COMPLETE.** Owner-approved closure, independently
re-verified by Terminal D. No production-code change, no test rewrite, no
commit, no push, no deployment, no percentage moved.

Candidate identity. The working tree is uncommitted, so closure is pinned to
content, not to a revision:

```
branch                = feat/sabiroute-routing-foundation
head                  = b360ffc9e804e19eaf99ec8e470a13a00c733ba5
tracked-delta sha256  = d5c24770d44ae35ccdf5c3a7c12a71837b72eee84cd224ff615b6695587d51c8
untracked-code sha256 = f7bb747ebfd3fad86036fddfe0e117de7231007e9a6989ac10a016e829961067
```

Verified this lane (fingerprints identical before and after the run):

- Focused F-27 suite: **31 passed, 0 failed, 0 skipped** across six files —
  `test_accounting_lineage` (14), `test_lineage_compat_state` (3),
  `test_lineage_admission_concurrency` (6), `test_lineage_redis_continuity` (1),
  `test_lineage_rollback_injection` (2), `test_admin_lineage_http` (5).
- `ruff check src tests scripts config`: clean.
- `mypy src`: "Success: no issues found in 48 source files".
- Candidate preservation: tracked-delta and untracked-code fingerprints
  unchanged across the verification run.
- Owner-review re-run (Terminal D, same candidate, same date): focused suite
  re-executed fresh — **31 passed, 0 failed, 0 skipped, no xfail/xpass**. The
  Redis continuity proof genuinely executed rather than skipping (`redis-server`
  binary present; the test asserts it never binds 6379), so criterion 5 rests on
  runtime evidence, not on a skip. `ruff` clean; `mypy` clean (48 files).
- Implementation, not just decision: `_ACCOUNTING_LINEAGES` (`security/store.py:97`),
  `create_lineage` (:612), `get_lineage` (:636), migration ledger row
  `0006-accounting-lineages` (:142) — confirming ADR D7 Option C is built.
- The previously-pinned legacy-rotation defect is now **fixed**: `test_lineage_compat_state.py`
  carries no `xfail` marker and `test_rotated_legacy_key_has_backing_lineage_row`
  passes, so the earlier row-89 note "2 passed + 1 xfail" is superseded (historical
  text in the R1–R8 lane left intact for audit).

Real-runtime proofs (not source inspection):

- **Redis continuity** — disposable `redis-server` 8.10.2 on an ephemeral
  loopback port, real `RedisTokenBucket`: Key A exhausts its burst; rotation
  yields Key B on the same lineage bucket; Key B is **not** admitted (no fresh
  allowance); a fresh-lineage control is admitted, proving the denial is
  exhaustion and not a broken limiter.
- **Rollback / failure injection** — deterministic seam: the lineage-table
  INSERT raises mid-transaction; no partial key or lineage row survives,
  pre-existing state is untouched, and an uninjected retry succeeds
  deterministically (both `create` and legacy `rotate` paths).
- **Concurrency** — barrier-synchronized 2- and 5-contender rotations yield
  exactly one winner, no split authority, zero partial key rows; in-flight
  rotation and attempt-1-rotate/attempt-2 retry keep one lineage bucket.

### Criterion reconciliation — F-27, 8 of 8 satisfied

| F-27 criterion | Evidence |
|---|---|
| Approve the exact reservation carry strategy | Owner approval (ADR D8); ADR D7 records Option C — dedicated `_ACCOUNTING_LINEAGES` |
| Preserve accounting history | `test_legacy_upgrade_preserves_data`, `test_rotation_preserves_lineage` |
| Preserve in-flight reservation semantics | `test_inflight_rotation_keeps_lineage_accounting_bucket`; lineage-aware reservation inserts |
| Preserve Redis rate-limit bucket lineage | `test_rotation_keeps_lineage_bucket_without_fresh_allowance` (real Redis) |
| Verify atomicity, idempotency, rollback and recovery | `test_lineage_rollback_injection` (2), `test_lineage_idempotent_creation`, `test_reconcile_idempotent` |
| Test concurrent and in-flight rotation | `test_concurrent_rotation_*` (2 and 5 contenders), `test_retry_attempt1_rotate_attempt2_same_lineage_bucket` |
| Prove rotation does not reset budget or rate-limit allowance | Redis no-fresh-allowance proof; `test_shared_lineage_single_rate_limit_authority`; `test_missing_lineage_never_falls_back_to_key_bucket` |
| Budget reconciliation authority — approve strategy, record operator (Q1) | Router-level `require_admin_key` (`api/admin.py:25`); handler passes the fixed role token `admin-role` to `reconcile_lineage_budgets(conn, lineage_id, key_id, "admin-role")`, which records it as the audit marker and never fabricates an operator (`security/store.py:645`); `test_reconcile_requires_approver`, `test_reconcile_lineage_missing_admin_secret_returns_401`, `test_reconcile_lineage_wrong_admin_secret_returns_401`, `test_reconcile_lineage_conflicting_budgets_returns_409`, `test_reconcile_lineage_success_records_audit_marker` |

### Explicit classification — not F-27 blockers

- **Q2 — 90-day superseded-lineage archival policy:** POST-F-27 ROADMAP.
- **Q3 — conditional Redis TTL operationalization and soak acceptance:**
  POST-F-27 ROADMAP; the `1h-conditional` description retains its own proof
  obligations.
- **Dangling-lineage auth-denial telemetry:** POST-F-27 OBSERVABILITY.
- **D6/A6 integrated acceptance battery:** SEPARATE FUTURE GATE. This closure
  is not an A6 sign-off; the A2 group gate separately requires hosted CI at the
  integrated tip, which remains unverified.

### Scope boundary

This section closes F-27 only. It does not close A2, A6, B0 or B1, and does
not change any percentage in the tables above. The R1–R8 lane's R4 row is
superseded on its blocker cell by this section; its historical text is left
intact for audit.

### Open integrity note

`REPORTS-MANIFEST.sha256` still reports `reports/my_scorecard.md: FAILED`
(`shasum -c` exit 1) because this file postdates the manifest. Regenerating the
manifest is an owner decision and was not performed here.

Reconciliation 2026-11-18: the manifest was regenerated with
`uv run python scripts/generate_reports_manifest.py` after the R1/R4/R6/R7 row
corrections. The FAILED result above records the state at the time of that
append, not the current state; no evidence correctness or approval is claimed
by the regeneration.

Fingerprint reproducibility. The `tracked-delta` fingerprint **reproduces
bit-exact** (`git diff | shasum -a 256`) on this candidate. The
`untracked-code` fingerprint could **not** be reproduced, because its
derivation method was never documented and no natural variant (sorted object
ids, concatenated contents, per-file digests, six-file scopes) reproduces
`f7bb747e…`. It is therefore carried as recorded but must be treated as
**UNVERIFIED**. This does not weaken the closure: the untracked files in
question are the F-27 tests themselves, which were re-executed green in this
review, and the tracked delta — the part that pins production source — is
identical to the value recorded at closure.

---

## Commit freeze verification — `e9f383b` (2026-11-01, Africa/Lagos)

**Status: VERIFIED WITH ONE RELEASE-BLOCKING GAP.** Read-only review of the
frozen commit. No production code changed, no test rewritten, no commit, no
push, no deployment, no percentage moved. This section is appended; the R1–R8
lane table and the R8 row above are left byte-intact (including the R8
"web-blocker cleared" edit already present in the working tree).

Candidate identity. `HEAD` = `e9f383bcbea51044c902406203f3c5485238b85a`,
parent = `524a017e4e889a5037b0ced162231afa63308cf8`, branch
`feat/sabiroute-routing-foundation`, message
`feat(gateway): freeze shared schema and application baseline` (one line, no
body). Scope verified exact: **25 files, +2313 / −151** (`git diff --numstat`
aggregate), 0 staged, sole tracked modification `reports/my_scorecard.md`.

### What the commit actually does (inspected, not inferred)

| Area | Change |
|---|---|
| F-27 lineage (R4) | New `sabiroute_accounting_lineages` table; `lineage_id` on `sabiroute_api_keys` and `sabiroute_budget_reservations`; revision `0006-accounting-lineages`; `create_lineage` / `get_lineage` / `reconcile_lineage_budgets`; `get()` denies a dangling lineage (fail closed); `rotate` carries lineage forward; rate-limit authority follows `lineage_id or key_id` |
| Schema groups (B1) | `SABIROUTE_SCHEMA_GROUPS` = `core`\|`full`; `CORE_TABLES` / `SABICHAT_PRODUCT_TABLES` inventories; `0005-schema-groups:<group>` ledger rows; refuses `core` on a product-table DB and `full`→`core` downgrade |
| Migration locking | `pg_advisory_xact_lock` + `SET LOCAL lock_timeout='30s'` in `ensure_schema`, `apply_schema_migrations`, `migrate_usage_columns`, and the new `python -m sabiroute.migrate` |
| BYOK-0 (R3) | Provider credential/identity deny-list (`apikey`, `apibase`, `authorization`, `customllmprovider`, `provider`), normalized to lowercase alphanumerics, nesting-scanned, depth-bounded **fail-closed**; now also scans `messages`, not just `extra_body` |
| Request bounds | `BodySizeMiddleware` (413 before routing/auth/accounting), `MAX_MESSAGES_PER_REQUEST` 256, `MAX_MESSAGE_CHARS` 500 000, `model` max_length 256 |
| D-R3-3 redaction | New `security/redaction.py`; wired into auth 503 (`from None`), startup/readiness, completions error+telemetry, admin error tracker |
| F-04 docs gating | `/docs`, `/redoc`, `/openapi.json` disabled unless `SABIROUTE_DOCS_ENABLED` |
| SabiChat surface | `chat_router` **newly mounted** (defined but unmounted at parent); `web/{index.html,app.js,styles.css}` added → `/app/` now served. This is why the recorded `/app/` 404 no longer reproduces: the mount already existed at parent, but the `web/` directory was empty |
| Startup contract | `PostgresApiKeyStore.__init__` and `SabiChatStore.__init__` **stop** calling `ensure_schema`; replaced by read-only `check_schema` in `build_gateway_state` / lifespan |
| Session hygiene | Best-effort purge at startup+shutdown; 30-day retention for revoked sessions |
| Tenant scoping | Usage finalize now requires `key_id` in addition to `request_id` |

### Fresh evidence gathered this review

- `ruff check src tests scripts config`: **clean**.
- `mypy src`: **clean, 49 source files**.
- `git diff --check`: **clean**.
- Full suite: **656 passed / 0 failed / 9 skipped** (services unset) — exactly
  the figure the R8 row cites, so that claim reproduces.
- Frontend scan: `web/app.js` contains **no** `innerHTML`, `outerHTML`,
  `eval`, `new Function`, `document.write`, or web storage; the bearer token
  is held in memory and sent only as an `Authorization` header.
- Fresh-database probe (disposable SQLite, `DATABASE_URL` unset): store
  construction creates **zero tables**; `check_schema` then raises
  `ValueError: Incompatible schema: missing tables ['sabiroute_api_key_budgets',
  'sabiroute_api_keys', 'sabiroute_budget_reservations', 'sabiroute_request_usage',
  'sabiroute_schema_versions']`; after an explicit `ensure_schema(groups="full")`
  it passes and the ledger reads
  `0001, 0002, 0003, 0004, 0006-accounting-lineages, 0005-schema-groups:full`.

### Findings

**F1 — HIGH — startup auto-migration removed, but no deployment path runs the
replacement.** `PostgresApiKeyStore.__init__` and `SabiChatStore.__init__` no
longer create schema, and the new `src/sabiroute/migrate.py` is wired **nowhere**:
`Dockerfile` ends at `CMD ["sabiroute"]` with no migrate step, `docker-compose.yml`
has no migrate service, and `sabiroute.migrate` appears in **no** file under
`docs/`, `scripts/`, `Makefile`, or `config/`. `docs/deployment.md` still states
schema is "applied transactionally at startup by every store entry point" — now
false. Consequence, proven above: a fresh deployment builds, fails `check_schema`,
degrades, and serves 503 on completions until an undocumented manual
`python -m sabiroute.migrate`. **Masked in tests** by the new autouse
`_ensure_schema_for_stores` fixture in `tests/conftest.py`, which monkeypatches
both `__init__`s to call `ensure_schema(groups="full")` — so the suite never
exercises the production startup contract, and no test builds the app from a
fresh `DATABASE_URL`. This is a tests-green / deploy-broken divergence, not a
test failure.

**F2 — MEDIUM — `check_schema` never validates `_ACCOUNTING_LINEAGES`.**
`_REQUIRED_COLUMNS` lists `sabiroute_accounting_lineages`, but `required_tables`
omits it, so that entry is unreachable; a database missing the lineages table
passes the check.

**F3 — LOW/MEDIUM — readiness permanently degrades on a transient DB blip.**
`api/health.py` sets `gateway.startup_error` and nulls `key_store`/`chat_store`
on any schema re-check failure. A momentary connection error during a readiness
poll is therefore sticky until process restart (self-heals only via container
restart).

**F4 — LOW — stale counts in docstrings.** `security/store.py` still says "`core`
creates only the nine Core-owned tables; `full` creates all 13" and "Core owns
the nine gateway tables below"; the actual inventories are **10** and **14**
(`CORE_TABLES` now includes `_ACCOUNTING_LINEAGES`). `reconcile_lineage_budgets`
also carries a duplicated comment line.

**F5 — LOW — `reconcile_lineage_budgets` no-ops on a missing lineage row.** The
final `UPDATE ... WHERE lineage_id = :id` affects 0 rows without error, so an
out-of-band-deleted lineage would still report `{"status": "reconciled"}`.
`api/admin.py` guards only the `record.lineage_id is None` case.

**F6 — LOW — URI redaction truncates at the first `@`.** `_URI_USERINFO` masks
only up to the first `@`, so a non-percent-encoded password containing `@` is
partially retained. Well-formed URIs percent-encode, and the module documents
its pattern-based limits; recorded for completeness.

**F7 — LOW — ledger assertions weakened.** Four tests changed
`applied_revisions() == [...]` to `applied_revisions()[:4] == [...]`; nothing now
asserts the full ledger, and the new `0005-schema-groups:*` row is asserted only
indirectly via the `SCHEMA_MIGRATIONS` constant.

### Scope boundary

This section records verification of `e9f383b` only. It does **not** close A2,
A6, B0, B1, or R8, and it moves **no** percentage in the tables above: the
commit is a freeze of already-lane-scored work, and F1 is a deployment-contract
gap rather than new capability. Recommended follow-up before any deploy: add
`python -m sabiroute.migrate` to the image/compose startup path (or reinstate a
guarded startup migration), correct `docs/deployment.md`, and add a test that
exercises startup against a schema-less database so the conftest fixture can no
longer mask F1.

### Manifest status (measured, not carried forward)

`REPORTS-MANIFEST.sha256` records `04e376bb…` for this file; the working copy
hashes `6b7d1c08…` (measured before this append), so
`shasum -c REPORTS-MANIFEST.sha256` reports `reports/my_scorecard.md: FAILED`.
Note that `REPORTS-PROVENANCE.md:124–125` asserts the scorecard "verifies OK in
the current manifest" — that held at the earlier repair but is **no longer
true** after subsequent edits (the R8 row, and now this section). Regenerating
the manifest remains an owner decision and was not performed here.

Reconciliation 2026-11-18: regenerated after the R1/R4/R6/R7 row corrections
and this append; the historical FAILED measurement above is superseded for the
current file bytes.
