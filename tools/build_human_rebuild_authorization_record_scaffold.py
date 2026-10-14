"""Build the v0.4.14.2 human rebuild authorization record scaffold.

The scaffold reads only saved v0.4.14.0/v0.4.14.1 reports and prepares the
fields a future human authorization record would need. It does not collect
human values, create or accept authorization, run live preflight, access
Qdrant, rebuild collections, call RAG/embedding/LLM services, run full eval,
or mutate runtime/eval artifacts.
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


VERSION = "0.4.14.2"

DEFAULT_DESIGN_PATH = legacy_report_path("production_rebuild_execution_design_report.json")
DEFAULT_DESIGN_GATE_PATH = legacy_report_path("production_rebuild_execution_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_scaffold_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md")

AUTHORIZATION_FIELD_ORDER = [
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

REQUIRED_RECORD_ORDER = [
    "preflight_record",
    "backup_or_rollback_record",
    "rebuild_execution_record",
    "post_rebuild_validation_record",
    "abort_or_acceptance_decision_record",
]

REQUIRED_PREFLIGHT_CHECKS = {
    "authorization_record_present_and_valid",
    "target_collection_confirmed",
    "backup_or_rollback_collection_verified",
    "source_lineage_confirmed",
    "expected_id_drift_acknowledged",
    "maintenance_window_active",
    "rollback_owner_available",
    "post_rebuild_validation_owner_available",
}

REQUIRED_ABORT_CONDITIONS = {
    "authorization_record_missing_or_invalid",
    "target_collection_mismatch",
    "backup_or_rollback_unavailable",
    "source_lineage_mismatch",
    "unexpected_preflight_failure",
    "post_rebuild_validation_failure",
    "rollback_owner_unavailable",
    "expected_id_drift_not_acknowledged",
    "maintenance_window_not_active",
}

FIELD_GUIDANCE = {
    "target_collection": "填写未来拟重建的精确 collection 名称；本版本不确认、不锁定该值。",
    "rebuild_scope": "填写未来重建范围、包含/排除对象和边界；本版本不批准该范围。",
    "source_version": "填写未来执行时的代码、报告和 source lineage；本版本不接受该 lineage。",
    "expected_id_drift_acknowledgement": "填写是否已理解 chunk_id/qdrant_point_id 的预期漂移；本版本不视为确认。",
    "backup_plan": "填写 snapshot/export 或备用 collection 方案；本版本不验证备份存在。",
    "rollback_plan": "填写回滚策略、负责人和停止条件；本版本不验证回滚可用性。",
    "operator_approval": "未来可填写审批人、时间和明确 yes/no；本版本不把该行视为当前批准。",
    "maintenance_window": "填写未来维护窗口和沟通责任；本版本不启动维护窗口。",
    "post_rebuild_validation_plan": "填写未来 metadata、ID drift、smoke 和 rollback readiness 验证计划；本版本不运行验证。",
    "abort_conditions_acknowledgement": "填写是否已理解全部阻断条件；本版本不放行任何阻断条件。",
}

CRITICAL_DESIGN_GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "closeout_report_only": True,
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
    "scaffold_only": True,
    "saved_reports_only": True,
    "human_values_collected": False,
    "formal_authorization_record_created": False,
    "human_authorization_record_created": False,
    "human_authorization_record_accepted": False,
    "captures_formal_authorization_outcome": False,
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

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "authorized_actions",
    "ready_to_apply",
    "commands",
    "rebuild_steps",
    "qdrant_operation_log",
    "implementation_plan",
    "execution_commands",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def forbidden_output_keys(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted(set(matches))


def source_blockers(design_report: dict[str, Any], gate_report: dict[str, Any]) -> list[str]:
    summary = as_dict(design_report.get("summary"))
    gate_summary = as_dict(gate_report.get("summary"))
    guardrails = as_dict(design_report.get("guardrails"))
    execution_design = as_dict(design_report.get("execution_design"))
    records = as_dict(execution_design.get("record_contracts"))
    preflight_record = as_dict(records.get("preflight_record"))
    rebuild_record = as_dict(records.get("rebuild_execution_record"))
    decision_record = as_dict(records.get("abort_or_acceptance_decision_record"))
    decision_policy = as_dict(execution_design.get("decision_policy"))

    blockers: list[str] = []
    if design_report.get("version") != "0.4.14.0":
        blockers.append("design_version_mismatch")
    if design_report.get("schema_kind") != "production_rebuild_execution_design":
        blockers.append("design_schema_mismatch")
    if summary.get("status") != "ready_for_production_rebuild_execution_design_gate":
        blockers.append("design_not_ready")
    if summary.get("allowed_next_step") != "production_rebuild_execution_design_gate":
        blockers.append("design_next_step_mismatch")

    expected_summary = {
        "authorization_record_required": True,
        "authorization_record_created": False,
        "authorization_granted": False,
        "live_preflight_run": False,
        "production_rebuild_executed": False,
        "qdrant_write_allowed": False,
        "rebuild_allowed": False,
        "full_eval": "not_run",
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            blockers.append(f"design_{key}_mismatch")
    if summary.get("blockers") != []:
        blockers.append("design_blockers_present")

    for key, expected in CRITICAL_DESIGN_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            blockers.append(f"design_guardrail_{key}_mismatch")

    if as_list(execution_design.get("required_authorization_fields")) != AUTHORIZATION_FIELD_ORDER:
        blockers.append("design_authorization_field_order_mismatch")
    if list(records.keys()) != REQUIRED_RECORD_ORDER:
        blockers.append("design_record_contract_order_mismatch")
    if set(as_list(preflight_record.get("checks"))) != REQUIRED_PREFLIGHT_CHECKS:
        blockers.append("design_preflight_checks_mismatch")
    if preflight_record.get("must_pass_before") != "backup_or_rollback_verification":
        blockers.append("design_preflight_gate_mismatch")
    if rebuild_record.get("must_not_be_created_in_this_version") is not True:
        blockers.append("design_rebuild_record_creation_mismatch")
    if set(as_list(execution_design.get("blocking_conditions"))) != REQUIRED_ABORT_CONDITIONS:
        blockers.append("design_abort_conditions_mismatch")
    if decision_record.get("automatic_acceptance_allowed") is not False:
        blockers.append("design_automatic_acceptance_mismatch")
    if decision_record.get("main_flow_change_authorized_by_this_record") is not False:
        blockers.append("design_main_flow_authorization_mismatch")
    if decision_policy.get("all_checks_pass") != "requires_explicit_human_acceptance_record":
        blockers.append("design_acceptance_policy_mismatch")
    if decision_policy.get("main_flow_change") != "not_authorized_by_this_design":
        blockers.append("design_main_flow_policy_mismatch")

    if gate_report.get("version") != "0.4.14.1":
        blockers.append("gate_version_mismatch")
    if gate_report.get("schema_kind") != "production_rebuild_execution_design_gate":
        blockers.append("gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("gate_not_passed")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("gate_failed_checks_present")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_record_scaffold":
        blockers.append("gate_next_step_mismatch")
    expected_gate_summary = {
        "authorization_record_created": False,
        "authorization_granted": False,
        "live_preflight_run": False,
        "production_rebuild_executed": False,
        "qdrant_write_allowed": False,
        "rebuild_allowed": False,
        "full_eval": "not_run",
    }
    for key, expected in expected_gate_summary.items():
        if gate_summary.get(key) != expected:
            blockers.append(f"gate_{key}_mismatch")
    return sorted(set(blockers))


def build_rows(ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, field_id in enumerate(AUTHORIZATION_FIELD_ORDER, start=1):
        rows.append(
            {
                "row_id": f"authorization_record_field_{index:02d}_{field_id}",
                "field_id": field_id,
                "requirement": "required",
                "source": "v0.4.14.0 execution_design.required_authorization_fields",
                "scaffold_status": "pending_human_input" if ready else "blocked",
                "human_input_required": True,
                "human_value_status": "not_collected",
                "empty_authorization_value": None,
                "authorization_granted": False,
                "live_preflight_allowed": False,
                "qdrant_write_allowed": False,
                "rebuild_allowed": False,
                "captures_formal_authorization_outcome": False,
                "guidance": FIELD_GUIDANCE[field_id],
            }
        )
    return rows


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
    }


def build_report(
    design_path: Path = DEFAULT_DESIGN_PATH,
    design_gate_path: Path = DEFAULT_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    design_report = load_json(design_path)
    gate_report = load_json(design_gate_path)
    blockers = source_blockers(design_report, gate_report)
    ready = not blockers
    rows = build_rows(ready)
    status = "pending_human_authorization_record" if ready else "blocked"
    allowed_next_step = "human_rebuild_authorization_record_scaffold_gate" if ready else "blocked"

    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_scaffold",
        "scope": "human rebuild authorization record scaffold only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "production_rebuild_execution_design": source_meta(design_path, design_report),
            "production_rebuild_execution_design_gate": source_meta(design_gate_path, gate_report),
        },
        "guardrails": GUARDRAILS,
        "authorization_record_scaffold_gate": {
            "status": "ready_for_human_authorization_record_review" if ready else "blocked",
            "allowed_use": "human_authorization_record_scaffold_only" if ready else "blocked",
            "formal_authorization_record_created": False,
            "human_authorization_record_created": False,
            "human_authorization_record_accepted": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "production_rebuild_executed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "captures_formal_authorization_outcome": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "allowed_use": "human_authorization_record_scaffold_only" if ready else "blocked",
            "allowed_next_step": allowed_next_step,
            "scaffold_row_count": len(rows),
            "required_field_count": len(AUTHORIZATION_FIELD_ORDER),
            "human_value_count": 0,
            "human_values_collected": False,
            "formal_authorization_record_created": False,
            "human_authorization_record_created": False,
            "human_authorization_record_accepted": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "production_rebuild_executed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
            "blockers": blockers,
        },
        "input_contract": {
            "required_source_reports": [
                "tests/production_rebuild_execution_design_report.json",
                "tests/production_rebuild_execution_design_gate_report.json",
            ],
            "required_authorization_fields": AUTHORIZATION_FIELD_ORDER,
            "required_record_contracts": REQUIRED_RECORD_ORDER,
            "required_preflight_checks": sorted(REQUIRED_PREFLIGHT_CHECKS),
            "required_abort_conditions": sorted(REQUIRED_ABORT_CONDITIONS),
        },
        "authorization_record_scaffold_rows": rows,
        "authorization_record_packet": {
            "packet_status": "scaffold_only" if ready else "blocked",
            "formal_authorization_record_created": False,
            "record_creation_status": "not_created",
            "record_acceptance_status": "not_accepted",
            "formal_authorization_value_status": "not_collected",
            "manual_completion_required": True,
            "operator_approval_note": "operator_approval is a future field and does not grant current approval.",
        },
        "next_version_handoff": {
            "allowed_next_step": allowed_next_step,
            "not_allowed_yet": [
                "accept the scaffold as authorization",
                "create formal authorization record",
                "run live preflight",
                "write Qdrant",
                "rebuild collection",
                "switch collection",
                "call RAG, embedding, or LLM services",
                "run full eval as a substitute for authorization",
                "modify runtime, ingestion, retriever, rerank, prompt, anchors, rules, fixtures, or eval cases",
            ],
        },
        "excluded_scope": [
            "human authorization value collection",
            "formal authorization record creation",
            "formal authorization acceptance",
            "live preflight",
            "Qdrant access or write",
            "collection rebuild or switch",
            "runtime or eval-case mutation",
        ],
        "traceability": {
            "source_of_truth": "v0.4.14.0 production rebuild execution design gated by v0.4.14.1",
            "authorization_field_count": len(AUTHORIZATION_FIELD_ORDER),
            "record_contract_count": len(REQUIRED_RECORD_ORDER),
            "preflight_check_count": len(REQUIRED_PREFLIGHT_CHECKS),
            "abort_condition_count": len(REQUIRED_ABORT_CONDITIONS),
        },
        "assertions": [
            {"assertion_id": "scaffold_only", "passed": True, "details": "The output is a blank scaffold only."},
            {"assertion_id": "no_human_values", "passed": True, "details": "All human values remain not_collected."},
            {"assertion_id": "no_authorization", "passed": True, "details": "No authorization is created or accepted."},
            {"assertion_id": "no_runtime_action", "passed": True, "details": "No live preflight, Qdrant write, rebuild, or main-flow change is authorized."},
        ],
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        new_blockers = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["authorization_record_scaffold_gate"]["status"] = "blocked"
        report["authorization_record_scaffold_gate"]["allowed_use"] = "blocked"
        report["authorization_record_scaffold_gate"]["blockers"] = new_blockers
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["blockers"] = new_blockers
        report["forbidden_output_keys_detected"] = forbidden
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.14.2 Human Rebuild Authorization Record Scaffold",
        "",
        "本版本只生成未来人工授权记录的空白脚手架。它不是授权记录，不收集人工值，不接受审批结论，不运行 live preflight，不访问或写入 Qdrant，也不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许用途: `{summary.get('allowed_use')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 字段行数: `{summary.get('scaffold_row_count')}`",
        f"- 已收集人工值: `{summary.get('human_value_count')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已创建授权记录: `{summary.get('human_authorization_record_created')}`",
        f"- 是否已接受授权记录: `{summary.get('human_authorization_record_accepted')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否已运行 live preflight: `{summary.get('live_preflight_run')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 脚手架字段",
        "",
    ]
    for row in report.get("authorization_record_scaffold_rows", []):
        lines.append(
            f"- `{row.get('field_id')}`: `{row.get('human_value_status')}`, "
            f"required=`{row.get('human_input_required')}`"
        )
    lines.extend(
        [
            "",
            "通过本 scaffold 只允许进入 `human_rebuild_authorization_record_scaffold_gate`。它仍不代表已经允许 live preflight、Qdrant write、production rebuild 或主流程改动。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.2 human rebuild authorization record scaffold.")
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN_PATH)
    parser.add_argument("--design-gate", type=Path, default=DEFAULT_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.design, args.design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization record scaffold: "
        f"{summary.get('status')}, rows={summary.get('scaffold_row_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
