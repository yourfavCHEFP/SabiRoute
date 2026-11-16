# R6-REG-PROTOCOL-03B-R1

**Status:** DRAFT — OWNER-APPROVED PROTOCOL DECISIONS, NOT YET REGISTERED OR
EXECUTED

**Created:** 2026-11-06  
**Repository baseline:** `feat/sabiroute-routing-foundation` @
`319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`

This artifact encodes the approved PROTOCOL/D-1 through PROTOCOL/D-5 decisions.
It is a procedure draft, not a registration record. No decision is registered,
verified, complete, or gate-accepted by creating this file.

## 1. Purpose and scope

This protocol defines the controlled procedure for recording an owner response
against an existing canonical decision card, independently verifying that
record, and reporting the resulting lifecycle counts.

It applies to canonical decision registration only. It does not create decision
cards, change decision options, resolve unresolved decisions, or sign a gate.

## 2. Authority and limitations

The owner-approved protocol decisions are:

- **PROTOCOL/D-1:** use separate response and approval axes.
- **PROTOCOL/D-2:** use Protocol 03B safeguards: normalized-text hashing,
  independent verification, and mandatory post-COMPLETE read-back.
- **PROTOCOL/D-3:** report five distinct lifecycle counts.
- **PROTOCOL/D-4:** A3 is the first intended registration, subject to all
  prerequisites and the designated roles.
- **PROTOCOL/D-5:** supplementary evidence cannot replace canonical
  owner-response recording.

The intended registration date is **2026-11-06**. This date is not evidence
that execution occurred. Every execution record must use its actual execution
timestamp.

Markdown procedures are procedural safeguards, not cryptographic access
controls. This document cannot authenticate an owner, registrar, verifier, or
approval. Authority remains with the designated human and governance process.

## 3. Two-axis decision state model

The axes and values are fixed:

### Response

- `PENDING`
- `SELECTED`

### Approval

- `OUTSTANDING`
- `APPROVED`

`PENDING + APPROVED` is unreachable. An approval record must identify the
owner-authorized response it approves. A selected response is not by itself
approved, registered, verified, complete, or gate-accepted.

Registration must not add `DURABLY_RECORDED`, `REGISTERED`, or `COMPLETE` as
values on either axis. Those are lifecycle/reporting concepts only.

## 4. Five lifecycle reporting counts

Report these independently; none is an axis value and none implies another:

1. **Owner-selected** — the owner selected an available option.
2. **Durably recorded** — the selection is preserved in the approved durable
   record.
3. **Canonically registered** — the canonical decision register contains the
   owner response in its designated field.
4. **Independently verified** — the distinct verifier confirmed the canonical
   record and matching hash.
5. **Gate-accepted** — the authorized gate owner accepted the applicable
   closure condition.

Counts must include their scope, denominator, timestamp, and evidence
references. A count of zero is a valid result.

## 5. Registration marker grammar

The REG marker is a separate structured comment. `REG:v1` is the marker
identifier, not a tenth named field. Preserve the following field names and
order exactly:

```text
<!-- REG:v1 decision=<ID> state=<STATE> option=<OPT> owner_sha256=<HEX64>
     confirmed=<DATE|UNRESOLVED> recorded=<DATE|UNRESOLVED>
     registrar=<ID|UNRESOLVED> revision=<SHA|UNRESOLVED> prev_state=<STATE> -->
```

The nine named fields are:

1. `decision`
2. `state`
3. `option`
4. `owner_sha256`
5. `confirmed`
6. `recorded`
7. `registrar`
8. `revision`
9. `prev_state`

The field values must conform to the original grammar. `REG:v1` is not counted
as a field, and no additional mandatory marker fields may be invented. A REG
marker is not a VER record.

## 6. Independent verification record grammar

Verification is a separate append-only ledger entry (`PARAM-A.2`), one canonical
JSON object per line:

**Envelope — 4 keys**

| # | Key | Type | Rule |
|---:|---|---|---|
| 1 | `seq` | integer | `0` at genesis, `+1` per entry, no gaps |
| 2 | `prev` | string | previous `entry_sha256`; genesis uses the domain constant |
| 3 | `entry_type` | string | `GENESIS` or `VER` — no `REG` member |
| 4 | `entry_sha256` | string | SHA-256 of the canonical JSON bytes, **excluding** the terminating LF |

**Payload — 8 keys**, in this order: `decision`, `verifier`, `verified`,
`result`, `marker_sha256`, `items_checked`, `card_sha256`, `file_sha256`.

| # | Key | Type | Rule |
|---:|---|---|---|
| 5 | `decision` | string | the canonical T16 decision ID |
| 6 | `verifier` | string | the designated independent verifier |
| 7 | `verified` | string | actual verification date, `YYYY-MM-DD` UTC |
| 8 | `result` | string | `PASS` or `FAIL` only |
| 9 | `marker_sha256` | string | U4 REG-marker digest, lowercase hex |
| 10 | `items_checked` | integer | count of the ten-item inventory (§7) |
| 11 | `card_sha256` | string | U1 digest of the card at verification time |
| 12 | `file_sha256` | string | U2 digest of the register at verification time |

**Hash input.** `entry_sha256` is **computed, never serialised**. A `VER` entry's
hashed object contains **eleven** keys — `seq`, `prev`, `entry_type` and the eight
payload fields. The twelve-key count includes the computed digest as a ledger
field. A genesis entry hashes **nine** keys (six payload + three envelope).

**Provenance.** Envelope and payload per the O3/O4/O5 owner decision pack §5.2
(`:474-481`), payload order at `:490-491`.

The six named fields are:

1. `decision`
2. `verifier`
3. `verified`
4. `result`
5. `marker_sha256`
6. `items_checked`

`result` is restricted to `PASS` or `FAIL`. `VER:v1` is not counted as a field.
The verifier must compare the canonical record and the applicable REG marker;
the post-COMPLETE read-back is mandatory. A COMPLETE registration is valid only
when a matching VER ledger entry exists with `result=PASS`, and the mandatory
post-COMPLETE read-back independently confirms the marker and verification
record. A missing, malformed, mismatched, or FAIL VER record makes COMPLETE
invalid and requires reconciliation. No automatic downgrade or repair is
permitted.

**REG/VER asymmetry.** REG and VER are deliberately asymmetric: a REG marker is an
HTML comment written adjacent to its T16 decision card (§10), whereas a VER entry
is a canonical JSON line in a separate append-only ledger (`PARAM-A.2`). The
asymmetry is intentional and is not an inconsistency to be resolved.

**`items_checked` bound.** `1 ≤ items_checked ≤ 10`. A `PASS` result requires
exactly `10`; a `FAIL` result is permitted at any count in `1..10`. A count of `0`
is invalid.

## 7. Ten-item registration inventory

Before any REG marker is emitted, confirm all ten items:

### Authoritative owner-decision records

1. The owner response.
2. The approval.
3. The conditions and provenance.

### Derived records

4. The index response/status.
5. The §2 summary.
6. The §13 final status.
7. The §1 header.

### Canonical registration evidence

8. The REG marker.

### Independent verification evidence

9. The VER record.

### Independent post-COMPLETE read-back evidence

10. The mandatory post-COMPLETE read-back.

The inventory is evidence to collect, not a claim that any item is complete.

Additional operational checks may support these records, but they do not
replace or reorder the ten original inventory items.

## 8. Hash normalization

Normalize only for the purpose of calculating the registration hash:

1. Convert CRLF to LF.
2. Convert remaining CR to LF.
3. Apply Unicode NFC normalization.
4. Strip leading and trailing whitespace.
5. Preserve internal whitespace exactly.
6. Encode as UTF-8 without a BOM.
7. Compute SHA-256.
8. Render the digest as lowercase hexadecimal.

The hash guarantees normalized textual equality. It does not guarantee
byte-for-byte fidelity of the source file.

## 9. RECORD procedure

1. Identify the canonical card and qualify its namespace.
2. Confirm the designated registrar and independent verifier are available and
   distinct identities.
3. Capture the owner's exact response text and provenance.
4. Confirm the response is one of the documented options.
5. Set the response and approval axes without adding lifecycle values.
6. Normalize the response and calculate the hash under §8.
7. Prepare the REG marker under §5.
8. Stop if any prerequisite, provenance, or field validation fails.

Recording a selection does not execute canonical registration. The RECORD
procedure prepares auditable input for the REGISTER procedure.

## 10. REGISTER procedure

1. Re-read the canonical register and confirm the target field is still
   unchanged and eligible for registration.
2. Confirm the owner response, source, normalized text, and hash match.
3. Write exactly one REG record to the approved canonical registration locus.
4. Do not write a VER record as the registrar.
5. Do not mark a gate accepted.
6. Have the designated independent verifier perform §6.
7. Perform the mandatory post-COMPLETE read-back under §15.
8. Treat COMPLETE as valid only after a matching `VER:v1` record has
   `result=PASS` and the post-COMPLETE read-back independently confirms both
   records.

The REGISTER procedure is not authorized by this draft. It may be executed only
by the designated registrar under separately confirmed operational authority.

## 11. Interruption and recovery

An interruption must preserve all already-written evidence and the last known
operation boundary. Do not infer completion from a partial write, process exit,
file existence, or timestamp.

Recovery must re-read the canonical register, REG record, and any VER record.
Conflicting or incomplete evidence is `INVALID / RECONCILIATION REQUIRED`.
Recovery must not automatically downgrade, repair, rewrite, or delete records.

## 12. Duplicate operation handling

Before writing, search for an existing REG record for the same qualified
canonical decision context and the same complete marker content. The
deterministic identity available from the restored grammar is the tuple:

```text
(decision, state, option, owner_sha256, confirmed, recorded,
 registrar, revision, prev_state)
```

- An exact tuple match must not be emitted again; report it as a duplicate.
- A different tuple for the same canonical decision context is a conflict
  requiring reconciliation, not a second operation.
- The marker grammar contains no operation identifier or nonce. Therefore it
  cannot guarantee unique identity for two otherwise identical operations;
  that limitation remains unresolved and no new marker field is invented.

No duplicate operation may be treated as independent verification or as a new
owner selection.

## 13. Failure and conflict handling

The following are failures requiring explicit reconciliation:

- missing or ambiguous owner provenance;
- undocumented option text;
- invalid axis combination;
- hash mismatch;
- missing independent verifier;
- registrar and verifier having the same identity;
- missing or mismatched REG/VER linkage;
- canonical read-back mismatch;
- duplicate or conflicting REG records;
- `COMPLETE` without a matching VER record with `result=PASS`.

The outcome for these cases is `INVALID / RECONCILIATION REQUIRED`. There is
no automatic downgrade, repair, rewrite, or inferred approval.

## 14. Registrar and verifier responsibilities

The designated roles are:

- **Registrar:** Claude Code in VS Code.
- **Independent verifier:** Claude Desktop Chat 05.

The roles must be performed by different identities. Copilot, this assistant,
or any substitute identity must not silently assume either role.

The registrar records only the owner response and registration evidence. The
verifier independently checks the evidence and writes the separate VER record.
Neither role may sign BL-22 or grant G7 through this protocol.

## 15. Post-COMPLETE read-back

After a registration operation reaches `COMPLETE` in the operational record,
the verifier must read back the canonical decision register and compare:

- canonical ID and namespace;
- exact owner-response text;
- response and approval axes;
- normalized hash;
- REG record;
- matching VER record.

A COMPLETE registration is valid only when a matching VER record exists with
`result=PASS`, and this mandatory read-back independently confirms the marker
and verification record. A missing, malformed, mismatched, or FAIL VER record
makes COMPLETE invalid and requires reconciliation. It must not be
automatically downgraded, repaired, or rewritten.

The read-back result and actual timestamp are part of the audit evidence.

## 16. Audit evidence and acceptance criteria

A registration package is auditable only when it contains the applicable
canonical source, owner-response provenance, REG record, normalized text/hash,
distinct VER record, and post-COMPLETE read-back.

The protocol itself is satisfied only when:

- D-1 through D-5 are preserved;
- no axis has gained lifecycle values;
- five lifecycle counts are reported separately;
- REG and VER remain separate;
- registrar and verifier are distinct;
- COMPLETE has a matching VER record with `result=PASS` and a successful
  post-COMPLETE read-back;
- all failures use `INVALID / RECONCILIATION REQUIRED`;
- no registration, verification, or gate acceptance is claimed without its
  corresponding evidence.

## 17. Explicit exclusions and non-authorisations

This draft does not:

- edit T16 or any canonical decision register;
- register A3, B1, B6, or any other decision;
- create REG or VER records;
- act as registrar or independent verifier;
- resolve the B1 package-name value;
- resolve B5 or any other outstanding decision;
- sign BL-22;
- grant G7, Track A, R6.1, or implementation authority;
- authorize tests, migrations, provider calls, deployment, commits, or pushes.

### Open issues

1. The approved operational locus for REG and VER records is not specified.
2. Field escaping, if needed by values outside the displayed grammar, is not
   specified by the available protocol material.
3. Hash extraction boundaries for the owner response and REG marker remain
   unresolved.
4. Date semantics beyond the displayed field formats remain unresolved.
5. Revision semantics and the authoritative revision source remain unresolved.
6. Marker parsing and persistence guarantees remain unresolved.
7. The owner-context instruction identifies 2026-11-06 as the intended
   registration date, but no execution has occurred.

**DRAFT — OWNER-APPROVED PROTOCOL DECISIONS, NOT YET REGISTERED OR EXECUTED.**

---

## 18. Dated provenance notes

### 2026-11-16 — `VER:v1` token: retained by deferral, not retired

Finding F-03 records that this protocol "still reads `VER:v1` record". The token
appears twice: at `:155` (§6, "`VER:v1` is not counted as a field") and at `:248`
(§10 step 8, "a matching `VER:v1` record has `result=PASS`"). The finding's cited
line `:213` is stale — in this 384-line file `:213` falls inside §8 hash
normalization, which contains no `VER:v1` passage.

**The token is retained deliberately, and this note does not retire it.** The
WP-2 owner decision record (Part 4 §14.1) records the question — retire the
`VER:v1` token entirely, or retain it as the field-name-set identifier while the
container changes from an HTML comment to a JSONL line — as **OPEN**, the
correction **DEFERRED**, and states that no other decision in that record
silently resolves it. Resolving it here would be exactly that silent resolution,
and the deferred sixth has no owner code.

Recorded status: **`VER:v1` token — RETAINED, question OPEN, correction
DEFERRED.** No owner approval, commit, signature or G7 grant attaches to this
note. It records a state; it does not change one.

**DRAFT — OWNER-APPROVED PROTOCOL DECISIONS, NOT YET REGISTERED OR EXECUTED.**
