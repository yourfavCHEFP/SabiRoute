# SabiRoute API-key security

## Authentication boundary

- `POST /v1/chat/completions` requires `Authorization: Bearer <SabiRoute client API key>`.
- Every `/admin/*` route requires the separate `Authorization: Bearer <SABIROUTE_ADMIN_KEY>` bootstrap credential.
- `GET /health` and `GET /health/live` intentionally remain public liveness endpoints.
- FastAPI's `/openapi.json`, `/docs`, and `/redoc` are disabled by default in this candidate: `main.py` sets `docs_url`, `redoc_url`, and `openapi_url` to `None` unless `SABIROUTE_DOCS_ENABLED` is set to a truthy value (`1`, `true`, `yes`, `on`). The documentation endpoints are therefore served only when that variable is explicitly enabled. This behaviour is established from the candidate implementation; the candidate's test suite asserts only that `.env.example` documents the variable, not the resulting endpoint behaviour.
- Missing, malformed, invalid, and revoked client credentials receive the same `401` response body. A missing key store fails closed with `503`.
- A SabiRoute client key is never forwarded to LiteLLM. The existing `LITELLM_MASTER_KEY` remains the internal SabiRoute-to-LiteLLM credential.

## Key lifecycle

An administrator creates a key with `POST /admin/api-keys` and JSON such as:

```json
{"project_id":"project-a","name":"production"}
```

The response contains the generated `api_key` once. Copy it into the calling application's secret store; SabiRoute cannot recover it later. Rotation via `POST /admin/api-keys/{id}/rotate` atomically revokes the old key and returns its replacement once. Revocation uses `POST /admin/api-keys/{id}/revoke`. These management endpoints themselves require the admin bearer credential.

Use HTTPS on any non-loopback deployment, restrict access to the admin route at the network edge, and provision the admin key through a secret manager or protected environment. The admin bootstrap secret is not stored in PostgreSQL.

Keys are random, high-entropy credentials. PostgreSQL stores only a SHA-256 digest, a non-secret random identifier, project/name metadata, creation/revocation timestamps, and a JSON metadata field reserved for future policy metadata. Plaintext is not logged or returned by later endpoints. The key table is `sabiroute_api_keys`; SQLAlchemy initializes that SabiRoute-owned table in the configured PostgreSQL database. Budgets and permission tiers are not implemented in this phase. Per-key rate
limits are, but only for keys that have a limit row: `security/rate_limit.py`
implements a Redis-backed token bucket (`RedisTokenBucket`, key prefix
`sabiroute:rate:v1`) whose Lua script performs an atomic per-key admit or
deny using the Redis server clock, so enforcement is shared across instances
pointing at the same Redis. A key with no limit row is not metered, and the
limiter is consulted only for keys that have one. The bucket's admit and deny
behaviour has been exercised at component level against Redis; end-to-end
enforcement over the HTTP request path has not been verified for a key with a
configured limit.

## Configuration and deployment

Set `DATABASE_URL` to the PostgreSQL database used by the deployment and set a unique `SABIROUTE_ADMIN_KEY` in the local secret environment. Do not use `LITELLM_MASTER_KEY` as the SabiRoute admin or client key. Do not commit `.env` or provide credentials in YAML. The example file contains no value for `SABIROUTE_ADMIN_KEY` by design.

The Compose file in this candidate defines a `sabiroute` service built from the repository `Dockerfile` and published on `127.0.0.1:${SABIROUTE_API_PORT:-8000}`, alongside `litellm`, `postgres`, and `redis`; all four publish on loopback only. Inside the Compose network the `sabiroute` service overrides `DATABASE_URL` and the `REDIS_*` addresses to the Compose service names. When SabiRoute runs on the host instead, the database hostname in `DATABASE_URL` must resolve from the host (typically `127.0.0.1` with the published port); the Compose service name `postgres` is only valid from containers on that Compose network. The SabiRoute table is separately namespaced and does not use LiteLLM's internal schema.

The repository has no SabiRoute migration framework yet; the key table is created idempotently by the SQLAlchemy store during app initialization. PostgreSQL access must be available to SabiRoute at runtime. If `DATABASE_URL` is absent, health endpoints remain available, but protected API/key-store operations fail closed rather than using ephemeral credential storage.
