# THE BUILD MAP — R6.0 → R6.7, AND WHAT LIES BEYOND

**Date of record:** 2026-11-16 · **Branch:** `sec/deps-nov` · **HEAD:** `e0530e5`
**Prepared by:** Claude Code · **Consolidates:** `SPRINT_PHOENIX_BUILD_MAP.md` (retained), `MASTER-PROMPT.md` (retained), `OVERNIGHT-RUN-REPORT.md` (retained)

---

## 0. READ THIS FIRST — three corrections to the brief you gave

You asked for a map "till the end of R1–R8". Three things must be said plainly before the map,
because a map that flatters the request is worth less than one you can plan a week from.

### 0.1 R1–R5 and R7–R8 are CLOSED — an earlier draft of this map was wrong

**A first draft of this document claimed R1–R5, R7 and R8 did not exist in this repository. That
was wrong, and the correction is recorded here rather than quietly deleted.**

The error was methodological: it was written from a search of **document filenames**
(`docs/r6-*.md`) and never checked the code, tests or commit history, where that work actually
lives. R1–R8 evidence largely takes the form of commits and suite runs, not protocol documents —
so a filename search could not have found it.

The programme dashboard (`SabiRoute — R1–R8 Implementation & Acceptance Status`, snapshot
2026-11-02, baseline HEAD `319a711`) records R1–R5 and R7–R8 as **COMPLETE and ACCEPTED**, with
R6 the only open run:

| Release | Area | Dashboard | Evidence cited |
|---|---|---|---|
| R1 | Evidence & Provenance | COMPLETE 100% | `302d76e`; manifest 13/13; scorecard synced |
| R2 | Provider Compatibility & Execution | COMPLETE 100% | 14 aliases + 1 item param; 19 model YAMLs |
| R3 | Routing, Policy & Correctness | COMPLETE 100% | 43 RF3 files verified; B1 acceptance |
| R4 | F-27 Accounting & Rotation | COMPLETE 100% | 46/46 (7-suite), 31/31 (6-suite core) |
| R5 | Reliability & Execution Semantics | COMPLETE 100% | 25/25 across 3 files |
| **R6** | **Compression & Context Optimization** | **IN PROGRESS 0%** | **design only — no implementation, no tests** |
| R7 | Integrated Regression & Release Evidence | COMPLETE 100% | 672 full suite; RP6 + Redis; 656+ offline |
| R8 | T8 Consolidation & Acceptance | DONE — OWNER GREEN R8-G1 | Stable SHA `1d91f73`; fresh T1/T8 re-review PASS; 839 passed / 10 skipped; six legacy badges `UNTRACEABLE / WITHDRAWN` |

**`319a711` is confirmed present in this repository** — `git cat-file -t` → `commit` `[M]`. The
active HEAD is `e0530e5`, **later** than the dashboard snapshot.

### 0.1a The dashboard and the tree's own scorecard disagree — and both drafts of this section were wrong

`reports/my_scorecard.md` is the repository's own record. It does **not** agree with the
dashboard:

| Release | Dashboard says | `reports/my_scorecard.md` says |
|---|---|---|
| R5 | COMPLETE 100% | *"scoped PASS (historical)"* `:90` — scoped and historical, not current |
| R7 | COMPLETE 100% | **partial** `:92` — *"Managed-PG/TLS, backup/restore, compose E2E, GH run, staging"* outstanding |
| **R8** | **DONE — OWNER GREEN R8-G1** | Previously BLOCKED `:93`; now DONE at stable SHA `1d91f73` after fresh T1/T8 re-review PASS, recorded in `R8-OWNER-GREEN-CLOSURE.md` |

**There is no T8 consolidation document in the tree**, so the dashboard's legacy *"6 verdicts
ACCEPTED"* could not be traced to a source. Those badges were withdrawn under `R8-W1` as
`UNTRACEABLE / WITHDRAWN`. R8 closure now rests on fresh evidence and owner green `R8-G1`, not on
that legacy badge.

**Two drafts of this section, both wrong:**

1. The first said R1–R5, R7 and R8 *did not exist here* — written from a filename search, which
   cannot find work that lives in code, tests and commit history.
2. The second said they were *CLOSED* — which took the dashboard at face value. Confirming
   `319a711` exists is not confirming that R8 was accepted.

**The accurate position:** R1–R6 carry substantial, genuinely verified code and test evidence
(R3 alone: 129 passed against real disposable PostgreSQL + Redis, three consecutive runs,
mutation-verified). **R7 is partial. R8 is DONE by owner row R8-G1** at stable SHA `1d91f73`
after fresh T1/T8 re-review PASS. The historical R8 badge was unsupported; the closure is not.

**This was not a defect the executioner created.** It was an open conflict between two records,
recorded rather than silently reconciled. Owner row `R8-G1` now closes R8 and authorises this
dashboard correction; the six legacy badges remain withdrawn.

### 0.2 "Everything done when I get back" is not achievable tonight

Phase 1 of the sprint is **already complete** — it was executed and I scrutinised it. There is
very little unblocked execution work left. What remains is **six owner signatures** (§7) plus
one ruling (§6.3). No prompt, however large, converts a signature into something an agent can
do on your behalf.

**What you will actually have in the morning:** a small, honest set of Phase-1 refinements
(§8), and this map — which is what you said you want to plan the week from.

### 0.3 The executioner is not the bottleneck, and has not been since last night

Last night's run did the right thing: it stopped at the gate. If you send another overnight run
without signing the sheet, it will stop at the same gate again. **The fastest path to progress
is fifteen minutes with the signature sheet, not another overnight run.**

---

## 1. WHAT THIS DOCUMENT IS

A consolidated, current map of the R6 programme: what it is, what has been built, what is
blocked and on whom, and what the sequence to R6.7 looks like.

**Evidence labels** (repository standard, `CLAUDE.md` §2):

- `[M]` — **Measured** this session, command output recorded
- `[R]` — **Reported** by another actor or prior document; not re-derived here
- `[I]` — **Inferred** from structure or reasoning; not executed
- `[?]` — **Unverified** — absence of evidence, or a claim nobody has checked
- **BLOCKED** — cannot proceed; a named gate stops it
- **OWNER** — requires an owner act; no agent may perform it

**The standard this map is held to:** configured ≠ installed ≠ reachable ≠ working ≠ tested ≠
production-ready. Nothing below is upgraded a label without re-derivation.

---

## 2. WHAT R6 IS

**R6 — Intelligent Input Optimization.** The programme that makes SabiRoute decide *what the
provider is allowed to see*, before the request is executed.

### 2.1 The architectural boundary (the load-bearing rule)

> **SabiRoute decides. LiteLLM executes.**

`CLAUDE.md` §1. Every design decision in R6.2–R6.5 is tested against this line. It is the
reason R6.4 **reimplements** the compression policies rather than importing them: adopting the
engine's compressor places a *decision* inside the *execution engine*, leaving SabiRoute no
seam to audit, tune or attribute it.

### 2.2 The four-phase shape

| Phase | What it establishes | Why it must come first |
|---|---|---|
| **R6.0** | Closure — the governance and evidence base | Nothing downstream can be honestly built on an unclosed foundation |
| **R6.1** | Foundation contract — immutable original request, canonical representation, metadata, policy/capability checks **precede** transformation, explicit bypass | Every later phase rewrites provider-bound bytes; the contract decides what an immutable original means |
| **R6.2–R6.5** | The optimisation pipeline | Changes what is sent, therefore what is metered |
| **R6.6–R6.7** | Validation and staged rollout | Specifies evidence; produces none |

### 2.3 The dependency the order rests on — CORRECTED 2026-11-16

**Both defects below are FIXED. The construction dependency no longer holds.**

- **F1** — *was:* `attempted` read at `:602` before it was bound at `:1311` → `NameError`
  swallowed by the broad handler at `:621–632` → a denial masked as `503 quota_unavailable`,
  reservation stranded.
- **F3** — *was:* no `usage_unknown` parameter; the quota block recomputed at `:603`.

**Fixed in `08201da` — *"fix: preserve unknown usage across budget and quota settlement"*.** `[M]`
Verified directly: `attempted` is now bound at `:397` and first read at `:616`;
`provider_usage_unknown` is initialised at `:402` and threaded through every settlement path.

**What that changes.** An earlier version of this map — and of the completion prompt — argued
that R6.2–R6.5 were gated *by construction* because compression settles below its reservation and
the settlement path mis-settled. **That argument is spent.**

**What still gates them.** R6.1 remains a prerequisite — not because the settlement path is
broken, but because R6.1 defines the seam the pipeline fills: the immutable original request, the
canonical form, the metadata, and the rule that policy and capability checks **precede**
transformation. Building the pipeline first means building against an assumed contract.

**The gate is weaker, and it is still real — but it is a design dependency now, not a
correctness one.** Do not restate the old reason; it is no longer true.

---

## 3. WHERE THE PROGRAMME STANDS — the one-screen view

| Item | State | Evidence |
|---|---|---|
| Branch / HEAD | `sec/deps-nov` @ `e0530e5` | `[M]` |
| R6.0 corpus tracked | **42 of 42** | `[M]` |
| Evidence manifest | **13 of 13 verify** | `[M]` |
| `ruff check src tests scripts config` | **All checks passed** | `[M]` |
| `mypy src` | **clean, 49 files** | `[M]` |
| Conformance suite | 105 passed, **1 skipped** (`:570`) | `[M]` |
| Settlement suite | 6 passed | `[M]` |
| Full suite | 774 passed, 10 skipped, 0 failed | `[R]` |
| **DoD rows holding** | **6 of 10** (rows 1, 2, 3, 4, 5, 7) | `[M]` |
| **R6.0** | **OPEN** — rows 6, 8, 9, 10 | `[M]` |
| PH-0 / PH-2 / PH-3 | **DONE** | `[M]` |
| PH-1 / PH-4 | **BLOCKED — owner** | `[M]` |
| PH-5 / PH-6 | **NOT STARTED** | — |

**The `:570` skip is a finding, not a pass.** It asserts the protocol's own incompleteness
pending authorised ledger instantiation. It must stay skipped.

---

## 4. WHAT HAS BEEN BUILT — the dated record

### 4.1 The R6.0 document corpus (42 documents)

The closure programme produced 42 protocol documents under `docs/r6-*.md`, plus seven
`r6-close-final-*` closure documents, the T9–T17 working documents, and four implementation-prep
documents. **All 42 are now tracked** — this was PH-2, and it closed F-09.

### 4.2 The conformance suite

`tests/test_r6_registration_digest_conformance.py` — 105 tests, 1 skip. Currently **untracked**
in git; durability depends on C-3 (§7). It carries the entire R6 registration conformance
programme in a single working-tree file.

`tests/test_r6_settlement_integrity.py` — 6 tests, tracked.

### 4.3 PH-0 — closure correction (DONE)

F-03, F-04, F-05 and F-06 corrected by **dated supersession**: originals retained verbatim, a
dated note appended with the live values. Never rewritten. `[M]`

| Finding | Defect | Correction |
|---|---|---|
| **F-03** | `VER:v1` token retired silently against Part 4 §14.1 | Token retained; question OPEN; correction DEFERRED |
| **F-04** | Stale byte/sha measurements | Re-derived: protocol 15,898 B; addendum 42,917 B; proposal 49,995 B |
| **F-05** | Parts 1–3 stale measurements, no supersession note | Supersession at Part 2 `:391-417`; live `grep -c O5` = **4** `[M]` |
| **F-06** | 15 stale protocol anchors | Re-derived by content; addendum §13 records old→new |

### 4.4 PH-2 — corpus durability (DONE)

42-document corpus staged **by explicit path**, diff inspected (0 paths outside `docs/r6-*.md`),
committed as **`e0530e5`**. `REPORTS-MANIFEST.sha256` 13/13 verify. **F-09 CLOSED.** `[M]`

### 4.5 PH-3 — F-02 partial proof (DONE)

`test_determinism_total_sensitivity` added, proving determinism on a **synthetic** genesis hash.
The real genesis hash remains gated on WP-5. **F-02 is PARTIALLY PROVEN — NOT CLOSED**, and
remains **blocking** (§6.3).

### 4.6 The overnight run — Phase 1 (DONE)

WO-1…WO-7 executed and stopped at the signature gate. Results:
DoD table re-derived and cited; build map §1.2 reconciled; `REPORTS-PROVENANCE.md` attributed
(unstaged); F-10 and F-11 searched — **absence NOT established**; PH-1 decision record
assembled. Nothing committed, staged or pushed. `[M]`

**Reviewer corrections applied:** the report's "seven of ten" corrected to **six**; the
reclassification of F-02 withdrawn (it was an unauthorised edit made mid-session and is now
reverted in §4.3 and DoD row 8).

---

## 5. THE ARCHITECTURE, AS IT STANDS

### 5.1 What exists in `src/sabiroute/`

`api`, `chat`, `config`, `freepool`, `intelligence`, `monitoring`, `providers`, `routing`,
`security`, `utils` + `capabilities.py`, `gateway…` `[R]`

**What does not exist:** no `compression/` package, no `request_transform/` package. R6.1–R6.5
are greenfield within that tree.

### 5.2 The settlement path (where the risk lives)

`api/completions.py`:

- `:542` `finish()` — the settlement entry point
- `:602` reads `attempted` — **before** it is bound at `:1311` (defect F1)
- `:621–632` broad handler — swallows the `NameError`
- `:603` quota block recomputes (defect F3)

**Every R6.2–R6.5 phase changes the bytes sent to the provider, therefore the token count that
is metered. This path must be sound first.**

### 5.3 The compression decision (R6.4, decided)

The stock `litellm.compress()` path is **rejected** — eight findings, established by inspection
of LiteLLM 1.103.0. The two that matter most:

- **It injects a retrieval tool** (`litellm_content_retrieve`) that SabiRoute cannot serve —
  every call becomes a guaranteed dangling tool call. **This alone disqualifies it as a
  drop-in.** `[R]`
- **The tokenizer is ASCII-only** (`re.findall(r"[a-z0-9_]+", text.lower())`) — non-Latin
  content yields no query terms, every message scores equally, ranking is arbitrary insertion
  order. This is the same defect class T16 C2 already gates release claims on, now established
  at implementation level. `[R]`

**What R6.4 adopts — the design, not the code:**

1. `get_protected_indices` — system messages, last user message, last assistant message, and
   **every message up to and including the last Anthropic `cache_control` breakpoint**. That
   last is a genuine insight: rewriting any row inside a cached prefix turns the next request's
   cache *read* into a cache *write*, making compression actively **more** expensive.
2. The **atomic tool-exchange span** concept — the right shape for preserving tool-call pairing.

R6.4 **reimplements** both. It does not import them.

### 5.4 The four decisions a compression implementation must make explicitly

| Decision | Default if unspecified | Why it matters |
|---|---|---|
| Granularity | Whole messages (stock behaviour) | A constraint buried in a low-ranked message is deleted with it |
| Truncation safety | Line-split 70/30 (stock) | On a JSON body this yields **syntactically invalid content** |
| Token accounting | Engine's estimator | Two estimators = two "tokens saved" numbers, no reconciliation |
| Bypass surface | Protected indices only | Needs a policy enum and request correlation |

---

## 6. THE REGISTERS

### 6.1 The authorisation ledger (build map §6 — the authority)

| Row | Act | State |
|---:|---|---|
| 1 | Correct F-03/F-04/F-05/F-06 in place | **YES — owner 2026-11-16 (C-1)**; amendment row recorded below |
| 2 | Re-run test suites and record output | **YES — owner 2026-11-16 (C-1)**; amendment row recorded below |
| 3 | Designate the O1–O5 registration locus (D-2) | **YES — owner 2026-11-16 (S-1)** — locus is the **T16 decision option register** |
| 4 | Adopt U4 reading R-A | **YES — owner 2026-11-16 (S-2)** — **R-A** adopted |
| 5 | Compute `marker_sha256` / answer O3 | **YES — owner 2026-11-16 (S-3)** — **Alt-1** (163 B) chosen; computation authorised |
| 6 | Stage and commit the 42-doc corpus (F-09.2) | **YES — owner 2026-11-16**, conditional on green suites **MET** (`e0530e5`) |
| 7 | Add the synthetic genesis-hash test (F-02) | **YES — owner 2026-11-16 (C-1)**; amendment row recorded below |
| 8 | Instantiate any registration ledger | **PERMANENTLY GATED** — never |
| 9 | Sign BL-22 | **YES — owner 2026-11-16 (S-4)** — **signed** |
| 10 | Grant G7 | **YES — owner 2026-11-16 (S-5)** — granted; WO-1 precondition met |
| 11 | Authorise R6.1 | **YES — owner 2026-11-16 (S-6)** — **tranche 1 only**, review point at contract draft |
| 12–15 | [as recorded in the build map] | **No** |
| 16 | [as recorded in the build map] | **No** |

### 6.1a Amendments recorded 2026-11-16 (C-1, S-1 … S-6)

One row per act, each quoting the owner's words. The §6 table above was **not** edited to "YES"
in advance of a basis — every row below names the basis it rests on.

| Date | Row | Amendment | Basis (owner's words) |
|---|---:|---|---|
| 2026-11-16 | 1 | `No` → **YES** | C-1: *"Yes — I granted rows 1, 2 and 7 on 2026-11-16, in the PHOENIX execution prompt"* |
| 2026-11-16 | 2 | `No` → **YES** | C-1: same basis |
| 2026-11-16 | 7 | `No` → **YES** | C-1: same basis |
| 2026-11-16 | 3 | `No` → **YES** | S-1: ticked *"A — T16 decision option register"* |
| 2026-11-16 | 4 | `No` → **YES** | S-2: ticked *"R-A — delimiters inclusive, no other change"* |
| 2026-11-16 | 5 | `No` → **YES** | S-3: ticked *"Alt-1 — value only, `A3: ` retained, 163 bytes"* and *"Authorise `marker_sha256` computation"* |
| 2026-11-16 | 9 | `No` → **YES** | S-4: ticked *"Sign BL-22 — the stated precondition is met"* |
| 2026-11-16 | 10 | `No` → **YES** | S-5: ticked *"Grant G7 after WO-1 re-derives the DoD table"* — WO-1 was completed 2026-11-16 |
| 2026-11-16 | 11 | `No` → **YES** | S-6: ticked *"R6.1 only — tranche 1"*, with a review point at the contract draft |

**Row 8 is unchanged and remains permanently gated.** No ledger was instantiated.

**Superseded text, retained for audit:** *"Rows 1, 2 and 7 are the C-1 defect:** three acts
were performed against a grant the ledger does not record. The table says "No"; §6.1 prose says
granted; the amendment table has one row only (row 6).* That state was **correct when written**
and is now **resolved** by C-1 above — the table and the prose now agree because each row has a
recorded basis. The table says "No"; §6.1 prose says granted; the amendment table has one row
only (row 6). **Do not fix this by editing the table to "YES"** — that fabricates an
authorisation record. The owner confirms the basis; then one dated amendment row per act is
written, quoting the owner's words, exactly as row 6 was done.

### 6.1b Dated act — the `tests/` edit (C-2, recorded 2026-11-16)

| Field | Value |
|---|---|
| File | `tests/test_r6_registration_digest_conformance.py` |
| Line | `:877` (at the time of the edit) |
| Change | An `E731` violation — a lambda assigned to a name — replaced with a `def h(s: str) -> str:` function. Behaviour identical; the helper still returns `hashlib.sha256(s.encode("utf-8")).hexdigest()`. |
| Owner's words | *"yes, fix it"* (C-2), and *"C-3: track the conformance file AND fix E731 at :877 in the same commit"* |
| Supersedes | Build map §0.3, which says the PHOENIX approval does **not** authorise editing `src/` or `tests/`. **This one edit is authorised; §0.3 is unchanged for every other file.** |

**Verified 2026-11-16** `[M]`: `ruff check src tests scripts config` → `All checks passed!` with the
conformance file included. The fix is in the working tree and C-3's condition is met.

---

### 6.2 Findings — the census

**12 findings: 1 blocking (F-01, resolved 2026-11-16 by S-1), 1 accepted-unproven (F-02, owner 2026-11-16), 4 corrected (F-03–F-06), 1 closed (F-09), 1 recorded
(F-12), 1 accepted-by-design (F-07), 1 preserved-unexplained (F-08), 1 open-gap (F-10),
1 unverified (F-11).**

| ID | Finding | State |
|---|---|---|
| **F-01** | O1–O5 registration locus undefined | **BLOCKING** — D-2 / S-1 |
| **F-02** | Genesis hash not proven | **ACCEPTED, UNPROVEN — owner 2026-11-16** — *"not resolved, not blocking"*; real hash still gated on WP-5, which needs the permanently-gated ledger |
| F-03 | `VER:v1` token retired silently | **CORRECTED** — token retained, question OPEN, correction DEFERRED |
| F-04 | Stale byte/sha measurements | **CORRECTED** |
| F-05 | Parts 1–3 stale, no supersession note | **CORRECTED** |
| F-06 | 15 stale protocol anchors | **CORRECTED** |
| F-07 | Supersession without deletion | **ACCEPTED BY DESIGN** |
| F-08 | Untracked drift 146→147→149 | **PRESERVED UNEXPLAINED** — no 147 snapshot exists |
| F-09 | Corpus not tracked | **CLOSED 2026-11-16** — `e0530e5` |
| F-10 | No hashed owner-decision record for R1 | **OPEN GAP** — searched, NOT FOUND, absence not established |
| F-11 | Copilot never searched for O6–O8 / ledger | **UNVERIFIED** — searched, NOT FOUND, absence not established |
| F-12 | Three-way digest coupling unaccounted | **RECORDED** — do not model yet |

### 6.3 The one ruling that changed today

F-02 was briefly reclassified from *blocking* to *partially proven* by an editor working on this
sprint — **without authority**. That reclassification has been **withdrawn**. F-02's scorecard
status is `PARTIALLY PROVEN — NOT CLOSED`; "partially proven" describes its **evidence state**,
not its severity.

**Consequence:** DoD row 8 fails on **F-01 and F-02**, not F-01 alone. The ruling you owe is
larger than the overnight report concluded, not smaller.

**Owner ruling outstanding:** does F-02 stay in the blocking set?

### 6.4 Decisions register

| ID | Decision | State |
|---|---|---|
| D-1 | Closure is document-level | **APPROVED** |
| D-2 | One existing tracked document as the locus — no new file | **Recommendation approved; document NOT named** → S-1 |
| D-3 | WRITE/UPDATE both supported | **APPROVED** |
| D-4 | Privacy/evidence exceptions (P-6) | **OUTSTANDING** — build map records a *recommendation* ("No exceptions"), not an owner answer |
| D-5 | BL-22 signature | **NOT SIGNED** → S-4 |
| D-6 | G7 grant | **NOT GRANTED** → S-5 |
| D-7 | R6.1 authorisation | **NOT GRANTED** — recommended in tranches → S-6 |
| D-8 | Old untracked proposal → archive | **APPROVED** |
| D-9 | R-1 branch mismatch → report, never resolve | **APPROVED** |

### 6.5 The Definition of Done — 6 of 10

| # | Condition | State |
|---:|---|---|
| 1 | Canonical decision register accurate | ✅ F-05 corrected; Part 2 `:391-417`; `grep -c O5` = 4 `[M]` |
| 2 | Owner selections and formal approvals distinguished | ✅ addendum `PARAM-A.5` `:142-148` `[M]` |
| 3 | Foundation contract documented without implementation claim | ✅ ADR-2 recorded as **draft** `[M]` |
| 4 | Protocols internally consistent | ✅ F-06 corrected; two §8 citations named as out of scope |
| 5 | Evidence manifests reconcile | ✅ 13/13 `[M]` |
| 6 | Privacy and trusted-checkpoint addressed | ⚠️ **D-4 OUTSTANDING**; trusted-checkpoint half **never re-derived in three passes** |
| 7 | Copilot completes independent verification | ✅ WP-4 `[R]` |
| 8 | Blocking findings resolved or accepted | ❌ **F-01 and F-02 both unresolved** |
| 9 | BL-22 signed | ❌ D-5 |
| 10 | G7 granted | ❌ D-6 |

**Until every row is ✅: R6.0 OPEN.**

---

## 7. THE SIX SIGNATURES — the only thing standing between you and R6.1

All in `OWNER-SIGNATURE-SHEET.md`. Each has a recommendation; accepting all of them is a
complete answer.

| # | Decision | Recommendation | Unblocks |
|---|---|---|---|
| **S-1** | Registration locus (row 3) | `docs/r6-t16-r6-decision-option-register.md` | F-01 |
| **S-2** | U4 reading R-A vs R-C (row 4) | **R-A** — delimiters inclusive, no other change | PH-1 step 5.4 |
| **S-3** | O3 boundary (row 5) | **Alt-1** — value only, `A3: ` retained, 163 B | `marker_sha256` |
| **S-4** | Sign BL-22 (row 9) | **Sign** — the F-05/F-06 precondition is met | DoD row 9 |
| **S-5** | Grant G7 (row 10) | **Grant after** the DoD re-derivation (now done) | DoD row 10 |
| **S-6** | Authorise R6.1 (row 11) | **R6.1 only** — tranche 1 | PH-5 |

**Plus three confirmations:** C-1 (rows 1/2/7 were granted), C-2 (the `tests/` edit was
authorised), C-3 (track the conformance file).

---

## 8. TONIGHT — what an executioner can actually do

**Be honest with yourself about the size of this list.** Phase 1 is done. What remains is small.

| # | Task | Gate | Value |
|---|---|---|---|
| 1 | **Re-derive DoD row 6's trusted-checkpoint half** | none | The largest unexamined area left — no one has touched it in three passes |
| 2 | Correct `EXECUTIONER-WORK-ORDER.md:7-9` header contradiction | none | It is my defect, not the executioner's; WO-3/WO-4 say "Gate: none" while the header lists them as gated, and WO-9 is gated on C-2 while the header omits it |
| 3 | Assemble the **R6.1 entry-gate evidence pack** | none (prep) | Feeds S-6: what R6.1 must satisfy, cited from T17 |
| 4 | Assemble the **R6.2–R6.5 dependency surface** | none (prep) | Feeds the week's planning: phase order, what each touches, the F1/F3 coupling |
| 5 | Re-run the full suite and record | none | 774 passed is `[R]`; make it `[M]` |
| 6 | Draft **week-plan options** | none | Three sequences, with costs, for you to choose between |

**What an executioner may NOT do tonight, regardless of instruction:** proceed past rows 3, 4, 5,
9, 10, 11 without a signature; instantiate any ledger; edit §6 to "YES"; commit without a named
row; push, merge or rebase.

---

## 9. BEYOND R6 — closed, and what that rests on

### 9.1 The dashboard is a report, not a measurement

The R1–R8 dashboard states 100% A6 readiness with 139 of 148 deliverables complete. It is a
**`[R]`-class artifact**: it asserts results; it does not carry the command output behind them.
Its baseline is `319a711` (2026-11-02), older than the active HEAD `e0530e5`.

**Nothing here disputes it.** But by this repository's own standard, an acceptance badge is not
evidence. What would convert it to `[M]`:

| Check | Why it matters |
|---|---|
| Full suite re-run at `e0530e5` | The dashboard's 672/0/0 was at `319a711`; the tree has moved |
| The 6 R8 verdicts re-read against their source reports | "ACCEPTED" must trace to a decision record |
| R1's manifest re-verified | 13/13 is a file state; files change |
| R4's accounting suites re-run | 46/46 and 31/31 predate the R6 corpus commit |

This is a **read-only** audit — Phase A of `R6-COMPLETION-PROMPT.md`.

### 9.2 R6 is the only release with work left **to build** — it is not the only open record

**R7 is partial; R8 is DONE by owner row R8-G1** at stable SHA `1d91f73` (§0.1a). R6 is the only
release where nothing has been built yet; R7 still needs an owner act rather than code, while R8
is closed and recorded.

R6 shows **0%**: *"Design documented (requirements, strategy)"* is ticked; *"Corpus and dataset
preparation"*, *"Compression pipeline (CD1–CD6)"* and *"Evaluation and operational evidence"* are
not. The dashboard names the remaining milestones explicitly:

1. Finalise R6 requirements and design (CD1–CD6)
2. Implement compression pipeline and integration
3. Add evaluation and quality tests (cost, latency, token savings)
4. Validate end-to-end and update scorecard (R6 → 100%)

**That is the whole of R6.1 → R6.7**, and it is the entirety of the remaining programme.

### 9.3 What R6.7 completion actually means

R6.7 is **staged rollout with pre-registered stop rules**. Its exit is not "it works" but
"the evidence specified in R6.6 was obtained, and no stop rule fired."

**R6.6 defines thresholds as slot identifiers with derivation rules — numeric values appear
nowhere.** That is deliberate: the thresholds cannot be set until there is data, and setting
them in advance would be inventing evidence.

---

## 10. THE SEQUENCE, STATED ONCE

```
R6.0  CLOSURE                          [OPEN — rows 6, 8, 9, 10]
  │   needs: S-1, S-2, S-3 (F-01) · S-4 (BL-22) · S-5 (G7)
  │          ruling on F-02 · real derivation of row 6's trusted-checkpoint half
  ▼
R6.1  FOUNDATION CONTRACT              [NOT STARTED — gate S-6]
  │   immutable original request · canonical representation · metadata ·
  │   policy/capability checks PRECEDE transformation · explicit bypass
  │   source: r6-t17-foundation-contract-extraction-and-track-a-engagement-packet.md
  ▼
R6.2–R6.5  OPTIMISATION PIPELINE       [NOT STARTED — entry-gated on R6.1 by construction]
  │   gated because they change metered bytes, and the settlement path carries F1/F3
  │   source: r6-impl-prep-02-r62-r65-pipeline-preparation.md
  ▼
R6.6–R6.7  VALIDATION AND ROLLOUT      [NOT STARTED — specification only, no evidence]
      thresholds are slots, not values · pre-registered stop rules
      source: r6-impl-prep-03-r6.6-r6.7-validation-and-rollout-preparation.md

R1–R5, R7, R8                          [DO NOT EXIST in this repository]
```

**Running in parallel, permanently:** the P0 lane. Sprint PHOENIX does not block P0-2.

---

## 11. WHAT YOU SHOULD DECIDE IN THE MORNING

1. **The F-02 ruling** — does it stay in the blocking set? (§6.3)
2. **D-4** — the privacy recommendation, and the trusted-checkpoint half of row 6 (§6.5)
3. **The six signatures** (§7) — the only path to R6.1
4. **Whether R1–R5 say anything real** (§9.1) — if they do, they exist somewhere outside this repo and need importing before they can be planned

---

## 12. STANDING INVARIANTS — never broken, by anyone

1. **Row 8 — ledger instantiation — is permanently gated.** No REG record, no VER record, no
   chain head, no ledger file. The `:570` skip stays skipped.
2. **No `git add .` or `-A`.** Explicit paths; inspect `git diff --cached` before any commit.
3. **No commit without a named authorisation row.**
4. **No push, merge, rebase, reset, stash, checkout.** R-1 is reported, never resolved (D-9).
5. **No real provider calls. No model training.** `training_authorized` stays `false`.
6. **No deferred question resolved by silence.** Part 4 §14.1 governs `VER:v1`.
7. **The quality bar is scoped:** `ruff check src tests scripts config` and `mypy src`. It does
   **not** cover `artifacts/`. Running either repo-wide measures scratch scripts and produces a
   false failure that already cost this sprint a full stop.
8. **A recommendation is not a decision.** A measurement is not a verification. A green suite is
   not a closed finding. A skipped test is never a pass.
9. **A failed search does not establish absence.** Record the search surface, not a conclusion.
10. **Do not reclassify a finding to make a gate pass.** That happened once on this sprint and
    was withdrawn.

---

## 13. FILE INDEX

| File | What it is |
|---|---|
| `BUILD-MAP-R6-TO-R8.md` | **This document** — the map of record |
| `SPRINT_PHOENIX_BUILD_MAP.md` | The prior build map — retained as history |
| `MASTER-PROMPT.md` | The overnight-run prompt — retained |
| `EXECUTIONER-WORK-ORDER.md` | Eleven work orders (header defect at `:7-9`, see §8) |
| `OWNER-SIGNATURE-SHEET.md` | **The six signatures + three confirmations** |
| `NEXT-BRIEF-PH1-PH4.md` | The analysis behind the signature sheet |
| `PH-1-DECISION-RECORD.md` | R-A, O3 and the locus candidates, quoted verbatim |
| `PH0-PH3-EXECUTION-REPORT.md` | The PH-0/PH-3 run — corrected in place |
| `OVERNIGHT-RUN-REPORT.md` | The Phase 1 run — corrected by reviewer |
| `R6_SCORECARD.md` | Findings, decisions, DoD |
| `REPORTS-MANIFEST.sha256` | 13/13 `[M]` |

---

**THE MAP'S OWN LIMIT.** This document covers R6.0 → R6.7. It does not cover R1–R5, R7 or R8,
because no material for them exists in this repository. If you need those scoped, that is a
planning act — and it needs a source, not an inference from what happens to be lying around.

**Current position: R6.0 OPEN, 6 of 10 DoD rows, blocked on six owner signatures.**
