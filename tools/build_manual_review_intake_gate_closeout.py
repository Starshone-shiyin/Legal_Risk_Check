"""Build the manual-review intake gate closeout report.

The closeout summarizes the intake contract, import, diff, proposed validation,
and promotion dry run. It decides whether the intake gate has ready promoted
decisions, but does not promote or mutate anything.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VERSION = "0.4.7.7.5"

DEFAULT_CONTRACT_PATH = Path("tests/manual_review_intake_contract_report.json")
DEFAULT_IMPORT_REPORT_PATH = Path("tests/manual_review_workbench_import_report.json")
DEFAULT_DIFF_REPORT_PATH = Path("tests/manual_review_decision_diff_report.json")
DEFAULT_VALIDATION_REPORT_PATH = Path("tests/proposed_manual_review_decision_validation_report.json")
DEFAULT_PROMOTION_REPORT_PATH = Path("tests/validated_decision_promotion_dry_run_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_intake_gate_closeout_report.json")


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def gate_status(import_summary: dict[str, Any], diff_summary: dict[str, Any], validation_summary: dict[str, Any], promotion_summary: dict[str, Any]) -> tuple[str, list[str]]:
    blockers = []
    if import_summary.get("imported_rows", 0) == 0:
        blockers.append("no_imported_review_rows")
    if diff_summary.get("blocked_cases", 0):
        blockers.append("blocked_decision_diff_cases")
    if validation_summary.get("invalid_records", 0):
        blockers.append("invalid_proposed_decisions")
    if promotion_summary.get("promotion_candidates", 0) == 0:
        blockers.append("no_promotion_candidates")
    if promotion_summary.get("ready_action_candidates", 0) == 0:
        blockers.append("no_ready_action_candidates")
    return ("open" if not blockers else "blocked", blockers)


def build_report(
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    import_report_path: Path = DEFAULT_IMPORT_REPORT_PATH,
    diff_report_path: Path = DEFAULT_DIFF_REPORT_PATH,
    validation_report_path: Path = DEFAULT_VALIDATION_REPORT_PATH,
    promotion_report_path: Path = DEFAULT_PROMOTION_REPORT_PATH,
) -> dict[str, Any]:
    contract = load_json(contract_path)
    import_report = load_json(import_report_path)
    diff_report = load_json(diff_report_path)
    validation_report = load_json(validation_report_path)
    promotion_report = load_json(promotion_report_path)

    import_summary = import_report.get("summary") or {}
    diff_summary = diff_report.get("summary") or {}
    validation_summary = validation_report.get("summary") or {}
    promotion_summary = promotion_report.get("summary") or {}
    status, blockers = gate_status(import_summary, diff_summary, validation_summary, promotion_summary)

    return {
        "version": VERSION,
        "scope": "manual review intake gate closeout",
        "inputs": {
            "contract_report": str(contract_path),
            "contract_report_version": contract.get("version"),
            "import_report": str(import_report_path),
            "import_report_version": import_report.get("version"),
            "diff_report": str(diff_report_path),
            "diff_report_version": diff_report.get("version"),
            "proposed_validation_report": str(validation_report_path),
            "proposed_validation_report_version": validation_report.get("version"),
            "promotion_dry_run_report": str(promotion_report_path),
            "promotion_dry_run_report_version": promotion_report.get("version"),
        },
        "guardrails": {
            "overwrite_original_schema": "disallowed",
            "main_flow_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
            "risk_rule_mutation": "disallowed",
        },
        "summary": {
            "gate_status": status,
            "blockers": blockers,
            "imported_rows": import_summary.get("imported_rows", 0),
            "rejected_rows": import_summary.get("rejected_rows", 0),
            "changed_cases": diff_summary.get("changed_cases", 0),
            "blocked_diff_cases": diff_summary.get("blocked_cases", 0),
            "valid_proposed_records": validation_summary.get("valid_records", 0),
            "invalid_proposed_records": validation_summary.get("invalid_records", 0),
            "pending_proposed_records": validation_summary.get("pending_records", 0),
            "promotion_candidates": promotion_summary.get("promotion_candidates", 0),
            "ready_action_candidates": promotion_summary.get("ready_action_candidates", 0),
        },
        "next_step": (
            "Fill manual review workbench and rerun intake gate."
            if status == "blocked"
            else "Proceed to ready action planning dry run."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manual-review intake gate closeout report.")
    parser.add_argument("--contract-report", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--import-report", type=Path, default=DEFAULT_IMPORT_REPORT_PATH)
    parser.add_argument("--diff-report", type=Path, default=DEFAULT_DIFF_REPORT_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_PROMOTION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.contract_report, args.import_report, args.diff_report, args.validation_report, args.promotion_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review intake gate closeout built: "
        f"{summary['gate_status']}, "
        f"{summary['promotion_candidates']} promotion candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
