# SabiRoute Architecture Decision Record (ADR)

Authoritative architecture + roadmap consolidation. Status of every claim is
labelled: code-inspected, unit-tested, integration-tested,
browser-smoke-tested, live-provider-tested, CI-verified, or not yet verified.
Nothing here is proven by this document existing — only by the cited evidence.

Note on placement: `docs/architecture.md` and `docs/troubleshooting.md` are
deliberately empty phase-gated placeholders per standing repository orders.
This record lives under its own filename so those orders stay intact.

## 1. Thesis (unchanged)

**SabiRoute decides; LiteLLM executes.**

SabiRoute owns routing policy, eligibility, scoring, budgets, usage
attribution, observability, and fallback policy. LiteLLM owns provider
execution, adapters, retries at the provider layer, and streaming mechanics
(code-inspected: `providers/litellm_client.py` posts to the proxy and never
implements provider logic; `providers/registry.py` is metadata-only).

Three pillars: **SabiRoute Core** (routing/policy foundation),
**SabiRoute Developer** (local-first gateway for IDEs/CLIs/agents),
**SabiChat** (accessible chat). **Free Pool is a governed eligibility/quota
policy, not a model list** (integration-tested: allowlist gate + stable
denials + attribution; catalogue mapping, quotas, and shared inference are
not yet verified).

## 2. Verified current state

- **Routing/fallback path** (integration-tested): `POST /v1/chat/completions`
  → key auth → usage admission → rate limit → alias/policy resolution →
  classification → capability → health → (Free Chat: allowlist gate) →
  budget reservation → attempt loop (`Router.choose_deployment` per attempt)
  → LiteLLM → `finish()` reconciliation. There is no `FallbackEngine` or
  `routing/fallback.py` in the tree (code-inspected: zero references) — the
  loop in `api/completions.py` is the only fallback implementation.
- **Health: passive only** (unit-tested): `HealthRegistry` tracks
  success/failure with a 3-failure/30s-cooldown discipline
  (code-inspected). There is no active checker (`providers/healthcheck.py`
  does not exist); "health" never means probed availability.
- **Free Pool** (integration-tested, stub + sqlite): disabled-by-default
  allowlist (`FreePoolPolicy.enabled is False`; env parsing fail-closed),
  pre-execution gate reusing the router, five stable denial reasons, zero
  LiteLLM calls on denial. Not yet verified: catalogue→registry mapping,
  concurrency-safe quotas, provider-terms validation, shared inference.
- **Usage attribution + ledger** (integration-tested, local PG 16):
  `usage_source` in {unknown, free_pool, byok, paid}; admission always
  `unknown`, upgraded only on gate-allow; legacy NULL reads as `unknown`.
  Ordered additive revisions `0001-usage-source`, `0002-sabichat-backend`
  recorded in `sabiroute_schema_versions`; re-runs are no-ops; failures
  propagate transactionally.
- **SabiChat backend** (integration-tested, stub + sqlite): PBKDF2 sessions
  (digest-only, 7-day expiry, revocation), owner-scoped conversations, chat
  via the in-process gateway path with a memory-only service key, fixed
  public error mapping. Limits: one service key (re-minted on restart),
  single-process rate limits, 20-message history, fixed response cap.
- **SabiChat in-process timeout limit** (source-inspected + isolated
  exploratory probe, not a regression test): `SabiChatService.complete()`
  calls the gateway in-process through `httpx.ASGITransport`
  (`api/chat.py`). Under the inspected HTTPX 0.28.1 implementation, the
  configured `httpx.Timeout(INTERNAL_TIMEOUT_SECONDS=120.0)` is not
  enforced on that path — no timeout wrapper exists in
  `AsyncClient._send_single_request` or the ASGI transport
  (`TimeoutException` is raised only by network transports). Probe: 0.3s
  and 1.5s client timeouts against a hanging ASGI app both reached their
  external caps with no `httpx.TimeoutException`; the fast-response
  control succeeded and externally imposed cancellation reached the app.
  The inner completions deadline is therefore the effective
  request-level bound here (it bounds the response wait, not necessarily
  worker-thread or downstream work). The `504 gateway_timeout` mapping
  remains in code but was not demonstrated to fire for an in-process hang.
  Version- and transport-specific; not generalized to other HTTPX
  versions or network-based paths.
- **SabiChat frontend** (browser-smoke-tested, manual + static tests):
  zero-build UI at `/app/`; token memory-only; textContent-only rendering;
  double-submit/cancel/switch guards browser-proven. No automated browser
  suite; no mobile/a11y passes.
- **Local PG 16 gate** (integration-tested): 19/19 on disposable PostgreSQL
  16.15 — fresh init, round trips, idempotent re-run, pre-ledger upgrade
  with legacy preservation, clear `OperationalError` on bad credentials,
  `pg_dump`/restore equality. Managed PostgreSQL/TLS: not yet verified.
- **Container + compose** (integration-tested, local): image builds
  (2.71 GB) and smokes green (`live`/`ready`/`app` 200, non-root, healthy);
  compose defines the API loopback-only with fail-fast password guards and
  validates; full-stack `up` not run.
- **CI** (code-inspected + locally executed steps): workflow defined (locked
  install, pytest with Redis service, ruff, mypy, JS check, docker build);
  a hosted GitHub Actions run is not yet verified.
- **Tests**: 308 passed / 4 skipped (env-gated Redis), ruff/mypy/diff/`node
  --check` clean — all re-run for this record (integration-tested locally).
  Live-provider evidence remains documentary and success-only; no staging
  evidence exists.
- **Concurrency/ops limits** (code-inspected): the only bound is the
  32-slot store executor; no HTTP concurrency limits; shutdown closes key
  store, limiter, and chat store; logs carry IDs, never secrets. Single
  node throughout — no HA claims.

## 3. Decisions (accepted) vs open questions

Accepted: one routing engine (no parallel router, no BYOK execution
bypass); budgets before execution with reconciliation; Free Pool
disabled-by-default with fail-closed semantics; additive-only migrations
with an explicit ledger instead of a framework; stdlib PBKDF2 over a new
dependency; bearer sessions over cookies (no CSRF surface); zero-build UI
over a frontend toolchain; env-pinned paths in containers over
repo-relative resolution.

Open: per-user gateway keys vs single service key; session persistence
across reloads; catalogue data model and its mapping to deployments;
quota-accounting design (request counters vs token aggregation); Redis
managed vs VPS with caps; image slimming strategy; which metrics/alerts
define staging readiness.

## 4. Roadmap (planning milestones, not completions)

Order follows code dependencies; cost is low/medium/high tooling effort.

**A. Architecture/documentation reconciliation.** Objective: one truthful
record. Prerequisites: none. Scope: this ADR, README/roadmap consistency.
Acceptance: claims labelled, links valid, no stale bullets. Evidence: this
file + `git diff --check`. Risks: doc drift. Cost: low (this task).
Non-goals: behavior changes.

**B. Local deployment + Compose end-to-end.** Objective: `docker compose up`
serving the gateway + UI with stub-safe smoke. Prerequisites: Sprint 5
artifacts (done). Scope: full-stack up, loopback smoke incl. a chat round
trip with test keys. Acceptance: live/ready/app 200 from compose;
shutdown clean. Evidence: command outputs. Risks: provider keys needed for
real completions (stub-safe smoke only). Cost: low. Non-goals: cloud, DNS.

**C. CI verification + failure testing.** Objective: prove the workflow runs
hosted and fails loudly. Prerequisites: B. Scope: push to trigger GH run;
break-the-build trial (reverted) to prove red0769efb states. Acceptance: green run
ID + red trial linked. Evidence: GH UI records. Risks: runner availability.
Cost: low. Non-goals: deploy jobs.

**D. Managed PostgreSQL/TLS + staging readiness.** Objective: close the data
safety gap. Prerequisites: local-PG gate (done). Scope: disposable managed
instance — TLS connect, backup → migrate → count/revision check, restore
test, rollback rehearsal. Acceptance: documented outputs on real managed
infrastructure. Risks: cost, credential handling. Cost: medium. Non-goals:
production cutover.

**E. Developer-gateway alpha.** Objective: external clients succeed.
Prerequisites: C, D. Scope: OpenAI-compatible validation ( IDE/CLI/agent
clients), key lifecycle docs, rate-limit/budget behavior notes. Acceptance:
named clients complete scripted flows against staging. Risks: client
quirks. Cost: medium. Non-goals: public launch.

**F. SabiChat closed beta.** Objective: real users, bounded. Prerequisites:
E + per-user quota design (from §3 open questions). Scope: invite-only UI
with abuse brakes, feedback channel. Acceptance: beta cohort completes
journeys; incident-free window. Risks: abuse, cost exposure. Cost: high.
Non-goals: open signup, paid plans.

**G. Free Pool catalogue + quotas + provider policy.** Objective: make Free
Pool real and safe. Prerequisites: F telemetry. Scope: catalogue data +
mapping, concurrency-safe quotas, budget enforcement, provider-terms review
per arrangement. Acceptance: quota-exhaustion and denial paths tested live;
terms documented per provider. Risks: ToS violations, cost overruns.
Cost: high. Non-goals: unlimited free inference claims.

**H. Deterministic benchmarks + task-aware experiments.** Objective: measure
before learning. Prerequisites: G traffic. Scope: fixed benchmark harness,
measured-vs-priority comparisons on real telemetry. Acceptance: published
methodology + numbers, no formula change without evidence. Risks:
benchmark gaming. Cost: medium. Non-goals: production ML ranking.

**I. Optional paid services.** Objective: only with unit economics proven.
Prerequisites: G, H, Phase 20 review. Scope: pricing, billing, operating
controls. Acceptance: cost controls demonstrated, incident drills passed.
Cost: high. Non-goals: anything before G–H evidence exists.

Phase 13 training gates and deterministic-v1 stay frozen throughout; no
learned routing enters production in any milestone above.

## 5. Production-readiness gates (all outstanding)

Actual GH Actions execution · full-stack Compose E2E · PG partial-failure
and recovery testing · managed PostgreSQL/TLS validation · managed backup
and restore validation · staging deploy + rollback evidence ·
Redis/concurrency behavior · provider failure/fallback/quota/rate-limit
behavior live · monitoring/budgets/incident/off-host-backup policy ·
security/privacy/abuse review. Each opens only on cited evidence, never on
configuration alone.

## 6. Green Closure owner decisions (recorded 2026-10-27; D2/D4/D5/D6 decided, not re-asked)

- **D1 B3 shared-completion-code ownership — DECIDED/RECORDED (`owner-self`):** the user explicitly accepts B3 stewardship. Enforcement verified in code (`completions.py` BYOK-0 + error contract) and covered by focused tests. No human name/email/username invented; `owner-self` is the declared accountability token.
- **D2 OD-3b session purge — DECIDED (direction + scope):** 30-day retention approved for `sabichat_sessions` rows where `expires_at < now` OR (`revoked_at` non-null AND `revoked_at < now − 30d`) — verified at `chat/store.py:213-232`, no other data class affected. Recorded as decided; implementation already matches.
- **D3 OD-1/OD-2 — DECIDED/RECORDED (`owner-self`, `accept-adr`):** single accountable owner accepted (`owner-self` token; no human identity invented) and `docs/architecture-decision-record.md` accepted as the canonical decision log, subject to normal repository tracking and review. Tracking is applied by the R1/R4 status reconciliation commit on `sec/deps-nov` (this change); canonical status takes effect when that commit lands, not by a text edit alone. No review approval or push is claimed here.
- **D4 OD-12 push policy — DECIDED/SETTLED:** no push without explicit owner authorization; no exceptions (`CLAUDE.md:189`, checklist gate). No push performed.
- **D5 Core rollout — DECIDED/SETTLED:** default stays `full`; no per-environment `core` flip authorized or performed.
- **D6 A6 suite — CONDITIONAL BASELINE APPROVED:** 18-file suite + static checks + isolated PG/Redis evidence adopted as the baseline package; every mandatory criterion keeps its own verdict. Not a waiver of any criterion. Full-suite sign-off remains conditional on the criterion matrix, not on this token alone.
- **D7 F-27 — IMPLEMENTATION AUTHORIZED (2026-10-29):** Owner explicitly authorized local implementation of F-27 Option C (dedicated `_ACCOUNTING_LINEAGES` table) under the constraints in the Green Closure Owner Decision Record. Implementation completed in this mission: table + `lineage_id` columns on `_API_KEYS` and `_BUDGET_RESERVATIONS`, `create_lineage`/`reconcile_lineage_budgets` helpers, lineage carry on rotation, lineage-aware reservation inserts, migration ledger row `0006-accounting-lineages`, legacy migration support. No shared/production DB mutation, no push, no deployment. Historical design-only restriction is superseded by this explicit authorization; prior design-only status preserved as historical context.
  - **F-27 Q1 reconciliation authority (`admin-role`):** budget reconciliation requires an explicit administrative budget-approver role; every reconciliation action must record the authorized operator. No operator identity invented.
  - **F-27 Q2 superseded lineage retention (`90d-archive`):** archive superseded lineage records after 90 days under a defined, auditable archival policy. Never delete unattributed accounting history. Archival policy definition itself remains a design deliverable.
  - **F-27 Q3 Redis compatibility TTL (`1h-conditional`):** one hour is a proposed starting TTL only; acceptance requires a documented soak criterion and verified rollback. Not tested or production-safe; `min()` never-looser property carries proof obligations (equivalent units, scope, limit semantics, concurrency, rotation, stale state, dual-write failures, outages, rollback).
- **D8 F-27 — FORMALLY CLOSED / COMPLETE (2026-10-31, owner-approved):** Owner formally accepts F-27 (key-rotation accounting continuity) as complete on candidate `b360ffc` (`feat/sabiroute-routing-foundation`), independently re-verified by Terminal D with no production-code change, no test rewrite, no commit, no push, no deployment. Evidence: focused F-27 suite 31 passed / 0 failed / 0 skipped across six files (`test_accounting_lineage`, `test_lineage_compat_state`, `test_lineage_admission_concurrency`, `test_lineage_redis_continuity`, `test_lineage_rollback_injection`, `test_admin_lineage_http`); `ruff check src tests scripts config` clean; `mypy src` clean (48 files); candidate fingerprints unchanged across the verification run. Real-runtime proof: disposable Redis demonstrates Key A exhausting its burst, rotation carrying one lineage bucket, and Key B receiving no fresh allowance (fresh-lineage control admits); deterministic failure injection leaves no partial key/lineage state and a retry succeeds deterministically; barrier-synchronized 2- and 5-contender rotations produce exactly one winner with no split authority, including in-flight rotation. Full reconciliation, criterion table and content fingerprint: `reports/my_scorecard.md` § "F-27 formal closure — 2026-10-31".
  - **F-27 post-closure items — explicitly NOT closure blockers:** Q2 (`90d-archive`) → POST-F-27 ROADMAP; Q3 (`1h-conditional`) → POST-F-27 ROADMAP; dangling-lineage auth-denial telemetry → POST-F-27 OBSERVABILITY; D6/A6 integrated acceptance battery → SEPARATE FUTURE GATE (D6 unchanged; D8 is not an A6 sign-off).
  - **D8 scope boundary:** closes F-27 only. Does not close A2, A6, B0 or B1, and asserts no hosted-CI or live-provider evidence.
- **AMBER-A/B — PREPARED, BLOCKED:** live-provider matrix ready (endpoint/credentials/budget unauthorised — zero live calls); recovery/shutdown mock+disposable tests green, live-procedure runs pending authorization/environment.
