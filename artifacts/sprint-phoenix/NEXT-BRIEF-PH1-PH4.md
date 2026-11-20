# SPRINT PHOENIX — NEXT BRIEF (PH-1 / PH-4)

**Date:** 2026-11-16 · **Branch:** `sec/deps-nov` @ `e0530e5`
**Prepared by:** Claude Code · **For:** the executioner, and the owner

> **Read §0 first.** Sprint PHOENIX is **not** 100% done, and the remaining distance is
> **not execution work**. Six acts belong to the owner alone. A brief that lets an
> executioner "get to work" on PH-1 or PH-4 would cross gates this sprint exists to hold.

---

## 0. Where the sprint actually stands

| Phase | What it is | State |
|---|---|---|
| PH-0 | R6.0 closure correction (F-03/F-04/F-05/F-06) | **DONE** |
| PH-1 | Registration locus + marker definition | **BLOCKED — owner rows 3, 4, 5** |
| PH-2 | Corpus durability (F-09) | **DONE — `e0530e5`** |
| PH-3 | F-02 partial proof | **DONE** |
| PH-4 | WP-5 owner closure decision pack | **BLOCKED — owner rows 9, 10, 11** |
| PH-5 | R6.1 foundation | NOT STARTED — depends on PH-1 + PH-4 |
| PH-6 | R6.2–R6.7 | NOT SCOPED |

**3 of 6 phases complete.** PH-5 and PH-6 cannot begin until PH-1 and PH-4 exit, and both
of those exit on owner signatures, not on code.

---

## 1. Three record defects found while preparing this brief

These are **not** new findings about the system. They are defects in the *record*, and
they matter because the owner is about to be asked to decide things on the strength of it.

### 1.1 The authorisation ledger does not record three grants it claims

- Build map §6 table: rows **1, 2 and 7** each read **No**.
- Build map §6.1 prose: *"Rows 1, 2, 6 and 7 are now granted."*
- Build map §6.1 amendment table: **one row — row 6 only.** Rows 1, 2 and 7 have no
  amendment entry and no recorded basis.

Their acts were nonetheless performed: F-03–F-06 were corrected, the suites were re-run,
and the PH-3 test was added. **Three acts were executed against a grant the ledger does
not record.**

**Do not fix this by editing the table to say "YES".** That fabricates an authorisation
record. The owner confirms the basis; then one amendment row is written per act, dated,
with the owner's words quoted — exactly as row 6 was done.

### 1.2 An edit to `tests/` was made outside the map's stated scope

Build map §0.3: the PHOENIX approval does **not** authorise *"editing any source file
under `src/` or `tests/`"*.

The E731 fix at `tests/test_r6_registration_digest_conformance.py:877` edited `tests/`.
It was made on direct owner instruction (*"yes, fix it"*), which supersedes the default —
**but that instruction is recorded nowhere.** Either record it as a dated act, or revert
the fix. Leaving it unrecorded is the same defect class as §1.1.

### 1.3 The Definition-of-Done table was never updated after PH-0

`R6_SCORECARD.md` §6 still reads:

| # | Condition | Recorded | Should now read |
|---:|---|---|---|
| 1 | Canonical decision register accurate | ⚠️ Part 2 `:318` false (F-05) | F-05 **CORRECTED** — re-derive |
| 4 | Registration and verification protocols internally consistent | ❌ F-06 | F-06 **CORRECTED** — re-derive |
| 8 | Blocking findings resolved or explicitly accepted | ❌ F-05, F-06 open | both **CORRECTED** — re-derive |
| 6 | Privacy and trusted-checkpoint requirements addressed | ⚠️ P-6 open (D-4) | D-4 decided "no exceptions" — re-derive |

The findings table in the **same document** marks F-05 and F-06 `CORRECTED 2026-11-16`.
The DoD table contradicts it. The executioner's own report claimed *"EXIT: DoD rows 4 and
8 become ✅"* — the scorecard was never updated to match.

**Why this is the highest-value unblocked task:** build map §1.2 gives two independent
grounds for R6.0 being open. Ground 2 is *"F-05 and F-06 are OPEN; DoD rows 4 and 8 are ❌."*
If that re-derivation holds, **ground 2 is gone** and R6.0 rests on ground 1 alone
(registration not executable — F-01/D-2, i.e. PH-1). That materially changes what the
owner is being asked to sign in PH-4.

---

## 2. What the executioner may start now — no gate crossed

### A. Re-derive the DoD table (§1.3) — **do this first**

Re-read each of the ten conditions against the current corpus and record the state with
evidence. Do not mark a row ✅ on the strength of a findings-table entry alone; re-read the
underlying document. Where a row moves, record the old value and the reason.

This is a record reconciliation, not a gate crossing. It is the single most useful thing
that can be done before the owner answers.

### B. Record the two attribution defects (§1.1, §1.2)

Write the amendment rows and the dated act for the `tests/` edit — **but only with the
owner's confirmation of the basis.** Until then, record them as *unattributed* in a
clearly-marked block. Do not invent a basis.

### C. Attribute `REPORTS-PROVENANCE.md`

29 uncommitted insertions, insertions only, unstaged, and not listed in the executioner's
§10 working-tree table. Determine what changed and why. Record the attribution, or leave
it unstaged and named. Do not commit it.

### D. F-11 — run the search Copilot did not

Search the workspace for O6–O8 artifacts and for any registration ledger file. Record the
result as `FOUND — <path>` or `NOT FOUND — <what was searched>`. **Absence is not
established by a failed search**; record the search surface, not a conclusion.

**Do not instantiate anything.** Row 8 (ledger instantiation) is permanently gated.

### E. F-10 — the missing R1 owner-decision record

Investigate whether a separately hashed owner-decision record for R1 exists. Record what
was searched and what was found.

### F. Track the conformance test file — **only on a named act**

The owner has indicated yes. But row 6 authorises *"the 42-doc corpus"* and nothing else.
Tracking `tests/test_r6_registration_digest_conformance.py` is a **new** act: it brings 105
tests into the repository for the first time, and it carries the E731 fix. It needs its own
authorisation row, its own explicit-path staging, and its own diff inspection. Do not fold
it into a corpus commit.

---

## 3. The six owner acts — the actual blocker

Each is a row in build map §6. None can be delegated. For each: what is being asked, the
recorded recommendation, the cost, and what it unblocks.

### Act 1 — Row 3 · Designate the O1–O5 registration locus (D-2)

**Asked:** name **one existing, already-tracked document** as the sole registration locus
for O1–O5, and name it explicitly in the protocol.

**Recommendation (approved):** an existing tracked document, **not** a new file — a new
file becomes the 43rd artifact and re-opens the 42-doc / 13-entry reconciliation.

**Cost:** the register then moves whenever the prose moves, and the prose has drifted twice
(F-06). The new-file option is inventory-expensive but anchor-stable.

**The owner must supply the document's name.** The recommendation is approved; the
designation is not made.

**Unblocks:** F-01, and with it PH-1's exit.

### Act 2 — Row 4 · Adopt U4 reading R-A

**Asked:** adopt reading **R-A** for U4.

**Before the owner answers:** the executioner must quote R-A **verbatim** from its source
(`r6-close-final-03-…-u4-decision-pack.md` / the T16 register) into the decision record.
An owner cannot adopt a reading they have not been shown in full. Do not paraphrase it.

**Unblocks:** PH-1 step 5.4.

### Act 3 — Row 5 · Compute `marker_sha256` / answer O3

**Asked:** answer **O3** — the `owner_sha256` boundary — and authorise computing a
re-computable `marker_sha256`.

**Order matters:** O3 is an owner answer; `marker_sha256` is then computable. Do not
compute first and ask after.

**Unblocks:** PH-1 step 5.5, and registration executability.

### Act 4 — Row 9 · Sign BL-22 (D-5)

**Recorded recommendation:** withhold the signature until **F-05 and F-06 are resolved**.

**State change since the map was written:** F-05 and F-06 are now **CORRECTED**. The
condition the recommendation was waiting on has been met. **This act is now ripe in a way
it was not when the map was written** — put it to the owner on that basis, and let them
decide, rather than carrying the old "withhold" forward unexamined.

**Unblocks:** DoD row 9.

### Act 5 — Row 10 · Grant G7 (D-6)

**Recorded recommendation:** withhold until the closure exit gate is met.

**State change:** if §1.3's re-derivation holds, the closure exit gate is now down to
BL-22 and G7 themselves — a circularity the owner must break deliberately. Say so plainly
rather than presenting G7 as merely "not yet".

**Unblocks:** DoD row 10, and R6.0 closure.

### Act 6 — Row 11 · Authorise R6.1 (D-7)

**Recorded recommendation:** grant **in tranches, R6.1 only first**. R6.2 renews only after
R6.1's exit evidence is accepted.

**Cost:** up to seven owner acts instead of one. Blanket authorisation is one act and moves
faster; it also pre-commits six phases whose design is currently blocked.

**Unblocks:** PH-5.

---

## 4. Sequence once the owner answers

```
PH-1  locus named (Act 1) + R-A adopted (Act 2) + O3 answered (Act 3)
      → marker_sha256 computed → F-01 cleared → registration executable
PH-4  BL-22 signed (Act 4) + G7 granted (Act 5) + R6.1 authorised (Act 6)
      → R6.0 CLOSED, or explicitly held open
PH-5  R6.1 foundation: immutable original request · canonical representation ·
      metadata · policy/capability checks precede transformation · explicit bypass
PH-6  R6.2–R6.7, per tranche, each renewing on the prior exit
```

**Runs in parallel, permanently:** the P0 lane. Sprint PHOENIX does not block P0-2.

---

## 5. Invariants the executioner must not break

1. **Row 8 — ledger instantiation — is permanently gated.** No REG record, no VER record,
   no chain head, no ledger file. The `:570` skip stays skipped. It is the protocol
   correctly asserting its own incompleteness, not a defect to clear.
2. **No `git add .` or `-A`.** Explicit paths only, diff inspected before every commit.
3. **No commit without a named authorisation row.** If the row does not exist, the act does
   not happen — report instead.
4. **No push, merge, rebase, or branch operation.** R-1 (origin divergence, branch
   mismatch) is reported, never resolved (D-9).
5. **No real provider calls. No model training.** `training_authorized` stays `false`.
6. **Do not resolve a deferred question by silence.** Part 4 §14.1 governs the `VER:v1`
   token: retained, question OPEN, correction DEFERRED. F-03 recorded that; do not retire it.
7. **A skipped test is never a pass.** A green suite is not a closed finding.

---

## 6. Evidence standard (`CLAUDE.md` §2, §11)

- `[M]` measured this session · `[R]` reported by another actor · `[I]` inferred ·
  `[?]` unverified. **Never promote a label without re-deriving it.**
- **Configured ≠ installed ≠ reachable ≠ working ≠ tested ≠ production-ready.**
- **The quality bar is scoped:** `ruff check src tests scripts config` and `mypy src`.
  It does **not** cover `artifacts/`. Running either repo-wide measures scratch scripts and
  produces a false gate failure — that mistake cost this sprint a full stop already.
- **Report the command you ran, verbatim, with its trailing output.** Not a summary of it.

---

## 7. The one-line answer to "is it done?"

**No. Three of six phases. The next two need six owner signatures, and no amount of
execution work substitutes for them.** The useful work available today is §2 A–E: re-derive
the DoD table, attribute the two record defects, and close out F-10 and F-11. That work
makes the owner's six decisions answerable on accurate evidence — which is the only thing
standing between this sprint and its next phase.
