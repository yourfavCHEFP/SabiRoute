# SabiRoute — Build Map

**Part I: State of the build · Part II: Forward build order**

| Field | Value |
|---|---|
| Status | **PROPOSED — NOT GOVERNING** until owner review |
| Date | 2026-11-11 |
| Repository baseline | `1e69ada943f3d3921122219e7a569cdff989d3fd` |
| Working branch at authoring | `sec/deps-nov` (see **R-1**, Part III) |
| Supersedes | Nothing. Consolidates: `CLAUDE.md` §11, `README.md` roadmap, `SabiRoute-Master-Build-Checklist-v1.2-CANDIDATE.md` |
| Author | Claude Code |

> **This document approves nothing, authorizes nothing, and executes nothing.** It maps
> what exists and what must happen next. Every action it describes remains subject to the
> owner-authorization gates it names.

---

## Evidence basis — read this before relying on any row

**This map was assembled by inspection only.** Shell execution was unavailable during the
authoring session (the auto-mode permission classifier blocked every `Bash` call), so the
following were **not re-executed**:

- the pytest suite (last recorded: **663 passed, 9 skipped** — `CLAUDE.md` §11, 2026-11-04);
- `ruff` / `mypy` (last recorded clean, 2026-11-04);
- the R6 digest conformance suite (last recorded: **81 passed, 1 skipped / 82 collected** —
  `r6-close-final-06`, 2026-11-08);
- any provider call, database connection, or migration.

Per the repository evidence standard (`CLAUDE.md` §2), **no row below is labelled
`VERIFIED BY RUNTIME` on the strength of this session.** Rows carry their actual basis:

| Label | Applied to |
|---|---|
| **INSPECTION** | Read directly from the tree in this session (module inventory, config, document text) |
| **CARRIED** | Carried forward from a dated prior record; not re-executed here |
| **INFERRED** | Reasoned from structure; not executed |
| **UNVERIFIED** | Assumed; no evidence |

A green suite is evidence. It is **not** proof of live provider behaviour, integration
correctness, or production readiness. Those are four different states and this map never
collapses them (`CLAUDE.md` §2).

---

# PART I — STATE OF THE BUILD

## I.1 Repository position

| Fact | Value | Basis |
|---|---|---|
| HEAD | `1e69ada9` — `test: strengthen settlement integrity regression coverage` | INSPECTION |
| Working branch | `sec/deps-nov` | INSPECTION |
| Documented authoritative branch | `feat/sabiroute-routing-foundation` | INSPECTION (`CLAUDE.md` §9A) |
| Branch divergence from origin | **DIVERGED both ways** — local 6 commits ahead, origin 3 ahead. Origin's unique contribution is narrow: PostgreSQL CI service, `.env.example` docs, 12 lines of `docs/security.md`. 61 of the 86 paths origin touches are byte-identical to local HEAD | CARRIED (2026-11-04) |
| Suite | 663 passed, 9 skipped — all 9 environment-gated on `SABIROUTE_TEST_REDIS_URL` / `SABIROUTE_TEST_PG_URL`, none a contract skip | CARRIED (2026-11-04) |
| Lint / types | `ruff check src tests scripts config` clean; `mypy src` clean over 49 files | CARRIED (2026-11-04) |
| R6 digest conformance | 81 passed, 1 skipped (82 collected) | CARRIED (2026-11-08) |

**The branch does not match the documented authoritative branch.** This is recorded, not
resolved — resolving it is an owner act (**R-1**).

## I.2 Module inventory — where the build actually lives

**41 non-empty Python modules, ~11,332 lines, under `src/sabiroute/`** (INSPECTION).

| Package | Modules | Lines | Role |
|---|---:|---:|---|
| `api/` | 8 | 3,849 | HTTP surface, request path, accounting, deadline, shutdown |
| `security/` | 7 | 2,600 | Auth, keys, budgets, rate limits, redaction, persistence |
| `chat/` | 3 | 500 | SabiChat sessions, passwords, conversation store |
| `freepool/` | 2 | 192 | Free Pool allowlist + eligibility |
| `routing/` | 4 | 782 | Router, policies, health, deterministic scoring |
| `providers/` | 4 | 536 | Registry, base contract, LiteLLM client |
| `config/` | 3 | 318 | Typed models, loader, validation |
| `monitoring/` | 4 | 172 | Latency, usage, errors, metrics trackers |
| `intelligence/` | 1 | 1,561 | Phase 13.1 feature snapshots + read-only audit |
| root modules | 5 | 822 | `gateway.py`, `main.py`, `capabilities.py`, `quotas.py`, `migrate.py` |

### Detail map

```
api/
  completions.py   2,136  ← THE request path. Auth → caps → BYOK → usage event →
                            rate → budget → capability → health → Router.choose_deployment
                            → LiteLLM → retry/fallback → settlement. Free Pool gate lives here.
  chat.py            858  SabiChat gateway chat surface (interim-grade)
  admin.py           400  Key lifecycle, rate-limit, budget, usage, telemetry endpoints
  body_limit.py      122  F-05 request body/message caps
  shutdown.py        119  Kill-switch
  deadline.py        105  Absolute request deadlines (300s)
  health.py           89  /health, /health/live, /health/ready
  models.py           20  API response models

security/
  store.py         1,626  ← Persistence: SQLite + PostgreSQL, schema ledger, settlement
  keys.py            449  Key issue / rotate / revoke, hashing, plaintext-once return
  store_executor.py  180  Off-loop executor offload for store operations
  auth.py            124  Client/admin boundary
  rate_limit.py       84  Per-key request rate + burst
  budgets.py          72  Daily/monthly token and cost budgets
  redaction.py        65  Credential redaction

routing/
  router.py          262  Candidate filtering + deterministic selection
  scoring.py         252  deterministic-v1: 0.7·success + 0.3·latency_normalized
  policies.py        143  Six virtual route policies
  health.py          125  Passive success/failure + cooldown registry

intelligence/
  dataset.py       1,561  Phase 13.1 feature snapshots (schema 1.1) + read-only audit
```

**Structural observation (INFERRED):** `api/completions.py` at 2,136 lines carries the request
path, the retry/fallback loop, the Free Pool pre-execution gate, and settlement. It is the
single highest-risk module in the tree and the one every P0 defect touches.

## I.3 Phase status map

Statuses reproduce `CLAUDE.md` §11 and the `README.md` roadmap, which **agree** (INSPECTION).
They are CARRIED — not re-derived here. Vocabulary is the repository's own and is never
interchangeable: **Complete** = implemented + tested + live-verified · **Implemented** = code
and tests exist, verification incomplete · **In progress** · **Blocked** · **Planned**.

| Phase | Focus | Status | Where it lives | The gap that keeps it from "Complete" |
|---:|---|---|---|---|
| 00 | Architecture & environment | **Complete** | `config/`, `main.py`, `gateway.py` | — |
| 01 | Basic LiteLLM gateway | **Complete** | `api/completions.py`, `providers/litellm_client.py` | Fallback has test evidence only, no live failure injection |
| 02 | Provider expansion | **In progress** | `config/config.yaml`, `providers/registry.py` | 3 of 14 aliases have runtime evidence |
| 03 | Model registry | **Complete** | `config/config.yaml`, `providers/registry.py` | — |
| 04 | Virtual models / policies | **Complete** | `routing/policies.py` | — |
| 05 | Fallback engine | **Implemented** | `api/completions.py` (no separate module) | No live failure-injection evidence |
| 06 | Health monitoring | **Implemented** | `routing/health.py` | Passive cooldown only; active checker removed |
| 07 | Observability | **Implemented** | `monitoring/` + `api/admin.py` | No stored failure-metric evidence |
| 08 | PostgreSQL | **Complete** | `security/store.py` | Managed-PostgreSQL never exercised |
| 09 | Auth & API keys | **Complete** | `security/auth.py`, `security/keys.py` | — |
| 10 | Budgets & rate limits | **Implemented** | `security/budgets.py`, `security/rate_limit.py` | Live rejection paths never exercised |
| 11 | Capability-aware routing | **Implemented** | `capabilities.py`, `routing/router.py` | Capability evidence missing for 11 of 14 |
| 12 | Measured deterministic scoring | **Implemented** | `routing/scoring.py` | Benchmark evidence synthetic only; signals process-local |
| 13 | ML-assisted routing | **In progress** | `intelligence/dataset.py` | 13.2 aggregate closure pending; **13.3 blocked** |
| 14 | Benchmarking | **Planned** | — | — |
| 15 | Admin dashboard | **Planned** | — | — |
| 16 | Remote access / Tailscale | **Planned** | — | — |
| 17 | Security hardening | **Planned** | — | — |
| 18 | Testing & regression | **Planned** | — | Tests required throughout earlier phases |
| 19 | CI/CD | **Implemented** | `.github/workflows/ci.yml` | Hosted Actions run never verified |
| 20 | Production architecture | **Planned** | — | — |

**Read the last column, not the status word.** Nine phases read "Complete" and eleven read
"Planned"/"In progress"; the operative fact is that **no phase in this table has been
re-verified at the current baseline** — the 2026-11-04 measurement predates `1e69ada9`.

## I.4 Cross-cutting workstreams (not phases)

These carry no phase number and **must not** be renumbered into the roadmap.

| Workstream | Status | Where | Boundary |
|---|---|---|---|
| Free Pool runtime enforcement | Implemented, API-tested (stub execution, file-backed DB) | `freepool/eligibility.py`, gate in `api/completions.py` | Disabled by default (`SABIROUTE_FREEPOOL_ENABLED`); fails closed. Catalogue mapping, quotas, shared inference **not built** |
| Usage-source attribution | Implemented | settlement in `security/store.py` | Only `free_pool` is assigned today; legacy rows never backfilled |
| SabiChat backend | Implemented, API-tested | `chat/`, `api/chat.py` | Interim-grade: memory-held service key, single-process limits, in-memory session token |
| SabiChat frontend | Implemented | `web/`, served at `/app/` | Minimal; **no automated browser test suite** |
| R6 governance corpus | **Untracked — evidence not durable** | `docs/r6-*` (42 files on disk) | See II.0 |

## I.5 Deliberately empty — do not fill

Five source files are **zero bytes by design** and absent from the module inventory above
(INSPECTION — they do not appear in a scan of populated modules):

- `src/sabiroute/security/permissions.py`
- `src/sabiroute/intelligence/classifier.py`
- `src/sabiroute/intelligence/scorer.py`
- `src/sabiroute/intelligence/selector.py`
- `src/sabiroute/routing/intelligent.py`

Root placeholders awaiting their phases: `CHANGELOG.md`, `Makefile`, `requirements.txt`,
`docs/architecture.md`, `docs/troubleshooting.md`.

**Do not fill gaps to make the tree look complete.** (`CLAUDE.md` §12)

## I.6 Things that do not exist — stop looking for them

Each of the following has been claimed or assumed at some point and **is not in the tree**.
Their absence is enforced by tests, not merely unreported:

| Absent artefact | Reality | Enforcement |
|---|---|---|
| `routing/fallback.py` | Never existed. Retry/fallback loop lives in `api/completions.py` | `tests/test_health.py:88` asserts `find_spec(...) is None` |
| `providers/healthcheck.py` | Deleted after verification nothing referenced it | `tests/test_health.py:89` asserts no `ProviderHealthChecker` |
| `FallbackEngine` class | Does not exist anywhere | Same |
| Alembic | Not used. Ordered additive revision ledger (`sabiroute_schema_versions`: `0001-usage-source`, `0002-sabichat-backend`) | `security/store.py`, `migrate.py` |
| `config/models/` fragments | Present but **not loaded** — `config/config.yaml` is the single catalog | Runtime loader |

## I.7 Claims that are known-invalid — carry them as invalid

- **Aggregate dataset integrity: FAILED.** One feature/outcome count mismatch and one outcome
  without a feature snapshot remain, **deliberately unrepaired**. Do not fabricate timestamps
  or reconstructed features to close them.
- **Training is blocked.** No outcome variation (all 6 provider attempts successful), incomplete
  temporal provenance (2 of 6 verified), no defensible chronological split.
- **No model has been trained or deployed.** `training_authorized` stays false.
- **Capability metadata:** 11 of 14 deployments are `unknown` across every capability.

---

# PART II — FORWARD BUILD ORDER

## II.0 The gate that governs everything else

> **R6.0 IS NOT CLOSED. R6.0 REGISTRATION IS NO-GO. `R6/G7` IS NOT GRANTED.**
> — `r6-close-final-06` §0 (2026-11-07, corrected 2026-11-08)

Three facts, each independently sufficient:

1. **All 23 owner selections are recorded; none is registered.** 23 of 23 responses, 0
   outstanding — but **0 approved, 0 registered, 0 independently verified, 0 gate-accepted.**
   Selection is not registration.
2. **The registration protocol is not executable.** `marker_sha256` — a required VER-record
   field — is **uncomputable** because the owner has not answered **O1** (the U4 REG-marker
   digest boundary). No O1 → no VER record → no registration can reach COMPLETE.
3. **The evidence is not durable.** The R6 corpus is **untracked** (`git ls-files | grep -c "r6-"`
   = 0). Gate **R6.0-D is NOT MET**. A `git clean`, fresh clone, or branch switch discarding
   untracked files destroys the evidence the U2 digests bind.

**This is not a finding that the work is wrong.** The digest layer is mechanically sound
(81 passed, 1 skipped). The remaining distance is **owner-time and repository-time, not
engineering-time** — and it is bounded and enumerable.

## II.1 Two tracks that must not be confused

The most common planning error in this repository is conflating them.

| Track | Question it answers | Governed by | Current state |
|---|---|---|---|
| **R6 governance** | Who approves, registers, and verifies the decisions? | `r6-*` corpus, T16, 03B-R1 protocol | **NO-GO** — awaiting owner O1/O2 + corpus tracking |
| **Phase build** | What gets engineered next? | `CLAUDE.md` §11, roadmap | Phase 13 blocked; P0 defects open |

Engineering can proceed on the Phase track **without** R6 closing — but no engineering action
may be represented as satisfying an R6 gate, and no R6 decision may be inferred from engineering
progress.

## II.2 The P0 defect lane — dependency-ordered, authorization-gated

Three phases. Each has an exit gate and each requires **separate, explicit owner authorization**.

```
P0 PHASE 1 — BYOK-0                        [NOT STARTED / NOT AUTHORIZED]
  Guard exact top-level fields: api_key, api_base, authorization
  Position: after auth + F-05 caps, BEFORE request_id and create_usage_event
            (therefore before rate admission and all accounting writes)
  Response: HTTP 400, error.type == "invalid_request_error", generic, non-echoing
  Must prove zero: usage rows · reservations · snapshots · rate tokens ·
                   provider calls · credential leakage
  EXIT: agreed matrix passes on ONE exact candidate
        │
        ▼
P0 PHASE 2 — MIGRATION SAFETY PROOF        [NEXT: READ-ONLY PROOF PREPARATION]
  Read-only. No edits, no migrations, no DB/Redis connections, no provider calls, no tests.
  Analyse SQLite and PostgreSQL SEPARATELY — do not assume with_for_update, DDL
  transactions, or savepoint behaviour is equivalent across dialects.
  Must answer: can one migration/backfill owner be guaranteed across column addition,
  backfill, and ledger commit? Does restart converge? What happens on concurrent
  key creation?
  CRITICAL PROOF GATE: two simultaneous initializers → one backfill owner,
  no escaped IntegrityError, one ledger entry.
        │
        ▼
P0 PHASE 3 — ACCOUNTING CONTINUITY         [BLOCKED]
  Depends on Phase 2's accepted strategy AND separate implementation authorization.
  Stable undashed UUID-hex accounting_id (String(32)); key_id retained for auth/audit;
  accounting_id inherited on every rotation; disjoint Redis v2 namespace;
  pre-fix historical rotations stay split; quota ledger unchanged.
```

**The critical proof gate is Phase 2, two-simultaneous-initializers.** It is currently
*Unproven in this pass* for **both** dialects. A savepoint that merely tolerates a duplicate
ledger insert is explicitly **not sufficient proof**.

Also unexecuted: fresh install, legacy populated database backfill, crash-between-stages
convergence, key-created-during-backfill, historical rotation separation, and the enforced
single-writer fallback.

## II.3 The ML gate — Sprints 13–15

```
13  DATA RECONCILIATION      OPEN — audit succeeded, integrity FAILED
    Decision-time features linked to attempts/outcomes; timestamps, labels,
    leakage, provenance audited.
    7 requests · 6 attempts · 5 snapshots · 6 outcomes
    → 1 count mismatch · 1 outcome without snapshot · 2/6 verified provenance
        │
        ▼
14  VALID EVALUATION         OPEN
    Chronological split, fallback grouping, versioned data/features,
    reproducible deterministic baseline, confidence intervals.
    BLOCKED: no usable chronological split (one attempt lacks a decision timestamp)
        │
        ▼
15  MODEL EVALUATION         OPEN
    Interpretable model vs deterministic-v1; shadow mode; disagreement analysis;
    reversible rollout only after review.
```

**ML gate rule:** do not begin ML routing because the sprints have plan entries. The
data-quality and evaluation criteria must pass on exact, reproducible evidence.
**HTTP success is an operational outcome, not answer quality.** Never invent labels,
timestamps, selection propensities, counterfactuals, or failures.

## II.4 Earliest available engineering work, ranked

Ranked by dependency clearance — everything here is unblocked **today** and needs no new
authorization to *prove* (as opposed to to *change*):

| # | Work | Why it is available | Gate |
|---:|---|---|---|
| 1 | **O1 answer + R6 corpus tracking** | Pure owner act; blocks all registration | Owner |
| 2 | **Migration safety proof (P0 Phase 2)** | Explicitly read-only | Owner authorization to *begin* |
| 3 | **Phase 02 provider evidence** | 11 unverified aliases; harness exists (`scripts/test_providers.py`) | Makes real provider calls — needs authorization |
| 4 | **Phase 05 live failure injection** | Fallback is unit-tested only; runbook exists | Disposable fixtures only |
| 5 | **Phase 10 rejection paths** | Budget/rate rejection never exercised live | Local services only |
| 6 | **Phase 13.2 aggregate closure** | Audit tool exists and is read-only | Unrepairable rows stay unrepairable by design |
| 7 | **Phase 19 hosted CI run** | Every step executed locally; hosted unverified | Push authorization |

## II.5 Blocked — do not start

- **Anything requiring single-owner migration proof** — P0 Phase 3.
- **Phase 13.3 training** — `training_authorized` false; needs fresh read-only audit *and*
  human approval.
- **ML routing, RL, dashboards, Go rewrite, enterprise control plane, cloud deployment,
  native IDE extensions, autonomous agents** — gated on a proven gateway foundation
  (`CLAUDE.md` §10).
- **Shared hosted inference** — Phase 20 gate plus its own acceptance review.
- **Any push, merge, rebase, cherry-pick, reset, or force-push** — `CLAUDE.md` §9A forbids
  without explicit owner authorization. The origin divergence is **reported, not resolved**.
- **Filling placeholder files** to make the tree look complete.

## II.6 Authorization ledger — what needs an owner decision

| Action | Authorization required | Granted? |
|---|---|---|
| Answer **O1** / **O2** | Owner | **No** |
| Track the R6 corpus (stage/commit) | Owner | **No** |
| Begin P0 Phase 2 proof | Owner | **No** |
| Implement BYOK-0 | Owner | **No** |
| Implement accounting continuity | Owner | **No** |
| Make real provider calls for Phase 02 | Owner | **No** |
| Run Redis/PG integration tests | Owner + disposable loopback instance | **No** |
| Train any model | Owner, after audit | **No** |
| Push / merge / resolve origin divergence | Owner | **No** |
| Resolve branch mismatch (**R-1**) | Owner | **No** |

**Nothing in this column is granted.** The correct posture at this baseline is: prove,
report, wait.

---

# PART III — RECONCILIATION FINDINGS

Discrepancies surfaced while assembling this map. Recorded, not resolved — each is an owner
act, per `CLAUDE.md` §11's rule that where documents disagree, evidence decides and both get
corrected.

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| **R-1** | Working branch is `sec/deps-nov`; documented authoritative branch is `feat/sabiroute-routing-foundation` | INSPECTION | Every phase record is attributed to the latter. Attribution is unsound until reconciled |
| **R-2** | The v1.2 checklist is dated 2026-10-23 and cites Core `0cb053d`; HEAD is `1e69ada9` | INSPECTION | Its P0 statuses and baseline are **5 weeks stale**. Its *gates and procedures* remain valid; its *statuses* do not |
| **R-3** | Checklist is marked `NOT YET GOVERNING` and was never registered | INSPECTION | It cannot be cited as authority. This map does not promote it |
| **R-4** | R6 corpus is 42 files on disk, 0 tracked | CARRIED (FINAL-06 §0) | Evidence is one `git clean` from destruction; gate R6.0-D unmet |
| **R-5** | No phase status has been re-derived since 2026-11-04; `1e69ada9` postdates it | INSPECTION | Phase table is CARRIED, not current. Re-verification is the cheapest high-value action available |
| **R-6** | `CLAUDE.md` §11 Phase 06 says "active checker unwired"; `README.md` says "removed" | INSPECTION | Wording divergence only — the module is genuinely absent, asserted by two tests. README's wording is the accurate one |
| **R-7** | `api/completions.py` is 2,136 lines and carries four distinct responsibilities | INSPECTION | Highest-risk module; every P0 defect lands here. Not a defect — a structural risk to record |

---

## How this map is maintained

- **Regenerate the state half** whenever a phase advances, a suite is re-run, or the baseline
  moves. A status without a date and a basis is not a status.
- **Never upgrade a label** without evidence. `Implemented` → `Complete` requires
  implementation + tests + live verification + documentation (`CLAUDE.md` §2).
- **Never renumber** Phases 00–20. Free Pool, SabiChat, and the web platform are cross-cutting
  workstreams and stay unnumbered.
- **Where this map and the repository disagree, the repository and test evidence win** — then
  correct both this file and the document that drifted.

---

*End of Build Map. Part I describes what exists. Part II describes what may happen next and
who must authorize it. Neither part asserts release readiness.*
