# R6-CLOSE-FINAL-07 — R6.0 Correction Report and Patch Map

**Status:** EVIDENCE — **PARTIALLY EXECUTED (documentation only, 2026-11-08)**.
Of the four corrections `C-1…C-4` in §3, **C-1 and C-3 are FIXED**, **C-4 is
fixed in its FINAL-06 half only**, and **C-2 is RECORDED, NOT FIXED** — §3.0
gives the per-correction authority. Three of the eight §5 patches (**P-1b, P-3,
P-4b**) are applied; the remainder, including the owner-blocked P-7, are not.
This document still tracks nothing, stages nothing, commits nothing, approves
nothing, registers nothing and grants no gate. The R6 corpus remains untracked
and Gate R6.0-D remains **NOT MET** at baseline
`1e69ada943f3d3921122219e7a569cdff989d3fd`.

**Date:** 2026-11-07 (UTC)
**Author identity:** Claude Code — the registrar under 03B-R1 §14 (`:268-280`),
therefore **not** an independent verifier. Nothing here satisfies `PARAM-F.3`
(CF-06 §7.2, B-1).

**Repository baseline (checked at authorship, not inherited):** branch
`sec/deps-nov` — which points at the **same commit** as
`feat/sabiroute-routing-foundation` — at
`1e69ada943f3d3921122219e7a569cdff989d3fd`, committed
`2026-11-07T14:45:03+01:00`. Tracked modifications: **0**. Untracked entries:
**146**. `git ls-files | grep -c "r6-"` = **0**. `git ls-files docs | wc -l` =
**16**.

**Subject:** a correction report over the R6 closure chain
(CF-01…CF-06), and a patch map for the defects found. Read-only: no source,
test or canonical document was modified to produce it.

---

## 0. Bottom line

**Five corrections. Two are material. None touches a U2-bound document except
C-5, which is owner-blocked and must not be applied.**

| # | Severity | Defect | Affects a U2 digest? |
|---|---|---|---|
| **C-1** | **Material** | Every CF document states baseline `08201da8`. The repository has since advanced one commit to `1e69ada9`, which **commits the two tracked modifications** the documents describe as uncommitted. CF-06 §2.1 and §7.3 now assert a repository state that no longer exists. | No |
| **C-2** | **Material** | FINAL-05 §3 verifies "**38** rows of FINAL-04 §2". FINAL-04 was subsequently revised to **39** rows, with FINAL-05 itself at row 7. The verification statement now cites a table it no longer describes. | No |
| **C-3** | Low | The corpus count is stale by one. FINAL-04 §4's "holds for the corpus as a whole" rests on a 40-file scan; FINAL-06 now exists outside both the manifest and the scan. | No |
| **C-4** | Low | "Reproducing all **33 assertions plus the two behavioural tests**" (CF-03 §B-1, CF-06 §7.2 B-1) double-counts: the 33 already contain the six behavioural assertions (proposal §8.5). | No |
| **C-5** | Low | Addendum §12.2 row 3 (`:463`) does not name U4 as still open. **This is exactly decision O2** — it is owner work, not a registrar correction. | **Yes — the addendum is U2-bound** |

**Verified with no correction needed (at authoring; see §2 for the current
single skip):** the conformance result, the two skips and their blocker
attributions, the T16 counts and terminal status, the three U2 digests, the 39
manifest rows, the single privacy finding, and the F3 citation repair (including
its trap — see §3.6).

**What this changes for the owner:** nothing is approved and nothing is closed.
C-1 does not unblock R6.0-D — the corpus is *still* entirely untracked, which is
the actual gate. It only removes the now-false premise (a dirty working tree) on
which the D-1 tracking act was scoped.

---

## 1. Method

Read-only, over the working tree at the baseline above:

| Step | Command | Purpose |
|---|---|---|
| Suite | `.venv/bin/python -m pytest tests/test_r6_registration_digest_conformance.py -q` | Reproduce CF-03 §1 |
| Suite | `.venv/bin/python -m pytest tests/test_r6_settlement_integrity.py -q` | Reproduce CF-03 §1 |
| Manifest | independent SHA-256 / byte-size / line-count recomputation of all FINAL-04 §2 rows | Reproduce FINAL-05 §3 |
| U2 | `sha256sum` on the three U2-bound files | Confirm FINAL-05 §3 |
| Privacy | `grep -rn '/Users/' docs/r6-*.md` | Reproduce CF-04 §4 |
| Git | `rev-parse`, `status`, `log`, `show --stat`, `ls-files` | Establish the current baseline |
| Text | line-addressed reads of each cited span | Confirm every citation in §3 |

No file was written to reach a conclusion. This document is the only file
created, and it creates it after all measurement.

---

## 2. Verified — no correction needed

| Claim | Source | Reproduction |
|---|---|---|
| Conformance suite: **67 passed, 2 skipped** (69 collected) | CF-03 §1, CF-06 §2.1 | **Reproduced exactly** (0.18 s) |
| Settlement suite: **6 passed** | CF-03 §1 | **Reproduced exactly** (0.27 s) |
| Combined: **73 passed, 2 skipped** | CF-03 §1 | **Reproduced exactly** |
| Skip 1 attributed to **O3** (`PARAM-B.1` undefined for multi-line responses) | CF-03 §1.1 | `test_r6_registration_digest_conformance.py:370`, verbatim |
| Skip 2 attributed to **O4 + O5** (genesis entry hash not derivable) | CF-03 §1.1 | `test_r6_registration_digest_conformance.py:389`, verbatim |
| T16: **23** owner responses, **0** `PENDING` | CF-06 §2.1 | `grep -c` = 23 / 0 |
| T16 `:629`: 0 APPROVED, 0 REGISTRATIONS, 0 INDEPENDENT VERIFICATIONS, NO GATE ACCEPTED | CF-06 §2.2 | Present verbatim at `:629` |
| Three U2 digests | FINAL-05 §3 | All three reproduced byte-identically (`43c7331c…`, `3a003632…`, `2ff885e3…`) |
| Manifest: 39 rows × 3 attributes | FINAL-04 §2 | **0 mismatches**, 0 missing files |
| Privacy: **1** low-severity finding, absolute home path | CF-04 §4, CF-05 §5 | Exactly one `/Users/` hit in the corpus, at the stated file and line (`:229`) |
| F3: the A3 response is at `T16:163-164`, not `165-166` | CF-05 §7 | Confirmed: `:163` is the response, `:164` its hard-broken continuation |
| O1, O2 remain open; `marker_sha256` uncomputable | CF-06 §5.2 | Consistent with the suite: only a synthetic U4 vector passes |

The digest layer, the manifest and the privacy conclusion are sound. The defects
below are **bibliographic**: baselines, counts and arithmetic. None of them
undermines a digest already computed.

**Re-measured 2026-11-08 at `1e69ada9` (current, not the §2 authoring baseline).**
The two suites have advanced since the figures in the table above, which are
retained as the authoring measurement:

| Suite | Then (§2 above) | Now |
|---|---|---|
| `test_r6_registration_digest_conformance.py` | 67 passed, 2 skipped | **81 passed, 1 skipped** |
| `test_r6_settlement_integrity.py` | 6 passed | **6 passed** |
| Combined | 73 passed, 2 skipped | **87 passed, 1 skipped** |

The single surviving skip is `test_u11_genesis_entry_hash_is_computable`, reason
`awaiting authorised ledger instantiation` (`:570`). The O3-keyed skip resolved
when O3 landed; the O4/O5-shaped skip is now this ledger-instantiation block.
Corpus on disk: **42** files. R6 documents tracked: **0**.

---

## 3. Corrections

### 3.0 Applied status (2026-11-08)

| # | Correction | Applied? | Target | Note |
|---|---|---|---|---|
| **C-1** | Baseline one commit behind | **Yes** | FINAL-05 §2, FINAL-06 §2.1/§7.3/§11 | FINAL-06 side applied; FINAL-05 side outside the authorised file set and not edited. |
| **C-2** | 38 rows vs 39-row table | **No — recorded only** | FINAL-05 §3 | Patch target is FINAL-05, which this pass is not authorised to edit. FINAL-05 still reads "38". |
| **C-3** | Corpus count stale by one | **Yes** | FINAL-06 §7.3 | Current count recorded as **42** files on disk. |
| **C-4** | "33 assertions plus two" double-counts | **Yes (part)** | FINAL-06 §7.2 B-1, CF-03 §5 B-1 | FINAL-06 half applied; CF-03 half outside the authorised file set. |

Nothing below in §3 is retracted. The historical measurements at `08201da8` stand
as measurements; §3 states what changed after them.

### 3.1 C-1 (material) — the stated baseline is one commit behind

**Evidence.** `HEAD` is `1e69ada943f3d3921122219e7a569cdff989d3fd`, whose subject
is `test: strengthen settlement integrity regression coverage` and whose diffstat
is:

```
 src/sabiroute/api/completions.py      |  20 +++--
 tests/test_r6_settlement_integrity.py | 164 ++++++++++++++++++++++++++++++++++
 2 files changed, 176 insertions(+), 8 deletions(-)
```

Those are precisely the two files CF-05 §2 and CF-06 §2.1 report as *modified and
uncommitted*. They are now **committed**, and
`git status --porcelain --untracked-files=no` returns **0**.

**Statements that are now false as descriptions of the repository:**

- CF-05 §2 rows: `Modified tracked files — 2`, and the trailing sentence
  "`test_r6_settlement_integrity.py` is purely additive (+161, −0)". The commit
  records the file as +164 in a two-file change totalling +176/−8.
- CF-06 §2.1 row `Tracked modifications — 2`.
- CF-06 §2.1 paragraph "The two modified tracked files are **not** among the
  three U2-bound documents… `completions.py` carries comment-only reflow".
- CF-06 §7.3 D-1 scope: "**excluding** the two modified settlement files
  (`src/sabiroute/api/completions.py`, `tests/test_r6_settlement_integrity.py`),
  which are unrelated and must not be swept in." **The exclusion is now moot** —
  there is nothing left to sweep in. A reader following D-1 today would look for
  a dirty tree and find none.

**What is *not* affected.** No digest. The U2-bound set (T16, 03B-R1, addendum)
is untouched by `1e69ada`. **Gate R6.0-D is still NOT MET** — `git ls-files |
grep -c "r6-"` = 0. This correction removes a false premise; it closes no gate.

**Historical accuracy.** CF-05 and CF-06 were correct at `08201da8`. The
correction is to add a re-baseline note, **not** to rewrite the measurement as
though it had been taken at `1e69ada`.

### 3.2 C-2 (material) — FINAL-05 verifies 38 rows of a 39-row table

**Evidence.** FINAL-04 §2 has **39** rows (verified by parse and count), and row
**7** is `docs/r6-close-final-05-independent-verification-2026-11-07.md` — this
report's subject. FINAL-04's revision note states this explicitly: "The report is
row 7." Its `§4` scope note likewise says the scan covers 39 files.

FINAL-05 §3 says: "All **38** rows of FINAL-04 §2 were recomputed… 0 mismatches
across **38** files × 3 attributes."

**Assessment.** FINAL-05's measurement was correct when taken: at that moment it
could not be a row in a table it was producing, so the table had 38 rows. The
defect is that FINAL-04 was afterwards revised — adding FINAL-05 as row 7 — and
FINAL-05's own text was never reconciled. The count is stale, not the work.

**Consequence if unpatched.** A verifier recomputing the manifest today gets 39
rows and must reconcile 39 against FINAL-05's "38" — exactly the arithmetic
friction that invites a wrong conclusion (e.g. "FINAL-04 has an unverified row").

**Recommended wording** (patch P-2): keep the measurement, restate its scope.

### 3.3 C-3 (low) — the corpus count is stale by one

**Evidence.** `ls docs/r6-*.md | wc -l` = **41** (before this document). The
manifest covers **39**. The files on disk that no manifest row covers are exactly:

- `docs/r6-close-final-04-…-manifest-and-privacy-review-2026-11-07.md` (self-excluded by design)
- `docs/r6-close-final-06-…-consolidated-closure-decision-pack-2026-11-07.md` (created after the scan)

CF-06 §7.3 says "39 files … plus FINAL-04 itself as the 40th". At authorship that
was complete; CF-06 itself was the 41st and no scan of it exists.

**Consequence.** FINAL-04 §4's sentence — the independent verification "scanned
all **40** corpus files … so the conclusion below holds for the corpus as a
whole" — holds for 40, not for 41. The privacy conclusion is *probably* still
true for FINAL-06, but that is inference, not measurement, and this report does
not claim it. A one-line scan of FINAL-06 would convert it to measurement.

**Since performed (2026-11-08).** The scan was extended to all **42** files. It
returned exactly the one finding above — no new disclosure appears in FINAL-06 or
FINAL-07 after the redaction recorded in §7 — so the privacy conclusion is now
measurement, not inference, across the whole corpus. The historical 40-file scope
above stands as the measurement at the time it was taken.

### 3.4 C-4 (low) — "33 assertions plus the two behavioural tests" double-counts

**Evidence.** Proposal §8.5 enumerates the 33: U1 **23** + U2 **3** + U3 **1** +
behavioural **6** = **33**. The six behavioural assertions are *inside* the 33.

"Plus the two behavioural tests" therefore cannot mean those six. The genuinely
additional items are the two **proposed** additions in §8.3: the span-identity
assertion (now executed, 67-pass suite) and the synthetic `marker_sha256` fixture
(now executed, U4 group). Both are already in the suite, so the margin is not
"33 versus 35" — it is "33, of which 6 are behavioural, plus 2 proposed additions
that the suite already covers".

**Why it matters.** This sentence is the acceptance criteria for `PARAM-F.3`
(B-1). A verifier holding "all 33 assertions **plus** two" would look for 35
items and could report a shortfall of two that does not exist. This is an
acceptance-criteria defect, not a cosmetic one.

**Recommended wording** (patches P-4a/P-4b): enumerate by group, drop "plus".

### 3.5 C-5 (low) — addendum §12.2 row 3 omits U4 (owner-blocked; do not patch)

**Evidence.** Addendum `:463` reads: "3. Hash extraction boundaries
(`:340-341`) | **Partially closed** — `PARAM-B.1` closed; extracted-card/whole-file
remain **U1, U2**". U4 is not named. This is precisely what decision **O2**
prescribes: "Amend addendum §4 'four digest classes' → five, and correct §12.2
row 3 to name U4 as still open" (CF-06 §5.2).

**Status: not a registrar correction.** The addendum is **U2-bound**; its digest
`2ff885e3…` enters the genesis entry. Amending §4 or §12.2 before genesis is
derived produces a genesis entry that does not match the file it binds (CF-06 R1,
§7.3 binding order). C-5 is recorded here so it is not mistaken for an oversight
and "helpfully" patched out of order. **It is O2's work, after O1.**

### 3.6 A trap worth recording — do not "fix" every `T16:165`

F3 is genuinely fixed: the decision pack now cites `T16:163-164` (`:129`), and
T16 `:163-164` is the A3 response. **But three surviving references to `T16:165`
are correct and must not be swept up by a find-and-replace:**

| Location | Refers to | Correct? |
|---|---|---|
| Addendum `:74` | provenance classes list (`:47, :55, :165`) | **Yes** — `:165` is `**Source provenance:**` |
| Addendum `:116` | "must never be presented as `EXACT OWNER`" | **Yes** — the provenance line is the one that says so |
| Addendum §12.3 `:474` | "provenance classes (`:47, :55, :165`)" | **Yes** |

CF-05 §7 F3 already states this ("they were not changed"). Recording it here
because a corpus-wide sweep for `T16:165` is the obvious wrong move, and one of
the three sits in the U2-bound addendum.

---

## 4. What is *not* a correction

- **The NO-GO.** R6.0 registration remains NO-GO; O1 and O2 are unanswered; all
  23 selections remain `NOT APPROVED`. Nothing in §3 changes that.
- **The digest layer.** Re-verified, not corrected.
- **R6.0-D.** Still NOT MET. C-1 removes a stale premise, not the gate.
- **`PARAM-F.3`.** Still unsatisfied. C-1…C-4 are registrar findings by a party
  disqualified from verifying itself.
- **The skips.** Correctly attributed as findings, not passes — two at authoring,
  one now (§2).

---

## 5. Patch map

Nine patch-map rows (P-1 and P-1b are distinct targets, not duplication), ordered
by dependency rather than severity. **Three are applied and six are not.** The
three whose target is FINAL-06 — **P-1b, P-3,
P-4b** — were applied as documentation corrections on 2026-11-08 and are marked
***(applied)*** in the table. Of the rest, P-1, P-2, P-4a and P-5 target FINAL-05,
CF-03 and FINAL-04, which this pass is not authorised to edit, and **P-7 remains
owner-blocked (O2) and must not be applied.** P-6 also targets an out-of-scope
file and is unaffected by the redaction of its own quote. Each entry is
independent of the others except P-3, which must follow P-2 (both describe the
same table).

| ID | File | Location | Current text (verbatim) | Replacement | Authority | Digest effect |
|---|---|---|---|---|---|---|
| **P-1** | CF-05 | §2, after the baseline table | `Both modified files are preserved and were not altered by this verification.` | Append: *"**Re-baselined:** at `1e69ada9` both files are committed (`test: strengthen settlement integrity regression coverage`, +176/−8) and the tree carries 0 tracked modifications. This section describes the baseline at which it was measured and is not a current-state claim."* | [REPO]/registrar, non-binding note | None (not U2-bound). Changes this file's manifest row. |
| **P-1b** *(applied)* | CF-06 | §2.1 table row + following paragraph | `**2** — src/…/completions.py, tests/test_r6_settlement_integrity.py` | Add a `Superseded at 1e69ada9 — 0` note; keep the `08201da8` measurement. | Same | None |
| **P-2** | CF-05 | §3, heading + first line | `## 3. Manifest verification — 38 files` / `All **38** rows of FINAL-04 §2 were recomputed.` | `## 3. Manifest verification — 38 rows (as then constituted)` and *"**38 rows were present at verification time** — this report could not be one of them. FINAL-04 §2 was afterwards revised to 39 rows, adding this report as row 7; the other 38 are unchanged. Current manifest total: **39** rows."* | [REPO]/registrar | None |
| **P-3** *(applied)* | CF-06 | §7.3, evidence paragraph | `39 files with SHA-256, byte size and line count, plus FINAL-04 itself as the 40th (excluded from its own table)` | Split into two paragraphs: keeps the 39-row manifest statement, then records **42** files on disk at `1e69ada9`, notes FINAL-06/FINAL-07 sit outside the 39-row manifest, and states the privacy scan now covers all 42 | [REPO]/registrar | None |
| **P-4a** | CF-03 | §5 B-1 | `reproducing all 33 assertions plus the two behavioural tests` | `reproducing the 33 assertions (23 U1 + 3 U2 + U3 + 6 behavioural) and the two proposed additions (span identity; U4 marker fixture)` | [REPO]/registrar | None — but see note on B-1 authority |
| **P-4b** *(applied)* | CF-06 | §7.2 B-1 | `reproducing all 33 assertions plus the two behavioural tests` | as P-4a | Same | None |
| **P-5** *(not applied — draft wording superseded)* | FINAL-04 | §4 scope paragraph | `scanned all **40** corpus files … so the conclusion below holds for the corpus as a whole` | Drafted when the corpus stood at 41. **Superseded:** the 2026-11-08 scan covers all **42** files, so if this is ever applied the wording must read 42, not 41 — see §3.3. | [REPO]/registrar | None |
| **P-6** | u1-u3 verification report | `:229` | `REPO = "/Users/<USER>/My ML Hub/SabiRoute"` *(OS username elided here for privacy; verbatim in the source file — see §7)* | `REPO = "<REPO>"` | [REPO], recommended non-blocking by CF-04 §4 | None to U2, **but changes this file's SHA and line count → its manifest row must be recomputed** |
| **P-7** | Addendum | `:131` (`§4`) and `:463` (`§12.2` row 3) | `Four digest classes …` / `Partially closed — … remain U1, U2` | **DO NOT APPLY** — this is decision **O2**, owner authority, and the file is **U2-bound**. Listed so the omission reads as *blocked*, not *missed*. | **[OWNER] — O2, after O1** | **Changes U2 digest `2ff885e3…`** |

**P-1 meets B-1? No.** No patch in this map satisfies `PARAM-F.3`; P-4a/P-4b only
make the acceptance criteria verifiable. The verifier must still be an identity
distinct from the registrar.

---

## 6. Ordering, if these are ever applied

The corpus's own binding order (CF-06 §7.3) governs, and these patches do not
change it:

1. Answer **O1** (U4 REG-marker definition) — unchanged by this report.
2. Apply P-7 (O2) — the *only* patch touching a U2-bound file, hence **after**
   O1 and **before** genesis derivation.
3. Apply P-1, P-1b, P-2, P-3, P-4a, P-4b, P-5 — all on non-U2-bound documents.
4. Apply P-6 only if the owner accepts the privacy recommendation; then recompute
   that file's manifest row.
5. **Re-derive the manifest** (FINAL-04 §2) against the patched corpus. Any patch
   changes a SHA-256 and a line count; the manifest is a measurement, not a
   commitment, and must be re-measured rather than edited.
6. Track the corpus (D-1) — **now with no settlement files to exclude** (C-1).
7. Derive genesis from post-amendment digests; then register.

**Anti-order.** Applying P-7 before O1, or deriving genesis from
`08201da8`-era digests, reproduces R1: a genesis entry that does not match the
bytes it binds.

---

## 7. This document's own corpus impact

This file is `docs/r6-*.md` number **42** and is untracked. It is not a row in the
39-row manifest and adds no decision card; it does not modify T16 or any
protocol. It is evidence only, never an authority, and should be tracked in the
same batch as the rest and included in the re-derivation at §6 step 5.

**Measured 2026-11-08:** `ls -1 docs/r6-*.md | wc -l` = **42**, of which **0**
are tracked. This file was the 41st when C-3 was written and is the 42nd now, so
the counts in C-3 and P-3/P-5 shift by one accordingly.

**Privacy note (2026-11-08).** The P-6 row in §5 previously reproduced the OS
username verbatim, adding a *second* instance of the class CF-04 reports at the
source file's `:229`. That occurrence in this report has been elided to `<USER>`.
The source file is outside this correction's authorised set and was **not**
edited, so its `:229` occurrence **remains unresolved** — a distinct, still-open
finding from the one repaired here.

---

## 8. What this report does not do

- It applies no patch to any file outside FINAL-06/FINAL-07. C-1, C-3 and the
  FINAL-06 half of C-4 are applied as documentation corrections (2026-11-08);
  P-1, P-2, P-4a, P-5, P-6 and P-7 remain proposals against files this pass may
  not edit.
- It approves, adopts or registers nothing; O1–O5, R6.0-D and all 23 decisions
  are untouched.
- It does not satisfy or partially satisfy `PARAM-F.3`.
- It does not mark Gate R6.0-D met; the corpus is still untracked.
- It records the 2026-11-08 privacy scan extended to all 42 files (§3.3, §7), which
  returned the single unresolved finding at the source file's `:229`; it does not
  edit that file.
- It does not modify T16, the protocol, the addendum or any canonical document.
- It does not claim runtime behaviour; every claim is a reproduction of a
  command or a byte comparison.

**EVIDENCE — PARTIALLY EXECUTED. C-1, C-3 and the FINAL-06 half of C-4 applied as
documentation corrections on 2026-11-08; C-2 recorded but not applied; P-1, P-2,
P-4a, P-5, P-6 and P-7 unapplied; P-7 owner-blocked. The corpus remains untracked
and Gate R6.0-D remains NOT MET. R6.0 remains open; registration remains NO-GO;
R6/G7 remains not granted.**

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
