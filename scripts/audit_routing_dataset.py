"""Read-only audit and sanitized export of SabiRoute routing telemetry."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from sabiroute.intelligence.dataset import (
    FEATURE_SCHEMA_VERSION,
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
    parser.add_argument(
        "--exclude-pre-instrumentation",
        action="store_true",
        help=(
            "scope the audit to rows carrying a stored feature schema version, "
            "reporting how many pre-instrumentation rows were excluded; excluded "
            "rows are named in the report, never silently dropped, and default "
            "behaviour is unchanged"
        ),
    )
    args = parser.parse_args()
    config = {**dotenv_values(".env"), **os.environ}
    database_url = config.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL is required; no connection value will be displayed")

    all_events = read_usage_events(str(database_url))
    scope: dict[str, Any] = {
        "filter": "exclude_pre_instrumentation",
        "applied": False,
        "rows_read": len(all_events),
        "rows_included": len(all_events),
        "rows_excluded": 0,
        "required_feature_schema_version": None,
        "excluded_request_ids": [],
        "reason": None,
    }
    events = all_events
    if args.exclude_pre_instrumentation:
        # Phase 13.1's feature contract is the current schema version. A row
        # stored before feature instrumentation existed cannot supply it and so
        # can never be part of a Phase 13 dataset. Such rows are excluded by an
        # explicit, reported scope decision rather than by weakening the
        # readiness gate: the gate's strictness and its verdict for any given
        # input remain unchanged.
        def conforms(event: dict[str, Any]) -> bool:
            return event.get("feature_schema_version") == FEATURE_SCHEMA_VERSION

        events = [event for event in all_events if conforms(event)]
        excluded = [event for event in all_events if not conforms(event)]
        scope.update(
            applied=True,
            rows_included=len(events),
            rows_excluded=len(excluded),
            required_feature_schema_version=FEATURE_SCHEMA_VERSION,
            excluded_request_ids=sorted(
                str(event.get("request_id")) for event in excluded
            ),
            reason=(
                "stored feature_schema_version is absent or predates the current "
                "feature contract, so the row cannot satisfy Phase 13's required "
                "temporal provenance"
            ),
        )
    assessment = readiness_report(
        events, low_sample_threshold=args.low_sample_threshold
    )
    report = assessment["audit"]
    report["time_split"] = assessment["time_split"]
    report["phase13_readiness"] = assessment["readiness"]
    report["audit_scope"] = scope
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
