# R6.0 — WP-2 DECISION CLARIFICATION ADDENDUM

**Actor:** Claude Code Desktop (coordinator — **not** the independent verifier)
**Date:** 2026-11-10 (WP-2 line date, matching the sibling artefacts in this directory)
**Scope:** Restore the complete original framing of O1–O5 and R6.0-D so the owner can answer the
WP-2 decision set without answering a collapsed rendering of it.
**Status:** Clarification only · **WP-2 remains BLOCKED** pending the owner answers in §6.2
**Relationship to siblings:** supplements `wp2-final-owner-decision-pack-2026-11-10.md` (the corrected
pack) and `wp2-consolidated-decision-pack-2026-11-10.md` (retained historical record). **Supersedes
neither.** Where this addendum disagrees with either, the disagreement is stated in §5.

> **This document decides nothing, approves nothing and edits nothing.** It re-presents source that
> already exists, so that a selection is made against the real option space. Every claim below is
> traceable to a file and line in §9; where evidence is missing, it is recorded as missing rather
> than filled in.

---

## 0. Why this addendum exists

A successor brief is reported to have rendered **O5 as a single binary — "Option C — hybrid, yes/no"**
— without the original framing. If that is what reached the owner, then the owner has been invited to
answer a question that the record does not contain.

Three things go wrong when a multi-part owner decision is flattened to a yes/no:

1. **The option space disappears.** O5 was never a binary. It was four competing schema
   *representations* (S1–S4) with a composite recommendation and a five-passage correction set.
2. **"Yes" stops being decidable.** A single yes cannot say which of five corrections is approved,
   nor whether the optional sixth is in scope.
3. **The label collides.** `Option C` already carries four unrelated meanings in this corpus, one of
   which (`O4-C`) is an explicitly *not-recommended* alternative. A bare "Option C" is therefore
   ambiguous in a way that can invert the owner's intent. See §3.

This addendum restores the framing. It does not re-open anything the owner has already decided; §6
separates what is settled from what is genuinely open.

---

## 1. Evidence basis — what this addendum could and could not verify

Everything below was read from the working tree in this session. Nothing was carried from memory.

| Item | Result |
|---|---|
| Original O3/O4/O5 framing | **Located** — `docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §2–§4 |
| Owner selections for O3/O4/O5 + R6.0-D | **Located** — same file, §0 (`:17-30`) |
| `PARAM-A.1/.2/.4/.6/.7`, `PARAM-B.1/.3/.5/.6` live text | **Located** — owner-parameter addendum §3–§4 |
| 12-key VER field set | **Located, but only as a diff** — proposal §3.3 + envelope §5.2; **no approved consolidated table exists** (§7) |
| Original framing of **O1** and **O2** | **NOT LOCATED** — see §4.0. Not reconstructed. |
| The "successor brief" itself | **NOT PRESENT in this workspace** — see §1.1 |
| Build map §1.3/§9 (cited as authority for the U2 refresh) | **NOT PRESENT** — `find` over the repository (excluding `.git`/`node_modules`) returns no build-map file |
| Claude Code Terminal return | **UNRECEIVED** — `list_sessions(linked=true)` returns "No other sessions found" |
| Live baseline | **`sec/deps-nov` @ `1e69ada943f3d3921122219e7a569cdff989d3fd`** — the declared `feat/sabiroute-routing-foundation @ 08201da8…` is an ancestor, not the working branch (P3, unchanged) |

### 1.1 The successor brief is unverified here, and this matters

No document in `docs/` or `artifacts/` is a "successor brief". The phrase, and the collapsed O5
binary, reached this session **only through the owner's description**.

Consequently this addendum does **not** quote the successor brief, does not attribute the collapse to
a named file, and does not assert what else it may have altered. It does one thing only: it restates
the O1–O5 framing **from source**, so that whatever the successor brief said can be checked against
the record by the owner. If the successor brief turns out to be accurate on some point, this
addendum does not dispute it; §5 addresses only the specific O5 collapse the owner described.

**Handoff requirement for any future brief:** a brief that re-renders an owner decision must cite
file, line range and verbatim quoted text for the option set it restates. A restatement without
provenance cannot be reconciled against a decision the owner already made.

---

## 2. The five items, and the two structural choices

The WP-2 directive's phrase "five open parameters (O1–O4)" is arithmetically short by one: the
record carries **O1, O2, O3, O4 and O5** — five. O5 is the fifth and is the one the successor brief
flattened, which is very likely why it dropped out of the count.

| ID | Subject | Parameter it produced | Owner selection recorded |
|---|---|---|---|
| **O1** | REG-marker digest (`marker_sha256`, U4) | `PARAM-B.6` | Recorded; framing **not located** (§4.0) |
| **O2** | Digest source = the exact Owner response field | absorbed into `PARAM-B.1` via O3 | Recorded; framing **not located** (§4.0) |
| **O3** | Boundary of `owner_sha256` for a multi-line response | `PARAM-B.1` (multi-line rule) | **Alt-1**, 2026-11-07 |
| **O4** | Genesis `entry_sha256` canonicalisation | `PARAM-B.5` | **Nine-field payload + safeguards**, 2026-11-07 |
| **O5** | Three incompatible VER/genesis schemas | `PARAM-A.7` | **JSONL VER ledger authoritative**, 2026-11-07 |

**The two structural choices**, recorded alongside them in the same §0 and distinct from O1–O5:

| ID | Subject | Owner selection |
|---|---|---|
| **R6.0-D** | Corpus durability — the R6 governance corpus must be tracked in Git **before** the registration act | Selected 2026-11-07; **not executed** |
| **R6.0-D ordering** | The five-step act sequence (corrections → track → re-derive U2 → build genesis → register) | Binding; already decided — the "auditability paradox" raised against it was **withdrawn** (F-WP2-1) |

R6.0-D is a **repository act**, not a text correction, and it is **not** in WP-2's authority (§8).

---

## 3. Identifier collisions — resolve before answering anything

The corpus carries **four** meanings of `Option C` and **two** unrelated `O1`/`O2` series. Any answer
given using a bare label is at risk of being misfiled.

| Label as written | Which register | What it actually means | Source |
|---|---|---|---|
| `Option C — hybrid` | **none** | **No such label exists in the corpus** (§5.1) | — |
| `O4-C` | O4 alternatives | §3.1 rules but preimage **includes** the terminating LF — **explicitly NOT recommended** | pack §3.3 `:270` |
| `Option C` (RTK) | 2026-11-04 supplement | RTK architecture — two-stage | supplement `:218-222` |
| `Option C` (Q5) | 2026-11-04 supplement | B6 measurement — dual measurement; held at `MISSION-FRAMED` | supplement `:290-302` |
| `Option C` (telemetry) | T10/T11 | The **rejected** inline synchronous fail-closed telemetry shape | T10 `:316`; T11 `:32` |
| `Option C` (F-27) | ADR | `_ACCOUNTING_LINEAGES` table — **authorised** 2026-10-29 | ADR `:196` |
| `O1` / `O2` (retry) | campaign §9.3 | Retry headroom: O1 natural headroom / O2 pinned estimate | campaign `:262-263` |
| `O1` / `O2` (registration) | this document | `marker_sha256` / digest source | addendum `PARAM-B.6` |

**Rule for the owner's answers:** qualify every identifier — `O5`, `O4-C`, `PARAM-B.6`,
`WP2-D2`. A bare `Option C` must never be used, for the same reason the addendum's namespace rule
forbids a bare `C-1` (addendum `:95-100`).

---

## 4. The original framing, restored

### 4.0 O1 and O2 — recorded, but their option sets are not in this corpus

**This is an evidence gap, and it is stated rather than filled.** O1 and O2 are decided and are
cited by the bindings they produced, but **no document in this workspace frames them as a decision
with enumerated options and consequences.** Enumerating options for them here would be invention and
is refused.

What the record *does* establish:

- **O1 → `PARAM-B.6`** (`marker_sha256`, U4). Its normative definition is recorded in full at
  addendum `:254-263`: `marker_sha256` is the SHA-256 of the **complete canonical `REG:v1` marker
  bytes**, including the literal opening `<!--` and closing `-->`, **excluding** the terminating line
  break; nothing before `<!--` or after `-->` is hashed. It is a class distinct from `owner_sha256`,
  which the marker itself carries; `marker_sha256` digests the marker as a syntactic object and is
  carried by the VER record. It must never be substituted for, or derived from, `owner_sha256`.
- **O2 → the digest source.** O2 established that the digest source is **the exact Owner response
  field**. It survives inside O3: the decision-pack O3 cell states *"This preserves O2: the source
  remains the exact Owner response field."* O2 has no independent option set in the record because
  O3 is the question that asked *where inside that field* the boundary falls.

**Consequence for WP-2:** O1 and O2 need no further owner answer. They are decided, their normative
text exists, and §6 does not re-ask them. If the owner believes either had a live option set that is
now missing, that must be raised as **new evidence**, not reconstructed from this addendum.

**Provenance limitation, recorded:** Amendment 1 attributed the O1/O2 selections to a 2026-11-07
owner work order. Amendment 2 (`:24-38`) states that artefact *"has not been independently located in
the available evidence"* and that the owner confirmed O1/O2 **in session on 2026-11-09 UTC**. This
addendum repeats that limitation and does not upgrade it.

---

### 4.1 O3 — Boundary of the `owner_sha256` digest source for a multi-line response

**Exact question.** The approved rule is that `owner_sha256` is the SHA-256 of *the owner-response
field*, normalised per 03B-R1 §8. **That rule is not in question.** The ambiguity is what *"the
field"* denotes, for A3 — a value that spans two physical lines, the first ending in **two trailing
spaces** (a Markdown hard break) then one LF.

Three things were simultaneously undetermined: **label inclusion** (is `**Owner response:**` hashed?),
**prefix inclusion** (is `A3: ` hashed?), and the **embedded line break** (§8 step 4 strips
leading/trailing only; the two hard-break spaces sit *internally*, so §8 preserves them — correct but
non-obvious, and a naive per-line strip produces a different digest).

| Alt | Boundary | Bytes hashed | `owner_sha256` | Consequence |
|---|---|---|---:|---|
| **Alt-1** | Field **value** only; `A3: ` prefix **retained**; embedded LF preserved | **163** | `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149` | Matches the approved rule's ordinary reading of `**Label:** value`. **Digest is sensitive to the two hard-break spaces** — a real fragility. |
| **Alt-1b** | Field **value** only; `A3: ` prefix **stripped** | **159** | `e067ed95785ab190ca658cf1b05e9576d74c98e1b340da421a2fce046e769098` | Requires an editorial normalisation the rule does not authorise. |
| **Alt-2** | **Label + one space + value** (`**Owner response:** A3: …`) | **183** | `35de850fa80b00ecbe2c03b7846b489f3247c251351f53a9456f19176d926ccb` | Makes the digest sensitive to presentation markup; breaks if the label is ever reworded. |
| *(Alt-3)* | Single-line canonical form | — | — | **Not viable for A3.** Its value is irreducibly two lines; collapsing it needs an editorial decision the rule does not license and would change recorded decision text — prohibited by `PARAM-A.6`. Available **only prospectively**. |

**Hazard, not an alternative:** stripping the two hard-break spaces as *trailing* whitespace yields
**161 bytes** / `fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6`. That is a
fourth, **wrong** digest, retained as a **negative conformance vector**. Any implementation must be
tested against it.

**Arithmetic check:** `183 − 163 = 20` = `**Owner response:**` (19) + one space; `163 − 159 = 4` =
length of `A3: `.

**Pack recommendation:** Alt-1 for A3, Alt-3 as a prospective single-line rule.

**Owner selection (2026-11-07):** **Alt-1**, with binding requirements recorded verbatim in pack §0
— hash the exact extracted response value, not the surrounding label; preserve `A3: ` when it forms
part of the value; apply §8 without additional transformation; preserve internal line breaks and
whitespace; do not strip Markdown hard-break spaces merely because they end a visually wrapped line;
exclude the surrounding field label; **reject ambiguous extraction boundaries** rather than silently
choosing an interpretation; retain the 161-byte result as a negative conformance vector. The selection
**does not** authorise rewriting historical responses or changing previously approved decisions.

**Produced:** `PARAM-B.1` multi-line response rule (addendum `:185-198`). **Status:** `NOT APPROVED`
as an approval; decided as a selection.

---

### 4.2 O4 — Genesis `entry_sha256` canonicalisation

**Exact question — corrected from the handoff.** The handoff described O4 as an undefined
canonicalisation. **That was not the case.** Proposal §3.1 already specified canonical JSON in full.
O4 is therefore: **(a)** adopt §3.1/§3.2 as normative, and **(b)** close the two gaps §3.1 left open —
**duplicate keys**, and the choice between bespoke canonical JSON and **RFC 8785 JCS**.

| Alt | Canonicalisation | Preimage | Consequence |
|---|---|---|---|
| **O4-A** | Proposal §3.1 verbatim: sorted keys, compact separators, `ensure_ascii=false`, `/` unescaped, decimal integers | Canonical JSON bytes **without** terminating LF | **Recommended.** Consistent with the VER `entry_sha256` rule in the same section — one newline convention governs the whole ledger. |
| **O4-B** | **RFC 8785 JCS** instead of bespoke rules | JCS bytes without LF | Viable. All values are strings or non-negative integers, so JCS number-formatting edge cases do not arise — **byte-identical to O4-A for this field set**. Buys a published standard at no cost. |
| **O4-C** | §3.1 rules, but preimage **includes** the terminating LF | Canonical JSON bytes **plus** one LF | **NOT recommended.** Makes `entry_sha256` inconsistent with the VER entry rule and sensitive to the file's final-newline state. Digest: `452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe` (509 bytes). |

**Gap §3.1 did not close — duplicate keys (normative addition required).** Neither §3.1 nor JCS
specifies behaviour when a JSONL line contains a duplicate object key. Two parsers can disagree
(last-wins / first-wins / reject), letting two implementations compute different digests over the
"same" line. **Required:** a line containing a duplicate key is **malformed**, rejected as
`MALFORMED LEDGER ENTRY`, never repaired, never last-wins or first-wins.

**Nine genesis fields** (the handoff said eight; `t16_sha256` was missing):

| # | Field | Type | Genesis value |
|---|---|---|---|
| 1 | `addendum_sha256` | 64 lowercase hex | whole-file digest of the addendum |
| 2 | `created` | `YYYY-MM-DD` UTC | actual creation date (`PARAM-C.1`) |
| 3 | `entry_type` | string | `"GENESIS"` (uppercase) |
| 4 | `ledger_id` | string | first-execution parameter (**D-U3-2**) |
| 5 | `owner_key_fingerprint` | `SHA256:<base64>` | owner Ed25519 public key (`PARAM-D.4`) |
| 6 | `prev` | 64 lowercase hex | `e893bd2c…d307` (domain-separated constant) |
| 7 | `protocol_sha256` | 64 lowercase hex | whole-file digest of 03B-R1 |
| 8 | `seq` | integer | `0` |
| 9 | `t16_sha256` | 64 lowercase hex | whole-file digest of the canonical register |

**Normative worked example:** the canonical line is **508 bytes**, `entry_sha256` =
`ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28`; the same line plus one LF is
**509 bytes** / `452a05bb…bbbe`. **Proposal §3.2's own example is illustrative and non-normative** —
it contains `YYYY-MM-DD` and `<LEDGER_ID>` placeholders and must never be used as a test input.

**Interop hazard:** `SHA256:<base64>` contains `+`, `/`, `=`; `/` is **not** escaped, so the payload
appears literally. An implementation that escapes `/` as `\/` produces a different digest. This must
be in the conformance set.

**Owner selection (2026-11-07):** nine-field genesis payload and canonicalisation from proposal §3.1,
subject to the recorded safeguards — include all nine fields including `t16_sha256`; use §3.1
serialisation; **reject duplicate keys before hashing**; distinguish omitted fields from explicit
`null`; enforce field types; use the approved UUIDv4 `ledger_id`; **recompute** `entry_sha256` from
the complete payload rather than trusting a supplied digest; retain the genesis constant and the
worked example as conformance vectors; placeholders are not acceptable test inputs.

**Produced:** `PARAM-B.5` (addendum `:232-252`). **Note:** O4 adopted canonicalisation but **left the
citation choice open** — that residue is **WP2-D6** (O4-A vs O4-B), and it changes **no bytes**.

---

### 4.3 O5 — Three incompatible VER / genesis schemas

**This is the item the successor brief flattened. Here is what was actually on the table.**

#### 4.3.1 The four representations

| # | Source | Container | Fields | Chain |
|---|---|---|---|---|
| **S1** | 03B-R1 §6 `:110-135` | HTML comment `<!-- VER:v1 … -->` | 6: `decision`, `verifier`, `verified`, `result`, `marker_sha256`, `items_checked` | none |
| **S2** | `PARAM-A.2` (addendum `:121-126`) | "a distinct append-only verification ledger" — **form unspecified** | unspecified | unspecified |
| **S3** | Proposal §3.3 `:275-292` | JSONL line in the append-only ledger | 8 payload: S1's six **plus** `card_sha256`, `file_sha256`; envelope `seq`, `prev`, `entry_type`, `entry_sha256` | full hash chain |
| **S4** | Proposal §3.2 `:244-273` | JSONL line, `seq=0` | 9 (see §4.2) | genesis of the chain |

#### 4.3.2 The five conflicts that made this a real decision

1. **Container conflict (S1 vs S2).** §6 says verification is "a separate structured comment".
   `PARAM-A.1` places the REG record **adjacent to T16**; a comment written into that same file is
   therefore **co-located** with the REG record, which `PARAM-A.2` **explicitly forbids**
   ("never co-located with the REG record they verify"). **S1 as written violates S2.** This is a
   direct contradiction between two approved documents, not a gap.
2. **Chainability conflict (S1 vs D-U3-1).** S1 has no `seq`, `prev` or `entry_sha256`. **D-U3-1**
   (checkpoint after every VER entry) needs a chain head to sign. **D-U3-1 is unimplementable under
   S1** — any §6-conforming record cannot be anchored.
3. **Field-count conflict (S1 vs S3).** S3 carries two content digests (`card_sha256`,
   `file_sha256`) that S1 lacks. Under S1 a VER record **does not bind to the content it verified** —
   only to the marker. That materially weaker guarantee is precisely what U1/U2 were created to close.
4. **Genesis has no counterpart in S1 or S2.** S4 is purely additive; it does not conflict, it is
   simply absent from the two approved documents.
5. **`PARAM-A.4` still assumes S1's grammar.** It says COMPLETE is valid only when "a matching
   `VER:v1` record has `result=PASS`". That stays compatible with S3 **only because S3 preserves the
   six field names and the `result` domain verbatim**. Had S3 renamed any field, `PARAM-A.4` breaks.

#### 4.3.3 Effect on already-approved decisions

| Decision | Under S1 | Under S3/S4 |
|---|---|---|
| **D-U3-1** checkpoint cadence | **Unimplementable** — no chain head | Implementable |
| **D-U3-2** `ledger_id` scheme | Not required | **Required** (genesis field 4) |
| **D-U3-3** `allowed_signers` identity | Not required | **Required** (§3.4) |
| `PARAM-A.2` separate ledger | **Violated** by S1's comment container | Satisfied |
| `PARAM-A.4` COMPLETE derivation | Satisfied | Satisfied (field names preserved) |

#### 4.3.4 The recommendation was composite, not binary

**Adopt S3 + S4 as the single normative schema**, which decomposes into four separable commitments:

- S1's **container** ("a separate structured comment") is **superseded**;
- S1's **six field names and the `result` domain are retained verbatim**, so `PARAM-A.4` continues to
  hold **without amendment to its substance**;
- S2 is **satisfied** by the JSONL ledger and needs only its form **named**;
- S4 is adopted as the genesis record, with the nine-field set of §4.2.

**Five correction passages** are required to implement it:

| # | File | Lines | Current text | Required change |
|---|---|---|---|---|
| 1 | 03B-R1 | `:112` | "Verification is a separate structured comment:" | "Verification is a separate append-only ledger entry (`PARAM-A.2`), one canonical JSON object per line:" |
| 2 | 03B-R1 | `:114-117` | fenced `<!-- VER:v1 … -->` block | replace with the S3 JSONL field table; **retain the six field names** |
| 3 | 03B-R1 | `:130-135` | "a matching VER record exists" | "a matching VER **ledger entry** exists" |
| 4 | addendum | `:93-99` | "a distinct append-only verification ledger" | append: "— realised as the JSONL ledger of proposal §3.1–§3.3, one canonical JSON object per line" |
| 5 | addendum | `:110-116` | "a matching `VER:v1` record has `result=PASS`" | "a matching VER ledger entry has `result=PASS`" |

**The optional sixth.** The pack explicitly did **not** correct the `VER:v1` **token** itself. It
appears in §6 and `PARAM-A.4` as a grammar name; retaining it as the *field-name set identifier*
(while the container changes) is the least invasive option and keeps `PARAM-A.4` intact. The pack
states: *"If the owner prefers to retire the token entirely, that is a sixth correction and a larger
edit."*

**Owner selection (2026-11-07):** **"The append-only JSONL VER ledger is authoritative."** The
recorded binding requirements: the three conflicting representations must not remain competing
schemas; REG stays adjacent to the relevant T16 decision card as previously approved; VER entries
reside in the separate append-only JSONL ledger; each VER entry carries the approved sequence and
hash-chain fields including `seq`, `prev`, `entry_sha256`; genesis establishes ledger identity and
initial chain state; **every successfully appended VER entry receives its own checkpoint**, bound to
the ledger identity and corresponding ledger state; **the HTML-comment VER representation in §6 must
not be treated as an alternative authoritative ledger format.**

**Produced:** `PARAM-A.7` (addendum `:153-168`).

---

## 5. What the collapse loses — and why the loss is not cosmetic

### 5.1 `Option C — hybrid` is not a label in any source

`grep` across `docs/` and `artifacts/` returns **no** occurrence of `Option C` in the O-series,
registration-protocol, decision-pack or WP-2 documents. Every hit belongs to a different register
(§3). The O-series never used A/B/C labels: **O3 used Alt-1 / Alt-1b / Alt-2 (plus non-viable
Alt-3); O4 used O4-A / O4-B / O4-C; O5 used S1 / S2 / S3 / S4.**

### 5.2 "Hybrid" is a fair *description* and an unsafe *decision* label

It is true that the adopted O5 outcome is hybrid in substance — S4 genesis, S3 VER entries, S1's
field names retained, S1's container discarded. A reader who calls that "the hybrid" is not
misdescribing the result.

But a **decision label** is what the owner selects, and this one cannot carry the answer:

- It **fuses four separable commitments** (§4.3.4). A yes/no cannot say whether the owner approves
  superseding S1's container, retaining S1's six field names, naming S2's form, or adopting S4 as
  genesis. Those were separately argued and have separately attached consequences.
- It **silently absorbs the five corrections** (§4.3.4 table). Approving the *decision* is not
  approving the *edits* — the distinction the packs already enforce at **WP2-D2** ("The decision (O5)
  is already made; this approves the edits that implement it"). A "yes to the hybrid" cannot tell
  WP-3 which of the five passages to change.
- It **loses the sixth-correction question.** Retiring the `VER:v1` token was deliberately left to
  the owner as a yes/no *within* O5. Collapsing O5 removes the place it was meant to be asked.
- It **loses the reason O5 mattered.** The consequences are not stylistic: under S1, `D-U3-1` is
  *unimplementable* and `PARAM-A.2` is *violated*. An owner answering "hybrid: no" would have no way
  to see that the alternative destroys two already-approved decisions.

### 5.3 The label collides in a way that can invert the answer

`Option C` in this corpus most often denotes something **rejected**: telemetry "Option C" is the
shape T10 **rejected**; `O4-C` is **explicitly not recommended**. An owner reading "Option C —
hybrid: yes/no" may reasonably hesitate, and a "no" could be recorded against the very
canonicalisation the owner already approved under O4, or misread as rejecting the O5 schema that
three approved decisions depend on.

**This is the single most important correction in this addendum: a "yes" and a "no" to
"Option C — hybrid" are both unsafe to record without the decomposition in §4.3.4.**

### 5.4 What is *not* claimed about the successor brief

This addendum does not assert that the successor brief changed any decision, dropped any other item,
or misreported anything else. That document is not in this workspace (§1.1) and has not been read. It
may have included framing not described to this session. Only the O5 collapse described by the owner
is addressed.

---

## 6. Settled versus open — the answer key

Answering a settled decision again would re-litigate it, which the WP-2 directive forbids. This table
exists so the owner can see, per item, whether a question is genuinely live.

### 6.1 Settled — do not re-ask

| Item | Settled by | When | Current status |
|---|---|---|---|
| O3 boundary = Alt-1 (163 bytes, `97dc52a6…`) | Owner selection | 2026-11-07 | Decided; `NOT APPROVED` |
| O4 = nine-field genesis, §3.1 canonicalisation, duplicate-key fail-closed | Owner selection | 2026-11-07 | Decided; `NOT APPROVED` |
| O5 = JSONL VER ledger authoritative; §6 HTML comment not authoritative | Owner selection | 2026-11-07 | Decided; **edits unapplied** |
| R6.0-D five-step ordering (corrections → track → re-derive U2 → genesis → register) | Owner selection | 2026-11-07 | Decided; **not executed** |
| D-U3-1 / D-U3-2 / D-U3-3 | Carried forward | 2026-11-07 | Decided; first-execution values pending |
| O1 → `PARAM-B.6`; O2 → digest source | Recorded | 2026-11-07 / 2026-11-09 | Decided; framing not located (§4.0) |

### 6.2 Genuinely open — the owner's remaining answers

| ID | Question, stated so the collapse cannot recur | Class |
|---|---|---|
| **WP2-D1** | Confirm Amendment 2 as operative provenance authority (2026-11-07 work order = corroborating evidence, not authenticated authority) | Confirmation |
| **WP2-D5** | Confirm the nine-field genesis schema needs **no change**; optional inline-table locality fix rides D8 only | Confirmation |
| **WP2-D6** | Choose the **citation** for canonical JSON: `O4-A` (proposal §3.1) or `O4-B` (RFC 8785 JCS). **Byte-identical for this field set.** | Genuine — low risk |
| **WP2-D7** | Confirm the WP-1 U2 vector refresh (2026-11-09), recording that build-map §1.3/§9 authority is **unverified here** | Confirmation w/ limitation |
| **WP2-D8** | Approve the single-pass stabilisation ordering (edits → embedded reference → recompute vectors **once** → run suite) | Confirmation of a plan |
| **WP2-D2** | Approve the **six-item edit set**: the five §4.3.4 corrections **plus** the consolidated 12-key VER table **plus** the one-line REG/VER asymmetry note. **O5 is already decided; this approves the edits.** | Genuine |
| **WP2-D3** | Confirm O1–O5 are **protocol parameters, not registrable decisions** → no REG locus; withdraw the WP-1 §4 blocker | Genuine (governance act) |
| **WP2-D9** | Approve the five negative-first test groups (VER schema; F7 bound; REG/VER separation; COMPLETE derivation; genesis conformance), authored **after** D8 | Genuine — new scope |
| **WP2-D11** | Approve the new normative `items_checked` bound: `0 ≤ items_checked ≤ 10`; `result=PASS` requires `== 10` | **Genuine — most consequential** |
| **WP2-D12** | Update correction-proposal status banner and stale line counts (349→348, 499→646) | Documentary |
| **O5 sixth correction** | Retire the `VER:v1` **token**, or retain it as the field-name-set identifier? **Never asked in a collapsed rendering.** | Genuine — belongs inside D2 |

**No answer required:** **WP2-D4** (subsumed by D2 — its only live element is the asymmetry note) and
**WP2-D10** (withdrawn, F-WP2-1).

### 6.3 Why WP2-D11 must not ride WP2-D2 silently

`items_checked` is the only F1–F7 item that is **both unfixed and unblocked by policy**. 03B-R1 §6
restricts `result` to `PASS|FAIL` but states **no bound** on `items_checked`; §7 fixes the inventory at
**ten** items; `PARAM-A.4` makes COMPLETE valid on `result=PASS` alone.

**Failure scenario:** an entry with `result="PASS"` and `items_checked=3` satisfies **every rule
currently stated**, and makes a registration `COMPLETE` while **seven of ten** inventory items were
never checked. Nothing forbids it. Nothing detects it. WP2-D11 is the **only edit adding a normative
constraint the owner has never approved**, which is exactly why a collapsed O5 binary must not carry
it in.

---

## 7. The consolidated 12-key VER entry — derived, not approved

F2 holds: **no approved document carries one consolidated table for the 12-key VER entry.** It exists
only as a *diff* (pack §4.2) and as a payload table in the **non-approved** proposal §3.3. The table
below is **reconstructed** from proposal §3.3 (payload) + the envelope in §5.2, and is what **WP2-D2**
would insert. It is **not approved text** until the owner answers D2.

**Envelope (4) — every entry:**

| Field | Type | Rule |
|---|---|---|
| `seq` | integer | `0` at genesis, `+1` per entry, no gaps |
| `prev` | string | previous `entry_sha256`; genesis uses the domain constant `e893bd2c…d307` |
| `entry_type` | string | `"GENESIS"` or `"VER"` |
| `entry_sha256` | string | SHA-256 of canonical JSON bytes **excluding** the terminating LF |

**Payload (8) — VER entry, `seq = n`:**

| Field | Meaning |
|---|---|
| `decision` | Decision ID |
| `verifier` | Verifier identity (`Claude Desktop`) |
| `verified` | Actual verification date, UTC `YYYY-MM-DD` |
| `result` | `PASS` or `FAIL` (`PARAM-E.8`: both retained) |
| `marker_sha256` | Digest of the REG marker verified (**O1** / `PARAM-B.6`) |
| `items_checked` | Integer count of the ten-item inventory checked — **bound missing (§6.3)** |
| `card_sha256` | U1 digest of the card at verification time |
| `file_sha256` | U2 digest of the register at verification time |

**4 + 8 = 12 keys.** `entry_type` deliberately has **no `REG` member** — REG is a marker adjacent to
T16, not a ledger entry, and adding one would violate `PARAM-A.2` and O5 by co-locating the two
families (F6, rejected).

---

## 8. Not authorised by this addendum

Explicitly **not** granted:

- Any **file edit** to `docs/r6-*.md`, `tests/` or `src/` — this is a clarification only.
- **Staging, committing, pushing, tagging**; `git add`, `reset`, `clean`, `stash`, branch switch, rebase.
- **Creating a worktree**; **tracking the corpus** (R6.0-D step 2 — separate repository act).
- **Genesis, REG, VER, marker, ledger, `ledger_id`, key, signature, checkpoint.**
- **BL-22** (stays `NOT SIGNED`) · **G7** (stays `NOT GRANTED`) · Track A · R6.1 · R6.2–R6.7.
- **WP-3, WP-4, WP-5.**
- Migrations, deployments, production use.
- Any act on the **security-remediation lane** (`src/sabiroute/api/completions.py`,
  `tests/test_r6_settlement_integrity.py`) — tracked, clean, out of scope.
- Reading or printing credentials; no `.env` access.

**Also unchanged by this addendum:** WP-4 remains unable to start — no Terminal return exists (§1).
WP-1's exit gate remains open pending the VS Code Copilot read-only report. The 146-vs-147 untracked
discrepancy remains unreconciled.

---

## 9. Source index

| Ref | File | Location |
|---|---|---|
| O3/O4/O5 framing, alternatives, recommendations | `docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` | §2–§4 (`:119-460`) |
| Owner selections O3/O4/O5 + R6.0-D | same | §0 (`:17-30`), ordering `:82-90` |
| Five correction passages | same | §4.5 (`:446-454`) |
| Nine-field genesis + worked example | same | §3.2 (`:244-256`), §3.5–§3.6 (`:290-366`) |
| `PARAM-A.1/.2/.4/.6/.7` | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | §3 (`:113-168`) |
| `PARAM-B.1`, `PARAM-B.3` (U1/U2), `PARAM-B.5`, `PARAM-B.6` | same | §4 (`:177-263`) |
| Namespace rule (no bare `C-1`, `PARAM-*` are not decision cards) | same | `:94-99` |
| Amendment 2 provenance limitation, digest supersession | same | `:24-38` |
| S3 payload field table | `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md` | §3.3 (`:284-300`) |
| S4 genesis field table; non-normative example warning | same | §3.2 (`:244-282`) |
| 23-card register, `PARAM-A.6` ID set | `docs/r6-t16-r6-decision-option-register.md` | §3, §4–§6 |
| F1–F7 adjudication, WP2-D decisions, P1–P4, §5 U2 authority | `artifacts/r6-closure/wp2-final-owner-decision-pack-2026-11-10.md` | §1–§7 |
| Predecessor findings (retained) | `artifacts/r6-closure/wp2-consolidated-decision-pack-2026-11-10.md` | §1–§3 |
| O1–O5 locus blocker | `artifacts/r6-closure/wp0-wp1-evidence-2026-11-09.md` | §4 (`:187-188`) |
| Unrelated `Option C` registers | supplement `:218-222`, `:290-302`; T10 `:316`; T11 `:32`; ADR `:196`; campaign `:262-263` | see §3 |

---

## 10. Compliance

| Requirement | Status |
|---|---|
| No file edited in `docs/`, `tests/`, `src/` | Confirmed |
| No staging / commit / push / branch switch / worktree | Confirmed |
| No corpus tracking (R6.0-D step 2) | Confirmed — not executed |
| No genesis / REG / VER / marker / ledger / key / signature / checkpoint | Confirmed |
| No T16 card touched; BL-22 unsigned; G7 not granted | Confirmed |
| Security lane untouched | Confirmed |
| No credential read or printed | Confirmed |
| No claim of Terminal communication | Confirmed — `UNRECEIVED`, §1 |
| No option invented for O1/O2 | Confirmed — gap recorded, §4.0 |
| No quote attributed to the unread successor brief | Confirmed — §1.1, §5.4 |
| New file created | **1** — this addendum, under `artifacts/r6-closure/` |
