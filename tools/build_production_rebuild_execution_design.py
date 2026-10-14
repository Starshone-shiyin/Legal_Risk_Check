"""Build the v0.4.14.0 production rebuild execution design.

The design reads only the saved v0.4.13.18 planning-series closeout report. It
defines the future production rebuild execution records and gates without
accepting a real authorization record, running live preflight, accessing
Qdrant, rebuilding a collection, calling RAG/embedding/LLM, running full eval,
or mutating runtime and eval artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.14.0"

DEFAULT_CLOSEOUT_PATH = legacy_report_path("ingestion_metadata_rebuild_planning_series_closeout_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_execution_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/production_rebuild_execution_design_v0.4.14.0.md")

REQUIRED_AUTHORIZATION_FIELDS = [
    "target_collection",
    "rebuild_scope",
    "source_version",
    "expected_id_drift_acknowledgement",
    "backup_plan",
    "rollback_plan",
    "operator_approval",
    "maintenance_window",
    "post_rebuild_validation_plan",
    "abort_conditions_acknowledgement",
]

EXECUTION_PHASES = [
    "preflight_validation",
    "backup_or_rollback_verification",
    "target_collection_lock_confirmation",
    "rebuild_execution",
    "post_rebuild_metadata_validation",
    "post_rebuild_smoke_validation",
    "rollback_or_acceptance_decision",
]

PREFLIGHT_CHECKS = [
    "authorization_record_present_and_valid",
    "target_collection_confirmed",
    "backup_or_rollback_collection_verified",
    "source_lineage_confirmed",
    "expected_id_drift_acknowledged",
    "maintenance_window_active",
    "rollback_owner_available",
    "post_rebuild_validation_owner_available",
]

ABORT_CONDITIONS = [
    "authorization_record_missing_or_invalid",
    "target_collection_mismatch",
    "backup_or_rollback_unavailable",
    "source_lineage_mismatch",
    "unexpected_preflight_failure",
    "post_rebuild_validation_failure",
    "rollback_owner_unavailable",
    "expected_id_drift_not_acknowledged",
    "maintenance_window_not_active",
]

PREFLIGHT_RECORD_FIELDS = [
    "authorization_record_reference",
    "target_collection",
    "backup_or_rollback_reference",
    "source_lineage_reference",
    "expected_id_drift_acknowledged",
    "maintenance_window",
    "operator_identity",
    "preflight_checks",
    "preflight_status",
    "blocking_conditions",
]

BACKUP_OR_ROLLBACK_RECORD_FIELDS = [
    "backup_or_snapshot_reference",
    "rollback_collection_reference",
    "backup_verification_status",
    "rollback_owner",
    "rollback_procedure_reference",
    "restore_or_swap_readiness",
]

REBUILD_EXECUTION_RECORD_FIELDS = [
    "authorization_record_reference",
    "target_collection",
    "source_lineage_reference",
    "execution_window",
    "operator_identity",
    "execution_status",
    "qdrant_operation_log_reference",
    "expected_id_drift_recorded",
    "abort_condition_triggered",
]

POST_REBUILD_VALIDATION_RECORD_FIELDS = [
    "metadata_boundary_check_status",
    "id_drift_accounting_status",
    "limited_smoke_status",
    "evidence_metadata_snapshot_status",
    "rollback_readiness_status",
    "validation_owner",
    "validation_status",
    "validation_blockers",
]

ABORT_OR_ACCEPTANCE_DECISION_RECORD_FIELDS = [
    "decision",
    "decision_owner",
    "decided_at",
    "rollback_required",
    "rollback_status",
    "acceptance_status",
    "residual_risks",
    "main_flow_change_authorized",
]

DENIED_GUARDRAILS = {
    "human_authorization_record_created": False,
    "human_authorization_record_accepted": False,
    "authorization_granted": False,
    "live_preflight_run": False,
    "production_rebuild_executed": False,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "collection_switch": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "runtime_mutation": "disallowed",
    "ingestion_source_mutation": "disallowed",
    "retriever_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "closeout_report_only": True,
    **DENIED_GUARDRAILS,
}

CLOSEOUT_EXPECTATION = {
    "version": "0.4.13.18",
    "schema_kind": "ingestion_metadata_rebuild_planning_series_closeout",
    "status": "closed_for_execution_design_handoff",
    "allowed_next_step": "production_rebuild_execution_design",
}

CLOSEOUT_SUMMARY_BOUNDARIES = {
    "authorization_granted": False,
    "qdrant_write_allowed": False,
    "rebuild_allowed": False,
    "live_preflight_run": False,
    "production_rebuild_executed": False,
    "full_eval": "not_run",
}

CLOSEOUT_GUARDRAIL_BOUNDARIES = {
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "runtime_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(data.get("summary"))
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": summary.get("status"),
        "allowed_next_step": summary.get("allowed_next_step"),
    }


def closeout_blockers(closeout: dict[str, Any]) -> list[str]:
    summary = as_dict(closeout.get("summary"))
    guardrails = as_dict(closeout.get("guardrails"))
    blockers: list[str] = []
    if not closeout:
        blockers.append("planning_closeout_missing")
    if closeout.get("version") != CLOSEOUT_EXPECTATION["version"]:
        blockers.append("planning_closeout_version_mismatch")
    if closeout.get("schema_kind") != CLOSEOUT_EXPECTATION["schema_kind"]:
        blockers.append("planning_closeout_schema_mismatch")
    if summary.get("status") != CLOSEOUT_EXPECTATION["status"]:
        blockers.append("planning_closeout_status_mismatch")
    if summary.get("allowed_next_step") != CLOSEOUT_EXPECTATION["allowed_next_step"]:
        blockers.append("planning_closeout_allowed_next_step_mismatch")
    for field, expected in CLOSEOUT_SUMMARY_BOUNDARIES.items():
        if summary.get(field) != expected:
            blockers.append(f"planning_closeout_{field}_mismatch")
    for field, expected in CLOSEOUT_GUARDRAIL_BOUNDARIES.items():
        if guardrails.get(field) != expected:
            blockers.append(f"planning_closeout_guardrail_{field}_mismatch")
    return blockers


def build_record_contracts() -> dict[str, dict[str, Any]]:
    return {
        "preflight_record": {
            "fields": PREFLIGHT_RECORD_FIELDS,
            "checks": PREFLIGHT_CHECKS,
            "must_pass_before": "backup_or_rollback_verification",
        },
        "backup_or_rollback_record": {
            "fields": BACKUP_OR_ROLLBACK_RECORD_FIELDS,
            "must_pass_before": "target_collection_lock_confirmation",
        },
        "rebuild_execution_record": {
            "fields": REBUILD_EXECUTION_RECORD_FIELDS,
            "must_not_be_created_in_this_version": True,
        },
        "post_rebuild_validation_record": {
            "fields": POST_REBUILD_VALIDATION_RECORD_FIELDS,
            "must_pass_before": "rollback_or_acceptance_decision",
        },
        "abort_or_acceptance_decision_record": {
            "fields": ABORT_OR_ACCEPTANCE_DECISION_RECORD_FIELDS,
            "automatic_acceptance_allowed": False,
            "main_flow_change_authorized_by_this_record": False,
        },
    }


def build_report(closeout_path: Path = DEFAULT_CLOSEOUT_PATH) -> dict[str, Any]:
    closeout = load_json(closeout_path)
    blockers = closeout_blockers(closeout)
    ready = not blockers
    status = "ready_for_production_rebuild_execution_design_gate" if ready else "blocked"
    record_contracts = build_record_contracts()
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_execution_design",
        "scope": "production rebuild execution design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "planning_closeout": source_meta(closeout_path, closeout),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": "production_rebuild_execution_design_gate" if ready else "blocked",
            "authorization_record_required": True,
            "authorization_record_created": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "production_rebuild_executed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
            "record_contract_count": len(record_contracts),
            "execution_phase_count": len(EXECUTION_PHASES),
            "preflight_check_count": len(PREFLIGHT_CHECKS),
            "abort_condition_count": len(ABORT_CONDITIONS),
            "blockers": blockers,
        },
        "execution_design": {
            "purpose": "define future production rebuild execution records without executing rebuild",
            "source_of_truth": "v0.4.13.18 planning closeout report",
            "required_authorization_fields": REQUIRED_AUTHORIZATION_FIELDS,
            "phase_order": EXECUTION_PHASES,
            "record_contracts": record_contracts,
            "blocking_conditions": ABORT_CONDITIONS,
            "decision_policy": {
                "preflight_failure": "abort_before_rebuild",
                "backup_or_rollback_failure": "abort_before_rebuild",
                "post_rebuild_validation_failure": "rollback_or_hold_for_manual_decision",
                "all_checks_pass": "requires_explicit_human_acceptance_record",
                "main_flow_change": "not_authorized_by_this_design",
            },
        },
        "output_contract": {
            "summary_fields": [
                "status",
                "allowed_next_step",
                "authorization_record_required",
                "authorization_record_created",
                "authorization_granted",
                "live_preflight_run",
                "production_rebuild_executed",
                "qdrant_write_allowed",
                "rebuild_allowed",
                "full_eval",
                "blockers",
            ],
            "required_records": list(record_contracts),
        },
        "handoff": {
            "next_allowed_step": "gate this production rebuild execution design" if ready else "resolve execution design blockers",
            "not_allowed_yet": [
                "create or accept human authorization record",
                "run live preflight",
                "write Qdrant",
                "rebuild collection",
                "switch collection",
                "call rag_query",
                "call embedding or LLM services",
                "run full eval as a substitute for authorization",
                "modify runtime, ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("execution_design"))
    records = as_dict(design.get("record_contracts"))
    lines = [
        "# v0.4.14.0 Production Rebuild Execution Design",
        "",
        "本版本只设计未来生产 rebuild execution series 的记录契约和门禁顺序。它只读取 v0.4.13.18 closeout report，不创建或接受人工授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "source-of-truth 口径：v0.4.13.18 closeout 已聚合 v0.4.13.13-v0.4.13.17 的授权设计、worksheet、gate、runbook/preflight contract 与 planning closeout 结论；本 design 不再直接读取旧分散报告。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已创建授权记录: `{summary.get('authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否已运行 live preflight: `{summary.get('live_preflight_run')}`",
        f"- 是否已执行生产 rebuild: `{summary.get('production_rebuild_executed')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 执行阶段",
        "",
    ]
    for phase in design.get("phase_order", []):
        lines.append(f"- `{phase}`")
    lines.extend(["", "## 记录契约", ""])
    for name, contract in records.items():
        lines.append(f"- `{name}`: {len(contract.get('fields', []))} fields")
    lines.extend(["", "## 当前禁止动作", ""])
    for item in as_dict(report.get("handoff")).get("not_allowed_yet", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "通过本 design 只允许进入 `production_rebuild_execution_design_gate`，仍不代表已经允许 live preflight、Qdrant write 或生产 rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.0 production rebuild execution design.")
    parser.add_argument("--closeout", type=Path, default=DEFAULT_CLOSEOUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.closeout)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild execution design: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
