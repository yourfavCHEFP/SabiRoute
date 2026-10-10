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
