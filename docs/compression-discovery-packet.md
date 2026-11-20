# Compression Discovery Packet — CD1–CD6 Design-Review Input (Read-Only)

**Status:** design-review input only. No compression implementation, no
dependency installation, no benchmarking, no runtime changes. Track B
implementation stays frozen until Track A is green, T8 reviews the design,
and the owner explicitly authorizes Sprint 9 (checklist Part IV gate;
`docs/architecture-decision-record.md` §3 roadmap order H; CLAUDE.md §10).

**Baseline pinned:** `feat/sabiroute-routing-foundation` @ `b360ffc`
(tree per `reconciliation-plan.md` §1; diverged ahead 2 / behind 3 —
origin Batch 2 line carries F-04/F-05 absent locally).

**Search scope:** `src/sabiroute/**` + `config/**` + `tests/**`, read-only
grep/code-inspection on 2026-10-29. Search terms: `compress`, `summariz`,
`truncat`, `token budget`, `context window`, `dedup`, `history aging`,
`preview`, `dry-run`. Limitations: keyword + import-graph inspection only;
no execution profiling, no dependency audit beyond `pyproject.toml`.

## CD1 — Capability inventory

| Candidate area | Finding | Evidence |
|---|---|---|
| Prompt/context compression | **None.** No compression, summarization, or truncation module exists | VERIFIED BY INSPECTION: zero `compress`/`summariz` hits in `src/sabiroute/**` outside token-budget quota arithmetic; placeholder files `intelligence/classifier.py`, `intelligence/scorer.py`, `intelligence/selector.py`, `routing/intelligent.py` are 0 bytes (CLAUDE.md §12 — deliberately unimplemented, left empty) |
| RTK-inspired command/output filtering | **None.** No RTK-Query-style cache, response filter, or tool-output dedup | VERIFIED BY INSPECTION: no `dedup`, no response-cache layer; `conftest.py` `StubLiteLLMClient` returns fixed payloads, no filtering |
| Caveman-style prose compression | **None.** No lossy simplification pass | VERIFIED BY INSPECTION: no prose transform; build report §7 warning heeded — absence stated only after this audit, not assumed |
| History aging / summarization | **Partial primitive, not compression.** SabiChat caps history at 20 messages (`api/chat.py`, `chat/store.py` window query) | VERIFIED BY INSPECTION: fixed `LIMIT 20`-style window, no summarization, no aging policy beyond OD-3b 30-day session purge |
| Token estimation / context budgeting | **Quota arithmetic only, not compression.** `max_tokens` guards, reservation estimates, `reserved_tokens`/`accounted_tokens` ledger fields | VERIFIED BY INSPECTION: `completions.py` quota/budget admission, `store.py` budget tables; estimates drive admission, never transform content |
| Engine interfaces / registries / config modes / preview / benchmarks | **None.** No engine ID, registry, policy mode, preview/dry-run, or benchmark harness for transformation | VERIFIED BY INSPECTION: no such symbols in tree |

**Prior/duplicate/blocked work:** none found — there is no earlier
compression implementation to protect, duplicate, or unblock. The
"RTK Token Saver" naming collision (Redux Toolkit Query caching vs.
command/output compression) and "Caveman Mode" collision (offline
philosophy vs. lossy simplification) noted in the build report §7 remain
terminology risks for any future design; they describe nothing in-tree.

## CD2 — Safe gateway hook (proposed insertion point, not implemented)

Ingress → auth/identity → usage admission → rate limit → alias/policy →
classification → capability → health → (Free Pool gate) → budget reserve →
attempt loop (`Router.choose_deployment` per attempt) → **proposed
transformation point here: after final deployment selection, before
LiteLLM invocation** → LiteLLM → `finish()` reconciliation.

Constraints the design must prove (checklist CD2; build-report §7):

- Covers streaming and non-streaming paths.
- Covers context limits, tools/schemas, cache-sensitive prefixes,
  structured content.
- Deterministic pass-through when disabled, unsupported, misconfigured,
  timed out, or errored.
- Transformation **cannot** alter routing eligibility, credentials,
  endpoint selection, tool authorization, protected request fields, or
  the 300-second hard deadline.
- Telemetry correlation without prompt-content retention (CD6).

The only transformation-adjacent seam in-tree is `max_tokens`
propagation (`test_provider_harness.py` mocked contract tests) — a
limit parameter, not a content transform. The hook is therefore a
greenfield insertion, not a modification of existing logic.

## CD3 — Independent implementation boundary (proposed)

New package (suggested): `src/sabiroute/compression/` with
`engine.py` (registry + deterministic pipeline), `policies.py`
(`off`/`lite`/`standard`/`aggressive`/`ultra`/`rtk`/`stacked` as policy
modes/presets, **not** separate engines), `preserve.py` (preservation
rules), `telemetry.py` (content-minimizing run records).

- New files: the package above + `tests/test_compression_*.py` +
  config schema additions (validated, default-off).
- Modified files (later integration only): one call site in
  `api/completions.py` attempt loop + telemetry field passthrough.
  **Not touched during discovery** — T2/T4/T5 shared files
  (`completions.py`, `main.py`, `gateway.py`, `security/store.py`,
  `config/validation.py`) are Terminal A-owned and out of scope.
- Cannot-be-isolated integrations: none identified at design level; the
  telemetry/ledger coordination point (CD6) requires Track A owner
  agreement before implementation.

## CD4 — Engine contract and preservation (requirements, not code)

- Engine ID/version + supported targets; config validation; result
  statuses (`changed`/`unchanged`/`fallback` + reason).
- Inputs/outputs: token estimates, bytes, duration, transformation
  counts; deterministic pass-through + failure semantics; registry +
  deterministic pipeline composition.
- Preservation set (lossless tiers must keep): instructions,
  constraints, negation, identifiers, code, JSON, tool schemas, URLs,
  paths, exit codes, warnings, errors, actionable tail context.
- Lossy summarization gated separately by quality/latency tests.
- `off` must be byte-identical pass-through.

## CD5 — Benchmark corpus and evaluation (requirements, not code)

- Versioned synthetic or approved-redacted corpus: Git/test/build
  outputs, install/audit logs, stack traces, shell output,
  Docker/infra output, prose, source, JSON, tool results.
- Adversarial cases: whitespace, negation, numeric thresholds, paths,
  identifiers, warnings, exit codes, truncated logs, near-duplicates,
  conflicting instructions.
- Gold preservation assertions + expected task/tool outcomes.
- Token-estimation baseline + latency methodology; engines evaluated
  individually before stacked pipelines.
- Metrics: task success, tool-call correctness, quality degradation,
  latency, provider-reported usage, estimated savings, net cost per
  successful task.

## CD6 — Telemetry integration contract (requirements, not code)

- Correlate each run with `request_id`, `decision_id`, `attempt_id`,
  final outcome; engine/pipeline version; policy mode.
- Track input/output token estimates, actual usage where available,
  duration, bytes, transformation counts, changed/not-changed status,
  fallback/error reason, correlation status.
- No prompt contents in routine telemetry.
- Correct accounting across retries, fallback, failures, partial
  streams — no double-counting; estimated vs. provider-reported vs.
  net savings distinguished.
- Any shared telemetry/ledger change coordinated with Track A owners.

## Sprint 9 design-acceptance checklist (all OPEN — owner/T8 gated)

- [ ] CD1–CD6 report complete (**this packet is input, not the report**).
- [ ] Exact baseline SHA/tree, worktrees, search scope recorded.
- [ ] Hook and independent file boundary justified.
- [ ] Engine contract + policy/configuration model specified.
- [ ] Pass-through + preservation rules specified.
- [ ] Preview/dry-run + token-budget behavior specified.
- [ ] Benchmark corpus + methodology versioned or fully specified.
- [ ] Telemetry correlation + quantitative test criteria specified.
- [ ] Track A conflicts + dependencies identified.
- [ ] **T8 reviews and accepts the design.**
- [ ] **Owner explicitly authorizes Sprint 9 implementation after Track A green.**

## Track A conflicts / dependencies

- `api/completions.py` attempt loop is the only viable hook — owned by
  Terminal A, **not touched**.
- Telemetry/ledger fields overlap `security/store.py` migration ledger —
  coordinated change only with Track A owners.
- No implementation, dependency, config-default, or deadline change is
  authorized by this packet.
