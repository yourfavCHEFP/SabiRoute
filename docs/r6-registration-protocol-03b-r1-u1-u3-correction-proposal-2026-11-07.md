# R6-REG-PROTOCOL-03B-R1 — U1–U3 Specification Defect Correction Proposal

**PROPOSAL — OWNER-ADOPTED IN PART (WP2-D2 · WP2-D11); INCORPORATED BY THE WP-2 EDIT PASS — NOT EXECUTED**

**Date:** 2026-11-07 (UTC)

**Author identity:** Claude Code (registrar role, `PARAM-F.2`). This document is a
registrar-side correction proposal. It is **not** the `PARAM-F.3` independent
verification, **not** an approval, and **not** an incorporation.

**Subject:** the four specification defects recorded in
`docs/r6-registration-protocol-03b-r1-u1-u3-independent-verification-2026-11-07.md`
(§5.4, §5.2, §5.5, and the ordinal-origin contradiction underlying §5.4).

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`.

**Scope boundary.** This document proposes corrections only. It does not edit the
protocol, the addendum, the U1–U3 proposal, or either verification report. It
does not change T16, any owner decision, any decision identifier, or any register
numbering. It does not approve U1, U2 or U3, does not resolve D-U3-1, D-U3-2 or
D-U3-3, and creates no REG record, VER record, manifest, key, signature,
checkpoint, or registration. Operational registration authority remains
**DEFERRED**.

**Revision history.**

| Rev | Timestamp (UTC) | Change |
|---|---|---|
| 1 | 2026-11-06 ~23:36 | Initial proposal. Digests carried forward; no SHA-256 recomputed (command execution unavailable). |
| 2 | 2026-11-06 23:47 | §8.1 rewritten and §8.5 added: all 33 assertions recomputed by a third independent implementation — 33/33 reproduce. §3.4(B) parenthetical imprecision noted. R6a added (working tree no longer clean). No digest value changed. |

> **Date note.** The document title and header carry `2026-11-07`, which is the
> **local** calendar date at authoring. The actual UTC date of both revisions is
> **2026-11-06**. Under `PARAM-C.1` (UTC calendar dates) the correct date is
> 2026-11-06. The title is left unchanged because it is a filename, not a
> recorded field; this note is the authoritative date statement.

---

## 1. Executive summary

The independent re-derivation reproduced every digest in the U1–U3 proposal:
23/23 U1 card digests, 3/3 U2 whole-file digests, the U3 genesis constant, and
6/6 behavioural assertions. **The arithmetic is sound and no digest changes.**

The defects are in the *specification around* the digests. Four are addressed
here:

| ID | Defect | Consequence | Digest impact | Owner classification |
|---|---|---|---|---|
| **D1** | Ordinal origin is stated three incompatible ways | A verifier cannot tell which line ordinal is recorded | **None** | 1 — editorial |
| **D2** | `marker_sha256` has no defined byte boundary | A mandatory VER field is uncomputable; VER cannot be written | **None** (no value exists to change) | 3 — new owner decision |
| **D3** | Load-bearing choices are absent from the open-decision list | Owner is asked to approve an incomplete decision set | **None** directly; the *answers* change `entry_sha256` | 1 for the list; 3 for each added decision |
| **D4** | Three of 23 test-vector line ranges are wrong | A verifier following the table gets 3 false failures | **None** — labels only | 1 — editorial |

**Bottom line.** D1 and D4 are label defects: they change what the table *says*
about a byte span, not the span itself. D2 and D3 are substantive: D2 blocks VER
execution outright, and D3 means the owner is currently being asked to approve a
proposal whose open-decision list omits choices that determine the ledger's hash
chain.

**No digest in §4.1, §4.2 or §4.3 of the U1–U3 proposal changes.** §8 shows why
this is a proof, not an assumption.

**One limitation, stated up front.** Revision 1 of this document was produced in
a session where command execution was unavailable, so no SHA-256 was recomputed
there. **Revision 2 (2026-11-06 23:47 UTC) closed that gap:** all 33 assertions
were recomputed by a third independent implementation and every one reproduces.
See §8.1 and §8.5. This document still does **not** substitute for the
`PARAM-F.3` verifier — it was produced by the registrar identity (§10 R7).

---

## 2. Source documents and evidence inspected

| # | Document | Lines | Role in this analysis |
|---|---|---:|---|
| 1 | `docs/r6-registration-protocol-03b-r1.md` | 348 | Governing procedure. §5 REG grammar, §6 VER grammar, §8 normalisation, §17 open issues |
| 2 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 646 | Owner-approved parameters. §4 `PARAM-B`, §11 unresolved items, §12.2 disposition table |
| 3 | `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md` | 544 | The proposal under correction. §1.1 U1, §2.1 U2, §3 U3, §4 vectors, §5 deviations, §6 open decisions |
| 4 | `docs/r6-registration-protocol-03b-r1-u1-u3-verification-report.md` | 389 | Registrar self-check. §3 U1 table, Appendix A script |
| 5 | `docs/r6-registration-protocol-03b-r1-u1-u3-independent-verification-2026-11-07.md` | 434 | Second-implementation re-derivation. §5 defect register |
| 6 | `docs/r6-t16-r6-decision-option-register.md` | 634 | Canonical decision register — the U1 source object |
| 7 | `docs/r6-fast-04-r6.0-closure-architecture.md` | — | Closure architecture. §2.3 Gate R6.0-C3 (13 registrations under Reading B) |

**Method.** Every claim below was checked against the source text directly, not
taken from the prior reports. The three disputed card spans (A4, B9, D6) were
re-read line by line from T16 and their trailing-separator structure confirmed
by inspection. Where a prior report's conclusion is repeated, it is because the
source text was re-checked and agrees — not because the report said so.

**A note on the brief's framing of D1.** The assignment describes D1 as a
"card-ordinal contradiction" in which "the normative ordinal rule and worked
example disagree about which card is ordinal zero." No literal *card* ordinal
exists in any of the seven documents: T16 §3 (`:87-116`) indexes the 23 decisions
by ID only, with no positional numbering, and no document assigns a card an
ordinal. The ordinal contradiction that **does** exist is a **line-ordinal**
contradiction, and it is real, demonstrable, and has the same practical effect
the brief describes. §4.1 documents that defect precisely rather than inventing a
card-ordinal construct to match the brief's wording.

---

## 3. Four-defect register

### 3.1 D1 — Ordinal origin is stated three incompatible ways

**Severity: high. Blocks reproducible verification.**

**A. Exact location**

| Artifact | Location | What it says |
|---|---|---|
| Normative rule | proposal §1.1 steps 8–10 (`:82-89`) | "Locate the card heading…"; "Take the lines from the card heading line up to, but excluding, the end line." |
| Normative evidence list | proposal §1.1 (`:106-109`) | "heading line number (**1-based**, canonical form); end line (**exclusive**)" |
| Worked example | proposal §4.1 table (`:435-459`), column `Lines (canonical)` | Unlabelled range, e.g. `A1 \| 123–135`, `A4 \| 168–182` |
| Verification report | `…verification-report.md` §3 (`:91-93`) | "`start` is the 1-based line number of the card heading; `end` is the exclusive end line. Both are in the newline-canonicalised form, and both agree with the 'Lines (canonical)' column." |

**B. Root cause**

The specification never states **which span** the recorded end ordinal measures.
There are two candidate spans for every card:

- the **raw span** produced by step 10 — heading line through the line before the
  terminating heading, *before* step 11 strips trailing separators;
- the **canonical span** produced by step 11 — the same region after trailing
  blank lines and horizontal rules are removed.

Step 10 defines the raw span. Step 11 then shortens it. The evidence list at
`:106-109` says "end line (exclusive)" and "canonical form" but does not say
whether "end" is the step-10 end or the step-11 end. The implementation recorded
the **step-10** end. The table inherited it.

For 20 of 23 cards the two ordinals coincide numerically, which is why the defect
survived two verification passes. Exactly one line is stripped from those cards
(the blank line before the next heading), so:

```
raw span inclusive end  ==  canonical span exclusive end
```

For A4, B9 and D6, **three** lines are stripped — blank, `---`, blank — so the
two ordinals diverge by 2. The coincidence is an accident of T16's layout, not a
property of the rule.

The verification report compounds this: its `end` value is the 0-based index of
the next heading line, which equals the 1-based exclusive end of the **raw**
span. The report asserts it is the exclusive end of the **canonical** span. For
A4/B9/D6 that assertion is false.

**C. Proposed correction**

Replace proposal §1.1 step 10 and the evidence list with the following, which
fixes the ordinal origin, the base, and the span in one place.

> **10.** Take the lines from the card heading line up to, but excluding, the end
> line. Call this the **raw span**.
>
> **11.** **Strip trailing separators:** remove trailing blank lines; then, if the
> last remaining line is a horizontal rule matching
> `^ {0,3}(-{3,}|\*{3,}|_{3,})\s*$`, remove it; repeat step 11 until stable. Call
> the result the **canonical span**.
>
> **11a. Ordinal convention (normative).** All line ordinals recorded as evidence
> are **1-based** and describe the **canonical span**, expressed as the half-open
> interval `[start, end)`:
>
> - `start` = the 1-based ordinal of the card heading line;
> - `end` = the 1-based ordinal of the first line **after** the canonical span,
>   i.e. `start + (number of lines in the canonical span)`.
>
> The raw span is **not** recorded as evidence. An implementation may use
> 0-based indices internally but must convert before recording. A recorded
> `[start, end)` must satisfy `end − start = canonical line count`; a record that
> does not satisfy this identity is malformed and must be rejected.

And replace the evidence list at `:106-109` with:

> **Evidence recorded with the digest** (so the byte span is stated, per
> `PARAM-B.4`): source path; source whole-file digest (U2); decision ID;
> `start` (1-based, canonical span); `end` (1-based, exclusive, canonical span);
> canonical line count; canonical byte length; digest. The identity
> `end − start = canonical line count` must hold.

**Technical rationale.** The half-open `[start, end)` form is the only one that
makes the recorded ordinals self-checking: `end − start` must equal the line
count, which is independently recorded. An inclusive range cannot be validated
without knowing the span length by another route. The 1-based base matches the
existing evidence list and every line citation in the corpus (all of which are
1-based), so no other document needs renumbering.

**Compatibility implications.** No digest changes (§8). The three affected table
rows change (§5). The verification report's §3 table becomes wrong in its `end`
column for A4/B9/D6 and must be superseded, not edited — it is a dated record.

**D. Reproducibility.** No U1 digest, U2 digest, U3 constant, behavioural test,
manifest or VER entry structure changes. See §8.

**E. Owner classification: 1 — pure editorial clarification.** The evidence list
already says "1-based" and "exclusive" and "canonical form". Step 11a states
which span those words attach to. No approved owner parameter is altered.

---

### 3.2 D2 — `marker_sha256` has no defined byte boundary

**Severity: high. Blocks VER execution.**

**A. Exact location**

| Artifact | Location | What it says |
|---|---|---|
| VER grammar | 03B-R1 §6 (`:110-135`) | Six named fields; field 5 is `marker_sha256=<HEX64>` |
| Field list | 03B-R1 §6 (`:119-127`) | `marker_sha256` is mandatory; "no additional mandatory marker fields may be invented" (§5, `:106-108`) |
| VER entry | proposal §3.3 (`:275-291`) | Payload field `marker_sha256` — "Digest of the REG marker verified" |
| Open issue | 03B-R1 §17 issue 3 (`:340-341`) | "Hash extraction boundaries for the owner response **and REG marker** remain unresolved." |
| Disposition | addendum §12.2 (`:464`) | "**Partially closed** — `PARAM-B.1` closed; extracted-card/whole-file remain **U1, U2**" |
| Unresolved list | addendum §11 (`:392-396`) | U1, U2, U3 only — no REG-marker item |

**B. Root cause**

03B-R1 §17 issue 3 named **two** unresolved boundaries: the owner response and
the REG marker. The addendum's §12.2 disposition table accounts for the first
(`PARAM-B.1`) and routes the extracted-card/whole-file boundaries to U1/U2 — but
the **REG-marker half is neither closed nor assigned an identifier**. It is
silently dropped from the disposition.

The U1–U3 proposal then scoped itself to exactly the three items in addendum §11
(U1, U2, U3). Since the REG-marker boundary was never given an identifier, it was
never in scope, and no section of the proposal defines it.

The result is a mandatory field with no derivation. `marker_sha256` is required
by 03B-R1 §6, required again by proposal §3.3, and cannot be computed. It is
undefined whether the digest covers:

- the `<!--` and `-->` delimiters;
- the leading indentation of the continuation lines in the §5 grammar;
- the internal newlines and their exact form;
- trailing whitespace before `-->`.

**C. Proposed correction**

Add a fourth digest class to the proposal, **U4 — REG-marker digest**, and add a
matching unresolved item to addendum §11. Proposed normative text:

> ### 4. U4 — REG-marker digest
>
> **4.1 Definition.** The **REG-marker digest** is the SHA-256 of the **canonical
> marker text** of one REG marker, and is the value carried by `marker_sha256` in
> the VER record (03B-R1 §6) and in the VER ledger entry (proposal §3.3).
>
> **Source object:** the REG marker as written at the canonical registration
> locus (`PARAM-A.1`), in the grammar of 03B-R1 §5 (`:88-92`).
>
> **Extraction procedure (normative):**
>
> 1. Read the source file as **raw bytes**.
> 2. **Reject** if the file begins with a UTF-8 BOM (`EF BB BF`).
> 3. Decode as **UTF-8, strict**.
> 4. **Canonicalise newlines:** `CRLF` → `LF`, then remaining `CR` → `LF`.
> 5. Locate the marker: the unique byte sequence beginning with `<!-- REG:v1 `
>    and ending with the first subsequent `-->`.
>    - zero matches → **fail closed** (`MISSING MARKER`);
>    - more than one match → **fail closed** (`AMBIGUOUS MARKER`).
> 6. The canonical marker text is the bytes from the opening `<!--` through the
>    closing `-->` **inclusive**, with **no** other change.
> 7. Encode as **UTF-8, no BOM**.
> 8. Compute **SHA-256**; render as **lowercase hexadecimal**.
>
> **Explicitly NOT applied:** NFC/NFD; stripping of leading indentation on
> continuation lines; collapsing of internal newlines; stripping of trailing
> whitespace before `-->`; removal of the delimiters.
>
> **4.2 Rationale.** The marker is a single syntactic object with explicit
> delimiters. Hashing the delimited object makes the boundary self-evident and
> satisfies `PARAM-B.4`'s requirement that the hashed byte span be stated. The
> delimiters are included because excluding them would make the digest
> insensitive to a change that alters the marker's syntactic identity (for
> example, a `<!--` replaced by a `<!---`).
>
> **4.3 Security implications.** Detects any change to the marker's content or
> delimiters. Does not detect changes outside the marker — that is U2's role.
> Is a content binding, not an authentication.
>
> **4.4 Source references.** 03B-R1 §5 (`:82-108`), §6 (`:110-135`), §17 issue 3
> (`:340-341`); addendum `PARAM-A.1` (`:87-91`), `PARAM-B.4` (`:160-163`),
> `PARAM-E.6` (`:267-270`).

And add to addendum §11:

> | **U4** | Byte definition of the **REG-marker digest** (`marker_sha256`) | 03B-R1 §17 issue 3 named the REG-marker boundary; addendum §12.2 disposed of the owner-response half only and assigned the extracted-card/whole-file halves to U1/U2, leaving the REG-marker half unassigned. | `marker_sha256` is uncomputable; no VER record can be written until U4 is resolved. |

And correct addendum §12.2 row 3 to:

> | 3. Hash extraction boundaries (`:340-341`) | **Partially closed** — `PARAM-B.1` closed (owner response); extracted-card/whole-file remain **U1, U2**; **REG-marker boundary remains open as U4** |

**Technical rationale.** The alternative — hashing the marker's *field values*
rather than its text — would require a canonical field serialisation that
`PARAM-E.6` explicitly forbids ("Values are not escaped, quoted, encoded, or
otherwise coerced into legality"). Hashing the delimited text avoids inventing a
serialisation and keeps the digest a byte-faithful binding to a locatable region,
consistent with U1's design.

**Compatibility implications.** Adds a fifth digest class. The addendum §4
opening states "**Four** digest classes are distinct" — that count becomes five,
which is an addendum amendment and therefore an owner act. No existing digest
changes. No REG marker exists yet, so no `marker_sha256` value is invalidated.

**D. Reproducibility.** No U1/U2/U3 value changes. There is no existing
`marker_sha256` to recompute — no REG marker has been written. A new test vector
is required once a marker exists; until then U4 can only be tested against a
synthetic marker fixture.

**E. Owner classification: 3 — new owner decision required.** `PARAM-B.4`
(`:160-163`) states that a byte boundary "may not be widened, narrowed, or
shifted without an explicit owner decision." Defining a new boundary is exactly
that. The owner must also decide whether to amend the addendum's "four digest
classes" count.

---

### 3.3 D3 — Load-bearing choices are absent from the open-decision list

**Severity: medium-high. The owner is asked to approve an incomplete decision set.**

**A. Exact location**

| Artifact | Location | What it says |
|---|---|---|
| Deviations list | proposal §5 (`:487-508`) | Five items "the reviewer should scrutinise rather than accept by default" |
| Item 4 | proposal §5 (`:502-504`) | The two extra VER fields (`card_sha256`, `file_sha256`) — "at the cost of two extra fields beyond the `VER:v1` grammar" |
| Item 5 | proposal §5 (`:505-508`) | "Canonical JSON is specified rather than RFC 8785 JCS… If the reviewer prefers JCS, it is a drop-in substitution." |
| Item 1 | proposal §5 (`:492-496`) | U1/U2 do not apply NFC while `PARAM-B.1` does |
| Open decisions | proposal §6 (`:512-527`) | **D-U3-1, D-U3-2, D-U3-3 only** |

**B. Root cause**

The proposal maintains two separate lists — §5 "Deliberate deviations and points
for reviewer attention" and §6 "Open sub-decisions for the owner" — with **no rule
connecting them**. Items flagged in §5 as choices the reviewer should not accept
by default were never promoted into §6. The owner reading §6 sees three open
decisions; the proposal actually contains at least seven.

The omissions that matter most are the ones that change a **digest**:

1. **VER record form** (proposal §3.1/§3.3 vs 03B-R1 §6). Whether the VER record
   is a `VER:v1` comment, a JSONL ledger entry, or both determines what is
   hashed, whether `card_sha256`/`file_sha256` exist at all, and whether
   `marker_sha256` is even a field. This is the single largest open question in
   the proposal and it is not in §6.
2. **The two extra VER fields** (§5 item 4). These are part of the entry's
   canonical JSON, so they change `entry_sha256`, the chain head, and therefore
   the checkpoint message bytes the owner signs.
3. **Canonical JSON vs RFC 8785 JCS** (§5 item 5). Directly determines
   `entry_sha256` for any entry containing a non-ASCII string or a number.
4. **The NFC regime** (§5 item 1). Currently inert — all three source files are
   already NFC-normalised — but it becomes live the moment a T16 edit introduces
   a non-NFC sequence, at which point U1 and U2 diverge from an NFC-applying
   implementation.

**C. Proposed correction**

Add a normative rule to §5, and add the missing decisions to §6.

> **§5 closing rule (new).** Any deviation in this section that changes a digest
> value, a digest's byte boundary, a record's field set, or a record's
> serialisation **must** also appear in §6 as a numbered open decision. A
> deviation that appears only in §5 is not approved by approving this proposal.

> **§6 additions.**
>
> - **D-U1-1 — Normalisation regime for U1/U2.** Options:
>   - (a) keep the current two-regime design: `PARAM-B.1` applies NFC, U1/U2 do
>     not (§5 item 1);
>   - (b) apply 03B-R1 §8 normalisation to U1/U2 as well, accepting that the
>     digests then correspond to no byte range in the file.
>   *Currently inert: all three source files are NFC-normalised. Becomes live on
>   the first non-NFC edit to T16.*
> - **D-U3-4 — VER record form.** Options:
>   - (a) the ledger entry **is** the VER record; 03B-R1 §6's six-field comment
>     grammar is superseded for VER and the ledger entry's field set governs;
>   - (b) a `VER:v1` comment is written **in addition** to the ledger entry, and
>     the proposal must define the relationship between the two;
>   - (c) the ledger entry carries the six `VER:v1` fields only, and
>     `card_sha256`/`file_sha256` are dropped.
>   *This decision determines whether `marker_sha256` is a field at all, and
>   therefore interacts with D2/U4.*
> - **D-U3-5 — VER entry field set.** Whether `card_sha256` and `file_sha256` are
>   retained (§5 item 4). Retaining them changes `entry_sha256` and the
>   checkpoint message bytes.
> - **D-U3-6 — Canonical JSON vs RFC 8785 JCS** (§5 item 5). Determines
>   `entry_sha256` for entries containing non-ASCII strings or numbers.

**Technical rationale.** The owner cannot approve a proposal whose open decisions
are understated. The §5/§6 split is a presentational convenience that has become
a correctness problem: §5 items 4 and 5 are described as "drop-in substitutions"
and "points for reviewer attention", which reads as *settled with a note* rather
than *open*. They are open.

**Compatibility implications.** No digest changes. The identifier scheme
`D-U1-1`, `D-U3-4`…`D-U3-6` is **proposal-local** and is not a T16 register
entry, not a `PARAM-*` identifier, and not a `PROTOCOL/D-*` decision. The owner
may renumber freely; no existing identifier is changed by this proposal.

**D. Reproducibility.** No U1/U2/U3 value changes. The *answers* to D-U3-5 and
D-U3-6 will change `entry_sha256` for future ledger entries, but no ledger entry
exists, so nothing is invalidated.

**E. Owner classification: 1 for the §5→§6 rule; 3 for each added decision.**
The rule is editorial — it makes an existing implicit obligation explicit. Each
added decision is a new owner decision.

---

### 3.4 D4 — Three of 23 test-vector line ranges are wrong

**Severity: medium. Causes a false reproducibility failure.**

**A. Exact location**

Proposal §4.1 (`:435-459`), column `Lines (canonical)`, rows A4, B9, D6.

**B. Root cause**

The column reports the **raw span's inclusive end** (equivalently the step-10
exclusive end) rather than the **canonical span's exclusive end** required by
§1.1's evidence list. This is D1's root cause manifesting as three concrete wrong
values.

Verified directly against T16:

| ID | Heading line | Content ends | Trailing lines stripped | Canonical span | Canonical exclusive end | Table says | Delta |
|---|---:|---:|---|---|---:|---:|---:|
| A4 | 168 | 179 | 180 blank, 181 `---`, 182 blank | 168–179 (12 lines) | **180** | 182 | **+2** |
| B9 | 322 | 333 | 334 blank, 335 `---`, 336 blank | 322–333 (12 lines) | **334** | 336 | **+2** |
| D6 | 473 | 484 | 485 blank, 486 `---`, 487 blank | 473–484 (12 lines) | **485** | 487 | **+2** |

The other 20 cards are correct because exactly one line is stripped from each, so
the raw inclusive end and the canonical exclusive end coincide numerically.

**Why this matters.** Proposal §1.3 (`:135-138`) tells the independent verifier to
"reproduce the 23 vectors in §4.1 … Any mismatch is a reproducibility failure and
blocks approval." A verifier that locates the span from the line column will hash
the wrong bytes for A4, B9 and D6 and report three false failures. A verifier that
implements §1.1 normatively gets the right answer. The table and the procedure
must agree.

**C. Proposed correction**

Rename the column and replace the three values. Full replacement table in §5.

> Column header: `Lines (canonical)` → **`Canonical span [start, end)`**
>
> Add a note beneath the table: "`start` and `end` are 1-based ordinals of the
> canonical span, half-open: `end − start` equals the canonical line count. The
> raw span before trailing-separator stripping is not recorded."

**Technical rationale.** The header change makes the convention visible at the
point of use, so a verifier cannot read the column as an inclusive range. The
`end − start = line count` identity gives the verifier a self-check before
hashing.

**Compatibility implications.** No digest changes. The `Bytes` and `SHA-256`
columns are already correct and describe the canonical span; only the line labels
change.

**D. Reproducibility.** No U1 digest, U2 digest, U3 constant, behavioural test,
manifest or VER entry structure changes. See §8.

**E. Owner classification: 1 — pure editorial correction.** The normative rule
and every digest are unchanged; three labels were wrong.

---

## 4. Exact proposed corrections

### 4.1 D1 — replacement text for proposal §1.1

Replace steps 10–11 and the evidence list with the text given in §3.1(C) above.
The replacement is self-contained: it defines the raw span, the canonical span,
the ordinal base (1-based), the interval form (half-open), and the validation
identity (`end − start = canonical line count`).

### 4.2 D2 — replacement text for a new proposal §4, plus addendum amendments

Add the new §4 "U4 — REG-marker digest" given in §3.2(C) above, renumbering the
existing §4–§7 to §5–§8. Amend addendum §11 (add U4) and §12.2 row 3.

### 4.3 D3 — replacement text for proposal §5 and §6

Add the §5 closing rule and the four §6 decisions given in §3.3(C) above.

### 4.4 D4 — replacement table

See §5 below.

### 4.5 Mandatory-field derivation register

The brief requires that every mandatory field's derivation source be defined
explicitly. The following register covers every field in every record the
proposal defines. **Fields marked ⚠ are not computable as specified.**

**REG marker — 03B-R1 §5, nine named fields**

| # | Field | Derivation source | Status |
|---:|---|---|---|
| 1 | `decision` | T16 canonical ID, `A1`–`A4`, `B1`–`B9`, `C1`–`C4`, `D1`–`D6` (T16 §3 `:87-116`) | Defined |
| 2 | `state` | Response axis value, `PENDING` or `SELECTED` (03B-R1 §3 `:48-51`) | Defined |
| 3 | `option` | The selected option label as written in the card | Defined |
| 4 | `owner_sha256` | `PARAM-B.1` owner-response digest | ⚠ **Boundary narrowed, not closed** — see §10 R3 |
| 5 | `confirmed` | Owner authorisation date, UTC `YYYY-MM-DD` (`PARAM-C.3`) | Defined |
| 6 | `recorded` | REGISTER execution date, UTC `YYYY-MM-DD` (`PARAM-C.3`) | Defined |
| 7 | `registrar` | `Claude Code` (`PARAM-F.2`) | Defined |
| 8 | `revision` | `PARAM-B.2` manifest digest | ⚠ **Uncomputable** — no manifest exists; grammar permits `UNRESOLVED` |
| 9 | `prev_state` | Prior response axis value | Defined |

**VER record — 03B-R1 §6, six named fields**

| # | Field | Derivation source | Status |
|---:|---|---|---|
| 1 | `decision` | As REG field 1 | Defined |
| 2 | `verifier` | `Claude Desktop` (`PARAM-F.3`) | Defined |
| 3 | `verified` | Actual verification date, UTC `YYYY-MM-DD` (`PARAM-C.1`) | Defined |
| 4 | `result` | `PASS` or `FAIL` (`PARAM-E.8`) | Defined |
| 5 | `marker_sha256` | **U4 REG-marker digest** | ⚠ **Undefined — D2** |
| 6 | `items_checked` | Integer count of the ten-item inventory (03B-R1 §7) | Defined, but **no bound stated** — see §10 R4 |

**VER ledger entry — proposal §3.1/§3.3**

| Field | Derivation source | Status |
|---|---|---|
| `seq` | Monotonic integer, genesis `0`, +1 per entry | Defined |
| `prev` | `entry_sha256` of entry `seq−1`; genesis constant for `seq=0` | Defined |
| `entry_type` | `GENESIS` or `VER` | Defined |
| `entry_sha256` | SHA-256 of the entry's canonical JSON bytes, excluding the terminating `LF` | Defined — **but see D-U3-6** |
| `card_sha256` | U1 digest of the card at verification time | Defined — **retention is D-U3-5** |
| `file_sha256` | U2 digest of the register at verification time | Defined — **retention is D-U3-5** |

**Genesis payload — proposal §3.2**

| Field | Derivation source | Status |
|---|---|---|
| `ledger_id` | Stable ledger identifier | ⚠ **Open — D-U3-2** |
| `created` | Actual creation date, UTC `YYYY-MM-DD` (`PARAM-C.1`) | Defined |
| `owner_key_fingerprint` | `SHA256:<base64>` of the owner Ed25519 public key (`PARAM-D.4`) | Defined |
| `protocol_sha256` | U2 of `docs/r6-registration-protocol-03b-r1.md` | Defined |
| `addendum_sha256` | U2 of the owner-parameter addendum | Defined |
| `t16_sha256` | U2 of the canonical decision register | Defined |

**Checkpoint message — proposal §3.4, five lines**

| Line | Derivation source | Status |
|---|---|---|
| `R6-VER-CHECKPOINT:v1` | Literal domain-separation tag | Defined |
| `ledger_id=<LEDGER_ID>` | As genesis `ledger_id` | ⚠ **Open — D-U3-2** |
| `seq=<N>` | `seq` of the highest-`seq` entry at checkpoint time | Defined |
| `chain_head=<HEX64>` | `entry_sha256` of that entry | Defined |
| `created=<YYYY-MM-DD>` | Actual checkpoint date, UTC (`PARAM-C.1`) | Defined |

**`allowed_signers` identity** — ⚠ **Open — D-U3-3.**

**Summary of undefined mandatory fields:** `marker_sha256` (D2, this proposal),
`owner_sha256` boundary (pre-existing, §10 R3), `ledger_id` (D-U3-2),
`allowed_signers` identity (D-U3-3), `items_checked` bound (§10 R4). Of these,
only `marker_sha256` is addressed by this proposal.

---

## 5. Updated U1 test-vector table

Only the line column changes. `Bytes` and `SHA-256` are carried forward unchanged
from proposal §4.1 — see §8 for why they cannot change.

| ID | Canonical span `[start, end)` | Bytes | SHA-256 |
|---|---|---|---|
| A1 | 123–135 | 767 | `70cb1ddeed5b84f17520e90ba69e4182e519a5998ec10747d9eb5f22c7353bc4` |
| A2 | 136–148 | 1022 | `afbb96c4ea74efd862d775ce49b32d637b22d0e1f746a352acd28d5209208e34` |
| A3 | 149–167 | 1763 | `9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b` |
| A4 | **168–180** | 683 | `ce9c8e2926efbb0a189d68ae050e1e9d052f013360467bd76ef56044ea6965d3` |
| B1 | 187–212 | 2410 | `b19da622ef05d57be53f0932714b51643ebb8a79cee81a43a92df07e034fa2f4` |
| B2 | 213–225 | 723 | `e041985cee5b4bcd1408c412a3d88b11ede018ce29d60231565c01a918fe3466` |
| B3 | 226–238 | 721 | `db9606a1d44ec430ba38937585802f85255b6bbd77960661695c72a03fc8c4b1` |
| B4 | 239–251 | 620 | `a7836a4847f15714e894d4c0e54eef054f0789aa537e6424959783b7bfb80d2d` |
| B5 | 252–270 | 1891 | `f39ef13072107af456090507b7d6538493460dc6616f6aac266fc9aceae6045e` |
| B6 | 271–295 | 2076 | `9c22e56afab5a367db13d451c04fdbb022b74a93d367b0bbc6963e0bf8907374` |
| B7 | 296–308 | 924 | `b1e497bf590185cbaaf370bfd59133c47fb4a9c7b6db38489e635917efc92fff` |
| B8 | 309–321 | 689 | `50afcf458560cb68994906bf2b9fcc195c33174c8ddba9a3c4466e07e6771dae` |
| B9 | **322–334** | 630 | `851a80438990ea0c6221c654821029a84b3411265d01679b8eb7c77a1ea6b88a` |
| C1 | 343–355 | 1354 | `071f1cb93a3b4f8489cad63c6d9f0e6cbd5606cb64a77364083bfdcf036312c5` |
| C2 | 356–368 | 800 | `10e53984d2a684283886872e7085ec0d63f7776235ccd92f9ec95e57f333442a` |
| C3 | 369–381 | 843 | `6bfeebbed8775506db300068733fcce8bdfeffa568febd1bbca06113946a4a3b` |
| C4 | 382–394 | 1071 | `51e4e7491f2333eee0c274dd2091ba5b9b4e8a4f35d7d73944d333ec27b19bab` |
| D1 | 399–412 | 858 | `62905f789fa0efa97fbf3abaaa34aa93fcd710347a3ea76e30172c9428cc014f` |
| D2 | 413–425 | 1038 | `77cb466bffba3f3d14195c009362b8bb20e5f130241fc47d778f5371aa54cdb2` |
| D3 | 426–446 | 1933 | `bf1c0075f445f3bbfbd7b1b7b302e5112dc7762f3037b44a00ebe3f9aac108ef` |
| D4 | 447–459 | 922 | `55a557ceb62ab25df55d73e3a456cf405a4e5f398ca3524ca4bd28b9a22e5c99` |
| D5 | 460–472 | 841 | `9fcda8d4f9a2b1a842f0afec2f370be71e398d5de5a694a141047fee6e4f5485` |
| D6 | **473–485** | 807 | `21c67a9aa474b442d98389e17ee49cc1dfa3f6db3087ad47f5caa27b5eec3109` |

**Self-check.** For every row, `end − start` equals the canonical line count
recorded in the independent re-derivation: A1 12, A2 12, A3 18, A4 12, B1 25,
B2 12, B3 12, B4 12, B5 18, B6 24, B7 12, B8 12, B9 12, C1 12, C2 12, C3 12,
C4 12, D1 13, D2 12, D3 20, D4 12, D5 12, D6 12. All 23 satisfy the identity.

**Three rows changed:** A4 `168–182` → `168–180`; B9 `322–336` → `322–334`;
D6 `473–487` → `473–485`.

---

## 6. Updated U2 vectors

**No change.** U2 hashes the whole canonical file, not a card span. None of the
four corrections touches the U2 procedure, the source files, or the byte
boundaries.

| File | Canonical bytes | SHA-256 |
|---|---:|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52782 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| `docs/r6-registration-protocol-03b-r1.md` | 12619 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 26782 | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` |

**Important consequence for D2 and D3.** If the owner adopts the D2 correction,
the addendum is amended, and **`addendum_sha256` changes** — because U2 hashes the
addendum file. The genesis entry's `addendum_sha256` field would then carry the
post-amendment digest, not `2ff885e3…`. The same applies to `protocol_sha256` if
the protocol is amended. This is not a defect; it is the intended behaviour of a
whole-file digest. It does mean **U3 cannot be executed against the current
digests if the addendum is amended first** — the genesis entry must be built from
the post-amendment digests. This ordering constraint is recorded in §10 R1.

---

## 7. U3 implications

| U3 element | Impact of the four corrections |
|---|---|
| Genesis constant `e893bd2c…d307` | **Unchanged.** It is `SHA-256("R6-VER-LEDGER-GENESIS:v1")`, independent of every correction. |
| Genesis `prev` | **Unchanged.** |
| Genesis `protocol_sha256` / `addendum_sha256` / `t16_sha256` | **Unchanged by D1/D4.** **Changed by D2/D3 if the protocol or addendum is amended** — see §6. |
| `entry_sha256` computation | **Unchanged by D1/D4.** **Determined by D-U3-5 and D-U3-6** if adopted. |
| Chain head / checkpoint message | **Unchanged by D1/D4.** **Determined by D-U3-5 and D-U3-6.** |
| `marker_sha256` in the VER entry | **Becomes computable** under D2/U4. |
| `ledger_id`, `allowed_signers` identity | **Still open** — D-U3-2, D-U3-3. Not resolved here. |
| Checkpoint cadence | **Still open** — D-U3-1. Not resolved here. |

**Dependency note.** U3 depends on U2 (the genesis entry carries three U2
digests). If D2 or D3 is adopted and the protocol or addendum is amended, U3 must
be executed against the amended files. U3 cannot be approved and executed
independently of that ordering.

---

## 8. Reproducibility results

### 8.1 What was and was not recomputed

**Revision 1 (superseded).** Command execution was unavailable in the session
that produced revision 1, so no SHA-256 was recomputed and no script was run.
Every digest value in §5 and §6 was carried forward from the two prior reports.

**Revision 2 — recomputed in full.** Command execution was available. A **third**
implementation was written from the normative prose of proposal §1.1 (U1), §2.1
(U2) and §3.2 (U3) — not from the verification report's Appendix A script and not
from the independent re-derivation — and run against the three source files at
baseline `08201da8`. Results in §8.5.

**Recomputed by direct inspection (revision 1, retained).** The line arithmetic
for all 23 cards was re-derived by reading T16 directly. The three disputed spans
(A4, B9, D6) were confirmed line by line: heading line, last content line, and
the three trailing lines (blank, `---`, blank) before the next heading. The
`end − start = line count` identity was checked for all 23 rows in §5.

### 8.2 Why no digest can change — a proof, not an assumption

The brief warns: "Do not silently preserve old digest values if the corrected
specification changes their meaning." The corrected specification does **not**
change any digest's meaning, and the reason is structural:

1. **A digest is a function of bytes, not of labels.** U1 hashes the canonical
   card text. D1 and D4 change only the *line ordinals recorded as evidence
   metadata*. The canonical card text for A4 is lines 168–179 — twelve lines,
   683 bytes — both before and after the correction. The table previously
   *labelled* that span `168–182`; the label was wrong, the span was not.
2. **The `Bytes` column is the independent witness.** For A4 the table records
   683 bytes. Twelve lines of A4's content cannot be 683 bytes if the span
   included lines 180–182 (a blank, a `---`, and a blank) — those add 6 bytes.
   The `Bytes` column already proves the hashed span excluded them, which is why
   the `SHA-256` column is correct and only the line label was wrong.
3. **D2 adds a digest class; it does not alter an existing one.** No REG marker
   exists, so no `marker_sha256` value exists to change.
4. **D3 adds open decisions; it does not alter a digest.** The answers to
   D-U3-5/D-U3-6 will determine future `entry_sha256` values, but no ledger entry
   exists.

Therefore: **0 of 23 U1 digests change; 0 of 3 U2 digests change; the U3 genesis
constant does not change; 0 of 6 behavioural assertions change; the canonical
manifest and VER entry structures are unchanged by D1 and D4, and changed only if
the owner adopts D2 or D3.**

### 8.3 Behavioural tests

The six assertions in proposal §4.4 are unaffected. None depends on the line
column. Two additions are proposed:

| Test | Expected | Status |
|---|---|---|
| Extract `A3` twice | identical digest | Unchanged |
| Extract `A3` from a CRLF-converted copy | identical digest | Unchanged |
| Extract a non-existent ID (`Z9`, `A5`) | fail closed (`MISSING CARD`) | Unchanged |
| Extract from a file with a duplicated card heading | fail closed (`AMBIGUOUS CARD`) | Unchanged |
| Whole-file digest of a CRLF-converted copy | identical to LF original | Unchanged |
| **Recorded span satisfies `end − start = line count`** | **true for all 23 cards** | **New — tests D1/D4** |
| **`marker_sha256` of a synthetic REG marker** | **reproducible across CRLF conversion** | **New — tests D2/U4, requires a fixture** |

### 8.4 What the `PARAM-F.3` verifier must still do

1. Recompute all 23 U1 digests, 3 U2 digests, the U3 constant, and the 6
   behavioural assertions from the source files.
2. Confirm the corrected `[start, end)` values in §5 against the source.
3. Confirm the `end − start = line count` identity for all 23 rows.
4. Confirm that the three corrected rows hash the same bytes as before — i.e.
   that the correction is label-only.
5. Independently assess whether the U4 definition in §3.2(C) is unambiguous.

### 8.5 Revision 2 — third-implementation recomputation (2026-11-06 23:47 UTC)

**Method.** Python 3.11, standard library only (`hashlib`, `re`, `tempfile`). The
U1 extractor was written from proposal §1.1's prose: fence masking, ATX heading
detection, span termination at the first heading of level ≤ L, and the
trailing-separator loop were each implemented from the text, not copied from
either prior script. Baseline confirmed at run time: `git rev-parse HEAD` =
`08201da8013a58b486d5fa2d6c46b36588a27781`, branch
`feat/sabiroute-routing-foundation`.

**Result: 33 / 33 assertions reproduce. 0 failures.**

| Group | Assertions | Result |
|---|---:|---|
| U1 extracted-card digests | 23 | **23 / 23 PASS** — digest, canonical byte count and `start` all match §5 |
| U2 whole-file digests | 3 | **3 / 3 PASS** — 52782 / 12619 / 26782 bytes; digests match §6 |
| U3 genesis constant | 1 | **PASS** — `e893bd2c…d307`, confirmed not 64 zeros |
| Behavioural assertions | 6 | **6 / 6 PASS** |

**Baseline byte facts (independently measured).** All three source files are
LF-only, BOM-free, with no lone CR, so raw-byte SHA-256 equals canonical SHA-256
for each — confirming the proposal §2.2 note.

**D1/D4 correction values confirmed against the source.** The canonical span
`[start, end)` computed from the normative procedure matches the corrected §5
table exactly for all three disputed cards:

| ID | Computed canonical span | §5 corrected value | Trailing lines stripped | Verdict |
|---|---|---|---:|---|
| A4 | `[168, 180)` | `168–180` | 3 | **MATCH** |
| B9 | `[322, 334)` | `322–334` | 3 | **MATCH** |
| D6 | `[473, 485)` | `473–485` | 3 | **MATCH** |

The other 20 cards strip exactly **1** trailing line each, which is why their raw
inclusive end and canonical exclusive end coincide — the accident described in
§3.1(B) and §3.4(B) is confirmed, not assumed.

**D1 identity confirmed.** `end − start` equals the canonical line count for all
23 rows (12, 12, 18, 12, 25, 12, 12, 12, 18, 24, 12, 12, 12, 12, 12, 12, 12, 13,
12, 20, 12, 12, 12).

**Behavioural assertions confirmed.** A3 extracted twice → identical; A3 from a
CRLF-converted copy → identical; U2 of a CRLF-converted copy → identical to the
LF original; `Z9` and `A5` → `MISSING CARD`; a duplicated `A3` heading →
`AMBIGUOUS CARD`.

**One imprecision found in §3.4(B) during recomputation.** §3.4(B) describes the
`Lines (canonical)` column as "the raw span's inclusive end (equivalently the
step-10 exclusive end)". The first clause is correct; the parenthetical is only
true under **0-based** indexing. In 1-based terms the column equals the raw
span's *inclusive* end, which is `raw_exclusive_end − 1` — for A1 the column is
135 while the 1-based step-10 exclusive end is 136. Since D1 exists precisely to
remove ordinal-base ambiguity, this parenthetical reintroduces it. It does not
affect any value in §5; the corrected table is right. Suggested wording: "the
raw span's inclusive end (the 0-based index of the next heading)".

**What this does not establish.** This is a third *registrar-side*
implementation. A misreading shared by the proposal author, both prior passes and
this one would survive all four. Only Claude Desktop (`PARAM-F.3`) can close that
gap (§10 R7).

---

## 9. Owner-decision requirements

| Correction | Classification | What the owner must do |
|---|---|---|
| **D1** — ordinal convention | **1 — pure editorial clarification** | Confirm the 1-based half-open `[start, end)` convention. No parameter changes. |
| **D2** — U4 REG-marker digest | **3 — new owner decision required** | Decide whether to adopt U4 as a fifth digest class, and whether to amend the addendum's "four digest classes" statement. `PARAM-B.4` requires an explicit owner decision to fix a byte boundary. |
| **D3** — open-decision list | **1 for the §5→§6 rule; 3 for each added decision** | Confirm the rule; then answer D-U1-1, D-U3-4, D-U3-5, D-U3-6. |
| **D4** — three line values | **1 — pure editorial correction** | Confirm the three corrected values. No parameter changes. |

**No correction is classification 2 or 4.** None falls within an already-approved
owner decision in a way that changes its substance, and none requires
reconsideration of an earlier owner decision. The closest case is D2: it adds a
digest class alongside `PARAM-B.3`'s existing classes, which is additive rather
than contradictory — but it does change the addendum's stated count of four, which
is why it is classified 3 rather than 2.

**Decisions this proposal does not make.** D-U3-1 (checkpoint cadence), D-U3-2
(`ledger_id` scheme) and D-U3-3 (`allowed_signers` identity) remain open and
unresolved. This proposal does not answer them, does not narrow them, and does not
recommend an option for any of them.

---

## 10. Remaining technical risks

**R1 — Amendment ordering invalidates the genesis digests.** If the owner adopts
D2 or D3 and the protocol or addendum is amended, `protocol_sha256` and
`addendum_sha256` change. The genesis entry must be built from the
**post-amendment** digests. Building it from the current values and amending
afterwards would produce a genesis entry that does not match the files it claims
to bind. **Mitigation:** fix the document set before genesis, and re-derive U2 at
the genesis act.

**R2 — `marker_sha256` remains uncomputable until U4 is adopted.** D2 proposes a
definition; it does not adopt one. Until the owner decides, no VER record can be
written. This is a hard block on verification, not a documentation gap.

**R3 — `owner_sha256` boundary is still not fully closed.** `PARAM-B.1` says the
digest covers "the exact canonical Owner response field value only" and excludes
surrounding prose — but it does not define the delimiter, the multi-line rule, or
whether the `A3: ` prefix is part of the value. A3's owner response spans two
lines with a markdown hard break at T16:163-164. This is the **only** digest the
REG marker actually carries, and it has no test vector. It is outside the four
defects in this proposal's scope, but it is a higher-consequence gap than D1 or
D4 and should be resolved before registration.

**R4 — `items_checked` has no stated bound.** The inventory is ten items
(03B-R1 §7). Nothing constrains the field to `0 ≤ n ≤ 10`, so a malformed record
with `items_checked=99` would parse. `PARAM-E.5` requires a strict parser; a
strict parser needs a bound.

**R5 — The NFC divergence is currently inert but not permanently so.** All three
source files are NFC-normalised today. The first non-NFC edit to T16 makes U1 and
U2 diverge from an NFC-applying implementation. D-U1-1 exists to force that
decision before it bites.

**R6 — The evidence binds untracked files.** The U2 digests bind three untracked
files. A `git clean`, a fresh clone, or a branch switch that discards untracked
files destroys the evidence the digests refer to. FAST-04 §2.4 records this as
Gate R6.0-D, **NOT MET**. The digests are currently *recoverable, not durable*.

**R6a — The working tree is no longer clean (found at revision 2).** The proposal
header, the verification report and the independent re-derivation all record the
baseline as "no tracked modifications, nothing staged". At revision 2 that is no
longer true: `git status --porcelain` reports **two tracked modifications** —
`src/sabiroute/api/completions.py` (19 lines changed) and
`tests/test_r6_settlement_integrity.py` (+161 lines). Neither is one of the three
U2-bound documents, so **no digest in §5 or §6 is affected**; the three source
files still hash to the values recorded. But the "clean tree" statement in the
prior reports is now stale and must not be repeated as current fact. Any future
registration evidence that asserts a clean tree must re-check it at the time of
the act.

**R7 — This proposal is not independent.** It was produced by the registrar
identity. A misreading shared between the proposal author, the two prior
verification passes, and this correction proposal would survive all four. Only
Claude Desktop (`PARAM-F.3`) can close that gap.

---

## 11. Recommended next action

1. **Owner reviews this proposal** and classifies each correction. D1 and D4 need
   only confirmation. D2 and D3 need decisions.
2. **Owner answers D-U3-4 first**, because it determines whether `marker_sha256`
   is a field at all, and therefore whether D2/U4 is needed in the form proposed.
3. **`PARAM-F.3` independent verification** of the U1–U3 proposal, using the
   corrected §5 table, reproducing all 33 assertions plus the two new behavioural
   tests in §8.3.
4. **Only after 1–3:** incorporate the accepted corrections into the proposal and
   addendum, re-derive U2 against the amended files, and then proceed to U3
   genesis under separate operational authority.

**Nothing in this document is incorporated. Nothing is approved. Nothing is
executed.**

**PROPOSAL — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**

---

## Dated provenance note — 2026-11-16 (F-04)

The closing banner immediately above, and the statement at `:882-883` that
"Nothing in this document is incorporated. Nothing is approved. Nothing is
executed", are **superseded in place** and retained verbatim as the historical
closing of the pre-WP-2 text. They are not rewritten, because editing a prior
record to match today is the failure mode this corpus names explicitly.

**What supersedes them.** The document's own header banner at `:3`, updated under
WP2-D12, now reads: *"PROPOSAL — OWNER-ADOPTED IN PART (WP2-D2 · WP2-D11);
INCORPORATED BY THE WP-2 EDIT PASS — NOT EXECUTED"*. The WP-2 edit pass did
incorporate the accepted corrections into the protocol and the addendum, so the
`:885` claim that nothing is incorporated is false as of that pass.

**What does not change.** The proposal remains **NOT EXECUTED**, and it remains
**not an approval**: `PARAM-F.3` independent verification of the incorporated
result is still outstanding, and no T16 decision is approved by incorporation.
"Owner-adopted in part" is narrower than "owner-approved" — it records that
WP2-D2 and WP2-D11 were adopted, not that the proposal as a whole was approved.

No owner approval, commit, signature or G7 grant attaches to this note. It
corrects a stale banner; it authorises nothing and executes nothing.
