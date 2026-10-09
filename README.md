<div align="center">

<img src="docs/diagrams/readme-hero.svg" alt="SabiRoute — self-hosted AI gateway" width="100%" />

<br />

[![release](https://img.shields.io/badge/release-v0.1.0--dev-blue)](https://github.com/yourfavCHEFP/SabiRoute/releases)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![engine](https://img.shields.io/badge/engine-LiteLLM-6C5CE7)](https://github.com/BerriAI/litellm)
[![license](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![status](https://img.shields.io/badge/status-active--development-orange)]()

**One gateway. Multiple providers. Deterministic, health-aware routing.**

[Architecture](#architecture) · [Routing](#routing-intelligence) · [Providers](#provider-strategy) · [Quick Start](#quick-start) · [Roadmap](#engineering-roadmap) · [Contributing](#contributing) · [License](#license)

</div>

---

# SabiRoute

## The context-aware, health-aware AI gateway for developers

SabiRoute is an open-source, self-hosted AI gateway designed to give applications one OpenAI-compatible endpoint across multiple model providers.

It sits between clients such as Chatbox, IDEs, Python applications, CLI tools, ML projects, and coding agents and the model providers they use.

SabiRoute is being built to centralize:

- routing policy and request classification;
- explicit capability and health eligibility;
- deterministic candidate selection and fallback;
- latency, reliability, and usage telemetry;
- authentication, budgets, and rate limits;
- measured routing and, only when justified by evidence, future ML-assisted selection.

> **SabiRoute is not intended to be just a LiteLLM wrapper.** LiteLLM is the provider-execution layer. SabiRoute owns the higher-level policy, eligibility, routing intelligence, governance, and developer experience.

> **“Sabi”** is Nigerian Pidgin for “to know” or “to be skilled at.” The goal is a gateway that can make explainable routing decisions from real constraints and evidence.

## Why SabiRoute?

Different deployments can have different latency, reliability, capability, context, and cost characteristics. A deployment can also become unavailable or unsuitable for a particular request.

The systems problem is not only “How do I call a model?” It is:

**How should a gateway choose an eligible deployment for this request while respecting policy, reliability, and operational constraints?**

SabiRoute aims to answer that question through measured, explainable decisions—not provider marketing claims or assumptions.

## Core capabilities and direction

### Context-aware routing

The intended direction is to classify workloads and use their requirements to narrow the candidate pool before selection. Possible workload classes include:

- `INLINE_COMPLETION` — latency-sensitive;
- `CHAT` — general conversation and context handling;
- `CODING_AGENT` — coding, reasoning, and tool requirements.

These labels are routing concepts, not a claim that every classifier or capability is already production-complete.

### Health-aware fallback

A provider failure should become a controlled routing event rather than an automatic application outage. The design uses deployment health and eligibility to constrain routing and fallback. Retry behavior must distinguish retryable errors—such as eligible 429/5xx responses, timeouts, and connection failures—from errors that should not be blindly retried.

### Virtual model policies

Clients should be able to request a SabiRoute policy or virtual model rather than hard-coding every provider/model combination. Example policy names include `SabiRoute_Research`, `SabiRoute_Coding`, `SabiRoute_Fast`, and `SabiRoute_Cheap`. These names describe the intended policy interface; actual availability depends on the current configuration.

### Observability

The gateway records operational signals such as latency, success/failure, provider/deployment, token usage, error category, and routing decisions. Cost is reported only where it is actually available or defensibly estimated; missing cost data must not be presented as observed cost.

### Future ML-assisted routing

Machine learning is a later stage, not a substitute for safe deterministic routing. The intended progression is:

```text
Explicit eligibility and deterministic routing
                    ↓
          Measured routing signals
                    ↓
     Trustworthy, time-aware telemetry
                    ↓
       Dataset and evaluation checks
                    ↓
       Training only when justified
                    ↓
     Guarded inference and integration
                    ↓
       Benchmark against baseline
```

An ML selector may choose only among deployments already deemed eligible. It must never bypass authentication, authorization, budgets, capabilities, health exclusions, or fallback constraints. If ML inference is unavailable or invalid, the gateway must retain a safe deterministic path.

# Architecture

## Responsibility boundary

```text
Clients
  │
  ▼
SabiRoute API
  ├── Authentication / authorization
  ├── Policy and admission controls
  ├── Request classification
  ├── Capability eligibility
  ├── Health eligibility
  ├── Deterministic or measured selection
  ├── Fallback and telemetry
  └── Usage / governance
  │
  ▼
LiteLLM execution layer
  │
  ▼
Model providers

PostgreSQL: durable application and telemetry state
Redis: fast state/cache where configured
```

The boundary is intentional:

- **SabiRoute** owns eligibility, policy, routing, health constraints, governance, and routing telemetry.
- **LiteLLM** provides the current provider-execution abstraction.

## Request flow

The intended mature request path is:

1. Receive the client request.
2. Authenticate and authorize it.
3. Apply applicable rate-limit and budget checks.
4. Classify the request and establish required capabilities.
5. Discover candidate deployments.
6. Exclude candidates that fail capability, health, or policy requirements.
7. Select among eligible candidates using the configured routing strategy.
8. Execute through LiteLLM.
9. Apply fallback only according to the defined retry and eligibility rules.
10. Normalize the response and persist operational telemetry.

The exact controls available depend on the implementation and configuration in the current checkout. This flow describes the architecture; it is not a claim that every future feature is complete.

# Routing intelligence

SabiRoute is being developed in layers so that each later layer depends on a trustworthy earlier one.

## Layer 1 — Deterministic routing

Use configured policy/priority and safe fallback among eligible deployments. This is the operational baseline and must remain usable without ML.

## Layer 2 — Capability-aware routing

Required capabilities must be explicit. Unknown capability values must not be treated as confirmed support when a request requires that capability. Do not infer capability solely from provider or model names.

## Layer 3 — Measured deterministic scoring

For the current measured-routing baseline, the established formula is:

```text
score = 0.7 × success_rate + 0.3 × latency_normalized
```

The scoring version is `deterministic-v1`. Preserve this formula while Phase 13 work is underway; changes require a separately reviewed design and benchmark. Cold-start or insufficient/stale signals should use the configured safe fallback behavior rather than pretending evidence exists.

## Layer 4 — ML-assisted routing (future, gated)

The first intended target is **attempt-level operational success**. Every executed provider attempt must have its own observed outcome. A logical request with fallback may contain multiple attempts; do not label every attempt using only the final logical-request result.

Important constraints:

- HTTP success is an operational outcome, not answer quality.
- An unselected deployment has no observed outcome merely because it was not selected.
- API-level failures before provider execution must not be fabricated into provider-attempt failures.
- Do not infer timeout labels from generic transport errors.
- Do not invent cost values, answer-quality labels, or counterfactual outcomes.
- Observational routing data is selection-biased: outcomes are observed for selected deployments, not every eligible alternative.
- Training requires trustworthy feature/outcome pairing, temporal provenance, outcome variation, coverage, and a defensible chronological evaluation design.

The model must never override capability, health, security, budget, or policy constraints.

# Provider strategy

The configuration has included deployment definitions for providers and aggregators such as OpenAI, Google Gemini, Groq, Together AI, DeepInfra, Moonshot/Kimi, MiniMax, Cloudflare Workers AI, OpenRouter, Hugging Face, Cerebras, NVIDIA NIM, Cohere, and Pollinations AI. The actual providers and aliases available should be confirmed from the current `config/` files and live runtime.

Planned expansion may include DeepSeek, Mistral, xAI, Ollama, and others.

**A provider appearing in configuration does not prove that it is operational.** Verification should proceed through configuration validation, credential availability, provider access, health checks, real requests, streaming checks, and fallback checks as applicable. Never publish secrets or credentials in diagnostic output.

# Current repository structure

The repository includes configuration, the `src/sabiroute/` package, tests, scripts, migrations, and documentation. The exact tree may evolve as implementation changes. Key areas include:

- `src/sabiroute/config/` — configuration loading and validation;
- `src/sabiroute/routing/` — eligibility, routing, scoring, health, and fallback;
- `src/sabiroute/api/` — API request handling and administration;
- `src/sabiroute/security/` — authentication, key handling, and persistence;
- `src/sabiroute/monitoring/` — latency, errors, usage, and telemetry;
- `src/sabiroute/intelligence/` — dataset and future routing-intelligence components;
- `config/` — provider, deployment, route, and policy configuration;
- `tests/` — unit, integration, routing, persistence, and API tests;
- `scripts/` — operational checks and read-only dataset auditing;
- `docs/` — architecture, phase notes, and operational guidance.

# Technology stack

| Layer | Technology / direction |
|---|---|
| Primary language | Python |
| Environment and dependencies | `uv` |
| Provider execution | LiteLLM |
| Configuration | YAML and typed validation |
| API direction | OpenAI-compatible interface |
| Durable state | PostgreSQL |
| Fast state/cache | Redis |
| Testing | Pytest, Ruff, strict mypy where configured |
| Containers | Docker / Docker Compose |
| Private remote access | Tailscale, planned/phase-gated |
| Future monitoring | Prometheus / Grafana, planned |
| Future ML | Python ML ecosystem, only after data-readiness gates |
| Long-term core option | Go/single binary is a possible future direction, not the current implementation |

# Quick start

> **Important:** Use the project's current setup instructions and `.env.example` as the source of truth. Do not commit `.env`, API keys, provider credentials, or database secrets.

A typical local workflow is:

```bash
# From the repository root
source .venv/bin/activate

# Run the project's tests
.venv/bin/python -m pytest

# Run the read-only routing dataset audit
PYTHONPATH=src .venv/bin/python scripts/audit_routing_dataset.py
```

These commands assume the virtual environment and dependencies are already installed. Follow the repository's setup documentation for initial environment creation and service configuration. The dataset audit requires the configured database to be reachable; if the environment denies local database access, report that limitation rather than treating an old audit as current.

Do not start a second API server on a port already in use. Confirm the existing listener and its ownership before attempting a restart. Prefer a controlled, isolated verification instance when appropriate and safe.

# Current development status

SabiRoute is in active development. The project uses an evidence-based definition of completion:

```text
Code exists ≠ feature is complete

Completion requires the relevant combination of:
implementation + tests + integration + live evidence + failure validation
```

A unit-test pass is useful evidence, but it does not automatically prove live provider behavior, historical data integrity, or production readiness.

## Engineering roadmap

Statuses below distinguish implementation from verification and readiness. They are based on the latest project checkpoint available when this README was updated; they should be refreshed when new evidence is produced.

| Phase | Focus | Current status |
|---:|---|---|
| 00 | Architecture and environment | Foundation established; continue to maintain against current setup |
| 01 | Basic LiteLLM gateway | Real request and fallback behavior previously verified |
| 02 | Provider expansion | Partial; individual providers require their own operational verification |
| 03 | Model registry | Registry and aliases implemented; verify against current configuration |
| 04 | Virtual models / policies | Route configuration loading and validation implemented |
| 05 | Fallback engine | Deterministic fallback previously verified; preserve regression coverage |
| 06 | Health monitoring | Cooldown/recovery behavior previously verified; preserve regression coverage |
| 07 | Observability | Runtime metrics and error reporting foundations implemented |
| 08 | PostgreSQL | Persistence integration established; current database availability must be checked when auditing |
| 09 | Authentication and API keys | Implemented; continue validating lifecycle, authorization, and persistence |
| 10 | Budgets and rate limits | Implemented foundations; request/token/priced-cost behavior follows the documented estimator contract |
| 11 | Capability-aware deterministic routing | Implemented and previously verified; capability evidence remains explicit and must not be inferred from names |
| 12 | Measured deterministic routing | `deterministic-v1` implemented and previously live-verified; preserve its formula; broader benchmarking remains separate |
| 13.1 | ML data foundation | Dataset foundation implemented; historical integrity and coverage limitations remain |
| 13.2 | Target, labels, temporal provenance, and audit | Current-checkout bounded streaming/non-streaming verification passed; aggregate historical integrity remains invalid, so formal closure is pending |
| 13.3 | Model training and evaluation | **BLOCKED** — all six observed provider attempts were successful in the last successful audit; no outcome variation or defensible chronological split |
| 13.4 | Guarded inference | Blocked pending a valid trained artifact and defensible evaluation |
| 13.5 | ML selector integration | Blocked pending validated inference and safety tests |
| 14 | Benchmarking | Not started; compare against the unchanged deterministic baseline after ML integration is justified |
| 15 | Admin dashboard | Not started / future phase |
| 16 | Private remote access / Tailscale | Not started / future phase |
| 17 | Security hardening | Not started as a dedicated phase; security controls must still be maintained throughout development |
| 18 | Testing and regression | Dedicated phase not started; tests are required throughout all earlier phases |
| 19 | CI/CD | Not started / future phase |
| 20 | Production architecture | Not started / future phase |

### Phase 13 status: keep the gates separate

The most recent successful database audit reported:

- 7 logical requests;
- 6 provider attempts;
- 5 feature snapshots;
- 6 labeled outcomes, all successful;
- 2 attempts with verified temporal provenance;
- a historical feature/outcome mismatch and an outcome without a matching snapshot;
- no usable chronological evaluation split.

Two bounded requests through the current checkout—one non-streaming and one streaming—successfully persisted schema 1.1 records. The streaming request delivered SSE data frames and ended with `[DONE]`. This proves the tested request paths worked; it does **not** repair the older historical records or establish broad provider coverage.

Treat these as separate status dimensions:

| Dimension | Status |
|---|---|
| Data-foundation implementation | Present in the checkout |
| Bounded live verification | Passed for the tested non-streaming and streaming requests |
| Aggregate historical integrity | **Failed** — historical mismatch remains visible |
| Phase 13.2 formal closure | Pending the phase's approved integrity acceptance criteria |
| Phase 13.3 training readiness | **Blocked** — no outcome variation and no defensible chronological split in the last successful audit |
| Git commit status for the mixed Phase 09–13 work | No phase-specific commit created; changes need safe dependency-aware separation |

The last attempted database audit was blocked by `Operation not permitted` while connecting to local PostgreSQL. Therefore, the counts above are from the last successful audit, not a newly confirmed audit. Rerun the read-only audit when the intended environment can access PostgreSQL:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_routing_dataset.py
```

Do not train until a fresh audit establishes sound pairing and temporal provenance, meaningful outcome variation, adequate relevant coverage, and a defensible chronological evaluation design. Passing automated checks should lead to human review—not automatic authorization to train.

# Security philosophy

- Never commit `.env`, API keys, provider credentials, or database secrets.
- Do not log prompts, completions, credentials, or sensitive identity fields unless an explicitly reviewed requirement makes it necessary and safe.
- Keep authentication and authorization on the real request path.
- Apply budgets, rate limits, capability restrictions, health exclusions, and policy constraints before routing selection.
- Treat provider configuration as distinct from verified provider operation.
- Do not expose local services publicly without an approved deployment and security design.
- Preserve audit visibility for incomplete or inconsistent telemetry; do not rewrite history to make reports pass.

# Testing philosophy

SabiRoute must not rely only on an HTTP 200 response. Validation should cover the appropriate layers:

- **Provider:** credentials, request behavior, streaming, and supported capabilities.
- **Gateway:** authentication, policy, eligibility, routing, fallback, response handling, and telemetry persistence.
- **Data:** request/attempt/snapshot linkage, temporal provenance, schema compatibility, export privacy, and audit correctness.
- **Failure paths:** applicable 429/5xx responses, timeouts, connection failures, invalid credentials, ineligible candidates, interrupted streams, and persistence failures.
- **Client workflow:** verify the real client path when a claim depends on IDE/CLI/client compatibility.

Tests should exercise failure cases with isolated fixtures or controlled test doubles. Do not deliberately break production providers to manufacture training labels.

# Benchmarking philosophy

Future benchmarks may compare latency, time to first token, throughput, reliability, cost where observed, task performance, context handling, and streaming stability. Comparisons should be reproducible and account for eligibility and selection bias.

The goal is not to claim that one model is always best. It is to determine which eligible deployment performs best for a given request and set of constraints. ML-assisted routing must be compared against the unchanged deterministic baseline, and claims of superiority require evidence.

# Long-term product direction

The longer-term product may grow toward local-first developer tooling, IDE/CLI integrations, automatic configuration, private remote access, team governance, usage analytics, centralized budgets, and a cloud control plane. A self-contained Go core is only a possible future direction.

These are roadmap objectives, not claims about the current release. Native IDE integrations and broad automatic configuration remain future work.

# Contributing

SabiRoute is currently a solo engineering project in active development. Issues, ideas, architecture discussions, and reproducible bug reports are welcome. Before proposing a change, review the current architecture, phase acceptance criteria, and tests.

Engineering work should progress phase by phase:

1. inspect the current implementation and dependencies;
2. implement one coherent phase scope;
3. add or update tests;
4. run the relevant test suite and static checks;
5. verify integration or live behavior where required;
6. review the exact diff and protect unrelated work;
7. create a separate, meaningful commit only when that phase's acceptance criteria are met;
8. update the roadmap with evidence and proceed only when dependencies are satisfied.

Do not stage all files indiscriminately, combine unrelated phases into one commit, commit secrets or local artifacts, or mark a phase complete merely because its code compiles. Do not push commits without explicit authorization.

# License

Released under the MIT License. See [LICENSE](./LICENSE).

# Author

**Olumide “CHEF_P” Oladosu** — Machine Learning / AI engineering journey.

SabiRoute is a practical systems project at the intersection of machine learning, AI infrastructure, model routing, reliability, and developer tooling.

- GitHub: [@yourfavCHEFP](https://github.com/yourfavCHEFP)
- X: [@yourfavCHEF_P](https://x.com/yourfavCHEF_P)
- LinkedIn: [Olumide Oladosu](https://www.linkedin.com/in/olumide-oladosu-336a2b40a/)

---

*Built because developers shouldn't have to manually babysit every AI provider.*

**One endpoint. Multiple providers. Smarter, evidence-based routing.**
