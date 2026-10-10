"""Exercise Phase 10 request accounting and rate limits against local services."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClientError
from sabiroute.security.budgets import estimate_input_tokens
from sabiroute.security.keys import ApiKeyRateLimit
from sabiroute.security.rate_limit import RedisTokenBucket
from sabiroute.security.store import PostgresApiKeyStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_MODEL = "phase10-smoke-invalid-model"
SMOKE_MESSAGES = [{"role": "user", "content": "x"}]


class LocalCompletionStub:
    """Return deterministic usage without making any external provider calls."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail_once = False

    async def chat_completion(self, decision, messages, *, max_tokens=None, **kwargs):
        self.calls.append(decision.deployment)
        if self.fail_once:
            self.fail_once = False
            raise LiteLLMClientError(
                "local smoke fallback",
                status_code=503,
                response_body={"usage": {"prompt_tokens": 0, "completion_tokens": 0}},
            )
        return {
            "id": "phase10-local-smoke",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        }


async def check_atomic_redis_burst(
    host: str,
    port: int,
    password: str | None,
    burst: int,
) -> tuple[str, int]:
    client = Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
        socket_connect_timeout=3,
    )
    key_id = secrets.token_hex(12)
    limiter = RedisTokenBucket(client, key_prefix="sabiroute:phase10-smoke")
    try:
        if not await client.ping():
            raise RuntimeError("Redis PING did not return success.")
        limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=burst)
        decisions = await asyncio.gather(
            *(limiter.admit(key_id, limit) for _ in range(burst * 4))
        )
        admitted = sum(decision.admitted for decision in decisions)
        if admitted != burst:
            raise RuntimeError(
                f"Redis admitted {admitted} concurrent requests; expected burst {burst}."
            )
        return key_id, admitted
    finally:
        await client.delete(f"sabiroute:phase10-smoke:{key_id}")
        await client.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-host", default="127.0.0.1")
    parser.add_argument("--redis-host", default="127.0.0.1")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument(
        "--redis-no-auth",
        action="store_true",
        help="Connect to local Redis without the REDIS_PASSWORD from .env.",
    )
    parser.add_argument("--redis-burst", type=int, default=8)
    args = parser.parse_args()
    if args.redis_burst < 1:
        raise SystemExit("--redis-burst must be positive.")

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    admin_key = os.environ.get("SABIROUTE_ADMIN_KEY")
    if not database_url:
        raise SystemExit("DATABASE_URL is unset.")
    if not admin_key:
        raise SystemExit("SABIROUTE_ADMIN_KEY is unset.")

    database = make_url(database_url).set(
        drivername="postgresql+psycopg",
        host=args.postgres_host,
    )
    database_url_for_process = str(database)
    password = None if args.redis_no_auth else os.environ.get("REDIS_PASSWORD") or None
    escaped_password = quote(password, safe="") if password else None
    auth = f":{escaped_password}@" if escaped_password else ""
    redis_url = f"redis://{auth}{args.redis_host}:{args.redis_port}/0"

    engine = create_engine(database, connect_args={"connect_timeout": 5})
    project_id = f"phase10-smoke-{uuid4().hex}"
    key_ids: list[str] = []
    try:
        with engine.connect() as connection:
            db_name, role = connection.execute(
                text("SELECT current_database(), current_user")
            ).one()
        print(f"PostgreSQL reachable: database={db_name}, role={role}")

        _burst_key_id, admitted = asyncio.run(
            check_atomic_redis_burst(
                args.redis_host,
                args.redis_port,
                password,
                args.redis_burst,
            )
        )
        print(f"Redis atomic Lua burst: {admitted}/{args.redis_burst} admitted")

        os.environ["DATABASE_URL"] = database_url_for_process
        os.environ["REDIS_URL"] = redis_url
        os.environ["REDIS_HOST"] = args.redis_host
        os.environ["REDIS_PORT"] = str(args.redis_port)
        if password:
            os.environ["REDIS_PASSWORD"] = password
        else:
            os.environ.pop("REDIS_PASSWORD", None)

        app = create_app()
        with TestClient(app) as client:
            stub = LocalCompletionStub()
            app.state.gateway.client = stub
            admin_headers = {"Authorization": f"Bearer {admin_key}"}

            credentials: dict[str, tuple[str, str]] = {}
            for name in (
                "rate-limited",
                "rate-isolated",
                "daily-budget",
                "monthly-budget",
                "concurrent-budget",
                "priced-budget",
                "unknown-price-budget",
                "fallback-budget",
                "window-reset",
            ):
                created = client.post(
                    "/admin/api-keys",
                    headers=admin_headers,
                    json={"project_id": project_id, "name": f"phase10-{name}"},
                )
                if created.status_code != 201:
                    raise RuntimeError("Could not create temporary Phase 10 API key.")
                credentials[name] = (created.json()["id"], created.json()["api_key"])
                key_ids.append(created.json()["id"])

            first_id, first_key = credentials["rate-limited"]
            second_id, second_key = credentials["rate-isolated"]

            limit = client.put(
                f"/admin/api-keys/{first_id}/rate-limit",
                headers=admin_headers,
                json={"requests_per_minute": 1, "burst_capacity": 1},
            )
            if limit.status_code != 200:
                raise RuntimeError("Could not configure the temporary API-key rate limit.")

            limited_headers = {"Authorization": f"Bearer {first_key}"}
            first_request = client.post(
                "/v1/chat/completions",
                headers=limited_headers,
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            second_request = client.post(
                "/v1/chat/completions",
                headers=limited_headers,
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            isolated_request = client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {second_key}"},
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            usage = client.get(
                f"/admin/api-keys/{first_id}/usage?limit=10&offset=0",
                headers=admin_headers,
            )
            if first_request.status_code != 404:
                raise RuntimeError("First limited request did not pass admission.")
            if second_request.status_code != 429:
                raise RuntimeError("Second limited request was not rejected with HTTP 429.")
            if second_request.headers.get("Retry-After") is None:
                raise RuntimeError("Rate-limit rejection omitted Retry-After.")
            if isolated_request.status_code != 404:
                raise RuntimeError("A second API key did not have an isolated bucket.")
            if usage.status_code != 200 or usage.json().get("total") != 2:
                raise RuntimeError("Durable per-key usage history was not recorded.")
            if first_key in usage.text or second_key in usage.text or "key_hash" in usage.text:
                raise RuntimeError("Usage endpoint exposed credential material.")
            if client.get(
                f"/admin/api-keys/{first_id}/rate-limit", headers=admin_headers
            ).json().get("requests_per_minute") != 1:
                raise RuntimeError("Admin rate-limit inspection failed.")

            reservation = estimate_input_tokens(SMOKE_MESSAGES) + 16
            daily_id, daily_key = credentials["daily-budget"]
            monthly_id, monthly_key = credentials["monthly-budget"]
            daily_config = client.put(
                f"/admin/api-keys/{daily_id}/budget",
                headers=admin_headers,
                json={"daily_tokens": reservation, "monthly_tokens": reservation * 4},
            )
            monthly_config = client.put(
                f"/admin/api-keys/{monthly_id}/budget",
                headers=admin_headers,
                json={"daily_tokens": reservation * 4, "monthly_tokens": reservation},
            )
            if daily_config.status_code != 200 or monthly_config.status_code != 200:
                raise RuntimeError("Could not configure daily/monthly smoke budgets.")

            def budget_request(key: str, model: str = "sabiroute-openai"):
                return client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": model,
                        "messages": SMOKE_MESSAGES,
                        "max_tokens": 16,
                    },
                )

            daily_first = budget_request(daily_key)
            daily_second = budget_request(daily_key)
            monthly_first = budget_request(monthly_key)
            monthly_second = budget_request(monthly_key)
            if daily_first.status_code != 200 or daily_second.status_code != 429:
                raise RuntimeError("Daily token budget enforcement failed.")
            if monthly_first.status_code != 200 or monthly_second.status_code != 429:
                raise RuntimeError("Monthly token budget enforcement failed.")
            if budget_request(second_key).status_code != 200:
                raise RuntimeError("Per-key budget isolation failed.")

            updated_monthly = client.put(
                f"/admin/api-keys/{monthly_id}/budget",
                headers=admin_headers,
                json={"daily_tokens": reservation * 4, "monthly_tokens": reservation * 2},
            )
            inspected_monthly = client.get(
                f"/admin/api-keys/{monthly_id}/budget", headers=admin_headers
            )
            removed_monthly = client.delete(
                f"/admin/api-keys/{monthly_id}/budget", headers=admin_headers
            )
            if (
                updated_monthly.status_code != 200
                or inspected_monthly.status_code != 200
                or inspected_monthly.json()["budget"]["monthly_tokens"] != reservation * 2
                or removed_monthly.status_code != 200
                or client.get(
                    f"/admin/api-keys/{monthly_id}/budget", headers=admin_headers
                ).json()["budget"] is not None
            ):
                raise RuntimeError("Admin budget create/update/inspect/remove failed.")
            removed_rate = client.delete(
                f"/admin/api-keys/{first_id}/rate-limit", headers=admin_headers
            )
            if removed_rate.status_code != 200:
                raise RuntimeError("Admin rate-limit removal failed.")

            window_id, _window_key = credentials["window-reset"]
            if client.put(
                f"/admin/api-keys/{window_id}/budget",
                headers=admin_headers,
                json={"daily_tokens": 100, "monthly_tokens": 150},
            ).status_code != 200:
                raise RuntimeError("Could not configure window-reset budget.")
            budget_store = app.state.gateway.key_store
            day_one = datetime(2026, 3, 1, 12, tzinfo=UTC)
            day_two = datetime(2026, 3, 2, 12, tzinfo=UTC)
            month_two = datetime(2026, 4, 1, 12, tzinfo=UTC)
            if budget_store.reserve_budget(window_id, "window-1", 100, None, day_one):
                raise RuntimeError("Daily window rejected an exact-limit reservation.")
            if budget_store.reserve_budget(window_id, "window-2", 1, None, day_one) != (
                "daily_tokens_exceeded"
            ):
                raise RuntimeError("Daily token window did not reset/enforce correctly.")
            if budget_store.reserve_budget(window_id, "window-3", 50, None, day_two):
                raise RuntimeError("Daily window did not reset on the next UTC day.")
            if budget_store.reserve_budget(window_id, "window-4", 1, None, day_two) != (
                "monthly_tokens_exceeded"
            ):
                raise RuntimeError("Monthly token window did not enforce across days.")
            if budget_store.reserve_budget(window_id, "window-5", 100, None, month_two):
                raise RuntimeError("Monthly token window did not reset on the next UTC month.")

            concurrent_id, concurrent_key = credentials["concurrent-budget"]
            if client.put(
                f"/admin/api-keys/{concurrent_id}/budget",
                headers=admin_headers,
                json={"daily_tokens": reservation},
            ).status_code != 200:
                raise RuntimeError("Could not configure concurrent token budget.")
            with ThreadPoolExecutor(max_workers=8) as pool:
                responses = list(pool.map(lambda _: budget_request(concurrent_key), range(8)))
            if sum(response.status_code == 200 for response in responses) != 1:
                raise RuntimeError("Concurrent PostgreSQL token reservations were not atomic.")

            priced_id, priced_key = credentials["priced-budget"]
            model = app.state.gateway.registry.get("sabiroute-openai")
            app.state.gateway.registry._deployments["sabiroute-openai"] = replace(
                model,
                input_cost_per_million_tokens=Decimal("1"),
                output_cost_per_million_tokens=Decimal("2"),
            )
            price_estimate = (
                Decimal(reservation - 16) + Decimal(16) * Decimal(2)
            ) / Decimal(1_000_000)
            price_cap = price_estimate / Decimal(2)
            if client.put(
                f"/admin/api-keys/{priced_id}/budget",
                headers=admin_headers,
                json={"daily_cost_usd": str(price_cap)},
            ).status_code != 200:
                raise RuntimeError("Could not configure priced budget.")
            priced = budget_request(priced_key)
            if priced.status_code != 429 or priced.json()["error"]["type"] != "budget_exceeded":
                raise RuntimeError("Monetary budget enforcement with explicit pricing failed.")

            unknown_id, unknown_key = credentials["unknown-price-budget"]
            if client.put(
                f"/admin/api-keys/{unknown_id}/budget",
                headers=admin_headers,
                json={"daily_cost_usd": "1.00"},
            ).status_code != 200:
                raise RuntimeError("Could not configure unknown-price budget.")
            unknown_price = budget_request(unknown_key, model="sabiroute-gemini")
            if (
                unknown_price.status_code != 503
                or unknown_price.json()["error"]["type"] != "budget_pricing_unavailable"
            ):
                raise RuntimeError("Unknown pricing did not fail closed as unknown.")

            fallback_id, fallback_key = credentials["fallback-budget"]
            if client.put(
                f"/admin/api-keys/{fallback_id}/budget",
                headers=admin_headers,
                json={"daily_tokens": 1000},
            ).status_code != 200:
                raise RuntimeError("Could not configure fallback budget.")
            stub.fail_once = True
            before_fallback = len(stub.calls)
            fallback = budget_request(fallback_key, model="fast")
            fallback_usage = client.get(
                f"/admin/api-keys/{fallback_id}/usage?limit=10&offset=0",
                headers=admin_headers,
            )
            if fallback.status_code != 200 or len(stub.calls) - before_fallback != 2:
                raise RuntimeError("Budgeted fallback did not complete over two attempts.")
            if fallback_usage.status_code != 200 or fallback_usage.json().get("total") != 1:
                raise RuntimeError("Fallback was not stored as one logical request.")
            if fallback_usage.json()["items"][0]["reserved_tokens"] != reservation:
                raise RuntimeError("Fallback changed the single logical token reservation.")

            inspected = client.get(
                f"/admin/api-keys/{daily_id}/budget",
                headers=admin_headers,
            )
            if inspected.status_code != 200 or inspected.json()["usage"]["daily"]["tokens"] != 8:
                raise RuntimeError("Admin budget usage inspection failed.")

        with engine.connect() as connection:
            stored_hashes = connection.execute(
                text("SELECT key_hash FROM sabiroute_api_keys WHERE project_id = :project_id"),
                {"project_id": project_id},
            ).scalars().all()
        expected_hashes = {
            hashlib.sha256(secret.encode()).hexdigest()
            for _, secret in credentials.values()
        }
        if set(stored_hashes) != expected_hashes:
            raise RuntimeError("PostgreSQL key persistence did not contain only hashes.")
        durable_store = PostgresApiKeyStore(database_url_for_process)
        persisted_events, persisted_count = durable_store.list_usage_events(
            credentials["daily-budget"][0], limit=10, offset=0
        )
        if persisted_count != 2 or len(persisted_events) != 2:
            raise RuntimeError("Usage history did not persist after store restart.")
        durable_store.close()
        print(
            "Rate limits, daily/monthly budgets, concurrent reservations, pricing, "
            "fallback accounting, and PostgreSQL restart persistence: PASS"
        )
    finally:
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "DELETE FROM sabiroute_budget_reservations "
                        "WHERE key_id IN (SELECT key_id FROM sabiroute_api_keys "
                        "WHERE project_id = :project_id)"
                    ),
                    {"project_id": project_id},
                )
                connection.execute(
                    text(
                        "DELETE FROM sabiroute_api_key_budgets "
                        "WHERE key_id IN (SELECT key_id FROM sabiroute_api_keys "
                        "WHERE project_id = :project_id)"
                    ),
                    {"project_id": project_id},
                )
                connection.execute(
                    text(
                        "DELETE FROM sabiroute_request_usage "
                        "WHERE project_id = :project_id"
                    ),
                    {"project_id": project_id},
                )
                connection.execute(
                    text(
                        "DELETE FROM sabiroute_api_key_rate_limits "
                        "WHERE key_id IN (SELECT key_id FROM sabiroute_api_keys "
                        "WHERE project_id = :project_id)"
                    ),
                    {"project_id": project_id},
                )
                connection.execute(
                    text("DELETE FROM sabiroute_api_keys WHERE project_id = :project_id"),
                    {"project_id": project_id},
                )
        except Exception:
            pass
        if key_ids:
            async def cleanup_redis() -> None:
                cleanup_client = Redis(
                    host=args.redis_host,
                    port=args.redis_port,
                    password=password,
                    decode_responses=True,
                    socket_connect_timeout=3,
                )
                try:
                    await cleanup_client.delete(
                        *(f"sabiroute:rate:v1:{key_id}" for key_id in key_ids)
                    )
                finally:
                    await cleanup_client.aclose()

            try:
                asyncio.run(cleanup_redis())
            except Exception as exc:
                print(f"Warning: Redis smoke-key cleanup failed: {type(exc).__name__}")
        engine.dispose()


if __name__ == "__main__":
    main()
