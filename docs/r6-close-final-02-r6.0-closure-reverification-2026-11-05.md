# R6 CLOSE-FINAL-02 — R6.0 Closure Re-verification and Gap Annex

**Status:** RE-VERIFICATION AND GAP REPORT ONLY. This document closes nothing, freezes nothing, signs nothing, approves nothing, adopts no ADR, selects no option, grants no `R6/G7`, and authorises no implementation, test, or U0/U1/R6.1/Track A work.
> **Historical-status notice — 2026-11-06:** This is a historical record; its earlier counts describe the state at the time of this record. As of 2026-11-06, T16 records 23 owner responses: 22 selected and one deferred (C1).

**Mode:** read-only verification of the live repository plus read-only review of the existing corpus. **Exactly one new file was created — this one.** No existing document was modified. No register was amended. No tracked file was touched.

**Baseline (READ this session, not inherited):** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`, divergence **ahead 6 / behind 3** against `origin/feat/sabiroute-routing-foundation`.

**Relationship to `docs/r6-close-final-01-r6.0-closure-package.md` (CLOSE-FINAL-01):** this annex **supplements** it. It does not supersede it, does not restate it, and does not amend it. CLOSE-FINAL-01 remains the closure package of record. This document records only what changed, what was newly verified, and what CLOSE-FINAL-01 does not yet know.

**Canonical count unaffected: 23 decisions remain 23. All 23 remain `OUTSTANDING`. `0 approved by this document.`**

---

## 1. Baseline re-derived — the §0 limitation is lifted for this session

CLOSE-FINAL-01 §0 recorded that `git rev-parse`, `git status --porcelain`, `ls`, `find` and `grep` were all **BLOCKED** by the execution environment, and stated the consequence plainly: *"every Git-level fact in this document is **INHERITED**, not re-derived."*

**That limitation did not recur this session.** The following were executed and their output read directly.

| Fact | Command | Result | Label |
|---|---|---|---|
| Branch | `git rev-parse --abbrev-ref HEAD` | `feat/sabiroute-routing-foundation` | **VERIFIED BY RUNTIME** |
| HEAD | `git rev-parse HEAD` | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` | **VERIFIED BY RUNTIME** |
| Divergence | `git rev-list --left-right --count HEAD...origin/feat/sabiroute-routing-foundation` | `6	3` (6 ahead, 3 behind) | **VERIFIED BY RUNTIME** |
| Tracked modifications | `git status --porcelain --untracked-files=no` | *no output* — **zero** | **VERIFIED BY RUNTIME** |
| Untracked entries | `git status --porcelain --untracked-files=all \| wc -l` | `1365` | **VERIFIED BY RUNTIME** |
| Tracked files under `docs/` | `git ls-files docs` | 16 files, **none of them R6** | **VERIFIED BY RUNTIME** |
| Register decision cards | `grep -c "Owner response:"` on T16 | `23` | **VERIFIED BY RUNTIME** |
| Register approvals | `grep -n "APPROVED"` excluding `NOT APPROVED` | one hit, line 571: *"0 APPROVED; 0 SELECTED"* | **VERIFIED BY RUNTIME** |

> **Historical-state note (added during R6.0 closure execution).** The T16 citation above — line
> 571, *"0 APPROVED; 0 SELECTED"* — records T16 as it stood at the time of this verification. T16
> has since been updated: it now records 23 owner responses (22 selected, C1 deferred) with 0
> approved, and line 571 no longer carries the quoted wording. This note distinguishes the
> historical verification from current T16 state and does not alter the historical record.

**What this establishes.** The baseline CLOSE-FINAL-01 was written against is **still current**. There is no drift: branch, HEAD and divergence all match the values recorded in T16, T17 and CLOSE-FINAL-01. The inherited baseline is now **confirmed**, not merely assumed.

**What it does not establish.** RC-13 of CLOSE-FINAL-01 §10 requires the baseline be re-derived **at the closure act**. That act has not occurred. **RC-13 therefore remains `UNMET`** — but its *reason* has changed: it is no longer "could not re-derive", it is "the closure act has not happened yet". That is a materially better position and it is recorded here rather than silently upgraded.

---

## 2. Durability finding — the entire R6 corpus is untracked

**This is the most consequential new finding in this annex.**

`git ls-files docs` returns **16 tracked files**. The R6 corpus is **not among them**. Every R6 document — T9 through T17, the ADR pack, the decision pack, the prep documents, the owner-decision supplement and worksheet, the BM25 selection record, the register amendment proposal, and **CLOSE-FINAL-01 itself** — exists only as an **untracked working-tree file**.

| Layer (per the five-status ledger) | State |
|---|---|
| Owner-selected | 1 of 23 (A3) |
| **Durably recorded** | **`PARTIAL` — and weaker than CLOSE-FINAL-01 §1 records** |
| Canonically registered | 0 of 23 |
| Independently verified | 0 of 23 |
| Gate-accepted | 0 of 23 |

**Why this matters.** CLOSE-FINAL-01 §1 marks A3 as `PARTIAL` durably recorded on the basis that a file exists. A file that is untracked is **recoverable but not durable**: it survives a reboot, and it does not survive `git clean`, a fresh clone, a branch switch that discards untracked files, or any of the destructive operations §9A of `CLAUDE.md` forbids but does not prevent. **The corpus has no version-control history at all.** No R6 document has ever been committed.

**This is not a defect in any single document.** It is a property of the whole corpus, and it is the reason the audit trail is currently one filesystem event away from being unrecoverable.

**It is also not something this document may fix.** Committing is prohibited by the mission and by `CLAUDE.md` §9A without explicit owner authorisation. **It is reported, not acted on.**

**Consequence for the closure act.** A closure signed against an untracked corpus is a closure whose own evidence is not preserved. **Durability should be established before BL-22 is signed, not after.** This is a new prerequisite and it is not in CLOSE-FINAL-01's checklist.

---

## 3. Fifth identifier collision — CLOSE-FINAL-01 §4 says "four"; there are five

CLOSE-FINAL-01 §4 opens: *"Four live collisions exist in this corpus, plus one set of identifiers that does not resolve at all."* **That count is now stale.**

`docs/r6-register-amendment-proposal-2026-11-05.md` (read this session) documents a **fifth** collision, and it is the widest one:

| Register | Symbols | Meaning of `A1` |
|---|---|---|
| **Accounting defects** (T12 §5–§9A) | `A1`–`A6` | Unknown-usage detection is budget-gated |
| **Group A decisions** (T13 §7; T16 §4) | `A1`–`A4` | Adopt §§8–15 as the frozen architecture |

**The overlap is four of four** — every Group A decision label collides with an accounting defect. The reverse is not symmetric: defects `A5` and `A6` have no decision counterpart, so the collision is bounded at four labels and **no fifth decision is implied**.

**Why it is worse than the `ADR-2/C-1` collision CLOSE-FINAL-01 §4.1 already handles:**

| | `ADR-2/C-1` vs `GROUP-C/C1` | `T12/A1`–`A6` vs `GROUP-A/A1`–`A4` |
|---|---|---|
| Labels shared | 1 | **4** |
| Crosses the authority boundary | No — both are decision/ADR literature | **Yes — one register is the defect set the settlement decisions are written against** |
| Already addressed | Yes, T16 §7 | **No** |

**The clearest proof it is live, not theoretical:** decision **A2**'s recommendation reads *"BL-01…BL-04/**A6**/BL-06/BL-07 close live holes"* — and **there is no decision `A6`**. It is accounting defect `A6` (the client-cancel path). A reader answering A2 from the register must leave the register to discover what the recommendation's own justification means.

**Proposed resolution (not applied):** write accounting defects as **`T12/A1`…`T12/A6`** and Group A decisions as **`GROUP-A/A1`…`GROUP-A/A4`** in cross-reference, exactly parallel to the existing `GROUP-C/C1` convention. **No decision is renumbered; the canonical count remains 23; no new decision ID is created.**

**Status: `PROPOSAL ONLY`.** The amendment is drafted in `r6-register-amendment-proposal-2026-11-05.md` §4 and requires explicit owner authorisation. **Nothing in this annex applies it.**

### 3.1 `G16` and `G17` do not resolve in this repository

The closure mission asks which gates `R6/G7`, naming **`G16`/`G17` sub-items**. **Neither identifier exists as a gate anywhere in this repository.**

| Search | Command | Result |
|---|---|---|
| `G16` in `docs/` | `grep -rn "G16" docs` | **no matches** |
| `G16` anywhere in the tree | `grep -rln "G16" .` (excluding `.git`, `node_modules`, `.venv`) | **no matches** |
| `G17` anywhere in the tree | `grep -rln "G17" .` | **one match — `reports/my_scorecard.md:71`** |
| That match, read in context | `grep -n "G17" reports/my_scorecard.md` | `…393 passed / 4 skipped (PG17,` — **`PG17` is a PostgreSQL test identifier, not a gate** |
| `G10`–`G15` in `docs/` | `grep -rn "G10\|G11\|…\|G15" docs` | **no matches** |

**The R6 gate scale tops out at `G7`.** CLOSE-FINAL-01 §4.2 records the two colliding G-scales — R6 programme (`G4` benchmark, `G5` red-team, `G7` implementation authorisation) and Developer Workflow Overhaul (`G4` deadline/retries, `G5` async lifecycle, `G7` deployment/security) — plus repository remediation's separate `A`–`E` vocabulary. **No scale in this corpus defines a `G16` or a `G17`.**

**Status: `UNRESOLVED` — external input required.** They are programme-level identifiers taken outside this repository, in the same class as `Q3`/`Q5` (CLOSE-FINAL-01 §4.5). **Nothing is inferred about their content, and no `G16`/`G17` sub-item is invented here.** If the mission's author holds a gate register that defines them, that register must be supplied before the question can be answered; **answering it from this repository would require fabricating the sub-items.**

---

## 4. The §6 amendments have been formalised — as a proposal, still unauthorised

CLOSE-FINAL-01 §6 lists **ten** proposed amendments and states each *"requires an explicit owner-authorised amendment task"*. That list is still accurate as a list of defects.

**What has changed:** a formal amendment proposal now exists — `docs/r6-register-amendment-proposal-2026-11-05.md` — carrying **five exact-text amendments to T16** (§4, `A-1`…`A-5`) plus recommended corrections to T13 and T12 (§5). It states its own status as *"PROPOSAL ONLY… Every proposed edit in §4 and §5 requires explicit owner authorisation before it may be applied."*

**So the position is:** the amendments are **drafted and refusable**, not applied. CLOSE-FINAL-01 §6's highest-value item — *"Amendment 1 is the single highest-value action available"* (register A3) — **remains unperformed**. The proposal does not perform it either; it addresses the `A1`–`A4` collision, which is a different defect.

**Do not read the existence of a proposal as progress toward registration.** A prepared amendment is not an applied amendment, exactly as a prepared card is not a taken decision.

---

## 5. Track A — the engagement packet exists; issuance is still gated

CLOSE-FINAL-01 §7 states Track A *"cannot be engaged today"* and that D4 depends on D5. **That remains true.** What CLOSE-FINAL-01 does not record is that the packet itself has since been prepared.

`docs/r6-t17-foundation-contract-extraction-and-track-a-engagement-packet.md` (read this session) supplies:

- **I1–I9 reproduced verbatim** from T11 §8.2 with the **Owner column intact** — the column that decides which protected file each contract lands in.
- **T1–T8 reproduced verbatim** from T11 §15, un-renumbered.
- **Per-item requests for T1–T8 (7+1)**, the verified protected surface, and the acceptance form (§6).
- **Three defects found during extraction**, of which the first is the most important:

> **The nominal R6.1 insertion window contains a landmine.** T11 §8.3 places construction "immediately before `:1345`", and I9's Owner cell names the guard window `:1309–:1345`. VERIFIED at HEAD: `attempted: list[str] = []` is bound at **`:1311`** — *inside* that window. `finish()` reads `attempted` at `:602`, which is the exact mechanism of BL-04. **The window must be re-pinned to strictly after `:1311`.**

**Two protected-surface paths in T11 §15 do not exist as written:** there is no `config/validation.py` (it is `src/sabiroute/config/validation.py`) and no `src/sabiroute/dataset.py` (it is `src/sabiroute/intelligence/dataset.py`). **A reviewer signing T4 or T6/T7 against a path that does not exist has signed a surface that does not exist** — the same failure class as X-3 that D5 exists to prevent.

**Track A status remains `NOT OBTAINED`.** No reviewer was contacted. No prompt was sent. **Silence is not approval.**

---

## 6. What this annex changes in CLOSE-FINAL-01's own numbers

| CLOSE-FINAL-01 statement | Status after this annex |
|---|---|
| §0 — "every Git-level fact is INHERITED, not re-derived" | **Superseded for this session** — baseline re-derived (§1) |
| §1 — A3 `PARTIAL` durably recorded | **Weakened** — the file is untracked; the corpus has no VCS history (§2) |
| §4 — "Four live collisions exist" | **Stale** — five exist (§3) |
| §6 — ten amendments, none drafted | **Partly stale** — five T16 amendments now drafted as a proposal, still unauthorised (§4) |
| §7 — Track A cannot be engaged | **Unchanged** — but the packet is now prepared (§5) |
| §10 RC-13 — baseline not re-derivable | **Reason changed** — re-derivable; the closure act has not occurred |
| §11 — R6.0 closure ~29% | **Unchanged** — no registration, no signature, no gate acceptance occurred |
| §12 — **NO-GO** | **Unchanged** — see §7 |

**No percentage is revised.** The ~29% figure is driven by registrations and signatures, and this session produced neither. Re-deriving a baseline and finding a fifth collision are **audit improvements, not closure progress**, and are not credited as such.

---

## 7. What this annex does not change

**The verdict stands: NO-GO for R6.0 closure and NO-GO for architecture freeze.**

All three R6.0 conditions (T13 §19.1) remain **NOT MET**:

| Condition | Actual | Verdict |
|---|---|---|
| 1. Adopt ADR-1 (A3) | Owner-selected, **unregistered** | **NOT MET** |
| 2. Adopt ADR-2 (B1) incl. `ADR-2/C-1` | `OUTSTANDING`; `C-1` unrecorded | **NOT MET** |
| 3. Record Group A + Group B, then sign BL-22 | 0 registered; `C-02` open; unsigned | **NOT MET** |

**`R6/G7` — implementation authorisation: `NOT GRANTED`.** Never requested. Cannot be requested by a review report.

**BL-22 — the R6.0 signature act: `NOT SIGNED`.**

---

## 8. Safety boundary — what this session did not do

| Prohibition | Status |
|---|---|
| Implement R6.1–R6.7 | **Not done** |
| Change production code | **Not done** — zero writes outside this document |
| Execute tests | **Not done** — nothing executed |
| Provider calls | **Not done** |
| Migrations, deployments | **Not done** |
| Commits, staging, resets, cleanups, rebases, destructive Git | **Not done** — only read-only Git commands were run |
| Amend a shared register or protected document | **Not done** — T12–T17 unmodified |
| Invent an owner decision, approval, signature, test result, threshold or gate acceptance | **Not done** |
| Assume current HEAD / branch / worktree | **Not done** — re-derived and reported (§1) |

**Commands executed, in full:** `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git status --porcelain | wc -l`, `git rev-list --left-right --count HEAD...origin/feat/sabiroute-routing-foundation`, `git status --porcelain --untracked-files=all`, `git status --porcelain --untracked-files=no`, `git ls-files docs`, `ls -1 docs`, and four `grep` reads against T16. **All read-only. Nothing was written by any of them.**

---

## 9. Final status

| Field | Value |
|---|---|
| **Baseline** | **Re-derived** — `feat/sabiroute-routing-foundation` @ `319a711`, ahead 6 / behind 3 |
| **Tracked modifications** | **0** |
| **R6 documents tracked in Git** | **0 of the entire corpus** |
| **Decision package** | Complete and canonical — **23 decisions, 0 registered** |
| **Owner-selected** | **1** (A3 Option A, conditional, P1–P5 unmet) — **unregistered** |
| **Identifier collisions** | **5** (CLOSE-FINAL-01 records 4) |
| **Unresolvable identifiers** | **`Q3`, `Q5`, `G16`, `G17`** — external, unmapped (§3.1) |
| **R6.0 closure** | **~29% — unchanged** |
| **R6.0** | **CONDITIONALLY READY — not closed, not frozen, not signed** |
| **`R6/G7`** | **NOT GRANTED** |
| **Track A / Terminals B–E** | **`NOT OBTAINED`** |
| **Verdict** | **NO-GO** |
| **Next action** | **Belongs to CHEF_P** — settle `C-02`, record `ADR-2/C-1`, register A3 then B1; and decide whether to commit the corpus before signing |

**This annex adds evidence and removes a limitation. It does not move the gate.**

---

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
