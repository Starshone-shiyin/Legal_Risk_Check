"""Check evidence enrichment field stability for coverage diagnostics."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


VERSION = "0.4.7.4.1"

DEFAULT_COVERAGE_REPORT_PATH = Path("tests/evidence_coverage_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_enrichment_hardening_report.json")

REQUIRED_EVIDENCE_FIELDS = (
    "content_preview",
    "functional_type",
    "functional_type_confidence",
    "functional_type_matched_rule",
    "enrichment_status",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_items(coverage_report: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for case in coverage_report.get("cases") or []:
        for evidence in case.get("final_evidence") or []:
            if isinstance(evidence, dict):
                items.append({"case_id": case.get("case_id"), **evidence})
    return items


def missing_field_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for item in items:
        for field in REQUIRED_EVIDENCE_FIELDS:
            if item.get(field) in (None, "", []):
                counts[field] += 1
    return dict(sorted(counts.items()))


def unmatched_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if item.get("enrichment_status") != "matched"
    ]


def build_report(coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    items = evidence_items(coverage_report)
    unmatched = unmatched_items(items)
    missing_fields = missing_field_summary(items)
    matched = len(items) - len(unmatched)
    return {
        "version": VERSION,
        "scope": "offline evidence enrichment hardening",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
        },
        "summary": {
            "total_final_evidence": len(items),
            "matched_evidence": matched,
            "unmatched_evidence": len(unmatched),
            "matched_ratio": round(matched / len(items), 3) if items else 1.0,
            "missing_required_field_counts": missing_fields,
            "field_stability_passed": not unmatched and not missing_fields,
        },
        "unmatched_items": unmatched,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check evidence enrichment hardening.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-missing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.coverage_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Evidence enrichment hardening completed: "
        f"{summary['matched_evidence']}/{summary['total_final_evidence']} matched, "
        f"{summary['unmatched_evidence']} unmatched"
    )
    if args.fail_on_missing and not summary["field_stability_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
