"""Validate proposed manual-review decisions.

This wraps the existing decision validator for proposed schemas produced by
the intake importer. It does not promote decisions or overwrite the original
schema.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.validate_manual_review_decisions import build_report as build_validation_report


VERSION = "0.4.7.7.3"

DEFAULT_PROPOSED_SCHEMA_PATH = Path("tests/proposed_manual_review_decision_schema.json")
DEFAULT_OUTPUT_PATH = Path("tests/proposed_manual_review_decision_validation_report.json")


def build_report(proposed_schema_path: Path = DEFAULT_PROPOSED_SCHEMA_PATH) -> dict:
    report = build_validation_report(proposed_schema_path)
    return {
        **report,
        "version": VERSION,
        "scope": "offline proposed manual review decision validation",
        "inputs": {
            "proposed_decision_schema": str(proposed_schema_path),
            "proposed_decision_schema_version": report.get("inputs", {}).get("decision_schema_version"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate proposed manual-review decisions.")
    parser.add_argument("--proposed-schema", type=Path, default=DEFAULT_PROPOSED_SCHEMA_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-invalid", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.proposed_schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Proposed manual review validation completed: "
        f"{summary['total_records']} records, "
        f"{summary['invalid_records']} invalid, "
        f"{summary['pending_records']} pending"
    )
    if args.fail_on_invalid and summary["invalid_records"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
