# SPRINT PHOENIX — EXECUTIONER WORK ORDER

**Date:** 2026-11-16 · **Branch:** `sec/deps-nov` @ `e0530e5`
**Companion to:** `OWNER-SIGNATURE-SHEET.md` (the nine decisions) and
`NEXT-BRIEF-PH1-PH4.md` (the analysis).

**Read this first.** Eleven work orders. **WO-1 through WO-7 need no owner signature** —
start there. **WO-8, WO-9, WO-10 and WO-11 are gated** on a specific signature and must not
begin until that box is ticked: WO-8 and WO-11 on **C-1**, WO-9 on **C-2**, WO-10 on **C-3**.

*Corrected 2026-11-16 (RB-2).* The previous header read *"WO-1 through WO-7 and WO-9 need no
owner signature … WO-3, WO-4, WO-8 and WO-10 are gated"*, which contradicted the work orders
themselves: WO-3 and WO-4 each declare **"Gate: none"**, and WO-9 declares **"Gate: C-2"**.
The per-work-order declarations are authoritative; the header was wrong. This is a template
defect, not a governance act — no gate changed. Every task states what "done" means and what is
forbidden.

---

## Standing rules — apply to every work order

1. **No `git add .` or `-A`.** Explicit paths only. Inspect `git diff --cached` before any
   commit.
2. **No commit without a named authorisation row.** If the row does not exist, the act does
   not happen — report instead.
3. **No push, merge, rebase, reset, stash, checkout, or branch operation.** R-1 (origin
   divergence, branch mismatch) is reported, never resolved (D-9).
4. **No ledger instantiation.** No REG record, no VER record, no chain head, no ledger file.
   Row 8 is permanently gated. The `:570` skip stays skipped.
5. **No real provider calls. No model training.** `training_authorized` stays `false`.
6. **Do not resolve a deferred question by silence.** Part 4 §14.1 governs the `VER:v1`
   token: retained, question OPEN, correction DEFERRED. F-03 recorded that; do not retire it.
7. **Evidence labels** (`CLAUDE.md` §2): `[M]` measured this session · `[R]` reported ·
   `[I]` inferred · `[?]` unverified. Never promote a label without re-deriving it.
8. **The quality bar is scoped:** `ruff check src tests scripts config` and `mypy src`.
   It does **not** cover `artifacts/`. Running either repo-wide measures scratch scripts and
   produces a false gate failure — that mistake already cost this sprint a full stop.
9. **Report the command you ran, verbatim, with its trailing output.** Not a summary of it.
10. **A skipped test is never a pass. A green suite is not a closed finding.**

---

# PHASE A — unblocked, start now

## WO-1 · Re-derive the Definition-of-Done table

**Gate:** none. **Priority: highest.**

**Why.** `R6_SCORECARD.md` §6 still shows DoD rows 1, 4 and 8 as failing on F-05/F-06, while
the findings table in the **same document** marks both `CORRECTED 2026-11-16`. The DoD table
was never updated after PH-0. Build map §1.2 gives two independent grounds for R6.0 being
open, and ground 2 is exactly those rows.

**What.** Re-read all ten DoD conditions against the current corpus and record each state
with evidence.

**Where.** `artifacts/r6-closure/R6_SCORECARD.md` §6.

**Done when.** All ten rows carry a state and a citation. Every row that moves records its
old value and the reason. Rows 1, 4, 6 and 8 are re-derived from the underlying documents —
**not** from the findings table alone.

**Forbidden.** Do not mark a row ✅ because a findings-table entry says CORRECTED. Re-read
the document the row is about. Do not touch rows 9 and 10 — they are owner acts (S-4, S-5).

**Then.** Report whether build map §1.2 ground 2 is cleared. If it is, say so explicitly —
it changes what S-5 is asking.

---

## WO-2 · Reconcile build map §1.2 after WO-1

**Gate:** none, but **depends on WO-1**.

**What.** Update build map §1.2's two grounds for R6.0 being open to match WO-1's result.
Retain the original text as a dated supersession; do not rewrite it.

**Where.** `artifacts/sprint-phoenix/SPRINT_PHOENIX_BUILD_MAP.md` §1.2.

**Done when.** §1.2 states the current grounds with citations, and the superseded text is
still visible.

---

## WO-3 · Attribute `REPORTS-PROVENANCE.md`

**Gate:** none.

**What.** 29 uncommitted insertions, insertions only, unstaged, and **not listed** in the
PH-0/PH-3 execution report's §10 working-tree table. Determine what changed and why.

**Where.** `REPORTS-PROVENANCE.md` (tracked, modified).

**Done when.** Either the change is attributed to a named actor and date, or it is recorded
as **unattributed** in a clearly-marked block. Either way it stays **unstaged**.

**Forbidden.** Do not commit it. Do not revert it without owner instruction.

---

## WO-4 · F-11 — run the search Copilot did not

**Gate:** none.

**What.** Search the workspace for O6–O8 artifacts and for any registration ledger file.

**Done when.** The result is recorded as `FOUND — <path>` or `NOT FOUND — <what was
searched>`. **Record the search surface, not a conclusion.** A failed search does not
establish absence.

**Forbidden.** Do not instantiate anything. Do not create a ledger to "test" the search.

---

## WO-5 · F-10 — the missing R1 owner-decision record

**Gate:** none.

**What.** Investigate whether a separately hashed owner-decision record for R1 exists.

**Done when.** What was searched and what was found are both recorded, with the same
absence caveat as WO-4.

---

## WO-6 · Prepare the PH-1 decision record

**Gate:** none — this is preparation, not decision.

**What.** Assemble the material the owner needs to answer S-1, S-2 and S-3, so the answers
can be recorded the moment they are given.

**Where.** A new `artifacts/sprint-phoenix/PH-1-DECISION-RECORD.md`.

**Contents, all quoted verbatim — no paraphrase:**

1. **R-A** in full, from `r6-close-final-03-…-u4-decision-pack.md` §2.4, plus the R-C
   alternative and the §2.5 case for and against.
2. **O3's three alternatives** with their byte counts and digests, from
   `r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §2.2 — **including the 161-byte
   hazard digest**, which is not an alternative and must be labelled as a hazard.
3. **The locus candidates** for S-1, each with its byte size, line count and current tracked
   status.

**Done when.** The record contains the full text of every option, so an owner can answer
without opening another document.

**Forbidden.** Do not paraphrase R-A. Do not pre-select an answer. Do not compute
`marker_sha256` — that is gated on S-3.

---

## WO-7 · Reconcile the scorecard status block and build map §1.1

**Gate:** none, but **depends on WO-1**.

**What.** The scorecard's `CURRENT GATE` / `PROVEN` / `UNPROVEN` / `BLOCKED BY` / `NEXT`
block and the build map's §1.1 measurement table both still carry pre-PH-2 values in places.

**Done when.** Both blocks match the re-derived state, with the superseded values retained.

---

# PHASE B — gated on a signature

## WO-8 · Write the amendment rows for rows 1, 2 and 7

**Gate: C-1.** Do not begin until C-1 is ticked.

**What.** Build map §6 table rows 1, 2 and 7 read **No**; §6.1 prose says they are granted;
the amendment table has **one row — row 6 only**. Three acts ran against a grant the ledger
does not record.

**Done when.** One amendment row per act, dated, with the owner's words quoted — exactly as
row 6 was done — **and** the §6 table rows updated to match.

**Forbidden.** **Do not edit the table to "YES" without C-1.** That fabricates an
authorisation record. If C-1 is answered "No", record the acts as unauthorised and report;
do not repair the ledger.

---

## WO-9 · Record the `tests/` edit as a dated act

**Gate: C-2.**

**What.** Build map §0.3 says the PHOENIX approval does not authorise editing `src/` or
`tests/`. The E731 fix at `tests/test_r6_registration_digest_conformance.py:877` edited
`tests/` on direct owner instruction, recorded nowhere.

**Done when.** A dated act is recorded naming the file, the line, the change, the owner's
words, and the fact that it supersedes §0.3 for this one edit.

**Forbidden.** If C-2 is answered "No", revert the fix and record the gate as still failing.

---

## WO-10 · Track the conformance test file

**Gate: C-3.**

**What.** `tests/test_r6_registration_digest_conformance.py` — 105 tests, untracked, carrying
the E731 fix.

**Done when.** Staged by explicit path, `git diff --cached` inspected and confirmed to
contain **exactly one** path, committed as its own commit with its own authorisation row.

**Forbidden.** Do not fold it into a corpus commit. Do not use `git add tests/`. Do not
commit it under row 6 — row 6 authorises the 42-doc corpus and nothing else.

---

## WO-11 · Fix the build map §6 table / §6.1 contradiction

**Gate: C-1** (same basis as WO-8; do them together).

**What.** The §6 table and §6.1 prose disagree about rows 1, 2 and 7. WO-8 resolves the
ledger; this resolves the prose.

**Done when.** §6, §6.1 and the amendment table all agree, and the superseded text is
retained.

---

# PHASE C — after the owner signs

| Signature | Then |
|---|---|
| S-1 + S-2 + S-3 | Compute `marker_sha256` per R-A and the chosen O3 boundary. Record F-01 cleared. PH-1 exits. |
| S-4 | Record BL-22 signed. DoD row 9 → ✅. |
| S-5 | Record G7 granted. DoD row 10 → ✅. |
| S-6 | Scope PH-5 (R6.1 foundation) to the authorised tranche only. |

**PH-4 exits when S-4, S-5 and S-6 are all recorded** — R6.0 then closes, or is explicitly
held open with a stated reason.

---

# What is NOT in this work order, and why

- **PH-1 steps 5.4 and 5.5** — owner acts (S-1, S-2, S-3). Not executable.
- **PH-4** — owner acts (S-4, S-5, S-6). Not executable.
- **PH-5, PH-6** — depend on PH-1 and PH-4 exiting.
- **Ledger instantiation** — permanently gated (row 8), regardless of anything else.
- **R-1 branch divergence** — reported, never resolved (D-9).

**If a task in this order turns out to need a gate crossed, stop and report.** That is the
correct outcome, not a failure.
