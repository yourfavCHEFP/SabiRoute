# R6-CLOSE-FINAL-03 — R6.0 Registration Go/No-Go and U4 Decision Pack

**Status:** DECISION PACK — **REGISTRAR-SIDE**. This document approves nothing,
incorporates nothing, executes nothing, signs nothing, and creates no REG record,
VER record, ledger entry, key or checkpoint.

**Date:** 2026-11-07 (UTC)

**Author identity:** Claude Code, which 03B-R1 §14 (`:268-280`) and addendum
`PARAM-F.2` (`:301-303`) designate as **registrar**. This is therefore **not** the
`PARAM-F.3` independent verification. See §4.1 — that limitation is binding and
is one of the reasons the verdict below is what it is.

**Subject:** (a) a binary go/no-go for the R6.0 registration act; (b) the
**U4** owner decision, presented for resolution.

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`.

**Baseline working-tree state (re-checked at authorship, not inherited):**
`git status --porcelain` reports **two tracked modifications** —
`src/sabiroute/api/completions.py` (19 lines, comment-accuracy only) and
`tests/test_r6_settlement_integrity.py` (+161 lines, new F4 test) — plus
untracked files. Neither modified file is one of the three U2-bound documents,
so **no digest in this document is affected**. The "clean tree" statements in
the proposal header, the verification report and the independent re-derivation
are **stale** and are not repeated here as current fact (correction proposal
R6a).

---

## 0. Bottom line

**R6.0 REGISTRATION: NO-GO.**

Three independent grounds, any one of which is sufficient:

1. **`owner_sha256` is uncomputable.** `PARAM-B.1` excludes surrounding prose but
   defines no delimiter, no `<ID>: ` prefix rule, no markdown-hard-break rule and
   no line-join rule. A3's owner response spans two lines. Five defensible
   readings yield five distinct digests. This is the **only** digest the REG
   marker actually carries, and A3 is the first intended registration.
   → **owner decision O3**.
2. **`marker_sha256` is uncomputable.** No byte boundary for the REG-marker
   digest is adopted. 03B-R1 §17 issue 3 named the REG-marker half; addendum
   §12.2 disposed of the owner-response half only, leaving the marker half
   unassigned. No VER record can be written without it. → **owner decision O1**.
3. **The genesis `entry_sha256` is not derivable.** It depends on the VER entry's
   field set, which is itself contradicted across three documents (six fields as
   a `VER:v1` comment per 03B-R1 §6; eight fields as a JSONL ledger entry per
   proposal §3.3), and on a `ledger_id` that does not exist. The chain head the
   owner would sign therefore cannot be constructed. → **owner decisions O4, O5**.

**What *is* established, and is not in doubt:** the digest layer is mechanically
executable and reproduces. 67 of 69 conformance assertions pass against the
source files at this baseline, including all 23 U1 card digests, all 3 U2
whole-file digests, the U3 genesis constant, the first U4 marker vectors in the
corpus, and every fail-closed behaviour. The arithmetic is sound. The
**specification around it is not executable**.

A NO-GO here is therefore **not** a finding that the work is wrong. It is a
finding that five questions are still open, all of which only the owner can
answer, and that no amount of further registrar-side computation can close them.

### 0.1 Relationship to the prior NO-GO verdicts

This is **not** a restatement of CLOSE-FINAL-01 §12 or CLOSE-FINAL-02, and it
supersedes neither. Those record **NO-GO for R6.0 closure and NO-GO for
architecture freeze**; FAST-04 §7 enumerates the explicit NO-GO conditions for
those acts. This document answers a different and later question: **may the
registration act itself proceed?**

The two verdicts are independent in the direction that matters. **Even if R6.0
closure and architecture freeze were both resolved to GO tomorrow, this
registration verdict would remain NO-GO**, because O1/O3/O4/O5 would still be
unanswered and `owner_sha256`, `marker_sha256` and the genesis `entry_sha256`
would still be uncomputable. The reverse is also true: resolving every decision
in this pack does not produce a closure GO. Neither verdict implies the other.

---

## 1. What was actually executed

Everything in this section was run at the baseline above. Nothing is inferred.

**Runner:** `python -m pytest` under the project interpreter `.venv/bin/python`
(Python 3.11.16). The system interpreter `miniforge3/envs/ml` was tried first and
**cannot** run `tests/test_r6_settlement_integrity.py` — it lacks `redis`, a
declared dependency in `pyproject.toml:38`. That is a pre-existing environment
gap, unrelated to any change in this package; results below are from `.venv`.

| File | Result |
|---|---|
| `tests/test_r6_registration_digest_conformance.py` | **67 passed, 2 skipped** (69 collected) |
| `tests/test_r6_settlement_integrity.py` | **6 passed** |
| Combined | **73 passed, 2 skipped** in 0.52 s |

### 1.1 Conformance census

| Group | Assertions | Result |
|---|---:|:--|
| U1 — card digest reproduces published vector | 23 | PASS |
| U1 — span identity `end − start = line count` | 23 | PASS |
| U1 — determinism (extract twice) | 1 | PASS |
| U1 — CRLF invariance | 1 | PASS |
| U1 — `MISSING CARD` fail-closed (`Z9`, `A5`) | 2 | PASS |
| U1 — `AMBIGUOUS CARD` fail-closed | 1 | PASS |
| U2 — whole-file digest reproduces published value | 3 | PASS |
| U2 — CRLF invariance | 3 | PASS |
| U3 — genesis constant | 1 | PASS |
| U4 — synthetic marker vector | 1 | PASS |
| U4 — newline invariance | 1 | PASS |
| U4 — sensitivity to indentation / content / trailing space | 1 | PASS |
| U4 — `MISSING MARKER` fail-closed | 1 | PASS |
| U4 — `AMBIGUOUS MARKER` fail-closed | 1 | PASS |
| U4 — delimiter mutation fails closed at locator | 1 | PASS |
| Harness — BOM rejected | 1 | PASS |
| Harness — invalid UTF-8 rejected | 1 | PASS |
| Provenance — source digests stable against the record | 1 | PASS |
| **T10 — owner-response digest single-valued** | 1 | **SKIP — BLOCKED on O3** |
| **T11 — genesis entry hash computable** | 1 | **SKIP — BLOCKED on O4, O5** |

**A skipped test in this suite is a finding, not a pass.** The two skips are the
executable form of blockers 1 and 3 above. They are not "pending work"; they are
the protocol asserting its own incompleteness, and they will not un-skip until
the owner answers.

### 1.2 Corrections carried into the assertions

The A4/B9/D6 rows assert the **corrected** canonical spans `[168,180)`,
`[322,334)`, `[473,485)` — not the original published labels, which report the
raw span's inclusive end and are wrong by +2 for those three cards. This is
correction proposal **D4**. All other 20 cards strip exactly one trailing line,
which is why their raw inclusive end and canonical exclusive end coincide. That
coincidence is now asserted as an identity (`end − start = line count`) rather
than assumed.

### 1.3 A correction to code comments, not to the protocol

`src/sabiroute/api/completions.py` carried a comment claiming the request-local
accounting ledger "drives" cancellation compensation. It does not: `finish()`,
`_compensate_all()` and `snapshot_persistence_failure()` read the
`budget_reserved` / `quota_reserved` / `quota_user_id` flags. The ledger is
observability and audit state. The comment now says so. **No behaviour changed.**
This is noted only because a reader comparing this baseline against the prior
reports will see the file listed as modified and should not read a protocol
change into it.

---

## 2. The U4 decision

### 2.1 What is being decided

`marker_sha256` is a required field of the VER record (03B-R1 §6) and of the VER
ledger entry (proposal §3.3). It is the digest of the REG marker that was
verified. **No definition of the hashed byte span exists.**

The gap is real and was named: 03B-R1 §17 issue 3 (`:340-341`) states that "hash
extraction boundaries for the owner response **and REG marker** remain
unresolved." Addendum §12.2 (`:464`) marks issue 3 **partially closed** —
`PARAM-B.1` for the owner response, U1/U2 for extracted-card and whole-file — and
**silently omits the REG-marker half**. It was never assigned a U-number. It is
uncomputable today.

`PARAM-B.4` (`:160-163`) is the binding constraint: a byte boundary "may not be
widened, narrowed, or shifted without an explicit owner decision." Defining one
is exactly that. **U4 is therefore an owner act, not a registrar act.**

### 2.2 Why the boundary must be decided rather than assumed

The marker is a single syntactic object with explicit delimiters. It nonetheless
admits at least seven defensible readings, and they produce **six distinct
digests**. Measured against the synthetic fixture in §2.3:

| Reading | What is hashed | Bytes | SHA-256 |
|---|---|---:|---|
| **R-A** | whole marker, delimiters inclusive, **no other change** | 236 | `c69ea393c1f2760c6c338327dedcca4586cec1c80b8669fd0ff40198f743d8d7` |
| R-B | delimiters excluded | 227 | `850cfa268319be241d966528f3c593be668c813e1a36dd755976e27145d778f3` |
| R-B2 | field-value tail only, excluding the `REG:v1 ` prefix | 220 | `6045cb28fa4589f7b30c79152e821563257b2dd3ecb04a43a8c193edf63f776b` |
| R-C | delimiters inclusive, continuation indentation stripped | 231 | `7ee758ea70f698318afc2948bf61c1c12e6ddebb093db98995555f37991cc7c0` |
| R-D | delimiters inclusive, NFC applied | 236 | `c69ea393c1f2760c6c338327dedcca4586cec1c80b8669fd0ff40198f743d8d7` |
| R-E | delimiters inclusive, trailing space before `-->` stripped | 235 | `167937780a4db7921254fd996f076149b7bd0e01030393993070c3f24182aa03` |
| R-F | delimiters inclusive, internal newlines collapsed to a space | 231 | `500309d3d4782799bc4bb34c5209e172d2f3c6797edbe20dd04c96fdcd48d63b` |

R-A and R-D coincide only because the fixture is already NFC-normalised. They
diverge the first time a marker contains a non-NFC sequence — the same latent
divergence already flagged for U1/U2 (independent re-derivation §5.7, correction
proposal R5). The U4 decision inherits that question; it does not create it.

### 2.3 The fixture

No REG marker exists in the corpus, so the vectors were computed against a
synthetic marker in the 03B-R1 §5 (`:88-92`) grammar:

```
<!-- REG:v1 decision=A3 state=SELECTED option=A owner_sha256=9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b
     confirmed=2026-11-06 recorded=2026-11-06 registrar=Claude Code revision=UNRESOLVED prev_state=PENDING -->
```

**Caveat, stated plainly:** the `owner_sha256` field carries **A3's card digest**
(`9dadd0f2…e3b`, U1 §4.1). That is a deliberate stand-in, not a correct value —
the real `owner_sha256` is the `PARAM-B.1` owner-response digest, which is
uncomputable (O3). **These U4 vectors validate U4 mechanics. They do not
validate a real marker, and must not be cited as if a compliant marker exists.**

### 2.4 The proposed definition (correction proposal §3.2(C), = reading R-A)

> **U4 — REG-marker digest**
>
> **4.1 Definition.** The REG-marker digest is the SHA-256 of the **canonical
> marker text** of one REG marker, and is the value carried by `marker_sha256` in
> the VER record (03B-R1 §6) and in the VER ledger entry (proposal §3.3).
>
> **Extraction procedure (normative):**
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

### 2.5 The case for R-A, and the case against

**For.** The marker is one syntactic object with explicit delimiters, so hashing
the delimited object makes the boundary self-evident and satisfies `PARAM-B.4`'s
requirement that the hashed byte span be stated. Including the delimiters makes
the digest sensitive to a change that alters the marker's *syntactic identity* —
a `<!--` replaced by `<!---` fails closed at the locator rather than silently
hashing the same inner text (asserted by
`test_u4_delimiter_mutation_fails_closed_at_locator`). Excluding them (R-B, R-B2)
would require defining what "the content" is, which reopens exactly the delimiter
question U4 exists to close.

The alternative — hashing the marker's *field values* (R-B2) — would require a
canonical field serialisation that `PARAM-E.6` (`:267-270`) explicitly forbids:
"Values are not escaped, quoted, encoded, or otherwise coerced into legality."
Hashing delimited text avoids inventing a serialisation and keeps the digest a
byte-faithful binding to a locatable region, consistent with U1's design.

**Against.** R-A is sensitive to whitespace that carries no meaning — the
indentation of the continuation line in the §5 grammar. A marker reflowed by an
editor, with no semantic change, produces a different digest. R-C and R-E exist
precisely to eliminate that sensitivity. This is a real cost and the owner should
weigh it: **R-A chooses "any byte change is detected" over "any formatting change
is tolerated."** For a protocol whose entire purpose is tamper-evidence over an
owner's decisions that is the right trade — but it is the owner's trade to make,
not the registrar's.

### 2.6 Recommendation

**Adopt R-A.** It is the only reading that leaves the boundary self-evident, it
is the reading the correction proposal already specifies and the conformance
suite already asserts, and its cost (whitespace sensitivity) falls on the
registrar who writes the marker, not on the owner who signs it.

If the owner prefers whitespace tolerance, **R-C** is the coherent alternative
and the only one worth considering: R-A with the continuation indentation
normalised, still binding the delimiters and the content. **R-E is not
recommended** — stripping trailing whitespace before `-->` makes the digest
insensitive to a change in the marker's own terminator padding while remaining
sensitive to everything else, which is an arbitrary line. **R-B, R-B2 and R-F
should be rejected**: each reopens a boundary question U4 exists to close.

### 2.7 Consequence of *not* deciding

`marker_sha256` stays uncomputable, no VER record can be written, no
verification can occur, and the registration act cannot begin. This is a hard
block on execution, not a documentation gap (correction proposal R2).

### 2.8 Consequence of adopting R-A

- Adds a **fifth digest class**. Addendum §4 (`:131`) opens "Four digest classes
  are distinct"; that count becomes five. **This is an addendum amendment and
  therefore a second owner act** (O2).
- No existing digest changes. No REG marker exists, so no `marker_sha256` value
  is invalidated.
- Addendum §12.2 row 3 must be corrected to name the REG-marker boundary as still
  open, rather than omitting it.
- **Ordering hazard (R1):** if the protocol or addendum is amended to adopt U4,
  `protocol_sha256` and `addendum_sha256` change. The genesis entry must be built
  from the **post-amendment** digests. Building it from current values and
  amending afterwards yields a genesis entry that does not match the files it
  claims to bind.

---

## 3. Owner decision register

Five decisions. Three (O3, O4, O5) block execution directly; two (O1, O2) are the
U4 adoption itself. Prior item labels are given so nothing is lost in
translation.

| ID | Decision | Gates | Prior label | Class |
|---|---|---|---|:--:|
| **O1** | Adopt the U4 REG-marker digest definition (§2.4, reading R-A) as a fifth digest class, with the boundary delimited as written | `marker_sha256` computable; VER record writable | D2 / U4 | **3** |
| **O2** | Amend addendum §4's "four digest classes" to five, and correct §12.2 row 3 to name U4 as still open | Genesis entry valid post-amendment | D2 (amendment half) | **3** |
| **O3** | Define the `PARAM-B.1` owner-response boundary: delimiter, `<ID>: ` prefix rule, markdown-hard-break trailing spaces, line-join | `owner_sha256` computable; A3 registrable | R3 / T10 | **3** |
| **O4** | Resolve the VER-record contradiction: `VER:v1` comment (six fields, 03B-R1 §6), JSONL ledger entry (eight fields, proposal §3.3), or both — and whether `card_sha256` / `file_sha256` exist | Field set; `entry_sha256`; whether `marker_sha256` is a field at all | §5.1 / D-U3-4 | **3** |
| **O5** | Fix `ledger_id` scheme and `allowed_signers` identity (and, still open, checkpoint cadence D-U3-1) | Genesis `entry_sha256`; the bytes the owner signs | D-U3-2, D-U3-3, D-U3-1 | **3** |

All five are **classification 3** — a new owner decision required. None falls
within an already-approved owner decision such that its substance changes
(classification 2), and none requires reconsideration of an earlier owner
decision (classification 4).

**Recommended answering order: O3 → O1 → O4 → O5 → O2.**

O3 first, because `owner_sha256` is the only digest the marker carries: if it is
undefined a marker cannot be authored, so U4 has no object to bind and O1 is
premature. O4 before O5, because whether `marker_sha256` is a field at all
determines whether O1 is needed *in the form proposed* — if the owner selects the
six-field comment form, the ledger entry and its extra fields disappear, and
`ledger_id` may become moot. O2 last, because it is the amendment that records
whatever O1 and O4 came to; amending first invalidates the genesis digests (R1).

**Decisions this pack does not make.** It does not answer O1–O5, does not
recommend an option for O4 or O5, and does not narrow them. Its single
recommendation is R-A for O1 (§2.6).

---

## 4. Blockers that are not owner decisions

These cannot be closed by any decision. They require a different act.

### 4.1 `PARAM-F.3` independent verification has not been performed

Every digest reproduction in the corpus — the verification report, the
independent re-derivation, the correction proposal's revision-2 pass, and this
document's own suite — was produced by **Claude Code**, the identity the protocol
designates as **registrar**. A misreading of §1.1/§2.1/§3.2/§3.2(C) shared
between the proposal author and every re-implementation survives all of them.
Only **Claude Desktop** can close that gap.

Nothing in this document satisfies `PARAM-F.3`, and it must not be cited as if it
did. The conformance suite raises the count of independent-style re-derivations
to four; it does not change the identity of any of them.

### 4.2 Gate R6.0-D — the evidence binds untracked files (NOT MET)

The U2 digests bind three **untracked** files:

- `docs/r6-t16-r6-decision-option-register.md`
- `docs/r6-registration-protocol-03b-r1.md`
- `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md`

A `git clean`, a fresh clone, or a branch switch that discards untracked files
destroys the evidence the digests refer to. FAST-04 §2.4 records this as Gate
R6.0-D, **NOT MET**, and that status has not changed. The digests are
*recoverable, not durable.* This was re-confirmed at authorship: all three files
still hash to their published U2 values, so the evidence is intact **right now**.

### 4.3 Prior findings still standing

Recorded elsewhere in the corpus and not re-litigated here: BL-22 **NOT SIGNED**
(CLOSE-FINAL-01 `:469`), RC-8 **UNMET** (`:502`), and all 23 approval records
remain `NOT APPROVED` (T16 `:57`, `:76`, `:575`). Operational registration
authority remains **DEFERRED**.

---

## 5. What would make this a GO

In order. Each step is a separate act with its own authority; none is implied by
this document.

1. **Owner answers O3** (owner-response boundary). → T10 un-skips.
2. **Owner answers O1**, adopting R-A or R-C. → §2.4 enters the proposal as §4.
3. **Owner answers O4** (VER record form and field set).
4. **Owner answers O5** (`ledger_id`, `allowed_signers`, checkpoint cadence).
5. **Addendum §4 / §12.2 amended** to record O1's outcome (O2).
6. **`PARAM-F.3` independent verification** by Claude Desktop, using the
   **corrected** A4/B9/D6 spans, reproducing the 33 assertions (23 U1 + 3 U2 +
   U3 + 6 behavioural) and the two proposed additions (span identity; U4 marker
   fixture), and independently assessing whether the adopted U4 definition is
   unambiguous.
7. **Corpus made durable** — the three U2-bound files tracked, so Gate R6.0-D can
   be met.
8. **U2 re-derived against the post-amendment files**, genesis built from those
   digests (R1), then — and only then — the registration act, under separate
   operational authority.

Steps 1–5 are owner acts. Step 6 requires an agent identity distinct from the one
that authored every prior pass. Step 7 is a repository act. **No registrar-side
computation can substitute for any of them.**

---

## 6. Risks carried forward

**R1 — Amendment ordering invalidates the genesis digests.** Adopting O1 or O2
changes `protocol_sha256` / `addendum_sha256`. Genesis must be built from
post-amendment digests. *Mitigation:* fix the document set before genesis and
re-derive U2 at the genesis act.

**R2 — `marker_sha256` remains uncomputable until O1.** Hard block on
verification, not a documentation gap.

**R3 — `owner_sha256` boundary not closed until O3.** Higher consequence than
U4: it is the digest the marker actually carries, and it has no test vector.

**R4 — `items_checked` has no stated bound.** Nothing constrains it to
`0 ≤ n ≤ 10` (the inventory is ten items, 03B-R1 §7), so `items_checked=99` would
parse. `PARAM-E.5` requires a *strict* parser; a strict parser needs a bound.
This is assigned to no O-decision above and should not be lost — it is a small
decision that belongs in the register below whichever O opens the parser rules.

**R5 — NFC divergence inert, not permanent.** All three source files are
NFC-normalised today (0 codepoints changed). The first non-NFC edit to T16 makes
U1/U2 diverge from an NFC-applying implementation, and makes R-A/R-D diverge for
U4. D-U1-1 exists to force that choice.

**R6 — Evidence durability.** See §4.2. Gate R6.0-D remains NOT MET.

**R7 — No pass in this corpus is independent.** See §4.1.

**R8 — U4's chain layer is entirely unexercised.** No key exists, no ledger
exists, no checkpoint has been signed. Proposal §3.4–§3.9 remain specified and
untested. This pack adds nothing to them: U4 covers one digest, not the chain.
Approving U4 must not be read as progress on U3.

**R9 — CITATION DEFECT (found at authorship, in a prior document).** The
independent re-derivation cites addendum §12.2 at `:463` for the disposition of
03B-R1 §17 issue 3. `:463` is in fact **row 2** (field escaping, `PARAM-E.6`);
the issue-3 row is at **`:464`**. This document cites `:464`. The error is
off-by-one and changes no conclusion — the row it points at is in the same table
and the disposition it describes is real — but it is recorded here because the
corpus treats citation resolution as evidence (§4.5 of that report resolves every
other citation correctly), and a later document inheriting `:463` would be
inheriting a wrong reference.

---

## 7. What this document does not do

- It does not approve, incorporate, adopt or execute U4, or any part of the
  U1–U3 proposal or the correction proposal.
- It satisfies **no** part of `PARAM-F.3`.
- It does not create a REG or VER record, a ledger, an entry, a key, a signature,
  or a checkpoint.
- It does not modify T16 or change any approval status.
- It does not mark any gate COMPLETE, and it explicitly records Gate R6.0-D as
  **NOT MET**.
- It does not authorise BL-22, R6.1, or any implementation.
- It does not supply operational registration authority, which remains
  **DEFERRED**.
- It does not answer O1–O5.
- It does not supersede CLOSE-FINAL-01 or CLOSE-FINAL-02; it records a verdict on
  a different act (§0.1).

**DECISION PACK — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**

**VERDICT: R6.0 REGISTRATION — NO-GO.**
