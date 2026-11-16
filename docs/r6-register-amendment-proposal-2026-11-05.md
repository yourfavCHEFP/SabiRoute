# R6 — Register Amendment Proposal: the `A1`–`A4` identifier collision

**Status:** PROPOSAL ONLY. This document amends nothing, applies nothing, approves nothing, adopts no ADR, records no decision, changes no decision status, grants no G7 and authorises no implementation, test, or U0/U1/R6.1/Track A work. **Every proposed edit in §4 and §5 requires explicit owner authorisation before it may be applied.**
**Mode:** read-only audit of the existing corpus. Exactly one new file was created — this one. **T12, T13, T14, T15 and T16 were not modified by this proposal.**
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`. The working tree carried pre-existing untracked files only; no tracked modification existed before this proposal and none was introduced. `docs/` was searched (33 entries) and contains no prior amendment, proposal or collision artefact — this file duplicates and supersedes nothing.
**Proposes amendments to:** `docs/r6-t16-r6-decision-option-register.md` (T16, the register) — §4 below.
**Recommends corrections to, without authority to apply:** `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` (T13, the authority) and `docs/r6-t12-accounting-integrity-and-gate-closure.md` (T12) — §5 below.

**Canonical count unaffected: 23 decisions remain 23. All 23 remain `OUTSTANDING`. `0 approved by this proposal.`**

---

## 1. What is proposed, and what is not

**What is proposed.** One finding and two response sets. The finding is that **two independent identifier registers both label their members `A1`–`A4`**, that the collision is live and material, and that it crosses the boundary between the register the owner answers and the defect set against which the settlement decisions are specified. The responses are a set of **amendments to the register** (§4) and a set of **recommended corrections to the authority documents** (§5).

**What is not proposed.** This document does **not** apply any edit. It does **not** create a decision, retire a decision, or renumber anything. It does **not** adopt an option, resolve `C-02`, resolve `ADR-2/C-1`, or advance any status off `OUTSTANDING`. It does **not** claim that any defect is fixed, that any settlement contract is implemented, or that any gate is satisfied.

**Why this is a proposal and not an applied correction.** T16 is a `COMPLETE` extraction artefact whose only authorised change was its own creation. T13 is the decision authority and T14 audited it; T15 briefs it. Amending any of them requires an owner act, because the difference between "the register said `A1`" and "the register said `GROUP-A/A1`" is itself part of the audit trail. A proposal keeps the amendment documentable and refusable; editing in place would destroy the record that the register ever carried an unqualified label.

---

## 2. Finding — two registers, four shared labels

The corpus contains two identifier systems that both use the letters `A1`–`A4`.

### 2.1 Register 1 — Accounting defects (native to T12)

| ID | Defect | Anchor |
|---|---|---|
| **A1** | Unknown-usage detection is budget-gated | T12 §5; T12 L19, L94 |
| **A2** | No-usage success is never flagged | T12 §6; T12 L20, L117 |
| **A3** | `finish()` reads `attempted` before binding (masked 503 + quota leak) | T12 §7; T12 L21, L131 |
| **A4** | `cleanup_errors` / `ledger` written, never read | T12 §8; T12 L22, L159 |
| **A5** | Mixed known/unknown settlement | T12 §9, L183 |
| **A6** | Client-cancel attempt sets no unknown flag | T12 §9A, L207 |

T12 L252 states the set explicitly: *"four root causes — A1 (gating), A2 (success path), A3 (pre-loop binding), A5 (mixed settlement) — plus A6 (cancel path) and A4 (unobservable failure)."*

### 2.2 Register 2 — Group A architecture decisions (native to T13 §7, extracted as T16 §4)

| ID | Decision question | Anchor |
|---|---|---|
| **A1** | Adopt §§8–15 as the frozen architecture? | T13 L276; T16 L63, L91 |
| **A2** | Treat Tier-1 metering fixes as integrity work, not optional feature work? | T13 L277; T16 L64, L104 |
| **A3** | Adopt ADR-1: Option A conditional, explicitly not implemented? | T13 L278; T16 L119 |
| **A4** | Adopt T10-1…T10-7 scoping? | T13 L279; T16 L66, L134 |

### 2.3 The overlap is four of four

**The overlap is `A1`, `A2`, `A3`, `A4` — every single Group A decision label collides with an accounting defect.** The reverse is not symmetric: defects `A5` and `A6` have no decision counterpart, so the collision is bounded at four labels and no fifth decision is implied. **No decision `A5` or `A6` exists and none is created here.**

### 2.4 This is not the collision T16 §7 already handles

T16 §7 already resolves `ADR-2/C-1` (package-name conflict) against `GROUP-C/C1` (byok/paid billing semantics). That collision is **one label, one document pair, and both members are internal to the ADR/decision literature.** This collision is materially different:

| | T16 §7 collision (`C-1` / `C1`) | This collision (`A1`–`A4`) |
|---|---|---|
| Labels shared | 1 | **4** |
| Registers | ADR-2 internal conflicts vs Group C | **Accounting defects vs Group A decisions** |
| Crosses authority boundary | No — both are decision/ADR literature | **Yes — one register is the defect set the settlement decisions are written against** |
| Already addressed | Yes, T16 §7 | **No** |

The `A1`–`A4` collision therefore inherits none of §7's protection and needs its own rule.

---

## 3. Harm analysis — why this is not cosmetic

Four harm-bearing clusters were verified by reading the lines, not by inference.

### Cluster 1 — Decision A2's rationale cites an accounting defect by a label that has no decision meaning

Decision **A2** reads, in all three places it is recorded:

> **Yes** — BL-01…BL-04/**A6**/BL-06/BL-07 close live holes

- T13 L277 (the authority row)
- T12 L752 (§22, the reproduced decision table)
- T16 L64 (the register index row)

**There is no decision `A6`.** Within the Group A register, `A6` resolves to nothing. It is accounting defect `A6` (T12 §9A, the client-cancel path). A reader answering A2 from the register must leave the register to discover what the recommendation's own justification means. This is the single clearest proof that the two registers leak into each other rather than merely coexisting.

### Cluster 2 — Accounting labels inside T13's decision-native prose

T13's native `A1`–`A4` are **decisions**. Two of its lines use the same labels for **defects**, unqualified:

- **T13 L516** (the `X2` scenario row): *"… Flag `False` ⇒ partial sum charged | **BL-02 / A1**"* — this `A1` is the gating defect, not the architecture decision.
- **T13 L787**: *"The **A4** finding (`cleanup_errors` / `ledger` written but never read) was not re-derived by T13…"* — this `A4` is the dead-observability defect, not the T10 scoping decision.

Both sit inside the document a reviewer must read to answer A1–A4.

### Cluster 3 — The decision table reproduced inside the defect register

T12 is native to **defects**. Its §22 (L751–754) nevertheless reproduces the **decision** table:

| T12 line | Row |
|---|---|
| L751 | `| A1 | Adopt §§8–15 as the frozen architecture? …` |
| L752 | `| A2 | Treat Tier-1 metering fixes as integrity work …` |
| L753 | `| A3 | Adopt ADR-1: Option A conditional …` |
| L754 | `| A4 | Adopt T10-1…T10-7 scoping? …` |

So within one document, `A1` in §5 and `A1` in §22 denote different objects. T12 L891 compounds it in the audit checklist: *"All five accounting findings adjudicated | A1–A5 **plus A6 (new)**"* — correct as accounting, indistinguishable from decisions if read out of context.

### Cluster 4 — A4's dependency cell is empty in both T16 registers

| Location | Current cell |
|---|---|
| T16 L66 (§3 master index, A4 row) | `—` |
| T16 L141 (§4 A4 card) | `— (none recorded).` |

Compare **A1**, whose dependency cell reads `Group B record` in both places (T16 L63, L98). The two cards are inconsistent in granularity: A1's cell names a record; A4's names nothing, although A4's own subject — "Adopt T10-1…T10-7 scoping" — is itself a record that must exist for the decision to be answerable. The cell is not wrong, but it is **under-specified**: a reader cannot tell whether A4 has no dependency, or whether T13 recorded none, or whether the T10 record is simply assumed.

### Materiality in one paragraph

The owner session answers **the register**. In the register, `A1`–`A4` are architecture decisions. In the settlement argument, `A1` and `A5` are defects, and decision **B5**'s required contract is specified against them (T16 §5 C-07); decision **A2**'s rationale is specified against defect **A6**. If a session records "A1" unqualified and a later fixer reads "A1" in T12, **the two acts are indistinguishable in the audit trail** — and one of them authorises an architecture freeze while the other names a cause of under-billing. T16 §7 and T14 `C-02` were raised precisely to prevent this class of ambiguity. This instance is four times the surface and sits closer to the money.

---

## 4. Proposed amendments to T16 (the register)

Five amendments. Each is stated as exact target, exact current text, exact proposed text. **None is applied.**

### A-1 — Insert a new §7.1 defining the qualified-identifier rule

**Target:** T16, immediately after §7 ("Identifier collision — `ADR-2/C-1` versus `GROUP-C/C1`"), before §8.

**Current text:** *(no such section exists)*

**Proposed insertion:**

> ### 7.1 Identifier collision — accounting defects `A1`–`A6` versus Group A decisions `A1`–`A4`
>
> A second, larger collision exists alongside the `ADR-2/C-1` one above. It is four labels wide and is not covered by §7's rules.
>
> | Register | Meaning | Source |
> |---|---|---|
> | **Accounting defects** `A1`–`A6` | 1 = gating · 2 = no-usage success · 3 = pre-loop binding · 4 = dead observability · 5 = mixed settlement · 6 = client-cancel | T12 §5–§9A |
> | **Group A decisions** `A1`–`A4` | 1 = adopt §§8–15 · 2 = Tier-1 as integrity work · 3 = ADR-1 · 4 = T10 scoping | T13 §7; this register §4 |
>
> Rules, applied in the same spirit as §7:
> 1. The canonical decision IDs in this register remain **`A1`–`A4`**, unchanged. No decision is renumbered, and the canonical count remains **23**.
> 2. Accounting defects are never given a decision ID and are never written bare in cross-reference. When referred to outside T12's own native prose, they are written **`T12/A1` … `T12/A6`**.
> 3. Group A decisions, when referred to outside this register's own native prose, are written **`GROUP-A/A1` … `GROUP-A/A4`** — parallel to the existing `GROUP-C/C1` convention.
> 4. **No new decision ID is created** for any part of this collision.
> 5. In the §11 response sheet, an `A1`–`A4` row is **always a decision question**. It records a decision selection and nothing else.
>
> **Owner-session instruction:** when answering `A2`, read its justification as *"BL-01…BL-04 / `T12/A6` / BL-06/BL-07"*. The `A6` is a defect, not a decision.

### A-2 — Qualify `A6` in decision A2's rationale

**Target 1:** T16 L64 (§3 master index, A2 row).
**Current:** `**Yes** — BL-01…BL-04/A6/BL-06/BL-07 close live holes`
**Proposed:** `**Yes** — BL-01…BL-04/`T12/A6`/BL-06/BL-07 close live holes`

**Target 2:** T16 §4, the A2 card, "Existing recommendation" line.
**Current:** `**Yes** — BL-01…BL-04/A6/BL-06/BL-07 close live holes (T13 §7).`
**Proposed:** `**Yes** — BL-01…BL-04/`T12/A6`/BL-06/BL-07 close live holes (T13 §7).`

### A-3 — Make A4's dependency cells explicit

**Target 1:** T16 L66 (§3 master index, A4 row, Dependencies column).
**Current:** `—`
**Proposed:** `— (no cross-decision dependency; the T10-1…T10-7 record is the decision's **input**, not a gating dependency)`

**Target 2:** T16 §4, the A4 card, `**Dependencies:**` line (L141).
**Current:** `**Dependencies:** — (none recorded).`
**Proposed:** `**Dependencies:** — (no cross-decision dependency; the T10-1…T10-7 record is the decision's **input**, not a gating dependency).`

**Note on A-3.** This asserts no new dependency and reverses no source. It records, in words, what "—" already means, and removes the ambiguity between "none", "unrecorded", and "assumed". If the owner prefers the cell to stay as `—`, the amendment is withdrawn without affecting A-1, A-2, A-4 or A-5.

### A-4 — Add the collision footnote to the §11 response sheet

**Target:** T16 §11, immediately below the 23-row table, inside the "Non-decision items to record separately" list.

**Current:** *(four bullets: `ADR-2/C-1`, `C-02` reading, BL-22, CLAUDE.md §12)*

**Proposed:** add a fifth bullet —

> - **`A1`–`A4` collision** — the rows `A1`–`A4` above are **decision** questions (`GROUP-A/`). The same labels in T12 are accounting defects (`T12/`). Answer the decision; do not record a defect disposition here. See §7.1.

### A-5 — Cross-reference §7 forward to §7.1

**Target:** T16 §7, final paragraph ("Owner-session instruction").
**Proposed:** append one sentence — *"A second and larger collision of the same class — the four-way `A1`–`A4` overlap between accounting defects and Group A decisions — is handled in §7.1."*

---

## 5. Recommended corrections outside this document's authority

These are **not amendments this proposal can make.** T13 is the decision authority and was audited by T14; T12 is an evidence report. Changing either is a separate owner act. They are listed because leaving them uncorrected means the register is qualified while its sources are not, and the ambiguity would survive in exactly the documents a reviewer reads first.

| ID | Document | Line | Current | Proposed |
|---|---|---|---|---|
| **C-1** | T13 | L516 | `… \| **BL-02 / A1**` | `… \| **BL-02 / `T12/A1`**` |
| **C-2** | T13 | L787 | `The **A4** finding (…)` | `The **`T12/A4`** finding (…)` |
| **C-3** | T12 | L751–754 | decisions reproduced with bare `A1`–`A4` | annotate the four rows as `GROUP-A/A1`–`GROUP-A/A4` |
| **C-4** | T12 | L891 | `All five accounting findings adjudicated \| A1–A5 **plus A6 (new)**` | `… \| `T12/A1`–`T12/A5` **plus `T12/A6` (new)**` |

**Why these four and no others.** They are the sites where a label is used for the *other* register inside a document whose native register is the opposite one. T12's §5–§9A headings and T13's A1–A4 decision rows are native and need no change; T15's three mentions (L156, L183, L231) are all decisions and are already unambiguous in context.

---

## 6. What the amendment does not change

| Item | Before | After (if A-1…A-5 applied) |
|---|---|---|
| Canonical decision count | **23** | **23** — unchanged |
| Decision IDs | `A1`–`A4`, `B1`–`B9`, `C1`–`C4`, `D1`–`D6` | **identical** |
| Approval status of all 23 | `OUTSTANDING` | **`OUTSTANDING`** |
| ADR-1 / ADR-2 | `PROPOSED` | **`PROPOSED`** |
| G7 | `NOT GRANTED` | **`NOT GRANTED`** |
| R6.0 freeze | `CONDITIONALLY READY` | **unchanged** |
| Panel B/C/D/E | `NOT OBTAINED` | **unchanged** |
| `C-02` reading | unresolved, both readings live | **unresolved, both readings live** |
| `ADR-2/C-1` | unresolved, must be recorded | **unresolved, must be recorded** |
| Implementation authority | none | **none** |

**The amendment is a labelling act, not a governance act.** It changes how two registers name their members. It resolves no question, closes no gate, and satisfies no condition. `T12/A6` being unambiguous does not fix the client-cancel path; naming the collision does not settle the settlement contract.

---

## 7. Verification log — what was verified and what was not

**Verified by direct read at `319a711` (line-anchored, quoted above):**
- T12 §5–§9A define accounting defects `A1`–`A6` (headings L94, L117, L131, L159, L183, L207; table L19–L22).
- T13 §7 L276–L279 define Group A decisions `A1`–`A4`.
- T16 L63, L64, L66, L91, L119, L134, L141 reproduce those four decisions faithfully.
- Decision A2's rationale cites `A6` at T13 L277, T12 L752 and T16 L64 — three sightings, all identical.
- T13 L516 and L787 use `A1`/`A4` as accounting defects inside decision-native prose.
- T12 §22 L751–L754 reproduce the decision table inside the defect register.
- T16 §7 handles the `C-1`/`C1` collision and its rules do **not** reach `A1`–`A4`.
- `docs/` contains no prior amendment, proposal or collision artefact; this file is not a duplicate.

**Not verified, and not claimed:**
- No accounting defect was re-derived, re-tested or confirmed fixed by this proposal. Their `CONFIRMED DEFECT` status is inherited from T12/T13 and quoted, not re-established.
- No runtime behaviour, test result, or settlement computation was exercised.
- The exact count of ambiguous sites would depend on how "ambiguous" is defined; §5 names the four sites where a *cross-register* label appears in a document native to the other register, and that set was enumerated line by line rather than counted by search, because a token count cannot distinguish a decision `A1` from a defect `A1`.
- T13 L178 and T12 L457 both enumerate "A1–A4" as the **T11 §18 question** set, i.e. decisions. They are unambiguous in context and are therefore not listed in §5.

---

## 8. Decision requested

**Recommendation:** apply **A-1 … A-5** to T16, and hold **C-1 … C-4** for the same owner session that resolves `ADR-2/C-1` and `C-02`, because all three are the same class of defect — an identifier that means two things — and settling them once is cheaper and more defensible than settling them in three sittings.

**The specific authorisation sought:** permission to apply A-1…A-5 to `docs/r6-t16-r6-decision-option-register.md` as a recorded amendment, leaving the canonical count at 23 and every status at `OUTSTANDING`.

**Nothing in this proposal is in force.** Until the owner answers, T16 stands exactly as written, with the collision live and undocumented — which is precisely the condition this document was written to make visible.

---

## 9. Final status

**PROPOSAL COMPLETE — ONE FINDING (FOUR-WAY `A1`–`A4` REGISTER COLLISION), FIVE PROPOSED AMENDMENTS TO T16, FOUR RECOMMENDED CORRECTIONS TO T13/T12; 0 APPLIED; 0 DECISIONS TAKEN; 0 STATUSES CHANGED; CANONICAL COUNT 23 UNCHANGED; T12/T13/T14/T15/T16 UNMODIFIED.**

*This document approves nothing and applies nothing. A proposed amendment is not an amendment. A named collision is not a resolved collision.*

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
