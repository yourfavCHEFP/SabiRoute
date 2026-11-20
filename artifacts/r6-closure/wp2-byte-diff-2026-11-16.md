# WP-2 — BYTE-LEVEL DIFF RECORD

**Date:** 2026-11-16
**Authority:** `BUILD-MAP-WP0-WP5-TO-100-2026-11-16.md` §6B step 9 (F-WP2-1 residue)
**Branch / HEAD:** `sec/deps-nov` / `1e69ada943f3d3921122219e7a569cdff989d3fd`
**Status:** RECORD ONLY — nothing committed, nothing staged, nothing tracked

All four affected files are **untracked**, so `git diff` produces nothing. This record is the
substitute audit trail. It is the only byte-level evidence that the WP-2 edit sequence ran.

---

## 1. Summary table

| # | File | Before bytes | After bytes | Δ | Before lines | After lines | Before SHA-256 | After SHA-256 |
|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | `docs/r6-registration-protocol-03b-r1.md` | 12,619 | 14,620 | +2,001 | 348 | 384 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` | `d3125df37b74535633b4860119ddc83d539b161c6219c3d8892fa8c4628a772c` |
| 2 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 38,603 | 38,699 | +96 | 646 | 647 | `6916650940b73219f20f427227f4f677ea6f84bcd0ab727135d25b28b63399a6` | `a3195ac6ffa3624651e550ca65adfe2d4eafc9fa5417f18065ac0de43cbeab45` |
| 3 | `tests/test_r6_registration_digest_conformance.py` | 26,272 | 36,229 | +9,957 | 632 | 919 | `951db05583b656676f009c12d4881096c210efe08f06f5bb035964e83f8638ff` | `b25b2e88b1f1f4f07c26fddd6701ff764e593d517b73cfbe7e1a621f2ec52a33` |
| 4 | `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` | 48,596 | 48,634 | +38 | 885 | 885 | `0a6c0f762b3836cbb0a4a0bb2d39d31461fc0948de9e18e8e76a94e60d5e8e6f` | `61c68807efb13360686076f1047b3582d6be6b180fcaad5fc27e67e713bad414` |

**`docs/r6-t16-r6-decision-option-register.md` is unchanged** — 52,782 bytes / 633 lines /
`43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c`. T16 is not in the affected set.

---

## 2. File 1 — `docs/r6-registration-protocol-03b-r1.md`

**Lines changed: 5 hunks. 348 → 384 lines (+36).**

### 2.1 E1 — §6 opening sentence (WP2-D2)

**Before** (line 112, 1 line):

```
Verification is a separate structured comment:
```

**After** (lines 112–113, 2 lines):

```
Verification is a separate append-only ledger entry (`PARAM-A.2`), one canonical
JSON object per line:
```

### 2.2 E2 — the fenced HTML comment replaced by the 12-key table (WP2-D2)

**Before** (lines 114–117, 4 lines):

```
```text
<!-- VER:v1 decision=<ID> verifier=<ID> verified=<YYYY-MM-DD>
     result=<PASS|FAIL> marker_sha256=<HEX64> items_checked=<N> -->
```
```

**After** (30 lines): the envelope table (4 keys), the payload table (8 keys), the hash-input rule,
and the provenance line. Verbatim:

```
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
```

**Six field names retained:** `decision`, `verifier`, `verified`, `result`, `marker_sha256`,
`items_checked` — still enumerated immediately after, at what is now `:150-157`. `PARAM-A.4` survives
E2 unamended (F-WP2-2).

### 2.3 E3 — "VER record" → "VER ledger entry" (WP2-D2)

**Before** (was line 131):

```
when a matching VER record exists with `result=PASS`, and the mandatory
```

**After:**

```
when a matching VER ledger entry exists with `result=PASS`, and the mandatory
```

### 2.4 E4 — the REG/VER asymmetry note (WP2-D2, new content)

**Before:** absent.

**After** (5 new lines, inserted after the `result` restriction and before `## 7.`):

```
**REG/VER asymmetry.** REG and VER are deliberately asymmetric: a REG marker is an
HTML comment written adjacent to its T16 decision card (§10), whereas a VER entry
is a canonical JSON line in a separate append-only ledger (`PARAM-A.2`). The
asymmetry is intentional and is not an inconsistency to be resolved.
```

### 2.5 E8 — the `items_checked` bound (WP2-D11, new content)

**Before:** absent.

**After** (4 new lines, immediately after E4):

```
**`items_checked` bound.** `1 ≤ items_checked ≤ 10`. A `PASS` result requires
exactly `10`; a `FAIL` result is permitted at any count in `1..10`. A count of `0`
is invalid.
```

---

## 3. File 2 — `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md`

**Lines changed: 3 hunks. 646 → 647 lines (+1).**

### 3.1 E5 — `PARAM-A.2` JSONL realisation (WP2-D2)

**Before** (was lines 125–126, 2 lines):

```
with the REG record they verify. They live in a distinct append-only verification
ledger (integrity requirements: `PARAM-E.7`).
```

**After** (3 lines):

```
with the REG record they verify. They live in a distinct append-only verification
ledger (integrity requirements: `PARAM-E.7`) — realised as the JSONL ledger of
proposal §3.1–§3.3, one canonical JSON object per line.
```

### 3.2 E6 — `PARAM-A.4` "`VER:v1` record" → "VER ledger entry" (WP2-D2)

**Before** (was line 137):

```
`VER:v1` record has `result=PASS` **and** the mandatory post-COMPLETE read-back
```

**After:**

```
VER ledger entry has `result=PASS` **and** the mandatory post-COMPLETE read-back
```

### 3.3 E7 — embedded protocol reference (WP2-D8, sequenced last)

**Before** (lines 10–11):

```
(348 lines; SHA-256
`3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b`)
```

**After:**

```
(384 lines; SHA-256
`d3125df37b74535633b4860119ddc83d539b161c6219c3d8892fa8c4628a772c`)
```

**Verified after step 3:** the live protocol measures 384 lines and
`d3125df37b74535633b4860119ddc83d539b161c6219c3d8892fa8c4628a772c`. The embedded reference matches
exactly. The §6B stop condition ("the addendum's `:9-11` reference does not match the live protocol
after step 3") was **not** triggered.

---

## 4. File 3 — `tests/test_r6_registration_digest_conformance.py`

**Lines changed: 2 modified + 287 appended. 632 → 919 lines (+287).**

### 4.1 Step 5 — the single vector recomputation

**Before** (lines 173–174):

```python
    PROTOCOL: (12619, "3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b"),
    ADDENDUM: (38603, "6916650940b73219f20f427227f4f677ea6f84bcd0ab727135d25b28b63399a6"),
```

**After:**

```python
    PROTOCOL: (14620, "d3125df37b74535633b4860119ddc83d539b161c6219c3d8892fa8c4628a772c"),
    ADDENDUM: (38699, "a3195ac6ffa3624651e550ca65adfe2d4eafc9fa5417f18065ac0de43cbeab45"),
```

**`T16` at line 172 is unchanged** — `(52782, "43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c")`.
This was the **only** vector recomputation in the sequence.

### 4.2 Step 7 — the five negative-first groups (WP2-D9)

**Appended** after `test_source_digests_are_stable_against_the_record`, 287 lines, no new module:

| Group | Tests added | Negative cases |
|---|---:|---|
| 1 — VER schema | 7 | duplicate key · `\/`-escaped `/` · reordered keys · space after `:` · `seq` as `0.0` · `seq` as `"0"` |
| 2 — F7 bound | 6 | `0` · `11` · `-1` · `PASS` with `9` |
| 3 — REG/VER separation | 2 | `entry_type="REG"` · VER co-located with a REG marker |
| 4 — `COMPLETE` derivation | 5 | missing · malformed · mismatched marker · `FAIL` |
| 5 — genesis conformance | 3 | `+LF` must differ from no-LF |
| **Total** | **23** | |

Supporting helpers added: `VER_PAYLOAD_KEYS`, `VER_HASHED_KEYS` (11), `VER_LEDGER_KEYS` (12),
`_ver_entry`, `_ver_line`, `_validate_ver_line`, `_validate_items_bound`, `_complete_is_valid`,
`_genesis_line`.

**One defect found and fixed during step 8.** The first run failed
`test_d9_g4_malformed_ver_makes_complete_invalid`: `parse_canonical_json("{not json")` raises
`json.JSONDecodeError`, which is a `ValueError` but not a `SpecError`, so `_complete_is_valid`'s
`except SpecError` did not catch it. Fixed by normalising the decode error inside
`_validate_ver_line`:

```python
    try:
        entry = parse_canonical_json(text)  # duplicate keys raise here
    except ValueError as exc:  # JSONDecodeError is a ValueError
        raise SpecError("MALFORMED LEDGER ENTRY") from exc
```

This is a defect in the **newly authored test helper**, not a stale vector and not a defect in the
protocol. It was fixed within step 7's scope. Re-run: green.

---

## 5. File 4 — `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md`

**Lines changed: 3 hunks. 885 → 885 lines (0).**

### 5.1 WP2-D12 — status banner (`:3`)

**Before:**

```
**PROPOSAL — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**
```

**After:**

```
**PROPOSAL — OWNER-ADOPTED IN PART (WP2-D2 · WP2-D11); INCORPORATED BY THE WP-2 EDIT PASS — NOT EXECUTED**
```

### 5.2 WP2-D12 — §2 stale line counts

**Before** (lines 79–80):

```
| 1 | `docs/r6-registration-protocol-03b-r1.md` | 349 | Governing procedure. §5 REG grammar, §6 VER grammar, §8 normalisation, §17 open issues |
| 2 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 499 | Owner-approved parameters. §4 `PARAM-B`, §11 unresolved items, §12.2 disposition table |
```

**After:**

```
| 1 | `docs/r6-registration-protocol-03b-r1.md` | 348 | Governing procedure. §5 REG grammar, §6 VER grammar, §8 normalisation, §17 open issues |
| 2 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 646 | Owner-approved parameters. §4 `PARAM-B`, §11 unresolved items, §12.2 disposition table |
```

These are the **pre-edit** counts (348 / 646), correct for the 2026-11-07 inspection date. They are
not the post-edit counts (384 / 647), which did not exist when the proposal was written.

---

## 6. Test results

| Run | Command | Result |
|---|---|---|
| Baseline, before any edit | `./.venv/bin/python -m pytest tests/test_r6_registration_digest_conformance.py -q` | **81 passed, 1 skipped** in 0.47s |
| Baseline, before any edit | `./.venv/bin/python -m pytest tests/test_r6_settlement_integrity.py -q` | **6 passed** in 0.33s |
| After step 7, first run | conformance suite | **103 passed, 1 failed, 1 skipped** — the helper defect in §4.2 |
| After the fix | conformance suite | **104 passed, 1 skipped** in 0.26s |
| After the fix | settlement suite | **6 passed** in 0.27s |

**Delta: +23 tests, all passing.** 81 + 23 = 104. ✅

**The skip is unchanged and is a finding, not a pass.** `tests/test_r6_registration_digest_conformance.py:570`
— *"awaiting authorised ledger instantiation"*. No ledger was instantiated. The skipped count did
**not** fall.

---

## 7. Residual findings from this pass

| # | Finding | Status |
|---|---|---|
| 1 | `docs/r6-registration-protocol-03b-r1.md:213` (§10 step 8) still reads "a matching `VER:v1` record has". It is **outside** the authorised E3 anchor (`:130-135`), so it was not edited. | **Recorded, not fixed** — expanding the edit set would exceed WP2-D2 |
| 2 | The correction proposal's closing line `:885` still reads "NOT OWNER-APPROVED — NOT INCORPORATED". D12 authorises the banner at `:3` only. | **Recorded, not fixed** — scope discipline |
| 3 | `wp2-consolidated-decision-pack-2026-11-10.md:331` records E8's locus as "addendum §6", which does not exist. E8 was applied at protocol §6. | **Recorded** in Part 2 §6.2 and Part 3 §13.3 |
| 4 | The E5/E6 anchor corrections (`:93-99` → `:122-126`, `:110-116` → `:134-139`) are recorded in Part 2 §8.4 but the two upstream records were **not** edited — they are outside the four-file affected set. | **Recorded, not fixed** |
| 5 | The 146 → 147 → 149 untracked drift remains unexplained. | **Carried to WP-3** |
| 6 | All four files remain **untracked**. This record is the only audit trail. | **By design** — R6.0-D step 2 is not authorised |

---

## 7.1 Scope note for WP-4 — one file outside the four was modified, in WP-3

The WP-4 check "**No file outside the four was modified**" must be read against **this record's
scope, which is the WP-2 nine-step sequence only.**

During **WP-3** (after this record was written), `REPORTS-PROVENANCE.md` was modified — a dated
correction section was appended, as build-map §7.1 requires. That file is **tracked**, so the change
appears as an unstaged tracked modification (`git diff --stat`: 1 file changed, insertions only).

| File | Modified in | Tracked? | Authorised by |
|---|---|---|---|
| the four WP-2 files | WP-2 steps 1–7 | no (all untracked) | build-map §0.2 |
| `REPORTS-PROVENANCE.md` | WP-3 | **yes** | build-map §7.1 ("corrected with dated entries") |

**So the accurate statement is:** no file outside the four was modified **by the WP-2 sequence**; one
further file was modified **by WP-3**, under separate authorisation. Nothing was staged or committed.

---

## 8. What this record does not prove

- It does not prove the edits are **correct** — that is WP-4's job, performed by Copilot, read-only.
- It does not prove the corpus is **durable** — all four files are untracked.
- It does not prove the **skipped** test is correct, only that it is skipped.
- It does not authorise any further edit, commit, signature or grant.

**NOTHING COMMITTED · NOTHING STAGED · NOTHING TRACKED · BL-22 NOT SIGNED · G7 NOT GRANTED**

---

## 9. Second pass — 2026-11-16 (§6C, addendum only)

This section is **appended**. Sections 1–8 above are the first-pass record and are
retained unchanged. The second pass touched **one file only** — the owner parameter
addendum — and recomputed **one vector only**.

### 9.1 Scope

| Item | First pass (end state) | Second pass (end state) |
|---|---|---|
| `docs/r6-registration-protocol-03b-r1.md` | 14,620 B / 384 L | **unchanged** |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 38,699 B / 647 L | **39,784 B / 661 L** |
| `tests/test_r6_registration_digest_conformance.py` | 36,229 B / 919 L | 36,229 B / 919 L (one tuple value changed, same byte length) |
| `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` | 48,634 B / 885 L | **unchanged** |
| `docs/r6-t16-r6-decision-option-register.md` | 52,782 B / 633 L | **unchanged** |

### 9.2 Addendum byte diff

| | Bytes | Lines | SHA-256 |
|---|---|---|---|
| Before | 38,699 | 647 | `a3195ac6ffa3624651e550ca65adfe2d4eafc9fa5417f18065ac0de43cbeab45` |
| After | 39,784 | 661 | `9a817f6dec3bb01f55cf3ef77cddbb85d31612bf9399ca4dba2aa49aadfafd3d` |
| Delta | **+1,085** | **+14** | — |

Four edits. Three are line-for-line replacements; one inserts a new paragraph.

### 9.3 Edit 1 — §12.1 `PARAM-A.7` row (N1-O5 provenance inline)

Before:

```
| `PARAM-A.7` | VER-ledger entry schema (U3) | `EXACT OWNER` — incorporated 2026-11-07 | Owner work order 2026-11-07; schema detail restated from `PARAM-E.7`, `PARAM-D.3` |
```

After:

```
| `PARAM-A.7` | VER-ledger entry schema (U3) | `EXACT OWNER` — incorporated 2026-11-07 | Owner work order 2026-11-07 (O5); schema detail restated from `PARAM-E.7`, `PARAM-D.3` |
```

Change: `(O5)` added to the Source column, matching the existing `(O4)` / `(O1)`
inline-provenance form used by neighbouring rows.

### 9.4 Edit 2 — §12.1 `PARAM-A.2` row (cross-reference)

Before:

```
| `PARAM-A.2` | VER records in separate append-only ledger | `EXACT OWNER` | Owner instruction 2026-11-06 |
```

After:

```
| `PARAM-A.2` | VER records in separate append-only ledger | `EXACT OWNER` | Owner instruction 2026-11-06; O5 selection 2026-11-07 (§12.4) |
```

Change: the Source column previously read only "Owner instruction 2026-11-06"; it now
carries the N1-O5 cross-reference and points at §12.4.

### 9.5 Edit 3 — §12.4 new paragraph (N1-O5 provenance reconciliation)

Inserted immediately after the Phase 1 provenance reconciliation paragraph and before
the closing `---`. No existing text was altered.

```
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
```

The paragraph asserts the owner selection and explicitly **declines** to assert that
the 2026-11-07 artefact was located, consistent with §12.4's existing record that it
was not.

### 9.6 Edit 4 — §12.3 protocol identity and section anchors

Before:

```
- `docs/r6-registration-protocol-03b-r1.md` — 348 lines, SHA-256
  `3a003632…cd512b`. §2:23-42, §5:82-108, §6:110-135, §8:171-185,
  §10:202-217, §11:219-227, §12:229-248, §13:250-266, §14:268-280,
  §15:282-300, §16:302-319, §17:321-346.
```

After:

```
- `docs/r6-registration-protocol-03b-r1.md` — 384 lines, SHA-256
  `d3125df3…628a772c`. §2:23-42, §5:82-108, §6:110-171, §8:207-221,
  §10:238-253, §11:255-263, §12:265-284, §13:286-302, §14:304-316,
  §15:318-336, §16:338-355, §17:357-382.
```

The embedded reference at `:9-12` was **not touched** — it already read 384 lines /
`d3125df3…628a772c`. The addendum's two protocol references now agree.

### 9.7 Vector recomputation — ADDENDUM only

| Vector | Recorded before | Measured after | Verdict |
|---|---|---|---|
| `T16` | 52,782 / `43c7331c…` | 52,782 / `43c7331c…` | **MATCH — not recomputed** |
| `PROTOCOL` | 14,620 / `d3125df3…` | 14,620 / `d3125df3…` | **MATCH — not recomputed** |
| `ADDENDUM` | 38,699 / `a3195ac6…` | 39,784 / `9a817f6d…` | **MOVED — recomputed** |

`tests/test_r6_registration_digest_conformance.py:174` now reads:

```python
ADDENDUM: (39784, "9a817f6dec3bb01f55cf3ef77cddbb85d31612bf9399ca4dba2aa49aadfafd3d"),
```

T16 and PROTOCOL were measured and confirmed unmoved before the tuple was written, so
the chain established in the first pass is intact.

### 9.8 Test results

| Suite | Result |
|---|---|
| `tests/test_r6_registration_digest_conformance.py` | **104 passed, 1 skipped** |
| `tests/test_r6_settlement_integrity.py` | **6 passed** |

The single skip remains `tests/test_r6_registration_digest_conformance.py:570`
("awaiting authorised ledger instantiation"). It is a **finding, not a pass**, and no
ledger was instantiated to clear it.

### 9.9 Acceptance checks

| Check | Result |
|---|---|
| `grep -c "O5"` on the addendum | **4** (> 0) |
| Addendum's two protocol references agree | **yes** — both 384 lines / `d3125df3…628a772c` |
| Conformance suite | 104 passed / 1 skipped |
| Settlement suite | 6 passed |

### 9.10 What this pass does not prove

- It does not prove the edits are **correct** — that remains WP-4's job (Copilot, read-only).
- It does not prove the 2026-11-07 owner work-order artefact exists or was located; §12.4 records that it was not.
- It does not prove the corpus is **durable** — the addendum is untracked.
- It does not prove the **skipped** test is correct, only that it is skipped.
- It does not authorise any further edit, commit, signature or grant.

**NOTHING COMMITTED · NOTHING STAGED · NOTHING TRACKED · BL-22 NOT SIGNED · G7 NOT GRANTED**
