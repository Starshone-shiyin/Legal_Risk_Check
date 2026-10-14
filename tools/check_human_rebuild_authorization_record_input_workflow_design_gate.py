"""Check the v0.4.14.9 human rebuild authorization input workflow design gate.

The gate validates only the saved v0.4.14.8 input workflow design report. It
does not collect human values, create an input form or importer, import or
validate real values, create or accept formal authorization, run live preflight,
access Qdrant, rebuild collections, call RAG/embedding/LLM, run full eval, or
mutate runtime and eval artifacts.
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


VERSION = "0.4.14.9"

DEFAULT_INPUT_WORKFLOW_DESIGN_PATH = legacy_report_path(
    "human_rebuild_authorization_record_input_workflow_design_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_input_workflow_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md")

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

REQUIRED_GUARDRAILS = {
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


def check_row(check_id: str, passed: bool, details: str) -> dict[str, Any]:
    return {"check_id": check_id, "passed": passed, "details": details}


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def forbidden_output_key_count(report: dict[str, Any]) -> int:
    matches = set()
    for node in walk_dicts(report):
        matches.update(FORBIDDEN_OUTPUT_KEYS & set(node))
    return len(matches)


def workflow_phases_locked(input_workflow_design: dict[str, Any]) -> bool:
    phases = [row for row in as_list(input_workflow_design.get("workflow_phases")) if isinstance(row, dict)]
    return (
        input_workflow_design.get("workflow_status") == "design_only"
        and input_workflow_design.get("value_collection_status") == "not_collected"
        and phases == WORKFLOW_PHASES
    )


def field_input_contracts_locked(input_workflow_design: dict[str, Any]) -> bool:
    contracts = [row for row in as_list(input_workflow_design.get("field_input_contracts")) if isinstance(row, dict)]
    if len(contracts) != len(FIELD_ORDER):
        return False
    if [row.get("field_id") for row in contracts] != FIELD_ORDER:
        return False
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        row = contracts[index - 1]
        if row.get("contract_id") != f"input_contract_{index:02d}_{field_id}":
            return False
        if row.get("source_row_id") != f"draft_scaffold_row_{index:02d}_{field_id}":
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
        if row.get("workflow_design_status") != "ready_for_future_input_design_gate":
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
    operator_row = contracts[FIELD_ORDER.index("operator_approval")]
    return (
        operator_row.get("future_input_shape") == "future_explicit_yes_no_authorization"
        and operator_row.get("authorization_effect_now") == "none"
        and operator_row.get("authorization_granted") is False
    )


def build_report(input_workflow_design_path: Path = DEFAULT_INPUT_WORKFLOW_DESIGN_PATH) -> dict[str, Any]:
    design_report = load_json(input_workflow_design_path)
    inputs = as_dict(design_report.get("inputs"))
    draft_scaffold_input = as_dict(inputs.get("human_rebuild_authorization_record_draft_scaffold"))
    draft_scaffold_gate_input = as_dict(inputs.get("human_rebuild_authorization_record_draft_scaffold_gate"))
    summary = as_dict(design_report.get("summary"))
    guardrails = as_dict(design_report.get("guardrails"))
    internal_gate = as_dict(design_report.get("input_workflow_design_gate"))
    input_workflow_design = as_dict(design_report.get("input_workflow_design"))
    future_validation_policy = as_dict(input_workflow_design.get("future_validation_policy"))
    future_import_policy = as_dict(input_workflow_design.get("future_import_policy"))
    handoff = as_dict(design_report.get("handoff"))
    traceability = as_dict(design_report.get("traceability"))
    forbidden_count = forbidden_output_key_count(design_report)

    checks = [
        check_row(
            "input_workflow_design_version",
            design_report.get("version") == "0.4.14.8",
            "Input workflow design report must be v0.4.14.8.",
        ),
        check_row(
            "input_workflow_design_schema",
            design_report.get("schema_kind") == "human_rebuild_authorization_record_input_workflow_design",
            "Input workflow design schema must match.",
        ),
        check_row(
            "input_workflow_design_status",
            summary.get("status") == "ready_for_human_rebuild_authorization_record_input_workflow_design_gate"
            and summary.get("allowed_next_step") == "human_rebuild_authorization_record_input_workflow_design_gate"
            and summary.get("input_workflow_design_only") is True
            and summary.get("blockers") == [],
            "Input workflow design must open only this gate and have no blockers.",
        ),
        check_row(
            "source_lineage",
            set(inputs) == {
                "human_rebuild_authorization_record_draft_scaffold",
                "human_rebuild_authorization_record_draft_scaffold_gate",
            }
            and draft_scaffold_input.get("present") is True
            and draft_scaffold_input.get("version") == "0.4.14.6"
            and draft_scaffold_input.get("schema_kind") == "human_rebuild_authorization_record_draft_scaffold"
            and draft_scaffold_input.get("status") == "pending_human_rebuild_authorization_record_draft_scaffold_gate"
            and draft_scaffold_gate_input.get("present") is True
            and draft_scaffold_gate_input.get("version") == "0.4.14.7"
            and draft_scaffold_gate_input.get("schema_kind")
            == "human_rebuild_authorization_record_draft_scaffold_gate"
            and draft_scaffold_gate_input.get("status") == "passed",
            "Input workflow design must retain only v0.4.14.6 draft scaffold and v0.4.14.7 gate saved-report lineage.",
        ),
        check_row(
            "no_values_or_authorization",
            summary.get("workflow_phase_count") == 6
            and summary.get("field_input_contract_count") == 10
            and summary.get("human_value_count") == 0
            and summary.get("human_values_collected") is False
            and summary.get("input_form_created") is False
            and summary.get("input_values_imported") is False
            and summary.get("input_values_validated") is False
            and summary.get("draft_record_created") is False
            and summary.get("formal_authorization_record_created") is False
            and summary.get("human_authorization_record_created") is False
            and summary.get("human_authorization_record_accepted") is False
            and summary.get("authorization_granted") is False
            and summary.get("live_preflight_run") is False
            and summary.get("production_rebuild_executed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("rebuild_allowed") is False
            and summary.get("full_eval") == "not_run",
            "Input workflow design must remain design-only, blank, unauthorized, and non-executing.",
        ),
        check_row(
            "internal_gate_locked",
            internal_gate.get("status") == "ready_for_human_rebuild_authorization_record_input_workflow_design_gate"
            and internal_gate.get("allowed_use") == "workflow_design_review_only"
            and internal_gate.get("human_values_collected") is False
            and internal_gate.get("input_form_created") is False
            and internal_gate.get("input_values_imported") is False
            and internal_gate.get("input_values_validated") is False
            and internal_gate.get("formal_authorization_record_created") is False
            and internal_gate.get("authorization_granted") is False
            and internal_gate.get("live_preflight_run") is False
            and internal_gate.get("qdrant_write_allowed") is False
            and internal_gate.get("rebuild_allowed") is False
            and internal_gate.get("blockers") == [],
            "Internal gate fields must preserve workflow-design-only and non-authorization boundary.",
        ),
        check_row(
            "guardrails_locked",
            set(guardrails) == set(REQUIRED_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must block value collection, input creation/import, authorization, live preflight, Qdrant, rebuild, runtime, and eval mutation.",
        ),
        check_row(
            "workflow_phases_locked",
            workflow_phases_locked(input_workflow_design),
            "Workflow phases must preserve the 6-stage future design and no current authorization effect.",
        ),
        check_row(
            "field_input_contracts_locked",
            field_input_contracts_locked(input_workflow_design),
            "Field input contracts must preserve order, empty current values, future-only shapes, and blocked permissions.",
        ),
        check_row(
            "future_validation_policy_locked",
            future_validation_policy == REQUIRED_FUTURE_VALIDATION_POLICY,
            "Future validation policy must require future record completeness while granting no current execution effect.",
        ),
        check_row(
            "future_import_policy_locked",
            future_import_policy == REQUIRED_FUTURE_IMPORT_POLICY,
            "Future import policy must require staging and reviewer confirmation while granting no current authorization effect.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("allowed_next_step") == "human_rebuild_authorization_record_input_workflow_design_gate"
            and set(as_list(handoff.get("not_allowed_yet"))) == REQUIRED_NOT_ALLOWED,
            "Handoff must block real values, input/import implementation, formal authorization, live preflight, Qdrant write, rebuild, runtime/eval mutation, and full eval substitution.",
        ),
        check_row(
            "traceability_counts",
            traceability.get("source_of_truth") == "v0.4.14.6 draft scaffold gated by v0.4.14.7"
            and traceability.get("source_field_count") == 10
            and traceability.get("field_input_contract_count") == 10
            and traceability.get("workflow_phase_count") == 6
            and traceability.get("next_gate") == "human_rebuild_authorization_record_input_workflow_design_gate",
            "Traceability counts and next gate must match the input workflow design contract.",
        ),
        check_row(
            "forbidden_output_keys_absent",
            forbidden_count == 0,
            "Input workflow design report must not expose execution-style output keys.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_input_workflow_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_input_workflow_design": {
                "path": str(input_workflow_design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": summary.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "human_rebuild_authorization_record_input_packet_scaffold"
            if status == "passed"
            else "blocked",
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
            "forbidden_output_key_count": forbidden_count,
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.14.9 Human Rebuild Authorization Record Input Workflow Design Gate",
        "",
        "本 gate 只检查 v0.4.14.8 保存的 input workflow design。它不收集人工值，不创建输入表单或 importer，不导入或校验真实审批值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已收集人工值: `{summary.get('human_values_collected')}`",
        f"- 是否已创建输入表单: `{summary.get('input_form_created')}`",
        f"- 是否已导入人工值: `{summary.get('input_values_imported')}`",
        f"- 是否已校验人工值: `{summary.get('input_values_validated')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 检查项",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    lines.extend([
        "",
        "通过本 gate 只允许进入 `human_rebuild_authorization_record_input_packet_scaffold`，仍不代表已经允许填写真实人工值、创建输入入口、导入审批值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the v0.4.14.9 human rebuild authorization input workflow design gate."
    )
    parser.add_argument("--input-workflow-design", type=Path, default=DEFAULT_INPUT_WORKFLOW_DESIGN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input_workflow_design)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization input workflow design gate: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
