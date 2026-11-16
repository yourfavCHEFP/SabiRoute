# R6 T11 — R6.0 Closure, R6.1 Readiness & Implementation Authorization Preparation

**Status: T11 COMPLETE — R6.0 CONDITIONALLY READY; R6.1 NOT READY. NO IMPLEMENTATION AUTHORIZED.**

**Programme:** SabiRoute Build Archive
**Workstream:** R6 — Intelligent Input Optimization
**Role of record:** T11 autonomous investigator (read-only preparation)
**Mode:** Extended autonomous operation. **Implementation NOT AUTHORIZED. No approval granted, no G7 requested or granted.**
**Verified baseline:** `feat/sabiroute-routing-foundation` @ `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
**Baseline verified on:** 2026-11-03 (before investigation and after; §2, §23)
**Source documents (read, preserved intact, not modified):**
- `docs/r6-architecture-decision-pack.md` (R6.0 pack, untracked)
- `docs/r6-decision-resolution-and-approval-campaign.md` (resolution campaign, untracked)
- `docs/r6-t9-capability-recovery-review.md` (T9 report, untracked)
- `docs/r6-t10-decision-consolidation-and-freeze-preparation.md` (T10 report, untracked)
- Live tree `src/`, `config/`, `tests/` at HEAD `319a711` (static inspection; no execution except read-only `grep`/`sed`/`git show`; no provider calls; no installs)

**Files created by this task:** `docs/r6-t11-r6-readiness-and-implementation-preparation.md` (this file) — **one file, no others.**
**Files modified:** none. No source, config, dependency, migration, dataset, scorecard, or existing-doc modification. No code written. No tests run (static inspection only). No compression executed. No benchmarks run. No provider calls made. No packages installed. No commits, pushes, deploys, resets, cleans, stashes, prunes, or branch changes.

---

## 1. Executive Summary

**Question:** *What exactly prevents us from freezing R6.0 and starting R6.1, and what is the smallest evidence-backed path to both?*

**Answer.**

1. **R6.0 is CONDITIONALLY READY** (unchanged from T10). All architecture decisions are adjudicated and the consolidated target (§§8–15) is internally consistent. What remains is approvals plus specified evidence — not open design. The single R6.0 blockers are: owner written approval (BL-22), Track A engagement scheduling (BL-21/BL-24), and a documentation cross-reference defect corrected here (BL-25, no architectural impact).
2. **R6.1 is NOT READY.** T11 independently re-derived T10's partial-settlement defect (D1/BL-01) and found **four additional live defects** that T10's stated fix does not cover: budget-gated unknown detection (BL-02), no-usage success never flagged — including on the budget path (BL-03), a pre-attempt-loop `NameError` that converts budget denials into 503s and leaks quota reservations (BL-04), and dead compensation observability (BL-05). Each requires a source change; each is specified as a regression test plus a fix direction, but **no fix is implemented in T11**.
3. **The R6.1 foundation interface is now specified** (§8: nine contracts I1–I9, insertion point between budget reservation `:1309` and loop entry `:1345`, monotone-shrink as the load-bearing invariant). What is missing is not engineering clarity but **authorization artifacts**: there is no R6.1 design document in the repository (BL-26), scope (chat-completions-only vs SabiChat path) is undecided (BL-27), bypass authority is undecided (BL-32), and the Phase-13 telemetry interaction needs an explicit keep-out decision (BL-31, recommended: keep out).
4. **Telemetry architecture can freeze only as an explicitly conditional, not-implemented target.** The live system is inline, synchronous, fail-closed telemetry on the accounting row — the shape T10 rejected as Option C. Freezing "Option A" without that label would be a false release claim (§14, §16).
5. **The owner must decide 12 questions** (§18, grouped A–D). Nothing else requires the owner: 8 autonomous investigations are small, bounded, and listed with acceptance evidence (§21). Track A owns 7+1 sign-offs (§15).

No invariant is weakened. No proposal is presented as owner-approved except the mission-stated T8 acceptances. No implementation was performed.

---

## 2. Verified Repository Baseline

VERIFIED by direct inspection this session (main agent; subagent worktree caveat below):

| Item | Value |
|---|---|
| Branch | `feat/sabiroute-routing-foundation` |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` — matches expected baseline |
| Tracked modifications | none (`git diff --stat` and `--cached` empty; `git status` shows only `??` untracked lines) |
| Stash / resets / cleans | none performed, none needed |
| R6 pack / campaign / T9 / T10 | present under `docs/`, untracked, read, unmodified |
| `src/sabiroute/api/completions.py` | ~2,100 lines; retry loop entry `:1345` VERIFIED |
| `config/config.yaml` | 14 aliases (`:22–239`), zero pricing keys, `tool_use`/`structured_output: unknown` repo-wide VERIFIED |
| `tests/` | 55 test files present; **no tests executed** (read-only mandate) |
| This report | absent before this task, no conflict |
| Isolation worktrees | main checkout on-branch untouched; four harness-spawned `.claude/worktrees/agent-*` snapshots were checked out at `e4ddc8d` (pre-R3 skeleton, not the mission ref) — investigators read `319a711` via absolute path / `git show` instead; no mission files written there |

---

## 3. T10 Findings and Acceptance Status

T10's conclusions, reconstructed from the full report (not the terminal summary):

- **R6.0: CONDITIONALLY READY** (T10 §19: 17-criterion audit; PASS on 4, CONDITIONAL on 12, BLOCKED on Track A sign-off).
- **R6.1: NOT READY** (T10 §20: prerequisites — written R6.0 approval, Track A T1–T7 + Tier-1 estimator, S0–S5 interface definitions, config/migration decisions, B1 test subset, G7 — all unmet by design at freeze-preparation stage).
- **Implementation: NOT AUTHORIZED. No G7 requested.**
- **T8 owner-accepted decisions** (mission §2, T10 §4): D6, D8, D14, D10/D20, D18, D19, D21, D22, D23 — scoped strictly to stated text.
- **T9 adjudication A–H** (T10 §5): A (BM25 → narrowed b′ vendored scorer), B (tool-bearing → Class matrix, Class-2 deferred), C (structured quota → Tier 1 + Tier 3 accept, Tier 2 conditional), D (retry → CONFIRMED O2 + quota governor added), E (estimator → ladder as process), F (ordering → E3→E1→E2 staged), G (unknown settlement → fix accepted + reconciler, blind TTL rejected), H (telemetry → Option A conditional).
- **New T10 proposals T10-1…T10-7** (T10 §7): all RECOMMENDED/PROPOSED/CONDITIONAL; none owner-approved.

T11 disposition per T10 item: §§4–6 record accept / narrow / extend. Net changes T11 makes to T10: **(a)** four new settlement defects BL-02…BL-05; **(b)** documentation correction BL-25; **(c)** "no R6.1 design doc in repo" BL-26; **(d)** telemetry freeze re-framed as conditional-not-implemented (§14). Nothing in T10 is overturned; several T10 conditions are now more precisely specified.

---

## 4. Complete Blocker Register

Severity: Critical (wrong accounting / data loss), High (blocks R6.1 start or R6.0 signature), Medium (required before stage exit), Low (bounded investigation).
Type: evidence · owner-decision · external-approval · implementation-dependency · documentation.

| ID | T10 ref | Subject | Sev | Type | Smallest next step | Autonomous? | Acceptance evidence | Blocks R6.0? | Blocks R6.1? |
|---|---|---|---|---|---|---|---|---|---|
| BL-01 | §5 T9-G; §6 D23 | Quota partial-settlement hole (mixed known/unknown settles partial sum as complete) | Critical | implementation-dependency | Regression tests T11-B §6 items 1–2, then pass-unknown-into-`finish()` fix | No (fix needs Track A + G7) | Mixed-sequence tests green; `total_tokens NULL` on unknown; `settled_estimate` status | No (fix specified as prerequisite) | **Yes** |
| BL-02 | NEW (T11-B D2) | Unknown-usage detection is budget-gated (`:1573,:1627,:1693,:1812`); quota-only requests never set the flag, so T10's "pass the flag" fix is insufficient | Critical | implementation-dependency | Budget-independent `any_attempt_unknown` signal set on every attempt outcome incl. success | No | Quota-only mixed tests green without any budget row | No (specified) | **Yes** |
| BL-03 | NEW (T11-B D3) | No-usage success never flagged (`:1897–1911`, stream `:1795–1808`); budget path replaces estimate with partial sum, violating `docs/limits-and-usage.md:61–63` | Critical | implementation-dependency | Flag-on-success-without-usage + test T11-B §6 item 5 | No | Budgeted known-fail→no-usage-success holds estimate, 200 | No (specified) | **Yes** |
| BL-04 | NEW (T11-B D4) | `finish()` reads `attempted` (`:602`) before binding (`:1311`); pre-loop exits with quota held raise `NameError` → masked 503 + day-long quota leak | High | implementation-dependency | Bind `attempted` at admission (or guard); test T11-B §6 item 6 | No | Quota+denied-budget returns true denial code; zero leaked reservation | No (specified) | **Yes** |
| BL-05 | NEW (T11-B D5) | `cleanup_errors` (`:406`) and `ledger` (`:403`) written, never read; stuck reservations are log-lines only | Medium | implementation-dependency | Wire to metrics/admin or remove; reconciler alerting reuses it | Conditional (read-only spec done; change needs Track A) | Every stuck reservation operator-visible | No | **Yes** (ops) |
| BL-06 | §7 T10-5; §6 D10/D20 | Quota token governor absent (N·(in+n·M) overrun bound, T10 §5 T9-D) | High | implementation-dependency | Mirror `:1599–1608` behind `quota_reserved` | No (Track A surface) | Multi-attempt quota test: consumption ≤ reservation | No (specified) | **Yes** |
| BL-07 | §6 D19 | Tier 1 quota extras parity + `quota_request_unsupported` type + n>1 accounting note; budget path frozen | High | implementation-dependency | Gap-closure + distinct error type + budget-regression tests | No (Track A surface) | Extras-carrying quota request denied with named reason, never under-reserved | No (specified) | **Yes** |
| BL-08 | §7 T10-6 | In-message tool-key detection for classification/telemetry/bypass | High | implementation-dependency | Syntactic detector + bypass-direction tests | No (likely `completions.py`) | Tool-history request bypasses + is logged; no verbatim-forward to unverified deployment | No (specified) | **Yes** (Class-1 FULL claim) |
| BL-09 | §5 T9-B | Role-aware system/developer freeze prerequisite to any Class-1 FULL claim | Medium | implementation-dependency | Freeze semantics + byte-diff tests | No | System/developer byte-identical post-transform, or bypass | No | Partial (FULL claim only) |
| BL-10 | §7 T10-4 | Capability-verification prerequisite (≥1 deployment verifies `tool_use`/`structured_output`) | Medium | owner-decision + evidence | Runtime capability probe program | No | Verified-true deployment or Class-2 stays bypass | No | No (Class-2 only) |
| BL-11 | §7 T10-1 | SDK-coupling exception evidence (import timing + env-diff + startup cost) | Low | evidence | ~10-min sandbox throwaway `import litellm` timing | **Yes** | Numbers recorded; rule stands unless evidence passes | No | No (R6.4 only) |
| BL-12 | §21.3 | `compress()` null-crash runtime proof (isolated `stub_message({content:None})`) | Low | evidence | ~5-min scratch interpreter call | **Yes** | Crash confirmed or refuted; B1 fixture updated | No | No |
| BL-13 | §21.5 | Service-key budget row (quota-gap reachability) | Low | evidence | Seed config / admin read | **Yes** | Budget-row presence recorded; §11 reachability closed | No | No |
| BL-14 | §21.6/21.7 | Streaming `GeneratorExit`/disconnect settlement guarantee (T11-B scenario 7 hazard: no `BaseException` arm in `stream_body`) | High | evidence then implementation-dependency | Real-disconnect test vs fake ASGI server | **Partial** (test design autonomous; fix needs Track A) | Disconnect finalizes row + terminal reservation in all close paths | No | **Yes** (test must exist) |
| BL-15 | T11-B §5.8 | Budget reservation schema has no terminal marker (`store.py:433–446`: no status/`updated_at`); reconciler cannot distinguish settled-at-estimate from never-settled | High | implementation-dependency | Additive status column (+`settled_estimate`) migration spec | No (migration = Track A) | Marker present; reconciler spec executable | No | **Yes** (reconciler) |
| BL-16 | §6 D14; §15 | Telemetry Option A freeze must be conditional + explicitly not-implemented (live shape is inline/sync/fail-closed) | High | owner-decision | ADR stating target-vs-interim + migration prerequisites | No | Signed ADR or inline-redesign decision | **Yes** (freeze honesty) | Partial (R6.7 writes) |
| BL-17 | §7 T10-7 | Non-blocking write convention + failure-proof test | Medium | implementation-dependency | Convention spec + test (telemetry failure ⇒ request unaffected) | No | Proof test green | No (specified) | **Yes** |
| BL-18 | §7 T10-3 | Null-content hardening for any pre-provider transform | Medium | implementation-dependency | Crash fixtures in B1 + guard code | No | Null-matrix green | No (specified) | **Yes** |
| BL-19 | §7 T10-2 | Multilingual scoring limitation + adversarial corpus (Yoruba/Arabic/CJK/emoji) | Medium | external-approval (Terminal D) + evidence | Corpus + coverage expectations | Partial | Corpus versioned; claims exclude non-Latin until proven | No | No (R6.6) |
| BL-20 | §17; §20 | E3 integrity harness + R6.1 B1 subset (placement, byte-identity, bypass, null-crash, retry-identity, quota-governor, mixed-settle, unknown-break, idempotency, non-blocking) | High | implementation-dependency | Harness built under R6.1 authorization | No | E3 green | No | **Yes** |
| BL-21 | §18 | Track A sign-off T1–T7 + Tier-1 estimator | High | external-approval | Sign-off requests issued per §15 matrix | No | Written sign-off per item | **Yes** (sign-off outstanding) | **Yes** |
| BL-22 | §19 | Owner written R6.0 architecture approval | High | owner-decision | Decision package §18 group A | No | Written approval of §§8–15 + Tier-1 as integrity work | **Yes** | **Yes** (gates G7) |
| BL-23 | §20 | G7 separate R6.1 implementation authorization | High | owner-decision | G7 request after BL-22 + BL-21 scheduled | No | Written G7 scoped to §17 units | — | **Yes** |
| BL-24 | §19 | Terminal B/C/D/E reconciliation (O2 arithmetic, benchmark/corpus, red-team) | Medium | external-approval | Prompts in campaign §13 reused; schedule recorded | No | Reports or scheduled prompts | Conditional (schedule ≥) | No |
| BL-25 | §24 | T10 "18 invariants (§7)" cross-reference defect — §7 holds T10-1…T10-7, not invariants | Low | documentation | Correction recorded in §16 of this report | **Yes (done)** | §16 authoritative mapping | No | No |
| BL-26 | NEW (T11-C Q1) | No R6.1 design document exists in repo (`docs/compression-discovery-packet.md` absent; no transform vocabulary in `src/`) | High | documentation + owner-decision | Adopt §8 of this report as draft foundation contract for approval | Partial (draft done) | Owner-approved foundation contract | **Yes** (nothing to approve) | **Yes** |
| BL-27 | NEW (T11-C Q2) | Scope: `/v1/chat/completions` only, or also `api/chat.py` (SabiChat path, own admission+store) | Medium | owner-decision | Scope ruling | No | Stated scope in contract | No | **Yes** |
| BL-28 | §6 D21 | B2 entirely unmeasured; all 14 aliases UNKNOWN; no pricing anywhere | Medium | evidence | Paired-row census + pricing decision (owner for byok/paid) | Partial | Census numbers; ladder positions unchanged until evidence | No | No (claims only) |
| BL-29 | §21.2 | Proxy `tools`/`response_format` forwarding fidelity | Low | evidence | Proxy version/config read + one invalid-key validation call (~20 min) | **Yes** | Fidelity recorded | No | No |
| BL-30 | §21.10 | byok/paid semantics + billing-source scope | Medium | owner-decision | Conversation | No | Scoped definitions | No | No |
| BL-31 | NEW (T11-C Q4/I4) | Phase-13 interaction: does transform metadata enter telemetry in R6.1? (Recommended: no — `extra="forbid"` schema, T11-C I4) | Medium | owner-decision (T8 advice) | Keep-out ruling | No | Explicit keep-out in contract | Conditional | **Yes** |
| BL-32 | NEW (T11-C Q5/I7) | Bypass authority: operator-only vs trusted-service signal (caller-controlled routing input risk) | Medium | owner-decision | Authority ruling (recommended: operator-only, per-route, default-off) | No | Authority stated + malformed-signal tests | No | **Yes** |

No artificial blockers. No genuine blocker downgraded: BL-01…BL-04 are Critical and stay Critical; R6.0 stays CONDITIONAL (not READY) while BL-22/BL-21/BL-24/BL-26 are outstanding.

---

## 5. R6.0 Freeze Conditions

Per mission §4, each with freeze verdict (FREEZE-OK = freezable with implementation disabled; CONDITIONAL = freezable with recorded prerequisite; BLOCKED = stops signature):

1. **Decision register completeness — CONDITIONAL.** D1–D23 + T10-1…10-7 adjudicated (T10 §§4–7; §4 here). Gap: T8 register still uncommitted in tree (T10 §19.1); T11 correction BL-25/BL-26 recorded in §16.
2. **T8 owner-accepted decisions — FREEZE-OK.** D6/D8/D14/D10/D20/D18/D19/D21/D22/D23 scoped acceptance stands; T11 re-verified the underlying code facts (capability gate §10, governors §12, settlement §7).
3. **T9 adjudication — FREEZE-OK.** A–H reconciled; A/C rejected paths stay rejected; Class-2 deferred; quota governor added. Extended (not overturned) by BL-02…BL-04.
4. **Architectural invariants — FREEZE-OK with §16 mapping.** Authoritative sets: T9 §4 (15 architectural invariants) + pack §11 (owner R6-S01…S20). T10's "18 (§7)" is a wrong pointer, not a wrong decision.
5. **Stage ownership — FREEZE-OK.** S0–S5 owners/interfaces per T10 §8; T11 adds the foundation placement (§8: between `:1309` and `:1345`) and ownership rule T10-1.
6. **Request lifecycle placement — FREEZE-OK.** VERIFIED order: admission `:374` → … → classification `:966` → eligibility `:1166` → budget reservation `:1216` → loop `:1345`. R6.1 insertion point unambiguous (§8–§9).
7. **Budget and quota policy — CONDITIONAL.** Tier 1 + quota governor specified (T10 §§12–13); implementation + Track A pending (BL-06, BL-07).
8. **Retry and fallback policy — CONDITIONAL.** O2 confirmed; quota governor + unknown-break specified; code change pending (§12, BL-01…BL-04, BL-06).
9. **Unknown-usage settlement — CONDITIONAL.** Fix + bounded reconciler specified (§7, §14 of T10); hole reproduced, not closed; extended by BL-02…BL-05.
10. **BM25 integration policy — CONDITIONAL.** (b′) vendored scorer, disabled-built R6.4, six enablement proofs; construction + enablement gates pending (§10, BL-11, BL-12, BL-19).
11. **Tool-bearing eligibility — CONDITIONAL.** Class matrix stands; T10-6 detection + role-freeze + T10-4 prerequisite pending (§10, BL-08…BL-10).
12. **Estimator confidence policy — FREEZE-OK.** Ladder + labelling + auto-demotion as process; all aliases UNKNOWN (re-verified §14); no code grants calibration.
13. **Benchmark design — CONDITIONAL.** B1 additions + corpus deltas specified (§14, §17); Terminal D reconciliation pending (BL-19, BL-24).
14. **Telemetry architecture — CONDITIONAL (BL-16).** Option A freezable only as conditional, not-implemented ADR; convention + table pending (§14).
15. **Track A dependencies — BLOCKED (BL-21).** Matrix recorded (§15); sign-off not obtained; silence is not approval.
16. **Deployment-tokenizer policy — CONDITIONAL.** Policy C + compat-matrix gate; matrices pending (BL-19).
17. **Rollout and release gates — FREEZE-OK.** Default-off + kill-switch + G4/G5/G7 positions preserved. Note: G4/G5/G7 have zero tree occurrences (T11-F §5.4) — mission/campaign must supply definitions; existing repo gates are A–E (`reports/remediation-roadmap-and-gates.md:30-50`).

**Architecture freeze vs implementation authorization:** freeze approves the target and its constraints (§§8–15 + prerequisites); it authorizes zero file changes. R6.1 needs the separate G7 (BL-23). No implementation detail beyond §17's blueprint needs to be final before freeze; the deferred items are listed, not hidden.

---

## 6. R6.1 Implementation Conditions

R6.1 may start **only** when all of the following hold (each names its blocker):

1. Written R6.0 owner approval (BL-22) **and** scoped G7 authorization (BL-23).
2. Track A sign-off on T1–T7 + Tier-1 estimator, or written deferral per item (BL-21, §15).
3. Adopted foundation contract: §8 (I1–I9) approved **plus** rulings on scope (BL-27), bypass authority (BL-32), Phase-13 keep-out (BL-31), monotone-shrink permanence (T11-C Q7 — recommended: never expand without re-baselining reservation), and per-attempt re-derivation forbidden (recommended: forbid).
4. Settlement-defect specifications accepted as R6.1 must-fix with regression tests first: BL-01, BL-02, BL-03, BL-04 (§7.6 items 1, 2, 5, 6 fail today by inspection).
5. Quota governor (BL-06) + Tier 1 estimator (BL-07) + T10-6 detection (BL-08) + null-hardening (BL-18) + non-blocking convention (BL-17) in the R6.1 unit plan (§17).
6. Role-aware freeze decision for the Class-1 FULL claim (BL-09); otherwise R6.1 ships Class-1-gated-behind-bypass for system/developer-role traffic.
7. Budget schema terminal marker decision (BL-15) if the reconciler is in R6.1 scope; else reconciler explicitly deferred to R6.7 with stuck rows visible.
8. Streaming-disconnect test (BL-14) designed; `GeneratorExit` hazard adjudicated by runtime test under R6.1.
9. E3 harness + §17 B1 subset scoped as the R6.1 exit gate (BL-20).

---

## 7. Accounting and Settlement Audit

Independent T11-B re-derivation (absolute-path static inspection at `319a711`; no execution, no provider calls). All claims cite `src/sabiroute/api/completions.py` (C:) and `src/sabiroute/security/store.py` (S:).

### 7.1 Execution path (VERIFIED)

Admission: pilot quota gate C:1069–1163 (`check_and_reserve_quota` C:1096–1104, `quota_reserved=True` C:1161) → budget reservation C:1213–1309 (`budget_reserved=True` C:1308). Loop state: `attempted` C:1311, `actual_usage_parts` C:1314, `provider_usage_unknown=False` C:1316. Collection: `_actual_tokens` C:239–250; `_sum_actual_tokens` C:253–264 **skips `None` per column, returns partial sums**. `finish()` C:542–679: in-flight barrier C:555–562 → budget reconcile-or-release C:563–595 → quota settle-or-release C:596–620 → finalize event C:633–679. Store: `settle_quota` S:1343–1390 (`settled = actual or estimate` S:1369; **any non-`None` treated complete**; no `settled_estimate`); `reconcile_budget` S:1213–1247 (`None` holds estimate; non-`None` replaces); both transitions status-guarded (idempotent, VERIFIED). No reconciler exists (only unrelated `reconcile_lineage_budgets` S:645+; zero sweeper/TTL hits repo-wide).

### 7.2 Ten adversarial scenarios

| # | Scenario | Verdict |
|---|---|---|
| 1 | Known → unknown | **VERIFIED DEFECT** (quota settles partial; budget correct only when failure path sets flag) |
| 2 | Unknown → known | **VERIFIED DEFECT** (no-budget: flag never set C:1573; existing test asserts nothing about `consumed_tokens`) |
| 3 | Multiple known | CORRECT (sums; both heads) |
| 4 | All unknown | CORRECT (estimate held; covered by `test_unknown_usage_holds_estimate`) |
| 5 | Timeout/deadline | Partial — all-unknown correct; mixed defective on quota |
| 6 | Disconnect (non-stream) | Partial — event correct (`tokens=(None,None,None)`), quota settle still partial; flag not set on this branch |
| 7 | Streaming cancel | Partial + **UNRESOLVED `GeneratorExit` hazard**: `stream_body` has no `BaseException` arm — Starlette `aclose()` may bypass `finish()` entirely → unfinalized row + held reservations (framework-path dependent; needs real-disconnect test) |
| 8 | Duplicate settlement | SAFE (status guards S:1359/S:1404; guarded finalize S:1518) |
| 9 | Persistence failure at settlement | **VERIFIED GAP**: settle-raise → 503 + leaked reservation; finalize-raise → 503 after settlement with permanently unfinalized row |
| 10 | Crash recovery | **VERIFIED GAP**: no worker; quota bounded by UTC day (`quotas.py:21–25`), budget stale rows persist unboundedly; no alert/metric |

### 7.3 Defects (BL-01…BL-05; D1 = T10-D23 reproduced, D2–D5 new)

- **D1 (BL-01): quota settlement ignores unknown usage — VERIFIED.** C:596–620 never consults the flag; C:603 partial-sums; S:1369 treats as complete. Comment C:597–599 describes unimplemented intent.
- **D2 (BL-02): unknown detection is budget-gated — VERIFIED, new.** Set-sites C:1573, C:1627, C:1693, C:1812 all require `budget_reserved` (except failure-body-without-total C:1571–1572). Quota-only Free Chat shape never sets the flag. **T10's "pass the flag into `finish()`" is therefore insufficient.**
- **D3 (BL-03): no-usage success never flagged — VERIFIED, new, affects budget path too.** C:1897–1911 + stream C:1795–1808 append-only; mixed known-fail→no-usage-success replaces the estimate with the partial sum (S:1233–1236), violating `docs/limits-and-usage.md:61–63`.
- **D4 (BL-04): `finish()` reads `attempted` before binding — VERIFIED, conditionally reproducible.** `:602` vs `:1311`; pre-loop exits with quota held (`:1171,:1180,:1189,:1205,:1272,:1282/:1299`) raise `NameError` → caught at `:623` → masked 503 `quota_unavailable` + day-long leak. Deterministic when service key carries a budget and a budget denial fires; no test combines quota admission with budget denial.
- **D5 (BL-05): dead observability — VERIFIED.** `cleanup_errors` C:406 appended 9×, never read; `ledger` C:403 never read (`_compensate_all` C:681–721 uses flags).

### 7.4 Required settlement contract (exact)

1. One quota + one budget reservation per logical request, pre-execution; retries never re-reserve. 2. Exactly-once terminal machine: quota `reserved → settled | settled_estimate | released`; budget `reserved → reconciled | released` with explicit marker; terminal rows immutable. 3. Settlement basis: no attempt → release; all-known → sum of actuals; **any-unknown → full original estimate (unknown wins)**; unknown = missing body/usage/total, cancel, deadline, exception, stream-without-usage, no-usage success. 4. Partial actuals are telemetry only; request-level `total_tokens` NULL with incompleteness marker on any-unknown. 5. Unknown detection budget-independent (BL-02 fix). 6. Every pre-execution exit releases (BL-04 fix). 7. Settlement failure fails closed (held + identifiable, never zero). 8. No fabricated values, zero-fill, or inferred usage.

### 7.5 Bounded reconciler requirements

Settle-only; evidence-based release only (no-stale-proof → settle-at-estimate; **no blind TTL**); N/pass (100–500) oldest-first; jitter + single-runner (`FOR UPDATE SKIP LOCKED`/advisory lock); status-guarded idempotency; per-row/pass counters + admin visibility (reuse `cleanup_errors`); quota within `window_start` day, budget within its window; **schema prerequisite: budget needs a terminal marker first** (BL-15).

### 7.6 Smallest regression-test specification (no code; failing-today items marked ★)

1. ★ Mixed known→unknown quota (estimate wins; event NULL). 2. ★ Mixed unknown→known quota (same). 3. Multiple known control. 4. All-unknown control (keep). 5. ★ Budgeted known-fail→no-usage-success holds estimate, 200. 6. ★ Quota-held + budget-denied returns true denial + zero leak. 7. Streaming cancel mixed + real-disconnect `GeneratorExit` test. 8. Duplicate-settlement control. 9. Settlement/finalize-raise → 503 + identifiable row. 10. Reconciler one-pass contract (N=1, stale-only, estimate, no-op rerun, counts emitted).

---

## 8. Optimization Foundation Interface Blueprint

T11-C reconstruction (worktree was on `main` `e4ddc8d`; all anchors re-verified from `319a711` via `git show`): **no R6.1 design document and no transformation vocabulary exist in the tree** (VERIFIED negative grep for `canonical|effective|immutable|optimization|bypass` in `src/`; `docs/compression-discovery-packet.md` absent). What follows is the proposed contract derived from the actual code — recommended for adoption as the draft foundation contract (BL-26).

### 8.1 Proven lifecycle order (actual, not assumed)

Ingress (`body_limit` 1 MiB → `DeadlineMiddleware` 300 s; `main.py`, `api/body_limit.py:16–47`, `api/deadline.py:13–14,50–90`) → auth (`security/auth.py:68–95`) → handler (`completions.py:301–321`) → **BYOK guard** `:322–346` → message caps `:348–363` → admission usage row `:365–383` → rate limit `:830–873` → target/candidates `:890–905` → extras projection `:901–919` → budget estimate `:922–965` → **classification** `:966–971` → Free Pool gate `:997–1066` → **quota reservation** `:1069–1163` → eligibility `:1166–1177` → **budget reservation** `:1195–1309` → **R6.1 INSERTION POINT** → loop entry **`:1345`** → per-attempt selection `:1387–1395` → snapshot `:1433–1502` (`dataset.py:128–247`) → provider `:1520/:1539` (`litellm_client.py:81–84/:143–147`) → settlement `finish()` `:542–680`. Two material facts: admission/rate-limit precede classification (a rejecting classifier leaves a usage row — deliberate, `:373–374`); nothing named "effective construction" exists — `payload.messages` travels unmodified to the provider body.

### 8.2 Proposed interfaces (smallest architecture: new `src/sabiroute/request_transform/` — value objects + pure functions, ~250 LOC, no registry, no I/O, no provider adapters in R6.1)

| ID | Contract | Input → Output | Owner | Mutability | Failure | Timeout/Cancel | Limits | Telemetry (R6.1: none in snapshot) | Tests |
|---|---|---|---|---|---|---|---|---|---|
| I1 | Immutable original | Request → `FrozenOriginal` deep-frozen copy at `:919` | API layer | Structurally immutable (new list of new dicts — current client shallow-copies, STATIC-ANALYSIS FINDING) | Total (input Pydantic-validated) | n/a (pure) | 256 msgs / 500k chars / 1 MiB | None (never persist text — `dataset.py:52–56,129`) | Frozen-ness, deep-copy isolation, byte-equality pre/post |
| I2 | Canonical representation | FrozenOriginal → deterministic `CanonicalRequest` | R6 module | Frozen | `CanonicalisationError` → fail-to-original | Pure CPU; bound by request deadline only | Output ≤ input; **250 ms / 2× bytes budget must be specified** | None | Determinism, idempotence, size non-expansion, unsupported-shape failure |
| I3 | Effective request | Canonical + policy + capabilities → `EffectiveRequest` (sole provider reader) | R6 module | Frozen; **one per logical request — re-derivation per attempt forbidden** | Never raises (I9) | Pure; request cancel unaffected (no awaits) | **Monotone-shrink: output ≤ original** — load-bearing for reservation `:1199` | Counts + hashes only | Disabled-policy byte-equality, monotone-shrink property, capability preservation, provider-payload snapshot |
| I4 | Transformation metadata | (original, effective, policy, rules) → immutable `TransformationRecord` (ids/versions/counts/hashes/`fallback_reason`; never text) | R6; read-only to API | Frozen tuple | Internal inconsistency → still fail-to-original; record not written | n/a | Scalar-only | **BLOCKED: `PreRoutingFeatureSnapshot` is `extra="forbid"` 1.0/1.1 — R6.1 must emit no snapshot fields (recommendation a); schema-1.2 question deferred** | Redaction, schema-exclusion (no transform keys in snapshot JSON) |
| I5 | Optimization policy | Config/route YAML → `OptimizationPolicy` (`enabled=false` default, strategy/version/`max_ratio`, per-route override) | Config layer, loaded once at startup | Frozen after load (mid-request flip would split one reservation across two requests) | Invalid → startup failure (existing convention) | n/a | `max_ratio` bounds shrinkage; no expansion knob | id/version in I4 only | Default-disabled, unknown-strategy startup failure, route precedence, frozen-after-load |
| I6 | Capability checks | Effective + selected deployment → preserved bool | R6, reusing `capabilities.py:11–60` (no new enum) | Pure | Dropping `tool_use`/`structured_output`/`vision`/multimodal → hard fail to original (eligibility ran at `:1166` on the original) | n/a | — | None in R6.1 | Property: every `classification.required_capabilities` still required post-transform; classification keeps reading the original |
| I7 | Explicit bypass | Operator policy (+ optional documented request signal) → immutable `BypassDecision` evaluated once pre-`:1345` | API layer | Immutable per request | Malformed signal ⇒ ignore signal, use operator default (cf. `:914` strict-marker pattern) | No awaits | — | Operational logs only, never the snapshot | Default-off, operator-on, caller-signal-rejected, malformed-ignored |
| I8 | Validation | Effective → `ValidatedEffective` or failure | R6 module | — | Failures degrade to original, **never 4xx** (no "our optimiser rejects your request" category exists) | — | Same caps as I1 | None | Structural validity, no reintroduction of `:323`-forbidden fields, size monotonicity |
| I9 | Fail-to-original | Any I1–I8 exception → original continues | Call-site guard `:1309–:1345` | — | Swallow-and-degrade (fallback is the tested path); log once at warning with `redact_secrets` | **`CancelledError` must propagate** (ledger `:385–420`, `_compensate_all` `:690–721` depend on it) | — | `fallback_reason` + one counter | Exception-injection ⇒ byte-identical payload; `CancelledError` passthrough; no reservation leak |

### 8.3 Placement rule

Before R6.1: admission, quota reservation, eligibility, budget reservation. R6.1 constructed **once, immediately before `:1345`**. After: per-attempt selection (must not read effective in R6.1), provider call (sole consumer), settlement on provider actuals (savings appear naturally in actuals, never in estimates).

### 8.4 What must never change (R6.1)

BYOK position/scope `:322–346`; classification reads original `:968`; router filter order capability→health→attempts (`router.py:177–231`); admission sequencing (usage `:374` → rate-limit `:850` → quota `:1097` → budget `:1216`); default pass-through byte-fidelity; `attempted` semantics `:1505`; Free Pool narrowing `:997–1066`; `finish()`/`_cancelled_finish()` ledger contract; Phase-13 schema immutability for R6.1.

---

## 9. Lifecycle and Execution Safety

- **Reservation basis (O2):** `reserved_tokens = estimated_input + max_tokens` (C:1199) from the original estimate (C:935); `estimated_cost` (C:1201). VERIFIED.
- **Cost governor** C:1406–1432 (remaining-cost input/output haircut; fail-closed on unpriceable). **Token governor** C:1599–1608 (monotone `max_tokens` shrink; `remaining <= E` break). Both gated on `budget_reserved`; quota has neither (BL-06). VERIFIED.
- **`max_attempts`:** per-policy 1–3 (cheap=1, default 2, several routes 3; `routing/policies.py`, C:163 alias default `max_attempts=2`). VERIFIED.
- **Unknown-break:** `if not retryable or (budget_reserved and provider_usage_unknown): break` (C:1601) — budget only; quota path needs the mirror (BL-02/BL-06). VERIFIED.
- **300-s deadline:** `DEFAULT_REQUEST_DEADLINE_SECONDS = 300.0` (`api/deadline.py:13`); ASGI middleware cancels downstream (`deadline.py:50–90`); endpoint distinguishes deadline-vs-client-cancel via published `sabiroute_deadline_at` (C:178–193, C:1612–1656, streaming C:1747–1817). VERIFIED.
- **Cancellation:** no `to_thread` on the provider path; store work runs on `BoundedStoreExecutor` (default 32, fair `_LoopSemaphore`; cancel-while-wait starts nothing; cancel-while-run keeps running — `store_executor.py:1–140`). VERIFIED. R6.1 pure functions need no executor; any future async stage needs bounded pool + input caps + `optimization_timeout` (pack D13), specified in §17 U4.
- **Shutdown/drain:** lifespan in `main.py:88`; shutdown router `api/shutdown.py`. VERIFIED present; full drain-behavior proof is an R6.1 test item (§17 U4).
- **Streaming terminal invariants:** completed→200 + usage appended; interrupted→`provider_usage_unknown` (budget-gated, BL-02) + 499/503/502; `finish()` with `release_budget=not attempted`. `GeneratorExit` bypass hazard UNRESOLVED (BL-14). VERIFIED by inspection.

**R6.1 without changing retry/settlement semantics: yes for the foundation** (I1–I9 are pre-loop, pure, fail-to-original). The settlement fixes (BL-01…BL-04) change settlement code but preserve its contract — they are the R6.1 prerequisite, not a redesign.

---

## 10. Capability Recovery Boundaries

- **BM25:** minimum adapter = SabiRoute-owned select-and-drop with **vendored/reimplemented scorer** (T10-1; zero SDK imports on the request path VERIFIED). Safety: no stock stubbing, no retrieval instructions, no content telemetry, no cache exposure, bounded execution, fail-to-original; ASCII-tokenizer limitation stands (non-Latin claims excluded until proven, T10-2); null-content hardening mandatory (T10-3). Boundary freezable pre-implementation (six enablement proofs + D11 matrix + D8-pairing independence); construction R6.4, enablement post-v1. No implementation in T11.
- **Tool-bearing:** eligibility boundary unchanged — Class 1 eligible; Class 2a CONDITIONAL (capability verification + five proofs + role-freeze; not enabled); Class 2b/3a–3d mandatory bypass. Capability-gate evidence re-verified: `evaluate_candidates` excludes on unknown (`router.py:195–210`); all deployments declare `tool_use`/`structured_output: unknown` (config.yaml; zero `true` repo-wide). In-message tool history invisible to classification — documented gap (BL-08), not a grant.
- **Structured quota estimation:** Tier 1 (text baseline + quota extras parity + `quota_request_unsupported` + quota-estimate recording) + Tier 3 (explicit refusal) accepted as metering-integrity fixes; Tier 2 capped-structural CONDITIONAL on telemetry-join audit caps. Never-zero rule; n>1 output-multiplier accounted (BL-07).
- **RTK-inspired state:** per-tenant namespace + TTL + policy/model/context in key; no cross-tenant semantic cache in v1 (pack D4 OPEN). R6.2 contract; not R6.1.
- **Caveman:** deterministic rules-based, natural-language spans only, protected-class bypass, fail-closed validation (pack D5 OPEN). R6.3 contract; not R6.1.
- **R6.1 vs later:** R6.1 owns I1–I9 + S0 eligibility gate + Class-1-only gating + Tier 1 bookkeeping + settlement fixes. R6.2/6.3/6.4 own RTK/Caveman/BM25 constructions (all disabled until gated).

---

## 11. Estimation and Quota Policy

- **Basis:** original request governs admission/reservation/retry arithmetic. Effective-request figures are forecasts only (shadow, clamped ≤ E, never control).
- **Estimator:** `estimate_input_tokens` (`security/budgets.py:16–40`): compact UTF-8 JSON + 16/msg + 4; text-only, scalar-metadata-only, else `UnsupportedBudgetRequest` (fail-closed). Unversioned; upper-bound claim untested (all UNKNOWN, §14).
- **Budget admission** (C:922–965): `max_tokens` required; unsupported-parameter allowlist (`top_p`, penalties, `stop`, `stream_options`); mislabeled-shape errors rejected with `budget_request_unsupported`. Frozen — Tier 1 does not touch it.
- **Quota admission** (C:1069–1163): same estimator; shape rejections currently mislabeled `quota_max_tokens_required` (BL-07: new distinct type); **no extras check** (gap; Tier 1 closes it).
- **Tiers:** Tier 1 text + extras parity + recording; Tier 2 capped structural (framing + depth/width/byte caps; trip→Tier 3; version `quota-est-v1`; canonical-JSON determinism); Tier 3 explicit refusal with reason pointer (counted distinctly from `quota_exceeded`).
- **Labelling:** `estimated_*` vs `provider_reported_*`/`actual_*` vs `billed_*` (never emit the last); `*savings*` forbidden until BOUNDED+. D18: uncomputable/invalid/over-original effective estimates → reject to original, never clamp.

---

## 12. Retry and Fallback Policy

O2 confirmed: eligibility and caps pinned to original-estimate basis; savings never buy attempts or headroom; settlement on actuals. Budget token governor (C:1599–1608) + cost governor (C:1406–1431) VERIFIED. **New:** quota token governor (BL-06, mirror behind `quota_reserved`); unknown-break extended to quota (BL-02). Unknown: break regardless of head type; settle-at-estimate; no control use of validated estimates beyond clamped shadow logging; fungible pools rejected. `max_tokens` mutation ratchets down all future attempts (never increases). Fallback reuses the same effective object; no per-attempt re-optimization (D12 structural). Tokenizer-agnosticism per stage or bypass.

---

## 13. Deadline and Cancellation Policy

300-s ingress-to-completion deadline preserved end-to-end: middleware publishes `sabiroute_deadline_at` and cancels downstream at expiry (`api/deadline.py`); retry loop re-checks per attempt (C:1346–1352); attempt handler classifies deadline-vs-cancel via the published instant (C:1612–1660); streaming distinguishes `deadline_expired`/`client_cancelled`/`stream_interrupted` (C:1747–1820) with health marks only for genuine provider failures. New optimization capacity (if any beyond pure functions) must consume the remaining deadline budget, never extend it; `optimization_timeout` is a distinct failure category from provider `deadline_exceeded`. Cancellation always propagates (`CancelledError` never swallowed by I9 or `finish()` paths — VERIFIED pattern C:1362, C:1480, C:1609–1620). Optimization execution bounded and off the event loop (S13); `to_thread` non-preemption documented as the reason for a bounded pool (§9).

---

## 14. Benchmark and Telemetry Readiness

Independent T11-F static inspection at `319a711` (git objects; no runs; no fabrication per `docs/phase13-natural-observation-v0.1.md` §3).

### 14.1 B1 (offline/mechanical)

Substantial base (55 test files): tenant isolation strong (`test_r3_db_isolation`, `test_identity_propagation`, `test_quota_summary`); accounting strong (`test_accounting_lineage`, `test_phase10:515–726`, `test_user_quotas` 30 tests); resource limits strong (`test_request_limits`, `test_store_executor`, `test_deadline`, rate-limit suites); retry census good at stub/proxy boundary (`test_proxy_attempt_census`, `test_r5_deterministic_reliability`, `test_fallback_injection`) — but provider retries are invisible to telemetry (`docs/proxy-retry-visibility.md:36–60`), so retry-cost consistency is unproven. **Fail-to-original is false today** (contract is fail-closed: finalization failure replaces the result, C:651–676). Of 8 specified B1 additions: null-crash partial, ASCII-multilingual absent, tool-atomicity absent, stub/cache-absence partial, frozen-subtree absent, order-conformance present-in-distributed-form, shadow-E′ absent, non-blocking contradicted (writes awaited on the response path — loop not stalled, response blocked). E3 harness absent (`scripts/benchmark.py` 42-byte placeholder); E1 live (deterministic-v1, synthetic evidence only); E2 absent.

### 14.2 B2 (provider-measured)

Entirely unmeasured (correctly). Captured-when-returned: prompt tokens + usage (`_actual_tokens` C:239–256, nullable, never substituted). Partial: latency (total/attempt only; no TTFT split; routing overhead synthetic). Unavailable: cost/task (zero pricing keys in config), all per-alias error metrics (bias/MAE/RMSE/p50/p95/p99/P(est<actual)/unknown-rate — no aggregator pairs estimate with actual).

### 14.3 Estimator ladder

Formula unversioned; docstring upper-bound claim untested. Promotion evidence: UNKNOWN (default) → UNCALIBRATED (named version + corpus, no error claim) → BOUNDED (per-alias corpus proving estimate ≥ actual at stated confidence, chronological, versioned) → CALIBRATED (measured errors within pre-registered owner thresholds on holdout). **All 14 aliases UNKNOWN** (config.yaml:22–239; 3 with chat-only probes, 1 with FAIL-auth record, none with token/latency/cost measurement). No pricing ⇒ no cost calibration possible.

### 14.4 Ordering experiments

E3→E1→E2 staged (T10 §5 T9-F). Only pre-BM25-distinguishable arms run before the adapter; full triple deferred to Stage B post-adapter. Comparability via frozen corpus versions + pre-registered criteria.

### 14.5 Telemetry architecture freeze

Physically implemented today: inline JSON columns on `sabiroute_request_usage` (`store.py:66–88`), no separate table (`CORE_TABLES` S:512–524), synchronous awaited writes, no telemetry flag/kill-switch (kill-switch exists only for shared inference). Schema-1.1 tripwires lockable (version literal, `extra="forbid"`, per-request immutability, feature/outcome agreement, timezone provenance, attempt ordering, count equality, deployment-set membership, `FOR UPDATE` snapshot append, additive-only migrations). **Startup-validation gap (SAF):** `store.py:709` requires only 5 columns — not the telemetry JSON columns — so an unmigrated DB passes startup and fails at snapshot time; freeze must add them to the startup contract. **Freeze verdict: Option A freezable only as a conditional, not-implemented ADR** (table + convention + predicate + retention + tripwires), with the inline row named as interim; freezing it as "the architecture" would contradict the shipped code.

---

## 15. Track A Approval Matrix

Protected (campaign §15 + conflict controls; path corrected: `gateway.py` lives at `src/sabiroute/gateway.py`): `api/completions.py`, `src/sabiroute/gateway.py`, `main.py`, `config/validation.py`, `security/store.py`, migrations, dataset-related files. Verified present at HEAD. Silence is not approval.

| Item | Change | Touches | Approval | Blocks |
|---|---|---|---|---|
| T1 | Optimisation insertion + effective binding (I1–I9, §8) | `completions.py` | Track A (external reviewer) | R6.1 |
| T2 | O2 pinning + quota governor (BL-06) + `:1601` hardening (BL-02) | `completions.py` | Track A | R6.1 |
| T3 | `optimization_timeout` category | `completions.py` (+ errors taxonomy) | Track A | R6.1 |
| T4 | R6 flag + limits + kill switch | `config/validation.py`, `gateway.py`/`main.py` | Track A | R6.1 |
| T5 | Bounded executor lifecycle (if async stage needed) | `gateway.py`, `main.py` | Track A | R6.1 |
| T6 | Content-free opt store + non-blocking convention (BL-17) | `store.py` (+ migration) | Track A | R6.1 convention / R6.7 writes |
| T7 | D23 settlement fix (BL-01…BL-04) + reconciler (BL-05/BL-15) | `completions.py`, `store.py` (+ migration for marker) | Track A | R6.1 fix / R6.7 ops |
| T8 | Tier-1 estimator + `quota_request_unsupported` + version field (BL-07) | `completions.py`, `security/budgets.py`, `store.py` | Track A | R6.1 |
| Architecture decisions (this report) | Freeze of §§8–15 | — | Owner (project owner) | R6.0 |
| New implementation (R6.1 units §17) | Per-unit changes | Per §17 file list | Owner G7 (scope) + Track A (surface) | R6.1 start |

---

## 16. Documentation Consistency Audit

T10 report defects found (this report corrects; T10 itself not edited):

1. **"18 invariants (§7)" (T10 §19 row 4; §24 check): WRONG POINTER.** T10 §7 contains proposals T10-1…T10-7, not invariants. Authoritative mapping: **(a)** T9 §4 = 15 architectural invariants (immutability, separate effective, once-per-request, fail-to-original, no re-transform, ownership ×2, estimate/actual separation, no prompt in telemetry, tenant isolation, bounded off-loop execution, 300-s deadline, routing/admission/reservation/settlement integrity, no silent damage, default-off gating); **(b)** pack §11 = owner R6-S01…S20 transformation invariants (20 items; S03/S05/S06/S07 enforced-by-bypass, S08 corpus-only). "18" matches neither set — unattested number. **Impact: none on decisions** (every ruling cites specific invariants/behavior, never the count).
2. **Gateway path:** T9/T10 "gateway.py" = `src/sabiroute/gateway.py` (no `src/sabiroute/api/gateway.py`). Corrected in §15.
3. **`completions.py` length** cited as 2,090–2,102 lines across investigators — same file, minor counting variance; anchors (§§7–9) verified individually.
4. **Decision identifiers:** no duplicates; D-series (owner/pack scope) vs T10-series (new proposals) namespaces kept distinct; no APPROVED label on Track A authority anywhere; OWNER-ACCEPTED used only for mission-§2 T8 items. Statuses consistent across T10 §§4–7 and this report §§4–5.
5. **Roadmap references:** T10 §16 stage exits preserved; G4/G5/G7 positions preserved but definitions absent from tree (T11-F §5.4: zero hits; repo gates are A–E in `reports/remediation-roadmap-and-gates.md`) — campaign/mission must supply G-definitions before G5/G7 execution (BL-23 note).
6. **No silent reconciliation:** T10 conflicts resolved explicitly (A/C rejected, Class-2 deferred, governor added); T11 extensions (BL-02…BL-04) narrow further, never widen.

---

## 17. R6.1 Implementation Preparation Package

No code written. Units are independently verifiable, ordered by dependency; each states necessity, invariant, requirement, preserved behavior, and tests.

| Unit | Content | Files touched (Track A ★) | Why / invariant / requirement | Preserved | Tests | Complexity |
|---|---|---|---|---|---|---|
| U0 | Regression tests first: §7.6 items 1, 2, 5, 6 (all fail today) + flaw 6 (D4) | `tests/test_user_quotas.py`, `tests/test_phase10.py` (test-only) | Prove BL-01…BL-04 before fixing; inv. 13 | No prod behavior change | 4 failing specs | S |
| U1 | Settlement basis fix: budget-independent unknown signal (BL-02) + flag-on-no-usage-success (BL-03) + settle-at-estimate on any-unknown (BL-01) + `attempted` binding fix (BL-04) | ★`completions.py` | Metering integrity; inv. 8, 13; R6.1 §6.4 | Retry/governor arithmetic otherwise unchanged | U0 green; idempotency; all-unknown + multi-known controls | M |
| U2 | Quota token governor (BL-06) + unknown-break mirror | ★`completions.py` | Close N·(in+n·M) overrun; inv. 13 | Budget governor untouched | Multi-attempt quota consumption ≤ reservation | S |
| U3 | Tier 1 estimator (BL-07): quota extras parity, `quota_request_unsupported`, estimate recording, n>1 note | ★`completions.py`, `security/budgets.py`, ★`store.py` (version field) | Metering integrity; inv. 13, 14 | Budget path frozen | Gap-closure + budget-regression suite | M |
| U4 | Foundation I1–I9 (T1–T5): frozen original, canonical, effective, metadata (memory-only), policy, capability checks, bypass, validation, fail-to-original + `optimization_timeout` + flag/limits/kill-switch | ★`completions.py`, ★`config/validation.py`, ★`gateway.py`/`main.py`, new `request_transform/` | R6.1 core; inv. 1–5, 9, 11, 15 | Disabled ⇒ byte-identical payloads; lifecycle order; ledger contract | Placement, byte-identity, bypass, null-crash, retry-identity, CancelledError passthrough | L |
| U5 | T10-6 in-message tool detection (BL-08) + role-aware freeze decision (BL-09) | ★`completions.py` or classifier + policy | Class-1 FULL claim; inv. 9, 10, 14 | Bypass-direction (no new admissions) | Syntactic detection; verbatim-forward closed; byte-diff | M |
| U6 | Non-blocking write convention + failure-proof test (BL-17) | ★`store.py`, ★`completions.py` | Telemetry must not change outcomes; inv. 9 | Fail-closed accounting stays | Telemetry-failure ⇒ request unaffected | M |
| U7 | Null-content hardening (BL-18) across I1–I8 | `request_transform/` + fixtures | Crash-shape; inv. 4, 14 | — | Null matrix incl. `content:null` + tool keys | S |
| U8 | B1 additions batch 1 (stub/cache absence, frozen-subtree, order conformance, tenant-namespace/TTL tests) | tests + fixtures | R6.1 exit; inv. 10 + S-series | — | New B1 files green | M |
| U9 | Budget terminal marker migration (BL-15) + `cleanup_errors`/ledger wiring (BL-05) | ★`store.py` migration, admin visibility | Reconciler prerequisite; inv. 13 | Additive-only migration | Marker + visibility tests | M |
| U10 | Streaming-disconnect adjudication test (BL-14) | tests (+ fake ASGI harness) | Close `GeneratorExit` question | No behavior change yet | Disconnect matrix green | M |
| U11 | E3 harness skeleton + R6.1 B1-subset gate wiring (BL-20) | tests/scripts | R6.1 exit gate | — | E3 green on no-op | M |
| U12 | Reconciler design-against-marker (settle-only, N/pass, jitter, alerts) — build in R6.7 unless owner pulls forward | ★`store.py`, ops docs | inv. 13; T11-B §5 | Never blind-TTL; never rewrite terminal | §7.6 item 10 contract | L |

**Ordering:** U0 → U1,U2,U3 (any order after U0) → U4 → U5,U6,U7 → U8,U10,U11 → U9 → U12. **Static checks:** no `litellm` import on request path (T10-1); snapshot-JSON transform-key absence; byte-identity under disabled policy; `extra="forbid"` untouched. **Acceptance:** U0–U8 + U10–U11 green, Track A per-unit sign-off, disabled-by-default, kill-switch verified. **Rollback:** each unit reverts independently (flag-off ⇒ byte-identical; settlement units revert to specified-but-hole behavior — hence ship U1–U3 together). **Estimated complexity:** S×3, M×7, L×2 — one focused R6.1 cycle, not a giant patch.

---

## 18. Owner Decision Package

Grouped for efficient resolution. Recommended defaults marked ★. None is pre-approved.

**Group A — R6.0 freeze (blocks signature):**
- **A1. Adopt §§8–15 as the frozen architecture?** ★ Yes — decisions adjudicated, conditions recorded. Alternative: return D14/D19-Tier-2 for re-scope (cost: re-opens §§11/14).
- **A2. Tier-1 metering fixes as integrity work (not feature work)?** ★ Yes (BL-01…BL-04, BL-06, BL-07 close live holes). Alternative: defer to post-v1 (risk: documented under-billing + leak ship in v1 accounting).
- **A3. Telemetry Option A as conditional, not-implemented ADR (BL-16)?** ★ Yes (honest freeze). Alternative: redefine target as inline-hardened (cost: new ADR; contradicts T8 D14 direction).
- **A4. T10-1…T10-7 scoping adopted?** ★ Yes. Risk of "no": adapter work proceeds without coupling/tokenizer/null/capability/governor/detection/convention guardrails.

**Group B — R6.1 scope (blocks G7):**
- **B1. Foundation contract (§8 I1–I9) approved as draft?** ★ Yes with §6.3 rulings. Alternative: require external R6.1 design doc first (cost: delay; benefit: second authorship).
- **B2. Scope: chat-completions-only (BL-27)?** ★ Yes — `api/chat.py` excluded from R6.1. Alternative: include SabiChat path (cost: second admission/store surface in scope).
- **B3. Bypass authority operator-only (BL-32)?** ★ Yes, per-route, default-off. Alternative: trusted-service signal (cost: provenance machinery like `sabichat_service_key_id`).
- **B4. Phase-13 keep-out for R6.1 metadata (BL-31)?** ★ Yes. Alternative: schema-1.2 amendment now (cost: Phase-13 coordination inside R6.1).
- **B5. Class-1 FULL vs gated (BL-09)?** ★ Gated for system/developer-role traffic until role-freeze proven. Alternative: FULL claim now (risk: byte-identity unproven for privileged roles).

**Group C — evidence & semantics (inform, don't block):**
- **C1. byok/paid semantics + billing-source scope (BL-30)?** Needed before any BOUNDED+ claim; no R6.1 impact.
- **C2. Multilingual claim exclusion (BL-19)?** ★ Exclude non-Latin from BM25 relevance until corpus proven (Terminal D owns corpus).
- **C3. Reconciler in R6.1 or R6.7 (BL-15/U12)?** ★ R6.7, with marker migration (U9) in R6.1 so rows are identifiable.

**Group D — external & authorization:**
- **D1. Track A engagement authorized to schedule (BL-21)?** Reviewer + cadence.
- **D2. Terminal B/C/D/E prompts re-issued (BL-24)?** ★ Yes, prompts in campaign §13.
- **D3. G7 scoped authorization (BL-23) after A+B?** Scope = §17 U0–U11.

---

## 19. R6.0 Final Readiness Assessment

**R6.0: CONDITIONALLY READY — NOT READY for owner signature until the following are scheduled/recorded.**

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Decision register completeness | CONDITIONAL | D1–D23 + T10-1…T10-7 adjudicated; T8 register uncommitted; BL-26 draft contract pending adoption |
| 2 | Owner-decision documentation | CONDITIONAL | Level-1 acceptance scoped (§3); written freeze approval outstanding (BL-22) |
| 3 | T8/T9 reconciliation | PASS | §§4–5, 10; conflicts resolved; T11 extends without overturning |
| 4 | Architectural invariants | PASS | §16 mapping (15 + S01–S20); every accepted proposal satisfies all; breaches rejected |
| 5 | Stage ownership | PASS | S0–S5 + foundation placement pre-`:1345` (§8) |
| 6 | Lifecycle placement | PASS | Verified order §8.1 |
| 7 | Budget and quota policy | CONDITIONAL | Specified; implementation + Track A pending |
| 8 | Retry and fallback policy | CONDITIONAL | O2 + governor specified; code pending |
| 9 | Unknown-usage settlement | CONDITIONAL | Fix + reconciler specified; hole reproduced, unclosed; extended BL-02…BL-05 |
| 10 | BM25 integration policy | CONDITIONAL | (b′) + six proofs + gates pending |
| 11 | Tool-bearing eligibility | CONDITIONAL | Matrix + prerequisites pending |
| 12 | Estimator confidence policy | PASS | Ladder as process; all UNKNOWN (§14.3) |
| 13 | Benchmark design | CONDITIONAL | B1/B2 specified; Terminal D pending |
| 14 | Telemetry architecture | CONDITIONAL | Option A conditional-ADR pending (BL-16) |
| 15 | Track A dependencies | BLOCKED | Matrix §15; sign-off outstanding (BL-21) |
| 16 | Deployment-tokenizer policy | CONDITIONAL | Policy C + matrix pending (BL-19) |
| 17 | Rollout and release gates | PASS | Default-off + kill-switch + G-positions; G-definitions to be supplied (BL-23 note) |

**Overall: CONDITIONALLY READY — SPECIFIC ITEMS REMAIN.** Decisions adjudicated, architecture consolidated; what remains is approvals + specified evidence, not open design. NOT READY for signature until Track A engagement + Terminal B/C/D/E reconciliation are at least scheduled with recorded prompts, BL-16/BL-26 ADRs adopted, and BL-22 written approval granted.

---

## 20. R6.1 Final Readiness Assessment

**R6.1: NOT READY.**

What exactly prevents starting R6.1: **(1)** owner authorization — no R6.0 written approval (BL-22) and no G7 (BL-23); **(2)** technical prerequisites — five live settlement/accounting defects with failing-today regression specs unimplemented (BL-01…BL-04 + U0), quota governor (BL-06), Tier-1 estimator (BL-07), tool detection (BL-08), non-blocking convention (BL-17), null-hardening (BL-18); **(3)** Track A — T1–T7 + Tier-1 sign-offs unobtained (BL-21) on files R6.1 must touch; **(4)** accounting-correctness risk — BL-01…BL-04 mean quota under-billing and reservation leaks are reproducible by inspection, and the streaming `GeneratorExit` path is unverified (BL-14). It is not "more testing needed" in general: it is the 9 conditions of §6, each with a named owner and acceptance evidence. R6.0 approval does not authorize R6.1; §17 is a blueprint, not a patch.

---

## 21. Remaining Unknowns

Consolidated (smallest next step; read-only unless noted; ★ = safely autonomous):

1. ★ SDK import cost/env-diff (BL-11, ~10 min sandbox). 2. ★ `compress()` null-crash runtime proof (BL-12, ~5 min). 3. Proxy tools/`response_format` fidelity (BL-29, ~20 min: version/config read + one invalid-key call). 4. First-turn vs live-tool traffic census (BL-10 scoping, ~30 min telemetry/log read). 5. ★ Service-key budget row (BL-13, ~10 min). 6. Completed-stream-without-usage provider behavior (~20 min stub SSE + docs). 7. Generator-close/`GeneratorExit` guarantee (BL-14 test). 8. Live paired-row census (BL-28, ~30 min + query). 9. Tokenizer-family map (BL-19 input, ~20 min). 10. ★ byok/paid + billing scope (BL-30, conversation). 11. R6 docs canonical status (owner ruling whether untracked copies commit). 12. Order-selection criteria (Terminal D pre-R6.6). 13. Configurable-ordering boundary (T8: S0-first/S4-last/S5-observer frozen). 14. Admin repair-path census (~15 min `admin.py` quota read). 15. Quota-without-budget liveness (~15 min config read). 16. Mixed-usage test expectations (`test_user_quotas.py` cases the fix must update, ~20 min). 17. Telemetry writer census (~15 min caller check). 18. A-vs-vendored scorer + last-assistant policy (owner decision, then contract test first).

---

## 22. Recommended Next Mission

**T12 — Scoped R6.1 authorization gate (not implementation).** Entry: this report + owner Group-A decisions (§18). Do: (a) record BL-22/BL-21/BL-24 scheduling; (b) run the 8 autonomous investigations (§21 ★ + BL-13/BL-29) and append evidence; (c) adopt §8 as draft contract with B-group rulings; (d) issue Track A T1–T8 + Terminal B/C/D/E prompts; (e) return with G7 scope (§17 U0–U11) or a named refusal. Explicitly not: code changes, test runs beyond read-only, provider calls. Success: owner can sign R6.0 and scope G7 with zero open technical questions. Alternative if owner prefers velocity: combine T12 with U0 (test-only, no prod change) under explicit test-authorization — U0 changes no production behavior and is the cheapest risk-reduction available.

---

## 23. Verification and Worktree Report

- **Initial state:** branch `feat/sabiroute-routing-foundation`; HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`; zero tracked modifications; empty staged; target T11 path absent.
- **Final state:** branch unchanged; HEAD identical (repository did not change under investigation); `git diff --name-only` empty; `--cached` empty; non-`??` porcelain lines zero.
- **After writing:** exactly ONE file created — `docs/r6-t11-r6-readiness-and-implementation-preparation.md` (this file). No existing file created-or-modified (pack, campaign, T9, T10, source, config, dependencies, migrations, datasets, scorecards untouched — verified via empty tracked diffs).
- **Dependencies:** unchanged (no installs; `litellm` inspected only as installed-tree text).
- **Branch:** never switched; no reset/clean/stash/prune/commit/push/deploy.
- **Worktrees:** main on-branch untouched; sibling detached/prunable + docs-publishing worktrees untouched. Four harness-spawned `.claude/worktrees/agent-*` snapshots were at `e4ddc8d` (wrong ref — pre-R3 skeleton); investigators read `319a711` via absolute path / `git show`. Three subagents (A/D/E) failed on model-endpoint errors and were covered by direct main-agent inspection; B/C/F delivered full hand-backs reconciled here. No mission files written outside this report.
- **Verification NOT completed:** runtime execution of any kind (read-only mandate — no tests run, including U0 specs); provider-measured (B2) evidence (none claimed); live-store paired-row census (§21.8); full admin/quota-test reads (spot-checked only); owner-conversation acceptances beyond mission-stated T8 scope; Terminal B/C/D/E reports (unavailable — prompts in campaign §13 reused, not fabricated); streaming `GeneratorExit` path (BL-14, needs runtime test).
- **Required-section check:** all 23 mission sections present (§§1–23); both Mermaid diagrams (§§8-arch/9-lifecycle below); consolidated blocker matrix (§4); decision matrix (§§5–6, §18); file ownership embedded in §15 + §17; implementation dependency graph (§17 order chain + diagram below); T8 register (§3); T9 A–H (§3); T10 adjudications (§3); accounting investigation (§7); R6.0 conclusion (§19, exactly one: CONDITIONALLY READY); R6.1 conclusion (§20, exactly one: NOT READY); unknowns (§21); rejected alternatives (carried from T10 §22 — stock `compress()`, direct SDK import, internals adapter, embedding scoring, broad tool-bearing optimization, pre-validation savings, unclamped forecasting, pre-BM25 third experiment, in-record telemetry merge, blind TTL release, weighted-score rescue — all reaffirmed, none re-litigated).
- **Authority check:** no proposed decision presented as owner-approved (OWNER-ACCEPTED only for mission-§2 T8 items; all else RECOMMENDED/PROPOSED/CONDITIONAL/UNRESOLVED/BLOCKED/owner-decision).

### Mermaid architecture diagram

```mermaid
flowchart TB
    Client --> Ingress["Ingress / BodyLimit / Deadline 300s<br/>main.py, body_limit, deadline"]
    Ingress --> Auth["Auth + BYOK-0 guard<br/>auth.py:68-95, completions.py:322-346"]
    Auth --> Admit["Admission: usage row :374 + rate limit :850"]
    Admit --> Est["Budget estimate ORIGINAL :935<br/>Tier 1/2 post-fix"]
    Est --> Classify["Classification ORIGINAL :966"]
    Classify --> FreePool["Free Pool gate :997-1066"]
    FreePool --> Quota["Quota reservation :1097<br/>check_and_reserve_quota"]
    Quota --> Elig["Eligibility evaluate_candidates :1166"]
    Elig --> Budget["Budget reservation :1216<br/>reserved = est + M"]
    Budget --> Opt["R6 Optimisation (NEW, once)<br/>I1 frozen + I2 canonical + I3 effective + I5 policy + I6 caps + I7 bypass + I8 validate"]
    Opt -->|"pass: immutable effective"| Loop["Retry Loop :1345<br/>deadline recheck :1346"]
    Opt -->|"fail: effective = original (I9)"| Loop
    Loop --> Choose["Per-attempt choose_deployment :1388"]
    Choose --> Snap["ORIGINAL snapshot :1433-1502"]
    Snap --> Prov["Provider via LiteLLM proxy<br/>EFFECTIVE only :1520/:1539"]
    Prov --> Tel["Attempt telemetry<br/>original features + actuals"]
    Tel --> Gov["Governors: O2 + cost + token + NEW quota<br/>unknown-break (budget-independent post-fix)"]
    Gov -->|"retryable"| Loop
    Gov -->|"exhausted / break"| Finish["finish(): reconcile + settle/settle_estimate/release<br/>:542-680 + bounded reconciler"]
    Finish --> Tele2["Content-free opt telemetry<br/>separate store R6.7 (Option A conditional)"]
    style Opt fill:#e8f4fd,stroke:#1a73e8
    style Prov fill:#fef7e0,stroke:#f9ab00
    style Finish fill:#e6f4ea,stroke:#1e8e3e
```

### Mermaid request lifecycle diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway
    participant O as R6 Optimiser (once, pre-:1345)
    participant R as Router
    participant P as LiteLLM Proxy/Provider
    participant S as Settlement
    C->>G: request (original immutable)
    G->>G: BYOK-0 + admission row + rate limit
    G->>G: budget est (ORIG) + classify (ORIG)
    G->>G: free-pool narrow + quota reserve + eligibility + budget reserve
    G->>O: eligible? S0 gate + I7 bypass + T10-6 detection
    O-->>G: effective = candidate | original (fail-closed, I9)
    loop each attempt (same effective object)
        G->>R: choose_deployment (exclude attempted)
        G->>G: ORIGINAL snapshot + telemetry
        G->>P: POST /v1/chat/completions (EFFECTIVE only)
        P-->>G: body + usage (or unknown)
        G->>G: governors (O2 + quota + budget-independent unknown-break)
    end
    G->>S: finish(): reconcile/settle (any-unknown → estimate)
    S-->>G: settled | settled_estimate | released
    G->>C: response (X-SabiRoute-Request-ID)
```

### Implementation dependency graph

```mermaid
flowchart LR
    U0["U0 regression tests<br/>(fail today)"] --> U1["U1 settlement fix<br/>BL-01..04"]
    U0 --> U2["U2 quota governor"]
    U0 --> U3["U3 Tier-1 estimator"]
    U1 --> U4["U4 foundation I1-I9"]
    U2 --> U4
    U3 --> U4
    U4 --> U5["U5 tool detection + role freeze"]
    U4 --> U6["U6 non-blocking convention"]
    U4 --> U7["U7 null hardening"]
    U5 --> U8["U8 B1 batch 1"]
    U6 --> U8
    U7 --> U8
    U4 --> U10["U10 disconnect test"]
    U4 --> U11["U11 E3 harness"]
    U8 --> U9["U9 budget marker + visibility"]
    U10 --> U9
    U9 --> U12["U12 reconciler (R6.7)"]
    style U0 fill:#e6f4ea,stroke:#1e8e3e
    style U4 fill:#e8f4fd,stroke:#1a73e8
    style U12 fill:#fef7e0,stroke:#f9ab00
```

**T11 success-criterion answers (§17 of mission):** architecture = §8 (+ diagrams §23); retained = Tier-1 metering fixes + Class-1-only gating + shadow-E′ + non-blocking convention + ladder process (§19 Group-A logic carried forward); narrowed = b′-adapter / Class matrix / Tier-1+governor / O2+shadow (§§10–12); deferred = Group B constructions, reconciler ops, BOUNDED+ promotion, Stage-B triple; excluded = Group C per T10 §22 reaffirmed; accepted = §3 T8 list; still-requires-owner = §18 Groups A–D; external outstanding = Track A T1–T8 + Terminals B/C/D/E (§15, BL-21, BL-24); R6.0 blocker = approvals + specified evidence, not design (§19); R6.1 prerequisites = §6 nine conditions + G7; trade-offs = T10 §22 (no scoring anywhere in either report).

**T11 FINAL STATUS: T11 COMPLETE — R6.0 CONDITIONALLY READY; R6.1 NOT READY.**

---

### Document control

Created by: T11 autonomous investigator (synthesis of pack + campaign + T9 + T10 + independent HEAD verification + 3 subagent hand-backs B/C/F + direct coverage of A/D/E)
Created on: 2026-11-03
Repository baseline: `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` (verified before and after; unchanged)
Files created: `docs/r6-t11-r6-readiness-and-implementation-preparation.md` (this file) — **one file, no others**
Files modified: none
Application source, configuration, dependencies, migrations: untouched
Tests executed: none (static inspection only) · Compression executed: no · Benchmarks run: no · Provider calls made: no · Packages installed: no
Commits, pushes, deploys, resets, cleans, stashes, prunes, branch switches: none
Authority: decision support only. Approves nothing; authorises no R6.1 work; grants no G7.
