# R6 / FAST-02 — Governance Reconciliation

**Status:** RECONCILIATION ONLY — NOT AN APPROVAL RECORD
**Baseline:** T16 canonical decision register (23 decisions)
**Companion record:** 2026-11-04 in-session supplement (unregistered)
**Authority granted by this document:** none

This document grants no approval, closes no gate, freezes no artefact, and carries no
signature. It exists to make the *current* state of FAST-02 legible before any owner
approval is recorded. Every decision below remains **PENDING / NOT APPROVED** unless a
later, separately-signed record says otherwise.

---

## 0. Scope, method, and evidence labels

### 0.1 Scope

FAST-02 governance only: the 23 registered decisions, the in-session selections made on
2026-11-04, the amendment set (AM-1…AM-21), the unresolved owner questions (UQ-1…UQ-18),
the identifier collision families (X-1…X-10), and the BL-22 precondition set.

Out of scope: implementation status of any decision, code review, test results, and the
R6.0 readiness percentage beyond restating it.

### 0.2 Method

Three sources were reconciled against each other:

| Label | Source | Standing |
|---|---|---|
| **[T16]** | Canonical decision register, 23 decisions | Authoritative for *what is registered* |
| **[SUP]** | 2026-11-04 in-session supplement | Authoritative for *what was said in session*; **not** registered |
| **[WS]** | Working worksheet used during the session | **Defective** — see AM-16 |

Where [T16] and [SUP] disagree, [T16] governs registration state and [SUP] governs
provenance. Where [WS] disagrees with either, [WS] is treated as unreliable and the
discrepancy is logged as an amendment requirement rather than silently resolved.

### 0.3 Evidence labels used below

- **S** — *selected in session*: the owner stated a preference on 2026-11-04.
- **R** — *recorded*: the selection appears in [SUP].
- **C** — *confirmed*: the owner restated or affirmed the selection.
- **G** — *registered*: the selection is entered in [T16] as an approved decision.

**No decision in this document reaches G.** Three decisions reach S+R; one reaches S+R+C.
The remaining nineteen reach none of these.

---

## 1. Reconciled 23-decision ledger

### 1.1 Summary

| Group | Count | S | R | C | G |
|---|---|---|---|---|---|
| A (architecture) | 4 | 1 | 1 | 0 | 0 |
| B (behaviour / packaging) | 9 | 2 | 2 | 0 | 0 |
| C (correctness / defects) | 4 | 1 | 1 | 1 | 0 |
| D (delivery / documentation) | 6 | 0 | 0 | 0 | 0 |
| **Total** | **23** | **4** | **4** | **1** | **0** |

**Approved decisions: 0 of 23.**
**Outstanding (no selection at all): 10** — A1, A2, A4, B2, B3, B4, B5, B7, B8, B9.

> Note on the count: 23 − 4 selected = 19 with no selection. Of those 19, nine are
> C- and D-group items that were never opened in session. The "10 outstanding" figure
> refers to the A/B items the owner was actively working through. Both numbers are
> correct; they count different sets. See §3.4 for the arithmetic discrepancy that
> this distinction does **not** resolve.

### 1.2 Full ledger

State legend: `—` = no selection · `S` = selected in session · `R` = recorded in [SUP] ·
`C` = confirmed · `G` = registered in [T16] (approved).

#### Group A — Architecture

| ID | Subject (as registered) | State | Blocking | Notes |
|---|---|---|---|---|
| A1 | *(options as registered in [T16]; not restated here)* | — | yes | Never opened in session. |
| A2 | *(as registered)* | — | yes | Never opened in session. |
| A3 | Target architecture | **S R** | yes | **Option A** selected. Conditional target architecture. **Not implemented.** Preconditions P1–P5 all unmet. |
| A4 | *(as registered)* | — | yes | Never opened in session. |

**A3 detail.** Option A was selected as a *conditional target* — it describes where the
architecture should land, not what exists. The five preconditions P1–P5 are unmet, so
Option A cannot be treated as a description of current state. Any document that reads
A3 as "the architecture is X" is misreading the selection.

#### Group B — Behaviour and packaging

| ID | Subject (as registered) | State | Blocking | Notes |
|---|---|---|---|---|
| B1 | Package placement | **S R** | yes | **Option A** selected: package → `src/sabiroute/request_transform/`. |
| B2 | *(as registered)* | — | yes | Never opened. |
| B3 | *(as registered)* | — | yes | Never opened. |
| B4 | *(as registered)* | — | yes | Never opened. |
| B5 | Scenario coverage | — | **yes** | **Not selected.** Five scenarios in scope: **1, 2, 3, 5, 12**. See §5. |
| B6 | Completion handling | **S R** | no | **Option A** selected. **Already implemented** — `min` at `completions.py:1608`. Selection ratifies existing behaviour. |
| B7 | *(as registered)* | — | yes | Never opened. |
| B8 | *(as registered)* | — | yes | Never opened. |
| B9 | *(as registered)* | — | yes | Never opened. |

**B1 / ADR-2 / C-1 collision.** The B1 selection fixes the package path. ADR-2 and C-1
both speak to package naming. These are not the same question and must not be merged —
see X-2 and X-3 in §4.

**B6 is the only decision whose selection is already true of the codebase.** It is
therefore the only decision that could be registered without an implementation
precondition. It is still **not registered**.

#### Group C — Correctness and defects

| ID | Subject (as registered) | State | Blocking | Notes |
|---|---|---|---|---|
| C1 | *(as registered)* | — | yes | Never opened. Collides with ADR-2 — see X-3. |
| C2 | *(as registered)* | — | yes | Never opened. |
| C3 | *(as registered)* | — | yes | Never opened. |
| C4 | *(as registered)* | — | yes | Never opened. |

**C-02 (defect) — Reading B selected.** C-02 is a **defect identifier**, not one of the
four numbered C-group decisions. The owner selected **Reading B**: *all Group A decisions
and all Group B decisions must be resolved before BL-22 may be attempted.*

- State: **S R C** — the only item in the register reaching C.
- Registration: **none.** Reading B is not entered in [T16].
- Mapping: whether C-02 maps onto one of C1–C4 is **unconfirmed** — see UQ-4.

**C-02 defect vs. C-02 Reading B.** These are two different things sharing one label:
the *defect* (what is wrong) and the *reading* (how the owner wants it handled). Reading B
is a sequencing decision, not a fix. Selecting Reading B does not close C-02.

#### Group D — Delivery and documentation

| ID | Subject (as registered) | State | Blocking | Notes |
|---|---|---|---|---|
| D1 | *(as registered)* | — | no | Never opened. |
| D2 | *(as registered)* | — | no | Never opened. |
| D3 | *(as registered)* | — | no | Never opened. |
| D4 | *(as registered)* | — | no | Never opened. |
| D5 | *(as registered)* | — | no | Never opened. |
| D6 | *(as registered)* | — | no | Never opened. |

Group D was not reached. Under Reading B, Group D is **not** a BL-22 precondition, so its
non-resolution does not block BL-22 — but it does block any claim that FAST-02 is
complete.

### 1.3 What the ledger establishes

1. **Zero of 23 decisions are approved.** No gate can be closed on this register.
2. **Four decisions have an owner selection** (A3, B1, B6, C-02 Reading B) — and none is
   registered.
3. **Ten A/B decisions have no selection at all**, and Reading B makes every one of them
   a BL-22 precondition.
4. **Group D is untouched** and is not a BL-22 precondition, but is a completeness gap.

---

## 2. Owner-selection provenance matrix

### 2.1 Matrix

| Item | S | R | C | G | Selection | Where it lives | Durable? |
|---|---|---|---|---|---|---|---|
| A3 | ✔ | ✔ | — | ✘ | Option A (conditional) | [SUP] only | **No** |
| B1 | ✔ | ✔ | — | ✘ | Option A | [SUP] only | **No** |
| B6 | ✔ | ✔ | — | ✘ | Option A | [SUP] only | **No** |
| C-02 Reading B | ✔ | ✔ | ✔ | ✘ | Reading B | [SUP] only | **No** |
| A1, A2, A4 | — | — | — | ✘ | none | — | n/a |
| B2, B3, B4, B5, B7, B8, B9 | — | — | — | ✘ | none | — | n/a |
| C1–C4 | — | — | — | ✘ | none | — | n/a |
| D1–D6 | — | — | — | ✘ | none | — | n/a |

### 2.2 Reading the matrix

- **S without G is the central finding.** Four selections exist; none is registered.
  A selection that is not registered is not a decision — it is a stated intention that
  the next reader cannot rely on.
- **C is not G.** C-02 Reading B was confirmed by the owner in session and is still not
  registered. Confirmation in conversation does not survive the conversation.
- **Durability is uniformly "No."** All four selections live only in [SUP]. If [SUP] is
  lost, mis-filed, or read as authoritative without [T16] alongside it, the selections
  are gone and the register reverts to 0/23 with no trace that anything was ever chosen.

### 2.3 Provenance risk

The four selections were made in a single session and recorded in a single supplement.
There is no second, independent record of any of them. This is a single point of failure
for 100% of the owner's expressed intent on FAST-02.

---

## 3. Durable-recording and registration gap list

### 3.1 Gap G-1 — Selections are not registered

**What:** A3, B1, B6, and C-02 Reading B are selected but absent from [T16].
**Consequence:** [T16] reports 0/23 approved, which is *correct as a registration fact*
and *misleading as a state-of-work fact*. A reader consulting only [T16] would conclude
nothing has been decided.
**Required action:** enter the four selections in [T16] as **selected, not approved** —
a distinct state from both PENDING and APPROVED. Do not mark them approved.

### 3.2 Gap G-2 — No "selected" state exists in the register

**What:** [T16] appears to model only PENDING and APPROVED. There is no slot for
"owner has chosen, approval not yet given."
**Consequence:** the four selections have nowhere to go. This is why they were recorded
in a supplement instead of the register — the register could not hold them.
**Required action:** add a SELECTED state to the register schema before any entry is made.
Without it, G-1 cannot be closed without falsely marking selections as approved.

### 3.3 Gap G-3 — Supplement has no standing

**What:** [SUP] is not referenced from [T16], and [T16] does not acknowledge that a
supplement exists.
**Consequence:** the two records can drift. A future reader may treat [T16] as complete.
**Required action:** add a forward reference from [T16] to [SUP], and a back-reference
from [SUP] to the [T16] baseline it supplements.

### 3.4 Gap G-4 — Worksheet arithmetic is defective (AM-16)

**What:** [WS] records *"thirteen of 23 recorded as answered."* [T16] records **zero**
approved and this reconciliation finds **four** selected.
**Consequence:** three different counts of the same quantity are in circulation
(13, 4, 0). None of them is a typo of another.
**Status:** **unresolved.** The 12-vs-13 arithmetic discrepancy was not closed in session.
**Required action:** do not use [WS] as a source until AM-16 is resolved. Treat any
figure derived from [WS] as unverified.

> This is the single most dangerous gap in the set. A worksheet claiming 13 answered,
> against a register showing 0 approved, is the kind of discrepancy that produces a
> false "we're nearly done" reading. It is not nearly done.

### 3.5 Gap G-5 — No registration procedure

**What:** no documented step sequence for moving an item from SELECTED to APPROVED.
**Consequence:** even with G-1 and G-2 closed, there is no defined act that constitutes
approval, no required signatory, and no record format.
**Required action:** define the approval act before the first approval is attempted.

### 3.6 Gap G-6 — claude-mem unavailable

**What:** the memory service returned **401** during this session.
**Consequence:** no cross-session recall was available. This reconciliation is built from
[T16], [SUP], and [WS] only. Any prior session context not captured in those three
sources is **not** reflected here.
**Required action:** re-run the reconciliation against claude-mem once the 401 is
resolved, and diff the result against this document.

### 3.7 Gap summary

| Gap | Severity | Blocks approval? | Blocks BL-22? |
|---|---|---|---|
| G-1 selections unregistered | high | yes | yes |
| G-2 no SELECTED state | high | yes | yes |
| G-3 supplement unreferenced | medium | no | no |
| G-4 worksheet arithmetic (AM-16) | **critical** | yes | yes |
| G-5 no approval procedure | high | yes | yes |
| G-6 claude-mem 401 | medium | no | no |

---

## 4. Identifier collision register

Ten collision families are registered as **X-1 … X-10**. A collision family is a set of
identifiers that are visually or lexically similar but denote different things, such that
a reader (or a tool) can silently substitute one for another.

The instances below are the ones this reconciliation can evidence directly. The remaining
families are carried forward **unenumerated** and must be resolved from [T16] before any
approval is recorded. They are not omitted because they are unimportant — they are
omitted because this document will not invent them.

### 4.1 Evidenced instances

| Family | Colliding identifiers | What each denotes | Failure mode |
|---|---|---|---|
| **X-1** | `ADR-1` / `ADR-2` | Two distinct architecture decision records | Citing "the ADR" without a number is ambiguous |
| **X-2** | `ADR-2` / `C-1` | ADR-2 is an architecture record; C-1 is a C-group decision | A reference to "C-1" may be read as ADR-2's first clause |
| **X-3** | `C-1` (decision) / `C-02` (defect) | Numbered decision vs. zero-padded defect | `C-1` and `C-02` differ by padding and by kind; both are "C-something" |
| **X-4** | `C-02` (defect) / `C-02 Reading B` (sequencing decision) | The defect vs. the owner's chosen handling of it | Selecting Reading B can be misread as closing C-02 |
| **X-5** | `B5` (decision) / scenarios `1, 2, 3, 5, 12` | A decision ID vs. five scenario numbers, one of which is `5` | "B5 scenario 5" is a real, ambiguous phrase |
| **X-6** | `AM-16` (amendment) / the "thirteen of 23" figure | The amendment requirement vs. the defective number it targets | Quoting the number without the amendment re-propagates the defect |

### 4.2 Unenumerated families

**X-7, X-8, X-9, X-10** — registered in [T16], not enumerated in this session's evidence.
They must be carried forward verbatim from [T16] §collision register. This document does
not guess at them.

### 4.3 Why collisions block approval

An approval record names a decision. If the name is ambiguous, the approval is ambiguous.
Registering an approval against a colliding identifier produces a record that cannot be
relied on later — which is worse than no record, because it *looks* like one.

**Therefore: X-1 … X-10 must be resolved before the first approval is entered.** This is
stage 1 of the recommended order in §6.

---

## 5. B5 five-scenario decomposition

### 5.1 The set

B5 is **not selected**. The scenarios in scope are:

| Scenario | In scope | Selection state |
|---|---|---|
| 1 | yes | not selected |
| 2 | yes | not selected |
| 3 | yes | not selected |
| 5 | yes | not selected |
| 12 | yes | not selected |

Five scenarios: **1, 2, 3, 5, 12**. Note the gaps — 4, 6–11 are out of scope. The set is
not contiguous, which is itself a source of error: a reader who assumes "1 through 5" will
include scenario 4 and omit scenario 12.

### 5.2 What "not selected" means here

The scenario *set* is established. What is **not** established is the owner's decision
about them — whether all five are required, whether any is optional, and in what order
they must pass. B5 remains an open decision.

### 5.3 Collision note

`B5` the decision and `5` the scenario number collide (X-5). Any reference must say
"B5" or "scenario 5", never "B5/5" or "B5 scenario 5" without disambiguation.

### 5.4 Interaction with Reading B

Reading B requires all Group B decisions resolved before BL-22. B5 is a Group B decision.
**B5 is therefore a BL-22 precondition**, and it is unselected. This alone is sufficient
to keep BL-22 closed.

---

## 6. Recommended order of owner approvals

Six stages. The order is driven by dependency, not by importance: each stage removes a
blocker that would otherwise make the next stage's records unreliable.

### Stage 1 — Resolve identifier collisions (X-1 … X-10)

**Why first:** an approval recorded against an ambiguous identifier is not an approval.
Nothing downstream is safe until names are unambiguous.
**Exit condition:** all ten families enumerated and disambiguated in [T16].
**Owner action required:** none — this is a documentation task, but it must be *done*
before stage 2, not alongside it.

### Stage 2 — Resolve the amendment set (AM-1 … AM-21)

**Why second:** the amendments correct the documents that the decisions are recorded in.
Approving a decision into a defective document propagates the defect.
**Blocking amendments:** **AM-1, AM-2, AM-3, AM-14, AM-21** — these five must be resolved
before any approval. The remaining sixteen may follow.
**AM-16 specifically:** the "thirteen of 23" worksheet defect. Until AM-16 is resolved,
no count in this register can be trusted, including the counts in §1.
**Owner action required:** confirm the five blocking amendments are accepted.

### Stage 3 — Register the four existing selections

**Why third:** the owner has already decided these. Registering them converts stated
intent into durable record at no additional decision cost.
**Items:** A3 (Option A), B1 (Option A), B6 (Option A), C-02 (Reading B).
**Precondition:** G-2 (add SELECTED state) must be closed first, or these will be
mis-registered as approved.
**Owner action required:** ratify the four selections as recorded in [SUP].

### Stage 4 — Resolve the ten outstanding A/B decisions

**Why fourth:** Reading B makes every Group A and Group B decision a BL-22 precondition.
This is the largest block of work and the one that actually gates BL-22.
**Items:** A1, A2, A4, B2, B3, B4, B5, B7, B8, B9.
**Note:** B5 carries the five-scenario set (§5) and is a precondition in its own right.
**Owner action required:** decide all ten. There is no shortcut — Reading B admits none.

### Stage 5 — Resolve Group C

**Why fifth:** C-group decisions are correctness decisions. They are not BL-22
preconditions under Reading B, but they are preconditions for any claim that FAST-02 is
correct rather than merely sequenced.
**Items:** C1, C2, C3, C4 — plus the C-02 defect itself (distinct from Reading B, X-4).
**Owner action required:** decide the four, and confirm whether C-02 maps to one of them
(UQ-4).

### Stage 6 — Resolve Group D and close BL-22

**Why last:** Group D is delivery and documentation. It is not a BL-22 precondition, but
it is a completeness precondition.
**Items:** D1–D6, then the BL-22 precondition check.
**BL-22 status:** **12 preconditions, all unmet.** BL-22 cannot be attempted.
**Owner action required:** decide D1–D6, then authorise the BL-22 precondition review.

### 6.1 Why not reorder

- **Collisions before amendments:** amendments reference identifiers. Fixing text before
  fixing names means fixing it twice.
- **Amendments before registration:** registering into a defective document is the exact
  failure mode AM-16 describes.
- **Registration before new decisions:** the four existing selections are free. Taking
  them first reduces the open set from 23 to 19 before any new work.
- **A/B before C:** Reading B mandates it. This is not a preference.
- **C before D:** correctness before delivery. A delivered-but-wrong FAST-02 is worse
  than an undelivered one.

---

## 7. Decisions the owner can make now

These require no further analysis. Each is a single question with a recorded
recommendation.

| # | Question | Recommendation |
|---|---|---|
| 1 | Ratify A3 = Option A (conditional target, not implemented)? | Yes — it is already selected; ratification makes it durable |
| 2 | Ratify B1 = Option A (`src/sabiroute/request_transform/`)? | Yes — same |
| 3 | Ratify B6 = Option A (already implemented at `completions.py:1608`)? | Yes — the only decision already true of the code |
| 4 | Ratify C-02 = Reading B (all A + all B before BL-22)? | Yes — it is the sequencing rule the rest of this order depends on |
| 5 | Accept the five blocking amendments (AM-1, AM-2, AM-3, AM-14, AM-21)? | Yes — nothing can be registered until they are accepted |
| 6 | Authorise resolution of AM-16 (the 13-vs-4-vs-0 count)? | Yes — this is the critical gap |
| 7 | Add a SELECTED state to the [T16] schema? | Yes — without it, G-1 cannot close honestly |
| 8 | Confirm whether C-02 maps to one of C1–C4 (UQ-4)? | Needs owner knowledge — cannot be recommended |

Items 1–7 are procedural and can be answered immediately. Item 8 requires information
this reconciliation does not have.

---

## 8. What this document does not do

Explicitly, and by design:

- **It does not approve anything.** 0 of 23 decisions are approved. This document does not
  change that number.
- **It does not close any gate.** R6 and G7 are **NOT GRANTED**.
- **It does not freeze any artefact.** Nothing is frozen.
- **It does not sign anything.** There is no signature on this document and none is
  implied.
- **It does not declare FAST-02 closed.** FAST-02 is **NOT CLOSED**.
- **It does not change the readiness figure.** R6.0 remains **~29%**, verdict **NO-GO**.
- **It does not resolve AM-16.** The 12-vs-13 arithmetic discrepancy is carried forward
  as an open defect.
- **It does not enumerate X-7 … X-10.** They are carried forward from [T16].
- **It does not reflect any context outside [T16], [SUP], and [WS].** claude-mem was
  unavailable (401) throughout.

### 8.1 Standing

| Claim | Standing |
|---|---|
| FAST-02 closed | **NO** |
| FAST-02 frozen | **NO** |
| FAST-02 signed | **NO** |
| R6 granted | **NO** |
| G7 granted | **NO** |
| R6.0 readiness | **~29%** |
| Verdict | **NO-GO** |
| Decisions approved | **0 / 23** |
| BL-22 preconditions met | **0 / 12** |

---

## 9. Open items carried forward

| ID | Item | Owner of the gap |
|---|---|---|
| UQ-1 … UQ-18 | Unresolved owner questions, as registered | owner |
| UQ-4 | Does C-02 map to one of C1–C4? | owner |
| AM-1, AM-2, AM-3, AM-14, AM-21 | Blocking amendments | owner |
| AM-16 | Worksheet arithmetic defect (13 vs 4 vs 0) | documentation |
| X-7 … X-10 | Unenumerated collision families | documentation |
| G-1 … G-6 | Recording and registration gaps (§3) | documentation |
| — | claude-mem 401 — reconciliation not cross-checked | infrastructure |

---

*End of reconciliation. No approval, gate closure, freeze, or signature is expressed or
implied by this document.*
