"""Export an offline manual-review workbench.

The workbench gives reviewers a compact JSON/CSV view of pending decisions.
It does not write reviewer conclusions, mutate the decision schema, patch eval
cases, or change retrieval, rerank, prompts, anchors, or risk rules.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_evidence_alignment import normalize_text


VERSION = "0.4.7.6.0"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_CSV_OUTPUT_PATH = Path("tests/evidence_manual_review_workbench.csv")

CSV_FIELDS = [
    "case_id",
    "priority_score",
    "risk_level",
    "expected_domains",
    "queue_tags",
    "issue_types",
    "suggested_root_causes",
    "suggested_follow_up_actions",
    "review_question_count",
    "missing_final_expected_count",
    "missing_scenario_core_count",
    "lost_evidence_count",
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


def pipe_join(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    return " | ".join(str(value) for value in values if value not in (None, "", []))


def evidence_count(record: dict[str, Any], key: str) -> int:
    evidence_context = record.get("evidence_context") if isinstance(record.get("evidence_context"), dict) else {}
    value = evidence_context.get(key)
    return len(value) if isinstance(value, list) else 0


def workbench_item(record: dict[str, Any], rank: int) -> dict[str, Any]:
    reviewer_decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    return {
        "rank": rank,
        "case_id": normalize_text(record.get("case_id")),
        "decision_status": normalize_text(record.get("decision_status") or "pending"),
        "priority_score": record.get("priority_score"),
        "risk_level": record.get("risk_level"),
        "expected_domains": record.get("expected_domains") or [],
        "queue_tags": record.get("queue_tags") or [],
        "issue_types": record.get("issue_types") or [],
        "suggested_root_causes": record.get("suggested_root_causes") or [],
        "suggested_follow_up_actions": record.get("suggested_follow_up_actions") or [],
        "suggested_review_questions": record.get("suggested_review_questions") or [],
        "diagnostic_summary": record.get("diagnostic_summary") or {},
        "evidence_context": record.get("evidence_context") or {},
        "evidence_context_counts": {
            "missing_final_expected": evidence_count(record, "missing_final_expected"),
            "missing_scenario_core": evidence_count(record, "missing_scenario_core"),
            "lost_evidence": evidence_count(record, "lost_evidence"),
            "final_evidence": evidence_count(record, "final_evidence"),
        },
        "reviewer_input_template": {
            "reviewer": reviewer_decision.get("reviewer") or "",
            "reviewed_at": reviewer_decision.get("reviewed_at") or "",
            "decision": reviewer_decision.get("decision") or "",
            "confirmed_root_causes": reviewer_decision.get("confirmed_root_causes") or [],
            "rejected_root_causes": reviewer_decision.get("rejected_root_causes") or [],
            "confirmed_follow_up_actions": reviewer_decision.get("confirmed_follow_up_actions") or [],
            "proposed_change_targets": reviewer_decision.get("proposed_change_targets") or [],
            "fixture_candidate": bool(reviewer_decision.get("fixture_candidate") or False),
            "rationale": reviewer_decision.get("rationale") or "",
            "notes": reviewer_decision.get("notes") or "",
        },
    }


def csv_row(item: dict[str, Any]) -> dict[str, Any]:
    template = item.get("reviewer_input_template") or {}
    counts = item.get("evidence_context_counts") or {}
    return {
        "case_id": item.get("case_id"),
        "priority_score": item.get("priority_score"),
        "risk_level": item.get("risk_level"),
        "expected_domains": pipe_join(item.get("expected_domains")),
        "queue_tags": pipe_join(item.get("queue_tags")),
        "issue_types": pipe_join(item.get("issue_types")),
        "suggested_root_causes": pipe_join(item.get("suggested_root_causes")),
        "suggested_follow_up_actions": pipe_join(item.get("suggested_follow_up_actions")),
        "review_question_count": len(item.get("suggested_review_questions") or []),
        "missing_final_expected_count": counts.get("missing_final_expected", 0),
        "missing_scenario_core_count": counts.get("missing_scenario_core", 0),
        "lost_evidence_count": counts.get("lost_evidence", 0),
        "reviewer": template.get("reviewer") or "",
        "reviewed_at": template.get("reviewed_at") or "",
        "decision": template.get("decision") or "",
        "confirmed_root_causes": pipe_join(template.get("confirmed_root_causes")),
        "rejected_root_causes": pipe_join(template.get("rejected_root_causes")),
        "confirmed_follow_up_actions": pipe_join(template.get("confirmed_follow_up_actions")),
        "proposed_change_targets": pipe_join(template.get("proposed_change_targets")),
        "fixture_candidate": str(bool(template.get("fixture_candidate"))).lower(),
        "rationale": template.get("rationale") or "",
        "notes": template.get("notes") or "",
    }


def build_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    queue_counts = Counter()
    root_counts = Counter()
    action_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    high_priority = []

    for item in items:
        for tag in item.get("queue_tags") or []:
            queue_counts[tag] += 1
        for root in item.get("suggested_root_causes") or []:
            root_counts[root] += 1
        for action in item.get("suggested_follow_up_actions") or []:
            action_counts[action] += 1
        for domain in item.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["workbench_items"] += 1
        if item.get("risk_level") == "high" or int(item.get("priority_score") or 0) >= 10:
            high_priority.append(item.get("case_id"))

    return {
        "total_workbench_items": len(items),
        "pending_items": sum(1 for item in items if item.get("decision_status") == "pending"),
        "high_priority_items": len(high_priority),
        "queue_summary": dict(sorted(queue_counts.items())),
        "suggested_root_cause_summary": dict(sorted(root_counts.items())),
        "suggested_follow_up_action_summary": dict(sorted(action_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "high_priority_case_ids": high_priority,
    }


def build_report(decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    records = [
        record
        for record in decision_schema.get("decision_records") or []
        if isinstance(record, dict) and normalize_text(record.get("case_id"))
    ]
    records = sorted(records, key=lambda item: (-int(item.get("priority_score") or 0), item.get("case_id") or ""))
    items = [workbench_item(record, rank=index + 1) for index, record in enumerate(records)]
    return {
        "version": VERSION,
        "scope": "offline manual review workbench export",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
        },
        "csv_fields": CSV_FIELDS,
        "summary": build_summary(items),
        "workbench_items": items,
    }


def write_csv(report: dict[str, Any], csv_output_path: Path) -> None:
    csv_output_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in report.get("workbench_items") or []:
            writer.writerow(csv_row(item))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export an offline manual review workbench.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(report, args.csv_output)
    summary = report["summary"]
    print(
        "Manual review workbench exported: "
        f"{summary['total_workbench_items']} items, "
        f"{summary['pending_items']} pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
