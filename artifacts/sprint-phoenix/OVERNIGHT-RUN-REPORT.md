# OVERNIGHT RUN REPORT — SPRINT PHOENIX

**Date:** 2026-11-16 · **Actor:** Claude Code (executioner)
**Branch:** `sec/deps-nov` @ `e0530e5` · **HEAD unchanged by this run**
**Phase executed:** Phase 1 only (WO-1 … WO-7)
**Phase NOT executed:** Phase 2 — `OWNER-SIGNATURE-SHEET.md` is **unsigned**

> **The hard gate held.** Every box in `OWNER-SIGNATURE-SHEET.md` is `- [ ]`; the attestation
> reads `Signed: ______ Date: ______`. `grep -c '^- \[x\]'` returns **0** `[M]`. Per §0 of the
> master prompt, the run stops at the end of Phase 1. No signature was inferred, and no verbal
> "go ahead" was treated as one.

---

# 1. WHAT WAS EXECUTED

## WO-1 · Definition-of-Done table re-derived

`artifacts/r6-closure/R6_SCORECARD.md` §6. All ten rows now carry a state and a citation.
Rows 1, 4, 6 and 8 were re-read against the **underlying documents**, not the findings table.

| Row | Before | After | Basis |
|---:|---|---|---|
| 1 | ✅ (pre-derived) | ✅ **verified** | Part 2 `:391-417` supersession exists; live `grep -c O5` = **4** `[M]` |
| 2 | ✅ bare | ✅ **cited** | addendum `PARAM-A.5` `:142-148` `[M]` |
| 3 | ✅ bare | ✅ **cited** | B1 Option A records ADR-2 as **draft** (`r6-close-final-06-…:205`) `[M]` |
| 4 | ✅ (pre-derived) | ✅ **verified** | F-06: 15 anchors; addendum §13 records old→new `[M]` |
| 5 | ✅ 13/13 | ✅ **cited** | `shasum -a 256 -c REPORTS-MANIFEST.sha256` → 13 `OK` `[M]` |
| 6 | ⚠️ "D-4 decided" | ⚠️ **corrected — D-4 NOT decided** | see §3 defect 1 |
| 7 | ✅ bare | ✅ **cited** | WP-4 independent verification (build map §4) `[R]` |
| 8 | ❌ "scope conflict" | ❌ **re-grounded on F-01** | see §3 defect 2 |
| 9 | ❌ D-5 | **untouched** | owner act — forbidden to touch |
| 10 | ❌ D-6 | **untouched** | owner act — forbidden to touch |

**Build map §1.2 ground 2 is cleared.** It read *"F-05 and F-06 are OPEN. DoD rows 4 and 8 are
❌."* F-05/F-06 are CORRECTED and row 4 is ✅. Row 8 remains ❌ but on **F-01**, so it is no
longer independent of ground 1. **This changes what S-5 is asking:** G7's stated precondition
was "do not grant until WO-1 re-derives the DoD table" — that is now done, and the table shows
three rows still open (6, 8, 9, 10), none of which G7 itself would close.

## WO-2 · Build map §1.2 reconciled

Original text retained verbatim under a dated supersession; current grounds restated as three
(F-01 / D-4 undecided / owner acts outstanding). The "two independent grounds" framing is
withdrawn because ground 2 no longer holds.

## WO-3 · `REPORTS-PROVENANCE.md` attributed

The 29-insertion change is the WP-3 dated correction. It was **omitted from the PH-0/PH-3
report's §10 table** — a reporting defect. Attributed in-file to **Claude Code (executioner),
2026-11-16**, with the caveat that its HEAD figure (`1e69ada9`) is now stale. The file is now
**37 insertions, still unstaged** `[M]`.

## WO-4 · F-11 — the search Copilot did not run

**Search surface** `[M]`:
- `grep -rln 'N1-O6\|N1-O7\|N1-O8\|\bO6\b\|\bO7\b\|\bO8\b'` over `*.md`, `*.txt`, `*.json`
- `find` for `*ledger*`, `*reg-record*`, `*ver-record*`, `*genesis*`
- `find` for filenames containing `o6` / `o7` / `o8`

**Result: `NOT FOUND`.** O6–O8 appear only as *references* in narrative documents (scorecard,
Parts 1/4, build map, PHOENIX files). No filename outside `.venv` contains o6/o7/o8. No ledger,
REG record, VER record or genesis file exists. The single `*ledger*` hit is
`docs/r6-command-centre-01-master-ledger-and-workstream-assignments-2026-11-05.md`, which
self-describes as **"COORDINATION DOCUMENT ONLY"** — a status ledger, not a registration ledger.

**A failed search does not establish absence.** F-11 is recorded as *searched, absence not
established*, not as closed.

## WO-5 · F-10 — the R1 owner-decision record

**Search surface** `[M]`: `grep -rln 'R1' docs/ artifacts/` cross-filtered for
`owner.decision.record|separately hashed`.

**Result: `NOT FOUND`.** Only the *statements that it is missing* were found —
`REPORTS-PROVENANCE.md:95-96` ("A separately hashed owner-decision record covering R1 therefore
remains an UNRESOLVED GOVERNANCE ITEM for A0") and the scorecard F-10 row. Same absence caveat.

## WO-6 · PH-1 decision record assembled

`artifacts/sprint-phoenix/PH-1-DECISION-RECORD.md`. Contains, quoted verbatim with no
paraphrase: R-A's full eight-step normative procedure and the readings table (R-A 236 B, R-C
231 B, plus R-B/R-B2/R-D/R-E/R-F); §2.5's case for and against; O3's three alternatives with
byte counts and digests (Alt-1 163, Alt-1b 159, Alt-2 183); the **161-byte hazard digest
labelled as a hazard, not an alternative**; and the three S-1 locus candidates measured.

`marker_sha256` was **not** computed `[M]`. No option was pre-selected.

## WO-7 · Status block and §1.1 reconciled

Scorecard `CURRENT GATE` / `PROVEN` / `UNPROVEN` / `BLOCKED BY` / `NEXT` and build map §1.1
both brought to the post-PH-2 state, superseded values retained.

## Quality bar — at the gate's actual scope

```text
$ ./.venv/bin/python -m ruff check src tests scripts config
All checks passed!

$ ./.venv/bin/python -m mypy src
Success: no issues found in 49 source files

$ ./.venv/bin/python -m pytest tests/test_r6_registration_digest_conformance.py -q
SKIPPED [1] tests/test_r6_registration_digest_conformance.py:570: awaiting authorised ledger instantiation
105 passed, 1 skipped in 0.47s

$ ./.venv/bin/python -m pytest tests/test_r6_settlement_integrity.py -q
6 passed in 0.27s
```

**The `:570` skip is unchanged and is a finding, not a pass.** No ledger was instantiated.

---

# 2. WHAT WAS NOT EXECUTED, AND THE GATE THAT STOPPED IT

| Row | Act | Gate | Why it did not run |
|---:|---|---|---|
| 3 | Designate the O1–O5 registration locus | **S-1** | Sheet unsigned |
| 4 | Adopt U4 reading R-A | **S-2** | Sheet unsigned |
| 5 | Compute `marker_sha256` / answer O3 | **S-3** | Sheet unsigned |
| 9 | Sign BL-22 | **S-4** | Owner act; cannot be delegated |
| 10 | Grant G7 | **S-5** | Owner act; cannot be delegated |
| 11 | Authorise R6.1 | **S-6** | Owner act; cannot be delegated |
| 8 | Instantiate any registration ledger | **permanent** | Gated regardless of signatures |
| 1, 2, 7 | Amendment rows for rows 1, 2, 7 | **C-1** | Sheet unsigned |
| — | Record the `tests/` E731 edit as a dated act | **C-2** | Sheet unsigned |
| — | Track the conformance test file | **C-3** | Sheet unsigned |

**WO-8, WO-9, WO-10 and WO-11 were not started.** In particular the §6 table was **not** edited
to "YES" for rows 1, 2 or 7 — that would fabricate an authorisation record.

---

# 3. EVERY RECORD DEFECT FOUND

1. **`R6_SCORECARD.md:217` (DoD row 6) — "D-4 decided" is unsupported.** The row read *"D-4
   decided: privacy exceptions **none**, absolute."* The build map §4.3 records only a
   **recommendation** ("No exceptions"), and the scorecard's own decisions table at `:142`
   still reads D-4 **OUTSTANDING**. A recommendation was promoted to a decision. **Corrected**
   to ⚠️ with the recommendation/decision distinction stated.

2. **`R6_SCORECARD.md:219` (DoD row 8) — misquotes build map §4.3.** The row read *"build map
   §4.3 defines the blocking findings as **F-01 and F-02**"*. §4.3 actually reads *"1 blocking
   (F-01), 1 partially proven (F-02), 4 corrected (F-03–F-06)"*. F-02 is **not** blocking.
   **Corrected**; the row stays ❌ because F-01 blocks independently.

3. **`MASTER-PROMPT.md:92-94` — carries the same misquote.** It states §4.3 "defines the
   *blocking* findings as **F-01 and F-02**". Same defect as (2). **Not edited** — it is the
   owner's instruction document, not mine to correct. Reported.

4. **`SPRINT_PHOENIX_BUILD_MAP.md` §1.2 ground 2 — stale.** Read *"F-05 … and F-06 … are OPEN.
   Definition-of-Done rows 4 and 8 are ❌."* Both findings are CORRECTED and row 4 is ✅.
   **Superseded** with the original retained.

5. **`SPRINT_PHOENIX_BUILD_MAP.md` §1.1 — three stale facts.** HEAD read `1e69ada9` (now
   `e0530e5`); the untracked row said the `docs/r6-*` corpus was untracked (it is now 42/42
   tracked); the manifest row carried `[R]` though it verifies. **Superseded.**

6. **`SPRINT_PHOENIX_BUILD_MAP.md` §6 table vs §6.1 prose — the C-1 defect, confirmed.**
   Table rows 1, 2 and 7 read **No**; §6.1 says *"Rows 1, 2, 6 and 7 are now granted"*; the
   amendment table has **one row — row 6 only**. Three acts ran against a grant the ledger does
   not record. **Not fixed** — gated on C-1. Reported, not repaired.

7. **`EXECUTIONER-WORK-ORDER.md:7-9` — the header's gate list contradicts the work orders.**
   The header says *"WO-1 through WO-7 and WO-9 need no owner signature … WO-3, WO-4, WO-8 and
   WO-10 are gated on a specific signature."* But WO-3 and WO-4 each declare **"Gate: none"**,
   and WO-9 declares **"Gate: C-2"**. I followed the per-work-order declarations (the more
   specific text) and treated WO-9 as gated. **Not edited**; reported.

8. **`REPORTS-PROVENANCE.md:129-156` — unattributed change, omitted from the prior report.**
   The WP-3 dated correction was never attributed and does not appear in the PH-0/PH-3 report's
   §10 working-tree table. Its HEAD figure (`1e69ada9`) is stale. **Attributed** at WO-3.

9. **`SPRINT_PHOENIX_BUILD_MAP.md` §4.3 — finding census now stale for F-10/F-11.** It lists
   F-10 as "open-gap" and F-11 as "unverified". Both have now been searched. Not edited (the
   census is the owner's summary); recorded in the scorecard rows instead.

---

# 4. CLAIMS I COULD NOT VERIFY

- `[?]` **Authorship of the `REPORTS-PROVENANCE.md` correction.** Attributed to Claude Code
  (executioner) 2026-11-16 on the strength of its content and the WP-3 record. It was never
  committed, so git cannot prove it. This is `[I]` inference presented as attribution.
- `[?]` **O6–O8 absence.** Searched, not found. Absence is **not** established.
- `[?]` **R1 owner-decision record absence.** Searched, not found. Absence is **not**
  established.
- `[?]` **Branch-vs-origin divergence.** Carried as `[R]` 2026-11-04. Not re-measured — no
  network or branch operations are permitted (D-9).
- `[?]` **Copilot's WP-4 independent verification.** Carried as `[R]`. I cannot reproduce
  another actor's verification.
- `[?]` **Whether the 42-doc corpus commit met its stated condition** ("only after PH-0
  corrections are verified and every suite is green"). I did not witness the commit and cannot
  verify the ordering.
- `[?]` **Whether a signed copy of the signature sheet exists off-repo.** I can only observe
  that the in-repo file is unsigned.

---

# 5. CURRENT STATE OF THE TEN DoD ROWS

| # | Condition | State | Citation |
|---:|---|---|---|
| 1 | Canonical decision register accurate | ✅ | Part 2 `:391-417`; `grep -c O5` = 4 `[M]` |
| 2 | Owner selections and formal approvals distinguished | ✅ | addendum `PARAM-A.5` `:142-148` `[M]` |
| 3 | Foundation contract documented without claiming implementation | ✅ | ADR-2 as **draft**, `r6-close-final-06-…:205` `[M]` |
| 4 | Registration and verification protocols internally consistent | ✅ | F-06; 15 anchors; addendum §13 `[M]` |
| 5 | Required evidence manifests reconcile | ✅ | 13/13 `OK` `[M]` |
| 6 | Privacy and trusted-checkpoint requirements addressed | ⚠️ | D-4 **OUTSTANDING**; trusted-checkpoint not re-derived |
| 7 | Copilot completes independent verification | ✅ | WP-4 (build map §4) `[R]` |
| 8 | Blocking findings resolved **or** explicitly accepted by owner | ❌ | **F-01** unresolved (D-2 / S-1) |
| 9 | BL-22 signed | ❌ | D-5 / S-4 — owner act |
| 10 | G7 explicitly granted | ❌ | D-6 / S-5 — owner act |

**Six of ten hold. R6.0 remains OPEN** on rows 6, 8, 9 and 10 — every one of which is an
owner act, not an execution act.

> **Correction 2026-11-16 (reviewer).** This section originally read *"Seven of ten hold"*.
> The table above shows **six** ✅ (rows 1, 2, 3, 4, 5, 7) and **four** not ✅ (rows 6, 8, 9,
> 10). §1 of this report also read *"three rows still open (6, 8, 9, 10)"* while listing
> four. Both are arithmetic slips that overstate progress by one; the underlying table is
> correct and unchanged.
>
> **Row 8's basis is also restated.** The reclassification of F-02 out of the blocking set
> was **unauthorised and has been withdrawn** (build map §4.3). Row 8 therefore fails on
> **F-01 and F-02**, not on F-01 alone, and the ruling the owner owes is larger than this
> report concluded — not smaller.

---

# 6. THE SINGLE NEXT ACTION THE OWNER MUST TAKE

**Complete and sign `artifacts/sprint-phoenix/OWNER-SIGNATURE-SHEET.md` — answering S-1, S-2
and S-3 first, because those three are what clear F-01 and unblock PH-1.**

---

# 7. CLOSING LINE

`COMMITTED: NONE · STAGED: NONE · PUSHED: NONE · BL-22: unsigned · G7: not granted`
