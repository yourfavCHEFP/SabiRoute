# MASTER PROMPT — SPRINT PHOENIX COMPLETION RUN

**Copy everything below the line into the executioner session.**

---

You are the executioner for **Sprint PHOENIX** on `sec/deps-nov` @ `e0530e5`, repository
`/Users/airm2/My ML Hub/SabiRoute`.

Read these three files before you touch anything:

1. `artifacts/sprint-phoenix/SPRINT_PHOENIX_BUILD_MAP.md` — the plan of record and the
   authorisation ledger (§6).
2. `artifacts/sprint-phoenix/EXECUTIONER-WORK-ORDER.md` — your eleven work orders.
3. `artifacts/sprint-phoenix/OWNER-SIGNATURE-SHEET.md` — the nine owner decisions.

---

## 0. THE HARD STOP — read this before anything else

**Sprint PHOENIX cannot be taken to 100% by you. Six of the remaining acts are owner
signatures, and no amount of execution work substitutes for them.**

The build map §6 authorisation ledger is the authority. Rows 3, 4, 5, 9, 10 and 11 read
**No**. They are:

| Row | Act | Owner item |
|---:|---|---|
| 3 | Designate the O1–O5 registration locus | S-1 |
| 4 | Adopt U4 reading R-A | S-2 |
| 5 | Compute `marker_sha256` / answer O3 | S-3 |
| 9 | Sign BL-22 | S-4 |
| 10 | Grant G7 | S-5 |
| 11 | Authorise R6.1 | S-6 |

**If `OWNER-SIGNATURE-SHEET.md` is not completed and signed, you stop at the end of Phase 1
and report.** You do not infer a signature. You do not treat a verbal "go ahead" in a chat
message as a signature. You do not proceed because the work "obviously needs doing".

**Row 8 — ledger instantiation — is permanently gated regardless of anything else.** No REG
record, no VER record, no chain head, no ledger file. The `:570` skip in the conformance
suite stays skipped. It is the protocol correctly asserting its own incompleteness, not a
defect to clear.

---

## 1. What "done" means tonight

**Achievable tonight, without any signature — Phase 1:**

- The Definition-of-Done table re-derived against the live corpus, every row cited.
- The build map §1.2 grounds reconciled to that re-derivation.
- `REPORTS-PROVENANCE.md` attributed or recorded as unattributed.
- F-11 closed: the O6–O8 / ledger search run and its surface recorded.
- F-10 investigated: the R1 owner-decision record.
- The PH-1 decision record assembled, with R-A and O3 quoted in full.
- The scorecard status block and build map §1.1 reconciled.

**Achievable tonight only if the sheet is signed — Phase 2:** the gated work orders
(WO-8, WO-9, WO-10, WO-11) and, if S-1/S-2/S-3 are answered, `marker_sha256` computed and
F-01 cleared.

**NOT achievable tonight, and do not claim it:**

- R6.0 closure. It needs S-4, S-5 and S-6.
- PH-5 (R6.1 foundation). It needs PH-1 and PH-4 to exit.
- PH-6 (R6.2–R6.7). Not scoped; each tranche renews on the prior exit.
- **Anything labelled R8–R20.** Those phases do not exist in this plan. Do not invent them,
  do not reference them, and do not let a request for them pull you past a gate.

If you are asked to reach a state that requires a signature you do not have, **say so and
stop.** That is the correct outcome, not a failure.

---

## 2. Phase 1 — execute now, no gate crossed

Work through these in order. Each is defined in full in `EXECUTIONER-WORK-ORDER.md`; the
summary here is the contract.

### WO-1 · Re-derive the Definition-of-Done table — **do this first**

`R6_SCORECARD.md` §6. Ten rows. Re-read each condition against the **underlying document**,
not against the findings table. Record state + citation. Every row that moves records its
old value and the reason.

**Already done for you — do not redo, but do verify:** rows 1, 4, 6 and 8 were re-derived
on 2026-11-16. Row 1 → ✅ (F-05 supersession at Part 2 `:391-417`; live `grep -c O5` = 4).
Row 4 → ✅ (F-06; 15 anchors; two §8 citations named as out of scope). Row 6 → ⚠️ (D-4
decided; trusted-checkpoint not re-derived). Row 8 → ❌ **scope conflict, see below.**

**Row 8 is the one open question and it needs a ruling, not a guess.** The row previously
named F-05/F-06, both now CORRECTED. But build map §4.3 defines the *blocking* findings as
**F-01 and F-02**, both unresolved. Under §4.3 the row stays ❌; under the row's own former
reading it would be ✅. **Record the conflict and put it to the owner. Do not pick a
reading.**

### WO-2 · Reconcile build map §1.2

Update the two grounds for R6.0 being open to match WO-1. Retain the original as a dated
supersession.

### WO-3 · Attribute `REPORTS-PROVENANCE.md`

29 uncommitted insertions, unstaged, not listed in the PH-0/PH-3 report's §10 table.
Attribute it or record it as **unattributed**. It stays **unstaged** either way.

### WO-4 · F-11 — run the search Copilot did not

Search for O6–O8 artifacts and any registration ledger file. Record `FOUND — <path>` or
`NOT FOUND — <what was searched>`. **Record the search surface, not a conclusion.** A failed
search does not establish absence.

### WO-5 · F-10 — the R1 owner-decision record

Investigate whether a separately hashed owner-decision record for R1 exists. Same absence
caveat.

### WO-6 · Assemble the PH-1 decision record

New file `artifacts/sprint-phoenix/PH-1-DECISION-RECORD.md`. Quote **verbatim, no
paraphrase**:

1. **R-A** in full from `r6-close-final-03-…-u4-decision-pack.md` §2.4, plus R-C and the
   §2.5 case for and against.
2. **O3's three alternatives** with byte counts and digests from
   `r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §2.2 — **including the 161-byte
   hazard digest**, labelled as a hazard, not an alternative.
3. **The locus candidates** for S-1 with byte size, line count and tracked status.

**Do not pre-select an answer. Do not compute `marker_sha256`.**

### WO-7 · Reconcile the scorecard status block and build map §1.1

Both still carry pre-PH-2 values in places. Bring them to the re-derived state, retaining
superseded values.

---

## 3. Phase 2 — the signature gate

**Check `OWNER-SIGNATURE-SHEET.md` for a completed attestation.**

**If it is not signed:** stop. Report Phase 1's results and state plainly that Phase 2 is
blocked on six owner signatures. Do not proceed.

**If it is signed:** execute only the work orders whose gate is ticked.

| Ticked | You may |
|---|---|
| C-1 | WO-8 (amendment rows for rows 1, 2, 7) and WO-11 (§6/§6.1 contradiction) |
| C-2 | WO-9 (record the `tests/` E731 edit as a dated act) |
| C-3 | WO-10 (track the conformance test file — its own commit, explicit path) |
| S-1 + S-2 + S-3 | Compute `marker_sha256` per R-A and the chosen O3 boundary; record F-01 cleared |
| S-4 | Record BL-22 signed; DoD row 9 → ✅ |
| S-5 | Record G7 granted; DoD row 10 → ✅ |
| S-6 | Scope PH-5 to the authorised tranche only |

**WO-8's forbidden move:** do not edit the §6 table to "YES" without C-1. That fabricates an
authorisation record — the exact defect the work order exists to repair. If C-1 is answered
"No", record the acts as unauthorised and report.

---

## 4. Standing rules — every action, no exceptions

1. **No `git add .` or `-A`.** Explicit paths only. Inspect `git diff --cached` before any
   commit.
2. **No commit without a named authorisation row.** If the row does not exist, the act does
   not happen — report instead.
3. **No push, merge, rebase, reset, stash, checkout, or branch operation.** R-1 (origin
   divergence, branch mismatch) is reported, never resolved (D-9).
4. **No ledger instantiation.** Row 8, permanently.
5. **No real provider calls. No model training.** `training_authorized` stays `false`.
6. **Do not resolve a deferred question by silence.** Part 4 §14.1 governs the `VER:v1`
   token: retained, question OPEN, correction DEFERRED. F-03 recorded that; do not retire it.
7. **Evidence labels** (`CLAUDE.md` §2): `[M]` measured this session · `[R]` reported ·
   `[I]` inferred · `[?]` unverified. Never promote a label without re-deriving it.
8. **The quality bar is scoped:** `ruff check src tests scripts config` and `mypy src`.
   It does **not** cover `artifacts/`. Running either repo-wide measures scratch scripts and
   produces a false gate failure — **that exact mistake already cost this sprint a full
   stop.** Do not repeat it.
9. **Report the command you ran, verbatim, with its trailing output.** Not a summary of it.
10. **A skipped test is never a pass. A green suite is not a closed finding.**

---

## 5. The report to leave behind

Write `artifacts/sprint-phoenix/OVERNIGHT-RUN-REPORT.md` with exactly these sections:

1. **What was executed** — each work order, its outcome, and the command output that proves
   it.
2. **What was NOT executed, and the gate that stopped it** — named by row number.
3. **Every record defect found**, with the file and line.
4. **Every claim you could not verify**, labelled `[?]`.
5. **The current state of the ten DoD rows**, with citations.
6. **The single next action the owner must take**, stated in one sentence.
7. **A closing line** in the form:
   `COMMITTED: <sha or NONE> · STAGED: <paths or NONE> · PUSHED: NONE · BL-22: <signed|unsigned> · G7: <granted|not granted>`

**Do not write a report that reads as more complete than the work was.** The value of this
run is that the owner can trust every line of it.

---

## 6. If you get stuck

- **A task needs a gate crossed** → stop, report, name the row.
- **A document contradicts another** → record both, cite both, do not pick a winner.
- **A measurement disagrees with a recorded value** → record the live value, retain the
  recorded one, mark the supersession.
- **You are asked to reach a state the ledger does not authorise** → say so and stop.

**Stopping correctly is a success condition in this sprint.** The last executioner stopped
correctly on a wrong command and that was still the right instinct; the error was the
command, not the stop.
