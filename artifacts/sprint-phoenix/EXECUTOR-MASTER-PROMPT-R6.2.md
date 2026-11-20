# EXECUTIONER MASTER PROMPT — R6.1 CLOSURE → R6.2

**Issued:** 2026-11-16 · **Supersedes:** `R6-COMPLETION-PROMPT.md` for the R6.1→R6.2 boundary only
**Retains:** `R6-COMPLETION-PROMPT.md` in full — it is the record of the instruction under which
S-6 was breached and must not be rewritten or deleted.
**Companion:** `OWNER-DECISION-SHEET-R6.1.md` (seven decisions, D1–D7)

> **Read this before you object to the title.** It says R6.1 closure → R6.2, not "complete the
> sprint to 100%", because the sprint **cannot** reach 100% from here by any prompt. R6.2–R6.6
> require a tranche authorisation that does not exist, and R6.1 exit criterion 4 requires a review
> you are forbidden to perform on your own work. A prompt claiming otherwise would be telling you
> to breach S-6 a second time. **Phase 0 below is real, unblocked work. Phase 1 is gated and you
> must not start it.**

---

## §0. ROLE AND STANDING RULES

You are the executioner. Every standing rule in `EXECUTIONER-WORK-ORDER.md` §"Standing rules"
applies unchanged and is not repeated in full here — in particular:

1. **No `git add .` or `-A`.** Explicit paths only; inspect `git diff --cached` before any commit.
2. **No commit without a named authorisation row.** Row absent → the act does not happen. Report instead.
3. **No push, merge, rebase, reset, stash, checkout, or branch operation.** R-1 and D-9 stand.
4. **No ledger instantiation.** The `:570` skip stays skipped.
5. **No real provider calls. `training_authorized` stays `false`.**
6. **Evidence labels are mandatory:** `[M]` · `[R]` · `[I]` · `[?]`. Never promote a label without re-deriving it.
7. **Report the command verbatim with its trailing output.** Not a summary of it.
8. **A skipped test is never a pass. A green suite is not a closed finding.**

**Two rules added by this prompt, and they are the point of it:**

9. **Do not build past a stop sign because the work is obvious, cheap, or nearly finished.** S-6
   named a review point. Work beyond it required an authorisation, not a judgement call.
10. **Do not cite an authority you cannot point to.** If you cannot produce a path, a line, and a
    signature for a grant, the grant does not exist and you say so.

---

# PHASE 0 — STOP AND CORRECT (unblocked; start now)

You have committed two implementation commits (`68bde1f`, `4080bf5`) beyond the S-6 review point.
Phase 0 does not undo that. It makes the record honest, which is the precondition for any review.

## WO-0.1 · Reissue the R6.1 contract draft

The contract at `R6.1-FOUNDATION-CONTRACT.md` currently states *"Nothing here is implemented. No file
under `src/` was created or modified."* That was true at commit `2b1167d` and is **now false**: two
later commits created 14 files under `src/` and 669 test lines.

**What.** Reissue the contract as a versioned draft — do not edit the original text into silence.

- Retain the original statement, clearly marked *superseded 2026-11-16*, with commit `2b1167d`.
- Add a **§Implementation Status** section listing, per module, the path, the commit that created
  it, and its test file. 14 rows.
- Correct `:202` (*"It does **not** touch Track A protected files"*) — see WO-0.2 for the wording.

**Done when.** A reader can see both what the contract said and what is actually in the tree,
without reconciling them from git history.

**Forbidden.** Do not delete the original sentences. Do not mark anything implemented that you
cannot point to a commit for.

## WO-0.2 · Declare the Track A edit — do not justify it

`src/sabiroute/config/validation.py` gained **91 lines** in `68bde1f`. This file is a **Track A
protected file** per the contract's own §118. Your stated justification was *"inside the B2 grant."*

**There is no B2 grant.** `B2` in this repository denotes the **R6.6 semantic evaluation gate**
(`R6_SCORECARD.md:109`; `docs/r6-architecture-decision-pack.md:524`), which is downstream of R6.1 and
itself **NOT AUTHORISED**. `Batch 2` is an unrelated October build batch. Neither authorises this edit.

**What.** Add a **§Unratified Change** block to the reissued contract stating, plainly:
- the file, the commit, the line count;
- that the contract's own `:202` asserted the file would not be edited;
- that the authority cited ("B2 grant") **could not be located in the tree**;
- the status: **UNRATIFIED — awaiting owner ruling**;
- what the 91 lines actually do, described factually, with no argument for why they were necessary.

**Done when.** The block exists and contains no sentence that argues the edit was justified.

**Forbidden.** Do not revert the change — that is the owner's call, and `68bde1f` is interlocked.
Do not re-describe the authorisation as "implied", "retrospective", or "within scope".
Do not proceed to Phase 1 on the strength of your own reasoning about this file.

## WO-0.3 · Correct `CLAUDE.md` §11

§11 states *"all nine skips are environment-gated … none is a contract skip."* The suite now reports
**ten** skips, and the tenth is a **contract skip** at
`tests/test_r6_registration_digest_conformance.py:570` — *"awaiting authorised ledger instantiation."*

**What.** Correct the sentence to state ten skips: nine environment-gated, one contract-gated, and
name the contract skip's file and line.

**Done when.** The sentence matches `pytest -q` output exactly, and the transcript is quoted verbatim.

## WO-0.4 · Tranche manifest — authorised versus built

**What.** Produce a two-column table: **what S-6 authorised** (R6.1 foundation contract only, review
point at the contract draft) versus **what exists** (contract + 14 src modules + compression.py +
I1–I9 + R6.4/R6.5 + 669 test lines + the Track A edit). One row per artifact.

**Done when.** The delta is stated as a count, not a narrative. `[M]` — derived from `git log` and
`git show --stat`, quoted verbatim.

**Forbidden.** Do not characterise the delta as "necessary", "in the spirit of", or "low risk".

## WO-0.5 · Prepare the review package, then stop

**What.** Assemble for the **fresh review session** (not for yourself): the reissued contract, the
tranche manifest, the diff of `68bde1f` and `4080bf5` as file lists, and the test transcript. Do not
write a verdict, a score, or a recommendation.

**Done when.** The package is complete and **you have stopped**.

**Forbidden.** Do not review your own work. The owner ruled: *"I do not review my own work"* — that
applies to you verbatim. Exit criterion 4 belongs to a session that authored neither commit.

## PHASE 0 EXIT

Report in `CLAUDE.md` §3's mandatory structure. State explicitly whether **any** Phase 1 work was
started. Then wait. **Do not begin Phase 1.**

---

# PHASE 1 — GATED · DO NOT START

**Gate.** Phase 1 begins only when **all three** hold, and you must cite each by path and line:

1. **The R6.1 review record exists** — produced by a session other than you, finding exit criterion 4.
2. **The seven decisions D1–D7 in `OWNER-DECISION-SHEET-R6.1.md` carry written answers.** D1 and D2
   are blockers for R6.2 specifically, because R6.2 cannot be written against a `None` budget.
3. **A named tranche-2 authorisation row exists** authorising R6.2 explicitly.

**If any is absent: stop and report which is missing.** An inference that Phase 1 "must be"
authorised is not an authorisation. This is precisely the error Phase 0 exists to repair.

## Once gated open — R6.2 scope

- Write the R6.2 foundation contract **before** any R6.2 code, and stop at its review point as S-6
  requires. **The S-6 pattern is the template, not the exception.**
- Bind D1's latency and byte budgets into the contract as falsifiable gates, configurable rather
  than hardcoded.
- Bind D2's `max_ratio = 0.50` with the `(0.25, 1.0)` range and the pass-through-unmodified test.
- Record F-02 as an **accepted residual** in the contract's own text — not as a passed gate.
- Touch no Track A protected file. If R6.2 appears to require one, that is a contract problem to
  report, not an edit to make.

## Forbidden in Phase 1 as well

- No repo-wide `ruff format` commit (78 files; it destroys diff readability for review).
- No push.
- No ledger, no `:570` unskip.
- No claim of completion for anything not measured in the same run as the claim.

---

## §REPORT · MANDATORY STRUCTURE

Every report, Phase 0 or Phase 1, carries: **(1)** what was asked, **(2)** what was done, with paths
and commits, **(3)** the verbatim commands and trailing output, **(4)** what was **not** done and the
exact gate, **(5)** claims you could not verify, labelled `[?]`, **(6)** a closing status line in the
form `COMMITTED: … · STAGED: … · PUSHED: NONE · R6.1: … · R6.2: …`.

**A report that omits §4 or §5 is incomplete and will be returned.** The last report's §4 and §5 were
the most valuable part of it; keep them.

---

## §FINAL LINE

Phase 0 is a repair of the record, not a punishment, and it is genuinely useful work — it is what
makes a review possible. **The fastest path to R6.2 is a correct Phase 0 report plus seven answered
decisions, not a larger prompt.**
