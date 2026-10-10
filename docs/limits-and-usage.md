# Phase 10: request limits, budgets, and usage

SabiRoute owns admission, budgets, and request accounting. LiteLLM executes the
deployment selected by SabiRoute.

## Request admission

`PUT /admin/api-keys/{key_id}/rate-limit` sets a per-key requests-per-minute
refill rate and burst capacity. Redis applies the token bucket atomically across
SabiRoute processes sharing the Redis database. Buckets start at burst
capacity; rejected attempts do not consume a token and return HTTP `429`,
`rate_limit_exceeded`, and `Retry-After`. Keys without a configured rate limit
remain unlimited. `GET` inspects the setting; `DELETE` removes it. Rotation
copies the configured limit. If Redis cannot safely check a configured limit,
SabiRoute fails closed with HTTP `503` before calling LiteLLM.

## Durable usage and logical requests

PostgreSQL stores one usage row per authenticated client request, using a
unique SabiRoute request ID. A fallback chain remains one logical usage record
and one rate-limit admission. Deployment attempts remain separately counted by
the operational request, latency, error, and health telemetry.

Each row keeps estimated input tokens and reserved tokens separate from
provider-reported prompt, completion, and total tokens. Missing provider usage
stays `null`; SabiRoute does not manufacture actual counts. Provider-reported
usage from failed attempts is included when available. The admin usage endpoint
is paginated and omits credentials and key hashes. Budget usage is visible from
`GET /admin/api-keys/{key_id}/budget`.

## Token reservation contract

Budgets are per API key and use UTC daily and monthly windows. Set a token or
cost budget with `PUT /admin/api-keys/{key_id}/budget`; `GET` inspects limits and
current usage, and `DELETE` removes the active limits. Configuration and
reservations persist in PostgreSQL. A transaction locks the API-key budget row,
checks all enabled windows, and writes the daily and monthly reservations
together. Concurrent requests therefore cannot reserve the same remaining
capacity twice. Existing reservations remain accounted after limits are
removed or changed.

For a configured token budget, callers must supply a positive `max_tokens`.
Admission reserves:

```text
estimated input tokens + max_tokens
```

The current estimator supports text-only chat messages and uses compact UTF-8
JSON byte length plus a fixed per-message framing allowance. Multimodal
messages and request parameters outside the documented estimator contract fail
with HTTP `400` before provider execution. Estimated and actual counts are
stored separately. When actual usage is reported, SabiRoute reconciles the
reservation to the reported aggregate; when it is not reported, the reservation
remains charged and actual usage remains unknown.

A logical request reserves once across fallback attempts. After a failed
attempt reports usage, the remaining output cap for a fallback is reduced to
fit the original reservation. If a failed attempt's usage is absent or cannot
be totaled, SabiRoute stops that budgeted fallback chain rather than assuming
the attempt consumed nothing. A no-usage success keeps the conservative
reservation charged. This avoids silently releasing capacity that may have
been spent upstream.

## Monetary budgets and pricing

Prices are optional and must be explicitly configured on a deployment in
`config/config.yaml`:

```yaml
- model_name: example
  input_cost_per_million_tokens: 0.15
  output_cost_per_million_tokens: 0.60
  litellm_params:
    model: provider/model
```

SabiRoute calculates the preflight quote using the highest priced routing
candidate and the token reservation. It does not fetch prices or invent missing
values. If a key has a monetary budget and any candidate lacks reliable price
metadata, admission fails closed with HTTP `503` and
`budget_pricing_unavailable`; the cost remains unknown, not zero. Actual cost is
recorded only when provider-reported prompt/completion tokens and configured
pricing both make it calculable. Otherwise the actual cost is `null` and the
estimated reservation remains charged.

Provider price changes are operational configuration changes; administrators
must keep this metadata current. Values are USD per one million input/output
tokens.

## Persistence and failure behavior

The budget configuration, reservations, and usage rows are SabiRoute-owned
PostgreSQL data. Table creation is additive, and existing usage tables receive
nullable accounting columns at startup. A failed database lookup, reservation,
or reconciliation fails closed with HTTP `503`; a token or monetary cap
violation returns HTTP `429` before provider execution. PostgreSQL persistence
survives SabiRoute restarts. Redis holds only the request-rate bucket state.

This remains Phase 10 governance and accounting. It does not add routing
intelligence, scoring, or ML behavior.
