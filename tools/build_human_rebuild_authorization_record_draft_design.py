"""Build the v0.4.14.4 human rebuild authorization record draft design.

The design reads only the saved v0.4.14.2 scaffold and v0.4.14.3 scaffold
gate reports. It defines how a future formal authorization record draft should
map scaffold fields into sections, but it does not collect human values,
create or accept an authorization record, run live preflight, access Qdrant,
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


VERSION = "0.4.14.4"

DEFAULT_SCAFFOLD_PATH = legacy_report_path("human_rebuild_authorization_record_scaffold_report.json")
DEFAULT_SCAFFOLD_GATE_PATH = legacy_report_path("human_rebuild_authorization_record_scaffold_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_draft_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md")

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

FIELD_GUIDANCE = {
    "target_collection": "Future draft field for exact collection name; this design does not verify or lock the value.",
    "rebuild_scope": "Future draft field for included and excluded rebuild scope; this design does not authorize the scope.",
    "source_version": "Future draft field for code/report lineage; this design does not accept a lineage value.",
    "expected_id_drift_acknowledgement": "Future draft field for ID drift acknowledgement; this design does not treat it as current acknowledgement.",
    "backup_plan": "Future draft field for backup or snapshot reference; this design does not verify backup readiness.",
    "rollback_plan": "Future draft field for rollback owner and procedure; this design does not verify rollback readiness.",
    "operator_approval": "Future draft field for explicit human yes/no authorization; this design does not grant current approval.",
    "maintenance_window": "Future draft field for execution window and communication owner; this design does not open a window.",
    "post_rebuild_validation_plan": "Future draft field for metadata, ID drift, smoke, and rollback validation plan; this design does not run validation.",
    "abort_conditions_acknowledgement": "Future draft field for abort condition acknowledgement; this design does not waive any blocker.",
}

REQUIRED_NOT_ALLOWED = {
    "accept the scaffold as authorization",
    "create formal authorization record",
    "run live preflight",
    "write Qdrant",
    "rebuild collection",
    "switch collection",
    "call RAG, embedding, or LLM services",
    "run full eval as a substitute for authorization",
    "modify runtime, ingestion, retriever, rerank, prompt, anchors, rules, fixtures, or eval cases",
}

REQUIRED_SCAFFOLD_GUARDRAILS = {
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

GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "human_values_collected": False,
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


def rows_preserve_blank_contract(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != len(FIELD_ORDER):
        return False
    if [row.get("field_id") for row in rows] != FIELD_ORDER:
        return False
    for row in rows:
        if row.get("human_value_status") != "not_collected":
            return False
        if row.get("empty_authorization_value") is not None:
            return False
        if row.get("authorization_granted") is not False:
            return False
        if row.get("qdrant_write_allowed") is not False:
            return False
        if row.get("rebuild_allowed") is not False:
            return False
        if row.get("captures_formal_authorization_outcome") is not False:
            return False
    return True


def source_blockers(scaffold: dict[str, Any], scaffold_gate: dict[str, Any]) -> list[str]:
    scaffold_summary = as_dict(scaffold.get("summary"))
    scaffold_guardrails = as_dict(scaffold.get("guardrails"))
    input_contract = as_dict(scaffold.get("input_contract"))
    gate_summary = as_dict(scaffold_gate.get("summary"))
    rows = [row for row in as_list(scaffold.get("authorization_record_scaffold_rows")) if isinstance(row, dict)]
    handoff = as_dict(scaffold.get("next_version_handoff"))

    blockers: list[str] = []
    if scaffold.get("version") != "0.4.14.2":
        blockers.append("scaffold_version_mismatch")
    if scaffold.get("schema_kind") != "human_rebuild_authorization_record_scaffold":
        blockers.append("scaffold_schema_mismatch")
    if scaffold_summary.get("status") != "pending_human_authorization_record":
        blockers.append("scaffold_status_mismatch")
    if scaffold_summary.get("allowed_next_step") != "human_rebuild_authorization_record_scaffold_gate":
        blockers.append("scaffold_next_step_mismatch")
    for key, expected in {
        "human_value_count": 0,
        "human_values_collected": False,
        "draft_record_created": None,
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
        if expected is None:
            continue
        if scaffold_summary.get(key) != expected:
            blockers.append(f"scaffold_{key}_mismatch")
    if scaffold_summary.get("blockers") != []:
        blockers.append("scaffold_blockers_present")
    if set(scaffold_guardrails) != set(REQUIRED_SCAFFOLD_GUARDRAILS):
        blockers.append("scaffold_guardrail_keys_mismatch")
    for key, expected in REQUIRED_SCAFFOLD_GUARDRAILS.items():
        if scaffold_guardrails.get(key) != expected:
            blockers.append(f"scaffold_guardrail_{key}_mismatch")
    if input_contract.get("required_authorization_fields") != FIELD_ORDER:
        blockers.append("scaffold_input_contract_fields_mismatch")
    if not rows_preserve_blank_contract(rows):
        blockers.append("scaffold_row_contract_mismatch")
    if handoff.get("allowed_next_step") != "human_rebuild_authorization_record_scaffold_gate":
        blockers.append("scaffold_handoff_next_step_mismatch")
    if set(as_list(handoff.get("not_allowed_yet"))) != REQUIRED_NOT_ALLOWED:
        blockers.append("scaffold_handoff_boundary_mismatch")

    if scaffold_gate.get("version") != "0.4.14.3":
        blockers.append("gate_version_mismatch")
    if scaffold_gate.get("schema_kind") != "human_rebuild_authorization_record_scaffold_gate":
        blockers.append("gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("gate_not_passed")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("gate_failed_checks_present")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_record_draft_design":
        blockers.append("gate_next_step_mismatch")
    for key, expected in {
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
        if gate_summary.get(key) != expected:
            blockers.append(f"gate_{key}_mismatch")
    return sorted(set(blockers))


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
    }


def build_field_mappings(ready: bool) -> list[dict[str, Any]]:
    mappings = []
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        mappings.append(
            {
                "mapping_id": f"draft_field_{index:02d}_{field_id}",
                "source_scaffold_field": field_id,
                "draft_section": FIELD_TO_SECTION[field_id],
                "draft_field_id": field_id,
                "requirement": "required",
                "fill_sequence": index,
                "future_human_input_required": True,
                "draft_value_status": "not_collected",
                "value_status": "not_collected",
                "draft_value_placeholder": None,
                "value": None,
                "design_status": "ready_for_future_draft" if ready else "blocked",
                "authorization_granted": False,
                "authorization_effect_now": "none",
                "qdrant_write_allowed": False,
                "rebuild_allowed": False,
                "captures_formal_authorization_outcome": False,
                "guidance": FIELD_GUIDANCE[field_id],
            }
        )
    return mappings


def build_report(
    scaffold_path: Path = DEFAULT_SCAFFOLD_PATH,
    scaffold_gate_path: Path = DEFAULT_SCAFFOLD_GATE_PATH,
) -> dict[str, Any]:
    scaffold = load_json(scaffold_path)
    scaffold_gate = load_json(scaffold_gate_path)
    blockers = source_blockers(scaffold, scaffold_gate)
    ready = not blockers
    mappings = build_field_mappings(ready)
    status = "ready_for_human_rebuild_authorization_record_draft_design_gate" if ready else "blocked"
    allowed_next_step = "human_rebuild_authorization_record_draft_design_gate" if ready else "blocked"

    section_contract = [
        {
            "section_id": section_id,
            "fields": [row["draft_field_id"] for row in mappings if row["draft_section"] == section_id],
            "value_collection": "not_collected",
            "authorization_effect": "none",
        }
        for section_id in SECTION_ORDER
    ]

    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_draft_design",
        "scope": "human rebuild authorization record draft design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_scaffold": source_meta(scaffold_path, scaffold),
            "human_rebuild_authorization_record_scaffold_gate": source_meta(scaffold_gate_path, scaffold_gate),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "draft_design_only": True,
            "draft_record_created": False,
            "field_mapping_count": len(mappings),
            "fill_step_count": len(mappings),
            "section_count": len(section_contract),
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
        "draft_design_gate": {
            "status": status,
            "allowed_use": "design_review_only" if ready else "blocked",
            "draft_record_created": False,
            "formal_authorization_record_created": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "blockers": blockers,
        },
        "draft_record_design": {
            "record_status": "not_created",
            "record_acceptance_status": "not_accepted",
            "value_collection_status": "not_collected",
            "section_order": SECTION_ORDER,
            "section_contract": section_contract,
            "field_mappings": mappings,
            "future_validation_policy": {
                "all_required_fields_present": "required_for_future_record",
                "explicit_yes_no_authorization": "required_for_future_record",
                "operator_approval_effect": "future_field_only_not_current_approval",
                "preflight_authorization_effect": "none_in_this_version",
                "qdrant_write_authorization_effect": "none_in_this_version",
                "rebuild_authorization_effect": "none_in_this_version",
            },
        },
        "handoff": {
            "allowed_next_step": allowed_next_step,
            "not_allowed_yet": [
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
            ],
        },
        "traceability": {
            "source_of_truth": "v0.4.14.2 scaffold gated by v0.4.14.3",
            "source_field_count": len(FIELD_ORDER),
            "draft_field_count": len(mappings),
            "section_count": len(section_contract),
            "next_gate": "human_rebuild_authorization_record_draft_design_gate",
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        new_blockers = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["blockers"] = new_blockers
        report["draft_design_gate"]["status"] = "blocked"
        report["draft_design_gate"]["allowed_use"] = "blocked"
        report["draft_design_gate"]["blockers"] = new_blockers
        report["forbidden_output_keys_detected"] = forbidden
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("draft_record_design"))
    lines = [
        "# v0.4.14.4 Human Rebuild Authorization Record Draft Design",
        "",
        "本版本只设计未来正式授权记录草案的字段映射和分区结构。它不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 字段映射数: `{summary.get('field_mapping_count')}`",
        f"- 分区数: `{summary.get('section_count')}`",
        f"- 已收集人工值: `{summary.get('human_value_count')}`",
        f"- 是否已创建草案记录: `{summary.get('draft_record_created')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 草案分区",
        "",
    ]
    for section in design.get("section_contract", []):
        lines.append(f"- `{section.get('section_id')}`: fields={section.get('fields')}; values=`not_collected`")
    lines.extend(
        [
            "",
            "通过本 design 只允许进入 `human_rebuild_authorization_record_draft_design_gate`。它仍不代表已经允许填写正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.4 human rebuild authorization record draft design.")
    parser.add_argument("--scaffold", type=Path, default=DEFAULT_SCAFFOLD_PATH)
    parser.add_argument("--scaffold-gate", type=Path, default=DEFAULT_SCAFFOLD_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.scaffold, args.scaffold_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization record draft design: "
        f"{summary.get('status')}, fields={summary.get('field_mapping_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
