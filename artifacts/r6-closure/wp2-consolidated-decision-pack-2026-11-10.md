# R6.0 — WP-2 Consolidated Decision Pack

**Actor:** Claude Code Desktop (coordinator; **not** the independent verifier)
**Date:** 2026-11-10
**Scope:** WP-2 protocol and schema reconciliation — **decision pack only, no execution**
**Status:** Pack complete · **WP-2 remains BLOCKED pending the owner decisions in §8**

> Written to `artifacts/r6-closure/` and not to `docs/r6-*.md` for the same reason as
> `wp0-wp1-evidence-2026-11-09.md`: the 42-document `docs/r6-*.md` inventory is WP-3's
> reconciliation input and must not be perturbed by WP-2 working papers.

---

## 0. Coordination status — read this first

**There is no Claude Code Terminal session linked to this session.** `list_sessions(linked=true)`
returned *"No other sessions found."* No message, transcript, artifact or hash from a Terminal
session exists in this workspace.

The findings F1–F7 therefore arrived **only as text inside the owner directive**. They are treated
here exactly as Part 6 of the directive requires: as **untested assertions**, adjudicated one by one
against the actual repository. I have not pretended that two models conferred, because they did not.

**Result of adjudication:**

| Finding as asserted | Survives contact with source? |
|---|---|
| F1 HTML-comment VER vs JSONL VER contradiction | **Partly** — real conflict, but **already owner-resolved** (O5); correction unapplied |
| F2 No consolidated normative VER field table | **Yes** |
| F3 Nine-field genesis schema not explicitly enumerated | **No** — enumerated twice, and pinned by a normative digest vector |
| F4 O1–O5 registration locus circularly unresolved | **Partly** — structurally true, but likely a **false blocker** (§3 D3) |
| F5 Stale proposal status descriptions | **Yes** |
| F6 `entry_type` cannot represent REG | **No** — false premise; REG is deliberately not a ledger entry |
| F7 `items_checked` has no defined bound | **Partly** — semantics defined, validation bound absent |
| Missing VER schema / REG-VER separation tests | **Yes** |

**Three of eight asserted findings do not hold as stated.** That is the most important WP-2 result,
because acting on F3 or F6 would have rewritten a schema that is already correct.

---

## 1. Authority hierarchy actually in force

| Rank | Instrument | Status | Digest bind |
|---|---|---|---|
| 1 | `docs/r6-registration-protocol-03b-r1.md` (03B-R1) | Procedure; **governs on conflict** (own §1, `:57-59`) | U2-bound |
| 2 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | Owner-approved **parameters**; **subordinate** to 03B-R1 | U2-bound |
| 3 | `docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §0 | **Owner decisions O3/O4/O5 + R6.0-D**, recorded 2026-11-07 | not U2-bound |
| 4 | `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md` | **Proposal** — technical text, adopted by reference | not U2-bound |
| 5 | `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` | **Proposal — self-declares NOT owner-approved** (`:3`) | not U2-bound |

**The hierarchy defect that generates most of WP-2's difficulty.** 03B-R1 §1 (`:62-64`) states the
addendum is subordinate, that *03B-R1's procedure governs on conflict*, and that a conflict must be
reported rather than silently resolved. But the addendum's `PARAM-A.7` and owner decision **O5**
specify a JSONL ledger that **contradicts 03B-R1 §6's HTML-comment container**. The coordinating
instrument (O5) says one thing, the governing instrument (03B-R1) says another, and the subordination
rule points at the wrong one. WP-2 cannot fix this by editing the subordinate document alone.

**Digest sourcing discipline.** Values below are those **reported by WP-1 as VERIFIED BY RUNTIME** on
2026-11-09. I did **not** recompute them: the Bash classifier blocked every command in this session
(see F-WP2-3). Treat them as *reported*, not *re-verified*.

| File | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| 03B-R1 | 12,619 | 348 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| Addendum | 38,603 | 646 | `6916650940b73219f20f427227f4f677ea6f84bcd0ab727135d25b28b63399a6` |
| T16 | 52,782 | — | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| Genesis constant `SHA256("R6-VER-LEDGER-GENESIS:v1")` | — | — | `e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` |
| Genesis worked-example line (no LF) | 508 | — | `ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28` |
| Genesis worked-example line (+LF) | 509 | — | `452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe` |

---

## 2. Finding adjudication, with evidence

### F1 — HTML-comment VER vs JSONL VER

**VERIFIED BY INSPECTION — already owner-resolved; correction unapplied.**

- `03B-R1 §6` (`:110-135`): verification is *"a separate structured comment"* `<!-- VER:v1 … -->`, six fields.
- `PARAM-A.2` (`addendum:121-125`): VER lives in *"a distinct append-only verification ledger"*, form unspecified.
- `PARAM-A.7` (`addendum:153-168`): that ledger is **append-only JSONL**, canonical JSON, hash-chained.

A sharper conflict the finding did not name: a comment written adjacent to T16 is **co-located** with
the REG record, which `PARAM-A.2` explicitly forbids ("never co-located with the REG record they verify").

**Already decided.** Owner decision **O5** (decision pack `:28`): *"The append-only JSONL VER ledger
is authoritative… The HTML-comment VER representation in 03B-R1 §6 must not be treated as an
alternative authoritative ledger format."* Recorded 2026-11-07.

F1 is **not an open contradiction**. It is a **five-item correction backlog** already specified at
decision pack §4.5 (`:448-454`) and never executed. Re-opening it would re-litigate a settled
decision, which Part 6 forbids.

### F2 — No consolidated normative VER field table

**VERIFIED BY INSPECTION.** The VER field set exists only as (a) a *diff* table at decision pack §4.2
(`:382-396`) and (b) a payload table in proposal §3.3 (`:291-300`), a non-approved document. No
approved document carries one consolidated table for the 12-key VER entry (8 payload + `seq`, `prev`,
`entry_type`, `entry_sha256`). F2 holds.

### F3 — Nine-field genesis schema "not explicitly enumerated"

**NOT ESTABLISHED — contradicted by source.** Enumerated explicitly, twice: decision pack §3.2
(`:245-255`) numbered table `#1`–`#9`; proposal §3.2 (`:256-265`) six payload fields plus envelope.
`PARAM-B.5` (`addendum:243-252`) adopts *"the nine-field set defined by proposal §3.2's field table,
including `t16_sha256`"*, pinning it with a **normative, fully reproducible 508-byte worked example**
(`ad1484b0…caf28`, decision pack §3.5/§3.6).

The real defect is narrower: the enumeration is **incorporated by reference**, so a reader holding
only the addendum cannot see the table. That is a **locality defect**, not a missing schema. No
schema change is warranted.

### F4 — O1–O5 registration locus

**STRUCTURALLY TRUE, PROBABLY A FALSE BLOCKER.** `PARAM-A.1` (`addendum:115-119`) writes REG
*"adjacent to the canonical T16 register entry it registers"*. O1–O5 are not T16 cards (T16 holds
A1–A4, B1–B9, C1–C4, D1–D6 = **23**), so no locus exists *if* O1–O5 require REG.

The record says they do not. The Reading-B registration inventory is **13 decisions: A1–A4 and
B1–B9** (`addendum §10:485-488`; FAST-04:221-227). O1–O5 are absent from it. O1–O5 are **owner
selections about the protocol itself** — O1 = `marker_sha256` (`PARAM-B.6`), O3 = multi-line response
rule (`PARAM-B.1`), O4 = canonical JSON/genesis (`PARAM-B.5`), O5 = JSONL-ledger authority. They sit
in the same namespace class as `PARAM-*`, which the namespace rule (`:94-99`) says are *not* decision
cards and do not enter the 23-decision register.

**O1–O5 most likely require no REG at all**, and the blocker recorded in
`wp0-wp1-evidence-2026-11-09.md §4` dissolves on that reading. Dissolving a recorded blocker is a
governance act, so it is raised as **D3**, not asserted.

### F5 — Stale proposal status descriptions

**VERIFIED BY INSPECTION.** The correction proposal still declares (`:3`): *"PROPOSAL — NOT
OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED"*. Since 2026-11-07 the owner has recorded O3/O4/O5,
and decision pack §0.3 (`:64-66`) states those safeguards are *"carried into the canonical corrections
proposal"*. The banner is stale on the O3/O4/O5 points. WP-1's F-WP1-2 reached the same place
independently. F5 holds.

### F6 — `entry_type` cannot represent REG

**NOT ESTABLISHED — false premise.** `entry_type ∈ {"GENESIS","VER"}` (proposal §3.2:246, §3.3:286).
REG is **deliberately not a ledger entry**: `PARAM-A.1` places REG adjacent to T16 as a marker
comment, and O5 confirms *"REG remains adjacent to the relevant T16 decision card… VER entries reside
in the separate append-only JSONL ledger."* `entry_type` never needs a `REG` member; adding one would
violate `PARAM-A.2` and O5 by co-locating the two families.

The legitimate observation inside F6 is a **documentation** one: REG and VER use different encodings
(HTML-comment marker vs JSONL line), intentional but nowhere stated as intentional. Fix is a rationale
note, not a schema change.

### F7 — `items_checked` bound

**PARTIALLY VERIFIED.** Semantics *are* defined — proposal §3.3 (`:298`): *"Integer count of the
ten-item inventory checked"*, and 03B-R1 §7 (`:136-168`) fixes that inventory at ten items. But **no
normative validation rule exists**: nothing requires `0 ≤ items_checked ≤ 10`, and nothing requires
`items_checked == 10` for `result=PASS`.

**Failure scenario (STATIC-ANALYSIS FINDING):** a VER entry with `result="PASS"` and
`items_checked=3` satisfies every rule currently stated, and makes a registration `COMPLETE` under
`PARAM-A.4` while three of the ten inventory items were never checked. This is the only F1–F7 item
that is both unfixed and unblocked by policy.

### Missing tests

**VERIFIED BY INSPECTION.** `tests/test_r6_registration_digest_conformance.py` (docstring `:1-27`)
encodes **U1/U2/U3/U4 digest vectors** — 33 values plus synthetic U4 marker vectors. It does **not**
validate a VER entry against any schema, does **not** assert REG/VER separation, does **not** test
`COMPLETE` without a matching `PASS` VER, and does **not** test the F7 bound. The claim holds.

---

## 3. The nine required WP-2 decisions

*Recommendations are recommendations — none is an owner decision.*

### D1 — Protocol authority and the C-2 amendment

- **Evidence:** addendum Amendment 2 (`:23-37`), `§12.4` (`:624-641`); directive Part 1.
- **Normative source:** the addendum as amended 2026-11-09.
- **Already approved?** **Yes.** Amendment 2 is applied and consistent with the directive's Part 1 classification (2026-11-07 work order = corroborating historical evidence, not independently authenticated authority).
- **Proposed correction:** none to substance; optional one-line owner restatement so WP-3 can cite it without re-deriving.
- **Files:** none. **Owner approval:** confirmation only.
- **Recommendation:** accept Amendment 2 as the operative authority statement.

### D2 — JSONL VER schema and HTML-comment supersession

- **Evidence:** O5 (decision pack `:28`); §4.3 conflicts (`:398-424`); §4.5 correction list (`:448-454`); F1, F2.
- **Normative source:** **O5**, 2026-11-07.
- **Already approved?** **The decision: yes. The edits: no.**
- **Proposed correction:** apply the five §4.5 corrections **plus** the sixth F2 requires — a consolidated normative 12-key VER-entry table at 03B-R1 §6.
- **Files:** `03B-R1` (`:112`, `:114-117`, `:130-135`); `addendum` (`:93-99`, `:110-116`).
- **Owner approval:** **Yes** — both files are U2-bound; every edit moves `protocol_sha256`/`addendum_sha256`.
- **Recommendation:** approve the six-item set as one atomic change, executed after D8's ordering decision.

### D3 — Separate REG architecture and the O1–O5 locus

- **Evidence:** `PARAM-A.1`/`A.2`; namespace rule (`:94-99`); 13-decision Reading-B inventory (`§10:485-488`); F4.
- **Already approved?** Locus rule for **T16 cards**: yes. For **O1–O5**: the question is malformed.
- **Proposed correction:** record that O1–O5 are **protocol parameters, not registrable decisions**, requiring no REG locus; withdraw the WP-1 §4 blocker on that basis.
- **Files:** `wp0-wp1-evidence-2026-11-09.md §4` (annotation), and whichever WP-3 document inherits the status.
- **Owner approval:** **Yes — a decision, not an edit.**
- **Recommendation:** confirm O1–O5 are non-registrable. *If the owner disagrees*, a new locus must be defined and the 23-card namespace rule revisited — an **architecture change** that halts WP-2 until approved (CLAUDE.md §5).

### D4 — REG/VER separation and entry-type design

- **Evidence:** proposal `§3.2:246`, `§3.3:286`; F6; O5.
- **Already approved?** **Yes.** The separation is the approved design.
- **Proposed correction:** **none to schema.** Add a rationale note in 03B-R1 §6 that REG (marker, adjacent to T16) and VER (JSONL, separate ledger) intentionally use different encodings. `entry_type` stays `{"GENESIS","VER"}`.
- **Files:** `03B-R1 §6` (rides with D2). **Owner approval:** covered by D2.
- **Recommendation:** **reject F6 as a defect.** Document the asymmetry; add no `REG` entry type.

### D5 — Explicit nine-field genesis schema

- **Evidence:** decision pack §3.2 (`:245-255`); proposal §3.2 (`:256-265`); `PARAM-B.5` (`:243-252`); 508-byte vector; F3.
- **Already approved?** **Yes** — owner decision **O4**.
- **Proposed correction:** **none for definition.** Optional locality fix: inline the nine-field table into the addendum. That moves `addendum_sha256` and must fold into D8's single pass — never a separate edit.
- **Owner approval:** yes for the optional inline; **no** for the schema.
- **Recommendation:** **reject F3 as an omission.**

### D6 — Canonical JSON and unresolved schema parameters

- **Evidence:** `PARAM-B.5` (`:232-252`); proposal `§3.1` (`:212-243`); decision pack §3.3/§3.4 (`:264-288`); addendum §11 (`:512-516`).
- **Normative source:** `PARAM-B.5` + **O4**.
- **Already approved?** Canonicalisation **yes** (O4-A). Duplicate-key rejection **required** by O4's safeguards. Genuinely open: **`O4-A` vs `O4-B` (RFC 8785 JCS)** — which produce **byte-identical output for this field set**, so the choice is *which standard to cite*, not what the bytes are.
- **Proposed correction:** record the citation choice; keep duplicate-key rejection; record the `/`-unescaping interop hazard as a mandatory conformance case.
- **Owner approval:** **yes** for the citation choice.
- **Recommendation:** retain **O4-A**; note JCS byte-equivalence so a future implementation may cite it without changing bytes.

**Still-open implementation details (not policy):** VER-ledger filename/path, canonical REG locus path,
manifest serialisation format. Addendum §11 (`:512-516`) already classes these as preconditions to fix
at first execution. No WP-2 action.

### D7 — U2 vector-refresh authority and provenance

- **Evidence:** addendum Amendment 2 (`:33-37`): *"the Amendment 1 digest `ab0bd89c…68ce891ea` (35,932 bytes, 611 lines) is superseded… any genesis entry must be derived from the latter, never the reverse"*; §11 U2 row (`:508`); `wp0-wp1 §2.2-§2.4`.
- **Already approved?** The **direction** is authorised by the document text. The **act** was executed in WP-1, reported as authorised by build-map §1.3/§9 — **which I have not seen and cannot verify** (no build-map file is present in this workspace). That authority claim is **UNVERIFIED** by me.
- **Proposed correction:** none. Record provenance: the stale vector `(35932, ab0bd89c…)` was exactly the superseded Amendment-1 digest, so the refresh restored truth and did not weaken the assertion.
- **Files:** `tests/test_r6_registration_digest_conformance.py:174` (already changed).
- **Owner approval:** **retroactive confirmation**, because the executing authority cited is not in evidence here.
- **Recommendation:** confirm the WP-1 refresh was authorised; otherwise re-derive the vector under D8.

### D8 — Protocol/addendum digest dependency (ordering)

- **Evidence:** `wp0-wp1 F-WP1-1`; addendum `:9-11` embeds 03B-R1's line count **and** digest; conformance test `:173` binds `PROTOCOL`, `:174` binds `ADDENDUM`; R6.0-D ordering (decision pack §0.4, `:81-89`).
- **Already approved?** The *ordering principle* (R6.0-D steps 1→5) is approved. The *collision* — that WP-1 and WP-2 mutually invalidate — was not anticipated by the build map.
- **Proposed correction — one stabilisation pass:**
  1. Apply D2's six-item edit set to 03B-R1 and the addendum.
  2. Correct the addendum's embedded reference at `:9-11` to the **new** 03B-R1 line count and digest.
  3. Recompute `PROTOCOL` and `ADDENDUM` U2 vectors **once**, same pass.
  4. Only then run the conformance suite.
- **Files:** the two normative docs + two vector lines.
- **Owner approval:** **Yes** — this is the execution plan for D2/D4/D5 (directive Part 7).
- **Recommendation:** adopt it. Refreshing vectors before the final normative edit re-breaks itself, exactly as F-WP1-1 predicts.

### D9 — Missing tests and validation strategy

- **Evidence:** conformance docstring (`:1-27`); F7; F2; O5; `PARAM-A.4`.
- **Already approved?** No — new test scope.
- **Proposed correction (minimum viable, negative-first):**
  1. **VER schema** — conforming 12-key entry passes; duplicate key, `\/`-escaped `/`, reordered keys, space after `:`, `seq` as `0.0`/`"0"` **fail closed** (six cases already specified, decision pack §3.6).
  2. **F7 bound** — `items_checked` outside `0..10` rejected; `result=PASS` with `n<10` rejected.
  3. **REG/VER separation** — VER co-located with a REG rejected; `entry_type` has no `REG` member.
  4. **`COMPLETE` derivation** — missing/malformed/mismatched/`FAIL` VER ⇒ invalid (`PARAM-A.4`, 03B-R1 §6/§16).
  5. **Genesis conformance** — reproduce `ad1484b0…caf28`; `+LF` yields `452a05bb…` and must differ.
- **Files:** extend `tests/test_r6_registration_digest_conformance.py` — **one file, no new module**, to leave the WP-3 inventory untouched.
- **Owner approval:** **Yes** — test expansion is implementation.
- **Recommendation:** author after D8's pass, so vectors are stable when tests land.

---

## 4. New findings raised by this reconciliation

### F-WP2-1 — WP-2's audit trail does not exist yet, and R6.0-D forbids creating it first

R6.0-D (decision pack `:29`, `:81-89`) orders: ***(1) apply canonical corrections → (2) track the
corpus → (3) re-derive U2 → (4) build genesis → (5) register.*** But the entire R6 governance corpus is
**untracked** — `close-final-07` records `git ls-files | grep -c "r6-"` = **0** at baseline `1e69ada9`,
and WP-0 recorded 147 untracked paths (`close-final-07` recorded 146 at the same commit; the one-path
difference is itself unreconciled).

Consequence: **the D2/D8 edits land on untracked files and produce no `git diff`.** WP-1 already hit
this — its record notes the changed test file "is untracked… so there is no git-level diff".

R6.0-D therefore asks for the corrections *before* the tracking that would make them auditable. That
is an **auditability paradox**: the act R6.0-D exists to protect is scheduled outside version control.

**This is not a licence to reorder R6.0-D.** It is owner decision **D10**: either (a) track first,
swapping R6.0-D steps 1 and 2, or (b) keep the order and accept a byte-level (not git-level) record for
the corrections, as WP-1 did.

### F-WP2-2 — `PARAM-A.4` survives O5 only by field-name preservation

`PARAM-A.4` (`addendum:133-138`) requires *"a matching `VER:v1` record has `result=PASS`"*. That holds
under the JSONL container **only because S3 preserved the six field names and the `result` domain
verbatim** (decision pack §4.3 item 5, `:421-424`). If any D2 edit renames a field, `PARAM-A.4` breaks
silently. The D2 set must be tested against `PARAM-A.4`, not only against the schema.

### F-WP2-3 — Digest values in this pack are reported, not re-measured

Every command was blocked by the Bash classifier this session, so no digest, byte count or line count
in §1 was recomputed here. They are WP-1's runtime results carried forward. Before WP-4, a
Terminal-side run must re-measure them; a verifier that trusts this pack's numbers would be verifying
a summary, not the tree.

### F-WP2-4 — Two colliding `C-` correction series

`docs/r6-close-final-07-…-2026-11-07.md` defines **`C-1…C-5`** over the CF-01…CF-06 closure chain
(baseline drift, FINAL-04/05 row-count, corpus count, double-counted assertions, addendum §12.2 U4
wording). The O3/O4/O5 decision pack orders **"canonical corrections `C-1…C-7`"** as R6.0-D step 1.

These are **different series with overlapping identifiers.** `close-final-07` also reports C-1 and C-3
FIXED and C-2 "RECORDED, NOT FIXED", so bare `C-2` now denotes both a fixed CF-chain correction and a
distinct canonical correction. All WP-2/WP-3 references must be **register-qualified**:
`close-final-07 C-n` vs `O3/O4/O5-pack C-n` (itself distinct from `correction-proposal C-1…C-7` and
from `T16 C1–C4`). This is the same collision class as the `ADR-2/C-1` vs `GROUP-C/C1` problem already
governed by T16 §7.

---

## 5. Proposed bounded edit set — **not executed**

| # | File | Location | Change | Gated by |
|---|---|---|---|---|
| E1 | `03B-R1` | `:112` | "separate structured comment" → separate append-only ledger entry | D2, D8 |
| E2 | `03B-R1` | `:114-117` | replace `<!-- VER:v1 … -->` fence with S3 **12-key** normative table (F2 folded in) | D2, D8 |
| E3 | `03B-R1` | `:130-135` | "a matching VER record exists" → "a matching VER **ledger entry** exists" | D2, D8 |
| E4 | `03B-R1` | `§6 new` | rationale note: REG-marker vs VER-JSONL asymmetry is intentional | D4, D8 |
| E5 | `addendum` | `:93-99` | append "— realised as the JSONL ledger of proposal §3.1–§3.3" | D2, D8 |
| E6 | `addendum` | `:110-116` | "a matching `VER:v1` record" → "a matching VER **ledger entry**" | D2, D8 |
| E7 | `addendum` | `:9-11` | correct embedded 03B-R1 line count + digest **after** E1–E4 | D8 step 2 |
| E8 | `addendum` | §6 | **new** normative `items_checked` bound (F7) | **D11** |
| E9 | `conformance test` | `:173-174` | single combined `PROTOCOL` + `ADDENDUM` vector refresh | D8 step 3 |
| E10 | `conformance test` | append | five negative-first test groups | D9 |
| E11 | `correction proposal` | `:3` | update status banner for O3/O4/O5 adoption (F5) | **D12** |

**E8 is the only edit adding a normative constraint the owner has not already approved.** It must not
be folded into D2 silently.

---

## 6. Consolidated status

| Item | Status |
|---|---|
| WP-0 live baseline | **Completed** (WP-1 record; not re-executed — F-WP2-3) |
| WP-1 measurement + U2 refresh | **Completed**; **exit gate OPEN** — Copilot report absent |
| WP-2 inspection and adjudication | **Completed** — this pack |
| WP-2 F1–F7 reconciliation | **Completed** — 3 of 8 rejected, 3 qualified, 2 upheld |
| WP-2 decision pack | **Completed** — §3, §8 |
| WP-2 implementation | **Blocked** — D2, D3, D8, D9, D10, D11, D12 unapproved |
| WP-3 manifest reconciliation | **Not authorised** — requires WP-2 exit |
| WP-4 Copilot verification | **Not authorised** — requires WP-3 |
| WP-5 owner closure | **Not authorised** |
| O1–O5 REG locus blocker | **In progress** — reclassified; awaits D3 |
| `items_checked` integrity hole | **Blocked** — awaits D11 |
| Audit-trail paradox (F-WP2-1) | **Blocked** — awaits D10 |
| `C-` series collision (F-WP2-4) | **Recorded** — register-qualify all references |
| R6.0 | **OPEN** |
| BL-22 | **NOT SIGNED** |
| G7 | **NOT GRANTED** |

```
CURRENT GATE:   WP-2
CURRENT PHASE:  R6.0 closure
PROVEN:         F1-F7 adjudicated against source; 3 of 8 findings rejected
UNPROVEN:       all §1 digest values this session (Bash classifier blocked)
BLOCKED BY:     D2 D3 D8 D9 D10 D11 D12 unapproved
NEXT:           owner answers §8
```

---

## 7. Explicitly not authorised / not performed

- No file modified. No test run. No `git add`, stage, commit, push, reset, clean, stash, branch switch or rebase.
- No genesis, REG, VER, marker, ledger, key, signature or checkpoint created.
- No protocol or addendum edit executed.
- No T16 card touched; no decision registered, verified or gate-accepted.
- Security-remediation lane (`sec/deps-nov`, settlement-integrity files) untouched.
- No credential read, printed or referenced; no `.env` accessed.
- No claim that a command ran: **none did** (F-WP2-3).

---

## 8. Owner decisions required

| ID | Decision | Recommended |
|---|---|---|
| **D1** | Confirm Amendment 2 as the operative provenance authority | Confirm |
| **D2** | Approve the bounded six-item edit set to both U2-bound docs | Approve |
| **D3** | Confirm O1–O5 are non-registrable protocol parameters (dissolve blocker) | Confirm |
| **D6** | Normative citation: `O4-A` (proposal §3.1) or `O4-B` (RFC 8785 JCS) | **O4-A** (bytes identical) |
| **D7** | Confirm the WP-1 U2 vector refresh was authorised | Confirm |
| **D8** | Approve the single-pass stabilisation ordering | Approve |
| **D9** | Approve the five test groups as WP-2 test scope | Approve |
| **D10** | Resolve F-WP2-1: track corpus first, or accept byte-level record for the edits | **Decide explicitly** |
| **D11** | Approve the new normative `items_checked` bound (E8) | Approve |
| **D12** | Approve the correction-proposal status banner update (F5) | Approve |

**No decision above has been taken.**

---

**DECISION PACK ONLY. NOT AN EXECUTION AUTHORISATION. WP-2 REMAINS BLOCKED.**
**R6.0 OPEN · BL-22 NOT SIGNED · G7 NOT GRANTED.**
