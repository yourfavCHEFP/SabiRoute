# SabiRoute — Architecture Decision Record

**Status:** living document · **Last verified:** 2026-11-23 · **Branch of record:** `feat/sabiroute-routing-foundation`

This is the authoritative record for the shape of the system, the decisions that fixed that
shape, the roadmap milestones, and the gates that stand between the current tree and a
production claim. It exists because the README links here for three things it deliberately does
not carry itself: the architecture record, milestone status, and production gates.

**Evidence convention.** `[V]` verified by command output or file read · `[R]` reported by a
prior session or another agent, not re-derived here · `[U]` unverified. A number without a tag
is not a number. When this document and the repository disagree, the repository wins and this
document is wrong.

---

## 1. What SabiRoute is

SabiRoute decides **which deployment should be attempted**; LiteLLM executes the provider
request. That division is the load-bearing decision behind everything below: SabiRoute is a
routing and admission layer in front of an executor, not a provider client and not a proxy
rewriter.

The request path implemented today `[V]`:

1. Receive the client request.
2. Authenticate and authorize it (client key / admin key boundary).
3. Apply rate-limit and budget admission checks.
4. Classify the request and establish required capabilities.
5. Discover candidate deployments from the route policy.
6. Exclude candidates that fail capability, health, or policy requirements.
7. Select among eligible candidates (configured priority or measured scoring).
8. Execute through LiteLLM.
9. On retryable failure, fall back per the retry and eligibility rules.
10. Normalize the response and persist operational telemetry.

Free Chat (SabiChat) requests insert an explicit-allowlist gate between steps 6 and 7: only
mapped deployments stay eligible, fallback cannot leave the allowlist, and denials happen
**before** execution with stable reasons.

### Package layout `[V]`

49 files under `src/sabiroute/`:

| Package | Responsibility |
|---|---|
| `api/` | HTTP surface — `completions.py` (the request path and retry/fallback loop), `chat.py`, `admin.py`, `health.py`, `models.py`, `body_limit.py`, `deadline.py`, `shutdown.py` |
| `routing/` | `router.py` (selection), `policies.py` (`PolicyRegistry`), scoring |
| `providers/` | `base.py`, `litellm_client.py`, `registry.py` — **no** `healthcheck.py` (see ADR-002) |
| `security/` | API keys, budgets, quotas, accounting lineages, `store.py` schema ledger |
| `freepool/` | Free-pool eligibility and catalogue |
| `chat/` | SabiChat backend — sessions, conversations, messages |
| `monitoring/` | Trackers feeding admin endpoints |
| `intelligence/` | ML-assisted routing (gated, see ADR-004) |
| `config/` | `config.yaml` loader |
| `request_transform/`, `utils/` | Normalization and shared primitives |

---

## 2. Decisions

Each entry records what was decided, why, and what it forbids. The "forbids" line is the part
that matters — it is what stops a future session from helpfully undoing a deliberate choice.

### ADR-001 — Routing and execution are separate concerns

**Decision.** SabiRoute selects a deployment; LiteLLM performs the provider call. Every
attempt, including fallback attempts, routes through `Router.choose_deployment`.

**Reason.** Provider-specific behaviour stays in one executor. Routing logic is testable
without network access.

**Forbids.** Reaching past the router to call a provider directly, and letting a fallback path
bypass eligibility. Both would make routing behaviour unobservable from the request path.

### ADR-002 — There is no separate fallback engine, and no active health checker

**Decision.** The retry/fallback loop lives in `src/sabiroute/api/completions.py`. There is no
`FallbackEngine` and no `routing/fallback.py`. `providers/healthcheck.py`
(`ProviderHealthChecker`) was deleted after verification that nothing referenced it
`[V]` — `providers/` contains only `base.py`, `litellm_client.py`, `registry.py`. Runtime health
is the passive success/failure and cooldown registry in `routing/`.

**Reason.** Two implementations of "which deployment next" would drift. A health checker with
no caller is dead weight that reads as a feature.

**Forbids.** Reintroducing an active checker without a caller and a test, and describing health
monitoring as active — it is passive-only by design.

**Trap.** `cooldown_until = None` on an unhealthy deployment is a **permanent removal**, not a
reset. Only an *expired* deadline re-enters the half-open path. This cost a session to find; do
not "simplify" recovery by clearing it.

### ADR-003 — Unknown capability is never treated as verified support

**Decision.** A deployment whose capability metadata is unknown is not eligible for a request
that requires that capability. Only deployment-specific evidence in `docs/capabilities.md`
enables it.

**Reason.** Treating absence of evidence as support converts a metadata gap into a runtime
failure at the provider.

**Forbids.** Capability inference from model name, provider family, or configuration presence.

### ADR-004 — Deterministic scoring ships before ML scoring

**Decision.** `deterministic-v1` is live on measured routes. ML-assisted routing (Phase 13) is
gated: it must pass its own sub-gates before it can influence selection, and it does not exist
in the request path today.

**Reason.** A learned ranker over an unvalidated dataset is not an improvement, it is an
unmeasured regression.

**Forbids.** Wiring ML scoring into `Router.choose_deployment` ahead of the Phase 13 gates, and
citing synthetic benchmark output as live performance evidence.

### ADR-005 — SabiChat is a gateway client, not a parallel router

**Decision.** The SabiChat backend traverses the same numbered request path in process. It is a
client of the gateway.

**Reason.** A second routing implementation inside the product surface would diverge silently
and would not inherit admission, budget, or accounting behaviour.

**Forbids.** Duplicating eligibility or selection logic under `chat/`.

### ADR-006 — Schema evolves through an ordered additive ledger, never destructive migrations

**Decision.** Schema changes are additive revisions recorded in `sabiroute_schema_versions`. No
Alembic. No destructive change. `[V]` `SCHEMA_MIGRATIONS` in `src/sabiroute/security/store.py`:

```
0001-usage-source            sabiroute_request_usage.usage_source
0002-sabichat-backend        sabichat_users/sessions/conversations/messages
0003-shared-inference-switch sabiroute_shared_inference_policy
0004-user-quota-ledger       sabichat_quota_windows/reservations
0006-accounting-lineages     sabiroute_accounting_lineages + lineage_id columns
```

Schema **group** state is a separate concern and lives in the same ledger as
`0005-schema-groups:<core|full>` rows — 0005 is a group marker, not a table-adding revision.
Ownership is by declared inventory (`CORE_TABLES`, ten tables) rather than by name prefix,
because `sabichat_quota_*` belongs to core while the four `sabichat_*` product tables belong to
the product surface.

**Reason.** Re-running an additive ledger is idempotent, which makes a restore-and-replay
recoverable without a migration tool holding state.

**Forbids.** Adding a revision that rewrites or drops a populated column, and inferring table
ownership from the name.

### ADR-007 — Token estimation is text-only; cost appears only when calculable

**Decision.** Multimodal token estimation stays null. A cost figure is emitted only when it can
be computed from configured pricing.

**Reason.** An estimated cost that silently substitutes zero for "unknown" corrupts every
downstream budget and telemetry aggregate.

**Forbids.** Zero-filling an unknown cost or token count.

### ADR-008 — Scoring telemetry is process-local

**Decision.** Reliability and latency signals reset on restart. The request path does not read
history from the database.

**Reason.** A database read on the selection path couples request latency to database
availability for a routing hint.

**Forbids.** Presenting measured scoring as durable or cross-process. A restart is a cold start
by design; this is a known limitation, not a defect.

### ADR-009 — Admission denies before execution, with stable reasons

**Decision.** Rate-limit, budget, allowlist, and capability denials are returned before any
provider call, and each carries a stable machine-readable reason.

**Reason.** A denial after execution bills a provider call for a request that was never
admissible. A stable reason is what makes the denial testable and loggable.

**Forbids.** Best-effort execution that "tries anyway", and free-text-only denial causes.

---

## 3. Roadmap milestones

Twenty-one phases, numbered 00–20 `[V]`. Status vocabulary is the repository's own, and it is
strict: **Complete means implemented *and* tested *and* live-verified.**

| Phase | Scope | Status |
|---|---|---|
| 00 | Architecture & environment | Complete (as recorded) |
| 01 | Basic LiteLLM gateway | Complete |
| 02 | Provider expansion | In progress — three of fourteen aliases have runtime evidence |
| 03 | Model registry | Complete — `config/config.yaml` is the runtime catalog |
| 04 | Virtual models / policies | Complete — six route policies loaded and validated at startup |
| 05 | Fallback engine | Implemented + failure-injection verified; **not Complete** — no real provider failure |
| 06 | Health monitoring | Implemented — passive cooldown only (ADR-002) |
| 07 | Observability | Implemented — no stored failure-metric evidence |
| 08 | PostgreSQL | Complete (documented live run) |
| 09 | Auth & API keys | Complete |
| 10 | Budgets and rate limits | Implemented — rejection paths not on the live path |
| 11 | Capability-aware routing | Implemented — capability evidence missing for most deployments |
| 12 | Measured deterministic scoring | Implemented — `deterministic-v1` live; benchmark evidence synthetic |
| 13 | ML-assisted routing | In progress — live sub-gate passed; aggregate integrity failed; 13.3 blocked |
| 14 | Benchmarking | Planned |
| 15 | Admin dashboard | Planned |
| 16 | Private remote access / Tailscale | Planned |
| 17 | Security hardening | Planned (baseline controls maintained throughout) |
| 18 | Testing and regression | Planned — tests required throughout earlier phases |
| 19 | CI/CD | Implemented (definition + local execution) — hosted run not verified |
| 20 | Production architecture | Planned |

**Read the totals honestly.** Six phases are Complete, nine are Implemented (tested but not
live-verified), four are In progress, and five are Planned. By the repository's own definition,
**zero phases are Complete on live evidence of failure behaviour** — the tested core is real,
the live-evidence layer is thin.

### Route policies `[V]`

Six policies in `config/routes/`, all `strategy: measured`:

| Route | `max_attempts` |
|---|---|
| `cheap` | 1 |
| `coding`, `fast`, `reasoning`, `research` | 2 |
| `ultimate` | 3 |

`research` has been exercised on the live path. The rest have not.

---

## 4. Production gates

Nothing below is a formality; each gate can independently block exposure.

**Gate A — Phase 20 review.** Gates any public exposure. The container, CI, and Compose service
exist and are smoke-tested without providers `[V]`, but there has been no managed-database test
and no staging deployment.

**Gate B — one real provider failure (Phase 05).** Ten of ten direct injections and seven of
seven through a real LiteLLM Proxy pass, but none of them is a genuine provider failure. The
cheapest closure is a real 404 from a retired model id — no spend, no accounts.

**Gate C — Phase 13 owner sign-off.** Aggregate dataset integrity is invalid: one historical
feature/outcome count mismatch and one outcome without a feature snapshot, deliberately
unrepaired. 13.3 stays blocked until an owner signs off.

**Gate D — capability evidence (Phase 11).** Only specific deployments have runtime evidence;
most capability metadata is `unknown`, and ADR-003 means `unknown` is dark, not permissive.

**Gate E — managed PostgreSQL.** Migrations are validated against a disposable local
PostgreSQL 16 (fresh init, upgrade, idempotent re-run, backup/restore) but never against a
managed instance.

**Gate F — hosted CI.** The workflow is defined and every step has executed locally. A hosted
Actions run is not yet verified.

---

## 5. Evidence record — SabiChat browser session

The README states that the SabiChat browser UI "has no automated browser test suite —
interactive behavior was exercised in a real browser session during development". This section
is the record it points to, stated at exactly the confidence it deserves.

**What was exercised.** Sign-in, session-token lifetime, conversation creation, message send and
response render, and reload behaviour, driven manually against a running local gateway.

**What that is not.** It is not a regression test. It has no assertions, no fixtures, and it
does not run in CI. A behavioural regression would be caught by a human noticing, or by
`tests/test_sabichat_web.py` for the serving/contract layer only `[V]` — that file's own
docstring says interactive behaviour is "covered by the optional Playwright smoke procedure, not
by this file".

**Consequence, stated plainly.** "The UI works" rests on a manual session, and manual sessions
decay. `docs/local-validation.md` records the repeatable path so the claim can be re-derived
instead of remembered.

---

## 6. Known limitations in force

Carried from the README so this record is self-contained.

- **Aggregate dataset integrity is invalid** — one count mismatch, one outcome without a feature
  snapshot, deliberately unrepaired.
- **Training is blocked** — no outcome variation, incomplete temporal provenance, no usable
  chronological split.
- **Capability evidence is narrow** — most deployments' capability metadata is `unknown`.
- **Phase 12 evidence is synthetic** — warm live-routing performance is not established.
- **Scoring telemetry is process-local** (ADR-008).
- **Token estimation is text-only** (ADR-007).
- **SabiChat is interim-grade** — one memory-held service key re-minted on restart,
  single-process rate limits, fixed history/response caps, in-memory session token (reload signs
  out). Per-user gateway keys and quotas are explicit future work.
- **Deployment foundation, not production** — no managed-database test, no staging deployment.

---

## 7. Traps — each cost a session to find

1. **`cooldown_until = None` is permanent removal**, not a reset (ADR-002).
2. **Verify Claude attribution by parsing trailers, never by grep.** A commit body can contain a
   line beginning `Co-Authored-By:` as prose. Use
   `git log -1 --format='%(trailers:key=Co-Authored-By,valueonly)' <sha>`.
3. **Run tests in the worktree that holds the branch being pushed.** The primary checkout may be
   on a different branch and yields a different count.
4. **`CLAUDE.md` roadmap lines are column-padded.** Match on a prefix, not on equality.
5. **A shared LiteLLM Proxy carries deployment-failure state between requests** and can change
   which alias answers. Use a fresh proxy per scenario when measuring routing behaviour.

---

## 8. Changing this document

Update it in the same commit as any change to architecture, milestone status, or gate standing.
Never restate a figure without the command that produced it. If you remove a decision, say which
one replaced it in "Forbids" — a deleted constraint reads as a forgotten one.
