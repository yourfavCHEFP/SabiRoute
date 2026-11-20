# Sprint 13 retry-budget experiment (isolated, review-only artifacts)

Compares three proxy retry configurations against a scripted stub. Fake
credentials only; `--internal` network (no egress); no real providers.

- `stub_server.py` — scripted stub with arrival/completion timestamps.
- `drill-config-{base,r1,r0}.yaml` — proxy configs (r1/r0 set per-deployment
  `litellm_params.num_retries`; base unset).
- `results.json` — measured stub counts per case and variant.

Headline: unset → 3 upstream attempts on retryable failures; `num_retries: 1`
→ 2; `num_retries: 0` → 1; 401 never retried. Stub counts are not billing
proof. SabiRoute-side bounds come from `tests/test_proxy_attempt_census.py`.

Cleanup (drill resources only):
`docker rm -f sabi-policy-proxy sabi-policy-stub && docker network rm sabi-policy-net`
Image stays cached; never `docker system prune`.
