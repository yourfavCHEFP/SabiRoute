# R6 T13 — Documentation Correction and Owner Decision Session Preparation

**Status:** preparation only. **This report approves nothing, adopts no ADR, grants no G7, and authorises no implementation.**
**Mode:** read-only investigation plus one new document. No application source, test, config, migration, dataset or prior report was modified.
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`.
**Authority source:** `docs/r6-t12-accounting-integrity-and-gate-closure.md` (sole predecessor of record for T13).

**Evidence labels used throughout:**

| Label | Meaning |
|---|---|
| `VERIFIED` | Read at HEAD `319a711`, exact anchor cited. |
| `STATIC-ANALYSIS FINDING` | Reachable by control flow inspection; runtime consequence not executed. |
| `PROPOSED` | Authored here; not approved, not adopted. |
| `RECOMMENDED` | A default offered for owner adjudication. A recommendation is **not** a decision. |
| `OUTSTANDING` | Awaiting an owner action. |
| `NOT OBTAINED` | External or owner input absent. Never inferred from silence. |
| `NOT EXECUTED` | Deliberately not run. |

---

## 1. Executive Summary

T13 converts T12's findings into a decision-ready package. It creates no code, adopts no decision, and changes no gate status.

**The substantive technical result: T12's hedge on U0 spec 5 is wrong, and spec 5 fails deterministically.** T12 §19.2 recorded that spec 5 "very likely passes today on the budget-only shape" and marked it *requires re-derivation before authoring*. T13 performed that re-derivation by source inspection and reached the opposite conclusion: on a **budgeted request whose first attempt fails with *known* usage**, the unknown-usage flag is **never set** (`completions.py:1568–1574`), so it cannot survive into the second attempt; the no-usage success at `:1903–1911` leaves the flag unset; `finish()` at `:1945` therefore settles the **partial sum** rather than holding the estimate. Spec 5 **fails**, and must be authored as `xfail(strict=True)`, not skipped or omitted.

T12's error is identifiable and narrow: it read `:1573 elif budget_reserved:` as firing whenever the request is budgeted. That `elif` is attached to `if failure_usage is not None` at `:1568`, so it fires only when the failure body carries **no usage object at all** — not when it carries a *known* total. "Known-fail" is precisely the case the spec names, and precisely the case that escapes the flag.

**Documentation corrections.** All six X-items are accounted for and independently verified, not carried forward on assertion:

| ID | Subject | T13 outcome |
|---|---|---|
| X-1 | Compression discovery packet claimed absent | **Corrected** — present, 8,645 B `VERIFIED` |
| X-2 | G4/G5/G7 meanings claimed undefined | **Corrected** — defined twice `VERIFIED`; real defect is namespace collision |
| X-3 | Track A T7 ambiguity | **Consolidated to T1–T8**, `PROPOSED`, pending D5 |
| X-4 | T11 internal contradictions | **Confirmed by direct count** — §18 enumerates **15**, §1 claims 12 |
| X-5 | "All 14 aliases UNKNOWN" | **Corrected** — 11 UNKNOWN, 3 BOUNDED `chat`, 1 also `streaming` |
| X-6 | Rollout graded PASS | **Corrected to SPECIFIED, UNBUILT** — zero apparatus found |

**Decision package.** 23 owner decisions across four groups, every one `OUTSTANDING`. Two ADR briefs `PROPOSED`. Four Terminal packets drafted, none issued, all lanes `NOT OBTAINED`.

**Gate status is unchanged by T13 preparation.** R6.0 remains **CONDITIONALLY READY**. R6.1 remains **NOT READY**. U0 remains **READY FOR SEPARATE OWNER AUTHORIZATION** — and T13 *reduces* its conditions from three to two by resolving the spec-5 question, while leaving D1 (merge policy) and D3 (G7 naming `tests/`) outstanding.

**What T13 explicitly did not do:** adopt an ADR, mark a decision approved, grant G7, claim a Track A or Terminal result, contact a reviewer, or write a test.

**Final status of this report:** `T13 COMPLETE — DECISION PACKAGE READY; OWNER ADJUDICATION OUTSTANDING; NO GATE GRANTED.`

---

## 2. Mission Authority and Scope

### 2.1 Authorised

- Inspection of the repository and its documentation.
- Creation of exactly one new report: this file.
- Preparation of correction, decision, ADR and Terminal packet content.
- Re-derivation of disputed U0 behaviour by **source inspection only**.
- Preparation of a test specification that is not written to disk.
- Read-only repository verification.

### 2.2 Not authorised — and not done

| Prohibition | Status |
|---|---|
| Modify application source | **Not done** — zero writes under `src/` |
| Modify tests | **Not done** — zero writes under `tests/` |
| Modify config, migrations, datasets, dependencies | **Not done** |
| Implement U0/U1/R6.1 | **Not done** |
| Adopt ADR-1 or ADR-2 | **Not done** — both `PROPOSED` |
| Mark any Group A/B/C/D decision approved | **Not done** — all 23 `OUTSTANDING` |
| Grant G7 or authorise implementation | **Not done** |
| Claim Track A or Terminal review completed | **Not done** — all `NOT OBTAINED` |
| Contact reviewers / send prompts | **Not done** |
| Commit, push, stage, reset, clean, stash, prune, rebase | **Not done** |
| Fetch, pull, merge, reconcile divergent branch | **Not done** |
| Delete, rename or overwrite an existing report | **Not done** |
| Edit CLAUDE.md | **Not done** — recorded as a candidate only (§5) |

### 2.3 Decision discipline

Five buckets are preserved exactly as the predecessors left them. No item is promoted across a boundary.

1. **T8 owner-accepted** (*accepted-but-scoped*): D6, D8, D14 (logical separation only — does not approve Option A as a table), D10/D20, D18, D19, D21, D22, D23.
2. **T9/T10 recommendations** (*recommended*): T10 states in its own document control that it "Approves nothing". `T10 ACCEPT Tier 1` and `T10 CONFIRMED Option A` are **not** owner decisions.
3. **T10 adjudications** (*adjudicated, not owned*): A BM25→b′ · B tool-bearing classes · C structured quota tiers · D retry/O2 · E estimator ladder · F ordering · G settlement + reconciler · H telemetry Option A conditional.
4. **T12 proposals** (*PROPOSED*): ADR-1, ADR-2, corrections X-1…X-5, and the A6 finding.
5. **T13 preparation** (*PROPOSED*): the spec-5 re-derivation and its verdict, the strict-xfail specification, the Terminal packets, and the consolidated registers.

---

## 3. Repository Baseline

`VERIFIED` at mission start by direct inspection.

| Fact | Value | Method |
|---|---|---|
| Repository root | `<repo-root>` | `pwd` |
| Branch | `feat/sabiroute-routing-foundation` | `git branch --show-current` |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` | `git rev-parse HEAD` |
| Tracking | `[ahead 6, behind 3]` of `origin/feat/sabiroute-routing-foundation` | `git status -sb` |
| Staged changes | none | `git diff --cached --stat` (empty) |
| Unstaged tracked changes | none | `git diff --stat` (empty) |
| Untracked entries | 109 | `git status --porcelain \| wc -l` |
| Worktrees | 6 registered, 2 `prunable`, none touched | `git worktree list` |
| T13 target before this file | **absent** | `ls` returned no such file |

**Baseline matches T12's recorded baseline exactly.** HEAD is unchanged since T12, so T12's line anchors remain valid and no re-anchoring was required. T13 spot-verified that assumption rather than assuming it: every anchor cited below was re-read at `319a711`.

**Corpus integrity.** All five predecessor reports present and non-trivial:

| Report | Bytes |
|---|---|
| `r6-architecture-decision-pack.md` | 35,947 |
| `r6-decision-resolution-and-approval-campaign.md` | 50,154 |
| `r6-t9-capability-recovery-review.md` | 96,860 |
| `r6-t10-decision-consolidation-and-freeze-preparation.md` | 54,604 |
| `r6-t11-r6-readiness-and-implementation-preparation.md` | 69,543 |
| `r6-t12-accounting-integrity-and-gate-closure.md` | 88,581 |

None was modified by T13.

**Divergence caveat, restated.** Local HEAD is six commits ahead of and three behind its upstream. Every anchor in this report is against **local** `319a711`. A reviewer working from a remote ref must re-anchor. T13 did not fetch, pull or reconcile.

---

## 4. Documentation Correction Register — X-1 to X-6

Each item states the defect, the verified position, and its consequence. **None overturns a T11 engineering verdict**, but four would otherwise be signed as fact.

### X-1 · The compression discovery packet is not absent

| | |
|---|---|
| **T11 claim** | `docs/compression-discovery-packet.md` is absent (cited against BL-26). |
| **Verified at HEAD** | **Present.** `8,645` bytes, `VERIFIED` by `ls -la`. |
| **Corrected statement** | The document **exists** and is a discovery packet covering **CD1–CD6**. It is **not** an adoptable R6.1 foundation contract: it names `src/sabiroute/compression/` with a seven-mode policy registry (`off/lite/standard/aggressive/ultra/rtk/stacked`), which is discovery-phase material outside R6.1 scope. |
| **Consequence** | BL-26's *substance* survives — no adoptable contract exists — but its evidence sentence is false and must be replaced. ADR-2 must carry the naming and package-boundary conflict explicitly (see §12, C-1). |
| **What it does not change** | R6.0's blocker list. BL-26 remains a blocker for a different and better-stated reason. |

### X-2 · G4/G5/G7 meanings are defined; the defect is a namespace collision

| | |
|---|---|
| **T12-C claim** | No set defines the R6 meanings of G4/G5/G7. |
| **Verified at HEAD** | **False.** Defined consistently in two documents: `docs/r6-t9-capability-recovery-review.md:417` — "Release gates G4 (benchmark — needs Terminal D), G5 (red-team — stays blocked pending D6/D8 corrections), G7 (implementation authorization — cannot be requested by this report)"; and `docs/r6-decision-resolution-and-approval-campaign.md:332` — "G4 (benchmark gate) requires Terminal D reconciliation; G5 (red-team) stays blocked pending D6/D8 corrections; G7 (implementation authorisation) cannot be requested." Both read verbatim at HEAD. |
| **Preserved R6 definitions** | **R6 G4 = benchmark gate.** **R6 G5 = red-team gate.** **R6 G7 = separate owner implementation authorisation.** |
| **Actual defect** | A **namespace collision** between three gate scales, not a governance gap. Three overlapping scales exist (§4.3 below). |
| **Recommendation** | Adopt a disambiguating **gate register** that names, for each document, which scale its G-identifiers belong to. This is citation hygiene, not new architecture. |
| **Boundary** | **G7 has not been granted.** Nothing in T13 changes that. |

#### 4.3 The three colliding namespaces `VERIFIED`

| Namespace | G4 | G5 | G7 | Source |
|---|---|---|---|---|
| **R6** | benchmark (needs Terminal D) | red-team (blocked on D6/D8) | implementation authorisation | `r6-t9:417`, campaign `:332` |
| Developer Workflow Overhaul plan | deadline/retries | async lifecycle | deployment/security | `SabiRoute_Developer_Workflow_Overhaul_Plan.md:239–247` |
| Repository remediation (A–E) | — | — | — | `reports/remediation-roadmap-and-gates.md:56–68` |

### X-3 · Track A numbering does not converge across three documents

| Document | Numbering | T7 means |
|---|---|---|
| Campaign §15 | T1–T7 | "no dataset/migration change in v1" |
| T10 | T1–T7 plus an unnamed "Tier-1 estimator" | T7 ambiguous |
| T11 §15 | T1–**T8** | **T7 = settlement/reconciler**, **T8 = Tier-1 estimator** |

Two distinct meanings for `T7` across three documents. **BL-21 cannot be issued until one numbering is fixed** — an ambiguous `T7` would have a reviewer sign off on the wrong artefact.

**T13 position:** the consolidated **T1–T8** mapping in §6 is a **RECOMMENDED canonical proposal awaiting owner decision D5**. It is **not** owner-approved and must not be cited as canonical until D5 is recorded. T11 and the campaign are **not rewritten**; this register is the correction of record.

### X-4 · T11 internal contradictions — confirmed by direct count

| Claim | Verified position |
|---|---|
| §1 omits BL-16 and BL-26 from the R6.0 blocker list | **Confirmed by direct reading.** §1 names exactly four: BL-22, BL-21, BL-24, BL-25. BL-26 appears only as an *R6.1 authorisation* gap, not an R6.0 blocker, though §4/§19 treat both BL-16 and BL-26 as R6.0-blocking. |
| §1 claims 12 questions in §18 | **Confirmed.** T11:33 states "The owner must decide 12 questions (§18, grouped A–D)." |
| §18 actually enumerates 15 | **Confirmed by direct enumeration.** A1–A4 (4) + B1–B5 (5) + C1–C3 (3) + D1–D3 (3) = **15**. |
| Two rulings are unenumerated | **Confirmed.** Monotone-shrink permanence and the prohibition on per-attempt re-derivation are absent from §18, taking the real total to **17**. T12 adds them as **B6** and **B7**. |

**Complete proposed Group B inventory B1–B9** is recorded in §8. T11 is **not silently rewritten**; this register is the correction of record.

**Note on renumbering.** T12 restructures T11's groups: T11's `B5` (Class-1 gating) becomes T12's `C3`; T11's `C3` (reconciler placement) becomes T12's `B9`; T11's `D1` (Track A engagement) becomes T12's `D4`. T12's `D1`, `D2` and `D5` are new. Anyone reconciling the two registers must map by *content*, not by identifier.

### X-5 · "All 14 aliases UNKNOWN" is false

**Re-verified independently by T13** in `config/config.yaml` at HEAD, not carried forward.

| Fact | Value |
|---|---|
| Configured aliases | **14** `VERIFIED` — `model_name` at `:22, :46, :72, :98, :110, :122, :134, :147, :160, :185, :197, :209, :221, :233` |
| Shared anchor | `&unverified_capabilities` at `:27`, referenced by 10 aliases |
| Fully UNKNOWN | **11** |
| BOUNDED for `chat` | **3** |
| Of those, BOUNDED for `chat` + `streaming` | **1** |
| UNKNOWN for `tool_use` and `structured_output` | **all 14** |

| Alias | Declared | Capability anchor | Dated evidence |
|---|---|---|---|
| `sabiroute-gemini` | `:46` | `:54` | `chat: true` — "Runtime-verified 2026-10-08: non-empty text completion through LiteLLM." |
| `sabiroute-groq` | `:72` | `:80` | `chat: true` **and `streaming: true` at `:88`** — "non-empty completion **and incremental SSE**". |
| `sabiroute-openrouter` | `:160` | `:167` | `chat: true` — dated 2026-10-08 comment. |

**Confidence ladder preserved exactly:** `UNKNOWN → UNCALIBRATED → BOUNDED → CALIBRATED`. **No alias is promoted to CALIBRATED.** No alias holds any evidence for `tool_use` or `structured_output`.

**Consequence.** This is a factual error in a document heading for signature, and it **narrows BL-10** from a from-scratch programme to a repeat of an established procedure — which is what makes C4 a cheap decision rather than a research project.

### X-6 · Rollout verification is an overclaim — SPECIFIED, UNBUILT

| | |
|---|---|
| **T11 grade** | Rollout / default-off verification: **PASS** (§19 criterion 17). |
| **Verified at HEAD** | **No apparatus exists.** `grep -rn "optimization_enabled\|optimization_flag\|feature_flag\|kill_switch\|killswitch\|default_off\|rollout"` over `src/` returns **zero hits**; the same over `config/` returns **zero hits**. |
| **Corrected status** | **SPECIFIED, UNBUILT.** |
| **Reasoning** | The architecture can *specify* default-off behaviour. Implementation and runtime verification belong to **R6.1 / U4**. There is nothing to gate because nothing is built, so "default-off + kill-switch verified" cannot be a verification result at R6.0. |
| **What it does not change** | The design is right; the grade overstates it. This does not block architecture approval, but the sign-off document must not claim verification it does not have. |

---

## 5. CLAUDE.md §12 Follow-Up Finding

**Recorded as a documentation correction candidate only. CLAUDE.md was not edited during T13.**

CLAUDE.md §12 names two integration gaps and requires that they be reported rather than silently rewired. T13 neither fixed nor rewired them. Re-verification at HEAD shows **CLAUDE.md §12 is itself stale** on the artefacts it names:

| CLAUDE.md §12 claim | Verified position at HEAD `319a711` |
|---|---|
| `routing/fallback.py` is implemented | **File does not exist.** Not on disk, not tracked. `src/sabiroute/routing/` contains only `health.py`, `intelligent.py` (0 bytes), `policies.py`, `router.py`, `scoring.py`. |
| `FallbackEngine` methods are never called | **No class of that name exists.** `grep -rn "class .*Engine" src/` returns zero hits; the symbol appears nowhere in the tracked tree. True only vacuously. |
| `providers/healthcheck.py` is referenced by nothing | **Module does not exist.** `src/sabiroute/providers/` contains only `base.py`, `litellm_client.py`, `registry.py`. `tests/test_health.py:88` actively asserts `find_spec("sabiroute.providers.healthcheck") is None` — the absence is *enforced by test*, not merely unreferenced. |

**Substance survives; phrasing does not.** The intended meaning — retry/fallback logic lives in `api/completions.py`, and no provider healthcheck module is wired — is consistent with the code. What is wrong is the description: §12 lists a file and a class that do not exist. An auditor working from §12's text will search for artefacts that were never there and may wrongly conclude the tree is incomplete.

**Recommended action (owner decision, not T13 action):** correct CLAUDE.md §12 at source in a separately authorised change. T13 records the finding and stops there, per mission instruction.

---

## 6. Consolidated Track A T1–T8 Proposal

**Status: `PROPOSED` / `RECOMMENDED`. Pending owner decision D5. Not canonical, not approved.**

Source: T11 §15, reconciled by T12 §16, consolidated here. Every mapping below was checked against the documents; the protected surface is `src/sabiroute/api/completions.py`, `src/sabiroute/gateway.py`, `src/sabiroute/main.py`, `src/sabiroute/config/validation.py`, `src/sabiroute/security/store.py`, migrations and dataset-related files. All verified present at HEAD.

| Item | Change | Files | Units |
|---|---|---|---|
| **T1** | Optimisation insertion and effective-request binding (I1–I9) | `completions.py` | U4 |
| **T2** | O2 pinning, quota governor (BL-06), `:1601` retry hardening (BL-02) | `completions.py` | U1, U2 |
| **T3** | `optimization_timeout` error category | `completions.py` (+ errors taxonomy) | U4 |
| **T4** | R6 feature flag, limits, kill switch | `config/validation.py`, `gateway.py`/`main.py` | U4 |
| **T5** | Bounded executor lifecycle | `gateway.py`, `main.py` | U4 |
| **T6** | Content-free optimisation store and non-blocking write convention (BL-17) | `store.py` (+ migration) | U6 |
| **T7** | Settlement fix (BL-01…BL-04, A6) and reconciler (BL-05/BL-15) | `completions.py`, `store.py` (+ migration) | **U0, U1, U9, U12** |
| **T8** | Tier-1 estimator, `quota_request_unsupported`, version field | `completions.py`, `security/budgets.py`, `store.py` | U3 |

### 6.1 What Track A approval actually is — and is not

Four distinctions that must survive into the owner session:

1. **U0 touches tests only.** U0 is `tests/test_user_quotas.py` and `tests/test_phase10.py` — **no Track A file**. Its diff is invisible to Track A.
2. **U0's subject matter belongs to the settlement workstream.** U0 proves defects that **T7** fixes. U0's *scope* therefore belongs in a T7 conversation even though its *diff* does not. This is the asymmetry that forces D3: G7's scope text must name `tests/` explicitly, or U0 has no authorisation basis at all because it appears in no Track A row.
3. **Track A approval is not owner architecture approval.** Track A signs sensitive source changes. It does not approve the architecture, and the owner's R6.0 signature does not substitute for it. Neither implies the other.
4. **The T1–T8 numbering is pending.** Until D5 is recorded, no Track A request may cite a T-number as canonical. An ambiguous `T7` risks a reviewer signing off the wrong artefact (X-3).

**T13 did not issue a Track A request and claims no external sign-off.** Track A status remains `NOT OBTAINED`.

---

## 7. Group A — R6.0 Architecture Approval

**All four items `OUTSTANDING`. None marked approved.**

R6.0 architecture signature depends on this group.

| ID | Question | T12 recommendation | Alternatives | Technical consequence | Depends on | Blocks | Status |
|---|---|---|---|---|---|---|---|
| **A1** | Adopt §§8–15 as the frozen architecture? | **Yes** | Return D14/D19-Tier-2 for re-scope | Re-scope re-opens §§11 and §14 and restarts the freeze package | Group B record | **R6.0** | `OUTSTANDING` |
| **A2** | Treat Tier-1 metering fixes as integrity work, not optional feature work? | **Yes** — BL-01…BL-04/A6/BL-06/BL-07 close live holes | Defer post-v1 | Deferring ships documented under-billing plus a quota leak in v1 accounting | — | **R6.0** | `OUTSTANDING` |
| **A3** | Adopt ADR-1: Option A conditional, explicitly not implemented? | **Yes** (honest freeze) | Redefine target as inline-hardened | Contradicts T8 D14 direction; requires a new ADR | §11 brief | **R6.0** | `OUTSTANDING` |
| **A4** | Adopt T10-1…T10-7 scoping? | **Yes** | Proceed without coupling/tokenizer/null/capability/governor guardrails | Adapter work proceeds without the guardrail set; increases later rework | — | **R6.0** | `OUTSTANDING` |

**Note on A2.** This is the highest-consequence item in Group A. If it is deferred, the defects confirmed by source inspection in §13 (quota under-charge on mixed usage, budget settlement at a partial sum, pre-execution denials misreported as 503 quota outages) ship to production as accepted billing error. It is stated plainly so the decision is made with its cost visible.

---

## 8. Group B — Accounting and Settlement Policy

**All nine items `OUTSTANDING`.** B1 blocks R6.0; B1–B8 block R6.1.

Complete proposed inventory **B1–B9** as required by X-4, including the two rulings T11 §18 omitted.

| ID | Question | T12 recommendation | Alternatives | Technical consequence | Depends on | Blocks | Status |
|---|---|---|---|---|---|---|---|
| **B1** | Adopt ADR-2: T11 §8 I1–I9 as the draft R6.1 foundation contract? | **Yes**, with C-1 name resolution | Require an external R6.1 design doc first | Delay; second authorship of the same contract | §12 brief | **R6.0, R6.1** | `OUTSTANDING` |
| **B2** | Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`? | **Yes** | Include the SabiChat path | Second admission and store surface enters R6.1; scope widens materially | — | **R6.1** | `OUTSTANDING` |
| **B3** | Bypass authority: operator-only, per-route, default-off? | **Yes** | Trusted-service signal | Requires provenance machinery comparable to `sabichat_service_key_id` | T4 flag | **R6.1** | `OUTSTANDING` |
| **B4** | Phase-13 keep-out: R6.1 emits no snapshot fields? | **Yes** | Amend to schema-1.2 now | Pulls Phase-13 coordination inside R6.1 | — | **R6.1** (R6.0 if deferred) | `OUTSTANDING` |
| **B5** | Settlement basis: unknown wins at the full original estimate, never a partial sum? | **Yes** — this is T12 §12's contract | Partial-sum settlement | Partial-sum settlement **is** the confirmed defect; choosing it ratifies the bug | — | **R6.1** | `OUTSTANDING` |
| **B6** | Monotone-shrink **permanent** unless the reservation is re-baselined? | **Yes** | Allow expansion | Expansion breaks reservation authority: the reservation would no longer bound the request | — | **R6.1** | `OUTSTANDING` |
| **B7** | Per-attempt re-derivation of the effective request forbidden? | **Yes** — forbid | Allow re-derivation | Breaks D12 and reservation identity across retries | — | **R6.1** | `OUTSTANDING` |
| **B8** | Adopt the budget terminal-marker pattern (BL-15) transferred from `_QUOTA_RESERVATIONS`? | **Yes** | Design a new state machine | Unnecessary second state machine for an already-solved problem | — | **R6.1** | `OUTSTANDING` |
| **B9** | Reconciler placement: R6.7, with the marker migration in R6.1? | **Yes** | Pull the reconciler into R6.1 | Materially widens R6.1 scope | U9 | Release (not R6.0/R6.1) | `OUTSTANDING` |

**B6 and B7 are the two rulings T11 §18 omitted** (X-4). They are load-bearing for ADR-2 and cannot be left implicit: without B6 the reservation stops bounding the request, and without B7 the effective request changes identity between attempts, which invalidates every settlement argument in T12 §12.

**B5 is the gating decision for U1.** U1 cannot be written without a decided settlement contract; T12 §12 supplies it as a proposal only.

---

## 9. Group C — Capability Recovery and Eligibility

**All four items `OUTSTANDING`.** Group C informs; it does not gate R6.0.

| ID | Question | T12 recommendation | Alternatives | Technical consequence | Depends on | Blocks | Status |
|---|---|---|---|---|---|---|---|
| **C1** | Resolve byok/paid semantics and billing-source scope (BL-30)? | Owner conversation before any BOUNDED+ claim | — | Any BOUNDED+ claim made first would rest on undefined billing semantics | — | Release claims | `OUTSTANDING` |
| **C2** | Exclude non-Latin BM25 relevance claims until Terminal D establishes a corpus? | **Yes** | Claim multilingual now | Unevidenced multilingual claim; not defensible against review | Terminal D | Release (G4) | `OUTSTANDING` |
| **C3** | Gate system/developer-role traffic until role-freeze behaviour is proven (BL-09)? | **Gated** until role-freeze proven | FULL now | Byte-identity unproven for privileged roles | U5 | Partial R6.1 | `OUTSTANDING` |
| **C4** | Extend the proven 2026-10-08 capability probe to `tool_use` and `structured_output` (BL-10)? | **Yes** — repeat a known procedure | Commission new methodology | New methodology is a research project; the established procedure already exists | §4.5 evidence | Release | `OUTSTANDING` |

**C4 is cheap because of X-5.** Three aliases already carry dated 2026-10-08 evidence for `chat`, one for `chat`+`streaming`. BL-10 is a *repeat of an established procedure* on two additional capability keys, not a from-scratch programme.

**No alias promotion follows from any C decision.** The ladder remains `UNKNOWN → UNCALIBRATED → BOUNDED → CALIBRATED`, and nothing in T13 promotes an alias.

---

## 10. Group D — R6.1 Implementation Authorization

**All six items `OUTSTANDING`.** D1, D2, D3 and D5 block R6.1.

| ID | Question | T12 recommendation | Alternatives | Technical consequence | Depends on | Blocks | Status |
|---|---|---|---|---|---|---|---|
| **D1** | **U0 merge policy: strict-xfail, land-with-U1, or skip?** | **Strict xfail** | Land with U1; skip | Land-with-U1 loses independent proof and violates "tests first"; skip proves nothing | §14 spec | **R6.1** | `OUTSTANDING` |
| **D2** | Authorise U0 **separately** under G7, ahead of U1–U12? | **Yes** — test-only and reversible | Bundle with U1 | Bundling forfeits the cheapest risk-reduction available | D1, D3 | **R6.1** | `OUTSTANDING` |
| **D3** | Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7? | **Yes** | Include U12 | Pulls R6.7 forward into R6.1 | — | **R6.1** | `OUTSTANDING` |
| **D4** | Authorise Track A engagement to schedule (BL-21) once T-numbering converges? | **Yes** | Defer | Blocks all Track A surface; nothing touching protected files can start | D5 | **R6.1** | `OUTSTANDING` |
| **D5** | Adopt T11 §15's T1–T8 numbering as canonical? | **Yes** | Use campaign §15's T1–T7 | Ambiguous `T7`; reviewer may sign the wrong artefact (X-3) | §6 | **R6.1** | `OUTSTANDING` |
| **D6** | Re-issue Terminal B/C/D/E prompts (BL-24)? | **Yes** — prompts exist in campaign §13 | Defer | G4/G5 remain blocked | §15–§18 packets | Release | `OUTSTANDING` |

**D3 is the sharpest item.** G7's scope must name `tests/` in words, because U0 appears in no Track A row. Without that text, U0 has no authorisation basis at all — not a weak one, none.

---

## 11. ADR-1 Decision Brief — Telemetry

**Status: `PROPOSED`. Adopting it is decision A3. Adopting freezes a target; it implements nothing.**

### 11.1 Proposed target

- Separate **content-free** table, working name `sabiroute_optimization_records`.
- Primary key `(request_id, attempt_number)`.
- `key_id` and `project_id` NOT NULL.
- Scalar, enum and id columns only — no free text, no message content.
- Frozen builder with `extra="forbid"`.
- **Explicitly not implemented** at `319a711`: no table, builder, projection or writer exists.

### 11.2 Interim behaviour, named honestly

Inline synchronous fail-closed telemetry on the accounting row (`store.py:65–88`) is the **production** behaviour today. It must be described as such in any release note. It is **not** the target and must not be documented as though it were.

### 11.3 Prerequisites — all currently unmet

| ID | Prerequisite |
|---|---|
| **P1** | Non-blocking write convention built and failure-proof tested *before* any optimisation write (BL-17). |
| **P2** | A `key_id`-write predicate mirroring `finalize_usage_event`'s tenant guard (`store.py:1515–1519`); snapshot append is currently request_id-only. |
| **P3** | Additive-only migration following `_SCHEMA_VERSIONS`. |
| **P4** | Extend `_REQUIRED_COLUMNS` so an unmigrated database **fails at startup**, not at first snapshot. |
| **P5** | The full-row admin projection must never gain optimisation columns. |

### 11.4 What the owner is being asked

Not "build this table". The ask is: **freeze the target shape and its tripwires, and label the live system as interim.** The cost of *not* adopting is that the freeze package would either omit a telemetry decision or silently endorse the inline fail-closed shape that T10 rejected.

**If P1 slips, Option A reverts to conditional-with-no-schedule and must be recorded as such** — not silently dropped.

---

## 12. ADR-2 Decision Brief — R6.1 Foundation Contract

**Status: `PROPOSED`. Adopting it is decision B1. It authorises no code.**

### 12.1 Proposed foundation

| Element | Proposed value |
|---|---|
| Contract | **I1–I9** from T11 §8 |
| Package | New `src/sabiroute/request_transform/` |
| Content | Pure functions and value objects |
| Excluded | No registry, no I/O, no provider adapters |
| Construction | **One** construction point, immediately before loop entry at `completions.py:1345` |
| Invariant | **Monotone-shrink** — effective output ≤ original on every path |
| Per-attempt rule | **Re-derivation forbidden**; fallback reuses the effective object |
| Failure semantics | Any I1–I8 exception ⇒ fail-to-original; never 4xx, never partial; `CancelledError` propagates |
| Phase-13 keep-out | R6.1 emits **no** snapshot fields |

### 12.2 The naming conflict, stated

`docs/compression-discovery-packet.md` **exists** (8,645 B, X-1) and names `src/sabiroute/compression/` with a seven-mode registry (`off/lite/standard/aggressive/ultra/rtk/stacked`). This report proposes `src/sabiroute/request_transform/` with a single `OptimizationPolicy`.

**One name must win.** The proposed resolution: adopt `request_transform/` for R6.1 and treat the packet's mode registry as discovery-phase material explicitly **outside R6.1 scope**. This must be recorded as a decision, not assumed — a silent preference here would leave two competing package names in the corpus.

### 12.3 Unresolved items carried forward, not papered over

1. **I2's 250 ms / 2× byte budget is still unspecified.** These are the only quantitative bounds in the contract.
2. **I5's configuration schema is described, not written.**

Neither is fatal to adoption — they bound *implementation*, not the contract's shape — but both must be named in the signature package so they are not mistaken for settled.

### 12.4 Conflicts that must be reconciled before adoption

- **C-1 (naming).** As §12.2.
- **C-2 (insertion point).** CD2's "after final deployment selection" is **superseded**: selection is `choose_deployment` *inside* the loop, so adopting CD2 literally forces per-attempt transformation and breaks B7. This is the one place where the packet is not merely stale but actively incompatible with the proposed contract.
- **C-3 (statuses).** CD4/CD6 (`changed`/`unchanged`/`fallback` + reason; correlation ids) are compatible with I4 — fold in rather than re-derive.

**Scope effect:** adopting ADR-2 *narrows* R6.1 — it excludes `api/chat.py`, registries, provider adapters and all telemetry writes — while fixing the package, file list, U4 unit and Track A surface.

---

## 13. U0 Spec 5 — Independent Source Re-Derivation

**This section re-derives spec 5 from source. It does not carry T12's conclusion forward.** T12 §19.2 explicitly marked this as *requires re-derivation before authoring* and hedged that spec 5 "very likely passes today on the budget-only shape". **T13 reaches the opposite conclusion and identifies the exact misreading that produced T12's hedge.**

### 13.1 The specification under test

> **Spec 5:** a **budgeted** request whose first attempt fails with **known** usage, then a second attempt **succeeds with no usage reported**, must **hold the original estimate** and return **HTTP 200**.

### 13.2 Required trace, executed in order

| # | Step | Anchor | Observed behaviour |
|---|---|---|---|
| 1 | Initial value of the unknown-usage flag | `completions.py:1316` | `provider_usage_unknown = False` |
| 2 | Attempt 1 fails, usage extracted | `:1567` | `failure_usage = _actual_tokens(exc.response_body)` |
| 3 | **Does attempt 1 set the flag?** | `:1568–1574` | **NO** — see §13.3 |
| 4 | Retry eligibility | `:1599–1601` | `retryable = status is None or status >= 500 or status in RETRYABLE_STATUS_CODES` (`RETRYABLE_STATUS_CODES = {401, 403, 429}` at `:59`); break only if `not retryable or (budget_reserved and provider_usage_unknown)` |
| 5 | Budget narrowing before retry | `:1603–1608` | `used = sum(known totals)`; `remaining = reserved_tokens - used`; break if `remaining <= estimated_input`; else `max_tokens` narrowed and retry proceeds |
| 6 | Attempt 2 succeeds with no usage | `:1903` | `success_usage = _actual_tokens(body)` → **`None`** (`_actual_tokens` returns None when no usage object, `:241–242`) |
| 7 | Does success set the flag? | `:1904–1911` | **NO** — `if success_usage is not None:` is False; the flag is never touched on the success path |
| 8 | Settlement value passed to `finish()` | `:1945–1953` | `tokens = (None,None,None) if provider_usage_unknown else _sum_actual_tokens(actual_usage_parts)` → flag is `False`, so **partial sum** |
| 9 | Budget settlement | `finish()` `:563–583` → `store.reconcile_budget` `:1213` | `actual_tokens` is not None ⇒ `accounted_tokens = actual_tokens` ⇒ **settled at attempt 1's total only** |
| 10 | HTTP response | `:1940–1944` | `JSONResponse(status_code=200, ...)` |
| 11 | Usage telemetry event | `:1948–1950` | records the partial sum, not the estimate |

### 13.3 The decisive line — why the flag is never set

```python
failure_usage = _actual_tokens(exc.response_body)          # :1567
if failure_usage is not None:                              # :1568  ← 12 spaces
    actual_usage_parts.append(failure_usage)               # :1569
    cost_usage_parts.append((..., failure_usage))          # :1570
    if failure_usage[2] is None:                           # :1571  ← 16 spaces
        provider_usage_unknown = True                      # :1572
elif budget_reserved:                                      # :1573  ← 12 spaces
    provider_usage_unknown = True                          # :1574
```

The `elif` at `:1573` is attached to the **outer** `if` at `:1568`. Therefore:

| Attempt-1 failure shape | Outer `if` `:1568` | Inner `if` `:1571` | `elif` `:1573` | Flag set? |
|---|---|---|---|---|
| Usage present, **total known** — *this is "known-fail"* | True | **False** | **not evaluated** | **NO** |
| Usage present, total unknown | True | True | not evaluated | Yes |
| **No usage object at all** | False | — | True (if budgeted) | Yes |

**Spec 5 names the first row.** A *known* failure sets no flag anywhere in the file. The flag is therefore already `False` when attempt 2 begins, and the success path never sets it either.

### 13.4 Why T12 reached the opposite conclusion

T12 §19.2 reasoned that "attempt 1's failure sets the flag at `:1572` (ungated when the error body has a total-less usage object) or `:1574` (budget-only)". The phrase *"budget-only"* treats `:1573` as firing whenever the request is budgeted. It does not: `:1573` is an `elif` on `failure_usage is not None`, so it fires only when the failure body carries **no usage object**. T12 further assumed the flag "survives attempt 2's success" — **that part is correct** (`:1904` never clears it) — but survivorship is irrelevant when the flag was never set.

The error is narrow, mechanical and consequential: it would have produced a test written against a false premise, passing immediately, and conveying false assurance — precisely the risk T12 itself flagged.

### 13.5 Verdict

| Question | Answer |
|---|---|
| Does spec 5 fail deterministically? | **Yes** — under a fixture that pins (a) attempt 1's failure is **retryable** (status ≥ 500, or in `{401,403,429}`), (b) attempt 1 carries **known** usage, (c) the reservation is large enough that `remaining > estimated_input` so the retry is not blocked at `:1606`. |
| Does it already pass? | **No.** |
| Does it pass for one governor combination? | **No — it fails on the budget path.** The quota path fails for its own reason (A5/A2) and is covered by specs 1 and 2. |
| Is it insufficiently specified? | **Partly, and that must be fixed.** T11 did not pin conditions (a)–(c). Without them the fixture can silently take the no-retry branch and test nothing. |

**Authoring instruction:** spec 5 is a **`xfail(strict=True)`** case with the three conditions pinned explicitly in the test body and in the marker reason. It is **not** to be skipped, omitted, or authored as a passing test.

**Evidence class:** `STATIC-ANALYSIS FINDING` for the runtime consequence; `VERIFIED` for every anchor and control-flow claim above. No test was executed.

---

## 14. U0 Strict-xfail Test Specification

**Specification only. `NOT EXECUTED`. Nothing was written to disk. No test file was modified.**

### 14.1 Placement and inheritance

| Element | Specification |
|---|---|
| Files | `tests/test_user_quotas.py` (**extend**), `tests/test_phase10.py` (**extend**) — **no new file**, to inherit existing fixtures |
| Verified sizes | 21,722 B and 30,804 B `VERIFIED` |
| Fixtures | **Existing only** — no new mock infrastructure (`VERIFIED` anchors below) |
| Provider access | None. No network. No provider call. |

**Fixture anchors verified at HEAD:**

| Fixture | Anchor |
|---|---|
| `InMemoryApiKeyStore` | `tests/conftest.py:26` |
| `StubLiteLLMClient` | `tests/conftest.py:374` |
| `_make_quota_and_budget_harness` | `tests/conftest.py:753` |
| `test_repeated_cancellation_during_budget_cleanup_completes_quota_and_finalizes` | `tests/conftest.py:792` |
| `test_unknown_usage_holds_estimate` (the all-unknown control) | `tests/test_user_quotas.py:187` |

### 14.2 Defect cases — to be marked `xfail(strict=True)`

| ID | Case | Attempt sequence | Expected (post-fix) | Actual at baseline | Blocker |
|---|---|---|---|---|---|
| **X5** | **Budgeted known-fail → no-usage-success** | Attempt 1: retryable failure, **known** usage. Attempt 2: 200, **no usage object**. Reservation large enough that `remaining > estimated_input`. | Budget settled at the **original estimate**; response **200** | Settled at attempt 1's **partial sum**; response 200 — estimate not held | BL-03 / A2 |
| **X1** | Mixed **known → unknown**, quota governor | Attempt 1: known usage. Attempt 2: unknown usage. | Quota `consumed_tokens == original estimate`; usage event `total_tokens is None` | Partial sum settled as complete | BL-01 / A5 |
| **X2** | Mixed **unknown → known**, quota governor | Attempt 1: unknown usage. Attempt 2: known usage. | Same as X1 | Flag `False` ⇒ partial sum charged | BL-02 / A1 |
| **X6** | **Pre-loop quota-held + budget-denied** | Quota reserved; budget denial before loop entry; first `finish()` call | True denial status returned; quota reservation **released**, zero leak | `NameError` swallowed ⇒ **503 `QUOTA_UNAVAILABLE`**, `quota_reserved` never cleared | BL-04 / A3 |

**Marker form for every case above:**

```python
@pytest.mark.xfail(strict=True, reason="BL-0x: <concise defect description>")
```

The reason string must name the blocker. A fix that silently stops failing the test is caught by `strict=True`; that is the intended mechanism.

### 14.3 Controls — must **pass** and must not be marked xfail

| ID | Control | Assertion | Why it matters |
|---|---|---|---|
| **Ctl-1** | **All-unknown usage** (`test_unknown_usage_holds_estimate`, `tests/test_user_quotas.py:187`) | Estimate retained; `total_tokens is None` | Guards against a fix that over-corrects by holding the estimate on *every* request |
| **Ctl-2** | **Duplicate settlement idempotency** | Settling twice produces one accounting effect | Guards against a fix that double-charges |

**Applying `xfail` to a currently-passing test is forbidden.** All-unknown is *correct today* — `reconcile_budget` receives `None` and, with empty `values`, performs no update at all, leaving the estimate in place. Marking it xfail would invert its meaning.

### 14.4 Per-case specification template

Each authored test must state, in its body: fixture used; setup; the exact attempt sequence (status, usage presence, and usage shape per attempt); expected behaviour; actual behaviour at baseline; the assertions; the blocker reference; and the U1 acceptance behaviour (what flips the marker from strict-xfail to strict-pass).

### 14.5 Acceptance criteria for the U0 package

1. Suite **green with** the xfail markers in place.
2. Every xfail reports its `BL-0x` in the reason string.
3. **No production file touched** — the diff is confined to `tests/`.
4. Both controls present and passing.
5. Rollback is total: deleting the added tests removes the entire change, with no source dependency.

### 14.6 Condition changed by T13

T12 §24.1 listed spec 5's re-derivation as a *condition* on U0 readiness. **T13 has discharged it** (§13). U0's remaining conditions are therefore **two**, not three: **D1** (merge policy) and **D3** (G7 naming `tests/`). This is the only place where T13 documentation work **reduces** an outstanding condition — and it reduces authoring risk, not authority. U0 is still **not authorised**.

---

## 15. Terminal B Evidence Packet

**Draft only. `NOT ISSUED`. Lane status: `NOT OBTAINED`.**

| Field | Content |
|---|---|
| **Reviewer lane** | Terminal B — independent red-team review. |
| **Question to adjudicate** | Are the settlement and accounting invariants in T12 §12 (I1–I9 and the unknown-wins contract) implemented such that no request can be settled at a partial sum when any attempt's usage is unknown, and is the claimed attack surface complete? |
| **Relevant sections** | T12 §§5–12, §13.1; T13 §13, §14. |
| **Source anchors** | `completions.py:1567–1574`, `:1599–1608`, `:1903–1954`, `:563–595`; `store.py:1213–1247` (`reconcile_budget`), `:1343` (`settle_quota`), `:1392` (`release_quota`). |
| **Artefact version** | Branch `feat/sabiroute-routing-foundation`, commit `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`. Reviewers must state this digest in their record or the finding is not re-anchorable. |
| **Expected output** | A finding set: each finding with severity, the invariant violated, a minimal reproduction, and the anchor it applies to. |
| **Evidence requirements** | Findings must cite code at the stated commit. Reasoning without an anchor is noted but not counted as a finding. |
| **Explicit exclusions** | Does not adjudicate benchmark corpus, multilingual relevance, or B1 mechanical correctness. Does not authorise fixes. |
| **Acceptance criteria** | A named record exists, names the commit reviewed, and lists findings — including "no findings" as an explicit finding set, not silence. |

**Status discipline.** Silence from this lane is not approval, not acceptance, and not absence of findings.

---

## 16. Terminal C Evidence Packet

**Draft only. `NOT ISSUED`. Lane status: `NOT OBTAINED`.**

| Field | Content |
|---|---|
| **Reviewer lane** | Terminal C — independent red-team review (second, distinct from B). |
| **Question to adjudicate** | Does the retry and fallback policy permit a request to exceed its reservation, re-derive its effective request mid-flight, or degenerate the unknown-usage signal into a partial settlement — and are the O2 pinning and governor interactions correctly reasoned? |
| **Relevant sections** | T12 §11 (reservation lifecycle, three-way asymmetry), §13.1; T13 §8 (B5–B8). |
| **Source anchors** | `completions.py:1308–1316`, `:1345–1610`, `:1601`, `:1603–1608`, `:1693`, `:1812`; `budgets.py:16–40`. |
| **Artefact version** | Branch `feat/sabiroute-routing-foundation`, commit `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`. |
| **Expected output** | A finding set covering reservation bound, retry identity, and settlement basis. |
| **Evidence requirements** | Anchored at the stated commit. Distinguish confirmed defect from unproven suspicion. |
| **Explicit exclusions** | Does not adjudicate benchmark corpus or multilingual claims. Does not authorise fixes. Does not overlap Terminal B's settlement-invariant adjudication; C owns retry/fallback lifecycle. |
| **Acceptance criteria** | Named record, commit named, explicit finding set. |

---

## 17. Terminal D Evidence Packet

**Draft only. `NOT ISSUED`. Lane status: `NOT OBTAINED`. This lane feeds G4.**

| Field | Content |
|---|---|
| **Reviewer lane** | Terminal D — benchmark corpus and comparability keys. |
| **Question to adjudicate** | Is there a benchmark corpus, with comparability keys, sufficient to support any B2 provider-dependent claim — prompt-token reduction, provider usage, latency, cost, per-alias estimation error — and any multilingual (BL-19) relevance claim? |
| **Relevant sections** | T12 §21 (B1 vs B2, pricing absence, freeze-versus-defer split); T13 §9 (C2). |
| **Source anchors** | `config/config.yaml` (no `input_cost`/`output_cost`/`pricing` keys — `VERIFIED`); `security/budgets.py:16–40` (`estimate_input_tokens`). |
| **Artefact version** | Branch and commit `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`; corpus version to be assigned by this lane and recorded. |
| **Expected output** | A versioned corpus plus comparability keys, and an explicit statement of which B2 metrics it can and cannot support. |
| **Evidence requirements** | Corpus version, sampling procedure, comparability keys, and the metric-to-corpus mapping. |
| **Explicit exclusions** | **Terminal D governs benchmark corpus claims and multilingual evidence. It does not govern B1 mechanical correctness.** No non-Latin BM25 relevance claim may be made until this lane proves a corpus. |
| **Acceptance criteria** | A named record with a corpus version and comparability keys, re-anchorable to this commit. |

**Firewall restated.** B1 (offline, mechanical: request correctness, message-structure preservation, protected-content preservation, accounting invariants, tenant isolation, retry consistency, resource bounds, fail-to-original) is **constructible entirely offline** and is unaffected by Terminal D. Terminal D cannot be used to validate or invalidate B1.

---

## 18. Terminal E Evidence Packet

**Draft only. `NOT ISSUED`. Lane status: `NOT OBTAINED`.**

| Field | Content |
|---|---|
| **Reviewer lane** | Terminal E — independent verification and scorecard attestation. |
| **Question to adjudicate** | Do the verification claims in the R6 freeze package (T11 §§19–20, T12 §§23–24, T13 §19) accurately describe the artefact at the stated commit, with no claim exceeding its evidence class? |
| **Relevant sections** | T12 §23, §24, §26; T13 §3, §19, §22, §23. |
| **Source anchors** | The full verified-anchor list in T12 §26.5 and T13 §3. |
| **Artefact version** | Branch and commit `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`. |
| **Expected output** | A verification record attesting which claims are supported, which are overstated, and which are unverifiable — per claim, not in aggregate. |
| **Evidence requirements** | Per-claim verdicts with anchors. An aggregate "verified" without per-claim detail does not satisfy this lane. |
| **Explicit exclusions** | Does not produce findings about code defects (that is B/C) or corpus adequacy (that is D). Does not sign R6.0. |
| **Acceptance criteria** | A named attestation record with per-claim verdicts, re-anchorable to this commit. |

**E does not substitute for the owner's signature.** An attestation that the package is internally accurate is not an approval of the architecture.

---

## 19. R6.0 / R6.1 / G7 Gate Reassessment

T13 preparation **changes no gate status**. Reassessment against T12 §§23–24:

| Gate | Status | Basis |
|---|---|---|
| **R6.0 architecture freeze** | **CONDITIONALLY READY** | Three owner-only conditions remain (§19.1). The decision package being *prepared* does not freeze the architecture. |
| **R6.1 overall** | **NOT READY** | Nine conditions from T11 §6 stand; accounting correctness is the binding constraint. |
| **U0** | **READY FOR SEPARATE OWNER AUTHORIZATION** | Conditions reduced from three to **two** by T13 (§14.6). |
| **U1** | **NOT READY** | Requires U0 green-with-xfail; B5/B6/B7 decided; Track A T2/T7; G7 granted. |
| **G7** | **NOT GRANTED** | Never requested. Cannot be requested by a review report. |
| **Track A** | **NOT OBTAINED** | No reviewer contacted. |
| **Terminal B/C/D/E** | **NOT OBTAINED** | Packets drafted (§15–§18), none issued. |

### 19.1 R6.0's three remaining conditions

1. **Adopt ADR-1** (Group A3).
2. **Adopt ADR-2** (Group B1), including the C-1 package-name resolution.
3. **Record Group A + Group B decisions, then sign BL-22.**

### 19.2 Explicit non-conclusions

- R6.0 is **not** fully frozen because the decision package exists. A prepared decision is not a taken decision.
- U0 is **not** authorised because its specification is ready. Ready ≠ authorised.
- The Terminal packets are **not** reviews. A drafted question is not an obtained record.
- G7 is **not** implied by approval readiness. Only the owner can record it.

### 19.3 The X-6 correction is permanent

Condition 17 (rollout) stays **CONDITIONAL**, corrected from T11's PASS to **SPECIFIED, UNBUILT**. This does not block architecture approval — the design is right and implementation is a U4 unit — but the signature package must not claim runtime verification it does not have.

---

## 20. Outstanding Owner Actions

Every item below is `OUTSTANDING`. **None is approved by T13.**

| # | Action | Decision ID | Blocks |
|---|---|---|---|
| 1 | Adopt §§8–15 as frozen architecture | A1 | R6.0 |
| 2 | Rule Tier-1 metering fixes as integrity work | A2 | R6.0 |
| 3 | Adopt ADR-1 (Option A conditional, not implemented) | A3 | R6.0 |
| 4 | Adopt T10-1…T10-7 scoping | A4 | R6.0 |
| 5 | Adopt ADR-2 with C-1 name resolution | B1 | R6.0, R6.1 |
| 6 | Rule R6.1 scope = `chat/completions` only | B2 | R6.1 |
| 7 | Rule bypass authority operator-only, per-route, default-off | B3 | R6.1 |
| 8 | Confirm Phase-13 keep-out | B4 | R6.1 |
| 9 | Adopt unknown-wins settlement at full estimate | B5 | R6.1 |
| 10 | Make monotone-shrink permanent | B6 | R6.1 |
| 11 | Forbid per-attempt re-derivation | B7 | R6.1 |
| 12 | Adopt budget terminal-marker pattern | B8 | R6.1 |
| 13 | Place reconciler in R6.7 with marker migration in R6.1 | B9 | Release |
| 14 | Resolve byok/paid and billing-source semantics | C1 | Release claims |
| 15 | Exclude non-Latin relevance claims pending Terminal D | C2 | Release (G4) |
| 16 | Gate system/developer-role traffic | C3 | Partial R6.1 |
| 17 | Extend the capability probe to `tool_use`/`structured_output` | C4 | Release |
| 18 | **Decide U0 merge policy** | D1 | R6.1 |
| 19 | Authorise U0 separately ahead of U1–U12 | D2 | R6.1 |
| 20 | Define G7 scope naming `tests/` | D3 | R6.1 |
| 21 | Authorise Track A engagement to schedule | D4 | R6.1 |
| 22 | Adopt the T1–T8 numbering | D5 | R6.1 |
| 23 | Re-issue Terminal B/C/D/E prompts | D6 | Release |
| 24 | Sign BL-22 (R6.0 written approval) | — | R6.0 |
| 25 | Correct CLAUDE.md §12 at source (separately authorised) | — | Documentation |

**Item 24 is not a Group decision; it is the signature act that follows Group A and B being recorded.** Item 25 is a T13 finding, not an R6 gate.

**Recommended session order** (recommendation, not a decision): A3 and B1 first — they are the two ADRs and they gate the signature — then A1, A2, A4, B2–B9, then C, then D. D1 and D3 can be settled independently at any point and unblock U0 without touching the architecture questions.

---

## 21. Outstanding External Actions

All `NOT OBTAINED`. **No reviewer was contacted and no prompt was sent.**

| # | Action | Lane | Feeds | Blocks |
|---|---|---|---|---|
| 1 | Issue and obtain Terminal B record | Independent red-team | G5 | Release |
| 2 | Issue and obtain Terminal C record | Independent red-team | G5 | Release |
| 3 | Issue and obtain Terminal D corpus + comparability keys | Benchmark | G4, BL-19 | Release |
| 4 | Issue and obtain Terminal E attestation | Verification | Scorecard | Release |
| 5 | Obtain Track A sign-off T1–T8 | External review | R6.1 start | R6.1 |
| 6 | Complete the 2026-10-08 capability probe extension for `tool_use`/`structured_output` | Provider evidence | C4, BL-10 | Release |

**Silence is not a result.** `NOT OBTAINED` remains the only correct label until a record exists.

---

## 22. Verification and Worktree Report

### 22.1 What was created

Exactly one file: `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md`. No other file was created, renamed, moved or deleted.

### 22.2 What was modified

**Nothing else.** No existing report, source file, test, config, migration, dataset or dependency file was modified. CLAUDE.md was deliberately left untouched (§5).

### 22.3 Safety boundary verification

| Boundary | Result |
|---|---|
| HEAD unchanged | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` |
| Branch unchanged | `feat/sabiroute-routing-foundation` |
| Staged | empty |
| Unstaged tracked changes | empty |
| `src/`, `tests/`, `config/`, `scripts/`, `migrations/` | zero modifications |
| Commit / push / stage / reset / clean / stash / prune / rebase | none performed |
| Fetch / pull / merge | none performed |
| Prior reports preserved | all six present, sizes unchanged |
| Reviewer contact | none |
| Tests executed | none |

### 22.4 What was independently re-derived (not inherited)

| Claim | Method |
|---|---|
| Spec 5 fails (§13) | Full control-flow trace across `completions.py:1316, 1567–1574, 1599–1608, 1903–1911, 1945–1953, 563–595` and `store.py:1213–1247` |
| `_actual_tokens` returns `None` without a usage object | `completions.py:239–250` |
| `_sum_actual_tokens` sums known parts into a partial sum | `completions.py:253–264` |
| `reconcile_budget` performs no update when both values are `None` | `store.py:1213–1247` |
| `finish()` has no `attempted` parameter; it is a free variable bound at `:1311` | `completions.py:542–550`, `:602`, `:1311` |
| 14 aliases and their capability anchors | `config/config.yaml` direct read |
| Zero rollout apparatus | `grep` over `src/` and `config/` |
| Gate definitions | `r6-t9:417`, campaign `:332` read verbatim |
| T11 §18 enumerates 15, §1 claims 12 | Direct enumeration and `r6-t11:33` |
| Fixture anchors | `tests/conftest.py:26, :374, :753, :792`; `tests/test_user_quotas.py:187` |

### 22.5 Evidence-class summary

| Class | Scope |
|---|---|
| `VERIFIED` | Baseline, all anchors above, config, fixtures, gate definitions, document sizes |
| `STATIC-ANALYSIS FINDING` | Spec 5 failure, A3 reachability and its 503 consequence, mixed-settlement arithmetic |
| `PROPOSED` | All 23 decisions, both ADRs, the T1–T8 mapping, all four Terminal packets |
| `NOT EXECUTED` | Any test, any provider call, any runtime confirmation, any benchmark |

---

## 23. Explicit Limitations and Final Status

### 23.1 What T13 did not establish

- **No runtime confirmation.** Every behavioural claim is static. Spec 5's failure is established by control-flow inspection, not by an executed test.
- **No test authored.** §14 is a specification; the tests do not exist.
- **No implementation.** U0, U1 and R6.1 are untouched.
- **No owner decision recorded.** All 23 remain `OUTSTANDING`.
- **No external record obtained.** Track A and Terminals B/C/D/E remain `NOT OBTAINED`.
- **No reviewer contacted.**
- **CLAUDE.md not corrected.** The §12 finding is recorded, not fixed.
- **No fetch or reconciliation** of the divergent branch; all anchors are local to `319a711`.

### 23.2 Honest gaps carried forward

- T12's `:1601` hardening rationale (BL-02) was not re-derived by T13 and is carried on T12's authority.
- The A4 finding (`cleanup_errors` / `ledger` written but never read) was not re-derived by T13; T12 §26.6 records its own independent re-verification.
- A per-transition partial-persistence matrix for the reservation lifecycle remains unbuilt.
- No file-level U1–U12 mapping exists beyond the dependency table.

### 23.3 The one place T13 contradicts its predecessor

**T12 §19.2's hedge on spec 5 ("very likely passes today on the budget-only shape") is incorrect.** §13 states the corrected position with the exact misreading identified. This is recorded prominently because T12's own verification apparatus was otherwise sound, and a silent divergence would be worse than a documented one. Anyone who cited T12 §19.2's hedge must re-read §13 before authoring U0.

### 23.4 Authority statement

This report is decision support only. It approves nothing, adopts no ADR, grants no G7, authorises no implementation, and records no owner decision. **Silence from any reviewer is not approval.** A recommendation is not a decision, and a prepared decision is not a taken one.

---

**FINAL STATUS: T13 COMPLETE — DECISION PACKAGE READY; OWNER ADJUDICATION OUTSTANDING; NO GATE GRANTED.**

**Next action belongs to the owner:** adjudicate the 23 proposed decisions, resolve ADR-1 and ADR-2, and explicitly decide whether to sign R6.0 and separately authorise G7/U0. T13's job was to make those decisions informed, precise and safe — not to make them.

---
---

# T14 Independent Audit Corrections — C-01 to C-08

**Integrated by T15.** This section is **additive**. It rewrites, deletes and re-grades nothing above it. Where a correction restates a T13 claim, the **original wording is preserved verbatim** in the record so the audit trail stays intact and the change is visible rather than silent.

**Status of this section:** documentation integration only. It approves nothing, adopts no ADR, selects no option, grants no gate, and authorises no implementation or test work. Every owner decision named below remains `OUTSTANDING`.

**Authority:** `docs/r6-t14-independent-t13-audit-and-decision-readiness.md` (T14) — verdict `READY WITH CORRECTIONS`. Every anchor below was **re-verified against the working tree at `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` during T15**; none is carried on T14's authority alone.

**Effect on T13's own verdict: none.** The `FINAL STATUS` block immediately above is the record of T13's status and is **not superseded** by this annotation. No correction below changes a gate, a verdict, an ADR status or any decision's status. C-07 widens the *scope* of a future fix; it does not change what is currently true.

### Integration summary

| ID | T13 location | Class | Severity | Integration |
|---|---|---|---|---|
| C-01 | §4.3 (X-2) | Wording / precision | Low | Integrated — restated, original preserved |
| C-02 | §19.1 condition 3 vs §8 | Governance clarity | Medium | Integrated as clarification; underlying inconsistency left **open for owner** |
| C-03 | §10 D3; §9 C1; §8 B1 | Decision quality | Medium | Integrated as annotation; no option invented |
| C-04 | §13.5 / §14.2 X5 | Test soundness | Medium | Integrated — three additive fixture conditions |
| C-05 | §14.2 X6 | Defect scope | Medium | Integrated — trigger widened, original preserved |
| C-06 | §14.6 | Wording | Low | Integrated — restated, original preserved |
| C-07 | §14.2 X2 | **Technical** | **High** | Integrated — mechanism corrected, original preserved |
| C-08 | §19.3 / §11.2 | Precision | Low | Integrated — additive nuance |

---

### C-01 · "Three colliding namespaces" overstates the defect

| Field | Content |
|---|---|
| **T13 section** | §4.3, heading "The three colliding namespaces `VERIFIED`", and the X-2 row "Real defect is namespace collision". |
| **T14 finding** | Only **two** scales actually collide on the G-identifiers G4/G5/G7. The third is a separate lettered vocabulary. |
| **Original T13 wording (preserved)** | §4.3 — "The three colliding namespaces `VERIFIED`" with rows R6, Developer Workflow Overhaul, Repository remediation (A–E). X-2 — "**Actual defect:** A **namespace collision** between three gate scales, not a governance gap. Three overlapping scales exist (§4.3 below)." |
| **Corrected statement** | **Two colliding G-scales plus one separate lettered gate scale.** R6: G4 = benchmark, G5 = red-team, G7 = implementation authorisation. Developer Workflow Overhaul: G4 = deadline/retries, G5 = async lifecycle, G7 = deployment/security — a **genuine collision**. Repository remediation uses gates **A–E** with **no G4/G5/G7**; T13's own §4.3 row already leaves those cells as "—". It is a third *vocabulary*, not a G-number collision. |
| **Evidence / anchor** | `docs/r6-t9-capability-recovery-review.md:417`; `docs/r6-decision-resolution-and-approval-campaign.md:332`; `SabiRoute_Developer_Workflow_Overhaul_Plan.md:239–247` (G4/G5/G7 confirmed verbatim); `reports/remediation-roadmap-and-gates.md` §2 "Release gates" — Gate A–E confirmed, no G-identifiers. All re-read at `319a711` during T15. |
| **Severity** | Low (precision) |
| **Dependency / owner decision** | None. Citation hygiene only. Does not touch any decision ID. |
| **Integration status** | **INTEGRATED** — additive. §4.3's table is unchanged; this entry is the correction of record. The recommendation (a disambiguating gate register) stands. |

---

### C-02 · R6.0 condition 3 and the §8 table disagree

| Field | Content |
|---|---|
| **T13 section** | §19.1 condition 3 against §7/§8's "Blocks" column and §20. |
| **T14 finding** | AF-14 — §8 marks only **B1** as blocking R6.0 (B2–B8 block R6.1; B9 blocks Release), but condition 3 reads "Record **Group A + Group B** decisions" — which would make all nine Group B items R6.0 conditions. |
| **Original T13 wording (preserved)** | §19.1 — "3. **Record Group A + Group B decisions, then sign BL-22.**" |
| **Corrected statement** | Two readings are live and the owner must choose one; T15 does not choose. Either **(a)** condition 3 becomes "Record the Group A decisions **and B1**, then sign BL-22" — matching the tables — or **(b)** B2–B9 are explicitly re-labelled "R6.0-adjacent" and the session is designed to record all of Group B before signature. Recording B2–B9 at the same session is harmless under either reading, so this is a clarity defect, not a scheduling trap. |
| **Evidence / anchor** | T13 §7 (A1–A4 all "Blocks R6.0"), §8 (only B1 "Blocks **R6.0, R6.1**"), §19.1 condition 3, §20 items 1–5 and 24. Read in full at `319a711`. |
| **Severity** | Medium (governance clarity) |
| **Dependency / owner decision** | **Owner-visible before BL-22 signature.** This is not a new decision ID; it is a pre-condition to reading condition 3 unambiguously. Left unresolved, the signature act has two possible scopes. |
| **Integration status** | **INTEGRATED** as clarification. The inconsistency is **not** silently repaired — repairing it would require choosing (a) or (b), which is the owner's call. |

---

### C-03 · Three decisions bundle independent choices or lack alternatives

| Field | Content |
|---|---|
| **T13 section** | §10 **D3**; §9 **C1**; §8 **B1**. |
| **T14 finding** | AF-15 — **D3** bundles three separately consequential choices; **C1** has **no recommendation and no alternatives**; **B1** couples ADR-2 adoption to one of ADR-2's own unresolved conflicts. |
| **Original T13 wording (preserved)** | D3 — "Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7?" C1 — "Resolve byok/paid semantics and billing-source scope (BL-30)?" with recommendation and alternatives both "—". B1 — "Adopt ADR-2: T11 §8 I1–I9 as the draft R6.1 foundation contract?" recommendation "**Yes**, with C-1 name resolution". |
| **Corrected statement** | **D3** contains three decisions: (i) G7 scope = U0–U11; (ii) explicit `tests/` naming; (iii) U12 placement in R6.7. They may be recorded together but must be **answerable separately** — an owner may accept (ii) and reject (iii). **C1** is an open conversation, not a binary: it needs an owner-supplied position, and no option may be invented for it. **B1** cannot be cleanly answered while C-1 (§12.4 naming) is unsettled. |
| **Evidence / anchor** | T13 §8 (B1 row), §9 (C1 row), §10 (D3 row), §12.2 ("One name must win… must be recorded as a decision, not assumed"), §12.4 C-1. Read at `319a711`. |
| **Severity** | Medium (decision quality) |
| **Dependency / owner decision** | D3 → D2 (U0 authorisation reads its scope). B1 → C-1 must be recorded first or B1 splits into two answers. C1 unblocks nothing mechanically. |
| **Integration status** | **INTEGRATED** as annotation. No option, alternative or recommendation has been invented — C1's gap is **reported**, not filled. |

**T15 identifier-collision warning (new, not in T14).** §12.4 names the ADR-2 conflicts **`C-1`, `C-2`, `C-3`** (hyphenated). §9 names the Group C decisions **`C1`, `C2`, `C3`, `C4`** (unhyphenated). These are **different registers with near-identical labels**. B1's text says "with C-1 name resolution" — the **hyphenated** ADR-2 conflict — but a reader scanning Group C will land on **C1** (byok/paid billing semantics), which has nothing to do with package naming. Recorded here so the owner session cannot conflate them. T15 does not rename either register; renaming would edit identifiers the owner has already been asked to adjudicate.

---

### C-04 · Spec 5 fixtures need three more conditions

| Field | Content |
|---|---|
| **T13 section** | §13.5 (spec 5's three pinned conditions), §14.2 X5, §14.4 (per-case template). |
| **T14 finding** | AF-03 addendum — T13 pins (a) retryable failure, (b) known usage, (c) `remaining > estimated_input`. Three more conditions are required or the test can pass or fail for the wrong reason. |
| **Corrected statement** | Add to every spec-5/X5 fixture: **(d)** quota absent or oversized, so the **budget** governor is the one under test rather than the quota governor; **(e)** the second attempt carries **no usage object at all**, not merely a missing `total`; **(f)** the primary assertion targets the **budget reservation row** (`accounted_tokens == original estimate`) **and** the usage event (`total_tokens is None`) — not only HTTP 200. |
| **Evidence / anchor** | (d) T13 §13.5 already notes the quota path "fails for its own reason" — the fixture must isolate budget. (e) `completions.py:245–247` — `_actual_tokens` **synthesises** `total = prompt + completion` when `total` is absent and both components are valid, so a total-less-but-complete usage object does **not** produce an unknown-usage part. Verified at `319a711`. (f) status alone cannot distinguish held-estimate from partial-sum. Fixture anchors re-verified: `tests/conftest.py:26` `InMemoryApiKeyStore`, `:374` `StubLiteLLMClient`, `:753` `_make_quota_and_budget_harness`, `:792` the cancellation test; `tests/test_user_quotas.py:187` `test_unknown_usage_holds_estimate`. |
| **Severity** | Medium (test soundness) |
| **Dependency / owner decision** | Feeds D1 (U0 merge policy) and the U0 package. No decision changes. |
| **Integration status** | **INTEGRATED** — additive. Conditions (a)–(c) stand as written; (d)–(f) extend them. |

---

### C-05 · X6's trigger is all eight pre-loop `finish()` sites, not "budget-denied"

| Field | Content |
|---|---|
| **T13 section** | §14.2 **X6** row. |
| **T14 finding** | AF-04 — the reachable window is **eight** pre-loop `finish()` call sites, not only budget denial. Consequence class identical; trigger set wider. |
| **Original T13 wording (preserved)** | X6 — "**Pre-loop quota-held + budget-denied** … Quota reserved; budget denial before loop entry; first `finish()` call … `NameError` swallowed ⇒ **503 `QUOTA_UNAVAILABLE`**, `quota_reserved` never cleared". |
| **Corrected statement** | The trigger is **any** of the eight pre-loop `finish()` sites reached while a quota reservation is held: `:1171`, `:1180`, `:1189` (eligibility denials), `:1205` (budget pricing), `:1272` (budget reservation unavailable), `:1282` (budget changed), `:1291` (budget pricing), `:1299` (budget exceeded, a **429**). |
| **Binding-order defect, stated exactly** | `finish()` (`completions.py:542–550`) takes **no `attempted` parameter**; it declares `nonlocal budget_reserved, quota_reserved` (`:551`) but **not** `attempted`. It **reads** `attempted` at `:602` (`if attempted:`). `attempted` is bound at `:1311` (`attempted: list[str] = []`). The quota is reserved earlier, at `:1161` (`quota_reserved = True`), with `quota_user_id` at `:1162`. Every site between `:1161` and `:1311` therefore reaches `:602` with an **empty closure cell** ⇒ `NameError`. |
| **Consequence chain, kept distinct** | The `NameError` is caught by `except Exception as exc:` at `:623`, which (1) logs and appends the cleanup-failure record; (2) **replaces the intended response** with `_error_response(503, "Quota reservation could not be reconciled.", QUOTA_UNAVAILABLE)`; (3) **skips** `quota_reserved = False` at `:620`, so the reservation is never released on that path. |
| **Outcomes are NOT identical across the eight sites** | The masking requires **both** a held quota **and** a pre-loop early return. `if attempted:` at `:602` is only reached inside `if quota_reserved and quota_user_id is not None:` (`:596`). With **no** quota reserved, the block is skipped, no `NameError` occurs, and each site returns its **true** status. With a quota held, all eight are masked to the same 503 shape — including turning `:1299`'s **429 `budget_exceeded`** into a 503 quota outage. T15 asserts the masking only for the quota-held case and claims **no** runtime reproduction. |
| **Evidence / anchor** | `completions.py:542–551`, `:596`, `:602`, `:620`, `:623`; `:1161–1162`; `:1311`; the eight sites `:1171, :1180, :1189, :1205, :1272, :1282, :1291, :1299` — each re-read at `319a711` during T15 and each confirmed to be `return await finish(`. |
| **Severity** | Medium (defect scope) |
| **Dependency / owner decision** | Feeds D1's U0 package and T7's settlement row. No decision changes. X6 remains a `STATIC-ANALYSIS FINDING`; no test was run. |
| **Integration status** | **INTEGRATED** — trigger widened, original wording preserved above. |

---

### C-06 · "Two conditions" is readiness, not execution

| Field | Content |
|---|---|
| **T13 section** | §14.6 "Condition changed by T13". |
| **T14 finding** | AF-19 — counting **readiness** conditions correctly, but "remaining conditions are two" can be misread as "two steps to running U0". |
| **Original T13 wording (preserved)** | §14.6 — "U0's remaining conditions are therefore **two**, not three: **D1** (merge policy) and **D3** (G7 naming `tests/`)." |
| **Corrected statement** | U0 has **two readiness conditions — D1 and D3**. **D2 is the authorisation act**, not a readiness condition: executing U0 requires D2 (separate G7 authorisation) on top of both. Ready ≠ authorised. |
| **Evidence / anchor** | T13 §14.6, §10 (D1/D2/D3 rows), §19 ("READY FOR SEPARATE OWNER AUTHORIZATION"), §19.2 ("U0 is **not** authorised because its specification is ready. Ready ≠ authorised."). Internally consistent already; wording only. |
| **Severity** | Low (wording) |
| **Dependency / owner decision** | D1, D2, D3 — all `OUTSTANDING`. |
| **Integration status** | **INTEGRATED** — restated, original preserved. |

---

### C-07 · The unknown-usage signal reaches the budget governor but not the quota governor

**This is the only correction with technical weight beyond T13. It widens the scope of a future fix; it changes nothing about current runtime status.**

| Field | Content |
|---|---|
| **T13 section** | §14.2 **X2** row (mixed unknown → known, quota governor); related §13.5 verdict line. |
| **T14 finding** | AF-05 — X2's stated **cause** ("Flag `False` ⇒ partial sum charged") is wrong for the sub-case where attempt 1 carries a usage object with a missing total: the flag is **`True`**, and quota still charges the partial sum. The **outcome** T13 predicts is right; the **reason** is not. |
| **Original T13 wording (preserved)** | X2 — "Mixed **unknown → known**, quota governor. Attempt 1: unknown usage. Attempt 2: known usage. … Flag `False` ⇒ partial sum charged." |
| **Corrected statement** | With a usage object whose `total` is absent **and at least one component also absent or invalid**, `completions.py:1571–1572` sets `provider_usage_unknown = True`. The **budget** path then honours it (`:1945–1950`: `tokens = (None,None,None) if provider_usage_unknown else _sum_actual_tokens(...)`, plus `_actual_cost(..., provider_usage_unknown)`), so the estimate is held. The **quota** path does not: `:603` computes `quota_total = _sum_actual_tokens(actual_usage_parts)[2]` from raw parts and **never receives the flag**. Result: budget holds the estimate while quota settles a partial sum — the two governors disagree on the same response. |
| **Structural root, stated precisely** | `finish()`'s signature (`:542–550`) has **no `usage_unknown` parameter**. The flag is computed in `finish()`'s **caller** and passed only to `tokens=` and `actual_cost=`. The quota block runs **inside** `finish()` (`:596–607`) and recomputes from `actual_usage_parts` directly. The signal cannot reach quota by construction — not by an oversight at one call site but because the function boundary excludes it. |
| **T15 refinement (new, beyond T14)** | "Total absent" is **not one case, it is two**, and T13's original wording is correct for one of them. `_actual_tokens` (`:239–247`) returns `None` only when **no usage object** exists; when a usage object exists it **synthesises** `total = prompt + completion` if both components are valid (`:245–247`), and returns `None` only if prompt, completion and total are **all** absent (`:247–248`). Therefore: **(i)** total absent but prompt+completion valid ⇒ synthesised total ⇒ `failure_usage[2] is not None` ⇒ flag stays **`False`** — T13's stated cause is correct here; **(ii)** total absent with a component also absent/invalid ⇒ `failure_usage[2] is None` ⇒ flag **`True`** — T13's stated cause is wrong here. In **both** sub-cases the *outcome* T13 predicts (partial sum charged) holds; the *cause* differs, and in (ii) the budget governor behaves differently from (i). Source verified at `319a711`: `_safe_token_count` (`:233–236`) accepts `0` but rejects negatives, `bool` and non-ints. |
| **Contract intent the caller can violate** | `settle_quota`'s own docstring (`store.py:1343–1352`) states: "Without actuals (unknown provider usage), the estimate moves reserved → consumed so the capacity stays conservatively held — never silently freed, never assumed zero." The caller passes a computed partial sum instead of `None`, so the store-level intent is met only when the caller chooses to pass `None`. |
| **Acceptance boundary** | A settlement fix **cannot** be counted complete because one governor is fixed. Full 12-scenario boundary in `docs/r6-t15-r6-owner-decision-brief.md` §5. |
| **Severity** | **High (technical)** |
| **Dependency / owner decision** | Must be visible **before B5** (settlement basis) and **before T7's** settlement row is scoped. B5's wording should name the **quota** governor explicitly, or the contract understates the work. Changes no decision ID and no gate. |
| **Integration status** | **INTEGRATED** — mechanism corrected, original wording preserved, T15 refinement recorded as T15's own. |

---

### C-08 · A kill-switch precedent exists; the R6 optimisation apparatus does not

| Field | Content |
|---|---|
| **T13 section** | §19.3 (X-6 correction is permanent), §4 X-6 row. |
| **T14 finding** | AF-06 — zero R6 rollout apparatus, **but** a different, implemented per-attempt kill-switch already exists and is reusable precedent. |
| **Original T13 wording (preserved)** | X-6 — "**No apparatus exists.** `grep -rn "optimization_enabled\|optimization_flag\|feature_flag\|kill_switch\|killswitch\|default_off\|rollout"` over `src/` returns **zero hits**". |
| **Corrected statement** | Both statements are true of different objects. **(i) Precedent exists:** the Free Chat / shared-inference switch — getter `store.py:1019`, setter `:1039`, table `sabiroute_shared_inference_policy` registered at `:111`/`:140`, re-checked **per attempt** at `completions.py:1351–1368`, producing `SHARED_INFERENCE_DISABLED`. **(ii) The R6 optimisation apparatus is absent:** no optimisation flag, no default-off path, no kill-switch for the new stage — the X-6 grep result stands. |
| **Documented limitation of the precedent** | Its own comment (`:1352–1354`) states the switch lands "no later than the next routing decision on every instance" and that "**In-flight attempts are never cancelled** by this — documented limitation". The precedent is a per-attempt admission gate, **not** an in-flight cancellation mechanism. |
| **What this does not prove** | An existing precedent is **not** proof that a complete rollout mechanism exists for the optimisation stage. `SPECIFIED, UNBUILT` remains the correct status for X-6, and condition 17 remains **CONDITIONAL**, not `PASS`. |
| **Evidence / anchor** | `store.py:1019`, `:1039`, `:111`/`:140`; `completions.py:1351–1368` (re-read at `319a711` during T15); zero-hit `grep` over `src/` and `config/` for the optimisation keys. |
| **Severity** | Low (precision) |
| **Dependency / owner decision** | None directly. Strengthens the X-6 correction; T4 (flag/limits/kill switch) may reuse the pattern. Changes no gate. |
| **Integration status** | **INTEGRATED** — additive nuance to §19.3; X-6's `SPECIFIED, UNBUILT` status unchanged. |

---

### Integration verification (T15)

| Check | Result |
|---|---|
| All eight correction IDs appear exactly once in this register | **Confirmed** |
| Each references its correct T13 section | **Confirmed** — §4.3, §19.1/§8, §10/§9/§8, §13.5/§14.2, §14.2, §14.6, §14.2, §19.3 |
| C-07 names **both** budget and quota settlement | **Confirmed** — including the structural root and the 12-scenario boundary reference |
| C-05 identifies all eight pre-loop sites without claiming identical outcomes | **Confirmed** — masking restricted to the quota-held case |
| C-08 distinguishes precedent from unbuilt apparatus | **Confirmed** — including the precedent's in-flight limitation |
| Original T13 wording preserved wherever a claim is restated | **Confirmed** — quoted verbatim in C-01, C-02, C-03, C-05, C-06, C-07, C-08 |
| Any decision marked approved | **None** — all 23 remain `OUTSTANDING` |
| Any gate granted | **None** |
| Implementation authority introduced | **None** |
| Historical T13 content erased | **None** — pure append |
| Original T13 verdict altered | **None** |

**This section approves nothing. A corrected statement is not an adopted one, and an integrated correction is not an owner decision.**

---

**T15 INTEGRATION STATUS: T13 CORRECTIONS C-01…C-08 INTEGRATED ADDITIVELY; NO VERDICT, GATE OR DECISION STATUS CHANGED; OWNER ADJUDICATION STILL OUTSTANDING.**
