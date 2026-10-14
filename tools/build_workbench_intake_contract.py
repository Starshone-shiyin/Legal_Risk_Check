"""Build the manual-review workbench intake contract.

The contract defines which workbench fields may be imported and how reviewer
input is interpreted. It does not import reviewer decisions, overwrite the
decision schema, or modify retrieval, rerank, prompts, anchors, risk rules,
eval cases, hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_decision_schema import (
    ALLOWED_DECISIONS,
    ALLOWED_FOLLOW_UP_ACTIONS,
    ALLOWED_ROOT_CAUSES,
    PROHIBITED_CHANGE_TARGETS,
)
from tools.export_manual_review_workbench import CSV_FIELDS


VERSION = "0.4.7.7.0"

DEFAULT_OUTPUT_PATH = Path("tests/manual_review_intake_contract_report.json")

IMPORTABLE_REVIEWER_FIELDS = [
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

READ_ONLY_CONTEXT_FIELDS = [
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
]

REQUIRED_FOR_COMPLETED = [
    "reviewer",
    "reviewed_at",
    "decision",
    "rationale",
]

LIST_FIELDS = [
    "confirmed_root_causes",
    "rejected_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
]

BOOLEAN_FIELDS = ["fixture_candidate"]

DATE_FORMAT = "YYYY-MM-DD or YYYY-MM-DD HH:MM[:SS]"
LIST_DELIMITER = "|"


def build_contract() -> dict[str, Any]:
    return {
        "version": VERSION,
        "scope": "manual review workbench intake contract",
        "allowed_input_formats": ["csv", "json_workbench"],
        "case_alignment": {
            "key": "case_id",
            "unknown_case": "reject_row",
            "duplicate_case": "reject_all_duplicate_rows",
            "missing_case_id": "reject_row",
        },
        "field_policy": {
            "csv_fields": CSV_FIELDS,
            "read_only_context_fields": READ_ONLY_CONTEXT_FIELDS,
            "importable_reviewer_fields": IMPORTABLE_REVIEWER_FIELDS,
            "required_for_completed": REQUIRED_FOR_COMPLETED,
            "list_fields": LIST_FIELDS,
            "boolean_fields": BOOLEAN_FIELDS,
            "list_delimiter": LIST_DELIMITER,
            "reviewed_at_format": DATE_FORMAT,
        },
        "allowed_values": {
            "decision": ALLOWED_DECISIONS,
            "confirmed_root_causes": ALLOWED_ROOT_CAUSES,
            "rejected_root_causes": ALLOWED_ROOT_CAUSES,
            "confirmed_follow_up_actions": ALLOWED_FOLLOW_UP_ACTIONS,
            "fixture_candidate": ["true", "false", True, False],
        },
        "prohibited_change_targets": PROHIBITED_CHANGE_TARGETS,
        "write_policy": {
            "overwrite_original_decision_schema": "disallowed",
            "output_proposed_schema_only": True,
            "main_flow_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
            "risk_rule_mutation": "disallowed",
        },
        "validation_flow": [
            "parse_workbench_input",
            "align_case_id_with_original_schema",
            "build_proposed_decision_schema",
            "run_decision_diff_audit",
            "run_proposed_decision_validation",
            "run_promotion_dry_run",
        ],
    }


def build_report() -> dict[str, Any]:
    contract = build_contract()
    return {
        "version": VERSION,
        "scope": "offline workbench intake contract report",
        "summary": {
            "importable_reviewer_fields": len(IMPORTABLE_REVIEWER_FIELDS),
            "read_only_context_fields": len(READ_ONLY_CONTEXT_FIELDS),
            "allowed_decisions": len(ALLOWED_DECISIONS),
            "allowed_root_causes": len(ALLOWED_ROOT_CAUSES),
            "allowed_follow_up_actions": len(ALLOWED_FOLLOW_UP_ACTIONS),
            "prohibited_change_targets": len(PROHIBITED_CHANGE_TARGETS),
        },
        "contract": contract,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build workbench intake contract report.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Workbench intake contract built: "
        f"{summary['importable_reviewer_fields']} importable fields, "
        f"{summary['read_only_context_fields']} read-only fields"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
