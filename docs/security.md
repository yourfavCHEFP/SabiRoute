# SabiRoute API-key security

## Authentication boundary

- `POST /v1/chat/completions` requires `Authorization: Bearer <SabiRoute client API key>`.
- Every `/admin/*` route requires the separate `Authorization: Bearer <SABIROUTE_ADMIN_KEY>` bootstrap credential.
- `GET /health` and `GET /health/live` intentionally remain public liveness endpoints.
- FastAPI's `/openapi.json`, `/docs`, and `/redoc` remain public documentation endpoints, as in the existing app configuration.
- Missing, malformed, invalid, and revoked client credentials receive the same `401` response body. A missing key store fails closed with `503`.
- A SabiRoute client key is never forwarded to LiteLLM. The existing `LITELLM_MASTER_KEY` remains the internal SabiRoute-to-LiteLLM credential.

## Key lifecycle

An administrator creates a key with `POST /admin/api-keys` and JSON such as:

```json
{"project_id":"project-a","name":"production"}
```

The response contains the generated `api_key` once. Copy it into the calling application's secret store; SabiRoute cannot recover it later. Rotation via `POST /admin/api-keys/{id}/rotate` atomically revokes the old key and returns its replacement once. Revocation uses `POST /admin/api-keys/{id}/revoke`. These management endpoints themselves require the admin bearer credential.

Use HTTPS on any non-loopback deployment, restrict access to the admin route at the network edge, and provision the admin key through a secret manager or protected environment. The admin bootstrap secret is not stored in PostgreSQL.

Keys are random, high-entropy credentials. PostgreSQL stores only a SHA-256 digest, a non-secret random identifier, project/name metadata, creation/revocation timestamps, and a JSON metadata field reserved for future policy metadata. Plaintext is not logged or returned by later endpoints. The key table is `sabiroute_api_keys`; SQLAlchemy initializes that SabiRoute-owned table in the configured PostgreSQL database. No budgets, per-key rate limits, or permissions are implemented in this phase.

## Configuration and deployment

Set `DATABASE_URL` to the PostgreSQL database used by the deployment and set a unique `SABIROUTE_ADMIN_KEY` in the local secret environment. Do not use `LITELLM_MASTER_KEY` as the SabiRoute admin or client key. Do not commit `.env` or provide credentials in YAML. The example file contains no value for `SABIROUTE_ADMIN_KEY` by design.

The current Compose file defines PostgreSQL for LiteLLM but does not define a SabiRoute application container. When SabiRoute runs on the host, the database hostname in `DATABASE_URL` must resolve from the host (typically `localhost` with the published port); the Compose service name `postgres` is only valid from containers on that Compose network. When SabiRoute later runs on the Compose network, use the service hostname. The SabiRoute table is separately namespaced and does not use LiteLLM's internal schema.

The repository has no SabiRoute migration framework yet; the key table is created idempotently by the SQLAlchemy store during app initialization. PostgreSQL access must be available to SabiRoute at runtime. If `DATABASE_URL` is absent, health endpoints remain available, but protected API/key-store operations fail closed rather than using ephemeral credential storage.
