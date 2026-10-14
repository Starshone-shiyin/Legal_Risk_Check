"""Build the v0.4.14.8 human rebuild authorization input workflow design.

The design reads only the saved v0.4.14.6 blank draft scaffold and v0.4.14.7
draft scaffold gate reports. It defines a future human input, import,
validation, and confirmation workflow, but it does not collect human values,
create or accept formal authorization, run live preflight, access Qdrant,
rebuild collections, call RAG/embedding/LLM, run full eval, or mutate runtime
and eval artifacts.
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


VERSION = "0.4.14.8"

DEFAULT_DRAFT_SCAFFOLD_PATH = legacy_report_path("human_rebuild_authorization_record_draft_scaffold_report.json")
DEFAULT_DRAFT_SCAFFOLD_GATE_PATH = legacy_report_path("human_rebuild_authorization_record_draft_scaffold_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_input_workflow_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md")

FIELD_ORDER = [
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

FIELD_TO_SECTION = {
    "target_collection": "target_and_scope",
    "rebuild_scope": "target_and_scope",
    "source_version": "source_lineage",
    "expected_id_drift_acknowledgement": "risk_acknowledgement",
    "backup_plan": "safeguards",
    "rollback_plan": "safeguards",
    "operator_approval": "formal_authorization_inputs",
    "maintenance_window": "execution_window",
    "post_rebuild_validation_plan": "post_rebuild_validation",
    "abort_conditions_acknowledgement": "risk_acknowledgement",
}

SECTION_ORDER = [
    "target_and_scope",
    "source_lineage",
    "risk_acknowledgement",
    "safeguards",
    "formal_authorization_inputs",
    "execution_window",
    "post_rebuild_validation",
]

REQUIRED_SCAFFOLD_GUARDRAILS = {
    "draft_scaffold_only": True,
    "saved_reports_only": True,
    "human_values_collected": False,
    "draft_record_scaffold_created": True,
    "draft_record_created": False,
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

GUARDRAILS = {
    "input_workflow_design_only": True,
    "saved_reports_only": True,
    "human_values_collected": False,
    "input_form_created": False,
    "input_values_imported": False,
    "input_values_validated": False,
    "draft_record_created": False,
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

REQUIRED_NOT_ALLOWED = {
    "collect human authorization values",
    "create formal authorization record",
    "accept formal authorization record",
    "run live preflight",
    "write Qdrant",
    "rebuild collection",
    "switch collection",
    "call RAG, embedding, or LLM services",
    "run full eval as a substitute for authorization",
    "modify runtime, ingestion, retriever, rerank, prompt, anchors, rules, fixtures, or eval cases",
}

FUTURE_VALIDATION_POLICY = {
    "all_required_fields_present": "required_for_future_record",
    "explicit_yes_no_authorization": "required_for_future_record",
    "operator_approval_effect": "future_field_only_not_current_approval",
    "preflight_authorization_effect": "none_in_this_version",
    "qdrant_write_authorization_effect": "none_in_this_version",
    "rebuild_authorization_effect": "none_in_this_version",
}

WORKFLOW_PHASES = [
    {
        "phase_id": "prepare_blank_input_packet",
        "sequence": 1,
        "purpose": "future blank packet preparation from the draft scaffold",
        "input_value_effect": "none_in_this_version",
        "authorization_effect": "none",
    },
    {
        "phase_id": "human_entry_session",
        "sequence": 2,
        "purpose": "future human completion of required fields",
        "input_value_effect": "not_collected_in_this_version",
        "authorization_effect": "none",
    },
    {
        "phase_id": "offline_import_staging",
        "sequence": 3,
        "purpose": "future import of completed fields into a staged packet",
        "input_value_effect": "not_imported_in_this_version",
        "authorization_effect": "none",
    },
    {
        "phase_id": "field_validation_review",
        "sequence": 4,
        "purpose": "future validation of completeness, shape, and acknowledgement fields",
        "input_value_effect": "not_validated_in_this_version",
        "authorization_effect": "none",
    },
    {
        "phase_id": "reviewer_confirmation_packet",
        "sequence": 5,
        "purpose": "future reviewer confirmation envelope before any formal record can exist",
        "input_value_effect": "not_confirmed_in_this_version",
        "authorization_effect": "none",
    },
    {
        "phase_id": "formal_record_candidate_handoff",
        "sequence": 6,
        "purpose": "future handoff to a separate formal record candidate design",
        "input_value_effect": "handoff_only_in_this_version",
        "authorization_effect": "none",
    },
]

FIELD_INPUT_SHAPES = {
    "target_collection": "non_empty_collection_name",
    "rebuild_scope": "structured_include_exclude_scope",
    "source_version": "source_version_or_commit_reference",
    "expected_id_drift_acknowledgement": "explicit_acknowledgement_text",
    "backup_plan": "backup_or_snapshot_reference",
    "rollback_plan": "rollback_owner_and_steps_reference",
    "operator_approval": "future_explicit_yes_no_authorization",
    "maintenance_window": "future_time_window_and_owner",
    "post_rebuild_validation_plan": "validation_owner_and_checks_reference",
    "abort_conditions_acknowledgement": "explicit_acknowledgement_text",
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


def scaffold_rows_locked(draft_scaffold: dict[str, Any]) -> bool:
    rows = [row for row in as_list(draft_scaffold.get("rows")) if isinstance(row, dict)]
    if len(rows) != len(FIELD_ORDER):
        return False
    if [row.get("field_id") for row in rows] != FIELD_ORDER:
        return False
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        row = rows[index - 1]
        if row.get("section_id") != FIELD_TO_SECTION[field_id]:
            return False
        if row.get("fill_sequence") != index:
            return False
        if row.get("value_status") != "not_collected":
            return False
        if row.get("human_value") is not None:
            return False
        if row.get("normalized_value") is not None:
            return False
        if row.get("authorization_effect_now") != "none":
            return False
        if row.get("authorization_granted") is not False:
            return False
        if row.get("qdrant_write_allowed") is not False:
            return False
        if row.get("rebuild_allowed") is not False:
            return False
    return True


def scaffold_sections_locked(draft_scaffold: dict[str, Any]) -> bool:
    sections = [row for row in as_list(draft_scaffold.get("sections")) if isinstance(row, dict)]
    if draft_scaffold.get("section_order") != SECTION_ORDER:
        return False
    if [row.get("section_id") for row in sections] != SECTION_ORDER:
        return False
    for section_id in SECTION_ORDER:
        section = next(row for row in sections if row.get("section_id") == section_id)
        expected_fields = [field for field in FIELD_ORDER if FIELD_TO_SECTION[field] == section_id]
        if section.get("field_ids") != expected_fields:
            return False
        if section.get("value_collection") != "not_collected":
            return False
        if section.get("authorization_effect") != "none":
            return False
    return True


def source_blockers(draft_scaffold_report: dict[str, Any], draft_scaffold_gate: dict[str, Any]) -> list[str]:
    summary = as_dict(draft_scaffold_report.get("summary"))
    inputs = as_dict(draft_scaffold_report.get("inputs"))
    design_input = as_dict(inputs.get("human_rebuild_authorization_record_draft_design"))
    gate_input = as_dict(inputs.get("human_rebuild_authorization_record_draft_design_gate"))
    guardrails = as_dict(draft_scaffold_report.get("guardrails"))
    draft_scaffold = as_dict(draft_scaffold_report.get("draft_scaffold"))
    handoff = as_dict(draft_scaffold_report.get("handoff"))
    traceability = as_dict(draft_scaffold_report.get("traceability"))
    gate_summary = as_dict(draft_scaffold_gate.get("summary"))

    blockers: list[str] = []
    if draft_scaffold_report.get("version") != "0.4.14.6":
        blockers.append("draft_scaffold_version_mismatch")
    if draft_scaffold_report.get("schema_kind") != "human_rebuild_authorization_record_draft_scaffold":
        blockers.append("draft_scaffold_schema_mismatch")
    if summary.get("status") != "pending_human_rebuild_authorization_record_draft_scaffold_gate":
        blockers.append("draft_scaffold_status_mismatch")
    if summary.get("allowed_next_step") != "human_rebuild_authorization_record_draft_scaffold_gate":
        blockers.append("draft_scaffold_next_step_mismatch")
    for key, expected in {
        "draft_scaffold_only": True,
        "draft_record_scaffold_created": True,
        "draft_record_created": False,
        "field_count": 10,
        "section_count": 7,
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
    }.items():
        if summary.get(key) != expected:
            blockers.append(f"draft_scaffold_{key}_mismatch")
    if summary.get("blockers") != []:
        blockers.append("draft_scaffold_blockers_present")
    if set(inputs) != {"human_rebuild_authorization_record_draft_design", "human_rebuild_authorization_record_draft_design_gate"}:
        blockers.append("draft_scaffold_input_lineage_mismatch")
    if design_input.get("version") != "0.4.14.4" or design_input.get("schema_kind") != "human_rebuild_authorization_record_draft_design":
        blockers.append("draft_scaffold_design_input_mismatch")
    if gate_input.get("version") != "0.4.14.5" or gate_input.get("schema_kind") != "human_rebuild_authorization_record_draft_design_gate":
        blockers.append("draft_scaffold_design_gate_input_mismatch")
    if set(guardrails) != set(REQUIRED_SCAFFOLD_GUARDRAILS):
        blockers.append("draft_scaffold_guardrail_keys_mismatch")
    for key, expected in REQUIRED_SCAFFOLD_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            blockers.append(f"draft_scaffold_guardrail_{key}_mismatch")
    if not scaffold_rows_locked(draft_scaffold):
        blockers.append("draft_scaffold_row_contract_mismatch")
    if not scaffold_sections_locked(draft_scaffold):
        blockers.append("draft_scaffold_section_contract_mismatch")
    if as_dict(draft_scaffold.get("future_validation_policy")) != FUTURE_VALIDATION_POLICY:
        blockers.append("draft_scaffold_future_validation_policy_mismatch")
    if handoff.get("allowed_next_step") != "human_rebuild_authorization_record_draft_scaffold_gate":
        blockers.append("draft_scaffold_handoff_next_step_mismatch")
    if set(as_list(handoff.get("not_allowed_yet"))) != REQUIRED_NOT_ALLOWED:
        blockers.append("draft_scaffold_handoff_boundary_mismatch")
    if traceability.get("source_of_truth") != "v0.4.14.4 draft design gated by v0.4.14.5":
        blockers.append("draft_scaffold_traceability_source_mismatch")
    if traceability.get("scaffold_field_count") != 10 or traceability.get("section_count") != 7:
        blockers.append("draft_scaffold_traceability_count_mismatch")

    if draft_scaffold_gate.get("version") != "0.4.14.7":
        blockers.append("draft_scaffold_gate_version_mismatch")
    if draft_scaffold_gate.get("schema_kind") != "human_rebuild_authorization_record_draft_scaffold_gate":
        blockers.append("draft_scaffold_gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("draft_scaffold_gate_not_passed")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("draft_scaffold_gate_failed_checks_present")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_record_input_workflow_design":
        blockers.append("draft_scaffold_gate_next_step_mismatch")
    for key, expected in {
        "human_values_collected": False,
        "draft_record_created": False,
        "formal_authorization_record_created": False,
        "human_authorization_record_created": False,
        "human_authorization_record_accepted": False,
        "authorization_granted": False,
        "live_preflight_run": False,
        "production_rebuild_executed": False,
        "qdrant_write_allowed": False,
        "rebuild_allowed": False,
        "full_eval": "not_run",
        "forbidden_output_key_count": 0,
    }.items():
        if gate_summary.get(key) != expected:
            blockers.append(f"draft_scaffold_gate_{key}_mismatch")
    return sorted(set(blockers))


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
    }


def scaffold_rows_by_field(draft_scaffold_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    draft_scaffold = as_dict(draft_scaffold_report.get("draft_scaffold"))
    rows = [row for row in as_list(draft_scaffold.get("rows")) if isinstance(row, dict)]
    return {str(row.get("field_id")): row for row in rows}


def build_field_input_contracts(draft_scaffold_report: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows_by_field = scaffold_rows_by_field(draft_scaffold_report)
    contracts = []
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        scaffold_row = rows_by_field.get(field_id, {})
        contracts.append({
            "contract_id": f"input_contract_{index:02d}_{field_id}",
            "source_row_id": scaffold_row.get("row_id"),
            "section_id": FIELD_TO_SECTION[field_id],
            "field_id": field_id,
            "requirement": "required",
            "input_sequence": index,
            "future_input_required": True,
            "future_input_shape": FIELD_INPUT_SHAPES[field_id],
            "current_value_status": "not_collected",
            "current_human_value": None,
            "current_normalized_value": None,
            "workflow_design_status": "ready_for_future_input_design_gate" if ready else "blocked",
            "validation_status_now": "not_run",
            "authorization_effect_now": "none",
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "guidance_source": scaffold_row.get("guidance"),
        })
    return contracts


def build_report(
    draft_scaffold_path: Path = DEFAULT_DRAFT_SCAFFOLD_PATH,
    draft_scaffold_gate_path: Path = DEFAULT_DRAFT_SCAFFOLD_GATE_PATH,
) -> dict[str, Any]:
    draft_scaffold = load_json(draft_scaffold_path)
    draft_scaffold_gate = load_json(draft_scaffold_gate_path)
    blockers = source_blockers(draft_scaffold, draft_scaffold_gate)
    ready = not blockers
    field_contracts = build_field_input_contracts(draft_scaffold, ready)
    status = "ready_for_human_rebuild_authorization_record_input_workflow_design_gate" if ready else "blocked"
    allowed_next_step = "human_rebuild_authorization_record_input_workflow_design_gate" if ready else "blocked"

    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_input_workflow_design",
        "scope": "future human authorization input workflow design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_draft_scaffold": source_meta(draft_scaffold_path, draft_scaffold),
            "human_rebuild_authorization_record_draft_scaffold_gate": source_meta(draft_scaffold_gate_path, draft_scaffold_gate),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "input_workflow_design_only": True,
            "workflow_phase_count": len(WORKFLOW_PHASES),
            "field_input_contract_count": len(field_contracts),
            "human_value_count": 0,
            "human_values_collected": False,
            "input_form_created": False,
            "input_values_imported": False,
            "input_values_validated": False,
            "draft_record_created": False,
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
        "input_workflow_design_gate": {
            "status": status,
            "allowed_use": "workflow_design_review_only" if ready else "blocked",
            "human_values_collected": False,
            "input_form_created": False,
            "input_values_imported": False,
            "input_values_validated": False,
            "formal_authorization_record_created": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "blockers": blockers,
        },
        "input_workflow_design": {
            "workflow_status": "design_only",
            "value_collection_status": "not_collected",
            "workflow_phases": WORKFLOW_PHASES,
            "field_input_contracts": field_contracts,
            "future_validation_policy": FUTURE_VALIDATION_POLICY,
            "future_import_policy": {
                "accepted_source": "future_completed_human_input_packet",
                "staging_required": True,
                "reviewer_confirmation_required": True,
                "formal_record_creation_effect": "none_in_this_version",
                "authorization_effect": "none_in_this_version",
            },
        },
        "handoff": {
            "allowed_next_step": allowed_next_step,
            "not_allowed_yet": [
                "collect human authorization values",
                "create input form or importer",
                "import completed human values",
                "validate completed human values",
                "create formal authorization record",
                "accept formal authorization record",
                "run live preflight",
                "write Qdrant",
                "rebuild collection",
                "switch collection",
                "call RAG, embedding, or LLM services",
                "run full eval as a substitute for authorization",
                "modify runtime, ingestion, retriever, rerank, prompt, anchors, rules, fixtures, or eval cases",
            ],
        },
        "traceability": {
            "source_of_truth": "v0.4.14.6 draft scaffold gated by v0.4.14.7",
            "source_field_count": len(FIELD_ORDER),
            "field_input_contract_count": len(field_contracts),
            "workflow_phase_count": len(WORKFLOW_PHASES),
            "next_gate": "human_rebuild_authorization_record_input_workflow_design_gate",
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        new_blockers = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["blockers"] = new_blockers
        report["input_workflow_design_gate"]["status"] = "blocked"
        report["input_workflow_design_gate"]["allowed_use"] = "blocked"
        report["input_workflow_design_gate"]["blockers"] = new_blockers
        report["forbidden_output_keys_detected"] = forbidden
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("input_workflow_design"))
    lines = [
        "# v0.4.14.8 Human Rebuild Authorization Record Input Workflow Design",
        "",
        "本版本只设计未来人工输入、导入、校验和确认流程。它不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 流程阶段数: `{summary.get('workflow_phase_count')}`",
        f"- 字段输入契约数: `{summary.get('field_input_contract_count')}`",
        f"- 已收集人工值: `{summary.get('human_value_count')}`",
        f"- 是否已创建输入表单: `{summary.get('input_form_created')}`",
        f"- 是否已导入人工值: `{summary.get('input_values_imported')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 未来流程阶段",
        "",
    ]
    for phase in design.get("workflow_phases", []):
        lines.append(f"- `{phase.get('sequence')}` `{phase.get('phase_id')}`: {phase.get('purpose')}; effect=`none`")
    lines.extend([
        "",
        "通过本 design 只允许进入 `human_rebuild_authorization_record_input_workflow_design_gate`。它仍不代表已经允许填写真实人工值、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.8 human rebuild authorization input workflow design.")
    parser.add_argument("--draft-scaffold", type=Path, default=DEFAULT_DRAFT_SCAFFOLD_PATH)
    parser.add_argument("--draft-scaffold-gate", type=Path, default=DEFAULT_DRAFT_SCAFFOLD_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.draft_scaffold, args.draft_scaffold_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization input workflow design: "
        f"{summary.get('status')}, phases={summary.get('workflow_phase_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
