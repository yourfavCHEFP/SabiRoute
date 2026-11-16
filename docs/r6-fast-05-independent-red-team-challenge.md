# R6 / FAST-05 — Independent Red-Team Challenge

**Status:** INDEPENDENT ADVERSARIAL REVIEW — NO APPROVAL AUTHORITY — NO DOCUMENT AMENDED
**Mission:** R6-FAST-05 · independent red-team challenge of the R6.0 closure operation
**Baseline (independently re-derived this session):** branch `feat/sabiroute-routing-foundation`, HEAD `319a711` (`319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`), divergence ahead 6 / behind 3 against origin
**Files created:** this document only. **Files modified:** none. **Registers amended:** none.
**Authority granted by this document:** none. It approves no decision, closes no gate, freezes no artefact, edits no protected path, and carries no signature.

This review does not agree with the other chats by default. Every accepted claim below names the
document and line that supports it, and every claim I could not support from the tree is marked
`UNSUPPORTED` rather than repeated. Where the corpus contradicts itself, the contradiction is
reported, not smoothed.

---

## 0. Method and evidence labels

The review re-derived the baseline from Git and read the primary evidence documents directly. It did
not inherit branch, HEAD or tracking state from any earlier report.

| Label | Meaning |
|---|---|
| **VERIFIED (tree)** | read directly from the repository this session |
| **VERIFIED (runtime)** | a Git command was executed and its output read |
| **STATIC FINDING** | code fact confirmed by reading; runtime consequence not executed |
| **CORPUS CLAIM** | asserted by an R6 document; accepted only after I located its source |
| **UNSUPPORTED** | asserted somewhere in the corpus but not locatable in the primary record |
| **CONTRADICTED** | two corpus documents state incompatible facts; both quoted |

Primary sources read this session:

- `docs/r6-owner-decision-supplement-2026-11-04.md` (Terminal F supplement, `[SUP]`)
- `docs/r6-fast-02-governance-reconciliation.md` (`[FAST-02]`)
- `docs/r6-close-final-01-r6.0-closure-package.md` (`[CF-01]`, the closure package of record)
- `docs/r6-close-final-02-r6.0-closure-reverification-2026-11-05.md` (`[CF-02]`)
- `docs/r6-decision-resolution-and-approval-campaign.md` (Terminal A campaign record)
- `src/sabiroute/api/completions.py` and `tests/test_r6_settlement_integrity.py`

---

## 1. Baseline — independently re-derived

| Fact | Value | Label |
|---|---|---|
| Branch | `feat/sabiroute-routing-foundation` | **VERIFIED (runtime)** |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` (`319a711`) | **VERIFIED (runtime)** |
| R6 documents tracked in Git | **none** — `git ls-files docs` returns 16 files, none R6 | **VERIFIED** — corroborated by `[CF-02]` §2, which records the same command result with the same conclusion |
| U0 test artefact | `tests/test_r6_settlement_integrity.py` **exists**, is substantive, and is **untracked** | **VERIFIED (tree)** |

`[CF-01]` §0 recorded that `git rev-parse`, `git status`, `ls`, `find` and `grep` were all `BLOCKED`
in its session, so *"every Git-level fact in this document is INHERITED, not re-derived."*
`[CF-02]` §1 states that limitation did not recur and re-runs the commands with results matching the
inherited baseline. **The inherited baseline is therefore confirmed** — but only by `[CF-02]`, not by
`[CF-01]`, which remains a document that does not certify its own baseline. This is disclosed well by
the corpus and is not a defect in honesty; it is a defect in the durability of the record of record
(see CRITICAL-1).

---

## 2. Findings

### CRITICAL — blocks closure

#### CRITICAL-1 — The entire R6 corpus is untracked; the closure evidence has no provenance anchor

**Evidence.** `git ls-files docs` returns 16 tracked files, none of them R6. `[CF-02]` §2 records this
**VERIFIED BY RUNTIME** and states: *"Every R6 document — T9 through T17, the ADR pack, the decision
pack, the prep documents, the owner-decision supplement and worksheet, the BM25 selection record, the
register amendment proposal, and CLOSE-FINAL-01 itself — exists only as an untracked working-tree
file."* I independently confirmed branch and HEAD and that no R6 path appears in tracked `docs/`.

**Why it blocks.** A closure signed against an untracked corpus is a closure whose own evidence is not
preserved. The corpus survives a reboot but not `git clean`, a fresh clone, or a branch switch that
discards untracked files. `CLAUDE.md` §9A forbids those destructive operations but does not prevent
them, and cannot bind an operator who has not read it. **Durability must be established before any
closure act, not after.** `[CF-02]` itself calls this *"the most consequential new finding"* and states
it is *"one filesystem event away from being unrecoverable."* I concur, and I note that `[CF-01]` —
the closure package of record — predates this finding and does not carry it.

#### CRITICAL-2 — `[CF-01]` upgrades A3's provenance to a status the supplement explicitly forbids

**Evidence — the claim under challenge.** `[CF-01]` §1, A3 row:

> `Owner-selected` — **YES** — *"owner stated directly (rule 5)"*

**Evidence — the primary record.** `[SUP]` §3.1 classifies A3 as:

> **Source class:** `MISSION-FRAMED` ⚠ — see the provenance warning below.

and states, verbatim:

> "The direct A3 utterance with its own timestamp is `MISSING` from every transcript inspected. A3 is
> recorded here on a mission-carried assertion, **not** on a located owner message. It must not be
> upgraded to `EXACT OWNER` status, and line 2805 must not be cited as the owner utterance itself."

`[SUP]` §2.4 defines `MISSION-FRAMED` as *"a mission prompt that **asserts** a prior owner approval;
not the owner's own decision utterance."*

**Verdict on this claim: CONTRADICTED.** `[CF-01]` describes A3 as "owner stated directly." The
supplement that is the sole durable record of the selection says the opposite and forbids the upgrade.
`[CF-01]` performs the exact upgrade `[SUP]` prohibits. This is the single most damaging provenance
error in the corpus, because `[CF-01]` is designated the closure package of record and its §1 ledger is
what a closure act would cite.

#### CRITICAL-3 — `[CF-01]` omits the two strongest selections (B1, B6) while keeping the weakest (A3)

**Evidence — the claim under challenge.** `[CF-01]` §1:

> `| All 22 remaining | NO | NO | NO | NO | NO |`
> "Owner-selected: **1 of 23** (A3)."

**Evidence — the primary record.** `[SUP]` §3.2 records **B1** with **Source class: `EXACT OWNER`**
(transcript line 2716). `[SUP]` §3.3 records **B6** with **Source class: `EXACT OWNER`** (transcript
line 3167). `[SUP]` §4.2 states:

> "Evidenced as selected in session | **3** — A3, B1, B6"

`[FAST-02]` §1.1 independently reconciles to the same set: A3 and B1 and B6 each read `S R`
(selected + recorded), with *"Approved decisions: 0 of 23."*

**Verdict on this claim: CONTRADICTED.** `[CF-01]` reports **one** selection and explicitly marks the
other 22 `NO`. The supplement and `[FAST-02]` both report **three** selections. `[CF-01]` therefore
drops the two selections that *do* carry `EXACT OWNER` provenance (B1, B6) and retains only the one
that does *not* (A3, `MISSION-FRAMED`). The closure package's ledger is wrong in both directions at
once: it overstates A3 and understates B1/B6. A closure act built on this ledger would tell the owner
they have one decision when they have three, and would tell them the strongest of the three is the
weakest.

> **Cross-check.** `[CF-02]` §2's table also repeats `Owner-selected | 1 of 23 (A3)`, inheriting
> `[CF-01]`'s error even though `[CF-02]` §2 is otherwise the most rigorous document in the corpus. The
> error is not isolated to one document; it propagated from `[CF-01]` into its own reverification.

#### CRITICAL-4 — 0 of 23 registered, and BL-22 cannot be discharged on the recorded state

**Evidence.** `[SUP]` §2.5 and §4.2: *"Canonically registered in T16 | **0**"* and *"Gate acceptance |
None is."* `[FAST-02]` §1.1: *"Approved decisions: 0 of 23"* with the ledger marking `G` (registered)
as `0` across every group. `[CF-01]` §1: *"Canonically registered: 0 of 23. Independently verified:
0 of 23. Gate-accepted: 0 of 23."*

**The BL-22 discharge test.** `[SUP]` §4.1 records C-02 Reading B as `EXACT OWNER` and states its
requirement: *"Every Group A decision and every Group B decision must be **recorded** before BL-22 is
signed"* — 13 canonical decisions. `[SUP]` §4.2: only 3 are durably recorded, 0 registered. BL-22
therefore cannot be signed on the current record, and C-02 Reading B is itself a selection the closure
package does not mention at all.

---

### HIGH — requires resolution before closure

#### HIGH-1 — Decision-count discrepancy (12 vs 13) is unresolved and determines the BL-22 discharge count

`[SUP]` §4.3 records that the authorising mission brief states C-02 Reading B requires *"12 canonical
decisions"* with *"nine"* remaining, while the register enumerates **13** A/B cards, and 13 − 3 = **10**
outstanding. `[SUP]` records the integer "12" as *"a miscount and is not adopted"* and flags the
arithmetic as an open owner/register question (§8.1) *"because it determines the BL-22 discharge
count."* **Unresolved.** No closure can state how many decisions must be recorded until this is
settled.

#### HIGH-2 — B5 is unselected; its "five scenarios" are scope, not a decision

`[FAST-02]` §1.2, B5 row: state `—` (**not selected**), with *"Five scenarios in scope: 1, 2, 3, 5,
12."* `[CF-01]` §2.2 warns B5 *"is not a binary checkbox. It carries **five separate owner
decisions**."* So B5 is doubly open: the decision is unselected **and** the five scenarios are an
inventory of what *would* need deciding, not decisions. Any reading of B5 as settled is unsupported by
any source I could locate. **Requires an explicit disposition: B5 is OPEN.**

#### HIGH-3 — `G16` and `G17` do not exist in this repository; the G7 question cannot be answered from it

`[CF-02]` §3.1 records `grep` results: `G16` — no matches anywhere in tree; `G17` — one match,
`reports/my_scorecard.md:71`, which is the PostgreSQL test identifier `PG17`, not a gate. *"The R6
gate scale tops out at `G7`."* The closure mission's reference to `G16`/`G17` sub-items therefore
points at identifiers that resolve nowhere in the repository. **They cannot be interpreted from this
tree without fabricating their content.** `[CF-02]` correctly refuses to invent them; I concur, and I
have not invented them either.

#### HIGH-4 — Track A was never obtained; silence is not approval

`[CF-02]` §5: *"Track A status remains `NOT OBTAINED`. No reviewer was contacted. No prompt was sent.
**Silence is not approval.**"* `[CF-01]` §7 states Track A *"cannot be engaged today."* `[CF-02]` §5
additionally records two protected-surface paths in T11 §15 that **do not exist as written**
(`config/validation.py` → `src/sabiroute/config/validation.py`; `src/sabiroute/dataset.py` →
`src/sabiroute/intelligence/dataset.py`), so *"a reviewer signing T4 or T6/T7 against a path that does
not exist has signed a surface that does not exist."* D17 (Track A sign-off) gates R6.4–R6.7 and is
`OPEN`.

#### HIGH-5 — C-05 is a real defect by inspection, but the U0 test is RED, not proof of a fix

**STATIC FINDING, confirmed.** In `src/sabiroute/api/completions.py`:

- `finish()` reads `attempted` at **`:602`** (`if attempted:`), and again at `:1321`.
- `attempted: list[str] = []` is bound at **`:1311`** — *after* the budget-denial `finish()` calls at
  **`:1291`** and **`:1299`**.
- Therefore a request that reserves quota and is then denied on budget reaches `finish()` → `:596`
  (`if quota_reserved and quota_user_id is not None:`) → `:602` (`if attempted:`) **before** `:1311`
  binds the free variable, raising `NameError` / `UnboundLocalError` instead of the intended 429/503.

This confirms the C-05 failure class by inspection. **What it does not prove:** runtime behaviour. The
U0 artefact `tests/test_r6_settlement_integrity.py` states in its own docstring: *"`test_e01_*` and
both `test_e02_unknown_*` cases are expected to **FAIL** against the current implementation. That
failure is the evidence this mission is asked to produce."* The test is written to be **red**. A red
test is evidence a defect exists; it is **not** evidence the defect has been fixed or closed. No source
I read shows the test executed with a captured result, and `[CF-01]` §13 admitted it could not locate
the artefact at all — the artefact exists, but its execution record does not.

---

### MEDIUM — requires an explicit disposition

#### MEDIUM-1 — Five identifier collisions, not four

`[CF-01]` §4 opens *"Four live collisions exist in this corpus."* `[CF-02]` §3 corrects this to
**five**, the fifth being `T12/A1`–`A6` (accounting defects) versus `GROUP-A/A1`–`A4` (decisions) — a
four-of-four overlap that *"crosses the authority boundary"* because one register is the defect set the
settlement decisions are written against. The clearest proof: decision **A2**'s recommendation cites
*"A6"*, and **there is no decision A6** — it is accounting defect A6. A proposal exists
(`r6-register-amendment-proposal-2026-11-05.md`) but is **`PROPOSAL ONLY`** and unapplied. **Disposition
required: record five collisions; apply the proposal only under owner authorisation.**

#### MEDIUM-2 — C-07 is a static finding, not runtime proof

`completions.py:597–603` comments *"attempts made settle with summed actuals (unknown usage holds the
estimate)"* and the code at `:603` does `_sum_actual_tokens(actual_usage_parts)[2]`. Whether that
actually holds the original estimate on unknown usage — the C-07 claim — is a property of
`_sum_actual_tokens` and the B5 annotation, and I did not execute it. **Label remains STATIC FINDING.**
It must not be cited as runtime-proven until the U0 `test_e02_*` cases are run and captured.

#### MEDIUM-3 — A3's "conditional target" is not current state; reading it as "the architecture is X" is a misread

`[FAST-02]` §1.2 A3 detail: *"Option A was selected as a **conditional target** — it describes where
the architecture should land, not what exists. The five preconditions P1–P5 are unmet."* `[SUP]` §3.1:
*"P1–P5 remain unmet until independently verified and closed. No implementation is authorised."* Any
document, including a closure act, that treats A3 as describing implemented architecture is wrong.
**Disposition required: A3 is a conditional target, P1–P5 open.**

#### MEDIUM-4 — `[FAST-02]` itself slightly flattens A3

`[FAST-02]` §0.3 defines `S` as *"the owner stated a preference on 2026-11-04"* and marks A3 as `S`.
For A3 the owner did **not** state a preference directly — `[SUP]` §3.1 establishes the utterance is
`MISSING` and the source is `MISSION-FRAMED`. `[FAST-02]` is far closer to the truth than `[CF-01]`,
but it still applies an `S` label that the supplement's own classification would not grant A3.
**Disposition: `[FAST-02]`'s A3 `S` should read `MISSION-FRAMED-selected (unconfirmed)`.**

---

### LOW — documentation improvement

- **LOW-1.** `[CF-01]` §0's honest disclosure that its baseline was `BLOCKED` and `INHERITED` is
  exemplary, but the closure package of record still carries an uncertified baseline; `[CF-02]` §1
  certifies it after the fact. The closure act must cite `[CF-02]`, not `[CF-01]` §0, for the
  baseline.
- **LOW-2.** Cross-reference labels are inconsistent (`T16`/`T13`/`T15`/`T17`, `[SUP]`/`[WS]`/`[T16]`).
  A reader must reconstruct the register topology. A single provenance index would remove the room for
  the `[CF-01]` inversion to recur.

---

## 3. Acceptance / rejection matrix

Disposition key: **ACCEPT** = claim independently supported by a primary source I read; **REJECT** =
claim contradicted by a primary source; **CONDITIONAL** = claim is accurate but insufficient as a
closure basis without a named action; **UNSUPPORTED** = claim could not be located in any primary
record.

| # | Claim under challenge | Claimed by | Independent evidence | Disposition |
|---|---|---|---|---|
| 1 | Baseline is `feat/sabiroute-routing-foundation` @ `319a711` | `[CF-01]` §0 (inherited), `[CF-02]` §1 | Re-derived: branch and HEAD match | **ACCEPT** |
| 2 | The R6 corpus is untracked | `[CF-02]` §2 | `git ls-files docs` = 16, none R6; no R6 in tracked `docs/` | **ACCEPT** (finding is correct; its consequence is CRITICAL-1) |
| 3 | A3 = "owner stated directly" | `[CF-01]` §1 | `[SUP]` §3.1: `MISSION-FRAMED`, direct utterance `MISSING`, upgrade forbidden | **REJECT** |
| 4 | Only 1 of 23 owner-selected (A3) | `[CF-01]` §1, `[CF-02]` §2 | `[SUP]` §3.2/§3.3/§4.2: B1 and B6 are `EXACT OWNER`; 3 selected | **REJECT** |
| 5 | 0 of 23 canonically registered | `[SUP]` §2.5, `[FAST-02]` §1.1, `[CF-01]` §1 | Consistent across three independent documents | **ACCEPT** |
| 6 | C-02 Reading B requires all 13 A/B recorded before BL-22 | `[SUP]` §4.1 | `[SUP]` §4.1, `EXACT OWNER`; register enumerates 13 cards | **ACCEPT** |
| 7 | BL-22 can be signed on the current record | implied by any closure proposal | Only 3 of 13 recorded, 0 registered | **REJECT** |
| 8 | C-02 decision count is 12 | mission brief (as quoted) | `[SUP]` §4.3: register enumerates 13; 12 is a miscount | **UNSUPPORTED** |
| 9 | B5 is decided | — (no source claims it) | `[FAST-02]` §1.2: B5 `—` unselected; `[CF-01]` §2.2: five decisions | **REJECT** (B5 is OPEN) |
| 10 | B5 scenarios 1, 2, 3, 5, 12 are in scope | `[FAST-02]` §1.2 | Single source only; no independent corroboration of the scenario numbers | **CONDITIONAL** |
| 11 | G16 / G17 sub-items exist | mission text | `[CF-02]` §3.1: neither exists in repo; `PG17` is a test id | **UNSUPPORTED** |
| 12 | G7 = implementation authorisation | `[CF-02]` §3.1 | `[CF-02]` §3.1 and `[CF-01]` §4.2 agree on gate scales | **ACCEPT** (definition only; not granted) |
| 13 | C-05 NameError on pre-loop `finish()` | corpus | `completions.py` `:602` reads `attempted`; bound `:1311`; `finish()` at `:1291`/`:1299` | **CONDITIONAL** (real by inspection; not runtime-proven) |
| 14 | C-07 unknown-usage settles at full estimate | corpus | `completions.py:597–603` asserts it; not executed | **CONDITIONAL** (static only) |
| 15 | U0 test proves the defects are fixed | — | `test_r6_settlement_integrity.py` is written to be **red** at HEAD | **REJECT** (red test ≠ fix) |
| 16 | Five identifier collisions | `[CF-02]` §3 | `[CF-02]` §3 corrects `[CF-01]` §4's "four"; fifth is `T12/A1–A6` vs `GROUP-A/A1–A4` | **ACCEPT** |
| 17 | Track A obtained or implied | — | `[CF-02]` §5: `NOT OBTAINED`, no contact | **REJECT** |
| 18 | A3 describes current architecture | — | `[FAST-02]` §1.2, `[SUP]` §3.1: conditional target, P1–P5 unmet | **REJECT** |
| 19 | A3 `S` (owner stated preference) | `[FAST-02]` §0.3/§1.2 | `[SUP]` §3.1: `MISSION-FRAMED` | **CONDITIONAL** (should read `MISSION-FRAMED-selected`) |
| 20 | R6.0 is closed | no document claims it | `[CF-01]` §0, `[CF-02]` §0: both state it is **not** closed | **REJECT** (and the corpus agrees) |

---

## 4. Verdict

**REJECT.**

R6.0 closure is not supportable, and this verdict does not rest on the corpus's unanimous
self-assessment that R6.0 is not closed. It rests on four independently verifiable facts:

1. **The corpus has no provenance anchor** — zero R6 documents are tracked in Git (CRITICAL-1).
2. **The closure package of record misstates provenance in both directions** — it upgrades A3 to
   "owner stated directly" (the supplement forbids exactly this) and omits B1 and B6, the two
   `EXACT OWNER` selections, from its ledger (CRITICAL-2, CRITICAL-3).
3. **0 of 23 decisions are canonically registered**, so BL-22 — which C-02 Reading B requires to follow
   all 13 A/B recordings — cannot be discharged (CRITICAL-4).
4. **B5 is unselected, Track A was never obtained, and G16/G17 resolve nowhere** — three independent
   gaps that no amount of reconciliation can close without new owner action (HIGH-2, HIGH-3, HIGH-4).

**What I accept.** `[CF-02]`, `[SUP]` and `[FAST-02]` are honest, self-critical documents whose
findings survive adversarial reading. Their factual claims, where I could verify them, are correct.
The corpus's repeated refusal to upgrade its own status is a credit. **It is not, however, a basis for
acceptance.** Honesty about a failed state does not make the state pass.

**What I reject.** The closure, and specifically `[CF-01]` as the closure record of it, because its §1
ledger is contradicted by the supplement and would mislead an owner signing on it. `[CF-01]` must be
corrected (A3 → `MISSION-FRAMED`; A3/B1/B6 → three selections) or superseded before any closure act
cites it.

---

## 5. What would change this verdict to ACCEPT-WITH-CONDITIONS

The verdict is not a permanent judgement on the corpus; it is a judgement on the current closure
operation. It would move if, and only if, all of the following held:

1. **The R6 corpus is tracked.** All R6 documents committed to `feat/sabiroute-routing-foundation`
   under explicit owner authorisation, so the evidence survives `git clean` and a fresh clone.
2. **`[CF-01]` §1 is corrected** — A3 relabelled `MISSION-FRAMED` with the direct-utterance `MISSING`
   note intact; the ledger records three selections (A3, B1, B6), not one.
3. **The 12-vs-13 count is settled** in the register by owner decision (HIGH-1).
4. **All Group A and Group B decisions are recorded and canonically registered** — 13, not 3 — before
   BL-22 is signed (C-02 Reading B).
5. **B5 is decided** across its five owner decisions (HIGH-2).
6. **Track A sign-off is obtained** for D17, with the two non-existent protected paths corrected first
   (HIGH-4).
7. **C-05 and C-07 have captured runtime evidence** — the U0 red tests executed and their results
   recorded — not merely static inspection (HIGH-5, MEDIUM-2).
8. **The G16/G17 question is either withdrawn or supplied from an external gate register** (HIGH-3).

Until then, **REJECT** stands.

---

*This document has no approval authority. It amends no protected file, registers no decision, and
closes no gate. It records one independent reviewer's challenge and the sources for every conclusion.*
