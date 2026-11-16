# PH-1 DECISION RECORD — REGISTRATION LOCUS, U4 READING, O3 BOUNDARY

**Date:** 2026-11-16 · **Actor:** Claude Code (executioner) · **Branch:** `sec/deps-nov` @ `e0530e5`
**Work order:** WO-6 · **Gate:** none — this is *preparation*, not decision.

> **What this document is.** The material needed to answer **S-1**, **S-2** and **S-3** in
> `OWNER-SIGNATURE-SHEET.md`, gathered so the answers can be recorded the moment they are
> given. Everything quoted below is **verbatim**. Nothing is paraphrased.
>
> **What this document is not.** It is **not** a decision. It selects nothing, recommends
> nothing, and computes nothing. `marker_sha256` is **not** computed here — that is gated on
> S-3. **This document authorises no registration, instantiates no ledger, and is not an
> approval.**

Evidence labels (`CLAUDE.md` §2): `[M]` measured this session · `[R]` reported · `[I]` inferred
· `[?]` unverified.

---

# S-1 · ROW 3 — DESIGNATE THE O1–O5 REGISTRATION LOCUS (D-2)

## Candidates, measured 2026-11-16

| # | Candidate | Path | Bytes | Lines | Tracked |
|---|---|---|---:|---:|---|
| A | T16 decision option register | `docs/r6-t16-r6-decision-option-register.md` | 52,782 | 633 | **YES** |
| B | Registration protocol 03B-R1 | `docs/r6-registration-protocol-03b-r1.md` | 15,898 | 410 | **YES** |
| C | O3/O4/O5 owner decision pack | `docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` | 39,580 | 708 | **YES** |

All three are **tracked** `[M]` — verified with `git ls-files --error-unmatch` at `e0530e5`.
This is what makes S-1 answerable now: when D-2's recommendation was first written, no
document satisfied the "tracked" condition. That condition is now met for all 42 documents.

**No candidate is pre-selected here.** The three differ in what they are *for*: A is the
register of decisions, B is the procedure that would write into a locus, C is the provenance
record for the three decisions in question. A protocol that names its own file as the
registration locus is a different act from a register that holds the decisions themselves.

---

# S-2 · ROW 4 — ADOPT U4 READING R-A

## The proposed definition, quoted verbatim

From `docs/r6-close-final-03-r6.0-registration-go-no-go-and-u4-decision-pack.md` **§2.4**:

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
> - zero matches → **fail closed** (`MISSING MARKER`);
> - more than one match → **fail closed** (`AMBIGUOUS MARKER`).
> 6. The canonical marker text is the bytes from the opening `<!--` through the
>    closing `-->` **inclusive**, with **no** other change.
> 7. Encode as **UTF-8, no BOM**.
> 8. Compute **SHA-256**; render as **lowercase hexadecimal**.
>
> **Explicitly NOT applied:** NFC/NFD; stripping of leading indentation on
> continuation lines; collapsing of internal newlines; stripping of trailing
> whitespace before `-->`; removal of the delimiters.

## The readings table, quoted verbatim

Same document, the table at `:178-184`. The alternative to compare against R-A is **R-C**.

| Reading | Boundary | Bytes hashed | Digest |
|---|---|---:|---|
| **R-A** | whole marker, delimiters inclusive, **no other change** | 236 | `c69ea393c1f2760c6c338327dedcca4586cec1c80b8669fd0ff40198f743d8d7` |
| R-B | delimiters excluded | 227 | `850cfa268319be241d966528f3c593be668c813e1a36dd755976e27145d778f3` |
| R-B2 | field-value tail only, excluding the `REG:v1 ` prefix | 220 | `6045cb28fa4589f7b30c79152e821563257b2dd3ecb04a43a8c193edf63f776b` |
| **R-C** | delimiters inclusive, continuation indentation stripped | 231 | `7ee758ea70f698318afc2948bf61c1c12e6ddebb093db98995555f37991cc7c0` |
| R-D | delimiters inclusive, NFC applied | 236 | `c69ea393c1f2760c6c338327dedcca4586cec1c80b8669fd0ff40198f743d8d7` |
| R-E | delimiters inclusive, trailing space before `-->` stripped | 235 | `167937780a4db7921254fd996f076149b7bd0e01030393993070c3f24182aa03` |
| R-F | delimiters inclusive, internal newlines collapsed to a space | 231 | `500309d3d4782799bc4bb34c5209e172d2f3c6797edbe20dd04c96fdcd48d63b` |

**Recorded asymmetry `[M]`.** R-A is specified by a full eight-step normative procedure.
**R-C is specified only by its one-line table entry** — "delimiters inclusive, continuation
indentation stripped". It does not say how indentation is detected, what counts as a
continuation line, or what "stripped" means (all leading whitespace, or a fixed width). An
owner choosing R-C is choosing a boundary whose procedure is not yet written. That gap is
recorded here rather than filled in.

## The case for R-A, and the case against — quoted verbatim

Same document, **§2.5**:

> **For.** The marker is one syntactic object with explicit delimiters, so hashing
> the delimited object makes the boundary self-evident and satisfies `PARAM-B.4`'s
> requirement that the hashed byte span be stated. Including the delimiters makes
> the digest sensitive to a change that alters the marker's *syntactic identity* —
> a `<!--` replaced by `<!---` fails closed at the locator rather than silently
> hashing the same inner text (asserted by
> `test_u4_delimiter_mutation_fails_closed_at_locator`). Excluding them (R-B, R-B2)
> would require defining what "the content" is, which reopens exactly the delimiter
> question U4 exists to close.
>
> The alternative — hashing the marker's *field values* (R-B2) — would require a
> canonical field serialisation that `PARAM-E.6` (`:267-270`) explicitly forbids:
> "Values are not escaped, quoted, encoded, or otherwise coerced into legality."
> Hashing delimited text avoids inventing a serialisation and keeps the digest a
> byte-faithful binding to a locatable region, consistent with U1's design.
>
> **Against.** R-A is sensitive to whitespace that carries no meaning — the
> indentation of the continuation line in the §5 grammar. A marker reflowed by an
> editor, with no semantic change, produces a different digest. R-C and R-E exist
> precisely to eliminate that sensitivity. This is a real cost and the owner should
> weigh it: **R-A chooses "any byte change is detected" over "any formatting change
> is tolerated."** For a protocol whose entire purpose is tamper-evidence over an
> owner's decisions that is the right trade — but it is the owner's trade to make,
> not the registrar's.

---

# S-3 · ROW 5 — ANSWER O3, AND AUTHORISE `marker_sha256`

## O3's three alternatives, quoted verbatim

From `docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` **§2.2**:

> All three were computed in this session against the exact T16 bytes, applying
> §8 normalisation (CRLF→LF, CR→LF, NFC, strip leading/trailing, preserve internal,
> UTF-8 no BOM, SHA-256, lowercase hex).
>
> | Alt | Boundary | Bytes hashed | `owner_sha256` |
> |---|---|---|---|
> | **Alt-1** | Field **value** only; `A3: ` prefix **retained**; embedded LF preserved | **163** | `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149` |
> | **Alt-1b** | Field **value** only; `A3: ` prefix **stripped** | **159** | `e067ed95785ab190ca658cf1b05e9576d74c98e1b340da421a2fce046e769098` |
> | **Alt-2** | **Label + one space + value** (`**Owner response:** A3: …`) | **183** | `35de850fa80b00ecbe2c03b7846b489f3247c251351f53a9456f19176d926ccb` |
>
> All three reproduce the digests recorded in the prior session **exactly**. The
> byte-count arithmetic is internally consistent: `183 − 163 = 20` = length of
> `**Owner response:**` (19) + one space; `163 − 159 = 4` = length of `A3: `.

## The 161-byte hazard — NOT an alternative

Quoted verbatim from the same section. This is a **hazard**, not a fourth option:

> **Sensitivity probe (not an alternative, a hazard):** if an implementation strips
> the two hard-break spaces as *trailing* whitespace of line 1 rather than treating
> them as internal, the result is **161 bytes**,
> `fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6` — a fourth,
> wrong digest. Any implementation must be tested against this case.

**Read this carefully before choosing.** The 161-byte value is what you get when a plausible
implementation makes an off-by-interpretation error. It is recorded so that any future
`marker_sha256` computation can be tested *against* it — not so that it can be selected.

## Alt-3 — why it is not offered for A3

Quoted verbatim from the same section:

> **Alt-3 (single-line canonical form) is not viable for A3.** A3's value is
> irreducibly two lines. Collapsing it to one line would require an editorial
> decision (join with space? drop the second sentence?) that the approved rule does
> not license, and would change the recorded decision text — prohibited by
> `PARAM-A.6` (`docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md:118-125`).
> Alt-3 is therefore available only as a **prospective** rule for future
> registrations, not as a boundary for A3.

## Part 2 of S-3 — authorising the computation

Separate from the O3 boundary choice, S-3 also asks whether to authorise computing a
re-computable `marker_sha256` **once S-1 and S-2 are answered**. All three are needed before
F-01 can clear: a marker digest needs a locus to sit in (S-1), a reading that defines the byte
span (S-2), and a field boundary (S-3).

`marker_sha256` is **not computed in this document** `[M]` — no digest appears above that was
not quoted from the decision packs.

---

# WHAT THE OWNER MUST ANSWER

| Item | Question in one line |
|---|---|
| **S-1** | Which of A / B / C is the registration locus for O1–O5? |
| **S-2** | R-A (no other change) or R-C (indentation normalised)? |
| **S-3** | Alt-1 (163) / Alt-1b (159) / Alt-2 (183) — **and** whether to authorise `marker_sha256` once S-1 and S-2 are answered |

Answering all three is what clears **F-01** and makes R6.0 registration executable.

**Recorded for the owner, not resolved here:** the S-2 choice is between a fully specified
reading and a one-line one; the S-3 choice turns on whether the `A3: ` prefix belongs to the
decision or to its presentation. Neither is a technical question an agent can settle.

---

**NO DECISION RECORDED. NO OPTION PRE-SELECTED. `marker_sha256` NOT COMPUTED.
NO LEDGER INSTANTIATED. NO REGISTRATION EXECUTED. BL-22 UNSIGNED. G7 NOT GRANTED.**
