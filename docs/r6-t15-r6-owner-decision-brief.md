# R6 T15 — Owner Decision Brief

**Status:** decision support only. **This brief approves nothing, selects no option, adopts no ADR, grants no G7 and authorises no implementation, test, or U0/U1/R6.1 work.**
**Mode:** documentation and decision preparation. Two files exist as a result: this brief, and an additive corrections section appended to T13. No source, test, config, migration, dataset, dependency or predecessor report was modified.
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`, ahead 6 / behind 3 of `origin/feat/sabiroute-routing-foundation`.
**Authority:** `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` (T13, the decision register) as audited by `docs/r6-t14-independent-t13-audit-and-decision-readiness.md` (T14, verdict `READY WITH CORRECTIONS`).

**Evidence labels used throughout:**

| Label | Meaning |
|---|---|
| `VERIFIED` | Read directly from the working tree at `319a711` during T15; exact anchor cited. |
| `STATIC-ANALYSIS FINDING` | Reachable by control-flow inspection; runtime consequence **not executed**. |
| `INHERITED RECOMMENDATION` | A recommendation carried from T12/T13. **Not an approval, not a decision.** |
| `OUTSTANDING` | Awaiting an owner action. |
| `OWNER DECISION REQUIRED` | The desired behaviour cannot be settled by evidence; only the owner can set it. |
| `IMPLEMENTATION/TEST PROOF REQUIRED` | Technically established, but not regression-tested; proof is owed later. |
| `UNPROVEN` | Evidence insufficient to state current behaviour. |

---

## 1. What this brief is, and what it is not

It is a session plan. It puts **A3** and **B1** in a form the owner can answer without reconstructing the technical history, and it states the **C-07** acceptance boundary that must be visible before **B5** and **T7** are decided.

It is **not** a decision. Every option below is reproduced from T13 or T14. Where a decision record contains no option or no recommendation, this brief **reports the gap** rather than inventing content to fill it — the one such case is **C1**, whose recommendation and alternatives are both "—" in T13 §9.

**Nothing here changes a gate.** R6.0 remains `CONDITIONALLY READY`, R6.1 remains `NOT READY`, U0 remains `READY FOR SEPARATE OWNER AUTHORIZATION`, G7 remains `NOT GRANTED`.

---

## 2. Two preconditions to the session itself

These are not decisions. They are things that must be settled for the session to be unambiguous.

### P-1 · C-07 must be read before B5 and T7

`C-07` (integrated into T13's corrections section) establishes that the unknown-usage signal reaches the **budget** governor but never reaches the **quota** governor, because `finish()` has no parameter for it (`completions.py:542–550`) and the quota block recomputes from raw parts (`:603`). A settlement fix that repairs one governor is therefore **incomplete**. If B5 is answered without this, the owner can approve a contract whose scope does not match the code.

### P-2 · C-02 must be settled before BL-22 is signed

T13 §19.1 condition 3 reads "Record **Group A + Group B** decisions, then sign BL-22", but §8 marks only **B1** as blocking R6.0. As written, the signature act has two possible scopes. The owner must choose one reading (C-02 in T13's corrections section sets out the two) **before** signing, or the signature's meaning is ambiguous at the moment it is made.

---

## 3. Decision A3 — ADR-1 (Telemetry)

| Field | Content |
|---|---|
| **Decision ID** | **A3** (T13 §7; also §20 item 3) |
| **Decision statement (exact, T13 §7)** | "Adopt ADR-1: Option A conditional, explicitly not implemented?" |
| **Status** | `OUTSTANDING` |
| **Why it matters** | It is **R6.0 condition 1** (§19.1). It freezes a telemetry *target shape* and its tripwires, and it names the live system as interim. It is the difference between the freeze package containing a telemetry decision, or silently endorsing the inline fail-closed shape T10 rejected (§11.4). |
| **Options as written (T13 §7)** | **(a)** Adopt ADR-1 Option A, conditional and explicitly not implemented. **(b)** Redefine the target as inline-hardened. |
| **Advantages** | **(a)** Honest freeze — the target is stated and labelled unbuilt; keeps prerequisites P1–P5 visible as tripwires; preserves T8 D14's direction. **(b)** Matches what actually ships today; no unimplemented target enters the signed contract. |
| **Disadvantages** | **(a)** Freezes something that does not exist; if P1 slips, Option A "reverts to conditional-with-no-schedule and must be recorded as such — not silently dropped" (§11.4). **(b)** Contradicts T8 D14's direction and **requires a new ADR**; it also ratifies the inline fail-closed shape T10 rejected. |
| **Technical consequences** | Adopting implements **nothing**. At `319a711` there is **no** `sabiroute_optimization_records` table, builder, projection or writer — `VERIFIED` by search; T14's AF-16 re-confirmed it. Option (b) would leave no target to build toward. |
| **Security / reliability consequences** | Current production behaviour is **inline synchronous fail-closed telemetry**: `finish()` awaits `store.finalize_usage_event` (`completions.py:649–656`) and, if persistence fails, **replaces the response** — `500` on validation failure, `503 usage_store_unavailable` otherwise (`:661–677`, `VERIFIED` during T15). So a provider call that succeeded can still surface to the client as 500/503. That is the interim behaviour ADR-1 labels; option (b) would make it the documented target instead. |
| **Migration / compatibility consequences** | **P3** additive migration following `_SCHEMA_VERSIONS`; **P4** extend `_REQUIRED_COLUMNS` so an unmigrated database fails **at startup**, not at first snapshot; **P5** the full-row admin projection must never gain optimisation columns; **P2** a `key_id`-write predicate mirroring `finalize_usage_event`'s tenant guard. All prerequisites are **currently unmet** (§11.3). |
| **Dependencies** | T13 §11 brief. No Group B dependency — **A3 and B1 are substantively independent of each other**, though both gate R6.0. |
| **Existing recommendation** | `INHERITED RECOMMENDATION`: **Yes** (honest freeze) — T12's recommendation as recorded in T13 §7. **Not an approval.** |
| **Evidence needed before approval** | No further code evidence can close this: the prerequisites are unmet by definition of a frozen-but-unbuilt target. What is required is the owner's explicit acknowledgement that (i) P1–P5 are unmet, and (ii) adopting freezes a target and builds nothing. If the owner wants P1 demonstrated first, that is a scheduling choice within option (a), not a third option — T13 does not supply one and T15 does not invent one. |
| **If option (a) is selected** | R6.0 condition 1 clears. Telemetry target is frozen; nothing is built. Remaining R6.0 blockers: condition 2 (B1) and condition 3 (C-02 scope, then BL-22). |
| **If option (b) is selected** | R6.0 condition 1 does **not** clear — a new ADR is required before it can. R6.0 slips by one ADR cycle. |
| **Exact owner response required** | One of: `A3: ADOPT Option A — conditional, explicitly not implemented` · `A3: ADOPT alternative — redefine target as inline-hardened, new ADR required` · `A3: DEFER — reason: <text>` |

---

## 4. Decision B1 — ADR-2 (R6.1 Foundation Contract)

| Field | Content |
|---|---|
| **Decision ID** | **B1** (T13 §8; also §20 item 5) |
| **Decision statement (exact, T13 §8)** | "Adopt ADR-2: T11 §8 I1–I9 as the draft R6.1 foundation contract?" — with T13's recommendation "**Yes**, with C-1 name resolution". |
| **Status** | `OUTSTANDING` |
| **Why it matters** | It is **R6.0 condition 2** (§19.1). It fixes the package, file list, U4 unit and Track A surface. **B5, B6 and B7 all depend on it**, and **U1 cannot be written** without a decided settlement contract (§8: "B5 is the gating decision for U1"). |
| **Options as written (T13 §8)** | **(a)** Adopt ADR-2 with the C-1 name resolution. **(b)** Require an external R6.1 design document first. |
| **Advantages** | **(a)** Adopting **narrows** R6.1: excludes `api/chat.py`, registries, provider adapters and all telemetry writes (§12.4); one construction point before loop entry; fail-to-original semantics; monotone-shrink; no per-attempt re-derivation. **(b)** Independent authorship of the contract. |
| **Disadvantages** | **(a)** Two quantitative items remain unspecified at adoption (I2's 250 ms / 2× byte budget; I5's configuration schema is described, not written — §12.3). **(b)** Delay; a **second authorship of the same contract**, which §8 already prices as "Delay; second authorship of the same contract". |
| **Technical consequences** | Adopting **authorises no code**. No `request_transform` package exists in `src/` at `319a711` (`VERIFIED`); loop entry is at `completions.py:1345`. |
| **Security / reliability consequences** | The contract's safety properties are the reason to adopt it: any I1–I8 exception ⇒ **fail-to-original**, never 4xx, never partial; `CancelledError` **propagates**; effective output ≤ original on every path. Its per-attempt prohibition is load-bearing against retry identity drift. |
| **Migration / compatibility consequences** | **C-1 (naming).** `docs/compression-discovery-packet.md` (8,645 B, exists) names `src/sabiroute/compression/` with a seven-mode registry; ADR-2 proposes `src/sabiroute/request_transform/`. **One name must win**, and §12.2 is explicit that this "must be recorded as a decision, not assumed". **C-2 (insertion point).** The packet's "after final deployment selection" is **superseded** — selection happens inside the loop, so adopting it literally would force per-attempt transformation and break B7. **C-3 (statuses).** CD4/CD6 are compatible; fold in rather than re-derive. |
| **Dependencies** | T13 §12 brief; X-1 (the packet exists and conflicts). **C-1 must be recorded as its own decision** — see the warning below. B5/B6/B7 depend on B1. **A3 is independent.** |
| **Existing recommendation** | `INHERITED RECOMMENDATION`: **Yes**, with C-1 name resolution — T12's recommendation as recorded in T13 §8. **Not an approval.** |
| **Evidence needed before approval** | The **C-1 naming decision recorded**, and the owner's explicit acceptance that I2 (250 ms / 2×) and I5 (schema) remain **unspecified** at adoption and are bounded later at implementation. Without the first, B1 is not cleanly decidable. |
| **If option (a) is selected** | R6.0 condition 2 clears **provided C-1 is recorded**. R6.1 contract is fixed; no code authorised. U1's settlement dependency (B5) becomes decidable. |
| **If option (b) is selected** | R6.0 condition 2 does **not** clear; R6.1 slips by one external authorship cycle. B5/B6/B7 are deferred with it. |
| **Exact owner response required** | One of: `B1: ADOPT ADR-2 with C-1 = request_transform/` · `B1: ADOPT ADR-2 with C-1 = compression/` · `B1: DEFER — require external R6.1 design doc first` · `B1: DEFER — reason: <text>` |

### 4.1 Governance warning — B1's hidden 24th decision, and a label collision

Two defects make B1 unsafe to answer in one breath. **Neither is resolved here.**

**The hidden decision.** B1's recommendation is "**Yes**, with C-1 name resolution", and §12.2 says the naming choice "must be recorded as a decision, not assumed". But **C-1 is not among the 23 registered decisions**. Answering B1 as worded therefore either (i) implicitly takes a 24th decision without registering it, or (ii) bundles it — which is exactly the composite-decision defect `C-03` records. The owner should either record C-1 explicitly as its own line, or state that B1 includes it. T15 does not choose.

**The label collision.** §12.4 names the ADR-2 conflicts **`C-1`, `C-2`, `C-3`** (hyphenated). §9 names the Group C decisions **`C1`, `C2`, `C3`, `C4`** (unhyphenated). They are different registers with near-identical labels. A reader resolving "C-1" from B1's text can land on **C1** (byok/paid billing semantics), which has nothing to do with package naming. **When answering B1, write the name, not the label** — e.g. "C-1 meaning the *package-name conflict*", not "C-1".

---

## 5. C-07 acceptance boundary — budget settlement vs quota settlement

**Why this exists.** A future settlement fix must not be counted complete because one governor was repaired. The two governors are separate accounting paths that can disagree on the same response. This section states, per scenario, what the code **proves today** and what remains **to be specified or proved**.

**Structural fact behind every row** — `VERIFIED` at `319a711`:

- The unknown-usage flag is `provider_usage_unknown`, initialised `False` at `completions.py:1316`, set `True` at `:1572` / `:1574` / `:1628`, and latched by `budget_reserved or provider_usage_unknown` at `:1693` and `:1812`. It is **never reset to `False`** once `True`.
- **Budget settlement honours it.** On the success and error paths the argument is `tokens=(None, None, None) if provider_usage_unknown else _sum_actual_tokens(actual_usage_parts)` and `actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown)` (`:1944–1955`, `:1961–1972`). `_actual_cost` returns `None` when `has_unknown_usage` is true (`:1997–1998`).
- **Quota settlement does not receive it.** The quota block runs **inside** `finish()` (`:596–620`) and computes `quota_total = _sum_actual_tokens(actual_usage_parts)[2]` at `:603`. `finish()`'s signature (`:542–550`) has **no `usage_unknown` parameter**, so the flag cannot reach it.
- `reconcile_budget` (`store.py:1213–1240`) sets `accounted_tokens` **only when `actual_tokens is not None`** (`:1229–1233`); with `None` it performs no update, leaving the estimate in place.
- `settle_quota`'s docstring (`store.py:1343–1352`) requires the opposite of what the caller sometimes passes: "Without actuals (unknown provider usage), the estimate moves reserved → consumed so the capacity stays conservatively held — never silently freed, never assumed zero."

| # | Scenario | What the code proves today | What remains unspecified or unproved | Marker |
|---|---|---|---|---|
| 1 | **Usage object absent** (no `usage`, no `error.usage`) | `_usage_object` returns `None` (`:224–230`); `_actual_tokens` returns `None` (`:241–242`). Failure branch takes `elif budget_reserved:` ⇒ flag `True` **only if a budget was reserved**; a quota-only request leaves it `False`. Budget then holds the estimate; quota receives `None` from an empty parts list and also holds. | Whether "no usage object" should be treated as unknown for **quota-only** (unbudgeted) requests — today it is not flagged. | `OWNER DECISION REQUIRED` |
| 2 | **Usage object present, `total` absent** | **Two distinct behaviours, not one.** `_actual_tokens` **synthesises** `total = prompt + completion` when both components are valid (`:245–247`) ⇒ `failure_usage[2]` is **not** `None` ⇒ flag stays `False` ⇒ budget settles the sum. If a component is absent/invalid, `total` stays `None` ⇒ flag `True` ⇒ budget holds while **quota still settles the partial sum**. | Whether a **synthesised** total counts as "known" usage for settlement purposes. The code says yes; no document states it as policy. | `OWNER DECISION REQUIRED` (semantics) + `IMPLEMENTATION/TEST PROOF REQUIRED` |
| 3 | **Usage object present, `total` = 0** | `_safe_token_count` accepts `0` (int, non-bool, `>= 0` — `:233–236`), so `0` is **known**, not unknown: flag stays `False`, and `_sum_actual_tokens` includes it (`total_values == [0]` is non-empty ⇒ total `0`). | Whether a provider-reported `0` is a legitimate charge or an artifact that should be treated as unknown. Nothing in the corpus decides this. | `OWNER DECISION REQUIRED` |
| 4 | **Usage object present, valid total** | Flag stays `False`; budget settles summed actuals via `reconcile_budget`; `_actual_cost` computes from prompt/completion prices when available. | Regression coverage only. | `IMPLEMENTATION/TEST PROOF REQUIRED` |
| 5 | **Multiple attempts, mixed known/unknown** | The flag **latches**: once any attempt sets it `True`, `:1693` / `:1812` keep it `True`. Budget therefore holds the estimate for the whole request. **Quota ignores the latch entirely** and sums whatever known parts exist ⇒ **under-charge**. This is the asymmetry C-07 records. | Which governor's semantics is canonical when they disagree, and whether a fix must make quota consume the flag or make budget match quota. | `OWNER DECISION REQUIRED` (canonical semantics) + `IMPLEMENTATION/TEST PROOF REQUIRED` |
| 6 | **Attempt 1 known usage; attempt 2 succeeds with no usage object** | **Spec 5 / X5.** Flag is never set: attempt 1's known failure takes the inner `if` and fails it (`:1571`); the success path never touches the flag (`:1904–1906`). Settlement therefore uses `_sum_actual_tokens` ⇒ **budget settles attempt 1's partial sum** instead of holding the estimate. | Nothing — this is the confirmed defect T7 fixes. It is `xfail(strict=True)` material, not a question. | `IMPLEMENTATION/TEST PROOF REQUIRED` |
| 7 | **Partial components available but `total` absent** | Same code path as scenario 2: valid prompt+completion ⇒ synthesised total ⇒ known; otherwise unknown. | Same undecided question as scenario 2. | `OWNER DECISION REQUIRED` |
| 8 | **Reservation estimates and reconciliation** | Reservation rows are written with `reserved_tokens = estimated_tokens` **and** `accounted_tokens = estimated_tokens` (`store.py:1200–1204`). Reconciliation overwrites `accounted_tokens` only on a non-`None` actual. The estimate is therefore the bound, and a held estimate is a real DB state, not a no-op. | The per-transition partial-persistence matrix for the reservation lifecycle is **unbuilt** (T13 §23.2, carried forward). | `UNPROVEN` |
| 9 | **Budget settlement** | Honours the flag on every settlement path (`:1944–1955`, `:1961–1972`, and the later error paths). Correct-by-construction when the flag is set. | Whether the flag is set for **every** shape that should count as unknown — scenarios 1–3 above say not. | `IMPLEMENTATION/TEST PROOF REQUIRED` |
| 10 | **Quota settlement** | `settle_quota` is called with `_sum_actual_tokens(...)[2]` at `:603` and **never** with `None` merely because the flag is `True`. The store-level contract in its docstring is therefore met only when the caller happens to pass `None`. | A fix must make the quota caller flag-aware; today it cannot be, because `finish()` has no parameter for it. Scope of that change is a T7 decision. | `IMPLEMENTATION/TEST PROOF REQUIRED` |
| 11 | **Reservation-row persistence** | `settle_quota` is idempotent — it filters on `status == "reserved"` (`store.py:1356–1360`). On the **C-05** path, `quota_reserved = False` at `:620` is **skipped** because the `NameError` aborts the `try` block, so the hold is never released. | The leak is established by control flow but **never reproduced**; no test exercises it. | `UNPROVEN` (leak, runtime) |
| 12 | **Usage-event persistence** | Inline and fail-closed: `finish()` awaits `store.finalize_usage_event` (`:649–656`); failure yields `500` (validation) or `503 usage_store_unavailable` and **replaces** the response (`:661–677`), even when the provider call succeeded. The event records the settled values, so a partial-sum settlement is what gets persisted. | Whether fail-closed telemetry is the accepted interim posture is decision **A3**. | `OWNER DECISION REQUIRED` (via A3) |

### 5.1 The acceptance rule this section establishes

> **A settlement correction is not complete when one governor is fixed.** It is complete only when, for every scenario above, the **budget** and **quota** governors are shown to reach the **same intended outcome**, with the intended outcome itself recorded as an owner decision where the evidence does not settle it.

Scenarios marked `OWNER DECISION REQUIRED` (1, 2, 3, 5, 12) cannot be closed by implementation alone. Scenarios marked `UNPROVEN` (8, 11) need evidence, not code. Scenario 6 is a settled defect awaiting its fix.

---

## 6. Dependency-ordered session plan

Ordered by dependency, not by document order. **No option is selected for the owner.**

### Stage 1 — Unblock the signature's meaning (preconditions)

| Step | Item | Why first |
|---|---|---|
| 1.1 | Read **C-07** (T13 corrections) and **§5** of this brief | Changes what "fixed" means for B5 and T7. |
| 1.2 | Settle **C-02** — one of the two readings of §19.1 condition 3 | BL-22's scope is ambiguous until this is chosen. |

### Stage 2 — The two ADRs (R6.0 conditions 1 and 2)

| Step | Decision | Note |
|---|---|---|
| 2.1 | **A3** — ADR-1 telemetry | Independent of B1. |
| 2.2 | **C-1** — package-name conflict (recorded explicitly, or folded into B1 by the owner's stated choice) | **Must precede or accompany B1.** See §4.1. |
| 2.3 | **B1** — ADR-2 foundation contract | Needs 2.2. Unblocks B5/B6/B7. |

### Stage 3 — Remaining Group A

**A1** (adopt §§8–15 as frozen architecture) · **A2** (Tier-1 metering fixes as integrity work) · **A4** (T10-1…T10-7 scoping).
A2 is the highest-consequence item in Group A: deferred, the confirmed defects ship as accepted billing error (T13 §7).

### Stage 4 — Settlement contract (depends on B1)

**B5** (unknown wins at the full estimate, never a partial sum) → **must name the quota governor** · **B6** (monotone-shrink permanent) · **B7** (no per-attempt re-derivation). Then **B2, B3, B4, B8, B9**.

### Stage 5 — R6.0 signature

**BL-22** — recorded only after Group A and B1 are recorded and C-02 is settled.

### Stage 6 — U0 readiness (independent of every architecture question)

**D1** (U0 merge policy) and **D3** (G7 scope naming `tests/`, answerable as three separate parts) can be settled at **any** point — they unblock U0 without touching R6.0. Then **D2** (the authorisation act) once D1 and D3 are answered.

### Stage 7 — Remaining Group D, then C

**D4, D5, D6**, then **C1–C4**. C1 has no recommendation and no alternatives in T13 — it needs an owner-supplied position, not a selection from a list.

---

## 7. Outstanding decisions — independently counted

**23**, counted from T13 §7–§10 directly during T15, not carried from T13's or T14's totals:

| Group | Register | Count |
|---|---|---:|
| A | §7 A1–A4 | 4 |
| B | §8 B1–B9 | 9 |
| C | §9 C1–C4 | 4 |
| D | §10 D1–D6 | 6 |
| **Total** | | **23** |

All 23 are `OUTSTANDING`. **0 approved. 0 deferred by decision** (some are recommended for deferral, which is not a deferral).

Two items in T13 §20 are **not** decisions: item 24 (**BL-22**, the signature act) and item 25 (the CLAUDE.md §12 correction, a documentation finding). Both are correctly excluded from the 23.

---

## 8. Governance status

| Statement | Status |
|---|---|
| No ADR approved | **Correct** — ADR-1 and ADR-2 remain `PROPOSED` |
| No architecture option selected | **Correct** — T15 selected nothing |
| No G7 granted | **Correct** — never requested |
| No implementation authorised | **Correct** — no U0/U1/R6.1/Track A authority exists |
| No production action authorised | **Correct** — no deployment, config or infrastructure action |
| No Track B implementation authorised | **Correct** — Track A and Terminals B/C/D/E remain `NOT OBTAINED` |
| No ML training authorised | **Correct** — no dataset, model, compression or routing work touched |
| No gate changed | **Correct** — R6.0 `CONDITIONALLY READY`, R6.1 `NOT READY`, U0 `READY FOR SEPARATE OWNER AUTHORIZATION` |

**Silence is not approval.** No reviewer was contacted; no prompt was sent; no external lane returned a record.

---

## 9. Limitations of this brief

- **No runtime confirmation.** Every behavioural statement is `VERIFIED` (read from source) or `STATIC-ANALYSIS FINDING` (reachable by control flow). **No test was executed and no provider was called.**
- **No decision taken.** All 23 remain `OUTSTANDING`; no option was selected; both readings of C-02 remain open.
- **No option invented.** Where T13 records no alternative (notably **C1**), this brief says so rather than supplying one.
- **Anchors are local.** All line numbers are against **local** `319a711`. The branch is ahead 6 / behind 3 of origin; a reviewer working from a remote ref must re-anchor.
- **Two T15-original observations are not T14's:** the split of "total absent" into synthesised-total and truly-absent sub-cases (§5 scenario 2), and the `C-1` / `C1` label collision (§4.1). Both are sourced to `319a711` above and are recorded as T15's.

---

## 10. Response format for the owner

Any unambiguous written record is sufficient. A minimal form:

```
A3:  ADOPT Option A — conditional, explicitly not implemented
C-1: request_transform/     (or)   compression/
B1:  ADOPT ADR-2 with the C-1 above
C-02: reading (a) — condition 3 covers Group A + B1 only
A1 / A2 / A4: <decision>
B5 / B6 / B7: <decision>   (B5 must name both budget and quota governors)
D1 / D3: <decision>        (D3 may be answered as three parts)
```

Answering A3 and B1 does **not** create a 24th decision, because C-1 is registered as its own line above. If the owner prefers to fold C-1 into B1, say so explicitly — that is a valid choice, and it is C-03's composite-decision issue being accepted knowingly rather than by accident.

---

**FINAL STATUS: T15 COMPLETE — DECISIONS PREPARED, NONE TAKEN; CORRECTIONS INTEGRATED INTO T13; NO GATE GRANTED; OWNER ADJUDICATION OUTSTANDING.**
