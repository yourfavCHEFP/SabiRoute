"""Provider-agnostic budget estimation and price quote helpers."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from ..providers.base import ProviderDeployment


class UnsupportedBudgetRequest(ValueError):
    """The request shape cannot be safely estimated for budget admission."""


def estimate_input_tokens(messages: list[dict[str, Any]]) -> int:
    """Return a conservative UTF-8 byte upper estimate for text chat messages.

    This intentionally supports text-only messages. JSON byte length upper
    bounds the token count for byte-oriented tokenizers; per-message framing
    allowance covers role and chat-template framing. Multimodal and custom
    message structures fail closed instead of being guessed.
    """
    if not messages:
        raise UnsupportedBudgetRequest("At least one message is required.")
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise UnsupportedBudgetRequest(
                "Budgeted requests currently require text-only messages."
            )
        if any(
            not isinstance(value, (str, int, float, bool, type(None)))
            for value in message.values()
        ):
            raise UnsupportedBudgetRequest("Budgeted message fields must be scalar text metadata.")
    try:
        serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise UnsupportedBudgetRequest("Message content cannot be safely estimated.") from exc
    return len(serialized.encode("utf-8")) + len(messages) * 16 + 4


def estimated_cost_usd(
    deployments: list[ProviderDeployment],
    input_tokens: int,
    max_output_tokens: int,
) -> Decimal | None:
    """Quote worst-case candidate cost from explicit per-million-token prices."""
    quotes: list[Decimal] = []
    for deployment in deployments:
        input_price = deployment.input_cost_per_million_tokens
        output_price = deployment.output_cost_per_million_tokens
        if input_price is None or output_price is None:
            return None
        try:
            input_price = Decimal(str(input_price))
            output_price = Decimal(str(output_price))
        except Exception:
            return None
        if not input_price.is_finite() or not output_price.is_finite():
            return None
        if input_price < 0 or output_price < 0:
            return None
        quotes.append(
            (
                Decimal(input_tokens) * input_price
                + Decimal(max_output_tokens) * output_price
            )
            / Decimal(1_000_000)
        )
    return max(quotes) if quotes else None
