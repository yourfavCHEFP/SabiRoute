# R6-CLOSE-FINAL-01 — R6.0 Final Closure Package

**Status: PREPARATION AND RECONCILIATION ONLY — R6.0 IS NOT CLOSED, NOT FROZEN AND NOT SIGNED.**
> **Historical-status notice — 2026-11-06:** This is a historical record; its earlier counts describe the state at the time of this record. As of 2026-11-06, T16 records 23 owner responses: 22 selected and one deferred (C1).
**Mission:** R6-CLOSE-FINAL-01 · **Objective:** maximum legitimate R6.0 closure
**Files created:** this document only. **Files modified:** none. **Registers amended:** none.
**Supersedes:** nothing — additive only. **Cross-references:** none yet; introduced by this mission alone.
**No implementation. No production code change. No test execution. No provider call. No migration. No deployment. No commit. No staging. No reset. No cleanup. No rebase. No destructive Git operation.**
**No owner decision, external approval, signature, test result, threshold or gate acceptance invented anywhere below.**

---

## 0. Verification environment — a named limitation, stated first

Mission rule 2 forbids assuming historical HEAD, branch or working-tree status. In this session that
verification could **not** be performed:

| Check | Attempted | Result |
|---|---|---|
| `git rev-parse --abbrev-ref HEAD` / `git rev-parse HEAD` | Yes | **BLOCKED** — command execution unavailable this session |
| `git status --porcelain` | Yes (×4) | **BLOCKED** |
| File inventory / `ls`, `find`, `grep` | Yes | **BLOCKED** |

**Consequence, stated plainly:** every Git-level fact in this document is **INHERITED**, not
re-derived. The values carried are branch `feat/sabiroute-routing-foundation`, HEAD
`319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`, ahead 6 / behind 3 — as recorded in the baselines of
T13, T15 and T16. **They may be stale. This document does not certify them.**

What *was* possible — and was done — is direct **file reading** of the evidence documents. Every
anchor cited below was read in this session from the working tree, and is labelled accordingly:

- **READ (this session)** — content read directly from the file named.
- **INHERITED** — carried from a prior document's authority; not re-derived.
- **UNVERIFIED** — could not be checked in this session.
- **OWNER-STATED** — supplied by the mission text, not yet a registered record.

**A closure verdict that inherits its own baseline is weaker than one that re-derives it.** The
GO/NO-GO in §12 is nonetheless safe: every reason for NO-GO is a *decision* or *signature*
absence, and no amount of revision re-derivation could close those.

---

## 1. Status ledger — five statuses kept apart (rule 3)

Mission rule 3 requires distinguishing **owner-selected · durably recorded · canonically
registered · independently verified · gate-accepted**. These are collapsed nowhere below.

**Only one decision has moved off `OUTSTANDING`, and only in the weakest of the five senses.**

| Decision | Owner-selected | Durably recorded | Canonically registered | Independently verified | Gate-accepted |
|---|---|---|---|---|---|
| **A3** (ADR-1 Option A, conditional) | **YES** — owner stated directly (rule 5) | **PARTIAL** — no register entry exists | **NO** — `t16` A3 card reads `PENDING` / `NOT APPROVED`; T15 §3 `OUTSTANDING`; T13 §20 item 3 `OUTSTANDING` | **NO** | **NO** |
| All 22 remaining | NO | NO | NO | NO | NO |

> **Historical-state note (added during R6.0 closure execution).** The T16 A3-card state recorded
> in this table — `PENDING` / `NOT APPROVED` — reflects T16 as it stood when this document was
> written. T16 has since been updated to record the A3 owner selection (Option A, conditional,
> explicitly not implemented; P1–P5 unmet). The current T16 A3 card no longer reads `PENDING`.
> This note distinguishes the historical observation from current T16 state; it does not alter the
> historical record, and the same historical caveat applies wherever this document cites T16's A3
> card as `PENDING`.

**Therefore, strictly:**

- **Owner-selected: 1 of 23** (A3).
- **Canonically registered: 0 of 23.**
- **Independently verified: 0 of 23.**
- **Gate-accepted: 0 of 23.**

R6.0 condition 1 ("Adopt ADR-1", T13 §19.1) is **owner-selected but not registered**, so it is
**not formally cleared**. Registering it is an amendment act requiring authorisation (§6).

---

## 2. Every remaining decision — exact wording and available options

Read from `docs/r6-t16-r6-decision-option-register.md` §3 (master index) and §4–§6 (cards).
**No wording paraphrased; no option invented.** `—` means *no option is documented*, and is
reproduced as a gap rather than filled.

### 2.1 Group A — Architecture (4)

| ID | Decision wording (exact) | Options as documented | Status |
|---|---|---|---|
| **A1** | Adopt §§8–15 as the frozen architecture? | (a) Adopt §§8–15; (b) Return D14/D19-Tier-2 for re-scope | `OUTSTANDING` |
| **A2** | Treat Tier-1 metering fixes as integrity work, not optional feature work? | (a) Integrity work — BL-01…BL-04/A6/BL-06/BL-07 close live holes; (b) Defer post-v1 | `OUTSTANDING` |
| **A3** | Adopt ADR-1: Option A conditional, explicitly not implemented? | (a) Adopt Option A, conditional, explicitly not implemented; (b) Redefine target as inline-hardened (**requires a new ADR**) | **owner-selected (a); unregistered** |
| **A4** | Adopt T10-1…T10-7 scoping? | (a) Adopt scoping; (b) Proceed without coupling/tokenizer/null/capability/governor guardrails | `OUTSTANDING` |

### 2.2 Group B — Accounting and settlement (9)

B1 blocks R6.0 **and** R6.1; B2–B8 block R6.1; B9 blocks Release.

| ID | Decision wording (exact) | Options as documented | Status |
|---|---|---|---|
| **B1** | Adopt ADR-2: T11 §8 I1–I9 as the draft R6.1 foundation contract? | (a) Adopt with `ADR-2/C-1` name resolution; (b) Require an external R6.1 design document first | `OUTSTANDING` |
| **B2** | Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`? | (a) Restrict; (b) Include the SabiChat path | `OUTSTANDING` |
| **B3** | Bypass authority: operator-only, per-route, default-off? | (a) Operator-only, per-route, default-off; (b) Trusted-service signal | `OUTSTANDING` |
| **B4** | Phase-13 keep-out: R6.1 emits no snapshot fields? | (a) No snapshot fields; (b) Amend to schema-1.2 now | `OUTSTANDING` |
| **B5** | Settlement basis: unknown wins at the full original estimate, never a partial sum? | (a) Unknown wins at full original estimate; (b) Partial-sum settlement (**choosing (b) ratifies the confirmed defect**) | `OUTSTANDING` |
| **B6** | Monotone-shrink **permanent** unless the reservation is re-baselined? | (a) Permanent unless re-baselined; (b) Allow expansion | `OUTSTANDING` |
| **B7** | Per-attempt re-derivation of the effective request forbidden? | (a) Forbid; (b) Allow re-derivation | `OUTSTANDING` |
| **B8** | Adopt the budget terminal-marker pattern (BL-15) transferred from `_QUOTA_RESERVATIONS`? | (a) Adopt transferred pattern; (b) Design a new state machine | `OUTSTANDING` |
| **B9** | Reconciler placement: R6.7, with the marker migration in R6.1? | (a) Reconciler in R6.7, marker migration in R6.1; (b) Pull reconciler into R6.1 | `OUTSTANDING` |

**B5 is not a binary checkbox.** It carries **five separate owner decisions** — see §3. Its
card's two options are necessary but **not sufficient** to answer it.

**B6 and B7 are separate decisions and must not be combined** (`t16:250`, `:493`). They are the two
rulings T11 §18 omitted (X-4).

### 2.3 Group C — Capability and eligibility (4)

Group C **informs; it does not gate R6.0**. No alias promotion follows from any C decision.

| ID | Decision wording (exact) | Options as documented | Status |
|---|---|---|---|
| **C1** | Resolve byok/paid semantics and billing-source scope (BL-30)? | **`—` NONE DOCUMENTED.** An open conversation, not a binary choice | `OUTSTANDING` |
| **C2** | Exclude non-Latin BM25 relevance claims until Terminal D establishes a corpus? | (a) Exclude until Terminal D; (b) Claim multilingual now | `OUTSTANDING` |
| **C3** | Gate system/developer-role traffic until role-freeze behaviour is proven (BL-09)? | (a) Gated until role-freeze proven; (b) FULL now | `OUTSTANDING` |
| **C4** | Extend the proven 2026-10-08 capability probe to `tool_use` and `structured_output` (BL-10)? | (a) Repeat the established procedure; (b) Commission new methodology | `OUTSTANDING` |

**C1 cannot be answered from a list.** It requires an owner-supplied position. No option has been
invented here, and none may be (`t16:293`, `t15:173`).

### 2.4 Group D — Implementation authorisation (6)

| ID | Decision wording (exact) | Options as documented | Status |
|---|---|---|---|
| **D1** | U0 merge policy: strict-xfail, land-with-U1, or skip? | (a) Strict xfail; (b) Land with U1; (c) Skip | `OUTSTANDING` |
| **D2** | Authorise U0 **separately** under G7, ahead of U1–U12? | (a) Separately under G7; (b) Bundle with U1 | `OUTSTANDING` |
| **D3** | Define G7 scope as U0–U11, explicitly naming `tests/`, with U12 in R6.7? | (a) As stated; (b) Include U12. **Three separately answerable components** — see below | `OUTSTANDING` |
| **D4** | Authorise Track A engagement to schedule (BL-21) once T-numbering converges? | (a) Authorise once numbering converges; (b) Defer | `OUTSTANDING` |
| **D5** | Adopt T11 §15's T1–T8 numbering as canonical? | (a) T11 §15 T1–T8; (b) Campaign §15 T1–T7 | `OUTSTANDING` |
| **D6** | Re-issue Terminal B/C/D/E prompts (BL-24)? | (a) Re-issue; (b) Defer | `OUTSTANDING` |

**D3's three components (T14 C-03) are separately answerable** and an owner may accept one and
reject another:
- **(i)** G7 scope = U0–U11.
- **(ii)** G7 scope text **explicitly names `tests/`** — without which U0 has **no authorisation
  basis at all**, because U0 appears in no Track A row.
- **(iii)** U12 placement in R6.7.

These are explanatory sub-choices, **not** three canonical decisions. **The canonical count remains
23.**

### 2.5 Two preconditions that are not decisions

| ID | What it is | Why it must precede |
|---|---|---|
| **`C-02` reading** | Choose Reading A (Group A + **B1** only) or Reading B (Group A **and all of Group B**) for T13 §19.1 condition 3 | BL-22's signature has **two possible scopes** until chosen |
| **`ADR-2/C-1`** | Record the ADR-2 package-name conflict (`request_transform/` vs `compression/`) | B1 is **not cleanly decidable** without it (§4.1) |

**Mission rule 4 is honoured and restated:** *Reading B requires A1–A4 **and** B1–B9 — thirteen
decisions.* **This document does not silently change the 13-decision requirement.** Under Reading B,
R6.0's decision condition is **13 registrations**, not 5.

---

## 3. B5 — the five owner-decision requirements (rule 7)

Read from `docs/r6-t15-r6-owner-decision-brief.md` §5. **B5 is not a single binary checkbox.** The
12-scenario investigation establishes that **five scenarios cannot be closed by implementation at
all** — the intended outcome is not derivable from evidence and must be set by the owner.

### 3.1 The structural fact that makes five decisions necessary

**READ (this session)** — `t15` §5:

- The unknown-usage flag is `provider_usage_unknown`, initialised `False` at `completions.py:1316`,
  set `True` at `:1572`/`:1574`/`:1628`, latched at `:1693`/`:1812`, and **never reset to `False`**.
- **The budget governor honours it** (`:1944–1955`, `:1961–1972`; `_actual_cost` returns `None` at
  `:1997–1998`).
- **The quota governor never receives it:** the quota block runs *inside* `finish()` (`:596–620`),
  `finish()`'s signature (`:542–550`) has **no `usage_unknown` parameter**, and `:603` recomputes
  `quota_total` from raw parts.

**The two governors can therefore disagree on the same response.** A settlement fix that repairs one
governor is **incomplete**. This is correction **C-07 — severity High, the only correction with
technical weight beyond T13.**

### 3.2 The five owner decisions

| # | Scenario | Why evidence cannot settle it | Marker |
|---|---|---|---|
| **1** | Usage object **absent** (no `usage`, no `error.usage`) | Flag is set **only if a budget was reserved**; a **quota-only** request leaves it `False`. Whether "no usage object" should be unknown for **quota-only** requests is undefined | `OWNER DECISION REQUIRED` |
| **2** | Usage object present, **`total` absent** | `_actual_tokens` **synthesises** `total = prompt + completion` when both components are valid (`:245–247`). Whether a **synthesised** total counts as "known" for settlement is policy the code implies but **no document states** | `OWNER DECISION REQUIRED` (semantics) |
| **3** | Usage object present, **`total` = 0** | `_safe_token_count` accepts `0` as **known** (`:233–236`). Whether a provider-reported `0` is a legitimate charge or an artefact to treat as unknown is undecided | `OWNER DECISION REQUIRED` |
| **5** | Multiple attempts, **mixed known/unknown** | The flag **latches** for budget but **quota ignores the latch entirely** ⇒ **under-charge**. **Which governor's semantics is canonical**, and whether a fix makes quota consume the flag or budget match quota, is undecided | `OWNER DECISION REQUIRED` (canonical semantics) |
| **12** | Usage-event persistence | Inline fail-closed: `finish()` awaits `finalize_usage_event` (`:649–656`); failure yields `500`/`503 usage_store_unavailable` and **replaces the response** (`:661–677`) even when the provider call succeeded. Whether this is the accepted **interim posture** is **decision A3** | `OWNER DECISION REQUIRED` (via A3) |

### 3.3 The other seven scenarios — and what is *not* an owner question

| # | Scenario | Marker | Meaning |
|---|---|---|---|
| 4 | Valid total | `IMPLEMENTATION/TEST PROOF REQUIRED` | Regression coverage only |
| 6 | Attempt 1 known failure; attempt 2 succeeds with no usage (**Spec 5 / X5**) | `IMPLEMENTATION/TEST PROOF REQUIRED` | **Settled defect awaiting its fix** — `xfail(strict=True)` material, **not a question** |
| 7 | Partial components, `total` absent | `OWNER DECISION REQUIRED` | **Same question as scenario 2**, not a sixth |
| 8 | Reservation estimates and reconciliation | `UNPROVEN` | Per-transition partial-persistence matrix **unbuilt** |
| 9 | Budget settlement | `IMPLEMENTATION/TEST PROOF REQUIRED` | Correct-by-construction when the flag is set |
| 10 | Quota settlement | `IMPLEMENTATION/TEST PROOF REQUIRED` | Fix must make the quota caller flag-aware |
| 11 | Reservation-row persistence (C-05 path) | `UNPROVEN` (leak, runtime) | Leak established by control flow, **never reproduced** |

**Scenario 7 collapses into scenario 2.** The five *distinct* owner requirements are therefore
**1, 2, 3, 5, 12** — matching T15 §5.1 exactly.

### 3.4 The acceptance rule B5 must be answered against

> **A settlement correction is not complete when one governor is fixed.** It is complete only when,
> for every scenario above, the **budget** and **quota** governors reach the **same intended
> outcome**, with the intended outcome itself recorded as an owner decision where evidence does not
> settle it.

**Consequence for B5's wording:** B5 must **name both governors explicitly**. Answered as written —
"unknown wins at the full original estimate, never a partial sum" — it is **silently budget-only**,
and the contract would **understate the work by half**.

---

## 4. Identifier collisions (rule 6) — resolved without renaming

Mission rule 6 requires resolution **without silently renaming, merging or retiring registers**.
Four live collisions exist in this corpus, plus one set of identifiers that does not resolve at all.
**None is resolved by deletion here.**

### 4.1 `ADR-2/C-1` versus `GROUP-C/C1` — one keystroke apart

| Register | Symbols | Meaning |
|---|---|---|
| ADR-2 internal conflicts (T13 §12.4) | `C-1`, `C-2`, `C-3` (**hyphenated**) | `C-1` = ADR-2 **package-name conflict** (`request_transform/` vs `compression/`) |
| Group C owner decisions (T13 §9) | `C1`, `C2`, `C3`, `C4` (**unhyphenated**) | `C1` = **byok/paid billing semantics and billing-source scope** |

**The hazard in one line:** B1's recommendation reads "with **C-1** name resolution" — the
*hyphenated* ADR-2 conflict — but a reader scanning Group C lands on **C1**, billing semantics,
**which has nothing to do with package naming.**

**Resolution — labels disambiguated in prose, identifiers untouched:**

1. Every original identifier is preserved; **neither register is renamed or retired**.
2. In cross-references, the ADR-2 conflicts are written **`ADR-2/C-1`**, `ADR-2/C-2`, `ADR-2/C-3`.
3. In cross-references, Group C decisions are written **`GROUP-C/C1`**, etc.
4. In the decision register proper, the canonical IDs remain exactly **`C1`–`C4`**, and the ADR-2
   conflicts **never receive a decision ID**.
5. **No new decision ID** is created for the naming conflict.

**Owner-session instruction:** when answering B1, **write the name, not the label** — e.g.
"`ADR-2/C-1` — package-name conflict resolved to `request_transform/`".

**Second defect — B1's hidden 24th decision.** §12.2 says the name "must be recorded as a decision,
not assumed", but **`C-1` is not among the 23 registered decisions**. Answering B1 as worded either
(i) **implicitly takes an unregistered 24th decision**, or (ii) bundles it — exactly the
composite-decision defect **C-03** records. **Resolution without a new decision ID:** record `C-1`
as its own **registration line** in the response sheet (§2.5), or the owner states explicitly that
B1 **includes** it. Either is valid; silence is not.

### 4.2 `G4`/`G5`/`G7` — two colliding scales, and a third vocabulary

**Correction C-01 (T14), read this session.** The *three colliding namespaces* framing
**overstates the defect**.

| Scale | G4 | G5 | G7 |
|---|---|---|---|
| **R6 programme** | benchmark | red-team | **implementation authorisation** |
| **Developer Workflow Overhaul** | deadline/retries | async lifecycle | deployment/security — **a genuine collision** |
| **Repository remediation** | **no G-identifiers** — gates are **A–E** | | |

**So: two colliding G-scales, plus one separate lettered vocabulary.** Repository remediation uses
`reports/remediation-roadmap-and-gates.md` §2 gates **A–E** with **no G4/G5/G7** — a third
*vocabulary*, not a G-number collision.

**Resolution:** every use of a G-number in this package is qualified by its scale —
**`R6/G7`** for implementation authorisation. `R6/G7` is the only one that gates this mission.

### 4.3 Group B — two different `B1–B5` / `B1–B9` sets

| Register | Range | Meaning of, e.g., `B5` |
|---|---|---|
| **T11** owner questions | **B1–B5** | T11's own group-B set |
| **T13 / T15 / T16 canonical** | **B1–B9** | Settlement basis (unknown wins at full estimate) |

**`B1` and `B5` are not interchangeable between these two registers.** The canonical register for
R6.0 is **T13/T16 (B1–B9)** — T16 states *"Canonical count: 23 decisions"*, and T15 §7
**independently recounted 23** from T13 §7–§10 directly. Any document citing `B7` outside `B1–B9`
is **not** citing the canonical register.

### 4.4 `D`-series — decision pack versus canonical register

| Register | Symbols | Example |
|---|---|---|
| **`r6-architecture-decision-pack.md`** | `D6`, `D8`, `D14` | `D14` = telemetry schema (coordinated, not additive) |
| **T13 / T16 canonical** | `D1`–`D6` | `D6` = re-issue Terminal B/C/D/E prompts |

**`D14` and `D6` are different registers.** `D6` means the **opposite** thing in each (pack-`D6` =
retrieval/stub strategy; register-`D6` = re-issue Terminal prompts). **Reading a pack-`D` number as a
register-`D` number produces a wrong answer.**

### 4.5 `Q3`/`Q5` — do not resolve in this repository

**Reported, not collapsed.** Search over the corpus finds **no Q-series** in the canonical register:
T13/T16 number **A1–A4, B1–B9, C1–C4, D1–D6** — no Q identifiers. T11 contains a **`T11-C Q1…Q5`
sub-investigation** numbering in which **`Q5` = bypass authority (operator-only vs trusted-service
signal)** — that is **not** a measurement contract.

**Status: `UNRESOLVED` — external input required.** They are programme-level identifiers taken
outside this repository. **Nothing is inferred about their content, and no Q-identifier is mapped
onto a canonical decision.**

### 4.6 The collisions have already propagated — evidence

`docs/r6-impl-prep-03-r6.6-r6.7-validation-and-rollout-preparation.md` (read this session) exhibits
**all four** collision classes in one decision table:

| Its label | Its stated meaning | Canonical register says | Result |
|---|---|---|---|
| `B7` | "Tier-1 estimator sign-off" | **Per-attempt re-derivation forbidden** | **Wrong register** — likely T11-`B*` |
| `B9` | "Release-scope decision" | **Reconciler placement: R6.7** | **Wrong meaning** |
| `C3` | "Reconciler placement (R6.1 vs R6.7)" | **Gate system/developer-role traffic** | **Wrong meaning** — `C3` ≠ `B9` |
| `D6` | "LiteLLM retrieval/stub strategy" | **Re-issue Terminal B/C/D/E prompts** | **Pack-`D6` read as register-`D6`** |
| `D14` | "Telemetry schema" | **Not a register decision at all** | Pack-`D` used as register-`D` |
| `Q3/Q5` | Cited as dependencies | **Do not resolve in repo** | External, unmapped |

**This is the concrete cost of the collisions** — a prepared document has already mixed at least
three registers. **It is why rule 6 exists**, and it is why `prep-03` must not be used as evidence
without correction (§6).

---

## 5. A3 provenance correction (rule 5)

**The stale narrative, corrected.**

Prior documents describe A3 as `OUTSTANDING` with an *inherited recommendation* whose provenance is
"T12's recommendation as recorded in T13 §7" (`t15` §3, "Existing recommendation":
`INHERITED RECOMMENDATION`). **That narrative is now stale.** It describes a *recommendation that
had not been answered*.

**What is now true — OWNER-STATED (mission rule 5), not yet registered:**

1. **The owner directly confirmed A3 Option A** — "ADR-1: Option A, conditional and explicitly not
   implemented."
2. **The ADR-1 target is conditional.** Adopting it **freezes a target shape and builds nothing**.
3. **Prerequisites P1–P5 are unmet.** `t15` §3 lists them: **P1** owner acknowledgement; **P2**
   `key_id`-write predicate mirroring `finalize_usage_event`'s tenant guard; **P3** additive
   migration following `_SCHEMA_VERSIONS`; **P4** extend `_REQUIRED_COLUMNS` so an unmigrated
   database fails **at startup**, not at first snapshot; **P5** the full-row admin projection must
   never gain optimisation columns. **All five remain unmet.**

**What this correction does and does not change:**

| Claim | Status after correction |
|---|---|
| A3 is owner-selected as Option A | **TRUE** (owner-stated) |
| A3 is canonically registered | **FALSE** — `t16` A3 card still `PENDING` / `NOT APPROVED` |
| A3 is gate-accepted (R6.0 condition 1 clears) | **FALSE** — registration must precede gate acceptance |
| Adopting ADR-1 implements telemetry | **FALSE** — implements nothing (`t15`, `VERIFIED`) |
| P1–P5 are satisfied | **FALSE** — all unmet |
| Option A "reverts to conditional-with-no-schedule" if P1 slips | **TRUE and must be recorded, not silently dropped** (T13 §11.4) |

**The provenance defect to fix:** documents must stop describing A3 as an *inherited
recommendation*. It is an **owner selection awaiting canonical registration**. Per rule 3 it is
**not** a gate acceptance. §6 lists the amendments required.

---

## 6. Documents requiring authorised amendment

**No document has been modified.** Each row is a **proposed amendment requiring an explicit
owner-authorised amendment task**, per the authority boundary.

| # | Document | Defect | Required amendment | Priority |
|---|---|---|---|---|
| 1 | `r6-t16-r6-decision-option-register.md` | A3 card still `PENDING` / `NOT APPROVED`; §11 response sheet row A3 blank | Record A3 **owner selection = Option A**, provenance "owner confirmed directly", note P1–P5 unmet | **Blocking R6.0** |
| 2 | `r6-t13-…preparation.md` §20 item 3 | A3 `OUTSTANDING` | Restate as **owner-selected, unregistered** | High |
| 3 | `r6-t15-r6-owner-decision-brief.md` §3 | A3 presented as `INHERITED RECOMMENDATION` | Restate provenance; add confirmation P1–P5 unmet | High |
| 4 | `r6-t16-…register.md` + `r6-t15-…brief.md` | `C-1` is a **24th decision** with no registration line; `C-1`/`C1` collision | Add **`ADR-2/C-1` registration line**; apply §4.1 label discipline | **Blocking B1** |
| 5 | `r6-t16-…register.md` §8 + `r6-t13` §19.1 | `C-02` unresolved; condition 3 says *Group A + Group B*, §8 says only B1 blocks R6.0 | Record **Reading A or Reading B**; if B, relabel B2–B9 "R6.0-adjacent" | **Blocking BL-22** |
| 6 | `r6-impl-prep-03-…preparation.md` | Decision table misattributes `B7`, `B9`, `C3`, `D6`, `D14`; cites unresolvable `Q3/Q5` | **Supersede or correct** the decision table against the canonical register | High |
| 7 | `r6-impl-prep-03-…preparation.md` | Claims G4/G5/G7 "have **zero** occurrences in the tree" | **Contradicted by C-01** — defined **twice**, verbatim, in `SabiRoute_Developer_Workflow_Overhaul_Plan.md:239–247` and the campaign `:332` | High |
| 8 | `r6-impl-prep-03-…preparation.md` | Claims "all 14 configured aliases are **UNKNOWN**" | **Contradicted by X-5** — **11 UNKNOWN, 3 BOUNDED** (`chat`), one also `streaming` | High |
| 9 | `CLAUDE.md` §12 | Documentation finding T13 §20 item 25 | Correct at source — **separately authorised**, explicitly **not** an R6 gate | Medium |
| 10 | `r6-t16-…register.md` §3 | Pack-`D` numbers appear in `Blocks` prose without scale qualification | Qualify as `pack-D14` per §4.4 | Low |

**Amendment 1 is the single highest-value action available.** It converts an owner selection into a
registered decision and moves R6.0 condition 1 from *owner-selected* to *registered*. **It requires
no code, no test and no external input.** Nothing in this document performs it.

---

## 7. Track A engagement and sign-off requirements

### 7.1 The blocking dependency chain

**Track A cannot be engaged today**, and the reason is administrative, not technical:

```
D5 (adopt T1–T8 numbering)  ──►  D4 (authorise Track A engagement to schedule / BL-21)
                                          │
                                          ▼
                                 Track A sign-off T1–T8  ──►  R6.1 start
```

**D4 depends on D5** (X-3): Track A numbering **does not converge** across three documents. `T7` is
**ambiguous** between T11 §15's `T1–T8` and campaign §15's `T1–T7`. **A reviewer could sign the
wrong artefact.** Until D5 is answered, engagement cannot be scheduled without that risk.

### 7.2 What Track A is being asked to sign

**READ (this session)** — T13 §21 item 5: **"Obtain Track A sign-off T1–T8 — External review —
feeds R6.1 start — blocks R6.1."** Status **`NOT OBTAINED`**. **No reviewer was contacted and no
prompt was sent.**

**Sign-off requirements:**

1. **Numbering fixed first** (D5), so the signed artefact set is unambiguous.
2. **Per-claim verdicts, not an aggregate.** T13 §18 is explicit for the verification lane:
   *"An aggregate 'verified' without per-claim detail does not satisfy this lane."* The same
   discipline applies to Track A.
3. **Anchored to a named commit.** Every claim must be re-anchorable to the stated commit —
   `319a711…` or its verified successor. Since HEAD **could not be re-derived this session**
   (§0), the anchor must be **re-established at engagement time**.
4. **Independent authorship.** Track A is external precisely because self-attestation is not
   independent verification.
5. **Silence is not a result.** `NOT OBTAINED` remains the only correct label until a **record**
   exists.

### 7.3 Track A independence boundary

Track A does **not** grant `R6/G7`, does **not** sign R6.0, and does **not** substitute for the
owner's signature. It is **one** of six external actions (§9), and it gates **R6.1**, not R6.0.

---

## 8. Remaining technical blockers and their owners

Every item is `STATIC-ANALYSIS FINDING` or `UNPROVEN` — **no runtime confirmation exists for any
of them**, and none was executed this session.

| # | Blocker | What is established | Owner of the resolution | Gate blocked |
|---|---|---|---|---|
| **TB-1** | **Spec 5 / X5 settlement defect.** Attempt 1 fails with *known* usage ⇒ flag never set ⇒ attempt 2's no-usage success settles attempt 1's **partial sum** instead of holding the estimate | Control-flow trace across `completions.py:1316, 1567–1574, 1599–1608, 1903–1911, 1945–1953, 563–595` + `store.py:1213–1247`. **T12 §19.2's hedge is wrong**; T13 §13 re-derived the opposite | **Engineering (U0/T7)** — needs D1/D2/D3 first | R6.1 |
| **TB-2** | **Dual-governor divergence (C-07).** Budget honours `provider_usage_unknown`; **quota structurally cannot** — `finish()` has no parameter for it | `finish()` `:542–550`; quota block `:596–620`; `:603` recomputes from raw parts; `settle_quota` docstring `store.py:1343–1352` requires `None` and the caller does not pass it | **Owner (B5 + five decisions, §3), then Engineering (T7)** | R6.1 |
| **TB-3** | **C-05 pre-loop `NameError` masking — eight sites.** With a quota held, any pre-loop `finish()` returns **503 `QUOTA_UNAVAILABLE`**, and `:1299`'s **429 `budget_exceeded` becomes a 503 quota outage**; the reservation is **never released** | `finish()` declares `nonlocal` for `budget_reserved, quota_reserved` but **not** `attempted`; `attempted` bound at `:1311`; `if attempted:` read at `:602`; sites `:1171, :1180, :1189, :1205, :1272, :1282, :1291, :1299` | **Engineering (U0)** — D1/D2/D3 | R6.1 |
| **TB-4** | **ADR-2 quantitative items unspecified at adoption.** I2's 250 ms / 2× byte budget; I5's configuration schema is *described, not written* | T13 §12.3 | **Owner (accept-as-bounded) at B1** | R6.0, R6.1 |
| **TB-5** | **Reservation partial-persistence matrix unbuilt.** Per-transition state not mapped | T13 §23.2, carried forward; T15 scenario 8 `UNPROVEN` | **Engineering (U0/U1)** | R6.1 |
| **TB-6** | **Rollout apparatus absent — `SPECIFIED, UNBUILT`.** X-6 corrected from T11's `PASS`; condition 17 stays **CONDITIONAL** | Zero-hit `grep` over `src/` and `config/` for optimisation flag/kill-switch keys | **Engineering (U4)** | Release |
| **TB-7** | **`ADR-2/C-1` package-name conflict unrecorded.** `compression/` (packet, 8,645 B) vs `request_transform/` (ADR-2) | T13 §12.2 / §12.4 | **Owner** — prerequisite to B1 | R6.0 |
| **TB-8** | **X-2 reachability 503 consequence** (pre-loop budget pricing) — same family as TB-3 | `STATIC-ANALYSIS FINDING` | Engineering (U0) | R6.1 |

**Note on TB-6:** a **reusable precedent exists** but is **not** the missing apparatus — the Free
Chat / shared-inference switch (`store.py:1019` getter, `:1039` setter, table `:111`/`:140`,
re-checked per attempt at `completions.py:1351–1368`, producing `SHARED_INFERENCE_DISABLED`). Its own
comment records the limitation: **in-flight attempts are never cancelled.** It is an admission gate,
**not** a kill-switch for the optimisation stage. This is **C-08**.

---

## 9. External signatures still required

All **`NOT OBTAINED`**. **No reviewer was contacted; no prompt was sent.** (T13 §21, read this session.)

| # | Action | Lane | Feeds | Blocks | Status |
|---|---|---|---|---|---|
| 1 | Issue and obtain **Terminal B** record | Independent red-team | G5 | Release | `NOT OBTAINED` |
| 2 | Issue and obtain **Terminal C** record | Independent red-team | G5 | Release | `NOT OBTAINED` |
| 3 | Issue and obtain **Terminal D** corpus + comparability keys | Benchmark | G4, BL-19 | Release | `NOT OBTAINED` |
| 4 | Issue and obtain **Terminal E** attestation | Verification | Scorecard | Release | `NOT OBTAINED` |
| 5 | Obtain **Track A sign-off T1–T8** | External review | R6.1 start | **R6.1** | `NOT OBTAINED` |
| 6 | Complete the **2026-10-08 capability probe** extension for `tool_use` / `structured_output` | Provider evidence | C4, BL-10 | Release | `NOT OBTAINED` |
| **7** | **Owner signature — BL-22** (R6.0 written approval) | Owner | R6.0 | **R6.0** | `NOT SIGNED` |

**The approval boundaries, named as rule 9 requires:**

- **`R6/G7` — implementation authorisation: `NOT GRANTED`.** Never requested. **Cannot be requested
  by a review report.** Only the owner can record it.
- **Track A sign-off — `NOT OBTAINED`.** No reviewer contacted.
- **BL-21 — Track A engagement to schedule.** Gated behind D5 (numbering), then D4 (authorisation).
- **BL-22 — the R6.0 signature act.** Not a Group decision (T13 §20 item 24). Follows Group A + B1
  being recorded **and** `C-02` being settled.
- **BL-23 — the `R6/G7` / implementation-authorisation boundary.** `R6/G7` is `NOT GRANTED`; nothing
  may be implemented until it is recorded.

**Six of the seven block Release or R6.1, not R6.0.** R6.0 depends on **Item 7 (BL-22)** plus
decisions. **This is why R6.0 can close without any external signature — and why it cannot close
without the owner.**

---

## 10. Independently auditable R6.0 closure checklist

Each row states **how a third party confirms it independently**. **Every row is `UNMET`.** No row may
be marked met by this document, by a plan, or by the existence of a prepared decision.

| # | Requirement | How to verify independently | Current |
|---|---|---|---|
| **RC-1** | `C-02` reading chosen (A or B) and recorded | Locate the recorded reading; confirm §19.1 condition 3 matches it | **UNMET** |
| **RC-2** | `ADR-2/C-1` package-name recorded as its own line | Read response sheet; confirm a `C-1` row exists with a recorded name | **UNMET** |
| **RC-3** | **A3** registered (Option A, conditional, not implemented) | `t16` A3 card shows the selection, not `PENDING` | **UNMET** — owner-selected only (§1) |
| **RC-4** | **B1** registered with `ADR-2/C-1` resolution | `t16` B1 card shows the selection | **UNMET** |
| **RC-5** | **A1, A2, A4** registered | `t16` cards A1/A2/A4 show selections | **UNMET** |
| **RC-6** | **Reading B:** **B2–B9** registered (all eight) | `t16` cards B2–B9 show selections | **UNMET** — *not required under Reading A* |
| **RC-7** | Decision condition satisfied at the chosen scope | Count registered rows: **13** (Reading B) or **5** (Reading A) | **0 registered** |
| **RC-8** | **BL-22** signed | Locate the signed written approval, dated, scope per RC-1 | **UNMET** |
| **RC-9** | Each decision marked approved **only** by an owner record | Grep for approval basis; silence must not read as approval | **UNMET** |
| **RC-10** | No decision marked approved by a report, plan or test | Audit trail: every change cites an owner record | **HOLDS** (nothing approved) |
| **RC-11** | `CLAUDE.md` §12 corrected *if* separately authorised | Diff the section | **UNMET** — not authorised, not done |
| **RC-12** | `prep-03` decision table corrected or superseded | Compare its table to the canonical register | **UNMET** (§6 items 6–8) |
| **RC-13** | Baseline re-derived at closure time, not inherited | Confirm HEAD/branch recorded **at the closure act** | **UNMET** — could not re-derive (§0) |

**RC-13 is not cosmetic.** A closure signed against an unverified baseline is a closure of an
unknown commit. **The signature act must re-anchor first.**

**What the checklist deliberately excludes:** `R6/G7`, Track A, Terminals B/C/D/E and the capability
probe. **They do not gate R6.0.** Including them would inflate the apparent distance to closure and
invite the error of waiting on external lanes to freeze an architecture.

---

## 11. Honest R6.0 closure percentage

### 11.1 Component ledger

| Component | Weight | Complete | Basis |
|---|---:|---:|---|
| Decision **registration** (Reading B: 13 decisions) | 40% | **0%** | 0 of 13 registered; A3 owner-selected only |
| Preconditions (`C-02` reading, `ADR-2/C-1` line) | 15% | **0%** | Neither settled |
| **BL-22** signature act | 15% | **0%** | Not signed |
| Externals that gate R6.0 | 5% | **100%** | **None gate R6.0** |
| Documentation / decision package prepared | 25% | **~90%** | T13/T14/T15/T16 complete; `prep-03` needs correction (§6) |

### 11.2 The arithmetic, shown rather than asserted

```
0.40 × 0.00  =  0.0%     decisions registered
0.15 × 0.00  =  0.0%     preconditions settled
0.15 × 0.00  =  0.0%     BL-22 signed
0.05 × 1.00  =  5.0%     externals (none gate R6.0)
0.25 × 0.90  = 22.5%     documentation prepared
              ─────
               27.5%
```

**Partial credit for A3, honestly:** A3 is 1 of 13 registrations. Owner-selected is **real
progress but is not registration**. Crediting half of its share:

```
A3 share = 0.40 × (1/13) = 3.1%  →  half-credit +1.5%
```

**R6.0 CLOSURE = 29.0% — call it ~29%.**

### 11.3 What the number means, and what it does not

- **It is not a measure of engineering quality.** The architecture package is substantially
  prepared; the underlying defects are identified with precise anchors.
- **It is a measure of governance completion**, because R6.0 *is* a governance act. Its three
  conditions are **adopt, adopt, record-then-sign**. Two are decision registrations and one is a
  signature. **None requires code.**
- **The remaining ~71% is almost entirely owner-time, not engineering-time.**

**Ceiling estimates, stated as arithmetic rather than forecast:**

| If the owner does… | R6.0 reaches | Because |
|---|---:|---|
| Register A3 only | ~32% | RC-3 met; condition 1 clears |
| Register A3, B1, `ADR-2/C-1`; settle `C-02` | ~55% | RC-1…RC-4 met; conditions 1–2 clear, signature unblocked |
| Above + Reading B (A1–A4, B1–B9 = 13) + sign BL-22 | **~95%** | RC-1…RC-9 met |
| Above + `prep-03` correction + baseline re-derivation | **100%** | RC-11…RC-13 met |

**No option above is recommended.** They state the arithmetic only, so the owner can see that the
distance to closure is **bounded and entirely within their authority**.

---

## 12. GO / NO-GO verdict

# **NO-GO for R6.0 closure and NO-GO for architecture freeze.**

**Stated exactly: R6.0 remains `CONDITIONALLY READY` — it does not close, and it does not freeze.**

### 12.1 The three conditions and their true state

| Condition (T13 §19.1) | Required | Actual | Verdict |
|---|---|---|---|
| **1. Adopt ADR-1** (A3) | Registered owner decision | Owner-selected, **unregistered** | **NOT MET** |
| **2. Adopt ADR-2** (B1) incl. `ADR-2/C-1` | Registered decision + name recorded | `OUTSTANDING`; `C-1` unrecorded | **NOT MET** |
| **3. Record Group A + Group B, then sign BL-22** | Registered + `C-02` settled + signed | 0 registered; `C-02` open; unsigned | **NOT MET** |

**All three conditions are unmet. The verdict is not a judgement call.**

### 12.2 Why this is NO-GO rather than CONDITIONAL-GO

A conditional GO would be appropriate if the remaining work were **engineering**. It is not:

- **Every** R6.0 condition is a **decision registration** or a **signature**.
- **No engineering action** can advance R6.0 by one point.
- **No external lane** gates R6.0 (§10) — so waiting on Track A or the Terminals **cannot** close it.
- The **one** item that could advance closure today — registering A3 — is **not performed here**,
  because registering an owner decision is an owner act and this mission is not authorised to amend
  a shared register.

### 12.3 What would flip the verdict

**GO becomes legitimate when:** `C-02` chosen · `ADR-2/C-1` recorded · A3 and B1 registered ·
A1, A2, A4 (+ B2–B9 under Reading B) registered · **BL-22 signed against a re-derived baseline**.

**In that order.** BL-22 signed before `C-02` is settled produces a signature of **ambiguous scope** —
the specific failure mode `C-02` exists to prevent.

### 12.4 What this document does not do

It does not close R6.0. It does not declare closure legitimate, and it does not present preparation
as progress toward a signature. **It reports distance, precisely, with anchors.**

---

## 13. Safety boundary — what this mission did not do

| Prohibition | Status |
|---|---|
| Implement R6.1–R6.7 | **Not done** |
| Change production code | **Not done** — zero writes outside this document |
| Execute tests (including the **U0 test artefact**, which remains **unauthorised evidence**) | **Not done** — nothing executed, nothing modified |
| Provider calls | **Not done** |
| Migrations, deployments | **Not done** |
| Commits, staging, resets, cleanups, rebases, destructive Git | **Not done** |
| Amend a shared register or protected document | **Not done** — §6 lists amendments as **proposals requiring authorisation** |
| Invent an owner decision, approval, signature, test result, threshold or gate acceptance | **Not done** |
| Assume current HEAD / branch / worktree | **Not done** — and **not verifiable this session** (§0) |

**On the U0 test artefact (rule 8):** it is treated throughout as **unauthorised evidence**. It was
**not executed and not modified**. This session could not locate it (execution blocked, §0), so its
continued preservation is **asserted from the mission's own instruction, not reverified here** — a
gap stated rather than hidden.

---

## 14. Final status

| Field | Value |
|---|---|
| **Decision package** | Complete and canonical — **23 decisions, 0 registered** |
| **Owner-selected** | **1** (A3 Option A, conditional, P1–P5 unmet) — **unregistered** |
| **R6.0 closure** | **~29%** |
| **R6.0** | **CONDITIONALLY READY — not closed, not frozen, not signed** |
| **R6.1** | **NOT READY** |
| **`R6/G7`** | **NOT GRANTED** |
| **Track A / Terminals B–E** | **`NOT OBTAINED`** |
| **Verdict** | **NO-GO** |
| **Next action** | **Belongs to CHEF_P** — settle `C-02`, record `ADR-2/C-1`, register A3 then B1 |

**This document closes nothing. It makes the remaining distance auditable, ordered and bounded — and
shows that the distance is entirely owner-time, not engineering-time.**

---

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
