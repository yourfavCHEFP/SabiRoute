"""
SabiRoute Provider Verification

Tests configured LiteLLM deployments without exposing API keys.

Checks:
    1. Configuration/model presence
    2. Environment credential presence
    3. Non-streaming completion
    4. Streaming completion
    5. Latency
    6. Error classification

Usage:

    uv run python scripts/test_providers.py

Optional:

    uv run python scripts/test_providers.py --no-stream
    uv run python scripts/test_providers.py --model sabiroute-groq
    uv run python scripts/test_providers.py --timeout 60

The script never prints API key values.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import litellm
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_PATH = REPORT_DIR / "provider_verification.json"


TEST_PROMPT = "Reply with exactly: SABIROUTE_PROVIDER_TEST_OK"


@dataclass
class ProviderResult:
    model_name: str
    litellm_model: str
    status: str
    credential_status: str
    non_stream_status: str
    stream_status: str
    latency_ms: float | None
    stream_latency_ms: float | None
    error_type: str | None
    error_message: str | None
    timestamp: str


def load_config() -> dict[str, Any]:
    """Load SabiRoute's LiteLLM configuration."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise ValueError("config.yaml must contain a YAML mapping.")

    return config


def required_environment_variable(
    litellm_params: dict[str, Any],
) -> str | None:
    """
    Extract an environment variable from:

        api_key: os.environ/OPENAI_API_KEY

    without exposing the secret itself.
    """

    api_key = litellm_params.get("api_key")

    if not isinstance(api_key, str):
        return None

    prefix = "os.environ/"

    if not api_key.startswith(prefix):
        return None

    return api_key.removeprefix(prefix)


def classify_error(error: Exception) -> str:
    """Classify provider failures into useful routing categories."""

    message = str(error).lower()

    if any(
        value in message
        for value in (
            "401",
            "unauthorized",
            "authentication",
            "invalid api key",
            "invalid_api_key",
            "api key",
        )
    ):
        return "AUTHENTICATION_ERROR"

    if any(
        value in message
        for value in (
            "403",
            "forbidden",
            "permission denied",
            "permission_denied",
        )
    ):
        return "PERMISSION_ERROR"

    if any(
        value in message
        for value in (
            "404",
            "not found",
            "model_not_found",
            "unknown model",
        )
    ):
        return "MODEL_NOT_FOUND"

    if any(
        value in message
        for value in (
            "429",
            "rate limit",
            "rate_limit",
            "too many requests",
            "quota",
        )
    ):
        return "RATE_LIMIT"

    if any(
        value in message
        for value in (
            "timeout",
            "timed out",
            "time out",
        )
    ):
        return "TIMEOUT"

    if any(
        value in message
        for value in (
            "connection",
            "connecterror",
            "connection reset",
            "network",
            "dns",
        )
    ):
        return "CONNECTION_ERROR"

    if any(
        value in message
        for value in (
            "500",
            "502",
            "503",
            "504",
            "server error",
            "internal server error",
            "bad gateway",
            "service unavailable",
        )
    ):
        return "PROVIDER_5XX"

    if any(
        value in message
        for value in (
            "400",
            "bad request",
            "invalid request",
            "invalid_request",
        )
    ):
        return "INVALID_REQUEST"

    return "UNKNOWN_ERROR"


def safe_error_message(error: Exception) -> str:
    """
    Return a sanitized error message.

    We intentionally do not attempt to print environment variables
    or request headers.
    """

    message = str(error).strip()

    if len(message) > 500:
        message = message[:500] + "..."

    return message


def test_non_streaming(
    model: str,
    timeout: int,
) -> tuple[str, float | None, str | None, str | None]:
    """Test a normal non-streaming completion."""

    started = time.perf_counter()

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": TEST_PROMPT,
                }
            ],
            timeout=timeout,
            stream=False,
            num_retries=0,
        )

        elapsed = (time.perf_counter() - started) * 1000

        content = response.choices[0].message.content

        if content is None:
            return (
                "FAIL",
                elapsed,
                "INVALID_RESPONSE",
                "Provider returned no message content.",
            )

        return "PASS", elapsed, None, None

    except Exception as error:
        elapsed = (time.perf_counter() - started) * 1000

        return (
            "FAIL",
            elapsed,
            classify_error(error),
            safe_error_message(error),
        )


def test_streaming(
    model: str,
    timeout: int,
) -> tuple[str, float | None, str | None, str | None]:
    """Test an SSE/streaming completion."""

    started = time.perf_counter()

    try:
        stream = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": TEST_PROMPT,
                }
            ],
            timeout=timeout,
            stream=True,
            num_retries=0,
        )

        chunks = 0

        for chunk in stream:
            chunks += 1

            if chunks >= 1:
                break

        elapsed = (time.perf_counter() - started) * 1000

        if chunks == 0:
            return (
                "FAIL",
                elapsed,
                "EMPTY_STREAM",
                "Provider returned an empty stream.",
            )

        return "PASS", elapsed, None, None

    except Exception as error:
        elapsed = (time.perf_counter() - started) * 1000

        return (
            "FAIL",
            elapsed,
            classify_error(error),
            safe_error_message(error),
        )


def test_deployment(
    deployment: dict[str, Any],
    timeout: int,
    test_stream: bool,
) -> ProviderResult:
    """Run all applicable tests for one configured deployment."""

    model_name = deployment.get("model_name", "unknown")

    params = deployment.get("litellm_params", {})

    if not isinstance(params, dict):
        params = {}

    litellm_model = params.get("model", "")

    credential_variable = required_environment_variable(params)

    if credential_variable:
        credential_present = bool(os.getenv(credential_variable))
    else:
        credential_present = True

    timestamp = datetime.now(UTC).isoformat()

    if not litellm_model:
        return ProviderResult(
            model_name=model_name,
            litellm_model="",
            status="FAIL",
            credential_status="UNKNOWN",
            non_stream_status="SKIPPED",
            stream_status="SKIPPED",
            latency_ms=None,
            stream_latency_ms=None,
            error_type="INVALID_CONFIGURATION",
            error_message="No LiteLLM model configured.",
            timestamp=timestamp,
        )

    if not credential_present:
        return ProviderResult(
            model_name=model_name,
            litellm_model=litellm_model,
            status="SKIPPED",
            credential_status="MISSING",
            non_stream_status="SKIPPED",
            stream_status="SKIPPED",
            latency_ms=None,
            stream_latency_ms=None,
            error_type="MISSING_CREDENTIAL",
            error_message=(
                f"Required environment variable is missing: " f"{credential_variable}"
            ),
            timestamp=timestamp,
        )

    non_stream_status, latency, error_type, error_message = test_non_streaming(
        model=litellm_model,
        timeout=timeout,
    )

    if test_stream and non_stream_status == "PASS":
        (
            stream_status,
            stream_latency,
            stream_error_type,
            stream_error_message,
        ) = test_streaming(
            model=litellm_model,
            timeout=timeout,
        )
    else:
        stream_status = "SKIPPED"
        stream_latency = None
        stream_error_type = None
        stream_error_message = None

    final_error_type = error_type or stream_error_type
    final_error_message = error_message or stream_error_message

    if non_stream_status == "PASS" and (not test_stream or stream_status == "PASS"):
        overall_status = "PASS"
    else:
        overall_status = "FAIL"

    return ProviderResult(
        model_name=model_name,
        litellm_model=litellm_model,
        status=overall_status,
        credential_status="PRESENT",
        non_stream_status=non_stream_status,
        stream_status=stream_status,
        latency_ms=latency,
        stream_latency_ms=stream_latency,
        error_type=final_error_type,
        error_message=final_error_message,
        timestamp=timestamp,
    )


def print_result(result: ProviderResult) -> None:
    """Print one provider result without exposing credentials."""

    status_symbol = {
        "PASS": "✓",
        "FAIL": "✗",
        "SKIPPED": "—",
    }.get(result.status, "?")

    latency = f"{result.latency_ms:.0f} ms" if result.latency_ms is not None else "-"

    print(
        f"{status_symbol} "
        f"{result.model_name:<25} "
        f"{result.status:<8} "
        f"{latency:<10} "
        f"{result.error_type or '-'}"
    )


def write_report(results: list[ProviderResult]) -> None:
    """Write a machine-readable verification report."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "project": "SabiRoute",
        "test_prompt": TEST_PROMPT,
        "results": [asdict(result) for result in results],
        "summary": {
            "total": len(results),
            "passed": sum(result.status == "PASS" for result in results),
            "failed": sum(result.status == "FAIL" for result in results),
            "skipped": sum(result.status == "SKIPPED" for result in results),
        },
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify SabiRoute LiteLLM provider deployments."
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Skip streaming tests.",
    )

    parser.add_argument(
        "--model",
        help="Test only one SabiRoute model alias.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Per-provider request timeout in seconds.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    config = load_config()

    deployments = config.get("model_list", [])

    if not isinstance(deployments, list):
        raise ValueError("model_list must be a YAML list.")

    if args.model:
        deployments = [
            deployment
            for deployment in deployments
            if deployment.get("model_name") == args.model
        ]

        if not deployments:
            raise SystemExit(f"Model alias not found in config: {args.model}")

    print()
    print("=" * 80)
    print("SabiRoute Provider Verification")
    print("=" * 80)
    print()
    print(f"{'Deployment':<25} " f"{'Status':<8} " f"{'Latency':<10} " f"Error")
    print("-" * 80)

    results: list[ProviderResult] = []

    for deployment in deployments:
        result = test_deployment(
            deployment=deployment,
            timeout=args.timeout,
            test_stream=not args.no_stream,
        )

        results.append(result)
        print_result(result)

    print("-" * 80)

    passed = sum(result.status == "PASS" for result in results)
    failed = sum(result.status == "FAIL" for result in results)
    skipped = sum(result.status == "SKIPPED" for result in results)

    print()
    print(
        f"Total: {len(results)} | "
        f"PASS: {passed} | "
        f"FAIL: {failed} | "
        f"SKIPPED: {skipped}"
    )

    write_report(results)

    print()
    print(f"Report written to: {REPORT_PATH}")
    print()


if __name__ == "__main__":
    main()
