# R6-REG-PROTOCOL-03B-R1 — U1–U3 Independent Review

**Status:** INDEPENDENT REVIEW — `PARAM-F.3`. **Advisory only.** This document
approves nothing, incorporates nothing, executes nothing, and creates no record
of any kind. Approval remains the owner's decision.

**Date:** 2026-11-06 (UTC)

**Reviewer:** Claude Code, separate session, acting as the `PARAM-F.3`
independent verifier.

**Subject:** `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md` — the U1
(extracted-card digest), U2 (whole-file digest) and U3 (checkpoint anchoring /
VER-ledger genesis) proposals, and the §4 test vectors.

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`. Confirmed at review time:
`git rev-parse HEAD` returned that commit; `git status --porcelain` showed no
tracked modifications and nothing staged.

---

## 0. Verdict

**The §4 test vectors reproduce exactly and independently. The digest and
anchoring contracts are sound, implementable and correctly fail-closed. I
recommend the owner approve U1, U2 and U3, subject to the four clarifications in
§6.**

| Group | Vectors | Reproduced | Mismatch |
|---|---|---|---|
| U1 — extracted-card digests (§4.1) | 23 | **23** | 0 |
| U2 — whole-file digests (§4.2) | 3 | **3** | 0 |
| U3 — genesis constant (§4.3) | 1 | **1** | 0 |
| §4.4 behavioural tests | 6 assertions | **6** | 0 |
| Adversarial probes (mine, §5) | 7 | **7** | 0 |

**Total: 40 assertions, 0 mismatch.**

No blocking defect was found. The findings in §6 are specification
clarifications, not errors: each is a place where two competent implementers
could diverge, not a place where the current text is wrong.

---

## 1. What this review is, and what it is not

**It is** an independent re-implementation of the normative procedures in
proposal §1.1 (U1), §2.1 (U2) and §3.2 (U3), written from the specification text
alone, plus a field-by-field comparison against the §4 tables, plus adversarial
probes the registrar did not run.

**Independence, stated precisely.** I did **not** consult the registrar's
Appendix A script while writing my implementation; the structure, function
decomposition and test harness are my own. I did not see the registrar's
reasoning. What this excludes is a *session-level* error — a transcription slip,
an arithmetic mistake, a copy-paste of a wrong constant. What it does **not**
exclude is a *model-level* misreading: I am a separate session of the same model
family as the registrar, so if the specification text is genuinely ambiguous and
we both resolve it the same wrong way, this review will not catch it. That
residual risk is inherent to the arrangement and is recorded in §7.

**It is not** an approval, an incorporation, an execution, or a record. It does
not create a REG or VER record, a manifest, a key, a signature, a ledger or a
checkpoint. It does not modify T16 or change any approval status. It does not
mark any gate COMPLETE. It does not authorise BL-22, R6.1, or any implementation.
Operational registration authority remains **DEFERRED**.

---

## 2. Method

- **Runtime:** Python 3.11, standard library only (`hashlib`, `re`, `json`). No
  third-party packages, no network access.
- **Script:** `/tmp/desktop_indep_review_u1u3.py`, written from the spec text.
  Read-only: it reads the three source documents and writes nothing.
- **U1/U2 pipeline as implemented:** raw bytes → reject if the file begins with
  `EF BB BF` → decode UTF-8 strict → replace `CRLF` with `LF`, *then* remaining
  `CR` with `LF` → split on `LF`.
- **U1 card location:** fence mask (a line whose first non-space characters are
  ` ``` ` or `~~~` opens a fence; the matching token closes it); ATX headings
  `^(#{1,6})\s+(.*)$` outside fences; card heading
  `^(#{1,6})\s+(<ID>)\s+[—–-]\s+` outside fences, required unique; span ends at
  the first subsequent heading outside a fence whose level is `≤` the card
  heading's level, else at end of file.
- **U1 trailing-separator stripping:** remove trailing blank lines, then remove a
  trailing horizontal rule matching `^ {0,3}(-{3,}|\*{3,}|_{3,})\s*$`, repeating
  to a fixpoint.
- **U1 canonical card text:** remaining lines joined with a single `LF`, encoded
  UTF-8 with no BOM, hashed SHA-256, lowercase hex.
- **U2:** canonical text encoded UTF-8 with no BOM, hashed SHA-256, lowercase hex.
- **U3:** `SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))`, lowercase hex.

No NFC/NFD normalisation, no whitespace trimming and no trailing-newline
retention were applied — matching the proposal's explicit exclusions.

---

## 3. U1 — extracted-card digests

`start` is the 1-based line number of the card heading; `end` is the exclusive
end line, both in the newline-canonicalised form. All 23 agree with the
"Lines (canonical)" column of proposal §4.1.

| ID | start | end | Bytes | SHA-256 (independently reproduced) | vs §4.1 |
|---|---|---|---|---|---|
| A1 | 123 | 135 | 767 | `70cb1ddeed5b84f17520e90ba69e4182e519a5998ec10747d9eb5f22c7353bc4` | MATCH |
| A2 | 136 | 148 | 1022 | `afbb96c4ea74efd862d775ce49b32d637b22d0e1f746a352acd28d5209208e34` | MATCH |
| A3 | 149 | 167 | 1763 | `9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b` | MATCH |
| A4 | 168 | 182 | 683 | `ce9c8e2926efbb0a189d68ae050e1e9d052f013360467bd76ef56044ea6965d3` | MATCH |
| B1 | 187 | 212 | 2410 | `b19da622ef05d57be53f0932714b51643ebb8a79cee81a43a92df07e034fa2f4` | MATCH |
| B2 | 213 | 225 | 723 | `e041985cee5b4bcd1408c412a3d88b11ede018ce29d60231565c01a918fe3466` | MATCH |
| B3 | 226 | 238 | 721 | `db9606a1d44ec430ba38937585802f85255b6bbd77960661695c72a03fc8c4b1` | MATCH |
| B4 | 239 | 251 | 620 | `a7836a4847f15714e894d4c0e54eef054f0789aa537e6424959783b7bfb80d2d` | MATCH |
| B5 | 252 | 270 | 1891 | `f39ef13072107af456090507b7d6538493460dc6616f6aac266fc9aceae6045e` | MATCH |
| B6 | 271 | 295 | 2076 | `9c22e56afab5a367db13d451c04fdbb022b74a93d367b0bbc6963e0bf8907374` | MATCH |
| B7 | 296 | 308 | 924 | `b1e497bf590185cbaaf370bfd59133c47fb4a9c7b6db38489e635917efc92fff` | MATCH |
| B8 | 309 | 321 | 689 | `50afcf458560cb68994906bf2b9fcc195c33174c8ddba9a3c4466e07e6771dae` | MATCH |
| B9 | 322 | 336 | 630 | `851a80438990ea0c6221c654821029a84b3411265d01679b8eb7c77a1ea6b88a` | MATCH |
| C1 | 343 | 355 | 1354 | `071f1cb93a3b4f8489cad63c6d9f0e6cbd5606cb64a77364083bfdcf036312c5` | MATCH |
| C2 | 356 | 368 | 800 | `10e53984d2a684283886872e7085ec0d63f7776235ccd92f9ec95e57f333442a` | MATCH |
| C3 | 369 | 381 | 843 | `6bfeebbed8775506db300068733fcce8bdfeffa568febd1bbca06113946a4a3b` | MATCH |
| C4 | 382 | 394 | 1071 | `51e4e7491f2333eee0c274dd2091ba5b9b4e8a4f35d7d73944d333ec27b19bab` | MATCH |
| D1 | 399 | 412 | 858 | `62905f789fa0efa97fbf3abaaa34aa93fcd710347a3ea76e30172c9428cc014f` | MATCH |
| D2 | 413 | 425 | 1038 | `77cb466bffba3f3d14195c009362b8bb20e5f130241fc47d778f5371aa54cdb2` | MATCH |
| D3 | 426 | 446 | 1933 | `bf1c0075f445f3bbfbd7b1b7b302e5112dc7762f3037b44a00ebe3f9aac108ef` | MATCH |
| D4 | 447 | 459 | 922 | `55a557ceb62ab25df55d73e3a456cf405a4e5f398ca3524ca4bd28b9a22e5c99` | MATCH |
| D5 | 460 | 472 | 841 | `9fcda8d4f9a2b1a842f0afec2f370be71e398d5de5a694a141047fee6e4f5485` | MATCH |
| D6 | 473 | 487 | 807 | `21c67a9aa474b442d98389e17ee49cc1dfa3f6db3087ad47f5caa27b5eec3109` | MATCH |

All 23 cards were located unambiguously on the unmodified source; no
`MISSING CARD` or `AMBIGUOUS CARD` condition arose.

---

## 4. U2 and U3

### 4.1 U2 — whole-file digests

| File | Canonical bytes | SHA-256 (independently reproduced) | vs §4.2 |
|---|---|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52782 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` | MATCH |
| `docs/r6-registration-protocol-03b-r1.md` | 12619 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` | MATCH |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 26782 | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` | MATCH |

All three files are LF-only with no BOM at this baseline, so the canonical byte
form equals the raw byte form — as proposal §2.2 anticipates. The three digests
in the proposal header also match, so the proposal is bound to the source it
claims.

### 4.2 U3 — genesis constant

| Item | Value (independently reproduced) | vs §4.3 |
|---|---|---|
| `SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))` | `e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` | MATCH |

Confirmed to be the domain-separated hash of the literal, and confirmed **not**
64 zeros. The domain-separation choice (§5.3 of the proposal) is sound: a
genesis `prev` can never collide with a real predecessor hash.

**Not verified:** the example genesis line in proposal §3.2 carries placeholder
values (`YYYY-MM-DD`, `<LEDGER_ID>`, `SHA256:<base64>`), so its `entry_sha256` is
not computable and was not computed. By inspection the example's key order is
ascending by Unicode code point, separators are bare `,` and `:`, and `seq` is a
bare integer `0` — all consistent with the §3.1 canonical-JSON rules.

---

## 5. Behavioural and adversarial results

### 5.1 §4.4 behavioural tests

| Test | Expected | Observed | Result |
|---|---|---|---|
| Extract `A3` twice | identical digest | identical | PASS |
| Extract `A3` from a CRLF-converted copy | identical digest | identical | PASS |
| Whole-file digest of a CRLF-converted copy | identical to LF original | identical | PASS |
| Extract non-existent ID `Z9` | fail closed (`MISSING CARD`) | `MISSING CARD` | PASS |
| Extract non-existent ID `A5` | fail closed (`MISSING CARD`) | `MISSING CARD` | PASS |
| Extract from a file with a duplicated card heading | fail closed (`AMBIGUOUS CARD`) | `AMBIGUOUS CARD` | PASS |

The CRLF tests re-ran the **full** pipeline on the converted text, not a
shortcut comparison.

### 5.2 Adversarial probes (mine — the registrar did not run these)

| Probe | Expected | Observed | Result |
|---|---|---|---|
| Card heading inside a fenced block | ignored for heading detection | ignored | PASS |
| Fence indented 3 spaces | still opens a fence | opens | PASS |
| Setext heading (`===` underline) | not an ATX heading → `MISSING CARD` | `MISSING CARD` | PASS |
| Heading inside an HTML block | matched (spec has no HTML rule) | matched | PASS |
| Trailing blanks + two `---` rules | stripped to fixpoint | stripped | PASS |
| UTF-8 BOM at file start | rejected | rejected | PASS |
| Invalid UTF-8 byte sequence | rejected | rejected | PASS |

Two of these probes initially reported failures. **Both were defects in my own
test assertions, not in the specification**, and I record them because they are
instructive:

1. I first placed a decoy card heading *outside* the fence, which correctly
   produced `AMBIGUOUS CARD` — the spec was right, my fixture was wrong.
2. I then asserted that fenced text must not appear in the card *body*. It
   correctly does: a fence excludes lines from **heading detection**, not from
   the **card span**. The spec is right; my assertion was wrong.

Neither is a finding against the proposal. I note them so the owner can see the
probes were genuinely adversarial rather than tuned to pass.

---

## 6. Findings — clarifications recommended before approval

None of these is an error. Each is a place where two competent implementers
could diverge, or where a future input could behave surprisingly.

### 6.1 Canonical JSON: code-point ordering is not JCS (medium)

§3.1 sorts object keys "ascending by Unicode code point". RFC 8785 (JCS) sorts
by **UTF-16 code unit**. These agree for all-ASCII keys — which is every key in
the current schema — but diverge for keys containing non-BMP characters. The
proposal §5.5 offers JCS as a "drop-in substitution".

**Recommendation:** either (a) adopt JCS explicitly, or (b) state that ledger
object keys are restricted to ASCII, which makes the two orderings identical and
removes the ambiguity. Option (b) is cheaper and sufficient for the current
schema. Without one of these, a future non-ASCII key silently breaks
cross-language reproducibility.

### 6.2 Duplicate `seq` is not addressed (medium)

`PARAM-E.7` makes the ledger append-only, and §3.1 makes `seq` monotonic. But the
specification does not say what happens if two writers both append `seq = n`, or
what a verifier should do on encountering a duplicate `seq` or a broken `prev`
link other than the generic `INVALID / RECONCILIATION REQUIRED`.

**Recommendation:** state explicitly that the ledger is **single-writer**, and
that a duplicate `seq` or a `prev` mismatch is `INVALID` and halts verification.
This is a one-sentence addition and closes a real concurrency hole.

### 6.3 Checkpoint `created` field is ambiguous (low)

The checkpoint message (§3.4) carries `created=<YYYY-MM-DD>`. It is not stated
whether this is the **checkpoint's** creation date or the **genesis** date. The
genesis entry also carries a `created` field.

**Recommendation:** state that the checkpoint message's `created` is the date the
checkpoint was signed, distinct from the genesis `created`.

### 6.4 Fence closing-token length is unspecified (low)

§1.1 step 6 says "the matching token closes it". CommonMark requires a closing
fence to be **at least as long** as the opening fence. The proposal does not say.
An opening ` ```` ` (four backticks) closed by ` ``` ` (three) closes under a
literal reading but not under CommonMark.

**Recommendation:** state the rule explicitly — either "the closing fence must
use the same token and be at least as long as the opening fence" (CommonMark) or
"the first line beginning with the same three-character token closes it"
(simpler). Either is fine; the point is that it should be written down.

### 6.5 Observations that are correct as written (no action)

Recorded so the owner knows they were checked, not overlooked:

- **CRLF→LF before CR→LF** is the correct order. Reversing it would turn `CRLF`
  into `LFLF`. The proposal gets this right.
- **No NFC on U1/U2** is correct. NFC would make the digest correspond to no byte
  range in the file, weakening the byte-boundary claim. The proposal's rationale
  (§1.2) is sound, and the deliberate divergence from `PARAM-B.1` is properly
  flagged in §5.1.
- **Trailing-separator stripping** is necessary and correctly specified. Without
  it the last card in each group absorbs the `---` separator and earlier cards do
  not.
- **The card heading line is inside the span**, so the card ID and title are
  bound by the digest. This is a design choice, not an accident, and it is the
  right one.
- **U2 does not strip a trailing newline**, so a file with and without a final
  `\n` hash differently. Correct for byte-binding; worth knowing.
- **The unanchored-tail risk** (§3.10) is correctly identified, and D-U3-1
  (checkpoint cadence) is the right mitigation. Option (a) — sign after every VER
  entry — is the stronger choice and I would favour it if the owner's signing
  burden allows.

---

## 7. Limitations of this review

1. **Same model family as the registrar.** A shared *model-level* misreading of
   §1.1/§2.1/§3.2 would survive this review. Only a different model, or a human
   reading the spec cold, closes that gap.
2. **One implementation, one language.** Python 3.11 only. The cross-language
   reproducibility claim — notably the §3.1 canonical-JSON rules — is **not
   exercised**, because no ledger entry with real values exists to hash. Finding
   6.1 is a reading of the spec, not a demonstrated divergence.
3. **The U3 chain, checkpoint and signature layers are unexercised.** No key
   exists, no ledger exists, no checkpoint message was signed. §3.4–§3.9 are
   reviewed as text only.
4. **Adversarial coverage is not a proof of robustness.** My seven probes are my
   own construction. Nested fences, fences with info strings, headings inside
   blockquotes and lists, and CRLF inside fenced regions were not exercised.
5. **Content correctness was not assessed.** I verified that the digests bind the
   bytes; I did not verify that the card *text* is the correct decision content.
   That is a separate review.
6. **The script lives outside the repository** (`/tmp`) and is not preserved as a
   tracked artifact. If the owner wants it retained, it should be committed
   deliberately, not incidentally.

---

## 8. What this review does not do

- It does not approve, incorporate, or execute the proposal.
- It does not create a REG or VER record, a ledger, a key, a signature, or a
  checkpoint.
- It does not modify T16 or change any approval status.
- It does not mark any gate COMPLETE.
- It does not authorise BL-22, R6.1, or any implementation.
- It does not supply operational registration authority, which remains
  **DEFERRED**.

**INDEPENDENT REVIEW — ADVISORY ONLY. NOT AN APPROVAL.**
