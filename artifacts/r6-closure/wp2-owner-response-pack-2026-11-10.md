# R6.0 — WP-2 OWNER RESPONSE PACK

**Actor:** Claude Code Desktop (coordinator — **not** the independent verifier)
**Date:** 2026-11-10
**Scope:** Re-anchor WP2-D2's edit set and the 12-key VER table against **live source**; verify
the five mandatory O5 corrections and the deferred sixth; locate the O1–O8 series discrepancy.
**Status:** Verification and restatement only · **WP-2 remains BLOCKED** pending the owner's
answers in the sibling packs §6
**Relationship:** supplements `wp2-final-owner-decision-pack-2026-11-10.md` (governing decisions) and
`wp2-decision-clarification-addendum-2026-11-10.md` (governing framing). **Supersedes neither, and
decides nothing.** Its only novel content is **measured drift** and **one technical defect** (§4).

> This document edits nothing, approves nothing, and re-opens nothing. Where it reports that a
> governing artefact is wrong, the correction is stated explicitly and the upstream origin is named,
> per the corpus's own rule that a finding is not preserved because an earlier report carried it.

---

## 0. Tooling limitation — stated first, because it bounds every claim below

The shell was **unavailable** in this session: every `Bash` invocation (11 attempts, including
`wc`, `grep`, `git status`) returned *"Auto mode could not evaluate this action and is blocking it for
safety."* This is the same classifier failure recorded as F-WP2-3 and as a §6.D blocked item in the
governing packs.

**Consequences, recorded rather than papered over:**

| Claim class | Status this pass |
|---|---|
| Line numbers, headings, verbatim text, table contents | **VERIFIED** — read directly with `Read` |
| File **line counts** | **VERIFIED** — last-line index observed (348 / 646) |
| Byte counts, SHA-256 digests, `git` state, untracked counts | **NOT RE-MEASURED** — reported from governing artefacts, not independently computed |
| Cross-file whole-corpus searches (e.g. `O6`/`O7`/`O8`) | **NOT PERFORMED** — no shell; see §7 |

No digest in this document is newly computed. Every digest quoted is **inherited** and labelled as
such. `UNRECEIVED` remains `UNRECEIVED`; no Terminal return exists (§1 of the governing pack).

---

## 1. Verification disposition — summary

| # | Verified this pass | Result |
|---|---|---|
| 1 | Protocol file is **348 lines** | ✅ matches F-WP1-3 live value |
| 2 | Addendum file is **646 lines** | ✅ matches F-WP1-3 live value |
| 3 | O5 corrections **#1, #2, #3** (protocol) | ✅ **all three anchors exact** |
| 4 | O5 corrections **#4, #5** (addendum) | ❌ **both anchors wrong** — see §2 |
| 5 | 12-key VER table, all 12 names/types/rules | ✅ **all 12 verified** — see §3 |
| 6 | `entry_sha256` serialisation semantics | ❌ **table as written is ambiguous** — see §4 |
| 7 | R6.0-D five-step ordering at `:82-90` | ✅ exact |
| 8 | Nine-field genesis set (O4) | ✅ exact, `#1`–`#9`, decision pack `:244-256` |
| 9 | 508/509-byte worked example | ✅ exact, decision pack `:317`, `:322-325` |
| 10 | Test U2 vectors `:173-174` | ✅ `PROTOCOL (12619, 3a003632…)`, `ADDENDUM (38603, 69166509…)` |
| 11 | Correction-proposal banner `:3` | ✅ exact |
| 12 | Correction-proposal §2 stale counts (349/499) | ⚠️ **NOT VERIFIED** — outside the range read |
| 13 | T16 cardinality = 23 | ⚠️ **NOT RE-VERIFIED** this pass |
| 14 | O1–O8 registration-design series | ❌ **NOT LOCATED** — see §7 |

**Score: 10 verified · 3 defective (2 anchors + 1 semantic) · 1 origin traced · 3 unverified.**

---

## 2. WP2-D2 edit anchors — re-anchored against live source

The governing pack's implementation sequence (step 1, `wp2-final-owner-decision-pack §7:500`) lists
five file/line anchors for the five mandatory corrections. **Three are correct. Two are wrong, and
both wrong ones are in the addendum.**

### 2.1 The five mandatory corrections

| # | Target file | Pack anchor | **Live anchor** | Verdict | Live text (verified) |
|---|---|---|---|---|---|
| **E1** | `r6-registration-protocol-03b-r1.md` | `:112` | `:112` | ✅ **EXACT** | `Verification is a separate structured comment:` |
| **E2** | same | `:114-117` | `:114-117` | ✅ **EXACT** | fenced block; content on `:115-116` (`<!-- VER:v1 … -->`) |
| **E3** | same | `:130-135` | `:130-135` | ✅ **EXACT** | paragraph containing `when a matching VER record exists with `result=PASS`` |
| **E4** | `…-owner-parameter-addendum.md` | `:93-99` | **`:122-126`** | ❌ **WRONG** | `:93` = G7 line · `:94` blank · `:95-100` = **namespace rule**. Target text `a distinct append-only verification ledger` is at **`:125-126`**, inside `PARAM-A.2`. |
| **E5** | same | `:110-116` | **`:134-139`** | ❌ **WRONG** | `:110` = `UNRESOLVED` table row · `:112` = `---` · `:114` = `## 3.` heading · `:116` = `PARAM-A.1`. Target text `a matching `VER:v1` record has `result=PASS`` is at **`:136-138`**, inside `PARAM-A.4`. |

### 2.2 Why this matters operationally

E4 and E5 as dated would have an implementer editing the **namespace rule** and the **§3 heading** —
two passages that are *load-bearing elsewhere*:

- Editing `:95-100` would touch the rule that makes WP2-D3 itself coherent (§4 of the governing pack
  relies on `PARAM-A.6` + this namespace rule to dissolve the O1–O5 blocker).
- Editing `:110-116` would corrupt the provenance-class table's closing row and the §3 heading.

**Neither would raise an error.** Both edits would succeed, produce valid Markdown, change the
addendum's bytes, move `addendum_sha256`, and silently leave the actual O5 contradiction in place.
This is a **silent-failure class defect**, not a cosmetic one.

### 2.3 Upstream origin — the error is not WP-2's

Both bad anchors are **inherited**. They originate in the owner-recorded decision pack
`docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §4.1 (`:374-380`), which tabulates:

| Row | Source cited there | Actual live location | Verdict |
|---|---|---|---|
| **S2** `:377` | addendum `:93-99` | addendum `:122-126` | ❌ wrong |
| **S3** `:378` | proposal `:275-292` | proposal `:284-300` | ❌ wrong |
| **S4** `:379` | proposal `:244-273` | proposal `:244-282` | ⚠️ start right, **end wrong** |

The WP-2 pack copied `:93-99` / `:110-116` faithfully from that table. **Correcting WP-2 alone would
leave the owner-recorded pack still carrying the bad anchors**, and the next brief would re-inherit
them. Recommended: correct §4.1 at the same single pass, under **WP2-D2**, noting that it moves
`addendum_sha256`/`protocol_sha256` — which the D8 single-pass ordering already absorbs.

### 2.4 Secondary anchor drift — lower severity, same class

| Claim | Stated | Live | Verdict |
|---|---|---|---|
| Addendum's embedded protocol reference (E7) | `:9-11` | **`:10-12`** (`(348 lines; SHA-256` … digest) | ⚠️ off by one |
| Namespace rule (clarification addendum §9) | `:94-99` | `:95-100` | ⚠️ off by one — the *pack* (§F-WP2-6, F4) has `:95-100`, which is **right** |
| `PARAM-A.7` locus | `:153-168` | `:154-166` body; `:168-169` closure note | ⚠️ off by one |
| `PARAM-A.2` locus (clarification §4.3.1) | `:121-126` | `:122-126` | ⚠️ off by one |
| Decision pack §3.3 cites proposal "§5 deviation 5 (`:487-511`)" | `:487-511` | proposal §5 = `:496-519`; deviation 5 = `:514-517` | ⚠️ wrong |
| Proposal §2.5 cites "Addendum §4 … (`:142-168`)" | `:142-168` | addendum §4 = `:173-271`; `PARAM-B.2/.3/.4` = `:201-231` | ⚠️ stale |

**E7 is confirmed safe to sequence last.** The addendum's embedded reference currently reads
`348 lines; SHA-256 3a003632…cd512b`, and both values are **correct today** — the protocol is 348
lines and `3a003632…cd512b` is exactly `PROTOCOL`'s live vector at test `:173`. It becomes wrong
*only after* E1–E3 change protocol bytes. D8's ordering is therefore not merely prudent; without it
the addendum would be corrected to a value that is already correct and would then be re-broken.

---

## 3. The 12-key VER table — all twelve keys verified

Requested: verify each of the 12 keys. Done against the two **owner-recorded** sources plus the
proposal. **All 12 names, types and rules reproduce. `4 + 8 = 12` is arithmetically correct.**

### 3.1 Envelope — 4 keys (decision pack §5.2 `:474-481`)

| # | Key | Type | Rule (verbatim) | Source |
|---|---|---|---|---|
| 1 | `seq` | integer | `0` at genesis, `+1` per entry, no gaps | `:478` |
| 2 | `prev` | string | previous `entry_sha256`; genesis uses the domain constant | `:479` |
| 3 | `entry_type` | string | `"GENESIS"` or `"VER"` | `:480` |
| 4 | `entry_sha256` | string | SHA-256 of canonical JSON bytes **excluding** terminating LF | `:481` |

### 3.2 Payload — 8 keys (decision pack §5.4 `:488-491`; proposal §3.3 `:291-300`)

| # | Key | Type | Meaning | Source |
|---|---|---|---|---|
| 5 | `decision` | string | Decision ID | proposal `:293` |
| 6 | `verifier` | string | Verifier identity (`Claude Desktop`) | `:294` |
| 7 | `verified` | string | Actual verification date, UTC `YYYY-MM-DD` | `:295` |
| 8 | `result` | string | `PASS` or `FAIL` (`PARAM-E.8`) | `:296` |
| 9 | `marker_sha256` | string | Digest of the REG marker verified (O1 / `PARAM-B.6`) | `:297` |
| 10 | `items_checked` | integer | Count of the ten-item inventory checked — **no bound** (§6.3) | `:298` |
| 11 | `card_sha256` | string | U1 digest of the card at verification time | `:299` |
| 12 | `file_sha256` | string | U2 digest of the register at verification time | `:300` |

**Six-field preservation confirmed.** `PARAM-A.4` survives only because keys 5–10 are byte-identical
to 03B-R1 §6's six names (`:121-126`), and `result`'s domain is unchanged (`:128`). E2's
"retain the six field names" requirement is **satisfied by this table as written** — subject to §4.

**`entry_type` has no `REG` member — confirmed, and correctly so.** `:480` is a closed two-value
domain. Adding `REG` would co-locate the two families in one container, violating `PARAM-A.2`
(`:124-126`) and O5 (`:29`). F6's rejection stands on live text.

**Citation defect in the reconstructed table.** Clarification addendum §7 attributes the envelope to
*"the envelope in §5.2"* without naming a document. It **is** resolvable — but only by inferring
**decision pack** §5.2. The **proposal has no §5.2**: its §5 is *"Deliberate deviations"*
(`:496-519`), and its envelope is §3.1 (`:220-230`). As written the citation points at nothing in
the document it most naturally names. Fix: cite `decision pack §5.2 (:474-481)` explicitly in the
inserted table's provenance line.

---

## 4. **The defect the table will introduce if inserted as-is**

This is the one substantive finding of this pass, and it is **not** in either governing document.

### 4.1 The problem

The 12-key table presents `entry_sha256` as **envelope field #4**, type `string`, with rule
*"SHA-256 of canonical JSON bytes excluding terminating LF."* Read as a field table for the JSONL
entry — which is exactly what E2 asks it to become — an implementer serialises all twelve keys into
the canonical object and then hashes that object. **The hash then covers itself.** No digest can
satisfy it, and no two implementations can agree on what to exclude.

### 4.2 What the normative worked example proves

Decision pack §3.5 gives the only fully specified, reproducible record in the corpus:

- Stated inputs at `:298-312` (9 values).
- Canonical genesis line at `:317` — **nine keys**: `addendum_sha256`, `created`, `entry_type`,
  `ledger_id`, `owner_key_fingerprint`, `prev`, `protocol_sha256`, `seq`, `t16_sha256`.
- **`entry_sha256` does not appear in the line.** `:314` states *508 bytes, no trailing LF in the
  hashed preimage*; `:324` gives the digest `ad1484b0…caf28` computed **over** those bytes.
- Reference implementation at `:340-354` builds a **9-key** dict and hashes it — `entry_sha256` is
  produced, never inserted.
- `:328-329` lists the key order produced by code-point sort: **nine names, `entry_sha256` absent.**

Corroborated by proposal §3.1: the entry table (`:222-227`) lists `seq`, `prev`, `entry_type` and a
`*(payload)*` placeholder — `entry_sha256` is defined **separately below** (`:229-230`), deliberately
kept out of the field table.

### 4.3 The arithmetic that follows

| Record | Serialised (hashed) keys | Computed | Total fields |
|---|---:|---:|---:|
| Genesis | 6 payload + 3 envelope = **9** | `entry_sha256` | 10 |
| VER entry | 8 payload + 3 envelope = **11** | `entry_sha256` | **12** |

So **"12 keys" is correct as a field count** (the governing packs are not wrong to say twelve), but
**only 11 keys are hashed for a VER entry.** The table must say so, or E2 installs a self-referential
rule into the protocol at the moment it replaces the HTML comment.

### 4.4 Recommended wording for the inserted table

Add one line to the envelope table, and one note beneath it:

> `entry_sha256` | string | SHA-256 of the entry's canonical JSON bytes **excluding** the terminating
> `LF`. **Computed, not serialised:** `entry_sha256` is never a member of the object it hashes. A VER
> entry's hashed object therefore contains **eleven** keys — `seq`, `prev`, `entry_type` and the eight
> payload fields — and the twelve-key count of this table includes the computed digest as a ledger
> field, exactly as the normative genesis worked example demonstrates (nine hashed keys,
> `entry_sha256` = `ad1484b0…caf28`).

This costs one line, changes no byte of the schema, and prevents a conformance test from encoding the
wrong preimage. **It should be folded into E2 under WP2-D2, not raised as a new decision** — it
clarifies the approved schema rather than constraining it. If the owner prefers it as a formal
amendment, it belongs inside D2 and nowhere else.

---

## 5. Five mandatory corrections + the deferred sixth — status

| Item | Status | Note |
|---|---|---|
| **The five corrections** | **5 of 5 identified, 3 of 5 correctly anchored** | E4/E5 re-anchored in §2.1 |
| **Sixth correction** — retire the `VER:v1` token | **Correctly deferred; still unasked** | `:456-460` of the decision pack states it plainly. **Recommendation: retain the token** as the field-name-set identifier. Retiring it would touch §6, `PARAM-A.4`, §10 step 8, §13, §15 and §16 acceptance criteria — a materially larger edit that **changes no schema semantics**, since S3 preserves all six names. Retaining is the least invasive option and keeps `PARAM-A.4` intact. |
| **REG/VER asymmetry note** (F6 residue) | Approved to ride D2 | Text is sound: REG is an HTML-comment marker adjacent to T16 (`PARAM-A.1 :116-120`); VER is a JSONL line in a separate ledger (`PARAM-A.7 :154-166`). The asymmetry is real and intentional; it is merely nowhere *stated* as intentional. One line closes it. |
| **`items_checked` bound** (E8) | **Correctly separated** (WP2-D11) | Live confirmation: protocol `:116` declares `items_checked=<N>`; `:126` lists the field; `:128` restricts `result` only. **No bound exists.** §7 fixes the inventory at ten (`:137-169`). The failure scenario in the governing packs is **verified as live text**, not inferred. |

---

## 6. Also verified incidentally — two live inconsistencies worth recording

Neither is blocking; both are the same drift class that produced F-WP1-3.

1. **U1 card-table span mismatch.** The test fixture records `D6` as lines **473–485**
   (`tests/test_r6_registration_digest_conformance.py:168`); proposal §4.1 records **473–487**
   (`:468`). Byte count (807) and digest (`21c67a9a…`) **agree**, so the divergence is in the
   cosmetic line-range metadata only. Record as a low-severity documentary defect; do **not** change
   the digest.
2. **Proposal's illustrative genesis line carries a stale `addendum_sha256`.** Proposal `:279` embeds
   `addendum_sha256 = 2ff885e3…fee14f`, which is the **pre-Amendment** value (§4.2 `:476`, 26,782
   bytes), while the same line embeds the **current** `protocol_sha256 = 3a003632…cd512b`. The line is
   explicitly non-normative (`:267-274`), so nothing depends on it — but it is a mixed-vintage
   example and will mislead a reader who ignores the warning.

---

## 7. The O1–O8 registration-design series — **NOT LOCATED**

Requested: locate the discrepancy evidence for an **O1–O8** registration-design series.

**Result: not located, and the search could not be performed.** The shell was blocked (§0), so no
`grep` over `docs/` or `artifacts/` was possible. **No claim is made about whether such a series
exists.** Naming it absent from an unperformed search would be exactly the inference this corpus
forbids.

**What the record establishes without a search**, from files read in full this pass:

| Document | O-series it carries | Count |
|---|---|---|
| `r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §0 `:18-30` | **O3, O4, O5** (+ R6.0-D) | 3 |
| `…-owner-parameter-addendum.md` §12.1/§12.4 `:532-538`, `:613-619` | **O1, O2, O3, O4** (+ U1–U4) | 4 |
| Clarification addendum §2 `:79-85`, §4.0 `:122-149` | **O1–O5** | 5 |
| WP-2 final pack §1.2 F4 `:136-141` | **O1, O3, O4, O5** → parameters | 4 |
| Proposal §6 `:521-536` | **D-U3-1, D-U3-2, D-U3-3** — *not* O-series | 3 |

**Arithmetic note, and this is the discrepancy the record already supports:** the corpus has been
counted **four different ways in five documents** — "three", "four", "five (O1–O4)", and
"five (O1–O5)". The clarification addendum §2 (`:75-78`) already flags one of these:
the WP-2 directive's *"five open parameters (O1–O4)"* is **arithmetically short by one** (it names
five numerals but writes O1–O4).

**An eight-item O-series is not derivable from any document read.** If the owner's source reports
**O1–O8**, that source is either (a) counting a different register, (b) counting O1–O5 **plus** the
three D-U3 items (= 8, and the most likely explanation), or (c) reporting a series that is absent
from this workspace. **(b) is the most probable: 5 + 3 = 8 exactly**, and proposal §6 is the only
place in the corpus where a three-item open series sits alongside the O-series.

**To close this, run — this is the exact command set, and it must be run by an actor with a working
shell:**

```bash
cd "/Users/airm2/My ML Hub/SabiRoute" && grep -rn -E "\bO[678]\b" docs/ artifacts/ tests/ 2>/dev/null | head -40
```

```bash
cd "/Users/airm2/My ML Hub/SabiRoute" && grep -rn "O1–O8\|O1-O8\|O1..O8" docs/ artifacts/ 2>/dev/null | head -20
```

If those return nothing, the O1–O8 framing is **not present in this workspace** and must be treated
as `UNLOCATED` in the same class as the 2026-11-07 work-order artefact and build-map §1.3/§9 — a
citation to evidence that exists only outside the tree. **It must not be reconstructed.**

---

## 8. What this pack does not do

Not granted, not performed, not implied:

- Any **file edit** to `docs/r6-*.md`, `tests/` or `src/` — including every E1–E11 correction it
  describes. **This pack is analysis only.**
- **Staging, committing, pushing, tagging**; `git add`, `reset`, `clean`, `stash`, branch switch,
  rebase, worktree.
- **Tracking the corpus** (R6.0-D step 2) — separate repository act, separate authority.
- **Genesis, REG, VER, marker, ledger, `ledger_id`, key, signature, checkpoint.**
- **BL-22** (stays `NOT SIGNED`) · **G7** (stays `NOT GRANTED`) · Track A · R6.1 · R6.2–R6.7.
- **WP-3, WP-4, WP-5.** Migrations, deployments, production use.
- Any act on the **security-remediation lane** (`src/sabiroute/api/completions.py`,
  `tests/test_r6_settlement_integrity.py`) — tracked, clean, out of scope.
- Reading or printing credentials; no `.env` access.
- **Any new digest computation** (§0) · **any claim of Terminal communication** · **any answer to a
  WP2-D question on the owner's behalf.**

---

## 9. Compliance

| Requirement | Status |
|---|---|
| No file edited in `docs/`, `tests/`, `src/` | **Confirmed** |
| No staging / commit / push / branch switch / worktree | **Confirmed** |
| No corpus tracking (R6.0-D step 2) | **Confirmed** — not executed |
| No genesis / REG / VER / marker / ledger / key / signature / checkpoint | **Confirmed** |
| No T16 card touched; BL-22 unsigned; G7 not granted | **Confirmed** |
| No digest newly computed or re-measured | **Confirmed** — inherited values labelled as such |
| No option invented for O1/O2 or for O1–O8 | **Confirmed** — §7 records the gap, does not fill it |
| No rejected finding revived | **Confirmed** — F3, F6 rejected; F-WP2-1/D10 withdrawn; N2/N3 untouched |
| No settled decision re-litigated | **Confirmed** — O5, O4, O3, R6.0-D order treated as settled |
| New file created | **1** — this pack, under `artifacts/r6-closure/` |

```
CURRENT GATE:   WP-2
CURRENT PHASE:  R6.0 closure
PROVEN:         5 O5 corrections located — 3 anchors exact, 2 wrong (E4->:122-126, E5->:134-139);
                all 12 VER keys verified; entry_sha256 found NOT serialised (9-key genesis proves it);
                bad anchors traced upstream to decision pack §4.1 (:374-380); E7 safe only if last
UNPROVEN:       correction-proposal §2 stale counts; T16 cardinality; all digests (shell blocked)
UNLOCATED:      O1-O8 series (search could not run); build-map §1.3/§9; 2026-11-07 work order
UNRECEIVED:     any Terminal return — WP-2 still has exactly one actor
BLOCKED BY:     WP2-D2, D3, D6, D9, D11 (genuine) · D7 (partial) · R6.0-D step 2 (separate act)
NEXT:           owner answers §6 of the governing pack — then step 1, on the §2.1 live anchors
```

**VERIFICATION PACK ONLY. NOT AN EXECUTION AUTHORISATION.**
**WP-2 REMAINS BLOCKED. R6.0 OPEN · BL-22 NOT SIGNED · G7 NOT GRANTED.**
