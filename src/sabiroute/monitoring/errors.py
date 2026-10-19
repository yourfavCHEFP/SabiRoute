from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ErrorRecord:
    category: str
    model: str
    message: str
    timestamp: datetime


@dataclass
class ErrorTracker:
    records: list[ErrorRecord] = field(default_factory=list)

    def record(
        self,
        category: str,
        model: str,
        message: str,
    ) -> None:
        self.records.append(
            ErrorRecord(
                category=category,
                model=model,
                message=message,
                timestamp=datetime.now(UTC),
            )
        )

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}

        for record in self.records:
            result[record.category] = result.get(record.category, 0) + 1

        return result
