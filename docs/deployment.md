# Supported runtime topology

The supported application topology is host-run SabiRoute. The repository's Compose
stack supplies LiteLLM, PostgreSQL, and Redis; it does not currently define a
SabiRoute application container. Do not point a host process at Compose-only names.

| Process | Local host address | Compose address |
| --- | --- | --- |
| SabiRoute → LiteLLM | `http://127.0.0.1:4000` | Not a Compose service; SabiRoute runs on the host |
| SabiRoute → PostgreSQL | `127.0.0.1:5432` | Not applicable to a host process |
| SabiRoute → Redis | `127.0.0.1:6379` | Not applicable to a host process |
| LiteLLM → PostgreSQL | Not applicable to a host process | `postgres:5432` |
| LiteLLM → Redis | Not applicable to a host process | `redis:6379` |

`.env.example` uses loopback addresses for host-run SabiRoute. Compose overrides
LiteLLM's database and Redis addresses to the Compose service names. PostgreSQL and
Redis publish only on `127.0.0.1` by default. `LITELLM_PORT` controls the host port published for
LiteLLM. The old `SABIROUTE_PORT` name is accepted as a Compose fallback only.

PostgreSQL passwords embedded in `DATABASE_URL` must be URL-encoded when they contain
reserved URL characters. Keep `.env` local and never include it in diagnostic output.

## Runtime database addresses

The Compose service hostname `postgres` resolves only for containers on the
Compose network. When SabiRoute runs directly on the host, use the published
PostgreSQL port and a host-resolvable name such as `127.0.0.1` in that process's
`DATABASE_URL`. Keep the repository `.env` configured for the runtime that uses
it; do not copy credentials into command output or commit them.

SabiRoute's API-key table is named `sabiroute_api_keys` and is separate from
LiteLLM's tables in the same PostgreSQL database. The application currently
creates this table idempotently with SQLAlchemy during startup. The repository
does not yet have a versioned migration framework; introduce one before making
non-additive schema changes.

To check a host-run database without editing `.env`, provide a process-local
host override to `scripts/verify_postgres.py`:

```bash
./.venv/bin/python scripts/verify_postgres.py --host 127.0.0.1
```

The check creates a temporary API key, verifies authentication, rotation and
revocation against PostgreSQL, then deletes its temporary rows. It prints the
database and role names, but never the connection password or generated keys.
