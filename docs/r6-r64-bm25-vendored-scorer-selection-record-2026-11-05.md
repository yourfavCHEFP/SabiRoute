# R6.4 — Vendored BM25 scorer: selection record

**Record type:** *selection record.* **Not** a decision, **not** a register entry, **not** an approval.
**Selected:** a **vendored (SabiRoute-owned) BM25 scorer** for R6.4, rather than a dependency on `litellm.compression.scoring.bm25`.
**Date:** 2026-11-05 · **Baseline:** `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` — **VERIFIED BY RUNTIME** this session (`git rev-parse HEAD`). Branch inherited as `feat/sabiroute-routing-foundation` (**INHERITED**, `git branch --show-current` blocked this session).
**Mode:** recording only. **This document implements nothing, imports nothing, adds no module, runs no test, calls no provider, changes no decision status, and authorises no phase.** One file was created: this one.

**Does this record originate the direction? No.** The vendored scorer is already recorded twice in the corpus: as the **minimum adapter** (T11 §10 — *"vendored/reimplemented scorer (T10-1; zero SDK imports on the request path VERIFIED)"*) and as a **`CONDITIONAL` integration policy** (T11 §5 item 10 — *"(b′) vendored scorer, disabled-built R6.4, six enablement proofs"*). This record adds an operator's 2026-11-05 confirmation of a direction already carried, and separates that confirmation from registration and approval. **It changes no phase's state, and it does not make a conditional policy item unconditional.**

**Canonical count unaffected: 23 decisions remain 23. All 23 remain `OUTSTANDING`. `0 approved by this record.`**

---

## 0. The four statuses, kept apart

The single purpose of this document is to separate four things that a casual reading would collapse into "R6.4 was decided". They are different acts, performed by different parties, with different standing, and **three of the four have not happened.**

| # | Layer | What it is | Status | Performed by | Where it lives |
|---|---|---|---|---|---|
| **S0** | **Chat-level selection** | An operator's stated direction for R6.4's scorer, given in conversation on 2026-11-05 | **OCCURRED** | Operator | This conversation only — **no standing in the corpus** |
| **S1** | **Durable recording** | This file: a persisted, citable account of what S0 said | **PERFORMED — by this document** | Recording author | `docs/` (this file) |
| **S2** | **Canonical registration** | An entry in the R6 decision register (T16), carrying a canonical ID, an owner response and an approval record | **NOT PERFORMED** | Owner, via the register act | `docs/r6-t16-r6-decision-option-register.md` |
| **S3** | **Implementation approval** | Authorisation to write the module, the tests and the call site | **NOT PERFORMED — and not requestable here** | Owner + G7 + Track A | T16 D-group; §6.2 below |

**This distinction is already a recorded principle, not one invented here.** T17 §A states it in one line: *"Silence is not approval. A prepared card is not a taken decision. **A recorded selection is not a registration.**"* This document applies that principle to one R6.4 axis; it does not establish it.

**The load-bearing distinction.** S1 makes S0 *recoverable*; it does not make S0 *authoritative*. A future reader who opens this file learns what was selected and on what evidence. A future reader who opens the register learns what governs. **Those are not the same fact, and this file does not move the selection from the first to the second.** Until S2 occurs, "vendored BM25" is a recorded direction, not a registered decision — and a recorded direction is exactly the class of artefact this corpus already carries several of while labelling them *unregistered* (U-1 package name, B6 monotone-shrink, B7 no re-derivation; prep-02 §7.1, §9 — **INHERITED**).

**Why the distinction is not pedantry here.** The selection cannot change what any phase is permitted to do, because every R6.2–R6.5 phase is entry-gated behind R6.1 closure by construction (prep-02 §0). A document that blurred S1 into S2 would authorise nothing in practice while appearing to authorise everything in the audit trail — the same failure shape as the `A1`–`A4` collision the register-amendment proposal raises, where one label, unqualified, denotes both a decision that freezes an architecture and a defect that causes under-billing.

---

## 1. What exactly was selected

**Scope of the selection: one axis.** Where the R6.4 relevance scorer's *code* comes from.

| Selected | Rejected |
|---|---|
| **Vendored:** `src/sabiroute/request_transform/bm25.py` (path per prep-02 §4; package name itself unregistered — U-1), written in-repo, owned by Track B, Okapi BM25 arithmetic implemented as ours | **SDK dependency:** calling `litellm.compression.scoring.bm25.bm25_score_messages` |

**What "vendored" concretely commits to.**

1. **No import of `litellm.compression` from any SabiRoute module** — not the scorer, not `compress()`, not `get_protected_indices`, not `truncate_message`.
2. **The two policies in `compress.py` are reimplemented, not transcribed.** Prep-02 §1.1 already identifies them: protected-index selection (system, last user, last assistant, and every message up to and including the last Anthropic `cache_control` breakpoint) and the atomic tool-exchange span. Copying text from a dependency into a module we then own requires the licence check in §6.3; reimplementing the *design* does not.
3. **The scorer is ours to correct.** The Unicode tokenizer fix is inside the scope of the selection, because the reason to vendor is precisely that the SDK's tokenizer is not ours to fix.

### 1.1 Constraints the selection inherits and cannot waive

T11 §10 fixes the minimum adapter's safety envelope and T11 §5 item 10 attaches enablement proofs. **Selecting a vendored scorer relaxes none of them**, and a selection record read as relaxing them would be materially wrong.

| Constraint | Source | Status under this record |
|---|---|---|
| No stock stubbing, no retrieval instructions | T11 §10 | **Binding** — the reason U-3 stays open |
| No content telemetry, no cache exposure | T11 §10; CD6 | Binding |
| Bounded execution, fail-to-original | T11 §10; prep-02 §6 X-01/X-02 | Binding |
| Null-content hardening mandatory | T11 §10 (T10-3) | Binding — P-16 |
| ASCII-tokenizer limitation **stands**; non-Latin claims excluded until proven | T11 §10 (T10-2); register **C2** | Binding — vendoring fixes the *defect*, it does not lift *C2* |
| Zero SDK imports on the request path | T11 §10 — recorded there as **VERIFIED** | Binding, and now testable via L-3 (§6.3) |
| **Disabled-built**; construction R6.4, enablement post-v1 | T11 §5-10, §10 | Binding — even a future S3 ships a module that does nothing |
| Six enablement proofs + D11 matrix + D8-pairing independence | T11 §5-10, §10 | **Not enumerated here**; they gate *enablement*, not this selection |

**The last two rows are the consequential ones.** Vendoring does not enable anything. R6.4 lands **disabled** and enablement is **post-v1**, so no reading of this selection produces a live scorer, and no claim of "BM25 shipped" can be constructed from it.

**What the selection does *not* decide — and must not be read as deciding.** The vendoring axis is independent of six open R6.4 questions, each already recorded as unresolved in prep-02 §7.1:

| ID | Question still open | Consequence if read as settled by this record |
|---|---|---|
| **U-2** | Which estimator is authoritative for "tokens saved", reconciled how? | Budget arithmetic defined by accident |
| **U-3** | Truthfulness-only elision marker, or a retrieval tool? | The tool-injection defect returns under a new name |
| **U-4** | Message granularity only, or sentence-level select-and-drop? | Scope expands with no approval |
| **U-5** | `k1`/`b`, trigger and target — policy values or tunables? | Provisional defaults silently become policy |
| **U-6** | Non-Latin support now, or bypass-with-reason pending Terminal D? | C2's release-claim gate is bypassed |
| **U-1** | Package name (`request_transform` vs `compression/`) | Every file path in prep-02 §4 treated as fixed |

Vendoring answers "whose code" and nothing else. It makes **U-6 addressable** — the tokenizer is ours to fix, which is the reason for vendoring — **without lifting C2**, leaves **U-2, U-3, U-4 and U-5** untouched, and does not create the directory **U-1** must name.

---

## 2. What this record is not

Stated as refusals, because a selection record is most useful for what it forecloses:

- **Not a decision.** No canonical ID is created, amended, answered or retired. The 23 remain 23.
- **Not a register amendment.** T16 is unmodified. The proposal pathway in `r6-register-amendment-proposal-2026-11-05.md` is unaffected and uninvoked.
- **Not an owner response.** No `Owner response:` field anywhere transitions off `PENDING`; no `Approval record:` leaves `NOT APPROVED`.
- **Not a gate.** B5, B6, B7, D1, D2, D3, G7 and Track A engagement are all in the states prep-02 §7.2 records. This selection satisfies none of them and is not a substitute for any.
- **Not a licence determination.** §6.3 states what must still be confirmed.
- **Not evidence that R6.4 may start.** See §6.2.

---

## 3. Evidence verified this session

Distinct from what is cited. Ten observations were made directly; the rest are marked inherited.

| Claim | Basis | Status |
|---|---|---|
| Installed LiteLLM is **1.103.0** | `.venv/lib/python3.11/site-packages/litellm-1.103.0.dist-info` present | **VERIFIED BY RUNTIME** |
| A scoring package exists at `litellm/compression/scoring/` | `__init__.py` (210 B), `bm25.py` (3,687 B), `embedding_scorer.py` (3,081 B) | **VERIFIED BY RUNTIME** |
| The SDK BM25 tokenizer is ASCII-only | `re.findall(r"[a-z0-9_]+", text.lower())` — `bm25.py:14`, read in full | **VERIFIED BY INSPECTION** |
| The SDK scorer applies a **prefix-expansion** heuristic (query term of ≥ 4 chars also accumulates TF from longer tokens that start with it) — `bm25.py:86–93` | read directly | **VERIFIED BY INSPECTION** — *not previously recorded in prep-02* |
| The SDK IDF is the `log((N − df + 0.5)/(df + 0.5) + 1)` form — `bm25.py:80` | read directly | **VERIFIED BY INSPECTION** — *not previously recorded in prep-02* |
| **No** `request_transform/` or `compression/` package exists in `src/sabiroute/` | `src/sabiroute/` = `api`, `chat`, `config`, `freepool`, `intelligence`, `monitoring`, `providers`, `routing`, `security`, `utils` + 6 modules | **VERIFIED BY RUNTIME** |
| Stock `compress()` is unsuitable — eight grounded findings | prep-02 §1.1 | **INHERITED** |
| Suite state 4 failed / 664 passed / 9 skipped | C-01 §3 | **INHERITED** — no test executed this session |
| All 23 decisions `OUTSTANDING`; no canonical decision covers scorer/provenance choice | T16 §3 master index, all 23 decision questions read | **VERIFIED BY INSPECTION** *(T16 §5–§10 card bodies not read in full this session; a sub-clause there is not excluded)* |
| The vendored scorer is already recorded as the **minimum adapter** and as a `CONDITIONAL` policy item, `disabled-built`, with six enablement proofs | T11 §10 (L253), §5 item 10 (L130) | **VERIFIED BY INSPECTION** |
| *"A recorded selection is not a registration"* is an existing corpus principle; T16 governs register status, the supplement is a separate selection channel, T17 holds no authority | T17 §0 (L10, L14), §A (L30) | **VERIFIED BY INSPECTION** |
| The owner-decision supplement contains **no** BM25 / vendored / compression / R6.4 entry | `grep -n -i` over `r6-owner-decision-supplement-2026-11-04.md` — no output | **VERIFIED BY RUNTIME** |

**The two new observations matter to the selection.** `bm25.py:86–93` and `:80` are behaviour a faithful vendored implementation must consciously **include or omit**. Prefix expansion is a semantic choice, not an implementation detail: it makes `auth` match `authentication` and therefore changes ranking, and it has no counterpart in the textbook Okapi formula. A vendored scorer that omits it is not behaviourally equivalent to the dependency it replaced — which is *acceptable* (the replacement was rejected), but it must be a decision rather than an accident. This record does not make it; it adds it to the list R6.4 owes.

---

## 4. Why vendored — the deciding axes

Compressed from prep-02 §1.2, with the ranking it already states made explicit.

| Axis | Vendored | SDK dependency |
|---|---|---|
| **Boundary** (`CLAUDE.md` §1: *SabiRoute decides. LiteLLM executes.*) | Decision stays in SabiRoute | Decision moves into the engine — **violates §1** |
| Tool injection | None emitted | Injects a tool SabiRoute cannot serve |
| Tokenizer | Unicode + identifier-aware, ours to fix | ASCII-only, upstream's to fix |
| Granularity | Message **and** sentence, structure-aware truncation | Message only, line-based truncation |
| Reproducibility | Pinned in-repo; changes only via our diff | Changes on a `>=1.80.0` MINOR bump |
| Maintenance | ~150–250 lines we own, plus IDF math we must test | Zero code, inherits all eight findings |
| Supply chain | No new dependency | Already a dependency |

**The deciding axis is the first row, not effort.** A compression stage that cannot be audited inside SabiRoute fails CD6's telemetry-correlation requirement before it reaches R6.2–R6.5 at all, and the effort delta is a few hundred lines of textbook arithmetic.

**This does not originate the direction.** Prep-02 §1.2 concluded *"Recommendation: vendored."* T11 went further and recorded it twice: as the **minimum adapter** (§10) and as a `CONDITIONAL` **integration policy** (§5 item 10, `(b′)`), with *zero SDK imports on the request path* marked **VERIFIED**. The chat selection therefore **confirms a direction the freeze package already carries**.

That cuts both ways, and the honest reading is the narrower one. It establishes **consistency** — the operator's direction contradicts no recorded artefact, and no artefact has to be walked back. It does **not** advance S2: a freeze-package record and a register decision are different registers, and neither prep-02's recommendation nor T11's policy item is one of the canonical 23. And it does **not** make the direction unconditional: T11 records it as `CONDITIONAL`, not `FREEZE-OK`, with six enablement proofs outstanding. **A chat confirmation of a conditional policy item leaves the condition exactly where it was.**

---

## 5. Consequences the selection does not settle

Recorded so the next reader does not have to rediscover them.

1. **Prefix expansion and IDF form (§3).** Include the SDK's prefix heuristic and IDF shape, or implement textbook Okapi? Affects ranking output and therefore every R6.4 fixture. **Unresolved by this record.**
2. **The licence question is not answered by choosing to vendor.** Prep-02 §8's P-R6.4 prompt states the requirement: *confirm LiteLLM's `LICENSE` text before transcribing any structure from it.* MIT is recorded as present in the dist-info (**INHERITED**); **the text was not read this session.** Reimplementation-of-design and transcription-of-text are different acts with different obligations, and only the first is unambiguously safe.
3. **The estimator gap is untouched (U-2).** Vendoring makes "two estimators" *fixable*; it does not fix it. The reconciliation rule remains blocked on R6.1 (§9 of prep-02).
4. **The non-Latin gate is not lifted (U-6 / C2).** C2 excludes non-Latin BM25 relevance claims from release until Terminal D establishes a corpus. Vendoring makes the tokenizer *correctable*; it does not make the claim *permissible*, and no result produced by the vendored scorer may be cited as a multilingual claim while C2 stands `OUTSTANDING`.
5. **The package does not exist (U-1).** Naming it is a separate registration act. This record does not name a directory into existence, and §4 of prep-02 lists `request_transform/` provisionally.

---

## 6. What would make it canonical (S2), and what would make it real (S3)

### 6.1 The registration gap

The canonical register holds **23** decisions — A1–A4, B1–B9, C1–C4, D1–D6 — and **none of the 23 asks this question.** The closest is **C2**, which governs *non-Latin BM25 relevance claims* at release, not *where the scorer's code comes from*. B6/B7 are settlement rules the scorer must obey; D3 governs whether `tests/` is writable at all. **None of them is the scorer-provenance decision.**

So S2 cannot be achieved by answering an existing open item. Registration would require an **owner act that creates or amends a register entry** — a new decision, a scope amendment, or a recorded design determination attached to an existing one — with its own ID, wording, options, dependency cell and approval record. **This record proposes none of those, drafts none, and does not choose which shape is right.** It states only that the gap exists and that a chat selection is not a way around it.

### 6.1.1 Which channel would hold the durable record

T17 §0 maps the corpus's channels and their limits: **T16 governs canonical register status**, the 2026-11-04 supplement *"records selections in a channel the register cannot see"*, and T17 itself is a derived view that *"holds no authority and must not be cited as if it did"*. This file is **none of the three** — it exists because no existing channel has a slot for this selection. The supplement was searched and contains **no occurrence** of `BM25`, `vendored`, `compression` or `R6.4` (**VERIFIED BY RUNTIME**), so there is no entry to amend and none was created.

Whether S2 should be reached by a new register decision, a supplement entry, both, or a different instrument is **an owner choice this record does not make** — and note T17's own verdict that the corpus currently has *no specified mechanism* to record an R6.0 closure. That structural gap is larger than this selection and is not addressed here.

### 6.2 The implementation gap

Even with S2 complete, S3 would remain unsatisfied. The gates are prep-02 §7.2's, not this document's:

```
R6.1 settlement contract frozen   NO  — 0 of 23 approved
B5 / B6 / B7                      UNSELECTED / unregistered
F1 / F2 / F3 repaired             NO  — 4 failing tests
D1 / D2 / D3                      UNSELECTED — D3 governs tests/ writability
G7                                NOT GRANTED, not requested
Track A engagement                NOT OBTAINED (one insertion, completions.py:1309–:1345)
Package name registered (U-1)     NO
```

**Enablement is a further gate beyond S3.** T11 §5 item 10 records R6.4 as **disabled-built**, with **six enablement proofs**, a D11 matrix and D8-pairing independence outstanding. Those are not enumerated here and this record does not speak to them. It notes only that **S3 (write the code) and enablement (let it run) are separate acts**, and this selection touches neither.

**The honest reading of S3: not "not yet", but "not reachable from here".** R6.4 is gated behind R6.1 by construction, and this selection changes nothing about that — a scorer choice is not a settlement contract.

### 6.3 Pre-implementation obligations this selection adds

| # | Obligation | Why it attaches to *this* record |
|---|---|---|
| L-1 | Read LiteLLM's `LICENSE` text before transcribing any structure | Prep-02 §8 P-R6.4; not discharged |
| L-2 | Decide prefix expansion and IDF form, and record the decision | §3, §5-1 — discovered here |
| L-3 | Add the "no import of `litellm.compression`" assertion to X-10's network/import test | The selection's whole content is a negative import claim; it must be testable |
| L-4 | State explicitly that vendoring is not an equivalence claim | Omitting prefix expansion makes output differ from the dependency |

---

## 7. What would reverse it

A selection record that cannot be reversed is a decision wearing a weaker title. This one reverses if:

1. **Licence review finds transcription unavoidable and the terms incompatible** — then neither vendoring-by-transcription nor dependency is available, and the scorer question reopens.
2. **Effort is re-estimated beyond the ~150–250-line assumption** such that the boundary argument no longer pays for itself. (Weak: the boundary is the reason, and effort was never the deciding axis.)
3. **The owner registers a different design** — a registered decision outranks a recorded selection by construction, and this file then becomes a record of a superseded direction rather than a live one.
4. **`CLAUDE.md` §1's boundary is amended** such that executing-engine decisions become permissible. No such amendment exists.

Reversal is cheap precisely because S2 has not occurred. **After S2 it stops being cheap, which is the argument for not letting S1 drift into the appearance of S2.**

---

## 8. How a future reader tells the levels apart

Three tests, each answerable from artefacts alone.

| Question | Where to look | What S1-only looks like |
|---|---|---|
| Is there a canonical ID? | T16 §3 master index | **No entry for scorer provenance.** This file is the only artefact. |
| Has an owner responded? | T16 §5–§10 cards, `Owner response:` | All 23 read `PENDING`. |
| May code be written? | prep-02 §7.2 gate table; G7 grant | Every gate `NOT SATISFIED`; no G7. |

If all three answer as above, the selection is **recorded and unregistered**, and any downstream document citing this file must reproduce that qualifier. A later document citing it as "R6.4 decided vendored BM25" without the qualifier is mis-citing this record.

---

## 9. Status

```
SELECTION:  vendored BM25 scorer for R6.4 — S0 chat, 2026-11-05
RECORDED:   this file (S1). 1 file created. 0 modified, 0 staged, 0 committed.
REGISTERED: NO (S2 not performed). Canonical 23 unchanged, all OUTSTANDING.
APPROVED:   NO (S3 not performed, not requestable from this record).
PRIOR ART:  vendored already recorded — T11 §10 minimum adapter, T11 §5-10 CONDITIONAL
            policy (b'), disabled-built, six enablement proofs. This record confirms,
            does not originate, and does not lift the condition.
PRINCIPLE:  "A recorded selection is not a registration" — already corpus law (T17 §A).
CHANNEL:    T16 = register · supplement = selections the register cannot see · T17 = no
            authority · this file = none of the three. Supplement has no R6.4/BM25 entry.
VERIFIED:   litellm 1.103.0 present; scoring/bm25.py read in full (ASCII tokenizer,
            prefix expansion, log IDF form); no request_transform/ in src/; HEAD 319a711e.
INHERITED:  eight stock-compress findings; licence text; suite 4F/664P/9S; gate states.
OPEN:       U-1 package name · U-2 estimator · U-3 marker · U-4 granularity ·
            U-5 k1/b · U-6 non-Latin (C2) · U-7 dedup stub · U-8 telemetry ownership
ADDED:      L-2 (prefix expansion / IDF form), L-3 (import boundary assertion) — new obligations
NEXT:       S2 requires an owner register act; S3 requires R6.1 closure + G7 + Track A.
            Neither is initiated by this document.
```
