# SabiRoute local validation

How to verify a SabiRoute change on a developer machine, offline-first, without live services or secrets.

Working directory for every command below: the repository root (`/Users/airm2/My ML Hub/SabiRoute` in the
current checkout; any clone works the same way). The project interpreter is `./.venv/bin/python`.

## Tiers

| Tier | Command | Needs | Offline | What it proves |
|---|---|---|---|---|
| T1 fast checks | `./.venv/bin/ruff check src tests scripts config` | nothing | yes | maintained tree lints clean |
| T1 fast checks | `./.venv/bin/mypy src` | nothing | yes | 46 source files type-check |
| T1 fast checks | `node --check web/app.js` | node | yes | frontend syntax valid |
| T1 fast checks | `./.venv/bin/python scripts/validate_free_pool_catalogue.py docs/free-pool-catalogue-v0.1-draft.json` | nothing | yes | catalogue draft schema-valid |
| T2 local regression | `./.venv/bin/python -m pytest -q` | nothing | yes | full offline suite (stubs only; integration tests skip) |
| T2 narrow | `./.venv/bin/python -m pytest tests/test_sabichat.py tests/test_completions.py -k "register or login or disabled or password or startup or upstream or empty_registry or exhausted or malformed" -q` | nothing | yes | F-01/F-02/F-03 security paths |
| T3 opt-in integration | `SABIROUTE_TEST_REDIS_URL=redis://127.0.0.1:6379/0 ./.venv/bin/python -m pytest tests/test_rate_limit_redis.py -q` | loopback Redis | no | Lua token-bucket against real Redis |
| T3 opt-in integration | `SABIROUTE_TEST_PG_URL=<disposable-loopback-url> ./.venv/bin/python -m pytest tests/test_user_quotas.py tests/test_shared_inference.py -q` | disposable loopback PostgreSQL | no | concurrent quota/share-inference behavior |
| External (explicit only) | `./.venv/bin/python scripts/test_providers.py ...` | provider keys + owner approval | no | live provider behavior; **never** part of local validation |

Skipped integration tests are reported as `SKIPPED ... is not set`, never as passes. A green T2 run with
skips means "offline behavior verified; integration behavior unverified" — see § Skips.

## Expected T2 result (verified 2026-10-17)

```
404 passed, 7 skipped in ~17s
```

The 7 skips: 4 Redis (`SABIROUTE_TEST_REDIS_URL` unset), 3 PostgreSQL (`SABIROUTE_TEST_PG_URL` unset).
411 tests collect in total. If your run shows different numbers, note the delta and investigate —
do not weaken tests or skip assertions to recover a green summary.

## What never runs locally by default

- No live provider requests: the suite uses `StubLiteLLMClient` (`tests/conftest.py`). `scripts/test_providers.py`
  is the only script that makes real provider calls, and CI never runs it.
- No service startup: no `docker compose up`, no `sabiroute` server, no migrations against shared databases.
- No secrets: validation never reads `.env`. Never run `docker compose config` (it can expose interpolated secrets).

## Contract tests that guard the workflow itself

`tests/test_deployment.py` pins the deployment contract in code: `Dockerfile` runtime contents,
`.dockerignore` secret exclusions, CI workflow presence/secret-freedom, and `.env.example` placeholder
discipline. If CI, Docker, or the env template drifts from the contract, this file fails first.

## Failure triage

| Symptom | Likely cause | First step |
|---|---|---|
| `mypy src` reports errors in files you did not touch | owner work in progress on the branch | report the file/line; do not reformat unrelated code |
| `ruff format --check` flags files | pre-existing style drift (accepted; formatting is not a gate) | leave untouched; only `ruff check` is the lint gate |
| pytest failures mentioning Redis/PostgreSQL URLs | pointed at an unreachable or non-loopback instance | unset the env var to return to skip mode; never point opt-in vars at shared databases |
| `test_ci_workflow_is_valid_and_secret_free` fails | CI workflow edited with secrets or `${{ }}` interpolation | inspect `.github/workflows/ci.yml` diff |

A green T1+T2 run is local-merge confidence, not release readiness: live-provider behavior, managed-database
proof, and staging review are separate gates (see `reports/remediation-roadmap-and-gates.md` and
`docs/architecture-decision-record.md`).
