# Supported runtime topology

Two supported topologies: host-run SabiRoute (development default) and the
SabiRoute application container (staging/production foundation). The
repository's Compose stack supplies LiteLLM, PostgreSQL, Redis, and — since
Sprint 5 — the SabiRoute API itself. Do not point a host process at
Compose-only names.

| Process | Local host address | Compose address |
| --- | --- | --- |
| SabiRoute → LiteLLM | `http://127.0.0.1:4000` | `http://litellm:4000` |
| SabiRoute → PostgreSQL | `127.0.0.1:5432` | `postgres:5432` |
| SabiRoute → Redis | `127.0.0.1:6379` | `redis:6379` |
| LiteLLM → PostgreSQL | Not applicable to a host process | `postgres:5432` |
| LiteLLM → Redis | Not applicable to a host process | `redis:6379` |

`.env.example` uses loopback addresses for host-run SabiRoute. Compose overrides
both LiteLLM's and SabiRoute's database and Redis addresses to the Compose
service names. PostgreSQL, Redis, LiteLLM, and SabiRoute publish only on
`127.0.0.1` by default. `LITELLM_PORT` controls the host port published for
LiteLLM and `SABIROUTE_API_PORT` the one for SabiRoute. The old
`SABIROUTE_PORT` name is accepted as a Compose fallback only.

PostgreSQL passwords embedded in `DATABASE_URL` must be URL-encoded when they contain
reserved URL characters. Keep `.env` local and never include it in diagnostic output.

## Application container

Build with `docker build -t sabiroute .` (verified: 2.71 GB, litellm
dependency weight included). The image installs from `uv.lock`, runs as the
non-root `sabiroute` user, serves the API on 8000 with the SabiChat UI at
`/app/`, and probes `GET /health/ready`. Readiness — not liveness — is the
container gate: it reports 503 while the schema is unmigrated or the gateway
is otherwise degraded, so an unready container cannot present as healthy.
File-based configuration is pinned via
`SABIROUTE_CONFIG_PATH`, `SABIROUTE_ROUTES_PATH`, and `SABIROUTE_WEB_DIR`
because a wheel install relocates the package away from repository-relative
paths. Secrets arrive via environment only; `.env` never enters the image
(see `.dockerignore`).

Smoke-tested without provider credentials using a sqlite `DATABASE_URL`:
`/health/live` 200, `/health/ready` reporting startup/registry/key_store,
`/app/` 200. A local full-stack run is `docker compose up --build`
(requires real provider keys in `.env` for actual completions).

## Managed PostgreSQL (DigitalOcean target)

Point `DATABASE_URL` at the managed instance and require TLS:

```bash
DATABASE_URL=postgresql://sabiroute:<url-encoded-password>@<host>:25060/sabiroute?sslmode=require
```

`psycopg` honors `sslmode=require` from the URL; the store passes the URL
through untouched. SabiRoute tables are namespaced (`sabiroute_*`) and live
alongside LiteLLM's tables in the same database without touching them.

## Schema migration (explicit, one-shot)

Schema is **never** created or altered by application startup or by a store
constructor. `PostgresApiKeyStore` and `SabiChatStore` only open connections;
startup runs a read-only compatibility check (`security/store.py:check_schema`
and friends). Bringing a database to the current schema is a separate,
explicit migration step:

```bash
python -m sabiroute.migrate
```

This is the only supported schema writer. It reads `DATABASE_URL` (or
`SABIROUTE_DATABASE_URL`) and `SABIROUTE_SCHEMA_GROUPS` (`core` or `full`,
default `full`), then applies the ordered, additive revision ledger recorded in
`sabiroute_schema_versions` (see `security/store.py:SCHEMA_MIGRATIONS`). Fresh
databases build all tables for the selected group; existing databases gain
nullable columns via `ADD COLUMN IF NOT EXISTS`; re-running is a no-op.

Exit status is meaningful: `0` means the schema exists and passed validation,
`1` means migration failed (the transaction rolls back, leaving nothing
half-applied), `2` means no database URL was configured. On PostgreSQL the
whole migration runs inside one transaction holding `pg_advisory_xact_lock`
with `lock_timeout = '30s'`, so concurrent migrators serialize instead of
racing.

The deployment contract is therefore:

```
fresh database
  → explicit migration (python -m sabiroute.migrate)
  → migration succeeded
  → schema exists and validates
  → gateway starts normally
```

`docker-compose.yml` encodes that ordering: the one-shot `sabiroute-migrate`
service runs the migration after PostgreSQL is healthy, and the `sabiroute`
API service declares
`depends_on: sabiroute-migrate: condition: service_completed_successfully`.
A failed migration therefore prevents the API from starting at all. For a
standalone container or a host-run process, run the migration first:

```bash
docker run --rm --env-file .env sabiroute:local python -m sabiroute.migrate
```

**If migration is skipped on a fresh database**, startup does not fake success:
the read-only check fails, the gateway degrades (liveness stays up, readiness
returns 503, completions return 503 with the startup error), and the image
`HEALTHCHECK` — which probes `/health/ready` — reports the container unhealthy.
The older `GET /health/live` probe passes in that state and must not be used as
a deployment gate.

**Managed-PostgreSQL upgrade and backup validation remain outstanding**:
exercise backup → apply → row-count check → revision check against a
disposable managed instance before any real migration. Never run migrations
against a database whose target has not been positively identified.

## Redis

Redis is required only when per-key rate limits are configured: without a
limiter the gateway serves (readiness reports `rate_limiter: absent`); with
configured limits but unreachable Redis, admission fails closed (503).
Size the VPS instance with an explicit memory cap and treat Redis loss as
rate-limiting-unavailable, not data loss — all durable state lives in
PostgreSQL. Managed Redis (or the VPS instance) is selected via `REDIS_URL`
/ `REDIS_HOST`; see `.env.example`.

## Startup, shutdown, and rollback

- Startup builds gateway state (config → registry → stores → limiter) and then
  runs a read-only schema check. Migration is **not** part of startup — apply
  it first (see "Schema migration" above). Any failure degrades loudly:
  liveness stays up, readiness reports the failing component, completions
  return 503 with the startup error. Never route traffic on a `not_ready`
  instance.
- Shutdown closes the key store, rate limiter, and chat store via the
  lifespan handler.
- Request logs are structured (see `utils/logging.py`); they carry request
  IDs, deployments, and error categories — never keys, tokens, or provider
  credentials.
- Rollback is image-tag based: revisions are additive-only, so running the
  previous image against a migrated database is safe (new columns are
  ignored). Keep the previous image tagged until the new revision is
  verified against `/health/ready`.

## Runtime database addresses

The Compose service hostname `postgres` resolves only for containers on the
Compose network. When SabiRoute runs directly on the host, use the published
PostgreSQL port and a host-resolvable name such as `127.0.0.1` in that process's
`DATABASE_URL`. Keep the repository `.env` configured for the runtime that uses
it; do not copy credentials into command output or commit them.

To check a host-run database without editing `.env`, provide a process-local
host override to `scripts/verify_postgres.py`:

```bash
./.venv/bin/python scripts/verify_postgres.py --host 127.0.0.1
```

The check creates a temporary API key, verifies authentication, rotation and
revocation against PostgreSQL, then deletes its temporary rows. It prints the
database and role names, but never the connection password or generated keys.

## Proposed DigitalOcean topology (not provisioned)

- 1× API VPS (2 vCPU / 4 GiB target): SabiRoute container + LiteLLM + VPS
  Redis (memory-capped). Single node: no HA claims.
- 1× managed PostgreSQL, single node: SabiRoute + LiteLLM tables, TLS
  required, off-host backups enabled before any migration.
- Cloudflare Pages: static `web/` build and docs.
- Prerequisites: provider keys in the host secret environment (never in the
  image), DNS + TLS termination at the edge (not configured here), Phase 20
  acceptance review before any public shared-inference exposure.
