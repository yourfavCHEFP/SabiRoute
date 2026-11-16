# R6 — O3 / O4 / O5 — Smallest Canonical Corrections Proposal

**Status:** PROPOSAL — NOT APPLIED — NOT APPROVED
**Date:** 2026-11-07
**Repository:** `SabiRoute`
**Branch:** `feat/sabiroute-routing-foundation`
**HEAD:** `08201da8013a58b486d5fa2d6c46b36588a27781`

This document proposes the **smallest exact** corrections needed to align
`docs/r6-registration-protocol-03b-r1.md` §6 and
`docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` with the
owner's O3/O4/O5 selections recorded in
`docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §0.

**Nothing here is applied.** The canonical documents are unchanged. No REG or VER
record, ledger, key, signature, checkpoint, migration, deployment, staging,
commit or push is authorised by this document.

The corrections are deliberately narrow. They touch only:

- protocol §6 (the VER record grammar);
- addendum `PARAM-A.2` (VER ledger location);
- addendum `PARAM-A.4` (COMPLETE derivation);
- addendum `PARAM-B.1` (owner-response digest boundary, O3);
- addendum `PARAM-B.4` (new `PARAM-B.5`, canonical JSON and genesis, O4).

No other protocol section is rewritten.

---

## 1. Correction index

| # | File | Anchor | Decision | Kind |
|---|---|---|---|---|
| **C-1** | protocol | §6, line 112 | O5 | Replace container sentence |
| **C-2** | protocol | §6, lines 114–117 | O5 | Replace HTML-comment grammar with JSONL field table |
| **C-3** | protocol | §6, lines 130–135 | O5 | `VER record` → `VER ledger entry` |
| **C-4** | addendum | `PARAM-A.2`, lines 93–97 | O5 | Append JSONL realisation and checkpoint binding |
| **C-5** | addendum | `PARAM-A.4`, lines 105–110 | O5 | `VER:v1 record` → `VER ledger entry` |
| **C-6** | addendum | `PARAM-B.1`, lines 134–139 | O3 | Append owner-response boundary rule |
| **C-7** | addendum | after `PARAM-B.4`, line 163 | O4 | Insert new `PARAM-B.5` canonical JSON and genesis rule |

---

## 2. C-1 — protocol §6 container sentence

**Location:** `docs/r6-registration-protocol-03b-r1.md:112`

**Current text (exact):**

```text
Verification is a separate structured comment:
```

**Proposed text (exact):**

```text
Verification is a separate append-only ledger entry (`PARAM-A.2`), one canonical
JSON object per line. The HTML-comment `VER:v1` form is superseded and is not an
alternative authoritative ledger format.
```

**Rationale:** O5 selects the append-only JSONL ledger as authoritative and
explicitly retires the HTML-comment representation as an alternative.

---

## 3. C-2 — protocol §6 grammar block

**Location:** `docs/r6-registration-protocol-03b-r1.md:114-117`

**Current text (exact):**

````text
```text
<!-- VER:v1 decision=<ID> verifier=<ID> verified=<YYYY-MM-DD>
     result=<PASS|FAIL> marker_sha256=<HEX64> items_checked=<N> -->
```
````

**Proposed text (exact):**

```text
| Field | Type | Meaning |
|---|---|---|
| `decision` | string | Decision ID |
| `verifier` | string | Verifier identity |
| `verified` | string | Verification date, UTC `YYYY-MM-DD` |
| `result` | string | `PASS` or `FAIL` |
| `marker_sha256` | string | Digest of the REG marker verified |
| `items_checked` | integer | Count of the ten-item inventory checked |
| `card_sha256` | string | U1 digest of the card at verification time |
| `file_sha256` | string | U2 digest of the register at verification time |
| `seq` | integer | Monotonic sequence number; `0` is genesis |
| `prev` | string | `entry_sha256` of the previous entry |
| `entry_type` | string | `"VER"` |
| `entry_sha256` | string | SHA-256 of the canonical JSON bytes excluding the terminating `LF` |
```

**Rationale:** O5 requires each VER entry to carry `seq`, `prev` and
`entry_sha256`, and the proposal §3.3 adds `card_sha256` and `file_sha256`. The
six `VER:v1` field names are retained verbatim so `PARAM-A.4` continues to hold.

---

## 4. C-3 — protocol §6 COMPLETE sentence

**Location:** `docs/r6-registration-protocol-03b-r1.md:130-135`

**Current text (exact):**

```text
when a matching VER record exists with `result=PASS`, and the mandatory
post-COMPLETE read-back independently confirms the marker and verification
record. A missing, malformed, mismatched, or FAIL VER record makes COMPLETE
invalid and requires reconciliation. No automatic downgrade or repair is
permitted.
```

**Proposed text (exact):**

```text
when a matching VER ledger entry exists with `result=PASS`, and the mandatory
post-COMPLETE read-back independently confirms the marker and verification
entry. A missing, malformed, mismatched, or FAIL VER ledger entry makes COMPLETE
invalid and requires reconciliation. No automatic downgrade or repair is
permitted.
```

**Rationale:** The container changes from a comment to a ledger entry; the
derivation rule and the `result` domain are unchanged.

---

## 5. C-4 — addendum `PARAM-A.2`

**Location:** `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md:93-97`

**Current text (exact):**

```text
`PARAM-A.2` — **VER records belong in a separate append-only verification
ledger.**
Verification records are not written adjacent to T16 and are never co-located
with the REG record they verify. They live in a distinct append-only verification
ledger (integrity requirements: `PARAM-E.7`).
```

**Proposed text (exact):**

```text
`PARAM-A.2` — **VER records belong in a separate append-only verification
ledger.**
Verification records are not written adjacent to T16 and are never co-located
with the REG record they verify. They live in a distinct append-only verification
ledger (integrity requirements: `PARAM-E.7`), realised as the JSONL ledger of
proposal §3.1–§3.3: UTF-8, LF-terminated, one canonical JSON object per line,
hash-chained by `entry_sha256`, genesis at `seq = 0`. Every successfully appended
VER entry receives its own checkpoint under D-U3-1, bound to the ledger identity
and the corresponding ledger state.
```

**Rationale:** O5 names the ledger form and requires a checkpoint per appended
entry, bound to the ledger identity and state.

---

## 6. C-5 — addendum `PARAM-A.4`

**Location:** `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md:105-110`

**Current text (exact):**

```text
COMPLETE is a derived reporting state: it is valid only when a matching
`VER:v1` record has `result=PASS` **and** the mandatory post-COMPLETE read-back
independently confirms both records (03B-R1 §6:130-135, §10 step 8:212-214,
§15:282-300). It may never be written as an assertion.
```

**Proposed text (exact):**

```text
COMPLETE is a derived reporting state: it is valid only when a matching
VER ledger entry has `result=PASS` **and** the mandatory post-COMPLETE read-back
independently confirms both records (03B-R1 §6:130-135, §10 step 8:212-214,
§15:282-300). It may never be written as an assertion.
```

**Rationale:** Aligns the referent with the JSONL ledger entry while preserving
the derivation rule.

---

## 7. C-6 — addendum `PARAM-B.1` (O3)

**Location:** `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md:134-139`

**Current text (exact):**

```text
`PARAM-B.1` — **Owner-response digest.**
The digest is computed over the **exact canonical Owner response field value**
only. Surrounding prose, card titles, headings, notes, and mission commentary are
**not** hashed. The response text is not reinterpreted, reformatted, or
paraphrased before hashing. Normalization is exactly 03B-R1 §8 (03B-R1:171-185)
and nothing else; no additional or alternative normalization may be introduced.
```

**Proposed text (exact):**

```text
`PARAM-B.1` — **Owner-response digest.**
The digest is computed over the **exact canonical Owner response field value**
only. Surrounding prose, card titles, headings, notes, and mission commentary are
**not** hashed. The response text is not reinterpreted, reformatted, or
paraphrased before hashing. Normalization is exactly 03B-R1 §8 (03B-R1:171-185)
and nothing else; no additional or alternative normalization may be introduced.
The field label (`**Owner response:**`) is excluded. Any decision-ID prefix
present in the value (for example `A3: `) is **retained**. Embedded line breaks
are internal whitespace under §8 step 5 and are preserved exactly; they are never
collapsed, joined or stripped. Markdown hard-break spaces are not stripped merely
because they occur at the end of a visually wrapped line. An ambiguous extraction
boundary fails closed as `MALFORMED OWNER RESPONSE` and is never repaired.
```

**Rationale:** O3-Alt-1. The 161-byte stripped result is retained as a negative
conformance vector in the conformance suite, not in the normative text.

**Owner direction 2026-11-07 — prospective single-line rule excluded.** An
earlier draft of this correction appended a prospective rule requiring every
owner response registered from 2026-11-07 onward to be a single physical line.
The owner has directed that this rule is **not approved**: the O3 decision
authorises the exact-response-value boundary only and does not authorise a
mandatory response-format policy. The rule is removed. Multi-line responses
remain registrable under the Alt-1 boundary above. O3 is **not** reinterpreted as
Alt-3.

---

## 8. C-7 — addendum new `PARAM-B.5` (O4)

**Location:** `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md`,
inserted immediately after `PARAM-B.4` (line 163).

**Proposed text (exact):**

```text
`PARAM-B.5` — **Canonical JSON and genesis `entry_sha256`.**
Canonical JSON is defined by proposal §3.1: keys sorted ascending by Unicode code
point; no whitespace between tokens; separators `,` and `:`; RFC 8259 string
escaping with non-ASCII emitted as literal UTF-8 and `/` **not** escaped; integers
in decimal with no leading zeros, no `+` and no exponent; no BOM.
`entry_sha256` is the SHA-256 of these bytes **excluding** the terminating `LF`;
the on-disk line is the same bytes followed by exactly one `LF`. A line containing
a duplicate object key is malformed and is rejected as `MALFORMED LEDGER ENTRY`;
it is never resolved last-wins or first-wins. Omitted fields and explicit `null`
are distinct and are never equated. Field types are enforced; unsupported values
are rejected. `entry_sha256` is recomputed from the complete canonical payload and
a supplied digest is never trusted. The genesis payload is the nine-field set
defined by proposal §3.2's field table, including `t16_sha256`; `ledger_id` is the approved UUIDv4
(D-U3-2). The **normative worked example** is the fully specified nine-field
genesis record in decision pack §3.5/§3.6, whose concrete synthetic values are
reproducible: the canonical line is **508 bytes** with `entry_sha256` =
`ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28`, and the same
line plus one `LF` is **509 bytes** with
`452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe`. Proposal §3.2's
example is **illustrative and non-normative**; it is not a reproducibility
reference and must not be used as a test input.
```

**Rationale:** O4 adopts the nine-field genesis payload and §3.1 canonicalisation,
with the owner's safeguards: duplicate-key rejection, omitted-vs-null distinction,
type enforcement, recomputation, and the UUIDv4 `ledger_id`.

**Owner direction 2026-11-07 — worked-example reference corrected.** The owner's
O4 decision requires that the worked example be fully specified and reproducible,
and that placeholder values such as `YYYY-MM-DD` and `<LEDGER_ID>` are not
acceptable test inputs. Proposal §3.2's example still contains those placeholders,
so it cannot serve as the reproducibility reference. C-7 therefore names decision
pack §3.5/§3.6 — which supplies concrete synthetic values and a reference
computation — as the normative worked example, and marks §3.2's example
illustrative and non-normative. The approved genesis schema and canonicalisation
rules are unchanged by this correction.

---

## 9. Ordering hazard (R1) — binding

Applying C-1 through C-7 changes the bytes of both canonical documents. Therefore:

- `protocol_sha256` and `addendum_sha256` **change**.
- The genesis entry must be built from the **post-amendment** digests.
- Building genesis from the current values and amending afterwards yields a
  genesis entry that does not match the files it claims to bind.

This is the same R1 hazard recorded in
`docs/r6-close-final-03-r6.0-registration-go-no-go-and-u4-decision-pack.md` §6.
No genesis entry is built by this proposal.

---

## 10. What this proposal does not do

- It does not apply any correction. The canonical documents are unchanged.
- It does not create a REG or VER record, a ledger, an entry, a key, a signature,
  or a checkpoint.
- It does not satisfy `PARAM-F.3` independent verification.
- It does not mark Gate R6.0-D met.
- It does not authorise staging, committing, or pushing.
- It does not authorise registration, signing, checkpoint creation, R6.1,
  migrations, deployment, or production use.

**PROPOSAL — NOT APPLIED — NOT APPROVED**
