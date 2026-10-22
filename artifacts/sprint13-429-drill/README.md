# Sprint 13 HTTP 429 retry drill (isolated, review-only artifacts)

Closes the 429 evidence gap left by the earlier retry-budget drill. Fake
credentials only; `--internal` network (no egress); no real providers.

- `stub_server.py` — scripted stub; 429 mode returns `Retry-After: 2`.
- `drill-config-{base,r1,r0}.yaml` — proxy configs (r1/r0 set
  per-deployment `litellm_params.num_retries`).
- `results.json` — measured stub counts, elapsed times, log evidence.

Headline: pinned proxy retries 429s exactly like 500s (3/2/1 across
base/r1/r0), with ~2s gaps matching the Retry-After header. Stub counts
are not billing proof. SabiRoute treats upstream 429 as retryable with
bounded fallback (unit-tested); stacked worst case per logical request is
SabiRoute attempts × proxy retries for the configured variant.

Cleanup (drill resources only):
`docker rm -f sabi-429-proxy sabi-429-stub && docker network rm sabi-429-net`
Image stays cached; never `docker system prune`.
