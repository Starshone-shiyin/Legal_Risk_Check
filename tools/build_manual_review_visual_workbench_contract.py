"""Build the manual-review visual workbench contract.

This contract describes a standalone, offline visual review bench for existing
RAG grounding diagnostics. It reads saved reports and defines UI/data/export
boundaries. It does not launch a frontend, import reviewer decisions, overwrite
schemas, or modify retrieval, rerank, prompts, anchors, risk rules, eval cases,
hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VERSION = "0.4.7.8.0"

DEFAULT_OUTPUT_PATH = Path("tests/manual_review_visual_workbench_contract_report.json")

DEFAULT_WORKBENCH_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_INTAKE_CONTRACT_PATH = Path("tests/manual_review_intake_contract_report.json")
DEFAULT_PROGRESS_REPORT_PATH = Path("tests/evidence_manual_review_progress_report.json")
DEFAULT_GOVERNANCE_REPORT_PATH = Path("tests/evidence_manual_review_governance_report.json")
DEFAULT_IMPORT_REPORT_PATH = Path("tests/manual_review_workbench_import_report.json")
DEFAULT_DIFF_REPORT_PATH = Path("tests/manual_review_decision_diff_report.json")
DEFAULT_VALIDATION_REPORT_PATH = Path("tests/proposed_manual_review_decision_validation_report.json")
DEFAULT_PROMOTION_REPORT_PATH = Path("tests/validated_decision_promotion_dry_run_report.json")
DEFAULT_CLOSEOUT_REPORT_PATH = Path("tests/manual_review_intake_gate_closeout_report.json")


DATA_SOURCES = [
    {
        "key": "workbench",
        "label": "manual review workbench",
        "path_attr": "workbench",
        "default_path": DEFAULT_WORKBENCH_PATH,
        "required_for_ui": True,
        "ui_role": "case queue and case detail source",
    },
    {
        "key": "intake_contract",
        "label": "workbench intake contract",
        "path_attr": "intake_contract",
        "default_path": DEFAULT_INTAKE_CONTRACT_PATH,
        "required_for_ui": True,
        "ui_role": "field permissions and allowed values",
    },
    {
        "key": "progress_report",
        "label": "manual review progress report",
        "path_attr": "progress_report",
        "default_path": DEFAULT_PROGRESS_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "progress counters and blockers",
    },
    {
        "key": "governance_report",
        "label": "manual review governance report",
        "path_attr": "governance_report",
        "default_path": DEFAULT_GOVERNANCE_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "issue/action/domain summaries",
    },
    {
        "key": "import_report",
        "label": "workbench import report",
        "path_attr": "import_report",
        "default_path": DEFAULT_IMPORT_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "latest import acceptance/rejection status",
    },
    {
        "key": "diff_report",
        "label": "manual review decision diff report",
        "path_attr": "diff_report",
        "default_path": DEFAULT_DIFF_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "proposed decision audit status",
    },
    {
        "key": "validation_report",
        "label": "proposed decision validation report",
        "path_attr": "validation_report",
        "default_path": DEFAULT_VALIDATION_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "validator status display",
    },
    {
        "key": "promotion_report",
        "label": "validated decision promotion dry run",
        "path_attr": "promotion_report",
        "default_path": DEFAULT_PROMOTION_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "ready promotion and ready action display",
    },
    {
        "key": "closeout_report",
        "label": "manual review intake gate closeout",
        "path_attr": "closeout_report",
        "default_path": DEFAULT_CLOSEOUT_REPORT_PATH,
        "required_for_ui": False,
        "ui_role": "single gate status badge",
    },
]


GUARDRAILS = {
    "standalone_offline_tool": True,
    "rag_query_integration": "disallowed",
    "backend_api_write": "disallowed",
    "overwrite_original_decision_schema": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def data_source_inventory(paths: dict[str, Path]) -> list[dict[str, Any]]:
    inventory = []
    for source in DATA_SOURCES:
        path = paths[source["key"]]
        inventory.append(
            {
                "key": source["key"],
                "label": source["label"],
                "path": str(path),
                "present": path.exists(),
                "required_for_ui": source["required_for_ui"],
                "ui_role": source["ui_role"],
            }
        )
    return inventory


def contract_section(intake_contract: dict[str, Any]) -> dict[str, Any]:
    contract = intake_contract.get("contract") if isinstance(intake_contract.get("contract"), dict) else {}
    field_policy = contract.get("field_policy") if isinstance(contract.get("field_policy"), dict) else {}
    allowed_values = contract.get("allowed_values") if isinstance(contract.get("allowed_values"), dict) else {}
    write_policy = contract.get("write_policy") if isinstance(contract.get("write_policy"), dict) else {}

    read_only = field_policy.get("read_only_context_fields") or []
    importable = field_policy.get("importable_reviewer_fields") or []
    return {
        "source_contract_version": contract.get("version"),
        "read_only_context_fields": read_only,
        "importable_reviewer_fields": importable,
        "readonly_importable_overlap": sorted(set(read_only) & set(importable)),
        "required_for_completed": field_policy.get("required_for_completed") or [],
        "list_fields": field_policy.get("list_fields") or [],
        "boolean_fields": field_policy.get("boolean_fields") or [],
        "list_delimiter": field_policy.get("list_delimiter"),
        "allowed_values": allowed_values,
        "write_policy": write_policy,
    }


def current_state_summary(
    workbench: dict[str, Any],
    progress: dict[str, Any],
    governance: dict[str, Any],
    import_report: dict[str, Any],
    validation_report: dict[str, Any],
    promotion_report: dict[str, Any],
    closeout_report: dict[str, Any],
) -> dict[str, Any]:
    workbench_summary = workbench.get("summary") if isinstance(workbench.get("summary"), dict) else {}
    progress_summary = progress.get("summary") if isinstance(progress.get("summary"), dict) else {}
    governance_summary = governance.get("summary") if isinstance(governance.get("summary"), dict) else {}
    import_summary = import_report.get("summary") if isinstance(import_report.get("summary"), dict) else {}
    validation_summary = validation_report.get("summary") if isinstance(validation_report.get("summary"), dict) else {}
    promotion_summary = promotion_report.get("summary") if isinstance(promotion_report.get("summary"), dict) else {}
    closeout_summary = closeout_report.get("summary") if isinstance(closeout_report.get("summary"), dict) else {}

    return {
        "gate_status": closeout_summary.get("gate_status", "unknown"),
        "gate_blockers": closeout_summary.get("blockers") or [],
        "workbench_items": workbench_summary.get("total_workbench_items", 0),
        "pending_workbench_items": workbench_summary.get("pending_items", 0),
        "high_priority_items": workbench_summary.get("high_priority_items", 0),
        "completed_cases": progress_summary.get("completed_cases", 0),
        "pending_cases": progress_summary.get("pending_cases", 0),
        "valid_cases": progress_summary.get("valid_cases", 0),
        "invalid_cases": progress_summary.get("invalid_cases", 0),
        "imported_rows": import_summary.get("imported_rows", 0),
        "rejected_rows": import_summary.get("rejected_rows", 0),
        "valid_proposed_records": validation_summary.get("valid_records", 0),
        "invalid_proposed_records": validation_summary.get("invalid_records", 0),
        "pending_proposed_records": validation_summary.get("pending_records", 0),
        "promotion_candidates": promotion_summary.get("promotion_candidates", 0),
        "ready_action_candidates": promotion_summary.get("ready_action_candidates", 0),
        "blocked_action_candidates": governance_summary.get("blocked_action_candidates", 0),
        "blocked_fixture_candidates": governance_summary.get("blocked_fixture_candidates", 0),
        "readiness_state": governance_summary.get("readiness_state", "unknown"),
    }


def visual_model() -> dict[str, Any]:
    return {
        "reference": {
            "name": "BiliSum Light UI Spec",
            "url": "https://github.com/lycohana/BiliSum/blob/master/docs/bilisum-light-ui-spec.md",
            "adaptation": "Use the light workbench structure, not the consumer pink brand palette.",
        },
        "layout": {
            "shell": "two_column_workbench",
            "left_sidebar": [
                "brand_card",
                "queue_navigation",
                "status_panel",
            ],
            "top_bar": [
                "page_title",
                "gate_status_badge",
                "data_freshness_badges",
            ],
            "main_grid": [
                "primary_review_queue",
                "status_overview",
                "case_list",
                "case_detail",
                "reviewer_decision_form",
                "validation_pipeline_status",
            ],
        },
        "queues": [
            {
                "key": "all_cases",
                "label": "All review cases",
                "source": "workbench.workbench_items",
            },
            {
                "key": "high_priority",
                "label": "High-risk manual review",
                "source": "workbench.summary.high_priority_case_ids",
            },
            {
                "key": "awaiting_manual_review",
                "label": "Awaiting reviewer input",
                "source": "progress_report.cases[decision_status=pending]",
            },
            {
                "key": "blocked_intake_gate",
                "label": "Blocked intake gate",
                "source": "closeout_report.summary.blockers",
            },
            {
                "key": "ready_for_promotion",
                "label": "Ready from valid decisions",
                "source": "promotion_report.promotion_candidates",
            },
        ],
        "case_detail_tabs": [
            "diagnostic_summary",
            "evidence_context",
            "suggested_review_questions",
            "reviewer_decision",
            "pipeline_status",
        ],
        "design_tokens": {
            "page_bg": "#F7F8FC",
            "surface": "#FFFFFF",
            "surface_muted": "#F8FAFC",
            "text_primary": "#1F2937",
            "text_secondary": "#556274",
            "accent_primary": "#0F766E",
            "accent_secondary": "#2563EB",
            "warning": "#D58918",
            "danger": "#E14B5A",
            "success": "#22A866",
            "border": "rgba(129, 140, 160, 0.28)",
            "card_radius": "8px",
            "control_radius": "8px",
            "font_sans": "Inter, Noto Sans SC, PingFang SC, Microsoft YaHei, sans-serif",
            "font_mono": "JetBrains Mono, Consolas, monospace",
        },
    }


def export_policy() -> dict[str, Any]:
    return {
        "browser_export_only": True,
        "allowed_exports": [
            "filled_workbench_json",
            "filled_workbench_csv",
            "visual_review_session_json",
        ],
        "allowed_next_tools": [
            "tools/import_manual_review_workbench.py",
            "tools/audit_manual_review_decision_diff.py",
            "tools/validate_proposed_manual_review_decisions.py",
            "tools/build_validated_decision_promotion_dry_run.py",
            "tools/build_manual_review_intake_gate_closeout.py",
        ],
        "disallowed_writes": [
            "tests/evidence_manual_review_decision_schema.json",
            "tests/rag_eval_cases.json",
            "config/hidden_eval_seed_cases.json",
            "config/rag_anchor_rules.json",
            "config/risk_payload_supplement_rules.json",
            "src/rag/retriever.py",
            "src/rag/domain_router.py",
        ],
    }


def build_report(
    workbench_path: Path = DEFAULT_WORKBENCH_PATH,
    intake_contract_path: Path = DEFAULT_INTAKE_CONTRACT_PATH,
    progress_report_path: Path = DEFAULT_PROGRESS_REPORT_PATH,
    governance_report_path: Path = DEFAULT_GOVERNANCE_REPORT_PATH,
    import_report_path: Path = DEFAULT_IMPORT_REPORT_PATH,
    diff_report_path: Path = DEFAULT_DIFF_REPORT_PATH,
    validation_report_path: Path = DEFAULT_VALIDATION_REPORT_PATH,
    promotion_report_path: Path = DEFAULT_PROMOTION_REPORT_PATH,
    closeout_report_path: Path = DEFAULT_CLOSEOUT_REPORT_PATH,
) -> dict[str, Any]:
    paths = {
        "workbench": workbench_path,
        "intake_contract": intake_contract_path,
        "progress_report": progress_report_path,
        "governance_report": governance_report_path,
        "import_report": import_report_path,
        "diff_report": diff_report_path,
        "validation_report": validation_report_path,
        "promotion_report": promotion_report_path,
        "closeout_report": closeout_report_path,
    }
    workbench = load_json(workbench_path)
    intake_contract = load_json(intake_contract_path)
    progress = load_json(progress_report_path)
    governance = load_json(governance_report_path)
    import_report = load_json(import_report_path)
    diff_report = load_json(diff_report_path)
    validation_report = load_json(validation_report_path)
    promotion_report = load_json(promotion_report_path)
    closeout_report = load_json(closeout_report_path)

    inventory = data_source_inventory(paths)
    missing_required = [
        source["key"]
        for source in inventory
        if source["required_for_ui"] and not source["present"]
    ]

    return {
        "version": VERSION,
        "scope": "manual review visual workbench contract",
        "purpose": "standalone grounding-quality review UI contract",
        "source_ui_reference": visual_model()["reference"],
        "data_sources": inventory,
        "summary": {
            **current_state_summary(
                workbench,
                progress,
                governance,
                import_report,
                validation_report,
                promotion_report,
                closeout_report,
            ),
            "data_sources_present": sum(1 for source in inventory if source["present"]),
            "missing_required_sources": missing_required,
            "visual_contract_ready": not missing_required,
        },
        "field_contract": contract_section(intake_contract),
        "visual_model": visual_model(),
        "export_policy": export_policy(),
        "validation_flow": [
            "open_visual_workbench",
            "load_saved_reports",
            "review_case_context",
            "fill_reviewer_fields",
            "export_filled_workbench",
            "run_existing_import_diff_validation_promotion_closeout_tools",
        ],
        "guardrails": GUARDRAILS,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manual review visual workbench contract.")
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH_PATH)
    parser.add_argument("--intake-contract", type=Path, default=DEFAULT_INTAKE_CONTRACT_PATH)
    parser.add_argument("--progress-report", type=Path, default=DEFAULT_PROGRESS_REPORT_PATH)
    parser.add_argument("--governance-report", type=Path, default=DEFAULT_GOVERNANCE_REPORT_PATH)
    parser.add_argument("--import-report", type=Path, default=DEFAULT_IMPORT_REPORT_PATH)
    parser.add_argument("--diff-report", type=Path, default=DEFAULT_DIFF_REPORT_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_PROMOTION_REPORT_PATH)
    parser.add_argument("--closeout-report", type=Path, default=DEFAULT_CLOSEOUT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        workbench_path=args.workbench,
        intake_contract_path=args.intake_contract,
        progress_report_path=args.progress_report,
        governance_report_path=args.governance_report,
        import_report_path=args.import_report,
        diff_report_path=args.diff_report,
        validation_report_path=args.validation_report,
        promotion_report_path=args.promotion_report,
        closeout_report_path=args.closeout_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review visual workbench contract built: "
        f"{summary['workbench_items']} cases, "
        f"gate={summary['gate_status']}, "
        f"ready={summary['visual_contract_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
