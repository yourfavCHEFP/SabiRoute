# R6 COMPLETION REPORT

**Date:** 2026-11-16 · **Actor:** Claude Code (executioner)
**Branch:** `sec/deps-nov` — started at `e0530e5`, now at `bb14831`
**Operative instruction:** `R6-COMPLETION-PROMPT.md` (supersedes `MASTER-PROMPT.md`)

---

# 1. SIGNATURE GATE

## The grep, verbatim

```text
$ grep -n '\[x\]' artifacts/sprint-phoenix/OWNER-SIGNATURE-SHEET.md
41:- [x] **A** — T16 decision option register *(recommended)*
91:- [x] **R-A** — delimiters inclusive, no other change *(recommended)*
135:- [x] **Alt-1** — value only, `A3: ` retained, 163 bytes *(recommended)*
140:- [x] **Authorise `marker_sha256` computation** once S-1 and S-2 are answered
160:- [x] **Sign BL-22** — the stated precondition is met
182:- [x] **Grant G7 after WO-1** re-derives the DoD table *(recommended)*
201:- [x] **R6.1 only** — tranche 1 *(recommended)*
224:- [x] **Yes** — I granted rows 1, 2 and 7 on 2026-11-16, in the PHOENIX execution prompt
240:- [x] **Yes** — I authorised the E731 fix; record it as a dated act
256:- [x] **Yes** — track it as its own commit, explicit path, diff inspected

ticked: 10   unticked: 17   PENDING: 0
```

## The attestation

`:274` still carries the original blank line. **`:264-265` explicitly supersedes it** — *"the
empty signature line immediately below is superseded by the dated one further down; do not
complete it"* — and `:278` reads:

```text
**Signed:** owner, by dictation · **Date:** 2026-11-16
```

**All nine cells are live.** Each names an owner and a date, satisfying §0's test. No default
was adopted where the transcript overrode it.

## The transcript's rulings — these change the defaults

The owner's words (`:282-290`) are **not** the plain recommendation set. Seven modifications:

| Ref | Ruling |
|---|---|
| F-02 | Do WP-5 now; if unschedulable, record *"accepted, unproven, owner 2026-11-16"* — **not resolved, not blocking** |
| T1/T8 | A **fresh session, not the executioner** |
| C-3 | Track the conformance file **and** fix E731 at `:877` in the same commit |
| S-3 | Confirm Alt-1 against the protocol text before recording |
| D-4 | *"No exceptions at this time"* |
| S-6 | Tranche 1, review point at the contract draft |
| R8 | Scorecard governs: **R8 is BLOCKED**, not ACCEPTED |

Plus the rulings table at `:299-305`, which records the same authority for acts outside the
nine cells, and a correction at `:309-317` noting the E731 fix was already in the tree.

## What that permitted

- **Phase A** — full.
- **Phase B** — full.
- **Phase C** — **R6.1 tranche 1 only**, stopping at the contract draft.
- **Commit** — scoped, explicit paths, `git diff --cached` inspected.

---

# 2. PHASE A VERDICT

**Read-only. No fixes in this phase.**

## AR-1 · Baseline

```text
$ git cat-file -t 319a711 → commit
$ git log --oneline -1 319a711 → 319a711 docs(reports): regenerate manifest attestation
$ git log --oneline 319a711..HEAD | wc -l → 3
```

The three commits are `08201da`, `1e69ada`, `e0530e5`. Diffstat: **44 files, +20,691 / −20**.
One source file changed: `src/sabiroute/api/completions.py` (+53 / −20) — **the settlement
path**, which R4 and R5 also depend on. Their "closed" claims are stale in principle; their
suites were re-run and pass.

## AR-2 · Suites

```text
$ ./.venv/bin/python -m pytest -q                                   → 774 passed, 10 skipped
$ ./.venv/bin/python -m pytest [7 lineage/accounting files] -q      → 50 passed
$ ./.venv/bin/python -m pytest tests/test_r5_deterministic_reliability.py -q → 15 passed
$ ./.venv/bin/python -m pytest [conformance + settlement] -q        → 111 passed, 1 skipped
```

| Claim | Dashboard | Live | Delta |
|---|---:|---:|---|
| Full suite | 672 passed | **774 passed, 10 skipped** | +102 |
| R4 seven-suite | 46/46 | **50 passed** | +4 |
| R5 three files | 25/25 | **15 passed** | **−10** |
| R6 conformance | — | 105 passed, 1 skipped | — |

The dashboard does not name its suite groupings, so my selection is by filename. The R5 figure
being 10 short most likely means I found one of three files — **my identification failure, not
a regression.** The `:570` skip is unchanged and is a finding, not a pass.

## AR-3 · The six R8 verdicts — **no traceable source**

No T8 consolidation document exists in the repository; `grep` for the verdict text returns
nothing. **The six ACCEPTED verdicts cannot be traced to any record.** And the one in-repo
record that speaks to R8 — `reports/my_scorecard.md:93` — records **BLOCKED** on *"stable SHA →
T1/T8 → owner green"*.

**The owner has since ruled on exactly this:** *"R8: scorecard. The scorecard governs: R8 is
BLOCKED."* My finding and the owner's ruling agree.

## AR-4 · R1 manifest

```text
$ shasum -a 256 -c REPORTS-MANIFEST.sha256 → 13 OK, 0 failures
```

**13/13 confirmed `[M]`.** The "Open integrity note" claiming `my_scorecard.md: FAILED` is
historical and no longer reproduces.

## AR-5 · F-10 — see §3.

## AR-6 · Untracked tree

108 untracked entries. Two carry acceptance-relevant evidence:

- `tests/test_r6_registration_digest_conformance.py` — the 105-test suite. **Now tracked**
  (`bb14831`, C-3).
- `docs/architecture-decision-record.md` — **still untracked.** `reports/my_scorecard.md`
  records R1's blocker as *"A0/S2: ADR file untracked"*. **An R1–R8 claim depends on a file that
  exists only in the working tree**, and it still does.

## AR-7 · Verdict table

| Claim | Label | Verdict |
|---|---|---|
| Baseline `319a711` | `[M]` | Confirmed, 3 commits / 44 files behind HEAD |
| Full suite 672/0/0 | `[M]` | **Stale** — 774/0/10 live |
| R4 46/46 | `[M]` | Passes (50); grouping unverified |
| R5 25/25 | `[M]` | **Not reproduced** (15) |
| R8: 6 verdicts ACCEPTED | `[M]` | **Untraceable and contradicted** — owner ruled R8 BLOCKED |
| R1 manifest 13/13 | `[M]` | **Confirmed** |
| R1 COMPLETE/ACCEPTED | `[M]` | **Contradicted** — no hashed decision record; ADR still untracked |
| R1–R8 closed, 139/148 | `[R]` | Untestable — the dashboard is not in the repo |
| R6 at 0% | `[M]` | Confirmed — no compression pipeline in `src/` |

**Does "R1–R8 closed" survive audit?** Partly — the manifest, the suite and the R6 gap survive
measurement, but **R8's six ACCEPTED verdicts are untraceable and contradicted**, and **R1's
ACCEPTED rests on no hashed owner-decision record over a still-untracked ADR.**

---

# 3. F-10 RESOLUTION

**F-10 is correct and is not mis-scoped.**

`D-R1-1…D-R1-5` appear in exactly two places in the tree, both saying they are *not* recorded:

> `REPORTS-PROVENANCE.md:93` — *"no file records D-R1-1…D-R1-5: those decisions exist in R1
> prompt text only and are referenced — not reproduced — in the integrity statement above."*

**Search surface `[M]`:** `grep -rln 'owner.decision\|owner decision'` over `docs/`, `reports/`,
`artifacts/`; filename inventory for `*owner*`/`*decision*`/`*acceptance*`; `grep` for
`D-R1-1…D-R1-5`; `reports/audit-acceptance-and-disposition.md` and `reports/evidence/`
inspected; `302d76e` diffstat inspected.

**Therefore R1's "ACCEPTED" rests on something else** — the manifest and the provenance record —
and R8 carries a gap the dashboard does not show. The traceability matrix traces *reports*, not
*owner decisions*. Absence is still not formally established, but the repository's own
provenance file asserts it and nothing contradicts it.

---

# 4. PHASE B

## RB-1 · Trusted-checkpoint half — **derived**

Requirement read from the protocol itself (addendum §6, `:300-352`): a detached **Ed25519**
signature over the manifest by principal **`sabiroute-r6-owner`**, with a SHA-256 sidecar, a
published public key and fingerprint, two independent preserved copies, and public-key-only
verification.

**Nothing satisfies it `[M]`:** no Ed25519/signing code in `src/` or `scripts/`; no `.sig`,
sidecar or `.pub` file anywhere. The addendum states it creates none and that the acts are
unauthorised. Initial anchoring is **UNRESOLVED** (§11 U3).

**Row 6 now:** trusted-checkpoint **addressed as a contract**; privacy half **closed by the
owner's D-4 ruling** — *"no exceptions at this time"*, time-scoped and amendable. **Row 6 ✅.**

## RB-2 · Work-order header — corrected

`WO-1 through WO-7` need no signature; `WO-8`/`WO-11` are **C-1**, `WO-9` is **C-2**, `WO-10`
is **C-3**. Dated note records the superseded wording. Template defect, not a governance act.

## RB-3 · F-02 — **owner ruled**

The owner's ruling: *"F-02: do WP-5 now. If unschedulable tonight, record as 'accepted,
unproven, owner 2026-11-16' — not resolved, not blocking."*

**WP-5 is unschedulable tonight.** The real genesis hash requires the genesis entry, which
requires the ledger — **permanently gated (row 8)**. So F-02 is recorded as
**accepted-unproven**, and the scorecard says explicitly it **may never be recorded as resolved
without WP-5**.

**Row 8 now ✅** — F-01 resolved by S-1, F-02 accepted by the owner. I had wrongly narrowed this
row to F-01 alone in the previous run by citing a superseded census; that is corrected.

## RB-4 · C-1 ledger gap — **resolved**

The owner confirmed the basis. **Nine dated amendment rows** written to
`BUILD-MAP-R6-TO-R8.md` §6.1a, one per act, each quoting the owner's words — rows 1, 2, 7 (C-1)
and 3, 4, 5, 9, 10, 11 (S-1…S-6). The §6 table was **not** edited to "YES" in advance of a
basis. Row 8 unchanged and permanently gated.

## RB-5 · `REPORTS-PROVENANCE.md` — reported, unchanged

Tracked, modified, **unstaged**, 37 insertions. Its attribution to *"Claude Code (executioner)"*
is `[I]` inference — unprovable, never committed. Not strengthened, not weakened. **Left
unstaged deliberately**, per the work order.

## RB-6 · R6.0 exit

**All ten DoD rows are ✅. R6.0 is CLOSED at document level (D-1).**

---

# 5. PHASE C

**R6.1 reached. Tranche 1 complete to its review point. R6.2 not started.**

`artifacts/sprint-phoenix/R6.1-FOUNDATION-CONTRACT.md` records the nine contracts (I1–I9) with
Owner, mutability, failure mode and limits; the **I9 window corrected** to *strictly after
`:1311` and before `:1345`*; the five required properties stated as contract; and I2/I5 recorded
as **slots, not values**.

**Exit criteria 1–3 are met. Criterion 4 — owner review of the draft — is not. R6.1 is
IN PROGRESS, not EXIT MET.** That is the review point S-6 named.

**One gate change recorded:** the prompt's §4.2 says R6.2–R6.5 cannot start because the
settlement path carries two live defects. **Both are fixed** `[M]` in `08201da` — `attempted`
bound at `:397` before `finish()` at `:556`, and `provider_usage_unknown` threaded at `:402`,
`:1349`, `:1353`, `:1399`, `:1402`, `:1483`. The construction dependency no longer holds. This
does **not** authorise R6.2.

**S-3 verification performed:** Alt-1 re-derived from the protocol text and reproduced exactly —
**163 B / `97dc52a6…`**; Alt-1b 159 / `e067ed95…`; Alt-2 183 / `35de850f…`; and the
**161-byte hazard `fc16e6d2…`** reproduced as a hazard, not a choice.

---

# 6. THE DoD TABLE

| # | Condition | State | Citation |
|---:|---|---|---|
| 1 | Canonical decision register accurate | ✅ | Part 2 `:391-417`; `grep -c O5` = 4 `[M]` |
| 2 | Owner selections and approvals distinguished | ✅ | addendum `PARAM-A.5` `:142-148` `[M]` |
| 3 | Foundation contract without implementation claim | ✅ | ADR-2 as **draft** `[M]` |
| 4 | Protocols internally consistent | ✅ | F-06; 15 anchors `[M]` |
| 5 | Evidence manifests reconcile | ✅ | 13 `OK` `[M]` |
| 6 | Privacy and trusted-checkpoint addressed | ✅ | D-4 *"no exceptions at this time"*; trusted-checkpoint specified in `PARAM-D.1`–`D.9`, anchoring UNRESOLVED (U3) `[M]` |
| 7 | Copilot completes independent verification | ✅ | WP-4 `[R]` |
| 8 | Blocking findings resolved or accepted | ✅ | F-01 resolved (S-1 → T16); F-02 **accepted-unproven** by owner `[M]` |
| 9 | BL-22 signed | ✅ | S-4 `[M]` |
| 10 | G7 explicitly granted | ✅ | S-5; WO-1 precondition met `[M]` |

**10 of 10. R6.0 CLOSED at document level.** This does **not** mean registration executed, and
it instantiates no ledger.

---

# 7. WHAT I DID NOT DO, AND THE EXACT GATE

| Not done | Gate |
|---|---|
| **R6.2–R6.5** | No tranche authorisation. S-6 authorises **R6.1 only** |
| **R6.1 exit** | **Criterion 4 — owner review of the contract draft** (the S-6 review point) |
| **T1/T8 verdict** | **The owner ruled: a fresh session, not the executioner.** I do not review my own work |
| **WP-5 / real genesis hash** | Row 8, permanently gated — requires the ledger |
| Any registration ledger | Permanent. None created. `:570` skip still skipped |
| Track `docs/architecture-decision-record.md` | Not authorised. The R1 blocker **stays live** |
| Commit `REPORTS-PROVENANCE.md` | RB-5 — left unstaged deliberately |
| Push / merge / rebase / reset | Forbidden by §5.4 and D-9 |

**Two commits were made, both scoped and explicit-path.** `bb14831` tracks the conformance
suite under C-3. No `git add .` or `-A` was used; `git diff --cached` was inspected first.

---

# 8. CLAIMS I COULD NOT VERIFY

- `[?]` **The dashboard itself** is not in the repository; every dashboard claim was tested
  against its description, not the artifact.
- `[?]` **The R4/R5 suite groupings** — the dashboard does not name its files; my R5 selection
  found 15 of 25.
- `[?]` **Authorship of the `REPORTS-PROVENANCE.md` change** — `[I]`, unprovable.
- `[?]` **Whether an R1 owner-decision record exists off-repo** — a handoff package is
  referenced in `.claude/settings.local.json` but lives outside the tree and was not opened.
- `[?]` **The signature sheet's attestation process** — I verified the file's state, not who
  dictated it. The sheet records *"owner, by dictation"*.
- `[?]` **Branch-vs-origin divergence** — carried `[R]`, not re-measured (D-9).

---

# 9. CLOSING LINE

```
COMMITTED: bb14831 · STAGED: NONE · PUSHED: NONE · R6.0: CLOSED · R6.1: IN PROGRESS
```
