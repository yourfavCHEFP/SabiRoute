# CD1–CD6 Final Report — discovery-evidence compilation

**Status:** evidence compilation only. This report does not accept a design,
authorize implementation, execute a benchmark, change a configuration default,
or upgrade any Sprint 9 gate.

**Compiled at:** branch `sec/deps-nov`, HEAD `df2acac3be6e84e1702f1f67f969cf732745d8be`.
**Source packet:** `docs/compression-discovery-packet.md` (read-only, dated 2026-10-29).
**Packet baseline:** `feat/sabiroute-routing-foundation` @ `b360ffc`; the packet records
that baseline as diverged ahead 2 / behind 3. The current compilation did not repeat
the packet's grep or import-graph search.

**Gate sentence, verbatim requirement:** Sprint 9 design acceptance, T8 review, and owner implementation authorization remain open. Nothing in this report converts the packet's proposals into an approved engine contract, a review verdict, or permission to execute R6.6/R6.7.

## 1. What the source packet actually establishes

`docs/compression-discovery-packet.md:1-16` labels itself design-review input and
states that Track B implementation stays frozen until Track A is green, T8 reviews
the design, and the owner explicitly authorizes Sprint 9. Its search covered
`src/sabiroute/**`, `config/**`, and `tests/**` using keyword and import-graph
inspection on 2026-10-29. There was no execution profiling, no dependency audit
beyond `pyproject.toml`, and no runtime change. `[VERIFIED BY INSPECTION]`

The packet's CD1 findings describe its pinned baseline, not a fresh claim about
the present tree. `artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md:16-19`
records the current-HEAD position separately: R6.1–R6.5 engine work is present,
tested, and dark; R6.6 L1/L2 replay is recorded; Sprint 9 authorization and T8
review are not re-verified. Those two observations have different dates and must
not be merged into a claim that the original capability void still exists at HEAD
or that later code work completed Sprint 9 acceptance. `[VERIFIED BY INSPECTION]`

## 2. CD1 — capability inventory at the packet baseline

| Area | Packet finding | Evidence label |
|---|---|---|
| Prompt/context compression | None; no compression, summarization, or truncation module outside token-budget quota arithmetic. Four named source placeholders were 0 bytes at the baseline. | VERIFIED BY INSPECTION |
| RTK-inspired command/output filtering | None; no RTK-Query-style cache, response filter, or tool-output dedup. `StubLiteLLMClient` returned fixed payloads. | VERIFIED BY INSPECTION |
| Caveman-style prose compression | None; no lossy simplification pass. | VERIFIED BY INSPECTION |
| History aging / summarization | Partial primitive only: SabiChat caps history at 20 messages; no summarization or aging policy beyond OD-3b 30-day session purge. | VERIFIED BY INSPECTION |
| Token estimation / context budgeting | Quota arithmetic only: `max_tokens` guards, reservation estimates, and `reserved_tokens`/`accounted_tokens` ledger fields. Estimates govern admission; they do not transform content. | VERIFIED BY INSPECTION |
| Engine interface, registry, config modes, preview, benchmark | None at the packet baseline. | VERIFIED BY INSPECTION |

The packet found no prior/duplicate/blocked compression implementation to protect.
It records two naming collisions as terminology risks, not in-tree artefacts:
"RTK Token Saver" (Redux Toolkit Query caching versus command/output compression)
and "Caveman Mode" (offline philosophy versus lossy simplification).
`docs/compression-discovery-packet.md:18-34` `[VERIFIED BY INSPECTION]`

## 3. CD2 — proposed gateway hook, not an implemented seam

The packet's proposed insertion point is after final deployment selection and
before LiteLLM invocation: ingress → auth/identity → usage admission → rate limit
→ alias/policy → classification → capability → health → Free Pool gate → budget
reserve → per-attempt `Router.choose_deployment` → proposed transformation →
LiteLLM → `finish()` reconciliation. `docs/compression-discovery-packet.md:36-42`

Constraints the design must still prove: streaming and non-streaming coverage;
context limits, tools/schemas, cache-sensitive prefixes, and structured content;
byte-identical deterministic pass-through when disabled, unsupported,
misconfigured, timed out, or errored; no change to routing eligibility,
credentials, endpoint selection, tool authorization, protected request fields, or
the 300-second deadline; and telemetry correlation without prompt-content
retention. The only transformation-adjacent seam identified was `max_tokens`
propagation in mocked contract tests, which is a limit parameter rather than a
content transform. `docs/compression-discovery-packet.md:44-59`
`[VERIFIED BY INSPECTION]`

## 4. CD3 — independent boundary, proposed only

The packet suggested a new `src/sabiroute/compression/` package with `engine.py`,
`policies.py`, `preserve.py`, and `telemetry.py`, plus `tests/test_compression_*.py`
and validated, default-off configuration additions. Later integration would touch
one call site in the `api/completions.py` attempt loop and telemetry passthrough.
It expressly puts `completions.py`, `main.py`, `gateway.py`,
`security/store.py`, and `config/validation.py` under Terminal A ownership and out
of scope for the discovery lane. The telemetry/ledger coordination point requires
Track A owner agreement before implementation.
`docs/compression-discovery-packet.md:61-78` `[VERIFIED BY INSPECTION; INFERRED]`

## 5. CD4 — engine contract and preservation requirements

The packet specifies, but does not approve or implement: engine ID/version and
supported targets; config validation; `changed`/`unchanged`/`fallback` result
statuses with reasons; token, byte, duration, and transformation-count telemetry;
deterministic pass-through and failure semantics; registry plus deterministic
pipeline composition; lossless preservation of instructions, constraints,
negation, identifiers, code, JSON, tool schemas, URLs, paths, exit codes,
warnings, errors, and actionable tail context; separately gated lossy
summarization; and byte-identical `off` behavior.
`docs/compression-discovery-packet.md:80-91` `[VERIFIED BY INSPECTION]`

## 6. CD5 — benchmark corpus and evaluation requirements

The packet specifies a versioned synthetic or approved-redacted corpus covering
Git/test/build outputs, install/audit logs, stack traces, shell output, Docker
and infrastructure output, prose, source, JSON, and tool results; adversarial
cases for whitespace, negation, numeric thresholds, paths, identifiers,
warnings, exit codes, truncated logs, near-duplicates, and conflicting
instructions; gold preservation assertions and expected task/tool outcomes; a
token-estimation baseline and latency methodology; individual engines before
stacked pipelines; and task success, tool-call correctness, quality degradation,
latency, provider-reported usage, estimated savings, and net cost per successful
task. `docs/compression-discovery-packet.md:93-106` `[VERIFIED BY INSPECTION]`

No corpus was versioned, no baseline was executed, and no result is reported here.

## 7. CD6 — telemetry integration contract

The packet requires correlation by `request_id`, `decision_id`, `attempt_id`, and
final outcome, with engine/pipeline version and policy mode; input/output token
estimates, actual usage where available, duration, bytes, transformation counts,
changed status, fallback/error reason, and correlation status; no prompt contents
in routine telemetry; and correct accounting across retries, fallback, failures,
and partial streams without double-counting. Estimated, provider-reported, and
net savings must remain distinguishable. Shared telemetry/ledger changes require
Track A owner coordination. `docs/compression-discovery-packet.md:108-119`
`[VERIFIED BY INSPECTION]`

## 8. Sprint 9 checklist position

The packet records every acceptance item as open at its baseline, including the
T8 review and owner authorization after Track A is green.
`docs/compression-discovery-packet.md:121-133` `[VERIFIED BY INSPECTION]`

This report supplies the missing report artifact only. It does **not**:

- approve the engine contract or registry;
- record a T8 verdict;
- grant owner implementation authorization;
- verify that Track A is green for Sprint 9;
- execute R6.6 mutations, instantiate the registration ledger, or authorize
  R6.7 rollout; or
- claim that the packet's proposed file boundary is accepted.

`artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md:16` and
`artifacts/sprint-phoenix-2/OPEN-POINTS-DISPOSITION.md:29-38` keep those gates
open at the current evidence line. `[VERIFIED BY INSPECTION]`

## 9. Position

`CD1–CD6: packet compiled into a report artefact · design review input only · Sprint 9 design acceptance OPEN · T8 review OPEN · owner implementation authorization OPEN`
