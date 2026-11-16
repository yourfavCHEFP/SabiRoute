# R6-REG-PROTOCOL-03B-R1 — U1–U3 Technical Proposal

**Status:** PROPOSAL — NOT APPROVED, NOT INCORPORATED, NOT EXECUTED

**Prepared by:** Claude Code (registrar role, `PARAM-F.2`) under the owner's
Option-B authorisation dated 2026-11-06.

**Review required before owner approval:** Claude Desktop (independent verifier,
`PARAM-F.3`) must independently review all three proposals and reproduce the
test vectors in §4.

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`; no tracked modifications, nothing
staged.

**Source digests at this baseline (raw = canonical; all three files are LF-only,
no BOM):**

| Document | SHA-256 |
|---|---|
| `docs/r6-registration-protocol-03b-r1.md` | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` |
| `docs/r6-t16-r6-decision-option-register.md` | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |

---

## 0. Scope, authority and what this document is not

This document answers the three unresolved items recorded at addendum §11
(`:386-402`) under the owner's Option-B authorisation:

- **U1** — byte definition of the extracted-card digest;
- **U2** — byte definition of the whole-file digest;
- **U3** — initial trusted-checkpoint anchoring and VER-ledger genesis.

It is a **proposal for review**. It does not:

- create a REG or VER record;
- create, modify or sign a manifest;
- generate a signing key or any signature;
- create the VER ledger or establish a checkpoint;
- modify T16 or change any decision's approval status;
- mark any gate COMPLETE;
- authorise BL-22, R6.1, or any implementation.

Operational registration authority remains **DEFERRED** by the owner. Nothing
here supplies the "separately confirmed operational authority" required by
03B-R1 §10 (`:216-217`).

**Out of scope (first-execution parameters, to be proposed separately):** the
concrete filesystem path of the VER ledger, the concrete path of the canonical
REG locus, and the manifest's serialisation format. This proposal defines the
*digest and anchoring contracts* those parameters will reference; it does not
choose the paths.

---

## 1. U1 — Extracted-card digest

### 1.1 Definition

The **extracted-card digest** is the SHA-256 of the **canonical card text** of
one canonical decision card, identified by its decision ID (`A1`–`A4`, `B1`–`B9`,
`C1`–`C4`, `D1`–`D6`).

**Source object:** `docs/r6-t16-r6-decision-option-register.md` — the canonical
decision register. The card is a contiguous region of that file.

**Extraction procedure (normative):**

1. Read the source file as **raw bytes**.
2. **Reject** if the file begins with a UTF-8 BOM (`EF BB BF`).
3. Decode as **UTF-8, strict** (reject invalid byte sequences).
4. **Canonicalise newlines:** replace every `CRLF` with `LF`, then every
   remaining `CR` with `LF`.
5. Split into lines on `LF`.
6. Identify **fenced code regions** (a line whose first non-space characters are
   ` ``` ` or `~~~` opens a fence; the matching token closes it). Lines inside a
   fence are excluded from heading detection.
7. Identify **ATX headings** outside fenced regions: lines matching
   `^(#{1,6})\s+(.*)$`.
8. Locate the **card heading**: the unique line outside fenced regions matching
   `^(#{1,6})\s+(<ID>)\s+[—–-]\s+`, where `<ID>` is the requested decision ID.
   - zero matches → **fail closed** (`MISSING CARD`);
   - more than one match → **fail closed** (`AMBIGUOUS CARD`).
9. Let `L` be the heading level (number of `#`). The card span **ends** at the
   first subsequent heading line (outside fenced regions) whose level is `≤ L`;
   if none exists, at end of file.
10. Take the lines from the card heading line up to, but excluding, the end line.
11. **Strip trailing separators:** remove trailing blank lines; then, if the last
    remaining line is a horizontal rule matching
    `^ {0,3}(-{3,}|\*{3,}|_{3,})\s*$`, remove it; repeat step 11 until stable.
12. Join the remaining lines with a single `LF`. This is the **canonical card
    text**.
13. Encode the canonical card text as **UTF-8, no BOM**.
14. Compute **SHA-256**; render as **lowercase hexadecimal** (64 characters).

**Explicitly NOT applied** (each is a deliberate exclusion, not an omission):

- Unicode NFC/NFD normalisation;
- stripping of leading/trailing whitespace on the first or last content line;
- any change to internal whitespace;
- retention of trailing newlines;
- retention of trailing horizontal rules or blank separators.

**Evidence recorded with the digest** (so the byte span is stated, per
`PARAM-B.4`): source path; source whole-file digest (U2); decision ID; heading
line number (1-based, canonical form); end line (exclusive); canonical byte
length; digest.

### 1.2 Rationale

- **Byte-faithful modulo newline canonicalisation.** The digest corresponds to a
  real, locatable region of the file. This satisfies `PARAM-B.4`'s requirement
  that the hashed byte span be stated and not silently shifted.
- **Newline canonicalisation is required for cross-platform reproducibility.**
  The registrar (Claude Code) and the independent verifier (Claude Desktop) may
  read the file through different checkouts. A Windows checkout with
  `core.autocrlf=true` would otherwise change every digest. Canonicalising
  newlines makes the digest invariant to line-ending convention while leaving
  all content bytes untouched. This is the same first step as 03B-R1 §8
  (`:175-176`).
- **No NFC.** The card is a source artifact; its exact bytes are the evidence.
  Applying NFC would make the digest correspond to *no* byte range in the file,
  weakening the byte-boundary claim. NFC is appropriate for `PARAM-B.1` because
  that hashes a *transcribed field value*; it is not appropriate for a *file
  region*.
- **Trailing-separator stripping.** Without it, the last card in each group
  absorbs the `---` section separator while earlier cards do not, making the
  digest inconsistent in what it covers. Stripping makes all 23 cards bind
  content only.
- **Fail-closed on missing/duplicate.** Consistent with `PARAM-E.5` (strict
  parser rejects malformed, duplicate, conflicting markers).

### 1.3 Reproducibility test

Claude Desktop must reproduce the 23 vectors in §4.1 from the source file at the
stated digest. Any mismatch is a **reproducibility failure** and blocks approval.

### 1.4 Security implications

- Detects **any** change to a card's content, including a single character.
- Does **not** detect changes to inter-card whitespace or separators (by design).
- Does **not** detect changes outside the card — that is U2's role.
- Is a **content binding, not an authentication**. It proves the card text is
  what was hashed; it does not prove who produced it. Authentication is the
  signature/checkpoint layer (`PARAM-D`, U3).
- Is **not** a substitute for the REG marker or the VER record.

### 1.5 Source references

- Addendum §4 `PARAM-B.3`, `PARAM-B.4` (`:148-168`).
- 03B-R1 §8 hash normalisation (`:171-185`).
- 03B-R1 §12 duplicate handling (`:229-248`); §13 failure handling (`:250-266`).
- T16 §3 master index (`:87-116`); §4 A3 card (`:149-166`).

---

## 2. U2 — Whole-file digest

### 2.1 Definition

The **whole-file digest** is the SHA-256 of the **canonical byte form** of an
entire source file.

**Procedure (normative):**

1. Read the file as **raw bytes**.
2. **Reject** if it begins with a UTF-8 BOM (`EF BB BF`).
3. Decode as **UTF-8, strict**.
4. **Canonicalise newlines:** `CRLF` → `LF`, then remaining `CR` → `LF`.
5. Encode as **UTF-8, no BOM**.
6. Compute **SHA-256**; render as **lowercase hexadecimal**.

**Explicitly NOT applied:** NFC/NFD; whitespace stripping; trailing-newline
removal; any trimming; any re-serialisation.

**Evidence recorded:** source path; canonical byte length; digest.

### 2.2 Rationale

- Binds the **entire** register, complementing U1 (which binds one card). A
  change anywhere in the file — including outside any card — changes U2.
- **Distinct from `PARAM-B.2`** (revision digest). `PARAM-B.2` hashes the
  *canonical manifest bytes*; U2 hashes the *register file*. Different source
  objects, different purposes, different evidence fields.
- Same newline-canonicalisation rationale as U1.

**Note on the current baseline:** all three source documents are LF-only with no
BOM, so for them the whole-file digest equals the raw-byte SHA-256. The rule
still matters because a future checkout may introduce CRLF.

### 2.3 Reproducibility test

Claude Desktop must reproduce the whole-file digest in §4.2. A CRLF-converted
copy of the file must yield the **same** digest (newline invariance test).

### 2.4 Security implications

- Detects any change anywhere in the file.
- Does **not** authenticate the file.
- Does **not** replace per-card binding: a whole-file digest alone cannot tell
  *which* card changed.

### 2.5 Source references

- Addendum §4 `PARAM-B.2`, `PARAM-B.3`, `PARAM-B.4` (`:142-168`).
- 03B-R1 §8 (`:171-185`).

---

## 3. U3 — Trusted-checkpoint anchoring and VER-ledger genesis

### 3.1 Ledger structure

The VER ledger is an **append-only** file (`PARAM-E.7`), UTF-8, LF-terminated,
**one canonical JSON object per line** (JSONL). Appending never rewrites prior
lines.

Each entry carries:

| Field | Type | Meaning |
|---|---|---|
| `seq` | integer | Monotonic, starts at `0` (genesis), increments by 1 |
| `prev` | string | `entry_sha256` of the previous entry; for genesis, the genesis constant (§3.2) |
| `entry_type` | string | `GENESIS` or `VER` |
| *(payload)* | — | Type-specific fields (§3.2, §3.3) |

**`entry_sha256`** = SHA-256 of the entry's **canonical JSON bytes** (excluding
the terminating `LF`), lowercase hex.

**Canonical JSON rules** (normative, for cross-language reproducibility):

- object keys sorted ascending by Unicode code point;
- no whitespace between tokens; separators `,` and `:`;
- strings JSON-escaped per RFC 8259, non-ASCII emitted as literal UTF-8
  (`ensure_ascii=false`), `/` not escaped;
- integers in decimal, no leading zeros, no `+`, no exponent;
- no BOM; no trailing newline in the hashed bytes;
- the on-disk line is the same bytes followed by exactly one `LF`.

**Chain head** = `entry_sha256` of the highest-`seq` entry.

### 3.2 Genesis record

`seq = 0`, `entry_type = "GENESIS"`, `prev` = the **genesis constant**:

```
e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307
```

which is `SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))`. This is a
**domain-separated constant**, not 64 zeros, so a genesis `prev` can never be
confused with a real predecessor hash.

Genesis payload fields:

| Field | Meaning |
|---|---|
| `ledger_id` | Stable identifier for this ledger instance (first-execution parameter) |
| `created` | Actual creation date, UTC `YYYY-MM-DD` (`PARAM-C.1`) |
| `owner_key_fingerprint` | `SHA256:<base64>` of the owner's Ed25519 public key (`PARAM-D.4`) |
| `protocol_sha256` | Whole-file digest of `docs/r6-registration-protocol-03b-r1.md` |
| `addendum_sha256` | Whole-file digest of the owner-parameter addendum |
| `t16_sha256` | Whole-file digest of the canonical decision register |

**Illustrative and non-normative example.** The line below is a *shape*
illustration only. It contains placeholder values (`YYYY-MM-DD`, `<LEDGER_ID>`,
`SHA256:<base64>`) and therefore **cannot** be hashed to a reproducible
`entry_sha256`; it is not a test input and must not be used as a conformance
vector. The normative, fully specified worked example — with concrete synthetic
values, a 508-byte canonical line, and the reproducible digest
`ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28` — is in
`docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §3.5/§3.6.

Illustrative canonical genesis line (placeholders; non-normative):

```json
{"addendum_sha256":"2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f","created":"YYYY-MM-DD","entry_type":"GENESIS","ledger_id":"<LEDGER_ID>","owner_key_fingerprint":"SHA256:<base64>","prev":"e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307","protocol_sha256":"3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b","seq":0,"t16_sha256":"43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c"}
```

The genesis `entry_sha256` is the **initial chain head**.

### 3.3 VER record entry

`seq = n`, `entry_type = "VER"`, `prev` = previous `entry_sha256`.

Payload mirrors the `VER:v1` grammar (03B-R1 §6, `:110-135`) and adds the two
content digests so the verification is bound to the exact card and file:

| Field | Meaning |
|---|---|
| `decision` | Decision ID |
| `verifier` | Verifier identity (`Claude Desktop`) |
| `verified` | Actual verification date, UTC `YYYY-MM-DD` |
| `result` | `PASS` or `FAIL` (`PARAM-E.8`: both retained) |
| `marker_sha256` | Digest of the REG marker verified |
| `items_checked` | Integer count of the ten-item inventory checked |
| `card_sha256` | U1 digest of the card at verification time |
| `file_sha256` | U2 digest of the register at verification time |

### 3.4 Checkpoint message and owner authentication

A **checkpoint** is the owner's detached Ed25519 signature over a canonical
checkpoint message binding the current chain head.

**Checkpoint message (canonical bytes):** exactly these five lines, each
terminated by one `LF` (so the message ends with exactly one `LF`), UTF-8, no
BOM, no leading/trailing spaces:

```
R6-VER-CHECKPOINT:v1
ledger_id=<LEDGER_ID>
seq=<N>
chain_head=<HEX64>
created=<YYYY-MM-DD>
```

**Signing** (owner, locally, private key never leaves the owner's control):

```
ssh-keygen -Y sign -f <private_key> -n r6-ver-checkpoint <message_file>
```

produces `<message_file>.sig`.

**Verification** (any party, public key only — `PARAM-D.6`):

```
ssh-keygen -Y verify -f <allowed_signers> -I <identity> \
  -n r6-ver-checkpoint -s <message_file>.sig < <message_file>
```

`allowed_signers` line: `<identity> ssh-ed25519 <base64_public_key>`.

**Fingerprint:** `ssh-keygen -lf <public_key_file>` → `SHA256:<base64>`, recorded
in the genesis entry and in the checkpoint evidence.

**Owner authentication** is the checkpoint signature itself. No agent asserts
owner identity; the signature is the only owner-authentication evidence, and it
is verifiable with the public key alone.

### 3.5 Genesis anchoring procedure (proposed; not executed)

1. Owner generates an Ed25519 keypair **locally, outside the repository and
   outside any agent context**.
2. Owner provides the **public key and fingerprint** to the registrar.
3. Registrar creates the ledger file with the genesis entry (`seq=0`) and
   computes its `entry_sha256` = initial chain head.
4. Registrar writes the checkpoint message (§3.4) to a file.
5. Owner signs the checkpoint message **locally** with the private key.
6. Owner provides the **detached signature** to the registrar.
7. Registrar records as evidence: ledger, checkpoint message, signature, public
   key, fingerprint, and all digests.
8. Claude Desktop independently verifies: recompute the genesis `entry_sha256`;
   recompute the checkpoint message bytes; verify the signature with the public
   key only.
9. Copies are made to offline and independent cloud storage (§3.6); digests
   recorded.

### 3.6 Offline and independent cloud preservation

Per `PARAM-D.5` and `PARAM-D.7`:

- **(a) Offline copy** — ledger, checkpoint message, signature, and public key
  copied to offline media; the copy's digest recorded.
- **(b) Independent cloud copy** — the same set copied to cloud storage; the
  provider, path, and digest-at-copy recorded.
- The cloud copy is **explicitly not immutable or tamper-proof** and must never
  be described or relied upon as such.

### 3.7 Independent verification by Claude Desktop

Claude Desktop must, using the public key only:

1. Recompute every `entry_sha256` from the ledger lines and confirm the chain
   links (`prev` of entry *n* equals `entry_sha256` of entry *n−1*).
2. Confirm the genesis `prev` equals the genesis constant.
3. Recompute the checkpoint message bytes and verify the signature.
4. Confirm the checkpoint's `chain_head` and `seq` match the ledger.
5. Confirm `owner_key_fingerprint` matches the public key used.

Any mismatch → `INVALID / RECONCILIATION REQUIRED` (`PARAM-E.10`).

### 3.8 Recovery

Per `PARAM-E.4`, `PARAM-E.10`, and 03B-R1 §11 (`:219-227`):

- On loss or corruption, restore from the independently preserved copies.
- Re-verify the chain from genesis and the checkpoint signature.
- If the recomputed chain head does not match the checkpoint `chain_head` →
  `INVALID / RECONCILIATION REQUIRED`.
- No automatic repair, rewrite, downgrade, or deletion. Recovery is performed by
  the recovery engineer (`PARAM-F.4`), who may not write REG or VER records
  (`PARAM-F.5`).

### 3.9 Private-key handling

The owner-controlled private key:

- is generated and held **locally by the owner**;
- **never** enters the repository, any agent context, any log, or any shared
  evidence (`PARAM-D.2`, `PARAM-G.1`);
- is used only by the owner, out-of-band, to sign checkpoint messages;
- is never requested, handled, or stored by the registrar or verifier.

Agents receive only: the public key, its fingerprint, the checkpoint message, and
the detached signature.

### 3.10 Security implications and limitations

- **Signatures detect change; copies enable recovery** (`PARAM-D.8`). A signature
  cannot restore lost content.
- **The chain is only as strong as the latest checkpoint.** Entries appended
  after the last checkpoint are chain-protected but **not anchored** until the
  next checkpoint. An attacker with write access could rewrite unanchored
  entries. This is why checkpoint cadence matters (§6, D-U3-1).
- **Domain separation** of the genesis constant prevents a genesis `prev` from
  being mistaken for a real predecessor hash.
- **The ledger is not the REG record.** It is the append-only verification
  ledger; REG records live at the canonical registration locus (`PARAM-A.1`).
- **The checkpoint is not the manifest sidecar.** `PARAM-D.3`'s SHA-256 sidecar
  is the revision referent of `PARAM-B.2`; the checkpoint anchors the VER-ledger
  chain head. Different objects, different purposes.

### 3.11 Source references

- Addendum §6 `PARAM-D.1`–`D.8` (`:197-240`).
- Addendum §7 `PARAM-E.4`, `E.7`, `E.8`, `E.9`, `E.10` (`:254-289`).
- Addendum §8 `PARAM-F.4`, `F.5` (`:310-318`).
- Addendum §9 `PARAM-G.1` (`:335-341`).
- Addendum §11 U3 (`:396`).
- 03B-R1 §6 VER grammar (`:110-135`); §11 recovery (`:219-227`).

---

## 4. Consolidated test vectors

All values computed at the baseline in the header. Claude Desktop must reproduce
every value independently.

### 4.1 U1 — extracted-card digests (23 cards)

| ID | Lines (canonical) | Bytes | SHA-256 |
|---|---|---|---|
| A1 | 123–135 | 767 | `70cb1ddeed5b84f17520e90ba69e4182e519a5998ec10747d9eb5f22c7353bc4` |
| A2 | 136–148 | 1022 | `afbb96c4ea74efd862d775ce49b32d637b22d0e1f746a352acd28d5209208e34` |
| A3 | 149–167 | 1763 | `9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b` |
| A4 | 168–182 | 683 | `ce9c8e2926efbb0a189d68ae050e1e9d052f013360467bd76ef56044ea6965d3` |
| B1 | 187–212 | 2410 | `b19da622ef05d57be53f0932714b51643ebb8a79cee81a43a92df07e034fa2f4` |
| B2 | 213–225 | 723 | `e041985cee5b4bcd1408c412a3d88b11ede018ce29d60231565c01a918fe3466` |
| B3 | 226–238 | 721 | `db9606a1d44ec430ba38937585802f85255b6bbd77960661695c72a03fc8c4b1` |
| B4 | 239–251 | 620 | `a7836a4847f15714e894d4c0e54eef054f0789aa537e6424959783b7bfb80d2d` |
| B5 | 252–270 | 1891 | `f39ef13072107af456090507b7d6538493460dc6616f6aac266fc9aceae6045e` |
| B6 | 271–295 | 2076 | `9c22e56afab5a367db13d451c04fdbb022b74a93d367b0bbc6963e0bf8907374` |
| B7 | 296–308 | 924 | `b1e497bf590185cbaaf370bfd59133c47fb4a9c7b6db38489e635917efc92fff` |
| B8 | 309–321 | 689 | `50afcf458560cb68994906bf2b9fcc195c33174c8ddba9a3c4466e07e6771dae` |
| B9 | 322–336 | 630 | `851a80438990ea0c6221c654821029a84b3411265d01679b8eb7c77a1ea6b88a` |
| C1 | 343–355 | 1354 | `071f1cb93a3b4f8489cad63c6d9f0e6cbd5606cb64a77364083bfdcf036312c5` |
| C2 | 356–368 | 800 | `10e53984d2a684283886872e7085ec0d63f7776235ccd92f9ec95e57f333442a` |
| C3 | 369–381 | 843 | `6bfeebbed8775506db300068733fcce8bdfeffa568febd1bbca06113946a4a3b` |
| C4 | 382–394 | 1071 | `51e4e7491f2333eee0c274dd2091ba5b9b4e8a4f35d7d73944d333ec27b19bab` |
| D1 | 399–412 | 858 | `62905f789fa0efa97fbf3abaaa34aa93fcd710347a3ea76e30172c9428cc014f` |
| D2 | 413–425 | 1038 | `77cb466bffba3f3d14195c009362b8bb20e5f130241fc47d778f5371aa54cdb2` |
| D3 | 426–446 | 1933 | `bf1c0075f445f3bbfbd7b1b7b302e5112dc7762f3037b44a00ebe3f9aac108ef` |
| D4 | 447–459 | 922 | `55a557ceb62ab25df55d73e3a456cf405a4e5f398ca3524ca4bd28b9a22e5c99` |
| D5 | 460–472 | 841 | `9fcda8d4f9a2b1a842f0afec2f370be71e398d5de5a694a141047fee6e4f5485` |
| D6 | 473–487 | 807 | `21c67a9aa474b442d98389e17ee49cc1dfa3f6db3087ad47f5caa27b5eec3109` |

### 4.2 U2 — whole-file digests

| File | Canonical bytes | SHA-256 |
|---|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52782 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| `docs/r6-registration-protocol-03b-r1.md` | 12619 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 26782 | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` |

### 4.3 U3 — genesis constant

| Item | Value |
|---|---|
| `SHA-256("R6-VER-LEDGER-GENESIS:v1")` | `e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` |

### 4.4 Behavioural tests

| Test | Expected |
|---|---|
| Extract `A3` twice | identical digest (determinism) |
| Extract `A3` from a CRLF-converted copy | identical digest (newline invariance) |
| Extract a non-existent ID (`Z9`, `A5`) | fail closed (`MISSING CARD`) |
| Extract from a file with a duplicated card heading | fail closed (`AMBIGUOUS CARD`) |
| Whole-file digest of a CRLF-converted copy | identical to LF original |

---

## 5. Deliberate deviations and points for reviewer attention

These are the places where this proposal makes a choice the reviewer should
scrutinise rather than accept by default.

1. **U1/U2 do not apply NFC, while `PARAM-B.1` does.** Deliberate: `PARAM-B.1`
   hashes a transcribed field value; U1/U2 hash file regions. If the owner
   prefers a single normalisation regime, U1/U2 can be changed to full §8
   normalisation — but that would make the digests correspond to no byte range in
   the file.
2. **Trailing horizontal rules and blank separators are excluded from the card
   span.** Without this, the last card in each group absorbs the `---` separator
   and earlier cards do not.
3. **The genesis `prev` is a domain-separated constant, not 64 zeros.** Chosen to
   prevent confusion with a real predecessor hash.
4. **The VER entry carries `card_sha256` and `file_sha256`.** This binds the
   verification to the exact content verified, at the cost of two extra fields
   beyond the `VER:v1` grammar. The `VER:v1` marker itself is unchanged.
5. **Canonical JSON is specified rather than RFC 8785 JCS.** All values are
   strings or non-negative integers, so the number-formatting edge cases JCS
   exists to solve do not arise. If the reviewer prefers JCS, it is a drop-in
   substitution.

---

## 6. Open sub-decisions for the owner

These are not resolved by this proposal and need an owner decision before
execution.

- **D-U3-1 — Checkpoint cadence.** Options:
  - (a) after **every** VER entry, before COMPLETE is reported (strongest; owner
    must sign each time);
  - (b) at each **gate boundary** and at the close of each registration session
    (lighter; entries after the last checkpoint are chain-protected but
    unanchored).
- **D-U3-2 — `ledger_id` scheme.** A stable identifier for the ledger instance
  (e.g. a fixed string, or a date-stamped identifier). Needed for the genesis
  record and every checkpoint.
- **D-U3-3 — `allowed_signers` identity string.** The `-I` identity used in
  verification (e.g. `owner@r6`). Needed for reproducible verification.

---

## 7. What this proposal does not do

- It does not create, modify, or sign a manifest.
- It does not generate a signing key or any signature.
- It does not create the VER ledger or establish a checkpoint.
- It does not create a REG or VER record.
- It does not modify T16 or change any approval status.
- It does not mark any gate COMPLETE.
- It does not authorise BL-22, R6.1, or any implementation.
- It does not supply operational registration authority, which remains
  **DEFERRED**.

**PROPOSAL — NOT APPROVED, NOT INCORPORATED, NOT EXECUTED.**
