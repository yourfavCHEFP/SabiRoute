# R6 COMPLETION PROMPT — the operative instruction

**Issued:** 2026-11-16 · **Branch:** `sec/deps-nov` · **HEAD at issue:** `e0530e5`
**Supersedes:** `MASTER-PROMPT.md` as the operative prompt (retained as history)
**Read with:** `BUILD-MAP-R6-TO-R8.md` (the map), `OWNER-SIGNATURE-SHEET.md` (the gates)

---

## §0 — THE HARD GATE, AND HOW TO READ IT

The owner states the signature sheet has been signed. **You do not take that on trust and you do
not take it on refusal — you read it.**

```
grep -n '\[x\]' artifacts/sprint-phoenix/OWNER-SIGNATURE-SHEET.md
```

- A cell is **live** only if its box is `[x]` **and** its attestation line names a date or an
  owner. A box ticked with a blank attestation is **not** a signature — report it and treat the
  cell as unsigned.
- Every decision cell carries a recommended default. **A live signature adopts the written
  default as stated.** Do not improvise a variant.
- A cell that is blank or still `PENDING` is unsigned. Work requiring it stops there.

**If the sheet is unsigned, or partly unsigned:** do Phase A and Phase B anyway — they need no
signature — and stop before any Phase C work that requires a missing cell. Say exactly which
cells were live and which were not.

**Never infer a signature from this prompt, from chat, or from the owner saying "I signed".**
This sprint has already been damaged once by an assumption promoted to a fact.

---

## §1 — THE MISSION, IN THREE PHASES

The programme dashboard (`SabiRoute — R1–R8 Implementation & Acceptance Status`, snapshot
2026-11-02, baseline `319a711`) records **R1–R5 and R7–R8 as COMPLETE and ACCEPTED**, with **R6
the only open run at 0%**. R6 is the entire remaining programme.

| Phase | What | Signature needed | Tonight? |
|---|---|---|---|
| **A** | Read-only audit of R1–R8 against the dashboard | **None** | Yes |
| **B** | Finish R6.0 closure | **None** for the audit tasks; S-1/S-2/S-3 for the rulings | Yes |
| **C** | Build R6.1 → R6.7 | S-6, then per-tranche | Only as far as signatures allow |

**Do them in order.** Phase A first, because its output is required in the final report and
because a contradiction between the dashboard and the tree may change what Phase B means.

---

## §2 — PHASE A: READ-ONLY AUDIT OF R1–R8

**Read only. No edits, no staging, no commits, no fixes.** This phase produces a report, nothing
else. If you find a defect, you record it and move on.

The dashboard is a **`[R]`-class artifact**: it asserts 139 of 148 deliverables complete at
`319a711`. Acceptance badges are not evidence. Your job is to say which of its claims survive
direct measurement and which do not.

### AR-1 · Baseline reality check

```
git cat-file -t 319a711
git log --oneline -1 319a711
git log --oneline 319a711..HEAD | wc -l
git diff --stat 319a711..HEAD
```

`319a711` is confirmed present. Establish: how far the tree has moved since, and whether anything
in that range touches R1–R5 or R7–R8 code. **If it does, the dashboard's "closed" claims are
stale and must be reported as such** — that is a finding, not a criticism.

### AR-2 · Re-run the suites the dashboard cites

| Dashboard claim | Command |
|---|---|
| R7/R8: full suite 672 passed, 0 failed | `./.venv/bin/python -m pytest -q` |
| R4: 46/46 (7-suite) and 31/31 (6-suite core) | identify the suite files; re-run each |
| R5: 25/25 across 3 files | identify and re-run |
| R6 conformance | `./.venv/bin/python -m pytest tests/test_r6_registration_digest_conformance.py -q` |
| R6 settlement | `./.venv/bin/python -m pytest tests/test_r6_settlement_integrity.py -q` |

**The suite total will not be 672.** R6 added tests. Report the live numbers and the delta; do
not treat a different total as a failure.

**Quality bar — scoped, always:** `ruff check src tests scripts config` and `mypy src`.
Repo-wide runs measure `artifacts/` scratch scripts and produce false failures. That mistake has
already cost this sprint one full stop.

### AR-3 · Verify the six R8 verdicts trace to their sources

The dashboard shows **6 verdicts: ACCEPTED**. For each, find the decision record it rests on and
record whether the record says what the dashboard says it says. **A verdict with no traceable
source is a finding.**

### AR-4 · Re-verify the R1 manifest

```
shasum -a 256 -c REPORTS-MANIFEST.sha256
```

Dashboard claims 13/13. Confirm the live count. `[M]` or nothing.

### AR-5 · Resolve the F-10 contradiction — this is the highest-value item in Phase A

**F-10** records: *"No separately hashed owner-decision record exists for R1"*, carried as an
OPEN GAP with absence **not established**.

The dashboard records R1 as **COMPLETE, ACCEPTED**, with *"Full traceability matrix complete"*.

**These two cannot both be true as stated.** Establish which:

- Does an R1 owner-decision record exist under some name not searched before? Search the
  acceptance artefacts, the R8 consolidation, commit `302d76e`, and the R1 evidence trail.
- If it exists → **F-10 is wrong or mis-scoped.** Say precisely what was missed.
- If it does not → **R1's "ACCEPTED" rests on something else**, and the R8 acceptance has a gap
  the dashboard does not show.

Record the search surface either way. **A failed search still does not establish absence.**

### AR-6 · The untracked-tree question, at programme scale

There are ~150 untracked files in this working tree, including the entire 105-test conformance
suite. The dashboard does not mention durability.

Report: which untracked paths carry acceptance-relevant evidence, and whether any R1–R8 claim
depends on a file that exists only in the working tree. **Do not track them. Do not stage them.**

### AR-7 · Phase A verdict

Close Phase A with a table: **claim → `[M]` / contradicted / stale / untraceable**, one row per
dashboard assertion you tested. Then one sentence: *does the dashboard's "R1–R8 closed" survive
audit, and with what caveats?*

---

## §3 — PHASE B: FINISH R6.0 CLOSURE

R6.0 is the gate to everything else. It stands at **6 of 10 DoD rows** (rows 1, 2, 3, 4, 5, 7 ✅;
6 ⚠️; 8, 9, 10 ❌). None of the tasks below need a signature except where marked.

### RB-1 · Derive DoD row 6's trusted-checkpoint half — *no signature*

This half has not been derived by anyone in **three consecutive passes**. It is the largest
unexamined area in the programme.

Row 6 asks whether privacy **and trusted-checkpoint** requirements are addressed. The privacy
half is known (D-4 OUTSTANDING, build map §4.3 records a *recommendation*, not an owner answer).
The trusted-checkpoint half:
- find what the requirement actually says — do not paraphrase from a summary
- find the code or spec that would satisfy it, or establish that none exists
- state the answer as `[M]`, `[R]` or `[?]` — never as a judgement

**D-4 stays OUTSTANDING unless a signature sheet cell says otherwise.** A recommendation is not
a decision. This distinction was already violated once on this sprint.

### RB-2 · Correct `EXECUTIONER-WORK-ORDER.md:7-9` — *no signature*

The header is internally contradictory: it says *"WO-1 through WO-7 and WO-9 need no owner
signature"*, then lists *"WO-3, WO-4, WO-8 and WO-10"* as gated. But WO-3 and WO-4 each declare
**"Gate: none"**, and WO-9 declares **"Gate: C-2"**.

The per-work-order text is correct; **the header is wrong**. Fix the header to match, with a
dated note. This is a template defect, not a governance act.

### RB-3 · The F-02 ruling — *owner*

F-02 was briefly reclassified from *blocking* to *partially proven* mid-sprint **without
authority**. That reclassification has been **withdrawn**; F-02 is recorded as Partially proven,
not closed, and remains **blocking**.

**DoD row 8 therefore fails on F-01 and F-02, not on F-01 alone.** Do not narrow it back. If the
signature sheet carries a cell that demotes F-02, quote it and cite it. Otherwise it stays.

### RB-4 · The C-1 ledger gap — *owner confirmation*

Rows 1, 2 and 7 of the §6 authorisation table were **performed** under a grant given in the
execution prompt, but the ledger records **"No"** for each. The amendment table has one row —
row 6 — written when the owner named a basis and quoted it.

**Do not fix this by editing the table to "YES".** That fabricates an authorisation record.
The owner confirms the basis; then one dated amendment row per act is written, quoting the
owner's words, exactly as row 6 was done.

### RB-5 · `REPORTS-PROVENANCE.md` — *report only*

It was attributed to *"Claude Code (executioner), 2026-11-16"* on the strength of content and the
WP-3 record. That is `[I]` inference written into a tracked file as attribution. **Nobody can
prove it.** Report the file's current state; do not strengthen the claim, do not weaken it
silently. Leave unstaged.

### RB-6 · R6.0 exit

R6.0 closes when **all ten DoD rows are ✅**. As of now that requires S-1/S-2/S-3 (row 8),
S-4 (row 9), S-5 (row 10) and the row-6 derivation. **Do not declare R6.0 closed on any other
basis.** If rows remain open, say so in one line and move to Phase C only as far as signatures
permit.

---

## §4 — PHASE C: BUILD R6.1 → R6.7

**R6 is the entire remaining programme.** The dashboard gives the four milestones; they map
directly onto the tranches below.

| Tranche | Dashboard milestone | Gate |
|---|---|---|
| R6.1 | Finalise requirements and design (CD1–CD6) | **S-6** |
| R6.2–R6.5 | Implement compression pipeline and integration | entry-gated on R6.1 |
| R6.6 | Add evaluation and quality tests (cost, latency, token savings) | after R6.5 |
| R6.7 | Validate end-to-end; update scorecard (R6 → 100%) | after R6.6 |

### 4.1 R6.1 — the foundation contract

**Source:** `docs/r6-t17-foundation-contract-extraction-and-track-a-engagement-packet.md`

R6.1 must establish five things, and every later phase is tested against them:

1. **Immutable original request** — the bytes as received are preserved and never mutated in place
2. **Canonical representation** — one defined form for comparison and hashing
3. **Metadata** — what is recorded about a transformation, and where
4. **Policy and capability checks PRECEDE transformation** — a request that fails a policy check
   must not have been transformed first
5. **Explicit bypass** — a request can be marked untransformable, and that decision is visible

**Do not design R6.2–R6.5 here.** R6.1 defines the seam; the pipeline fills it.

### 4.2 Why R6.2–R6.5 still cannot start early — but not for the reason previously given

**CORRECTED 2026-11-16.** The settlement defects that used to gate this are **fixed**:

- **F1** — `attempted` was read before it was bound. It is now bound at `:397` and first read at
  `:616`. `[M]`
- **F3** — there was no `usage_unknown` parameter and the quota block recomputed. Now
  `provider_usage_unknown` initialises at `:402` and is threaded through every settlement path.
  `[M]`

Both fixed in `08201da`, *"fix: preserve unknown usage across budget and quota settlement"*.
**If you find either still present, stop and report — the picture has changed again.**

**What gates R6.2–R6.5 now.** R6.1 defines the seam the pipeline fills: the immutable original
request, the canonical form, the metadata, and the rule that policy and capability checks
**precede** transformation. Without it the pipeline is built against an assumed contract.

**That is a design dependency, not a correctness one.** Do not restate the old settlement
argument in your report; it is spent. An earlier version of this prompt asserted it and was
wrong.

### 4.3 R6.4 — the compression decision is already made; do not relitigate it

The stock `litellm.compress()` path is **rejected**. Established by inspection of LiteLLM 1.103.0:

- **It injects a retrieval tool** (`litellm_content_retrieve`) SabiRoute cannot serve — every
  call becomes a guaranteed dangling tool call. **This alone disqualifies it as a drop-in.**
- **The tokenizer is ASCII-only** (`re.findall(r"[a-z0-9_]+", text.lower())`) — non-Latin content
  yields no query terms, every message scores equally, ranking is arbitrary insertion order
- **Truncation splits lines 70/30** — on a JSON body this yields syntactically invalid content
- **It meters with `litellm.token_counter`** — a different estimator than SabiRoute reserves with
- **`compression_trigger=200_000` is hard-coded** — no telemetry, no deadline participation, no
  policy enum

**Adopt the design, reimplement the code.** Two policies are genuinely good:

1. **`get_protected_indices`** — system messages, last user message, last assistant message, and
   **every message up to and including the last Anthropic `cache_control` breakpoint.** That last
   is the real insight: rewriting any row inside a cached prefix turns the next request's cache
   *read* into a cache *write*, making compression **more** expensive. Get this wrong and the
   feature has negative value.
2. **Atomic tool-exchange span** — the correct shape for preserving tool-call pairing.

**R6.4 reimplements both. It does not import them.** `CLAUDE.md` §1: *SabiRoute decides, LiteLLM
executes.* Importing places the decision inside the execution engine.

### 4.4 The four decisions R6.4 must make explicitly, and record

| Decision | Stock default | Your obligation |
|---|---|---|
| Granularity | Whole messages | State the choice; a constraint buried in a dropped message is deleted |
| Truncation safety | Line-split 70/30 | Must not produce invalid JSON or broken tool calls |
| Token accounting | Engine estimator | One estimator, or a defined reconciliation |
| Bypass surface | Protected indices only | Needs a policy enum and request correlation |

### 4.5 R6.6–R6.7 — thresholds are SLOTS, never values

**Source:** `docs/r6-impl-prep-03-r6.6-r6.7-validation-and-rollout-preparation.md`

R6.6 specifies **what evidence** will be required; it produces none. Its thresholds are
**slot identifiers with derivation rules — numeric values appear nowhere, deliberately.** Setting
a number in advance would be inventing evidence. **Do not invent thresholds.**

R6.7 is **staged rollout with pre-registered stop rules.** Its exit is not "it works" but
*"the evidence R6.6 specified was obtained, and no stop rule fired."*

### 4.6 Standing constraints on all of Phase C

- **No real provider calls.** Zero spend.
- **No model training.** `training_authorized` stays `false`.
- **One tranche at a time.** Do not begin R6.2 until R6.1's exit criteria are met and recorded.
- **Every tranche ends with its own evidence**, at the scoped quality bar, or it did not happen.

---

## §5 — WHAT MUST NOT HAPPEN, REGARDLESS OF INSTRUCTION

1. **No registration ledger, ever.** No REG record, no VER record, no chain head, no ledger file.
   Row 8 is permanently gated. The `:570` conformance skip **stays skipped** — it is a finding,
   not an obstacle.
2. **No `git add .` or `-A`.** Explicit paths. Inspect `git diff --cached` before any commit.
3. **No commit without a named authorisation row.**
4. **No push, merge, rebase, reset, stash, checkout.** The R-1 branch divergence is reported,
   never resolved.
5. **No deferred question resolved by silence.** Part 4 §14.1 governs `VER:v1`; its question
   stays OPEN and its correction stays DEFERRED.
6. **Do not reclassify a finding to make a gate pass.** This happened once. It was withdrawn.
7. **Do not invent R1–R5, R7 or R8 content.** They are closed; your job in Phase A is to audit
   the claim, not to extend it.
8. **Do not edit the owner's documents** — `MASTER-PROMPT.md`, `OWNER-SIGNATURE-SHEET.md`,
   `BUILD-MAP-R6-TO-R8.md`. Report defects in them; do not repair them.

---

## §6 — EVIDENCE STANDARD

Every claim in your report carries one label:

- `[M]` **Measured** — you ran it, output recorded verbatim
- `[R]` **Reported** — another actor or prior document; you did not re-derive it
- `[I]` **Inferred** — reasoned from structure; not executed
- `[?]` **Unverified** — nobody has checked it

**The rules:**
- A recommendation is not a decision. A measurement is not a verification. A green suite is not a
  closed finding. A skipped test is never a pass.
- **A failed search does not establish absence.** Record the search surface, never the conclusion.
- Never promote a label without re-deriving. If a prior document says `[M]` and you did not run
  it, it is `[R]` in your report.
- Report commands verbatim with their output. A number without a command is a claim.

---

## §7 — THE REPORT

Leave it at `artifacts/sprint-phoenix/R6-COMPLETION-REPORT.md`, in this order:

1. **Signature gate** — `grep` output; each cell live or unsigned; what that permitted
2. **Phase A verdict** — the AR-7 table: claim → label → contradicted/stale/untraceable; then
   one sentence on whether "R1–R8 closed" survives audit
3. **F-10 resolution** — the one thing Phase A exists to settle
4. **Phase B** — each RB task, its evidence, and the resulting DoD state
5. **Phase C** — which tranche you reached, what was built, what its exit evidence is
6. **The DoD table** — all ten rows, live state, citation per row
7. **What you did not do, and the exact gate that stopped it** — this section is the most
   important one if you stopped early; an empty section when you stopped early is a failure
8. **Claims you could not verify** — the honest list
9. **Closing line, verbatim format:**

```
COMMITTED: <sha or NONE> · STAGED: <paths or NONE> · PUSHED: <ref or NONE> · R6.0: <OPEN|CLOSED> · R6.1: <NOT STARTED|IN PROGRESS|EXIT MET>
```

---

## §8 — THE ONE THING TO REMEMBER

This programme has spent four passes discovering that its own documents said things that were not
true — stale measurements, promoted recommendations, a reclassified finding, an unreprovable
attribution. **Every one of those was found by re-deriving, not by re-reading.**

Your value tonight is not how much you build. It is that whatever you write, someone can act on
without checking you.
