# R6.0 — Architecture and Decision Pack

**Status: BLOCKED — DECISIONS REQUIRED**

**Programme:** SabiRoute Build Archive
**Workstream:** R6 — Intelligent Input Optimization
**Role of record:** Terminal A — R6 Architecture Coordinator
**Mode:** Architecture and repository inspection only. **Implementation NOT AUTHORIZED.**
**Verified baseline:** `feat/sabiroute-routing-foundation` @ `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
**Baseline verified on:** 2026-11-03
**Document authority:** design input. This document does not approve itself, does not authorise R6.1, and does not grant G7.

---

## 1. Executive summary

R6 reduces unnecessary input tokens, redundant context and processing overhead without
compromising meaning, security, routing correctness, provider compatibility, tool semantics,
deadlines, accounting or reliability.

The owner has approved the strategic direction: a **hybrid, default-off, input-only**
optimisation pipeline in which SabiRoute owns orchestration, policy, safety, validation,
execution limits, telemetry and accounting, and LiteLLM remains an execution dependency.
That direction is preserved here without change.

This pack consolidates the available evidence and reaches one conclusion that the owner and
T8 must confront before R6.1 begins: **the stock `litellm.compress()` path cannot be adopted
as-is, and the reason is not a missing safety wrapper.** The engine's output contract is
built around a retrieval round-trip SabiRoute does not implement — it replaces message
content with a stub that *instructs the model to call `litellm_content_retrieve`*, and it
returns that tool definition for injection. Removing the tool does not remove the
instruction. This is a correctness defect in the integration, not a hardening gap.

Three decisions are therefore blocked and cannot be resolved by Terminal A:

- **D6** — LiteLLM retrieval/stub strategy.
- **D8** — tool-call and tool-result pairing.
- **D14** — telemetry schema, because `dataset.py:341–344` rejects any attempt record whose
  schema version is not exactly `"1.1"`, so a compression telemetry field is a coordinated
  Track A schema change, not an additive one.

Everything else in the pack is either verified, approved by the owner, or carries a
recommended outcome with a named owner. Nothing has been implemented. No application source,
configuration, dependency file or migration was modified.

---

## 2. R6 mission and scope

### 2.1 Mission

Reduce input-side token consumption and redundant processing while preserving:

meaning · security · routing correctness · provider compatibility · tool semantics ·
deadlines · accounting · reliability.

### 2.2 Locked strategic choices

| Choice | Value | Source |
|---|---|---|
| Engine strategy | Hybrid | Owner (R6-D1) |
| Benchmark corpus | Synthetic | Owner (R6-D2) |
| Optimisation scope | Input only | Owner (R6-D3) |
| Orchestration ownership | SabiRoute | Owner |
| Provider execution | LiteLLM | Owner |
| Initial configuration | Disabled by default | Owner (R6-D4) |
| Failure behaviour | Byte-identical original request | Owner (R6-D5) |
| Admission and quota policy | Preserved unchanged | Owner |
| Original request | Immutable | Owner |

### 2.3 Non-goals for R6

Output-side filtering, streaming-response transformation, semantic caching across tenants,
provider-side prompt caching changes, routing-formula changes, learned compression, and any
change to the deterministic-v1 scoring policy.

---

## 3. Evidence inventory

**Availability statement — read this before relying on any section below.**

| Source | Available to Terminal A? | How it is used here |
|---|---|---|
| Owner R6 decision document | **Yes** — supplied verbatim | §2 locked choices, §14 roadmap |
| Terminal A — LiteLLM discovery and feasibility | **Partially.** The original Terminal A discovery report is *not* in this session's context. A fresh inspection of the installed package was performed instead, and its results are used | §4 verified findings |
| Terminal B — architecture and integration review | **No** | Not used. No claim is made about its contents |
| Terminal C — safety contract and lifecycle analysis | **No** — only the R6-S01…S20 identifiers are known, via the owner document | Invariants referenced by ID only; their full acceptance evidence is **not** reproduced here |
| Terminal D — synthetic benchmark design | **No** | §16 states a plan that must be reconciled with Terminal D's actual design before G4 |
| Terminal E — independent red-team review | **No.** Only the verdict and the finding list quoted in the R6.0 brief | Treated as **second-hand evidence**, attributed as such throughout |

This pack therefore makes no assertion about what Terminals B, C, D or E concluded beyond the
verbatim findings quoted in the brief. Where a finding is confirmed below, it is confirmed by
**fresh inspection of the live tree and the installed package**, not by deferring to a report
this terminal cannot see.

### 3.1 Freshly verified evidence (this session, at `319a711`)

| # | Claim | Evidence |
|---|---|---|
| E1 | Baseline unchanged | `git rev-parse HEAD` → `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`; branch `feat/sabiroute-routing-foundation`; zero tracked modifications; no stash |
| E2 | Installed engine version | `litellm-1.103.0.dist-info`; `tiktoken>=0.8.0` is a hard dependency of litellm |
| E3 | Public API | `litellm/__init__.py:1335` → `from .compression import compress`; `compression/__init__.py` → `__all__ = ["compress"]` |
| E4 | Signature | `compress(messages, model, call_type=CallTypes.completion, compression_trigger=200_000, compression_target=None, embedding_model=None, embedding_model_params=None, compression_cache=None) -> CompressedResult` |
| E5 | Strategies | Exactly two: BM25-only (default) and BM25+embedding blended 0.4/0.6 (`compress.py:440`) |
| E6 | Network call on embedding path | `scoring/embedding_scorer.py:86` → `litellm.embedding(**kwargs)` |
| E7 | BM25 path is local | `scoring/bm25.py` — pure arithmetic over term counts; no I/O |
| E8 | Role preserved | `message_stubbing.py:72` → `{**message, "content": stub_content}` |
| E9 | Message count **not** preserved on Anthropic path | `compress.py:346–351` computes dropped spans; `:487` `continue`s past them |
| E10 | `system` protected, `developer` **not** | `compress.py:240` matches `role == "system"` only |
| E11 | Retrieval tool always injected when content is stubbed | `retrieval_tool.py:5`; stub text at `message_stubbing.py:67–70` instructs the model to call `litellm_content_retrieve` |
| E12 | Full original text returned in `cache` | `compress.py:493–494` — `cache[key] = _content_to_text(msg["content"])` |
| E13 | Default trigger 200,000 tokens; docstring/code mismatch | `compress.py:358`; docstring `:384` says target = `trigger // 2`, code `:403` uses `trigger * 7 // 10` |
| E14 | Token counting is model-keyed | `token_counter(model=...)`; SabiRoute sends `decision.deployment` (`litellm_client.py:82,144`) = public alias, not the provider model in `config/config.yaml` |
| E15 | Routing inputs frozen before the loop | `classification = classify_request(` at `completions.py:966`; retry loop begins `:1345` |
| E16 | Snapshot is per-attempt, inside the loop | built `:1443`, persisted `:1471` |
| E17 | Provider calls | streaming `:1520–1526`, non-streaming `:1539–1545`; `started = time.perf_counter()` at `:1510` |
| E18 | Admission estimate computed once, outside the loop | `estimated_input = estimate_input_tokens(payload.messages)` at `:943`; used `:1088`, `:1606` |
| E19 | 300-second deadline | `api/deadline.py:13` `DEFAULT_REQUEST_DEADLINE_SECONDS = 300.0`; `_deadline_expired` at `:1346`, `:1626` |
| E20 | Schema hard-gate | `dataset.py:341–344` returns `temporal_provenance_unknown_for_schema` when `feature_schema_version != "1.1"` **or** `attempt_schema_version != "1.1"` |
| E21 | BYOK-0 exists | deny-list `completions.py:75`; enforcement `:322` |
| E22 | `payload.model_extra` is read in three places | `:337`, `:902`, `:968` |

### 3.2 Findings from Terminal E, treated as second-hand

Quoted in the R6.0 brief, not independently sourced: retrieval stubs SabiRoute cannot serve;
irreversible multimodal content loss; OpenAI tool-call/result pairing damage; routing-feature
and capability contamination; synchronous compression blocking the event loop; developer
instruction protection gaps; retry transformation consistency; admission/reservation/
settlement boundaries; potential future RTK cross-tenant cache leakage; potential Caveman
semantic erosion; telemetry privacy risks from future wrappers.

**Of these, E6/E10/E11/E12/E19 independently corroborate** the retrieval-stub, developer-role,
multimodal, event-loop and telemetry concerns. The RTK cross-tenant and Caveman semantic
concerns are **hypothetical risks about code that does not yet exist** and cannot be verified
against the tree — they are design obligations, not findings.

---

## 4. Verified findings, assumptions and hypothetical risks

The brief requires this separation explicitly. They are not interchangeable.

### 4.1 Verified (see §3.1)

- No compression, simplification, deduplication or state-cache implementation exists in
  `src/sabiroute/**`. Four placeholder modules remain 0 bytes.
- The routing decision is computed from the original request before any optimisation could
  plausibly run (`completions.py:966`).
- The pre-routing snapshot is built **per attempt inside the retry loop** (`:1443`).
- The admission estimate is computed **once outside the loop** (`:943`).
- Stock `litellm.compress()` emits retrieval instructions SabiRoute cannot serve.
- Stock `litellm.compress()` returns full original message text in `cache`.
- The attempt schema is hard-pinned to `"1.1"` by an integrity gate, not merely by a Literal.

### 4.2 Assumptions (believed, not proven here)

- SabiRoute's provider boundary is OpenAI chat-completions only, so `CallTypes.anthropic_messages`
  is never exercised. *Evidence:* `litellm_client.py:95,157` post to `/v1/chat/completions`.
  **Not proven** for every future client path.
- `compress()` performs no file, network or clock access on the BM25 path. *Evidence:* source
  inspection of `compress.py`, `bm25.py`, `message_stubbing.py`, `content_detection.py`,
  `retrieval_tool.py`. **Not proven** by execution, which is prohibited.
- Provider-reported usage remains available on the success path. *Evidence:* `_actual_tokens`
  handling in `completions.py`. Failure-path usage is already treated as unknown.

### 4.3 Hypothetical risks (no code exists)

- RTK cross-tenant cache leakage — a risk of a design not yet written.
- Caveman semantic erosion — a risk of a design not yet written.
- Wrapper-induced telemetry leakage — a risk of a design not yet written.

These must be designed against, not "fixed".

---

## 5. End-to-end architecture

Logical pipeline. **Stage ordering is a decision (D9), not an assumption.**

```
client request
      │
      ▼
[0] ingress · auth · BYOK-0 (completions.py:322)
      │
      ▼
[1] admission estimate (ORIGINAL)        :943
      │
      ▼
[2] classification (ORIGINAL)            :966
      │
      ▼
[3] policy · capability · health eligibility
      │
      ▼
┌───────────── retry loop begins :1345 ─────────────┐
│  [4] route decision per attempt        :1388      │
│  [5] ORIGINAL feature snapshot         :1443      │
│  [6] provider invocation               :1520/:1539│
│  [7] attempt telemetry                            │
└───────────────────────────────────────────────────┘
      │
      ▼
[8] finish() — budget reconcile · quota settle   :542
```

**Proposed optimisation placement:** a single stage between `[3]` and the loop entry at
`:1345`, producing an immutable `effective_messages` binding. The original `payload.messages`
is never mutated, so stages `[5]` and `[1]` continue to observe the original.

Inside the optimisation stage:

```
original request (immutable)
   │
   ├─▶ eligibility & capability gate ──▶ bypass ──▶ effective = original
   │
   ├─▶ [S1] RTK-style state optimisation      (R6.2)
   ├─▶ [S2] Caveman-style simplification      (R6.3)
   ├─▶ [S3] LiteLLM BM25 context selection    (R6.4)
   │
   ▼
validation & safety gate  ── fail ──▶ effective = original
   │ pass
   ▼
immutable effective request
```

**Ordering is unresolved (D9).** The brief proposes RTK → Caveman → BM25. That order is
plausible — deduplicate before simplifying before selecting — but it is not proven, and two
alternatives are at least as defensible: BM25 → RTK → Caveman (select first, so later stages
process less) and RTK → BM25 → Caveman (simplify only what survives selection). R6.6 must
measure orderings rather than inherit one.

---

## 6. Stage responsibilities and interfaces

Each stage is a pure function over an immutable request representation, returning a result
object and never mutating its input.

| Stage | Input | Output | May fail how | Owner |
|---|---|---|---|---|
| S0 eligibility | request + policy | `eligible` / `bypass(reason)` | fail-closed to bypass | SabiRoute |
| S1 RTK state | eligible request | request + state metadata | bypass, no partial reuse | SabiRoute |
| S2 Caveman | natural-language spans only | request + simplification record | fail-closed to input | SabiRoute |
| S3 BM25 | request | selected request | bypass on unsupported shape | **blocked — D6** |
| S4 validation | candidate request | `accept` / `reject(reason)` | reject → original | SabiRoute |
| S5 telemetry | transformation record | content-free record | drop record, never block request | SabiRoute |

**Invariant across every stage:** a stage returns either a complete, validated candidate or
the original. No stage returns a partially transformed request. No stage receives an
already-transformed request from a previous attempt.

---

## 7. Data lifecycle and immutable request model

### 7.1 Three representations

| Representation | Used by | Mutability |
|---|---|---|
| **Original** (`payload.messages`) | admission `:943`, classification `:966`, feature snapshot `:1443`, routing `:1388` | **immutable** |
| **Effective** (`effective_messages`) | provider invocation `:1520`/`:1539` only | immutable once built |
| **Record** (transformation telemetry) | telemetry only | content-free |

The separation is what makes R6 safe. Routing, snapshots, capability derivation and
accounting all read the original; only the provider call reads the effective request. This
satisfies §4H of the brief — routing and dataset integrity frozen from the original — **by
construction rather than by discipline.**

### 7.2 Prohibited content flows

- `CompressedResult["cache"]` — full original message text (E12). **Must never be logged,
  persisted, serialised, or passed to any telemetry sink.** This is the single most likely
  accidental disclosure path in the design.
- Transformed message bodies — same prohibition.
- Any transformation record containing substrings of prompt content.

---

## 8. Admission, reservation, execution and settlement

| Boundary | Basis | Changes in R6? |
|---|---|---|
| Admission estimate | **Original** — `estimated_input` `:943` | **No** |
| Budget reservation | Original estimate | **No** |
| Retry headroom | `estimated_input` vs `reserved_tokens` `:1606–1608` | **Behavioural side effect — see D10** |
| Provider usage | Provider-reported actual | No |
| Cost | `_actual_cost` from registry prices `:1992` | No |
| Quota settlement | `_sum_actual_tokens` `:603` | No |

**Accounting position (recommended, pending T8):** keep every existing boundary on the
original request. Compression then produces an *under-consumption* relative to reservation,
which is the safe direction — it can never become a quota bypass. Actual billed savings come
only from provider-reported usage; estimated reductions are labelled estimates and never
reported as billed savings.

**Unresolved:** whether the enlarged retry headroom that follows from lower actual usage is
acceptable, or whether retry arithmetic must be pinned to the pre-compression estimate.
See D10.

---

## 9. Retry and fallback semantics

Because the optimisation stage sits **outside** the loop at `:1345`, all attempts observe the
same `effective_messages` object. This satisfies "one validated effective request per logical
request" and "do not transform an already transformed request" **structurally**, not by
convention.

Two consequences must be documented rather than discovered:

1. **Deployment changes across fallback do not change the payload.** If S3 token counting is
   model-keyed (E14), a fallback to a different deployment means the selection was made using
   the *first* attempt's tokenizer. This is acceptable only if the transformation is
   tokenizer-agnostic in effect; it is **not** acceptable to re-run optimisation per attempt.
   See D11.
2. **Alias-keyed counting is approximate.** SabiRoute passes the public alias
   (`sabiroute-openai`) as `model`, which `token_counter` does not recognise, so it falls back
   to a default encoding. Deterministic, but not model-accurate. All engine token figures must
   be labelled estimated.

---

## 10. Deadline and resource isolation

- The 300-second deadline (`api/deadline.py:13`) is **preserved unchanged**.
- `compress()` is **synchronous**. Executing it on the event loop would stall every
  concurrent request. It must run on dedicated bounded capacity.
- **`asyncio.to_thread()` alone does not provide cancellation.** A Python thread cannot be
  forcibly killed; `to_thread` returns control on timeout but leaves the worker running,
  holding its reference to prompt content. The design must therefore bound the *work*, not
  merely the wait: hard input-size caps, a cooperative deadline check inside any SabiRoute-
  written loop, and a process-level isolation boundary if a stage cannot be made cooperatively
  cancellable.
- `_deadline_expired` is checked at `:1346`, immediately after loop entry, so an optimisation
  stage that overruns is caught before any provider call. That is the correct failure point.
- **Attribution defect:** the existing path reports `deadline_exceeded`, which reads as a
  provider failure. R6 needs a distinct `optimization_timeout` category (D13).

---

## 11. Security, privacy and preservation invariants

Inherited from the owner's R6-S01…S20 set. The full acceptance evidence for each lives in
Terminal C's contract, which is **not available to this terminal** (§3). The table below
records only what fresh inspection can say about each.

| ID | Engine satisfies it? | Control required |
|---|---|---|
| S01 default off | n/a — SabiRoute policy | config flag, default false |
| S02 original immutable | n/a | separate `effective_messages` binding |
| S03 system/developer byte-identical | **No** — `developer` unprotected (E10) | SabiRoute pre/post byte-diff |
| S04 roles/count/order | **Only** on `call_type=completion` (E9) | pin call type; assert length/order |
| S05 tool-call pairing | **No** — injects a tool (E11) | **blocked, D8** |
| S06 structured output | **No** — ignores `response_format` | bypass requests carrying it |
| S07 multimodal bypass | **No** — `_content_to_text` discards image blocks | bypass non-text content |
| S08 negation/numbers/paths | **No** — no such protection | corpus evidence only; no machine control |
| S09 BYOK-0 recheck | n/a | re-run deny-list on effective request |
| S10 no external calls | **Only** on BM25 path (E6) | hard-pin `embedding_model=None` |
| S11 no prompt in telemetry | **No** — `cache` holds full text (E12) | structural exclusion |
| S12 fail to original | n/a | adapter try/except |
| S13 off event loop, bounded | n/a — synchronous | dedicated capacity + input caps |
| S14 consumes 300 s | n/a | pass remaining budget |
| S15 one transform per request | n/a | satisfied by placement |
| S16 separate latency | n/a | satisfied by placement (`:1510`) |
| S17 budget semantics | n/a | **D10** |
| S18 distinguishable measurements | n/a | **D14** |
| S19 no output filtering | n/a — input-only engine | satisfied by scope |
| S20 kill switch | n/a | config flag → byte-identical |

**R6-S08 has no machine enforcement available at all.** It can only be demonstrated by an
adversarial corpus. That must be stated in the acceptance record rather than implied.

---

## 12. T8 decision register

Status vocabulary: **APPROVED · CONDITIONAL · OPEN · DEFERRED · REJECTED**.
No decision below is marked APPROVED on Terminal A's authority alone; where the owner has
already approved, that is recorded as the source.

| ID | Decision | Status | Evidence | Options considered | Tradeoffs | Recommendation | Owner | Dependency | Consequence |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Hybrid modular architecture | **APPROVED** (owner R6-D1) | Owner document | monolithic / library-only / hybrid | library-only surrenders policy control | keep hybrid | Owner | — | governs all stages |
| D2 | Input-only scope | **APPROVED** (owner R6-D3) | Owner document | input / output / both | output-side touches streaming | keep input-only | Owner | — | R6-S19 trivially satisfied |
| D3 | Original request immutable | **APPROVED** (owner) | E15, E18, §7 | mutate in place / separate binding | mutation contaminates routing + snapshots | separate `effective_messages` | Owner + T8 | — | enables D12 |
| D4 | RTK cache isolation and invalidation | **OPEN** | no code exists | per-tenant namespace / content-addressed / no cache | content-addressed leaks across tenants; per-tenant costs hit rate | per-tenant namespace + explicit TTL + model/context in key | T8 | D17 | blocks R6.2 |
| D5 | Caveman preservation boundaries | **OPEN** | no code exists | rules-based / model-assisted / none | model-assisted breaks S10 | rules-based, fail-closed, natural-language spans only | T8 | — | blocks R6.3 |
| D6 | LiteLLM retrieval/stub strategy | **BLOCKED** | E11, E12; Terminal E (2nd-hand) | (a) SabiRoute-owned retrieval round-trip (b) stub-free selection (c) reviewed fork/adapter (d) exclude stock stubbing | (a) adds a tool loop, new failure surface; (b) loses recoverability; (c) forks a dependency; (d) forfeits the engine | **(b) or (d) for v1**; (a) is a separate workstream | T8 + Owner | D8 | **blocks R6.4** |
| D7 | Multimodal bypass | **CONDITIONAL** | E7, `_content_to_text` | bypass / preserve blocks / reject | preserving blocks means rewriting the engine | bypass any non-text content | T8 | — | narrows R6.4 scope |
| D8 | Tool-call and tool-result pairing | **BLOCKED** | E9, E11 | strip tools + rewrite stub / bypass tool-bearing requests / implement handler | bypass excludes agentic workloads — the main long-context case | **bypass tool-bearing requests in v1** unless D6(b) is chosen | T8 | D6 | **blocks R6.4** |
| D9 | Stage ordering | **OPEN** | §5 | RTK→Caveman→BM25 / BM25→RTK→Caveman / RTK→BM25→Caveman | each changes what later stages see | measure all three in R6.6 | T8 + Terminal D | — | blocks R6.5 |
| D10 | Placement vs admission/reservation/snapshot | **CONDITIONAL** | E15–E18, E19 | before loop / first-iteration-only | literal "after snapshot" conflicts with "outside loop" | **before `:1345`**, snapshot keeps reading `payload.messages` | T8 | — | see §9, §8 |
| D11 | Deployment/tokenizer compatibility | **OPEN** | E14 | resolve alias→model / accept default encoding / per-deployment re-run | re-running breaks D12 | accept default encoding, label estimates, never re-run | T8 | — | informs D9 |
| D12 | Retry/fallback consistency | **CONDITIONAL** | §9 | transform once / transform per attempt | per-attempt breaks immutability and comparability | **once, by construction** | T8 | D3 | satisfied structurally |
| D13 | Execution capacity and deadline | **CONDITIONAL** | §10 | `to_thread` / bounded pool / process isolation | `to_thread` cannot cancel | bounded pool + input caps + `optimization_timeout` category | T8 | — | R6.1 interface |
| D14 | Telemetry schema and privacy | **BLOCKED** | E20, E12 | reuse 1.1 / bump to 1.2 / separate store | 1.1 gate rejects new fields; 1.2 requires coordinated migration | **separate content-free record, no change to 1.1** | Track A + T8 | D17 | **blocks R6.7** |
| D15 | Benchmark scope and acceptance thresholds | **OPEN** | §16 | B1 only / B1+B2 | B1 alone cannot detect semantic loss | B1 mechanical gates mandatory, B2 advisory until thresholds agreed | Terminal D + T8 | — | blocks R6.6 exit |
| D16 | Default-off rollout | **APPROVED** (owner R6-D4) | Owner document | — | — | keep default off | Owner | — | R6-S01 |
| D17 | Track A ownership and sign-off | **OPEN** | `completions.py`, `gateway.py`, `main.py`, `config/validation.py`, `security/store.py` all Track A | — | R6.4/R6.5 touch `completions.py` | formal sign-off before R6.4 | Track A | — | gates R6.4–R6.7 |

---

## 13. Options and tradeoffs

### 13.1 Engine integration (D6)

| Option | Correctness | Cost | Maintenance | Security | Verdict |
|---|---|---|---|---|---|
| (a) SabiRoute-owned retrieval round-trip | High, but requires implementing `litellm_content_retrieve` and a tool loop | High | High — owns a tool protocol | Medium — new surface | Defer past v1 |
| (b) Stub-free BM25 selection | High — emits no unresolved instruction | Medium — adapter post-processes engine output | Medium | High | **Recommended for v1** |
| (c) Reviewed fork/adapter | High if fork is maintained | High | High — fork divergence on every upgrade | Medium | Not recommended |
| (d) Exclude stock stubbing | High — trivially safe | Low | None | Highest | **Recommended fallback** |

Option (b) requires rewriting the stub to a non-actionable marker and discarding
`result["tools"]`. It is not a wrapper around the defect; it replaces the engine's output
convention with one SabiRoute can honour. It must be validated by R6.6 that the model behaves
acceptably with a non-actionable marker.

**No option is approved merely because it reuses `litellm.compress()`.**

### 13.2 Optimisation stages

RTK and Caveman have **no existing implementation** and no prior work to preserve. They are
greenfield designs in R6.2 and R6.3 respectively. Neither may introduce a dependency that
makes a network call (R6-S10).

---

## 14. Eight-stage roadmap

Preserved exactly from the owner document.

### R6.0 — Architecture and Decision Freeze
Resolve Terminal E's findings · finalise the T8 decision register · approve transformation
invariants · define stage interfaces and ownership · resolve lifecycle placement and
deployment-tokenizer policy.
**Exit:** written architecture approval.

### R6.1 — Optimization Foundation
Immutable original request · canonical request representation · transformation metadata ·
optimisation policy and capability checks · explicit bypass handling.
**Exit:** safe no-op and bypass behaviour proven.

### R6.2 — RTK-Style State Optimization
Canonical cache keys · tenant and policy isolation · deduplication · TTL and invalidation ·
cache correctness tests.
**Exit:** no stale or cross-tenant reuse in tested cases.

### R6.3 — Caveman Simplification
Eligible-content boundaries · conservative simplification rules · protected-content
preservation · fail-closed validation.
**Exit:** all approved invariants pass.

### R6.4 — LiteLLM BM25 Integration
Direct integration, not proxy interception · retrieval/stub safety · supported-format checks ·
dedicated bounded execution · model/tokenizer compatibility.
**Exit:** no unresolved retrieval instructions and no unsupported content damage.

### R6.5 — Pipeline Orchestration
Stage ordering · per-request transformation record · retry and fallback consistency · deadline
integration · validation and bypass orchestration.
**Exit:** one validated effective request per logical request.

### R6.6 — Synthetic Benchmark and Adversarial Validation
Synthetic corpus · mechanical safety tests · individual stage comparisons · pipeline ordering
experiments · performance and reduction measurements.
**Exit:** all mandatory safety gates pass.

### R6.7 — Observability, Rollout and Final Verification
Content-free telemetry · savings versus actual usage reporting · configuration defaults and
limits · disabled-by-default rollout · regression and integration verification.
**Exit:** release evidence and scorecard approval.

---

## 15. Terminal ownership and conflict controls

| Terminal | Mandate | Participates in |
|---|---|---|
| A | Implementation and R6 coordination | R6.0–R6.7 |
| B | Architecture review | R6.0, R6.4, R6.5 |
| C | Security, reliability, lifecycle | R6.0, R6.1, R6.4, R6.7 |
| D | Synthetic benchmark and testing | R6.6 (and R6.2–R6.5 test design) |
| E | Independent red-team | R6.0, R6.5, R6.7 |

**Conflict controls**

1. One terminal owns a file group at a time.
2. Reviewers do not independently modify implementation-owned files.
3. Track A owns `completions.py`, `gateway.py`, `main.py`, `config/validation.py`,
   `security/store.py` and migration files. R6 changes there require Track A sign-off (D17).
4. A red-team finding reopens the owning decision rather than being absorbed as a task.

---

## 16. Synthetic benchmark plan

Separated as required: **B1 mechanical** (machine-checkable, blocking) and **B2 semantic**
(quality, advisory until thresholds are agreed — D15).

### 16.1 B1 — mechanical safety tests (blocking)

| Test | Asserts |
|---|---|
| Identity engine | Zero transformation, zero savings, unchanged outcomes — proves the harness can detect no effect |
| Byte-identity pass-through | Disabled mode produces byte-identical provider payloads |
| Role/count/order | S04 holds on every corpus item |
| System/developer preservation | S03 holds, including `developer` |
| Tool pairing | No tool call is orphaned; no unknown tool is referenced (S05) |
| Structured output | Requests with `response_format` bypass (S06) |
| Multimodal | Non-text content bypasses (S07) |
| No network | Provider-call census is zero for optimisation (S10) |
| No content leakage | Canary secret never appears in any telemetry sink (S11) |
| Fail-to-original | Fault injection returns byte-identical original (S12) |
| Bounded execution | Timeout and overload paths produce `optimization_timeout` (S13, D13) |
| Retry identity | All attempts receive the same effective request (S15) |
| Latency separation | Optimisation time never appears in provider latency (S16) |
| Streaming identity | Response frames are untouched (S19) |

### 16.2 B2 — semantic evaluation (advisory pending thresholds)

Paired comparison: identical corpus item with optimisation off and on. Report task success,
tool-call correctness, provider-reported prompt tokens, byte reduction, optimisation latency,
end-to-end latency, cost per successful task, routing invariance, and preservation failures.

**Routing invariance is a blocking metric even in B2:** any unexplained deployment or
capability difference between paired arms is a defect, not a quality variance.

Sample sizes, minimum detectable effect, primary metric, arm order and evaluation conditions
must be declared before execution. Thresholds may not be set after seeing results.

### 16.3 Corpus requirements

Synthetic, versioned, secret-free. Categories: install/audit logs, build/test output, stack
traces, shell sessions, Docker/infra config, technical prose, source and review, JSON, tool
results, long-context and near-duplicate, and adversarial negation/numerics/paths/identifiers.
Each version carries stable item IDs, category labels, payloads, gold assertions, content
hash, version, provenance statement, redaction scan and expected preservation behaviour.

**This plan must be reconciled with Terminal D's actual design before G4.** Terminal D's
report is not available to this terminal (§3).

---

## 17. Deferred features and explicit non-goals

**Deferred beyond v1:** output-side and streaming-response optimisation; SabiRoute-owned
retrieval round-trip; cross-tenant semantic caching; model-assisted simplification; learned
compression policies; per-deployment tokenizer resolution; optimisation for agentic tool
loops.

**Explicit non-goals:** any change to routing scoring, capability derivation, the
deterministic-v1 formula, provider credentials, endpoint selection, admission policy, quota
policy or the 300-second deadline; any use of SabiChat production conversations without a
separate owner decision and privacy basis; any introduction of Redux Toolkit or a frontend
state library (RTK Query is architectural inspiration only).

---

## 18. Open blockers and approval dependencies

| Blocker | Blocks | Resolvable by Terminal A? |
|---|---|---|
| D6 retrieval/stub strategy | R6.4, R6.5 | No — T8 + Owner |
| D8 tool pairing | R6.4 | No — T8 |
| D14 telemetry schema (1.1 hard gate) | R6.7 | No — Track A + T8 |
| D17 Track A sign-off | R6.4–R6.7 | No — Track A |
| D9 stage ordering | R6.5 | Partially — needs R6.6 measurement |
| D15 acceptance thresholds | R6.6 exit | No — Terminal D + T8 |
| Terminal B/C/D/E reports unavailable | §3 evidence completeness | No — must be supplied |

**G5 (red-team) remains blocked** pending D6 and D8 corrections.
**G7 (implementation authorisation) cannot be requested.**

---

## 19. R6.0 exit checklist

- [ ] Terminal E findings resolved or explicitly classified — **partially: D6 and D8 remain blocked**
- [ ] T8 decision register finalised — **drafted, not accepted**
- [ ] Transformation invariants approved — **proposed in §11**
- [ ] Stage interfaces and ownership defined — **proposed in §6, §15**
- [ ] Lifecycle placement resolved — **recommended in §5, §9; needs T8 confirmation of the snapshot-ordering reading**
- [ ] Deployment-tokenizer policy resolved — **open (D11)**
- [ ] Track A sign-off obtained — **not obtained (D17)**
- [ ] Written architecture approval — **not granted**

---

## 20. Final recommendation

**Do not open R6.1.**

The architecture direction is sound and should be preserved without change. The blocker is
narrow and specific: the stock `litellm.compress()` output contract assumes a retrieval
round-trip SabiRoute does not implement, and no wrapper makes that contract correct. A design
that adopts the engine unchanged will ship a request whose text tells the model to call a tool
that does not exist.

The smallest safe adjustment is to fix the integration, not the architecture: adopt the BM25
selection capability while replacing the stub convention and discarding the injected tool
(D6 option b), or exclude stock stubbing from v1 entirely (D6 option d) and deliver RTK and
Caveman first. Either keeps the hybrid, default-off, input-only architecture intact and keeps
the RTK and Caveman strategic direction fully preserved.

Three decisions must close before this pack can be called approved: **D6, D8 and D14**. None
is Terminal A's to make.

**R6.0 status: BLOCKED — DECISIONS REQUIRED.**

---

### Document control

Created by: Terminal A — R6 Architecture Coordinator
Created on: 2026-11-03
Repository baseline: `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
Files created by this task: `docs/r6-architecture-decision-pack.md` (this file) — **one file, no others**
Files modified: none
Application source, configuration, dependencies, migrations: untouched
Compression executed: no · Benchmarks run: no · Provider calls made: no · Packages installed: no
Commits, pushes, deploys, resets, cleans, stashes, prunes: none
