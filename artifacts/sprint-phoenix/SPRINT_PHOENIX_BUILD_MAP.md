# SPRINT PHOENIX — The Build Map

**Status:** **LOCKED — OWNER-APPROVED.** Every recommendation below is approved by the owner
(2026-11-16). Approval *of the map* is not approval *of execution* — see §0.3.

| Field | Value |
|---|---|
| Date | 2026-11-16 |
| Branch | `sec/deps-nov` @ `1e69ada9` |
| Documented authoritative branch | `feat/sabiroute-routing-foundation` — **mismatch is finding R-1, unresolved** |
| Consolidates | `docs/build-map.md`, `artifacts/r6-closure/R6_SCORECARD.md` (§3 decisions, §4 findings), `CLAUDE.md` §11, `README.md` roadmap |
| Supersedes | Nothing. This map does not delete or demote any prior record. |
| Author | Claude Code |

> This document authorises nothing by itself. It resolves *what the owner wants to happen and
> what each choice costs*. Every action it lists still crosses an authorization gate in §6.

---

## 0. How to read this map

### 0.1 Evidence labels (repository standard, `CLAUDE.md` §2)

| Label | Meaning |
|---|---|
| `[M]` **Measured** | Re-derived from live bytes / live git state in this session |
| `[R]` **Reported** | Carried from a dated prior record; **not** re-executed here |
| `[I]` **Inferred** | Reasoned from structure; not executed |
| `[?]` **Unverified** | Assumed; no evidence located |

**What was NOT re-executed in this session:** the pytest suite (`663 passed / 9 skipped`,
carried 2026-11-04 `[R]`), the conformance suite (`104 passed / 1 skipped`, carried 2026-11-16
`[R]`), the settlement suite (`6 passed`, carried `[R]`), `ruff`, `mypy`, and any provider,
database or Redis connection. **No row here is `[M]` on the strength of a test run.**

### 0.2 The one distinction this sprint lives or dies on

**Selected ≠ Approved ≠ Implemented ≠ Tested ≠ Independently verified ≠ Gate accepted.**
All 23 T16 cards are *selected*. None is *registered*. Zero are *gate-accepted*.

### 0.3 What this approval does NOT authorise

The owner approved **every recommendation** in §3 and §4. That authorises the *plan*. It does
**not** authorise, and this document does not authorise:

- any `git add`, commit, push, merge, rebase, reset, or branch operation (`CLAUDE.md` §9A);
- instantiating a registration ledger or writing any REG/VER record (F-02's gate);
- making real provider calls;
- training any model (`training_authorized` stays `false`);
- editing any source file under `src/` or `tests/`;
- resolving the origin divergence or the `sec/deps-nov` / `feat/…` branch mismatch (R-1).

Each of those remains a separate act, listed in §6.

---

## 1. STATE OF THE BUILD (current, labelled)

### 1.1 Position

| Fact | Value | Basis |
|---|---|---|
| HEAD | `e0530e5` — *docs: track the R6.0 corpus (42 documents)* | `[M]` |
| Working branch | `sec/deps-nov` | `[M]` |
| Tracked modifications | **1** — `REPORTS-PROVENANCE.md`, insertions only, unstaged (37 insertions after the WO-3 attribution block) | `[M]` |
| Untracked paths | Large; includes `.claude/`, `artifacts/`, and the PHOENIX working files. The `docs/r6-*` corpus is **no longer** untracked | `[M]` |
| Branch vs origin | **DIVERGED both ways.** Origin's unique contribution is narrow: PG CI service, `.env.example` docs, 12 lines of `docs/security.md` | `[R]` 2026-11-04 |
| `docs/r6-*.md` inventory | **42** documents | `[M]` |
| R6 corpus tracked in git | **42 of 42** — F-09 closed 2026-11-16 | `[M]` |
| `REPORTS-MANIFEST.sha256` | 13 entries, all 13 verify `OK` | `[M]` |

**Dated supersession — 2026-11-16 (WO-7).** Superseded values, retained: HEAD was
`1e69ada9`; the untracked-paths row read *"includes the entire `.claude/`, `artifacts/`,
`docs/r6-*` corpus"*; the manifest row carried `[R]`. HEAD advanced to `e0530e5` when the
42-document corpus was committed, which is also what moved the corpus out of the untracked
set. The manifest row is promoted to `[M]` because it was re-verified this session.

### 1.2 The gate that governs everything

> **R6.0 IS NOT CLOSED. R6.0 REGISTRATION IS NO-GO. `G7` IS NOT GRANTED.**

*Original text, retained under dated supersession (see below):*

> Two independent grounds, either sufficient:
>
> 1. **Registration is not executable.** `marker_sha256` and the genesis `entry_sha256` are
>    uncomputable; the registration locus for O1–O5 is undefined (F-01, D-2).
> 2. **Two findings block the closure exit gate.** F-05 (Parts 1–3 stale measurements) and F-06
>    (stale protocol anchors) are OPEN. Definition-of-Done rows 4 and 8 are ❌.

**Dated supersession — 2026-11-16 (WO-2).** Ground 2 above no longer holds as written. F-05 and
F-06 are **CORRECTED** (PH-0), and Definition-of-Done row 4 is now ✅. Row 8 remains ❌, but on
**F-01**, not on F-05/F-06 — so it is no longer independent of ground 1. The "two independent
grounds" framing is withdrawn.

**Current grounds, as re-derived at WO-1:**

1. **Registration is not executable** (unchanged): `marker_sha256` and the genesis
   `entry_sha256` are uncomputable, and the O1–O5 registration locus is undefined — **F-01**,
   awaiting owner decision **D-2** (signature item S-1).
2. **D-4 remains undecided.** The privacy/evidence exception question is **OUTSTANDING** — the
   build map records only a recommendation. DoD row 6 stays ⚠️.
3. **Owner acts outstanding.** BL-22 unsigned (DoD row 9) and G7 not granted (DoD row 10).

The digest layer itself is mechanically sound — **105** conformance assertions pass (81 at the
2026-11-09 baseline). **This is not a finding that the work is wrong.** The remaining distance is
owner-time and repository-time.

### 1.3 Phase status — carried, not re-derived

Nine phases read "Complete", eleven "Planned"/"In progress". **No phase has been re-verified at
`1e69ada9`.** The 2026-11-04 measurement predates HEAD. Read the gap, not the status word.

| Phase | Status | The gap that keeps it from Complete |
|---:|---|---|
| 00 Architecture | Complete | — |
| 01 LiteLLM gateway | Complete | Fallback is test-only; no live failure injection |
| 02 Provider expansion | In progress | 3 of 14 aliases have runtime evidence |
| 03 Model registry | Complete | — |
| 04 Virtual models | Complete | — |
| 05 Fallback engine | Implemented | No live failure-injection evidence |
| 06 Health monitoring | Implemented | Passive cooldown only; checker removed |
| 07 Observability | Implemented | No stored failure-metric evidence |
| 08 PostgreSQL | Complete | Managed PG never exercised |
| 09 Auth & API keys | Complete | — |
| 10 Budgets & rate limits | Implemented | Live rejection paths never exercised |
| 11 Capability routing | Implemented | Capability evidence missing for 11 of 14 |
| 12 Deterministic scoring | Implemented | Benchmark evidence synthetic; signals process-local |
| 13 ML-assisted routing | In progress | 13.2 closure pending; **13.3 blocked** |
| 14 Benchmarking | Planned | — |
| 15 Admin dashboard | Planned | — |
| 16 Remote access | Planned | — |
| 17 Security hardening | Planned | — |
| 18 Testing & regression | Planned | — |
| 19 CI/CD | Implemented | Hosted Actions run never verified |
| 20 Production | Planned | — |

### 1.4 Known-invalid claims — carry as invalid

- Aggregate dataset integrity: **FAILED.** One count mismatch, one outcome without a snapshot,
  deliberately unrepaired.
- Training blocked: no outcome variation, 2 of 6 provenances verified, no defensible split.
- No model trained or deployed.
- `api/completions.py` (2,136 lines) carries four responsibilities — structural risk, not a defect.

---

## 2. THE P0 DEFECT LANE (unchanged by this sprint)

```
P0-1 BYOK-0        NOT STARTED / NOT AUTHORISED
     Exact top-level fields api_key, api_base, authorization.
     Position: after auth + F-05 caps, BEFORE request_id and create_usage_event.
     HTTP 400, invalid_request_error, generic, non-echoing.
     Prove zero: usage rows · reservations · snapshots · rate tokens · provider calls · leakage.

P0-2 MIGRATION SAFETY PROOF    NEXT — READ-ONLY, NOT AUTHORISED TO BEGIN
     SQLite and PostgreSQL analysed SEPARATELY.
     Critical gate: two simultaneous initializers → one backfill owner,
     no escaped IntegrityError, one ledger entry.  UNPROVEN for both dialects.

P0-3 ACCOUNTING CONTINUITY     BLOCKED on P0-2
```

**Sprint PHOENIX does not reorder this lane.** It runs beside it.

---

## 3. OWNER-ONLY DECISIONS — recommendation + tradeoff

Every recommendation here is **approved**. Each carries its cost, because a recommendation
without its tradeoff is marketing.

---

### D-1 · Formal approval for the 23 T16 cards

**Recommendation.** Approve all 23 as **one dated owner attestation**, recorded as a single
registration act — not 23 separate acts.

**Why.** All 23 were already individually answered. Per-card re-approval adds owner hours without
adding information; the selections are on the record and unchanged.

**TRADEOFF — what you give up.** Block approval **collapses granularity**. If one card is wrong,
the whole block is compromised and correcting it is a public retraction rather than a quiet fix.
Per-card approval is 23× the owner time but localises error. Block approval is also harder to
someone auditing later — "which card did they actually think about?" becomes unanswerable.

**Cost to reverse.** Low while uncommitted; high once a REG marker binds the block digest.

---

### D-2 · Registration locus for O1–O5

**Recommendation.** Designate **one existing, already-tracked document** as the sole registration
locus, named explicitly in the protocol — do **not** create a new file.

**Why.** A new file becomes the 43rd artifact, re-opens the closed 42-doc / 13-entry
reconciliation that WP-3 spent a packet settling, and needs its own digest. An existing tracked
document adds no inventory surface.

**TRADEOFF — what you give up.** Coupling the register to document prose means the register moves
whenever the prose moves — and **the prose is already drifting** (F-06: six stale anchor sets).
You are binding a permanent, digest-verified record to a line-numbered surface that has failed
line-numbering twice. The new-file option is inventory-expensive but *anchor-stable*.

**Cost to reverse.** Choosing the locus is cheap; changing it after the first REG marker exists
invalidates every digest that followed.

---

### D-3 · Conflicting legacy budget limits

**Recommendation.** **Defer to R6.1** with a written precedence rule — "the original reservation
estimate governs; a legacy numeric limit that conflicts is superseded, not reconciled" — rather
than picking numbers now.

**Why.** The conflict is not yet load-bearing. Picking numbers now requires deciding settlement
semantics that P0-3 has not yet settled; you would be pre-empting a blocked lane.

**TRADEOFF — what you give up.** You carry a **known ambiguity into implementation**. It can
surface later as a settlement discrepancy that looks like a bug but is a documented deferral —
and by then the code will encode one reading implicitly. The three-line precedence rule is not
free: a reader may mistake it for a resolution.

**Cost to reverse.** Cheap now, expensive once code depends on the precedence rule.

---

### D-4 · Privacy / evidence exceptions (P-6)

**Recommendation.** **No exceptions.** Keep the prohibition on prompt-text logging and
persistence absolute — including for compression-fidelity debugging.

**Why.** The single most likely accidental disclosure path in the R6 design is
`CompressedResult["cache"]`, which returns **full original message text** (`compress.py:493-494`,
E12). One exception creates the precedent and the code path.

**TRADEOFF — what you give up.** You lose **hard debuggability** of compression fidelity. When a
transform degrades an answer, you cannot see the before/after text — you get digests and token
counts only. Debugging becomes inference rather than inspection, and some classes of semantic
erosion will be undiagnosable in production.

**Cost to reverse.** An exception, once granted, is effectively permanent — revoking it later
means auditing whatever was retained.

---

### D-5 · BL-22 signature

**Recommendation.** **Withhold** the signature until F-05 and F-06 are resolved or explicitly
owner-accepted in writing.

**Why.** Definition of Done row 8 requires blocking findings resolved *or* explicitly accepted.
Signing before either makes BL-22 attest to a record containing known-stale measurements.

**TRADEOFF — what you give up.** Calendar time. The closure date slips by the length of the F-05/
F-06 correction pass. If you sign now, R6.0 closure unblocks immediately — at the price of an
owner signature standing over a document that says things that are not true.

**Cost to reverse.** A signature is the highest-cost thing to withdraw in this repository.

---

### D-6 · G7 grant

**Recommendation.** **Do not grant G7 now.**

**Why.** G7 *is* the gate. Granting it before the gate's own exit conditions are met converts it
from a gate into a formality, and every later gate inherits the reduced standard.

**TRADEOFF — what you give up.** R6.1 stays blocked. That is the entire cost, and it is
deliberate. The alternative — grant early to buy velocity — buys speed by spending the gate's
credibility, which cannot be repurchased.

**Cost to reverse.** G7 cannot be un-granted without recording a retraction.

---

### D-7 · Authority to implement R6.1–R6.7

**Recommendation.** Grant **in tranches, R6.1 only first.** Authority for R6.2 renews only after
R6.1's exit evidence is accepted.

**Why.** R6.2–R6.7 each depend on R6.1's immutable-original-request contract. Authorising seven
phases against an unproven foundation authorises six phases whose prerequisite does not exist.

**TRADEOFF — what you give up.** **Repeated owner acts** — up to seven, not one. Each tranche
boundary is a pause. If R6.1 lands clean, the tranche structure will feel like friction with no
payoff. Blanket authorization is one act and moves faster; it also pre-commits you to six phases
whose design is currently blocked (D-2, F-01, F-06).

**Cost to reverse.** Tranche boundaries are cheap. A blanket grant is expensive to narrow.

---

### D-8 · Migration / deployment / production / customer-facing claims

**Recommendation.** **Prohibited** until R6.7 and production-grade evidence exist. No exceptions
for internal drafts labelled "preliminary".

**Why.** Configured ≠ installed ≠ reachable ≠ working ≠ tested ≠ production-ready. Draft claims
leak into slides and get quoted.

**TRADEOFF — what you give up.** Almost nothing operationally — it costs only the ability to
describe the system aspirationally. The real cost is that stakeholders reading internal docs will
see no forward claim at all and may read the project as stalled.

**Cost to reverse.** None; the claim ban simply lifts when evidence arrives.

---

### D-9 · Origin divergence and branch mismatch (R-1) — **added to the D-list by this map**

**Recommendation.** **Report, do not resolve.** The owner must decide the target branch separately.

**Why.** `CLAUDE.md` §9A forbids merge/rebase/force-push without explicit authorization, and every
phase record is attributed to `feat/sabiroute-routing-foundation` while work happens on
`sec/deps-nov`. Resolving it silently would rewrite attribution for the whole phase table.

**TRADEOFF — what you give up.** Every record written between now and resolution is attributed to
a branch that is not the one being built on — the attribution debt compounds. Resolving now is
expensive and risky; deferring is free today and costlier every week.

**Cost to reverse.** Low while nothing new is committed; rises with every commit on `sec/deps-nov`.

---

## 4. OPEN FINDINGS — disposition + recommendation + tradeoff

### 4.1 The two the owner named

---

#### **F-02 — skipped test `test_u11_genesis_entry_hash_is_computable`**

**Current status:** `BLOCKED, NOT A PASS`. Gate: no ledger may be instantiated without separate
first-execution authority.

**RECOMMENDATION (approved).** Split the finding in two and treat each half differently:

1. **Keep the live test skipped.** Do **not** instantiate a registration ledger. The skip is the
   protocol correctly asserting its own incompleteness — it is not a defect to be cleared.
2. **Add one synthetic-fixture proof that instantiates nothing.** A test that feeds a fabricated
   in-memory entry through the genesis-hash function and asserts determinism, totality, and
   sensitivity to each field. This exercises the **arithmetic** without creating any REG/VER
   record, any ledger file, or any chain head.

Resulting disposition: **F-02 becomes `PARTIALLY PROVEN`** — the hash function is proven; the
real genesis hash is **not** and stays gated on WP-5.

**TRADEOFF — what you give up.**

- **It does not close F-02.** You trade a clean "blocked" for a messier "partially proven", and a
  careless reader will read the green synthetic test as closure. The label must be defended in
  every later document.
- **It costs a new test file** under `tests/`, which is a source edit requiring its own
  authorization — so F-02's "improvement" is itself gated.
- **The synthetic fixture can drift** from the real schema. If the real entry shape changes, the
  synthetic proof keeps passing while proving something that no longer exists.
- **Against the alternative:** granting first-execution authority for a disposable ledger would
  fully un-skip the test — but it crosses the exact boundary the protocol exists to protect, and
  a "disposable" ledger is one directory-path mistake from being the real one.

---

#### **F-09 — R6 corpus untracked, 0 of 42 documents in git**

**EXECUTED 2026-11-16 — F-09 CLOSED.** PH-2 steps 5.6 and 5.7 ran. The 42 documents were staged
by explicit path, the staged diff was inspected (0 paths outside `docs/r6-*.md`), and committed
as `e0530e5`. Re-derived after the commit: **42 of 42 tracked** `[M]`; `REPORTS-MANIFEST.sha256`
13/13 verify `[M]`. The recommendation below is retained as the plan of record; the exposure it
describes is now retired.

**Owner note:** the machine will not die, so the durability risk is **accepted by the owner** and
does not drive urgency.

**RECOMMENDATION (approved).** Add corpus tracking to the plan as a **gated, later step** —
sequenced **after** the F-05/F-06 corrections, never before:

- **Step F-09.1** — correct F-05 and F-06 in place (supersede, do not rewrite).
- **Step F-09.2** — stage the 42 documents **explicitly, by path** (`git add <path>` ×42, never
  `git add .` or `-A`), inspect the full staged diff, commit.
- **Step F-09.3** — re-derive the 42-doc inventory and the manifest count after the commit, and
  record the new baseline.

**Why after, not before.** Tracking is what makes a record durable. Tracking a record that still
contains known-false text makes the false text durable too — and history is much harder to correct
than a working tree.

**TRADEOFF — what you give up.**

- **The corpus stays destroyable until F-09.2.** The owner has judged this acceptable ("the
  machine won't die"); the residual exposure is a stray `git clean -fdx`, not hardware failure.
- **Sequencing behind F-05/F-06 costs time** and means the durability win arrives later.
- **Against the alternative (track now):** earlier durability, but it commits Parts 1–3 carrying
  stale measurements — you bake F-05 into git history, and later corrections must be visible
  amendments rather than clean first commits.
- **Against the alternative (track only the corrected docs now):** avoids the stale-content
  problem but leaves a **split corpus** — some tracked, some not — which is worse than either
  clean state and will make the 42-count question unanswerable.
- **One commit of 42 files** is a large, review-hostile diff. A reviewer cannot meaningfully
  inspect it, so "reviewed the staged diff" becomes procedural rather than real.

---

### 4.2 The rest of the register — disposition table

| ID | Finding | Recommendation | Tradeoff |
|---|---|---|---|
| **F-01** | Registration locus for O1–O5 undefined | Resolve as **D-2** before any REG act | Locus choice binds all later digests (see D-2) |
| **F-03** | `03b-r1.md:213` still reads `VER:v1` | Correct under the F-06 pass, inside the authorised anchor | Widening the E3 anchor to reach it is itself an unauthorised edit |
| **F-04** | Correction proposal `:885` "NOT OWNER-APPROVED" | Correct in the same pass; D12 authorises the `:3` banner only | Bundling corrections risks scope creep in one edit |
| **F-05** | Parts 1–3 stale measurements, no supersession | **Correct by dated supersession** — do not rewrite history | Adds amendment noise; old numbers remain visible |
| **F-06** | Addendum §12 stale anchors; Part 2 off-by-one | **Correct anchors to live line numbers**; re-verify each | Anchors will drift again on the next edit — this recurs |
| **F-07** | `:223` asserts zero O5, superseded at `:225-239` | **No action** — accepted by design | None; supersession is the stated convention |
| **F-08** | Untracked drift 146 → 147 → 149 | **Preserve, record, do not explain by assumption** | The gap stays permanently unexplained in the record |
| **F-10** | No separately hashed owner-decision record for R1 | Record as pre-existing gap; fold into WP-5 pack | Adds an item to an already-blocked gate |
| **F-11** | Copilot did not search for O6–O8 or ledger artifacts | **Treat absence as UNVERIFIED, never as absence** | An unverified absence claim can hide a real artefact |
| **F-12** | Three-way digest coupling unaccounted for | Record in the WP-5 pack; do not model it yet | Unmodelled coupling can produce a silent digest mismatch |

### 4.3 Current count

**12 findings: 2 blocking (F-01, F-02), 4 corrected (F-03, F-04, F-05, F-06), 1 closed
(F-09, 2026-11-16), 1 recorded (F-12), 1 accepted-by-design (F-07), 1
preserved-unexplained (F-08), 1 open-gap (F-10), 1 unverified (F-11).**

> **Correction 2026-11-16 — reclassification withdrawn.** An earlier edit this session moved
> F-02 from *blocking* to *partially proven*, reducing the blocking set to F-01 alone. That
> reclassification was **not authorised and is withdrawn**. F-02's scorecard status is
> `PARTIALLY PROVEN — NOT CLOSED`; "partially proven" describes its **evidence state**, it
> does not remove it from the blocking set. **Whether F-02 should remain blocking is an owner
> ruling, not a registrar edit.** Until that ruling, the original classification stands.
>
> The status updates for F-03–F-06 (corrected) and F-09 (closed) are **retained** — those
> reflect the scorecard's findings table and are not in dispute. Only the F-02 move is
> withdrawn.

---

## 5. SPRINT PHOENIX — SEQUENCE

Ordered by dependency clearance. **Every block is gated in §6.**

```
PH-0  R6.0 CLOSURE CORRECTION                          [gate: owner]
      5.1  Correct F-05 (Parts 1–3 supersession) + F-06 (anchors) + F-03 + F-04
      5.2  Re-run conformance + settlement suites; record exact output
      5.3  Re-measure the §1.1 baseline table; promote [R] → [M]
      EXIT: DoD rows 4 and 8 become ✅

PH-1  REGISTRATION LOCUS + MARKER DEFINITION            [gate: owner]
      5.4  Designate the locus (D-2) and adopt reading R-A for U4
      5.5  Re-computable marker_sha256; owner_sha256 boundary answered (O3)
      EXIT: F-01 cleared; registration becomes executable

PH-2  CORPUS DURABILITY                                 [gate: owner]
      5.6  F-09.2 — stage 42 docs by explicit path, inspect diff, commit
      5.7  F-09.3 — re-derive inventory + manifest count
      EXIT: R6.0-D step 2 met; F-09 closed

PH-3  F-02 PARTIAL PROOF   (independent of PH-0..PH-2)  [gate: owner]
      5.8  Synthetic-fixture genesis-hash test; no ledger instantiated
      EXIT: F-02 → PARTIALLY PROVEN; live test still skipped by design

PH-4  WP-5 OWNER CLOSURE DECISION PACK                  [gate: owner]
      5.9  BL-22 (D-5) · G7 (D-6) · R6.1 authority (D-7)
      EXIT: R6.0 CLOSED — or explicitly held open

PH-5  R6.1 FOUNDATION                                   [gate: owner]
      5.10 Immutable original request · canonical representation · metadata
           · policy/capability checks precede transformation · explicit bypass
      EXIT: contract implemented, tested, and reviewed

PH-6  R6.2 … R6.7                                       [gate: owner, per tranche]
      Not scoped further here. Each renews on the prior exit.
```

**Runs in parallel, permanently:** the P0 lane (§2). Sprint PHOENIX does **not** block P0-2.

---

## 6. AUTHORIZATION LEDGER

| # | Action | Authorised? |
|---|---|---|
| 1 | Correct F-03/F-04/F-05/F-06 in place | **No — recommendation approved, act not granted** |
| 2 | Re-run test suites and record output | **No** |
| 3 | Designate the O1–O5 registration locus (D-2) | **No** |
| 4 | Adopt U4 reading R-A | **No** |
| 5 | Compute `marker_sha256` / answer O3 | **No** |
| 6 | Stage and commit the 42-doc corpus (F-09.2) | **YES — owner, 2026-11-16.** Conditional: only after PH-0 corrections are verified and every suite is green |
| 7 | Add the synthetic genesis-hash test (F-02) | **No** |
| 8 | Instantiate any registration ledger | **No — permanently gated** |
| 9 | Sign BL-22 (D-5) | **No** |
| 10 | Grant G7 (D-6) | **No** |
| 11 | Authorise R6.1 (D-7) | **No** |
| 12 | Begin P0-2 read-only migration proof | **No** |
| 13 | Implement BYOK-0 (P0-1) | **No** |
| 14 | Make real provider calls (Phase 02) | **No** |
| 15 | Push / merge / resolve origin divergence / R-1 | **No** |
| 16 | Train any model | **No** |

**Posture at this baseline: prove, report, wait.**

### 6.1 Authorization amendments

| Date | Row | Amendment | Basis |
|---|---:|---|---|
| 2026-11-16 | 6 | `No` → **YES**, conditional on green suites | Owner: *"yes, that makes sense"* — authorising the 42-doc corpus commit to run after PH-0 verification in the same execution |

**Rows 1, 2, 6 and 7 are now granted.** Rows 3, 4, 5, 8–16 remain **No**. Row 8 (ledger
instantiation) stays gated regardless of anything else in this map.

---

## 7. TRADEOFF SUMMARY — the costs in one place

| Decision | Chosen | The thing you give up |
|---|---|---|
| D-1 | Block-approve 23 cards | Per-card granularity; error localisation |
| D-2 | Existing tracked doc as locus | Anchor stability — bound to a surface that has drifted twice |
| D-3 | Defer budget conflict to R6.1 | A known ambiguity carried into code |
| D-4 | No privacy exceptions | Hard debuggability of compression fidelity |
| D-5 | Withhold BL-22 | Calendar time on closure |
| D-6 | Do not grant G7 | R6.1 velocity |
| D-7 | Tranche R6.1 first | Up to seven owner acts instead of one |
| D-8 | No production claims | Stakeholder legibility (reads as stalled) |
| D-9 | Report, don't resolve R-1 | Compounding attribution debt |
| F-02 | Partial proof, no ledger | A messier status; a test edit; possible fixture drift |
| F-05/06 | Supersede in place | Amendment noise; recurrence on next edit |
| F-09 | Track *after* correction | Later durability; residual `git clean` exposure |

**The single largest tradeoff in this map: D-7 and D-6 together cost calendar time in exchange for
keeping the gate meaningful.** If that exchange is wrong, it is wrong in one direction only — you
will have been slower than necessary, not looser than safe.

---

## 8. CURRENT PROJECT STATUS

```
CURRENT GATE:   WP-4 findings outstanding; WP-5 not started; R6.0 OPEN
CURRENT PHASE:  R6.0 closure — R6.1–R6.7 NOT AUTHORISED
PROVEN:         104 conformance passes · 6 settlement passes · 13/13 manifest · 42-doc
                inventory · digest layer mechanically sound
UNPROVEN:       live test suite at 1e69ada9 · O6–O8 absence · drift attribution (F-08)
                · genesis hash (F-02) · both-dialect migration
                safety · every live provider path beyond 3 of 14
BLOCKED BY:     F-01 (O1–O5 locus) · F-02 (ledger authority) · F-05/F-06 (stale record)
                · D-5 · D-6
NEXT:           PH-0 — owner-authorised F-05/F-06 correction pass, then re-run evidence
```

---

*End of Build Map. §3 and §4 are approved. §6 is not. The gap between those two sentences is the
whole discipline.*
