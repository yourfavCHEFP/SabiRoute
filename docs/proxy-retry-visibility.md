# LiteLLM proxy retry visibility (2026-10-11; updated 2026-10-15)

Scope: operator procedure + verified repository facts. No code changed by
this document. Nothing here starts services, contacts providers, or reads
secret values.

Update 2026-10-15: `config/config.yaml` now sets `num_retries: 1` on every
deployment (was: no retry knobs), and the HTTP 429 evidence gap is closed
by `artifacts/sprint13-429-drill/results.json`. Sections below marked
accordingly; the layering model and blocked-claims discipline are unchanged.

## Verified repository facts

- SabiRoute's `LiteLLMClient` issues exactly one raw httpx request per
  execution attempt (no client retries, backoff, or `num_retries` payload).
  Proven by `tests/test_proxy_attempt_census.py` against a local stub.
- `config/config.yaml` (also mounted read-only as the proxy's
  `/app/config.yaml` in `docker-compose.yml`) sets an explicit
  per-deployment proxy retry knob: `litellm_params.num_retries: 1` on all
  14 deployments (added in `fa60576`; verify with
  `grep -c "num_retries: 1" config/config.yaml`, which should print 14).
  Meaning: one retry after the first try — up to 2 stub-observed requests
  per SabiRoute→proxy attempt for the tested failure classes (see
  "Measured layering" below; a configured count is not proof of
  provider executions). `litellm_settings` carries only
  `request_timeout: 120`, `drop_params`, `set_verbose`;
  `general_settings` carries only `master_key`. No `fallbacks`,
  `allowed_fails`, or cooldown entries exist in-repo.
- Compose `retries: 5` entries are container healthcheck/restart policy,
  not HTTP retries. Do not infer runtime retry behavior from them.
- The proxy image floats (`ghcr.io/berriai/litellm:main-latest`), so its
  exact version — and therefore its defaults — is unknown from the repo.

## Measured layering (history, not fresh results)

Three distinct numbers; do not conflate them:

- **SabiRoute logical attempts** (`max_attempts`: direct-alias requests 2;
  route files e.g. `fast: 2`, `cheap: 1`, `ultimate: 3`). Owned by
  SabiRoute, bounded by the attempt loop in
  `src/sabiroute/api/completions.py`, counted per attempt in telemetry
  `routing_decisions`.
- **LiteLLM proxy retries within one attempt** (`num_retries: 1` now
  configured). Owned by the proxy, invisible to SabiRoute telemetry except
  as latency inside the attempt.
- **Total upstream requests observed in controlled stub experiments** =
  attempts × per-attempt proxy requests. Worst observed shape for `fast`
  under r1 is 2 × 2 = 4 stub requests per logical request (3-attempt
  policies: 3 × 2 = 6).

Historical drill evidence (do not re-cite as fresh measurements):

- `artifacts/sprint13-policy-experiment/results.json` (2026-10-12/13,
  pinned proxy image, 10s proxy timeout): per proxy inbound, base
  (unset) 3 / r1 2 / r0 1 stub requests for 500, reset, malformed-200,
  hang, and delay classes; 401 never retried in any variant.
- `artifacts/sprint13-429-drill/results.json` (2026-10-13, same pinning):
  HTTP 429 with `Retry-After: 2` retried exactly like 500s (3/2/1 across
  base/r1/r0) with ~2.3–2.7s inter-retry gaps. The earlier "429
  unmeasured" caveat is closed for the stub boundary.

Stub request counts prove requests reached the stub — nothing about real
provider executions, billing, or cancellation. Whether `num_retries: 1`
is production-correct (resilience vs. duplicate-execution cost) remains
an owner policy decision; this document only records what is configured
and what was measured.

## Version-grounded default chain (reference only, venv litellm 1.103.0)

In the pinned SDK source (litellm 1.103.0, `router.py:1031-1036`), `Router`
resolves retries as: explicit `num_retries` → `litellm.num_retries`
(module default `None`, `__init__.py:532`; a separate
`num_retries_per_request` knob also defaults `None`) →
`openai.DEFAULT_MAX_RETRIES` (= 2 with openai 2.54.0). LiteLLM's own
`proxy_server.py` (a LiteLLM-internal module, not a file in this
repository) sets no `num_retries`, so *under 1.103.0 semantics* an unconfigured proxy
may retry failed provider calls before SabiRoute ever sees a response. The
running `main-latest` image may differ — treat this as a concrete suspicion
to verify, not a fact about the deployment.

## Operator verification procedure (read-only, no secret output)

1. **Static:** confirm `config/config.yaml` still carries `num_retries: 1`
   on every deployment
   (`grep -c "num_retries: 1" config/config.yaml` should print 14; any
   other count means the retry posture changed and the layering numbers
   above must be re-derived, not assumed) and record the deployed image
   digest (`docker inspect sabiroute-gateway --format '{{.Image}}'`).
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
- Deployed image identification from this machine (2026-10-12): the local
  Docker daemon holds no LiteLLM image, so no digest or version can be
  read without pulling — which is out of scope.
- Pinning the proxy image or changing the configured `num_retries: 1`
  (including to 0) / fallback policy (proxy config change; owner decision,
  out of scope — changing the retry count in either direction is itself a
  behavior change needing review, not a default to assume).

## Duplicate-execution and billing risk (analysis, not observed behavior)

- A provider may execute a request whose response is then lost (timeout,
  reset, malformed body). SabiRoute's no-retry rule for malformed-200 and
  its bounded `max_attempts` limit SabiRoute-side re-execution, but usage
  for failed attempts is recorded only when the failure body carries
  parsable token counts; otherwise usage stays null and budgets reconcile
  against the reservation rather than actuals.
- Any proxy-internal retry would consume real provider quota and budget
  outside SabiRoute's reservation accounting, and its latency would land
  inside the attempt's measured latency (depressing deterministic-v1
  scores without a visible cause). Treat per-attempt cost/latency
  anomalies as a signal to run the verification procedure above.
