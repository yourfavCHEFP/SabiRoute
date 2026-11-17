# R6 SCORECARD — SabiRoute R6.0 Closure

**Living document.** Update in place as work advances; do not rewrite history — supersede with dated rows.
**Created:** 2026-11-16 · **Aligned to:** WP-4 independent audit date
**Branch:** `sec/deps-nov` @ `1e69ada9` · **Status:** **R6.0 OPEN**

> **Why this file lives here.** It is deliberately *not* `docs/r6-*.md`. The manifest/inventory scope was
> reconciled by WP-3 at exactly **42** documents; adding a 43rd there would re-open a closed question.
> `artifacts/r6-closure/` is outside both the 42-doc inventory and the 13-entry manifest scope.

---

## Status vocabulary (from Build Map §0.1)

These are **not** interchangeable. A row may be *selected* without being *approved*, *implemented* without
being *tested*, and *tested* without being *independently verified*.

| Term | Meaning |
|---|---|
| **Selected** | Owner chose an option |
| **Approved** | Owner explicitly authorised a decision or action |
| **Implemented** | Code or documentation was changed |
| **Tested** | A check actually ran |
| **Independently verified** | A different authorised actor reviewed the evidence |
| **Gate accepted** | Owner explicitly accepted the exit gate |

## Evidence grades used below

| Grade | Meaning |
|---|---|
| `[M]` | **Measured** — re-derived from live bytes in this session |
| `[R]` | **Reported** — asserted by an actor's record; not re-derived by me |
| `[O]` | **Owner** — owner disposition, recorded in a dated entry |
| `[I]` | **Inferred** — my reading, not a measurement |
| `[?]` | **Unverified** — no evidence located |

---

# 1. CLOSURE WORK PACKAGES — WP-0 … WP-5

| WP | Title | State | Evidence | Exit gate | Verdict |
|---|---|---|---|---|---|
| **WP-0** | Live baseline | **DONE** | `wp0-wp1-evidence-2026-11-09.md` §1; re-measured 2026-11-16 §8 `[R]` | Reproducible baseline; no destructive action; untracked work preserved | **MET** |
| **WP-1** | Phase 1 verification + U2 vector refresh | **DONE** | `wp0-wp1-evidence` §2, §7.3 `[R]` `[O]` | Copilot report exists; digest independently measured; only ADDENDUM vector changed; focused tests pass | **MET — owner-accepted** |
| **WP-2** | Phase 2 protocol/schema reconciliation | **RECORD COMPLETE · GATE NOT MET** | `WP2_Owner_Decision_Record_Part_1..4.txt` `[R]` | Protocol/addendum internally consistent; fields trace to approved decisions; registration-locus blocker explicit; no ledger created | **PARTIAL** |
| **WP-3** | Phase 3 manifest + historical corrections | **DONE** | `wp3-manifest-reconciliation-2026-11-16.md` §1–§6 `[R]` | Manifest scope reconciles; every required digest reproducible; historical reports distinguish old from new | **MET, with 9 open items (§4)** |
| **WP-4** | Phase 4 independent verification | **DONE — report delivered** | Copilot WP-4 report, 2026-11-16 `[R]` | Complete independent report; blocking discrepancies resolved **or explicitly presented to owner**; no closure claim before owner acceptance | **ACT COMPLETE · FINDINGS UNRESOLVED** |
| **WP-5** | Owner closure decision | **DONE — OWNER ACCEPTED 2026-11-17** | Owner Row A, `R6.1-FOUNDATION-CONTRACT.md` §10 | Explicit owner acceptance | **MET — owner-accepted** |

## 1.1 WP-by-WP detail

**WP-0 — Live baseline · DONE**
- Branch `sec/deps-nov`, HEAD `1e69ada9`. Nothing staged, nothing committed `[R]`.
- Superseded baseline note: the build map's §1.1 (0 tracked modifications) is **historical**; live state carries
  **1 unstaged tracked modification** (`REPORTS-PROVENANCE.md`, insertions only) `[R]`.

**WP-1 — Phase 1 · DONE, owner-accepted**
- **Recorded honestly:** Copilot's independent result on 2026-11-11 was **WP-1 EXIT BLOCKED**, because the complete
  pre-refresh fixture was unavailable for direct byte comparison. The owner then accepted **WP-1 EXIT PASS** on
  2026-11-11 based on the recovered historical fixture. Both facts stand; neither is rewritten `[R]` `[O]`.
- U2 ADDENDUM vector refreshed to current bytes; focused tests passed `[R]`.

**WP-2 — Phase 2 · RECORD COMPLETE, GATE NOT MET**
- The four-part decision record is complete as a record. That is **not** the same as the exit gate.
- Exit gate requires *"protocol/addendum internally consistent"*. It is **not**:
  - Addendum §12 cites protocol anchors that no longer resolve — `:337` now blank, `§8:171–185` /
    `:208–214` / `:130–135` / `:212–214` / `:325` all stale; current §8 is `:207–221`, §12 is `:265–284`,
    §13 is `:286–302` `[R]`.
  - `docs/r6-registration-protocol-03b-r1.md:213` still reads `VER:v1` record — **recorded, outside the
    authorised E3 anchor** `[R]`.
- **Persisting blocker:** registration locus for **O1–O5 is undefined**. Must be resolved before any REG act.
  Not chosen, not inferred, correctly left open.

**WP-3 — Phase 3 · DONE**
- `REPORTS-MANIFEST.sha256`: **13 entries**, all 13 verify `OK` `[R]`.
- `REPORTS-PROVENANCE.md`: corrected by dated entry (the file's claim that the attestation triple is untracked
  was **wrong**; all three are tracked — corrected in §7.1 of that report) `[R]`.
- `docs/r6-*.md` inventory: **42** documents `[M]`.
- Untracked drift 146 → 147 → 149: **PRESERVED, NOT EXPLAINED** — no 147-entry snapshot exists, so a set-difference
  is impossible. Not closed by assumption `[R]`.
- `r6-close-final-08`: **NOT CREATED** — forbidden by that brief's §7.2.

**WP-4 — Phase 4 · ACT COMPLETE, FINDINGS OPEN**
- Reproduced: 3/3 U2 vectors `[R]`; 13/13 manifest `[R]`; conformance **104 passed / 1 skipped** `[R]`;
  settlement **6 passed** `[R]`.
- **Two FAIL findings** (see §4, F-05 and F-06): Parts 1–3 stale claims; stale line anchors across Part 2 and
  addendum §12.
- Part 4 changed **during** the audit (16,448 B → 18,710 B) — classified *unsettled, not wrong*. Correct call;
  it was a writer/reader race, not a defect `[R]`.

**WP-5 — Owner closure · DONE — OWNER ACCEPTED 2026-11-17**
- Closed by Owner Row A (`R6.1-FOUNDATION-CONTRACT.md` §10), not by another audit.
- Basis: **F-05 / F-06** corrected, **BL-22** signed, **G7** granted.
- F-02 remains accepted-unproven; the registration ledger is never instantiated and the `:570`
  conformance skip remains skipped. Closing WP-5 does not resolve F-02.

---

# 2. IMPLEMENTATION SEQUENCE — R6.1 … R6.7

**All rows: NOT AUTHORISED.** Build Map §4.2 lists *"Authority to implement R6.1–R6.7"* as an owner-only decision
still outstanding. Nothing below may start until WP-5 closes and the owner grants authority.

| ID | Phase | Purpose | Prereq | State |
|---|---|---|---|---|
| **R6.1** | Foundation | Immutable original request, canonical representation, metadata, policy/capability checks, explicit bypass | WP-5 + authority grant | **NOT AUTHORISED** |
| **R6.2** | State optimisation | RTK-style state optimisation | R6.1 | **NOT AUTHORISED** |
| **R6.3** | Simplification | Caveman simplification | R6.2 | **NOT AUTHORISED** |
| **R6.4** | Scorer / select-and-drop | SabiRoute-owned vendored BM25 scorer | R6.3 | **NOT AUTHORISED** |
| **R6.5** | Orchestration | Pipeline orchestration | R6.4 | **NOT AUTHORISED** |
| **R6.6** | Validation | Synthetic benchmark + adversarial validation. **Exit requires both mechanical (B1) and semantic (B2) gates; routing invariance mandatory** | R6.5 | **NOT AUTHORISED** |
| **R6.7** | Rollout | Observability and rollout | R6.6 | **NOT AUTHORISED** |

## 2.1 Frozen constraints that bind R6.1–R6.7

Settled and **not** reopened without new evidence (Build Map §2.2, §4.1):

1. Preserve the immutable original request. 2. Canonical representation and metadata explicit.
3. Policy/capability checks **precede** transformation. 4. Explicit bypass preserved.
5. Compression separate from routing policy. 6. Transform **once** before the provider-attempt loop, never per retry.
7. Original reservation estimate preserved. 8. **Never silently re-baseline** reservations.
9. Unknown usage uses the **full original estimate** for budget and quota. 10. No prompt text logging or persistence.
11. No provider-specific prompt mutation without explicit policy. 12. **Do not adopt `litellm.compress()`** without
source-level inspection of installed LiteLLM and its dependencies. 13. Seven-mode vocabulary is discovery terminology
only. 14. No production/customer-readiness claims without evidence.

**Settled decisions carried forward:** A3 Option A (ADR-1 conditional target, not implemented) · B1 Option A + C-1
(ADR-2 as *draft* R6.1 foundation contract, draft only) · B6 Option A (monotone-shrink) · B5 Option A (unknown usage
wins at full original estimate) · Seven-mode Option B · Q2 Option A (internal developer gateway) · Q3 Option B
(mechanical + semantic both block R6.6 exit) · Q5 Option C (dual measurement) · O1–O8 and D1–D7 as recorded ·
C-02 Reading B (13 total / 10 outstanding).

---

# 3. OWNER-ONLY DECISIONS OUTSTANDING

Do not infer or manufacture any of these (Build Map §4.2).

| # | Decision | State | Blocks |
|---:|---|---|---|
| D-1 | Formal approvals for **T16 cards** | **OUTSTANDING** | WP-5 |
| D-2 | **Registration locus for O1–O5** | **OUTSTANDING** | Any REG act; WP-2 exit |
| D-3 | Resolution of conflicting legacy **budget limits** where relevant | **OUTSTANDING** | R6.1+ |
| D-4 | Exceptions to **privacy/evidence** requirements (P-6) | **OUTSTANDING** | WP-3 exit condition |
| D-5 | **BL-22 signature** | **OUTSTANDING** | R6.0 closure |
| D-6 | **G7 grant** | **OUTSTANDING** | R6.0 closure |
| D-7 | **Authority to implement R6.1–R6.7** | **OUTSTANDING** | §2 above |
| D-8 | Migration / deployment / production / customer-facing claims | **OUTSTANDING** | R6.7 |

---

# 4. OPEN FINDINGS REGISTER

| ID | Finding | Source | Status | Note |
|---|---|---|---|---|
| **F-01** | Registration locus for O1–O5 undefined | Build Map §3 WP-2 | **OPEN — blocking** | Owner decision D-2 |
| **F-02** | 1 skipped test: `test_u11_genesis_entry_hash_is_computable` (conformance `:570`) — *"awaiting authorised ledger instantiation"* | Both actors | **PARTIALLY PROVEN — NOT CLOSED** | PH-3 added a synthetic-fixture proof of the genesis hash (determinism, totality, per-field sensitivity) that instantiates nothing. The live test **stays skipped**; the real genesis hash remains gated on WP-5. |
| **F-03** | `docs/r6-registration-protocol-03b-r1.md:213` still reads `VER:v1` record | WP-3 §7 #4 | **CORRECTED 2026-11-16** | Token is at `:155` and `:248`, not `:213`. Retained by deferral (Part 4 §14.1); protocol §18 records it. **Not retired.** |
| **F-04** | Correction proposal `:885` still reads "NOT OWNER-APPROVED" | WP-3 §7 #5 | **CORRECTED 2026-11-16** | Dated note supersedes `:885` and `:882-883`; the `:3` D12 banner governs. Still **NOT EXECUTED**. |
| **F-05** | **Parts 1–3 carry stale measurements with no supersession note.** Part 1 `:102` protocol `12,619 B / 3a003632…`; `:103` addendum `38,603 B / 69166509…`. Part 2 `:73`/`:220`/`:223`/`:229` "348 lines"; **`:318` "zero occurrences of O5"** — live is **four** | Copilot WP-4 finding 5; re-confirmed `[M]` | **CORRECTED 2026-11-16** | Dated supersession notes appended to Part 1 and Part 2; originals retained verbatim. |
| **F-06** | **Addendum §12 carries stale protocol anchors** (`:337` blank, `§8:171–185`, `:208–214`, `:130–135`, `:212–214`, `:325`); **Part 2 addendum anchors** off by one (E6 `:134–139` → live `:135–140`); `§12.4` heading `:606` not `:605` | Copilot WP-4 finding 6 `[R]` | **CORRECTED 2026-11-16** | 15 anchors re-derived by content across addendum §3/§12.1/§12.2; addendum §13 records old→new. Two §8 citations (`:267`, `:402`) left stale and named. |
| **F-07** | `:223` in Part 4 still asserts zero O5, superseded in place at `:225-239` | Executioner | **ACCEPTED BY DESIGN** | Supersession is the stated convention; not a defect |
| **F-08** | Untracked drift 146 → 147 → 149 | WP-3 §4.3 | **PRESERVED, NOT EXPLAINED** | No 147-entry snapshot exists |
| **F-09** | R6 corpus is untracked — **0 of 42** documents in git | WP-3 §7 #2 | **CLOSED 2026-11-16** | PH-2 (build map §6 row 6, owner-authorised 2026-11-16) staged the 42 documents by explicit path and committed them as `e0530e5`. Re-derived after commit: **42 of 42 tracked**; `REPORTS-MANIFEST.sha256` 13/13 verify. |
| **F-10** | `REPORTS-PROVENANCE.md` A0 item — no separately hashed owner-decision record for R1 | WP-3 §7 #3 | **SEARCHED 2026-11-16 — NOT FOUND** | WO-5. Surface: `grep -rln 'R1' docs/ artifacts/` cross-filtered for `owner.decision.record\|separately hashed`. Only the *statements that it is missing* were found (`REPORTS-PROVENANCE.md:95-96`, this row). **Absence not established** — a failed search is not proof. |
| **F-11** | Copilot did not search the workspace for O6–O8 or ledger artifacts | Copilot limitation | **SEARCHED 2026-11-16 — NOT FOUND** | WO-4. Surface: `grep -rln 'N1-O6\|N1-O7\|N1-O8\|\bO6\b\|\bO7\b\|\bO8\b'` over `*.md`/`*.txt`/`*.json`; `find` for `*ledger*`, `*reg-record*`, `*ver-record*`, `*genesis*`; `find` for filenames containing o6/o7/o8. O6–O8 appear only as *references* in narrative documents. No ledger, REG/VER record or genesis file exists. The only `*ledger*` hit is `r6-command-centre-01-master-ledger-…`, self-described **"COORDINATION DOCUMENT ONLY"**. **Absence not established.** |
| **F-12** | Three-way digest coupling the build map does not account for | WP-1 F-WP1-1 | **RECORDED** | Raised, not resolved |

---

# 5. BASELINE MEASUREMENTS (drift detection)

Re-measure these before claiming any state. `[M]` = re-derived this session.

| Artifact | Bytes | Lines | SHA-256 | Grade |
|---|---:|---:|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52,782 | 633 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` | `[M]` |
| `docs/r6-registration-protocol-03b-r1.md` | 15,898 | 410 | `59643d242effe3bca2a50ae4e52e86d28d9b5105465c446cab87e38fc69a6590` | `[M]` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 42,917 | 710 | `601a27a36e1fc4ed25de0ef45ced6afec67ea61f45a12f12ecf352eaa51c49f5` | `[M]` |
| `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` | 49,995 | 910 | `b3acfcb3481a2adb67f2ac7b346d3c1df0279851571cbcfc8f6d2274cd891414` | `[M]` |
| `artifacts/r6-closure/WP2_Owner_Decision_Record_Part_4.txt` | 18,710 | 258 | `50251c079b6ac2cb6d74e10c5202ff74b78a475e7127276ee9cc24fb895c9eb3` | `[M]` |
| `REPORTS-MANIFEST.sha256` | — | — | 13 entries, all 13 verify `OK` | `[M]` |
| `docs/r6-*.md` inventory | — | — | **42** documents | `[M]` |

**Key addendum anchors `[M]`:** `:528` PARAM-A.2 (O5) · `:533` PARAM-A.7 (O5) · `:538` PARAM-B.5 **(O4)** ·
`:539` PARAM-B.6 **(O1)** · `:644` N1-O5 heading · `:646` N1-O5 body — **exactly four O5 occurrences**.

**Test baseline `[M]`** (re-run 2026-11-16 under `./.venv/bin/python -m pytest`):

```text
tests/test_r6_registration_digest_conformance.py   105 passed, 1 skipped
tests/test_r6_settlement_integrity.py                6 passed
full suite (tests/)                                 774 passed, 10 skipped
ruff check .                                       350 errors (repo-wide — WRONG SCOPE; superseded below)
mypy .                                             1 error (repo-wide — WRONG SCOPE; superseded below)
ruff check src tests scripts config All checks passed! (gate scope, 2026-11-16)
mypy src Success: no issues found in 49 source files (gate scope, 2026-11-16)
```

**Scope correction (2026-11-16).** `CLAUDE.md` §11 scopes the quality bar to
`src tests scripts config` for ruff and to `src` for mypy; it does not cover `artifacts/`.
The two repo-wide lines above therefore measure `artifacts/` scratch scripts, not the
codebase. At the gate's actual scope the only blocker was one pre-existing E731 at
`tests/test_r6_registration_digest_conformance.py:877`, since fixed.

---

# 6. DEFINITION OF DONE — R6.0

R6.0 is **not** complete because documents look consistent or tests pass. All ten must hold (Build Map §10):

| # | Condition | State |
|---:|---|---|
| 1 | Canonical decision register accurate | ✅ **re-derived 2026-11-16** — F-05 corrected; dated supersession at Part 2 `:391-417`, covering `:73`, `:219`, `:220`, `:223`, `:229`, `:318`. Live `grep -c O5` = **4** `[M]` |
| 2 | Owner selections and formal approvals distinguished | ✅ — addendum `PARAM-A.5` `:142-148` requires every registration to carry T16's provenance class and forbids upgrading `MISSION-FRAMED` to `EXACT OWNER`; §1.1 separates selection from approval `[M]` |
| 3 | Foundation contract documented without claiming implementation | ✅ — B1 Option A records ADR-2 as a **draft** R6.1 foundation contract (`r6-close-final-06-…:205`; `r6-command-centre-01-…:63`) with no implementation claim `[M]` |
| 4 | Registration and verification protocols internally consistent | ✅ **re-derived 2026-11-16** — F-06 corrected; 15 anchors re-derived by content, addendum §13 records old→new. Two §8 citations (`:267`, `:402`) remain stale and are **named** as outside F-06's recorded scope |
| 5 | Required evidence manifests reconcile | ✅ 13/13 — `shasum -a 256 -c REPORTS-MANIFEST.sha256` → 13 `OK`, 0 failures `[M]` |
| 6 | Privacy and trusted-checkpoint requirements addressed | ✅ **closed 2026-11-16.** **Privacy half:** D-4 answered by the owner — *"no exceptions at this time"* (signature sheet rulings `:303`), time-scoped and amendable, **not** permanent. **Trusted-checkpoint half:** fully specified in addendum §6 `PARAM-D.1`–`D.9` `:300-352` `[M]`; satisfaction is deferred by design and unauthorised, and initial anchoring remains UNRESOLVED (§11 U3) `[M]`. |
| 7 | Copilot completes independent verification | ✅ — WP-4 independent verification completed; findings F-05/F-06 originate there (build map §4) `[R]` |
| 8 | Blocking findings resolved **or** explicitly accepted by owner | ✅ **closed 2026-11-16.** **F-01 resolved** — S-1 designated the **T16 decision option register** as the O1–O5 locus. **F-02 explicitly accepted by the owner** — *"accepted, unproven, owner 2026-11-16 — not resolved, not blocking"* (signature sheet `:301`). WP-5 is unschedulable tonight: the real genesis hash requires the ledger, which is permanently gated. **F-02 may never be recorded as resolved without WP-5.** |
| 9 | BL-22 signed | ✅ **signed 2026-11-16** — S-4 ticked *"Sign BL-22 — the stated precondition is met"* (F-05/F-06 corrected) |
| 10 | G7 explicitly granted | ✅ **granted 2026-11-16** — S-5 ticked *"Grant G7 after WO-1 re-derives the DoD table"*; WO-1 completed 2026-11-16 |

**All ten rows are ✅ as of 2026-11-16. R6.0 is CLOSED at document level (D-1).** Closure means the decisions are recorded and the documents are consistent — it does **not** mean registration has been executed, and it does **not** instantiate a ledger (row 8 remains permanently gated).

---

# 7. UPDATE LOG

| Date | Actor | Change |
|---|---|---|
| 2026-11-16 | Claude Code Desktop | Scorecard created. WP-0–WP-4 mapped from live records; F-01–F-12 registered; R6.1–R6.7 confirmed not authorised. F-05 and baseline measurements re-derived from live bytes. |
| 2026-11-16 | Claude Code (executioner) | PH-0/PH-3. F-03/F-04/F-05/F-06 corrected by dated supersession; F-02 → PARTIALLY PROVEN with `:570` still skipped. §5 baseline re-measured: protocol 14,620→15,898 B, addendum 39,784→42,917 B, proposal 48,634→49,995 B; manifest and test baseline promoted `[R]`→`[M]`. PH-2 commit **not performed** — ruff/mypy not clean. |
| 2026-11-16 | Claude Code | PH-2. Gate commands re-run at the §11 scope (`ruff check src tests scripts config`, `mypy src`): the "350 errors" were `artifacts/` scratch scripts, not the codebase. The single real blocker, a pre-existing E731 at conformance `:877`, was fixed. Scoped ruff now **All checks passed**; `mypy src` clean over 49 files. The 42-document corpus was then staged by explicit path, diff-inspected and committed as `e0530e5`. Re-derived: **42 of 42 tracked**; manifest **13/13 verify**. **F-09 CLOSED.** |
| 2026-11-16 | Claude Code (executioner) | PHOENIX Phase 1 (WO-1…WO-7). DoD table re-derived: rows 2,3,5,7 cited; **row 6 corrected** — "D-4 decided" was unsupported (build map records a *recommendation*; §3 still OUTSTANDING); **row 8** re-grounded on F-01 and the misquote of §4.3 corrected. Build map §1.2 ground 2 withdrawn; §1.1 reconciled to `e0530e5`. F-10/F-11 searched, absence not established. `REPORTS-PROVENANCE.md` attributed (WO-3), still unstaged. PH-1 decision record assembled. **Phase 2 not started — signature sheet unsigned.** |

---

## How to update this file

1. **Never edit a green row to red.** Add a dated row to §7 and a new finding to §4; supersede in place.
2. **Re-measure before promoting.** `[R]` → `[M]` only by reading live bytes this session.
3. **`Implemented` ≠ `Tested` ≠ `Independently verified` ≠ `Gate accepted`.** Do not conflate.
4. **A skipped test is never a pass.** It stays a finding until it runs.
5. **Do not advance WP-5, BL-22, G7 or R6.1–R6.7** without an explicit owner disposition recorded in §7.

```text
CURRENT GATE: Phase 1 complete — Phase 2 blocked on six owner signatures (S-1…S-6)
CURRENT PHASE: R6.0 closure (R6.1–R6.7 NOT AUTHORISED)
PROVEN: 3/3 U2 vectors · 13/13 manifest · 42/42 corpus tracked · test baseline · genesis hash arithmetic · DoD rows 1,2,3,4,5,7 ✅
UNPROVEN: O6–O8 / ledger absence · untracked drift attribution · real genesis hash · trusted-checkpoint half of row 6
BLOCKED BY: F-01 (O1–O5 locus — S-1/S-2/S-3) · D-4 undecided (row 6) · D-5/D-6 (rows 9,10) · C-1/C-2/C-3
NEXT: Owner completes OWNER-SIGNATURE-SHEET.md — S-1/S-2/S-3 unblock F-01 and PH-1
```

| 2026-11-16 | Claude Code (executioner) | R6 completion run. **RB-1:** trusted-checkpoint half of row 6 derived for the first time — `PARAM-D.1`–`D.9` fully specify it, nothing satisfies it, anchoring UNRESOLVED (U3). **RB-2:** `EXECUTIONER-WORK-ORDER.md` header corrected to match the per-WO gates. **RB-3:** row 8 **restored to F-01 *and* F-02** — the earlier narrowing to F-01 alone used the superseded `SPRINT_PHOENIX_BUILD_MAP.md` §4.3 census; `BUILD-MAP-R6-TO-R8.md` §6.2 records 2 blocking and §6.3 withdrew the reclassification. Phase C not started — S-6 unsigned. |
| 2026-11-16 | Claude Code (executioner) | **Signature sheet live — 10 ticks, attestation dated 2026-11-16.** DoD rows 6, 8, 9, 10 closed: D-4 answered ("no exceptions at this time"); F-01 resolved by S-1 (T16 locus); F-02 accepted-unproven by owner (WP-5 unschedulable — needs the gated ledger); BL-22 signed (S-4); G7 granted (S-5). **All ten rows ✅ — R6.0 CLOSED at document level.** C-1 amendment rows written for rows 1, 2, 7. S-3 Alt-1 re-verified against the protocol text: 163 B / `97dc52a6…`, and the 161-byte hazard `fc16e6d2…` reproduced. |