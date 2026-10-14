"""Audit differences between original and proposed manual-review decisions.

The audit trail records field-level changes and prohibited targets. It does
not promote decisions, overwrite schemas, patch eval cases, or modify retrieval,
rerank, prompts, anchors, risk rules, hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_decision_schema import PROHIBITED_CHANGE_TARGETS
from tools.check_evidence_alignment import normalize_text


VERSION = "0.4.7.7.2"

DEFAULT_ORIGINAL_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_PROPOSED_SCHEMA_PATH = Path("tests/proposed_manual_review_decision_schema.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_decision_diff_report.json")

TRACKED_FIELDS = [
    "decision_status",
    "reviewer",
    "reviewed_at",
    "decision",
    "confirmed_root_causes",
    "rejected_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
    "fixture_candidate",
    "rationale",
    "notes",
]


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def case_map(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        normalize_text(record.get("case_id")): record
        for record in schema.get("decision_records") or []
        if isinstance(record, dict) and normalize_text(record.get("case_id"))
    }


def field_value(record: dict[str, Any], field: str) -> Any:
    if field == "decision_status":
        return record.get("decision_status")
    reviewer_decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    return reviewer_decision.get(field)


def value_changed(before: Any, after: Any) -> bool:
    return before != after


def target_is_prohibited(target: Any) -> bool:
    text = normalize_text(target).lower()
    return bool(text) and any(prohibited.lower() in text for prohibited in PROHIBITED_CHANGE_TARGETS)


def diff_case(case_id: str, original: dict[str, Any], proposed: dict[str, Any]) -> dict[str, Any] | None:
    changes = []
    for field in TRACKED_FIELDS:
        before = field_value(original, field)
        after = field_value(proposed, field)
        if value_changed(before, after):
            changes.append({
                "field": field,
                "before": before,
                "after": after,
            })
    proposed_targets = field_value(proposed, "proposed_change_targets") or []
    prohibited_targets = [target for target in proposed_targets if target_is_prohibited(target)]
    if not changes and not prohibited_targets:
        return None
    return {
        "case_id": case_id,
        "change_count": len(changes),
        "changes": changes,
        "reviewer": field_value(proposed, "reviewer") or "",
        "reviewed_at": field_value(proposed, "reviewed_at") or "",
        "decision": field_value(proposed, "decision") or "",
        "prohibited_change_targets": prohibited_targets,
        "audit_status": "blocked" if prohibited_targets else "changed",
    }


def build_summary(diff_cases: list[dict[str, Any]], missing_in_proposed: list[str], new_in_proposed: list[str]) -> dict[str, Any]:
    field_counts = Counter()
    decision_counts = Counter()
    blocked = 0
    for item in diff_cases:
        for change in item.get("changes") or []:
            field_counts[change.get("field")] += 1
        if item.get("decision"):
            decision_counts[item.get("decision")] += 1
        if item.get("audit_status") == "blocked":
            blocked += 1
    return {
        "changed_cases": len(diff_cases),
        "blocked_cases": blocked,
        "missing_in_proposed": len(missing_in_proposed),
        "new_in_proposed": len(new_in_proposed),
        "changed_field_summary": dict(sorted(field_counts.items())),
        "decision_summary": dict(sorted(decision_counts.items())),
    }


def build_report(
    original_schema_path: Path = DEFAULT_ORIGINAL_SCHEMA_PATH,
    proposed_schema_path: Path = DEFAULT_PROPOSED_SCHEMA_PATH,
) -> dict[str, Any]:
    original_schema = load_json(original_schema_path)
    proposed_schema = load_json(proposed_schema_path)
    original_by_case = case_map(original_schema)
    proposed_by_case = case_map(proposed_schema)
    missing = sorted(set(original_by_case) - set(proposed_by_case))
    new = sorted(set(proposed_by_case) - set(original_by_case))
    diff_cases = []
    for cid in sorted(set(original_by_case) & set(proposed_by_case)):
        item = diff_case(cid, original_by_case[cid], proposed_by_case[cid])
        if item:
            diff_cases.append(item)
    return {
        "version": VERSION,
        "scope": "offline manual review decision diff audit",
        "inputs": {
            "original_decision_schema": str(original_schema_path),
            "original_decision_schema_version": original_schema.get("version"),
            "proposed_decision_schema": str(proposed_schema_path),
            "proposed_decision_schema_version": proposed_schema.get("version"),
        },
        "summary": build_summary(diff_cases, missing, new),
        "missing_in_proposed": missing,
        "new_in_proposed": new,
        "diff_cases": diff_cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit manual-review decision diffs.")
    parser.add_argument("--original-schema", type=Path, default=DEFAULT_ORIGINAL_SCHEMA_PATH)
    parser.add_argument("--proposed-schema", type=Path, default=DEFAULT_PROPOSED_SCHEMA_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.original_schema, args.proposed_schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review decision diff built: "
        f"{summary['changed_cases']} changed cases, "
        f"{summary['blocked_cases']} blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
