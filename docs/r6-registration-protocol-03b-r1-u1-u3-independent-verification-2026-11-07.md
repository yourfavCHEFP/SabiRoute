# R6-REG-PROTOCOL-03B-R1 — U1–U3 Independent Re-derivation and Defect Register

**Status:** SECOND-IMPLEMENTATION RE-DERIVATION — **NOT** the `PARAM-F.3`
independent verification. Approves nothing, incorporates nothing, executes
nothing.

**Date:** 2026-11-07 (UTC)

**Author identity:** Claude Code. Under 03B-R1 §14 (`:268-280`) and addendum
`PARAM-F.2` (`:301-303`), Claude Code is the **registrar** identity. This report
is therefore a *second registrar-side re-implementation*, not the independent
verification the proposal requires. See §1.

**Subject:** the §4 test vectors of
`docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md`, and the claims of
`docs/r6-registration-protocol-03b-r1-u1-u3-verification-report.md`.

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`. Confirmed at verification time:
`git rev-parse HEAD` returned that commit, `git branch --show-current` returned
that branch, and `git status --porcelain` returned **only** `??` (untracked)
entries — no tracked modifications, nothing staged.

---

## 0. Bottom line

**Every digest in the proposal reproduces exactly.** 23 of 23 U1 card digests,
3 of 3 U2 whole-file digests, the U3 genesis constant, and all 6 behavioural
assertions were re-derived from the source files by an independently written
implementation and match the proposal's §4 tables byte for byte.

**The proposal is not ready for approval.** The digests are right; the
*specification around them* has one contradiction, one uncomputable required
field, one incomplete open-decision list, and one test-vector column that is
wrong for 3 of 23 cards. Details in §5.

---

## 1. Identity limitation (binding)

The proposal header and §1.3 require **Claude Desktop** (`PARAM-F.3`) to
reproduce the vectors independently. This report was produced by **Claude Code**,
the identity the protocol designates as **registrar** (`PARAM-F.2`).

Consequences, stated plainly:

- This report **does not satisfy** the `PARAM-F.3` independent-verification
  requirement, and must not be cited as if it did.
- It **does** establish something narrower and still useful: the §4 numbers are
  not an arithmetic, transcription, or single-implementation artefact. A second
  implementation, written from the normative prose rather than from the
  appendix script, produces the same bytes.
- A misreading of §1.1/§2.1/§3.2 **shared** between the proposal author and this
  re-implementation would survive this check. Only a distinct identity can close
  that gap.

---

## 2. Method

- **Runtime:** Python 3.11, standard library only (`hashlib`, `re`, `json`,
  `unicodedata`). No third-party packages, no network access.
- **Independence measure:** the implementation was written from the normative
  text of proposal §1.1 (U1), §2.1 (U2) and §3.2 (U3) **without** copying the
  appendix script in the verification report. Fence detection, heading
  detection, span termination and trailing-separator stripping were each
  re-derived from the prose.
- **Additional checks not performed by the verification report:**
  - raw-byte vs canonical-byte comparison for all three files;
  - BOM / CRLF / lone-CR detection;
  - NFC and NFD normalisation status of each file, and the number of codepoints
    NFC would change;
  - raw-span vs stripped-span line accounting for every card (this is what
    exposed the defect in §5.4);
  - programmatic parse-and-compare of the proposal's §4.1/§4.2/§4.3 tables
    against the re-derived values, rather than visual comparison;
  - resolution of every section/line citation in addendum §12.3 and proposal
    §1.5 against the actual files.

---

## 3. Baseline facts (independently measured)

| File | Raw bytes | BOM | CRLF | Lone CR | Raw SHA-256 = canonical SHA-256 | NFC? | NFC-changed codepoints |
|---|---:|---|---|---|---|---|---:|
| `docs/r6-t16-r6-decision-option-register.md` | 52782 | no | no | no | yes | yes | 0 |
| `docs/r6-registration-protocol-03b-r1.md` | 12619 | no | no | no | yes | yes | 0 |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 26782 | no | no | no | yes | yes | 0 |

Line counts (split on `LF`, trailing empty element included): T16 = 634,
protocol = 349, addendum = 499. The addendum's claim that the protocol is
**348 lines** (`:10`) is correct.

All three files are already NFC-normalised, so the proposal's decision to
**exclude** NFC from U1/U2 (§5.1) has **zero effect on the current content**.
It remains a latent divergence — see §5.7.

---

## 4. Results

### 4.1 U1 — extracted-card digests: 23 / 23 reproduced

| ID | start (1-based) | canonical lines | canonical bytes | SHA-256 | vs §4.1 |
|---|---:|---:|---:|---|---|
| A1 | 123 | 12 | 767 | `70cb1ddeed5b84f17520e90ba69e4182e519a5998ec10747d9eb5f22c7353bc4` | MATCH |
| A2 | 136 | 12 | 1022 | `afbb96c4ea74efd862d775ce49b32d637b22d0e1f746a352acd28d5209208e34` | MATCH |
| A3 | 149 | 18 | 1763 | `9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b` | MATCH |
| A4 | 168 | 12 | 683 | `ce9c8e2926efbb0a189d68ae050e1e9d052f013360467bd76ef56044ea6965d3` | MATCH |
| B1 | 187 | 25 | 2410 | `b19da622ef05d57be53f0932714b51643ebb8a79cee81a43a92df07e034fa2f4` | MATCH |
| B2 | 213 | 12 | 723 | `e041985cee5b4bcd1408c412a3d88b11ede018ce29d60231565c01a918fe3466` | MATCH |
| B3 | 226 | 12 | 721 | `db9606a1d44ec430ba38937585802f85255b6bbd77960661695c72a03fc8c4b1` | MATCH |
| B4 | 239 | 12 | 620 | `a7836a4847f15714e894d4c0e54eef054f0789aa537e6424959783b7bfb80d2d` | MATCH |
| B5 | 252 | 18 | 1891 | `f39ef13072107af456090507b7d6538493460dc6616f6aac266fc9aceae6045e` | MATCH |
| B6 | 271 | 24 | 2076 | `9c22e56afab5a367db13d451c04fdbb022b74a93d367b0bbc6963e0bf8907374` | MATCH |
| B7 | 296 | 12 | 924 | `b1e497bf590185cbaaf370bfd59133c47fb4a9c7b6db38489e635917efc92fff` | MATCH |
| B8 | 309 | 12 | 689 | `50afcf458560cb68994906bf2b9fcc195c33174c8ddba9a3c4466e07e6771dae` | MATCH |
| B9 | 322 | 12 | 630 | `851a80438990ea0c6221c654821029a84b3411265d01679b8eb7c77a1ea6b88a` | MATCH |
| C1 | 343 | 12 | 1354 | `071f1cb93a3b4f8489cad63c6d9f0e6cbd5606cb64a77364083bfdcf036312c5` | MATCH |
| C2 | 356 | 12 | 800 | `10e53984d2a684283886872e7085ec0d63f7776235ccd92f9ec95e57f333442a` | MATCH |
| C3 | 369 | 12 | 843 | `6bfeebbed8775506db300068733fcce8bdfeffa568febd1bbca06113946a4a3b` | MATCH |
| C4 | 382 | 12 | 1071 | `51e4e7491f2333eee0c274dd2091ba5b9b4e8a4f35d7d73944d333ec27b19bab` | MATCH |
| D1 | 399 | 13 | 858 | `62905f789fa0efa97fbf3abaaa34aa93fcd710347a3ea76e30172c9428cc014f` | MATCH |
| D2 | 413 | 12 | 1038 | `77cb466bffba3f3d14195c009362b8bb20e5f130241fc47d778f5371aa54cdb2` | MATCH |
| D3 | 426 | 20 | 1933 | `bf1c0075f445f3bbfbd7b1b7b302e5112dc7762f3037b44a00ebe3f9aac108ef` | MATCH |
| D4 | 447 | 12 | 922 | `55a557ceb62ab25df55d73e3a456cf405a4e5f398ca3524ca4bd28b9a22e5c99` | MATCH |
| D5 | 460 | 12 | 841 | `9fcda8d4f9a2b1a842f0afec2f370be71e398d5de5a694a141047fee6e4f5485` | MATCH |
| D6 | 473 | 12 | 807 | `21c67a9aa474b442d98389e17ee49cc1dfa3f6db3087ad47f5caa27b5eec3109` | MATCH |

All 23 cards located unambiguously; no `MISSING CARD` or `AMBIGUOUS CARD`
condition on the unmodified source.

### 4.2 U2 — whole-file digests: 3 / 3 reproduced

| File | canonical bytes | SHA-256 | vs §4.2 |
|---|---:|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52782 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` | MATCH |
| `docs/r6-registration-protocol-03b-r1.md` | 12619 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` | MATCH |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 26782 | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` | MATCH |

### 4.3 U3 — genesis constant: reproduced

`SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))` =
`e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` — MATCH.
Confirmed not 64 zeros.

### 4.4 Behavioural assertions: 6 / 6 pass

| Test | Observed |
|---|---|
| Extract `A3` twice | identical |
| Extract `A3` from CRLF-converted copy | identical |
| Whole-file digest of CRLF-converted copy | identical to LF original |
| Non-existent `Z9` | `MISSING CARD` |
| Non-existent `A5` | `MISSING CARD` |
| Duplicated `A3` heading | `AMBIGUOUS CARD` |

### 4.5 Citation resolution

Every section/line citation checked resolves correctly:

- **Protocol §12.3 claims** — §2:23, §5:82, §6:110, §8:171, §10:202, §11:219,
  §12:229, §13:250, §14:268, §15:282, §16:302, §17:321 all match the actual
  heading lines. §17 open-issue line numbers `:337`, `:338-339`, `:340-341`,
  `:342`, `:343`, `:344`, `:345-346` all match.
- **T16 citations** — `:8`, `:13`, `:47`, `:55`, `:76`, `:87`, `:116`, `:149`,
  `:165`, `:166`, `:488`, `:508`, `:512`, `:520`, `:555`, `:567`, `:575` all
  resolve to the claimed content. In particular `:57`, `:76` and `:575` do
  support "all 23 approval records remain `NOT APPROVED`".
- **FAST-04** — `:160` is N9/BL-22; `:221-227` is Gate R6.0-C3 with the 13
  registrations under Reading B. Correct.
- **CLOSE-FINAL-01** — `:469` is BL-22 `NOT SIGNED`; `:502` is RC-8 `UNMET`.
  Correct.
- **CLOSE-FINAL-02** — `:45-65` is the durability finding. Correct.

---

## 5. Defects and open questions

Ranked by consequence. None of these changes any digest in §4.

### 5.1 — CONTRADICTION: the VER record has two incompatible definitions

**Severity: high. Blocks approval.**

Three documents define the VER record three ways:

| Source | Form | Fields |
|---|---|---|
| 03B-R1 §6 (`:110-135`) | markdown comment `<!-- VER:v1 … -->` | **six** named fields |
| Addendum `PARAM-A.2` (`:92-96`) | "a distinct append-only verification ledger" | unspecified |
| Proposal §3.1/§3.3 (`:213-290`) | JSONL, one canonical JSON object per line | **eight** fields (adds `card_sha256`, `file_sha256`) |

The proposal §5.4 says "The `VER:v1` marker itself is unchanged" — but it never
says **where, or whether, a `VER:v1` comment is written**. Two readings, both
broken:

- If the ledger entry **is** the VER record, then the VER record is no longer a
  comment and no longer has six fields. 03B-R1 §6 is violated.
- If a `VER:v1` comment is **also** written, the proposal does not say so, and
  there are now two VER records with no defined relationship. 03B-R1 §6's
  "the VER record" becomes ambiguous, and §15's read-back has two objects to
  confirm.

This is not a stylistic point: 03B-R1 §6 is the grammar the whole verification
lifecycle hangs on, and the addendum §1 (`:39-40`) explicitly promises "no new
marker field".

### 5.2 — GAP: `marker_sha256` has no defined byte boundary

**Severity: high. Blocks execution.**

Both 03B-R1 §6 and the proposal's VER entry require `marker_sha256` — the digest
of the REG marker that was verified. 03B-R1 §17 issue 3 (`:340-341`) states:
"Hash extraction boundaries for the owner response **and REG marker** remain
unresolved."

The addendum §12.2 (`:463`) disposes of issue 3 as "**Partially closed** —
`PARAM-B.1` closed; extracted-card/whole-file remain **U1, U2**". It **silently
omits the REG-marker half**. The proposal defines U1, U2 and U3 — none of which
is the REG marker. So `marker_sha256` remains uncomputable: it is undefined
whether the digest covers the `<!--`/`-->` delimiters, the leading indentation,
the internal newlines, or the trailing whitespace.

A VER record cannot be produced as specified until this is defined.

### 5.3 — GAP: `PARAM-B.1` does not fully close the owner-response boundary

**Severity: medium.**

`PARAM-B.1` (`:133-139`) says the digest is over "the **exact canonical Owner
response field value** only", excluding "surrounding prose, card titles,
headings, notes, and mission commentary". That says what to *exclude*; it does
not define the **delimiter** or the **multi-line rule**.

This matters concretely. A3's owner response spans two lines with a markdown
hard break (two trailing spaces) at T16:163-164:

```
**Owner response:** A3: ADOPT Option A — ADR-1 conditional, explicitly not implemented.··
Acknowledge that P1–P5 remain unmet and that this selection authorises no implementation.
```

It is unspecified whether the value includes the `A3: ` prefix, whether the two
trailing spaces are part of the value, and whether the two lines are joined with
`LF`, a space, or preserved as-is. `PARAM-B.1` claims to close issue 3 for the
owner-response digest; it narrows it but does not close it.

### 5.4 — DEFECT: the "Lines (canonical)" column is wrong for 3 of 23 cards

**Severity: medium. Can cause a false reproducibility failure.**

Proposal §1.1 step 10 requires the recorded evidence to include "end line
(exclusive)" of the **canonical** (post-stripping) span. The §4.1 table does not
do that for the three cards followed by `blank + --- + blank`:

| ID | §4.1 "Lines (canonical)" | canonical span (1-based) | canonical exclusive end | table end | delta |
|---|---|---|---:|---:|---:|
| A4 | 168–182 | 168–180 | **180** | 182 | **+2** |
| B9 | 322–336 | 322–334 | **334** | 336 | **+2** |
| D6 | 473–487 | 473–485 | **485** | 487 | **+2** |

The other 20 cards match exactly, because for them exactly one trailing line is
stripped, which makes the raw span's inclusive end numerically equal the
canonical span's exclusive end. For A4, B9 and D6 three lines are stripped
(blank, `---`, blank), so the two diverge by 2.

The column is therefore reporting the **raw** span's inclusive end, not the
**canonical** span's exclusive end. The `Bytes` and `SHA-256` columns are
correct and describe the canonical span.

**Why this matters:** proposal §1.3 tells the independent verifier to
"reproduce the 23 vectors in §4.1 … Any mismatch is a reproducibility failure
and blocks approval." A verifier that locates the span from the line column
will get 3 mismatches and report a false failure. A verifier that implements
§1.1 normatively will get the right answer. The table should be corrected so
the two paths agree.

The verification report §3 inherits the same defect: it states "`end` is the
exclusive end line", but its `end` values for A4/B9/D6 (182/336/487) are the
0-indexed index of the next heading, not the canonical exclusive end
(180/334/485). Its `start` is 1-based and its `end` is 0-indexed — mixed
indexing.

### 5.5 — GAP: the §5.4 deviation is not carried into §6's owner decisions

**Severity: medium.**

Proposal §5 ("Deliberate deviations and points for reviewer attention") item 4
flags the two extra VER fields as a choice "the reviewer should scrutinise
rather than accept by default". But §6 ("Open sub-decisions for the owner")
lists only **D-U3-1, D-U3-2, D-U3-3** — checkpoint cadence, `ledger_id` scheme,
`allowed_signers` identity.

The VER-record-form question (§5.1) and the extra-fields question are decisions
the owner must make before execution, and they are **not** in the list of
decisions the owner is asked to make. The proposal's own open-decision list is
incomplete.

### 5.6 — GAP: D-U3-1/2/3 are necessary but not sufficient

**Severity: medium.**

Even with D-U3-1, D-U3-2 and D-U3-3 answered, U3 is not executable. Missing:

1. **Key rotation / revocation.** No procedure exists for a lost, compromised or
   rotated owner Ed25519 key. The genesis pins `owner_key_fingerprint`; nothing
   defines how a successor key is authorised or how the chain continues.
2. **Rollback to an earlier checkpoint.** §3.10 correctly notes that entries
   after the last checkpoint are unanchored. It does **not** address the
   stronger attack: an attacker with write access truncates the ledger back to
   an *earlier* checkpointed state and presents that checkpoint's still-valid
   signature. Detection requires the verifier to know the latest checkpoint
   out-of-band; nothing in §3.7 or §3.8 requires that.
3. **Duplicate ledger entry definition.** `PARAM-E.5` says a strict parser
   rejects duplicates, but the proposal never defines what makes two ledger
   entries duplicates (same `seq`? same `decision`+`marker_sha256`? same
   content?).
4. **`ledger_id` verification step.** §3.7 checks chain links, genesis `prev`,
   the signature, `chain_head`/`seq` match, and the fingerprint — but never
   checks that the checkpoint's `ledger_id` equals the genesis `ledger_id`.
5. **`items_checked` bound.** No stated upper bound (the inventory is ten items).

### 5.7 — DIVERGENCE: U1/U2 exclude NFC while 03B-R1 §8 includes it

**Severity: low (currently inert).**

03B-R1 §8 step 3 applies Unicode NFC. U1/U2 deliberately do not (§1.1, §2.1,
§5.1). This is **not** a contradiction — §8 is scoped to "the registration
hash", and U1/U2 are different digest classes under `PARAM-B.3` — and the
proposal flags it. It is currently inert because all three files are already
NFC-normalised (0 codepoints changed).

It becomes live the moment a future T16 edit introduces a non-NFC sequence: U1
and U2 would then produce digests that differ from an NFC-applying
implementation. The owner should confirm the two-regime design is intended.

### 5.8 — AMBIGUITY: `PARAM-B.2` vs `PARAM-D.3` on the revision referent

**Severity: low.**

`PARAM-B.2` says `revision` carries "the SHA-256 of the **exact canonical
manifest bytes**". `PARAM-D.3` says "the **sidecar digest** is the revision
referent of `PARAM-B.2`". "Sidecar digest" can be read as (a) the digest
*recorded in* the sidecar, i.e. the manifest's SHA-256 — consistent with
`PARAM-B.2`; or (b) the digest *of* the sidecar file itself — a different value.
The addendum should say which.

### 5.9 — DEFECT: the appendix script digest is not reproducible

**Severity: low.**

Verification report §1 states: "**Script:** reproduced in full at Appendix A.
Its own SHA-256 is `d2d9a541a5f5fcf7e15b3b147f92deb76a045c6670a7268308fe5c1a1f004c00`."

The appendix code block as written hashes to
`14445a0566b2e0439f76ca1493450d2b0790a7fea51636a74653475ee00bdad2` (as-is) or
`8a7c2856e4b1276f53ce2b664f131e8e6c9fefd97a942b5e6588f449affa6ee7` (with a
trailing LF). Neither matches. The report's §7 limitation 5 clarifies that the
digest "refers to the `/tmp` copy as run", so the §1 statement is misleading
rather than false — but the claimed digest cannot be checked from the document,
and the appendix is not byte-identical to the script that produced the numbers.

### 5.10 — COVERAGE GAP: `PARAM-B.1` is untested

**Severity: medium.**

The proposal's test vectors cover U1, U2 and U3. They do **not** cover
`PARAM-B.1` — the owner-response digest, which is the **only** digest the REG
marker actually carries (`owner_sha256`). The digest that matters most for
registration is the one with no test vector and, per §5.3, no fully defined
boundary.

### 5.11 — DURABILITY: the evidence binds untracked files

**Severity: low, but real.**

CLOSE-FINAL-02 §2 (`:45-65`) records that the entire R6 corpus is untracked.
The U2 digests bind three untracked files. A `git clean`, a fresh clone, or a
branch switch that discards untracked files destroys the evidence the digests
refer to. The proposal does not flag this; the addendum does not either. This is
consistent with the corpus-wide durability finding, not a new defect — but it
means the U2 digests are currently *recoverable, not durable*.

### 5.12 — COUPLING: approving U3 requires approving U2

**Severity: low.**

The genesis entry (§3.2) carries `protocol_sha256`, `addendum_sha256` and
`t16_sha256` — all **U2** digests. U3 therefore cannot be approved and executed
independently of U2. The proposal presents U1/U2/U3 as three items; they are
really one package with a dependency edge U3 → U2.

---

## 6. What this report does not do

- It does not satisfy the `PARAM-F.3` independent-verification requirement
  (§1).
- It does not approve, incorporate, or execute the proposal.
- It does not create a REG or VER record, a ledger, a key, a signature, or a
  checkpoint.
- It does not modify T16 or change any approval status.
- It does not mark any gate COMPLETE.
- It does not authorise BL-22, R6.1, or any implementation.
- It does not supply operational registration authority, which remains
  **DEFERRED**.

---

## 7. Verdict

**Digests: PASS.** All 33 assertions reproduce exactly from an independently
written implementation. The proposal's arithmetic is sound.

**Specification: NOT READY FOR APPROVAL.** Four items must be resolved first:

1. **§5.1** — decide whether the VER record is a `VER:v1` comment, a ledger
   entry, or both, and reconcile with 03B-R1 §6's six-field grammar.
2. **§5.2** — define the REG-marker hash boundary so `marker_sha256` is
   computable.
3. **§5.3 / §5.10** — define the owner-response extraction boundary and add a
   `PARAM-B.1` test vector.
4. **§5.4** — correct the "Lines (canonical)" column for A4, B9 and D6 so the
   table and the normative procedure agree.

Then, before execution: **§5.5** (add the VER-form decision to §6), **§5.6**
(key rotation, rollback protection, duplicate definition, `ledger_id` check),
and **§5.7** (confirm the two-regime normalisation design).

**SECOND-IMPLEMENTATION RE-DERIVATION. NOT THE `PARAM-F.3` INDEPENDENT
VERIFICATION. NOT AN APPROVAL.**
