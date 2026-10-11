# LiteLLM proxy retry visibility (2026-10-11)

Scope: operator procedure + verified repository facts. No code changed by
this document. Nothing here starts services, contacts providers, or reads
secret values.

## Verified repository facts

- SabiRoute's `LiteLLMClient` issues exactly one raw httpx request per
  execution attempt (no client retries, backoff, or `num_retries` payload).
  Proven by `tests/test_proxy_attempt_census.py` against a local stub.
- `config/config.yaml` (also mounted read-only as the proxy's
  `/app/config.yaml` in `docker-compose.yml`) sets **no** retry knobs:
  `litellm_settings` has only `request_timeout: 120`, `drop_params`,
  `set_verbose`; `general_settings` has only `master_key`. No
  `num_retries`, `fallbacks`, `allowed_fails`, or cooldown entries exist
  anywhere in-repo (searched `config/`, compose, `src/`).
- Compose `retries: 5` entries are container healthcheck/restart policy,
  not HTTP retries. Do not infer runtime retry behavior from them.
- The proxy image floats (`ghcr.io/berriai/litellm:main-latest`), so its
  exact version — and therefore its defaults — is unknown from the repo.

## Version-grounded default chain (reference only, venv litellm 1.103.0)

In the pinned SDK source (litellm 1.103.0, `router.py:1031-1036`), `Router`
resolves retries as: explicit `num_retries` → `litellm.num_retries`
(module default `None`, `__init__.py:532`; a separate
`num_retries_per_request` knob also defaults `None`) →
`openai.DEFAULT_MAX_RETRIES` (= 2 with openai 2.54.0). `proxy_server.py`
sets no `num_retries`, so *under 1.103.0 semantics* an unconfigured proxy
may retry failed provider calls before SabiRoute ever sees a response. The
running `main-latest` image may differ — treat this as a concrete suspicion
to verify, not a fact about the deployment.

## Operator verification procedure (read-only, no secret output)

1. **Static:** confirm `config/config.yaml` still carries no retry keys
   (`grep -n "num_retries\|fallbacks\|allowed_fails\|cooldown" config/config.yaml`
   should print nothing) and record the deployed image digest
   (`docker inspect sabiroute-gateway --format '{{.Image}}'`).
2. **Startup:** read the proxy's effective model list via the authenticated
   model-info endpoint, which redacts keys and api bases
   (`GET /model/info` on the proxy with the master key; never log or
   commit the key or the response's credential fields).
3. **Runtime-observed:** with a non-production key, send one request to a
   deployment forced to fail (e.g., invalid test credential at the
   *provider* level, or a locally stubbed provider base) and count
   provider-side attempts in the proxy logs (`set_verbose` is false by
   default; raise log verbosity temporarily if needed). Compare against
   the single inbound request.
4. **Record:** image digest, observed attempt multiple (1:1 or N:1), and
   which failure classes retried. Do not generalize one failure class to
   all errors.

Prerequisites if unavailable: a running proxy (do not start services
without approval), the master key held by the operator (never place it in
repo files), and proxy log access.

## How hidden proxy retries would affect SabiRoute (risks, not claims)

- **Attempts vs provider calls:** SabiRoute telemetry counts
  SabiRoute→proxy attempts; proxy-internal retries would make provider
  calls a multiple of that. The census tests prove the first number only.
- **Budgets/rate limits:** SabiRoute reserves once per logical request and
  reconciles from observed usage; untracked proxy retries consume real
  provider quota and latency outside that accounting.
- **Latency:** proxy-retry time lands inside SabiRoute's per-attempt
  latency, inflating measured latency and depressing deterministic-v1
  scores for that deployment without a visible cause.
- **Duplicate execution:** a provider may process a request whose response
  is then retried — the same replay hazard that motivates SabiRoute's own
  no-retry rule for malformed responses, one layer down.
- **Phase 13:** inflated failure/latency observations would enter feature
  snapshots as ground truth; selection-bias and provenance analysis must
  treat proxy-multiplied attempts as a confounder until ruled out.

## What stays blocked

- Any claim that the production proxy performs exactly one provider
  attempt per request (needs the procedure above).
- Pinning the proxy image or setting explicit `num_retries: 0` /
  fallback policy (proxy config change; owner decision, out of scope —
  note that disabling proxy retries is itself a behavior change needing
  review, not a default to assume).
