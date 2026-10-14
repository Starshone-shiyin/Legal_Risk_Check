"""Build offline examples for manual-review decisions.

The examples teach reviewers how to fill completed, rejected, deferred, and
invalid decisions. They are synthetic examples and are never merged into the
real decision schema.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_decision_schema import (
    ACTION_ANCHOR_GOVERNANCE,
    ACTION_METADATA_QUERY,
    ACTION_NO_ACTION,
    DECISION_CONFIRM_ISSUE,
    DECISION_DEFER,
    DECISION_REJECT_ISSUE,
    DECISION_STATUS_COMPLETED,
    DECISION_STATUS_DEFERRED,
    ROOT_ANCHOR_GOVERNANCE,
    ROOT_METADATA_QUERY,
)
from tools.check_evidence_alignment import normalize_text
from tools.validate_manual_review_decisions import validate_record


VERSION = "0.4.7.6.1"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_decision_examples.json")


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def base_record(decision_schema: dict[str, Any]) -> dict[str, Any]:
    for record in decision_schema.get("decision_records") or []:
        if isinstance(record, dict) and normalize_text(record.get("case_id")):
            result = deepcopy(record)
            result["case_id"] = "example_" + normalize_text(result.get("case_id"))
            return result
    return {
        "case_id": "example_manual_review_case",
        "decision_status": "pending",
        "priority_score": 1,
        "risk_level": "normal",
        "expected_domains": [],
        "queue_tags": [],
        "issue_types": [],
        "suggested_root_causes": [],
        "suggested_follow_up_actions": [],
        "reviewer_decision": {},
    }


def completed_confirmation(record: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(record)
    result["case_id"] = "example_valid_confirm_metadata"
    result["decision_status"] = DECISION_STATUS_COMPLETED
    result["reviewer_decision"] = {
        "reviewer": "example_reviewer",
        "reviewed_at": "2026-05-11",
        "decision": DECISION_CONFIRM_ISSUE,
        "confirmed_root_causes": [ROOT_METADATA_QUERY],
        "rejected_root_causes": [],
        "confirmed_follow_up_actions": [ACTION_METADATA_QUERY],
        "proposed_change_targets": ["knowledge_manifest_metadata", "chunking_quality"],
        "fixture_candidate": False,
        "rationale": "Example: saved diagnostics support a generic metadata/chunking review.",
        "notes": "Synthetic example only; do not merge into real decisions.",
    }
    return result


def completed_rejection(record: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(record)
    result["case_id"] = "example_valid_reject_issue"
    result["decision_status"] = DECISION_STATUS_COMPLETED
    result["reviewer_decision"] = {
        "reviewer": "example_reviewer",
        "reviewed_at": "2026-05-11",
        "decision": DECISION_REJECT_ISSUE,
        "confirmed_root_causes": [],
        "rejected_root_causes": [ROOT_ANCHOR_GOVERNANCE],
        "confirmed_follow_up_actions": [ACTION_NO_ACTION],
        "proposed_change_targets": [],
        "fixture_candidate": False,
        "rationale": "Example: reviewer rejects this diagnostic issue after evidence inspection.",
        "notes": "Synthetic example only; do not merge into real decisions.",
    }
    return result


def deferred_decision(record: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(record)
    result["case_id"] = "example_valid_defer"
    result["decision_status"] = DECISION_STATUS_DEFERRED
    result["reviewer_decision"] = {
        "reviewer": "example_reviewer",
        "reviewed_at": "2026-05-11",
        "decision": DECISION_DEFER,
        "confirmed_root_causes": [],
        "rejected_root_causes": [],
        "confirmed_follow_up_actions": [],
        "proposed_change_targets": [],
        "fixture_candidate": False,
        "rationale": "Example: reviewer needs additional saved evidence context.",
        "notes": "Synthetic example only; do not merge into real decisions.",
    }
    return result


def invalid_prohibited_target(record: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(record)
    result["case_id"] = "example_invalid_prohibited_target"
    result["decision_status"] = DECISION_STATUS_COMPLETED
    result["reviewer_decision"] = {
        "reviewer": "example_reviewer",
        "reviewed_at": "2026-05-11",
        "decision": DECISION_CONFIRM_ISSUE,
        "confirmed_root_causes": [ROOT_ANCHOR_GOVERNANCE],
        "rejected_root_causes": [],
        "confirmed_follow_up_actions": [ACTION_ANCHOR_GOVERNANCE],
        "proposed_change_targets": ["rag_anchor_rules"],
        "fixture_candidate": False,
        "rationale": "Example invalid case: anchor mutation is prohibited in this governance layer.",
        "notes": "Synthetic invalid example; validator should reject this.",
    }
    return result


def build_examples(decision_schema: dict[str, Any]) -> list[dict[str, Any]]:
    seed = base_record(decision_schema)
    return [
        {
            "example_id": "valid_confirm_metadata",
            "expected_validation_status": "valid",
            "record": completed_confirmation(seed),
        },
        {
            "example_id": "valid_reject_issue",
            "expected_validation_status": "valid",
            "record": completed_rejection(seed),
        },
        {
            "example_id": "valid_defer",
            "expected_validation_status": "valid",
            "record": deferred_decision(seed),
        },
        {
            "example_id": "invalid_prohibited_target",
            "expected_validation_status": "invalid",
            "record": invalid_prohibited_target(seed),
        },
    ]


def build_report(decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    examples = build_examples(decision_schema)
    validated_examples = []
    status_summary: dict[str, int] = {}
    mismatches = []

    for example in examples:
        validation = validate_record(example["record"])
        actual = validation.get("validation_status")
        expected = example.get("expected_validation_status")
        status_summary[actual] = status_summary.get(actual, 0) + 1
        if actual != expected:
            mismatches.append({
                "example_id": example.get("example_id"),
                "expected": expected,
                "actual": actual,
            })
        validated_examples.append({
            **example,
            "validation": validation,
        })

    return {
        "version": VERSION,
        "scope": "offline manual review completed decision examples",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
        },
        "policy": {
            "synthetic_examples_only": True,
            "merge_into_real_decisions": "disallowed",
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
        },
        "summary": {
            "total_examples": len(validated_examples),
            "valid_examples": status_summary.get("valid", 0),
            "invalid_examples": status_summary.get("invalid", 0),
            "pending_examples": status_summary.get("pending", 0),
            "expectation_mismatches": len(mismatches),
        },
        "expectation_mismatches": mismatches,
        "examples": validated_examples,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build synthetic manual-review decision examples.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review decision examples built: "
        f"{summary['total_examples']} examples, "
        f"{summary['valid_examples']} valid, "
        f"{summary['invalid_examples']} invalid"
    )
    return 0 if summary["expectation_mismatches"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
