"""Read-only audit and sanitized export of SabiRoute routing telemetry."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import dotenv_values

from sabiroute.intelligence.dataset import (
    DatasetExportBlocked,
    read_usage_events,
    readiness_report,
    write_diagnostic_export,
    write_training_candidate_export,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument(
        "--export",
        type=Path,
        help=(
            "write a readiness-gated training candidate JSON for human review; "
            "refuses BLOCKED data and never authorizes training"
        ),
    )
    export_group.add_argument(
        "--diagnostic-export",
        type=Path,
        help=(
            "write a diagnostic-only JSON envelope; quarantined records and reasons "
            "remain visible and must not be used for training"
        ),
    )
    parser.add_argument(
        "--low-sample-threshold",
        type=int,
        help="optional caller-chosen descriptive threshold; none is assumed by default",
    )
    args = parser.parse_args()
    config = {**dotenv_values(".env"), **os.environ}
    database_url = config.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL is required; no connection value will be displayed")

    events = read_usage_events(str(database_url))
    assessment = readiness_report(
        events, low_sample_threshold=args.low_sample_threshold
    )
    report = assessment["audit"]
    report["time_split"] = assessment["time_split"]
    report["phase13_readiness"] = assessment["readiness"]
    exit_code = 0

    if args.export is not None:
        try:
            payload = write_training_candidate_export(
                events, args.export
            )
        except DatasetExportBlocked as exc:
            report["export"] = {
                "type": "training_candidate_for_human_review",
                "status": "BLOCKED",
                "path_written": False,
                "blockers": exc.readiness["blockers"],
                "training_authorized": False,
            }
            exit_code = 2
        else:
            report["export"] = {
                "type": payload["export_type"],
                "status": payload["readiness_status"],
                "path": str(args.export),
                "records": len(payload["records"]),
                "training_authorized": False,
            }
    elif args.diagnostic_export is not None:
        payload = write_diagnostic_export(
            events, args.diagnostic_export
        )
        report["export"] = {
            "type": payload["export_type"],
            "status": "DIAGNOSTIC_ONLY",
            "path": str(args.diagnostic_export),
            "records": len(payload["records"]),
            "quarantined_records": sum(
                row["disposition"] == "quarantined" for row in payload["records"]
            ),
            "training_authorized": False,
        }
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
