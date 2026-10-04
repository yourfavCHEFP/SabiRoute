from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UsageRecord:
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class UsageTracker:
    records: list[UsageRecord] = field(default_factory=list)

    def record(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        self.records.append(
            UsageRecord(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
        )

    def totals(self) -> dict[str, int]:
        result: dict[str, int] = {}

        for record in self.records:
            result[record.model] = result.get(record.model, 0) + record.total_tokens

        return result
