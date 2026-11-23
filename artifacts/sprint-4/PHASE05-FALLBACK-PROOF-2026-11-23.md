# Sprint 4 — Phase 05 Fallback Failure-Injection Proof — 2026-11-23

## ACTION COMPLETED

Files created (2, VERIFIED BY RUNTIME):
- `scripts/phase05_fallback_injection.py` — a repeatable failure-injection harness with two
  modes: direct (SabiRoute → stub upstream) and `--via-proxy` (SabiRoute → real LiteLLM Proxy
  → stub upstream).
- `artifacts/sprint-4/PHASE05-FALLBACK-PROOF-2026-11-23.md` (this file)

Files modified: **none**. No source, configuration, dependency, schema or test file changed.

Commands executed (VERIFIED BY RUNTIME):
- `./.venv/bin/python scripts/phase05_fallback_injection.py` → **10/10**, exit 0
- `./.venv/bin/python scripts/phase05_fallback_injection.py --via-proxy` → **7/7**, exit 0
- `./.venv/bin/python -m ruff check scripts/phase05_fallback_injection.py` → All checks passed
- `./.venv/bin/python -m pytest -q tests/test_fallback_injection.py tests/test_health.py tests/test_router.py` → 22 passed

## WHY

Phase 05 was recorded as "Implemented — unit-tested; no live failure-injection evidence". The
existing suite says so in its own docstring: "Fallback failure-injection tests using in-process
mocks (no live providers)." Its `StubLiteLLMClient` raises a hand-built
`LiteLLMClientError(status_code=...)`, proving the **branching logic** but not the **seam**
between that logic and a real HTTP exchange — nor the translation LiteLLM Proxy performs
before SabiRoute ever sees a status.

`api/completions.py:1662` decides retryability from `exc.status_code`. That attribute exists
only because `LiteLLMClient` populated it from a real `httpx` response. If that mapping were
wrong, every mocked test would still pass while live fallback silently stopped working.

## RESULT

### The two chains exercised (VERIFIED BY RUNTIME)

```
direct:   FastAPI app → real LiteLLMClient (httpx) → stub upstream (loopback socket)
proxy:    FastAPI app → real LiteLLMClient (httpx) → real LiteLLM Proxy → stub upstream
```

- The stub is an `http.server` on `127.0.0.1:0`; every scenario crosses a real TCP connection
  and returns through the real `LiteLLMClientError` mapping (`providers/litellm_client.py:119`).
- The stub selects a fault by the `model` field, which SabiRoute sets to the deployment alias
  it chose — so the recorded call sequence is direct proof of the routing decisions taken.
- A fresh `GatewayState` per scenario, and in proxy mode a **fresh proxy process per
  scenario** (see finding 2).
- No provider credential, no egress, no database, no Redis. The only keys present authenticate
  a locally-spawned proxy and a stub; neither reaches a provider.

### Matrix A — direct chain (VERIFIED BY RUNTIME — 10/10)

| # | Scenario | Result | Aliases in order | Claim proven |
|---|---|---|---|---|
| A | 500 on first candidate | 200 | `primary, secondary` | `>=500` retryable; fallback succeeds |
| B | 429 on first candidate | 200 | `primary, secondary` | 429 in `RETRYABLE_STATUS_CODES` |
| C | 401 on first candidate | 200 | `primary, secondary` | 401/403 are deployment-credential faults |
| D | 404 on first candidate | **502** | `primary` | **No fallback** on 4xx |
| E | 400 on first candidate | **502** | `primary` | **No fallback** on 4xx |
| F | Both candidates fail | **502** | `primary, secondary` | Exhaustion is classified, not a crash |
| G | Streaming (SSE) 500 | 200 | `primary, secondary` | SSE error caught before hand-off |
| H | Upstream delay > client timeout | 200 | `primary, secondary` | Timeout has no status and is retryable |
| I | 3 consecutive failures each | **503** | unchanged on 4th | Cooldown refuses with **zero** new upstream calls |
| J | Cooldown deadline passes | **502**, calls 3→4 | one fresh attempt | Half-open recovery, fresh failure budget |

Scenario I's trip responses were `[502, 502, 502]`; the fourth was `503` with the upstream-call
list byte-identical to before it. Scenario J's post-recovery health read
`healthy: true, consecutive_failures: 1` — a fresh budget, not `4`. D and E both returned
`type: sabiroute_upstream_error`.

### Matrix B — through the real LiteLLM Proxy (VERIFIED BY RUNTIME — 7/7)

| # | Scenario | Result | Aliases in order | Raw upstream calls |
|---|---|---|---|---|
| A | 500 | 200 | `primary, secondary` | `primary×3, secondary` |
| B | 429 | 200 | `primary, secondary` | `primary×3, secondary` |
| C | 401 | 200 | `primary, secondary` | `primary, secondary` |
| D | 404 | **502** | `primary` | `primary` |
| E | 400 | **502** | `primary` | `primary` |
| F | All fail | **502** | `primary, secondary` | `primary×3, secondary×3` |
| G | Streaming 500 | 200 | `primary, secondary` | `primary×3, secondary` |

The alias order through the real proxy is **identical** to the direct chain. Every classification
decision survived the proxy hop.

### Finding 1 — LiteLLM retries 5xx/429 three times; 401 once (VERIFIED BY RUNTIME)

The raw call counts expose the retry behaviour of the executor rather than of SabiRoute:
`primary` appears three times for 500, 429 and streaming-500, but only once for 401 and once
for 404/400. That is LiteLLM's own `num_retries` handling, and it is the correct division of
labour: CLAUDE.md §1 assigns **execution-level retries** to LiteLLM and **deterministic
fallback** to SabiRoute. The proof is that SabiRoute's alias order never repeats an alias —
its `attempted` set prevents it — so every repeated call came from the executor.

This also means an operator reading raw upstream request counts will see ~3× the traffic per
logical failure. That is expected, not a leak.

### Finding 2 — a shared proxy changes which alias answers (VERIFIED BY RUNTIME)

The first proxy run produced nonsense: D/E/F/G skipped `primary` entirely and were served by
`secondary`. The cause was not the gateway. Running scenario D alone against a fresh proxy
returned the correct `502` with `calls=['primary']`, so the difference was the **proxy's own
state carried between scenarios**, not SabiRoute's. The harness now starts a fresh proxy per
scenario, which is why Matrix B is clean.

**INFERRED, not established:** the mechanism. LiteLLM's router keeps deployment-failure state
and can change which deployment serves a request after earlier failures; the exact rule is
LiteLLM's and was not inspected. What is established is the consequence: a SabiRoute deployment
alias is not guaranteed to reach the same upstream target across requests, so any future
reasoning that assumes "alias X always means provider X" would be wrong.

### Correction to my own expectations, not to the code (VERIFIED BY RUNTIME)

**D and E return 502, not the upstream status.** I first expected the upstream 4xx to reach the
caller. SabiRoute returns `502` with `type: sabiroute_upstream_error`, which is deliberate and
already test-pinned at `tests/test_completions.py:617`. Leaking an upstream 404 as if SabiRoute's
own route were missing would misclassify a provider fault as a gateway fault, which §7 forbids.
The load-bearing half of the claim — **no fallback occurred** — held on the first run: calls
were exactly `['primary']`.

### Latent trap recorded — `cooldown_until = None` is permanent, not a reset

A first attempt to prove recovery set `cooldown_until = None` and the deployment stayed
unavailable. That is correct: `HealthRegistry.is_available()` returns `False` when `healthy` is
`False` and `cooldown_until` is `None`. Clearing the deadline on an unhealthy deployment is a
**permanent removal**. Only an **expired** deadline re-enters the half-open path in
`available()`. Recorded so no future change "simplifies" recovery into an outage.

### What this still does NOT prove (UNVERIFIED)

- **A real provider failure.** Every failure here was synthesised by the stub. A retired model
  id or an exhausted account through a real alias remains the live datapoint.
- **A real provider behind the proxy.** The proxy is real and unmodified, but its upstream was
  the stub. Provider-side error *shapes* (which upstream fault becomes which proxy status) are
  therefore still unexercised.

**Honest label:** Phase 05 is now **Tested and verified through the real LiteLLM Proxy** on a
controlled upstream. It is not *Complete*, because CLAUDE.md defines Complete as implemented,
tested and **live-verified**, and no real provider failed in this run.

## ARCHITECTURAL POSITION

```
Client → SabiRoute API → Auth/Policy → Classification → Capability Filter → Health Filter
       → Routing Engine → Fallback → LiteLLM → Provider → Response
```

The Fallback stage was exercised, including the Fallback→LiteLLM boundary. Nothing was
modified. No pipeline or configuration change.

- **PostgreSQL:** not contacted; key store was in-memory.
- **Redis:** not contacted.
- **Telemetry:** no database writes; `routing_decisions` events were produced and inspected
  in-process only.
- **Security:** no credential read, printed or committed. Configuration carries
  `os.environ/SABIROUTE_PHASE05_STUB_KEY` whose value is `sk-stub-not-a-credential`; the proxy
  master key unlocks only the proxy this process spawned. Repository credential validation
  accepts the reference form and rejects a literal key, which is itself evidence the policy is
  enforced.
- **Future intelligence:** none. This run deliberately produces no training data.

## ROADMAP POSITION

Phase 05 (Fallback Engine): **Implemented → Tested + proxy-verified.** Not Complete.
Phase 06 (Health Monitoring): cooldown trip and half-open recovery now have runtime evidence on
a real socket path — the first that module has had — but the active checker remains unwired, so
Phase 06 status is unchanged.

## DEPENDENCY IMPACT

Nothing imports `scripts/phase05_fallback_injection.py`. It depends on `tests/conftest.py`
helpers (`InMemoryApiKeyStore`, `provision_test_key`) and on the `litellm` executable in the
project venv for `--via-proxy`; either changing breaks it loudly. Proxy mode takes roughly
20–30 s per scenario because each spawns a proxy.

## NEXT STEP

One datapoint closes Phase 05 to Complete: a genuine provider-side failure through a working
alias — a retired model id, or an exhausted account. That needs one credentialed alias, which
is the Phase 02 blocker, not an engineering gap.

## DO NOT TOUCH YET

- `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`, `.playwright-cli/**`,
  `brag-output/**`, `reports/provider_verification.json`.
- `config/config.yaml` and `config/routes/` — the harness builds its own in-memory config and
  must never be pointed at the production one.
- `training_authorized`, the Phase 13 gate, and the 5 excluded legacy telemetry rows.
- The `cooldown_until = None` trap: do not "simplify" recovery without deciding deliberately
  whether a cleared deadline means permanent or temporary removal.

## CURRENT PROJECT STATUS

```
CURRENT GATE: Sprint 4 — Phase 05 fallback failure-injection complete: 10/10 direct, 7/7 through the real LiteLLM Proxy.
CURRENT PHASE: Phase 05 Tested + proxy-verified; NOT Complete (no real provider failure). Phase 13 READY_FOR_HUMAN_REVIEW, training not authorized.
PROVEN: 500/429/401 fall back; 400/404 do not; exhaustion returns classified 502 sabiroute_upstream_error; SSE failure falls back; timeout retryable; cooldown refuses with zero new upstream calls; half-open recovery restores a fresh failure budget; LiteLLM retries 5xx/429 3x and 401 1x while SabiRoute never repeats an alias; 22 existing tests pass; ruff clean.
UNPROVEN: any real provider-side failure; provider error shapes through the proxy; the mechanism behind LiteLLM's cross-request deployment state.
BLOCKED BY: one working credentialed alias to induce a genuine failure; 7 provider aliases on external account state.
NEXT: induce one real provider failure through a working alias to close Phase 05 to Complete.
```
