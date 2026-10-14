"""Build the v0.4.14.12 human rebuild authorization input form scaffold.

The scaffold reads only the saved v0.4.14.10 input packet scaffold and
v0.4.14.11 input packet scaffold gate reports. It creates a blank future input
form scaffold for review, but it does not create a runnable input form or
importer, collect, import, normalize, or validate real human values, create or
accept formal authorization, run live preflight, access Qdrant, rebuild
collections, call RAG/embedding/LLM, run full eval, or mutate runtime and eval
artifacts.
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


VERSION = "0.4.14.12"

DEFAULT_INPUT_PACKET_SCAFFOLD_PATH = legacy_report_path(
    "human_rebuild_authorization_record_input_packet_scaffold_report.json"
)
DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH = legacy_report_path(
    "human_rebuild_authorization_record_input_packet_scaffold_gate_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_input_form_scaffold_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md")

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

SECTION_LABELS_ZH = {
    "target_and_scope": "目标与范围",
    "source_lineage": "来源版本",
    "risk_acknowledgement": "风险确认",
    "safeguards": "备份与回滚",
    "formal_authorization_inputs": "正式授权输入",
    "execution_window": "执行窗口",
    "post_rebuild_validation": "重建后验证",
}

FIELD_LABELS_ZH = {
    "target_collection": "目标集合",
    "rebuild_scope": "重建范围",
    "source_version": "来源版本",
    "expected_id_drift_acknowledgement": "预期 ID 漂移确认",
    "backup_plan": "备份方案",
    "rollback_plan": "回滚方案",
    "operator_approval": "操作人批准",
    "maintenance_window": "维护窗口",
    "post_rebuild_validation_plan": "重建后验证方案",
    "abort_conditions_acknowledgement": "终止条件确认",
}

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

FIELD_WIDGET_HINTS = {
    "non_empty_collection_name": "future_single_line_text",
    "structured_include_exclude_scope": "future_structured_text_area",
    "source_version_or_commit_reference": "future_single_line_reference",
    "explicit_acknowledgement_text": "future_acknowledgement_text_area",
    "backup_or_snapshot_reference": "future_reference_text_area",
    "rollback_owner_and_steps_reference": "future_reference_text_area",
    "future_explicit_yes_no_authorization": "future_yes_no_authorization_control",
    "future_time_window_and_owner": "future_time_window_reference",
    "validation_owner_and_checks_reference": "future_reference_text_area",
}

FIELD_HELP_TEXT_ZH = {
    "target_collection": "未来由人工填写目标 Qdrant collection 名称；本版本不接收该值。",
    "rebuild_scope": "未来说明包含与排除的 rebuild 范围；本版本不授权该范围。",
    "source_version": "未来填写来源版本或 commit 引用；本版本不锁定生产来源。",
    "expected_id_drift_acknowledgement": "未来确认已理解 chunk/document id 漂移风险；本版本不记录确认结果。",
    "backup_plan": "未来填写备份或 snapshot 引用；本版本不验证备份是否存在。",
    "rollback_plan": "未来填写回滚负责人和步骤引用；本版本不执行或验证回滚。",
    "operator_approval": "未来只能作为明确 yes/no 授权输入；本版本不构成当前批准。",
    "maintenance_window": "未来填写维护窗口和负责人；本版本不安排执行时间。",
    "post_rebuild_validation_plan": "未来填写重建后验证负责人和检查项；本版本不运行验证。",
    "abort_conditions_acknowledgement": "未来确认已理解终止条件；本版本不记录确认结果。",
}

REQUIRED_PACKET_GUARDRAILS = {
    "input_packet_scaffold_only": True,
    "saved_reports_only": True,
    "blank_input_packet_scaffold_created": True,
    "input_form_created": False,
    "input_importer_created": False,
    "human_values_collected": False,
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

GUARDRAILS = {
    "input_form_scaffold_only": True,
    "saved_reports_only": True,
    "blank_input_form_scaffold_created": True,
    "runnable_input_form_created": False,
    "input_form_created": False,
    "input_importer_created": False,
    "human_values_collected": False,
    "input_values_imported": False,
    "input_values_validated": False,
    "form_values_exported": False,
    "form_values_accepted": False,
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

REQUIRED_FUTURE_VALIDATION_POLICY = {
    "all_required_fields_present": "required_for_future_record",
    "explicit_yes_no_authorization": "required_for_future_record",
    "operator_approval_effect": "future_field_only_not_current_approval",
    "preflight_authorization_effect": "none_in_this_version",
    "qdrant_write_authorization_effect": "none_in_this_version",
    "rebuild_authorization_effect": "none_in_this_version",
}

REQUIRED_FUTURE_IMPORT_POLICY = {
    "accepted_source": "future_completed_human_input_packet",
    "staging_required": True,
    "reviewer_confirmation_required": True,
    "formal_record_creation_effect": "none_in_this_version",
    "authorization_effect": "none_in_this_version",
}

REQUIRED_PACKET_COMPLETION_POLICY = {
    "all_required_fields_blank_in_this_version": True,
    "future_completed_packet_required_before_import": True,
    "current_packet_importable": False,
    "current_packet_authorization_effect": "none",
}

FORM_EXPORT_POLICY = {
    "future_completed_form_export_required_before_import": True,
    "current_form_exportable": False,
    "current_form_importable": False,
    "current_form_authorization_effect": "none",
}

FORM_COMPLETION_POLICY = {
    "all_required_fields_blank_in_this_version": True,
    "future_completed_form_required_before_export": True,
    "current_form_submittable": False,
    "current_form_authorization_effect": "none",
}

REQUIRED_NOT_ALLOWED = {
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
    "enter values into the blank input packet",
}

FORM_SCAFFOLD_NOT_ALLOWED = sorted(
    REQUIRED_NOT_ALLOWED
    | {
        "render an interactive input form",
        "enter values into the blank input form scaffold",
        "export completed form values",
    }
)

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "authorized_actions",
    "ready_to_apply",
    "commands",
    "rebuild_steps",
    "qdrant_operation_log",
    "implementation_plan",
    "execution_commands",
    "submitted_values",
    "form_submission",
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


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
    }


def packet_rows_by_id(packet_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scaffold = as_dict(packet_report.get("input_packet_scaffold"))
    rows = [row for row in as_list(scaffold.get("rows")) if isinstance(row, dict)]
    return {str(row.get("field_id")): row for row in rows}


def packet_sections_locked(packet_report: dict[str, Any]) -> bool:
    scaffold = as_dict(packet_report.get("input_packet_scaffold"))
    sections = [row for row in as_list(scaffold.get("sections")) if isinstance(row, dict)]
    if scaffold.get("scaffold_status") != "blank_input_packet_scaffold":
        return False
    if scaffold.get("packet_status") != "not_completed":
        return False
    if scaffold.get("packet_acceptance_status") != "not_accepted":
        return False
    if scaffold.get("value_collection_status") != "not_collected":
        return False
    if scaffold.get("section_order") != SECTION_ORDER:
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
        if section.get("input_form_effect") != "none":
            return False
        if section.get("import_effect") != "none":
            return False
        if section.get("authorization_effect") != "none":
            return False
    return True


def packet_rows_locked(packet_report: dict[str, Any]) -> bool:
    rows_by_id = packet_rows_by_id(packet_report)
    if [rows_by_id.get(field_id, {}).get("field_id") for field_id in FIELD_ORDER] != FIELD_ORDER:
        return False
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        row = rows_by_id[field_id]
        if row.get("row_id") != f"input_packet_row_{index:02d}_{field_id}":
            return False
        if row.get("section_id") != FIELD_TO_SECTION[field_id]:
            return False
        if row.get("requirement") != "required":
            return False
        if row.get("input_sequence") != index:
            return False
        if row.get("future_input_shape") != FIELD_INPUT_SHAPES[field_id]:
            return False
        if row.get("entry_status") != "blank":
            return False
        if row.get("value_status") != "not_collected":
            return False
        if row.get("human_value") is not None:
            return False
        if row.get("normalized_value") is not None:
            return False
        if row.get("import_status") != "not_imported":
            return False
        if row.get("validation_status_now") != "not_run":
            return False
        if row.get("authorization_effect_now") != "none":
            return False
        if row.get("authorization_granted") is not False:
            return False
        if row.get("qdrant_write_allowed") is not False:
            return False
        if row.get("rebuild_allowed") is not False:
            return False
        if not isinstance(row.get("guidance_source"), str) or not row.get("guidance_source"):
            return False
    return True


def packet_policy_locked(packet_report: dict[str, Any]) -> bool:
    scaffold = as_dict(packet_report.get("input_packet_scaffold"))
    return (
        as_dict(scaffold.get("future_validation_policy")) == REQUIRED_FUTURE_VALIDATION_POLICY
        and as_dict(scaffold.get("future_import_policy")) == REQUIRED_FUTURE_IMPORT_POLICY
        and as_dict(scaffold.get("packet_completion_policy")) == REQUIRED_PACKET_COMPLETION_POLICY
    )


def source_blockers(input_packet_scaffold: dict[str, Any], input_packet_scaffold_gate: dict[str, Any]) -> list[str]:
    summary = as_dict(input_packet_scaffold.get("summary"))
    guardrails = as_dict(input_packet_scaffold.get("guardrails"))
    inputs = as_dict(input_packet_scaffold.get("inputs"))
    design_input = as_dict(inputs.get("human_rebuild_authorization_record_input_workflow_design"))
    design_gate_input = as_dict(inputs.get("human_rebuild_authorization_record_input_workflow_design_gate"))
    handoff = as_dict(input_packet_scaffold.get("handoff"))
    traceability = as_dict(input_packet_scaffold.get("traceability"))
    gate_summary = as_dict(input_packet_scaffold_gate.get("summary"))

    blockers: list[str] = []
    if input_packet_scaffold.get("version") != "0.4.14.10":
        blockers.append("input_packet_scaffold_version_mismatch")
    if input_packet_scaffold.get("schema_kind") != "human_rebuild_authorization_record_input_packet_scaffold":
        blockers.append("input_packet_scaffold_schema_mismatch")
    if summary.get("status") != "pending_human_rebuild_authorization_record_input_packet_scaffold_gate":
        blockers.append("input_packet_scaffold_status_mismatch")
    if summary.get("allowed_next_step") != "human_rebuild_authorization_record_input_packet_scaffold_gate":
        blockers.append("input_packet_scaffold_next_step_mismatch")
    for key, expected in {
        "input_packet_scaffold_only": True,
        "blank_input_packet_scaffold_created": True,
        "packet_field_count": 10,
        "packet_section_count": 7,
        "human_value_count": 0,
        "human_values_collected": False,
        "input_form_created": False,
        "input_importer_created": False,
        "input_values_imported": False,
        "input_values_validated": False,
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
            blockers.append(f"input_packet_scaffold_{key}_mismatch")
    if summary.get("blockers") != []:
        blockers.append("input_packet_scaffold_blockers_present")
    if set(inputs) != {
        "human_rebuild_authorization_record_input_workflow_design",
        "human_rebuild_authorization_record_input_workflow_design_gate",
    }:
        blockers.append("input_packet_scaffold_source_lineage_mismatch")
    if (
        design_input.get("version") != "0.4.14.8"
        or design_input.get("schema_kind") != "human_rebuild_authorization_record_input_workflow_design"
        or design_input.get("status") != "ready_for_human_rebuild_authorization_record_input_workflow_design_gate"
    ):
        blockers.append("input_packet_scaffold_design_input_mismatch")
    if (
        design_gate_input.get("version") != "0.4.14.9"
        or design_gate_input.get("schema_kind") != "human_rebuild_authorization_record_input_workflow_design_gate"
        or design_gate_input.get("status") != "passed"
    ):
        blockers.append("input_packet_scaffold_design_gate_input_mismatch")
    if set(guardrails) != set(REQUIRED_PACKET_GUARDRAILS):
        blockers.append("input_packet_scaffold_guardrail_keys_mismatch")
    for key, expected in REQUIRED_PACKET_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            blockers.append(f"input_packet_scaffold_guardrail_{key}_mismatch")
    if not packet_sections_locked(input_packet_scaffold):
        blockers.append("input_packet_scaffold_section_contract_mismatch")
    if not packet_rows_locked(input_packet_scaffold):
        blockers.append("input_packet_scaffold_row_contract_mismatch")
    if not packet_policy_locked(input_packet_scaffold):
        blockers.append("input_packet_scaffold_policy_mismatch")
    if handoff.get("allowed_next_step") != "human_rebuild_authorization_record_input_packet_scaffold_gate":
        blockers.append("input_packet_scaffold_handoff_next_step_mismatch")
    if set(as_list(handoff.get("not_allowed_yet"))) != REQUIRED_NOT_ALLOWED:
        blockers.append("input_packet_scaffold_handoff_boundary_mismatch")
    if traceability.get("source_of_truth") != "v0.4.14.8 input workflow design gated by v0.4.14.9":
        blockers.append("input_packet_scaffold_traceability_source_mismatch")
    if (
        traceability.get("source_field_count") != 10
        or traceability.get("packet_field_count") != 10
        or traceability.get("section_count") != 7
        or traceability.get("next_gate") != "human_rebuild_authorization_record_input_packet_scaffold_gate"
    ):
        blockers.append("input_packet_scaffold_traceability_count_mismatch")
    if forbidden_output_keys(input_packet_scaffold):
        blockers.append("input_packet_scaffold_forbidden_output_key_present")

    if input_packet_scaffold_gate.get("version") != "0.4.14.11":
        blockers.append("input_packet_scaffold_gate_version_mismatch")
    if input_packet_scaffold_gate.get("schema_kind") != "human_rebuild_authorization_record_input_packet_scaffold_gate":
        blockers.append("input_packet_scaffold_gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("input_packet_scaffold_gate_not_passed")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("input_packet_scaffold_gate_failed_checks_present")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_record_input_form_scaffold":
        blockers.append("input_packet_scaffold_gate_next_step_mismatch")
    for key, expected in {
        "human_values_collected": False,
        "input_form_created": False,
        "input_importer_created": False,
        "input_values_imported": False,
        "input_values_validated": False,
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
            blockers.append(f"input_packet_scaffold_gate_{key}_mismatch")
    if forbidden_output_keys(input_packet_scaffold_gate):
        blockers.append("input_packet_scaffold_gate_forbidden_output_key_present")
    return sorted(set(blockers))


def build_form_fields(input_packet_scaffold: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    packet_rows = packet_rows_by_id(input_packet_scaffold)
    fields = []
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        packet_row = packet_rows.get(field_id, {})
        future_shape = FIELD_INPUT_SHAPES[field_id]
        fields.append({
            "form_field_id": f"input_form_field_{index:02d}_{field_id}",
            "source_packet_row_id": packet_row.get("row_id"),
            "source_contract_id": packet_row.get("source_contract_id"),
            "section_id": FIELD_TO_SECTION[field_id],
            "field_id": field_id,
            "label_zh": FIELD_LABELS_ZH[field_id],
            "display_order": index,
            "input_sequence": index,
            "requirement": "required",
            "required": True,
            "future_input_shape": future_shape,
            "future_widget_hint": FIELD_WIDGET_HINTS[future_shape],
            "future_editable": True,
            "editable_now": False,
            "interactive_control_created": False,
            "entry_status": "blank",
            "field_status": "blank",
            "value_status": "not_collected",
            "human_value": None,
            "normalized_value": None,
            "import_status": "not_imported",
            "validation_status_now": "not_run",
            "review_status": "pending_future_human_input",
            "authorization_effect_now": "none",
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "form_scaffold_status": "ready_for_future_form_scaffold_gate" if ready else "blocked",
            "help_text_zh": FIELD_HELP_TEXT_ZH[field_id],
            "guidance_source": packet_row.get("guidance_source"),
        })
    return fields


def build_form_sections(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "section_id": section_id,
            "label_zh": SECTION_LABELS_ZH[section_id],
            "field_ids": [field["field_id"] for field in fields if field["section_id"] == section_id],
            "value_collection": "not_collected",
            "interactive_form_effect": "none",
            "import_effect": "none",
            "authorization_effect": "none",
        }
        for section_id in SECTION_ORDER
    ]


def build_report(
    input_packet_scaffold_path: Path = DEFAULT_INPUT_PACKET_SCAFFOLD_PATH,
    input_packet_scaffold_gate_path: Path = DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH,
) -> dict[str, Any]:
    input_packet_scaffold = load_json(input_packet_scaffold_path)
    input_packet_scaffold_gate = load_json(input_packet_scaffold_gate_path)
    blockers = source_blockers(input_packet_scaffold, input_packet_scaffold_gate)
    ready = not blockers
    fields = build_form_fields(input_packet_scaffold, ready)
    status = "ready_for_human_rebuild_authorization_record_input_form_scaffold_gate" if ready else "blocked"
    allowed_next_step = "human_rebuild_authorization_record_input_form_scaffold_gate" if ready else "blocked"

    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_input_form_scaffold",
        "scope": "blank future human authorization input form scaffold only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_input_packet_scaffold": source_meta(
                input_packet_scaffold_path, input_packet_scaffold
            ),
            "human_rebuild_authorization_record_input_packet_scaffold_gate": source_meta(
                input_packet_scaffold_gate_path, input_packet_scaffold_gate
            ),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "input_form_scaffold_only": True,
            "blank_input_form_scaffold_created": ready,
            "form_section_count": len(SECTION_ORDER),
            "form_field_count": len(fields),
            "human_value_count": 0,
            "human_values_collected": False,
            "runnable_input_form_created": False,
            "input_form_created": False,
            "input_importer_created": False,
            "input_values_imported": False,
            "input_values_validated": False,
            "form_values_exported": False,
            "form_values_accepted": False,
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
        "input_form_scaffold_gate": {
            "status": status,
            "allowed_use": "blank_input_form_scaffold_only" if ready else "blocked",
            "blank_input_form_scaffold_created": ready,
            "runnable_input_form_created": False,
            "input_form_created": False,
            "input_importer_created": False,
            "human_values_collected": False,
            "input_values_imported": False,
            "input_values_validated": False,
            "form_values_exported": False,
            "form_values_accepted": False,
            "formal_authorization_record_created": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "blockers": blockers,
        },
        "input_form_scaffold": {
            "scaffold_status": "blank_input_form_scaffold" if ready else "blocked",
            "form_runtime_status": "not_created",
            "form_submission_status": "not_supported",
            "form_export_status": "not_supported",
            "form_acceptance_status": "not_accepted",
            "value_collection_status": "not_collected",
            "section_order": SECTION_ORDER,
            "sections": build_form_sections(fields),
            "fields": fields,
            "future_validation_policy": REQUIRED_FUTURE_VALIDATION_POLICY,
            "future_import_policy": REQUIRED_FUTURE_IMPORT_POLICY,
            "form_completion_policy": FORM_COMPLETION_POLICY,
            "future_form_export_policy": FORM_EXPORT_POLICY,
        },
        "handoff": {
            "allowed_next_step": allowed_next_step,
            "not_allowed_yet": FORM_SCAFFOLD_NOT_ALLOWED,
        },
        "traceability": {
            "source_of_truth": "v0.4.14.10 input packet scaffold gated by v0.4.14.11",
            "source_packet_field_count": len(FIELD_ORDER),
            "form_field_count": len(fields),
            "section_count": len(SECTION_ORDER),
            "next_gate": "human_rebuild_authorization_record_input_form_scaffold_gate",
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        new_blockers = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["blockers"] = new_blockers
        report["input_form_scaffold_gate"]["status"] = "blocked"
        report["input_form_scaffold_gate"]["allowed_use"] = "blocked"
        report["input_form_scaffold_gate"]["blockers"] = new_blockers
        report["forbidden_output_keys_detected"] = forbidden
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    scaffold = as_dict(report.get("input_form_scaffold"))
    lines = [
        "# v0.4.14.12 Human Rebuild Authorization Record Input Form Scaffold",
        "",
        "本版本只生成未来人工授权输入表单的空白 scaffold。它不是可运行表单，不是 importer，不收集、不导入、不校验真实人工值，也不创建或接受正式授权记录。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 表单分区数: `{summary.get('form_section_count')}`",
        f"- 表单字段数: `{summary.get('form_field_count')}`",
        f"- 已收集人工值: `{summary.get('human_value_count')}`",
        f"- 是否已创建可运行输入表单: `{summary.get('runnable_input_form_created')}`",
        f"- 是否已创建 importer: `{summary.get('input_importer_created')}`",
        f"- 是否已导出表单值: `{summary.get('form_values_exported')}`",
        f"- 是否已导入人工值: `{summary.get('input_values_imported')}`",
        f"- 是否已校验人工值: `{summary.get('input_values_validated')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 空白表单字段",
        "",
    ]
    for field in scaffold.get("fields", []):
        lines.append(
            f"- `{field.get('display_order')}` {field.get('label_zh')} (`{field.get('field_id')}`): "
            f"widget=`{field.get('future_widget_hint')}`, value=`{field.get('value_status')}`"
        )
    lines.extend([
        "",
        "通过本 scaffold 只允许进入 `human_rebuild_authorization_record_input_form_scaffold_gate`。它仍不代表已经允许填写真实人工值、创建 importer、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the v0.4.14.12 human rebuild authorization input form scaffold."
    )
    parser.add_argument("--input-packet-scaffold", type=Path, default=DEFAULT_INPUT_PACKET_SCAFFOLD_PATH)
    parser.add_argument("--input-packet-scaffold-gate", type=Path, default=DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input_packet_scaffold, args.input_packet_scaffold_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization input form scaffold: "
        f"{summary.get('status')}, fields={summary.get('form_field_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
