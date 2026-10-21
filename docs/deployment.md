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
non-root `sabiroute` user, serves the API on 8000, and probes
`GET /health/live` (dependency-free liveness, no
provider calls). File-based configuration is pinned via
`SABIROUTE_CONFIG_PATH` and `SABIROUTE_ROUTES_PATH`
because a wheel install relocates the package away from repository-relative
paths. Secrets arrive via environment only; `.env` never enters the image
(see `.dockerignore`).

Smoke-tested without provider credentials using a sqlite `DATABASE_URL`:
`/health/live` 200, `/health/ready` reporting startup/registry/key_store. A local
full-stack run is `docker compose up --build`
(requires real provider keys in `.env` for actual completions).

## Managed PostgreSQL (DigitalOcean target)

Point `DATABASE_URL` at the managed instance and require TLS:

```bash
DATABASE_URL=postgresql://sabiroute:<url-encoded-password>@<host>:25060/sabiroute?sslmode=require
```

`psycopg` honors `sslmode=require` from the URL; the store passes the URL
through untouched. SabiRoute tables are namespaced (`sabiroute_*`) and live
alongside LiteLLM's tables in the same database without touching them.

Schema evolution is an ordered additive revision ledger
(`sabiroute_schema_versions`; see `security/store.py:SCHEMA_MIGRATIONS`),
applied transactionally at startup by every store entry point. Fresh
databases build all tables; existing databases gain nullable columns via
`ADD COLUMN IF NOT EXISTS`; re-running is a no-op; failures propagate and
roll back, leaving readiness failed rather than half-migrated. Validated
against disposable local PostgreSQL 16: fresh init (both revisions, all
tables), representative usage/chat data round-trip, idempotent re-run,
pre-ledger upgrade with legacy rows preserved as `unknown`, clear
`OperationalError` on bad credentials, and `pg_dump`/restore into a second
database with identical revisions and counts. **Managed-PostgreSQL upgrade
and backup validation remain outstanding**: exercise backup → apply →
row-count check → revision check against a disposable managed instance
before any real migration. Never run migrations against a database whose
target has not been positively identified.

## Redis

Redis is required only when per-key rate limits are configured: without a
limiter the gateway serves (readiness reports `rate_limiter: absent`); with
configured limits but unreachable Redis, admission fails closed (503).
Size the VPS instance with an explicit memory cap and treat Redis loss as
rate-limiting-unavailable, not data loss — all durable state lives in
PostgreSQL. Managed Redis (or the VPS instance) is selected via `REDIS_URL`
/ `REDIS_HOST`; see `.env.example`.

## Startup, shutdown, and rollback

- Startup builds gateway state (config → registry → stores → limiter). Any
  failure degrades loudly: liveness stays up, readiness reports the failing
  component, completions return 503 with the startup error. Never route
  traffic on a `not_ready` instance.
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

To check a host-run database without editing `.env`, connect with `psql` using
the same `DATABASE_URL` the process will use, and exercise the key lifecycle
only against a disposable database.

**Unresolved (documented, not invented):** this candidate ships no
`scripts/verify_postgres.py` helper. The earlier helper created a temporary
API key, verified authentication, rotation and revocation against
PostgreSQL, then deleted its temporary rows. No candidate-shipped script
performs that check; the nearest candidate-shipped coverage is
`tests/test_security.py`, which exercises key creation, rotation and
revocation against its own test store. Do not point it at a production
database.

## Proposed DigitalOcean topology (not provisioned)

- 1× API VPS (2 vCPU / 4 GiB target): SabiRoute container + LiteLLM + VPS
  Redis (memory-capped). Single node: no HA claims.
- 1× managed PostgreSQL, single node: SabiRoute + LiteLLM tables, TLS
  required, off-host backups enabled before any migration.
- Prerequisites: provider keys in the host secret environment (never in the
  image), DNS + TLS termination at the edge (not configured here), Phase 20
  acceptance review before any public shared-inference exposure.
