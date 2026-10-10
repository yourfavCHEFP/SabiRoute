from __future__ import annotations

import time
from dataclasses import dataclass

import litellm
from litellm import exceptions as litellm_exceptions

from .base import ProviderDeployment


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    deployment: str
    healthy: bool
    latency_ms: float | None = None
    error_type: str | None = None
    error_message: str | None = None


class ProviderHealthChecker:
    """
    Performs active smoke tests against LiteLLM deployments.

    No secrets are logged.
    """

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    def check(
        self,
        deployment: ProviderDeployment,
    ) -> HealthCheckResult:
        started = time.perf_counter()

        try:
            response = litellm.completion(
                model=deployment.model,
                messages=[
                    {
                        "role": "user",
                        "content": "Reply with exactly: SABIROUTE_HEALTH_OK",
                    }
                ],
                timeout=self.timeout_seconds,
                **deployment.as_litellm_params(),
            )

            _ = response

            latency_ms = (time.perf_counter() - started) * 1000

            return HealthCheckResult(
                deployment=deployment.name,
                healthy=True,
                latency_ms=round(latency_ms, 2),
            )

        except litellm_exceptions.AuthenticationError as exc:
            return self._failure(
                deployment,
                "authentication_error",
                exc,
                started,
            )

        except litellm_exceptions.RateLimitError as exc:
            return self._failure(
                deployment,
                "rate_limit",
                exc,
                started,
            )

        except litellm_exceptions.Timeout as exc:
            return self._failure(
                deployment,
                "timeout",
                exc,
                started,
            )

        except litellm_exceptions.APIError as exc:
            return self._failure(
                deployment,
                "api_error",
                exc,
                started,
            )

        except Exception as exc:
            return self._failure(
                deployment,
                "unknown_error",
                exc,
                started,
            )

    @staticmethod
    def _failure(
        deployment: ProviderDeployment,
        error_type: str,
        error: Exception,
        started: float,
    ) -> HealthCheckResult:
        latency_ms = (time.perf_counter() - started) * 1000

        return HealthCheckResult(
            deployment=deployment.name,
            healthy=False,
            latency_ms=round(latency_ms, 2),
            error_type=error_type,
            error_message=str(error)[:500],
        )
