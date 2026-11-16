# R6-FAST-04 — R6.0 Closure Architecture

**Status:** PLANNING ARTEFACT ONLY. This document signs nothing, amends nothing, registers no decision, adopts no ADR, resolves no reading, grants no `R6/G7`, authorises no implementation, test, U0/U1/R6.1/Track A work, commit, push or deployment. It is the **path** to legitimate closure, not the closure.

**Mode:** read-only verification of the live repository plus read-only synthesis of the existing corpus. **Exactly one new file was created — this one.** No existing document was modified. No register was amended. No tracked file was touched.

**Baseline (re-derived this session, not inherited):**

| Fact | Command | Result | Label |
|---|---|---|---|
| Branch | `git rev-parse --abbrev-ref HEAD` | `feat/sabiroute-routing-foundation` | **VERIFIED BY RUNTIME** |
| HEAD | `git rev-parse HEAD` | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` | **VERIFIED BY RUNTIME** |
| Divergence | `git rev-list --left-right --count HEAD...origin/…` | `6	3` (6 ahead, 3 behind) | **VERIFIED BY RUNTIME** |
| Tracked modifications | `git status --porcelain --untracked-files=no` | **0** | **VERIFIED BY RUNTIME** |
| R6 documents tracked in Git | `git ls-files docs \| grep -c r6` | **0** | **VERIFIED BY RUNTIME** |
| `finish()` reads `attempted` | `sed -n '602p'` | `if attempted:` | **VERIFIED BY RUNTIME** |
| `attempted` binding | `sed -n '1311p'` | `attempted: list[str] = []` | **VERIFIED BY RUNTIME** |
| Loop entry | `sed -n '1345p'` | `for attempt in range(1, policy.max_attempts + 1):` | **VERIFIED BY RUNTIME** |
| `config/validation.py` | `ls` | present at `src/sabiroute/config/validation.py` | **VERIFIED BY RUNTIME** |
| `dataset.py` | `ls` | present at `src/sabiroute/intelligence/dataset.py` | **VERIFIED BY RUNTIME** |
| `request_transform/` | `ls -d` | **does not exist** | **VERIFIED BY RUNTIME** |

**Canonical count unaffected: 23 decisions remain 23. All 23 remain `OUTSTANDING`. `0 approved by this document.`**

---

## 0. The one distinction this document exists to enforce

> **R6.0 closure is a governance act. R6.1 entry is an engineering act. They are not the same gate, they do not share a signature, and neither implies the other.**

| | **R6.0 — architecture freeze** | **R6.1 — implementation entry** |
|---|---|---|
| Nature | Adopt, adopt, record-then-sign | Authorise, review, implement |
| Requires code | **No** | Yes |
| Requires external reviewer | **No** | **Yes** — Track A T1–T8 |
| Requires `R6/G7` | **No** | **Yes** — BL-23 |
| Requires BL-22 | **Yes** — it *is* BL-22 | Yes — as condition 1 |
| Owner-time vs engineering-time | ~100% owner | Mixed |
| Current state | `CONDITIONALLY READY` — **not closed** | `NOT READY` — **not authorised** |

**Consequence for sequencing.** Six of the seven external signatures in CLOSE-FINAL-01 §9 block **Release or R6.1**, not R6.0. Waiting on Track A, Terminals B/C/D/E or the capability probe **cannot close R6.0** — and treating them as R6.0 prerequisites would inflate the apparent distance to closure and invite the error of waiting on external lanes to freeze an architecture.

**The mission's requested sequence contains one structural error, corrected in §1.3.** It presents items 1–8 as a single linear chain. They are **two chains**: a five-node R6.0 subgraph and a downstream R6.1 chain that R6.0 does not depend on.

---

## 1. R6.0 closure dependency graph

### 1.1 The graph

> **Diagram interpretation (target path):** This diagram depicts the dependency path toward closure. `R6.0 CLOSED` is the target state after N9 / BL-22 is signed; it does not assert that R6.0 is currently closed. Current status remains `CONDITIONALLY READY — not closed`, consistent with the existing prose.

```
                        ┌─────────────────────────────────────────────┐
                        │  R6.0 CLOSURE SUBGRAPH                      │
                        │  (governance only — no code, no reviewer)   │
                        └─────────────────────────────────────────────┘

  ┌──────────┐   ┌──────────┐   ┌───────────────────────────┐
  │ N1       │   │ N2       │   │ N3                        │
  │ C-02     │──►│ C-02     │──►│ C-02 Reading B            │
  │ arithmetic│   │ recording│   │ PROPAGATED into           │
  │ 12 vs 13 │   │ locus    │   │ T13 §19.1 cond 3 + T16 §547│
  │ (G07-U2) │   │ (G07-U3) │   │                           │
  └──────────┘   └──────────┘   └───────────┬───────────────┘
                                            │
  ┌──────────┐                              │
  │ N4       │                              │
  │ ADR-2/C-1│──┐                           │
  │ package  │  │                           │
  │ name     │  │                           │
  │ recorded │  │                           │
  │ (RC-2)   │  │                           │
  └──────────┘  │                           │
                ▼                           │
  ┌──────────┐ ┌──────────┐                 │
  │ N5       │ │ N6       │                 │
  │ A3       │ │ B1       │                 │
  │ REGISTER │ │ REGISTER │                 │
  │ (RC-3)   │ │ w/ C-1   │                 │
  │          │ │ (RC-4)   │                 │
  └────┬─────┘ └────┬─────┘                 │
       │            │                       │
       │      ┌─────┴──────┐                │
       │      ▼            ▼                │
       │ ┌──────────┐ ┌──────────┐          │
       │ │ N7       │ │ N8       │          │
       │ │ A1,A2,A4 │ │ B2–B9    │          │
       │ │ REGISTER │ │ REGISTER │          │
       │ │ (RC-5)   │ │ (RC-6)   │          │
       │ └────┬─────┘ └────┬─────┘          │
       │      │            │                │
       │      └─────┬──────┘                │
       │            │                       │
       │            │        ┌──────────┐   │
       │            │        │ N10      │   │
       │            │        │ DURABILITY│  │
       │            │        │ corpus   │   │
       │            │        │ committed│  │
       │            │        │ (NEW)    │   │
       │            │        └────┬─────┘   │
       │            │             │         │
       └────────────┴─────────────┴─────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ N9  BL-22       │
                 │ SIGNED against  │
                 │ re-derived      │
                 │ baseline        │
                 │ (RC-8, RC-13)   │
                 └────────┬────────┘
                          │
                    ══════╧══════
                    R6.0 CLOSED
                    ═════════════

  ┌──────────────────────────────────────────────────────────────┐
  │  DOWNSTREAM CHAIN — does NOT gate R6.0                       │
  └──────────────────────────────────────────────────────────────┘

  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ M1       │──►│ M2       │──►│ M3       │
  │ D5       │   │ D4       │   │ BL-21    │
  │ T1–T8    │   │ Track A  │   │ Track A  │
  │ numbering│   │ engage   │   │ sign-off │
  │ canonical│   │ authorised│  │ T1–T8    │
  └──────────┘   └──────────┘   └────┬─────┘
                                     │
  ┌──────────┐   ┌──────────┐        │
  │ M4       │   │ M5       │        │
  │ D1,D3→D2 │   │ BL-23    │        │
  │ U0       │   │ R6/G7    │        │
  │ authorised│  │ GRANTED  │        │
  └────┬─────┘   └────┬─────┘        │
       │              │              │
       └──────────────┴──────────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ M6  R6.1 ENTRY  │
             │ 9 conditions    │
             │ (T11 §6)        │
             └─────────────────┘

```

### 1.2 Node definitions

| Node | Item | Type | Depends on | Evidence anchor |
|---|---|---|---|---|
| **N1** | C-02 arithmetic settled: 12 (brief) or 13 (register) | Owner act | — | G07-U2; supplement §8.1 |
| **N2** | C-02 recording locus defined — no register field exists | Owner act | — | G07-U3; supplement §8.7 |
| **N3** | C-02 Reading B propagated into T13 §19.1 cond 3 and T16 §547 | Documentation act | N1, N2 | G7 check 6, condition 3 |
| **N4** | `ADR-2/C-1` package name recorded as its own line | Owner act | — | RC-2; T15 §4.1 |
| **N5** | A3 registered (Option A, conditional, not implemented) | Owner act | — | RC-3; T16 A3 card |
| **N6** | B1 registered with the C-1 resolution | Owner act | N4 | RC-4; T16 B1 card |
| **N7** | A1, A2, A4 registered | Owner act | — | RC-5 |
| **N8** | B2–B9 registered (all eight) | Owner act | N6 | RC-6; Reading B |
| **N9** | **BL-22 signed** against a re-derived baseline | Owner act | N3, N5, N6, N7, N8, N10 | RC-8, RC-13 |
| **N10** | **Durability** — R6 corpus committed to version control | Owner act | — | CLOSE-FINAL-02 §2 |
| **M1** | D5 — T11 §15 T1–T8 numbering canonical | Owner act | — | T16 D5; X-3 |
| **M2** | D4 — Track A engagement authorised | Owner act | M1 | T16 D4; BL-21 |
| **M3** | BL-21 — Track A sign-off T1–T8 | External | M2 | T17 §6 |
| **M4** | D1, D3 → D2 — U0 authorised | Owner act | — | T16 D1–D3 |
| **M5** | BL-23 — `R6/G7` granted | Owner act | N9, M4 | T16 §10; T12 §18 |
| **M6** | R6.1 entry — all nine T11 §6 conditions | Composite | M3, M5, N6, N8, M4 | T17 §7 |

### 1.3 Corrections to the mission's requested sequence

The mission lists eight items as a single chain. Three corrections:

**Correction 1 — Track A does not gate R6.0.** The mission places "Track A engagement" at position 6, inside what reads as the R6.0 sequence. It is **M2/M3**, downstream of R6.0. R6.0 can and should close without any reviewer being contacted. CLOSE-FINAL-01 §10 states this explicitly: *"What the checklist deliberately excludes: `R6/G7`, Track A, Terminals B/C/D/E and the capability probe. They do not gate R6.0."*

**Correction 2 — A3 is independent, not sequential.** The mission places A3 registration at position 3, after C-02 and ADR-2/C-1. A3 has **no dependency on either**. T15 §3 records it: *"A3 and B1 are substantively independent of each other, though both gate R6.0."* A3 can be registered first, last, or in parallel. It is the **only** item that can advance R6.0 today without any other act.

**Correction 3 — "C-02 Reading B" is not a decision to be taken.** The mission lists it as item 1, as though the reading were open. It is **not**. The owner selected Reading B on 2026-11-04 (`ts=2026-11-04T16:25:06.624Z`, classed `EXACT OWNER`, supplement §4). What remains is **recording and propagation** — N1, N2, N3 — not selection. Re-opening the reading would be a regression, not progress.

**Corrected sequence:**

> **Diagram interpretation (target path):** This diagram depicts the dependency path toward closure. `R6.0 CLOSED` is the target state after N9 / BL-22 is signed; it does not assert that R6.0 is currently closed. Current status remains `CONDITIONALLY READY — not closed`, consistent with the existing prose.

```
R6.0:  N5 (A3)  ─┐
       N1 → N2 → N3 ─┤
       N4 → N6 → N8 ─┼──► N9 (BL-22) ──► R6.0 CLOSED
       N7 ──────────┤
       N10 ─────────┘

R6.1:  M1 → M2 → M3 ─┐
       M4 ───────────┼──► M5 (G7) ──► M6 (R6.1 entry)
       N9 ───────────┘
```

---

## 2. Gate-by-gate acceptance criteria

Each gate states what must be **observably true** for a third party to accept it, and what does **not** satisfy it.

### 2.1 Gate R6.0-C1 — Adopt ADR-1 (A3)

| Field | Content |
|---|---|
| **Requirement** | T13 §19.1 condition 1 |
| **Acceptance** | The T16 A3 card shows a recorded selection, not `PENDING`; the selection is `ADOPT Option A — conditional, explicitly not implemented`; the owner's acknowledgement that P1–P5 are unmet and that adopting builds nothing is recorded in the same act |
| **Does NOT satisfy** | Owner-selected-but-unregistered (current state); a report asserting the selection; a mission-framed inference |
| **Open defect** | A3's selection has **no direct owner utterance** (supplement §8.2, `UNRESOLVED`; G07-U6). Registration must either obtain one or record the limitation explicitly |
| **Current** | **NOT MET** — owner-selected only |

### 2.2 Gate R6.0-C2 — Adopt ADR-2 (B1) incl. `ADR-2/C-1`

| Field | Content |
|---|---|
| **Requirement** | T13 §19.1 condition 2 |
| **Acceptance** | A `C-1` row exists in the response sheet naming `request_transform/` or `compression/`; the T16 B1 card shows a recorded selection referencing that row; the owner's acceptance that I2 (250 ms / 2×) and I5 (schema) remain unspecified at adoption is recorded |
| **Does NOT satisfy** | B1 answered without C-1 recorded — that is either an unregistered 24th decision or a composite decision (`C-03`) |
| **Open defect** | `C-1` is **not among the 23 registered decisions** (T15 §4.1). Recording it as its own line is the only clean path |
| **Current** | **NOT MET** — `OUTSTANDING`; `C-1` unrecorded |

### 2.3 Gate R6.0-C3 — Record Group A + Group B, then sign BL-22

| Field | Content |
|---|---|
| **Requirement** | T13 §19.1 condition 3 |
| **Acceptance** | Under Reading B: **13** decisions registered (A1–A4, B1–B9); `C-02` settled and propagated; **BL-22 signed**, dated, scoped per the settled reading, against a baseline re-derived at the signature act |
| **Does NOT satisfy** | A signature before `C-02` is settled — that produces a signature of **ambiguous scope**, the exact failure `C-02` exists to prevent |
| **Current** | **NOT MET** — 0 registered; `C-02` open; unsigned |

### 2.4 Gate R6.0-D — Durability (new, not in CLOSE-FINAL-01)

| Field | Content |
|---|---|
| **Requirement** | CLOSE-FINAL-02 §2 — the entire R6 corpus is untracked |
| **Acceptance** | The R6 corpus is committed to version control, or the owner records an explicit, dated decision to sign against an untracked corpus with the risk accepted |
| **Does NOT satisfy** | A file existing on disk. **Recoverable ≠ durable.** The corpus survives a reboot; it does not survive `git clean`, a fresh clone, or a branch switch that discards untracked files |
| **Current** | **NOT MET** — 0 of the corpus tracked |

### 2.5 Gate M5 — `R6/G7` implementation authorisation (BL-23)

| Field | Content |
|---|---|
| **Requirement** | T11 §6 condition 1; T12 §18; T16 §10 |
| **Acceptance** | A written owner record granting `R6/G7`, **scoped**, explicitly naming `tests/` (D3), issued **after** BL-22 |
| **Does NOT satisfy** | A review report requesting it — *"cannot be requested by a review report"* (T12 §18; `r6-t9:417`; campaign `:332`). Silence. A Track A signature |
| **Current** | **NOT GRANTED** — never requested |

### 2.6 Gate M6 — R6.1 entry

| Field | Content |
|---|---|
| **Requirement** | All nine T11 §6 conditions |
| **Acceptance** | Each of the nine independently evidenced; none inferred from another |
| **Current** | **NOT READY** — 0 of 9 met (T17 §7) |

---

## 3. Owner action queue

Ordered by dependency. **Every item is an owner act. None is delegable to an implementer, a report, or a test.**

### 3.1 Tier 0 — can be done today, in any order, no prerequisites

| # | Action | Exact response form | Unblocks |
|---|---|---|---|
| **Q-1** | **Register A3** | `A3: ADOPT Option A — conditional, explicitly not implemented` | R6.0-C1 |
| **Q-2** | **Settle the 12/13 arithmetic** (G07-U2) | `C-02 count: 13 total / 10 outstanding` (or `12 / 9` with the register corrected to match) | N3, BL-22 scope |
| **Q-3** | **Define the C-02 recording locus** (G07-U3) | `C-02 recorded in: <named artefact + field>` | N3 |
| **Q-4** | **Record `ADR-2/C-1`** as its own line | `C-1 (package name): request_transform/` (or `compression/`) | N6 |
| **Q-5** | **Decide durability** (N10) | `Corpus: commit before BL-22` (or `sign against untracked, risk accepted`) | N9 |
| **Q-6** | **Authorise register governance** for `A`, `C` and `D` namespaces (G07-F3, G07-U5) | `Register governance: authorised for A/C/D` | Every further card |

**Q-1 is the single highest-value action available.** It is the only item that advances R6.0 without any other act, and it is the only one whose evidence gap (no direct owner utterance) is closed by the act of registering.

### 3.2 Tier 1 — the two ADRs

| # | Action | Exact response form | Depends on |
|---|---|---|---|
| **Q-7** | **Register B1** | `B1: ADOPT ADR-2 with C-1 = <name from Q-4>` | Q-4 |
| **Q-8** | **Register A1** | `A1: ADOPT §§8–15 as the frozen architecture` | — |
| **Q-9** | **Register A2** | `A2: Tier-1 metering fixes are integrity work` | — |
| **Q-10** | **Register A4** | `A4: ADOPT T10-1…T10-7 scoping` | — |

**A2 is the highest-consequence item in Group A.** Deferred, the confirmed defects ship as accepted billing error (T13 §7).

### 3.3 Tier 2 — Group B remainder (Reading B)

| # | Action | Note |
|---|---|---|
| **Q-11** | **B5** — settlement basis | **Must name both the budget and the quota governor** (C-07). Answering B5 without C-07 approves a contract whose scope does not match the code |
| **Q-12** | **B6** — monotone-shrink permanent | Separate from B7; must not be combined |
| **Q-13** | **B7** — per-attempt re-derivation forbidden | Separate from B6 |
| **Q-14** | **B2, B3, B4, B8, B9** | B2 scope · B3 bypass authority · B4 Phase-13 keep-out · B8 terminal marker · B9 reconciler placement |

### 3.4 Tier 3 — the signature

| # | Action | Precondition |
|---|---|---|
| **Q-15** | **Sign BL-22** | Q-1…Q-14 complete; `C-02` propagated (N3); baseline re-derived **at the signature act** (RC-13); durability decided (Q-5) |

**BL-22 is not a Group decision.** It is T13 §20 item 24, the signature act. It is correctly excluded from the 23.

### 3.5 Tier 4 — downstream, after R6.0 closes

| # | Action | Note |
|---|---|---|
| **Q-16** | **D5** — adopt T11 §15 T1–T8 numbering | Must precede D4 (X-3) |
| **Q-17** | **D4** — authorise Track A engagement | After D5 |
| **Q-18** | **D1, D3 → D2** — U0 authorisation | Independent of R6.0; can be done at any point |
| **Q-19** | **BL-23 / `R6/G7`** | After BL-22 and D3 |
| **Q-20** | **D6, C1–C4** | Release-scope, not R6.0/R6.1 |

---

## 4. External reviewer requirements

**All `NOT OBTAINED`. No reviewer was contacted. No prompt was sent. Silence is not approval.**

### 4.1 What gates what

| Reviewer lane | Artefact | Gates | Does **not** gate |
|---|---|---|---|
| **Track A** — external review | T1–T8 sign-off | **R6.1** | R6.0 |
| **Terminal B** — architecture review | Record | Release (G5) | R6.0, R6.1 |
| **Terminal C** — security/reliability | Record | Release (G5) | R6.0 |
| **Terminal D** — benchmark | Corpus + comparability keys | Release (G4, BL-19) | R6.0 |
| **Terminal E** — red-team | Attestation | Scorecard | R6.0 |
| **Capability probe** | `tool_use` / `structured_output` extension | Release (C4, BL-10) | R6.0 |

**R6.0 requires zero external signatures.** This is the single most important scheduling fact in this document.

### 4.2 Track A — the only reviewer that gates R6.1

**Preconditions to issuance — three, none met:**

| # | Precondition | State | Why it gates |
|---|---|---|---|
| 1 | **D5** — T1–T8 numbering canonical | `OUTSTANDING` | Under campaign §15's T1–T7, `T7` denotes two different changes and T8 has no row. A packet issued while numbering is unresolved can secure approval of the **wrong artefact** (X-3) |
| 2 | **D4** — engagement authorised | `OUTSTANDING` | Without D4 nothing is authorised to be sent |
| 3 | **Packet path hygiene** | **Two defects** | A packet naming a non-existent path invites rejection on its face |

**Path defects — VERIFIED at HEAD this session:**

| T# | Path as printed | Actual | Verdict |
|---|---|---|---|
| T4 | `config/validation.py` | `src/sabiroute/config/validation.py` | **DEFECT** — corrected path required |
| T1 (I1/I4 citation) | `src/sabiroute/dataset.py` | `src/sabiroute/intelligence/dataset.py` | **DEFECT** — corrected path required |

**Insertion-point defect — VERIFIED at HEAD this session:**

I9's Owner cell names the guard window `:1309–:1345`. `attempted: list[str] = []` is bound at **`:1311`** — *inside* that window. `finish()` reads `attempted` at **`:602`**. A guard beginning at `:1309` begins **two lines before `attempted` exists**; any `finish()` reached from inside that window raises `NameError`, is caught at handler level, and surfaces as a masked 503 with the reservation still held.

**Correction to record (a straight fix, not an option):** I9's Owner cell must read `Call-site guard: strictly after :1311 and before :1345`.

**Acceptance form.** A signature satisfies BL-21 for its item only when it is **written**, **names the T# and the numbered change**, and is **scoped to that item** — item, surface, basis, scope (R6.1 / R6.7), conditions. **Deferral is a valid answer and is not approval.** An unanswered request is neither.

**What Track A does not approve:** the R6.0 freeze (owner, BL-22), G7 (owner, BL-23), the foundation contract draft (owner, B1), settlement policy (owner, B5), scope/bypass/keep-out (owner, B2/B3/B4). **Track A approval of a change does not imply the change is authorised to be made.**

### 4.3 Reviewer-assignment defect to resolve before any packet issues

**G07-F4.** Terminal B's packet (T13 §15) asks B to adjudicate R6.1 settlement invariants. The ownership map (`r6-architecture-decision-pack.md:485`) excludes B from R6.1 and assigns R6.1 to Terminal C. Under the pack's own conflict controls, a B finding on settlement would reopen a decision in C's lane and in Track A's protected surface, with no rule saying who owns the result.

**This does not gate R6.0.** It gates the Terminal B packet, which gates Release. Resolve before issuing B.

---

## 5. Technical prerequisites

These are **not decisions**. They are facts about the tree that must be corrected or specified before the artefacts that depend on them are signed. None changes a decision, an option, a gate or a count.

### 5.1 Corrections — statements of fact, no owner decision required

| # | Defect | Correction | Blocks |
|---|---|---|---|
| **TP-1** | I9 guard window `:1309–:1345` spans the `attempted` binding at `:1311` | Re-pin to `strictly after :1311 and before :1345` | T1 signature |
| **TP-2** | T4 names `config/validation.py` — does not exist | `src/sabiroute/config/validation.py` | T4 signature |
| **TP-3** | I1/I4 cite `src/sabiroute/dataset.py` — does not exist | `src/sabiroute/intelligence/dataset.py` | T1 signature |
| **TP-4** | `tests/test_r6_settlement_integrity.py:11` asserts tests are "written against the **approved** contract" while B5 is `NOT APPROVED` | Correct the header wording and the failing-set count | Nothing — but it asserts an approval that does not exist (G07-F1) |
| **TP-5** | `prep-03` decision table diverges from the canonical register | Correct or supersede | RC-12 |

### 5.2 Specifications — owner sub-questions inside B1

**I2 — Canonical representation.** Four cells are mutually unsatisfiable as written: *output ≤ input* vs *2× bytes*; *deadline only* vs *250 ms*. Three independent sub-questions:

| Sub-question | Options | Recommended |
|---|---|---|
| **I2-a** — what does "2× bytes" bound? | A: peak working-set (output stays ≤ input) · B: output-size budget (≤ 2× input) · C: drop "2×" | **A** |
| **I2-b** — 250 ms vs deadline-only | A: hard cap independent of deadline · B: `min(250 ms, remaining)` · C: deadline only | **A** |
| **I2-c** — the 250 ms is a synchronous event-loop stall | A: keep sync, reduce cap to tens of ms · B: move to `to_thread` (pulls T5 into R6.1) · C: accept the stall | **A** |

**I2-c is the item most likely to be missed in review.** A pure synchronous function has no await point, so `asyncio` cannot deliver `CancelledError` mid-computation. "250 ms" is not a timeout in any runtime sense — it is a policy number enforceable only by capping input size or checking elapsed time at checkpoints.

**I5 — Optimization policy.** Four sub-questions:

| Sub-question | Issue | Recommended |
|---|---|---|
| **I5-a** — `strategy` with no registry | Closed enum with exactly one admissible value | **A** |
| **I5-b** — `max_ratio` direction | Retention semantics (output ≥ 80%) vs shrinkage semantics (shrink ≤ 80%) — **opposite behaviour on the same value** | **Retention**, renamed `min_retention_ratio` |
| **I5-c** — freeze rationale misattributed | The stated reason (reservation splitting) is **false** — the reservation is computed from the original estimate and never consults the policy. The real reasons are I3 identity, B7, I4 record integrity | **Restate the reason** |
| **I5-d** — I5 is a Track A surface | I5's Owner cell is the config layer = `src/sabiroute/config/validation.py` = **T4**, not T1 | **Confirm T4 coupling** |

**I5-d is a sequencing fact, not a scoping opinion.** The I5 schema cannot be *written* without landing in a Track A protected file. I5 sits behind BL-21 on row **T4**, not T1.

### 5.3 Durability

**TP-6.** The entire R6 corpus — T9 through T17, the ADR pack, the decision pack, the prep documents, the supplement, the worksheet, the BM25 record, the amendment proposal, CLOSE-FINAL-01 and CLOSE-FINAL-02 — is **untracked**. `git ls-files docs | grep -c r6` returns **0** (VERIFIED BY RUNTIME this session).

**A closure signed against an untracked corpus is a closure whose own evidence is not preserved.** Durability should be established **before** BL-22 is signed, not after. This is a new prerequisite and it is not in CLOSE-FINAL-01's checklist.

### 5.4 What is *not* a technical prerequisite

| Item | Why not |
|---|---|
| `request_transform/` package | Does not exist (VERIFIED). Its absence is **correct** — B1 authorises no code |
| `sabiroute_optimization_records` table | Does not exist. Its absence is **correct** — A3 freezes a target and builds nothing |
| Settlement remediation | R6.1 work, behind G7 and Track A |
| U0 test artefact | Unauthorised evidence; D1/D2/D3 outstanding |

---

## 6. Final closure checklist

Extends CLOSE-FINAL-01 §10 with the durability prerequisite. **Every row is `UNMET`.** No row may be marked met by this document, by a plan, or by the existence of a prepared decision.

| # | Requirement | How a third party verifies independently | Current |
|---|---|---|---|
| **RC-1** | `C-02` reading chosen and recorded | Locate the recorded reading; confirm §19.1 condition 3 matches it | **UNMET** |
| **RC-2** | `ADR-2/C-1` package name recorded as its own line | Read response sheet; confirm a `C-1` row exists with a recorded name | **UNMET** |
| **RC-3** | **A3** registered | T16 A3 card shows the selection, not `PENDING` | **UNMET** — owner-selected only |
| **RC-4** | **B1** registered with `ADR-2/C-1` resolution | T16 B1 card shows the selection | **UNMET** |
| **RC-5** | **A1, A2, A4** registered | T16 cards A1/A2/A4 show selections | **UNMET** |
| **RC-6** | **Reading B:** **B2–B9** registered (all eight) | T16 cards B2–B9 show selections | **UNMET** — *not required under Reading A* |
| **RC-7** | Decision condition satisfied at the chosen scope | Count registered rows: **13** (Reading B) or **5** (Reading A) | **0 registered** |
| **RC-8** | **BL-22** signed | Locate the signed written approval, dated, scope per RC-1 | **UNMET** |
| **RC-9** | Each decision marked approved **only** by an owner record | Grep for approval basis; silence must not read as approval | **UNMET** |
| **RC-10** | No decision marked approved by a report, plan or test | Audit trail: every change cites an owner record | **HOLDS** |
| **RC-11** | `CLAUDE.md` §12 corrected *if* separately authorised | Diff the section | **UNMET** — not authorised |
| **RC-12** | `prep-03` decision table corrected or superseded | Compare to the canonical register | **UNMET** |
| **RC-13** | Baseline re-derived **at the closure act** | Confirm HEAD/branch recorded at the signature | **UNMET** — re-derivable; act not performed |
| **RC-14** | **Durability** — corpus committed, or risk accepted in writing | `git ls-files docs \| grep r6` non-empty, or a dated owner record | **UNMET** — 0 tracked |
| **RC-15** | **C-02 arithmetic settled** (12 vs 13) | The recorded count matches the register's enumeration | **UNMET** — G07-U2 |
| **RC-16** | **C-02 recording locus defined** | A named artefact and field exist for a governance reading | **UNMET** — G07-U3 |

**RC-13 is not cosmetic.** A closure signed against an unverified baseline is a closure of an unknown commit. **The signature act must re-anchor first.**

**What the checklist deliberately excludes:** `R6/G7`, Track A, Terminals B/C/D/E and the capability probe. **They do not gate R6.0.**

---

## 7. Explicit NO-GO conditions

**R6.0 is NO-GO if any of the following is true. All are true today.**

### 7.1 Absolute NO-GO — a signature under any of these is illegitimate

| # | Condition | State |
|---|---|---|
| **NG-1** | `C-02` is not settled | **TRUE** — both readings formally live in the artefacts |
| **NG-2** | `ADR-2/C-1` is not recorded as its own line | **TRUE** — unrecorded |
| **NG-3** | Fewer than 13 decisions registered under Reading B | **TRUE** — 0 registered |
| **NG-4** | Any decision marked approved by a report, plan, test or inference | **FALSE** — RC-10 holds |
| **NG-5** | The baseline is not re-derived at the signature act | **TRUE** — act not performed |
| **NG-6** | The corpus is untracked and no written risk acceptance exists | **TRUE** — 0 tracked |
| **NG-7** | The 12/13 arithmetic is unresolved | **TRUE** — G07-U2 |

### 7.2 Structural NO-GO — a signature under any of these is meaningless

| # | Condition | Why it voids the act |
|---|---|---|
| **NG-8** | BL-22 signed **before** `C-02` is settled | Produces a signature of **ambiguous scope** — the exact failure `C-02` exists to prevent |
| **NG-9** | B1 answered without `C-1` recorded | Either an unregistered 24th decision or a composite decision (`C-03`) |
| **NG-10** | B5 answered without C-07 | Approves a contract whose scope does not match the code — one governor repaired, the other not |
| **NG-11** | A3 registered on a mission-framed inference with no owner utterance and no recorded limitation | Registers a decision the owner may not have made |
| **NG-12** | Any decision registered by an implementer, a report, or a test | The register's authority is the owner's alone |

### 7.3 Conflation NO-GO — the error this document exists to prevent

| # | Condition | Why it is wrong |
|---|---|---|
| **NG-13** | R6.0 declared closed because Track A signed | Track A gates R6.1, not R6.0 |
| **NG-14** | R6.0 declared closed because `R6/G7` was granted | G7 is downstream of BL-22, not a substitute for it |
| **NG-15** | R6.1 declared authorised because R6.0 closed | R6.0 closure is R6.1 **condition 1, part one**. Eight further conditions remain |
| **NG-16** | A prepared amendment, packet, brief or card counted as progress toward registration | *"A prepared decision is not a taken decision. Ready ≠ authorised."* (T13 §19.2) |
| **NG-17** | Silence from a reviewer read as approval | *"Silence is not approval."* |

### 7.4 What flips the verdict

**GO becomes legitimate when, in this order:**

1. `C-02` arithmetic settled (NG-7 cleared)
2. `C-02` recording locus defined (RC-16)
3. `C-02` Reading B propagated into T13 §19.1 cond 3 and T16 §547 (RC-1)
4. `ADR-2/C-1` recorded as its own line (RC-2)
5. A3 registered (RC-3)
6. B1 registered with C-1 (RC-4)
7. A1, A2, A4 registered (RC-5)
8. B2–B9 registered (RC-6)
9. Durability established or risk accepted (RC-14)
10. Baseline re-derived **at the signature act** (RC-13)
11. **BL-22 signed** (RC-8)

**Steps 1–2 and 5 are independent of each other and of everything else.** Steps 3–4 and 6–8 are independent of each other. Only step 11 is strictly last.

---

## 8. Honest position

| Field | Value |
|---|---|
| **Baseline** | Re-derived — `feat/sabiroute-routing-foundation` @ `319a711`, ahead 6 / behind 3 |
| **Tracked modifications** | **0** |
| **R6 documents tracked in Git** | **0 of the entire corpus** |
| **Decision package** | Complete and canonical — **23 decisions, 0 registered** |
| **Owner-selected** | **1** (A3, conditional, P1–P5 unmet) — **unregistered** |
| **R6.0 closure** | **~29% — unchanged** |
| **R6.0** | **CONDITIONALLY READY — not closed, not frozen, not signed** |
| **`R6/G7`** | **NOT GRANTED** |
| **Track A / Terminals B–E** | **`NOT OBTAINED`** |
| **Verdict** | **NO-GO** |
| **Next action** | **Belongs to CHEF_P** — Q-1 (register A3) is the only item that advances R6.0 today without any other act |

**The remaining ~71% is almost entirely owner-time, not engineering-time.** R6.0's three conditions are *adopt, adopt, record-then-sign*. Two are decision registrations and one is a signature. **None requires code.**

---

## 9. Safety boundary — what this document did not do

| Prohibition | Status |
|---|---|
| Sign, amend, or declare closure | **Not done** |
| Register, approve or select any decision | **Not done** — all 23 remain `OUTSTANDING` |
| Adopt ADR-1 or ADR-2 | **Not done** — both remain `PROPOSED` |
| Resolve `C-02` or `ADR-2/C-1` | **Not done** — both remain open |
| Grant or request `R6/G7` | **Not done** |
| Contact a reviewer or issue a Track A request | **Not done** |
| Implement R6.1–R6.7 | **Not done** |
| Change production code | **Not done** — zero writes outside this document |
| Execute tests, provider calls, migrations, deployments | **Not done** |
| Commit, stage, reset, clean, rebase, push | **Not done** — only read-only Git commands were run |
| Amend a shared register or protected document | **Not done** — T12–T17 unmodified |
| Invent an owner decision, approval, signature, test result, threshold or gate acceptance | **Not done** |
| Assume current HEAD / branch / worktree | **Not done** — re-derived and reported (§0) |

**Commands executed, in full:** `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git rev-list --left-right --count HEAD...origin/feat/sabiroute-routing-foundation`, `git status --porcelain --untracked-files=no | wc -l`, `git ls-files docs | grep -c r6`, `sed -n '602p;1311p;1345p' src/sabiroute/api/completions.py`, `ls -1 src/sabiroute/config/validation.py src/sabiroute/intelligence/dataset.py`, `ls -d src/sabiroute/request_transform`, plus read-only `grep`/`sed` reads against the R6 corpus. **All read-only. Nothing was written by any of them.**

---

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
