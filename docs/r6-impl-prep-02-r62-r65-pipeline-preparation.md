# R6.2–R6.5 — Optimization Pipeline Implementation Preparation

**Prompt:** R6-IMPL-PREP-02 · **Terminal:** Claude Desktop Chat 4
**Date:** 2026-11-05
**Mode:** preparation only. **This document implements nothing, tests nothing, migrates nothing, calls no provider, stages nothing, commits nothing, and deploys nothing. It authorises no phase and grants no gate.** One file was created: this one.
**Baseline:** branch `feat/sabiroute-routing-foundation`, HEAD `319a711`. Branch and HEAD **VERIFIED BY RUNTIME** this session (`git rev-parse`); working tree contains **no tracked modifications** (untracked files only) — **VERIFIED BY RUNTIME** (`git status --porcelain`).

---

## 0. Entry verdict — the stop condition is partially triggered

The prompt's stop clause reads: *"Stop if an unresolved R6.1 contract makes downstream design unsafe."* The honest answer is neither "stop" nor "proceed". It splits:

| Question | Verdict |
|---|---|
| Can the **architecture** of R6.2–R6.5 be specified now? | **Yes.** Composition, ordering, ownership and preservation invariants do not depend on any undecided owner question. They are specified below. |
| Can any R6.2–R6.5 **implementation** land now? | **No.** Every phase changes the bytes sent to the provider, and therefore the token count that is metered. The contract governing "reserved estimate → actual usage" is **not frozen**: B5/B6/B7 are unselected-or-unregistered and F1/F2/F3 are live defects. |
| Is the *accounting interaction* section finalisable? | **No.** §9 states which claims are blocked and on what. It is written as a dependency surface, not a design. |

**The load-bearing reason.** R6.1's contract decides what happens when a provider reports less usage than was reserved. Compression makes that the *normal* case rather than an exception: every compressed request that succeeds settles below its reservation. That path runs through `finish()` (`api/completions.py:542`), which:

- reads `attempted` at `:602` before it is bound at `:1311` → `NameError` swallowed by the broad handler at `:621–:632` → a denial class masked as 503 `quota_unavailable` with the reservation stranded (**INHERITED**, C-01 F1; anchors re-verified in the 2026-11-05 reconciliation T-1/T-3/T-4);
- has no `usage_unknown` parameter, and the quota block recomputes at `:603` (**INHERITED**, C-01 F3).

A feature whose entire value proposition is "settle lower than reserved" cannot be built on a settlement path that mis-settles. **R6.2–R6.5 are gated behind R6.1 closure by construction, not by policy convenience.**

**What this document therefore is:** a dependency-aware implementation plan whose phases are all *entry-gated*, plus the evidence needed to make each phase's eventual authorisation a decision rather than an investigation.

---

## 1. What was verified for R6.4, and what it changes

R6.4 required inspection of the installed SDK rather than assumption. This was done.

| Claim | Evidence | Status |
|---|---|---|
| Installed LiteLLM is **1.103.0**; `pyproject.toml` floor is `litellm[proxy,extra_proxy]>=1.80.0` | `litellm-1.103.0.dist-info/` present; `pyproject.toml:30` | **VERIFIED BY INSPECTION** |
| A compression package exists in the SDK at `litellm/compression/` | `__init__.py`, `compress.py` (19,435 B), `content_detection.py`, `message_stubbing.py`, `retrieval_tool.py`, `scoring/` | **VERIFIED BY INSPECTION** |
| A BM25 scorer exists at `litellm/compression/scoring/bm25.py` (3,687 B) | read in full | **VERIFIED BY INSPECTION** |
| `litellm.compression.__all__ == ["compress"]` | `compression/__init__.py` | **VERIFIED BY INSPECTION** |
| **No** `compression/` or `request_transform/` package exists in `src/sabiroute/` | `src/sabiroute/` holds `api`, `chat`, `config`, `freepool`, `intelligence`, `monitoring`, `providers`, `routing`, `security`, `utils` + `capabilities.py`, `gateway.py`, `main.py`, `migrate.py`, `quotas.py` | **VERIFIED BY INSPECTION** |
| The attempt loop begins at `api/completions.py:1345`; `attempted` is bound at `:1311` | read directly | **VERIFIED BY INSPECTION** |
| No compression test module exists | 56 files under `tests/`, none matching `*compress*` or `*transform*` | **VERIFIED BY INSPECTION** |
| Suite state 4 failed / 664 passed / 9 skipped | C-01 §3 | **INHERITED** — no test executed this session |

### 1.1 Suitability of stock `litellm.compression.compress()` — verdict: **not suitable**

Eight findings, each grounded in the implementation as read. These are the substance of R6.4.

1. **It inverts the architectural boundary.** BM25 select-and-drop is a *decision about what the model is allowed to see*. `CLAUDE.md` §1: **SabiRoute decides. LiteLLM executes.** Adopting the engine's compressor places a decision inside the execution engine and leaves SabiRoute no seam to audit, tune or attribute it.
2. **It injects a retrieval tool.** The return value carries `tools` — a `litellm_content_retrieve` definition — plus a `cache` dict of original content the *caller* must serve (`compress.py:497–511`; `message_stubbing.py:67–70`). CD2 forbids a transform that alters tool authorization, and SabiRoute has no server-side executor for that tool, so every injected tool is a guaranteed dangling call. **This single finding disqualifies the stock function as a drop-in.**
3. **Granularity is whole messages.** `bm25_score_messages` returns one score per message; selection keeps or drops whole messages with a truncation fallback for a single over-budget message. A constraint buried in a low-ranked message is deleted with the rest of it.
4. **The tokenizer is ASCII-only.** `re.findall(r"[a-z0-9_]+", text.lower())` (`bm25.py:14`). Non-Latin content yields no query terms; `bm25.py:52–53` then returns `[0.0] * len(messages)`, every message scores equally and the ranking is arbitrary insertion order. Same defect class T16 C2 already gates release claims on, now established at implementation level.
5. **Its truncation can break tool-call correctness.** `truncate_message` splits on lines, keeps first 70 % and last 30 %, inserts `...[truncated for context window]...` (`message_stubbing.py:97–111`). On a JSON body or tool result this yields syntactically invalid content.
6. **It meters with a different estimator than SabiRoute reserves with.** Counts come from `litellm.token_counter(model=...)` (`compress.py:405`). Two estimators means two "tokens saved" numbers with no defined reconciliation.
7. **No telemetry, deadline or policy contract.** Hard-coded `compression_trigger=200_000` and `target = trigger * 7 // 10`; no request correlation, no participation in the 300-second deadline, no policy enum, no bypass surface beyond protected indices.
8. **Version coupling on a private path.** `litellm.compression.*` is an internal module of a dependency pinned at a minor version. Its stub text is literally model input; a MINOR upgrade can change model behaviour with no diff in SabiRoute.

**What is genuinely reusable — the design, not the code.** `get_protected_indices` (`compress.py:225–243`) encodes a correct, well-argued policy: system messages, the last user message, the last assistant message, and **every message up to and including the last Anthropic `cache_control` breakpoint**. The last is a real insight — rewriting any row inside a cached prefix turns the next request's cache *read* into a cache *write*, making compression actively more expensive. The atomic tool-exchange span concept (`compress.py:164–205`) is the right shape for preserving tool-call pairing. **R6.4 adopts these two policies and reimplements them; it does not import them.**

### 1.2 Vendored scorer vs SDK dependency

| Axis | Vendored (SabiRoute-owned) | SDK dependency |
|---|---|---|
| Boundary (`CLAUDE.md` §1) | Decision stays in SabiRoute | Decision moves into the engine — **violates §1** |
| Tool injection | None emitted | Injects a tool SabiRoute cannot serve |
| Tokenizer | Unicode + identifier-aware, ours to fix | ASCII-only, upstream's to fix |
| Granularity | Message **and** sentence, structure-aware truncation | Message only, line-based truncation |
| Reproducibility | Pinned in-repo; changes only via our diff | Changes on a `>=1.80.0` MINOR bump |
| Maintenance | ~150–250 lines we own, plus IDF math we must test | Zero code, but inherits all eight findings |
| Supply chain | No new dependency | Already a dependency |
| Licence | MIT (LiteLLM `LICENSE` present in dist-info); confirm text before any transcription | MIT |

**Recommendation: vendored.** The deciding axis is the first row, not effort. A compression stage that cannot be audited inside SabiRoute fails CD6's telemetry-correlation requirement before it reaches R6.2–R6.5 at all, and the effort delta is a few hundred lines of textbook arithmetic.

---

## 2. Phase-by-phase architecture

All four phases share one package, one entry point and one pass. The package **does not exist yet**; its name is owner-selected but unregistered (§7, U-1). This document writes `request_transform` because that is the name selected in B1 (supplement §3.2, `EXACT OWNER` transcript line 2716 — **INHERITED**, unregistered). CD3's earlier `compression/` suggestion is superseded by that selection and is not used here.

### 2.0 The ordering invariant that governs everything

> **Routing reads the original request. Compression reads the original request. The provider receives the transformed request.**

- Eligibility, capability filtering, health filtering, alias/policy resolution and **deployment selection** keep consuming the **original** token count. Compression can never change which model is chosen, whether a model fits its context window, or which provider is eligible.
- A request exceeding the selected model's context window **bypasses compression** and fails exactly as it fails today. Making an over-window request fit by dropping content would be compression influencing routing eligibility — out of scope in every phase.
- This resolves a real conflict between source documents: CD2 places the hook *"after final deployment selection, before LiteLLM invocation"*, but deployment selection happens **per attempt inside the loop** (`completions.py:1345`), while R6.5 requires **one transformation pass before provider-attempt retries**. Those cannot both hold at that location; §2.5 gives the resolution.

### 2.1 R6.2 — Within-request deduplication only

**Scope.** R6.2-A only. Cross-request caching (R6.2-B) is **not authorised** and nothing below creates or requires cross-request state.

**Unit of work.** Exact-byte-identical message content where an earlier retained copy precedes the duplicate.

**Algorithm (deterministic, single pass, indices ascending).**

1. Digest each message's *original* content after a documented minimal normalisation (line endings only — no whitespace collapsing, no unicode normalisation; both change bytes the model would otherwise see and belong to R6.3).
2. Walk ascending. For index *i*, if the digest was seen at *j < i*, *j* is retained, *i* is unprotected, and neither participates in a tool_use/tool_result pair, replace *i*'s content with a deterministic reference stub naming *j* and its role.
3. Retain every first occurrence unconditionally, even when it is not itself protected.

**Blocking predicates (any true → bypass that message, record reason).** Protected index; tool-call carrier in either direction; content is a structured list containing any non-text block; content empty or whitespace-only; the digest's first occurrence was itself bypassed; message count below a floor.

**Invariants.** Message order preserved (the stub stays in position; nothing reordered or removed). No state survives the request. Byte-identical pass-through when `off`. Identical input → identical output, asserted by test.

**Open risk, stated plainly.** A reference stub still asks the model to look backwards. It is lossy in the only sense that matters — it changes what the model reads in place. It is included in R6.2-A because the prompt scopes it there, but its quality must be proven by §5 before it is enabled by default, and its default must be `off` at first landing.

### 2.2 R6.3 — Caveman simplification

**Scope.** Natural-language simplification, rule-based only. **No LLM call anywhere in this module** — enforced structurally (§6, X-10).

**First-scope rule set — deliberately near-lossless.** Only two transformations:

- collapse runs of intra-line whitespace to one space, and 3+ newlines to 2;
- delete lines consisting solely of filler from a **closed, versioned, reviewed list** (bare acknowledgements, empty markdown rules).

**Explicitly excluded from first scope:** sentence deletion; synonym substitution; abbreviation; reordering; summarisation; any rewrite of a sentence containing a protected token.

**Content-type bypass (any true → bypass).** Detected code, JSON, YAML, logs, stack traces, diffs, tool results, shell output, or anything failing a prose gate. CD4/CD5 already define this discrimination problem; R6.3 reuses it rather than inventing a second one.

**Preservation oracle — per message, atomic.** Before accepting a simplified message, verify **token-set containment**: every identifier, numeric literal, quoted string, URL, path, negation marker (`not`, `never`, `no`, `except`, `unless`, `must`, `only`) and constraint keyword in the input must be present in the output. On failure, **revert that message to its original** and record `reverted_preservation`. Reversion is per message, never per request, so one bad message cannot disable the stage.

**Bypass conditions, complete.** `off`; protected index; non-prose content type; oracle failure; per-message reduction below a floor (a 2 % saving is not worth a semantic risk); request below trigger; standing deadline pressure.

### 2.3 R6.4 — BM25 select-and-drop, SabiRoute-owned

**Scorer.** Okapi BM25, `k1=1.5`, `b=0.75` — provisional defaults, not policy (U-5).

**Tokenizer (the material improvement over the SDK).** Unicode-aware word extraction (`\w+` over the normalised string, so non-Latin scripts tokenise rather than vanish), plus identifier expansion so `getUserById` and `get_user_by_id` share sub-terms. This closes the SDK's finding 4 and is the precondition for any non-Latin claim.

**Granularity.** Message-level selection (R6.4-A). Where a single message is chosen for reduction and does not fit, truncate **structure-aware**: for JSON and code never cut inside a string, object or line continuation; for prose cut at sentence boundaries with an explicit marker. The line-splitting behaviour of `message_stubbing.py:97–111` is not copied.

**Select-and-drop semantics (SabiRoute's, not the SDK's).** No retrieval tool. No stub promising recovery. A dropped message becomes a short deterministic marker naming its index, role and line count — a truthful statement that content was elided, not a promise the model can retrieve it. Where truthfulness and recoverability conflict, the marker is truthful.

**Budget.** Target expressed as a fraction of the selected model's context window, converted with **SabiRoute's** estimator, then reconciled against the already-computed reservation — the reconciliation rule is blocked (§9). Scoring runs on text **after** R6.2 and R6.3, because the budget must be spent on bytes actually sent.

### 2.4 Phase independence

R6.2, R6.3 and R6.4 are mutually independent: any one can be enabled with the others `off`, each with its own kill switch. Only their *composition* is order-sensitive, which is R6.5's subject.

### 2.5 R6.5 — Pipeline orchestration

**Order: dedup → simplify → BM25 select-and-drop.** Cheapest and most deterministic first; each stage reduces input to the next; the budget-driven stage runs last because it must reason about final token counts. Reversing any adjacent pair changes the outcome, so the order is part of the contract.

**Hook — one site, before the attempt loop.** The transform runs **once**, after budget reservation completes (`:1308–:1309`) and **before** the attempt loop begins (`:1345`), producing an immutable transformed request object that **every** attempt consumes unchanged. This satisfies three constraints at once: B7's prohibition on per-attempt re-derivation (**INHERITED**, unregistered); R6.5's one-pass rule; and §2.0's requirement that routing never sees a transformed request.

**Provenance.** Each request carries a transform record: original byte digest, per-stage status (`changed` / `unchanged` / `bypassed` / `reverted` / `error`) with reason, stages applied in order, original and transformed token estimates, stage durations. **No prompt content retained** (CD6).

**Error isolation.** Any exception, timeout or invalid result discards the partial transform and proceeds with the original request. No partial application: either the whole chain succeeds or the request is byte-identical to what arrived. A transform failure never fails a request.

**Deadline.** The transform has its own bounded slice inside the 300-second deadline. Exceeding it aborts to pass-through; it never consumes retry budget and never shortens an attempt's provider timeout.

**Telemetry.** Stage records join the existing request/decision/attempt correlation. Estimated savings and provider-reported usage stay **distinct fields** — collapsing them is the F2 failure mode in a new place.

**Rollback.** Config `off` (default) is byte-identical pass-through, proven by a test comparing serialised bytes. A runtime kill switch follows the `free_chat_requested` precedent — re-checked before each attempt, never cancelling an in-flight one.

**Priority composition.** If two stages disagree about a message, the **more conservative outcome wins**: keep, or revert. No stage may override another's preservation decision.

---

## 3. Dependency graph

```
                    ┌─────────────────────────────┐
                    │ R6.1 settlement contract    │  NOT FROZEN
                    │ B5 · B6 · B7 · F1 · F2 · F3 │  0 approved
                    └──────────────┬──────────────┘
                                   │ blocks all implementation
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  ┌───────────┐             ┌───────────┐              ┌───────────┐
  │  R6.2     │             │  R6.3     │              │  R6.4     │
  │  dedup    │             │ simplify  │              │  BM25     │
  └─────┬─────┘             └─────┬─────┘              └─────┬─────┘
        └───────────┬─────────────┴──────────────┬───────────┘
                    ▼                            ▼
        ┌───────────────────────┐    ┌──────────────────────────┐
        │ shared primitives     │    │ token estimator          │
        │ preserve · policy ·   │    │ (reservation basis)      │
        │ engine · telemetry    │    └──────────────────────────┘
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │  R6.5 orchestration   │  depends on all three + R6.1
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │ single call site      │  api/completions.py — Track A owned
        └───────────────────────┘
```

**External dependencies, each a hard gate.** `request_transform` package exists and is named (U-1, B1 registration); `tests/` lies inside the authorised write boundary (D3/G7); Track A has agreed the one call-site change (CD3 conflict control); the estimator question is answered (U-2).

---

## 4. File and test ownership matrix

Legend: **NEW** = does not exist; **TA** = Track A / Terminal A owned, **not touched by R6.2–R6.5**; **TB** = Track B, created by this programme.

| Path | State | Owner | Phase | Notes |
|---|---|---|---|---|
| `src/sabiroute/request_transform/__init__.py` | NEW | TB | R6.5 | Public surface: `transform()`, record type, policy enum |
| `…/request_transform/policy.py` | NEW | TB | R6.5 | Mode enum + validation; default `off` |
| `…/request_transform/engine.py` | NEW | TB | R6.5 | Ordered stage registry, single-pass driver |
| `…/request_transform/preserve.py` | NEW | TB | shared | Protected indices, preservation oracle, content detection |
| `…/request_transform/dedup.py` | NEW | TB | R6.2 | Within-request exact-duplicate collapse |
| `…/request_transform/simplify.py` | NEW | TB | R6.3 | Rule-based prose simplification |
| `…/request_transform/bm25.py` | NEW | TB | R6.4 | Vendored scorer — **verified non-existent today; created here, never imported from `litellm`** |
| `…/request_transform/telemetry.py` | NEW | TB | R6.5 | Content-free run records |
| `src/sabiroute/api/completions.py` | exists | **TA** | R6.5 | Exactly one insertion, pre-loop between `:1309` and `:1345`; **Terminal A performs it** |
| `src/sabiroute/config/validation.py` | exists | **TA** | R6.5 | Config schema addition; **Terminal A performs it** |
| `src/sabiroute/security/store.py` | exists | **TA** | — | Not touched. Ledger/telemetry overlap requires Track A agreement |
| `src/sabiroute/quotas.py`, `capabilities.py` | exist | TA | — | Estimator basis to be read, not modified |
| `tests/test_r6_transform_dedup.py` | NEW | TB | R6.2 | Needs D3 |
| `tests/test_r6_transform_simplify.py` | NEW | TB | R6.3 | Needs D3 |
| `tests/test_r6_transform_bm25.py` | NEW | TB | R6.4 | Needs D3 |
| `tests/test_r6_transform_pipeline.py` | NEW | TB | R6.5 | Ordering, pass-through, error isolation |
| `tests/test_r6_transform_preservation.py` | NEW | TB | shared | The §5 catalogue |
| `tests/test_r6_settlement_integrity.py` | exists | **TA** | — | **Not touched.** Currently the only 4 failures in the repo |

**Ownership conflict, stated rather than assumed.** CD3 records `completions.py`, `main.py`, `gateway.py`, `security/store.py` and `config/validation.py` as Terminal A-owned. The architecture above is deliberately shaped so R6.2–R6.5 own **no shared file** and require exactly **one** insertion in one Terminal-A file. If Track A declines that insertion point, every phase is blocked — there is no viable alternative seam in-tree (CD2).

---

## 5. Semantic preservation test catalogue

Preservation is the acceptance criterion; savings are not. The oracle is token-set containment plus structural assertion — never a similarity score.

| # | Case | Input shape | Required outcome |
|---|---|---|---|
| P-01 | System/developer instruction survives | system + user msg | System message byte-identical under every mode |
| P-02 | Negation preserved | "do **not** call the tool unless…" | Marker set intact, or message reverted |
| P-03 | Constraint preserved | "max 3 retries, only for 5xx" | Number and qualifier both present |
| P-04 | Identifier preserved | `get_user_by_id`, `SABIROUTE_TEST_PG_URL` | Every identifier present, exact case |
| P-05 | Numeric threshold preserved | `>= 0.85`, `timeout=300` | Exact literal present |
| P-06 | Code block untouched | fenced block | Byte-identical; R6.3 bypasses |
| P-07 | JSON body untouched | JSON content | Byte-identical; truncation never cuts inside structure |
| P-08 | Tool-call pairing intact | assistant `tool_use` + user `tool_result` | Both retained or both dropped; never orphaned |
| P-09 | Message order preserved | 12-message transcript | Relative order identical after transform |
| P-10 | Exact duplicate collapses | same 40-line log twice | Second becomes a marker naming the first; first byte-identical |
| P-11 | Near-duplicate **not** collapsed | differs by one character | Both retained |
| P-12 | Protected indices never transformed | system, last user, last assistant | Byte-identical; each stage records `bypassed:protected` |
| P-13 | Cache prefix integrity | Anthropic `cache_control` breakpoint | Every message up to the last breakpoint byte-identical |
| P-14 | Non-Latin text scored honestly | Arabic / Hausa / Yoruba prose | Non-zero scores; if tokenisation cannot support it, **bypass with reason**, never silent arbitrary drop |
| P-15 | Structured content list | text + image + tool blocks | No non-text block ever rewritten or dropped |
| P-16 | Empty / whitespace-only content | `""`, `"   \n"` | Pass-through, no crash, no marker |
| P-17 | Streaming path equivalence | `stream=true` | Same transformed object used; no per-chunk transformation |
| P-18 | Unicode normalisation stability | NFC/NFD pairs | No normalisation applied; bytes preserved |
| P-19 | Determinism | same input twice, separate processes | Identical output bytes |
| P-20 | Prompt-injection shape | message instructing "ignore prior instructions" | Treated as data; never promoted, never dropped for containing it |

Cross-cutting: `off` mode is byte-identical for all 20 cases; every bypass produces a recorded reason (no silent no-ops).

---

## 6. Performance and failure-mode test plan

**Performance — measured, not assumed.**

| # | Measurement | Method | Acceptance shape |
|---|---|---|---|
| F-01 | Per-stage latency p50/p95 | corpus at 1 k / 10 k / 100 k tokens | Pre-registered cap per stage; breach fails the phase, not a warning |
| F-02 | Total pipeline p95 | same corpus | Fits inside its deadline slice with margin |
| F-03 | Token-estimate error | estimator vs provider-reported usage | Error band stated, not hidden; feeds §9 |
| F-04 | Pathological input | 1 MB single line, 10 000-message transcript, deeply nested JSON | Bounded memory and time; bypass on breach |
| F-05 | Memory ceiling | peak RSS during transform | Ceiling asserted in test |
| F-06 | Savings honesty | estimated vs actual per run | Reported separately; never summed into one number |

**Failure modes — each must degrade to pass-through.**

| # | Injected fault | Required behaviour |
|---|---|---|
| X-01 | Exception in any stage | Original used; `error` recorded; request succeeds |
| X-02 | Stage exceeds slice | Abort to pass-through; no partial application |
| X-03 | Invalid config value | Startup validation rejects; never half-configured at runtime |
| X-04 | Preservation oracle raises | Message reverted, stage continues |
| X-05 | Provider error after transform | Retry uses the **same** transformed object (B7); never re-derives |
| X-06 | Provider timeout after transform | Deadline arithmetic unchanged by transform duration |
| X-07 | Client cancellation mid-transform | Cancellation honoured; no reservation side effect introduced |
| X-08 | Kill switch mid-request | Re-checked per attempt; no in-flight cancellation |
| X-09 | Unknown model for estimator | Bypass with reason; never guess a token count |
| X-10 | **No network** | Test asserts the module opens no socket and imports no provider client |
| X-11 | Concurrency | Concurrent requests share no state; no cross-request leakage (R6.2-B boundary) |
| X-12 | Ledger integrity | Transform adds no reservation, release or settlement side effect |

---

## 7. Unresolved decisions and entry/exit gates

### 7.1 Decisions this plan needs, and does not take

| ID | Question | Blocks | Owner |
|---|---|---|---|
| **U-1** | Package name — `request_transform` (B1-selected, unregistered) vs CD3's `compression/` | Every file in §4 | Owner + T16 register update |
| **U-2** | Which estimator is authoritative for "tokens saved", and how is it reconciled with the reservation estimate? | R6.4 budget, §9 entirely | Owner / R6.1 |
| **U-3** | Truthfulness-only elision marker, or is recoverability (retrieval tool) required? | R6.4 semantics | Owner |
| **U-4** | Message granularity only, or sentence-level select-and-drop? | R6.4 scope | Owner |
| **U-5** | `k1`/`b`, trigger and target defaults — policy values or tunables? | R6.4 | Owner |
| **U-6** | Non-Latin support: implement in tokenizer now, or bypass-with-reason until the Terminal D corpus exists? | R6.4, C2 | Owner + Terminal D |
| **U-7** | Does R6.2-A's reference stub meet the "preserve semantic boundaries" bar at all, or must dedup wait for a lossless framing? | R6.2 default-on | Owner |
| **U-8** | Who owns the new telemetry fields — Track B alone, or a coordinated `store.py` change? | R6.5 | Track A |

### 7.2 Entry gates (all currently **NOT SATISFIED**)

| Gate | State | Evidence |
|---|---|---|
| R6.1 settlement contract frozen | **NO** — 0 of 23 approved | T16 master index, all `OUTSTANDING` |
| B5 (settlement basis) | **UNSELECTED** | not among the selected set |
| B7 (no per-attempt re-derivation) | **UNSELECTED** | idem |
| F1/F2/F3 repaired | **NO** — 4 failing tests | `tests/test_r6_settlement_integrity.py` |
| D1 / D2 / D3 | **UNSELECTED** — and D3 governs whether `tests/` is writable at all | T16 D1–D3 |
| G7 | **NOT GRANTED**, not requested — a review report cannot request it | T13 §19 |
| Track A engagement | **NOT OBTAINED** | packets drafted, none issued |
| Package name registered (U-1) | **NO** | supplement O-5 |

### 7.3 Exit criteria per phase

| Phase | Exits when |
|---|---|
| R6.2 | 20/20 preservation cases pass with `off`-equivalence; dedup never orphans a tool pair; stub semantics accepted under U-7 |
| R6.3 | Zero oracle revertions on the approved corpus; no LLM import reachable; prose gate has a measured false-positive rate |
| R6.4 | Non-Latin behaviour decided and tested (U-6); scoring reproducible across processes; truncation never yields invalid structure; no retrieval tool emitted |
| R6.5 | Byte-identical `off` proven; every X-case degrades to pass-through; one transformed object across all attempts; no ledger side effect |

---

## 8. Proposed implementation prompts

Each prompt is narrow, names its forbidden actions, and presumes §7.2 gates are satisfied. **None is issued by this document.**

**P-R6.2 — dedup.** Implement `request_transform/dedup.py` and `preserve.py` against §2.1. No cross-request state, no config default change, no call-site edit. Deliver: module, the P-10/P-11/P-12/P-13 cases, and every bypass reason with counts. Do not touch `api/`, `config/`, or any existing test.

**P-R6.3 — simplify.** Implement `request_transform/simplify.py` with the closed two-rule first scope and the containment oracle. Bypass on every non-prose content type. Prove by test that no provider client is importable from the module. Deliver the revert-rate measurement on the CD5 corpus; a rate above the pre-registered threshold fails the phase.

**P-R6.4 — BM25.** Implement `request_transform/bm25.py` from the Okapi formula with the Unicode identifier-aware tokenizer, structure-aware truncation and truthful elision markers. **Do not import `litellm.compression`.** Deliver P-14 and P-07 plus cross-process determinism. Confirm LiteLLM's `LICENSE` text before transcribing any structure from it.

**P-R6.5 — orchestration.** Implement `engine.py`, `policy.py`, `telemetry.py` and request the single Track A insertion between `completions.py:1309` and `:1345`. Deliver `off`-byte-identity, all X-cases, and a demonstration that every attempt in a multi-attempt run consumed the identical transformed object.

---

## 9. Accounting interaction (blocked — stated as a dependency surface)

Listed separately because it cannot be finalised. What is *known*:

- Every phase reduces prompt tokens on the wire, so settled usage will routinely fall below the reservation.
- B6 (monotone-shrink, owner-selected, **unregistered**) is the mechanism that handles a downward settlement — the phases depend on it and it is not yet canonically recorded.
- B7 (no per-attempt re-derivation, **unselected**) is what makes the one-pass rule mandatory rather than stylistic.
- F1's masked `NameError` and F3's unhonourable `usage_unknown` mean an unknown-usage compressed request cannot settle correctly today.

What is *not* known, and must not be guessed: whether savings are credited, retained as headroom, or re-baselined; how estimated and provider-reported savings are reconciled; and whether a compression-induced settlement change needs its own ledger field. **No R6.2–R6.5 implementation may define these by accident.** They are decided in R6.1, and this plan consumes them.

---

## 10. Status

```
BASELINE:  feat/sabiroute-routing-foundation @ 319a711, no tracked modifications
READ:      litellm 1.103.0 compression/ (compress, bm25, message_stubbing, __init__),
           compression-discovery-packet CD1–CD6, completions.py attempt-loop region,
           src/sabiroute layout, tests/ inventory (56 files), pyproject.toml
METHOD:    direct file read; git state verified by shell; NO test executed
EDITS:     1 file created (this one). 0 modified, 0 staged, 0 committed.
PROVEN:    stock litellm compress() is unsuitable, with eight grounded findings;
           no compression/request_transform package exists in SabiRoute;
           the attempt loop starts at :1345, so CD2's hook conflicts with B7's one-pass rule;
           the resolution is a pre-loop transform that routing never reads.
GATED:     B5, B6, B7, D1, D2, D3, G7, Track A, U-1 — none satisfiable here.
NEXT:      U-1 package-name registration, then U-2 estimator basis, then P-R6.2.
```
