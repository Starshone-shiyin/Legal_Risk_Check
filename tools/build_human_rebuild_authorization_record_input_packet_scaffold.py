"""Build the v0.4.14.10 human rebuild authorization input packet scaffold.

The scaffold reads only the saved v0.4.14.8 input workflow design and
v0.4.14.9 input workflow design gate reports. It creates a blank future input
packet scaffold, but it does not create an input form or importer, collect,
import, or validate real human values, create or accept formal authorization,
run live preflight, access Qdrant, rebuild collections, call RAG/embedding/LLM,
run full eval, or mutate runtime and eval artifacts.
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


VERSION = "0.4.14.10"

DEFAULT_INPUT_WORKFLOW_DESIGN_PATH = legacy_report_path(
    "human_rebuild_authorization_record_input_workflow_design_report.json"
)
DEFAULT_INPUT_WORKFLOW_DESIGN_GATE_PATH = legacy_report_path(
    "human_rebuild_authorization_record_input_workflow_design_gate_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_input_packet_scaffold_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md")

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

WORKFLOW_PHASE_IDS = [
    "prepare_blank_input_packet",
    "human_entry_session",
    "offline_import_staging",
    "field_validation_review",
    "reviewer_confirmation_packet",
    "formal_record_candidate_handoff",
]

REQUIRED_DESIGN_GUARDRAILS = {
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

GUARDRAILS = {
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
}

SCAFFOLD_NOT_ALLOWED = sorted(REQUIRED_NOT_ALLOWED | {"enter values into the blank input packet"})

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


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
    }


def field_contracts_by_id(design_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    design = as_dict(design_report.get("input_workflow_design"))
    contracts = [row for row in as_list(design.get("field_input_contracts")) if isinstance(row, dict)]
    return {str(row.get("field_id")): row for row in contracts}


def field_contracts_locked(design_report: dict[str, Any]) -> bool:
    contracts = [row for row in field_contracts_by_id(design_report).values()]
    contracts_by_id = field_contracts_by_id(design_report)
    if len(contracts) != len(FIELD_ORDER):
        return False
    if [contracts_by_id.get(field_id, {}).get("field_id") for field_id in FIELD_ORDER] != FIELD_ORDER:
        return False
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        row = contracts_by_id[field_id]
        if row.get("contract_id") != f"input_contract_{index:02d}_{field_id}":
            return False
        if row.get("section_id") != FIELD_TO_SECTION[field_id]:
            return False
        if row.get("requirement") != "required":
            return False
        if row.get("input_sequence") != index:
            return False
        if row.get("future_input_required") is not True:
            return False
        if row.get("future_input_shape") != FIELD_INPUT_SHAPES[field_id]:
            return False
        if row.get("current_value_status") != "not_collected":
            return False
        if row.get("current_human_value") is not None:
            return False
        if row.get("current_normalized_value") is not None:
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


def workflow_design_locked(design_report: dict[str, Any]) -> bool:
    design = as_dict(design_report.get("input_workflow_design"))
    phases = [row for row in as_list(design.get("workflow_phases")) if isinstance(row, dict)]
    return (
        design.get("workflow_status") == "design_only"
        and design.get("value_collection_status") == "not_collected"
        and [row.get("phase_id") for row in phases] == WORKFLOW_PHASE_IDS
        and [row.get("sequence") for row in phases] == list(range(1, len(WORKFLOW_PHASE_IDS) + 1))
        and all(row.get("authorization_effect") == "none" for row in phases)
        and as_dict(design.get("future_validation_policy")) == REQUIRED_FUTURE_VALIDATION_POLICY
        and as_dict(design.get("future_import_policy")) == REQUIRED_FUTURE_IMPORT_POLICY
        and field_contracts_locked(design_report)
    )


def source_blockers(input_workflow_design: dict[str, Any], input_workflow_design_gate: dict[str, Any]) -> list[str]:
    summary = as_dict(input_workflow_design.get("summary"))
    inputs = as_dict(input_workflow_design.get("inputs"))
    draft_scaffold_input = as_dict(inputs.get("human_rebuild_authorization_record_draft_scaffold"))
    draft_scaffold_gate_input = as_dict(inputs.get("human_rebuild_authorization_record_draft_scaffold_gate"))
    guardrails = as_dict(input_workflow_design.get("guardrails"))
    handoff = as_dict(input_workflow_design.get("handoff"))
    traceability = as_dict(input_workflow_design.get("traceability"))
    gate_summary = as_dict(input_workflow_design_gate.get("summary"))

    blockers: list[str] = []
    if input_workflow_design.get("version") != "0.4.14.8":
        blockers.append("input_workflow_design_version_mismatch")
    if input_workflow_design.get("schema_kind") != "human_rebuild_authorization_record_input_workflow_design":
        blockers.append("input_workflow_design_schema_mismatch")
    if summary.get("status") != "ready_for_human_rebuild_authorization_record_input_workflow_design_gate":
        blockers.append("input_workflow_design_status_mismatch")
    if summary.get("allowed_next_step") != "human_rebuild_authorization_record_input_workflow_design_gate":
        blockers.append("input_workflow_design_next_step_mismatch")
    for key, expected in {
        "input_workflow_design_only": True,
        "workflow_phase_count": 6,
        "field_input_contract_count": 10,
        "human_value_count": 0,
        "human_values_collected": False,
        "input_form_created": False,
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
            blockers.append(f"input_workflow_design_{key}_mismatch")
    if summary.get("blockers") != []:
        blockers.append("input_workflow_design_blockers_present")
    if set(inputs) != {
        "human_rebuild_authorization_record_draft_scaffold",
        "human_rebuild_authorization_record_draft_scaffold_gate",
    }:
        blockers.append("input_workflow_design_source_lineage_mismatch")
    if (
        draft_scaffold_input.get("version") != "0.4.14.6"
        or draft_scaffold_input.get("schema_kind") != "human_rebuild_authorization_record_draft_scaffold"
    ):
        blockers.append("input_workflow_design_draft_scaffold_input_mismatch")
    if (
        draft_scaffold_gate_input.get("version") != "0.4.14.7"
        or draft_scaffold_gate_input.get("schema_kind") != "human_rebuild_authorization_record_draft_scaffold_gate"
        or draft_scaffold_gate_input.get("status") != "passed"
    ):
        blockers.append("input_workflow_design_draft_scaffold_gate_input_mismatch")
    if set(guardrails) != set(REQUIRED_DESIGN_GUARDRAILS):
        blockers.append("input_workflow_design_guardrail_keys_mismatch")
    for key, expected in REQUIRED_DESIGN_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            blockers.append(f"input_workflow_design_guardrail_{key}_mismatch")
    if not workflow_design_locked(input_workflow_design):
        blockers.append("input_workflow_design_contract_mismatch")
    if handoff.get("allowed_next_step") != "human_rebuild_authorization_record_input_workflow_design_gate":
        blockers.append("input_workflow_design_handoff_next_step_mismatch")
    if set(as_list(handoff.get("not_allowed_yet"))) != REQUIRED_NOT_ALLOWED:
        blockers.append("input_workflow_design_handoff_boundary_mismatch")
    if traceability.get("source_of_truth") != "v0.4.14.6 draft scaffold gated by v0.4.14.7":
        blockers.append("input_workflow_design_traceability_source_mismatch")
    if traceability.get("field_input_contract_count") != 10 or traceability.get("workflow_phase_count") != 6:
        blockers.append("input_workflow_design_traceability_count_mismatch")
    if forbidden_output_keys(input_workflow_design):
        blockers.append("input_workflow_design_forbidden_output_key_present")

    if input_workflow_design_gate.get("version") != "0.4.14.9":
        blockers.append("input_workflow_design_gate_version_mismatch")
    if input_workflow_design_gate.get("schema_kind") != "human_rebuild_authorization_record_input_workflow_design_gate":
        blockers.append("input_workflow_design_gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("input_workflow_design_gate_not_passed")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("input_workflow_design_gate_failed_checks_present")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_record_input_packet_scaffold":
        blockers.append("input_workflow_design_gate_next_step_mismatch")
    for key, expected in {
        "human_values_collected": False,
        "input_form_created": False,
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
            blockers.append(f"input_workflow_design_gate_{key}_mismatch")
    if forbidden_output_keys(input_workflow_design_gate):
        blockers.append("input_workflow_design_gate_forbidden_output_key_present")
    return sorted(set(blockers))


def build_packet_rows(input_workflow_design: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    contracts = field_contracts_by_id(input_workflow_design)
    rows = []
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        contract = contracts.get(field_id, {})
        rows.append({
            "row_id": f"input_packet_row_{index:02d}_{field_id}",
            "source_contract_id": contract.get("contract_id"),
            "source_row_id": contract.get("source_row_id"),
            "section_id": FIELD_TO_SECTION[field_id],
            "field_id": field_id,
            "requirement": "required",
            "input_sequence": index,
            "future_input_shape": FIELD_INPUT_SHAPES[field_id],
            "entry_status": "blank",
            "value_status": "not_collected",
            "human_value": None,
            "normalized_value": None,
            "import_status": "not_imported",
            "validation_status_now": "not_run",
            "future_validation_required": True,
            "review_status": "pending_future_human_input",
            "authorization_effect_now": "none",
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "scaffold_status": "ready_for_future_input_packet_gate" if ready else "blocked",
            "guidance_source": contract.get("guidance_source"),
        })
    return rows


def build_packet_sections(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "section_id": section_id,
            "field_ids": [row["field_id"] for row in rows if row["section_id"] == section_id],
            "value_collection": "not_collected",
            "input_form_effect": "none",
            "import_effect": "none",
            "authorization_effect": "none",
        }
        for section_id in SECTION_ORDER
    ]


def build_report(
    input_workflow_design_path: Path = DEFAULT_INPUT_WORKFLOW_DESIGN_PATH,
    input_workflow_design_gate_path: Path = DEFAULT_INPUT_WORKFLOW_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    input_workflow_design = load_json(input_workflow_design_path)
    input_workflow_design_gate = load_json(input_workflow_design_gate_path)
    blockers = source_blockers(input_workflow_design, input_workflow_design_gate)
    ready = not blockers
    rows = build_packet_rows(input_workflow_design, ready)
    status = "pending_human_rebuild_authorization_record_input_packet_scaffold_gate" if ready else "blocked"
    allowed_next_step = "human_rebuild_authorization_record_input_packet_scaffold_gate" if ready else "blocked"

    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_input_packet_scaffold",
        "scope": "blank future human authorization input packet scaffold only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_input_workflow_design": source_meta(
                input_workflow_design_path, input_workflow_design
            ),
            "human_rebuild_authorization_record_input_workflow_design_gate": source_meta(
                input_workflow_design_gate_path, input_workflow_design_gate
            ),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "input_packet_scaffold_only": True,
            "blank_input_packet_scaffold_created": ready,
            "packet_field_count": len(rows),
            "packet_section_count": len(SECTION_ORDER),
            "human_value_count": 0,
            "human_values_collected": False,
            "input_form_created": False,
            "input_importer_created": False,
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
        "input_packet_scaffold_gate": {
            "status": status,
            "allowed_use": "blank_input_packet_scaffold_only" if ready else "blocked",
            "blank_input_packet_scaffold_created": ready,
            "input_form_created": False,
            "input_importer_created": False,
            "human_values_collected": False,
            "input_values_imported": False,
            "input_values_validated": False,
            "formal_authorization_record_created": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "blockers": blockers,
        },
        "input_packet_scaffold": {
            "scaffold_status": "blank_input_packet_scaffold" if ready else "blocked",
            "packet_status": "not_completed",
            "packet_acceptance_status": "not_accepted",
            "value_collection_status": "not_collected",
            "section_order": SECTION_ORDER,
            "sections": build_packet_sections(rows),
            "rows": rows,
            "future_validation_policy": REQUIRED_FUTURE_VALIDATION_POLICY,
            "future_import_policy": REQUIRED_FUTURE_IMPORT_POLICY,
            "packet_completion_policy": {
                "all_required_fields_blank_in_this_version": True,
                "future_completed_packet_required_before_import": True,
                "current_packet_importable": False,
                "current_packet_authorization_effect": "none",
            },
        },
        "handoff": {
            "allowed_next_step": allowed_next_step,
            "not_allowed_yet": SCAFFOLD_NOT_ALLOWED,
        },
        "traceability": {
            "source_of_truth": "v0.4.14.8 input workflow design gated by v0.4.14.9",
            "source_field_count": len(FIELD_ORDER),
            "packet_field_count": len(rows),
            "section_count": len(SECTION_ORDER),
            "next_gate": "human_rebuild_authorization_record_input_packet_scaffold_gate",
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        new_blockers = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["blockers"] = new_blockers
        report["input_packet_scaffold_gate"]["status"] = "blocked"
        report["input_packet_scaffold_gate"]["allowed_use"] = "blocked"
        report["input_packet_scaffold_gate"]["blockers"] = new_blockers
        report["forbidden_output_keys_detected"] = forbidden
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    scaffold = as_dict(report.get("input_packet_scaffold"))
    lines = [
        "# v0.4.14.10 Human Rebuild Authorization Record Input Packet Scaffold",
        "",
        "本版本只生成未来人工授权输入包的空白 scaffold。它不是可填写输入表单，不是 importer，不收集、不导入、不校验真实人工值，也不创建或接受正式授权记录。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 字段数: `{summary.get('packet_field_count')}`",
        f"- 分区数: `{summary.get('packet_section_count')}`",
        f"- 已收集人工值: `{summary.get('human_value_count')}`",
        f"- 是否已创建输入表单: `{summary.get('input_form_created')}`",
        f"- 是否已创建 importer: `{summary.get('input_importer_created')}`",
        f"- 是否已导入人工值: `{summary.get('input_values_imported')}`",
        f"- 是否已校验人工值: `{summary.get('input_values_validated')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 空白输入行",
        "",
    ]
    for row in scaffold.get("rows", []):
        lines.append(
            f"- `{row.get('input_sequence')}` `{row.get('field_id')}`: "
            f"shape=`{row.get('future_input_shape')}`, value=`{row.get('value_status')}`"
        )
    lines.extend([
        "",
        "通过本 scaffold 只允许进入 `human_rebuild_authorization_record_input_packet_scaffold_gate`。它仍不代表已经允许填写真实人工值、创建输入入口、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the v0.4.14.10 human rebuild authorization input packet scaffold."
    )
    parser.add_argument("--input-workflow-design", type=Path, default=DEFAULT_INPUT_WORKFLOW_DESIGN_PATH)
    parser.add_argument("--input-workflow-design-gate", type=Path, default=DEFAULT_INPUT_WORKFLOW_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input_workflow_design, args.input_workflow_design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization input packet scaffold: "
        f"{summary.get('status')}, fields={summary.get('packet_field_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
