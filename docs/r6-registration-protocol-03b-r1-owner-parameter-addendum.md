# R6-REG-PROTOCOL-03B-R1 — Owner Parameter Addendum

**Status:** OWNER-APPROVED PROTOCOL PARAMETERS — NOT A REGISTRATION ACT, NOT AN
APPROVAL OF ANY DECISION, NOT AN EXECUTION AUTHORISATION

**Created:** 2026-11-06
**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`

**Addendum to:** `docs/r6-registration-protocol-03b-r1.md`
(410 lines; SHA-256
`59643d242effe3bca2a50ae4e52e86d28d9b5105465c446cab87e38fc69a6590`)

**Amendment 1 — 2026-11-07 (owner work order, at `1e69ada9`).** §4 now defines
**five** digest classes: `PARAM-B.3`'s U1/U2 byte definitions and `PARAM-B.5`
(genesis canonical JSON, O4) are incorporated, and `PARAM-B.6` (`marker_sha256`,
U4/O1) is added. `PARAM-A.7` records the VER-ledger entry schema (U3) and
`PARAM-D.9` the stable signer principal. §11's unresolved items are resolved by
these parameters. **This amendment changes this file's whole-document digest**, so
it is a U2-bound change: the genesis entry must be derived from the
**post-amendment** digests, never the reverse (correction proposal §9, R1). No
ledger, key, genesis entry, REG record, VER record or signature is created here.

**Amendment 2 — 2026-11-09 (Phase 1 provenance reconciliation, C-02).** Only the
documentary provenance of the O1/O2 owner selections is reconciled here. Amendment 1
above is preserved as the historical record, including its attribution of those
selections to a 2026-11-07 owner work order, which is retained and **not**
withdrawn. What is now stated more precisely is this: the 2026-11-07 owner
work-order artifact has **not been independently located** in the available
evidence, and the owner confirmed the O1/O2 selections in the current session on
**2026-11-09 UTC**. That confirmation is **not** an independently verified
transcript of any 2026-11-07 work order and **not** a new decision by the registrar;
the selections remain owner selections incorporated into the normative text, and
**no parameter value changes**. **This amendment changes this file's whole-file
digest**: the Amendment 1 digest `ab0bd89c…68ce891ea` (35,932 bytes, 611 lines) is
superseded for the current document bytes by the post-amendment digest, and any
genesis entry must be derived from the latter, never the reverse. No ledger, key,
genesis entry, REG record, VER record, marker or signature is created here.

This addendum records the protocol parameters the owner has approved. It closes
the documentary parameter gaps left open by protocol 03B-R1 §17. It does **not**
register any decision, create any REG or VER record, generate or sign any
manifest, create any signing key or checkpoint, or authorise the REGISTER
procedure.

---

## 1. Purpose and relationship to protocol 03B-R1

Protocol 03B-R1 defines the *procedure* for recording an owner response,
independently verifying it, and reporting lifecycle counts. It deliberately left
seven parameters unspecified (§17, "Open issues"). A procedure whose parameters
are undefined cannot be executed reproducibly, so this addendum supplies those
parameters from owner-approved decisions.

Relationship:

- **03B-R1 remains the governing procedure.** Its state model (§3), lifecycle
  counts (§4), marker grammars (§5, §6), inventory (§7), normalization (§8),
  RECORD/REGISTER procedures (§9, §10), recovery (§11), duplicate handling (§12),
  failure handling (§13), read-back (§15), and acceptance criteria (§16) are
  **unchanged** by this addendum.
- **This addendum is subordinate.** Where this addendum and 03B-R1 conflict,
  03B-R1's procedure governs and the conflict must be reported for reconciliation;
  it must not be resolved silently in either direction.
- **This addendum supplies parameters and their exact byte definitions only.** It
  adds no new procedure step, no new marker field, and no new axis value. The
  amendment of 2026-11-07 adds parameters (`PARAM-A.7`, `PARAM-B.5`, `PARAM-B.6`,
  `PARAM-D.9`) and resolves the U1–U4 byte/schema questions; it changes no marker
  grammar and no procedure step.

---

## 2. Authority and status of the addendum

**What this addendum is.** A record of owner-approved *protocol parameters*. The
owner stated these parameters directly in the instruction that authorised this
document (2026-11-06). Parameters sourced that way are classified `EXACT OWNER`.

**What this addendum is not.**

- It is **not** a decision card and does **not** enter the T16 23-decision
  register. The T16 canonical count remains **23** (T16:8, T16:13).
- It does **not** approve any T16 decision. All 23 approval records remain
  `NOT APPROVED` (T16:76, T16:57). Registration and parameter recording are not
  approval.
- It does **not** register any decision, and does **not** assert that any
  registration, verification, COMPLETE state, or gate acceptance has occurred.
- It does **not** authorise REGISTER execution (§10 below).
- It does **not** sign BL-22 or any closure act. BL-22 remains `NOT SIGNED`
  (CLOSE-FINAL-01:469, RC-8 `UNMET` at CLOSE-FINAL-01:502).
- It does **not** grant G7, Track A, R6.1, implementation, or deployment
  authority (T16:555-567).

**Namespace rule.** Parameters in this addendum are identified `PARAM-A` …
`PARAM-G`. These identifiers exist **only** in this document. They are not
decision cards, are not members of any decision-register family, do **not**
extend `PROTOCOL/D-1`…`PROTOCOL/D-5`, and must not be written as `D1`–`D7` or as
a bare `C-1`. No existing register family is created, merged, renamed, or
extended by this addendum.

**Provenance classes used throughout** (matching the T16 taxonomy at
T16:47, T16:55, T16:165):

| Class | Meaning |
|---|---|
| `EXACT OWNER` | Stated directly by the owner in the instruction authorising this addendum, 2026-11-06. |
| `MISSION-FRAMED` | An instruction-wrapper or structural requirement, not a direct owner utterance about protocol substance. |
| `DOCUMENTARY` | Already recorded in 03B-R1 or T16; restated here for locality, carrying no new authority. |
| `UNRESOLVED` | Referenced by the owner instruction but not defined in any recorded source. **Not guessed.** Listed in §11. |

---

## 3. Registration and verification record locations — `PARAM-A`

`PARAM-A.1` — **REG records belong adjacent to T16.**
A REG record for a decision is written adjacent to the canonical T16 register
entry it registers, in the canonical registration locus, under 03B-R1 §10 step 3.
It is not written into the T16 decision text, not into a decision card's prose,
and not into any other register.

`PARAM-A.2` — **VER records belong in a separate append-only verification
ledger.**
Verification records are not written adjacent to T16 and are never co-located
with the REG record they verify. They live in a distinct append-only verification
ledger (integrity requirements: `PARAM-E.7`) — realised as the JSONL ledger of
proposal §3.1–§3.3, one canonical JSON object per line.

`PARAM-A.3` — **Registration records selection/evidence status; it does not
constitute approval.**
Writing a REG record evidences that a selection was canonically recorded. It does
not approve, gate-accept, or complete the decision. This restates 03B-R1 §3
(03B-R1:58-60) and §10 (03B-R1:238-253).

`PARAM-A.4` — **COMPLETE must be derived from verified evidence, never manually
asserted.**
COMPLETE is a derived reporting state: it is valid only when a matching
VER ledger entry has `result=PASS` **and** the mandatory post-COMPLETE read-back
independently confirms both records (03B-R1 §6:157-161, §10 step 8:248-250,
§15:318-336). It may never be written as an assertion.

`PARAM-A.5` — **Preserve the distinction between EXACT OWNER,
CONVERSATION-DERIVED and MISSION-FRAMED decisions.**
Every registration must carry the provenance classification already recorded for
that decision in T16, and must not upgrade it. `MISSION-FRAMED` (e.g. A3,
T16:165) must never be presented as `EXACT OWNER`.

`PARAM-A.6` — **Do not alter T16 decision wording or canonical decision
identifiers.**
The canonical IDs remain exactly `A1`–`A4`, `B1`–`B9`, `C1`–`C4`, `D1`–`D6`
(23 total). The `ADR-2/C-1` versus `GROUP-C/C1` collision is governed by T16 §7
(T16:488-508): original identifiers preserved, no new decision ID created, bare
`C-1` never used. This restates 03B-R1 §17 (03B-R1:357-382).

`PARAM-A.7` — **VER-ledger entry schema (U3, incorporated 2026-11-07).**
The verification ledger is **append-only JSONL**: one canonical JSON object per
line (canonicalisation: `PARAM-B.5`), never reformatted, rewritten or deleted.
Each entry carries, at minimum, the **sequence number** (integer, contiguous from
the genesis entry), the **previous-entry hash**, and the **entry hash**
(`entry_sha256`). The genesis entry is **domain-separated** from ordinary entries
by the approved genesis constant `sha256("R6-VER-LEDGER-GENESIS:v1")`
(`e893bd2c…d307`); a genesis entry is never interchangeable with, or counted as, a
non-genesis entry. A **trusted checkpoint is written for every successfully
appended VER entry** (`PARAM-E.7`, `PARAM-D.3`). The immutable ledger identity is a
**UUIDv4**, generated at first execution and never regenerated. The ledger file,
its `ledger_id`, its genesis entry and its checkpoints do **not** exist and are
not created by this addendum (§10).

**Open-issue closure:** closes 03B-R1 §17 issue 1 (03B-R1:373); `PARAM-A.7`
supplies the ledger schema referenced by `PARAM-A.2` and `PARAM-E.7`.

---

## 4. Hash and revision contract — `PARAM-B`

Five digest classes are distinct and must never be conflated, substituted, or
recomputed across boundaries.

`PARAM-B.1` — **Owner-response digest.**
The digest is computed over the **exact canonical Owner response field value**
only. Surrounding prose, card titles, headings, notes, and mission commentary are
**not** hashed. The response text is not reinterpreted, reformatted, or
paraphrased before hashing. Normalization is exactly 03B-R1 §8 (03B-R1:171-185)
and nothing else; no additional or alternative normalization may be introduced.
`owner_sha256` in the REG marker (03B-R1 §5:89-100) carries this digest.

**Multi-line response rule (O3, owner-selected; incorporated 2026-11-07).** Where
the Owner response field spans more than one line, the hashed value is the **exact
extracted response value**: the `A3: `-style prefix is retained because it forms
part of the value, the embedded `LF` between lines is preserved, and §8's
normalisation is applied **without** any additional transformation. Markdown
hard-break spaces at the end of a visually wrapped line are **not** stripped. A3 is
the first intended registration: its canonical value is **163 bytes** with
`owner_sha256` = `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149`.
The **161-byte** form produced by stripping those two hard-break spaces hashes to
`fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6` and is retained as
a **negative conformance vector**; it is never the A3 value. An ambiguous extraction
boundary fails closed rather than selecting an interpretation. (The 161-byte digest
is reproduced at this amendment; the 163-byte digest is the value published in the
closure evidence.)

`PARAM-B.2` — **Revision digest.**
`revision=<SHA|UNRESOLVED>` in the REG marker carries the SHA-256 of the
**exact canonical manifest bytes**. The authoritative manifest is the sole
recorded source of the revision digest. No other file, transcript, or derived
artifact may supply it.

`PARAM-B.3` — **Extracted-card digest and whole-file digest.**
These are separate digest classes, distinct from `PARAM-B.1`, `PARAM-B.2`,
`PARAM-B.5` and `PARAM-B.6`. Their byte definitions are the owner-approved
technical direction incorporated 2026-11-07 (U1, U2). They are preserved exactly
as approved and must not be broadened.

**U1 — canonical card extraction.** SHA-256 over the **exact extracted canonical
card bytes**; UTF-8 encoding; **no BOM**; `LF` newline canonicalisation; **no**
NFC or NFD Unicode normalisation; zero-based card ordinal; one-based source line
numbers; zero-based, end-exclusive byte offsets; the separators between cards
**excluded**.

**U2 — whole-document digest.** SHA-256 over the **whole document**; `LF` newline
canonicalisation only; **no** Unicode normalisation; no removal of document
content; no other transformation.

**Asymmetry, stated deliberately.** `PARAM-B.1` applies 03B-R1 §8, which includes
an NFC step; U1 and U2 apply **no** Unicode normalisation. The two must never be
conflated, and §8 must not be applied to U1/U2. The 23 published card digests and
the 3 published whole-file digests reproduce under exactly the rules above.

`PARAM-B.4` — **No ambiguous normalization, no silent byte-boundary change.**
The byte span hashed for each class is fixed by its definition above and must be
stated in the registration evidence. A boundary may not be widened, narrowed, or
shifted without an explicit owner decision.

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
defined by proposal §3.2's field table, including `t16_sha256`; `ledger_id` is the
approved UUIDv4 (`D-U3-2`). The **normative worked example** is the fully specified
nine-field genesis record in decision pack §3.5/§3.6, whose concrete synthetic
values are reproducible: the canonical line is **508 bytes** with `entry_sha256` =
`ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28`, and the same
line plus one `LF` is **509 bytes** with
`452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe`. Proposal §3.2's
example is **illustrative and non-normative**; it is not a reproducibility
reference and must not be used as a test input.

`PARAM-B.6` — **REG-marker digest — `marker_sha256` (U4, O1).**
`marker_sha256` is the SHA-256 digest of the **complete canonical `REG:v1` marker
bytes**, including the literal opening `<!--` and the literal closing `-->`, and
**excluding** the terminating line break. Nothing before `<!--` or after `-->` is
hashed. It is a class distinct from `owner_sha256` (`PARAM-B.1`), which the marker
itself carries; `marker_sha256` digests the marker as a syntactic object and is
carried by the VER record. **No additional normalisation rule is introduced for
this digest**: only the canonical-byte handling already authorised by `PARAM-B.4`
applies, the definition of `owner_sha256` is unchanged, and `marker_sha256` must
never be substituted for, or derived from, `owner_sha256`.

**Open-issue closure:** closes 03B-R1 §17 issue 3 (03B-R1:340-341) for the
owner-response, extracted-card, whole-file, genesis and marker digests (U1, U2, U4
resolved; the fifth class is `PARAM-B.6`). Closes issue 5 (03B-R1:343) for the
revision referent; the manifest does not yet exist and is not created by this
addendum.

---

## 5. Date contract — `PARAM-C`

`PARAM-C.1` — **Actual execution dates only, as UTC calendar dates.**
Every date field records the actual event date, expressed as a UTC calendar date
(`YYYY-MM-DD`).

`PARAM-C.2` — **Never substitute an intended date for an actual execution date.**
The intended registration date `2026-11-06` (03B-R1:36-38) is not evidence that
any execution occurred and must never be written into an execution field.

`PARAM-C.3` — **Preserve the distinction between authorisation date and execution
date.**
`confirmed=<DATE>` records the owner's **authorisation** date. `recorded=<DATE>`
records the actual **REGISTER execution** date. They are distinct fields, may
differ, and must not be copied from one another.

`PARAM-C.4` — **Do not fabricate historical execution dates.**
Where an execution date is unknown, the field remains `UNRESOLVED` per the 03B-R1
§5 grammar (03B-R1:89-91). It is never back-filled with an assumed or intended
date.

**Open-issue closure:** closes 03B-R1 §17 issues 4 and 7 (03B-R1:342, 03B-R1:345-346).

---

## 6. Signature and trusted-checkpoint procedure — `PARAM-D`

The approved evidence-integrity checkpoint design is:

`PARAM-D.1` — **OpenSSH Ed25519 detached signatures.** Evidence integrity is
evidenced by detached Ed25519 signatures over the manifest.

`PARAM-D.2` — **Owner-controlled private signing key; never included or
exposed.** The private signing key is controlled by the owner and is never
written into the repository, the evidence corpus, any REG/VER record, or any
document. Its exposure is a failure, not a parameter.

`PARAM-D.3` — **SHA-256 manifest sidecar.** The manifest is accompanied by a
SHA-256 sidecar; the sidecar digest is the revision referent of `PARAM-B.2`.

`PARAM-D.4` — **Public verification key and fingerprint.** The public
verification key and its fingerprint are recorded as evidence so verification is
possible without the private key.

`PARAM-D.5` — **An offline preserved copy and an independent cloud copy.** The
manifest, sidecar, signature, and public key are preserved in (a) an offline copy
and (b) an independent cloud copy.

`PARAM-D.6` — **Independent verification using the public key only.** The
independent verifier (see `PARAM-F.3`) verifies signatures with the public key
only and never requires, requests, or handles the private key.

`PARAM-D.7` — **Cloud synchronisation is not immutable storage.** The independent
cloud copy must not be described, relied upon, or recorded as immutable or
tamper-proof. It is a copy, not a control.

`PARAM-D.8` — **Signatures detect change; independently preserved copies provide
recovery.** Signatures establish that content has not changed since signing. They
do not restore lost content; recovery depends on the independently preserved
copies in `PARAM-D.5`.

`PARAM-D.9` — **Stable signer principal (U3, incorporated 2026-11-07).**
The R6.0 signer principal is the stable identifier **`sabiroute-r6-owner`**. It
maps to the owner's **Ed25519 public key** (`PARAM-D.1`, `PARAM-D.4`), whose
fingerprint is recorded as evidence so verification needs no private key. The
principal identifier is fixed by this parameter; the key material, the public-key
fingerprint value, and every signature remain first-execution artefacts and are
not created by this addendum.

**Sequencing note (binding).** No manifest, signature, key, or checkpoint exists
at the time of this addendum, and none is created by it. This addendum defines
the contract only. The manifest's existence, signing, and checkpoint anchoring
are execution acts under §10 and remain unauthorised.

**Open-issue closure:** closes the unrecorded signature-scheme gap identified in
the prior reconciliation. The initial trusted-checkpoint **anchoring** procedure
is `UNRESOLVED` (see §11 U3).

---

## 7. Locking, parsing and persistence guarantees — `PARAM-E`

`PARAM-E.1` — **Single writer at a time.** At most one registration operation may
hold write authority over the canonical registration locus at any moment.

`PARAM-E.2` — **Exclusive lock; fail closed on contention.** Acquisition of write
authority requires an exclusive lock. If the lock cannot be acquired, the
operation stops and reports contention. It does not proceed, queue silently, or
degrade to a best-effort write.

`PARAM-E.3` — **No automatic stale-lock deletion.** A lock that appears stale is
never removed automatically.

`PARAM-E.4` — **Stale-lock recovery requires explicit authority and preserves
existing evidence.** Clearing a stale lock requires an explicit authorised act by
the recovery engineer (`PARAM-F.4`) and must preserve all existing evidence. It
must not delete, rewrite, or downgrade any REG or VER record.

`PARAM-E.5` — **Strict parser: reject malformed, duplicate, conflicting or
unsupported markers.** Any marker that is malformed, a duplicate, conflicting, or
of an unsupported version is rejected outright. This restates 03B-R1 §12 and §13
(03B-R1:229-266).

`PARAM-E.6` — **No escape syntax; out-of-grammar values are rejected.**
Values are not escaped, quoted, encoded, or otherwise coerced into legality. A
value that cannot be represented within the defined grammar is rejected as
malformed.

`PARAM-E.7` — **Append-only verification ledger with hash-chain integrity and
trusted checkpoint.** The VER ledger is append-only. Each entry is linked to its
predecessor by a hash chain, and the chain head is anchored to a trusted
checkpoint.

`PARAM-E.8` — **Preserve PASS and FAIL records.** Verification records with
`result=FAIL` are retained with the same integrity as `result=PASS`. A failure is
evidence, not something to be removed or overwritten.

`PARAM-E.9` — **Durable write/flush/fsync before reporting successful
persistence.** A write is reported as persisted only after the underlying data
has been flushed and fsynced (or the storage's equivalent durable barrier). A
process exit, a closed handle, or a file's appearance in a directory is not
evidence of persistence (03B-R1 §11:221-223).

`PARAM-E.10` — **Do not silently repair or rewrite evidence.** No automatic
repair, rewrite, reformat, or reconciliation is permitted. Any inconsistency is
reported as `INVALID / RECONCILIATION REQUIRED` (03B-R1 §13:265-266).

**Open-issue closure:** closes 03B-R1 §17 issues 2 and 6 (03B-R1:338-339,
03B-R1:344).

---

## 8. Role assignments and recovery procedure — `PARAM-F`

`PARAM-F.1` — **Owner: project owner.** The owner issues selections,
authorisations, and the closure signature. No role below may be exercised on the
owner's behalf in a way that manufactures an owner act.

`PARAM-F.2` — **Registrar: Claude Code.** Performs the RECORD and REGISTER
procedures (03B-R1 §9, §10) under separately confirmed operational authority
(§10 below). Records only the owner response and registration evidence.

`PARAM-F.3` — **Independent verifier: Claude Desktop.** Independently verifies the
canonical record and the applicable REG marker, writes the separate VER record
(03B-R1 §6), and performs the mandatory post-COMPLETE read-back (03B-R1 §15).

`PARAM-F.4` — **Recovery engineer: GitHub Copilot.** Performs interruption and
stale-lock recovery (`PARAM-E.4`) and reconciliation of conflicting evidence,
preserving all existing evidence.

`PARAM-F.5` — **Copilot's recovery role grants neither registrar nor
independent-verifier authority.** The recovery engineer must not write REG
records, must not write VER records, and must not perform the independent read-back
as verifier. The roles remain distinct identities; no identity may silently assume
another's role (03B-R1 §14:270-280).

**Recovery procedure (from `PARAM-E` and 03B-R1 §11).** On interruption: stop;
preserve all written evidence and the last known operation boundary; do not infer
completion from a partial write, process exit, file existence, or timestamp.
Recovery re-reads the canonical register, the REG record, and any VER record.
Conflicting or incomplete evidence is `INVALID / RECONCILIATION REQUIRED`. No
automatic downgrade, repair, rewrite, or deletion.

**Open-issue closure:** closes the previously unrecorded recovery-engineer role.
Registrar and verifier were already recorded at 03B-R1:272-273 and are restated
here as `DOCUMENTARY`.

---

## 9. Evidence privacy and retention exclusions — `PARAM-G`

`PARAM-G.1` — **Explicitly prohibited from any evidence corpus, record, or
document:**

- raw conversation archives;
- private keys, credentials, access tokens, or any secret;
- unnecessary personal information;
- unredacted machine-specific paths and session/transcript identifiers.

`PARAM-G.2` — **Retain only the minimum reproducible evidence:** the exact
response material required by the approved protocol, source references, digests,
and verification results.

`PARAM-G.3` — **No archive substitution.** A raw conversation archive is never
evidence of an owner response and never substitutes for canonical
owner-response recording (03B-R1 §2:33-34, PROTOCOL/D-5).

`PARAM-G.4` — **Redaction is not alteration of registered content.** Redacting
prohibited material from evidence must not change the canonical Owner response
field value that `PARAM-B.1` hashes.

---

## 10. Registration execution authority boundary

**This addendum does not authorise execution.** 03B-R1 §10 remains in force
verbatim:

> "The REGISTER procedure is not authorized by this draft. It may be executed
> only by the designated registrar under separately confirmed operational
> authority." (03B-R1:216-217)

Therefore:

- Recording these parameters does **not** close that gate and does **not**
  supply the "separately confirmed operational authority". That authority must be
  given by a distinct, explicit owner act.
- No registration, verification, COMPLETE state, or gate acceptance may be
  claimed on the strength of this addendum.
- The intended first registration remains A3 (PROTOCOL/D-4, 03B-R1:31-32),
  subject to all prerequisites and that separate authority.
- Reaching BL-22 readiness is a further, later state requiring Reading B's 13
  registrations (A1–A4, B1–B9), `C-02` propagation, and a baseline re-derived at
  the signature act (FAST-04:221-227, T16 §8:512-520). BL-22 is `NOT SIGNED`
  (CLOSE-FINAL-01:469, :502).

**Statement of current state: no REG or VER record exists; no manifest,
signature, key, or checkpoint exists; no decision is registered, verified,
complete, or gate-accepted.**

---

## 11. Items previously recorded as unresolved — resolution status

At the original authorship (2026-11-06) these items were referenced by the owner
instruction but **not defined in any recorded source**, and were recorded as
unresolved rather than guessed. The owner-approved technical direction incorporated
on 2026-11-07 (Amendment 1 above) supplies every definition. **Resolution of a
definition is not creation of an artefact**: each row's right-hand column names the
act that remains unauthorised.

| ID | What it was | Resolved by | Remaining execution act |
|---|---|---|---|
| **U1** | Byte definition of the **extracted-card digest** | `PARAM-B.3` U1 — exact card bytes, UTF-8, no BOM, `LF` canonicalisation, no NFC/NFD, zero-based ordinal, one-based source lines, zero-based end-exclusive offsets, separators excluded | None for the definition; first card digest of a real registration is produced at REGISTER time |
| **U2** | Byte definition of the **whole-file digest** | `PARAM-B.3` U2 — whole document, `LF` canonicalisation only, no Unicode normalisation, no content removal | None for the definition; the manifest must still be **frozen** first |
| **U3** | **Initial anchoring** of the ledger / VER-ledger genesis | `PARAM-A.7` (append-only JSONL, sequence, previous-entry hash, entry hash, genesis domain separation, per-entry checkpoint, UUIDv4 `ledger_id`), `PARAM-B.5` (canonical JSON and genesis `entry_sha256`), `PARAM-D.9` (signer principal) | **Ledger, `ledger_id`, genesis entry and checkpoints do not exist and are not created here** (§10) |
| **U4** | Byte definition of the **REG-marker digest** `marker_sha256` | `PARAM-B.6` — complete canonical marker bytes, delimiters inclusive, terminating line break excluded, no additional normalisation | None for the definition; no real marker exists, so only the synthetic conformance vector is in evidence |

**Not unresolved (recorded as implementation details to fix before first
execution, not policy decisions):** the exact filename/path of the VER ledger and
of the canonical REG locus, and the manifest's concrete serialisation format.
These must be fixed explicitly and recorded in the registration evidence at first
execution; they are preconditions, not open policy questions.

---

## 12. Source references and approval provenance

### 12.1 Parameter-to-source matrix

| Param | Subject | Provenance | Source |
|---|---|---|---|
| `PARAM-A.1` | REG records adjacent to T16 | `EXACT OWNER` | Owner instruction 2026-11-06 (previously unrecorded; supersedes 03B-R1:373 "not specified") |
| `PARAM-A.2` | VER records in separate append-only ledger | `EXACT OWNER` | Owner instruction 2026-11-06; O5 selection 2026-11-07 (§12.4) |
| `PARAM-A.3` | Registration ≠ approval | `DOCUMENTARY` | 03B-R1:58-60, :238-253 |
| `PARAM-A.4` | COMPLETE derived from evidence | `DOCUMENTARY` | 03B-R1:157-161, :248-250, :318-336 |
| `PARAM-A.5` | Provenance-class distinction preserved | `EXACT OWNER` + `DOCUMENTARY` | Owner instruction; T16:47, :55, :165 |
| `PARAM-A.6` | No alteration of T16 wording/IDs | `DOCUMENTARY` | 03B-R1:357-382; T16 §7:488-508 |
| `PARAM-A.7` | VER-ledger entry schema (U3) | `EXACT OWNER` — incorporated 2026-11-07 | Owner work order 2026-11-07 (O5); schema detail restated from `PARAM-E.7`, `PARAM-D.3` |
| `PARAM-B.1` | Owner-response digest = exact response field | `EXACT OWNER` + `DOCUMENTARY` | Owner instruction; normalization = 03B-R1 §8:207-221 |
| `PARAM-B.2` | Revision digest = manifest bytes | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-B.3` | Extracted-card & whole-file digests (U1, U2) | `EXACT OWNER` — incorporated 2026-11-07 (was `UNRESOLVED`) | Owner work order 2026-11-07; definitions reproduce the 23 card and 3 whole-file published vectors |
| `PARAM-B.4` | No ambiguous normalization / boundary change | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-B.5` | Canonical JSON and genesis `entry_sha256` (U3) | `EXACT OWNER` — incorporated 2026-11-07 | Owner work order 2026-11-07 (O4); correction proposal §8 (C-7) text incorporated |
| `PARAM-B.6` | `marker_sha256`, REG-marker digest (U4) | `EXACT OWNER` — incorporated 2026-11-07; owner re-confirmed 2026-11-09 (§12.4) | Owner work order 2026-11-07 (O1), **not independently located**; delimiters inclusive, terminating line break excluded, no additional normalisation |
| `PARAM-C.1` | Actual execution dates, UTC calendar | `EXACT OWNER` | Owner instruction; 03B-R1:36-38 |
| `PARAM-C.2` | No intended-date substitution | `EXACT OWNER` + `DOCUMENTARY` | Owner instruction; 03B-R1:36-38 |
| `PARAM-C.3` | Authorisation date ≠ execution date | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-C.4` | No fabricated historical dates | `EXACT OWNER` + `DOCUMENTARY` | Owner instruction; 03B-R1 §5 grammar :89-91 |
| `PARAM-D.1` | OpenSSH Ed25519 detached signatures | `EXACT OWNER` | Owner instruction 2026-11-06 (previously unrecorded) |
| `PARAM-D.2` | Owner-controlled private key, never exposed | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-D.3` | SHA-256 manifest sidecar | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-D.4` | Public key and fingerprint recorded | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-D.5` | Offline copy + independent cloud copy | `EXACT OWNER` | Owner instruction; durability driver CLOSE-FINAL-02:45-65 |
| `PARAM-D.6` | Verify with public key only | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-D.7` | Cloud sync is not immutable storage | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-D.8` | Signatures detect change; copies enable recovery | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-D.9` | Stable signer principal `sabiroute-r6-owner` → owner Ed25519 public key (U3) | `EXACT OWNER` — incorporated 2026-11-07 | Owner work order 2026-11-07 |
| `PARAM-E.1` | Single writer | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-E.2` | Exclusive lock, fail closed on contention | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-E.3` | No automatic stale-lock deletion | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-E.4` | Stale-lock recovery requires authority, preserves evidence | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-E.5` | Strict parser rejects bad markers | `DOCUMENTARY` | 03B-R1 §12:229-248, §13:250-266 |
| `PARAM-E.6` | No escape syntax; reject out-of-grammar | `EXACT OWNER` | Owner instruction (previously 03B-R1:374-375 unresolved) |
| `PARAM-E.7` | Append-only ledger, hash chain, trusted checkpoint | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-E.8` | Preserve PASS and FAIL | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-E.9` | Durable flush/fsync before success | `EXACT OWNER` | Owner instruction; 03B-R1:221-223 |
| `PARAM-E.10` | No silent repair/rewrite | `DOCUMENTARY` | 03B-R1 §11:227, §13:265-266 |
| `PARAM-F.1` | Owner | `DOCUMENTARY` | 03B-R1 §14:270-280 |
| `PARAM-F.2` | Registrar: Claude Code | `DOCUMENTARY` | 03B-R1:272 |
| `PARAM-F.3` | Independent verifier: Claude Desktop | `DOCUMENTARY` | 03B-R1:273 |
| `PARAM-F.4` | Recovery engineer: GitHub Copilot | `EXACT OWNER` | Owner instruction 2026-11-06 (previously unrecorded) |
| `PARAM-F.5` | Recovery role ≠ registrar/verifier | `EXACT OWNER` + `DOCUMENTARY` | Owner instruction; 03B-R1:275-276 |
| `PARAM-G.1` | Prohibited evidence categories | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-G.2` | Minimum reproducible evidence only | `EXACT OWNER` | Owner instruction 2026-11-06 |
| `PARAM-G.3` | No archive substitution | `DOCUMENTARY` | 03B-R1:33-34; PROTOCOL/D-5 |
| `PARAM-G.4` | Redaction ≠ alteration of hashed content | `EXACT OWNER` | Owner instruction; consistency with `PARAM-B.1` |

`MISSION-FRAMED` applies to this document's **structure** (§1–§12 and the
matrix), which derives from the mission brief, not from an owner utterance about
protocol substance. No parameter above is mission-framed.

### 12.2 Protocol §17 open-issue disposition

| 03B-R1 §17 issue | Disposition by this addendum |
|---|---|
| 1. REG/VER operational locus unspecified (`:373`) | **Closed** — `PARAM-A.1`, `PARAM-A.2` |
| 2. Field escaping unspecified (`:374-375`) | **Closed** — `PARAM-E.6` |
| 3. Hash extraction boundaries (`:376-377`) | **Closed** — `PARAM-B.1` (including the multi-line rule), `PARAM-B.3` (U1, U2) and `PARAM-B.6` (U4, `marker_sha256`); **U1, U2 and U4 are no longer open** |
| 4. Date semantics (`:378`) | **Closed** — `PARAM-C.1`…`C.4` |
| 5. Revision semantics/source (`:379`) | **Closed** — `PARAM-B.2` (referent defined; manifest not yet instantiated) |
| 6. Marker parsing/persistence (`:380`) | **Closed** — `PARAM-E.5`, `PARAM-E.7`…`E.10` |
| 7. Intended date, no execution (`:381-382`) | **Closed** — `PARAM-C.2`, `PARAM-C.4` |

### 12.3 Cited sources (current line numbers, verified 2026-11-06)

- `docs/r6-registration-protocol-03b-r1.md` — 410 lines, SHA-256
  `59643d24…69a6590`. §2:23-42, §5:82-108, §6:110-171, §8:207-221,
  §10:238-253, §11:255-263, §12:265-284, §13:286-302, §14:304-316,
  §15:318-336, §16:338-355, §17:357-382.
- `docs/r6-t16-r6-decision-option-register.md` — canonical 23 decisions (:8,
  :13, :76, :575); provenance classes (:47, :55, :165); §7 identifier collision
  (:488-508); §8 `C-02` Reading B (:512-520); §10 authority boundary
  (:555-567).
- `docs/r6-fast-04-r6.0-closure-architecture.md` — N9/BL-22 (:160); Gate
  R6.0-C3, 13 registrations under Reading B (:221-227).
- `docs/r6-close-final-01-r6.0-closure-package.md` — BL-22 `NOT SIGNED` (:469);
  RC-8 `UNMET` (:502).
- `docs/r6-close-final-02-r6.0-closure-reverification-2026-11-05.md` —
  durability finding (:45-65).

### 12.4 Approval provenance statement

The parameters marked `EXACT OWNER` were stated by the project owner in the
instruction authorising this addendum, dated **2026-11-06**. They are recorded
here at that classification and **no higher**. This addendum asserts no owner
approval beyond that instruction, no approval of any T16 decision, no
registration, no verification, no manifest, and no signature.

**Amendment 1 provenance (2026-11-07).** The U1/U2/U3 byte and schema definitions,
`PARAM-B.5` (O4), `PARAM-B.6` (O1/U4) and `PARAM-A.7`/`PARAM-D.9` were incorporated
from the owner's R6.0 closure work order of 2026-11-07, which records the owner's
selection of O1, O2 and the U1–U4 technical direction. They are recorded as
**owner selections incorporated into the normative text**, not as a new decision by
the registrar and not as an independently verified transcript. O3's multi-line rule
was already owner-recorded on 2026-11-07 and is incorporated here in the same class.
This amendment approves no T16 decision, registers nothing, verifies nothing,
creates no ledger, key, marker or signature, and does not authorise REGISTER
execution (§10).

**Phase 1 provenance reconciliation (2026-11-09, C-02).** The paragraph above is
retained unchanged as the historical Amendment 1 record: this document previously
attributed the O1/O2 selections, `PARAM-B.5` (O4), `PARAM-B.6` (O1/U4), `PARAM-A.7`,
`PARAM-D.9` and the U1–U4 technical direction to a 2026-11-07 owner R6.0 closure
work order. That attribution stands as history and is **not** withdrawn. Two facts
are now stated explicitly. First, the 2026-11-07 owner work-order **artifact has not
been independently located** in the available evidence, so no citation to it above
should be read as independent verification of its contents. Second, the owner
confirmed the O1/O2 selections in the current session on **2026-11-09 UTC**, and
that confirmation is the nearest available evidence for those selections. It is
**not** an independently verified transcript of the 2026-11-07 work order, and it is
**not** a new decision by the registrar. The distinction retained from Amendment 1
therefore continues to hold exactly as before: these are **owner selections
incorporated into the normative text**, recorded at that classification and **no
higher**. This reconciliation reopens no selection, changes no parameter value,
approves no T16 decision, registers nothing, verifies nothing, creates no ledger,
key, marker, genesis entry or signature, and does not authorise REGISTER execution
(§10).

**N1-O5 provenance reconciliation (2026-11-16).** The append-only JSONL verification
ledger recorded at `PARAM-A.2` and `PARAM-A.4` was selected by the owner on
**2026-11-07** as decision **N1-O5**: the settled finding that the append-only JSONL
ledger is the authoritative VER representation, and that the HTML-comment VER form is
**not** an alternative authoritative ledger format. `PARAM-A.2` realises the form;
`PARAM-A.4` derives COMPLETE from it. As with Amendment 1, this is recorded as an
**owner selection incorporated into the normative text**, not as a new decision by the
registrar and not as an independently verified transcript. The 2026-11-07 owner
work-order artefact **has not been independently located** in the available evidence
(see the Phase 1 paragraph above); this note therefore records the owner's selection
and cites no located instrument. It approves no T16 decision, registers nothing,
verifies nothing, creates no ledger, key, marker, genesis entry or signature, and does
not authorise REGISTER execution (§10).

---

**OWNER-APPROVED PROTOCOL PARAMETERS. NOT A REGISTRATION ACT. NOT AN APPROVAL OF
ANY DECISION. NOT AN EXECUTION AUTHORISATION. BL-22 REMAINS UNSIGNED.**

---

## 13. Dated provenance notes

### 2026-11-16 — protocol line anchors re-derived (F-06)

Finding F-06 records that this addendum cites protocol line anchors that no longer
resolve. The cause is that `docs/r6-registration-protocol-03b-r1.md` grew from 348
to 384 lines during the WP-2 edit pass, and to 410 lines on 2026-11-16 when §18
(the `VER:v1` deferral note, F-03) was appended. Every protocol anchor below was
re-derived by locating the cited **content** in the current protocol, not by
applying a fixed offset. The superseded values are retained here as history; the
citations in §3 and §12.1 were updated in place.

| Locus | Superseded | Current | Content the anchor must reach |
|---|---|---|---|
| §3 `PARAM-A.3`; §12.1 `PARAM-A.3` | `:208-214` | `:238-253` | §10 REGISTER procedure ("Do not mark a gate accepted") |
| §3 `PARAM-A.4`; §12.1 `PARAM-A.4` | `§6:130-135` | `§6:157-161` | §6 "independently confirms the marker and verification record" |
| §3 `PARAM-A.4`; §12.1 `PARAM-A.4` | `§10 step 8:212-214` | `§10 step 8:248-250` | §10 step 8, the `VER:v1` / `result=PASS` condition |
| §3 `PARAM-A.4`; §12.1 `PARAM-A.4` | `§15:282-300` | `§15:318-336` | §15 post-COMPLETE read-back |
| §3 `PARAM-A.6`; §12.1 `PARAM-A.6` | `:325` | `:357-382` | §17 explicit exclusions and non-authorisations |
| §3 open-issue closure; §12.1 `PARAM-A.1` | `:337` | `:373` | §17 open issue 1, REG/VER operational locus |
| §12.1 `PARAM-B.1` | `§8:171-185` | `§8:207-221` | §8 hash normalization |
| §12.2 §17 disposition table | `:337` | `:373` | §17 open issue 1 |
| §12.2 §17 disposition table | `:338-339` | `:374-375` | §17 open issue 2 |
| §12.2 §17 disposition table | `:340-341` | `:376-377` | §17 open issue 3 |
| §12.2 §17 disposition table | `:342` | `:378` | §17 open issue 4 |
| §12.2 §17 disposition table | `:343` | `:379` | §17 open issue 5 |
| §12.2 §17 disposition table | `:344` | `:380` | §17 open issue 6 |
| §12.2 §17 disposition table | `:345-346` | `:381-382` | §17 open issue 7 |

`03B-R1:58-60` (§3 two-axis state model) was re-measured and still resolves; it is
unchanged. §12.3's protocol line count and digest were re-derived after the §18
append: **410 lines, `59643d24…69a6590`**.

One further citation inside §12.1 was found stale and corrected in the same pass:
`PARAM-E.6` cited `:338-339` (now `:374-375`, §17 open issue 2).

**Scope note — what this pass did not correct.** F-06's recorded scope is §12.
Two protocol citations outside §12 carry the same staleness and are deliberately
left untouched rather than silently half-corrected: `:267` and `:402`, both in
§8, which cite `03B-R1:340-341` / `:338-339` / `:344` for §17 issues 3, 2 and 6.
Their correct current targets are `:376-377`, `:374-375` and `:380`. They are
recorded here so a later pass cannot mistake them for verified anchors, and so
that correcting them is an explicit decision rather than an oversight.

No owner approval, commit, signature or G7 grant attaches to this note. It
corrects citations; it changes no parameter value and authorises nothing.
