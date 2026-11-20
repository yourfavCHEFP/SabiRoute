# R6.0 Closure — WP-0 Baseline and WP-1 Evidence Record

**Actor:** Claude Code Desktop (collaborative builder — **not** the independent verifier)
**Date:** 2026-11-09
**Scope:** WP-0 (live baseline) and WP-1 (Phase 1 verification + U2 vector refresh) only
**Status at original record (2026-11-09):** WP-0 complete · WP-1 execution complete, **WP-1 exit gate OPEN** (formal Copilot report absent at that time)
**Current status (2026-11-11):** **WP-1 EXIT PASS accepted by the Project Owner**; see §7. This owner disposition is separate from the independent findings recorded after the original evidence date.

> This is a working evidence record, not a formal closure report. It is deliberately written to
> `artifacts/r6-closure/` rather than `docs/r6-*.md` so that it does **not** perturb the 42-document
> `docs/r6-*.md` inventory that WP-3 must reconcile. A formal `r6-close-final-08` document should be
> created only once WP-3 decides how new documents enter manifest scope.

---

## 1. WP-0 — Live baseline

**VERIFIED BY RUNTIME** (commands executed 2026-11-09):

| Item | Measured value |
|---|---|
| Branch | `sec/deps-nov` |
| HEAD | `1e69ada943f3d3921122219e7a569cdff989d3fd` |
| Upstream | **none configured** (`fatal: no upstream configured for branch 'sec/deps-nov'`) |
| Tracked modifications | 0 |
| Staged changes | 0 |
| Untracked paths | 147 |
| Recent log | `1e69ada`, `08201da`, `319a711`, `302d76e`, `e9f383b` |
| `docs/r6-*.md` documents | **42** |
| R6 test files | `tests/test_r6_registration_digest_conformance.py`, `tests/test_r6_settlement_integrity.py` |
| Python interpreter | `./.venv/bin/python` → Python 3.11.15 |

Baseline matches build map §1.1 exactly (branch, HEAD, 0 tracked mods, 0 staged). The 42-document
count matches the build map's "later inventory reported 42 `docs/r6-*.md` files".

**Note on divergence.** The build map §1.1 and CLAUDE.md §9A describe divergence between
`feat/sabiroute-routing-foundation` and `origin`. That is a **different branch**. `sec/deps-nov` has
**no upstream at all**, so no ahead/behind comparison is possible or meaningful here.

**Security lane:** not touched. No file outside `tests/test_r6_registration_digest_conformance.py`
and this record was modified.

---

## 2. WP-1 — Phase 1 measurement and U2 vector refresh

### 2.1 Independent measurement of the addendum

**VERIFIED BY RUNTIME.** Recalculated through the test module's own canonical algorithm
(`_read_canonical` → strict UTF-8, BOM-rejecting, CRLF→LF → `len(encode)` + SHA-256), not copied
from any report:

| File | Live bytes | Vector bytes | Vector matches | Live SHA-256 |
|---|---:|---:|:--:|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52,782 | 52,782 | **YES** | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| `docs/r6-registration-protocol-03b-r1.md` | 12,619 | 12,619 | **YES** | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 38,603 | 35,932 | **NO** | `6916650940b73219f20f427227f4f677ea6f84bcd0ab727135d25b28b63399a6` |

Addendum: **38,603 bytes, 646 lines, UTF-8, LF-only (0 CR bytes), 0 BOM.**
Canonicalisation is identity on all three files (disk bytes == canonical bytes), so the digest
equals the on-disk SHA-256. Two independent computations (BSD `shasum -a 256` and the test
algorithm) agree.

Measured values match build map §1.2 exactly: `6916650940b7…b63399a6`, 38,603 bytes, 646 lines.

### 2.2 Corroboration that the stale vector is pre-Amendment-2, not a weakened assertion

**VERIFIED BY INSPECTION.** The addendum's own Amendment 2 header states:

> "**This amendment changes this file's whole-file digest**: the Amendment 1 digest
> `ab0bd89c…68ce891ea` (35,932 bytes, 611 lines) is superseded for the current document bytes by
> the post-amendment digest, and any genesis entry must be derived from the latter, never the
> reverse."

The stale test vector `(35932, "ab0bd89c…")` is **exactly** the superseded Amendment 1 digest.
Refreshing it to post-Amendment-2 bytes restores the fixture's truth; it does not relax it.

### 2.3 The change

**File changed (one file, one line):** `tests/test_r6_registration_digest_conformance.py`

Before (line 173):
```python
    ADDENDUM: (35932, "ab0bd89ce810abdbedae3a21903e07a4d416e2cf7470c1bc8e8c14168ce891ea"),
```

After (line 174):
```python
    ADDENDUM: (38603, "6916650940b73219f20f427227f4f677ea6f84bcd0ab727135d25b28b63399a6"),
```

Unchanged and verified by re-reading the file: `T16` and `PROTOCOL` vectors (lines 172–173), the
digest algorithm (`_read_canonical`, `sha256_text`, `whole_file_digest`), canonicalisation rules,
the U1/U3/U4/A3 vector tables, and all test semantics.

**This file is untracked** (`?? tests/test_r6_registration_digest_conformance.py`), so there is no
git-level diff. The before/after line text above is the byte-level record. This is consistent with
finding F9 (R6 protocol corpus is untracked).

### 2.4 Test evidence

**VERIFIED BY RUNTIME.**

| Run | Command | Result |
|---|---|---|
| BEFORE (focused) | `pytest tests/test_r6_registration_digest_conformance.py -k u2 -q` | **1 failed, 5 passed, 76 deselected** — `assert 38603 == 35932` at `:381` |
| AFTER (focused) | same | **6 passed, 76 deselected** |
| AFTER (full file) | `pytest tests/test_r6_registration_digest_conformance.py -q` | **81 passed, 1 skipped** |
| AFTER (settlement) | `pytest tests/test_r6_settlement_integrity.py -q` | **6 passed** |

The single skip is `tests/test_r6_registration_digest_conformance.py:570` —
*"awaiting authorised ledger instantiation"*. This is the U11 first-execution artefact absence,
documented in the module docstring as a **finding, not a pass**. No ledger was instantiated.

**Full R6 test surface after change: 87 passed, 1 skipped.**

---

## 3. Findings raised by this work (not corrections)

### F-WP1-1 — Three-way digest coupling the build map does not account for

**VERIFIED BY INSPECTION.** The addendum embeds the protocol's identity in its own text
(addendum lines 10–12):

> `**Addendum to:** docs/r6-registration-protocol-03b-r1.md` `(348 lines; SHA-256`
> `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b)`

Live protocol is **348 lines** with digest **`3a003632…`** — the cross-reference is currently
accurate. But this means:

1. **Any WP-2 edit to the protocol** invalidates the `PROTOCOL` U2 vector (test line 173).
2. It also invalidates the addendum's embedded line count **and** digest (addendum lines 11–12).
3. Correcting that cross-reference changes the addendum digest — invalidating the `ADDENDUM`
   vector just refreshed in WP-1.

**Consequence:** WP-1 and WP-2 cannot both be "done" without a defined ordering, and every pass
through the loop re-invalidates the vector stabilised in the previous pass. The build map treats
WP-1 → WP-2 as sequential; mechanically they are **coupled**. An ordering decision is needed before
WP-2 edits begin. Recommended order: **WP-2 protocol edits first, then a single combined vector
refresh (PROTOCOL + ADDENDUM) with the addendum cross-reference corrected in the same pass**, so the
chain is stabilised once rather than twice.

### F-WP1-2 — The "source of truth" for WP-2 self-declares as unapproved

**VERIFIED BY INSPECTION.** WP-2 instructs: *"Use the existing correction proposal and approved
addendum as source of truth."* The document
`docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` states on line 3:

> **PROPOSAL — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**

and lines 18–24: *"This document proposes corrections only… It does not approve U1, U2 or U3…
Operational registration authority remains **DEFERRED**."*

So the correction proposal is a **registrar-side proposal**, not approved authority. Using it to
drive normative protocol edits would import unapproved content into the normative text. The
**addendum** is owner-approved (its status line says "OWNER-APPROVED PROTOCOL PARAMETERS"); the
correction proposal is not. WP-2 needs the owner to confirm which of the two governs each specific
edit, or to approve the proposal's incorporation.

### F-WP1-3 — Stale line counts inside the correction proposal

**VERIFIED BY INSPECTION.** The correction proposal's source table (§2) records the protocol at
**349 lines** and the addendum at **499 lines**. Live values are **348** and **646**. The proposal
predates Amendment 1 (2026-11-07) and Amendment 2 (2026-11-09). Any WP-2 work must not inherit those
figures.

### F-WP1-4 — Addendum baseline names a branch that is not the live branch

**VERIFIED BY INSPECTION.** Addendum lines 7–8 record: *"Repository baseline:
`feat/sabiroute-routing-foundation` @ `08201da8013a58b486d5fa2d6c46b36588a27781`"*. Live branch is
`sec/deps-nov` at `1e69ada9`. `08201da` **is** a real ancestor commit, and Amendment 1 correctly
cites `1e69ada9`, so the historical provenance is coherent — but the named branch is no longer the
working branch. Recorded only; **not corrected**, because editing the addendum would change the
digest chain stabilised in WP-1 and WP-1 forbids repeating Phase 1 edits.

### F-WP1-5 — Decision-ID collision, register-qualified

The correction proposal's defects are **D1–D4**. T16's canonical decision cards are **D1–D6**. The
build map refers to **D1–D7** selected design choices. These are three different registers. All
references in this record and in any WP-2/WP-3 work must be register-qualified
(e.g. "correction-proposal D1–D4 (defects)" vs "T16 D1–D6 (cards)").

---

## 4. WP-2 blocker requiring an owner decision

**Registration locus for O1–O5 is structurally undefined.** PARAM-A.1 says REG is adjacent to the
canonical T16 entry, but O1–O5 are **not** T16 cards (T16 holds A1–A4, B1–B9, C1–C4, D1–D6 = 23
cards). No valid locus exists in the current text.

Per WP-2: *"Present exact options and consequences to the owner before any REG act. Document the
blocker; do not choose a locus."* **No locus has been chosen. No REG act has occurred.**

---

## 5. Compliance statement

| Requirement | Status |
|---|---|
| Inspect live state before acting | Done (§1) |
| Preserve untracked and uncommitted work | Done — 147 untracked paths untouched; 0 deletions |
| No `git reset` / `clean` / stash / branch switch / rebase / force push | Not performed |
| No `git add` / blanket staging | Not performed |
| No commit / push / deploy / migration | Not performed |
| No secrets printed or exposed | Confirmed — no `.env` read |
| No ledger / genesis / REG / VER / signature instantiated | Confirmed |
| No T16 card approved; BL-22 unsigned; G7 not granted | Confirmed |
| No R6.1–R6.7 implementation begun | Confirmed |
| Security remediation lane untouched | Confirmed |
| Never claimed a command ran without observed output | All test results are verbatim captures |

**Owner approval required for this work?** Not for WP-1 as executed — the build map §1.3 and §9
explicitly authorise the addendum measurement and the single-vector refresh. **Owner approval IS
required** before WP-2 normative edits, given F-WP1-1 (ordering) and F-WP1-2 (unapproved source).

---

## 6. Status as recorded 2026-11-09

| Work package | Status |
|---|---|
| WP-0 Live baseline | **Complete** — reproducible, no destructive action |
| WP-1 measurement + vector refresh + focused tests | **Complete** |
| WP-1 exit gate | **OPEN** — requires the VS Code Copilot read-only report. A builder may not self-certify. |
| WP-2 | **BLOCKED** — ordering decision (F-WP1-1), source-authority confirmation (F-WP1-2), registration locus |
| WP-3 | Not started |
| WP-4 | Not started — independent verification is Copilot's act |
| WP-5 | Not started — owner-only |

**R6.0 remains OPEN.**

---

## 7. WP-1 independent verification and owner acceptance update (2026-11-11)

This section supplements the 2026-11-09 Desktop-authored evidence above. It does not convert the
Desktop record into an independent verification report.

### 7.1 Copilot independent findings

The formal WP-1 verification was returned for owner review in the conversation on 2026-11-11.
Copilot's independent result was **WP-1 EXIT BLOCKED** because the complete pre-refresh fixture
was then unavailable. The report independently confirmed the live addendum, current digest vector,
current test results, and vector-level comparison. It explicitly marked the full historical
comparison of test implementation and semantics **BLOCKED**. That classification remains the
historical Copilot finding; it is not rewritten as a Copilot PASS.

### 7.2 Recovered historical fixture

A subsequent read-only recovery found the complete pre-refresh fixture as local Git blob
`531480e2c7bbc5986fee47633d54644de3236500`. The blob is unreachable and has no recoverable
original pathname, author, or timestamp. Its content SHA-256 is
`835555927658d2f6f16579482cd24baf8b1c6ad2426f74da47cc4e42f250fd63`; it is 26,272 bytes and
632 lines.

The complete blob was compared with the current
`tests/test_r6_registration_digest_conformance.py` (content SHA-256
`951db05583b656676f009c12d4881096c210efe08f06f5bb035964e83f8638ff`). The sole difference is
the `ADDENDUM` tuple in `U2_VECTORS`: old `(35932, ab0bd89c…68ce891ea)` versus current
`(38603, 69166509…b63399a6)`. No other fixture content differs. This resolves the historical
comparison gap by direct comparison with the recovered complete blob; it does not resolve the
blob's missing provenance metadata.

### 7.3 Owner disposition

**OWNER DECISION — 2026-11-11:** The Project Owner accepts **WP-1 EXIT PASS**, based on the
recovered complete pre-refresh blob and its complete comparison with the current fixture. This is
the Owner's gate disposition, not a retrospective change to Copilot's earlier independent
classification. Preserve the orphan-blob provenance limitation above.

No repository test fixture or other implementation file was modified by this update.

---

## 8. Baseline re-measure — 2026-11-16

Dated re-measurement performed under `BUILD-MAP-WP0-WP5-TO-100-2026-11-16.md` §4. This section is
appended; §1–§7 above are unchanged.

### 8.1 The seven values

| # | Command | Measured 2026-11-16 | §1 value | Match |
|---|---|---|---|---|
| 1 | `git rev-parse --abbrev-ref HEAD` | `sec/deps-nov` | `sec/deps-nov` | ✅ |
| 2 | `git rev-parse HEAD` | `1e69ada943f3d3921122219e7a569cdff989d3fd` | `1e69ada943f3d3921122219e7a569cdff989d3fd` | ✅ |
| 3 | `git status --short --branch` (branch line) | `## sec/deps-nov` — no upstream configured | no upstream | ✅ |
| 4 | tracked modifications | `0` | `0` | ✅ |
| 5 | `git status --short \| wc -l` (untracked entries) | `149` | `149` | ✅ |
| 6 | `git ls-files \| grep -c "r6-"` | `0` | `0` | ✅ |
| 7 | `ls docs/r6-*.md \| wc -l` | `42` | `42` | ✅ |

`git log -5 --oneline --decorate` head: `1e69ada (HEAD -> sec/deps-nov, feat/sabiroute-routing-foundation) test: strengthen settlement integrity regression coverage`. Last commit date remains **2026-11-07 14:45 +0100**.

**All seven values match §1. No drift since 2026-11-09. No stop condition triggered.**

### 8.2 The three U2-bound digests

Re-measured this session; all three match §1.1 exactly.

| File | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52,782 | 633 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| `docs/r6-registration-protocol-03b-r1.md` | 12,619 | 348 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 38,603 | 646 | `6916650940b73219f20f427227f4f677ea6f84bcd0ab727135d25b28b63399a6` |

The fourth affected file, `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md`, measures **48,596 bytes / 885 lines / `0a6c0f762b3836cbb0a4a0bb2d39d31461fc0948de9e18e8e76a94e60d5e8e6f`**.

### 8.3 Test baseline before any edit

| File | Result |
|---|---|
| `tests/test_r6_registration_digest_conformance.py` | **81 passed, 1 skipped** in 0.47s |
| `tests/test_r6_settlement_integrity.py` | **6 passed** in 0.33s |

The single skip is `tests/test_r6_registration_digest_conformance.py:570` — *"awaiting authorised ledger instantiation"*. **That skip is a finding, not a pass.** No ledger was instantiated to clear it.

### 8.4 Untracked-count drift

The 2026-11-16 count is **149**, unchanged from the 2026-11-09 measurement of 147 → 149 recorded in
build-map §1.2. The 146 → 147 gap remains unexplained and is **not** reconciled here by assumption;
WP-3 must produce the actual path list and diff it.

### 8.5 What this section does not prove

It does not prove the corpus is durable — all 42 `docs/r6-*.md` documents remain untracked
(`git ls-files | grep -c "r6-"` = 0). It does not prove the skipped test is correct, only that it is
skipped. It does not authorise any edit; the WP-2 sequence is authorised separately by build-map §0.2.
