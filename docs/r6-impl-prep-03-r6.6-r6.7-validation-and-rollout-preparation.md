# R6-IMPL-PREP-03 — R6.6–R6.7 Validation and Rollout Preparation

**Status: PREPARATION ONLY — R6.6 AND R6.7 IMPLEMENTATION NOT AUTHORISED.**
**Programme:** SabiRoute Build Archive · **Workstream:** R6 — Intelligent Input Optimization
**Prompt:** R6-IMPL-PREP-03 · **Terminal:** Claude Desktop Chat 5
**Baseline of record:** `feat/sabiroute-routing-foundation` @ `319a711`
**Files created:** this document only. **Files modified:** none.
**No implementation. No tests. No benchmarks. No provider spend. No migrations. No commits. No staging. No deployment. No production change.**

---

## 0. What this document is, and what it is not

This is a **validation and rollout programme** — a specification of *what evidence will be
required, how it will be obtained, and what would stop a release*. It is not evidence itself.

| This document | Is | Is not |
|---|---|---|
| Thresholds | slot identifiers + derivation rule | **numeric values** (none appear anywhere below) |
| Acceptance | criteria + evidence source | a pass claim |
| Adversarial cases | a catalogue | executed tests |
| Observability | a proposal over existing surfaces | an implemented schema |
| Rollout | staged plan with pre-registered stop rules | an authorisation to deploy |
| Implementation prompts | drafted and **held** | issued |

**No claim is made that R6.6 or R6.7 passed, or that any gate is met.** No benchmark has been
run for this document. §7 records that every prerequisite decision remains `PENDING`.

### 0.1 Evidence labels

Used per the repository standard and consistent with T11/C-01:

- **VERIFIED (source)** — read directly from the tree at `319a711`.
- **INFERRED** — reasoned from structure; not executed.
- **UNVERIFIED** — asserted by a prior document, not independently checked here.
- **UNRESOLVED** — no owner decision exists; nothing is assumed.

### 0.2 Known-good grounding carried into this programme

Three facts from prior work materially shape everything below and are restated so this document
can be read standalone:

1. **The stock `litellm.compress()` path is rejected.** Its output contract depends on a
   retrieval round-trip SabiRoute does not implement — it replaces message content with a stub
   instructing the model to call `litellm_content_retrieve`. Removing the injected tool does not
   remove the instruction. This is a **correctness** defect in the integration, not a hardening
   gap (`r6-architecture-decision-pack.md:25–31`, VERIFIED (source)).
2. **Telemetry schema version `1.1` is hard-rejected on mismatch.** `dataset.py:341–344` rejects
   any attempt record whose schema version is not exactly `"1.1"`, so a transformation telemetry
   field is a **coordinated Track A schema change, not an additive one** (pack `:37–39`,
   VERIFIED (source)).
3. **B5 is not approved.** The settlement contract R6.1 implements is `PENDING` / `NOT APPROVED`
   (`r6-t16-r6-decision-option-register.md:529`). R6.6 benchmarks a pipeline whose accounting
   semantics are themselves undecided — see §7.1.

---

## 1. Benchmark protocol

### 1.1 Purpose and the one claim it may support

The programme exists to answer exactly one question:

> For a defined population of inputs, does the R6 transformation reduce input cost **without
> changing meaning, routing, tool semantics or accounting correctness** — and by a magnitude that
> satisfies thresholds fixed in advance?

**Prohibited inference (explicit):** a measured reduction in bytes or tokens is **never** evidence
of preserved meaning. Mechanical reduction and semantic preservation are separate gates, measured
separately, and neither may be cited to support the other (§2.3).

### 1.2 Measurement bases — three distinct quantities

These are separate measurements and must never be summed, averaged together, or reported as one
number:

| ID | Quantity | Basis | Notes |
|---|---|---|---|
| **MB-1** | Canonical serialized UTF-8 byte reduction | canonical serialisation of the message array, byte length before vs after | Deterministic; no tokenizer involved |
| **MB-2** | Token reduction | the **approved estimator** (§1.3) | Basis is unresolved — see §7.2 |
| **MB-3** | Provider-billed token delta | provider-reported `usage` on paired calls | **Not obtainable in this programme** — requires real provider spend, which is prohibited |

MB-3 is named so that no reader mistakes MB-1/MB-2 for billing truth. Any claim of *cost* saving
requires MB-3 and is **out of scope until separately authorised**.

### 1.3 The estimator problem (blocking, not a detail)

MB-2 requires "the approved estimator". **No approved estimator exists.**

- The Tier-1 estimator requires Track A sign-off; that sign-off is **not obtained** (BL-21,
  `r6-t11-...:99`).
- All 14 configured aliases are **UNKNOWN** for tokenizer family (BL-28).
- Deployment-tokenizer policy is **CONDITIONAL**; compatibility matrices are pending (BL-19,
  T11 §5 item 16).
- `estimate_input_tokens(...)` exists and is used for budget/quota estimation, but it is a
  **budgeting heuristic**, not a calibrated tokenizer. Using it for MB-2 without saying so would
  be a measurement claim resting on an unvalidated instrument.

**Consequence:** MB-2 cannot be preregistered against a named-estimator basis today. Either the
estimator is signed off, or MB-2 is explicitly recorded as *"budget-heuristic basis, not
tokenizer basis"* — an **owner** choice (§7.2). This programme does not select one.

### 1.4 Preregistration

Thresholds are registered **before** the first measurement, and the registry is frozen:

1. A threshold registry is created containing, for every criterion in §2, a **slot ID** and an
   **owner-assigned value**. No value is present in this document.
2. The registry is committed and its **SHA-256 recorded** together with the corpus digest and the
   estimator/tokenizer identification, before any run.
3. Any later change to a slot value, the corpus, or the estimator **voids the run** and requires a
   fresh registry; the superseded run is retained, not deleted.
4. **No post-hoc threshold.** A threshold proposed after seeing results is recorded as a *new*
   registry version and cannot validate the run that motivated it.

The registry digest is the anti-post-hoc mechanism; without it the whole gate is decorative.

### 1.5 Paired-case design (equivalence requirement)

Original and transformed inputs must be benchmarked on **equivalent cases**:

- Each case is a **pair**: the original payload and the transformed payload derived from it, with
  an immutable case ID shared between them.
- Both members of a pair are evaluated with **identical** model alias, parameters, seed (where the
  provider supports one), deadline, and routing configuration.
- A transformation that changes the case's *identity* (message count, role sequence, tool
  declarations) is recorded as a **structural mutation**, not a reduction, and is excluded from
  reduction statistics — it belongs in §3 (adversarial/structural), not in MB-1/MB-2.
- Cases where the transformation is bypassed remain in the population and are counted as
  **zero reduction with a named bypass reason** (§4.2), not dropped. Dropping bypassed cases is the
  easiest way to manufacture an average.

### 1.6 Input classes

Every case carries an input-class tag; results are reported **per class**, never only in aggregate:

| Class | Description |
|---|---|
| `plain-short` | single turn, small, no tools |
| `plain-long` | single turn, large context |
| `multi-turn` | conversational history |
| `tool-bearing` | tool declarations and/or tool-result messages (Class-1/Class-2 per T9-B) |
| `structured-output` | `response_format` constrained |
| `privileged-role` | system/developer-role traffic (role-freeze gate applies) |
| `non-latin` | Yoruba, Arabic, CJK, emoji (BL-19; claims excluded until corpus proven) |
| `degenerate` | empty, null-content, whitespace-only, single-token |
| `adversarial` | §3 catalogue |

Tokenizer coverage is reported per class. A class with **no** tokenizer identification is reported
as **UNKNOWN**, never as passing.

### 1.7 Mechanical overhead measurement

- **Latency:** transformation wall-clock time is measured separately from provider latency; reported
  as its own distribution, never folded into end-to-end latency.
- **Resource:** peak memory and allocation attributable to the transformation step.
- Overhead is measured **on the same hardware and process** as the control run, in the same session
  shape, to avoid comparing across environments.
- Deadline interaction is recorded: the transformation executes inside the request deadline
  (the lifecycle places optimisation after budget reservation and before the retry loop,
  T11 §8.1), so its cost is *taken from the provider's budget*, not added outside it.

### 1.8 Run isolation and reproducibility

- No real provider spend. Provider interaction is **stubbed or recorded-replay** only.
- Each run records: corpus digest, threshold-registry digest, estimator/tokenizer identification,
  code revision (`319a711` or successor), configuration, and environment shape.
- A run that cannot reproduce its corpus and registry digests is **not evidence**.

### 1.9 Reporting rules

- Report per-class and per-pair; aggregate figures are supplementary only.
- Report **bypass rate** and **failure-attribution rate** alongside every reduction figure.
- Report UNKNOWN outcomes explicitly. **An unreported UNKNOWN is treated as a failure**, not
  silently excluded (see §2.4).
- Never report a single "efficiency score" combining mechanical and semantic results.

---

## 2. Mechanical and semantic acceptance matrix

### 2.1 Status vocabulary

Every criterion resolves to exactly one of: **PASS**, **FAIL**, **UNKNOWN**, **NOT-RUN**.
`UNKNOWN` is a first-class outcome and never collapses into PASS. At the time of writing **every
row is NOT-RUN** — this document establishes no result.

### 2.2 Mechanical gate (blocking)

| ID | Criterion | Measured by | Threshold slot | Failure attribution |
|---|---|---|---|---|
| M-1 | Canonical UTF-8 byte reduction | MB-1 over paired corpus | `THR-M1` | per class; bypassed cases reported separately |
| M-2 | Token reduction, approved estimator | MB-2 | `THR-M2` | **UNKNOWN basis unless §7.2 resolved** |
| M-3 | Transformation latency overhead | §1.7 distribution | `THR-M3` | p50/p95/p99 per class |
| M-4 | Resource overhead | §1.7 peak memory | `THR-M4` | per class |
| M-5 | Tokenizer coverage completeness | §1.6 class × tokenizer matrix | `THR-M5` | UNKNOWN tokenizer ⇒ UNKNOWN, never PASS |
| M-6 | Bypass rate | §4.2 reasons | `THR-M6` | by reason code |
| M-7 | Unknown-usage / unknown-tokenizer rate | explicit attribution | `THR-M7` | must be explicitly attributed, never dropped |
| M-8 | Routing invariance | §2.5 | `THR-M8` — **must be zero-violation** | any divergence is FAIL |

`M-8` is stated as zero-violation by *kind*: no threshold value may permit a single routing
divergence. This is a semantic constraint, not a tunable.

### 2.3 Semantic gate (blocking)

| ID | Criterion | Method | Threshold slot |
|---|---|---|---|
| S-1 | Instruction preservation | per-case rubric over paired outputs | `THR-S1` |
| S-2 | Constraint and negation preservation | must/must-not/only/never probes | `THR-S2` |
| S-3 | Tool-call integrity | tool name/args/ordering preserved | `THR-S3` |
| S-4 | Structured-output integrity | schema-valid + value-equal | `THR-S4` |
| S-5 | Retrieval/context relevance | relevance judged against original | `THR-S5` |
| S-6 | Adversarial robustness | §3 catalogue | `THR-S6` |
| S-7 | Grounded human/independent assessment | see §2.6 | `THR-S7` |

**S-1 … S-7 cannot be satisfied by M-1 … M-8.** A transformation achieving maximal reduction and
failing S-2 is a **failure**, full stop.

### 2.4 Explicit failure attribution for unknown tokenizer and unknown usage

This is a required gate property, not an error-handling nicety:

- An input whose **tokenizer is unknown** ⇒ M-2 and M-5 resolve `UNKNOWN`; the case is attributed
  `tokenizer_unknown`. It is **not** estimated from a different family, and **not** counted as
  reduced.
- A request whose **provider usage is unknown** ⇒ MB-3 unavailable; any settlement/billing claim is
  `UNKNOWN`, attributed `usage_unknown`.
- The distinction is load-bearing because the R6.1 accounting path already fails exactly here:
  `_sum_actual_tokens` (`completions.py:253–264`) filters `None` components and sums what survives,
  so "unknown" is indistinguishable from "absent" unless every attempt is unknown. R6.6 measurement
  must not repeat that collapse in its own reporting — an unknown tokenizer must never average in
  as a measured reduction (F-2, `r6-independent-review-...:107–120`).

### 2.5 Routing invariance (mandatory)

**Definition.** For every pair, the routing decision sequence for the original input and the
transformed input must be **identical**: same candidate set, same chosen deployment, same attempt
order, same failure classification, same retry count.

**Structural support (VERIFIED (source)).** The lifecycle places classification (`:966`) and
eligibility (`:1166`) **before** the transformation insertion point, and the optimisation step sits
between budget reservation and loop entry (`:1345`). Classification and eligibility therefore
consume the **original** payload — invariance is partly structural rather than merely asserted.

**Why it is still mandatory.** Invariance is *not* guaranteed by placement alone: per-attempt
accounting (`:1601–1608`) clamps `max_tokens` from remaining reservation, and the transformation
can change `estimated_input`, which feeds that clamp. Deterministic routes can therefore drift.

**Observability.** `routing_decisions` is already persisted on the usage event
(`completions.py:645`, `finalize_usage_event`), so invariance is checkable **without logging any
prompt text** — the comparison is over the decision record, not the content.

**Any divergence is a blocking failure**, not a metric to be tolerated. A route-drift caused by
transformation is a *routing* defect and must be attributed as such, never filed as a quality
variance.

### 2.6 Grounded quality assessment

- Human or independently grounded assessment only; no self-assessment by the transforming system.
- Rubrics are **preregistered** with the threshold registry, before seeing outputs.
- Assessors are blind to which member of a pair is transformed, where the pipeline permits.
- Inter-rater agreement is reported; disagreement beyond the registered bound makes the criterion
  `UNKNOWN`, not PASS.
- Where automated judges are used to supplement, they are labelled as supplementary and **never
  substitute** for S-7.

### 2.7 Gate composition

Both gates block. The release position is the **conjunction**: mechanical PASS **and** semantic
PASS **and** routing invariance **and** explicit attribution of every unknown. There is no weighted
score, no "compensating" reduction, and no partial-credit path.

---

## 3. Adversarial test catalogue

A **catalogue only** — no case has been executed. Each entry states intent and required outcome.
Domain owners: Terminal D owns corpus construction (BL-19/BL-24); this document specifies *what*
must be present, not the corpus itself.

### 3.1 Instruction preservation

| ID | Case | Required outcome |
|---|---|---|
| ADV-I1 | Explicit numbered instructions | every instruction still satisfiable from transformed input |
| ADV-I2 | Instruction at the boundary of retained text | no instruction loss at truncation edges |
| ADV-I3 | Instructions split across messages | not reordered or merged in a way that changes scope |
| ADV-I4 | Contradictory instructions | transformation does not resolve the contradiction for the model |

### 3.2 Constraint and negation preservation

| ID | Case | Required outcome |
|---|---|---|
| ADV-C1 | `must not` / `never` / `never, under any circumstances` | polarity preserved byte-for-byte or semantically provably |
| ADV-C2 | Double negation | meaning preserved; no simplification to single negation |
| ADV-C3 | Numeric bounds (`at most`, `≤`, `no more than`) | bound and direction preserved |
| ADV-C4 | Scope quantifiers (`only`, `all`, `except`) | scope preserved |
| ADV-C5 | Negation adjacent to a deleted span | deletion forbidden if it changes polarity |

### 3.3 Tool-call and structured-output integrity

| ID | Case | Required outcome |
|---|---|---|
| ADV-T1 | Tool declarations present (Class-1) | declarations byte-identical or bypass |
| ADV-T2 | Tool-result messages paired to calls | D8 pairing preserved; no orphaned or reordered pairs |
| ADV-T3 | Tool schema with nested objects | schema unchanged |
| ADV-T4 | `response_format` constrained output | schema-valid, value-equal |
| ADV-T5 | Retrieval-stub detection | any `litellm_content_retrieve` stub ⇒ **bypass and alert** (pack `:25–31`) |
| ADV-T6 | Tool-history request | detected and bypassed, never verbatim-forwarded to an unverified deployment (BL-08) |

### 3.4 Retrieval / context relevance

| ID | Case | Required outcome |
|---|---|---|
| ADV-R1 | Redundant repeated context | reduction permitted; relevance retained |
| ADV-R2 | Single crucial sentence in large context | must not be removed |
| ADV-R3 | Near-duplicate but non-identical passages | no incorrect merge |
| ADV-R4 | Non-Latin context (Yoruba/Arabic/CJK/emoji) | **claims excluded** until corpus proven (C2) |
| ADV-R5 | Table/structured context | structure preserved |

### 3.5 Structural and degenerate

| ID | Case | Required outcome |
|---|---|---|
| ADV-S1 | `content: None` | no crash (BL-12/BL-18 null-hardening) |
| ADV-S2 | Empty message array | bypass, no crash |
| ADV-S3 | Whitespace-only content | bypass |
| ADV-S4 | Single-token content | bypass rather than reduction |
| ADV-S5 | Extremely long input (deadline pressure) | transformation yields before deadline; request not failed by our own step |
| ADV-S6 | Unicode/emoji boundaries | no byte-split corruption |

### 3.6 Injection and privileged-role

| ID | Case | Required outcome |
|---|---|---|
| ADV-P1 | Prompt-injection text inside user content | transformation does not *amplify* or *relocate* it into a privileged position |
| ADV-P2 | Content impersonating a tool result | not promoted to tool-result status |
| ADV-P3 | `system`/`developer`-role traffic | byte-identical or gated — role-freeze (BL-09, B5-gated per T11 §18) |
| ADV-P4 | Caller-supplied bypass signal | **rejected unless bypass authority is operator-only** (BL-32, §7.3) |

### 3.7 Catalogue governance

Every case records: ID, intent, input-class, expected outcome, required attribution code, and
owning domain. A case that cannot state its **required attribution on failure** is not admissible —
because an unattributable failure is indistinguishable from a quality regression.

---

## 4. Observability schema proposal

### 4.1 Boundary conditions (binding)

1. **No optimization-record table, writer or builder.** This proposal deliberately introduces
   none. If a dedicated record is ever required, it needs separate authorisation and a
   Track A-coordinated schema change (D14).
2. **Schema `1.1` is a hard gate.** `dataset.py:341–344` rejects any attempt record whose version
   is not exactly `"1.1"`; therefore every field proposed below is a **coordinated change**, not an
   additive one. This proposal does not assume it can be slipped in.
3. **No prompt text, at all.** Raw text, message bodies, and their substrings never enter logs,
   metrics labels, or records. Only counts, lengths, hashes, and enum codes.
4. **Phase-13 keep-out.** Transformation metadata does **not** enter telemetry in R6.1 (BL-31,
   recommended keep-out); this proposal is R6.7-scoped.
5. **Telemetry Option A remains conditional / not-implemented** (BL-16). The live shape is inline,
   synchronous, fail-closed on the accounting row. Any proposal that assumes a new async telemetry
   substrate is out of scope.
6. **Telemetry failure must not affect the request** (BL-17).

### 4.2 Transformation decision telemetry (enum)

One decision code per request, recorded once:

| Code | Meaning |
|---|---|
| `applied` | transformation executed and its output used |
| `applied_partial` | some spans transformed, others protected |
| `bypassed_disabled` | flag off |
| `bypassed_no_eligible` | nothing eligible to transform |
| `bypassed_size` | below/above configured bounds |
| `bypassed_class` | input class excluded (tool-bearing, structured, privileged) |
| `bypassed_declined` | transformation decided no safe reduction |
| `bypassed_explicit` | operator bypass signal (authority per §7.3) |
| `failed_validation` | post-transform validation refused the output |
| `failed_error` | transformation raised |
| `failed_deadline` | insufficient time budget |
| `unknown` | decision could not be determined — **attributed, never defaulted** |

`unknown` exists so that absence of a decision is visible rather than silently reading as
`bypassed_disabled`. This mirrors the F-2 discipline in §2.4.

### 4.3 Bypass and failure reason taxonomy

Two orthogonal axes — **why no transformation** (`DM-*`, decision) and **what went wrong when it
did** (`FM-*`, failure). Conflating them is the common error that makes dashboards unactionable.

| FM code | Condition | Operator meaning |
|---|---|---|
| `FM_TOOL_STRUCTURE` | tool pairing/declaration would change | safety refusal (expected) |
| `FM_STRUCTURED_OUTPUT` | schema would be invalidated | safety refusal (expected) |
| `FM_PRIVILEGED_ROLE` | system/developer role not proven frozen | gate refusal (expected) |
| `FM_VALIDATION_REFUSED` | post-transform validation rejected output | **investigate** |
| `FM_NULL_CONTENT` | null/empty content encountered | **investigate** (BL-12/18) |
| `FM_DEADLINE` | time budget exhausted | capacity signal |
| `FM_INTERNAL_ERROR` | unexpected exception | **page** |
| `FM_TOKENIZER_UNKNOWN` | tokenizer family unknown | coverage gap |
| `FM_USAGE_UNKNOWN` | provider usage unknown | accounting risk |

### 4.4 Metrics — latency, bytes, tokens

- **Latency:** transformation duration as a histogram, separate from provider latency; deadline
  margin reported so overhead is visible *against the budget it consumes*.
- **Bytes:** MB-1 reduction, per input class, with bypassed cases at zero and counted.
- **Tokens:** MB-2 **only with its basis labelled** (`estimator` vs `heuristic` — §7.2). A token
  metric without a basis label is treated as an unreported UNKNOWN.
- **Cardinality discipline:** labels are **enums and input-class tags only** — never request IDs,
  user IDs, message content, or hashes of short content. Metric labels are the easiest route to
  accidental text retention.

### 4.5 Where the data lives (existing surfaces only)

| Data | Proposed carrier | Basis |
|---|---|---|
| decision code | usage-event row (new field ⇒ coordinated schema change) | `finalize_usage_event` |
| failure reason | `state.errors.record(...)` taxonomy (`:1629`) | VERIFIED (source) |
| routing invariance | existing `routing_decisions` tuple (`:645`) | VERIFIED (source) |
| byte/token deltas | counts on the usage row, basis-labelled | `estimated_input_tokens` precedent |
| request tokens/cost | existing `prompt/completion/total_tokens`, `estimated_cost_usd`, `actual_cost_usd` | VERIFIED (source) |

**Dead observability to reuse rather than duplicate:** `cleanup_errors` (`:406`) and `ledger`
(`:403`) are written and never read (BL-05), and stuck reservations are log-lines only. The R6.7
reconciler (U12, per C3) is the natural consumer — reusing them is strictly better than adding a
parallel mechanism.

### 4.6 Privacy

- No prompt text; no content substrings; no reversible encoding of content.
- Lengths and counts are permitted; **hashes of short content are not** (a hash of a 3-word prompt
  is a prompt).
- Redaction uses the existing helper (`redact_secrets`, `:588`) rather than a new mechanism.
- Retention aligns to the existing usage-event retention; this proposal introduces no new store and
  therefore no new retention surface.

---

## 5. Rollout and rollback plan

### 5.1 Gate positions — a naming caution

The programme refers to **G4/G5/G7**. Those identifiers have **zero occurrences in the tree**
(T11 §5 item 17); the repository's existing gates are **A–E**
(`reports/remediation-roadmap-and-gates.md:30–50`). G4/G5/G7 are **programme-level** concepts whose
definitions must be supplied by the mission/campaign. This plan therefore states gate
*requirements* rather than assuming G-names carry repo-level meaning.

**G7 = implementation authorisation and is NOT GRANTED** (`t16:507`; BL-23). Nothing in §5 may be
executed before it.

### 5.2 Feature flag and staging

- **Default off**, globally and per route. Off means *unchanged passthrough*, not "disabled but
  active".
- Per-route enablement — a route is enabled individually, never by class-wide switch.
- Staged order: shadow-measure (no effect) → internal/single route → one bounded cohort → broader.
- Each stage requires the **previous** stage's evidence recorded, not merely elapsed.
- Kill-switch reaches the same code path as the flag: disabling must not require a deploy.

### 5.3 Bypass authority

Undecided (BL-32). Two documented positions:

- **Operator-only, per-route, default-off** (T11 recommendation, `:380`).
- Trusted-service signal (costs provenance machinery, caller-controlled routing-input risk).

**The plan assumes neither.** It records that a caller-supplied bypass signal is a
routing-invariance hazard (§2.5) and that ADV-P4 cannot be closed until §7.3 is decided.

### 5.4 Rollback criteria (pre-registered, no numbers here)

Rollback triggers are registered with the threshold registry (§1.4) and are **owner-assigned
values**. The *kinds* that must exist:

| ID | Trigger kind |
|---|---|
| RB-1 | Routing divergence of any kind (no tolerance) |
| RB-2 | Semantic criterion breach beyond registered bound |
| RB-3 | Attributable failure rate (`FM_VALIDATION_REFUSED`, `FM_INTERNAL_ERROR`) beyond bound |
| RB-4 | Latency overhead beyond bound / deadline margin erosion |
| RB-5 | Accounting anomaly attributable to the transform |
| RB-6 | Bypass rate implying the feature is not actually exercised |
| RB-7 | Any prompt-text retention discovered (immediate, no bound) |

RB-7 and RB-1 are **absolute**: they trigger regardless of threshold values.

Rollback is flag-off (no deploy) → verify passthrough → record incident with attribution. Rollback
must be rehearsed before the first cohort stage; an unexercised rollback is a claim, not a control.

### 5.5 Rollback vs reconciler interaction

R6.7 hosts the reconciler (U12, C3). A rollback that leaves reservations unreconciled is not a
clean rollback; the reconciler must be able to attribute a stuck reservation to the transform
period. This depends on BL-05 (dead `cleanup_errors`/`ledger`) and BL-15 (no terminal marker on
budget reservations) being addressed — **both unresolved**.

---

## 6. Release evidence checklist

Every line is **UNMET** at the time of writing. No line may be marked met by this document, by a
plan, or by the existence of a protocol.

| # | Evidence | Status | Blocked by |
|---|---|---|---|
| 1 | Threshold registry committed, digest recorded pre-measurement | **UNMET** | §1.4, §7.2 |
| 2 | Corpus versioned and digested; case pairing verified | **UNMET** | Terminal D (BL-19/BL-24) |
| 3 | Estimator/tokenizer basis named and signed off | **UNMET** | BL-21, §7.2 |
| 4 | M-1…M-8 recorded with per-class results | **UNMET** | 1–3 |
| 5 | S-1…S-7 recorded with blinded grounded assessment | **UNMET** | 1–3, §2.6 |
| 6 | Routing invariance zero-violation recorded | **UNMET** | run |
| 7 | Unknown-tokenizer / unknown-usage attribution complete | **UNMET** | §2.4 |
| 8 | Observability schema approved as coordinated change | **UNMET** | D14, BL-16, BL-31 |
| 9 | No-prompt-text audit of logs/metrics/records | **UNMET** | §4.6 |
| 10 | Dashboards + alerts defined, with FM→action mapping | **UNMET** | §4.3 |
| 11 | Rollback rehearsed successfully | **UNMET** | §5.4 |
| 12 | Bypass authority decision recorded | **UNMET** | BL-32, §7.3 |
| 13 | Reconciler capable of attributing transform-period reservations | **UNMET** | BL-05, BL-15 |
| 14 | Owner decisions in §7 resolved | **UNMET** | §7 |

---

## 7. Unresolved owner decisions

**Every item is `PENDING` / `NOT APPROVED`. None is selected here; a recommendation is not a
decision** (`t16:511`).

### 7.1 Q5 — the measurement-contract ambiguity (investigated, **not resolved**)

The mission asks this to be investigated and explicitly warns **not** to promote a mission-framed
choice to owner approval. Investigation result:

**(a) The identifier does not resolve in the repository.** No Q-series exists in the tree:

- `r6-t16-...register.md` canonically numbers **23 decisions** as A1–A4, B1–B9, C1–C4, D1–D6 — no Q
  identifiers (`t16 §11:521–543`).
- `r6-architecture-decision-pack.md` uses D-series (D6/D8/D14).
- `r6-t11-...:369–393` labels its owner questions **A1–A4, B1–B5, C1–C3, D1–D3** — again no Q.
- T11 *does* contain a "T11-C Q1…Q5" **sub-investigation** numbering, where **Q5 = "bypass
  authority: operator-only vs trusted-service signal"** (BL-32, `t11:110`). That is **not** a
  measurement contract.

So "Q3 and Q5" as cited in this mission's dependencies are **programme-level decisions taken outside
this repository**. They are recorded here as **external inputs that this terminal cannot read**.
Nothing is inferred about their content.

**(b) The substantive ambiguity is real and locatable.** Whatever Q5's identifier resolves to, the
measurement contract for R6.6 is genuinely underdetermined at four points:

| # | Ambiguity | Candidate readings | Consequence of picking wrongly |
|---|---|---|---|
| MC-1 | **Which estimator defines "token reduction"?** | (i) Tier-1 estimator (unsigned), (ii) `estimate_input_tokens` heuristic, (iii) deployment tokenizer per alias (all UNKNOWN) | MB-2 measures a different quantity than claimed; cross-class comparison invalid |
| MC-2 | **Reduce over what unit?** | (i) canonical serialized bytes, (ii) message content only, (iii) whole request body | MB-1 differs by framing/role overhead; non-comparable across runs |
| MC-3 | **Original-vs-transformed equivalence** | (i) same case pair, (ii) same token budget, (iii) same semantic target | §1.5 pairing changes; a "reduction" may be an apples-to-oranges comparison |
| MC-4 | **Who owns the number?** | (i) Track A estimator sign-off, (ii) Terminal D corpus, (iii) owner | acceptance can be satisfied by an instrument no one approved |

**This document selects none of them.** It records that MC-1…MC-4 must be resolved by owner
decision, and that until then **MB-2 and M-2 resolve `UNKNOWN`** — which is the correct answer, not
a failure of preparation.

**(c) The mission-framed-choice hazard, stated plainly.** There is a natural reading in which the
defaults fall out of convenience: measure with the existing `estimate_input_tokens` helper because
it is already in the code path, serialise the full body because it is what gets sent, and pair
cases by whatever the corpus builder emits. Each is defensible in isolation; **together they
constitute a measurement contract that no owner approved**, adopted, as `t16:511` puts it, by
"absence of objection". That is exactly the promotion this mission forbids. The ambiguity is
therefore **reported, not collapsed** — consistent with the register's own practice of preserving
`C-1`/`C1` and the `C-02` readings side by side rather than choosing for the owner (`t16 §12`).

### 7.2 Remaining decision table

| ID | Decision | Current status | Effect on this programme |
|---|---|---|---|
| **B5** | Settlement contract (must name **both** governors) | `PENDING` | semantic gate's accounting-adjacent criteria have undefined target |
| **B7** | Tier-1 estimator sign-off | `PENDING` (BL-21) | **blocks MB-2 / M-2** |
| **B9** | Release-scope decision | `PENDING` | blocks release checklist completion |
| **D1** | Landing policy for failing tests | `PENDING` | benchmarks cannot be landed as evidence |
| **D3** | U0–U11, `tests/` naming, **U12 in R6.7** | `PENDING` | R6.7 reconciler scope undefined |
| **D6** | LiteLLM retrieval/stub strategy | `PENDING` | ADV-T5 is the guard; strategy itself undecided |
| **D8** | Tool-call/tool-result pairing | `PENDING` | ADV-T2 outcome undefined |
| **D14** | Telemetry schema (coordinated, not additive) | `PENDING` | **blocks §4 entirely** |
| **BL-16** | Telemetry Option A conditional ADR | `PENDING` | observability substrate undefined |
| **BL-31** | Phase-13 keep-out for R6.1 metadata | `PENDING` | schema-1.2 timing |
| **BL-32** | Bypass authority | `PENDING` | ADV-P4 unclosable |
| **C1** | byok/paid + billing-source scope | `PENDING` | MB-3 scope |
| **C2** | Multilingual claim exclusion | `PENDING` | `non-latin` class claims |
| **C3** | Reconciler placement (R6.1 vs R6.7) | `PENDING` | §5.5 |
| **Q3/Q5** | Cited as dependencies; **not found in repo** (§7.1a) | `UNRESOLVED` | external input required |

### 7.3 Decisions that change this document's structure (not just its values)

Called out separately because they are not "fill in a threshold":

- **MC-1…MC-4** (§7.1b) — change *what is measured*, so §1.2, §1.5 and §4.4 change shape.
- **Bypass authority** (§5.3) — changes ADV-P4's expected outcome and the entire bypass taxonomy.
- **D14 / BL-16** (§4.1) — change observability from "coordinated change" to "not in this phase".
- **D3 / U12** — determines whether the reconciler is in R6.7 scope at all.

---

## 8. Paste-ready implementation prompts — HELD

**These are drafted and held. Do not issue until the stated prerequisites are satisfied.**
Issuing one early would be exactly the mission-framed promotion §7.1c forbids.

Each prompt ends with the same prohibition block, omitted below for brevity but binding: no
implementation beyond the stated scope, no provider spend, no migrations, no commits, no staging,
no deployment, and no claim of a passed gate.

### P-1 — Threshold registry (prerequisite: MC-1…MC-4 resolved)

> Create `docs/r6.6-threshold-registry.md` containing slot IDs `THR-M1`…`THR-M8`, `THR-S1`…`THR-S7`,
> `RB-1`…`RB-7`. For each: criterion, measurement basis (MB-1/MB-2/MB-3 or S-method), assigned
> value, assigning authority, date. Record the registry SHA-256. Do not populate any value not
> supplied verbatim by the owner or a recorded decision. Do not run any benchmark.

### P-2 — Corpus and pairing (prerequisite: Terminal D corpus authority, C2)

> Build the versioned corpus per input class in §1.6 of R6-IMPL-PREP-03, with paired original/
> transformed cases sharing a case ID. Record corpus digest. Include the §3 adversarial catalogue
> entries as cases with their required attribution. Do not execute transformations against any
> provider.

### P-3 — Mechanical harness (prerequisite: P-1, P-2, B7 estimator sign-off)

> Implement MB-1 (canonical UTF-8 bytes) and MB-2 (approved estimator) measurement as a read-only
> harness. Emit per-class and per-pair results, with bypassed cases at zero and counted. Resolve
> unknown tokenizer as `UNKNOWN`, never as reduction. No provider calls.

### P-4 — Routing-invariance check (prerequisite: P-1)

> Compare `routing_decisions` sequences across each pair using the existing usage-event field. Report
> any divergence as a blocking failure with the diverging attempt index. Log no prompt text.

### P-5 — Semantic assessment protocol (prerequisite: P-1, §2.6 rubric preregistered)

> Implement blinded pair review tooling and rubric capture. Record inter-rater agreement. Any
> criterion below the registered agreement bound resolves `UNKNOWN`.

### P-6 — Observability implementation (prerequisite: D14 + BL-16 + BL-31 resolved)

> Add the §4.2 decision enum and §4.3 failure taxonomy to the approved telemetry surface as a
> **coordinated schema change**, with the version bump per `dataset.py:341–344`. Do **not** create
> an optimization-record table, writer, or builder. Add no prompt text, no content hashes.

### P-7 — Reconciler attribution (prerequisite: D3/U12, BL-05, BL-15)

> Wire `cleanup_errors` (`:406`) and `ledger` (`:403`) to operator-visible output so stuck
> reservations are attributable to a transform period. Add the budget-reservation terminal marker
> before relying on settled-vs-never-settled distinction.

### P-8 — Rollout flag and rehearsal (prerequisite: G7 granted, P-6)

> Implement default-off, per-route flag reachable without deploy. Rehearse rollback end-to-end in a
> non-production environment and record the rehearsal as evidence. Do not enable in production.

**Prerequisites are gates, not a checklist to work around.** P-1 through P-5 cannot be issued
before MC-1…MC-4; P-6 cannot be issued before D14/BL-16/BL-31; P-8 cannot be issued before G7.

---

## 9. Status of this deliverable

| Requirement | Delivered |
|---|---|
| 1. Benchmark protocol | §1 |
| 2. Mechanical and semantic acceptance matrix | §2 |
| 3. Adversarial test catalogue | §3 |
| 4. Observability schema proposal | §4 |
| 5. Rollout and rollback plan | §5 |
| 6. Release checklist | §6 |
| 7. Unresolved owner decisions | §7 (incl. Q5 investigation §7.1) |
| 8. Paste-ready implementation prompts, held | §8 |

**Restrictions honoured:** no implementation; no tests; no benchmarks; no provider spend; no
migrations; no commits; no staging; no deployment; no production change; **no numeric threshold
invented**; no claim that R6.6 or R6.7 passed; no optimization-record table, writer or builder
introduced or proposed; no mission-framed choice promoted to owner approval.

**This document authorises nothing.** An investigated ambiguity is not a resolved one, a drafted
prompt is not an issued one, and a preregistered slot is not an accepted value.

**SabiRoute decides. LiteLLM executes. Evidence guides the path.**
