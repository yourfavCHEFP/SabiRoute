# Virtual models and routing policies

SabiRoute accepts either a deployment alias (for example, `sabiroute-gemini`)
or a virtual route name (`fast`, `cheap`, `coding`, `reasoning`, `research`, or
`ultimate`) in the `model` field.

The route files in `config/routes/` are loaded at startup. Each file defines an
ordered `deployments` list, a `priority` or `measured` strategy, and a bounded
`max_attempts` value. SabiRoute validates every deployment against
`config/config.yaml` when it starts. Unknown aliases, unsupported strategies,
empty candidate lists, and invalid retry counts fail startup instead of silently
falling back to every configured provider.

Example:

```yaml
name: fast
deployments:
  - sabiroute-gemini
  - sabiroute-openai
strategy: measured
max_attempts: 2
```

The list order is the deterministic tie-break and cold-start preference. Once
fresh, sufficiently sampled telemetry exists, a measured route ranks the
eligible deployments using the configured reliability and latency weights.
Health-aware routing skips deployments during cooldown, and fallback tries the
next remaining eligible deployment after retryable provider failure.
`max_attempts` caps those tries. Capability declaration and Phase 11 filtering
are documented in [capabilities.md](capabilities.md); scoring behavior is in
[routing-scoring.md](routing-scoring.md).

`config/config.yaml` is the canonical runtime deployment catalog for both
SabiRoute and the LiteLLM proxy. Set `SABIROUTE_ROUTES_PATH` only when running
with a separate route directory that matches the selected deployment catalog.

The `research` route currently requires verified chat support and contains the
runtime-verified OpenRouter and Groq deployments. It uses the same configured
measured scoring and fallback behavior as other measured routes; the label does
not imply a verified reasoning or answer-quality capability.

## Appendix: provider-health architecture decision (2026-10-11)

**Status:** decided and implemented — passive `HealthRegistry` is the single
health source of truth; the unused active `ProviderHealthChecker` was removed.

**Evidence:** `providers/healthcheck.py` (active smoke tests via direct
`litellm.completion`) had zero importers, zero tests, and zero references
outside its own file, while `routing/health.py` (`HealthRegistry`: passive
success/failure counting, three-consecutive-failure cooldown, half-open
recovery) is wired into candidate eligibility, deterministic scoring, and
gateway telemetry, with coverage in `tests/test_health.py`,
`tests/test_router.py`, and `tests/test_completions.py`.

**Options considered:** (A) integrate the active checker — rejected without
owner approval: it is synchronous (blocks the async path), bypasses
`LiteLLMClient`/telemetry/budgets, spends real provider budget per probe, and
needs a scheduler, persistence, and registry-bridge design; (B) remove the
dead abstraction — adopted, mirroring the earlier `FallbackEngine` removal;
(C) keep both — rejected: distinct responsibilities (active probing vs passive
eligibility) do not justify carrying unwired code with its own failure
semantics (`unknown_error` catch-all) and 500-char provider-error capture.

**Consequences:** one fewer health definition; no behavior change (the checker
never ran). Re-adding active probing later requires: async design, probe
spend/budget policy, registry integration, persistence decision, tests, and
explicit owner approval. Health thresholds (`failure_threshold`,
`cooldown_seconds`) are unchanged.

### Amendment 2026-11-23 — owner accepted passive-only; re-opening conditions

The owner reviewed the decision above and accepted it: passive `HealthRegistry`
cooldown stays the single health source of truth, and Phase 06 is recorded as
Complete rather than pending. The earlier phase wording ("active checker
unwired") read as unfinished work and invited a re-add; it has been corrected.

The cost this decision accepts, stated plainly: **passive health cannot detect a
dead deployment before it serves a request.** The first three requests to a
newly-broken provider fail before cooldown trips. That is bounded and it is
smaller than the alternative, but it is real, and it is the price of the choice.

Re-open active probing only when **all three** of these hold. Any one alone is
not sufficient:

1. **A route with a single candidate.** With no fallback, a dead deployment is a
   hard outage and pre-flight probing earns its keep. Every route currently has
   fallback, so this does not apply today.
2. **A provider that fails silently.** Passive health only observes failures
   that surface as errors. A provider returning HTTP 200 with unusable content
   looks healthy to `HealthRegistry`. This is the one gap passive health cannot
   close. It is not hypothetical: on 2026-11-23 both `sabiroute-groq` and
   `sabiroute-openrouter` returned 200 with empty assistant text.
3. **Probe cost near zero.** A free-tier `/models` endpoint or a cheap
   token-count call would make probing nearly free and change the arithmetic.
   With ten of fourteen aliases already failing on account balance, a feature
   whose purpose is to spend credits on a schedule is the wrong direction.

None of the three holds as of 2026-11-23.

**Cheaper alternative, if the goal is only to stop serving failed requests.**
Lowering `failure_threshold` for routes with few candidates — or tripping
cooldown on the first failure of a single-candidate route — captures most of the
benefit for a fraction of the cost. That is a config change with a test, not a
subsystem. It is still a behaviour change to health and needs the same explicit
owner approval.
