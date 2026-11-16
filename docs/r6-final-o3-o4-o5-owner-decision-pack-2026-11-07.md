# R6 — FINAL OWNER DECISION PACK — O3 / O4 / O5

**Status:** DECISION PACK — OWNER DECISIONS RECORDED 2026-11-07 — NOT EXECUTED
**Date:** 2026-11-07
**Repository:** `SabiRoute`
**Branch:** `feat/sabiroute-routing-foundation`
**HEAD:** `08201da8013a58b486d5fa2d6c46b36588a27781`
**Working tree at time of writing:** 2 modified tracked files, 0 staged, 0 commits made by this pack.

This document resolves nothing by itself. It presents three open blockers, the
alternatives for each, a recommendation, and the exact wording required to close
them. Every digest in this document was recomputed in this session against the
working tree; where a figure in the handoff was wrong, the correction is stated
explicitly rather than silently applied.

---

## 0. Owner decisions recorded — 2026-11-07

The owner has reviewed this pack and its supporting evidence and has selected the
following. These selections are **recorded here as owner decisions**. They do not
execute anything: no REG or VER record, ledger, key, signature, checkpoint,
migration, deployment, staging, commit or push is authorised by this section.

| ID | Owner selection | Binding requirements recorded by the owner |
|---|---|---|
| **O3** | **Alt-1** — hash the exact extracted Owner response value, retaining the `A3: ` prefix where it forms part of that value. | The hash input is the exact extracted Owner response value, not the surrounding field label and not a reconstructed or reformatted version. Preserve the `A3: ` prefix when it is part of the response value. Apply the already-approved protocol §8 normalisation rules without introducing additional transformations. Preserve internal line breaks and internal whitespace according to §8. Do not strip Markdown hard-break spaces merely because they occur at the end of a visually wrapped line. Do not include the surrounding Owner field label. Reject ambiguous extraction boundaries rather than silently selecting a different interpretation. The 161-byte result produced by stripping the Markdown hard-break spaces is retained as a **negative conformance vector**. This preserves O2: the source remains the exact Owner response field. It does not authorise rewriting historical responses or changing previously approved decisions. |
| **O4** | **Nine-field genesis payload and canonicalisation already specified in proposal §3.1**, subject to the safeguards below. | Include all nine specified fields, including `t16_sha256`. Use the canonical serialisation defined in §3.1. Reject duplicate JSON keys before hashing. Distinguish omitted fields from explicit `null`; do not silently equate them. Enforce the specified field types and reject unsupported values. Use the approved UUIDv4 `ledger_id`. Recompute `entry_sha256` from the complete canonical payload rather than trusting a supplied digest. Retain the verified genesis constant and the worked synthetic example as conformance vectors. The worked example must remain fully specified and reproducible; placeholder values such as `YYYY-MM-DD` and `<LEDGER_ID>` are not acceptable test inputs. This adopts the proposal's canonicalisation design; it does not authorise registration or ledger creation. |
| **O5** | **The append-only JSONL VER ledger is authoritative.** | The three conflicting representations must not remain competing schemas. REG remains adjacent to the relevant T16 decision card, as previously approved. VER entries reside in the separate append-only JSONL ledger. Each VER entry carries the approved sequence and hash-chain fields, including `seq`, `prev`, and `entry_sha256`. Genesis establishes the ledger identity and initial chain state. Every successfully appended VER entry receives its own checkpoint, as previously approved. The checkpoint is bound to the ledger identity and the corresponding ledger state. The HTML-comment VER representation in 03B-R1 §6 must not be treated as an alternative authoritative ledger format. |
| **R6.0-D** | **The R6 governance corpus must be made durable (tracked in Git) before the registration act.** | The three U2-bound files — `docs/r6-t16-r6-decision-option-register.md`, `docs/r6-registration-protocol-03b-r1.md`, `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` — and the R6 governance corpus they depend on must be tracked so that a `git clean`, a fresh clone, or a branch switch that discards untracked files cannot destroy the evidence the digests bind. The exact evidence manifest and privacy review are recorded in `docs/r6-close-final-04-r6.0-d-evidence-manifest-and-privacy-review-2026-11-07.md`. Tracking is a repository act under separate authority; this decision records the requirement and does not itself authorise the commit. |

### 0.1 Carried forward without reopening

- **D-U3-2:** one immutable UUIDv4 `ledger_id` per ledger, stored in genesis and
  bound to the checkpoint.
- **D-U3-3:** stable signer principal `sabiroute-r6-owner`, mapped to the owner's
  Ed25519 public key in `allowed_signers`.
- The actual UUIDv4 value and public-key fingerprint are **first-execution
  values**. Their generation or binding is not an additional architecture
  decision and is not permission to create keys, initialise a ledger, or register
  entries.

### 0.2 Scope boundary — explicitly not granted

These decisions resolve the specified O3/O4/O5 design questions. They do **not**:

- grant operational registration authority;
- authorise REG or VER creation;
- authorise key generation, signing, or checkpoint creation;
- sign BL-22;
- grant G7;
- authorise R6.1 implementation;
- authorise migrations, deployment, or production use;
- authorise staging, committing, or pushing.

The existing settlement-integrity modifications
(`src/sabiroute/api/completions.py`, `tests/test_r6_settlement_integrity.py`)
remain untouched and preserved.

### 0.3 Relationship to the analysis below

Sections 2–8 are retained unchanged as the record of the alternatives considered.
The owner's selections match the pack's recommendations: §2.3 recommended Alt-1,
§3.3 recommended O4-A (the nine-field §3.1 payload), and §4.5 recommended S3+S4.
The owner's **additional safeguards** in the table above are normative and are
carried into the canonical corrections proposal
(`docs/r6-final-o3-o4-o5-canonical-corrections-proposal-2026-11-07.md`).

### 0.4 R6.0-D — corpus durability

R6.0-D is a **repository act**, not a text correction. It is recorded here
because the owner has now selected it alongside O3/O4/O5, and because it gates
the registration act independently of them: even with O3/O4/O5 answered, a
`git clean` or fresh clone would destroy the untracked files the U2 digests bind.

The evidence for R6.0-D is the manifest and privacy review at
`docs/r6-close-final-04-r6.0-d-evidence-manifest-and-privacy-review-2026-11-07.md`.
That document records the SHA-256, byte size and line count of every file in the
R6 governance corpus, flags the three U2-bound files, and reports the privacy
scan. It does **not** track, stage, commit or push anything.

**Ordering (binding).** The acts must occur in this order, each under its own
authority:

1. Apply the canonical corrections C-1…C-7 (separate act; changes
   `protocol_sha256` and `addendum_sha256` — R1).
2. Track the corpus (R6.0-D; separate repository act).
3. Re-derive U2 against the **post-amendment** files.
4. Build genesis from those post-amendment digests.
5. Perform the registration act under separate operational authority.

Building genesis from the current (pre-amendment) digests and amending afterwards
yields a genesis entry that does not match the files it claims to bind.

---

## 1. Executive decision summary

| ID | Blocker | Class | Recommendation | Owner action |
|---|---|---|---|---|
| **O3** | Boundary of the `owner_sha256` digest source for a multi-line owner-response field | **OWNER DECISION** | **Alt-1** — hash the field *value* only, `A3: ` prefix retained, embedded LF preserved, §8-normalised | Select one of three boundaries |
| **O4** | Genesis `entry_sha256` canonicalisation | **OWNER DECISION** (narrow) | **O4-A** — adopt proposal §3.1/§3.2 verbatim | Confirm adoption; resolve duplicate-key rule |
| **O5** | Three mutually incompatible VER/genesis schemas | **OWNER DECISION** | Adopt proposal §3.2/§3.3 as sole normative schema; §6 container superseded, field names retained | Approve supersession + 5 text corrections |

**Two corrections to the handoff, established in this session:**

1. **O4's genesis payload has nine fields, not eight.** The handoff stated eight.
   `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md:244-273` defines
   `ledger_id`, `created`, `owner_key_fingerprint`, `protocol_sha256`,
   `addendum_sha256`, `t16_sha256` (six payload fields) plus the envelope
   `seq`, `entry_type`, `prev` — **nine** keys in the canonical line. The
   `t16_sha256` field was missing from the handoff's field list.
2. **R6.0-D's premise is narrower than stated.** `git ls-files docs` returns
   **16** tracked files, not 0. The product documentation *is* tracked. What is
   untracked is the **entire R6 governance corpus** — including all four
   documents this pack depends on. See §8.

---

## 2. O3 — `owner_sha256` boundary for a multi-line owner-response field

### 2.1 Exact ambiguity

The approved rule is: `owner_sha256` is the SHA-256 of the **owner-response
field**, normalised per 03B-R1 §8 (`docs/r6-registration-protocol-03b-r1.md:171-186`).
That rule is not in question and is not changed by this pack.

The ambiguity is what "the field" denotes. The A3 owner response in
`docs/r6-t16-r6-decision-option-register.md:163-164` is:

```
**Owner response:** A3: ADOPT Option A — ADR-1 conditional, explicitly not implemented.··
Acknowledge that P1–P5 remain unmet and that this selection authorises no implementation.
```

(`·` marks a literal space; line 1 ends with **two** trailing spaces — a Markdown
hard line break — followed by one LF.)

Three things are simultaneously undetermined:

- **Label inclusion** — is `**Owner response:**` part of the hashed bytes?
- **Prefix inclusion** — is the `A3: ` decision-ID prefix part of the hashed bytes?
- **Embedded line break** — the value spans two physical lines. §8 step 4 strips
  *leading and trailing* whitespace; step 5 preserves *internal* whitespace
  exactly. The two hard-break spaces sit **internally** (content follows them),
  so §8 preserves them. This is correct but non-obvious, and a naive
  implementation that strips per-line would produce a different digest.

### 2.2 Alternatives

All three were computed in this session against the exact T16 bytes, applying
§8 normalisation (CRLF→LF, CR→LF, NFC, strip leading/trailing, preserve internal,
UTF-8 no BOM, SHA-256, lowercase hex).

| Alt | Boundary | Bytes hashed | `owner_sha256` |
|---|---|---|---|
| **Alt-1** | Field **value** only; `A3: ` prefix **retained**; embedded LF preserved | **163** | `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149` |
| **Alt-1b** | Field **value** only; `A3: ` prefix **stripped** | **159** | `e067ed95785ab190ca658cf1b05e9576d74c98e1b340da421a2fce046e769098` |
| **Alt-2** | **Label + one space + value** (`**Owner response:** A3: …`) | **183** | `35de850fa80b00ecbe2c03b7846b489f3247c251351f53a9456f19176d926ccb` |

All three reproduce the digests recorded in the prior session **exactly**. The
byte-count arithmetic is internally consistent: `183 − 163 = 20` = length of
`**Owner response:**` (19) + one space; `163 − 159 = 4` = length of `A3: `.

**Sensitivity probe (not an alternative, a hazard):** if an implementation strips
the two hard-break spaces as *trailing* whitespace of line 1 rather than treating
them as internal, the result is **161 bytes**,
`fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6` — a fourth,
wrong digest. Any implementation must be tested against this case.

**Alt-3 (single-line canonical form) is not viable for A3.** A3's value is
irreducibly two lines. Collapsing it to one line would require an editorial
decision (join with space? drop the second sentence?) that the approved rule does
not license, and would change the recorded decision text — prohibited by
`PARAM-A.6` (`docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md:118-125`).
Alt-3 is therefore available only as a **prospective** rule for future
registrations, not as a boundary for A3.

### 2.3 Recommendation

**Adopt Alt-1 for A3, and Alt-3 as a prospective rule.**

- **Retroactive boundary (A3):** Alt-1 — value only, `A3: ` prefix retained,
  embedded LF preserved, §8-normalised. `owner_sha256` =
  `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149`, 163 bytes.
- **Prospective rule:** every owner response registered from 2026-11-07 onward
  must be a **single physical line**. A multi-line response is registrable only
  under Alt-1 with its byte length and digest recorded alongside, and any
  response whose normalised form cannot be reproduced deterministically **fails
  closed** (`MALFORMED OWNER RESPONSE`) rather than being silently repaired.

### 2.4 How this implements the already-approved rule

The approved rule says the digest source is *the owner-response field*. Alt-1
takes the field's **value** — the text after the label — which is the ordinary
reading of "the field" in a `**Label:** value` construct. It does **not**:

- change the normalisation regime (§8 is applied unchanged);
- change the digest algorithm or encoding;
- alter any T16 decision text or identifier (`PARAM-A.6` preserved);
- require migration of any already-recorded digest.

Alt-1b would require an editorial normalisation (stripping `A3: `) that the rule
does not authorise. Alt-2 would fold the Markdown label into the hashed bytes,
making the digest sensitive to presentation markup — a property the rule does not
ask for and which would break if the label were ever reworded.

**Residual risk accepted under Alt-1:** the digest is sensitive to the two
hard-break spaces. This is a real fragility, mitigated by the prospective
single-line rule and by the 161-byte negative test vector in §2.2.

---

## 3. O4 — Genesis `entry_sha256` canonicalisation

### 3.1 What is actually open

The handoff described O4 as an undefined canonicalisation. That is **not** the
case. `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md:212-243` (§3.1)
already specifies canonical JSON in full:

- object keys sorted ascending by Unicode code point;
- no whitespace between tokens; separators `,` and `:`;
- strings JSON-escaped per RFC 8259, non-ASCII emitted as literal UTF-8
  (`ensure_ascii=false`), `/` not escaped;
- integers in decimal, no leading zeros, no `+`, no exponent;
- no BOM; no trailing newline in the hashed bytes;
- the on-disk line is the same bytes followed by exactly one `LF`;
- `entry_sha256` = SHA-256 of the canonical JSON bytes **excluding** the
  terminating `LF`, lowercase hex.

The genesis `prev` constant is also already fixed and was **verified in this
session**:

```
SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))
  = e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307   ✓ matches §3.2 / §4.3
```

So O4 is not "define canonicalisation". O4 is: **adopt §3.1/§3.2 as normative,
and close the two gaps §3.1 leaves open** — duplicate keys, and the choice
between the proposal's bespoke canonical JSON and RFC 8785 JCS.

### 3.2 Field set (nine fields, corrected)

| # | Field | Type | Genesis value | Source |
|---|---|---|---|---|
| 1 | `addendum_sha256` | string, 64 lowercase hex | whole-file digest of the owner-parameter addendum | §3.2 |
| 2 | `created` | string, `YYYY-MM-DD` UTC | actual creation date (`PARAM-C.1`) | §3.2 |
| 3 | `entry_type` | string | `"GENESIS"` (uppercase) | §3.1 |
| 4 | `ledger_id` | string | first-execution parameter (**D-U3-2, open**) | §3.2 |
| 5 | `owner_key_fingerprint` | string, `SHA256:<base64>` | owner Ed25519 public key (`PARAM-D.4`) | §3.2 |
| 6 | `prev` | string, 64 lowercase hex | `e893bd2c…d307` (domain-separated constant) | §3.2 |
| 7 | `protocol_sha256` | string, 64 lowercase hex | whole-file digest of `docs/r6-registration-protocol-03b-r1.md` | §3.2 |
| 8 | `seq` | integer | `0` | §3.1 |
| 9 | `t16_sha256` | string, 64 lowercase hex | whole-file digest of the canonical decision register | §3.2 |

**Note on field 5:** `SHA256:<base64>` contains `+`, `/` and `=` characters.
`/` is explicitly **not** escaped per §3.1, so the base64 payload appears
literally in the JSON string. Any implementation that escapes `/` as `\/`
produces a different digest. This is a concrete interop hazard and must be in the
conformance test set.

### 3.3 Alternatives

| Alt | Canonicalisation | Preimage | Assessment |
|---|---|---|---|
| **O4-A** | Proposal §3.1 verbatim: sorted keys, compact separators, `ensure_ascii=false`, `/` unescaped, decimal integers | Canonical JSON bytes **without** terminating LF | **Recommended.** Consistent with the `VER` entry rule in the same section, so one newline convention governs the whole ledger. |
| **O4-B** | RFC 8785 JCS instead of bespoke rules | JCS bytes without LF | Viable. Proposal §5 deviation 5 (`:487-511`) offers this as a drop-in. All values are strings or non-negative integers, so JCS's number-formatting edge cases do not arise — the two regimes are **byte-identical for this field set**. Adopting JCS buys a published standard at no cost. |
| **O4-C** | Proposal §3.1 rules, but preimage **includes** the terminating LF | Canonical JSON bytes **plus** one LF | Not recommended. Would make `entry_sha256` inconsistent with the `VER` entry rule in the same section, and would make the digest sensitive to the file's final-newline state. |

**O4-A and O4-B produce identical bytes for the genesis field set.** The choice
is therefore about *which specification to cite*, not about output. O4-A is
recommended because it is what the proposal already says and what the reviewer
has already read; O4-B is a defensible substitute if the owner prefers a
published standard.

### 3.4 Gap §3.1 does not close: duplicate keys

Neither §3.1 nor JCS specifies behaviour when a JSONL line contains a duplicate
object key. Two parsers can disagree (last-wins vs first-wins vs reject), which
would let two implementations compute different digests over the "same" line.

**Required addition (normative):** a ledger line containing a duplicate key is
**malformed** and must be rejected (`MALFORMED LEDGER ENTRY`). It is never
repaired, never last-wins, never first-wins. This must be stated in §3.1 before
the schema is adopted, because it is the one place where a conforming
implementation could otherwise diverge silently.

### 3.5 Worked synthetic example — fully computable

The proposal's own example at `:265-267` is **not computable**: it contains the
placeholders `"created":"YYYY-MM-DD"` and `"ledger_id":"<LEDGER_ID>"`. The
example below is fully specified and was computed in this session.

**Stated inputs** (each derived from a literal, so the example is reproducible):

```
addendum_sha256       = SHA-256("sabiroute-r6-addendum-synthetic")
                      = 48db6807cc29c94aac2e54d180afdbcb31d28ace9f0f59a74257bdbd2b875543
protocol_sha256       = SHA-256("sabiroute-r6-protocol-03b-r1-synthetic")
                      = 8d28e088aa339772d27c06972ddecb082ac1d95623e75b0ea425f5d9e5936b00
t16_sha256            = SHA-256("sabiroute-r6-t16-synthetic")
                      = 98265a68719eb9083e947b2b6e5505a3915b8cf9c9abda2e5744cab0b6cb5bf1
owner_key_fingerprint = "SHA256:" + base64(SHA-256("sabiroute-r6-owner-ed25519-synthetic"))
                      = SHA256:aw43FRUN+TUl6EV2fmgTIrMmG9Cz3zKWI5qo5Y4/hO4=
ledger_id             = f47ac10b-58cc-4372-a567-0e02b2c3d479
created               = 2026-11-07
prev                  = e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307
seq                   = 0
entry_type            = GENESIS
```

**Canonical genesis line** (508 bytes, no trailing LF in the hashed preimage):

```json
{"addendum_sha256":"48db6807cc29c94aac2e54d180afdbcb31d28ace9f0f59a74257bdbd2b875543","created":"2026-11-07","entry_type":"GENESIS","ledger_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","owner_key_fingerprint":"SHA256:aw43FRUN+TUl6EV2fmgTIrMmG9Cz3zKWI5qo5Y4/hO4=","prev":"e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307","protocol_sha256":"8d28e088aa339772d27c06972ddecb082ac1d95623e75b0ea425f5d9e5936b00","seq":0,"t16_sha256":"98265a68719eb9083e947b2b6e5505a3915b8cf9c9abda2e5744cab0b6cb5bf1"}
```

**Resulting digests:**

| Preimage | Bytes | `entry_sha256` |
|---|---|---|
| Canonical line, **no** LF (O4-A / O4-B) | 508 | `ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28` |
| Canonical line **plus** one LF (O4-C) | 509 | `452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe` |

Key order produced by code-point sort:
`addendum_sha256`, `created`, `entry_type`, `ledger_id`, `owner_key_fingerprint`,
`prev`, `protocol_sha256`, `seq`, `t16_sha256`.

### 3.6 Reproducibility procedure

Any implementation claiming conformance must reproduce
`ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28` from the
stated inputs. The reference computation is:

```python
import hashlib, json, base64
h = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
obj = {
  "addendum_sha256": h("sabiroute-r6-addendum-synthetic"),
  "created": "2026-11-07",
  "entry_type": "GENESIS",
  "ledger_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "owner_key_fingerprint": "SHA256:" + base64.b64encode(
      hashlib.sha256(b"sabiroute-r6-owner-ed25519-synthetic").digest()).decode(),
  "prev": h("R6-VER-LEDGER-GENESIS:v1"),
  "protocol_sha256": h("sabiroute-r6-protocol-03b-r1-synthetic"),
  "seq": 0,
  "t16_sha256": h("sabiroute-r6-t16-synthetic"),
}
line = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
assert hashlib.sha256(line.encode("utf-8")).hexdigest() == \
    "ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28"
```

**Negative test vectors** that must also be in the conformance set:

| Mutation | Expected |
|---|---|
| Append one LF to the preimage | `452a05bb…bbbe` (must **not** equal the genesis digest) |
| Escape `/` as `\/` in `owner_key_fingerprint` | different digest — must be rejected as non-canonical |
| Reorder keys | different digest — must be rejected as non-canonical |
| Insert a space after `:` | different digest — must be rejected as non-canonical |
| Duplicate `seq` key | **fail closed** (`MALFORMED LEDGER ENTRY`) |
| `seq` as `0.0` or `"0"` | **fail closed** (integer required) |

---

## 4. O5 — Three incompatible VER / genesis schemas

### 4.1 The three schemas, with exact sources

| # | Source | Container | Fields | Chain |
|---|---|---|---|---|
| **S1** | `docs/r6-registration-protocol-03b-r1.md:110-135` (§6) | HTML comment `<!-- VER:v1 … -->` | 6: `decision`, `verifier`, `verified`, `result`, `marker_sha256`, `items_checked` | none |
| **S2** | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md:93-99` (`PARAM-A.2`) | "a distinct append-only verification ledger" — **form unspecified** | unspecified | unspecified |
| **S3** | `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md:275-292` (§3.3) | JSONL line in the append-only ledger | 8 payload: S1's six **plus** `card_sha256`, `file_sha256`; envelope `seq`, `prev`, `entry_type`, `entry_sha256` | full hash chain |
| **S4** | `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md:244-273` (§3.2) | JSONL line, `seq=0` | 9 (see §3.2 above) | genesis of the chain |

### 4.2 Field-level diff

| Field | S1 (§6) | S3 (§3.3) | Conflict |
|---|---|---|---|
| `decision` | ✓ | ✓ | none |
| `verifier` | ✓ | ✓ | none |
| `verified` | ✓ | ✓ | none |
| `result` | ✓ `PASS`\|`FAIL` | ✓ same domain | none |
| `marker_sha256` | ✓ | ✓ | none |
| `items_checked` | ✓ | ✓ | none |
| `card_sha256` | ✗ | ✓ | **S3 adds** |
| `file_sha256` | ✗ | ✓ | **S3 adds** |
| `seq` | ✗ | ✓ | **S3 adds** |
| `prev` | ✗ | ✓ | **S3 adds** |
| `entry_type` | ✗ | ✓ | **S3 adds** |
| `entry_sha256` | ✗ | ✓ | **S3 adds** |

### 4.3 Conflicts that matter

1. **Container conflict (S1 vs S2).** §6 says verification is "a separate
   structured comment". `PARAM-A.1` (`:87-92`) places the REG record *adjacent to
   T16*; a comment written into that same file is therefore **co-located** with
   the REG record — which `PARAM-A.2` explicitly forbids ("never co-located with
   the REG record they verify"). **S1 as written violates S2.** This is a direct
   contradiction between two approved documents, not a gap.

2. **Chainability conflict (S1 vs D-U3-1).** S1 has no `seq`, `prev` or
   `entry_sha256`. The approved decision **D-U3-1** (checkpoint after every VER
   entry) requires a chain head to sign. **D-U3-1 is unimplementable under S1.**
   Any VER record conforming to §6 cannot be anchored.

3. **Field-count conflict (S1 vs S3).** S3 carries two content digests
   (`card_sha256`, `file_sha256`) that S1 lacks. Under S1, a VER record does not
   bind to the content it verified — it binds only to the marker. That is a
   materially weaker guarantee and is the specific weakness U1/U2 were created to
   close.

4. **Genesis has no counterpart in S1 or S2.** S4 is purely additive; it does not
   conflict, it is simply absent from the two approved documents.

5. **`PARAM-A.4` still assumes S1's grammar.** `:110-116` says COMPLETE is valid
   only when "a matching `VER:v1` record has `result=PASS`". This is compatible
   with S3 **only because S3 preserves the six field names and the `result`
   domain verbatim**. If S3 had renamed any field, `PARAM-A.4` would break.

### 4.4 Effect on owner decisions

| Decision | Status under S1 | Status under S3/S4 |
|---|---|---|
| **D-U3-1** checkpoint cadence | **Unimplementable** — no chain head exists | Implementable |
| **D-U3-2** `ledger_id` scheme | Not required | **Required** (genesis field 4) |
| **D-U3-3** `allowed_signers` identity | Not required | **Required** (§3.4) |
| `PARAM-A.2` separate ledger | **Violated** by S1's comment container | Satisfied |
| `PARAM-A.4` COMPLETE derivation | Satisfied | Satisfied (field names preserved) |

### 4.5 Recommendation

**Adopt S3 + S4 (proposal §3.2/§3.3) as the single normative schema.**

- S1's **container** ("a separate structured comment") is **superseded**.
- S1's **six field names and the `result` domain are retained verbatim**, so
  `PARAM-A.4` continues to hold without amendment to its substance.
- S2 is **satisfied** by the JSONL ledger and needs only its form named.
- S4 is adopted as the genesis record, with the nine-field set of §3.2 above.

**Passages requiring correction (five):**

| # | File | Lines | Current text | Required change |
|---|---|---|---|---|
| 1 | `r6-registration-protocol-03b-r1.md` | `:112` | "Verification is a separate structured comment:" | "Verification is a separate append-only ledger entry (`PARAM-A.2`), one canonical JSON object per line:" |
| 2 | `r6-registration-protocol-03b-r1.md` | `:114-117` | fenced `<!-- VER:v1 … -->` block | replace with the S3 JSONL field table; retain the six field names |
| 3 | `r6-registration-protocol-03b-r1.md` | `:130-135` | "a matching VER record exists" | "a matching VER **ledger entry** exists" |
| 4 | `r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | `:93-99` | "a distinct append-only verification ledger" | append: "— realised as the JSONL ledger of proposal §3.1–§3.3, one canonical JSON object per line" |
| 5 | `r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | `:110-116` | "a matching `VER:v1` record has `result=PASS`" | "a matching VER ledger entry has `result=PASS`" |

**Not corrected by this pack:** the `VER:v1` token itself. It appears in §6 and
`PARAM-A.4` as a grammar name. Retaining it as the *field-name set* identifier
(while the container changes) is the least invasive option and keeps
`PARAM-A.4` intact. If the owner prefers to retire the token entirely, that is a
sixth correction and a larger edit.

---

## 5. Consolidated normative schema

The single schema that results from adopting O3-Alt-1, O4-A and O5-S3/S4.

### 5.1 Ledger file

- UTF-8, no BOM, LF-terminated, one canonical JSON object per line (JSONL).
- Append-only: appending never rewrites prior lines (`PARAM-E.7`).
- Duplicate keys in any line → **fail closed** (`MALFORMED LEDGER ENTRY`).

### 5.2 Envelope (every entry)

| Field | Type | Rule |
|---|---|---|
| `seq` | integer | `0` at genesis, `+1` per entry, no gaps |
| `prev` | string | previous `entry_sha256`; genesis uses the domain constant |
| `entry_type` | string | `"GENESIS"` or `"VER"` |
| `entry_sha256` | string | SHA-256 of canonical JSON bytes **excluding** terminating LF |

### 5.3 Genesis (`seq = 0`)

Nine fields as tabulated in §3.2. `prev` =
`e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307`.

### 5.4 VER entry (`seq = n`)

Eight payload fields: `decision`, `verifier`, `verified`, `result`,
`marker_sha256`, `items_checked`, `card_sha256`, `file_sha256`.

### 5.5 Canonical JSON

As §3.1 of the proposal, plus the duplicate-key rule of §3.4 above.

### 5.6 Owner-response digest (O3)

`owner_sha256` = SHA-256 over the **field value** (label excluded, `A3: ` prefix
retained), §8-normalised, embedded LF preserved. A3 =
`97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149` (163 bytes).

---

## 6. Cross-decision compatibility matrix

| | O3-Alt-1 | O3-Alt-1b | O3-Alt-2 | O4-A | O4-B | O4-C | O5-S3/S4 |
|---|---|---|---|---|---|---|---|
| **O3-Alt-1** | — | ✗ different digest | ✗ different digest | ✓ | ✓ | ✓ | ✓ |
| **O3-Alt-1b** | ✗ | — | ✗ | ✓ | ✓ | ✓ | ✓ |
| **O3-Alt-2** | ✗ | ✗ | — | ✓ | ✓ | ✓ | ✓ |
| **O4-A** | ✓ | ✓ | ✓ | — | ✓ identical bytes | ✗ | ✓ |
| **O4-B** | ✓ | ✓ | ✓ | ✓ identical bytes | — | ✗ | ✓ |
| **O4-C** | ✓ | ✓ | ✓ | ✗ | ✗ | — | ✗ inconsistent newline rule |
| **O5-S3/S4** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | — |

**Reading:** O3 and O4 are **orthogonal** — the owner-response digest and the
ledger canonicalisation never touch the same bytes, so any O3 choice combines
with any O4 choice. O4 and O5 are **coupled**: O4-C (LF in preimage) contradicts
S3's own `entry_sha256` rule, so O4-C is only available if O5 is *not* adopted.
O4-A and O4-B are byte-identical for this field set and therefore fully
interchangeable.

**Only one combination is internally consistent with all approved decisions:**
O3-Alt-1 + O4-A (or O4-B) + O5-S3/S4.

---

## 7. Exact proposed wording for protocol incorporation

### 7.1 New §6.0 — Owner-response digest boundary (O3)

> **§6.0 Owner-response digest boundary.**
> `owner_sha256` is the SHA-256 of the **value** of the owner-response field,
> normalised under §8. The field label (`**Owner response:**`) is excluded. Any
> decision-ID prefix present in the value (for example `A3: `) is **retained**.
> Embedded line breaks are internal whitespace under §8 step 5 and are preserved
> exactly; they are never collapsed, joined or stripped. A response whose
> normalised form cannot be reproduced deterministically fails closed as
> `MALFORMED OWNER RESPONSE` and is never repaired.
> From 2026-11-07, every newly registered owner response must be a single
> physical line. A multi-line response is registrable only with its normalised
> byte length and digest recorded alongside the entry.

### 7.2 New §6.1 — Canonical JSON and duplicate keys (O4)

> **§6.1 Canonical JSON.**
> Canonical JSON is defined by proposal §3.1: keys sorted ascending by Unicode
> code point; no whitespace between tokens; separators `,` and `:`; RFC 8259
> string escaping with non-ASCII emitted as literal UTF-8 and `/` **not**
> escaped; integers in decimal with no leading zeros, no `+` and no exponent; no
> BOM. `entry_sha256` is the SHA-256 of these bytes **excluding** the terminating
> `LF`; the on-disk line is the same bytes followed by exactly one `LF`.
> A line containing a duplicate object key is malformed and is rejected as
> `MALFORMED LEDGER ENTRY`. It is never resolved last-wins or first-wins.

### 7.3 Replacement for §6 container sentence (O5)

> Verification is recorded as a separate append-only ledger entry under
> `PARAM-A.2`, one canonical JSON object per line, and is never co-located with
> the REG record it verifies. The entry carries the six `VER:v1` fields
> (`decision`, `verifier`, `verified`, `result`, `marker_sha256`,
> `items_checked`) plus `card_sha256` and `file_sha256`, and the envelope
> `seq`, `prev`, `entry_type`, `entry_sha256`.

### 7.4 Addendum `PARAM-A.2` — appended clause

> The ledger is realised as the JSONL structure of proposal §3.1–§3.3: UTF-8,
> LF-terminated, one canonical JSON object per line, hash-chained by
> `entry_sha256`, genesis at `seq = 0`.

---

## 8. R6.0-D — evidence durability

### 8.1 The condition

R6.0-D requires that registration evidence bind content that is **tracked and
committed**, so that every digest in the evidence bundle is reproducible from a
git object reachable from a ref. A digest over working-tree bytes that exist in
no commit is not durable evidence: it cannot be re-derived by a third party, and
it silently changes if the file is edited.

### 8.2 Actual state (measured this session)

| Measurement | Result |
|---|---|
| `git ls-files docs \| wc -l` | **16** |
| `git diff --cached --name-only \| wc -l` | **0** |
| `docs/r6-registration-protocol-03b-r1.md` | **UNTRACKED** |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | **UNTRACKED** |
| `docs/r6-t16-r6-decision-option-register.md` | **UNTRACKED** |
| `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md` | **UNTRACKED** |

**The handoff's statement that `git ls-files docs` returns 0 is incorrect.** The
product documentation is tracked. The defect is narrower and more serious than
stated: **the entire R6 governance corpus is untracked**, including all four
documents this pack depends on.

### 8.3 Consequence

The three digests the genesis record depends on —

- `protocol_sha256` (of `r6-registration-protocol-03b-r1.md`),
- `addendum_sha256` (of the owner-parameter addendum),
- `t16_sha256` (of the decision register),

— are digests of **untracked working-tree files**. They are not reproducible from
any git object. The proposal's own example values
(`2ff885e3…`, `3a003632…`, `43c7331c…` at `:265-267`) are therefore
**unverifiable by a third party**, and would change silently on any edit.

**R6.0-D is NOT MET.**

### 8.4 Smallest valid way to satisfy it

**Option D-1 (recommended): commit the R6 governance corpus.**
A single dedicated commit adding the `docs/r6-*.md` files, **excluding** the two
modified settlement files (`src/sabiroute/api/completions.py`,
`tests/test_r6_settlement_integrity.py`), which are unrelated to this work and
must not be swept in. After that commit, all three digests are reproducible from
a git object and R6.0-D is met.

**Option D-2: owner-dated explicit acceptance of untracked-corpus risk.**
Record in the evidence bundle that the digests bind untracked working-tree bytes,
with the owner's dated acknowledgement. This satisfies the *letter* of a
risk-acceptance but leaves the digests unverifiable by any third party, which
defeats the purpose of the digest. **Not recommended.**

**Option D-3: defer R6.0-D.** Register the decisions now, mark R6.0-D as
`DEFERRED — EVIDENCE NOT DURABLE`, and re-derive the digests after the corpus is
committed. This is honest but leaves the ledger genesis anchored to
non-durable content, which is precisely what the checkpoint mechanism exists to
prevent.

**This pack does not execute any of these.** No file was staged, committed or
pushed.

---

## 9. Exact owner decisions required

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **1** | O3 boundary | Alt-1 / Alt-1b / Alt-2 | **Alt-1** (`97dc52a6…f149`, 163 bytes) |
| **2** | O3 prospective rule | single-line required / no rule | **single-line required** from 2026-11-07 |
| **3** | O4 canonicalisation | O4-A / O4-B / O4-C | **O4-A** (O4-B byte-identical) |
| **4** | O4 duplicate keys | fail closed / last-wins / first-wins | **fail closed** |
| **5** | O5 schema | S3+S4 / retain S1 / defer | **S3+S4**, S1 container superseded |
| **6** | O5 `VER:v1` token | retain as field-set name / retire | **retain** (keeps `PARAM-A.4` intact) |
| **7** | R6.0-D | D-1 commit corpus / D-2 accept risk / D-3 defer | **D-1** |
| **8** | D-U3-2 `ledger_id` scheme | fixed string / date-stamped | owner's call — required before genesis |
| **9** | D-U3-3 `allowed_signers` identity | e.g. `owner@r6` | owner's call — required before checkpoint |

Decisions 1–7 are resolvable from this pack. Decisions 8–9 are first-execution
parameters that this pack cannot supply.

**Recorded 2026-11-07:** the owner selected decisions 1–7 as recommended, with the
additional binding safeguards recorded in §0. Decision 8 is carried forward as
D-U3-2 (UUIDv4 `ledger_id`); decision 9 is carried forward as D-U3-3 (signer
principal `sabiroute-r6-owner`). The actual UUIDv4 value and public-key
fingerprint remain first-execution values and are not supplied by this pack.

---

## 10. Shortest remaining closure sequence

1. **Owner selects decisions 1–7** (this pack).
2. **Apply the five text corrections** of §4.5 and the four wording insertions of
   §7 to the protocol and addendum. *(Not done — requires owner approval.)*
3. **Owner supplies D-U3-2 and D-U3-3.**
4. **Commit the R6 governance corpus** (D-1), excluding the two settlement files.
5. **Re-derive** `protocol_sha256`, `addendum_sha256`, `t16_sha256` from the
   committed blobs.
6. **Compute the genesis line** and its `entry_sha256` using the §3.6 reference
   implementation; verify against the negative vectors of §3.6.
7. **Owner signs the genesis checkpoint** (§3.4 of the proposal).
8. **Register A1–A4, B1–B9, C1–C4, D1–D6** (23 decisions) under the consolidated
   schema of §5.
9. **Independent verification** by Claude Desktop, one VER entry per decision,
   checkpointed per D-U3-1.
10. **Post-COMPLETE read-back** (03B-R1 §15) before any COMPLETE state is
    reported.

Steps 1–3 are owner actions. Steps 4–10 are execution and are **not authorised by
this pack**.

---

## 11. Attestation

- No file was staged, committed or pushed in producing this pack.
- No canonical document was modified. The five corrections in §4.5 and the four
  insertions in §7 are **proposals**, not applied edits.
- All digests in §2.2, §3.1 and §3.5 were computed in this session against the
  working tree at HEAD `08201da8`.
- The three O3 digests reproduce the prior session's recorded values exactly.
- The genesis constant `e893bd2c…d307` was independently re-derived and matches
  proposal §3.2 and §4.3.
- Two handoff figures were found incorrect and are corrected in §1: the genesis
  field count (nine, not eight) and the tracked-docs count (16, not 0).

**Git state — before this pack:** HEAD `08201da8`, branch
`feat/sabiroute-routing-foundation`, 2 modified tracked files, 0 staged, 16
tracked files under `docs/`.

**Git state — after this pack:** unchanged, plus this file as a new untracked
path. No staging, no commit, no push.
