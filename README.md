<div align="center">

<img src="docs/diagrams/readme-hero.svg" alt="SabiRoute — self-hosted AI gateway" width="100%" />

<br/>

[![Typing SVG](https://readme-typing-svg.demolab.com/?font=Fira+Code&weight=600&size=20&pause=1200&color=8B5CF6&center=true&vCenter=true&width=900&lines=One+gateway.+Multiple+providers.;Context-aware+%2B+health-aware+routing;Deterministic+fallback+before+ML+intelligence;LiteLLM+execution.+SabiRoute+control.;Self-hosted+%C2%B7+OpenAI-compatible+%C2%B7+MIT)](https://git.io/typing-svg)

[![release](https://img.shields.io/badge/release-v0.1.0--dev-blue)](https://github.com/yourfavCHEFP/SabiRoute/releases)
[![made with](https://img.shields.io/badge/made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![engine](https://img.shields.io/badge/engine-LiteLLM-6C5CE7)](https://github.com/BerriAI/litellm)
[![license](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
![status](https://img.shields.io/badge/status-active--development-orange)

**One gateway. Multiple providers. Deterministic, health-aware routing.**

[Architecture](#-architecture) · [Routing](#-routing-intelligence) · [Providers](#-provider-strategy) · [Roadmap](#-engineering-roadmap) · [Phase 13](#-ml-readiness-status-phase-13) · [Free Pool](#-free-pool-planned-workstream) · [Getting started](#-getting-started) · [Testing](#-testing-and-validation) · [Contributing](#-contributing) · [License](#-license)

</div>

---

# SabiRoute

### The context-aware, health-aware AI gateway for developers

SabiRoute is an open-source, self-hosted, local-first AI gateway that gives applications **one OpenAI-compatible endpoint across multiple model providers**. It sits between clients — Chatbox, IDEs, Python applications, CLI tools, ML projects, and coding agents — and the providers they call, and decides centrally how each request should be routed.

SabiRoute owns the decision layer:

- routing policy and request classification;
- explicit capability and health eligibility;
- deterministic candidate selection and fallback;
- authentication, budgets, and rate limits on the real request path;
- latency, reliability, and usage telemetry;
- measured routing — and, only when justified by evidence, future ML-assisted selection.

> **SabiRoute is not another LiteLLM wrapper.**
>
> LiteLLM is the current provider-execution engine.
> **SabiRoute is the control, routing, intelligence, and governance layer built around it.**

> **"Sabi"** — Nigerian Pidgin for "to know" or "to be skilled at."
>
> A gateway that knows which model should handle a request, so the developer does not have to.

SabiRoute is in active development (v0.1.0-dev, alpha). The deterministic routing foundation is working and progressively verified; ML-assisted routing is a gated future layer, not a current feature. Status below is reported from real evidence, phase by phase.

## Contents

- [Why SabiRoute?](#-why-sabiroute)
- [Core capabilities and direction](#-core-capabilities-and-direction)
- [Architecture](#-architecture)
- [Routing intelligence](#-routing-intelligence)
- [Provider strategy](#-provider-strategy)
- [Engineering roadmap](#-engineering-roadmap)
- [ML readiness status (Phase 13)](#-ml-readiness-status-phase-13)
- [Getting started](#-getting-started)
- [Testing and validation](#-testing-and-validation)
- [What makes this an ML systems project?](#-what-makes-this-an-ml-systems-project)
- [Free Pool (planned workstream)](#-free-pool-planned-workstream)
- [Known limitations](#-known-limitations)
- [Contributing](#-contributing)
- [Long-term direction](#-long-term-direction)
- [License](#-license)
- [Author](#-author)

---

## 🎯 Why SabiRoute?

Modern AI applications depend on multiple model providers. One model is faster, another cheaper, another better at reasoning or coding or long context — and any of them can simply be unavailable.

The problem is not only:

> "How do I call an LLM?"

The more interesting systems problem is:

> **"How do I decide which available deployment should handle this particular request, while remaining reliable when providers fail?"**

SabiRoute is being built around that question. The goal is a system where applications talk to one stable endpoint while measured, explainable routing decisions happen underneath — based on real constraints and evidence, not provider marketing claims.

---

## ✨ Core capabilities and direction

### 🧠 Context-aware routing

Workload classes narrow the candidate pool before selection:

| Request type | Primary bias |
|---|---|
| `inline_completion` | Latency |
| `chat` | Quality and context |
| `coding_agent` | Reasoning and tool capability |

Classes come from explicit request metadata (`sabi_route_request_type`) and route requirements — prompt wording is never treated as evidence of a coding or reasoning task. Deployment-specific capability metadata drives filtering; see [docs/capabilities.md](docs/capabilities.md) for the classification rules and the current evidence matrix.

### 🛡️ Health-aware fallback

A provider failure becomes a controlled routing event, not an application outage. Unhealthy deployments are excluded from the eligible pool, deterministic fallback tries the next eligible candidate, and cooldown lets failed deployments recover. Retryable failures (eligible 429/5xx responses, timeouts, connection failures) are distinguished from errors that must not be blindly retried. Fallback and cooldown recovery are verified (Phases 05–06).

### 🧩 Virtual model policies

Clients request a virtual route instead of hard-coding provider/model pairs — `ultimate`, `coding`, `research`, `reasoning`, `fast`, or `cheap`. (`SabiRoute_Research`-style names resolve to the same policies, case-insensitively.) The underlying deployments can change without touching every client configuration. Route files are validated at startup; unknown aliases or invalid candidates fail loudly instead of silently routing everywhere. See [docs/routing.md](docs/routing.md).

### 🔐 Governance on the request path

Authentication, budgets, and rate limits run on the real request path, not in side configuration (Phases 09–10, verified):

- client API keys with create / rotate / revoke lifecycle, stored as SHA-256 digests only;
- a separate admin bootstrap credential for `/admin/*`;
- per-key token-bucket rate limits (atomic in Redis, fail-closed when Redis is unsafe);
- per-key daily and monthly token/cost budgets with transactional reservation.

Details: [docs/security.md](docs/security.md), [docs/limits-and-usage.md](docs/limits-and-usage.md).

### 📊 Observability

The gateway records latency, success/failure, provider/deployment, token usage, error category, and routing decisions with score breakdowns. Estimated and provider-reported tokens are kept separate; cost is recorded only when calculable from configured pricing — missing cost data is never presented as observed cost.

### 🤖 Future ML-assisted routing

Machine learning is a later, gated stage — never a substitute for safe deterministic routing:

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
       Benchmark against the baseline
```

An ML selector may only choose among deployments already deemed eligible. It must never bypass authentication, budgets, capabilities, health exclusions, or policy constraints — and if it fails, the deterministic path remains.

---

## 🏗️ Architecture

### Responsibility boundary

```text
                    Clients
        (Chatbox · IDEs · CLIs · apps · agents)
                       │
                       ▼
              ┌─────────────────┐
              │   SabiRoute API │◄──────────── PostgreSQL: keys, usage,
              ├─────────────────┤◄────────────   budgets, routing decisions
              │ Authentication  │
              │ Budgets & rate  │◄──────────── Redis: rate-limit buckets,
              │ Classification  │◄────────────   fast state
              │ Capability and  │
              │   health filters│
              │ Routing score   │
              │ Fallback        │
              └────────┬────────┘
                       ▼
             LiteLLM execution layer
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Gemini         Groq        OpenRouter · …
```

The boundary is intentional:

- **SabiRoute** owns eligibility, policy, routing, health constraints, governance, and routing telemetry.
- **LiteLLM** owns provider execution, provider adapters, and streaming mechanics.

SabiRoute decides which deployment should be attempted; LiteLLM executes the provider request.

### Request flow

The request path implemented today:

1. Receive the client request.
2. Authenticate and authorize it (client key / admin key boundary).
3. Apply rate-limit and budget admission checks.
4. Classify the request and establish required capabilities.
5. Discover candidate deployments from the route policy.
6. Exclude candidates that fail capability, health, or policy requirements.
7. Select among eligible candidates (configured priority or measured scoring).
8. Execute through LiteLLM.
9. On retryable failure, fall back per the retry and eligibility rules.
10. Normalize the response and persist operational telemetry.

Every stage above exists and has been exercised by tests and live requests; the maturity of each varies by phase (see the [roadmap](#-engineering-roadmap)). ML scoring is deliberately absent from this flow — it is a future, gated addition.

---

## 🧠 Routing intelligence

Routing intelligence is built in layers, each resting on a trustworthy one below it.

**Layer 1 — Deterministic routing.** Configured policy and priority, healthy candidates, bounded fallback. Verified and the operational baseline.

**Layer 2 — Capability-aware routing.** Required capabilities are explicit and filter candidates before selection. Unknown capability values never count as confirmed support, and capabilities are never inferred from provider or model names. Implemented with tests; deployment-specific evidence remains incomplete for most deployments (Phase 11).

**Layer 3 — Measured deterministic scoring.** For the current measured-routing baseline, the established formula is:

```text
score = 0.7 * success_rate + 0.3 * latency_normalized
```

The scoring version is `deterministic-v1` (weights and thresholds live in `config/config.yaml`). This formula is a preserved baseline; changing it requires a separately reviewed design and benchmark. Signals are process-local (operational success rate and mean observed latency); on cold start, missing, or stale signals the scorer falls back to configured route order rather than inventing evidence. Full semantics: [docs/routing-scoring.md](docs/routing-scoring.md).

**Layer 4 — ML-assisted routing (future, gated).** The first target is attempt-level operational success. Every executed provider attempt must have its own observed outcome — a logical request that fell back contains several attempts, and they are not all labeled by the final result. Hard constraints on the data:

- HTTP success is an operational outcome, not answer quality.
- An unselected deployment has no observed outcome; no counterfactual labels are invented.
- API-level failures before provider execution are not fabricated into provider-attempt failures.
- Timeout labels are not inferred from generic transport errors.
- Cost values, quality labels, and counterfactual outcomes are never invented.
- Observational data is selection-biased; training requires trustworthy pairing, temporal provenance, outcome variation, coverage, and a defensible chronological evaluation design.

The model must never override capability, health, security, budget, or policy constraints.

---

## 🌐 Provider strategy

`config/config.yaml` is the runtime deployment catalog for both SabiRoute and LiteLLM. Fourteen aliases are configured across providers such as OpenAI, Google Gemini, Groq, Together AI, DeepInfra, Moonshot/Kimi, MiniMax, Cloudflare Workers AI, OpenRouter, Hugging Face, Cerebras, NVIDIA NIM, Cohere, and Pollinations AI. The full alias → model → credential table lives in [docs/providers.md](docs/providers.md).

Runtime evidence is deployment-specific and deliberately narrow:

| Deployment | Verified capabilities | Evidence |
|---|---|---|
| `sabiroute-gemini` | `chat` | Non-empty text completion through SabiRoute → LiteLLM |
| `sabiroute-groq` | `chat`, `streaming` | Non-empty completion and incremental SSE chunks end to end |
| `sabiroute-openrouter` | `chat` | Non-empty text completion through the configured OpenRouter deployment |

All other configured deployments remain **configured but unverified** (`sabiroute-openai` has a prior request that returned no credits). Capability matrix: [docs/capabilities.md](docs/capabilities.md).

> **Configured ≠ operational.** A provider appearing in configuration proves only that the alias and credential reference exist. A deployment becomes operational after: configuration → credentials → provider access → health test → real request → streaming test → fallback test.

Planned expansion may include DeepSeek, Mistral, xAI, and Ollama. Note that the fragments under `config/models/` are **not** loaded by the current runtime — `config/config.yaml` is the single catalog. Never put credential values in YAML, reports, or terminal output.

---

## 🛣️ Engineering roadmap

> **Code exists ≠ feature works.** A phase is complete only with implementation + tests + integration + real execution + failure validation. A unit-test pass is evidence — but it does not prove live provider behavior or production readiness.

**Legend:** **Complete** — acceptance criteria verified · **Implemented** — code and tests exist, verification incomplete · **In progress** — active work, scope remains · **Blocked** — waiting on a data or dependency gate · **Planned** — not started

| Phase | Focus | Status | Evidence / notes |
|---:|---|---|---|
| 00 | Architecture and environment | Complete | Typed configuration, validation, and local environment in place |
| 01 | Basic LiteLLM gateway | Complete | Real request and fallback path previously verified (`sabiroute-gemini`) |
| 02 | Provider expansion | In progress | Gemini, Groq, and OpenRouter have runtime evidence; remaining deployments unverified |
| 03 | Model registry | Complete | Registry and aliases in place; `config/config.yaml` is the runtime catalog |
| 04 | Virtual models / policies | Complete | Six route policies loaded and validated at startup |
| 05 | Fallback engine | Complete | Deterministic fallback verified |
| 06 | Health monitoring | Complete | Cooldown and recovery behavior verified |
| 07 | Observability | Complete | Runtime metrics, latency, and error reporting on admin endpoints |
| 08 | PostgreSQL | Complete | API-key lifecycle verified against PostgreSQL |
| 09 | Authentication and API keys | Complete | Client/admin boundary and key lifecycle verified |
| 10 | Budgets and rate limits | Complete | Request, token, and priced-cost gates verified (text-only estimator contract) |
| 11 | Capability-aware deterministic routing | Implemented | Routing and tests in place; capability evidence missing for most deployments |
| 12 | Measured deterministic scoring | Implemented | `deterministic-v1` live on measured routes; benchmark evidence is synthetic only |
| 13 | ML-assisted routing | In progress | Data foundation and live path verified; training blocked — see [below](#-ml-readiness-status-phase-13) |
| 14 | Benchmarking | Planned | Compare against the unchanged deterministic baseline |
| 15 | Admin dashboard | Planned | — |
| 16 | Private remote access / Tailscale | Planned | — |
| 17 | Security hardening | Planned | Baseline controls maintained throughout earlier phases |
| 18 | Testing and regression | Planned | Tests are required throughout earlier phases |
| 19 | CI/CD | Planned | — |
| 20 | Production architecture | Planned | — |

Phase 11 note: unknown capabilities are never treated as verified support; only the deployment-specific evidence in [docs/capabilities.md](docs/capabilities.md) is enabled. Phase 12 note: `scripts/benchmark_routing.py` runs a fixed synthetic comparison of `priority` vs `measured` — it is a methodology check, **not** proof of warm live-routing performance against real providers.

---

## 📊 ML readiness status (Phase 13)

Five status dimensions, kept deliberately separate:

| Dimension | Status |
|---|---|
| ML data-foundation implementation | Implemented — schema `1.1` feature snapshots and a read-only audit tool in the working tree (not yet isolated in a phase-scoped commit) |
| Live request-path verification | Passed for two bounded requests — one non-streaming (`research` policy → OpenRouter) and one streaming (Groq, SSE frames terminated with `[DONE]`); schema `1.1` records persisted |
| Aggregate dataset integrity | **Failed** — one feature/outcome count mismatch and one outcome without a feature snapshot remain visible by design |
| Training readiness (13.3) | **Blocked** — no outcome variation and no defensible chronological split |
| Commit status | Foundation, capabilities, scoring, registry, route-loading, and standalone security-primitive commits are in (through `df0bc8a`); request-path wiring, intelligence work, and recent provider-harness changes remain uncommitted in the working tree |

The latest read-only database audit **succeeded** and reported:

- 7 logical requests · 6 provider attempts · 5 feature snapshots · 6 labeled outcomes;
- all six provider attempts successful → **no outcome variation**;
- 2 attempts with verified temporal provenance; 4 with unknown or unavailable provenance;
- 1 feature/outcome count mismatch; 1 outcome without a feature snapshot;
- **no usable chronological evaluation split** (at least one attempt lacks a decision timestamp).

An earlier audit attempt was blocked by the execution environment (`Operation not permitted`); that was an environment access limitation, **not** a PostgreSQL outage. The historical unmatched observation has a successful provider outcome but no feature snapshot or attempt timestamps — it is left unrepaired on purpose. Do not fabricate timestamps or reconstructed features for it; a future training export must exclude it unless an authoritative original snapshot is recovered.

Phase status: **13.1** data foundation — implemented · **13.2** target/labels/provenance/audit — in progress (live sub-gate passed, aggregate closure pending) · **13.3** training and evaluation — **blocked** · **13.4** guarded inference — blocked pending a valid trained artifact · **13.5** ML selector integration — blocked pending validated inference. **No model has been trained or deployed.**

Training stays locked until a fresh audit establishes sound feature/outcome pairing and temporal provenance, meaningful outcome variation, adequate coverage, and a leakage-safe chronological evaluation design — and even then, automated checks lead to human review, not automatic authorization to train. Observations should come from normal authorized traffic; never manufacture failures or randomize selection to grow the dataset. Details: [docs/phase13-data-foundation.md](docs/phase13-data-foundation.md).

---

## 🚀 Getting started

> **Local development setup.** Use `.env.example` as the environment template and keep `.env` local — never commit API keys, provider credentials, or database secrets.

**Prerequisites:** Python 3.11–3.13, [uv](https://docs.astral.sh/uv/), and Docker (for the Compose stack).

```bash
# 1. Install dependencies into .venv
uv sync

# 2. Configure the environment (fill in values locally)
cp .env.example .env

# 3. Start LiteLLM, PostgreSQL, and Redis
docker compose up -d

# 4. Run the gateway on the host (default 127.0.0.1:8000)
./.venv/bin/sabiroute
```

Key environment variables (names only — see `.env.example` for the full list): `DATABASE_URL`, `SABIROUTE_ADMIN_KEY`, `LITELLM_MASTER_KEY`, `LITELLM_SALT_KEY`, `LITELLM_PORT`, `REDIS_URL`, plus per-provider credentials (`GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, …). The gateway honors `SABIROUTE_HOST` and `SABIROUTE_API_PORT`, and `SABIROUTE_ROUTES_PATH` for a custom route directory.

The supported topology is **host-run SabiRoute** beside the Compose stack (LiteLLM + PostgreSQL + Redis). There is no SabiRoute container yet; when running on the host, point `DATABASE_URL` at `127.0.0.1` with the published port — the Compose service names only resolve inside the Compose network. Full topology notes: [docs/deployment.md](docs/deployment.md).

### API usage

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /v1/chat/completions` | client key | OpenAI-compatible chat completions (streaming supported) |
| `GET /health`, `GET /health/live` | public | Liveness |
| `POST /admin/api-keys` (+ rotate / revoke) | admin key | Client key lifecycle |
| `PUT/GET/DELETE /admin/api-keys/{id}/rate-limit` | admin key | Per-key request rate and burst |
| `PUT/GET/DELETE /admin/api-keys/{id}/budget` | admin key | Daily/monthly token and cost budgets |
| `GET /admin/api-keys/{id}/usage` | admin key | Per-key usage |
| `GET /admin/metrics`, `/admin/latency`, `/admin/errors`, `/admin/usage` | admin key | Telemetry |

```bash
# Create a client key (admin key required; the plaintext key is returned once)
curl -s http://127.0.0.1:8000/admin/api-keys \
  -H "Authorization: Bearer $SABIROUTE_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"project-a","name":"local-dev"}'
```

```bash
# OpenAI-compatible chat completion through a virtual policy
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer $SABIROUTE_CLIENT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "research",
    "messages": [{"role": "user", "content": "Summarize the trade-offs of HTTP/2 multiplexing."}],
    "max_tokens": 256
  }'
```

`model` accepts a deployment alias (for example `sabiroute-gemini`) or a virtual route name (`ultimate`, `coding`, `research`, `reasoning`, `fast`, `cheap`). Add `"stream": true` for SSE streaming — streaming requires a deployment with verified `streaming` support.

---

## 🧪 Testing and validation

```bash
# Unit and API tests (local development)
./.venv/bin/python -m pytest

# Lint and type checks (configured in pyproject.toml)
./.venv/bin/ruff check src tests scripts config
./.venv/bin/mypy src
```

The Ruff command is scoped to the maintained tree on purpose: `pyproject.toml` defines no excludes, so a whole-tree `ruff check .` also scans untracked local tool artifacts (for example vendored skill scripts under `.claude/`), which currently report hundreds of findings unrelated to this project. `ruff check src tests scripts config` is the reliable gate — it passes on the maintained code, and nothing in that scope is suppressed.

Operational and verification tooling:

| Script | Purpose | Notes |
|---|---|---|
| `scripts/audit_routing_dataset.py` | Read-only routing dataset audit; `--export` is readiness-gated candidate JSON and `--diagnostic-export` is diagnostic-only JSON | Requires `DATABASE_URL`; never trains or writes to the database |
| `scripts/verify_postgres.py` | Temporary-key PostgreSQL lifecycle check, self-cleaning | Prints database/role names, never passwords |
| `scripts/verify_phase10.py` | Exercises request accounting and rate limits against local services | Local services only |
| `scripts/benchmark_routing.py` | Synthetic `priority` vs `measured` comparison | No provider calls — methodology check, not provider evidence |
| `scripts/test_providers.py` | Live provider verification | Makes **real** provider requests; writes `reports/provider_verification.json` — review and sanitize before sharing |

An HTTP 200 is not acceptance. Validation covers the layers that actually fail:

- **Provider:** credentials, request behavior, streaming, supported capabilities.
- **Gateway:** authentication, policy, eligibility, routing, fallback, response handling, telemetry persistence.
- **Data:** request/attempt/snapshot linkage, temporal provenance, schema compatibility, audit correctness.
- **Failure paths:** 429/5xx, timeouts, connection failures, invalid credentials, ineligible candidates, interrupted streams, persistence failures.
- **Client workflow:** verify the real client path whenever a claim depends on IDE/CLI/client compatibility.

Exercise failure cases with isolated fixtures or controlled test doubles — never deliberately break production providers to manufacture training labels.

---

## 🔬 What makes this an ML systems project?

SabiRoute is built so the machine-learning component has a real systems problem to solve. The eventual dataset observes request shape (type, prompt/context size, required capabilities), execution (provider, deployment, latency, TTFT, tokens, cost when calculable), and outcome (success, failure type, retries):

```text
        ROUTING DATA
             │
             ▼
      Feature Engineering
             │
             ▼
       Model Scoring
             │
             ▼
  ML Router Training → Offline Evaluation
             │
             ▼
   Shadow Deployment → Controlled Online Routing
```

That progression — and the honesty about selection bias, missing outcomes, and provenance along the way — is what makes this a genuine ML systems project rather than an API wrapper. The benchmarking objective follows the same spirit: not *"Model X is always best,"* but **"which eligible deployment is best for this request, under these constraints?"** ML-assisted routing must beat the unchanged deterministic baseline on evidence before it earns a place in the request path.

---

## ⚠️ Known limitations

- **Aggregate dataset integrity is invalid:** one historical feature/outcome count mismatch and one outcome without a feature snapshot remain, deliberately unrepaired.
- **Training is blocked:** no outcome variation (all attempts successful), incomplete temporal provenance, and no usable chronological split.
- **Capability evidence is narrow:** only `sabiroute-gemini`, `sabiroute-groq`, and `sabiroute-openrouter` have runtime evidence; most deployments' capability metadata is `unknown`.
- **Phase 12 evidence is synthetic:** warm live-routing performance under real provider telemetry is not yet established.
- **Scoring telemetry is process-local:** reliability and latency signals reset on restart; the request path does not read history from the database.
- **Token estimation is text-only:** multimodal token estimation stays null; cost appears only when calculable from configured pricing.
- **No versioned migration framework yet:** the API-key table is created idempotently at startup; introduce migrations before non-additive schema changes.
- **Host-run topology only:** the Compose stack has no SabiRoute application container yet.
- **Phase-scoped commits still pending for recent work:** foundation through security-primitives commits are in; the remaining request-path wiring, telemetry, intelligence, and provider-harness changes still need dependency-aware separation before reviewable phase-scoped commits.
- Some root files (`Dockerfile`, `Makefile`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`) are placeholders awaiting their phases.

---

## 🤝 Contributing

SabiRoute is currently a solo engineering project in active development. Ideas, issues, architecture discussions, and reproducible bug reports are welcome. As the gateway and intelligence layers mature, the project can grow toward broader community contributions.

Engineering work progresses phase by phase:

1. inspect the current implementation and dependencies;
2. implement one coherent phase scope;
3. add or update tests and run the relevant suites;
4. verify integration or live behavior where required;
5. review the exact diff and protect unrelated work;
6. commit only when that phase's acceptance criteria are met — never stage everything indiscriminately or merge unrelated phases into one commit.

Do not commit secrets or local artifacts, mark a phase complete because it compiles, or push without explicit authorization.

---

## 🆓 Free Pool (planned workstream)

**Status: approved product direction — not yet implemented.** No catalogue, registry-mapping, or shared-inference code exists in the tree yet; what follows is the agreed design, not a feature description.

### What is Free Pool?

Two goals, in order:

A. **Free Model Discovery** — a trustworthy catalogue where developers discover models, free-tier conditions, capabilities, access requirements, and restrictions, each claim source-linked and verification-stamped.
B. **Shared Free Inference** — a possible future SabiRoute service through which users obtain inference without supplying their own provider API keys.

Discovery comes first; shared inference is a later, separately gated direction. Both remain subordinate to SabiRoute's original purpose: Free Pool expands the gateway's value without becoming a separate platform with its own routing engine.

### One platform, three experiences, one routing foundation

The long-term product is one platform with three top-level experiences over a single shared routing foundation:

1. **SabiRoute Gateway** — the core local-first gateway, policy engine, and routing system (this repository's focus today).
2. **SabiRoute Free Pool** — the evidence-backed model discovery and access-information layer.
3. **SabiRoute Web Platform** — the public website, documentation, catalogue interface, developer onboarding, and eventual playground/chat experiences.

The dashboard, playground, and chat are capabilities *of the Web Platform*, not separate routing backends. All request execution — local or hosted, BYOK or platform-managed — stays governed by the same SabiRoute routing, eligibility, security, and telemetry rules.

### Catalogue, registry, router: three distinct concepts

- **Free Pool catalogue** — discovered models, provider information, published allowances, access arrangements, restrictions, evidence, and verification status. Informational.
- **Runtime deployment registry** — the deployments actually configured for a SabiRoute instance to attempt (`config/config.yaml` today).
- **Routing and policy engine** — decides which configured deployments are eligible for a request and selects among them.

These may share validated data contracts, but they are not one undifferentiated source of truth. **A model listed in Free Pool is not thereby configured, accessible, healthy, or usable** through any particular SabiRoute instance.

### Free access, stated accurately

Free-tier claims differ by access arrangement:

- **BYOK** — the user supplies their own provider credentials; that provider's terms apply to that user.
- **Platform-managed access** — SabiRoute uses credentials it controls (future; requires explicit provider-terms acceptance, server-side credential handling, and quota/budget enforcement).
- **Local inference** — execution depends on the user's own runtime and hardware.
- Anything else only when explicitly identified and supported.

Quotas, restrictions, account eligibility, geography, and terms vary by arrangement — and a provider's free tier must never be assumed to permit shared platform usage. One-time promotional credits are not recurring capacity; request-rate limits do not imply monthly token allowances; identifiers sharing a quota pool are counted once. Only five distinct things may be claimed, each on its own evidence: the **published allowance**, the **access actually configured** under a specific arrangement, the **estimated aggregate capacity** (assumptions explicit), the **observed consumption**, and the **current runtime health**. Provider credentials are never exposed to the browser.

### Current versus future

**Now (discovery track):** source-linked provider/model information, published free-tier conditions, explicit capability evidence, access-mode distinctions, quota/restriction metadata, verification status, and mapping between catalogue entries and configured deployments — all without requiring ML.

**Later (shared inference track, gated):** a hosted inference service with explicit acceptance criteria covering provider terms and permissions, server-side credential handling, authentication, quota and budget enforcement, abuse controls, privacy and data retention, cost exposure, observability, incident handling, and operational capacity. Shared hosted inference is ambition, not an implemented feature.

### Fit with the existing roadmap

Free Pool is a cross-cutting workstream, not a roadmap replacement — phases keep their numbers, names, and gates:

- Phases 09–10 governance (auth, rate limits, budgets) underpins any future shared access.
- Phase 11 capability filtering constrains which catalogue-mapped deployments are ever eligible.
- Phase 12 `deterministic-v1` stays the measured baseline; Phase 14 benchmarks against it unchanged.
- Phase 13 gates stand: discovery needs no training data, and any future ML ranks only already-eligible candidates.
- Phase 15 dashboard work may surface verified catalogue, health, routing, and usage information.
- Phase 20 production architecture carries the operational, financial, and security controls shared inference would require.

---

## 🌍 Long-term direction

The longer-term product may grow toward local-first developer tooling, IDE and coding-agent integrations, automatic client configuration (for example, a future `sabiroute setup --all`), private remote access, team governance, usage analytics, centralized budgets, and a cloud control plane. A self-contained Go core remains a possible future direction, not a current plan of record.

These are roadmap objectives, not claims about the current release. The order matters: a reliable routing foundation first, trustworthy telemetry second, defensible ML only after the data earns it.

---

## 📄 License

Released under the [MIT License](./LICENSE).

Use it, fork it, improve it, route through it.

## 👤 Author

**Olumide "CHEF_P" Oladosu** — machine learning / AI engineering journey.

SabiRoute is a practical systems project at the intersection of machine learning, AI infrastructure, model routing, reliability, and developer tooling.

- [GitHub — @yourfavCHEFP](https://github.com/yourfavCHEFP)
- [X — @yourfavCHEF_P](https://x.com/yourfavCHEF_P)
- [LinkedIn — Olumide Oladosu](https://www.linkedin.com/in/olumide-oladosu-336a2b40a/)
- [SabiRoute repository](https://github.com/yourfavCHEFP/SabiRoute)

---

*Built because developers shouldn't have to manually babysit every AI provider.*

**One endpoint. Multiple providers. Smarter, evidence-based routing.**

*Built incrementally. Measured carefully. Improved with evidence.*
