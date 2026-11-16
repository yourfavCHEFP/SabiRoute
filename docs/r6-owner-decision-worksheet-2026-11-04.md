# R6 Owner Decision Worksheet -- Ten Outstanding Decisions

**Prepared:** 2026-11-04
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` (re-measured this session; matches T14's recorded baseline exactly).
**Authority:** worksheet only. **This document decides nothing.** It adopts no ADR, grants no gate, authorises no U0/U1/R6.1 work, and marks no decision approved. Every one of the ten below remains `OUTSTANDING` until the owner records an answer.
**Registers:** T16 and the 2026-11-04 supplement were **read, not edited**. No register, ADR brief, or predecessor report was modified. This is the only file created.
**Not a duplicate:** no worksheet exists in `docs/` (`grep -rln "worksheet" docs/` returns nothing). T16 is the option register; T15 is the brief; the supplement records answers. This is the working paper that grounds each unanswered decision in code.

**Purpose.** T16 gives the owner a canonical option register. T14 gives the owner an audit verdict. Neither is a *worksheet*: T16 is organised by identifier, quotes consequences in the language of the decision that produced them, and does not say where in the code each choice lands. This document answers one question per page: **what am I deciding, what does the code do now, what breaks under each option, and what do I write down?**

---

## Evidence classes used

Same vocabulary as T14, so the two documents read together.

| Label | Meaning |
|---|---|
| `VERIFIED` | Read directly from the working tree at `319a711` this session; exact `path:line` cited. |
| `STATIC-ANALYSIS FINDING` | Reachable by reading control flow. **Not executed**, no test run, no request made. |
| `PROPOSED` | A recorded proposal. Not adopted, not implemented. |
| `UNRESOLVED` | Evidence in the tree is insufficient to decide. |

**Note on `store.py`.** T13 and T14 cite a bare `store.py:NNNN`. At HEAD that resolves to `src/sabiroute/security/store.py` -- its line numbers match T13/T14 exactly (`reconcile_budget` 1213, `settle_quota` 1343). Confirmed, not assumed. The other `store.py` in the tree is `src/sabiroute/chat/store.py` and holds no reservation tables.

---

# PART 1 -- Owner Decision Queue (one page)

Answer in this order. The order is not cosmetic: three of the ten *change what the others mean*, and answering them out of order produces a register whose answers contradict each other.

| # | Decision | Blocks | Why it sits here |
|---|---|---|---|
| **1** | **B5 + B6** -- settlement basis; monotone-shrink | R6.1; **gates U1** | Defines what "fixed" means. A2 asks *whether* to fix; A4/T10-5 embeds *the same repair*. Answer B5 first or the other two are unmoored. |
| **2** | **A2 + A6** -- Tier-1 metering fixes as integrity work | R6.0 | Cost of deferral is now exact (see card). Only meaningful after B5 fixes the target contract. |
| **3** | **B7** -- per-attempt re-derivation forbidden | R6.1 | New invariant. Collides with per-attempt `choose_deployment`. Independent of B6 -- do not merge them. |
| **4** | **B2** -- restrict R6.1 to `/v1/chat/completions` | R6.1 | Scope boundary. Determines whether the C-07 repair has one call site or two. |
| **5** | **B3** -- bypass authority: operator-only, per-route, default-off | R6.1 | Three of its four properties already have a proven precedent; one ("per-route") does not exist anywhere. |
| **6** | **B4** -- Phase-13 keep-out, no snapshot fields | R6.1 (R6.0 if deferred) | Schema-version commitment. Mechanical either way once chosen. |
| **7** | **B8** -- budget terminal-marker pattern | R6.1 | Ratifies an asymmetry that already exists (`status` on one table, absent on the other). |
| **8** | **A1** -- adopt T11 ss.8-15 as the frozen architecture | **R6.0** | The container decision. A3 and B1 are **already answered**, so the containment problem is dissolved -- but only if A1 names T11. See card 8, item N-01. |
| **9** | **A4** -- adopt T10-1...T10-7 scoping | R6.0 | Not one decision. Seven rules in four different states. Card 9 splits it. |
| **10** | **B9** -- reconciler placement: R6.7 | Release (not R6.0/R6.1) | Lowest urgency, and under-specified: there is no runtime host for a reconciler in the tree today. |

### Two rules for the session

1. **B5 and B6 are two questions, not one.** T16 states this explicitly ("B6 and B7 are independent decisions and are not to be combined"). The worksheet puts B5 and B6 on one page because they are answered in one sitting; the answer line has **two slots**. Same for A2 and A6.
2. **A1 must be written with its document name.** "Adopt ss.8-15" is a dangling reference: in T13's and T16's own numbering, ss.8-15 are the decision groups, the two ADR briefs, the U0 spec and the Terminal B packet -- not architecture. The freeze target is **T11 ss.8-15**. Adopting "ss.8-15" as read inside T16 would adopt the decision register as the architecture, which is circular and would silently swallow A2, A3, A4 and B1. This is finding **N-01**; it is the single highest-consequence wording defect in the ten.

### What is already settled and must not be re-opened here

Thirteen of the 23 canonical decisions are recorded as answered (T16 master index). **This worksheet does not restate what any of them was answered as, and takes no view on it.** Where an unanswered decision is scoped *by* an answered one -- A1 by A3 and B1; B3 by the T4 flag; B9 by U9 -- the card says so and states the consequence of the recorded answer in either direction, rather than assuming the recommended one.

---

# PART 2 -- The Ten Decision Cards

---

## Card 1 of 10 -- B5 + B6: Settlement basis, and monotone-shrink

### The two questions (verbatim, T16 ss.5)

**B5:** Settlement basis: unknown wins at the full original estimate, never a partial sum?
**B6:** Monotone-shrink **permanent** unless the reservation is re-baselined?

**Blocks:** R6.1. **B5 gates U1** -- U1 cannot be written without a decided settlement contract.
**Existing recommendation (T12 ss.12, carried by T13/T16):** **Yes** to both. B5 Option B is recorded as ratifying a confirmed defect. B6 Option B is recorded as breaking reservation authority.
**Not deciding:** whether the defects exist (they do, see below), or how to fix them (that is A2's question).

### B5 -- what the code does now

| Fact | Anchor | Class |
|---|---|---|
| Quota settlement **already implements the B5 contract**: unknown actuals settle at the held estimate | `security/store.py:1369` -- `settled = actual_tokens if actual_tokens is not None else estimate` | `VERIFIED` |
| Its docstring states the contract in the same words B5 uses ("never silently freed, never assumed zero") | `security/store.py:1346-1352` | `VERIFIED` |
| Budget settlement **also** holds the estimate, by construction: reservation is inserted with `accounted_tokens = estimated_tokens` and only overwritten by a non-`None` actual | `security/store.py:1201-1202`, `:1233-1234` | `VERIFIED` |
| The caller defeats both. `finish()` has **no** usage-unknown parameter, so the quota path recomputes a total from raw parts and passes it as a concrete number | `api/completions.py:542-550`, `:603` | `VERIFIED` |
| `_sum_actual_tokens` returns `None` only when **no** part carries a total; one known part plus one unknown part yields a non-`None` **partial sum** | `api/completions.py:253-264` | `VERIFIED` |

**The precise defect (this is the card's main point).** T16 marks B5 as "Not implemented". That is imprecise in a way that matters for cost. The *store* implements the contract; the *call site* defeats it. Concretely:

- **All attempts unknown** -> summed total is `None` -> estimate held. Correct, by accident.
- **Mixed known + unknown, flag not set** -> summed total is a partial sum -> **under-charge**. This is the live hole.
- The flag is not set when the failing attempt had usage and the succeeding attempt had none (`api/completions.py:1568-1574`, `:1903-1906` -- `STATIC-ANALYSIS FINDING`).

So B5 Option A is **a call-site repair, not a store redesign**. The store already agrees with the contract; it is being handed a number that lies. This is materially cheaper than "rebuild settlement" and the owner should price it that way. (Finding **N-04**.)

**C-07, restated from T14.** The unknown-usage signal is asymmetric in a second way: budget settlement honours the flag (`api/completions.py:1944-1955`, `:1961-1972`), quota settlement never receives it. B5's contract must therefore be written to cover **both governors**. A settlement fix that repairs only budget leaves the quota under-charge live.

**Third axis, not previously recorded (N-05).** Quota is under-protected on **three** axes, not one. Both retry controls are gated on `budget_reserved` and never on `quota_reserved`:

| Control | Anchor | Budget | Quota |
|---|---|---|---|
| `max_tokens` narrowing before retry | `api/completions.py:1603-1608` | yes | **no** |
| Break-out when usage is unknown | `api/completions.py:1601` | yes | **no** |
| Settlement honours unknown-usage flag | `api/completions.py:603` vs `:1948-1951` | yes | **no** |

`STATIC-ANALYSIS FINDING`. This is the mechanism behind A2's "quota leak" and behind T10-5 ("mirror budget token governor behind `quota_reserved`"). It is one finding in three places, and it should be fixed as one.

**Fourth, smaller (N-06).** When computing how much budget remains for a retry, unknown parts are counted as **zero** consumption (`api/completions.py:1604` -- `sum(part[2] or 0 ...)`), while settlement treats them as unknown. So the retry allowance and the settled amount use different rules on the same data. `STATIC-ANALYSIS FINDING`. Worth deciding alongside B5 whether that `or 0` is intended.

### B6 -- what the code does now

`VERIFIED`: monotone-shrink is **already the implemented behaviour** for the one quantity that is narrowed.

`api/completions.py:1608` -- `max_tokens = min(max_tokens, remaining - estimated_input)`. The mutation is against the outer variable that the next iteration reads at `:1406`, and `min` cannot increase. The request therefore cannot expand across attempts; narrowing is permanent for the life of the request. There is no code path that raises `max_tokens` after a retry.

**Consequence for the owner:** B6 Option A **ratifies behaviour that already exists**. Adopting it costs nothing and forecloses nothing; declining it would require *writing new code* to permit expansion. It is the lowest-cost decision of the ten.

### Option comparison

| | B5 Option A (unknown wins at full original estimate) | B5 Option B (partial-sum settlement) |
|---|---|---|
| What it means in code | Pass unknown-ness to `settle_quota` instead of a synthesised sum | Keep `:603` as-is and declare it correct |
| Cost | One call site plus both-governor coverage | Zero code; permanent under-billing |
| Breaks | Nothing. Matches the store's own docstring | The reservation stops bounding the request; matches the confirmed defect |

| | B6 Option A (monotone-shrink permanent) | B6 Option B (allow expansion) |
|---|---|---|
| What it means in code | Change nothing; record the existing `min` as the invariant | Add a raise path to `max_tokens` between attempts |
| Cost | Zero | New code + new argument that the reservation still bounds the request |
| Breaks | Nothing | Reservation authority; the bound is no longer an upper bound |

### Answer line (two slots -- they are separate decisions)

```
B5: [ A | B ]   conditions: ______________________________________
B6: [ A | B ]   conditions: ______________________________________
```


---

## Card 2 of 10 -- A2 + A6: Tier-1 metering fixes as integrity work

### The question (verbatim, T16 ss.4)

**A2:** Treat Tier-1 metering fixes as integrity work, not optional feature work?
**Companion:** **A6** is carried with A2 in the outstanding set (BL-01...BL-04, A6, BL-06, BL-07).

**Blocks:** R6.0. T13 states plainly that **A2 is the highest-consequence item in Group A.**
**Existing recommendation:** **Yes** -- these close live holes.
**Not deciding:** the settlement contract itself (that is B5/B6, card 1), or how the quota governor is repaired (A4/T10-5, card 9).

### What the code does now

Three defects, all `STATIC-ANALYSIS FINDING` -- read from control flow, **not** executed this session and not reproduced by any test.

| Defect | Mechanism | Anchor |
|---|---|---|
| **D-1 Budget settles at a partial sum** | First attempt fails with known usage; second succeeds with no usage object; the unknown-usage flag is only set when a usage object exists but lacks a total, so it stays `False`; settlement takes the partial sum | `api/completions.py:1568-1574`, `:1903-1906`, `:1945-1953` |
| **D-2 Quota under-charges** | The quota path recomputes a total from raw parts and ignores unknown-ness entirely | `api/completions.py:602-603`, `:253-264`; `security/store.py:1369` |
| **D-3 Pre-execution denial reported as a 503 quota outage** | `finish()` reads `attempted`, which is not bound until after the reservation is taken; eight pre-loop call sites execute before that binding; the resulting `NameError` is caught by the quota handler, which replaces the real response (including a **429** budget denial) with `503 QUOTA_UNAVAILABLE` and skips the release | `api/completions.py:542-550` (no `attempted` parameter), `:1311` (binding), `:602` (read), `:623-632` (handler); sites `:1171, :1180, :1189, :1205, :1272, :1282, :1291, :1299` |

On D-3, T14's **C-05** widens the trigger from "budget-denied" to all eight pre-loop sites. The consequence class is identical; the reachable set is larger than T13 states.

**N-05 applies here.** The quota leak is not one bug: quota has no `max_tokens` narrowing, no unknown-usage break, and no flag in settlement (see card 1, three-axis table). A2 Option A on the strength of "a quota leak" alone undercounts the work; A2 should name all three.

### Option comparison

| | Option A (integrity work, mandatory) | Option B (defer post-v1) |
|---|---|---|
| Ships | Correct accounting before v1 | Documented under-billing in v1 |
| Live consequence of the defects | None once fixed | D-1 and D-2 under-charge real spend; D-3 turns a 429 into a 503 quota outage and **leaks the quota hold**, which degrades every later request by that user until the window rolls |
| Coupling | Requires B5 answered first, or "fixed" has no target | Contradicts B5 Option A if both are recorded -- the register would then hold a contract and its negation |

**Ordering constraint.** A2 and B5 must not be answered in an order that produces A2=A with B5=B. If B5 is B, A2 Option A has no contract to implement.

### Answer line

```
A2 (with A6): [ A | B ]   conditions: ____________________________
```


---

## Card 3 of 10 -- B7: Per-attempt re-derivation forbidden

### The question (verbatim, T16 ss.5)

**B7:** Per-attempt re-derivation of the effective request forbidden?

**Blocks:** R6.1.
**Existing recommendation:** **Yes** -- forbid. B7 is one of the two rulings T11 ss.18 omitted; T16 states it must **not** be combined with B6.
**Not deciding:** whether narrowing may occur (that is B6, card 1) or where the transform is constructed (that is B1/ADR-2, already answered).

### What the code does now

| Fact | Anchor | Class |
|---|---|---|
| No transform exists yet -- there is no request-transform package in `src/` | absence confirmed by directory listing; T14 AF-17 | `VERIFIED` |
| Deployment selection is **inside** the retry loop | `api/completions.py:1388` -- `state.router.choose_deployment(...)`, loop at `:1345` | `VERIFIED` |
| The original `max_tokens` is captured **before** the loop and is the identity the loop narrows | `api/completions.py:907`, `:1406` | `VERIFIED` |

**What B7 actually constrains.** It forbids building the *effective* request more than once. That is a forward-looking invariant on code that does not exist (`PROPOSED`), and it is the reason ADR-2's insertion point is "one construction point before loop entry `:1345`" rather than "after deployment selection". The tension is real and worth seeing: **deployment is chosen per attempt (`:1388`), but the effective request must be built once before the loop.** Any transform whose output depends on which deployment was chosen therefore cannot be constructed before selection. B7 Option A rules that dependency out.

So B7 is not a formality. Answering A commits the design to: *no transform input may depend on the per-attempt deployment.* If the owner expects a future transform to be deployment-aware, B7 must be B, and ADR-2's insertion point must move -- which re-opens B1.

### Option comparison

| | Option A (forbid re-derivation) | Option B (allow re-derivation) |
|---|---|---|
| Effective request identity | Stable across retries | Changes between attempts |
| Settlement | Every settlement argument in T12 ss.12 holds | Settlement arguments are invalid: the thing being settled is a different request each attempt |
| Constrains | Transform may not depend on the chosen deployment | Deployment-aware transforms remain possible |
| Re-opens | Nothing new | ADR-2 insertion point, hence B1 |

### Answer line

```
B7: [ A | B ]   conditions: ______________________________________
```


---

## Card 4 of 10 -- B2: Restrict R6.1 scope to `/v1/chat/completions`

### The question (verbatim, T16 ss.5)

**B2:** Restrict R6.1 scope to `/v1/chat/completions`, excluding `api/chat.py`?

**Blocks:** R6.1.
**Existing recommendation:** **Yes.**
**Not deciding:** whether SabiChat is ever in scope -- only whether it is in scope for **R6.1**.

### What the code does now

`VERIFIED`: `api/chat.py` is a materially different admission and identity surface, not a thin alias of the completions path.

| Fact | Anchor |
|---|---|
| `chat.py` authenticates a **user session** (`require_chat_session`), not an API key quota identity | `api/chat.py:66`, `:311` |
| It resolves its own service identity into `sabichat_service_key_id` | `api/chat.py:134`, `:159`, `:164` |
| The reservation tables it touches are the `sabichat_*` user-quota family, separate from `sabiroute_*` API-key budgets | `security/store.py:127` (`sabichat_quota_reservations`) vs `:433` (`sabiroute_budget_reservations`) |

**Why this matters for the C-07 repair.** Card 1's fix lands at `api/completions.py:603`. If B2 is Option B, the same three-axis quota gap exists on a **second** admission surface with a different identity object, and the repair needs a second call site and a second set of tests. B2 therefore sets the price of B5's fix, not just its scope.

### Option comparison

| | Option A (exclude `chat.py`) | Option B (include it) |
|---|---|---|
| R6.1 surface | One admission path, one reservation family | Two admission paths, two reservation families, two identity models |
| C-07 / T10-5 repair | One call site | Two call sites, two test matrices |
| Risk | SabiChat keeps its current behaviour, unfixed and out of scope | Scope widens materially; the R6.1 exit condition ("safe no-op") must hold on both paths |

### Answer line

```
B2: [ A | B ]   conditions: ______________________________________
```


---

## Card 5 of 10 -- B3: Bypass authority -- operator-only, per-route, default-off

### The question (verbatim, T16 ss.5)

**B3:** Bypass authority: operator-only, per-route, default-off?

**Blocks:** R6.1. **Depends on:** the T4 flag (already answered).
**Existing recommendation:** **Yes.**
**Not deciding:** the T4 flag itself.

### What the code does now -- three of the four properties already exist

The question bundles four properties. Exactly one of them has no precedent in the tree, and that is the one the owner should focus on. (Finding **N-10**.)

| Property | Status at HEAD | Anchor | Class |
|---|---|---|---|
| **Operator-only** | Precedent exists: admin surface with an audit field `updated_by` | `api/admin.py:139` (`/api-keys/{key_id}/reconcile-lineage`), `security/store.py:116` (`updated_by`) | `VERIFIED` |
| **Default-off / fail-closed** | Precedent exists and is strict: the value is only allowed when **exactly** `True`; anything else denies | `api/completions.py:1351-1372` -- `None if allowed_shared is True else SHARED_INFERENCE_DISABLED` | `VERIFIED` |
| **Re-checked per attempt** | Precedent exists | `api/completions.py:1351` (comment: a disable lands no later than the next routing decision) | `VERIFIED` |
| **Per-route** | **No precedent anywhere.** The existing switch is a single **global** row, keyed by `id`, tri-state via a nullable `enabled` | `security/store.py:110-117` | `VERIFIED` |
| Per-route config dimension in the store | **Absent** -- no `route_id`, no `per_route`, no route-keyed table | grep over `security/store.py` returns nothing | `VERIFIED` |

**The concrete agenda item.** B3 as written is 3/4 already-proven pattern plus 1/4 new design. "Per-route" needs: a route-keyed table, a resolution rule for the absent row (which should be *off*, matching the fail-closed precedent), an operator endpoint, and a decision about what a "route" is keyed by -- the endpoint path, or the stage/phase. None of that exists. If the owner wants the cheapest defensible answer, **a global operator switch is already implemented and proven**; per-route is where the new work is.

T16 records B3's Option B ("trusted-service signal") as requiring "provenance machinery comparable to `sabichat_service_key_id`". That machinery **does** exist (`api/chat.py:134-164`), so Option B is not fantasy -- but it answers a different question (who is calling) than Option A (who may switch it off).

### Option comparison

| | Option A (operator-only, per-route, default-off) | Option B (trusted-service signal) |
|---|---|---|
| New code | Per-route table + resolution rule + endpoint | Provenance check on the request |
| Precedent | 3 of 4 properties proven; per-route is new | `sabichat_service_key_id` proves the shape |
| Failure mode | A misconfigured route row silently bypasses | A forged/forwarded service identity bypasses |
| Default | Off (matches existing fail-closed semantics) | Whatever the provenance check yields -- needs its own fail-closed rule |

### Answer line

```
B3: [ A | B ]   if A, per-route required?  [ yes | global switch acceptable ]
                conditions: ______________________________________
```


---

## Card 6 of 10 -- B4: Phase-13 keep-out -- R6.1 emits no snapshot fields

### The question (verbatim, T16 ss.5)

**B4:** Phase-13 keep-out: R6.1 emits no snapshot fields?

**Blocks:** **R6.1** (R6.0 if deferred).
**Existing recommendation:** **Yes.**
**Not deciding:** whether Phase-13 ever happens -- only whether R6.1 opens the schema for it.

### What the code does now

| Fact | Anchor | Class |
|---|---|---|
| Feature schema is version-pinned to a **literal** `"1.1"` | `intelligence/dataset.py:23` -- `FEATURE_SCHEMA_VERSION: Literal["1.1"] = "1.1"` | `VERIFIED` |
| The model accepts only `"1.0"` or `"1.1"` | `intelligence/dataset.py:57` | `VERIFIED` |
| Pre-routing snapshots **are** written today, on the usage row, when present | `api/completions.py:646-647`, `:757`; `security/store.py:1461-1495` | `VERIFIED` |

**Read this carefully, because the wording invites a mistake.** "R6.1 emits no snapshot fields" does **not** mean R6.1 stops writing the existing pre-routing snapshot -- that is live behaviour on the accounting row. It means R6.1 adds **no new snapshot fields for the optimisation stage**, i.e. the schema stays at `1.1`.

The Option B consequence ("amend to schema-1.2 now") is therefore mechanical and cheap in *code* terms -- add `"1.2"` to two literals -- and expensive in *coordination* terms, because it pulls Phase-13 inside R6.1 and makes the R6.1 exit condition depend on a later phase's schema.

### Option comparison

| | Option A (no snapshot fields; schema stays 1.1) | Option B (amend to schema-1.2 now) |
|---|---|---|
| Code | Zero | Add `"1.2"` to `dataset.py:23` and `:57`, plus a writer |
| R6.1 exit | "safe no-op" verifiable against a frozen schema | Exit depends on Phase-13 coordination |
| Reversibility | Later amendment is available | Hard to withdraw once consumers exist |
| Gate effect | Stays R6.1 | Becomes an R6.0 matter if deferred |

### Answer line

```
B4: [ A | B ]   conditions: ______________________________________
```


---

## Card 7 of 10 -- B8: Budget terminal-marker pattern (BL-15)

### The question (verbatim, T16 ss.5)

**B8:** Adopt the budget terminal-marker pattern (BL-15) transferred from `_QUOTA_RESERVATIONS`?

**Blocks:** R6.1.
**Existing recommendation:** **Yes.**
**Not deciding:** the marker's exact vocabulary (that is implementation).

### What the code does now -- the asymmetry is real and exactly as described

`VERIFIED`, read directly from both table definitions:

| Table | Terminal marker | Lifecycle |
|---|---|---|
| `sabichat_quota_reservations` | **has** `status String(16)` | reserved -> settled (`security/store.py:1389`); only `reserved` rows are ever touched, which makes settle and release idempotent (`:1359`, `:1395-1396`) |
| `sabiroute_budget_reservations` | **has none** | Reconciled by `UPDATE` (`:1238-1247`) or removed by `DELETE` (`release_budget`, `:1249-1256`) |

**What the owner gains by transferring it.** The quota table's pattern solves two problems the budget table currently does not: (a) idempotence via a `WHERE status = 'reserved'` guard on both settle and release, and (b) an auditable terminal state -- today a released budget reservation **ceases to exist**, so "was this released, or never created?" is unanswerable after the fact. The budget table is a strict subset of the quota pattern, so this is genuinely a transfer, not a parallel design.

**One honest caveat** (`VERIFIED`, and it cuts *for* B8): `release_budget` deletes, which means the budget ledger currently cannot distinguish a released reservation from an absent one. Adding a terminal marker changes retention semantics -- rows that used to disappear now persist. That is a schema migration and a data-growth decision, and it belongs in the R6.1 marker migration that B9 already assumes.

### Option comparison

| | Option A (adopt the transferred pattern) | Option B (design a new state machine) |
|---|---|---|
| Reuses | A solved, in-repo, tested state machine | Nothing |
| Cost | One column + migration + guard clauses | Full design + second vocabulary for the same concept |
| Risk | Retention growth from rows that no longer delete | Two reservation state machines that drift |

### Answer line

```
B8: [ A | B ]   conditions: ______________________________________
```


---

## Card 8 of 10 -- A1: Adopt T11 ss.8-15 as the frozen architecture

### The question (verbatim, T16 ss.4)

**A1:** Adopt ss.8-15 as the frozen architecture?

**Blocks:** **R6.0.**
**Existing recommendation:** **Yes.** Alternative: return D14/D19-Tier-2 for re-scope, which re-opens ss.11 and ss.14 and restarts the freeze package.
**Not deciding:** A3 or B1. Both are already answered. A1 adopts the surrounding block **as amended by** those answers.

### The defect in the question as written (N-01) -- highest-consequence wording issue in the ten

`VERIFIED` by reading the section headings of both documents this session:

| Document | What its ss.8-15 actually are |
|---|---|
| **T11** (the intended target) | ss.8 Optimization Foundation Interface Blueprint; ss.9 Lifecycle and Execution Safety; ss.10 Capability Recovery Boundaries; ss.11 Estimation and Quota Policy; ss.12 Retry and Fallback Policy; ss.13 Deadline and Cancellation Policy; ss.14 Benchmark and Telemetry Readiness; ss.15 Track A Approval Matrix |
| **T13 / T16** (where the phrase now appears) | ss.8 Group B; ss.9 Group C; ss.10 Group D; ss.11 ADR-1; ss.12 ADR-2; ss.13-14 U0 spec and tests; ss.15 Terminal B packet |

The phrase originates in T11 ss.18 ("A1. Adopt ss.8-15 as the frozen architecture?") where it is unambiguous. T12, T13 and T16 carried it forward **without the document name**, and in those documents the same token now resolves to the decision groups. Adopting "ss.8-15" as a reader of T16 would adopt the decision register as the architecture -- circular, and it would absorb A2, A3, A4 and B1 into their own container.

**This is not a reason to doubt A1's substance.** It is the correct R6.0 architecture decision. It is a reason to write the answer down with the document named, and to fix the question text before signature. Recommend: *"Adopt **T11 ss.8-15** as the frozen architecture."*

Note the internal consistency this restores: re-opening ss.11 (Estimation and Quota Policy) and ss.14 (Benchmark and Telemetry Readiness) is exactly where D14 (telemetry) and D19-Tier-2 (tiered estimation) live. Under T13's numbering, "re-opens ss.11 and ss.14" would point at ADR-1 and the U0 test spec, which does not fit the sentence at all. The T11 reading is the one that makes the option coherent.

### Why A1 can now be answered cleanly (N-02)

A1's recorded dependency is "Group B record". The real dependency is narrower and, as it happens, **already discharged**: T11 ss.8 is the ADR-2 foundation contract itself (B1's subject), and T11 ss.14 is telemetry readiness (A3's subject). Both A3 and B1 are among the answered decisions. So A1's containment problem is dissolved -- provided A1 is answered **after** them and read as amended by them.

**Consequence if either was recorded as its Option B:** A1's Option A scope changes. A3 Option B means the inline fail-closed telemetry shape is ratified, so T11 ss.14's freeze must carry that; B1 Option B means an external R6.1 design document is authoritative, so T11 ss.8 is not the frozen foundation. This card does not assume either way.

### Option comparison

| | Option A (adopt T11 ss.8-15) | Option B (return D14/D19-Tier-2 for re-scope) |
|---|---|---|
| Freeze package | Proceeds on current text | Restarts; ss.11 and ss.14 re-opened |
| R6.0 | Reachable | Delayed by a re-scope cycle |
| Risk | Freezes a block in which the owner has already answered the two load-bearing sub-parts | Re-opens quota-policy arithmetic that three other decisions (B5, B6, A4/T10-5) already assume |

### Answer line

```
A1: [ A | B ]   scope as written: "Adopt T11 ss.8-15 as the frozen architecture,
                as amended by the recorded A3 and B1 answers."
                conditions: ______________________________________
```


---

## Card 9 of 10 -- A4: Adopt T10-1...T10-7 scoping

### The question (verbatim, T16 ss.4)

**A4:** Adopt T10-1...T10-7 scoping?

**Blocks:** **R6.0.**
**Existing recommendation:** **Yes.** Alternative: proceed without coupling/tokenizer/null/capability/governor guardrails, increasing later rework.
**Recorded dependencies:** "**--** (none recorded)".

### Why this is not one decision (N-03)

`VERIFIED` by reading T10's register rows and checking each against the tree. The seven rules are in **four different states**, and one of them re-decides card 1.

| Rule | What it says (short) | State at HEAD | Anchor |
|---|---|---|---|
| **T10-1** | No `litellm` SDK import in the gateway request path | **Already satisfied.** The only litellm-named import is a local module, and that module imports `httpx`, not the SDK | `api/completions.py:34` -> `providers/litellm_client.py:6` (`import httpx`) |
| **T10-2** | BM25 relevance claims exclude non-Latin scripts until tokenizer coverage proven | **Evidence sentence unverifiable.** The cited `bm25.py:12-14` **does not exist**; there is no BM25 scorer in `src/`, and `routing/intelligent.py` is 0 bytes | `VERIFIED` by absence |
| **T10-3** | Any pre-provider transform must handle `content: null` + in-message tool keys without exception | **Unbuilt.** No transform exists to harden yet | `PROPOSED` |
| **T10-4** | No Class-2 enablement until a deployment verifies `tool_use`/`structured_output` at runtime | **Blocked.** All 14 aliases are `unknown` for both | T14 AF-07; `config.yaml` |
| **T10-5** | Mirror the budget token governor behind `quota_reserved` | **Unbuilt -- and this is card 1's three-axis gap.** Both retry controls are `budget_reserved`-gated | `api/completions.py:1601`, `:1603` |
| **T10-6** | Syntactic detection of in-message tool keys | **Unbuilt** | `PROPOSED` |
| **T10-7** | Non-blocking telemetry write convention; telemetry failure must not affect the request | **Contradicted by live behaviour**: telemetry failure currently returns 500/503 | `api/completions.py:666-677` |

**Three consequences the owner should see before answering.**

1. **T10-5 duplicates B5's substance.** Adopting A4 Option A commits the owner to mirroring the quota governor -- which is precisely the repair B5 and T14's C-07 govern. Yet T16 records A4 as having **no dependencies**, including on B5. A4 and B5 must be recorded consistently or the register will hold two instructions for one repair. Recommend A4 carry an explicit dependency on B5.
2. **T10-2's justification is false at HEAD**, in exactly the way T13's X-1 found BL-26's to be false. The *rule* may still be sound -- non-Latin relevance claims remain unproven, and there is no scorer at all -- but it should not be adopted on a citation to a nonexistent file. Adopt the rule, strike the anchor.
3. **T10-7 contradicts current behaviour and also underlies A3.** ADR-1 labels the inline fail-closed shape as *interim* precisely because telemetry failure blocks the request today. Adopting A4 (build T10-7 first) and A3 (freeze the non-inline target, implement nothing) are mutually consistent **only** in the stated order: T10-7 before any optimisation write. Worth writing down.

### Recommended split (this is a presentation change, not a new decision)

Because the seven rules gate different phases, a single yes/no hides which work is being authorised. A defensible answer format:

| Bucket | Rules | Meaning | Phase |
|---|---|---|---|
| **Ratify now** | T10-1, T10-2 (rule only) | Already true or already required; no code | -- |
| **Build in R6.1** | T10-3, T10-5, T10-6, T10-7 | Real work, mostly on the accounting/transform path | R6.1 |
| **Hold** | T10-4 | Cannot be adopted-and-built; requires capability verification first | R6.5+ |

### Answer line

```
A4: [ A | B ]   if A, answer per bucket:  ratify [ 1,2 ]  build [ 3,5,6,7 ]  hold [ 4 ]
                dependency on B5 acknowledged? [ yes | no ]
                conditions: ______________________________________
```


---

## Card 10 of 10 -- B9: Reconciler placement

### The question (verbatim, T16 ss.5)

**B9:** Reconciler placement: R6.7, with the marker migration in R6.1?

**Blocks:** **Release** (not R6.0, not R6.1). **Depends on:** U9 (already answered).
**Existing recommendation:** **Yes.**
**Not deciding:** what the reconciler does (U9's subject, answered) or whether the marker migration happens (B8, card 7 -- and B9 assumes it).

### What the code does now -- there is no host for a reconciler (N-09)

`VERIFIED`:

| Fact | Anchor |
|---|---|
| There is **no** scheduler, periodic worker, cron entry, or background loop anywhere in `src/` | grep for `asyncio.sleep` / `while True` / `BackgroundTasks` / `scheduler` / `periodic` / `cron` returns only a semaphore release loop (`security/store_executor.py:61`) and two request-scoped retry loops |
| The **only** existing reconciler is a **synchronous admin HTTP endpoint**, not a background job | `api/admin.py:139` -- `POST /api-keys/{key_id}/reconcile-lineage` |
| It requires an administrative identity and records who acted | `api/admin.py:148` (`admin-role` role token), `security/store.py:116` (`updated_by`) |

**The concrete agenda item.** "Reconciler in R6.7" defers *when*, but says nothing about *how it runs*, and the "how" is the expensive part because no runtime host exists. The tree offers exactly three shapes, all of which are real decisions:

| Shape | Precedent | Operational cost |
|---|---|---|
| Manual/admin endpoint, invoked by an operator | Exists (`reconcile-lineage`) | No new surface; requires a human, so drift persists until someone looks |
| New background worker / scheduled job | **None** -- would be the first in the repo | New config, runbook, monitoring, single-instance coordination |
| Lazy sweep on request path | None | Latency risk on the hot path; must not fail a request |

Recommend B9 be answered together with a one-line choice of shape, otherwise R6.7 inherits an unresolved design.

### Option comparison

| | Option A (R6.7; marker migration in R6.1) | Option B (pull reconciler into R6.1) |
|---|---|---|
| R6.1 scope | Bounded; ships the migration only | Materially wider; adds a runtime surface to R6.1 |
| Drift window | Marker rows can accumulate unreconciled until R6.7 | Shorter |
| Risk | R6.1 ships a marker whose consumer does not exist yet -- acceptable only if the marker is inert | R6.1 exit ("safe no-op") now depends on a new worker behaving |

### Answer line

```
B9: [ A | B ]   runtime shape:  [ admin endpoint | background worker | lazy sweep ]
                conditions: ______________________________________
```


---

# PART 3 -- Cross-Cutting Findings Index

These were produced by source-anchoring the ten cards at HEAD. Each is referenced from the card that needs it. None is a decision; all are for the owner to accept, correct, or ignore.

| ID | Finding | Class | Where |
|---|---|---|---|
| **N-01** | A1's "ss.8-15" is a **T11** reference carried bare into T12/T13/T16, where it now resolves to the decision groups. Must be written "T11 ss.8-15" before signature. Highest-consequence wording defect in the ten. | `VERIFIED` | Card 8 |
| **N-02** | A1's containment problem (it structurally contains A3 and B1) is **dissolved**, because both are already answered. A1's recorded dependency ("Group B record") is both too broad and narrower than reality: it depends on A3 and B1 only. | `VERIFIED` | Card 8 |
| **N-03** | A4 is seven rules in four states: T10-1 already satisfied; T10-2 cites a **nonexistent file**; T10-3/6/7 unbuilt; T10-5 is **card 1's substance**. T16 records A4 as dependency-free, including on B5. | `VERIFIED` | Card 9 |
| **N-04** | B5's contract **is already implemented in the store** (`settle_quota:1369`, `reconcile_budget:1233`); it is defeated at the **call site** (`completions.py:603`). B5 Option A is a one-call-site repair, not a store redesign. T16's "Not implemented" overstates the work. | `VERIFIED` + `STATIC-ANALYSIS FINDING` | Card 1 |
| **N-05** | Quota is under-protected on **three** axes, not one: no `max_tokens` narrowing, no unknown-usage break, no flag in settlement. Both retry controls are gated on `budget_reserved`. This is the mechanism behind A2's "quota leak" and T10-5. | `STATIC-ANALYSIS FINDING` | Cards 1, 2, 9 |
| **N-06** | Retry-allowance arithmetic counts unknown usage as **zero** (`completions.py:1604`) while settlement treats it as unknown -- two rules on one datum. | `STATIC-ANALYSIS FINDING` | Card 1 |
| **N-07** | B6 is **already implemented** (`min` at `completions.py:1608`) and is a zero-cost ratification; B7 is not implemented and collides with per-attempt `choose_deployment:1388`. | `VERIFIED` | Cards 1, 3 |
| **N-08** | B8's premise is exact: `_QUOTA_RESERVATIONS` has `status`; `_BUDGET_RESERVATIONS` has none and is hard-deleted. Transferring the pattern changes retention (rows that used to vanish now persist) -- a migration and growth decision. | `VERIFIED` | Card 7 |
| **N-09** | B9 has **no runtime host**: no scheduler or background worker exists in `src/`; the only reconciler is a synchronous admin endpoint. B9 should be answered with an explicit runtime shape. | `VERIFIED` | Card 10 |
| **N-10** | B3 bundles four properties; **three** (operator-only, default-off/fail-closed, per-attempt re-check) already have proven precedent. **Only "per-route" is new** -- no route-keyed config exists anywhere. | `VERIFIED` | Card 5 |
| **N-11** | B4's Option B is mechanically cheap (`Literal["1.1"]` -> add `"1.2"` at `dataset.py:23`, `:57`) and expensive in coordination. "No snapshot fields" means no **new** fields; the pre-routing snapshot is live behaviour and stays. | `VERIFIED` | Card 6 |

---

# PART 4 -- Limitations and non-authority

1. **No decision taken.** All ten remain `OUTSTANDING`. Nothing in this worksheet is an owner answer, an adopted ADR, or a granted gate.
2. **No runtime confirmation.** N-04, N-05, N-06 and every defect on card 2 are `STATIC-ANALYSIS FINDING`: read from control flow at `319a711`, never executed. No test was run, no request made, no provider contacted this session.
3. **No register edited.** T16, the 2026-11-04 supplement, T13, T14, both ADR briefs and every predecessor report are unmodified. This file is the only artefact created.
4. **Answered decisions not restated.** This worksheet does not restate what the thirteen answered decisions were answered *as*, and takes no view on it. Where an unanswered decision is scoped by an answered one, the card states the consequence in either direction. A1 is the load-bearing case.
5. **The baseline is local.** Branch and HEAD were re-measured and match T14. T14 records the branch as 6 ahead / 3 behind origin; this session did not fetch, pull, or reconcile, so a reviewer working from a remote ref must re-anchor every `path:line` above.
6. **Recommendations are not decisions.** Each card reports the *existing* recorded recommendation so the owner can see it. Where a card adds a finding (N-01...N-11), that finding is evidence for the owner's judgement, not a substitute for it.
7. **One editorial proposal, clearly marked as such.** Card 9 recommends answering A4 in three buckets rather than as a single yes/no. That is a presentation proposal to make the answer precise; it grants nothing and decides nothing.

**FINAL STATUS: WORKSHEET COMPLETE -- TEN CARDS AND ONE QUEUE; NOTHING DECIDED; NO GATE GRANTED.**
