# R6.0 — WP-2 FINAL OWNER DECISION PACK

**Actor:** Claude Code Desktop (coordinator — **not** the independent verifier)
**Date:** 2026-11-10
**Scope:** WP-2 reconciliation of F1–F7, the D-identifier register, N2/N3, and U2 refresh authority
**Status:** Pack complete · **WP-2 remains BLOCKED** pending §6
**Supersedes:** `artifacts/r6-closure/wp2-consolidated-decision-pack-2026-11-10.md` (retained as the historical record; three of its positions are corrected here — see §2)

> This pack **reverses or retracts three of its predecessor's positions** on the strength of source
> evidence gathered in this pass. Where the earlier pack is now wrong, that is stated explicitly
> rather than quietly overwritten. The directive's own rule applies to this document too: a finding is
> not preserved because it appeared in an earlier report.

---

## 0. Coordination reality — the evidence limitation, stated first

**There is no Claude Code Terminal return. None exists in this workspace.**

Verified this pass, not assumed:

| Check | Result |
|---|---|
| `list_sessions(linked=true)` | No linked sessions |
| Peer sessions listed | 3, all idle, none a Terminal actor for R6.0 |
| `artifacts/` contents | `compression-preflight`, `r6-closure`, `sprint13-429-drill`, `sprint13-policy-experiment`, `sprint13-proxy-drill`, `sprint15-sync-db-p1.md`, `t8-compression-gate` — **no Terminal report** |
| `artifacts/r6-closure/` contents | 2 files, both Desktop-authored |
| Any Terminal hash, transcript or artefact | **None** |

The directive refers to "the latest Terminal return". **No such return reached this session.** The
F1–F7 findings arrived as *text inside the owner directive* and nowhere else.

Per directive Part 5, this is recorded as an explicit handoff limitation and **not** papered over:

> **Terminal's position is recorded as `UNRECEIVED` for all eight findings.**
> No claim of session communication is made, because none occurred.

This does not weaken the adjudication below. Each finding is tested against the repository directly,
and the repository is the authority the directive names. It does mean **WP-2 has only ever had one
actor**, and that actor is also the one proposing the corrections. That is precisely the condition
WP-4 exists to catch.

**Terminal handoff requirement (for the next Terminal actor):** a return is admissible only if it
supplies, per finding, (a) file path, (b) line range, (c) verbatim quoted text, and (d) the digest of
the file as read. A return without (d) cannot be reconciled against a moving tree.

---

## 1. F1–F7 and the missing-test finding — final adjudication

Legend for **Normative source**: the instrument that governs on the point, applying the authority
hierarchy in §0 of the predecessor pack. **Supported reading** names which interpretation the source
actually sustains.

### 1.1 Summary table

| # | Finding | Terminal | Desktop | Supported reading | Final status | Owner decision |
|---|---|---|---|---|---|---|
| F1 | HTML-comment VER vs JSONL VER | `UNRECEIVED` | Real conflict; **already owner-resolved** | O5 (2026-11-07) | **UPHELD** as unapplied correction backlog — not an open contradiction | **WP2-D2** |
| F2 | No consolidated normative VER table | `UNRECEIVED` | Holds | 03B-R1 §6 vs `PARAM-A.7` | **UPHELD** | **WP2-D2** |
| F3 | Nine genesis fields not enumerated | `UNRECEIVED` | **Rejected** | Decision pack §3.2; `PARAM-B.5`; O4 | **REJECTED** — locality defect only | none (A) |
| F4 | O1–O5 registration locus undefined | `UNRECEIVED` | Structurally true, **false blocker** | `PARAM-A.6`; namespace rule `:95-100` | **RECLASSIFIED** — no REG required | **WP2-D3** |
| F5 | Stale proposal status banners | `UNRECEIVED` | Holds | Correction proposal `:3`; §2 table | **UPHELD** | **WP2-D12** |
| F6 | `entry_type` cannot represent REG | `UNRECEIVED` | **Rejected** — false premise | `PARAM-A.1`/`A.2`; O5 | **REJECTED** | none (A) |
| F7 | `items_checked` has no bound | `UNRECEIVED` | Holds | 03B-R1 §6 `:128` vs §7 `:137-169` | **UPHELD** — live integrity hole | **WP2-D11** |
| Tests | No VER/REG/conformance tests | `UNRECEIVED` | Holds | Test `:171-175` | **UPHELD** | **WP2-D9** |

**Score: 5 upheld (F1, F2, F5, F7, tests) · 2 rejected (F3, F6) · 1 reclassified (F4).**

### 1.2 Per-finding reconciliation

#### F1 — HTML-comment VER vs JSONL VER → **UPHELD, but not as an open contradiction**

- **03B-R1 §6** (`:110-118`): *"Verification is a separate structured comment:"* followed by a fenced
  `<!-- VER:v1 decision=… verifier=… verified=… result=… marker_sha256=… items_checked=… -->` block.
- **`PARAM-A.2`** (`:122-126`): VER records *"live in a distinct append-only verification ledger"*,
  *"never co-located with the REG record they verify."*
- **`PARAM-A.7`** (`:154-156`): that ledger is *"append-only JSONL: one canonical JSON object per
  line."*
- **O5** (decision pack `:29`): *"The append-only JSONL VER ledger is authoritative… The HTML-comment
  VER representation in 03B-R1 §6 must not be treated as an alternative authoritative ledger format."*

A sharper defect the finding did not name: a comment adjacent to T16 is **co-located** with the REG
marker, which `PARAM-A.2` forbids outright. So the HTML-comment container is not merely an
alternative format — it is architecturally prohibited.

**Supported reading:** O5. The container conflict was decided 2026-11-07. What remains is that the
**edits were never applied**, so the normative text still contradicts the decision. The correction set
already exists in full at decision pack §4.5 (`:446-454`), five passages, **verbatim**.

**Final status: UPHELD** — as an unapplied correction backlog, not as a live contradiction.
Re-opening the decision would violate the directive's Part 6. **Owner decision: WP2-D2** (approve the
edits, not the decision).

#### F2 — No consolidated normative VER field table → **UPHELD**

- **03B-R1 §6** carries a **six-field comment grammar** (`:119-126`).
- **`PARAM-A.7`** carries `seq`, `prev`, `entry_sha256` and the genesis/checkpoint rules.
- **Nowhere** does an approved document carry one table for the 12-key VER entry.

The correction already *contemplates* the table — decision pack §4.5 correction #2 (`:451`) says
*"replace with the S3 JSONL field table; retain the six field names"* — but the current text has no
such table, and the S3 table itself lives in the **non-approved** proposal §3.3. F2 holds.

**Final status: UPHELD.** **Owner decision: WP2-D2** (the sixth correction).

#### F3 — Nine genesis fields "not explicitly enumerated" → **REJECTED**

The nine fields are enumerated explicitly and numerically at decision pack **§3.2 `:244-256`**, rows
`#1`–`#9`, including `t16_sha256` as field 9. They are enumerated a second time at proposal §3.2
(`:256-265`). `PARAM-B.5` adopts *"the nine-field set defined by proposal §3.2's field table."* The set
is pinned by a **508-byte normative worked example** (`ad1484b0…caf28`).

**Supported reading: Desktop's rejection stands.** The defect is **locality** — the enumeration is
incorporated by reference, so a reader holding only the addendum cannot see it. That is a documentation
defect, not a missing schema. **No schema change is warranted, and proposing one would have rewritten a
schema that is already correct.**

**Final status: REJECTED.** Optional locality fix (inline the table into the addendum) is authorised
only as part of **WP2-D8**'s single pass, because it moves `addendum_sha256`. It is never a separate
edit. **Owner decision: none for the schema.** The optional inline is a sub-option of D8.

#### F4 — O1–O5 registration locus → **RECLASSIFIED, blocker dissolved**

- **`PARAM-A.1`** (`:116-120`): REG is written *"adjacent to the canonical T16 register entry it
  registers."*
- **`PARAM-A.6`** (`:147-152`): *"The canonical IDs remain exactly `A1`–`A4`, `B1`–`B9`, `C1`–`C4`,
  `D1`–`D6` (23 total)."*
- **Namespace rule** (`:95-100`): *"Parameters in this addendum are identified `PARAM-A` … `PARAM-G`.
  These identifiers exist **only** in this document. They are not decision cards, are not members of
  any decision-register family…"*

O1–O5 are **absent from the 23-card register** and absent from the Reading-B registration inventory of
13 (A1–A4, B1–B9). Each maps onto an approved parameter, not a decision card:

| Owner selection | Parameter it produced |
|---|---|
| O1 | `PARAM-B.6` (`marker_sha256`, U4) |
| O3 | `PARAM-B.1` (multi-line owner-response rule) |
| O4 | `PARAM-B.5` (canonical JSON, genesis) |
| O5 | `PARAM-A.7` (JSONL ledger authority) |

The namespace rule supplies the decisive sentence: parameters *"are not decision cards"* and *"must not
be written as `D1`–`D7`."* O1–O5 produced parameters. **O1–O5 therefore require no REG locus, and the
blocker recorded at `wp0-wp1-evidence-2026-11-09.md §4` is malformed.**

**Supported reading: Desktop's reclassification.** Note the epistemic discipline: this *dissolves* a
recorded blocker, which is a governance act, so it is raised as a decision (**WP2-D3**) and not
asserted as a finding.

**Final status: RECLASSIFIED.** **Owner decision: WP2-D3** — genuinely new, though strongly supported.
**If rejected**, a new locus must be defined and the 23-card namespace rule revisited: an architecture
change that halts WP-2 (CLAUDE.md §5).

#### F5 — Stale proposal status descriptions → **UPHELD**

- Correction proposal `:3`: *"PROPOSAL — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED."*
- Since 2026-11-07 the owner has recorded **O3, O4, O5**, and decision pack §0.3 (`:64-67`) states
  those safeguards are *"carried into the canonical corrections proposal."*

The banner is stale on the O3/O4/O5 points. WP-1's **F-WP1-2** reached the same place independently,
and **F-WP1-3** adds a second staleness: the proposal's §2 source table records the protocol at **349**
lines and the addendum at **499**; live values are **348** and **646**.

**Final status: UPHELD.** **Owner decision: WP2-D12** (documentary).

#### F6 — `entry_type` cannot represent REG → **REJECTED, false premise**

`entry_type ∈ {"GENESIS","VER"}`. REG is **deliberately not a ledger entry**: `PARAM-A.1` places it as
a marker adjacent to T16, and O5 confirms *"REG remains adjacent to the relevant T16 decision card…
VER entries reside in the separate append-only JSONL ledger."* Adding a `REG` member would place the
two families in one container — **violating `PARAM-A.2` and O5 simultaneously.**

The legitimate residue is documentary: REG and VER use different encodings (HTML-comment marker vs JSONL
line). That asymmetry is **intentional and nowhere stated as intentional.** Fix is one rationale note,
not a schema change.

**Final status: REJECTED.** Note rides **WP2-D2**. **Owner decision: none for the schema.**

#### F7 — `items_checked` bound → **UPHELD. The only live integrity hole.**

- **03B-R1 §6** (`:115-128`) declares the field and restricts `result` to `PASS|FAIL`. It states **no
  bound** on `items_checked`.
- **03B-R1 §7** (`:137-169`) fixes the inventory at **ten** items.
- **`PARAM-A.4`** (`:134-139`): COMPLETE *"is valid only when a matching `VER:v1` record has
  `result=PASS`."*

**Failure scenario (static analysis):** an entry with `result="PASS"` and `items_checked=3` satisfies
**every rule currently stated**, and makes a registration `COMPLETE` under `PARAM-A.4` while seven of
the ten inventory items were never checked. No rule forbids it. Nothing detects it.

This is the **only** finding that is unfixed **and** unblocked by policy. **Owner decision: WP2-D11.**

#### Missing tests → **UPHELD**

`tests/test_r6_registration_digest_conformance.py` `:171-175` holds the U2 vector table. The module does
**not**: validate a VER entry against any schema; assert REG/VER separation; test `COMPLETE` without a
matching `PASS` VER; test the F7 bound. **Owner decision: WP2-D9.**

---

## 2. Corrections to the predecessor pack

The predecessor pack is retained. These positions in it are **withdrawn or reversed** here.

### F-WP2-1 — the "auditability paradox" is **WITHDRAWN**

The predecessor pack claimed R6.0-D orders corrections *before* tracking and called this a paradox,
raising **D10** to choose between reordering and accepting a byte-level record.

**That was wrong on the evidence.** R6.0-D (`:30`, `:82-90`) already binds the ordering **and** already
addresses the gap:

> *"Tracking is a repository act under separate authority; this decision records the requirement and
> does not itself authorise the commit."*

and the binding sequence is explicit: *(1) apply canonical corrections → (2) track the corpus →
(3) re-derive U2 → (4) build genesis → (5) register.*

The owner has therefore **already decided** this. Offering to "swap steps 1 and 2" would have
re-litigated a settled decision — the exact failure the directive's Part 6 forbids, and one this pack
committed against. **D10 is withdrawn as a decision.** The residual point is a limitation, not a
question: edits made while untracked produce no `git diff`, and the audit mechanism is the **U2 digest
binding**, not git history. Git-level audit arrives at R6.0-D step 2.

### F-WP2-5 — Directive Part 3 mis-addresses **N2/N3**

Repository **N2** and **N3** are **not** repository-provenance nodes. See §4.

### F-WP2-6 — WP-2's own identifiers violate the addendum namespace rule

The predecessor pack used bare `D1`–`D12`. The addendum namespace rule (`:95-100`) states parameters
*"must not be written as `D1`–`D7` or as a bare `C-1`"*, and WP-1's **F-WP1-5** already recorded a
three-way D-collision (correction-proposal D1–D4, T16 D1–D6, build-map D1–D7). Bare `D1`–`D12` adds a
**fourth** colliding register.

**All identifiers in this pack are therefore `WP2-D<n>`.** See §3.

### Retained from the predecessor (§ unchanged)

F-WP2-2 (`PARAM-A.4` survives O5 only by field-name preservation — the D2 set must be tested against
`PARAM-A.4`, not only the schema); F-WP2-3 (digest values reported, not re-measured **by the Bash
classifier in that session**); F-WP2-4 (two colliding `C-` series: `close-final-07 C-n` vs
`O3/O4/O5-pack C-n`, plus `correction-proposal C-1…C-7` and `T16 C1–C4` — register-qualify everything).

---

## 3. The D-identifier count — resolved

The owner is correct that the predecessor pack was internally inconsistent. Three separate defects:

**Defect 1 — arithmetic.** The summary said *"ten decisions, eight confirmations and three genuine
decisions."* 8 + 3 = 11 ≠ 10, and the parenthetical list contained **seven** confirmations, not eight.
That sentence was wrong. Corrected below.

**Defect 2 — the §8 table listed 10 of 12 rows.** It dropped **D4** and **D5** without saying why.
Explanation now explicit:
- **D4** (REG/VER separation, `entry_type`) is **not a question.** Its recommendation is *"reject F6;
  no schema change."* Answering it would be answering "do nothing." Its one live element is a
  documentary rationale note that rides **WP2-D2**. → **subsumed, no owner answer.**
- **D5** (nine-field genesis) is **already decided by O4.** Only the *optional* inline-table locality
  fix remains, and it is gated by **WP2-D8** because it moves `addendum_sha256`. → **confirmation
  only, no separate approval.**

**Defect 3 — register collision.** See F-WP2-6.

### 3.1 Resolution

**12 identifiers exist. 10 require an owner answer. 2 require none.**

| Class | Count | IDs |
|---|---:|---|
| **A** — Already approved, confirmation only | 4 | WP2-D1, WP2-D5, WP2-D7, WP2-D8 |
| **B** — Documentary correction | 1 | WP2-D12 |
| **C** — Genuine owner decision | 5 | WP2-D2, WP2-D3, WP2-D6, WP2-D9, WP2-D11 |
| **No answer required** | 2 | WP2-D4 (subsumed by D2) · WP2-D10 (**withdrawn**, F-WP2-1) |

**4 + 1 + 5 = 10 answerable.** The predecessor's "eight confirmations / three genuine" is superseded:
the true split is **four confirmations, five genuine, one documentary, two non-questions.**

---

## 4. N2 and N3 — resolved, and the directive's addressing corrected

### 4.1 What the repository actually means by N2 and N3

`docs/r6-fast-04-r6.0-closure-architecture.md §1.2` (`:150-167`) defines the closure node graph:

| Node | Item | Type | Depends on | Anchor |
|---|---|---|---|---|
| **N1** | C-02 arithmetic settled: 12 (brief) or 13 (register) | Owner act | — | G07-U2; supplement §8.1 |
| **N2** | **C-02 recording locus defined — no register field exists** | Owner act | — | G07-U3; supplement §8.7 |
| **N3** | **C-02 Reading B propagated into T13 §19.1 cond 3 and T16 §547** | Documentation act | N1, N2 | G7 check 6, condition 3 |
| **N10** | **Durability — R6 corpus committed to version control** | Owner act | — | CLOSE-FINAL-02 §2 |

Correction 3 (`:177`) is explicit: *"the owner selected Reading B on 2026-11-04… What remains is
**recording and propagation** — N1, N2, N3 — not selection."*

### 4.2 The mismatch — recorded, not silently corrected

Directive Part 3 asks to *"resolve N2 and N3"* and then lists four **repository-provenance** items
(untracked corpus, untracked conformance test, baseline mismatch, security branch).

**Those four items are not N2 or N3.** They belong to **N10 (Durability)** plus two findings
(F-WP1-4 baseline mismatch) and one lane boundary (security remediation). N2/N3 are **C-02 governance
acts**, unrelated to git provenance. Treating them as synonyms would merge a governance node with a
repository operation.

To avoid a *third* collision, the four provenance items are registered here as **P1–P4**, and N2/N3
remain untouched as C-02 acts requiring the owner's separate attention.

### 4.3 Repository-provenance plan — P1–P4

**P1 — Untracked R6.0 document corpus.** VERIFIED BY RUNTIME this pass:

```
$ git status --porcelain docs/r6-registration-protocol-03b-r1.md \
    docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md \
    docs/r6-t16-r6-decision-option-register.md
?? docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md
?? docs/r6-registration-protocol-03b-r1.md
?? docs/r6-t16-r6-decision-option-register.md
```

**All three U2-bound files are untracked.** `docs/r6-*.md` count = **42** (matches WP-0 baseline and
build map §1.1). Consequence: a `git clean`, fresh clone, or discard-on-branch-switch **destroys the
files the U2 digests bind**. This is R6.0-D's stated rationale, verified.

**P2 — Untracked conformance test.**

```
$ git status --porcelain tests/test_r6_registration_digest_conformance.py
?? tests/test_r6_registration_digest_conformance.py
```

Confirmed untracked. This is the file WP-1 edited (§5). Consequence for audit: when it is eventually
tracked, its **first commit will contain the already-refreshed vector**. Git history will never show the
pre-refresh value. The byte-level record at `wp0-wp1-evidence-2026-11-09.md §2.3` is the **only**
record of the change.

**P3 — Declared vs live baseline mismatch.** VERIFIED BY RUNTIME:

| Declared in | Value |
|---|---|
| Addendum `:7-8` | `feat/sabiroute-routing-foundation` @ `08201da8013a58b486d5fa2d6c46b36588a27781` |
| Decision pack `:6-8` | same branch, same HEAD, "2 modified tracked files" |
| **Live** (this pass) | `sec/deps-nov` @ `1e69ada943f3d3921122219e7a569cdff989d3fd` |
| Last commit | `1e69ada9 … 2026-11-07 14:45:03 +0100 test: strengthen settlement integrity regression coverage` |

`git merge-base --is-ancestor 08201da8… 1e69ada9…` → **ANCESTOR-CONFIRMED**. The declared baseline is a
genuine ancestor, so historical provenance is coherent; the **named branch is simply no longer the
working branch**. This is WP-1's **F-WP1-4**, still unfixed — correctly, because fixing it moves the
digest chain. It must be folded into **WP2-D8**'s single pass if corrected at all.

**Tracked modifications: 0** (`git status --porcelain --untracked-files=no` → empty).

**P4 — Security remediation lane.** VERIFIED BY RUNTIME:

```
$ git status --porcelain src/sabiroute/api/completions.py tests/test_r6_settlement_integrity.py
(no output)
```

**Both files are tracked and clean.** The settlement-integrity work was **committed** in `1e69ada9`
itself ("test: strengthen settlement integrity regression coverage"), not left dangling untracked. This
is materially better than the decision pack's 2026-11-07 note implied. **Mission C and security
remediation therefore remain separable:** the security lane is already durable in git; the R6 corpus is
not. No R6.0 act needs to touch the security lane, and none may.

### 4.4 Untracked-count discrepancy — one of two now explained

| Measurement | Value | Explanation |
|---|---|---|
| WP-0 baseline (2026-11-09) | 147 | Baseline |
| `close-final-07` (2026-11-07) | 146 | **Unreconciled** — one-path difference |
| **Live now (2026-11-10)** | **148** | 147 + **this WP-2 line's own predecessor file** |

The 148 is fully accounted for: WP-2 created one untracked artefact. **The 146-vs-147 discrepancy
remains unexplained** and is recorded as an open evidence gap (§6.D). It is small but it is exactly the
class of drift that makes a manifest unreliable.

---

## 5. U2 vector-refresh authority — four-way separation

Directive Part 4 requires the sequence and four distinct questions. They are kept strictly apart.

### 5.1 The historical sequence (from source, not memory)

| Date | Act | Evidence |
|---|---|---|
| 2026-11-06 | Addendum created; baseline declared `feat/…foundation @ 08201da8` | addendum `:6-8` |
| 2026-11-07 | **Amendment 1** — five digest classes; owner work order; *"at `1e69ada9`"* | addendum `:14-22` |
| 2026-11-07 14:45 | Commit `1e69ada9` — settlement-integrity coverage | `git log -1` |
| 2026-11-07 | **O3/O4/O5 + R6.0-D** recorded | decision pack `:25-30` |
| **2026-11-09** | **Amendment 2** — C-02 provenance reconciliation; digest supersession stated | addendum `:24-38` |
| 2026-11-09 | WP-1 measures addendum = **38,603 bytes, 646 lines, `69166509…b63399a6`** | wp0-wp1 §2.1 |
| 2026-11-09 | WP-1 finds test vector = `(35932, ab0bd89c…)` → **test fails** `assert 38603 == 35932` at `:381` | wp0-wp1 §2.4 |
| 2026-11-09 | WP-1 refreshes to `(38603, 69166509…)`; 6 passed; full file 81 passed / 1 skipped | wp0-wp1 §2.4 |

**The decisive sentence**, addendum `:34-38`:

> *"This amendment changes this file's whole-file digest: the Amendment 1 digest `ab0bd89c…68ce891ea`
> (35,932 bytes, 611 lines) is superseded for the current document bytes by the post-amendment digest,
> and any genesis entry must be derived from the latter, never the reverse."*

### 5.2 The four questions, separated

| Dimension | Finding |
|---|---|
| **Technical correctness** | **CORRECT.** The old vector pinned a digest the normative text itself declares superseded. The stale value `(35932, ab0bd89c…)` is *exactly* the Amendment-1 value. The refresh corrected a genuinely **failing** assertion — it relaxed nothing. Verified: live vector at `:174` is `(38603, "69166509…")`. |
| **Historical evidence** | **CORROBORATED.** The supersession is documented inside the normative instrument (Amendment 2), not merely asserted by the actor who made the change. Two independent computations agreed (BSD `shasum` and the test's own canonical algorithm). |
| **Owner authority** | **PARTLY TRACEABLE — NOT RATIFIED.** Amendment 2's own text states the 2026-11-07 work-order artefact *"has not been independently located in the available evidence"*, and that the owner confirmed O1/O2 **in session on 2026-11-09 UTC**. So authority for the *amendment* is a recorded session confirmation. Authority for the *test edit* was claimed from **build map §1.3/§9 — which is not present in this workspace and cannot be verified.** |
| **Version-control provenance** | **ABSENT.** The file is untracked (`??`). No commit records the change. Git history contains no trace, and when first tracked the commit will show only the post-refresh value. The sole record is `wp0-wp1-evidence-2026-11-09.md §2.3`. |

### 5.3 Consequence — not silently ratified

The refresh is **not ratified by this pack**. It is assessed **conditional**:

- **Sound** on technical and documentary grounds.
- **Unverifiable** on executing authority (build map absent).
- **Unprovenanced** in version control (untracked file, byte-level record only).

**WP2-D7 requires explicit owner confirmation.** If the owner declines to confirm, the vector must be
re-derived under WP2-D8 — and because the file is untracked, re-derivation would leave the *same* audit
gap. Tracking (R6.0-D step 2) is the only remedy, and it is a separate act.

---

## 6. FINAL DECISION PACK

Per directive Part 6. Nothing here is executed. Nothing already decided is re-asked.

### A. Already approved — confirmation only

| ID | Exact decision statement | Historical owner decision | Supporting source | Recommended | Consequence of acceptance | Consequence of rejection |
|---|---|---|---|---|---|---|
| **WP2-D1** | Confirm **Amendment 2** as the operative provenance authority: the 2026-11-07 work order is *corroborating historical evidence*, not independently authenticated authority. | Amendment 2, 2026-11-09 | Addendum `:24-38` | **Confirm** | WP-3 may cite Amendment 2 without re-deriving; authority hierarchy stable. | Provenance reverts to the unlocated 2026-11-07 artefact; WP-2 has no authority statement and halts. |
| **WP2-D5** | Confirm the **nine-field genesis schema** is normatively enumerated and requires **no change**; the optional inline-table locality fix is a sub-option of D8 only. | **O4**, 2026-11-07 | Decision pack §3.2 `:244-256`; `PARAM-B.5`; 508-byte vector | **Confirm (no schema change)** | F3 is closed as rejected; schema untouched. | F3 would require rewriting a schema that is already correct — reopening a settled decision. |
| **WP2-D7** | Confirm the **WP-1 U2 vector refresh** (2026-11-09) was authorised, on the four-way basis in §5. | Amendment 2 supersession, 2026-11-09 | Addendum `:34-38`; test `:174`; wp0-wp1 §2.3 | **Confirm**, recording that build-map §1.3/§9 authority is **unverified here** | The vector is stable; WP-2 proceeds. The unverified-authority limitation is recorded permanently. | Vector must be re-derived under D8 — which cannot close the audit gap while the file is untracked. |
| **WP2-D8** | Approve the **single-pass stabilisation ordering**: (1) apply D2 edits → (2) correct addendum `:9-11` embedded reference → (3) recompute `PROTOCOL` + `ADDENDUM` vectors **once** → (4) run suite. | **R6.0-D steps 1→5**, 2026-11-07 | Decision pack `:82-90`; wp0-wp1 F-WP1-1 | **Approve the plan** | Chain stabilised once instead of re-breaking. | Refreshing vectors before the final edit re-breaks them — F-WP1-1 exactly. |

### B. Documentary correction

| ID | Exact decision statement | Historical | Source | Recommended | Acceptance | Rejection |
|---|---|---|---|---|---|---|
| **WP2-D12** | Update the correction-proposal **status banner** (`:3`) and its **§2 stale line counts** (349→348, 499→646) to reflect O3/O4/O5 adoption. | F5; F-WP1-2; F-WP1-3 | Correction proposal `:3`, §2 | **Approve** | Proposal stops misdescribing itself; WP-3 no longer inherits false status. | The "source of truth" for WP-2 continues to self-declare as unapproved, with wrong counts. |

### C. Genuine owner decisions

| ID | Exact decision statement | Historical | Source | Recommended | Acceptance | Rejection |
|---|---|---|---|---|---|---|
| **WP2-D2** | Approve the bounded **six-item edit set** to both U2-bound docs: the five §4.5 corrections **plus** the consolidated 12-key VER table (F2), including the one-line REG/VER asymmetry note (F6 residue). **The decision (O5) is already made; this approves the edits that implement it.** | **O5** approved the decision, **not** the edits | Decision pack §4.5 `:446-454`; O5 `:29` | **Approve as one atomic change**, after D8's ordering | 03B-R1 §6 and `PARAM-A.4` stop contradicting O5. Both files move `protocol_sha256`/`addendum_sha256`. | Normative text keeps authorising a container `PARAM-A.2` forbids. WP-2 cannot close. |
| **WP2-D3** | Confirm **O1–O5 are protocol parameters, not registrable decisions**, requiring no REG locus; withdraw the WP-1 §4 blocker on that basis. | T16 locus rule approved; **O1–O5 registrability never decided** | `PARAM-A.6` `:147-152`; namespace rule `:95-100` | **Confirm** | Blocker dissolves; WP-2 resumes. Recorded as a governance act, not an inference. | A new locus must be defined and the 23-card namespace rule revisited — **architecture change; WP-2 halts**. |
| **WP2-D6** | Choose the **normative citation** for canonical JSON: `O4-A` (proposal §3.1) or `O4-B` (RFC 8785 JCS). | **O4** approved canonicalisation; citation left open | Decision pack §3.3 `:264-276` | **O4-A**, noting JCS is byte-identical for this field set | No byte change either way. Requires the `/`-unescaping hazard as a mandatory test case (§3.2 `:258-262`). | Choosing JCS also produces identical bytes — the choice is citation only. Low risk. |
| **WP2-D9** | Approve the **five negative-first test groups** as WP-2 test scope: VER schema; F7 bound; REG/VER separation; COMPLETE derivation; genesis conformance. | None — new scope | Test `:171-175`; F7; `PARAM-A.4` | **Approve**, authored **after** D8 so vectors are stable | The conformance gaps close; F-WP2-2 is covered. | The protocol remains untested against its own schema; F7 stays undetected in code. |
| **WP2-D11** | Approve the **new normative `items_checked` bound** (edit E8): `0 ≤ items_checked ≤ 10`, and `result=PASS` requires `items_checked == 10`. | **None — new constraint** | 03B-R1 §6 `:128` vs §7 `:137-169` | **Approve** | Closes the only live integrity hole: a PASS claiming 3/10 items can no longer make COMPLETE valid. | A registration can be `COMPLETE` with 7 of 10 inventory items never checked. **This is the most consequential item in the pack.** |

> **WP2-D11 is the only edit adding a normative constraint the owner has never approved.** It must not
> be folded into D2 silently. It is separable and should be answered on its own terms.

### D. Blocked by evidence

| Item | Blocked on | Status |
|---|---|---|
| **WP2-D7 full ratification** | Build map **§1.3/§9** — the authority cited for the WP-1 refresh — is **not in this workspace** | Cannot verify. Confirmation must carry the limitation, or the owner must supply the build-map text. |
| **WP-1 exit gate** | **VS Code Copilot read-only report** | OPEN. A builder may not self-certify. |
| **WP-4 independent verification** | A second actor — **no Terminal return exists** (§0) | Cannot start. |
| **146 vs 147 untracked discrepancy** | `close-final-07` (146) vs WP-0 (147) at the same commit | **Unreconciled.** One path. Recorded, not explained. |
| **2026-11-07 owner work-order artefact** | *"not independently located"* per Amendment 2 `:28-29` | Unlocatable here. O1/O2 rest on the 2026-11-09 session confirmation. |
| **N1/N2/N3 (C-02)** | Owner acts, independent of WP-2 | **Untouched.** Not in WP-2 scope; must not be merged with P1–P4 (§4.2). |
| **Digest re-measurement** | Bash classifier blocked commands in the WP-1 and predecessor-pack sessions; working again this pass | WP-0/WP-1 figures re-confirmed where re-run; the rest remain *reported*. |

### E. Not authorised

Explicitly **not** granted by any decision above:

- Any **file edit** to `docs/r6-*.md`, `tests/`, or `src/` — this pack is a proposal only.
- **Staging, committing, pushing, tagging**; `git add`, `reset`, `clean`, `stash`, branch switch, rebase.
- **Creating a worktree** or moving the corpus to one.
- **Tracking the corpus** (R6.0-D step 2) — a separate repository act under separate authority.
- **Genesis, REG, VER, marker, ledger, `ledger_id`, key, signature, checkpoint.**
- **BL-22 signing** (stays `NOT SIGNED`) · **G7** (stays `NOT GRANTED`) · Track A · R6.1 · R6.2–R6.7.
- **WP-3, WP-4, WP-5.**
- **Migrations, deployments, production use.**
- Any act on the **security-remediation lane** (`src/sabiroute/api/completions.py`,
  `tests/test_r6_settlement_integrity.py`) — tracked, clean, and out of scope.
- **Reading or printing credentials**; no `.env` access.

---

## 7. Minimal implementation sequence — after approval only

Ordered by **R6.0-D's binding sequence** (`:82-90`) and **WP2-D8**'s single pass. Each step names its
authority and every file it touches.

| # | Step | Authority | Files touched |
|---|---|---|---|
| 0 | Owner answers §6.A–C | Owner | — |
| 1 | Apply the five §4.5 corrections (E1–E3, E5–E6) | WP2-D2 | `docs/r6-registration-protocol-03b-r1.md` `:112`, `:114-117`, `:130-135` · `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` `:93-99`, `:110-116` |
| 2 | Insert the consolidated **12-key VER table** + REG/VER asymmetry note (E2, E4) | WP2-D2 | `docs/r6-registration-protocol-03b-r1.md` §6 (replaces the fence; new note) |
| 3 | Insert the **`items_checked` bound** (E8) | **WP2-D11** | `docs/r6-registration-protocol-03b-r1.md` §6 |
| 4 | Correct the addendum's **embedded 03B-R1 line count + digest** `:9-11` to post-step-2 values (E7) — **after** steps 1–3 | WP2-D8 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` `:9-11` |
| 5 | Recompute `PROTOCOL` + `ADDENDUM` **once**, same pass (E9) | WP2-D8 | `tests/test_r6_registration_digest_conformance.py` `:173-174` |
| 6 | Update correction-proposal banner + stale line counts (E11) | WP2-D12 | `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` `:3`, §2 |
| 7 | Append the five negative-first test groups (E10) — **after** step 5 | WP2-D9 | `tests/test_r6_registration_digest_conformance.py` (append; **one file, no new module**, so the WP-3 inventory is untouched) |
| 8 | Run `pytest tests/test_r6_registration_digest_conformance.py -q` and `pytest tests/test_r6_settlement_integrity.py -q` | WP2-D8/D9 | — (read-only) |
| 9 | **Record the byte-level diff** (files are untracked; no `git diff` exists) | F-WP2-1 residue | `artifacts/r6-closure/` |
| — | Track the corpus — **R6.0-D step 2, separate act, NOT authorised here** | R6.0-D | the 147 tracked-to-be paths |
| — | Re-derive U2 → build genesis → register — **NOT authorised** | R6.0-D steps 3–5 | — |

**Exact affected-file set (4 files, all currently untracked):**

1. `docs/r6-registration-protocol-03b-r1.md`
2. `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md`
3. `tests/test_r6_registration_digest_conformance.py`
4. `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md`

Steps 1–4 change the bytes of both U2-bound docs. **Step 5 must be the only vector recomputation**, or
the chain re-breaks per F-WP1-1. Step 9 is mandatory precisely because step 2 of R6.0-D has not
happened: without it there is no audit record at all.

---

## 8. Compliance and status

| Requirement | Status |
|---|---|
| No file edited in `docs/`, `tests/`, `src/` | Confirmed — this pack is a proposal |
| No staging / commit / push / branch switch / worktree | Confirmed — none performed |
| No corpus tracking | Confirmed — R6.0-D step 2 not executed |
| No genesis / REG / VER / marker / ledger / key / signature / checkpoint | Confirmed |
| No migration / deployment | Confirmed |
| No T16 card touched; BL-22 unsigned; G7 not granted | Confirmed |
| Security lane untouched | Confirmed — tracked and clean, no read-modify |
| No credential read or printed; no `.env` | Confirmed |
| No claim of Terminal communication | Confirmed — §0 records `UNRECEIVED` |
| No rejected finding preserved | Confirmed — F3, F6 rejected; D10 withdrawn; N2/N3 re-addressed |
| New file created | **1** — this pack, under `artifacts/r6-closure/` |

```
CURRENT GATE:   WP-2
CURRENT PHASE:  R6.0 closure
PROVEN:         3 of 8 findings rejected/reclassified; git baseline re-measured this pass;
                all 3 U2-bound files untracked; security lane committed and clean
UNPROVEN:       build-map §1.3/§9 (absent); 146-vs-147 drift; WP-1 exit gate (no Copilot report)
UNRECEIVED:     any Terminal return — WP-2 has had exactly one actor
BLOCKED BY:     WP2-D2, D3, D6, D9, D11 (genuine) · D7 (partial) · R6.0-D step 2 (separate act)
NEXT:           owner answers §6 — then step 1
```

**DECISION PACK ONLY. NOT AN EXECUTION AUTHORISATION.**
**WP-2 REMAINS BLOCKED. R6.0 OPEN · BL-22 NOT SIGNED · G7 NOT GRANTED.**
