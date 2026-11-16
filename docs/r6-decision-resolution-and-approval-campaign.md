# R6.0 — Decision Resolution and Approval Campaign

**Status: READY FOR INDEPENDENT REVIEW — NOT READY FOR OWNER APPROVAL**

**Programme:** SabiRoute Build Archive
**Workstream:** R6 — Intelligent Input Optimization
**Role of record:** Terminal A — R6 Architecture Coordinator and Decision Pack Owner
**Mode:** Read-only investigation, decision resolution, documentation and review coordination. **Implementation NOT AUTHORIZED.**
**Verified baseline:** `feat/sabiroute-routing-foundation` @ `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
**Baseline verified on:** 2026-11-03
**Source pack:** `docs/r6-architecture-decision-pack.md` (626 lines; preserved intact, not modified)
**Document authority:** input to independent review (Terminals B/C/D/E), then owner decisions. This document approves nothing, authorises no R6.1 work, and does not grant G7.

**Owner Decision Sheet:** §5. Review assignments: §13. Exit checklist: §16. What is not authorised: §17.

---

## 1. Campaign record

### 1.1 Live repository verification

Verified 2026-11-03, before any investigation:

- Branch: `feat/sabiroute-routing-foundation`
- HEAD: `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` — matches the source pack baseline
- Tracked modifications: none (apart from pre-existing untracked files)
- Stash: empty
- Worktrees: main worktree on-branch; detached/prunable worktrees under `/private/tmp` and sibling docs-publishing worktrees exist — none touched
- Target path `docs/r6-decision-resolution-and-approval-campaign.md`: absent, no conflict
- Prohibited actions: none taken — no reset, clean, stash, rebase, branch switch, deletion, prune, install, execution, benchmark, provider call, commit, push or deploy

### 1.2 Files created or modified

- **Created:** `docs/r6-decision-resolution-and-approval-campaign.md` (this file) — **one file, no others.**
- **Modified:** none.
- Application source, configuration, dependency files and migrations: untouched. No compression executed, no benchmarks run, no provider calls made, no packages installed.

### 1.3 How this document relates to the source pack

The source pack is the existing architecture record. This document does not replace, rewrite, or alter its evidence. It reconciles the terminal evidence (§2), re-verifies load-bearing claims (§3), resolves every open decision D1–D17 to a recommended ruling (§4), states the Owner Decision Sheet (§5), fixes the authoritative lifecycle (§6), rules on D6/D8/D10/D11/D14/D17 (§7–§12), provides copy-ready review prompts (§13), restates the roadmap (§14), the Track A sign-off request (§15), the exit checklist (§16), what is not authorised (§17), and remaining blockers (§18).

Statuses: **APPROVED** (explicitly owner-approved) · **RECOMMENDED** (evidence supports; owner decision pending) · **CONDITIONAL** (accepted once stated conditions hold) · **OPEN** (unresolved) · **BLOCKED** (needs an external decision) · **DEFERRED** (moved to a later phase) · **REJECTED** (explicitly ruled out). No recommendation is marked APPROVED on Terminal A's authority.

---

## 2. Evidence reconciliation — Terminals A through E

### 2.1 Source locator

| Source | Identity in tree | Available? | Baseline/date |
|---|---|---|---|
| Terminal A — LiteLLM discovery | no standalone report file; evidence re-derived by fresh inspection of installed `litellm-1.103.0` + live tree | **Partially** — package facts verified, original report not in context | `319a711`, 2026-11-03 |
| Terminal B — architecture review | no report file found | **No** | — |
| Terminal C — safety contract | only R6-S01…S20 identifiers via the owner document | **No** (IDs only) | — |
| Terminal D — synthetic benchmark design | no report file found; scorecard "Terminal D" mentions concern R3/R4 accounting, not R6 | **No** | — |
| Terminal E — red-team review | verdict + finding list only, second-hand via the R6.0 brief | **No** (second-hand) | — |
| Compression discovery packet | `docs/compression-discovery-packet.md` (untracked) | **Yes** | `b360ffc`, 2026-10-29 |
| Architecture Decision Record | `docs/architecture-decision-record.md` (untracked) | **Yes** | `b360ffc`, F-27 closure 2026-10-31 |
| R6 architecture pack | `docs/r6-architecture-decision-pack.md` (untracked) | **Yes** | `319a711`, 2026-11-03 |
| R6 owner decision document | supplied verbatim inside the source pack | **Yes** (via pack) | — |
| Release scorecard | `reports/my_scorecard.md` | **Yes** — R3/R4 context only | — |

Terminal searches performed: `find` for `*terminal*`, `*red-team*`, `*redteam*`, `*benchmark-design*`, `*safety-contract*`, `*safety_case*` (no hits outside the pack/ADR/scorecard); content `grep` for "Terminal B/C/D/E" across `*.md` (hits only the source pack, the ADR on unrelated F-27/R3 work, and the scorecard on unrelated R3/R4 work). There is no hidden R6 terminal report in the tree.

### 2.2 Evidence reconciliation matrix

| # | Claim | Source class | Status |
|---|---|---|---|
| R1 | No compression/simplification/dedup/state-cache implementation exists in `src/sabiroute/**`; four placeholder modules are 0 bytes | Verified repo fact (discovery packet CD1 + pack claim) | **Verified** |
| R2 | Stock `compress()` output contract: stub text instructs the model to call `litellm_content_retrieve`; tool injected; full originals in `cache` | Verified package fact — `message_stubbing.py:68–71`, `retrieval_tool.py:14`, `compress.py:489–498` (re-verified §3) | **Verified** |
| R3 | Stock `compress()` needs a retrieval round-trip SabiRoute does not implement | Verified repo+package fact — no retrieval handler in tree; proxy posts to `/v1/chat/completions` only (`litellm_client.py:82,144`) | **Verified** |
| R4 | Attempt schema hard-pinned to `"1.1"` by an integrity gate | Verified repo fact — `dataset.py:109`, `:341–343`, `:902`, `:1434–1464` (re-verified §3) | **Verified** |
| R5 | Admission estimate once outside the loop; routing from the original; snapshot per-attempt inside the loop | Verified repo fact — `completions.py:943`, `:966`, `:1388`, `:1443`, `:1471` (re-verified §3) | **Verified** |
| R6 | 300-second absolute deadline at ASGI boundary + per-attempt check | Verified repo fact — `api/deadline.py:13`, `completions.py:1346` (re-verified) | **Verified** |
| R7 | Retry headroom arithmetic couples actual usage to remaining budget | Verified repo fact — `completions.py:1606–1608` (re-verified, ruled in §9) | **Verified** |
| R8 | Public alias is what the engine would receive as `model`; token counting model-keyed | Verified repo fact — `litellm_client.py:82,144`; `config/config.yaml` alias → provider model | **Verified** |
| R9 | BM25-only path is local arithmetic; embedding path makes a network call via `litellm.embedding()` | Verified package fact — `scoring/bm25.py` vs `scoring/embedding_scorer.py:86` | **Verified** |
| R10 | Anthropic tool-exchange spans kept/dropped atomically; OpenAI path has no span protection | Verified package fact — `compress.py:346–351, :487`, `get_protected_indices :225–240` | **Verified** |
| R11 | Terminal E verdict + finding list | Terminal report, **second-hand** via brief | **Partially corroborated** — stub, developer-role, multimodal, event-loop, telemetry concerns corroborated by R2/R9; RTK/Caveman risks are about unwritten code (H1/H2) |
| R12 | Owner strategic direction (hybrid, synthetic corpus, input-only, SabiRoute orchestration, LiteLLM execution, default-off, byte-identical failure, admission/quota preservation, immutable original) | Owner-approved strategic decision | **Approved** — locked |
| R13 | Eight-stage roadmap R6.0–R6.7 with exit criteria | Owner-approved structure | **Approved** — preserved exactly (§14) |
| R14 | Transformation invariants R6-S01…S20 | Proposed (owner IDs; acceptance evidence in unavailable Terminal C contract) | **Proposed** — corroboration in source pack §11; S08 has no machine enforcement (corpus evidence only) |
| R15 | Provider boundary is OpenAI chat-completions only, so the Anthropic path is never exercised | Assumption — `litellm_client.py` posts to `/v1/chat/completions` | **Assumed, not proven** for every future client path |
| R16 | `compress()` performs no file/network/clock access on the BM25 path | Assumption — source inspection only, no execution (prohibited) | **Assumed, not proven** by execution |
| H1 | RTK cross-tenant cache leakage | Hypothetical risk — no code exists | **Design obligation, not a finding** |
| H2 | Caveman semantic erosion | Hypothetical risk — no code exists | **Design obligation, not a finding** |
| H3 | Wrapper-induced telemetry leakage | Hypothetical risk — no code exists | **Design obligation, not a finding** |

### 2.3 Conflicts and corrections

1. **Docstring/code mismatch (corrected):** `compress()` docstring (`:384`) says default target is `trigger // 2`; code (`:403`) uses `trigger * 7 // 10`. The code governs. Any adapter pins to observed behaviour, not the docstring.
2. **"After snapshot" vs "outside loop" (resolved):** source pack D10 already resolves this — optimisation sits **before loop entry (`:1345`)**, snapshot keeps reading `payload.messages`. No contradiction once the binding separation (§6) is stated.
3. **`developer`-role scope (clarified):** `get_protected_indices` protects `role == "system"` only, plus last-user/last-assistant/cache-breakpoint rows. `developer` is **not** protected (pack E10, corroborated). S03 enforcement is SabiRoute-side byte-diff, never engine trust.
4. **Scorecard "Terminal D" mentions are out of scope:** they concern R3/R4 accounting on other candidates, not R6 benchmark design. No R6 Terminal D content is available.
5. **No conflicts found** between the discovery packet (CD1/CD2), the ADR lifecycle, and the source pack placement proposal: all agree the transformation point is greenfield, after final deployment selection, before LiteLLM invocation, modifying no existing logic.

### 2.4 Missing evidence and review assignments

| Gap | Assignment |
|---|---|
| Terminal B report unavailable | §13 prompt B |
| Terminal C contract unavailable (S01…S20 acceptance evidence) | §13 prompt C |
| Terminal D benchmark design unavailable | §13 prompt D |
| Terminal E report second-hand only | §13 prompt E |

---

## 3. Re-verification of load-bearing claims (live tree, 2026-11-03)

### 3.1 D6 — stub instruction lives in message content

`message_stubbing.py:68–71` (installed `litellm-1.103.0`): content is replaced with `"[Compressed: {key} — … Use litellm_content_retrieve tool to get full content.]"`, via `{**message, "content": stub_content}` (`:72`). The tool definition is built separately (`retrieval_tool.py:14`; `_build_retrieval_tools`, `compress.py:498`; returned in `CompressedResult.tools`, `:505–511`). Removing the tool definition does not remove the instruction. The pack's D6 conclusion stands exactly as written.

### 3.2 D8 — no OpenAI-path tool-span protection

`compress.py:346–351` computes `dropped_tool_span_indices`; `:487` skips them — but `tool_exchange_spans` is populated only inside `if _is_anthropic_call_type(call_type_str)`. On the `call_type=completion` path SabiRoute uses, spans are empty: tool-call/result messages are scored as independent units. Pairing damage on the OpenAI path is a property of the engine, not of any wrapper. Bypass is the only v1-safe policy (§8).

### 3.3 D14 — the 1.1 gate is an integrity gate

`dataset.py:109`: `attempt_schema_version: Literal["1.1"] | None`. Consumers enforce: `_temporal_reasons` `:341–343` returns `temporal_provenance_unknown_for_schema` on any non-1.1 version; `:902` gates readiness on `== "1.1"`; `:1434–1464` counts `unsupported_attempt_schema_version` as an integrity issue. Adding optimisation fields to the attempt record without a coordinated migration degrades temporal provenance and readiness across the existing pipeline. The separate content-free record (§11) is a consequence, not a preference.

### 3.4 Lifecycle anchors (all re-verified)

Request-level alias→policy resolution (`_resolve_target`, `:150`, called `:886`) yields the candidate list and routing policy before any accounting. Admission estimate once outside the loop (`:943`, used `:1088`, `:1606`); classification from the original (`:966`); request-level capability/health eligibility via `evaluate_candidates` — standard path `:1166`, Free Pool path `:1035` — before budget reservation (`:1199`); budget reservation of `estimated_input + max_tokens` (`:1199`, held `:1308`); loop entry + deadline check (`:1345–1346`); **per-attempt deployment selection** via `choose_deployment` (`:1388`) inside the loop; snapshot per attempt inside the loop from `payload.messages` (`:1435–1471`); provider invocation as the only future reader of the effective binding (streaming `:1520–1526`, non-streaming `:1539–1545`; `started` at `:1510`); retry headroom coupling (`:1606–1608` — full trace §9); settlement on provider-reported actuals via `_sum_actual_tokens` (`:253`) and `_actual_cost` (`:1992`); BYOK-0 deny-list (`:75`, enforced `:322`); `payload.model_extra` read in three places (`:337`, `:902`, `:968`).

---

## 4. Complete decision register D1–D17

| ID | Decision | Status | Evidence | Alternatives | Tradeoffs | Recommended ruling | Owner | Dependency | Roadmap | Verification | If rejected |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Hybrid modular architecture | **APPROVED** (owner R6-D1) | Owner document | monolithic / library-only / hybrid | library-only surrenders policy control | keep hybrid | Owner | — | all | none (locked) | revisit entire R6 |
| D2 | Input-only scope | **APPROVED** (owner R6-D3) | Owner document | input / output / both | output-side touches streaming | keep input-only | Owner | — | all; S19 trivially satisfied | none (locked) | streaming-response work is out of R6 |
| D3 | Original request immutable | **APPROVED** (owner) | R5, §6 | mutate in place / separate binding | mutation contaminates routing + snapshots | separate `effective_messages` | Owner + T8 | — | enables D12 | R6.1 byte-identity tests | D12 unenforceable |
| D4 | RTK cache isolation and invalidation | **RECOMMENDED** | no code exists (R1) | per-tenant namespace / content-addressed / no cache | content-addressed leaks across tenants; per-tenant costs hit rate | per-tenant namespace + policy/model/context in key + explicit TTL + fail-closed on miss | T8 | D17 | blocks R6.2 | R6.2 exit: no stale or cross-tenant reuse in tested cases | R6.2 cannot open |
| D5 | Caveman preservation boundaries | **RECOMMENDED** | no code exists (R1) | rules-based / model-assisted / none | model-assisted breaks S10 (no provider calls in mechanical pipeline) | deterministic rules-based, natural-language spans only, protected-class bypass, fail-closed | T8 | — | blocks R6.3 | R6.3 exit: all approved invariants pass | R6.3 cannot open |
| D6 | LiteLLM retrieval/stub strategy | **BLOCKED** | R2, R3, R11 | (a) SabiRoute-owned retrieval round-trip (b) stub-free selection (c) reviewed fork/adapter (d) exclude stock stubbing | (a) new tool loop + failure surface; (b) loses recoverability; (c) fork divergence on upgrade; (d) forfeits the engine | **(d) for v1**, (b) only with adapter proof; (a) separate workstream past v1; (c) not recommended | T8 + Owner | D8 | **blocks R6.4 enablement** (construction behind flag permitted, §7.1) | R6.4 exit (disabled boundary) + R6.6 adapter evidence | unresolved stub output reaches a provider |
| D7 | Multimodal policy | **RECOMMENDED** | R9, `_content_to_text` discards image blocks | bypass / preserve blocks / reject | preserving blocks means rewriting the engine | bypass any non-text content; original unchanged | T8 | — | narrows R6.4 | B1 multimodal test | image content silently destroyed |
| D8 | Tool-call and tool-result pairing | **BLOCKED** | R10, R2 | strip tools + rewrite stub / bypass tool-bearing requests / implement handler | bypass excludes agentic workloads — the main long-context case | **bypass tool-bearing requests in v1** unless D6(b) is chosen with pairing proof | T8 | D6 | **blocks R6.4** | B1 tool-pairing test | orphaned calls / unknown tools reach the model |
| D9 | Stage ordering | **OPEN** | no stages exist (R1) | RTK→Caveman→BM25 / BM25→RTK→Caveman / RTK→BM25→Caveman | each changes what later stages see | freeze stable stage interfaces in R6.5 with ordering configurable; measure all three in R6.6; select the order in R6.6 | T8 + Terminal D | — | R6.5 freezes interfaces (ordering stays configurable); R6.6 selects the order | R6.5 interface review; R6.6 ordering experiments | ordering baked in before evidence |
| D10 | Placement vs admission/reservation/snapshot | **RECOMMENDED** (recommendation, not approval) | R5, §6 | O1 natural headroom / O2 pinned estimate / O3 forfeit savings (full analysis §9) | O1 couples optimisation gain to retry behaviour; O3 destroys the feature's value | **single stage before `:1345`**; snapshot keeps reading `payload.messages`; retry eligibility pinned to the original estimate (O2, §9) | T8 | — | R6.1 interface | R6.1 placement tests; B1 retry-identity test | routing/snapshot contamination; retry divergence |
| D11 | Deployment/tokenizer compatibility | **RECOMMENDED** | R8 | model-independent transform / resolve actual tokenizer / accept alias default / per-attempt re-run | re-running breaks D12; alias default is approximate | **accept default encoding, label estimates, never re-run**; compatibility matrix required per stage (CONDITIONAL gate) | T8 | — | informs D9 | R6.4 compat matrix; B2 routing invariance | fallback changes the payload |
| D12 | Retry/fallback consistency | **CONDITIONAL** | §6, R5 | transform once / transform per attempt | per-attempt breaks immutability and comparability | **once, by construction** (placement before `:1345`); effective binding frozen for the logical request | T8 | D3 | satisfied structurally in R6.1 | B1 retry-identity test | attempts diverge |
| D13 | Execution capacity and deadline | **RECOMMENDED** | R6, R9 | `to_thread` / bounded pool / process isolation | `to_thread` cannot cancel; thread holds prompt reference past timeout | bounded pool + input caps + cooperative checks + remaining-budget propagation + distinct `optimization_timeout` category | T8 | — | R6.1 interface | B1 bounded-execution test | event-loop stall; misattributed timeouts |
| D14 | Telemetry schema and privacy | **BLOCKED** | R4, R2 (`cache` holds full text) | add fields to 1.1 / bump to 1.2 / separate store | 1.1 gate rejects new fields; 1.2 needs coordinated migration | **separate content-free record, no change to 1.1** | Track A + T8 | D17 | **blocks R6.7** | schema-conformance + canary tests | provenance degradation; secret leakage |
| D15 | Benchmark scope and acceptance thresholds | **OPEN** | no corpus exists | B1 only / B1+B2 | B1 alone cannot detect semantic loss | B1 mechanical gates mandatory and blocking; B2 advisory until thresholds agreed **before** execution | Terminal D + T8 | — | blocks R6.6 exit | thresholds declared pre-execution | thresholds set after seeing results |
| D16 | Default-off rollout | **APPROVED** (owner R6-D4) | Owner document | — | — | keep default off; kill switch; invalid config fails loudly | Owner | — | S01; R6.7 | R6.1 no-op proof; R6.7 rollout gates | optimisation active without approval |
| D17 | Track A ownership and sign-off | **OPEN** | R5; conflict controls | — | R6.4/R6.5 touch `completions.py` | formal sign-off before R6.4 per §15 request | Track A | — | gates R6.4–R6.7 | signed request | R6 stages touch Track A files without approval |

---

## 5. Owner Decision Sheet

Each item states the decision, the recommendation, and what happens if the owner decides otherwise. No technical re-read required.

1. **D6 — retrieval/stub strategy (blocks R6.4).** Recommended: **(d) exclude stock stubbing from v1**; BM25 stays a strategic capability, pursued only through a separately reviewed stub-free adapter with proof (§7). If the owner instead requires stock stubbing in v1, R6 must add a SabiRoute-owned retrieval round-trip as a separate workstream with its own tool loop, failure surface and security review — R6.4 scope and schedule change accordingly.
2. **D8 — tool-bearing requests in v1 (blocks R6.4).** Recommended: **bypass optimisation for tool-bearing requests and tool-call exchanges** unless D6(b) is chosen with pairing proof (§8). If the owner requires agentic coverage in v1, a pairing-preserving design must be independently validated before R6.4 opens — the current engine cannot supply it.
3. **D14 — telemetry strategy (blocks R6.7).** Recommended: **separate content-free optimisation record; schema 1.1 unchanged** (§11). If the owner prefers a 1.2 migration, Track A must scope and schedule it; R6.7 waits.
4. **D10 — retry headroom ruling (needed for R6.1 interface).** Recommended: **O2 — pin retry-eligibility accumulation to the original estimate basis** (§9.3); settlement stays on actuals. If the owner accepts O1 (natural under-consumption headroom), the acceptance must be recorded explicitly; retry behaviour then differs between optimised and non-optimised traffic by design. Terminal B/C adjudication of the §9.3 arithmetic is required before R6.1 regardless.
5. **D4/D5 — RTK and Caveman boundaries.** Recommended rulings in §4 (per-tenant namespace + TTL; rules-based fail-closed). Owner confirms or amends; either way the rulings gate R6.2/R6.3.
6. **D9 — stage ordering.** Recommended: **R6.5 freezes stable stage interfaces with ordering configurable; R6.6 measures and selects** (§4 D9). If the owner fixes an order now, it is recorded as CONDITIONAL pending R6.6 confirmation.
7. **D11 — tokenizer policy.** Recommended: **accept default encoding, label estimates, never re-run** (§10). If the owner requires model-accurate counting, each stage carries a compatibility matrix or bypass — R6.4 scope grows.
8. **D15 — benchmark thresholds.** B1 gates are mandatory; B2 stays advisory until the owner agrees thresholds **before** execution. No owner action needed now beyond noting that post-hoc thresholds will be rejected.
9. **D17 — Track A path.** The owner notes that R6.4–R6.7 require Track A sign-off (§15). No owner action substitutes for it.

---

## 6. Authoritative request lifecycle

Grounded in live `completions.py` at `319a711`. Step numbers are stable; line anchors are informational. Two levels are distinguished throughout: **request-level** steps run once per logical request; **per-attempt** steps run inside the retry loop.

```
REQUEST LEVEL (once per logical request)
[0] ingress · auth · BYOK-0 deny-list ............ :75, :322
[1] alias → policy resolution ..................... :150 via :886
        _resolve_target maps the public alias to (candidates, policy);
        this is routing configuration, not a deployment choice
[2] admission estimate (ORIGINAL payload.messages)  :943
        estimated_input covers the original input only
[3] classification (ORIGINAL) ..................... :966
[4] request-level eligibility ..................... :1035 (Free Pool) / :1166
        evaluate_candidates: capability + health screen over candidates;
        narrows the eligible set but selects no deployment
[5] budget reservation (original estimate) ........ :1199, held :1308
        reserved_tokens = estimated_input + max_tokens
[6] *** R6 optimisation stage (NEW, R6.1) *** ..... before :1345
        original ─▶ eligibility gate ─▶ S1/S2/S3 ─▶ validation
        pass ─▶ immutable effective_messages; fail ─▶ effective = original

PER ATTEMPT (inside retry loop :1345)
[7] loop entry + deadline check ................... :1345–1346
[8] per-attempt deployment selection .............. :1388
        choose_deployment picks ONE deployment from the eligible set,
        excluding already-attempted ones; NOT a request-level decision
[9] ORIGINAL feature snapshot ..................... :1435–1471
        built from payload.messages (the original), never the effective binding
[10] provider invocation (EFFECTIVE only) ......... :1520–1526 / :1539–1545
        the sole reader of effective_messages; same object every attempt
[11] attempt telemetry (ORIGINAL features + provider actuals)
[12] retry/fallback decision (pinned estimate, O2)  :1606–1608 as amended (§9)

REQUEST LEVEL (finalisation)
[13] finish(): budget reconcile · quota settle .... :542
        settlement on provider-reported actuals (§9)
[14] content-free optimisation telemetry (NEW, R6.7)
```

Authoritative answers: request-level eligibility (`evaluate_candidates`) narrows the candidate set once; **per-attempt selection (`choose_deployment`) picks the deployment each iteration**. Optimisation sits between the two levels — after request-level checks, before loop entry — once per logical request, never per attempt. Routing features and snapshots read the **original**; the provider reads the **effective** request and nothing else. The original governs admission, reservation, classification, snapshot and retry arithmetic. Fallback reuses the same effective request object. Optimisation time is measured separately from provider latency (`started` at `:1510` covers provider execution only). Optimisation overrunning its budget yields `optimization_timeout` and the original request. Optimisation failure yields the byte-identical original request.

---

## 7. D6 decision analysis

Options assessed on correctness, context preservation, effort, maintenance, upgrade risk, provider compatibility, security, failure behaviour, testability and extensibility:

- **(a) SabiRoute-owned retrieval round-trip.** Correct but large: implement `litellm_content_retrieve`, a tool loop, cache lifetime, and a new failure surface. A separate workstream past v1, not a v1 integration choice.
- **(b) Stub-free selection via a reviewed adapter.** Preserves BM25 ranking while replacing the stub convention with a self-contained selection. Not approved by marker-swap: the adapter must prove six conditions — no unresolved retrieval instructions; no unsupported tool definition injected; message structure valid; required context not silently discarded; result usable without a round-trip; failure returns the original. Proof is R6.6 corpus evidence, not argument. Viable only with that proof.
- **(c) Reviewed fork/adapter of the engine.** Fork divergence on every upstream upgrade; maintenance cost permanent. Not recommended.
- **(d) Exclude stock stubbing from v1.** Trivially safe, zero maintenance, highest security. RTK and Caveman deliver v1 value; BM25 remains a strategic capability for a later phase.

**Recommendation: (d) for v1.** (b) may proceed only as a separately reviewed adapter carrying the six proofs. Do not invent a safe adapter without implementation and test evidence — none exists in this tree.

### 7.1 What R6.4 is permitted to do under (d) — no circular dependency

D6-as-(d) blocks R6.4 **enablement**, not R6.4 **construction**. The apparent circle — D6 blocks R6.4, R6.4's exit unblocks D6, R6.6 validates both — is resolved by separating three gates:

1. **R6.4 construction gate (behind flag, never enabled in v1).** R6.4 may build: the direct-integration call path (not proxy interception), the BM25 scoring invocation with `embedding_model=None` hard-pinned (S10), the supported-format checks, the dedicated bounded execution boundary, and the model/tokenizer compatibility checks. All of this is constructed with the stage permanently disabled: the shipped effective request remains byte-identical to the original. This work does not need D6 resolved, because it cannot emit a stub to any provider — it is dead code paths plus their tests.
2. **R6.4 exit gate (disabled boundary proven).** R6.4 exits when B1 proves the disabled boundary: flag-off byte-identity, bypass correctness on every unsupported shape, bounded-execution behaviour, and no unresolved instruction in any emitted payload. The exit criterion "no unresolved retrieval instructions and no unsupported content damage" is satisfied **vacuously but verifiably** — by proof that no stubbed content can leave the stage while disabled. The R6.4 stage therefore completes as infrastructure, not as an enabled capability.
3. **Enablement gate (post-v1, needs D6(b) + R6.6 evidence).** Turning the stage on requires: (i) T8 + Owner resolving D6 to (b) with a named, reviewed adapter; (ii) the adapter's six proofs demonstrated as R6.6 corpus evidence — no unresolved retrieval instructions, no unsupported tool injection, valid message structure, no silent context loss, usability without a round-trip, fail-to-original; (iii) B1 re-run green against the enabled stage. This is a post-v1 decision, recorded as DEFERRED in the register, and it is the only path by which BM25 output ever reaches a provider.

BM25 is therefore **deferred as an enabled capability, not removed as a strategic capability**: the ranking knowledge, integration scaffolding and disabled-boundary proofs land in R6.4; the decision to enable waits on evidence that can only exist after R6.6. No stage is renamed or removed; the roadmap (§14) is unchanged.

---

## 8. D8 tool-safety contract

**Policy:** bypass optimisation for any request where `options.tools` is a non-empty list, `tool_choice` is not `none`/`null`, or any message carries `tool_calls`, `tool_call_id`, or a `tool` role. Eligibility gate S0 evaluates these before any stage runs; evaluation is syntactic and total — ambiguity bypasses.

Pairing invariants (enforced by bypass in v1, by construction in any future handler): no tool call orphaned; no tool result without its call; no unknown tool referenced; message ordering preserved; multi-step exchanges atomic. B1 tool-pairing tests encode each invariant. D6 does not resolve D8: even a stub-free adapter must prove pairing independently.

---

## 9. D10 accounting and retry ruling (RECOMMENDED, not approved)

### 9.1 Traced implementation (live source, `completions.py` at `319a711`)

All symbols below are read from the tree, not inferred:

- **Original estimated input tokens** `E`: `estimated_input = estimate_input_tokens(payload.messages)` at `:943`. Conservative UTF-8 byte upper estimate of the *original* input messages only (implementation: `security/budgets.py:16–40`; text-only, fail-closed). Computed once per logical request; reused at `:1088` (admission), `:1199` (reservation sizing) and `:1606–1608` (retry).
- **Reserved tokens** `R`: `reserved_tokens = estimated_input + max_tokens` at `:1199`, held in the budget ledger at `:1308` (`budget_reserved = True`). Covers one full attempt's worst case: the original input plus the maximum permitted output.
- **Actual provider-reported usage per attempt** `a_i = (prompt_i, completion_i, total_i)`: parsed by `_actual_tokens` (`:239`) from each attempt's provider response body; appended to `actual_usage_parts` on success and, when present, on retryable failure (`:1606–1608` region). Unknown on failure paths → `provider_usage_unknown = True`, which forces retry-loop exit (fail-closed).
- **Cumulative actual usage** `U_k = Σ a_i` over attempts so far: `_sum_actual_tokens` (`:253–266`) sums prompt/completion/total component-wise, ignoring `None` components; total is synthesised as prompt + completion only when both exist.
- **Retry eligibility threshold** (current code): after a retryable failure with known usage, `used = sum(part[2] or 0 for part in actual_usage_parts)` — the sum of **total** tokens across attempts — then `remaining = R - used; if remaining <= E: break` (`:1606–1608`). Note the asymmetry the errata anticipated: the ledger compares cumulative *totals* (input + output) against the *input-only* estimate `E`. This is conservative by construction (output tokens consume headroom too), and it is the existing Track A behaviour — R6 must not alter its shape, only its input.
- **Final settlement amount**: `finish()` reconciles the budget ledger and settles quota from provider-reported actuals: `_sum_actual_tokens` (`:603`) and `_actual_cost` from registry prices (`:1992`). Estimates never settle.

### 9.2 Why optimisation would change retry behaviour without a ruling

Without R6, `a_i.prompt ≈ E` (same content measured twice, once by estimator, once by provider). With input optimisation, the provider sees fewer input tokens, so `a_i.prompt < E` and each attempt consumes less of `R`. The current threshold `R - U_k > E` then stays true for more iterations: identical failure sequences retry further under optimisation than without it. That is a quota-policy side effect of a performance feature, and it differs between optimised and non-optimised traffic by design unless ruled out.

### 9.3 Options

- **O1 — natural headroom.** Accept the coupling. Simple, but optimisation changes retry behaviour: optimised traffic retries more than identical non-optimised traffic. A quota-policy side effect smuggled inside a performance feature.
- **O2 — pinned estimate (RECOMMENDED).** The retry decision uses a pinned ledger that is unaffected by optimisation savings: attempts stop when `R - U_k(pinned) <= E`, where `U_k(pinned)` accumulates per-attempt usage computed against the *original* estimate basis rather than the reduced provider-reported prompt tokens. Concretely, the retry check substitutes the original-estimate input figure for the provider-reported prompt figure when accumulating `used`, so optimisation savings never enlarge the remaining budget. Settlement still uses actuals (`_sum_actual_tokens`, `_actual_cost`) — savings are real and billed; only the *retry-eligibility* accumulation is pinned. Admission (`:943`) and reservation (`:1199`) policy unchanged in all options — optimisation never becomes a quota bypass. Specified as a one-region semantic change at `:1606–1608`, documented in the R6.1 interface, tested by B1 retry-identity. **This arithmetic is a recommendation: the exact substitution must be confirmed by Terminal B/C against the live ledger before R6.1, and any discrepancy they find reopens D10 rather than being absorbed.**
- **O3 — forfeit savings.** Settle at the estimate. Destroys the feature's value; rejected.

### 9.4 Ruling

**O2 (RECOMMENDED, pending owner confirmation — Decision Sheet item 4 — and Terminal B/C adjudication of §9.3).** If the owner accepts O1 instead, the acceptance is recorded explicitly: retry behaviour then differs between optimised and non-optimised traffic by design.

---

## 10. D11 tokenizer and fallback policy

SabiRoute passes the public alias (`sabiroute-openai`) as `model`; the engine's `token_counter` does not recognise it and falls back to a default encoding — deterministic but approximate (R8). Fallback across deployments must not change the payload (D12).

- **A — model-independent transform.** Ideal but unproven per stage; requires evidence, not assertion.
- **B — resolve the actual tokenizer.** Couples R6 to provider internals per deployment; brittle across fallback.
- **C — accept alias default (RECOMMENDED).** All engine token figures labelled estimated; transformation validated to be tokenizer-agnostic in effect; per-stage compatibility matrix or bypass where it cannot be demonstrated.
- **D — per-attempt re-run.** Breaks D12 logical-request consistency. Rejected.

**Ruling: C**, with the compatibility matrix as a CONDITIONAL gate on R6.4.

---

## 11. D14 telemetry proposal

Preserve schema 1.1 unchanged. New content-free optimisation record, separate store, keyed by `logical_request_id` + `attempt_number`, carrying only: stage outcomes and bypass reasons, estimated vs provider-reported token figures, optimisation latency, validation verdicts, config version. Expressly excluded: original prompt content, transformed content, `CompressedResult.cache`, secrets, API keys, retrieval content.

Track A assesses independent integration vs coordinated migration (§15). No dataset schema change, no incompatible attempt record, no Track A approval claimed.

---

## 12. D17 Track A ownership and sign-off

R6 touches Track A-owned files at: `completions.py` (optimisation stage insertion, effective binding, O2 ruling, timeout category), `gateway.py` / `main.py` (pipeline wiring, config flag, pool lifecycle), `config/validation.py` (new flag + limits schema), `security/store.py` (optimisation telemetry store), plus dataset/migration files if D14 ever migrates (it does not in v1). Sign-off request in §15 names each change, its behavioural impact, preserved invariants, test requirements, schema consequences and rollback.

---

## 13. Independent review assignments (copy-ready)

Section references audited against both documents' actual layouts. In the source pack: §11 is the transformation-invariants table (S01…S20), §16 is the benchmark plan (B1/B2/corpus), §6 the stage interfaces, §8 admission/reservation/settlement, §9 retry semantics, §10 deadline isolation, §12 the T8 register, §14 the roadmap. In this document: §4 the D1–D17 register, §5 the Owner Decision Sheet, §6 the lifecycle, §7 the D6 analysis with §7.1 construction/enablement gates, §9 the D10 ruling with §9.1 traced arithmetic, §14 the roadmap, §16 the exit checklist. Each prompt below names the exact sections to read in each document.

### Prompt B — Terminal B architecture review

> You are Terminal B — architecture and integration reviewer for SabiRoute R6.0. Read-only. Read the source pack `docs/r6-architecture-decision-pack.md` (§5 end-to-end architecture, §6 stage interfaces, §8 admission/reservation/settlement, §9 retry semantics, §10 deadline isolation, §12 T8 register — note pack §12 is the register draft, pack §18 the blocker table) and the campaign `docs/r6-decision-resolution-and-approval-campaign.md` (§2 evidence matrix, §4 D1–D17 register, §6 authoritative lifecycle, §7 D6 analysis with §7.1 gates, §9 D10 ruling with §9.1 traced source arithmetic, §14 roadmap). Challenge: overall architecture and stage interfaces; D6 alternatives (a)–(d), the (d)-for-v1 recommendation, and whether the §7.1 construction/enablement separation avoids the D6↔R6.4↔R6.6 circle; D9 — confirm R6.5 can freeze stable stage interfaces while ordering stays configurable for R6.6 measurement; D10 — adjudicate the §9.3 O2 substitution against the live ledger at `completions.py:1606–1608`, `:1199`, `:253–266` (any discrepancy reopens D10, it is not absorbed); D11 alias/approx counting across fallback; retry/fallback consistency; provider compatibility; modularity and LiteLLM upgrade risk. Identify contradictions and propose corrections with file:line evidence. Distinguish verified defects (with file:line) from hypothetical risks and from recommendations (which are not owner approvals — see campaign §4 status vocabulary). Return a report only. Do not modify any file. Do not approve the architecture — that is the owner's decision.

### Prompt C — Terminal C security, safety and reliability review

> You are Terminal C — security, safety and reliability reviewer for SabiRoute R6.0. Read-only. Read the source pack `docs/r6-architecture-decision-pack.md` §11 (the transformation-invariants table S01…S20 — the authoritative invariant material), pack §7.2 (prohibited content flows, especially the `cache` prohibition), §10 (deadline isolation) and the campaign `docs/r6-decision-resolution-and-approval-campaign.md` (§6 lifecycle, §8 D8 tool-safety contract, §9 D10 ruling, §11 D14 telemetry proposal, §15 Track A sign-off surface). Challenge: tenant isolation and cache-leakage paths; prompt retention and the `cache` prohibition; instruction preservation (system/developer — note the `developer` role is unprotected by the engine); tool integrity; multimodal bypass; deadline handling and cancellation semantics; resource exhaustion; accounting and quota bypass; privacy of telemetry; failure behaviour (fail-to-original, `optimization_timeout`). For every finding state whether it is a verified defect (with file:line) or a hypothetical risk in not-yet-written code (RTK/Caveman risks are design obligations, not findings). Distinguish recommendations from owner-approved decisions. Return a report only. Do not modify any file.

### Prompt D — Terminal D benchmark readiness review

> You are Terminal D — synthetic benchmark reviewer for SabiRoute R6.0. Read-only; no execution, no provider calls. Read the source pack `docs/r6-architecture-decision-pack.md` §16 (the benchmark plan: pack §16.1 B1 fourteen-test table, pack §16.2 B2 paired methodology with routing invariance as a blocking metric, pack §16.3 corpus requirements) and the campaign `docs/r6-decision-resolution-and-approval-campaign.md` (§4 D15, §9.3 O2 test hooks, §14 R6.6 exit criteria). Challenge: corpus design and adversarial coverage (negation, numerics, paths, identifiers); B1 mechanical test completeness against the fourteen-test table; B2 paired methodology, routing-invariance blocking metric, sample-size and power declarations; preservation assertions and idempotence; retry-consistency and tool-structure checks; measurement methodology (estimate labelling, latency separation); threshold discipline — thresholds declared before execution, post-hoc thresholds rejected. State what is missing before G4. Distinguish verified gaps from recommendations. Return a report only. Do not modify any file, execute benchmarks, or call providers.

### Prompt E — Terminal E independent red-team review

> You are Terminal E — independent red-team for SabiRoute R6.0. Read-only; no code, benchmarks, provider calls or repository modifications. Read the source pack `docs/r6-architecture-decision-pack.md` (§5 architecture, §7 data lifecycle and prohibited flows, §9 retry semantics, §11 invariants) and the campaign `docs/r6-decision-resolution-and-approval-campaign.md` (§6 lifecycle, §7.1 gates, §8 tool contract, §9 retry ruling) as the adversary's target description. Attempt, at minimum: losing required context; corrupting tool exchanges; bypassing tenant isolation; exposing original prompt content; altering routing features; causing retry divergence; defeating deadline enforcement; misrepresenting savings; serving stale cached context; altering negation or technical meaning. For each scenario give preconditions, attack/failure sequence, impact, detection, mitigation, test, and whether the risk is currently verified or hypothetical. Return a report only. A finding reopens the owning decision — it is not absorbed as a task.

---

## 14. Eight-stage roadmap — preserved exactly

- **R6.0 — Architecture and Decision Freeze.** Resolve red-team findings, finalise the T8 register, approve invariants, define interfaces and ownership, resolve lifecycle placement and deployment-tokenizer policy. Exit: written architecture approval.
- **R6.1 — Optimization Foundation.** Immutable original request, canonical representation, transformation metadata, policy/capability checks, explicit bypass. Exit: safe no-op and bypass behaviour proven.
- **R6.2 — RTK-Style State Optimization.** Canonical cache keys, tenant/policy isolation, dedup, TTL, invalidation, correctness tests. Exit: no stale or cross-tenant reuse in tested cases.
- **R6.3 — Caveman Simplification.** Eligible-content boundaries, conservative rules, protected-content preservation, fail-closed validation. Exit: all approved invariants pass.
- **R6.4 — LiteLLM BM25 Integration.** Direct integration, retrieval/stub safety, supported-format checks, bounded execution, model/tokenizer compatibility. Exit: no unresolved retrieval instructions and no unsupported content damage.
- **R6.5 — Pipeline Orchestration.** Stage ordering, transformation record, retry/fallback consistency, deadline integration, validation and bypass orchestration. Exit: one validated effective request per logical request.
- **R6.6 — Synthetic Benchmark and Adversarial Validation.** Synthetic corpus, mechanical tests, stage comparisons, ordering experiments, performance/reduction measurement. Exit: all mandatory safety gates pass.
- **R6.7 — Observability, Rollout and Final Verification.** Content-free telemetry, savings-vs-actual reporting, config defaults and limits, disabled-by-default rollout, regression/integration verification. Exit: release evidence and scorecard approval.

No stage merged, renamed or removed. G4 (benchmark gate) requires Terminal D reconciliation; G5 (red-team) stays blocked pending D6/D8 corrections; G7 (implementation authorisation) cannot be requested.

---

## 15. Track A sign-off request

Track A is asked to approve the following bounded R6 surface; silence is not approval.

| # | Proposed change | Files | Behavioural impact | Invariants preserved | Tests required | Schema consequence | Rollback |
|---|---|---|---|---|---|---|---|
| T1 | Optimisation stage insertion before loop entry; new immutable `effective_messages` binding; provider calls read it | `api/completions.py` | none when flag off (byte-identical); bypass returns original | original immutable; admission/reservation/routing/snapshot on original; 300 s deadline | R6.1 placement + byte-identity + bypass tests | none | flag off; binding = original |
| T2 | Retry arithmetic pinned to pre-optimisation estimate (O2) | `api/completions.py` `:1606–1608` region | retry decisions ignore optimisation savings; settlement still on actuals | reservation policy unchanged; no quota bypass | B1 retry-identity test | none | revert to natural headroom (explicit owner call) |
| T3 | Distinct `optimization_timeout` failure category | `api/completions.py`, error taxonomy | timeout attribution only; no flow change | deadline preserved; no misattribution to provider | B1 bounded-execution test | none (category string, not schema) | revert category |
| T4 | R6 configuration flag (default off) + limits + kill switch | `config/validation.py`, `gateway.py`, `main.py` | none unless explicitly enabled | default-off (S01); invalid config fails loudly | config validation tests | none | remove flag |
| T5 | Bounded optimisation executor lifecycle | `gateway.py`, `main.py` | capacity isolation; no event-loop execution | S13/S14; DB executor untouched | executor tests | none | disable stage |
| T6 | Content-free optimisation telemetry store | `security/store.py` (+ new record type) | additive only; never blocks requests | prompt content never persisted; 1.1 schema untouched | canary + conformance tests | none to attempt records | drop store |
| T7 | No dataset/migration change in v1 | — | none | schema 1.1 frozen | — | none | n/a |

---

## 16. R6.0 exit checklist

- [ ] Terminal E findings resolved or explicitly classified — partially: D6 and D8 remain blocked
- [ ] T8 decision register finalised — **drafted (§4), not accepted**
- [ ] Transformation invariants approved — proposed (§11 + source pack §11)
- [ ] Stage interfaces and ownership defined — proposed (§6 + source pack §6/§15)
- [ ] Lifecycle placement resolved — recommended (§6, §9); T8 confirmation of the snapshot-ordering reading pending
- [ ] Deployment-tokenizer policy resolved — recommended (D11 → C, §10); T8 confirmation pending
- [ ] Track A sign-off obtained — **not obtained** (§15 pending)
- [ ] Independent review challenged the final design — **not yet performed** (§13 prompts ready)
- [ ] No critical red-team finding unaddressed — pending Terminal E
- [ ] Written architecture approval — **not granted**

---

## 17. What is not authorised

No R6.1 implementation. No RTK, Caveman, BM25, adapter, corpus, benchmark, telemetry-schema, config, dependency, migration or Track A file change. No G7 request. No approval of this or the source pack — the owner approves. No Terminal B/C/D/E report fabricated: gaps are labelled in §2 and assigned in §13. No recommendation marked APPROVED on Terminal A's authority.

---

## 18. Remaining blockers and recommended owner decisions

| Blocker | Blocks | Resolvable by Terminal A? |
|---|---|---|
| D6 retrieval/stub strategy | R6.4 enablement (construction behind flag permitted, §7.1), R6.5 | No — T8 + Owner (recommendation: (d) for v1) |
| D8 tool pairing | R6.4 enablement | No — T8 (recommendation: v1 bypass) |
| D14 telemetry strategy (1.1 hard gate) | R6.7 | No — Track A + T8 (recommendation: separate record) |
| D10 retry-headroom ruling O2 | R6.1 interface | No — T8 + Owner (+ Terminal B/C adjudication of §9.3) |
| D11 tokenizer policy C | R6.4 compat matrix | No — T8 |
| D9 ordering selection | R6.6 (R6.5 freezes interfaces only) | No — T8 + Terminal D (R6.6) |
| D15 B2 thresholds | R6.6 exit | No — Terminal D + T8 + Owner |
| D17 Track A sign-off | R6.4–R6.7 | No — Track A |
| Terminal B/C/D/E reports unavailable | R6.0 approval | No — must be supplied via §13 |

**R6.0 status: READY FOR INDEPENDENT REVIEW — NOT READY FOR OWNER APPROVAL.** G5 remains blocked pending D6/D8 corrections. G7 cannot be requested.

---

### Document control

Created by: Terminal A — R6 Architecture Coordinator
Created on: 2026-11-03
Errata corrected: 2026-11-03 (D6/R6.4 gates §7.1; lifecycle request/per-attempt split §6; D10 traced arithmetic §§9.1–9.4; D9 interface/order split §4/D9/§18; §13 prompt cross-reference audit)
Repository baseline: `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
Files created by this campaign: `docs/r6-decision-resolution-and-approval-campaign.md` (this file) — **one file, no others**
Files modified: this file only (errata corrections); `docs/r6-architecture-decision-pack.md` unchanged
Application source, configuration, dependencies, migrations: untouched
Compression executed: no · Benchmarks run: no · Provider calls made: no · Packages installed: no
Commits, pushes, deploys, resets, cleans, stashes, prunes: none
