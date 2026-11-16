# R6 T9 — Capability Recovery and Architecture Preservation Review

**Status: INVESTIGATION COMPLETE — DECISION SUPPORT ONLY. NO IMPLEMENTATION AUTHORIZED.**

**Programme:** SabiRoute Build Archive
**Workstream:** R6 — Intelligent Input Optimization
**Role of record:** Terminal E — Independent red-team, final-challenge adjudication, acting as T9 investigator
**Mode:** Read-only investigation and decision support. **Implementation NOT AUTHORIZED. No approval granted.**
**Verified baseline:** `feat/sabiroute-routing-foundation` @ `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`
**Baseline verified on:** 2026-11-03 (before investigation and after; §2)
**Source documents (read in full, preserved intact, not modified):**
- `docs/r6-architecture-decision-pack.md` (R6.0 pack)
- `docs/r6-decision-resolution-and-approval-campaign.md` (resolution campaign)
- Installed `litellm-1.103.0` package (read-only inspection)
- Live tree `src/`, `config/`, `tests/` (static inspection only)

**Files created by this task:** `docs/r6-t9-capability-recovery-review.md` (this file) — **one file, no others.**
**Files modified:** none. Application source, configuration, dependencies, migrations, datasets: untouched.
No compression executed. No benchmarks run. No provider calls made. No packages installed.
No commits, pushes, deploys, resets, cleans, stashes, or branch changes.

---

## 1. Executive Summary

**Central question:** *What is the maximum useful optimization capability SabiRoute can safely retain or recover, and exactly what engineering evidence is required to achieve it?*

**Answer in brief.** More capability is recoverable than the current BLOCKED posture suggests — but none of it is recoverable by relaxing guards. Every recovery path found in this investigation works by *narrowing* the mechanism (select-and-drop instead of select-and-stub; first-turn-only text instead of all-tool-traffic; capped structural estimates instead of silent under-reservation; shadow-mode forecasting instead of live re-tuning), never by widening trust. The architectural invariants (§4) survive intact under every Group A and Group B proposal; each proposal that required violating one was rejected (§18).

**Headline findings by workstream:**

- **T9-A (D6, BM25): RECOVERABLE.** A retrieval-free BM25 path is technically feasible in installed `litellm-1.103.0` — not via stock `compress()` (whose stub/cache/tool stages are inseparable from its output contract), but via the standalone `bm25_score_messages` scorer (`compression/scoring/bm25.py:34`) inside a SabiRoute-owned select-and-drop loop, or equivalently a vendored ~60-line scorer. Recommended: SabiRoute-owned adapter, drop-only, fail-closed, behind flag, with a six-proof evidence bar before enablement.
- **T9-B (D8, tool-bearing): PARTIALLY RECOVERABLE.** The blanket v1 bypass can be narrowed. First-turn tool *declarations* with zero tool activity (no `tool_calls`, no tool messages, no `content: None`, no list content) are a restricted-eligibility candidate: transform trailing user text only, everything else deep-equal frozen. Live tool exchanges, forced `tool_choice`, structured output, and multimodal stay mandatory bypass. A role-aware system/developer freeze is prerequisite to any FULL eligibility.
- **T9-C (D19, structured quota estimation): RECOVERABLE with a metering-integrity fix.** The quota path admits tools/schemas/response_format *uncounted* (budget path rejects them; quota path has no extras allowlist). This silent under-reservation is a metering-integrity bug that must close regardless. A versioned tiered estimator (Tier 1 text / Tier 2 capped structural / Tier 3 explicit refusal) lets bounded-structured requests keep being admitted with a conservative hold instead of being rejected once the gap closes. Budget path untouched.
- **T9-D (D10/D20, retry headroom): NO CHANGE — status quo already embodies the O2 pin.** Traced both governors: retry eligibility and caps are monotone-shrink on write-once original-basis figures; no optimization symbol exists anywhere in `src/`, so savings currently *cannot* buy retries. Recommendation: keep (A); validated effective-estimates enter only as shadow-mode logging, then tightening-only at most.
- **T9-E (D21, estimator confidence): RECOVERABLE as process, not as numbers.** The estimate↔actual join keys already exist in finalized usage events; zero live paired rows exist in-repo, so all 14 aliases are UNKNOWN today. Proposed: UNKNOWN→UNCALIBRATED→BOUNDED→CALIBRATED ladder with promotion/demotion rules and labelling discipline (`estimated_*` vs `provider_reported_*` vs `billed_*`; savings language forbidden until validated).
- **T9-F (D22, ordering experiments): STAGED without forced BM25.** Pre-BM25, exactly two order experiments are distinguishable (RTK↔Caveman swap; stage ablation) plus a pipeline-integrity harness prerequisite. The full D9 triple is deferred until the retrieval-free adapter passes its six proofs. Comparability preserved via frozen corpus versions and pre-registered selection criteria.
- **T9-G (D23, unknown usage): BUG REPRODUCED — mixed known/unknown partial-settlement understates quota.** `finish()` settles `_sum_actual_tokens(...)[2]` with no unknown-usage consult (completions.py:602–603); the "unknown holds estimate" comment describes unimplemented intent. Unknown is fail-closed for budget, fail-open for quota. Proposed: bounded recovery (settle-at-estimate on any unknown, unknown-aware retry break, periodic reconciler that settles — never releases — stuck rows).
- **T9-H (D14, telemetry): RECOVERABLE via separate store (Option A).** The 1.1 gate is load-bearing (6+ enforcement points across 2 files); any in-record approach forces a disguised migration. Ranked: (A) separate table, conditioned on building a new non-blocking write convention first; (B) separate column acceptable with strict conditions; (C) in-record merge rejected.

**Groups:** §20 gives Group A (recoverable now), Group B (recoverable after adapter/proof), Group C (must remain deferred/excluded), each with required approval and evidence gate.

---

## 2. Verified Repository Baseline

VERIFIED by direct inspection this session (before investigation and re-confirmed before writing this report):

| Item | Value |
|---|---|
| Branch | `feat/sabiroute-routing-foundation` |
| HEAD | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` |
| Previously reviewed baseline | `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` — **matches; repository has not changed** |
| Tracked modifications | none (zero non-`??` lines in `git status --porcelain`) |
| Stash | empty |
| R6 pack | `docs/r6-architecture-decision-pack.md` — present, untracked (`??`), read in full (Terminal E final challenge) |
| Resolution campaign | `docs/r6-decision-resolution-and-approval-campaign.md` — present, untracked (`??`), read in full |
| T8 decision register / owner-decision documentation in tree | **none found** — no committed T8 register; tree search for terminal/owner-decision records returns only the two R6 docs, the ADR (unrelated F-27/R3 work), and the scorecard (unrelated R3/R4 work). Owner acceptance of T8 recommendations "in conversation" is **UNRESOLVED from the tree's perspective**: no committed record exists, so this report treats all non-owner-documented recommendations as recommendations, not approvals |
| This report | `docs/r6-t9-capability-recovery-review.md` — absent before this task, no conflict |

Worktree note: sibling detached/prunable worktrees exist under `/private/tmp` and docs-publishing worktrees exist as siblings; none were touched (§21).

---

## 3. Review Methodology and Evidence Standard

**Method.** Eight parallel read-only investigators (T9-A through T9-H), each constrained to static inspection (Read/grep/sed) at HEAD `319a711`, forbidden from creating, modifying, executing, installing, benchmarking, calling providers, committing, or altering git state. Each investigator returned a labelled report; this document synthesizes them. No investigator output is quoted as user input or as approval; where investigators disagree or leave gaps, this report says so.

**Evidence labels** (preserved from investigators; synthesis judgments by this author are marked PROPOSED/INFERRED):

- **VERIFIED** — read directly at the cited file:line on this baseline.
- **PARTIALLY VERIFIED** — corroborated but with a caveat (e.g. negative-search result, single-sided read, pipe-masked exit code).
- **INFERRED** — follows from verified code but not directly observed.
- **PROPOSED** — recommendation or new design, not fact.
- **UNRESOLVED** — could not be established; always paired with the smallest next investigation.

**Cross-cutting rule applied throughout:** a proposal that violates a §4 invariant is rejected or redesigned regardless of capability gain. No scoring system is used to offset safety failures.

**Limitations of this review.** All package claims are static-inspection (no execution, per mission rules); runtime confirmation of pure functions (e.g. executing `bm25_score_messages` on fixtures) is explicitly deferred as smallest-next-step work. No provider calls were made, so no B2 (provider-measured) evidence exists or is claimed. Investigator line citations are against HEAD `319a711` as inspected; drift in untracked working-tree docs is noted where relevant.

---

## 4. Existing Architectural Invariants

Non-negotiable (from the T9 mission; each recovery proposal in §§5–12 was tested against all fifteen):

1. The original request remains immutable.
2. The effective request is constructed separately.
3. One validated effective request is used consistently across retries and fallbacks.
4. A failed, unsupported, invalid or timed-out optimization returns the original request.
5. No repeated transformation of already-transformed input.
6. SabiRoute retains policy and orchestration ownership.
7. LiteLLM does not become the policy authority.
8. Actual provider usage remains distinct from estimated token savings.
9. No original or transformed prompt text in telemetry, logs, or persistent optimization metadata.
10. Tenant isolation maintained.
11. Optimization execution bounded and off the async event loop.
12. The 300-second ingress-to-completion deadline semantics preserved.
13. Routing, admission, reservation and settlement invariants intact.
14. Unsupported multimodal, structured-output and tool-bearing requests never silently damaged.
15. No new optimization capability enabled by default without passing its gates.

---

## 5. T9-A — BM25 Recovery (D6)

**Verdict: RECOVERABLE — retrieval-free BM25 is technically feasible in installed `litellm-1.103.0`. Not via stock `compress()`; via a SabiRoute-owned select-and-drop adapter.**

### 5.1 The independent BM25 primitive exists — VERIFIED

- `.venv/lib/python3.11/site-packages/litellm/compression/scoring/bm25.py:34–39` — `def bm25_score_messages(query: str, messages: list[dict], k1: float = 1.5, b: float = 0.75) -> list[float]`. Pure stdlib (`math`, `re`, `collections.Counter`; module docstring line 5: "No external dependencies — uses only stdlib"). No provider calls, no cache, no tools, no stubs. Deterministic, bounded. VERIFIED.
- Exported through `litellm.compression.scoring.__init__.py:1–4`, but NOT at top-level `litellm` or `litellm.compression` (`__init__.py` exports only `compress`). Status: public-by-export but undocumented; deep import path is version-coupling surface. PARTIALLY VERIFIED (read, not executed).
- Signature contract: consumes already-text `content` fields; internal text extraction handles `str` fully, list content partially (only `type=="text"` blocks plus bare strings — tool_result/image blocks silently score as empty → 0.0, fail-closed direction but silent, so the adapter must guard). VERIFIED.
- Empty query returns all-0.0 (`bm25.py:37–38`). The adapter must define query = last-user-message text (mirroring `compress.py:423`) and fail closed when empty. VERIFIED.

### 5.2 `compress()` call chain on `call_type=completion` — VERIFIED stage map

| Stage | Location | Reuse verdict |
|---|---|---|
| Normalization (shallow-copy + content surrogate) | `compress.py:99–124` | Reimplement (~10 lines); do not import private helpers |
| Trigger check (token counter on originals; below-trigger returns messages unchanged, `cache={}`, `tools=[]`) | `compress.py:405–420` | Reimplement concept (SabiRoute has its own estimator) |
| Scoring (last-user-message → `bm25_score_messages`) | `compress.py:127–132`, `:426` | **Reusable as-is — the one safe import.** Embedding branch (`:428–442`, `litellm.embedding()`) is a provider call: excluded |
| Selection (protected indices + budget selection) | `compress.py:225–243`, `:268–343` | Reimplement (SabiRoute protection policy differs; see §5.3) |
| Stubbing (dropped → key + cached content + stub text writing "Use litellm_content_retrieve tool…" into content) | `compress.py:485–495`, `message_stubbing.py:68–71` | **UNSAFE — must never be constructed** |
| Cache (`cache[key] = content`, full original text, returned in result) | `compress.py:494`, `:505–512` | **UNSAFE — must never be constructed, held, or forwarded** |
| Tools (retrieval-tool builder injecting `litellm_content_retrieve`) | `compress.py:47–66`, `:498`, `retrieval_tool.py:7–32` | **UNSAFE — must never be called; adapter passes no tools** |
| Truncation (first-70%-plus-last-30% lines) | `message_stubbing.py:76–112` | Reusable concept; reimplement or copy, don't import private-adjacent helpers |

### 5.3 Protection and span semantics on the completion path — VERIFIED

- `get_protected_indices` (`compress.py:225–243`) protects all `system` messages, the last user message, the last assistant message, and Anthropic cache-breakpoint prefixes. Limitation: "last assistant" assumes post-request transcript compression; SabiRoute trims the *outbound* request, so protecting it must be an explicit policy choice, not inherited. Recommended SabiRoute-owned set: all system + last user (+ explicit decision on last assistant, default include, documented). VERIFIED.
- Tool-span gating: `tool_exchange_spans` populated ONLY `if _is_anthropic_call_type(call_type_str)` (`compress.py:448–450`); on the completion path the list stays `[]` and the drop computation returns empty. Every message is therefore an independent keep/drop unit with **no atomic-span semantics** — a drop-based adapter can split assistant↔tool_result pairs with no stock guardrail. The adapter MUST enforce its own OpenAI tool-call atomicity (keep/drop pairs atomically or abort trim). VERIFIED.
- SabiRoute substitution point: `payload.messages` is `list[dict[str, Any]]` (`api/completions.py:146`); `LiteLLMClient.chat_completion` builds `{"model": decision.deployment, "messages": list(messages), **extra}` (`providers/litellm_client.py:81–85`, stream variant `:143–148`); call sites pass `payload.messages` through at `completions.py:1521–1522` / `:1539–1545`. Substituting a filtered list of the *original dicts* before the attempt loop requires zero client/provider changes. Constraints the trimmed list must satisfy: dicts keep original `role`+`content` shape (estimator raises `UnsupportedBudgetRequest` on non-str content, `security/budgets.py:26–30`); no new top-level keys (BYOK-0 key scan, `completions.py:111–137`, `:337–345`); cleanest insertion is a single point after classification/eligibility, before budget-reserve, so budget/snapshot/attempts all see the trimmed list. VERIFIED (code locations); insertion-point choice PROPOSED.

### 5.4 Options evaluation

- **(A) Direct use of the independent primitive** (import `bm25_score_messages`, own selection loop, drop-only): LOW-MODERATE version coupling (one deep-path function + text-extraction semantics, pinned by contract test); LOW maintenance (~100-line selector); structure preserved (original dicts, same objects); stubs/cache/tools eliminated by never constructing them; fail-closed; bounded (pure stdlib, O(messages × terms)); testable without providers. **Recommended core.** PARTIALLY VERIFIED (read, not executed).
- **(B) SabiRoute-owned retrieval-free adapter** (A fully specified: own normalization/selection, never-stub/never-cache): identical merits; REQUIRED framing, not optional — this is select-and-DROP (or truncate-then-drop), never select-and-stub. **Recommended together with A.**
- **(C) Minimal maintained adapter around internals** (import protected-indices/truncate/content helpers, post-process result to strip stubs/cache/tools): **REJECTED** — depends on private + semi-public names across 3 modules plus the cache/tools-bearing shape; fail-closed is inverted (must detect and remove unsafe artifacts rather than never creating them); strictly worse than B on every axis. PROPOSED (design judgment).
- **(D) Separate local BM25 implementation** (vendored ~60-line scorer, zero `litellm.compression` imports): ZERO coupling; trivial maintenance (stable math; prefix-expansion quirk droppable); otherwise identical to B. **Co-recommended** — A-vs-D is a judgment call (fewer lines + coupling vs more lines + decoupling); for a gateway owning its request path, D is defensible and arguably preferable. PROPOSED.

### 5.5 Recommended integration design + limitations

New module (e.g.) `src/sabiroute/routing/context_trim.py` — PROPOSED location in `routing/` (implemented package), not `intelligence/` (deliberately empty placeholders): `select_messages(messages, *, query_from_last_user, token_budget_fn, protected_roles={"system"}, protect_last_user=True, tool_integrity=True) -> (kept_messages, trim_report)`. Loop: extract query text from last user message (str only, else fail closed) → score via (A)/(D) → protected set → keep-protect + fill by score until budget → DROP the rest (never stub) → enforce OpenAI tool-call atomicity (restore pair or abort) → return original dicts in original order + report `{dropped_indices, scores_hash, reason}`. Insert once before budget-reserve; explicit opt-in (config flag + per-request trigger), default OFF; trim report into telemetry. PROPOSED.

Limitations: text-only str content (multimodal/custom fail closed to no-trim); lexical signal only, no embeddings; tool-pair atomicity is SabiRoute-owned (stock gives none); last-assistant protection is policy; scoring semantics (prefix expansion) pinned by test. Six enablement proofs required before any stub-free output reaches a provider (see §10/§15: no unresolved instructions, no unsupported tool injection, valid structure, no silent context loss, usable without round-trip, fail-to-original).

UNRESOLVED + smallest next steps: (a) execute `bm25_score_messages` on 3–5 fixtures in a scratch interpreter (no providers; pure function) to promote feasibility from inspection to runtime; (b) confirm live `payload.messages` dict-key inventory (do `tool_calls`/`tool_call_id` shapes occur? sets tool-integrity strictness); (c) owner decision A-vs-D + last-assistant policy, then contract test first.

---

## 6. T9-B — Tool-Bearing Request Recovery (D8)

**Verdict: PARTIALLY RECOVERABLE — narrow the blanket bypass to first-turn declarations; everything with live tool activity stays bypass.**

### 6.1 How tool-bearing requests appear — VERIFIED

- Request shape: `ChatCompletionRequest.model_config = ConfigDict(extra="allow")`, `messages: list[dict[str, Any]]` (`api/completions.py:140–147`). Unknown top-level fields (`tools`, `tool_choice`, `response_format`, …) land in `payload.model_extra`. VERIFIED.
- Top-level tool detection only (`capabilities.py:104–110`): `tools` non-empty list, or `tool_choice` not None/`"none"` → `tool_use_required=True` + `Capability.TOOL_USE`. Same predicate duplicated in the snapshot builder (`intelligence/dataset.py:189–192`). VERIFIED.
- Message-internal tool shapes are INVISIBLE to the gateway: repo-wide grep for `tool_calls|tool_call_id|function_call|parallel_tool` returns zero hits in `src/` and `tests/` outside the two top-level predicates (PARTIALLY VERIFIED negative result). Assistant `tool_calls`, `role: tool/function` messages, multi-step exchanges, `content: None` turns: NOT parsed, NOT validated, NOT classified anywhere. Messages are forwarded verbatim via `LiteLLMClient` (`providers/litellm_client.py:81–85`, `:143–148`; call sites `completions.py:1520–1526`, `:1539–1545`; shallow `list(messages)` copy only). VERIFIED.
- `response_format`: any non-None → `structured_output_required` + `Capability.STRUCTURED_OUTPUT`; dict with `type in {json_object,json_schema}` → `Capability.JSON` (`capabilities.py:112–121`); snapshot category none/text/json_object/json_schema/other (`dataset.py:165–177`). VERIFIED.
- Multimodal: `content: list` scanned for image/image_url/input_image (→ vision) and input_audio/audio/video/input_video (→ multimodal); unknown part types (e.g. `text`) explicitly NOT multimodal (test-covered, `tests/test_capabilities.py:115–129`). Same detector duplicated in `dataset.py:193–202`. Estimator FAILS CLOSED on anything non-text (`security/budgets.py:16–40`). Length cap applies only to `str` content (`completions.py:347–357`) — list/None content skips both estimation and length enforcement. VERIFIED.
- System/developer indistinguishability: no code in `completions.py`, `capabilities.py`, `budgets.py`, or `dataset.py` reads `message["role"]` (PARTIALLY VERIFIED negative result). Classification, budget, snapshot, eligibility are role-blind today; any "user-text-only" rule needs NEW role-aware code. PROPOSED prerequisite.

### 6.2 Preserve-set for any transform — VERIFIED

Everything in `model_extra` flows into `**extra → LiteLLM payload` verbatim except popped keys (`completions.py:900–918`: extras minus None/`model`/`messages`, popping `stream`, `temperature`, `max_tokens`, free-chat marker, user-id field; budgeted requests additionally reject extras outside `{top_p, frequency_penalty, presence_penalty, stop, stream_options}`, `:949–964`). Preserve byte-for-byte: `tools`, `tool_choice`, `response_format`, `stream`/`stream_options` (default `include_usage` injection at `:1516–1519`), `temperature`, `max_tokens` (or post-budget `attempt_max_tokens`, `:1406–1432`), sampling/stop params, any other caller extra. `model` always overridden — never preserve caller `model`. VERIFIED.

Even a text-only rewrite can still differ in: role sequence / pairing adjacency (gateway never checks; provider does); token counts (reservations use pre-transform estimates — transform MUST precede snapshot/estimation or telemetry describes unsent text); extras-drift. Internal validity ≠ provider-payload equivalence: UNRESOLVED without payload-capture tests (no such coverage exists today; stubs record deployment names only, `tests/conftest.py:374–440`).

### 6.3 Three-class evaluation + eligibility matrix — PROPOSED

- **Class 1 — plain-text, no tools:** FULL eligibility candidate under predicate `tool_use_required==False AND structured_output_required==False AND multimodal==False AND every message dict-with-str-content AND scalar metadata AND role order preserved` — but only with system/developer byte-frozen (new code). Without that freeze, degrades to RESTRICTED. PROPOSED.
- **Class 2 — tool-bearing, structures frozen, only independently-eligible text transformed:** narrow coexistence POSSIBLE iff ALL hold: (a) `options.tools`/`tool_choice`/`response_format` deep-equal pre/post; (b) message count + per-index role/name/`tool_calls`/`tool_call_id`/`function_call` keys identical — transform touches ONLY `content:str`; (c) NO `tool_calls`/`function_call`/`tool_call_id`, no `tool`/`function` role, no `content: None` in pre OR post (first-turn setup only: tools declared, no activity yet); (d) no list content; (e) extras deep-equal. Under this predicate the independent-unit-scoring concern is structurally excluded (no pairs exist yet). Anything with live `tool_calls`/tool messages → NOT Class 2. PROPOSED.
- **Class 3 — structurally ambiguous/unsupported:** mandatory BYPASS — any `tool_calls`/`tool_call_id`/`function_call`, `tool`/`function` role, `content: None`, list content (even text-only parts), non-scalar fields, forced `tool_choice` beyond absent/`none`/`auto` (exact forced-choice semantics UNRESOLVED), `response_format` + tools, any multimodal, any estimator rejection, any BYOK-adjacent key. PROPOSED.

Required validation before accepting a transformed request (PROPOSED, at an eligibility checkpoint AFTER classification, BEFORE budget/snapshot/reservation): (1) shape gate implementing the predicates (role-aware + ID-key scans); (2) frozen-subtree proof (canonical-JSON deep-equal of tools/choice/format/non-target messages/extras); (3) ordering proof (count + per-index role/name/key-set equality); (4) budget proof (post-transform re-estimate; reject on `UnsupportedBudgetRequest`/over-budget; snapshot AFTER transform); (5) provider-payload proof (capture `{model, messages, extras}` at the `LiteLLMClient` boundary in tests; diff confined to allowed strings).

Minimum adversarial fixtures (PROPOSED): first-turn tools + plain history (expect RESTRICTED pass); parallel `tool_calls` + reordered results; single-char `tool_call_id` mutation; assistant `content: None` + `tool_calls`; dropped/duplicated tool result; system-prompt paraphrase (must reject); mixed text+image; `json_schema` + tools; `stream_options`/`extra_body` passthrough; estimator rejections.

UNRESOLVED + smallest next steps: (1) pin the exact OpenAI/LiteLLM tool-message contract the proxy enforces (one read-only pass over pinned proxy version/config); (2) confirm optimizer insertion point vs classify → budget → snapshot → reserve → invoke chain; (3) locate the cited "engine scores tool messages as independent units" component in `src/` (name/symbol search found no such module — PARTIALLY VERIFIED) to check its pairing assumption against predicate C.

---

## 7. T9-C — Structured Quota Estimation (D19)

**Verdict: RECOVERABLE — and partly REQUIRED: the quota-path extras gap is a metering-integrity bug that must close; a versioned tiered estimator lets bounded-structured requests stay admitted once it does.**

### 7.1 Estimator and callers — VERIFIED

- `estimate_input_tokens(messages)` (`security/budgets.py:16–40`): compact-JSON UTF-8 bytes + `16/message + 4`. Fail-closed: empty list, non-dict message, non-str content, non-scalar metadata, serialization failure → `UnsupportedBudgetRequest`. Docstring claims "conservative UTF-8 byte upper estimate"; the 16/4 framing constants are asserted without per-provider proof — UNVERIFIED as universal bounds. VERIFIED (code); bound claim UNRESOLVED.
- Production callers: budget admission (`completions.py:943`, → 400 `budget_request_unsupported` on rejection); quota admission (`completions.py:1088`, → 400 `QUOTA_MAX_TOKENS_REQUIRED` on rejection — mislabeled, see §7.2); reservation sizing (`:1198–1201`, `reserved = estimated + max_tokens`); per-attempt monetary cap (`:1407–1430`, reuses admission estimate); retry guard (`:1601–1608`); telemetry snapshot (`dataset.py:161`, the only failure-tolerant caller). VERIFIED.

### 7.2 Budget-vs-quota gap — VERIFIED metering-integrity bug

- Budget path: closed extras allowlist (`completions.py:949–955` minus `{top_p, frequency_penalty, presence_penalty, stop, stream_options}` → 400 on remainder, `:956–964`). Tools, `tool_choice`, `response_format`, modality params: REJECTED when budget configured; list-content messages rejected by the estimator (`:943–948`; test-proven fail-closed). VERIFIED.
- Quota path (`completions.py:1073–1104`): after identity/`covers()`/max_tokens checks, the ONLY shape check is the same messages-only estimator (`:1088–1093`). NO extras allowlist, no tools/response_format/modality inspection. Consequences VERIFIED: (i) text-messages + tools/schemas/response_format in extras → ADMITTED with messages-only reservation (structured spend uncounted, unbounded underestimate); (ii) list-content or tool-call-bearing messages → 400 with type `QUOTA_MAX_TOKENS_REQUIRED` (`:1091`), conflating "shape unsupported" with "max_tokens missing" — mislabeled error; (iii) forwarding is verbatim (`litellm_client.py:81–85`), so unestimated extras ARE sent to the provider — real spend, no hold. Settle self-corrects only when actuals known (`:596–620`); unknown usage holds the (under-)estimate. VERIFIED (code); (iii)-spend-real is INFERRED from verbatim forwarding.
- Asymmetry: tool DEFINITIONS ride in extras (quota-ignored); tool CALLS ride in messages (quota-rejected). VERIFIED.

### 7.3 Tiered estimator proposal — PROPOSED (quota first, budget untouched)

Versioning: `ESTIMATOR_SCHEMA_VERSION` (e.g. `quota-est-v1`) persisted on reservation row and snapshot; additive-only per version; budget path keeps calling `estimate_input_tokens` unchanged.

- **Tier 1 — supported text** (str content + scalar metadata, incl. system/developer): reuse identical messages-only computation so budget/quota agree on the text baseline. Confidence: HIGH for admission-safety direction on byte-oriented text tokenizers, LOW for exactness — classification "conservative text upper-bound, uncalibrated." Policy: admit when estimate+max_tokens fits; reject only Tier 3 shapes (typed `unsupported`, and fix the error type: shape-unsupported must NOT reuse `QUOTA_MAX_TOKENS_REQUIRED` — introduce `quota_request_unsupported`). Settle to actuals; unknown holds estimate. PROPOSED.
- **Tier 2 — supported structured under caps** (tool definitions, JSON schemas, `json_object`/`json_schema` response formats, tool-call argument payloads — all JSON-serializable, text-representable): NEW function `estimate_structured_input(messages, tools, response_format, tool_calls, *, version)` = Tier 1 + Σ `len(compact_json(unit)) + per_unit_framing`, each unit under explicit caps (max units, max depth e.g. 8, max bytes e.g. 64KiB); any cap trip → Tier 3, never truncate-to-fit. Confidence MEDIUM for admission ordering, LOW for token equality — "conservative structural upper-bound, uncalibrated, capped." Policy: admit when Tier1+Tier2+max_tokens fits; cap trips denied with NAMED reason (depth/size/count). Settle to actuals; unknown holds Tier1+Tier2 (never downgrade at settle). Tests: per-category fixtures, cap-trip ±1 tests, determinism (canonical compact JSON), version persistence, budget-path regression proving no behavior change. PROPOSED.
- **Tier 3 — explicit unsupported/unknown** (multimodal list parts, non-JSON-serializable or over-cap structures, opaque passthrough like `extra_body`/`litellm_params`, unknown future fields): typed `unsupported(reason, pointer)`; NO number, NO zero, NO best-effort. Deny before reservation with specific reason; denial counted distinctly from `quota_exceeded`. Tests assert NO reservation row and NO provider call on Tier 3 denial. PROPOSED.

### 7.4 Explicit answer

Can structured-request quota estimation reduce unnecessary rejections? PARTIALLY — precisely scoped. Against *today's* quota behavior, Tier 2 does not reduce rejections (structured requests are currently admitted under-reserved, not rejected) — it increases hold accuracy. Its rejection-reducing value is against the SECURE baseline: once the extras gap closes (it must), the naive fix rejects ALL structured requests; Tier 2 is what lets text+bounded-tools/small-schema keep being ADMITTED with a conservative hold. It also converts mislabeled shape-denials into actionable ones. PROPOSED assessment on VERIFIED gap.

UNRESOLVED + smallest next step (no new instrumentation, no provider calls): read-only join of EXISTING telemetry — snapshot `estimated_input_tokens` vs provider `prompt_tokens` actuals grouped by alias + tool_use/response_format/multimodal flags — plus a shape census of Free Chat extras (keys, depth/size of tools/schemas in practice). Yields byte-estimate bias per alias, Tier 2 cap values, and an observed-shape-grounded Tier 3 list. Until that audit runs, no Tier 2 constant may be presented as calibrated.

---

## 8. T9-D — Retry Headroom Recovery (D10/D20)

**Verdict: NO CHANGE — the O2 pin is already embodied in current code; validated estimates enter at most as shadow-mode logging.**

### 8.1 Both governors traced — VERIFIED (`api/completions.py`)

Symbol table VERIFIED: E=`estimated_input` written ONCE at `:943` (budget-gated; unbudgeted keep E=0); M0=`max_tokens` popped at `:907` (budgeted must be positive-int, `:932–941`); R=`reserved_tokens` written ONCE at `:1199` (`E + max_tokens`; grep shows no other write); C_est=`estimated_cost` written ONCE at `:1201` (worst-case max across candidates, None if any price missing, `budgets.py:43–71`); a_i=`_actual_tokens(body)` tuples (`:239–250`); U_k=`_sum_actual_tokens` (`:253–264`, Nones skipped); `cost_usage_parts` → `_actual_cost` (`:1992–2012`, None on unknown/empty/missing-price); `provider_usage_unknown` set-only, never reset; attempt cap `range(1, policy.max_attempts+1)` (`:1345`; alias-direct cap 2, `:150–164`; named-policy caps UNVERIFIED — not read); `attempted` list gates `release_budget=not attempted` (zero-attempt ⇒ release, else reconcile/settle).

- **Cost governor** (`:1406–1432`): per-attempt local `attempt_max_tokens`; eligibility pinned to ORIGINAL E (`input_cost = E × price` at `:1420`) and ORIGINAL C_est (`remaining_cost` at `:1414`); fail-closed on unpriceable spend (`:1410–1411`), missing estimate (`:1412–1413`), missing price (`:1418–1419`); cap shrinks only (`min()` at `:1430`); `break` if `<1` (`:1431–1432`). VERIFIED.
- **Token governor** (`:1599–1609`, in the failure handler after recording): `retryable` = None-status or ≥500 or ∈ {401,403,429} (`:59`, `:1600`); `break` if not retryable OR (budget held AND usage unknown) (`:1601–1602` — fail-closed); budget-held + known failure usage → `used=Σ known totals`, `remaining=R−used`, `break` if `remaining ≤ E`, else OUTER `max_tokens = min(max_tokens, remaining − E)` (`:1603–1608`). This is the `max_tokens` mutation: it ratchets ALL future attempts' starting cap. `reserved_tokens` never rewritten. VERIFIED. Reachability note: `:1604`'s `or 0` executes in practice only with all-accumulated totals known (unknown breaks first at `:1601`) — INFERRED, high confidence.
- **Monotonicity** VERIFIED by grep: no code path increases `max_tokens`, `attempt_max_tokens`, `reserved_tokens`, or `estimated_cost` after admission; headroom is monotone non-increasing across attempts.
- **Settlement** VERIFIED (`finish()`, `:542–679`): budget reconcile overwrites `accounted_*` ONLY when actuals non-None, else the ORIGINAL ESTIMATE STAYS HELD (conservative; `store.py:1213–1247`); quota settle-or-release `:596–620`; telemetry records estimate + reservation + actuals side by side (`:633–648`).
- **Unknown → fail-closed** VERIFIED at every path: provider failure (`:1567–1574`, `:1601–1602`); generic attempt exception (`:1688–1727`, unknown if budgeted, loop exits via raise); deadline-cancel (`:1610–1662`); client-cancel (`:1663–1687`); incomplete streams (`:1812`, `:1869–1878`). Timeout (status None) IS retryable but still breaks when budget held and usage unknown. VERIFIED.

### 8.2 Could optimization enlarge retries under current code? NO — DISPROVED

(i) Absence VERIFIED: grep for `effective_estimate|validated_estimate|input_optim|optimiz.*input|savings.*retry` over `src/` returns NOTHING — no optimization/validated-estimate symbol exists; `completions.py` contains zero matches for `optimiz|effective|validated|savings|compress`. There is literally no input surface for savings to flow through. (ii) Mechanism VERIFIED: governors still charge E per future attempt (`:1420`, `:1606`) regardless of true prompt shrinkage; optimization can at most leave actuals under reservation (reconcile releases the difference) — it CANNOT buy an extra attempt or a larger output cap. The brief's warning is REAL but FUTURE: the moment anyone substitutes E′ for E at `:1420`/`:1606`/`:1608` (or rewrites R/C_est mid-loop), savings convert to headroom. O2's pin is exactly the right guardrail, and current code already implements it. VERIFIED mechanism + PARTIALLY VERIFIED absence (negative search).

### 8.3 Alternatives with worked numbers — PROPOSED analysis on VERIFIED code

Common scenario: E=8000, M0=2000 → R=10000, C_est=$0.01600 (in $1/M, out $4/M); two failed attempts at 600/200/800 each; U_2 totals 1200/400/1600.

- **(A) Original-estimate (= current code):** token: used=1600, remaining=8400 > 8000 → CONTINUE, M3=min(2000,400)=400. Cost: spent=$0.00280, remaining=$0.01320 > input $0.00800 → cap 1300 → attempt_max=min(400,1300)=400. Attempt 3 runs with 400 output tokens; max extra exposure ≈$0.0022, inside remaining. VERIFIED behavior.
- **(B) Validated effective-estimate forecasting** (E′=650 for line `:1420` only): no change here (token governor binds); matters only when cost binds — raises cost cap 1300→3137 (+1837 output tokens, ≈+$0.00735/attempt, compounding over an UNVERIFIED named-policy attempt bound). Failure modes: stale/underestimated E′ (prompt varies, deployment differs, adversarial growth) → overrun absorbed only because R/C_est stayed pinned; unknown-usage + E′ must still break. **REJECT as control change.** PROPOSED.
- **(C) Separate token/cost heads, non-fungible:** formalizes what code already does de facto; identical result here (400); divergence example favors cost binding on expensive-output deployments. Value is guardrail-against-fungible-pools, not behavior change. Acceptable as documentation/refactor; REJECT any fungible-pool variant. PROPOSED.
- **(D) Conservative hybrid (shadow-first):** eligibility/caps stay EXACTLY (A); validated E′ (max observed actual prompt + margin, clamped ≤E, recomputed per attempt) logged per attempt with ZERO control effect; promote to tightening-only after N requests of shadow agreement. Max exposure ≤ (A) by construction; only new risk is a missing clamp (assert E′≤E + log). **RECOMMENDED if anything beyond status quo.** PROPOSED.

**Recommendation: (A) status quo for all retry-eligibility and cap control.** UNRESOLVED + smallest next steps (read-only, ~15 min): (1) read named-policy `max_attempts` (config + `routing/policies.py`) — bounds worst-case compounding for ANY future (B); (2) confirm `reconcile_budget` parity across store backends for the unknown-hold path (interface seen `keys.py:322–339`, behavior not traced — PARTIALLY VERIFIED).

---

## 9. T9-E — Estimator Confidence (D21)

**Verdict: RECOVERABLE as an evidence process — structurally calibratable today, evidentially at zero. All aliases UNKNOWN; no code change can grant calibration, only paired data can.**

### 9.1 Estimator, consumers, usage trail — VERIFIED

- Definition: `budgets.py:16–40` (formula compact-JSON UTF-8 bytes + 16/msg + 4; fail-closed shapes); `estimated_cost_usd` worst-case quote `budgets.py:43–71`. "Conservative upper estimate" is an ASSERTION IN CODE (comment `:19–22`), not a proof — no tokenizer table, factor, or error bound implemented. VERIFIED.
- All six consumers traced: budget admission (`:943`), quota admission (`:1088`), reservation sizing (`:1198–1201`), per-attempt monetary cap (`:1407–1430`, estimate reused, never recomputed), retry guard (`:1601–1608`), telemetry snapshot (`dataset.py:159–163`, only failure-tolerant caller). VERIFIED.
- Provider-usage trail VERIFIED end-to-end: parse `_usage_object`/`_safe_token_count`/`_actual_tokens` (`:224–250`); per-attempt records on failure (`:1567–1597`), success (`:1903–1928`), streaming completed/interrupted (`:1798–1808`, `:1829–1858`); builder `_routing_attempt_event` (`:2015–2102`, usage dict + `actual_cost_usd` + 1.1 timestamps); cumulative idiom `tokens=None-tuple if unknown else sum` (8 sites); settlement — budget reconcile holds estimate on unknown (`store.py:1213–1247`), quota `settle(None)` holds estimate / `settle(actual)` consumes (`store.py:1343–1380`, idempotent); finalize `finish()` (`:542–679`) persisting estimate + reservation + actuals side by side (`:633–648`).
- **Cost is NOT billed cost** VERIFIED: `_actual_cost` (`:1992–2012`) is a registry-price computation returning None on unknown; no invoice/billing API called anywhere in this path (INFERRED from absence).
- **Savings fields do not exist** VERIFIED (grep for saving(s)/billed over src+tests+config: zero production hits). Realized savings needs an unrecorded counterfactual; estimated savings needs two estimates with stated assumptions.
- **Alias→model mapping** VERIFIED: `_resolve_target` (`:150–175`) → registry candidates; `config/config.yaml:17–254` maps 14 public aliases (`sabiroute-openai → openai/gpt-6-luna`, gemini, groq, together, deepinfra, kimi, minimax, cloudflare, openrouter, huggingface, cerebras, nvidia, cohere, pollinations) to provider routes whose tokenizers matter; `ProviderDeployment` (`providers/base.py:32–51`). NO per-alias calibration data, factors, error columns, tokenizer or tiktoken call anywhere in src/tests (VERIFIED negative; only hits are a comment and R6-doc D11 OPEN rows). D11's "accept default encoding, label estimates, never re-run" is DOCS-ONLY, not implemented. `usage_source` (`keys.py:89` = {unknown,free_pool,byok,paid}) has exactly one assignment (`free_pool`, `:1068`) — byok/paid semantics UNRESOLVED. VERIFIED.
- **Zero error measurement** VERIFIED: `test_phase10.py:586` is a tautology (implementation vs itself); `:657` checks cost arithmetic on stubbed 3/2/5 usage; quota tests assert hold/settle behavior, never error magnitude. No test computes estimate−actual, relative error, under-estimation rate, or per-alias tables.

### 9.2 What is recordable today vs needs authorization — VERIFIED paths

Recordable TODAY without new provider calls (all co-located in finalized `RequestUsageEvent`/dataset export): (estimate, provider prompt), (estimate, provider total), (estimate, computed actual_cost) — snapshot estimate + outcome usage joined by (request_id, attempt); audit counters (`attempts_with_provider_usage`, `attempts_with_actual_cost`, `dataset.py:894–901`) already built. Offline-only: estimate determinism on synthetic fixtures (pure function). NOT recordable: billed cost (no source); estimated/realized savings (no fields, no counterfactual); NEW paired observations (each costs one authorized provider call; stubbed 3/2/5 usage must never count). VERIFIED.

### 9.3 Proposed confidence strategy — PROPOSED

Categories: UNKNOWN (zero audited pairs — all 14 aliases start here) → UNCALIBRATED (some pairs, insufficient) → BOUNDED (≥N_min e.g. 100 pairs/alias within fixed code/config version across size+unicode buckets, under-estimation ≤ tolerance or documented headroom eliminating in-sample breach — empirically bounded, never universally proven) → CALIBRATED (BOUNDED sustained ≥2 windows + unchanged config/tokenizer + human review + approval record). Promotion UNKNOWN→UNCALIBRATED automatic on audited rows; higher promotions human-only on dataset audit reports; DEMOTION automatic on model-string change, alias re-point, payload-shape change, breach, or unknown-spike. Insufficient-evidence posture codifies current behavior (fail-closed shapes, estimate-held settlement, pricing-required gate; NO relaxation multipliers from "expected over-estimation"; NO savings language for UNKNOWN/UNCALIBRATED). Measurement: offline fixture suite for regression (not accuracy) + paired per-alias/per-bucket bias, MAE/RMSE, p50/p95/p99, P(estimate<actual), unknown-rate — on AUTHORIZED live runs only. Labelling: `estimated_*` (byte formula, unproven bound) vs `provider_reported_*`/`actual_*` (parsed bodies) vs `billed_*` (no source — never emit); `*savings*` forbidden until both legs actual with stated counterfactual.

UNRESOLVED + smallest next steps: (U1) run the existing dataset audit over the deployed usage-store copy (read-only, no provider calls) grouped by alias/deployment — decides whether N=0 truly; (U2) enumerate `litellm_params.model` → tokenizer families from config+docs (syntactic, no assertion) for future bucketing; (U3) confirm byok/paid semantics with owner before evidence reports filter on it; (U4) confirm savings workstream accepts computed-cost-only (no billing integration scoped here).

---

## 10. T9-F — Ordering Experiments (D22)

**Verdict: STAGED — two distinguishable pre-BM25 experiments plus an integrity harness; the full D9 triple deferred with comparability preserved.**

### 10.1 Greenfield confirmed; D6/D9 posture — VERIFIED

- No optimization/stages/pipeline module; no filename matching rtk/caveman/bm25/okapi/retrieval; seven 0-byte placeholders (`__init__`, `intelligence/classifier|scorer|selector`, `routing/intelligent`, `security/permissions`, `utils/time|logging`) beside substantial implemented neighbours (`intelligence/dataset.py` 71105 bytes, routing/router|scoring|health|policies). VERIFIED layout + PARTIALLY VERIFIED content-absence (two independent empty searches; pipe-free re-run still owed — U2). Corroborated by pack §13.2 and campaign §4-D9/D4/D5. So: RTK/Caveman greenfield, no BM25 code, D6 restriction stands.
- Stage contract VERIFIED (pack §6; campaign §4-D9, §5.6, §6, §7.1, §11): pure functions over immutable input; complete-candidate-or-original (never partial); transform-once before `:1345`; fixed gates S0-first/S4-last/S5-observer with only S1/S2[/S3] permuting (PROPOSED scoping — needs T8 confirmation, U4); three representations (original/effective/record); prohibited flows (cache/transformed/prompt-substring sinks).
- D6 gates VERIFIED (campaign §7.1): R6.4 construction-behind-flag permitted; exit = disabled-boundary proof (vacuous-but-verifiable); enablement post-v1 needs (i) T8+Owner D6→(b) with named reviewed adapter, (ii) six proofs as R6.6 corpus evidence, (iii) B1 re-run green. D9 ruling VERIFIED (campaign §4-D9, §5.6): freeze stable interfaces in R6.5 with ordering configurable; measure all three in R6.6; select in R6.6; owner-fixed order = CONDITIONAL.

### 10.2 Distinguishability — INFERRED from the disabled-boundary definition

Pre-BM25 the executable stage set is {S0,S1,S2,S4,S5} (S3 byte-identical passthrough) → exactly 2! = 2 distinguishable orders. Any arm differing ONLY in BM25 position while S3 is disabled is observationally identical — hence no third experiment pre-BM25.

- **E1 — order swap** (RTK→Caveman vs Caveman→RTK): executable pre-BM25. Varies relative order only; holds corpus version, configs, bypass rules, validation, tokenizer-C, O2 pinning, deadline/placement constant. Metrics: per-stage/total reduction, provider-reported prompt tokens (labelled estimated), per-stage + total latency (separate from provider latency), B1 gates per arm, routing invariance BLOCKING even in B2, B2 paired task-success/cost (advisory). Earns its place: the only true ordering comparison available. PROPOSED.
- **E2 — marginal-contribution ablation** (neither / RTK-only / Caveman-only / both-in-default-order): executable pre-BM25. Varies subset; holds same constants + fixed order for the both-arm (order belongs to E1). Metrics: incremental reduction/latency/cost per stage, B1 attribution, fail-closed rate. Earns its place: stops a superior order masking a useless stage; gates R6.2/R6.3 exits. PROPOSED.
- **E3 — pipeline-integrity harness** (prerequisite, not an ordering arm): flag/fault matrix over the B1 table (disabled byte-identity, validation-reject→original, retry-identity, latency separation, `optimization_timeout`, no-network, canary no-leakage, S03/S04/S06/S07/tool-bypass, streaming identity). Must be green before E1/E2 are interpretable. PROPOSED.
- **REJECTED pre-BM25:** R-A "BM25-bypass vs BM25-absent" (varies nothing observable — indistinguishable by definition); R-B/R-C any BM25-ENABLED arm incl. the D9 triple (emits unresolved stub instructions — DEFERRED to Stage B). PROPOSED rejections on VERIFIED D6 grounds.

### 10.3 Order-agnostic interfaces + future comparability — PROPOSED on VERIFIED sources

R6.5 freezes: ordering as validated configuration (transform-stage ID list; unknown/duplicate/disabled-enabled fail loudly; default-off); transformation record carrying `pipeline_order` + per-stage `{id, position_index, outcome/bypass, estimated-token delta, latency_ms}` + `config_version`, keyed by (logical_request_id, attempt_number), strictly content-free; retry-identity across orders (effective frozen before `:1345`, O2-pinned arithmetic, B1 retry-identity re-run per order); pure-function conformance per position (whichever stage runs second receives the first stage's COMPLETE candidate or the original); fixed-gate invariance (S0 eligibility incl. D8 contract always first; S4 + BYOK-0 recheck last; S5 observes only). PROPOSED (needs T8 scoping U4).

Comparability when BM25 arrives: reuse the SAME corpus version (pack §16.3: versioned, secret-free, stable IDs, hashes, redaction scan, adversarial negation/numerics/paths/identifiers — S08 has no machine enforcement so corpus is the only evidence); frozen arm definitions recorded as (corpus_version, stage_subset, pipeline_order, stage_config_versions incl. tokenizer-C label, O2 flag, bypass-rule version); pre-BM25 arms re-run unchanged alongside new BM25 arms; selection rule (primary metric, MDE, n/power, routing-invariance blocking status, arm order, conditions) written BEFORE R6.6 E1/E2 execution AND re-affirmed before the BM25-era run (D15: B1 mandatory/blocking, B2 advisory, post-hoc thresholds rejected; Terminal D reconciliation before G4 still pending). PROPOSED content on VERIFIED requirements.

UNRESOLVED + smallest next steps: (U1) confirm whether untracked working-tree R6 docs are canonical / should be committed — cite "working-tree R6 docs, 2026-11-03" until ruled; (U2) pipe-free greenfield re-run (`grep -rn … ; echo $?` + filename search); (U3) issue Prompt D (campaign §13) and record threshold demands before any R6.6 execution; (U4) T8 ruling that only S1/S2/S3 permute.

---

## 11. T9-G — Unknown Usage and Reservation Recovery (D23)

**Verdict: BUG REPRODUCED (mixed known/unknown partial-settlement) / DISPROVED (pure-unknown case). Bounded recovery proposed; blind TTL release rejected with accounting analysis.**

### 11.1 The mixed-case hole — VERIFIED line sequence

`finish()` (`completions.py:542–679`) takes NO unknown-usage parameter. Quota branch (`:596–620`): `if attempted: quota_total = _sum_actual_tokens(actual_usage_parts)[2]` → `settle_quota(user, req, quota_total)`. The identifier `provider_usage_unknown` appears 20× in the file and ZERO times in this branch — every caller instead uses the inline ternary `tokens=None-tuple if unknown else sum(...)` for TELEMETRY (`:1327–1329`, `:1377–1379`, `:1461–1463`, `:1490–1492`, `:1718–1720`, `:1872–1874`, `:1948–1950`, `:1966–1968`, `:1983–1985`) and budget reconcile (`:575–583`), while the quota path recomputes the sum from scratch, discarding the flag. The comment at `:597–599` ("unknown usage holds the estimate") documents UNIMPLEMENTED intent for the mixed case. VERIFIED.

`_sum_actual_tokens` (`:253–264`) SKIPS None components — a partial sum returns with no unknown marker. `settle_quota` (`store.py:1369`: `settled = actual if non-None else estimate`) then settles the partial sum AS IF COMPLETE. The unknown portion is neither consumed nor held — silently forgiven. VERIFIED.

Worked example VERIFIED against code (quota-only, reserved 6000): attempt 1 fails retryably with error-body usage total 5000 → banked; attempt 2 times out with no usage → `failure_usage` None → flag stays False on quota-only paths (`:1573–1574` requires `budget_reserved`) → retryable → loop ends → `settle_quota(user, req, 5000)`: reserved−6000, consumed+5000. True provider-side consumption ≥ 5000 + attempt-2's unknown tokens. Understatement up to ~100% of the unknown attempt; with budget held the ledgers additionally DISAGREE (budget holds estimate, quota settles partial). VERIFIED mechanism; numbers PROPOSED illustration.

### 11.2 Asymmetry, gaps, lifecycle — VERIFIED

- Unknown is fail-closed for BUDGET (`:1601` break; `:1410–1411`, `:1418–1419`; reconcile holds estimate, `store.py:1233–1236`) but fail-open for QUOTA (no break, no hold — settles partial). Cost is fail-unknown (`_actual_cost` None on unknown, `:1992–1998` — the cost path takes the flag; quota does not). VERIFIED.
- Flag-production gaps VERIFIED (all budget-gated, all silent on quota-only): failure-without-usage (`:1573–1574`), success-with-usage-None (`:1903–1911` — and budget reconcile then UNDERstates too, the one sub-case where budget is also wrong), stream-completed-without-usage (`:1798–1808` → `:1872–1874`), incomplete stream (`:1812`), deadline-cancel (`:1627–1628`), unexpected exception (`:1693`), mid-attempt caller-cancel (`:1680–1686`, telemetry None-tokens IGNORED for quota since parts uncleared and flag unset).
- Correct-by-construction sub-cases (DISPROVED as vulnerabilities): all-unknown/empty parts → sum None → estimate held; zero-attempt denials → release, never settle (`:612–619`); pre-attempt cancels → release + `_cancelled_finish` never settles (`:723–784`); store idempotency (reserved→settled once via SELECT..FOR UPDATE, `:1353–1390`; release-after-settle no-op; admission no-op on same request_id; finalize `final_status IS NULL` guard, `:1501–1522`). VERIFIED.
- No reservation expiry exists: `_QUOTA_RESERVATIONS` (`store.py:127–136`) has `created_at`, no `expires_at`, no status beyond reserved/settled/released; `_BUDGET_RESERVATIONS` (`:433–446`) likewise (sole `expires_at` at `:463` is unrelated chat sessions). Negative grep for reap/sweep/stale/orphan/TTL: no hits (PARTIALLY VERIFIED). A stuck `reserved` row (settle exception skips flag-clear at `:573`/`:620` while finalize still records; process crash between reserve and finish) pins tokens against the window FOREVER within it — damage bounded by daily window rollover (`:1318` counts reserved+consumed). VERIFIED schema + PARTIALLY VERIFIED absence. No cross-request reconciler, no sweeper, no admin repair path (PARTIALLY VERIFIED) — recovery ownership today: nobody.

### 11.3 Bounded recovery proposal — PROPOSED (not implemented)

Goal: never retain a reservation forever, NEVER treat partial actuals as complete.

1. States: reuse the column, add `settled_estimate` (settled-with-actuals-absent, auditable); transitions only out of `reserved` (existing guards extended). 2. Settlement rule (fix at `:602–610`): pass the unknown flag INTO `finish()` (new keyword, default False) and settle `None` (hold estimate) whenever attempted AND (unknown flag OR any banked total-None OR success/stream-completed with usage None). Partial sums must NEVER reach `settle_quota` as `actual_tokens`. 3. Idempotency: recovery uses the SAME store entry points (inherits guards). 4. Ownership: (i) request path — extend `:1601` to break on unknown regardless of budget (quota fail-closed like budget: stop spending + hold estimate, NOT release-to-zero); (ii) NEW periodic reconciler (gateway background task or admin-triggered job) owning stuck `reserved` rows older than threshold whose usage event is finalized — action settle-at-estimate ONLY, N rows/pass + jitter + metrics, failures surfaced never silent. 5. Limits: reconciler attempts/row bounded (e.g. 3, then alert, row stays reserved — visible over-retention beats invisible under-settlement); live-loop consecutive-unknown cap (e.g. break after 1 unknown when quota held). 6. Audit: `settled_estimate` status + reason (live-unknown / stuck-recovery) written to row or telemetry; stuck counts on admin (currently reserved-only at `admin.py:317` — PARTIALLY VERIFIED). 7. Failures: keep 503-on-settle-error; reconciler is the backstop; crash-mid-request = stuck-row case. 8. Expiry analysis (as required — NO blind TTL): blind TTL release = UNDER-SETTLEMENT (frees capacity the provider consumed → over-admission vs real bills; invisible leak) — unacceptable default. Over-retention / settle-at-estimate = availability cost only (bounded by window rollover; visible; self-healing for admission) — acceptable default, because provider spend is unrecoverable. Principle: unknown/stuck ⇒ hold/settle-at-estimate, never release-to-zero, never partial-as-complete. PROPOSED throughout.

UNRESOLVED + smallest next steps: (1) read `admin.py` quota endpoints fully (only `:317` spot-checked) to confirm no manual repair path; (2) confirm in config whether quota-gated keys ever run without monetary budget (is the quota-only fail-open path live or latent); (3) read `tests/test_user_quotas.py` mixed-usage cases for asserted settle-with-partial expectations the fix must update.

---

## 12. T9-H — Telemetry Infrastructure (D14)

**Verdict: RECOVERABLE — ranked (A) separate store > (B) separate column (conditional) > (C) in-record merge (rejected). A new non-blocking write convention is prerequisite to all.**

### 12.1 The 1.1 gate is load-bearing — VERIFIED (`intelligence/dataset.py`, `security/keys.py`)

Type freeze: `FEATURE_SCHEMA_VERSION: Literal["1.1"]` (`:23`); feature model accepts {"1.0","1.1"} defaulting 1.1 (`:57`); `attempt_schema_version: Literal["1.1"] | None` (`:109`); all three models `extra="forbid", frozen` (`:37`, `:55`, `:101`). Enforcement: temporal-provenance early-return (`:339–344` — any non-1.1 ⇒ `temporal_provenance_unknown_for_schema`, unrecoverable in-function); readiness blockers (`:1077–1103`, BLOCKED unless zero); export gate (`:666–682`, raises unless READY + all-diagnostic); integrity counting (`:1266–1530`, incl. schema-1.1 timestamp/tz/ordering requirements `:1467–1508`, version-disagreement bucket `:1460–1466`); write-path validation (`keys.py:146–263`, both-sides-1.1 agreement `:236–258`, snapshot continuity `:266–298`). Blast radius of ONE new attempt field VERIFIED as a chain: `_safe_outcome` allowlist (`:259–288`) must add it → model `extra="forbid"` forces declaration → declaration forces honest 1.2 → six literal `== "1.1"` tripwires (`:339–344`, `:902–912`, `:1247–1248`, `:1435`, `:1460–1466`, `keys.py:237–243`) count 1.2 rows as provenance-unknown → readiness BLOCKED. INFERRED conclusion: an attempt-record field is a schema migration in disguise; the freeze is load-bearing, not decorative.

### 12.2 Current telemetry inventory — VERIFIED

- Stores (`security/store.py`): `_API_KEYS`, `_API_KEY_RATE_LIMITS`, `_REQUEST_USAGE` (request_id PK, key_id FK, project_id, created_at, requested_alias — stored raw, redacted only at export — final_deployment/status, prompt/completion/total, failure_category, estimated_input/reserved/costs, `routing_decisions` + `pre_routing_features` JSON lists, feature_schema_version, usage_source), `_BUDGET_RESERVATIONS`, `_QUOTA_WINDOWS/_RESERVATIONS`, `_ACCOUNTING_LINEAGES`, 4 SabiChat tables. Migration rule additive-only. VERIFIED.
- No event-type mechanism exists: routing/feature columns are untyped JSON lists with NO discriminator or registry; only enum-like is per-request `usage_source` (`keys.py:89`). Option B must BUILD the type system, not flip a flag. VERIFIED absence.
- Attempt emission (`completions.py`): snapshot builder (`dataset.py:128–247`, allowlisted scalars only — `_safe_size` measures, text never returned — plus `tool_use`/`response_format_category`/multimodal/max_tokens/capabilities); outcome builder (`completions.py:2015–2102`, 1.1 timestamps hardcoded `:2085`); sinks: admission row (`:375`), per-attempt snapshot (`:1469–1474`), once `finalize_usage_event` (`:651–656`) — durable store is the ONLY attempt-telemetry sink; in-memory trackers (gateway) carry aggregates only. Admin read (`admin.py:281–331`): full `pre_routing_features` + `routing_decisions` to any holder of the single shared admin secret — NO projection, NO per-operator ACL. Any new usage-row field is admin-visible by default. VERIFIED.
- Tenant isolation today: application-level `key_id` predicates (strong on finalize `:1516–1518`, list `:1531`; ABSENT on snapshot-append by request_id-only lookup `:1461–1499` — PARTIALLY VERIFIED gap); no row-level security, no namespaces, no tenant-routing key prefixes (format-only `sr_live_`, `keys.py:16`); readers are binary (no access vs full-row admin). INFERRED: boundary = WHERE clause + shared secret. VERIFIED components as cited.
- Fail-closed telemetry is the CURRENT default and there is NO drop-record helper — VERIFIED ABSENT: snapshot failure 503s before the provider starts (`:1497–1502` → `:786–832`); finalize failure converts success to 500/503 (`:666–677`). Only in-memory trackers are non-blocking. Any optimization-telemetry write therefore needs a NEW explicit non-blocking convention (try/except + `redact_secrets` logging, response untouched) — must be built and tested, not assumed. VERIFIED absence.

### 12.3 Required record + option ranking — PROPOSED design on VERIFIED inventory

Content-free record INCLUDE (scalars/enums/ids only): stage-outcome map, bypass reasons, validation verdicts, estimated vs provider-reported token ints, optimization latency ms, config version, (logical_request_id, attempt_number) join keys. EXCLUDE (structural rule): prompt/transformed content, cache objects, secrets, keys, retrieval/chunk content, embeddings, raw messages/options/extras, provider error bodies. Structural form PROPOSED: Pydantic `extra="forbid"`, frozen, NO free-text fields except enums/ids/versions; builder accepting ONLY scalars + the sanitized usage tuple — never messages/options/responses.

- **(A) Separate table** (e.g. `sabiroute_optimization_records`, PK (request_id, attempt_number), key_id + project_id NOT NULL): LOW-MODERATE migration (one additive table + ledger revision, fits the rule); separable failure domain; BEST observability (query optimization without touching content-adjacent rows; narrow admin projection); ZERO 1.1 blast radius; STRONGEST isolation (partitioned by table, not predicate); leakage vector = builder only (guard: scalar-only signature + no text/blob column ⇒ content has nowhere to land even on regression); failure = new non-blocking convention (required). **Ranked first, conditioned on (1) the non-blocking write convention shipping first and (2) key_id-write predicate mirroring finalize.** PROPOSED.
- **(B) Separate nullable JSON column on the usage row + dedicated narrow endpoint:** LOWEST DDL; but invents the event-type system ad hoc; inherits parent-row scoping (ACL = convention to use the narrow endpoint — the existing full-row endpoint already reads everything); needs read-projection allowlist (`_safe_outcome`-style) + explicit exclusion from `diagnostic_export_rows`/training-candidate scope by test; same new non-blocking write needed; must keep the column out of `validate_usage_event_finalization` scope (separate today — VERIFIED). **Acceptable ONLY with all conditions in one change.** PROPOSED.
- **(C) Fields in the attempt record / feature snapshot:** LOWEST upfront DDL, HIGHEST total cost — forces the 1.2 migration (§12.1); merges control data into the training-audit surface (bypass reasons ride into every diagnostic/training envelope unless stripped — stripping = another allowlist; new "debug context" precedent invites content-adjacent fields that become accidental future training features — label leakage IN, the mirror of content leakage OUT); inherits fail-closed telemetry. Guard weakest (review discipline, not structure). **DO NOT PURSUE.** PROPOSED rejection on VERIFIED gate chain.

UNRESOLVED + smallest next steps (each <30 min): (1) repo-wide caller census for the two snapshot/finalize writers (only completions/store/keys/dataset/admin/gateway/auth/executor/redaction read this pass); (2) decide the non-blocking primitive (candidate: try/except around executor run; `BoundedStoreExecutor` run is await-only, `store_executor.py:130–179` — VERIFIED); (3) requested_alias handling needs no action for A (joins avoid it), but any B/C reader must confirm it never surfaces alias-adjacent content.

---

## 13. Cross-Cutting Capability Recovery Matrix

PROPOSED synthesis on the VERIFIED evidence cited in §§5–12. No weighting is used; any invariant breach would veto regardless of gain (none of the ACCEPT/narrow rows breaches one).

| Decision | Original restriction | Recoverable capability | Proposed implementation | Evidence | Architectural impact | Complexity | Risk | Required tests | Dependency | Recommendation | Approval |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D6 | BM25 integration deferred (stock stub/cache/tool contract unusable) | Lexical context selection via retrieval-free adapter | SabiRoute-owned select-and-drop (`routing/context_trim.py`): scorer (import `bm25_score_messages` or vendored) + own selection + drop-only + tool-atomicity + fail-closed; single insertion pre-reserve; flag-gated, default OFF | pkg `scoring/bm25.py:34`; `compress.py:448–450` (no span protection); `litellm_client.py:81–85` (verbatim forward); §5 | none (new module; no Track A file touched until insertion) | Medium | Medium | scorer contract test; structure-preservation (identity/order/roles/no-new-keys/no-tools); tool-atomicity; budget-order tests; six enablement proofs (R6.6 corpus) | D6→(b) + Owner; D8 pairing proof; D17 for insertion | **NARROW: build disabled infrastructure in R6.4; enable ONLY post-v1 on six proofs** | T8+Owner; Track A (insertion) |
| D8 | ALL tool-bearing requests bypassed in v1 | First-turn tool declarations (no activity) → restricted text optimization | Eligibility predicate C (§6.3) + five validation proofs (shape, frozen-subtree, order, budget, payload-capture); role-aware system/dev freeze prerequisite for FULL | `capabilities.py:104–121`; `dataset.py:189–202`; `completions.py:900–918`; §6 | none (new gate code; predicates additive) | Medium | Medium | 10-fixture adversarial matrix (§6); payload-capture diff tests | D8 narrowed; D17 if gate lives in `completions.py` | **NARROW: Class 1 FULL (with freeze), Class 2 RESTRICTED, Class 3 BYPASS** | T8+Owner; Track A if in Track A files |
| D19 | Structured requests: budget rejects, quota silently under-reserves | Bounded-structured requests admitted with conservative hold | Tiered versioned estimator (`quota-est-v1`): Tier 1 text baseline; Tier 2 capped structural (depth/width/byte caps, named denials); Tier 3 explicit refusal + NEW `quota_request_unsupported` type; budget path UNCHANGED | `budgets.py:16–40`; `completions.py:949–964` vs `:1073–1104`; `litellm_client.py:81–85`; §7 | none (quota path only; reservation basis stays conservative) | Medium | Low-Medium | cap-trip ±1; determinism; version persistence; budget-regression; no-reservation/no-call on Tier 3 | D19; D17 (quota path is Track A-adjacent) | **ACCEPT: close extras gap + Tier 1 now; Tier 2 after telemetry-join audit sets caps** | T8+Owner; Track A |
| D10/D20 | Retry uses original estimate only (O2); validated estimates excluded from control | Cost-forecast insight WITHOUT control change | (A) status quo for ALL eligibility/caps; (D) shadow-mode: log clamped E′ (≤E) per attempt, zero control effect; promote to tightening-only after N-request agreement | governors `:1406–1432`, `:1599–1609`; monotonicity grep; absence grep; §8 | none under (A)/(D-shadow) | Low | Low (shadow) | shadow-agreement metric; clamp assertion E′≤E; named-policy `max_attempts` bound read | D10 confirmed | **ACCEPT (A); DEFER (B); shadow-first (D)** | T8 notes; Owner only if (B) ever revived |
| D21 | No estimator trust (uncalibrated byte formula) | Evidence ladder + labelling discipline; future calibration | UNKNOWN→UNCALIBRATED→BOUNDED→CALIBRATED with auto-demotion; join-based measurement on authorized traffic; savings language forbidden until validated | `budgets.py:16–40`; join keys `finish()` `:633–648`; alias catalog `config.yaml:17–254`; zero-error-measurement §9 | none (process + audit queries; no admission change) | Low | Low | fixture determinism suite; per-alias error metrics (no bias assertions until BOUNDED+) | D21; owner on byok/paid semantics + billing-source scope | **ACCEPT as process** | T8; Owner (U3/U4 scoping) |
| D22 | D9 triple unmeasurable without BM25 | Two pre-BM25 experiments + harness; deferred triple with comparability | E3 harness → E1 swap → E2 ablation (Stage A, R6.5/R6.6); full triple + arm re-runs (Stage B, post-adapter); frozen corpus versions; pre-registered criteria | greenfield §10.1; D6 gates; D15 threshold discipline | none (experiment plan; interfaces frozen, ordering configurable) | Low-Medium | Low | B1 per arm; routing-invariance blocking; criteria pre-registration artifact | D22; D6(b) for Stage B; Terminal D before G4 | **ACCEPT staged plan** | T8+Terminal D; Owner only if fixing order early (CONDITIONAL) |
| D23 | Unknown usage handling as-coded (partial-settlement hole) | Correct settlement + bounded stuck-row recovery | pass unknown flag into `finish()`; settle-at-estimate on any unknown; `:1601` break regardless of budget; periodic reconciler (settle-only, bounded, audited); `settled_estimate` status | `:596–620` vs ternary sites; `store.py:1343–1390`; no-expiry §11.2 | strengthens invariant 13 (settlement integrity); reconciler is new surface (bounded, settle-only) | Medium | Medium (fix) / Low (reconciler, bounded) | mixed known/unknown settle test; unknown-break test; idempotency tests; reconciler scope/bound tests | D23 NEW; D17 (touches `completions.py` + store) | **ACCEPT: fix + reconciler; REJECT blind TTL release** | T8+Owner; Track A (required) |
| D14 | Optimization telemetry homeless (1.1 frozen) | Content-free optimization record WITHOUT touching 1.1 | (A) separate table + scalar-only forbid-model builder + NEW non-blocking write convention; (B) conditionally; (C) rejected | gate chain §12.1; store inventory §12.2; admin full-row read `:281–331` | none under (A) (additive table; attempt record untouched) | Medium (A) | Low-Medium (A, conditioned) | canary no-leakage; conformance; non-blocking proof (telemetry failure ⇒ request unaffected); projection tests | D14; D17 (store + `security/store.py`) | **ACCEPT (A) conditioned; (B) conditional; REJECT (C)** | Track A + T8; Owner (strategy) |

---

## 14. Benchmark and Adversarial Test Requirements

The R6 benchmark strategy (synthetic corpus, pack §16 / campaign §16-equivalent) stands; this report adds request-shape and execution-condition coverage required by the recovered capabilities. **B1 = offline/mechanical (blocking). B2 = provider-measured (advisory until thresholds agreed BEFORE execution — D15; no B2 results fabricated or claimed here).**

### 14.1 B1 — offline validation (new/augmented requirements from T9)

- **Request-shape preservation:** post-trim message count/order/roles/key-sets; same object identities where required; no added keys; no tool injection; str-content only on budgeted path.
- **Structural integrity:** frozen-subtree deep-equal (tools/choice/format/non-target messages/extras); OpenAI tool-pair atomicity (parallel `tool_calls` + reordered results; single-char `tool_call_id` mutation must abort trim).
- **Protected-content preservation:** system/developer byte-freeze (once role-aware gate lands); last-user protection; `content: None`/list-content never transformed.
- **Transformation correctness:** scorer contract (fixed-fixture score ordering; empty-query all-zero; prefix-expansion pinned); budget-order conformance; truncate-then-drop semantics where applicable.
- **Fallback correctness:** fault injection per stage → byte-identical original; validation-reject → original; `optimization_timeout` category on overrun (distinct from provider `deadline_exceeded`).
- **Tenant isolation:** per-tenant-namespace + TTL unit tests for RTK state (R6.2 exit: no stale or cross-tenant reuse); telemetry builder signature test (no message/options parameter exists); table-has-no-text-column assertion.
- **Accounting properties:** retry-identity (all attempts same effective object); Tier 2 cap-trip economics (reserve = Tier1+Tier2+max, settle to actuals); mixed known/unknown settle-at-estimate; unknown-break in retry governor; store idempotency (double-settle/release-after-settle/admission no-ops).
- **Resource bounds:** pure-stdlib scoring budget; max messages (256) + max chars scored caps; bounded pool + input caps + cooperative checks; `to_thread`-is-not-cancellation accounted (bounded *work*, not merely waited).
- **Retry consistency:** E1/E2 arms re-run retry-identity per order; shadow-E′ agreement metric (forecast vs actual, zero control effect).

### 14.2 B2 — provider-dependent validation (gated, not executed)

- Actual prompt-token reduction; provider-reported usage; per-stage + total latency vs provider latency separation; cost per successful task; per-alias estimation error (bias, MAE/RMSE, p50/p95/p99, P(estimate<actual), unknown-rate per size/unicode bucket).
- Minimum mandatory adversarial tests per recovered capability: the §6 ten-fixture tool matrix; Tier 2 cap-boundary fixtures (±1 on depth/bytes/count); multimodal-each-type denial with modality reason; stub-instruction absence proof (no `litellm_content_retrieve` substring in ANY emitted payload); cache-absence proof (no full-original-text object traverses the provider path); unknown-usage settlement reconciliation against provider-side meters where separately authorized.
- Threshold discipline: primary metric, MDE, sample size/power, routing-invariance blocking status, arm order, and evaluation conditions declared BEFORE execution (Terminal D reconciliation before G4 still pending — campaign Prompt D). Post-hoc thresholds rejected.

### 14.3 Corpus additions required

Beyond pack §16.3: tool-lifecycle shapes (first-turn declarations; parallel calls; reordered/duplicated/dropped results; ID mutations; `content: None` turns); structured shapes (tool defs at depth limits; JSON-schema response formats; over-cap units); extras-carried modalities; forced-`tool_choice` objects; `stream_options`/`extra_body` passthrough; unknown-usage trajectory shapes (timeout-after-banked-usage; usage-less success). Same corpus rules: versioned, secret-free, stable IDs, hashes, provenance, redaction scan.

---

## 15. Proposed R6 Roadmap Integration

No stage merged, renamed, reordered, or removed. Adjustments are dependency/gating clarifications only:

- **R6.0 (freeze):** ingest this report as input; resolve NEW decisions D19–D23 (§17) alongside D6/D8/D14/D10; T8 scope the "ordering configurable" boundary (U4, §10); confirm working-tree R6 docs canonical-or-commit (U1); owner notes (not approves) the extras-gap closure (D19) and D23 fix as metering/settlement integrity work.
- **R6.1 (foundation):** unchanged scope (immutable original, canonical representation, metadata, policy/capability checks, bypass) PLUS: role-aware eligibility scan + frozen-subtree/order/budget/payload validation hooks (T9-B, behind flag); estimator version field plumbed (T9-C Tier 1 bookkeeping only); unknown-flag-into-`finish()` + `:1601` hardening (T9-G fix — Track A surface); shadow-E′ logging (T9-D, zero control); non-blocking telemetry-write convention (T9-H prerequisite). Exit adds: E3 harness green (§10).
- **R6.2 (RTK):** unchanged + per-tenant namespace/TTL + no-stale/no-cross-tenant tests; state-key includes policy/model/context (per campaign D4).
- **R6.3 (Caveman):** unchanged + natural-language-spans-only + protected-class bypass + fail-closed validation; role-aware freeze shared with T9-B gate.
- **R6.4 (BM25):** construction-behind-flag + disabled-boundary exit UNCHANGED (§7.1 gates stand); the T9-A adapter design is what gets constructed; enablement still post-v1 on six proofs. Adds: D11 compat matrix (CONDITIONAL), D8-pairing proof independence, Tier 2 estimator available for its admission math.
- **R6.5 (orchestration):** freezes stable interfaces with ordering configurable (requires T8 U4 ruling); one validated effective request per logical request; E1/E2 executed on frozen corpus v1 with pre-registered criteria.
- **R6.6 (benchmark):** B1 gates (incl. all §14.1 additions) + E1/E2 evidence; D9 order NOT selected for BM25 positions (deferred); D15 thresholds pre-declared; Terminal D reconciliation before G4.
- **R6.7 (observability/rollout):** separate content-free record on Option-A store (R6.1 convention + R6.4+ writes); savings-vs-actual reporting ONLY for BOUNDED+ aliases (D21 ladder); disabled-by-default rollout; reconciler (T9-G) operationalized with bounds + admin visibility.

Release gates G4 (benchmark — needs Terminal D), G5 (red-team — stays blocked pending D6/D8 corrections), G7 (implementation authorization — cannot be requested by this report) unchanged.

---

## 16. Track A and Approval Dependencies

Track A owns (per campaign §15 + conflict controls): `completions.py` (`api/`), `gateway.py`, `main.py`, `config/validation.py`, `security/store.py`, plus dataset/migration files. Verified relevance to T9 proposals:

| T9 proposal | Track A surface touched | Sign-off needed before |
|---|---|---|
| D6 adapter insertion (effective binding, pre-reserve placement) | `api/completions.py` | R6.4 construction |
| D8 eligibility gate + validation (if placed in gateway path) | `api/completions.py`, possibly `gateway.py`/`main.py` (flag, pool lifecycle) | R6.1 |
| D19 Tier 1/2 estimator + `quota_request_unsupported` + reservation version | `api/completions.py` (quota path), `security/store.py` (version field) | R6.1 (Tier 1 bookkeeping) / R6.4 (Tier 2 use) |
| D10/D20 shadow-E′ logging | `api/completions.py` (logging only, zero control) | R6.1 |
| D23 settlement fix (`finish()` flag, `:1601` break) + reconciler | `api/completions.py`, `security/store.py` | R6.1 (fix) / R6.7 (reconciler ops) |
| D14 Option-A table + non-blocking write convention | `security/store.py` (+ executor), `config/validation.py` (flag/limits) | R6.1 (convention) / R6.7 (writes) |
| D22 experiments | none directly (plan + corpus + interfaces) | R6.5/R6.6 execution |

Approval layers distinguished (no T9 authorization claimed over any):

1. **Owner-accepted T8 recommendations:** NO committed record found in tree (§2) — treated as UNRESOLVED-from-tree; this report recommends but does not assume them.
2. **T9 findings:** VERIFIED/PARTIALLY VERIFIED technical results (§§5–12) — evidence, not decisions.
3. **T9 recommendations:** PROPOSED rulings (§§5–13, §17, §20) — input to review, not rulings.
4. **Renewed owner approval required:** D6 enablement path, D8 narrowing, D19 gap closure + Tier 2, D23 fix + reconciler bounds, D14 strategy, D22 order selection (when ripe), D15 thresholds, any (B)-style retry loosening (rejected — would need fresh case).
5. **External Track A approval:** every row in the table above — silence is not approval; no Track A change authorized by this report.
6. **R6.0 architecture freeze:** this report does not grant, amend, or substitute for it.
7. **Separate implementation authorization (G7):** cannot be requested by this report; R6.1 work remains unauthorized until granted.

---

## 17. New or Revised Decision Proposals

Revisions to existing decisions: **D6 → (d)-for-v1 + (b)-via-named-adapter construction path** (adapter specified, §5; recommendation unchanged, feasibility upgraded from argument to inspected primitive); **D8 → blanket bypass NARROWED to Class 3 + Class-2-restricted + Class-1-full-with-freeze** (§6; restriction reduced, guard raised); **D10 → confirmed (A) + (D)-shadow-only** (§8; O2 pin verified as already-implemented); **D14 → Option A conditioned on non-blocking-write-first** (§12; separate-record recommendation made implementable). D9, D11, D15 rulings confirmed unchanged.

New decisions required (all OPEN unless noted; none approved here):

- **D19 — structured quota estimation tiers.** Adopt Tier 1 (text baseline, quota-budget agreement) + close the extras gap with typed `quota_request_unsupported`; Tier 2 (capped structural) only after the telemetry-join audit sets caps; Tier 3 explicit refusal. Budget path frozen. Owner: T8 + Owner; Track A. Gates R6.1 bookkeeping / R6.4 use.
- **D20 — retry-estimate forecasting discipline.** (A) status quo control; validated estimates shadow-only with E′≤E clamp; any control use beyond tightening-only is a NEW decision with fresh evidence. Owner: T8 (+ Owner if control use ever proposed). Gates nothing until invoked.
- **D21 — estimator confidence ladder.** Adopt UNKNOWN→UNCALIBRATED→BOUNDED→CALIBRATED + labelling discipline + auto-demotion; savings language gated on BOUNDED+. Owner: T8; Owner scoping on U3/U4. Gates R6.7 savings reporting.
- **D22 — staged ordering experiments.** Adopt E3→E1→E2 (Stage A) now; full D9 triple deferred to Stage B on adapter proofs; T8 rules the configurable-ordering boundary. Owner: T8 + Terminal D; Owner only for early order-fixing (CONDITIONAL). Gates R6.5/R6.6.
- **D23 — unknown-usage settlement correction.** Adopt the §11.3 fix (flag into `finish()`, settle-at-estimate, unknown-break) + bounded settle-only reconciler; REJECT blind TTL release as default. Owner: T8 + Owner; Track A (required). Gates R6.1 fix / R6.7 ops.

---

## 18. Rejected Approaches and Why

| Rejected approach | Why (evidence, not preference) |
|---|---|
| Stock `compress()` adoption (any wrapper) | Retrieval instruction lives in message content (`message_stubbing.py:68–71`); discarding tools doesn't remove it; `cache` returns full originals (`compress.py:494`); correctness defect, not hardenable — Terminal E final challenge confirmed |
| Adapter (C): post-hoc strip of stubs/cache/tools around internals | Depends on private/semi-public names across 3 modules + cache/tools-bearing shape; fail-closed inverted (detect-and-remove vs never-create); strictly worse than (B) on every axis |
| Embedding-backed scoring in the mechanical pipeline | `litellm.embedding()` is a provider call (`embedding_scorer.py:86`); breaks S10 (no external calls) and bounded-offline testability |
| Full optimization of live tool exchanges (Classes D/E) | Gateway cannot see message-internal tool structure (PARTIALLY VERIFIED negative search); no pairing protection exists on the completion path (`compress.py:448–450`); single-bit ID corruption = misattributed execution |
| Structured-output + optimization in v1 (Class B) | Schema-satisfaction unproven; no schema-aware validator exists; revisit only with one |
| Multimodal transformation in v1 (Class G) | Estimator fail-closed + length-cap blind + text↔media linkage unproven; bypass is the only non-damaging policy |
| Replacing byte estimates with raw LiteLLM tokenizer counts | Couples metering to an execution dependency's internals; violates invariant 6/7 (SabiRoute owns policy); per-alias accuracy still unproven either way |
| (B) validated-estimate retry loosening; fungible token/cost pools | Buys ≤ ~1.8k output tokens/scenario while introducing stale/underestimate overrun modes compounding over an unverified attempt bound; current governors already embody O2 |
| Furnishing savings claims for UNKNOWN/UNCALIBRATED aliases | Zero paired rows; byte bound unproven; savings fields don't exist — claims would be fabrication |
| Pre-BM25 "BM25-bypass vs absent" experiment; any BM25-enabled arm now | Former varies nothing observable; latter emits unresolved stub instructions under BLOCKED D6 |
| In-record (C) telemetry merge | Forces disguised 1.2 migration (§12.1 chain); merges control data into training-audit surface (label-leakage risk); weakest structural guard |
| Blind TTL release of stuck reservations | Under-settlement direction: frees capacity the provider actually consumed — invisible money/consumption leak; over-retention is bounded (window rollover), visible, self-healing |
| Weighted-score rescue of invariant breaches | Not used anywhere in this report; any breach vetoes regardless of gain |

---

## 19. Remaining Unknowns

Consolidated UNRESOLVED items with smallest next investigations (all read-only unless noted):

1. **Runtime confirmation of pure functions** (A-a): execute `bm25_score_messages` on 3–5 fixtures in a scratch interpreter (no providers). Promotes T9-A from inspection to runtime. (~15 min)
2. **Live `payload.messages` key inventory** (A-b, B-2): confirm which tool/message shapes occur in practice (read-only telemetry/log inspection, no provider calls). Sets tool-integrity strictness + Tier 2 scope. (~30 min)
3. **OpenAI/LiteLLM tool-message contract pin** (B-1): exact proxy-enforced semantics (roles, nullability, forced-`tool_choice`). Unblocks precise Class 3/F definitions. (~30 min, read-only)
4. **Optimizer insertion-point confirmation** (B-2): decide placement vs classify→budget→snapshot→reserve→invoke chain. (~15 min, owner+T8)
5. **Named-policy `max_attempts` bound** (D-1): read policy configs — caps worst-case compounding for any future forecasting proposal. (~15 min)
6. **Store-backend reconcile parity** (D-2): Postgres vs in-memory unknown-hold behavior. (~20 min)
7. **Live paired-row census** (E-U1): run existing dataset audit over deployed store copy (read-only). Decides whether N=0 truly; feeds Tier 2 caps + per-alias bias. (~30 min + query)
8. **Tokenizer-family enumeration** (E-U2): map `litellm_params.model` → families from config+docs (no assertion). Future bucketing. (~20 min)
9. **byok/paid semantics + billing-source scope** (E-U3/U4): owner decisions before evidence reports filter on them. (conversation)
10. **R6 docs canonical status** (F-U1): confirm untracked working-tree copies canonical / should commit. (conversation)
11. **Greenfield pipe-free re-run** (F-U2): one read-only grep without pipes. (~2 min)
12. **Order-selection criteria content** (F-U3): issue campaign Prompt D; record Terminal D threshold demands pre-execution. (review coordination)
13. **Configurable-ordering boundary** (F-U4): T8 ruling S0-first/S4-last/S5-observer frozen. (review)
14. **Admin repair-path census** (G-1): full `admin.py` quota read. (~15 min)
15. **Quota-without-budget liveness** (G-2): is the quota-only fail-open path live-today or latent. (config read, ~15 min)
16. **Mixed-usage test expectations** (G-3): read `test_user_quotas.py` mixed cases for settle-with-partial assertions the D23 fix must update. (~20 min)
17. **Telemetry writer census** (H-1): repo-wide caller check for the two writers. (~15 min)
18. **A-vs-D scorer + last-assistant policy** (A-c): owner decisions, then contract test first. (conversation + test)

---

## 20. Final Recommendation

### 20.1 Explicit answers to the twelve required questions

1. **Can we recover BM25 without unsafe stock stubbing?** YES — via a SabiRoute-owned retrieval-free select-and-drop adapter (imported or vendored scorer), disabled-built in R6.4, enabled only post-v1 on six proofs. (T9-A)
2. **Can we safely optimize a restricted subset of tool-bearing requests?** YES, NARROWLY — first-turn declarations only (predicate C + five proofs); live exchanges, forced choice, structured output, multimodal stay bypass; role-aware freeze prerequisite. (T9-B)
3. **Can structured-request quota estimation reduce unnecessary rejections?** PARTIALLY — it increases hold accuracy today and prevents mass-rejection once the extras gap (which must close) is closed; Tier 2 needs the audit-set caps first. (T9-C)
4. **Can we improve retry opportunities without weakening reservation integrity?** NO CONTROL CHANGE — status quo already embodies O2; validated estimates shadow-only. (T9-D)
5. **Can we calibrate estimates per alias without pretending exactness?** AS PROCESS, YES — ladder + labelling + auto-demotion; all aliases UNKNOWN today; no code grants calibration, only paired data does. (T9-E)
6. **Can we preserve the BM25 ordering experiment for a later stage?** YES — staged E3→E1→E2 now, full triple deferred with corpus/criteria comparability preserved. (T9-F)
7. **Can unknown-usage reservations be recovered safely without indefinite holds?** YES — settle-at-estimate fix + unknown-break + bounded settle-only reconciler; blind release rejected on accounting grounds. (T9-G)
8. **Can optimization telemetry share infrastructure without compromising separation?** SEPARATE TABLE, YES (conditioned); separate column only with strict conditions; in-record merge NO. Non-blocking write convention first. (T9-H)
9. **Highest capability gain for lowest architectural risk?** D23 fix (closes a live settlement hole, strengthens invariant 13); D19 Tier 1 + gap closure (metering integrity, no behavior widening); D21 process (unlocks all future calibration); D22 staging (unblocks R6.5/R6.6 without BM25); D8-Class-2 restricted (recovers the highest-value agentic-adjacent traffic shape — first-turn tool setup — at five-proof cost). BM25 enablement is the largest gain but correctly the most gated.
10. **Which proposals belong in the revised R6 architecture?** All Group A now (§20.2); Group B constructions (disabled) with their enablement gates recorded.
11. **Which must wait for evidence or external approval?** All Group B enablements (adapter six proofs, Tier 2 caps audit, BOUNDED+ promotion, Stage-B triple, reconciler ops tuning) + every Track A surface (§16) + Terminal D thresholds + owner decisions (§17).
12. **Which capabilities genuinely remain excluded?** Group C (§20.4): stock stubbing, embedding-backed mechanical scoring, live-tool-exchange optimization, structured-output/multimodal transformation in v1, savings claims pre-validation, fungible retry pools, in-record telemetry, blind TTL release.

### 20.2 GROUP A — Recoverable with current architecture

Each: no invariant touched; gated by stated approval + evidence.

1. **D23 settlement correction** (flag into `finish()`, settle-at-estimate, unknown-break) — approval: T8+Owner, Track A (required); evidence: mixed-settle + unknown-break + idempotency tests. Risk Low-Medium; closes a live hole.
2. **D19 Tier 1 + extras-gap closure** (typed `quota_request_unsupported`, version bookkeeping; budget frozen) — approval: T8+Owner, Track A; evidence: gap-closure tests, budget-regression. Risk Low-Medium.
3. **D21 confidence process** (ladder, labelling, demotion; audit queries) — approval: T8 (+Owner scoping U3/U4); evidence: fixture suite + live-pair census. Risk Low.
4. **D22 Stage-A experiments** (E3 harness → E1 → E2 on frozen corpus, pre-registered criteria) — approval: T8+Terminal D; evidence: criteria artifact + B1 per arm. Risk Low.
5. **D8 Class-2 restricted + Class-1-with-freeze** (predicate C + five proofs; role-aware freeze) — approval: T8+Owner (+Track A if in Track A files); evidence: 10-fixture matrix + payload-capture tests. Risk Medium.
6. **D10/D20 shadow-E′ + D22/D21 bookkeeping in R6.1** (zero-control logging; version fields) — approval: T8 notes; evidence: clamp assertions + agreement metric. Risk Low.
7. **D14 non-blocking write convention** (standalone; benefits all future telemetry) — approval: Track A; evidence: failure-proof test (telemetry failure ⇒ request unaffected). Risk Low.

### 20.3 GROUP B — Recoverable after a dedicated adapter or additional proof

1. **D6 BM25 enablement** — needs: named reviewed adapter + six proofs as R6.6 corpus evidence + B1 re-run green + D8-pairing independence + D11 matrix + D17 + D10-confirmation. Disabled construction may proceed in R6.4 meanwhile. Approval: T8+Owner (+Track A insertion).
2. **D19 Tier 2 structural estimation** — needs: telemetry-join audit (bias per alias, observed shape census) setting depth/width/byte caps + cap-trip test suite. Approval: T8+Owner (+Track A).
3. **D21 BOUNDED/CALIBRATED promotion + R6.7 savings reporting** — needs: N_min audited pairs/alias, two-window sustain, human review + approval record. Approval: T8 (+Owner for reporting language).
4. **D22 Stage-B triple + order selection** — needs: Stage-A completion + adapter proofs + Terminal D criteria + pre-registered selection rule re-affirmed. Approval: T8+Terminal D+Owner.
5. **D14 Option-A writes at volume** — needs: convention (Group A.7) + table + builder + projection tests + canary suite. Approval: Track A+T8.
6. **D23 reconciler operations** — needs: fix live (Group A.1) + bound/threshold agreement + admin visibility. Approval: T8+Owner+Track A.
7. **(D) tightening-only E′ control** — needs: N-request shadow agreement + clamp proof; loosening use REJECTED pending entirely fresh case. Approval: T8+Owner.

### 20.4 GROUP C — Must remain deferred or excluded

Stock `compress()` output adoption (any wrapper); embedding-backed mechanical scoring; live-tool-exchange / forced-choice / structured-output / multimodal transformation in v1; pre-validation savings claims; validated-estimate retry loosening and fungible pools; in-record telemetry merge; blind TTL reservation release; any default-ON optimization before its gates; weighted-score rescue of invariant breaches (methodologically excluded).

---

## 21. Verification and Worktree Report

- **Initial state (before investigation):** branch `feat/sabiroute-routing-foundation`; HEAD `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf`; zero tracked modifications; empty stash; target `docs/r6-t9-capability-recovery-review.md` absent.
- **Final state (after investigation, before writing):** branch unchanged; HEAD `319a711` (identical — repository did not change under investigation); zero tracked modifications (grep for non-`??` status lines: empty); target still absent (no investigator wrote files — confirmed by re-check).
- **After writing:** exactly ONE file created — `docs/r6-t9-capability-recovery-review.md` (this file). No existing file created-or-modified by this task (R6 pack, campaign, source, config, dependencies, migrations, datasets, scorecards, T8 records: all untouched — investigators were read-only; synthesis wrote only here).
- **Dependencies:** unchanged (no installs; `litellm-1.103.0` inspected in place, not modified).
- **Branch:** never switched; no reset/clean/stash/prune/commit/push/deploy.
- **Worktrees:** main worktree on-branch at `<repo-root>`; sibling detached/prunable worktrees under `/private/tmp` and docs-publishing worktrees untouched.
- **Verification NOT completed:** runtime execution of package pure functions (mission-forbidden; deferred as §19.1); provider-measured (B2) evidence (none claimed); live-store paired-row census (needs deployed-store read access — §19.7); full `admin.py`/quota-test reads (spot-checked only — §§19.14/16); pipe-free greenfield re-run (§19.11); owner-conversation acceptances (no committed record — §2/§16). Each names its smallest next step in §19.
- **Investigation count:** eight read-only workstream investigations (T9-A…T9-H), all static-inspection at HEAD `319a711`; synthesis by Terminal E (this author). No benchmarks run, no provider calls made, no compression executed.

**T9 success criterion — answered:** the maximum useful safely-recoverable capability is Groups A+B above (§20.2–20.3) with the exact evidence gates stated per item; Group C (§20.4) is excluded on evidence, not on caution alone. Architecture preserved: every accepted proposal satisfies all fifteen §4 invariants; every rejected one is rejected for a cited invariant or evidence failure.

---

### Document control

Created by: Terminal E — T9 capability-recovery investigator (synthesis of eight read-only workstream investigations)
Created on: 2026-11-03
Repository baseline: `319a711ef4142e6232a13f6e4bc7ec7fb74cdfaf` (verified before and after; unchanged)
Files created: `docs/r6-t9-capability-recovery-review.md` (this file) — **one file, no others**
Files modified: none
Application source, configuration, dependencies, migrations: untouched
Compression executed: no · Benchmarks run: no · Provider calls made: no · Packages installed: no
Commits, pushes, deploys, resets, cleans, stashes, prunes, branch switches: none
Authority: decision support only. Approves nothing; authorises no R6.1 work; grants no G7.
