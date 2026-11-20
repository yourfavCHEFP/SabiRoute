# Sprint 13 proxy retry drill (isolated, review-only artifacts)

Isolated Docker lab measuring LiteLLM Proxy retry behavior. Fake credentials
only (`sabi-drill-test-only`, `sk-drill-fake`); no real providers contacted;
`--internal` network (no egress — verified by graceful cost-map fallback).

- `stub_server.py` — scripted OpenAI-compatible stub (`SABI_DRILL_MODE`).
- `drill-config.yaml` — proxy config: one stub-backed model, 10s timeout.
- `results.json` — measured per-case counters (sanitized, no bodies/keys).

Key result: unconfigured pinned proxy (`main-latest@sha256:de5b05…`)
retries 500/reset/malformed/timeout failures twice (3 stub requests per
proxy inbound); 401 is not retried. SabiRoute-side bounds are proven by
`tests/test_proxy_attempt_census.py`; stub counts are not billing proof.

Cleanup (drill resources only):
`docker rm -f sabi-drill-proxy sabi-stub && docker network rm sabi-drill-net`
Image stays cached; never `docker system prune`.
