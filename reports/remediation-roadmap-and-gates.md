# Remediation Backlog, Release Gates & Roadmap Proposal

Planning only. No implementation authorized. Scorecard untouched (no new
capability proven). Phase 13/training gates and deterministic-v1 frozen;
Phase 20 stays the production-review gate.

## 1. Remediation backlog (dependency order; parallelizable groups marked)

- **R-01 Per-user quotas + shared spend caps (AUD-01).** P1, blocks beta +
  Free Pool pilot. Outcome: authenticated choke points enforce per-user and
  global token/cost/window limits with safe exhaustion responses; metering
  first, billing explicitly out of scope. Requires: quota-design owner
  decision (Decision A). Tests: exhaustion/edge-window/multi-key live
  tests. Effort: high. Risk of fix: admission-latency + Redis dependency;
  rollback by flag-off. Gate: beta, pilot. Parallelizable: no (foundational).
- **R-02 Emergency shutdown (AUD-02).** P1, blocks pilot. Outcome: admin
  kill-switch for shared inference, no-redeploy activation, audited
  re-enable, startup-safe default. Requires: Decision B. Tests: activation/
  recovery without providers. Effort: low. Rollback: default-open removal.
  Gate: pilot. Parallelizable: yes.
- **R-03 Redis-backed limits + identity dimensions (AUD-03/AUD-04 slice).**
  P1, blocks beta scale. Outcome: auth/chat limits move to the proven Lua
  pattern with user/session/IP/key dimensions; fail-closed semantics kept.
  Requires: Decision C. Tests: concurrent-poconsistency tests. Effort:
  medium. Gate: beta. Parallelizable: with R-02.
- **R-04 Managed PG/TLS + backup/restore proof (AUD-05 slice).** P1, blocks
  staging/production. Outcome: disposable-managed TLS connect, migrate,
  backup, restore, rollback rehearsal — all with cited outputs. Effort:
  medium-high. Gate: production. Parallelizable: yes.
- **R-05 Hosted CI run + compose-up E2E (AUD-05 slice).** P1-evidence.
  Outcome: green GH run ID + red-trial proof; loopback full-stack up with
  stub-safe smoke. Effort: low-medium. Gate: alpha. Parallelizable: yes.
- **R-06 Security headers + CORS doctrine (AUD-06).** P2. Outcome: header
  middleware + test; CORS stays deny-by-default, documented. Effort: low.
  Gate: beta. Parallelizable: yes.
- **R-07 Browser suite + aria-live + mobile/a11y passes (AUD-07).** P2.
  Outcome: Playwright suite covering journeys + error states; announcements;
  measured contrast. Effort: medium. Gate: beta. Parallelizable: yes.
- **R-08 Retention/export/deletion (AUD-14).** P2. Outcome: retention
  windows, user export/delete, backup-retention rule, disclosures. Requires:
  Decision D. Effort: medium. Gate: beta. Parallelizable: with R-01.
- **R-09 Reports durability (AUD-09).** P2. Outcome: owner-chosen tracking
  or backup location. Requires owner decision (no ignore-rule change
  without approval). Effort: low. Gate: none (hygiene).
- **R-10 Image slimming + PG partial-failure tests (AUD-08/AUD-05 slice).**
  P2/P3. Outcome: smaller image; recovery-behavior tests. Effort: low-medium.
- **R-11 Hygiene (AUD-10/11/12/13).** P3. Process-local telemetry note,
  format pass (only if adopted as convention), `_web_dir` simplification,
  dep scan when a scanner is available. Never gate-blocking alone.

Out of scope for remediation: billing systems, paid plans, ML ranking,
feature bloat, rewrites of working routing code.

## 2. Release gates (independent; evidence, blockers, approver)

- **Gate A — local foundation.** Evidence: 308-test suite green, loopback
  compose config valid, container smokes, sqlite/PG-local migration proof.
  Residual: Redis skipped locally. Approver: owner (already largely met;
  R-05/R-10 polish outstanding). Verdict: CONDITIONAL GO.
- **Gate B — Developer Alpha.** Requires: R-05 green, client-compatibility
  matrix (untested), key-lifecycle docs, R-04 started. Audience: local
  single-user, own keys. Approver: owner. Verdict: CONDITIONAL GO (needs R-05).
- **Gate C — SabiChat Beta.** Requires: R-01, R-02, R-03, R-06, R-07 core,
  R-08 policy, invite-only boundary. Approver: owner. Verdict: NO-GO.
- **Gate D — Free Pool Pilot.** Requires: C + catalogue/mapping, provider
  ToS review, cohort + spend ceilings, shutdown drill. Approver: owner.
  Verdict: NO-GO.
- **Gate E — Public Production.** Requires: D + R-04 managed proof, staging
  + rollback rehearsal, monitoring/incident/off-host-backup policy,
  security/privacy review. Approver: owner. Verdict: NO-GO.

## 3. Target architecture (smallest coherent; deltas from current)

Current is retained, plus: quota service at the two choke points (auth +
chat) reusing the Lua pattern; kill-switch flag read at admission with
audited admin control; per-user gateway identity replacing the single
service key (one design decision); Redis for shared limits with fail-closed
semantics; retention worker for conversations/backups. No new services, no
control plane, no ML ranking. Dependency graph: R-09/R-06/R-07 (any order)
→ R-02/R-03 (needs A–C decisions) → R-01/R-08 → R-04/R-05 → gates C→D→E.
ADRs proposed: quota model, identity propagation, session persistence,
catalogue schema, Redis topology. Accepted already: one router, additive
ledger, PBKDF2, bearer sessions, zero-build UI, env-pinned containers.

## 4. Roadmap proposal (grouped by dependencies, not sprint counts)

- **M-1 Beta hardening** (R-02, R-03, R-06, R-09): kill-switch, shared
  limits, headers, reports fate. Non-goals: quotas, billing.
- **M-2 Quotas + privacy** (R-01, R-08): metering, exhaustion UX, retention/
  export/delete. Non-goals: payments.
- **M-3 Operational proof** (R-04, R-05, R-10): managed PG, GH green,
  compose E2E, slimming. Non-goals: production cutover.
- **M-4 Developer Alpha** (Gate B): client matrix + docs. Non-goals:
  multi-tenancy.
- **M-5 Closed Beta** (Gate C): invites, brakes, a11y core. Non-goals:
  open signup.
- **M-6 Free Pool Pilot** (Gate D): catalogue, ToS, ceilings, drill.
  Non-goals: unlimited-free claims.
- **M-7 Benchmarks** (deterministic only): methodology + numbers, no formula
  change without evidence. Non-goals: production ML.
- **M-8 Paid (optional)**: only with G economics + Phase 20. Non-goals:
  everything before G.
Each phase needs: goal/value, scope/non-goals, deps, acceptance tests +
  evidence, security/privacy note, cost, owner decisions. Rollback: flags
  off / previous image (migrations stay additive-only).

## 5. Owner decisions required (A–D condensed)

- **A quotas/catalogue:** meter-first with flag-off rollback (recommended)
  vs billing-coupled vs open-beta-no-limits (not recommended). Deferral
  blocks beta/pilot. Still needed: dimensions, exhaustion UX, mapping model.
- **B shutdown:** flag-in-DB fail-safe (recommended) vs redeploy-gated vs
  none. Deferral blocks pilot.
- **C identity/limits:** per-user gateway keys + Redis limits (recommended)
  vs single key + local limits (current, beta-blocking at scale).
- **D retention/reports:** 90-day conversations + export/delete + tracked
  reports (recommended; exact windows and ignore-rule change need approval)
  vs alternatives. Deferral blocks beta privacy bar.

## 6. Decision pack (executive answers)

1. Open: AUD-01–14 except none remediated (all class 1; A/D aspects need
   owner choice). 2. Remediated: none this mission (16A landed earlier —
   see dossier). 3. 16A/16B: 16A committed+pushed at HEAD, reviewed sound;
   16B uncommitted, reviewed-clean, awaiting owner commit decision. 4. Alpha
   blocked by: R-05 (GH run, compose E2E, client matrix). 5. Beta blocked
   by: R-01, R-02, R-03, R-06 core, R-07 core, R-08. 6. Pilot blocked by:
   beta + catalogue/ToS/ceilings/drill. 7. Production blocked by: everything
   above + R-04 + monitoring/incident/backup policy + reviews. 8. Decisions:
   §5 A–D. 9. Smallest first task: R-02 kill-switch (low effort, unblocks
   pilot path, no deps) — or R-09/R-06 if zero-risk starters preferred;
   recommended first: R-02. 10. Sequence: M-1 → M-2 → M-3 → gates. 11. Defer:
   slimming, format, paid, ML ranking, control plane. Abandon: nothing.
   12. Unavailable: GH run, managed PG, dep scan, automated browser suite.

**Planning completion does not authorize implementation.** No code changed,
nothing committed, no sprint started. Awaiting owner review and explicit
authorization of the first remediation task.
