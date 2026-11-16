# R6.0 — G-07 Independent Closure Readiness Review

**Terminal:** G — Independent reviewer
**Prompt:** G-07 — Cross-report evidence and dependency verification
**Review date:** 2026-11-05T01:33Z
**Artefact version reviewed:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
**Working-tree state at review:** 0 tracked modifications; 17 untracked files under `docs/`
**Status:** READ ONLY. No file modified, no test executed, no commit, no push, no approval, no gate change.

---

## 1. Mission and method

Independently challenge the combined R6.0 report set. Ten checks were assigned. Each is classified below as **VERIFIED**, **VERIFIED WITH CONDITIONS**, **NOT VERIFIED**, **CONTRADICTED**, or **OWNER DECISION REQUIRED**.

**Corpus read (all at `319a711`):**

| Document | Role in this review |
|---|---|
| `docs/r6-t16-r6-decision-option-register.md` (39.7 KB) | Canonical 23-card register; A/B/D statuses |
| `docs/r6-owner-decision-supplement-2026-11-04.md` (35.9 KB) | Decision-session record; C-02 Reading B; D-register collision analysis; items 8.1–8.8 |
| `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` (80.7 KB) | Gate table §19; conditions §19.1; 25 owner actions §20; U0 §14.6 |
| `docs/r6-t14-independent-t13-audit-and-decision-readiness.md` (33.7 KB) | Independent audit of T13; AF findings |
| `docs/r6-t15-r6-owner-decision-brief.md` (25.7 KB) | Decision brief; C-07 annotation requirement |
| `docs/r6-t12-accounting-integrity-and-gate-closure.md` (88.6 KB) | Invariants §12; Track A matrix §16; lanes §17; G7 §18 |
| `docs/r6-c01-settlement-integrity-and-remediation-dependency-report.md` (21.2 KB) | F1–F5; dependency graph §7; sequence §10 |
| `docs/r6-independent-review-r6-settlement-integrity-tests.md` (23.3 KB) | Conditions C1–C5; C-07 divergence §6.3 |
| `docs/r6-architecture-decision-pack.md` | Terminal ownership map §15; four D registers |
| `docs/r6-decision-resolution-and-approval-campaign.md` | Duplicated D register |
| `docs/architecture-decision-record.md` | Green Closure Record D1–D8 |
| `docs/r6-t11-…`, `docs/r6-t10-…`, `docs/r6-t9-…` | Gate conditions, reclassifications, G7 definition |
| `tests/test_r6_settlement_integrity.py` | Test-module header (read only, not executed) |

**Two provenance facts that bound every conclusion below:**

1. **No R6 report is tracked in git.** All thirteen are untracked working-tree files. `git log` is therefore not an evidential channel for any R6 artefact, including the absent ones named in check 8. Absence claims in this review are **filesystem** absence, verified by content search, not repository history.
2. **Nothing in this review is runtime evidence.** No test was run. Where a claim depends on observed behaviour, it is taken from `r6-c01-…` §3 (664 pass / 4 fail / 9 skipped at HEAD) and labelled as inherited, not re-verified.

---

## 2. Verdict summary

| # | Check | Classification |
|---|---|---|
| 1 | No owner approval has been inferred | **VERIFIED WITH CONDITIONS** |
| 2 | All 23 canonical decisions are accounted for | **VERIFIED WITH CONDITIONS** |
| 3 | All 13 A/B decisions have correct evidence classifications | **VERIFIED WITH CONDITIONS** |
| 4 | C/D register collisions are accurately represented | **VERIFIED WITH CONDITIONS** (D verified; C not addressed) |
| 5 | B5, C-07, U0, E-01/E-02 dependencies are technically correct | **VERIFIED WITH CONDITIONS** |
| 6 | C-02 Reading B is correctly applied to BL-22 | **VERIFIED WITH CONDITIONS** |
| 7 | R6.0 and R6.1 conditions are not conflated | **VERIFIED WITH CONDITIONS** |
| 8 | F-05/G-06 discrepancy is honestly resolved or explicitly unresolved | **NOT VERIFIED** |
| 9 | No completed work has been unnecessarily repeated | **VERIFIED WITH CONDITIONS** |
| 10 | Recommended parallel plan respects ownership and governance boundaries | **NOT VERIFIED** |

**Tally:** 8 verified with conditions · 2 not verified · 0 contradicted · 0 owner-decision-required.

**Aggregate.** The report set is unusually disciplined about authority — it repeatedly refuses to convert preparation into approval — but it carries one unresolved provenance defect (check 8), one ownership-boundary defect in its recommended plan (check 10), and a systematic identifier-collision problem that it has itself diagnosed for `D` but not for `C` (check 4). Each finding is a defect in the record, not in the system the record describes.

**This review closes no gate.** R6.0 remains **not closed**, R6.1 remains **not authorised**, G7 remains **not granted**, and no owner decision is inferred, implied or advanced by anything below.

---

## 3. Findings

### 3.1 Check 1 — No owner approval inferred: VERIFIED WITH CONDITIONS

**What holds.** Every one of the 23 canonical cards in T16 carries `Owner response: PENDING` and `Approval record: NOT APPROVED` — including A3 and B1, the two cards selected in the 2026-11-04 session. The supplement is explicit and correct about the limit of what was recorded:

- 13 canonical decisions in scope (Group A + Group B)
- 3 evidenced as selected in session (A3, B1, B6)
- **10 outstanding** (A1, A2, A4, B2–B5, B7–B9)
- **0 canonically registered in T16** — before and after that document

(`r6-owner-decision-supplement-2026-11-04.md` §4.2)

The supplement also declines two upgrades a weaker record would have taken: A3 is held at `MISSION-FRAMED` because no direct owner utterance with its own timestamp exists (§8.2), and Q5 Option C is held at `MISSION-FRAMED` because its approval appears in the third person (§8.8). T13 §19.2 states the discipline in the corpus's own words: *"A prepared decision is not a taken decision. Ready ≠ authorised."*

**Condition 1 (material, live).** An inferred approval persists in code-adjacent prose. `tests/test_r6_settlement_integrity.py:11` states that each test "is written against the **approved** contract", and the module's `E-02` contract line names "Owner decision B5" as its basis. **B5 is `OUTSTANDING` / `NOT APPROVED`**, and its Option B would ratify the current behaviour as correct. This is the independent review's condition **C1**, still `OPEN` at HEAD (`r6-c01-…` §8) after being raised three days earlier. It is a wording defect with real consequences: the test file asserts the authority it is meant to be testing the absence of.

**Condition 2 (structural).** Three decisions exist in two incompatible status channels. The supplement records A3, B1 and B6 as selected; the register records all three as `PENDING` / `NOT APPROVED`; nothing bridges them because Group D has no field for a session record and, per §8.7, **C-02 itself has no register field at all**. A reader consulting either document alone gets a different status for the same decision. Both documents are individually honest; the pair is not self-consistent.

**Verdict.** No owner approval is asserted in any R6 report. One inferred-approval string survives in a test header, and the selection-record path is unmodelled. Both are correctable and neither is an approval.

---

### 3.2 Check 2 — All 23 canonical decisions accounted for: VERIFIED WITH CONDITIONS

**The register is complete at 23.** Heading extraction of `r6-t16-…` returns exactly:

| Group | Cards | Count |
|---|---|---|
| A — architecture | A1, A2, A3, A4 | 4 |
| B — R6.1 rulings | B1 … B9 | 9 |
| C — release/claim scope | C1, C2, C3, C4 | 4 |
| D — implementation authorisation | D1 … D6 | 6 |
| **Total** | | **23** |

Every card is present with question, options, consequences, dependencies, gate impact, evidence status, owner response and approval record. No card is a stub, none is duplicated within T16, and the 23-card set matches T13 §20's items 1–23 one-to-one (1–4 → A1–A4; 5–13 → B1–B9; 14–17 → C1–C4; 18–23 → D1–D6).

**T13 §20 has 25 items, and that is correct.** Items 24 (sign BL-22) and 25 (correct `CLAUDE.md` §12) are explicitly flagged in T13 as *not* Group decisions: item 24 is the signature act and item 25 is a documentation finding. The 23-versus-25 difference is accounted for, not unexplained.

**Condition 1 (arithmetic defect in the brief, not the register).** The G-07 mission brief's own framing of C-02 Reading B uses "12 canonical decisions" and "nine outstanding"; the register enumerates 13 and lists ten outstanding identifiers. The supplement records this as §8.1 `UNRESOLVED` and refuses either to adopt 12 or to silently rewrite it. That refusal is correct — but it means the **brief that authorised this review was arithmetically wrong**, and the discrepancy is still open because it determines the BL-22 discharge count.

**Condition 2 (Group D is one decision set in two places, not two sets).** T16 §6.2 `D1`–`D6` and T13 §10 `D1`–`D6` are the same six decisions. The supplement states this correctly (§7.5 A). They have not been merged; the register's master index is the only thing that identifies them as shared.

**Verdict.** All 23 are accounted for and traceable. The count discrepancies in circulation are documented rather than papered over, which is the correct handling; one of them (12 vs 13) is unresolved in the authorising brief itself.

---

### 3.3 Check 3 — All 13 A/B decisions have correct evidence classifications: VERIFIED WITH CONDITIONS

**What holds.** All 13 A/B cards carry an `Evidence status` field, and the field is honest about what it is: no A/B card claims verified correctness for its own decision. Eleven read *"proposal per T13; unresolved"*, three of them carrying additional load-bearing qualifiers — B5 *"Not implemented"*; B6 and B7 each noting they are the two rulings T11 §18 omitted (X-4); B6 adding that it is load-bearing for ADR-2 and must not be combined with B7. A2 records that its defects are source-inspected while the decision remains unresolved — the correct separation. B1 and A3 are the strongest in the set: both use a three-part **Verified / Proposed / Unresolved** structure (A3: no `sabiroute_optimization_records` table exists at `319a711`; ADR-1 is `PROPOSED`; prerequisites P1–P5 unmet. B1: no `request_transform` package exists; ADR-2 is `PROPOSED`; I2's 250 ms / 2× budget and I5's config schema unspecified).

Crucially, none of the 13 conflates *evidence sufficiency* with *decision taken*: the classification channel and the approval channel are separate fields, and the approval channel is uniformly `PENDING` / `NOT APPROVED`.

**Condition 1 (classification is inconsistent in depth).** The set is not uniform. Two cards (A3, B1) use the full three-part structure; eleven use a single sentence. The consequence is that the two **selected** decisions are the best-evidenced cards while the ten **undecided** ones are the least decomposed — the inverse of where the risk sits. Nothing here is wrong; the classification is simply not uniform enough to be machine-checkable or to support a uniform sufficiency threshold.

**Condition 2 (the A3 card omits its own provenance defect).** A3's `Evidence status` grades the *technical* evidence rigorously but says nothing about the fact that A3's selection has **no direct owner utterance** — a fact the supplement records as §8.2 `UNRESOLVED`. A reader of T16 alone would not learn that A3 is source-limited. The register and the supplement disagree about the strength of A3, and only the supplement says so.

**Condition 3 (no evidence grade for A/B as there is for BL).** T12 §13.2 grades BL items with an explicit taxonomy (`SUF` / `PART` / `ERR` / `CLOSED`, plus reclassification flags). The A/B cards carry no equivalent grade. So "correct evidence classification" is verifiable only as *honest prose*, not as a graded judgement against a stated standard. The standard exists for BL items and was not carried into the canonical register.

**Verdict.** Every A/B classification is defensible and none overstates authority. Uniformity, and A3 provenance disclosure, are the conditions.

---

### 3.4 Check 4 — C/D register collisions accurately represented: VERIFIED WITH CONDITIONS

**D — represented accurately, and independently corroborated.** The supplement §7.5 identifies four D-numbered registers; I confirmed each live at `319a711`:

| Register | Range | Confirmed |
|---|---|---|
| `r6-architecture-decision-pack.md` | `D1`–`D17` | Range confirmed (highest token `D17`). `D1`, `D2`, `D3`, `D16` recorded APPROVED (`:387–389`, `:402`) |
| `r6-decision-resolution-and-approval-campaign.md` | `D1`–`D17` | Range confirmed. **Diverges from the pack** — `D4` `RECOMMENDED` (`:135`) vs `OPEN` (pack `:390`) |
| T13 §10 / T16 §6.2 | `D1`–`D6` | Confirmed — one shared six-decision set, all `OUTSTANDING` |
| `architecture-decision-record.md` | `D1`–`D8` | Confirmed (highest token `D8`); carries its own `DECIDED` / `APPROVED` / `AUTHORIZED` statuses |

The supplement's strongest claim is also its most important: **bare `D1` denotes three materially different decisions** — "Hybrid modular architecture" (pack, APPROVED), "U0 merge/landing policy" (T13/T16, `OUTSTANDING`), and "B3 shared-completion-code ownership" (ADR, `DECIDED`, `owner-self`). I verified all three exist and are as described. `D3` collides identically and is additionally a known composite (T14 AF-15). The supplement's conclusion — collision **UNRESOLVED**, no bare `D` identifier safe in a decision card, a separately authorised register-governance operation required — is accurate and correctly left undecided.

The supplement also corrects a prior Terminal G audit figure in place: §7.5 B records that "Terminal G's audit recorded the campaign register as `D1`–`D16`". Live inspection shows `D17`. My check agrees with the supplement, not the earlier audit.

**Condition 1 (the `C` collision is not represented at all).** §7.5 is a **D-only** analysis, yet the same collision exists for `C` across four distinct families:

| Source | `C-02` means |
|---|---|
| T13 corrections register (`C-01`–`C-07`) | The **defect**: "R6.0 condition 3 vs §8 disagree" (T14 AF-14) |
| `r6-owner-decision-supplement-2026-11-04.md` §4 | **"Reading B"** — the owner's selected reading of condition 3, recorded `EXACT OWNER` |
| T16 §4 (`C1`–`C4`) | A **decision card** family: release/claim scope |
| `r6-independent-review-…-tests.md` §8 (`C1`–`C5`) | The review's five **conditions**, all `OPEN` |

The specific hazard: `C-02` denotes a *defect* in one document and the owner's *selected reading* in another, and the correction list runs to `C-07`. Under the supplement's own standard — "no bare identifier is safe in a decision card" — the `C` namespace fails the same test the `D` namespace fails, and it is not covered.

**Condition 2 (the finding `C-07` sits numerically flush with the condition set).** `C-07` is an accounting-integrity finding (T16 §5 B5 annotation; T15 §5). The independent review's conditions run to `C5`. A reader sorting by identifier merges two unrelated families, and `C-07` is one of the two artefacts B5 depends on.

**Verdict.** The D collision is represented accurately, verified independently, and self-corrected where an earlier audit erred. The C collision — same class, same consequence, one namespace of which directly governs BL-22 and B5 — is absent from the analysis.

---

### 3.5 Check 5 — B5 / C-07 / U0 / E-01 / E-02 dependencies technically correct: VERIFIED WITH CONDITIONS

**B5 → C-07 → both governors: correct.** T16's B5 card records `Dependencies: C-07 (both governors)` and its annotation states the technical basis precisely: the budget governor honours the unknown-usage flag (`completions.py:1944–1955`, `:1961–1972`; `_actual_cost` returns `None` at `:1997–1998`) while the quota governor cannot, because `finish()` has no `usage_unknown` parameter (`:542–550`) and the quota block recomputes `quota_total` from raw parts at `:603`. The card draws the right conclusion — a settlement contract is incomplete when only one governor is repaired — and `r6-c01-…` F3 independently reproduces it from source. B5's `Gate impact: R6.1` and its role as the gating decision for U1 (T13 §8) are consistent across T13, T16 and C-01.

**B6 does not resolve B5: correct, and load-bearing.** The supplement §7.2 refuses the inference explicitly and cites B6's own boundary condition 6 ("does not weaken unknown-usage handling or settlement integrity for either budget or quota") and condition 5 (B6 and B7 independent). Given that B6 *was* selected in-session and B5 was not, this is the single most likely place for an inferred approval to enter the record, and it is closed.

**U0 conditions: correct but stale.** T13 §14.6 reduced U0's remaining conditions from three to **two** — `D1` (merge policy) and `D3` (G7 scope must name `tests/`) — by discharging spec 5's re-derivation in T13 §13. That reduction is technically sound: T13 §13 identifies T12 §19.2's exact misreading (`:1573` is an `elif` on `failure_usage is not None`, so it does not fire for a budgeted request whose failure body carries a usage object) and reaches the opposite conclusion — spec 5 **fails**, to be authored `xfail(strict=True)`. U0 is correctly labelled *ready for separate authorisation, not authorised*.

**E-01 / E-02 mapping: correct, with a split not yet applied.** E-01 ↔ `C-01-F1` (unbound `attempted` read at `:602` before `:1311`; `NameError` swallowed at `:623–:632`, `route_configuration_error` masked as `quota_unavailable`, reservation stranded). E-02 ↔ `C-01-F2` + `C-01-F3`, which C-01 correctly calls **independent defects with a shared symptom**, and which the review correctly asks to be split into `E-02a` (flag never set on the success path) and `E-02b` (quota block ignores the flag at `:603`). The split is specified in `r6-c01-…` §10 step 5 and **not yet applied to the test module**.

**Condition 1 (the U0 condition set is one artefact stale).** C-01 raises a fourth gate on U0 that T13 §14.6 does not know about: the review's **C4**, "add the C-07 divergence scenario" — `OPEN`, because no known-then-unknown cross-governor test exists (`r6-c01-…` §8). Since U0 *is* the test-only deliverable, and since C4's absence means the module cannot be presented as B5/C-07 evidence, U0's condition set is at least three: `D1`, `D3`, and C4 completion. T13's "two" was correct on its date and is now understated.

**Condition 2 (one decision, three names).** U0's `D1` is called **"merge policy"** in T13 §14.6 and §20 item 18, **"U0 merge policy"** in the supplement §7.5 C, and **"Landing policy for failing tests"** in `r6-c01-…` §7 and T16 §6.2. Same decision, three labels. Combined with the unresolvable bare `D1` (check 4), this is the namespace problem arriving inside the U0 dependency chain.

**Condition 3 (no runtime proof of the dependency claim).** The dependency structure is verified by source inspection and by inherited runtime evidence (4 failing tests, `r6-c01-…` §3). No test was executed for this review, and the C-07 divergence — the claim B5 rests on — has no test at all (C4 `OPEN`).

**Verdict.** Every stated dependency is technically correct at HEAD. The U0 condition count is understated by one artefact-behind state, and the C-07 dependency is asserted by inspection rather than proven by test — which the corpus itself already records as an open condition.

---

### 3.6 Check 6 — C-02 Reading B correctly applied to BL-22: VERIFIED WITH CONDITIONS

**The selection is well-sourced.** Supplement §4 records, verbatim, *"C-02: Reading B — Group A plus all of Group B (B1–B9) must be recorded before BL-22 is signed"* at line 2716, `ts=2026-11-04T16:25:06.624Z`, classed `EXACT OWNER` — the same owner submission as B1. Reading B is defined in T16 (`:456`/`:458`): Reading A narrows condition 3 to "Group A and B1"; Reading B treats B2–B9 as R6.0-adjacent and requires the whole Group B before signature. T15 does not choose between them; the owner did. Applying the owner's reading rather than the report's preference is exactly right.

**The application is substantive, not formal.** §4.2 does not merely restate Reading B; it computes the discharge position (13 in scope, 3 selected, 10 outstanding, 0 registered) and draws the correct consequence: *"Recording these three does not satisfy BL-22, and does not narrow the BL-22 requirement to the remaining ten."* That sentence is the point — Reading B could have been used to shrink the signature precondition, and the record explicitly refuses to use it that way. §7.1 repeats the ten-identifier list, so the requirement is not reducible by reading the summary alone.

**Condition 1 (the arithmetic this reading must produce is unresolved).** §4.3 and §8.1 record that the authorising brief says 12 decisions / nine outstanding while the register says 13 / ten. Reading B's discharge count is therefore formally open. The supplement's handling is defensible — adopt 13/10, flag the brief's 12 as a miscount, do not silently rewrite the governance record — but BL-22's discharge precondition currently rests on a count no artefact has authority to settle.

**Condition 2 (the reading cannot be canonically registered).** §8.7: C-02 is a governance reading, not an A/B decision card, so "canonical registration" has no mechanism for it. The owner has made a binding selection that has nowhere to live in the register. This is not a documentation nicety: check 1's Condition 2 (two status channels) is the same defect seen from the other side.

**Condition 3 (the source text still offers both readings).** T13 §19.1 condition 3 still reads "Record Group A + Group B decisions, then sign BL-22"; T13 §20 item 24 still stands as the signature act; T16 §547 still presents `C-02` as an open choice ("Reading A or Reading B"). Neither has been amended against the owner's chosen reading. The *application* is correct; the *artefacts* still read as if the choice were open.

**Verdict.** Reading B is correctly identified, correctly attributed, and correctly applied — including the part that costs the owner more work. Its discharge arithmetic, its registration path, and the source texts it governs all remain open.

---

### 3.7 Check 7 — R6.0 and R6.1 conditions not conflated: VERIFIED WITH CONDITIONS

**The gate table separates them cleanly.** T13 §19 distinguishes six gate states in one place: R6.0 **CONDITIONALLY READY**; R6.1 **NOT READY**; U0 **READY FOR SEPARATE OWNER AUTHORIZATION**; U1 **NOT READY**; G7 **NOT GRANTED**; Track A **NOT OBTAINED**. §19.1 states R6.0's three remaining conditions; §19.2 states four explicit non-conclusions. The supplement reinforces the separation from the other direction: §7.2 keeps **settlement remediation blocked** (an R6.1 binding constraint) while R6.0 freeze questions are being prepared, and §7.4 preserves the Terminal C block unchanged.

**The blocking-column discipline is correct.** T13 §8 marks only **B1** as blocking "R6.0, R6.1"; B2–B9 block R6.1; B9 additionally blocks Release. T16's B1 card carries `Gate impact: R6.0 and R6.1`; B5 carries `R6.1`; A1–A4 carry R6.0. Measured across all 23 cards, the gate labels are consistent with the tables.

**Condition 1 (the conflation risk is correctly diagnosed, correctly left open — and it is the same defect as C-02).** T13 §19.1 condition 3 says "Record **Group A + Group B** decisions", which sweeps B2–B9 into R6.0 and contradicts §8's table. T14 recorded this as **AF-14**; the correction register recorded it as **C-02**; the supplement resolves the *reading* question by owner selection (Reading B) but leaves the *wording* question open. Under Reading B the sweep is **intentional** (B2–B9 recorded before signature as R6.0-adjacent); under Reading A it is a defect. The reports handle this honestly, but the underlying inconsistency — a condition sentence that does not match the blocking table — remains in the source.

**Condition 2 (one place where the distinction is only implied).** T13 §19.3 keeps condition 17 (rollout) at **SPECIFIED, UNBUILT** and states it does not block architecture approval — correct. But T12 §17 marks all four external lanes "No" for R6.0 (they are release gates), while T13 §15 assigns Terminal B an explicit R6.0 role in the ownership map. A reader who saw only T12 §17 could infer that no external review conditions R6.0 at all. That inconsistency is pursued under check 10.

**Verdict.** R6.0 and R6.1 are distinguished consistently in every gate table, blocking column and card examined. The one genuine conflation — condition 3's scope sentence — is diagnosed, attributed and left for the owner, which is the correct disposition.

---

### 3.8 Check 8 — F-05 / G-06 discrepancy honestly resolved or explicitly unresolved: NOT VERIFIED

This is the review's strongest negative finding, and it is a provenance finding rather than a technical one.

**What was searched.** Content search across the entire working tree (all file types, including `media-library/`, `src/`, `tests/`, `docs/`, `config/`, `migrations/`, `monitoring/`, `scripts/`, `reports/`, `sprint13-429-drill/`, `web/`, `artifacts/`), plus `git log --all -S` for both strings.

**Result — `G-06`:**

- **Zero occurrences of the string `G-06` in any file in the working tree.** The only lexical matches for `G-06`-like tokens are unrelated media asset IDs (`MOTION-LOADING-PROCESSING-06` in the media-library manifest).
- **Zero commits in repository history ever introduced or removed the string** (`git log --all -S "G-06"` returns nothing).
- No `G-0x` document exists in `docs/`. The R6 series in the tree is T9–T16, C-01 and one independent review; there is no Terminal G acceptance artefact.
- The **only** surviving trace of G-06 anywhere is its *effect*: the supplement's amendment note records that it was amended "under owner authorisation — Terminal G audit Conditions 1 and 2 applied only. Condition 1 reclassifies the Q5 source … from `EXACT OWNER` to `MISSION-FRAMED`. Condition 2 corrects the D-register analysis (§7.5)." Conditions 3 and 4 "were **explicitly excluded** and remain unapplied."

**Result — `F-05`:** there is no `F-05` finding in the R6 corpus. Two candidate referents exist, both belonging to other eras:

1. **Batch 2, `F-05 body/message limits`** — committed in `d5a6268` ("Batch 2: F-04 docs policy, F-05 body/message limits, F-06 credential validation…"). `docs/compression-discovery-packet.md:11` records this lineage and states that the "Batch 2 line carries F-04/F-05 absent locally". This F-05 concerns request body and message-size limits. It has no technical relationship to settlement integrity, Terminal G, or R6.0 closure.
2. **`C-01-F5`** — "the documented accounting `ledger` is write-only" (`r6-c01-…` §5), created **after** the G-07 brief (report mtime 01:52Z versus brief 01:08Z). Also unrelated to Terminal G acceptance.

Neither is a finding a Terminal G audit would have adjudicated.

**Conclusion.** The F-05/G-06 discrepancy is **neither resolved nor explicitly recorded as unresolved in any artefact.** No document in the corpus mentions either identifier in connection with the other; no artefact states that the discrepancy exists, what it concerned, or that it remains open. The G-07 brief asks this review to verify an honest resolution; the honest answer is that the record contains none.

**Why the gap is material rather than cosmetic.** The only fragment of G-06 available — via the supplement's two applied conditions — contains a **demonstrable factual error**: §7.5 B records that "Terminal G's audit recorded the campaign register as `D1`–`D16`", while live inspection shows `D1`–`D17`. The supplement catches and corrects it, which is good practice by the supplement; but it also means the G-06 acceptance cannot be relied on as a correctness assurance for the D-register analysis it is cited against. An audit whose single surviving data point is wrong is not a closed loop.

**Classified: NOT VERIFIED.** Recorded as unresolved issue **G07-U1** (§5).

---

### 3.9 Check 9 — No completed work unnecessarily repeated: VERIFIED WITH CONDITIONS

**What holds.** Comparing the artefact set against every recommended plan in the corpus:

- T13 §20's recommended session order (A3, B1 → A1, A2, A4 → B2–B9 → C → D) does not re-commission T10–T12; it consumes them.
- T15 does not re-issue T13's analysis; it compresses it into decision briefs.
- T16 does not re-audit; it converts T13's proposals into 23 cards with status fields, and explicitly declines to rewrite or adopt the ADRs it references ("T16 neither rewrites nor adopts ADR-1").
- T14 audits T13 independently rather than restating it, and says so where it disagrees (AF-05, AF-14, AF-15) — the opposite of duplicated work.
- `r6-c01-…` re-runs the test suite (§3) to obtain **runtime** evidence no prior artefact had. New evidence, not repetition.
- The independent review re-derives C-07 from source and refuses the test module's own framing — again new work.

No document re-executes a completed analysis for the sake of form, and no artefact is written twice under two names.

**Condition 1 (restated work is legitimately restated, but should be labelled).** `r6-c01-…` §8 re-checks the review's five conditions at HEAD and reports all five still `OPEN`. This is a **re-verification**, and its value depends entirely on being performed at HEAD rather than copied forward — which it is (each row carries `VERIFIED BY INSPECTION` or `VERIFIED BY RUNTIME`). Fine as executed; the corpus would be stronger if re-verification were marked as such, since it is otherwise indistinguishable from inherited text.

**Condition 2 (one genuine near-duplication in the D space).** `r6-decision-resolution-and-approval-campaign.md` is a **duplicated campaign register over the same subjects** as `r6-architecture-decision-pack.md`, both running `D1`–`D17`, and they **already diverge** (`D4` `RECOMMENDED` at campaign `:135` vs `OPEN` at pack `:390`). This is not repeated *work* in the sense the check asks about — nobody re-derived anything — but it is a second live source of the same decisions with a different answer, and it is the mechanism by which check 4's collision became consequential.

**Condition 3 (a plan step that proposes work inside an unauthorised write boundary).** `r6-c01-…` §10 steps 3–6 propose edits to `tests/test_r6_settlement_integrity.py` (header correction C1/C3, C-07 test C4, E-02 split, C5 repair-shape record). `tests/` is not inside any authorised write boundary: T12 §16 and T13 §14.6 both state that **G7 must name `tests/` explicitly or U0 has no authorisation basis at all**, and that is `D3` — `OUTSTANDING`. Steps 3–6 are therefore work recommended ahead of the authority that would permit it. Pursued under check 10.

**Verdict.** No completed analytical work is repeated. The plan does, however, sequence new work under `tests/` before the decision (`D3`) that would authorise writing there.

---

### 3.10 Check 10 — Recommended parallel plan respects ownership and governance boundaries: NOT VERIFIED

Three distinct defects, each independently sufficient.

**Defect 1 — Terminal B is assigned work outside its mandate.**

The ownership map (`r6-architecture-decision-pack.md:485`) gives Terminal roles as:

| Terminal | Mandate | Participates in |
|---|---|---|
| A | Implementation and R6 coordination | R6.0–R6.7 |
| B | Architecture review | **R6.0, R6.4, R6.5** |
| C | Security, reliability, lifecycle | **R6.0, R6.1, R6.4, R6.7** |
| D | Synthetic benchmark and testing | R6.6 |
| E | Independent red-team | R6.0, R6.5, R6.7 |

Settlement integrity is **R6.1's binding constraint** — stated in T13 §19 ("accounting correctness is the binding constraint"), in T16's B5 card (`Gate impact: R6.1`), and in `r6-c01-…` §13 ("CURRENT GATE: R6.1 — settlement integrity"). Terminal **C** participates in R6.1. Terminal **B** does not.

Yet the Terminal B packet (T13 §15) asks B to adjudicate: *"Are the settlement and accounting invariants in T12 §12 (I1–I9 and the unknown-wins contract) implemented such that no request can be settled at a partial sum when any attempt's usage is unknown, and is the claimed attack surface complete?"* That is the R6.1 settlement question, addressed to the one review terminal whose mandate excludes R6.1. Meanwhile the supplement §7.4 preserves "the existing Terminal C block" — so C holds the R6.1 block and is not the terminal being asked.

This is not a labelling slip. Under the pack's own conflict controls — control 1 ("one terminal owns a file group at a time") and control 4 ("a red-team finding reopens the owning decision") — a B finding on settlement would reopen a decision in C's lane and in Track A's protected surface, with no rule saying who owns the result.

**Defect 2 — The proposed plan writes to `tests/` before `D3`.**

Covered in check 9 Condition 3; stated as an ownership defect here. `r6-c01-…` §10 steps 3–6 edit a file under `tests/`. T12 §16 states the boundary problem precisely: *"U0 is test-only and touches `tests/` only — no Track A file. But T7 covers the settlement defects U0 is designed to prove, so U0's scope belongs to a T7 conversation even though its diff does not. G7 must therefore name `tests/` explicitly, or U0 has no authorisation basis at all."* `D3` is `OUTSTANDING`. The plan sequences the work and not the authorisation.

**Defect 3 — The remediation step omits the Track A gate.**

`r6-c01-…` §10 step 7 reads: *"Then remediate, in the review's order: F3/C-07 → F2 → F1, each behind `CLAUDE.md` §5."* F3 and F2 are in `api/completions.py`; F1 spans `completions.py` and `security/store.py`. Those are **Track A-protected files** (pack §15 conflict control 3; T12 §16 protected surface), and R6 changes there **require Track A sign-off (`D17`)**, which is `NOT OBTAINED`. The plan names `CLAUDE.md` §5 (the architectural-change gate) and does not name Track A. Steps 1–2 are correctly marked "owner decisions and are not delegable to an implementer"; step 7 — the one that touches protected source — carries no equivalent marker and no blocked-by.

**What does respect the boundaries, and should be preserved.** The good behaviours are worth naming because they are what to keep: (a) `r6-c01-…` created exactly one file and modified nothing (`src/**`, `tests/**` untouched — §12); (b) T13 §19.2 refuses to convert readiness into authority; (c) the supplement refuses four separate inferences — B5 from B6, approval from preparation, Q5 from third-person assertion, A3 from mission framing; (d) the mission discipline that a review report cannot request G7 (T12 §18; `r6-t9:417`; campaign `:332`); (e) every status label is `NOT OBTAINED` / `NOT APPROVED` rather than blank, so silence is never read as assent.

**Verdict.** The corpus's *status* discipline is exemplary; its recommended *plan* has three boundary defects: a cross-mandate review assignment (Terminal B on R6.1 settlement), work sequenced ahead of its write authority (`tests/` before `D3`), and a protected-surface remediation step missing its Track A gate. None invalidates the analysis; all three would need resolving before any recommended work is executed.

---

## 4. New findings raised by this review

| ID | Finding | Class |
|---|---|---|
| **G07-F1** | `tests/test_r6_settlement_integrity.py:11` still asserts tests are "written against the approved contract" while B5 is `NOT APPROVED` (review C1 `OPEN`). | Documentation / authority defect |
| **G07-F2** | No G-06 acceptance artefact exists anywhere in the working tree or repository history, and no F-05 finding exists in the R6 corpus; the only surviving trace of G-06 is its two applied conditions, one of which contains a factual error (`D1`–`D16` vs live `D1`–`D17`). Collapsed to §5 as G07-U1. | Provenance defect |
| **G07-F3** | The `C` identifier namespace collides across four families (T16 `C1`–`C4`; T13 corrections `C-01`–`C-07`; the supplement's `C-02` "Reading B"; the independent review's conditions `C1`–`C5`). `C-02` denotes both a defect and the owner's selected reading. The supplement diagnoses this only for `D`. | Register defect |
| **G07-F4** | Terminal B's packet (T13 §15) asks B to adjudicate R6.1 settlement invariants; the ownership map (`pack:485`) excludes B from R6.1 and assigns R6.1 to Terminal C. | Ownership defect |
| **G07-F5** | `r6-c01-…` §10 steps 3–6 propose edits under `tests/` before `D3` places `tests/` inside an authorised write boundary. | Governance defect |
| **G07-F6** | `r6-c01-…` §10 step 7 proposes remediation in Track A-protected files (`completions.py`, `store.py`) without naming the Track A sign-off gate (`D17`, `NOT OBTAINED`) that T12 §16 and pack §15 require. | Governance defect |
| **G07-F7** | U0's condition set is understated by one: T13 §14.6 states two (`D1`, `D3`), while the review's `C4` (no C-07 divergence test) is `OPEN` and materially conditions U0's evidentiary value as the B5/C-07 proof. | Stale dependency record |
| **G07-F8** | Three decisions (A3, B1, B6) exist in two status channels — recorded as selected in the supplement, `PENDING` / `NOT APPROVED` in T16 — with no field bridging them; and C-02 has no register field at all (§8.7). | Register defect |
| **G07-F9** | No A/B decision card carries a graded evidence classification equivalent to T12 §13.2's `SUF` / `PART` / `ERR` taxonomy for BL items; "correct classification" is verifiable only as prose. | Documentation defect |

None of these findings modifies, blocks or advances any gate on its own authority. Each is an owner-visible defect in the record, not a defect in the system the record describes.

---

## 5. Explicit unresolved register

| ID | Unresolved question | Status | Owner-visible before |
|---|---|---|---|
| **G07-U1** | What did the F-05/G-06 discrepancy concern, and was it resolved? Neither artefact exists in the tree; no document records either identifier in relation to the other; both belong to the same Terminal G line of work. | **UNRESOLVED** — not reconstructable from available evidence | Any reliance on the G-06 acceptance |
| **G07-U2** | Is the BL-22 discharge count 12 (brief) or 13 (register), and therefore nine or ten outstanding? Inherited as supplement §8.1. | **UNRESOLVED** | BL-22 signature |
| **G07-U3** | Where is C-02 Reading B recorded, given no register field exists? Inherited as §8.7. | **OPEN** | BL-22 signature |
| **G07-U4** | Which terminal owns settlement review, given Terminal B's packet and the ownership map disagree? | **UNRESOLVED** — raised by G07-F4 | Terminal B packet issue |
| **G07-U5** | Is the D-register collision to be resolved by a separately authorised register-governance operation, and does that operation also cover `C`? Inherited as §7.5 C plus G07-F3. | **UNRESOLVED** | Further decision cards using bare `C` / `D` identifiers |
| **G07-U6** | Has A3's selection been independently re-confirmed by the owner? Inherited as §8.2. | **UNRESOLVED** | A3 canonical registration |
| **G07-U7** | Has Q5 Option C's approval been confirmed by a direct owner utterance? Inherited as §8.8. | **UNRESOLVED** | B6 measurement implementation |

---

## 6. What this review does not do

- It does **not** declare R6.0 closed. R6.0 remains **CONDITIONALLY READY** at best, and two of its checks are unmet.
- It does **not** authorise R6.1. R6.1 remains **NOT READY**; settlement integrity remains **BLOCKED**.
- It does **not** request, infer or record G7. G7 remains **NOT GRANTED** and cannot be requested by a review report (T12 §18; `r6-t9:417`; campaign `:332`).
- It does **not** approve any decision card. All 23 remain `PENDING` / `NOT APPROVED`; the 10 outstanding A/B decisions remain outstanding.
- It does **not** adopt, amend, correct or renumber any register, ADR, gate or condition — including the collisions it reports, which it reports precisely so that it does not fix them by inference.
- It does **not** execute tests. All runtime statements are inherited from `r6-c01-…` §3 and labelled as such.
- It does **not** modify any file. This report is the only file created; nothing is staged, committed, pushed or reformatted.

---

## 7. Recommended next owner actions (recommendation only — not a decision)

Ordered by whether the item gates a gate or merely gates a document.

1. **Owner, before BL-22:** settle the 12/13 arithmetic (G07-U2) and define where a governance reading is recorded (G07-U3). Both are pre-conditions to reading the signature's scope unambiguously.
2. **Owner, before any further decision card:** authorise register governance for the `D` **and** `C` namespaces (G07-F3, G07-U5). The collision is already consequential; every further card using a bare identifier adds to it.
3. **Owner, before the Terminal B packet is issued:** resolve which terminal owns settlement review (G07-F4, G07-U4). Issuing B a C-lane question creates an unowned finding.
4. **Implementer, no decision needed:** correct the test-module header (G07-F1) — the word "approved" and the three-to-four failing-set count. Wording only, but it asserts an approval that does not exist and should not survive another session.
5. **Owner, when sequencing U0:** treat C4 (C-07 divergence test) as part of U0's condition set (G07-F7), and land `D3` before any `tests/` edit is proposed (G07-F5).
6. **Owner, when remediation is scheduled:** attach the Track A sign-off gate (`D17`) to the remediation step (G07-F6), since the settlement fix touches Track A-protected files.
7. **Record, without needing to resolve:** file G07-U1 as an explicit open item. The G-06 acceptance cannot be reconstructed; saying so permanently is better than a silent gap a later reader might fill with an assumption.

---

## 8. Review status

```
REVIEW:        G-07 — Independent R6.0 closure readiness review
TARGET:        feat/sabiroute-routing-foundation @ 319a711e…
MODE:          READ ONLY — 0 files modified, 0 tests run, 0 commits
CHECKS:        10 assigned
               8 VERIFIED WITH CONDITIONS  (1, 2, 3, 4, 5, 6, 7, 9)
               2 NOT VERIFIED             (8, 10)
               0 CONTRADICTED
               0 OWNER DECISION REQUIRED  (all findings are record defects)
NEW FINDINGS:  G07-F1 … G07-F9
NEW UNKNOWNS:  G07-U1 … G07-U7
GATES:         R6.0 NOT CLOSED · R6.1 NOT AUTHORISED · G7 NOT GRANTED
               No approval inferred. No gate changed.
```
