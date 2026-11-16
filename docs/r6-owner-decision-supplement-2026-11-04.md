# R6 Owner-Decision Supplement — 2026-11-04 In-Session Selections

**Terminal:** F
**Document type:** Append-only supplemental owner-decision record
**Created:** 2026-11-04 decision session; recorded under Terminal F Prompt 1
**Repository state at creation:** `feat/sabiroute-routing-foundation` @ `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
**Source session:** `<owner-session-id>`
**Governance status:** `RECORDED — NOT REGISTERED — NO GATE CLEARANCE`

**Amended:** 2026-11-04 under owner authorisation — Terminal G audit Conditions 1 and 2 applied only. Condition 1 reclassifies the Q5 source (§5.5, §6.3, appendix, §8.8) from `EXACT OWNER` to `MISSION-FRAMED`. Condition 2 corrects the D-register analysis (§7.5). No other content, status, count, gate or decision was altered. Conditions 3 and 4 of that audit were **explicitly excluded** and remain unapplied.

---

## 1. Purpose and authority

This document preserves, in durable form, owner selections that were made **in session** on 2026-11-04 during the T19A architecture-resolution session and were, until now, recorded nowhere in the repository.

It is a supplement to the existing R6 record set. Specifically:

- It is a **supplemental record, not a replacement for T16**. The T16 decision option register remains the canonical register of record.
- It **does not rewrite historical decision statuses.** Every T16 A/B card continues to read exactly as it did before this document was created.
- It **does not grant implementation authority or gate clearance.** Recording a selection is not gate acceptance.
- It **does not itself constitute BL-22**, nor any part of BL-22's signature basis.
- It **does not close R6.0.**

Recording is not approval. This operation did not authorise, and must not be read as authorising: R6.1 implementation, settlement remediation, BL-22 signature, G7, Track A, benchmark execution, provider calls or spend, database migrations, commits, pushes, deployment, or release.

---

## 2. Evidence and provenance

### 2.1 Repository identity (verified live before writing)

| Fact | Verified value |
|---|---|
| Repository root | `<repo-root>` |
| Branch | `feat/sabiroute-routing-foundation` |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` |
| Upstream | `origin/feat/sabiroute-routing-foundation` |
| Divergence (upstream…HEAD) | 3 behind / 6 ahead |
| Tracked worktree | clean (0 modifications) |
| Untracked files | 1354, all preserved untouched |
| Canonical register | `docs/r6-t16-r6-decision-option-register.md`, unmodified |

The historical baseline carried into this mission (branch `feat/sabiroute-routing-foundation`, HEAD `319a711`) **matched** the live state on re-verification. No stash, stage, commit, push, branch switch, or destructive Git operation was performed.

### 2.2 Transcript identity

| Fact | Verified value |
|---|---|
| Path | `<owner-session-transcript>` |
| Session ID | `<owner-session-id>` |
| Length | 3508 lines |
| Inspection method | Direct read of the JSONL message envelopes (role, timestamp, content) — not the Terminal G summary, not the Terminal A report |

All ten referenced lines resolve inside the file, and each was read directly. Content below is quoted from those envelopes.

### 2.3 Line-number convention

Line numbers in this document are **1-based on the transcript file as it exists today**. The earlier Terminal A recovery report (transcript line 3501) cites the same messages at a consistently **one-lower** index (e.g. its 2804 / 2873 / 2934 / 2965 / 3158 / 3166 / 3367 correspond to this document's 2805 / 2874 / 2935 / 2966 / 3159 / 3167 / 3368). The offset is uniform and the timestamps agree exactly, so the two numbering schemes identify the same messages. No content conflict exists; only the index base differs.

### 2.4 Source classification used throughout

| Class | Meaning |
|---|---|
| `EXACT OWNER` | Verbatim text submitted by the owner as `pasted_content` |
| `MISSION-FRAMED` | A mission prompt that *asserts* a prior owner approval; not the owner's own decision utterance |
| `ASSISTANT` | Assistant framing, question, recommendation, or summary — never a decision |
| `PARAPHRASE` | Third-party summary of decisions; not source |
| `MISSING` | Not recovered verbatim from any transcript inspected |

Provenance note: eight of the ten sources below are `pasted_content` submitted by the owner — **pasted text, not direct free-text typing**; the remaining two (lines 3359 and 3501) are `ASSISTANT`. This distinction is preserved deliberately. Nothing here should be described as the owner's free-text wording where the source was a pasted block.

### 2.5 Four distinct states

This document keeps four states separate, and does not allow one to imply another:

1. **In-session selection** — the owner chose an option in the decision session.
2. **Durable recording** — the selection is written to a repository document (this one, for three selections).
3. **Canonical registration** — the selection is reflected in the T16 register's `Owner response` / `Approval record` fields. **None is.**
4. **Gate acceptance** — a gate (G7, Track A, BL-22, R6.1) is cleared. **None is.**

---

## 3. The three verified canonical selections

Each selection below maps to an existing T16 canonical card. None of them changes that card.

### 3.1 A3 — Option A (source-limited)

**T16 mapping:** `A3 — Adopt ADR-1 (Telemetry)`
**Transcript reference:** line 2805, `ts=2026-11-04T16:59:07.704Z`
**Source class:** `MISSION-FRAMED` ⚠ — see the provenance warning below.

Owner position as recorded in the session:

> **A3 — Option A:** Adopt ADR-1 as the conditional target architecture, explicitly not implemented, with P1–P5 prerequisites unmet.

The approved target remains a separate, content-free optimisation-record table:

- Table: `sabiroute_optimization_records`
- Primary key: `(request_id, attempt_number)`
- `key_id` and `project_id` required and non-null
- Scalar, enum and identifier fields only
- Frozen builder with `extra="forbid"`
- No prompt text or message content persisted

Retained qualifications, preserved without abbreviation:

- P1–P5 remain unmet until independently verified and closed.
- No implementation is authorised.
- No schema migration is authorised.
- No writer, builder, projection or table is to be created.
- No G7, Track A, BL-22 signature or implementation gate is granted by A3.
- Conditional adoption does not mean the prerequisites are satisfied.
- The current inline fail-closed telemetry on the accounting row remains **interim** behaviour and must not be represented as the approved final architecture.

**⚠ Provenance warning — unresolved.** Line 2805 is not the owner's own decision utterance. It is a continuation mission prompt whose body asserts *"The owner has now explicitly approved: A3: Option A"*, and which then instructs that the qualified position be recorded.

> "The original direct A3 owner utterance … predates the recoverable window and was not re-extracted verbatim in this pass." — transcript line 3501 (`ASSISTANT`, Terminal A recovery report)

The direct A3 utterance with its own timestamp is `MISSING` from every transcript inspected. A3 is recorded here on a mission-carried assertion, **not** on a located owner message. It must not be upgraded to `EXACT OWNER` status, and line 2805 must not be cited as the owner utterance itself. Whether A3 requires independent owner re-confirmation is left **unresolved** (§8.2).

### 3.2 B1 — Option A (package conflict resolved)

**T16 mapping:** `B1 — Adopt ADR-2 (R6.1 Foundation Contract)`
**Transcript reference:** line 2716, `ts=2026-11-04T16:25:06.624Z`
**Source class:** `EXACT OWNER`

Owner decision:

> B1: Option A — adopt ADR-2 (T11 §8, I1–I9) as the draft R6.1 foundation contract, with the package-name conflict resolved to `src/sabiroute/request_transform/`.
>
> C-02: Reading B — Group A plus all of Group B (B1–B9) must be recorded before BL-22 is signed.

Retained qualifications, verbatim:

- "This adopts the draft contract; it does not authorise implementation."
- "I2's latency/byte budget and I5's configuration schema remain unresolved design requirements and must be closed before R6.1 implementation."
- "This decision does not grant G7 or Track A authorisation."

**C-1 package resolution:** the `ADR-2/C-1` versus `GROUP-C/C1` identifier conflict is resolved to the package `src/sabiroute/request_transform/`. This is a package-boundary resolution only; it does not settle the separate identifier-collision question raised at T16 §7.

### 3.3 B6 — Option A (monotone-shrink permanent)

**T16 mapping:** `B6 — Monotone-shrink permanent unless re-baselined`
**Transcript reference:** line 3167, `ts=2026-11-04T17:57:42.499Z` (submitted as "Q4")
**Source class:** `EXACT OWNER`

Owner decision:

> Q4: APPROVE Option A — B6 monotone-shrink permanent unless the reservation is explicitly re-baselined.

All seven boundary conditions, preserved:

1. The original reservation estimate remains the authoritative upper bound on the effective request throughout transformation and optimisation.
2. Any transformation that would increase the effective request beyond the reserved bound must be rejected unless an explicit, auditable re-baselining operation has occurred.
3. Re-baselining must not be implicit, silent, or performed merely because a later transformation produces a larger estimate.
4. Re-baselining must have its own defined authority, accounting semantics, failure behaviour, and evidence requirements. This decision does not design or implement that mechanism.
5. B6 remains independent of B7. Do not combine their decisions.
6. Preserve the existing B5 settlement requirements. B6 does not weaken unknown-usage handling or settlement integrity for either budget or quota.
7. This is an in-session owner decision only, subject to durable recording and R6.0 governance.

Also stated: the decision does not authorise implementation, schema changes, migrations, benchmark execution, provider calls, G7, Track A, BL-22, or R6.1–R6.7 execution.

**Note.** Condition 6 is load-bearing: **B6 does not decide B5** and must not be used to infer B5 (see §7.2).

---

## 4. C-02 — Reading B

**Transcript reference:** line 2716, `ts=2026-11-04T16:25:06.624Z` (same owner submission as B1)
**Source class:** `EXACT OWNER`

Selected reading, verbatim:

> C-02: Reading B — Group A plus all of Group B (B1–B9) must be recorded before BL-22 is signed.

### 4.1 What this requires

Every Group A decision and every Group B decision must be **recorded** before BL-22 is signed. The identification of *which* decisions is unambiguous and comes from the register itself:

- Group A: `A1, A2, A3, A4` — 4 decisions (T16 §4)
- Group B: `B1 … B9` — 9 decisions (T16 §5)
- **Total: 13 canonical decisions**

### 4.2 Where the session stands against that requirement

| Measure | Count |
|---|---|
| Canonical decisions in scope (Group A + Group B) | **13** |
| Evidenced as selected in session | **3** — A3, B1, B6 |
| Outstanding / unselected | **10** — A1, A2, A4, B2, B3, B4, B5, B7, B8, B9 |
| Durably recorded **before** this document | **0** |
| Durably recorded **by** this document | **3** — A3, B1, B6 |
| Canonically **registered** in T16 | **0** |

Recording these three does **not** satisfy BL-22, and does not narrow the BL-22 requirement to the remaining ten. BL-22 additionally depends on the whole Group B set being genuinely decided, including B5, which remains open (§7.2).

### 4.3 ⚠ Decision-count discrepancy — unresolved

The authorising mission brief states that C-02 Reading B requires *"12 canonical decisions: A1–A4 and B1–B9"*, with *"nine"* remaining unselected, while separately warning not to conflate the *"13-item inventory, which includes additional Group D decisions"*.

That reconciliation does not close:

- `A1–A4` is **4** decisions and `B1–B9` is **9**; the register (T16 §4, §5) enumerates exactly those **13** cards, every one reading `PENDING` / `NOT APPROVED`.
- 13 total minus 3 selected leaves **10**, not 9. The brief's own outstanding list names **ten** identifiers, consistent with 10.
- The "13-item inventory" the brief sets aside as *including Group D* cannot be the 13 A/B cards; the A/B set is already 13 before any Group D decision is counted.

Position taken in this record: **the operative rule is unambiguous — all of Group A plus all of Group B — and that set contains 13 decisions, 10 of which remain unselected.** The integer *"12"* in the mission brief is recorded here as a miscount and is **not** adopted. It is not silently corrected into the governance record either: the arithmetic is an open owner/register question, flagged in §8.1, because it determines the BL-22 discharge count. No decision here depends on choosing 12 over 13 — the substantive requirement is identical either way.

---

## 5. Non-canonical decisions and clarifications

The items below were raised, selected or clarified in session. Each carries the source class shown on its own entry — `EXACT OWNER`, `MISSION-FRAMED`, or `ASSISTANT` — and the three mean different things: an **owner selection**, a **mission-framed assertion**, and **assistant framing** are not interchangeable, and a mission-framed assertion is **not** an independently verified owner decision (§2.4). **None of these items maps to a canonical T16 A/B decision ID**; they are recorded separately, are not forced into the register, and confer no authority of their own.

### 5.1 RTK architecture — Option C, two-stage

**Line 2874**, `ts=2026-11-04T17:04:33.863Z`, `EXACT OWNER`.

> RTK: Option C — two-stage.

Substance, preserved:

1. R6.2's initial deliverable is stateless, within-request deduplication — a deterministic, pure request transformation under `src/sabiroute/request_transform/`, preserving semantic correctness, original-request immutability and fail-closed behaviour. **No** cross-request state, prompt retention, TTL or invalidation mechanism is authorised in this first stage.
2. Cross-request caching is deferred to a separately gated future capability; it must not be silently treated as implemented or as equivalent to within-request deduplication.
3. R6.2 exit criteria must be amended to distinguish **R6.2-A** (stateless within-request deduplication, with correctness / semantic-preservation / determinism / bypass / representative-workload evidence) from **R6.2-B** (cross-request cache feasibility and implementation, requiring a separate owner decision and authorisation).
4. R6.2-B may re-enter only after representative SabiRoute traffic demonstrates material cross-request repetition, and a feasibility package establishes provider-side caching overlap, tenant/policy isolation, retention boundaries, invalidation correctness, collision resistance, operational cost and measurable incremental benefit.
5. Neither stage is implemented by this decision; roadmap, ADRs, discovery packet and source files are not edited by it.

Stated boundary: "This is an architecture decision, not G7, Track A, BL-22 or implementation authorisation."

**Canonical status:** non-canonical. No valid mapping to a T16 A/B card has been demonstrated, and none is asserted here. **Canonical mapping is unresolved (§8.5).**

**Provenance note:** the Terminal A report records this paste as duplicated at consecutive lines, one of which carries no timestamp. The timed copy is line 2874 above.

### 5.2 Seven-mode vocabulary — retained as non-binding terminology

**Line 2935**, `ts=2026-11-04T17:25:46.094Z`, `EXACT OWNER`.

> B — retain the seven labels as non-binding discovery terminology, with the explicit guard that they are NOT approved API or configuration values and cannot become implementation policy without a new owner decision.

Substance, preserved:

- Future `OptimizationPolicy` under I5 must distinguish enablement, intensity, technique, and composition.
- The historical discovery material is preserved, including the rationale that stacked pipelines require per-engine evaluation first.
- No silent redefinition, no replacement taxonomy, no edits during the decision session.
- In-session owner decision only, subject to subsequent durable recording and R6.0 governance.
- Does not authorise implementation, G7, Track A, BL-22, or R6.1.

**Canonical status:** non-canonical, and explicitly **non-binding**: the seven labels are not approved API or configuration values.

### 5.3 Q2 — product/release anchor, Option A

**Line 2966**, `ts=2026-11-04T17:29:34.360Z`, `EXACT OWNER`.

> Option A — R6.1 rests on developer-gateway and internal/dev-loop value. SabiChat production milestones (ADR F / Phase 19) are downstream consumers of the R6.1 value signal, not prerequisites for the R6.1 measurement milestone.

Substance, preserved:

- The R6.1 measurement/productisation claim requires the applicable ADR Milestone B and C internal/dev-loop criteria to be met and **independently evidenced**.
- R6.1 may report measured internal/dev-loop token and cost effects.
- It must **not** claim verified customer-facing, closed-beta, production, or paid-service value from those measurements.
- Customer-facing and production claims require separate evidence from the relevant downstream application and production gates.
- SabiChat remains paused and is not brought into the active R6 implementation path by this decision.
- In-session owner decision only; no implementation, G7, Track A, BL-22, or R6.1 execution.

**Canonical status:** non-canonical.

### 5.4 Q3 — R6.6 exit requires both gate families

**Line 3159**, `ts=2026-11-04T17:53:10.585Z`, `EXACT OWNER`.

> Q3: APPROVE Option B — B1 mechanical safety gates and B2 semantic-quality gates must both pass for R6.6 exit.

Boundary conditions, preserved:

1. Semantic-quality metrics, primary metric, minimum detectable effect, sample size, arm order, evaluation conditions and acceptance thresholds must be explicitly defined and approved **before** any evaluation begins.
2. No post-hoc threshold selection or adjustment after observing results.
3. Routing invariance remains a mandatory blocking condition.
4. Terminal D's actual design must be independently reconciled with the R6.6 evaluation plan before G4 or any semantic-quality evaluation.
5. Until the evaluation methodology and thresholds are approved, R6.6 semantic acceptance remains **blocked**. Thresholds must not be invented, and advisory measurements are not proof of quality.
6. No authorisation of benchmark execution, provider calls, implementation, G7, Track A, BL-22, or R6.1–R6.7 execution.

**⚠ Identifier warning.** The *"B1"* and *"B2"* in this quote are **benchmark gate families** — mechanical-safety and semantic-quality — and are **not** canonical decisions B1 (adopt ADR-2) or B2 (R6.1 scope restriction). The two naming systems must never be merged, and Q3 must never be cited as evidence for canonical B1 or B2.

**Canonical status:** non-canonical.

### 5.5 Q5 — B6 measurement contract, Option C (dual measurement)

**Line 3368**, `ts=2026-11-04T18:34:50.473Z`, `MISSION-FRAMED` ⚠.

The submission specifies:

1. **Measurement: Option C — Dual measurement.** Compare canonical serialised UTF-8 bytes for the original and effective requests; apply the same existing `estimate_input_tokens()` to both; **both** measurements must pass, and failure in either means the transformation fails the B6 measurement contract. The distinction between structural measurement and actual provider-token savings is preserved — neither measurement establishes model-accurate token reduction.
2. **Unknown-tokenizer rule: FAIL CLOSED.** Do not approve an optimisation transformation when its required measurement cannot be established; preserve the original-request path where existing policy permits; this is not permission to reject ordinary requests unnecessarily.
3. **Threshold registration: PRE-REGISTER.** Thresholds must be defined and approved before evaluation; no retrospective selection or adjustment after benchmark results.

**Status determined by source verification:** Q5 Option C was **asserted** as approved by a **mission-framed continuation prompt** (`ts=2026-11-04T18:34:50.473Z`), **not** by a located direct owner decision utterance. Line 3368 is a third-person assertion — *"The owner has now explicitly approved the following…"* — structurally identical to the A3 assertion at line 2805, and it falls squarely inside this document's own `MISSION-FRAMED` class (§2.4).

Q5 Option C is therefore recorded **only** as a mission-framed assertion of a measurement contract attached to B6. It is **not** recorded as an independently verified direct owner decision, **not** as an approved canonical decision, and **not** as durable approval. It confers no authority of its own, carries no canonical T16 mapping, and does not resolve any of the outstanding semantics below. **Source-limited — see §8.8.**

**⚠ Unresolved.** The same mission-framed submission explicitly assigned the reporting of ambiguity in *"the exact serialization, framing, comparison, or failure-attribution semantics"* and directed that unresolved details be reported rather than invented. Those semantics are **not** resolved anywhere in the inspected evidence. Canonical-serialisation framing, comparison boundaries and failure attribution remain **open** and are recorded as such (§8.4).

### 5.6 Numbering clarification — Q1 of 5 does not exist

**Line 3501**, `ts=2026-11-04T18:51:35.338Z`, `ASSISTANT` (Terminal A recovery report — **not** an owner statement).

Recorded content of the clarification:

- No `"Question 1 of 5"` assistant framing exists in the recovered history; the five-question numbering starts at **Q2** (product anchor).
- In reconciliation tables, **"Q1" denotes the B1 / C-02 package decision**.
- Therefore: *"There is no missing decision — there is a numbering gap."*

**Provenance caution.** This is an assistant-authored inference from absence across scanned transcripts, and the report itself labels it *"INFERRED from absence"*. It is a plausible and internally consistent reading, and it matches the direct evidence (line 2716 carries B1 + C-02 with no accompanying "Question 1" framing). It is nevertheless **not** an owner decision and must not be treated as one. Whether the gap is formally closed is an open question (§8.3).

The assistant message at line 3359, `ts=2026-11-04T18:01:57.727Z`, framed Q4 confirmation and Q5 presentation. It is `ASSISTANT` material and is not cited as a decision anywhere in this record.

---

## 6. Decision-status matrix

Legend for the four states: **S** = in-session selection, **R** = durable recording, **C** = canonical registration in T16, **G** = gate acceptance.

### 6.1 The three recorded selections

| Decision | S before | R before | C before | G before | S after | R after | C after | G after |
|---|---|---|---|---|---|---|---|---|
| **A3** — Option A (conditional ADR-1) | Yes — `MISSION-FRAMED` assertion | **No** | **No** — card `PENDING` / `NOT APPROVED` | **No** | Yes | **Yes — this document** | **No** — T16 unmodified | **No** |
| **B1** — Option A (draft ADR-2, `request_transform/`) | Yes — `EXACT OWNER` | **No** | **No** — card `PENDING` / `NOT APPROVED` | **No** | Yes | **Yes — this document** | **No** — T16 unmodified | **No** |
| **B6** — Option A (monotone-shrink permanent) | Yes — `EXACT OWNER` | **No** | **No** — card `PENDING` / `NOT APPROVED` | **No** | Yes | **Yes — this document** | **No** — T16 unmodified | **No** |
| **C-02** — Reading B | Yes — `EXACT OWNER` | **No** | n/a — governance reading, not a decision card | **No** | Yes | **Yes — this document** | **Outstanding** — no register field exists for it | **No** |

**Canonical registration (C) is outstanding for all four.** T16 was verified unmodified after this document was created. Every A1–A4 and B1–B9 card still reads `Owner response: PENDING` and `Approval record: NOT APPROVED`. Any registration requires a **separate, authorised T16 register update** — a distinct future mission, not performed here and not implied by this record.

**Gate acceptance (G) is not achieved by any decision here.** No gate is cleared by recording.

### 6.2 Remaining canonical decisions

| Decision | S | R | C | G |
|---|---|---|---|---|
| A1 — Adopt §§8–15 as frozen architecture | **No** | **No** | `PENDING` | **No** |
| A2 — Tier-1 metering fixes as integrity work | **No** | **No** | `PENDING` | **No** |
| A4 — Adopt T10-1…T10-7 scoping | **No** | **No** | `PENDING` | **No** |
| B2 — Restrict R6.1 scope to `/v1/chat/completions` | **No** | **No** | `PENDING` | **No** |
| B3 — Bypass authority: operator-only, per-route, default-off | **No** | **No** | `PENDING` | **No** |
| B4 — Phase-13 keep-out | **No** | **No** | `PENDING` | **No** |
| B5 — Settlement basis (with C-07 annotation) | **No** | **No** | `PENDING` | **No** |
| B7 — Per-attempt re-derivation forbidden | **No** | **No** | `PENDING` | **No** |
| B8 — Budget terminal-marker pattern | **No** | **No** | `PENDING` | **No** |
| B9 — Reconciler placement | **No** | **No** | `PENDING` | **No** |

### 6.3 Non-canonical items

| Item | Decided in session | Recorded | Canonical | Authority granted |
|---|---|---|---|---|
| RTK two-stage (R6.2-A / R6.2-B split) | Yes — `EXACT OWNER` | Yes — §5.1 | **No** — mapping unresolved | **None** |
| Seven-mode vocabulary retained, non-binding | Yes — `EXACT OWNER` | Yes — §5.2 | No — explicitly non-binding | **None** |
| Q2 product/release anchor (Option A) | Yes — `EXACT OWNER` | Yes — §5.3 | No | **None** |
| Q3 both gate families at R6.6 exit (Option B) | Yes — `EXACT OWNER` | Yes — §5.4 | No | **None** |
| Q5 B6 measurement contract (Option C) | Asserted only — `MISSION-FRAMED` | Yes — §5.5 | No — attaches to B6; source-limited (§8.8) | **None** |
| Numbering gap explanation | **No** — `ASSISTANT` inference | Yes — §5.6 | No | **None** |

---

## 7. Outstanding decisions and restrictions

### 7.1 Outstanding canonical decisions — 10

```
A1  A2  A4
B2  B3  B4  B5  B7  B8  B9
```

These ten have no in-session selection, no durable recording, and no canonical registration. Under C-02 Reading B, BL-22 cannot be signed while any remains undecided — subject to the arithmetic question in §4.3, which does not change this list.

### 7.2 Settlement remains blocked

Settlement remediation remains **blocked**, pending:

1. **B5** — settlement basis: unknown usage wins at the full original estimate, never a partial sum (T16 §5 B5). B5 is `OUTSTANDING` / `NOT APPROVED`.
2. **The U0 test-admission policy decision** — correctly identified as **T16 §6.2 D2** (*"Authorise U0 separately under G7, ahead of U1–U12?"*), whose dependencies are **D1** (U0 merge policy) and **D3** (G7 scope text must name `tests/`). All three remain `OUTSTANDING`. U0 is *ready for separate owner authorisation* but **not authorised**; readiness is not authorisation.

**B6 does not resolve B5.** B6 boundary condition 6 is explicit that B6 "does not weaken unknown-usage handling or settlement integrity for either budget or quota", and condition 5 keeps B6 and B7 independent. Resolving B5 by inference from B6 is prohibited, and no such inference is drawn here.

### 7.3 C-07 accounting-integrity finding — preserved

C-07 (T15 §5 annotation; T16 §5 B5) stands unchanged: the current budget and quota settlement paths **can disagree on the same response**. Nothing in this document alters, mitigates or resolves C-07. B5 must be decided against C-07, not around it.

### 7.4 Terminal C block — preserved

The existing Terminal C block stands unchanged. No implementation, remediation, migration, or execution work is admitted by this record.

### 7.5 D-register numbering — untouched, and ambiguous (corrected under Terminal G Condition 2)

No D-register has been renamed, renumbered, merged, retired, reconciled or resolved by this record. **No new namespace is adopted here.**

**A. The T13/T16 relationship.** The **T16 §6.2 Group D** decisions (`D1`–`D6`, implementation authorisation) and the **T13 §10 D1–D6** are **the same six decisions represented across two documents** — *not* two independent decision families. T16's master index records their source as T13 §10 / §20-18…23.

**B. Four D-numbered registers exist in the corpus.** Verified live at `319a711`:

| Register | Range | Verified status |
|---|---|---|
| `docs/r6-architecture-decision-pack.md` | `D1`–`D17` | **`D1`, `D2`, `D3`, `D16` recorded as APPROVED** (`:387–389`, `:402`); remainder OPEN / BLOCKED / CONDITIONAL |
| `docs/r6-decision-resolution-and-approval-campaign.md` | **`D1`–`D17`** | A **duplicated campaign register** over the same subjects. Its entries **already diverge** from the architecture decision pack — e.g. `D4` is `RECOMMENDED` here (`:135`) but `OPEN` in the pack (`:390`). It is **not** an independent source of new approval authority |
| `T13 §10` / `T16 §6.2` | `D1`–`D6` | One shared set of six Group D implementation-authorisation decisions; all `OUTSTANDING` |
| `docs/architecture-decision-record.md` | `D1`–`D8` | The **Green Closure Record** family, carrying its own recorded statuses (`DECIDED`, `APPROVED`, `AUTHORIZED`, closed) |

*Note on range:* Terminal G's audit recorded the campaign register as `D1`–`D16`. Live inspection shows it runs to **`D17`**, matching the pack. The live value is recorded here; the audit figure is superseded.

**C. Collision conclusion — UNRESOLVED.**

- Bare `D` identifiers are **ambiguous across these registers**. No bare `D` identifier is safe in a decision card.
- **`D1` alone refers to materially different decisions**: "Hybrid modular architecture" (pack — APPROVED) · "U0 merge policy: strict-xfail / land-with-U1 / skip" (T13/T16 Group D — `OUTSTANDING`) · "B3 shared-completion-code ownership" (architecture-decision-record — DECIDED). `D3` collides identically and is additionally a known composite (T14 AF-15).
- The collision **remains UNRESOLVED**. It is **not fixed** by this record, and nothing here should be read as fixing it.
- A **separately authorised register-governance operation** is required **before further owner decision cards use ambiguous `D` identifiers**.

No Group C or Group D decision is decided by this record.

---

## 8. Discrepancies and unresolved issues

Recorded rather than resolved. Each requires owner or register adjudication; none has been papered over.

| # | Issue | Status |
|---|---|---|
| 8.1 | **Decision-count arithmetic.** Mission brief states 12 canonical decisions for C-02 Reading B; the register enumerates 13 (A1–A4 + B1–B9). Brief's "nine outstanding" conflicts with its own ten-item list. This record uses **13 total / 10 outstanding** and flags the brief's "12" as a miscount. | **UNRESOLVED** — affects the BL-22 discharge count |
| 8.2 | **A3 direct owner utterance missing.** A3 rests on a `MISSION-FRAMED` assertion (line 2805), not an owner message. No direct utterance with its own timestamp exists in any inspected transcript. | **UNRESOLVED** — A3 recorded as source-limited; independent re-confirmation not obtained |
| 8.3 | **Numbering gap is inference, not owner statement.** The "no missing decision, only a numbering gap" explanation originates in an `ASSISTANT` recovery report, labelled INFERRED from absence. | **UNRESOLVED** — internally consistent, not owner-confirmed |
| 8.4 | **Q5 measurement-contract semantics.** Canonical-serialisation framing, comparison boundaries and failure attribution for the dual B6 measurement were explicitly left open by the owner's own instruction to report rather than invent ambiguity. | **UNRESOLVED** — blocks B6 measurement implementation |
| 8.5 | **RTK canonical mapping.** No valid mapping of the RTK two-stage decision to a canonical T16 decision ID has been demonstrated. It is therefore recorded as non-canonical, not assigned an invented ID. | **UNRESOLVED** — may affect whether R6.2 exit criteria require a canonical decision |
| 8.6 | **Line-index offset.** The Terminal A report cites the same messages one line lower than this document's 1-based indexing. Timestamps agree exactly; no content conflict. | **RECONCILED** — convention recorded in §2.3 |
| 8.7 | **C-02 has no register field.** C-02 Reading B is a governance reading, not an A/B decision card, so "canonical registration" has no defined mechanism for it. | **OPEN** — registration path undefined |
| 8.8 | **Q5 provenance is mission-framed, not owner-verified.** Line 3368 (`ts=2026-11-04T18:34:50.473Z`) asserts approval in the third person — *"The owner has now explicitly approved the following…"* — matching the A3 construction at line 2805. It is not a direct owner decision utterance. Q5 Option C is therefore recorded as an assertion only; neither its approval nor the measurement-contract boundaries built on it are independently verified. | **UNRESOLVED** — requires a direct owner utterance or owner re-confirmation to close |

---

## 9. Scope confirmation

- **One file created:** `docs/r6-owner-decision-supplement-2026-11-04.md`. No other file was created.
- **No existing file modified.** T16, ADR-1, ADR-2, the T13/T14/T15 records, all other governance documents, all source code, tests, configuration, migrations and schemas are byte-identical to their state before this operation.
- **No D-register renamed or renumbered.**
- **No staging, commit, push, deployment, branch change, stash, or destructive Git operation.** The 1354 pre-existing untracked files are preserved untouched.
- **No implementation, no benchmark, no provider call, no spend, no migration.**
- **No gate cleared:** G7, Track A, BL-22, R6.1 and R6.0 statuses are unchanged.
- **R6.0 is not closed by this document.** T19A is not declared complete by it.

**Net effect:** three in-session selections (A3, B1, B6) plus one governance reading (C-02) moved from *durable recording: none* to *durably recorded*. They remain **unregistered in T16** and **outside every gate**. Ten canonical decisions remain outstanding, and settlement remains blocked on B5 and D2.

**Amendment record.** This file was subsequently amended in place on 2026-11-04 under owner authorisation, applying Terminal G audit Conditions 1 and 2 only. The creation-time statements above describe the original operation and remain accurate as history; **no other file was modified then or now.** Conditions 3 and 4 remain unapplied.

---

## Appendix — Source reference table

| Item | Line | Timestamp (Z) | Class | Role |
|---|---|---|---|---|
| B1 Option A + C-02 Reading B | 2716 | 2026-11-04T16:25:06.624 | `EXACT OWNER` | user |
| A3 continuation / approval assertion | 2805 | 2026-11-04T16:59:07.704 | `MISSION-FRAMED` | user |
| RTK Option C, two-stage | 2874 | 2026-11-04T17:04:33.863 | `EXACT OWNER` | user |
| Seven-mode vocabulary (B) | 2935 | 2026-11-04T17:25:46.094 | `EXACT OWNER` | user |
| Q2 product/release anchor | 2966 | 2026-11-04T17:29:34.360 | `EXACT OWNER` | user |
| Q3 both gate families | 3159 | 2026-11-04T17:53:10.585 | `EXACT OWNER` | user |
| Q4 / B6 Option A | 3167 | 2026-11-04T17:57:42.499 | `EXACT OWNER` | user |
| Q4 confirmation + Q5 presentation | 3359 | 2026-11-04T18:01:57.727 | `ASSISTANT` | assistant |
| Q5 B6 measurement contract | 3368 | 2026-11-04T18:34:50.473 | `MISSION-FRAMED` | user |
| Numbering clarification / Terminal A report | 3501 | 2026-11-04T18:51:35.338 | `ASSISTANT` | assistant |

All entries from session `<owner-session-id>`, verified by direct envelope inspection.
