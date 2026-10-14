"""Build a dry run for the manual-review export pipeline.

The dry run consumes a filled workbench input and reuses the existing
importer, diff audit, proposed validator, promotion dry run, and closeout
gate. It writes isolated dry-run artifacts only; it does not overwrite the
canonical proposed schema or mutate retrieval, rerank, prompts, anchors, risk
rules, eval cases, hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.audit_manual_review_decision_diff import build_report as build_diff_report
from tools.build_manual_review_intake_gate_closeout import build_report as build_closeout_report
from tools.build_validated_decision_promotion_dry_run import build_report as build_promotion_report
from tools.import_manual_review_workbench import build_outputs as build_import_outputs
from tools.import_manual_review_workbench import read_input_rows
from tools._shared.layout import legacy_report_path
from tools.validate_proposed_manual_review_decisions import build_report as build_validation_report


VERSION = "0.4.7.8.14"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_WORKBENCH_INPUT_PATH = Path("tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json")
DEFAULT_CONTRACT_REPORT_PATH = legacy_report_path("manual_review_intake_contract_report.json")
DEFAULT_ARTIFACT_DIR = Path("tests/manual_review_export_pipeline_dry_run_artifacts")
DEFAULT_OUTPUT_PATH = legacy_report_path("manual_review_export_pipeline_dry_run_report.json")

PROPOSED_SCHEMA_NAME = "proposed_manual_review_decision_schema_dry_run.json"
IMPORT_REPORT_NAME = "manual_review_workbench_import_report_dry_run.json"
DIFF_REPORT_NAME = "manual_review_decision_diff_report_dry_run.json"
VALIDATION_REPORT_NAME = "proposed_manual_review_decision_validation_report_dry_run.json"
PROMOTION_REPORT_NAME = "validated_decision_promotion_dry_run_report_dry_run.json"
CLOSEOUT_REPORT_NAME = "manual_review_intake_gate_closeout_report_dry_run.json"

CANONICAL_OUTPUT_NAMES = {
    "proposed_manual_review_decision_schema.json",
    "manual_review_workbench_import_report.json",
    "manual_review_decision_diff_report.json",
    "proposed_manual_review_decision_validation_report.json",
    "validated_decision_promotion_dry_run_report.json",
    "manual_review_intake_gate_closeout_report.json",
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def input_profile(workbench_input_path: Path) -> dict[str, Any]:
    rows = read_input_rows(workbench_input_path)
    profile: dict[str, Any] = {
        "input_path": str(workbench_input_path),
        "input_suffix": workbench_input_path.suffix.lower(),
        "input_rows": len(rows),
        "workbench_items": 0,
        "reviewer_input_template_rows": 0,
        "ai_review_suggestion_rows": 0,
        "safe_ai_suggestion_input": False,
    }
    if workbench_input_path.suffix.lower() != ".json":
        return profile

    data = load_json(workbench_input_path)
    items = as_list(data.get("workbench_items")) if isinstance(data, dict) else []
    profile["workbench_items"] = len([item for item in items if isinstance(item, dict)])
    profile["reviewer_input_template_rows"] = sum(
        1
        for item in items
        if isinstance(item, dict) and isinstance(item.get("reviewer_input_template"), dict)
    )
    profile["ai_review_suggestion_rows"] = sum(
        1
        for item in items
        if isinstance(item, dict) and isinstance(item.get("ai_review_suggestion"), dict)
    )
    guardrails = data.get("guardrails") if isinstance(data.get("guardrails"), dict) else {}
    profile["safe_ai_suggestion_input"] = bool(
        data.get("human_confirmation_required") is True
        or data.get("reviewer_input_template_written") is False
        or guardrails.get("advisory_draft_only") is True
        or guardrails.get("reviewer_decision_import") == "disallowed_without_human_copy"
        or (profile["ai_review_suggestion_rows"] and not profile["reviewer_input_template_rows"])
    )
    return profile


def artifact_paths(artifact_dir: Path) -> dict[str, Path]:
    return {
        "proposed_schema": artifact_dir / PROPOSED_SCHEMA_NAME,
        "import_report": artifact_dir / IMPORT_REPORT_NAME,
        "diff_report": artifact_dir / DIFF_REPORT_NAME,
        "validation_report": artifact_dir / VALIDATION_REPORT_NAME,
        "promotion_report": artifact_dir / PROMOTION_REPORT_NAME,
        "closeout_report": artifact_dir / CLOSEOUT_REPORT_NAME,
    }


def stage_status(summary: dict[str, Any], stage: str) -> str:
    if stage == "import":
        return "ready" if summary.get("imported_rows", 0) > 0 else "blocked"
    if stage == "diff":
        return "blocked" if summary.get("blocked_cases", 0) else "ready"
    if stage == "validation":
        return "blocked" if summary.get("invalid_records", 0) else "ready"
    if stage == "promotion":
        return "ready" if summary.get("promotion_candidates", 0) > 0 else "blocked"
    if stage == "closeout":
        return summary.get("gate_status", "unknown")
    return "unknown"


def dry_run_blockers(import_summary: dict[str, Any]) -> list[str]:
    blockers = []
    if import_summary.get("rejected_rows", 0):
        blockers.append("rejected_import_rows")
    for key in ["missing_case_id", "unknown_case_id", "duplicate_case_id", "empty_importable_content"]:
        if import_summary.get(key, 0):
            blockers.append(key)
    for key in [
        "invalid_json_workbench_export",
        "incomplete_completed_reviewer_fields",
        "unsupported_workbench_input",
        "advisory_review_marker",
    ]:
        if import_summary.get(key, 0):
            blockers.append(key)
    return blockers


def pipeline_conclusion(
    input_meta: dict[str, Any],
    import_summary: dict[str, Any],
    closeout_summary: dict[str, Any],
    blockers: list[str] | None = None,
) -> str:
    if input_meta.get("safe_ai_suggestion_input") and import_summary.get("imported_rows", 0) == 0:
        return "blocked_as_expected_ai_suggestion_only"
    if blockers:
        return "blocked_input_rejections_require_review"
    if closeout_summary.get("gate_status") == "open":
        return "ready_for_governed_action_planning"
    return "blocked_manual_review_required"


def assert_safe_output_path(output_path: Path) -> None:
    if output_path.name in CANONICAL_OUTPUT_NAMES:
        raise ValueError(f"Refusing to write dry-run report over canonical pipeline artifact: {output_path}")


def build_report(
    decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH,
    workbench_input_path: Path = DEFAULT_WORKBENCH_INPUT_PATH,
    contract_report_path: Path = DEFAULT_CONTRACT_REPORT_PATH,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, Any]:
    paths = artifact_paths(artifact_dir)
    input_meta = input_profile(workbench_input_path)

    proposed_schema, import_report = build_import_outputs(decision_schema_path, workbench_input_path)
    write_json(paths["proposed_schema"], proposed_schema)
    write_json(paths["import_report"], import_report)

    diff_report = build_diff_report(decision_schema_path, paths["proposed_schema"])
    write_json(paths["diff_report"], diff_report)

    validation_report = build_validation_report(paths["proposed_schema"])
    write_json(paths["validation_report"], validation_report)

    promotion_report = build_promotion_report(paths["proposed_schema"], paths["validation_report"])
    write_json(paths["promotion_report"], promotion_report)

    closeout_report = build_closeout_report(
        contract_report_path,
        paths["import_report"],
        paths["diff_report"],
        paths["validation_report"],
        paths["promotion_report"],
    )
    write_json(paths["closeout_report"], closeout_report)

    import_summary = import_report.get("summary") or {}
    diff_summary = diff_report.get("summary") or {}
    validation_summary = validation_report.get("summary") or {}
    promotion_summary = promotion_report.get("summary") or {}
    closeout_summary = closeout_report.get("summary") or {}

    blockers = dry_run_blockers(import_summary)
    conclusion = pipeline_conclusion(input_meta, import_summary, closeout_summary, blockers)
    return {
        "version": VERSION,
        "scope": "manual review export pipeline dry run",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "workbench_input": str(workbench_input_path),
            "contract_report": str(contract_report_path),
            "artifact_dir": str(artifact_dir),
        },
        "input_profile": input_meta,
        "artifacts": {key: str(value) for key, value in paths.items()},
        "guardrails": {
            "overwrite_original_schema": "disallowed",
            "canonical_pipeline_artifact_overwrite": "disallowed",
            "ai_suggestion_as_completed_decision": "disallowed",
            "main_flow_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
            "risk_rule_mutation": "disallowed",
            "qdrant_access": "disallowed",
            "llm_access": "disallowed",
        },
        "summary": {
            "pipeline_conclusion": conclusion,
            "gate_status": closeout_summary.get("gate_status", "unknown"),
            "gate_blockers": closeout_summary.get("blockers") or [],
            "dry_run_blockers": blockers,
            "input_rows": import_summary.get("input_rows", input_meta.get("input_rows", 0)),
            "imported_rows": import_summary.get("imported_rows", 0),
            "rejected_rows": import_summary.get("rejected_rows", 0),
            "empty_importable_content": import_summary.get("empty_importable_content", 0),
            "invalid_json_workbench_export": import_summary.get("invalid_json_workbench_export", 0),
            "incomplete_completed_reviewer_fields": import_summary.get("incomplete_completed_reviewer_fields", 0),
            "unsupported_workbench_input": import_summary.get("unsupported_workbench_input", 0),
            "advisory_review_marker": import_summary.get("advisory_review_marker", 0),
            "changed_cases": diff_summary.get("changed_cases", 0),
            "blocked_diff_cases": diff_summary.get("blocked_cases", 0),
            "valid_proposed_records": validation_summary.get("valid_records", 0),
            "invalid_proposed_records": validation_summary.get("invalid_records", 0),
            "pending_proposed_records": validation_summary.get("pending_records", 0),
            "promotion_candidates": promotion_summary.get("promotion_candidates", 0),
            "ready_action_candidates": promotion_summary.get("ready_action_candidates", 0),
            "safe_ai_suggestion_input": input_meta.get("safe_ai_suggestion_input", False),
        },
        "pipeline_steps": [
            {
                "step": "import_filled_workbench",
                "status": stage_status(import_summary, "import"),
                "summary": import_summary,
            },
            {
                "step": "audit_decision_diff",
                "status": stage_status(diff_summary, "diff"),
                "summary": diff_summary,
            },
            {
                "step": "validate_proposed_decisions",
                "status": stage_status(validation_summary, "validation"),
                "summary": validation_summary,
            },
            {
                "step": "promotion_dry_run",
                "status": stage_status(promotion_summary, "promotion"),
                "summary": promotion_summary,
            },
            {
                "step": "closeout_gate",
                "status": stage_status(closeout_summary, "closeout"),
                "summary": closeout_summary,
            },
        ],
        "next_step": (
            "Proceed only to governed ready-action planning; do not mutate RAG without explicit reviewed action approval."
            if conclusion == "ready_for_governed_action_planning"
            else "Continue human review in the visual workbench; do not treat AI suggestions or blocked drafts as reviewer decisions."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a manual-review export pipeline dry-run report.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--workbench-input", type=Path, default=DEFAULT_WORKBENCH_INPUT_PATH)
    parser.add_argument("--contract-report", type=Path, default=DEFAULT_CONTRACT_REPORT_PATH)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema, args.workbench_input, args.contract_report, args.artifact_dir)
    try:
        assert_safe_output_path(args.output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Manual review export pipeline dry run built: "
        f"{summary['pipeline_conclusion']}, "
        f"gate={summary['gate_status']}, "
        f"{summary['imported_rows']} imported, "
        f"{summary['promotion_candidates']} promotion candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
