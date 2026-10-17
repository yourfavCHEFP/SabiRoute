# Contributing to SabiRoute

Thanks for taking an interest in SabiRoute. The project is in alpha, so focused bug reports, documentation improvements, and small, well-supported changes are especially useful. Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## Before starting

- Search existing issues and pull requests before opening a new one.
- For a large change, open an issue or discussion first so the scope and design can be agreed before implementation.
- Describe bugs with the affected route, expected behavior, actual behavior, and a minimal reproduction. Never include API keys, `.env` contents, or private user data.
- Keep the architecture boundary clear: **SabiRoute decides; LiteLLM executes.** Changes to routing, fallback, health, budgets, or security need tests and a clear explanation of their evidence and failure behavior.

## Development setup

Requirements: Python 3.11–3.13, [uv](https://docs.astral.sh/uv/), and Docker for the local service stack.

```bash
uv sync
cp .env.example .env
# Fill in local values in .env; never commit it.
docker compose up -d
```

Run SabiRoute from the project environment:

```bash
./.venv/bin/sabiroute
```

The supported local topology runs SabiRoute on the host beside the Compose services. See [docs/deployment.md](docs/deployment.md) before changing database or service addresses.

## Making a change

1. Work on a focused branch and keep unrelated work out of the change.
2. Follow the existing type hints, configuration validation, and error-handling patterns.
3. Add or update tests for changed behavior. Use fakes or local services for failure cases; do not deliberately disrupt live providers or manufacture telemetry.
4. Keep routing eligibility, authentication, budgets, capability requirements, health exclusions, and bounded fallback as hard constraints. Do not add training or ML routing without its documented data and evaluation gates.
5. Update relevant documentation and identify whether evidence is from inspection, automated tests, or live execution.
6. Review the full diff and remove secrets, generated reports, and local artifacts before opening a pull request.

## Validation

For code changes, run the relevant tests and the maintained-code checks:

```bash
./.venv/bin/python -m pytest
./.venv/bin/ruff check src tests scripts config
./.venv/bin/mypy src
```

Some provider and Redis checks require local services or make real provider requests. Read the relevant script or test documentation before running them, and do not share generated reports until they have been reviewed for sensitive data.

## Pull requests

Explain the problem, the behavior changed, and how you verified it. Call out any unverified assumptions or limitations. Keep the pull request limited to one coherent change; maintainer review and acceptance are required before merge.
