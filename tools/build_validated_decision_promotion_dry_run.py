"""Build a validated manual-review promotion dry run.

Only proposed decisions with decision_status=completed and validation_status=valid
are promotion candidates. The tool does not overwrite the original schema and
does not modify retrieval, rerank, prompts, anchors, risk rules, eval cases,
hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_action_candidates import candidates_for_record
from tools.check_evidence_alignment import normalize_text


VERSION = "0.4.7.7.4"

DEFAULT_PROPOSED_SCHEMA_PATH = Path("tests/proposed_manual_review_decision_schema.json")
DEFAULT_PROPOSED_VALIDATION_PATH = Path("tests/proposed_manual_review_decision_validation_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/validated_decision_promotion_dry_run_report.json")


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def case_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        normalize_text(item.get("case_id")): item
        for item in items
        if isinstance(item, dict) and normalize_text(item.get("case_id"))
    }


def promotion_candidate(record: dict[str, Any], validation_case: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("decision_status") != "completed":
        return None
    if validation_case.get("validation_status") != "valid":
        return None
    actions = [
        item
        for item in candidates_for_record(record, validation_case)
        if item.get("readiness") == "ready_from_valid_decision"
    ]
    reviewer_decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    return {
        "case_id": normalize_text(record.get("case_id")),
        "reviewer": reviewer_decision.get("reviewer") or "",
        "reviewed_at": reviewer_decision.get("reviewed_at") or "",
        "decision": reviewer_decision.get("decision") or "",
        "confirmed_root_causes": reviewer_decision.get("confirmed_root_causes") or [],
        "confirmed_follow_up_actions": reviewer_decision.get("confirmed_follow_up_actions") or [],
        "ready_action_candidates": actions,
    }


def build_summary(candidates: list[dict[str, Any]], validation_report: dict[str, Any]) -> dict[str, Any]:
    action_counts = Counter()
    root_counts = Counter()
    ready_action_count = 0
    for candidate in candidates:
        for root in candidate.get("confirmed_root_causes") or []:
            root_counts[root] += 1
        for action in candidate.get("ready_action_candidates") or []:
            ready_action_count += 1
            action_counts[action.get("action_type")] += 1
    validation_summary = validation_report.get("summary") or {}
    return {
        "promotion_candidates": len(candidates),
        "ready_action_candidates": ready_action_count,
        "valid_records": validation_summary.get("valid_records", 0),
        "invalid_records": validation_summary.get("invalid_records", 0),
        "pending_records": validation_summary.get("pending_records", 0),
        "confirmed_root_cause_summary": dict(sorted(root_counts.items())),
        "ready_action_type_summary": dict(sorted(action_counts.items())),
    }


def build_report(
    proposed_schema_path: Path = DEFAULT_PROPOSED_SCHEMA_PATH,
    proposed_validation_path: Path = DEFAULT_PROPOSED_VALIDATION_PATH,
) -> dict[str, Any]:
    proposed_schema = load_json(proposed_schema_path)
    validation_report = load_json(proposed_validation_path)
    validations = case_map(validation_report.get("cases") or [])
    candidates = []
    for record in proposed_schema.get("decision_records") or []:
        if not isinstance(record, dict):
            continue
        candidate = promotion_candidate(record, validations.get(normalize_text(record.get("case_id"))) or {})
        if candidate:
            candidates.append(candidate)
    candidates = sorted(candidates, key=lambda item: (item.get("case_id") or ""))
    return {
        "version": VERSION,
        "scope": "offline validated decision promotion dry run",
        "inputs": {
            "proposed_decision_schema": str(proposed_schema_path),
            "proposed_decision_schema_version": proposed_schema.get("version"),
            "proposed_validation_report": str(proposed_validation_path),
            "proposed_validation_report_version": validation_report.get("version"),
        },
        "promotion_policy": {
            "requires_completed_decision": True,
            "requires_valid_validation_status": True,
            "overwrite_original_schema": "disallowed",
            "main_flow_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
        },
        "summary": build_summary(candidates, validation_report),
        "promotion_candidates": candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build validated decision promotion dry-run report.")
    parser.add_argument("--proposed-schema", type=Path, default=DEFAULT_PROPOSED_SCHEMA_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_PROPOSED_VALIDATION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.proposed_schema, args.validation_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Validated decision promotion dry run built: "
        f"{summary['promotion_candidates']} promotion candidates, "
        f"{summary['ready_action_candidates']} ready actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
