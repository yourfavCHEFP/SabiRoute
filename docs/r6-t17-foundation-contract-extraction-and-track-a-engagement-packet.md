# R6 T17 — Foundation Contract Extraction and Track A Engagement Packet

**Status:** extraction and decision preparation only. **This document approves nothing, adopts no ADR, selects no option, grants no G7, contacts no reviewer, and authorises no implementation, test, or U0/U1/R6.1/Track A work.**

**Mode:** documentation extraction with read-only source verification. **Exactly one new file was created.** No existing report, source file, test, config, migration, dataset or dependency was modified.

**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`. Working tree carried no tracked modification before this task and none after it.

**Extraction authority (read, preserved intact, not modified):**
- `docs/r6-t11-r6-readiness-and-implementation-preparation.md` §8 (I1–I9), §15 (T1–T8), §6 (R6.1 conditions), §4 (BL-21)
- `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` §12 (ADR-2 brief), §19–§21
- `docs/r6-t16-r6-decision-option-register.md` (B1, D4, D5; §7 identifier collision; §10 governance status)

**How this document relates to B1, D4 and D5.** T16 already carries the decisions these artefacts feed: **B1** (adopt T11 §8 I1–I9 as the draft foundation contract), **D4** (authorise Track A engagement to schedule, BL-21) and **D5** (adopt T11 §15's T1–T8 numbering as canonical). This document does not answer any of them. It supplies the verbatim source material they require, and prepares the two owner decision requests that T13 §12.3 names as unresolved, plus the engagement packet D4 would release.

---

## 1. Executive summary

**What was extracted.** The nine-contract foundation interface (I1–I9) of T11 §8.2 is reproduced verbatim in §2 with its **Owner column intact**, followed by the T1–T8 Track A numbering of T11 §15 reproduced verbatim in §3. Neither table was re-worded, re-scoped or renumbered.

**Three defects were found during extraction, all in the surrounding text rather than in the contract's shape.** Presented in order of consequence:

1. **The nominal R6.1 insertion window contains a landmine.** T11 §8.3 places construction "immediately before `:1345`", and I9's Owner cell names the guard window `:1309–:1345`. VERIFIED at HEAD: `attempted: list[str] = []` is bound at **`:1311`** — *inside* that window (see `completions.py:1308–1316`). `finish()` reads `attempted` at `:602`, which is the exact mechanism of BL-04. A guard stated as spanning `:1309–:1345` therefore spans the one line whose non-binding already causes a masked 503 and a day-long quota leak. **The window must be re-pinned to strictly after `:1311`.** This is the single most important correction here and it costs nothing to record.
2. **Two protected-surface paths in T11 §15 do not exist as written.** T11 §16 corrected `gateway.py` and only `gateway.py`. VERIFIED at HEAD: there is no `config/validation.py`; the module is `src/sabiroute/config/validation.py` (exposes `validate_config`, `ConfigValidationError`). There is no `src/sabiroute/dataset.py`; the module is `src/sabiroute/intelligence/dataset.py` (contains `PreRoutingFeatureSnapshot`). A reviewer signing **T4** or **T6/T7** against a path that does not exist has signed a surface that does not exist — the same failure class as **X-3** that D5 exists to prevent.
3. **I2 and I5 each contain an internal contradiction, not merely an omission.** T13 §12.3 called them "unspecified". They are worse than unspecified: I2's own cells are mutually unsatisfiable as written, and I5's `max_ratio` is directionally ambiguous. §4 and §5 split each into separately answerable sub-questions.

**The Track A packet is prepared but not issued.** §6 gives per-item requests for T1–T8 (7+1), the verified protected surface, and the acceptance form. Two preconditions gate issuance and neither is met: **D4** authorises engagement only once **D5** has converged the numbering, and no reviewer has been contacted. **Track A status remains `NOT OBTAINED`. Silence is not approval.**

**R6.1 remains blocked.** §7 re-confirms all nine T11 §6 conditions as unmet, and adds that D5/D4 now gate the Track A condition itself.

**No recommendation in this document is a decision.** Every option is `PROPOSED`; every default is `RECOMMENDED`; every decision remains `OUTSTANDING`.

---

## 2. I1–I9 extracted verbatim (T11 §8.2, Owner column intact)

Reproduced without alteration from `docs/r6-t11-r6-readiness-and-implementation-preparation.md` §8.2. Column order, wording, `:919`-style anchors and bold emphasis are the source's. Where a cell is bolded in the source it is bolded here.

| ID | Contract | Input → Output | Owner | Mutability | Failure | Timeout/Cancel | Limits | Telemetry (R6.1: none in snapshot) | Tests |
|---|---|---|---|---|---|---|---|---|---|
| I1 | Immutable original | Request → `FrozenOriginal` deep-frozen copy at `:919` | API layer | Structurally immutable (new list of new dicts — current client shallow-copies, STATIC-ANALYSIS FINDING) | Total (input Pydantic-validated) | n/a (pure) | 256 msgs / 500k chars / 1 MiB | None (never persist text — `dataset.py:52–56,129`) | Frozen-ness, deep-copy isolation, byte-equality pre/post |
| I2 | Canonical representation | FrozenOriginal → deterministic `CanonicalRequest` | R6 module | Frozen | `CanonicalisationError` → fail-to-original | Pure CPU; bound by request deadline only | Output ≤ input; **250 ms / 2× bytes budget must be specified** | None | Determinism, idempotence, size non-expansion, unsupported-shape failure |
| I3 | Effective request | Canonical + policy + capabilities → `EffectiveRequest` (sole provider reader) | R6 module | Frozen; **one per logical request — re-derivation per attempt forbidden** | Never raises (I9) | Pure; request cancel unaffected (no awaits) | **Monotone-shrink: output ≤ original** — load-bearing for reservation `:1199` | Counts + hashes only | Disabled-policy byte-equality, monotone-shrink property, capability preservation, provider-payload snapshot |
| I4 | Transformation metadata | (original, effective, policy, rules) → immutable `TransformationRecord` (ids/versions/counts/hashes/`fallback_reason`; never text) | R6; read-only to API | Frozen tuple | Internal inconsistency → still fail-to-original; record not written | n/a | Scalar-only | **BLOCKED: `PreRoutingFeatureSnapshot` is `extra="forbid"` 1.0/1.1 — R6.1 must emit no snapshot fields (recommendation a); schema-1.2 question deferred** | Redaction, schema-exclusion (no transform keys in snapshot JSON) |
| I5 | Optimization policy | Config/route YAML → `OptimizationPolicy` (`enabled=false` default, strategy/version/`max_ratio`, per-route override) | Config layer, loaded once at startup | Frozen after load (mid-request flip would split one reservation across two requests) | Invalid → startup failure (existing convention) | n/a | `max_ratio` bounds shrinkage; no expansion knob | id/version in I4 only | Default-disabled, unknown-strategy startup failure, route precedence, frozen-after-load |
| I6 | Capability checks | Effective + selected deployment → preserved bool | R6, reusing `capabilities.py:11–60` (no new enum) | Pure | Dropping `tool_use`/`structured_output`/`vision`/multimodal → hard fail to original (eligibility ran at `:1166` on the original) | n/a | — | None in R6.1 | Property: every `classification.required_capabilities` still required post-transform; classification keeps reading the original |
| I7 | Explicit bypass | Operator policy (+ optional documented request signal) → immutable `BypassDecision` evaluated once pre-`:1345` | API layer | Immutable per request | Malformed signal ⇒ ignore signal, use operator default (cf. `:914` strict-marker pattern) | No awaits | — | Operational logs only, never the snapshot | Default-off, operator-on, caller-signal-rejected, malformed-ignored |
| I8 | Validation | Effective → `ValidatedEffective` or failure | R6 module | — | Failures degrade to original, **never 4xx** (no "our optimiser rejects your request" category exists) | — | Same caps as I1 | None | Structural validity, no reintroduction of `:323`-forbidden fields, size monotonicity |
| I9 | Fail-to-original | Any I1–I8 exception → original continues | Call-site guard `:1309–:1345` | — | Swallow-and-degrade (fallback is the tested path); log once at warning with `redact_secrets` | **`CancelledError` must propagate** (ledger `:385–420`, `_compensate_all` `:690–721` depend on it) | — | `fallback_reason` + one counter | Exception-injection ⇒ byte-identical payload; `CancelledError` passthrough; no reservation leak |

### 2.1 Owner column, read as a column

The Owner column is the load-bearing part for Track A scoping, because it decides which protected file each contract lands in. Read down it:

| Owner value (verbatim) | Contracts | Lands in | Track A surface |
|---|---|---|---|
| `API layer` | I1, I7 | `src/sabiroute/api/completions.py` | **T1** |
| `R6 module` | I2, I3, I8 | new `src/sabiroute/request_transform/` | **T1** |
| `R6; read-only to API` | I4 | `request_transform/` + no API write | **T1** |
| `R6, reusing capabilities.py:11–60` | I6 | `request_transform/` + `src/sabiroute/capabilities.py` (read-only) | **T1** |
| `Config layer, loaded once at startup` | I5 | **`src/sabiroute/config/validation.py`** | **T4** (see §5.5) |
| `Call-site guard :1309–:1345` | I9 | `src/sabiroute/api/completions.py` | **T1** (re-pin, §2.2) |

**Six of the nine contracts are T1.** One — **I5** — is **T4**, not T1. That division is easy to miss: I5 reads like a pure value object, but its Owner column names a config layer that is a Track A protected file. §5.5 develops this.

### 2.2 Correction required in I9's Owner cell — `:1309–:1345` is unsafe

VERIFIED at HEAD `319a711`, `src/sabiroute/api/completions.py`:

```
1308	        budget_reserved = True
1309	        ledger.append(("budget", None))
1310	
1311	    attempted: list[str] = []
1312	    last_error_category: str | None = None
1313	    last_deployment: str | None = None
1314	    actual_usage_parts: list[tuple[int | None, int | None, int | None]] = []
1315	    cost_usage_parts: list[tuple[str, tuple[int | None, int | None, int | None]]] = []
1316	    provider_usage_unknown = False
```

The loop entry at `:1345` is `for attempt in range(1, policy.max_attempts + 1):`, confirmed present. Between the budget reservation (`:1308–1309`) and the loop entry (`:1345`) the block binds `attempted` at **`:1311`**.

**Why this matters.** `finish()` reads `attempted` as a free variable bound at `:1311` and has no such parameter — this is the mechanism T11 §7.3 records as D4/BL-04, and T13 §22.4 independently re-derived it ("`finish()` has no `attempted` parameter; it is a free variable bound at `:1311`"). A fail-to-original guard whose stated window begins at `:1309` begins **two lines before `attempted` exists**. Any `finish()` or `_cancelled_finish()` reached from inside that window raises `NameError`, is caught at the handler level, and surfaces as a masked 503 with the reservation still held.

The contracts are pure and call neither function, so nothing in I1–I8 is itself unsafe. The defect is **positional ambiguity in the contract text**, not a present bug: an implementer reading "guard `:1309–:1345`" has no instruction telling them the safe side of `:1311`.

**Correction to record (no option, a straight fix):** I9's Owner cell should read `Call-site guard: strictly after :1311 and before :1345`. I1's construction point (`:919`) is unaffected — it is upstream of the whole block.

---

## 3. T1–T8 numbering preserved (T11 §15)

Reproduced verbatim from `docs/r6-t11-r6-readiness-and-implementation-preparation.md` §15. **This is the numbering D5 would adopt as canonical**, in preference to campaign §15's T1–T7. It is used unchanged throughout §6.

| Item | Change | Touches | Approval | Blocks |
|---|---|---|---|---|
| T1 | Optimisation insertion + effective binding (I1–I9, §8) | `completions.py` | Track A (external reviewer) | R6.1 |
| T2 | O2 pinning + quota governor (BL-06) + `:1601` hardening (BL-02) | `completions.py` | Track A | R6.1 |
| T3 | `optimization_timeout` category | `completions.py` (+ errors taxonomy) | Track A | R6.1 |
| T4 | R6 flag + limits + kill switch | `config/validation.py`, `gateway.py`/`main.py` | Track A | R6.1 |
| T5 | Bounded executor lifecycle (if async stage needed) | `gateway.py`, `main.py` | Track A | R6.1 |
| T6 | Content-free opt store + non-blocking convention (BL-17) | `store.py` (+ migration) | Track A | R6.1 convention / R6.7 writes |
| T7 | D23 settlement fix (BL-01…BL-04) + reconciler (BL-05/BL-15) | `completions.py`, `store.py` (+ migration for marker) | Track A | R6.1 fix / R6.7 ops |
| T8 | Tier-1 estimator + `quota_request_unsupported` + version field (BL-07) | `completions.py`, `security/budgets.py`, `store.py` | Track A | R6.1 |

**Count preserved: 7 + 1.** T11 §1 stated "Track A owns 7+1 sign-offs (§15)" — T1–T7 plus T8. The count is the same under either numbering; what differs is **T7's identity**, and that difference is the whole of X-3.

**Why the numbering is not a cosmetic issue.** T13 §20 item 22 and T16 D5 record it: under campaign §15's T1–T7 there is no T8, so the Tier-1 estimator has no row, and `T7` denotes whichever of two different changes the reader's source happens to contain. T13 §10 states the consequence plainly — "reviewer may sign the wrong artefact (X-3)". A signed approval for the wrong artefact is not a weaker approval; it is an approval of something else.

### 3.1 Path verification against HEAD — two rows need correction before issuance

Each `Touches` path was checked by direct read at `319a711`. T11 §16 corrected one path already (`gateway.py` → `src/sabiroute/gateway.py`); it did not correct the rest.

| T# | Path as printed in T11 §15 | VERIFIED at HEAD | Verdict |
|---|---|---|---|
| T1 | `completions.py` | `src/sabiroute/api/completions.py` ✓ (`:1345` loop entry read) | Resolve by package context; unambiguous |
| T2 | `completions.py` | as T1 ✓ | unambiguous |
| T3 | `completions.py` (+ errors taxonomy) | as T1 ✓ | unambiguous |
| T4 | **`config/validation.py`** | **DOES NOT EXIST at that path.** Actual: `src/sabiroute/config/validation.py` ✓ (`validate_config`, `ConfigValidationError`) | **DEFECT — correct path required** |
| T4/T5 | `gateway.py` | `src/sabiroute/gateway.py` ✓ | Already corrected by T11 §16 |
| T4/T5 | `main.py` | `src/sabiroute/main.py` ✓ (application factory) | unambiguous |
| T6 | `store.py` (+ migration) | `src/sabiroute/security/store.py` ✓ | unambiguous |
| T7 | `store.py` (+ migration) | as T6 ✓ | unambiguous |
| T7/I1 | **`dataset.py`** (cited in I1's Telemetry cell and §8.1) | **DOES NOT EXIST at `src/sabiroute/dataset.py`.** Actual: `src/sabiroute/intelligence/dataset.py` ✓ (`PreRoutingFeatureSnapshot`, `extra="forbid"`, schema `Literal["1.0","1.1"]`) | **DEFECT — correct path required** |
| T8 | `security/budgets.py` | `src/sabiroute/security/budgets.py` (per T11 §11 citation) | consistent with package layout |

**Effect on the packet.** T4 cannot be issued naming `config/validation.py` — a reviewer would be asked to approve changes to a file that is absent from the tree, and would be entitled to reject the packet on that ground alone. The `dataset.py` citation does not sit in a `Touches` cell but is cited by I1 and I4, so the same correction should travel with T1.

**Neither correction changes a decision, an option, a gate or a count.** They are path hygiene of the same class as T11 §16 item 2, which corrected `gateway.py` for exactly this reason and stopped one path short.

---

## 4. I2 owner decision request — Canonical representation

**Question for the owner.** T13 §12.3 item 1 records: *"I2's 250 ms / 2× byte budget is still unspecified. These are the only quantitative bounds in the contract."* This section turns that into answerable sub-questions. **It selects nothing.**

**Recommendation status.** `PROPOSED`. The bounds below are authored here as options for adjudication; none is adopted. I2 remains a `PROPOSED` contract inside a `PROPOSED` ADR (ADR-2 / B1).

### 4.1 The contract's own words

> **I2 | Canonical representation | FrozenOriginal → deterministic `CanonicalRequest` | R6 module | Frozen | `CanonicalisationError` → fail-to-original | Pure CPU; bound by request deadline only | Output ≤ input; **250 ms / 2× bytes budget must be specified** | None | Determinism, idempotence, size non-expansion, unsupported-shape failure**

Three cells, read together, do not agree:

| Cell | Says | Conflict |
|---|---|---|
| Limits | "Output ≤ input" | Constrains output **size** ≤ input size |
| Limits | "250 ms / 2× bytes budget" | A **2× bytes** allowance permits output up to twice input size |
| Timeout/Cancel | "Pure CPU; bound by request deadline only" | Says the **request deadline** is the only time bound |
| Tests | "size non-expansion" | Asserts the property the 2× allowance would violate |

Two pairs are mutually exclusive as written: *output ≤ input* versus *2× bytes*, and *deadline only* versus *250 ms*. A contract cannot be tested against all four statements at once. This is not an omission of detail; it is four statements that cannot all hold.

### 4.2 Sub-question I2-a — what does "2× bytes" bound?

| Option | Statement | Consequence | Verdict |
|---|---|---|---|
| **A** *(recommended)* | "2×" is a **peak working-set** budget: allocations during canonicalisation may reach 2× input bytes; **output** stays byte-≤ input, and "size non-expansion" stands as a test. | Keeps the size guarantee literal; makes "2×" a resource bound rather than a semantic one; no conflict with I3's monotone-shrink. | Recommended |
| **B** | "2×" is an **output-size** budget: `CanonicalRequest` may expand to 2× input bytes. "Output ≤ input" and "size non-expansion" are struck and replaced by "output ≤ 2× input". | Requires stating that I3's shrink absorbs the expansion, and that the reservation (O2, `:1199`, basis = **original** estimate) is therefore unaffected. Canonical forms (key ordering, escaping, defaults) genuinely can expand, so this is implementable where A forbids it. | Live alternative |
| **C** | Drop "2×" entirely. Bound I2 by output ≤ input bytes and the deadline only. | Least machinery, most ambiguity: no number to test against, and "deterministic within a bound" becomes untestable. | Weakest |

**What adopting A costs:** any canonicalisation rule whose canonical form is larger than its input must be rejected as an unsupported shape rather than performed. **What adopting B costs:** I2 can be locally non-shrinking, so the reservation guarantee has to be re-argued through I3 and B6 rather than being true by inspection at I2.

**Note on the reservation argument — this is why the two options are not symmetric.** Per T11 §9 and §8.3, `reserved_tokens = estimated_input + max_tokens` (`:1199`) is computed from the **original** estimate (`:935`). The provider never sees I2's output; it sees I3's. So under **both** options the reservation is bounded provided I3 enforces ≤ original, and B6 ("monotone-shrink permanent unless the reservation is re-baselined") is what makes that permanent. The choice between A and B is therefore about **what I2 is allowed to do, not about accounting safety**. Accounting safety lives entirely in I3 + B6. Stating that explicitly prevents a reviewer or implementer from assuming B needs new reservation work — it does not.

### 4.3 Sub-question I2-b — "250 ms" versus "bound by request deadline only"

The Timeout/Cancel cell says the deadline is the only bound; the Limits cell imposes 250 ms. Three coherent readings:

| Option | Statement | Consequence |
|---|---|---|
| **A** *(recommended)* | 250 ms is a **hard cap, independent of the deadline**: I2 stops at 250 ms whatever remains of the 300 s. | Predictable worst case; a request with 290 s left still spends ≤ 250 ms. Makes the bound testable in isolation. |
| **B** | `min(250 ms, remaining deadline)` — the cap is subordinate to the deadline. | The cap is not a constant, so a test must control both. Correct where the request is already near deadline. |
| **C** | Deadline only; 250 ms is guidance, not a bound. | Restores the Timeout cell literally and deletes the quantitative bound T13 §12.3 flagged as one of only two in the contract. |

**Bound-breach behaviour must also be pinned.** The Failure cell supplies the only admissible answer: exceeding either bound raises `CanonicalisationError` and **fails to original** (I9). It must **not** truncate. Truncating a canonical form silently damages the request, which T11 §16 invariant set (invariant 14) forbids as "no silent damage"; and I9's swallow-and-degrade path exists precisely so the original continues intact.

### 4.4 Sub-question I2-c — the 250 ms is a synchronous event-loop stall

This is a consequence the contract does not state, and it is the item most likely to be missed in review.

I2 is declared "Pure CPU" and "no awaits", and T11 §9 states "R6.1 pure functions need no executor". A pure synchronous function called from `completions.py` runs on the event loop. Therefore:

- **No timer can interrupt it.** A synchronous loop has no await point, so `asyncio` cannot deliver `CancelledError` mid-computation. "250 ms" is therefore **not** a timeout in any runtime sense — it is a policy number that can only be enforced by capping input size before entry, or by checking elapsed time at internal checkpoints and abandoning.
- **The event loop is blocked for up to the bound, per request.** Under concurrency this is a throughput ceiling, not merely a latency cost. A 250 ms cap means a 250 ms stall whenever I2 is enabled and its work is maximal.

| Option | Statement | Consequence |
|---|---|---|
| **A** *(recommended)* | Keep I2 synchronous; **reduce the cap to a stall-safe value** (order tens of milliseconds) and enforce it via I1's input caps plus in-loop elapsed checks. Record the stall explicitly as an accepted, bounded cost. | Preserves "no executor" (T11 §9) and keeps T5 out of the critical path. Requires the cap to be meaningfully below 250 ms. |
| **B** | Keep 250 ms and move I2 to `to_thread`. | Makes the bound enforceable as a real timeout, but **pulls T5 (bounded executor lifecycle) into R6.1's critical path** and moves I2 off the "no executor" assumption in T11 §9. |
| **C** | Keep 250 ms synchronous and accept the stall. | Cheapest to write; hardest to defend under load. If chosen it should be chosen knowingly, and stated in the signature package. |

**Relation to I9.** I9 requires `CancelledError` to propagate. Under A and C there is no cancellation point inside I2, so I9's obligation is discharged at entry and exit only — that is consistent, but it should be said, because a reviewer reading "`CancelledError` must propagate" next to "no awaits" will otherwise reasonably ask how.

### 4.5 What answering I2 does and does not do

| Effect | True? |
|---|---|
| Fixes the only quantitative bounds in the foundation contract (with I5, T13 §12.3) | Yes |
| Adopts ADR-2 or answers B1 | **No** — B1 remains `OUTSTANDING` |
| Changes I3, B6, or the reservation argument | **No** — accounting safety is I3 + B6, unchanged by this choice |
| Authorises any implementation of I2 | **No** |
| Decides whether I2 runs on the event loop | Only if I2-c is answered; otherwise the assumption stays implicit |

**Minimum answer the owner should give:** I2-a (A/B/C), I2-b (A/B/C), I2-c (A/B/C). The three are independent; answering one does not answer the others.

---

## 5. I5 owner decision request — Optimization policy

**Question for the owner.** T13 §12.3 item 2 records: *"I5's configuration schema is described, not written."* §5.2–§5.5 show that the description is also ambiguous in two places and mis-justified in a third. **It selects nothing.**

**Recommendation status.** `PROPOSED`, as for I2.

### 5.1 The contract's own words

> **I5 | Optimization policy | Config/route YAML → `OptimizationPolicy` (`enabled=false` default, strategy/version/`max_ratio`, per-route override) | Config layer, loaded once at startup | Frozen after load (mid-request flip would split one reservation across two requests) | Invalid → startup failure (existing convention) | n/a | `max_ratio` bounds shrinkage; no expansion knob | id/version in I4 only | Default-disabled, unknown-strategy startup failure, route precedence, frozen-after-load**

### 5.2 Sub-question I5-a — `strategy` with no registry

ADR-2 §12.1 excludes a registry ("No registry, no I/O, no provider adapters"). T11 §8.2 says the package is "value objects + pure functions, ~250 LOC, no registry". I5 nevertheless carries a `strategy` field, and its Tests cell requires an "unknown-strategy startup failure" — which presupposes a closed set of known strategies.

| Option | Statement | Consequence |
|---|---|---|
| **A** *(recommended)* | `strategy` is a closed enum containing **exactly one** admissible R6.1 value (e.g. `passthrough`); every other value fails startup. The field exists so I4 can record an id/version, and grants nothing. | Honest affordance: the knob exists, admits one value, and cannot silently grow. Matches "no registry". |
| **B** | Forward-declare the members and reject all of them at startup until implemented. | Schema is stable early, but a config that validates then refuses is confusing and hard to test. |
| **C** | Omit `strategy` from R6.1; add it with the first real strategy. | Cleanest surface, but I4's "policy id/version" then has no id to record. |

**What answering forces:** whether the field is a real selector or a placeholder. Under A and C the "unknown-strategy startup failure" test has a trivial subject; under B it has to enumerate. All three are consistent with "no registry"; none of them permits a strategy table.

### 5.3 Sub-question I5-b — `max_ratio` direction, scope and range

"`max_ratio` bounds shrinkage" is directionally ambiguous, and the two readings are opposite:

| Reading | `max_ratio = 0.8` means | Implementation |
|---|---|---|
| **Retention semantics** *(recommended)* | Output is **at least 80%** of input — i.e. shrink is **capped at 20%**. | `len(effective) >= 0.8 * len(original)` |
| **Shrinkage semantics** | Shrink is **capped at 80%** — i.e. output may fall to 20% of input. | `len(effective) >= (1 - 0.8) * len(original)` |

These produce different behaviour on the same config value and would each pass a test written by their own author. **Recommended: adopt retention semantics and rename the key to make it unmistakable** (`min_retention_ratio`), because "max" attached to "ratio" reads naturally as a ceiling on the ratio itself, which is the *retention* reading — and a name that can be misread by a competent implementer is a defect in the contract, not in the implementer.

Also unstated and needed: **scope** (per-request, per-message, or per-route), **range** (`(0, 1]` is the only sane domain), **default when `enabled=false`** (the value must not be required to be numerically meaningful while disabled), and **unit** (bytes or tokens — I1 caps are in chars/msgs/bytes, so bytes is consistent).

**No value of `max_ratio` may permit expansion** — the Limits cell says "no expansion knob", and B6 makes monotone-shrink permanent unless the reservation is re-baselined. The schema must make an expansion-permitting combination **unrepresentable**, not merely undocumented.

### 5.4 Sub-question I5-c — the freeze rationale is misattributed, and the resolution point is unpinned

**The stated reason is wrong.** I5's Mutability cell justifies "frozen after load" as "mid-request flip would split one reservation across two requests". It would not. The reservation is computed once from the **original** estimate: `reserved_tokens = estimated_input + max_tokens` at `:1199` from the estimate at `:935` (T11 §9, O2). `estimated_input` does not consult the optimisation policy at all, so a policy flip mid-request cannot alter or split a reservation.

**The requirement stands; the justification does not.** The real reasons to freeze are the ones already decided elsewhere:

- I3 requires **one** effective object per logical request, and B7 forbids per-attempt re-derivation. A policy that could change mid-request would give two attempts two different effective requests, invalidating that identity.
- I9 requires that fallback **reuse the same effective object**.
- I4 records one policy id/version per request; a second value would make the record ambiguous.

**Why it matters practically:** an implementer who takes the stated rationale at face value will look for, and fail to find, a reservation-splitting hazard, and may conclude the freeze is unnecessary. The correct guard is *single construction point + no re-derivation*, which is a T1/I3 obligation, not an accounting one.

| Option | Statement | Consequence |
|---|---|---|
| **A** *(recommended)* | Keep "frozen after load"; **restate the reason** as I3 identity + B7 + I4 record integrity, and note explicitly that the reservation is unaffected. | Correct guard is aimed at the correct hazard. Costs one sentence. |
| **B** | Keep the text as written. | An existing, load-bearing requirement rests on a false premise. |

**Resolution point is unpinned.** "per-route override" does not say *which route*. It must resolve from the **policy/classification route** known before the construction point (`:966`), **not** from the deployment selected inside the loop at `choose_deployment` (`:1388`). Resolving per selected deployment would make the policy per-attempt — precisely the re-derivation B7 forbids, and structurally the same error T13 §12.4 records as **`ADR-2/C-2`** for the insertion point ("selection is `choose_deployment` *inside* the loop, so adopting CD2 literally forces per-attempt transformation and breaks B7"). This is the same mistake in a second place; it should be closed in the same ruling.

### 5.5 Sub-question I5-d — I5 is a Track A surface (T4), not free R6 module work

I5's Owner cell is `Config layer, loaded once at startup`. The Config layer is `src/sabiroute/config/validation.py` — VERIFIED present at HEAD, exposing `validate_config()` and `ConfigValidationError`. That file is named in **T4** ("R6 flag + limits + kill switch", T11 §15) and appears in the protected-surface list ("Silence is not approval").

**Consequence, and it is a sequencing consequence rather than a scoping opinion:** the I5 schema cannot be *written* without landing in a Track A protected file. So I5 sits behind **BL-21** just as firmly as I1–I4 and I6–I9 do through T1 — but on a **different** row (**T4**, not T1). §2.1's table shows this division; it is easy to miss because I5 reads like a pure value object.

Two further interactions to pin while the schema is written:

1. **"Invalid → startup failure (existing convention)"** must be verified against `validate_config`'s actual behaviour rather than assumed; I5 cites the convention, not the code. A reviewer signing T4 should confirm the convention is what I5 says it is.
2. **Startup validation versus the runtime kill switch.** T4 introduces a kill switch; I5 makes invalid policy a *startup* failure. These are different mechanisms, and the contract does not say how they compose. If disabling the optimiser is a **config value**, any change to it is a policy flip — which I5 forbids. If it is an **operator surface outside config**, the schema must say so. Leaving it unstated invites a kill switch that quietly violates the freeze.

### 5.6 What answering I5 does and does not do

| Effect | True? |
|---|---|
| Writes the I5 configuration schema | **No** — this specifies what the schema must mean; it does not author it |
| Requires a registry or provider adapters | **No** — every option in §5.2 stays within "no registry" |
| Answers B1, B3, B6 or B7 | **No** — those remain `OUTSTANDING`; I5 must be consistent with B6/B7, not a substitute for them |
| Records that I5 needs Track A **T4** | Yes — §5.5, a sequencing fact |
| Authorises the config change | **No** |

**Minimum answer the owner should give:** I5-a (A/B/C), I5-b (retention vs shrinkage, plus scope/range/default), I5-c (restate the rationale — yes/no, and pin the resolution point), I5-d (confirm T4 coupling, and state whether the kill switch is config or operator surface).

---

## 6. BL-21 — Track A engagement packet

**Status of BL-21: `NOT OBTAINED`.** No reviewer has been contacted. No prompt has been issued. No sign-off exists for any of T1–T8. **Silence is not approval** (T11 §15, T13 §21).

**Status of this packet: PREPARED, NOT ISSUED.** It is material for the owner to issue after **D4** is recorded, not an issued request.

### 6.1 Preconditions — two, and neither is met

| # | Precondition | State | Why it gates issuance |
|---|---|---|---|
| 1 | **D5** — adopt T11 §15's T1–T8 as canonical | `OUTSTANDING` | Under campaign §15's T1–T7, `T7` denotes two different changes and T8 has no row. D4 depends on D5 for exactly this reason (T16 D4/D5, X-3). A packet issued while numbering is unresolved can secure an approval of the wrong artefact. |
| 2 | **D4** — authorise Track A engagement to schedule | `OUTSTANDING` | Without D4 nothing is authorised to be sent. |

**Third precondition, pack hygiene:** §3.1's two path defects. These do not need an owner decision — they need correcting in the packet text. A packet naming `config/validation.py` when no such file exists invites rejection on its face.

### 6.2 Protected surface, verified at HEAD

T11 §15: "Protected (campaign §15 + conflict controls; path corrected: `gateway.py` lives at `src/sabiroute/gateway.py`): `api/completions.py`, `src/sabiroute/gateway.py`, `main.py`, `config/validation.py`, `security/store.py`, migrations, dataset-related files. Verified present at HEAD. Silence is not approval."

Re-verified at `319a711`, with §3.1's corrections applied:

| Protected surface | Verified path | T# |
|---|---|---|
| Chat completions handler | `src/sabiroute/api/completions.py` | T1, T2, T3, T7, T8 |
| Gateway wiring | `src/sabiroute/gateway.py` | T4, T5 |
| Application factory / lifespan | `src/sabiroute/main.py` | T4, T5 |
| Config validation | **`src/sabiroute/config/validation.py`** (corrected from `config/validation.py`) | T4 |
| Persistence | `src/sabiroute/security/store.py` | T6, T7, T8 |
| Migrations | `migrations/` | T6, T7 |
| Dataset / snapshot | **`src/sabiroute/intelligence/dataset.py`** (corrected from `dataset.py`) | T1 (I1/I4 citation) |
| Budget estimation | `src/sabiroute/security/budgets.py` | T8 |

### 6.3 Per-item request — T1–T8 (7 + 1)

Each row states what the reviewer is being asked, the surface, and what a signature attests. **Signature attests to the change and its protected surface. It does not attest to correctness of accounting, does not grant G7, and does not freeze the architecture** — those are separate acts (§6.5).

| T# | What Track A is asked to approve | Surface | Reviewer needs | Signature attests |
|---|---|---|---|---|
| **T1** | Insertion of I1–I9 and effective-request binding, once per logical request, before loop entry. Includes the §2.2 re-pin (strictly after `:1311`). | `src/sabiroute/api/completions.py`; new `src/sabiroute/request_transform/`; read-only `src/sabiroute/capabilities.py` and `src/sabiroute/intelligence/dataset.py` | The I1–I9 table (§2), the corrected insertion point (§2.2), I2 answers (§4) | That the protected handler's lifecycle order is preserved and the transform cannot alter admission, reservation or settlement |
| **T2** | O2 pinning + quota token governor (BL-06) + `:1601` unknown-break hardening (BL-02). | `completions.py` | T11 §9 governor anchors; B5/B6/B7 rulings | That retry arithmetic stays pinned to the original estimate and quota gains the governor budget already has |
| **T3** | New `optimization_timeout` failure category, distinct from provider `deadline_exceeded`. | `completions.py` + errors taxonomy | T11 §13; the deadline mechanism (`api/deadline.py`, `sabiroute_deadline_at`) | That a new failure category is added without reclassifying existing ones |
| **T4** | R6 flag + limits + kill switch; **and the I5 configuration schema** (§5.5). | **`src/sabiroute/config/validation.py`**; `src/sabiroute/gateway.py`; `src/sabiroute/main.py` | I5 answers (§5); the kill-switch/startup-failure composition (§5.5 item 2) | That config validation extends without weakening existing validation, and that the kill switch cannot become a policy flip |
| **T5** | Bounded executor lifecycle — **only if an async stage is needed.** | `src/sabiroute/gateway.py`, `src/sabiroute/main.py` | I2-c (§4.4): if I2 stays synchronous, T5 is not needed for R6.1 | That any added pool is bounded and drained on shutdown |
| **T6** | Content-free optimisation store + non-blocking write convention (BL-17). | `src/sabiroute/security/store.py` (+ migration) | T11 §14.5; ADR-1 prerequisites P1, P3, P4 | That a new store surface is content-free and that telemetry failure cannot change a request's outcome |
| **T7** | D23 settlement fix (BL-01…BL-04) + reconciler (BL-05/BL-15). **This is the row X-3 makes ambiguous under the T1–T7 numbering.** | `src/sabiroute/security/store.py`, `completions.py` (+ migration for the terminal marker) | T11 §7.4 settlement contract; T13 §13 spec-5 re-derivation; B5, B8, B9 | That settlement semantics move to any-unknown→full-estimate, and that partial sums stop being treated as complete |
| **T8** | Tier-1 estimator: quota extras parity, `quota_request_unsupported`, version field (BL-07). | `completions.py`, `src/sabiroute/security/budgets.py`, `src/sabiroute/security/store.py` | T11 §11 tiers and labelling; A2 | That quota estimation gains parity with budget admission without touching the frozen budget path |

**Dependency note.** T1's surface is the widest and is the only row touching a new package. T4 is the only row that is *not* primarily `completions.py`. T7 is the only row whose identity changes between the two numberings — which is why D5 precedes D4.

### 6.4 Acceptance form

A signature satisfies BL-21 for its item only when it is **written**, **names the T# and the numbered change**, and **is scoped to that item**. Specifically:

| Field | Required |
|---|---|
| Item | The T# **and** the change title, from the T1–T8 table (§3) |
| Surface | Path(s) from §6.2, as corrected |
| Basis | The contract/anchors the reviewer actually read |
| Scope | Which of R6.1 / R6.7 the approval covers (T6 and T7 each span both — see the `Blocks` column) |
| Conditions | Any, recorded rather than assumed |

**Deferral is a valid answer and is not approval.** T11 §6 condition 2 admits "written deferral per item". A deferral must name the item and be written; an unanswered request is neither approval nor deferral.

### 6.5 What Track A does not approve

| Act | Owner of the act | Track A's role |
|---|---|---|
| R6.0 architecture freeze (§§8–15) | **Owner** (BL-22) | None |
| G7 implementation authorisation | **Owner** (BL-23) | None |
| Foundation contract draft (I1–I9) | **Owner** (B1) | Informs via T1/T4 surfaces |
| Settlement policy (B5) | **Owner** | Informs via T7 |
| Scope, bypass, Phase-13 keep-out (B2, B3, B4) | **Owner** | Informs via T1/T4 |

Track A approval of a change does not imply the change is authorised to be made. **T1–T8 sign-off is one of nine R6.1 conditions (§7), not the gate itself.**

---

## 7. R6.1 remains blocked — confirmation against all stated conditions

**R6.1: NOT READY.** Unchanged by this document. Re-confirmed against all nine T11 §6 conditions, none of which this extraction alters.

| # | T11 §6 condition (verbatim) | State | Gating artefact |
|---|---|---|---|
| 1 | "Written R6.0 owner approval (BL-22) **and** scoped G7 authorization (BL-23)." | **UNMET** | Both `OUTSTANDING`; G7 never requested (T13 §19, T16 §10) |
| 2 | "Track A sign-off on T1–T7 + Tier-1 estimator, or written deferral per item (BL-21, §15)." | **UNMET** | `NOT OBTAINED`; §6 packet prepared, not issued; gated by D5 → D4 |
| 3 | "Adopted foundation contract: §8 (I1–I9) approved **plus** rulings on scope (BL-27), bypass authority (BL-32), Phase-13 keep-out (BL-31), monotone-shrink permanence (T11-C Q7), and per-attempt re-derivation forbidden." | **UNMET** | B1 `OUTSTANDING`; B2/B3/B4/B6/B7 `OUTSTANDING`; I2/I5 gaps now specified (§4, §5) but undecided |
| 4 | "Settlement-defect specifications accepted as R6.1 must-fix with regression tests first: BL-01, BL-02, BL-03, BL-04." | **UNMET** | A2/B5 `OUTSTANDING`; U0 authorised by D1/D2/D3 only |
| 5 | "Quota governor (BL-06) + Tier 1 estimator (BL-07) + T10-6 detection (BL-08) + null-hardening (BL-18) + non-blocking convention (BL-17) in the R6.1 unit plan (§17)." | **UNMET** | Units specified in T11 §17; none authorised |
| 6 | "Role-aware freeze decision for the Class-1 FULL claim (BL-09); otherwise R6.1 ships Class-1-gated-behind-bypass for system/developer-role traffic." | **UNMET** | C3 `OUTSTANDING` |
| 7 | "Budget schema terminal marker decision (BL-15) if the reconciler is in R6.1 scope; else reconciler explicitly deferred to R6.7 with stuck rows visible." | **UNMET** | B8/B9 `OUTSTANDING` |
| 8 | "Streaming-disconnect test (BL-14) designed; `GeneratorExit` hazard adjudicated by runtime test under R6.1." | **UNMET** | U10 specified, not authorised |
| 9 | "E3 harness + §17 B1 subset scoped as the R6.1 exit gate (BL-20)." | **UNMET** | U11 specified, not authorised |

**Aggregate position, unchanged and corroborated by T16 §10:**

| Statement | Status |
|---|---|
| R6.0 architecture freeze | `CONDITIONALLY READY` — not frozen |
| R6.1 overall | **`NOT READY`** |
| G7 | `NOT GRANTED` |
| Track A | `NOT OBTAINED` |
| ADR-1 / ADR-2 | `PROPOSED` — not adopted |
| Owner decisions recorded | **0 of 23** |

**What would change this, and what would not.** Answering I2 (§4) and I5 (§5) closes a *content* gap inside condition 3; it does not satisfy condition 3, which additionally requires B1, B2, B3, B4, B6 and B7. Correcting the §2.2 insertion point and the §3.1 paths closes *defects*; neither is a condition. **Nothing in this document moves R6.1 forward by itself.** The nearest genuine movement available is D1/D2/D3, which unblock U0 without touching any architecture question (T13 §20, §10).

---

## 8. What this document does not do

| Prohibition | Status |
|---|---|
| Approve, adopt or select any option | **Not done** — every option `PROPOSED`, every decision `OUTSTANDING` |
| Modify any source, test, config, migration, dataset, dependency | **Not done** — zero writes outside this file |
| Contact a reviewer or issue a Track A request | **Not done** — packet prepared only |
| Execute a test, provider call or benchmark | **Not done** |
| Adopt ADR-1 or ADR-2 | **Not done** — both remain `PROPOSED` |
| Record an owner decision | **Not done** |
| Renumber T1–T8 or rename I1–I9 | **Not done** — extracted verbatim; §3.1 corrects *paths*, not numbering |
| Invent an option where the register has none | **Not done** — where the corpus records no option (e.g. GROUP-C/C1), none was added here |

**Corrections recorded here that are not options:** the §2.2 insertion-point re-pin and the §3.1 path corrections are statements of fact about the tree at `319a711`, not proposals. They were verified by direct read. They change no decision, gate or count.

---

## 9. Document control

| Field | Value |
|---|---|
| Created by | T17 extraction mission (verbatim extraction of T11 §8/§15 + read-only verification at HEAD + I2/I5 decision preparation + BL-21 packet) |
| Created on | 2026-11-05 |
| Repository baseline | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` (verified; unchanged before and after) |
| Files created | This file — **one file, no others** |
| Files modified | None |
| Source, config, tests, migrations, dependencies | Untouched |
| Tests executed · provider calls · benchmarks · installs | None |
| Commits, pushes, deploys, resets, cleans, stashes, branch switches | None |
| Reviewer contacted | No |
| **Authority** | **Decision support only. Approves nothing; adopts no ADR; grants no G7; obtains no Track A sign-off; authorises no implementation.** |

**Extraction fidelity note.** The tables in §2 and §3 are copied from their sources without emendation, including the source's own emphasis and its `:919` / `:1345` anchors. Where this document disagrees with a source it says so in a numbered correction (§2.2, §3.1) and leaves the source text intact rather than editing it.

**FINAL STATUS: T17 COMPLETE — I1–I9 AND T1–T8 EXTRACTED VERBATIM; TWO DECISION REQUESTS AND ONE ENGAGEMENT PACKET PREPARED; NOTHING ISSUED, NOTHING DECIDED, NO GATE MOVED.**
