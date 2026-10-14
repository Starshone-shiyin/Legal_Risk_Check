"""Build the v0.4.14.6 human rebuild authorization record draft scaffold.

The scaffold reads only the saved v0.4.14.4 draft design and v0.4.14.5 draft
design gate reports. It creates a blank scaffold for a future human-filled
authorization draft, but it does not collect human values, create or accept a
formal authorization record, run live preflight, access Qdrant, rebuild
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


VERSION = "0.4.14.6"

DEFAULT_DRAFT_DESIGN_PATH = legacy_report_path("human_rebuild_authorization_record_draft_design_report.json")
DEFAULT_DRAFT_DESIGN_GATE_PATH = legacy_report_path("human_rebuild_authorization_record_draft_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_draft_scaffold_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md")

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

SECTION_TITLES = {
    "target_and_scope": "Target and scope",
    "source_lineage": "Source lineage",
    "risk_acknowledgement": "Risk acknowledgement",
    "safeguards": "Safeguards",
    "formal_authorization_inputs": "Formal authorization inputs",
    "execution_window": "Execution window",
    "post_rebuild_validation": "Post-rebuild validation",
}

REQUIRED_DESIGN_GUARDRAILS = {
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

GUARDRAILS = {
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


def design_sections_locked(draft_record_design: dict[str, Any]) -> bool:
    sections = [row for row in as_list(draft_record_design.get("section_contract")) if isinstance(row, dict)]
    if draft_record_design.get("section_order") != SECTION_ORDER:
        return False
    if [row.get("section_id") for row in sections] != SECTION_ORDER:
        return False
    for section_id in SECTION_ORDER:
        section = next(row for row in sections if row.get("section_id") == section_id)
        expected_fields = [field for field in FIELD_ORDER if FIELD_TO_SECTION[field] == section_id]
        if section.get("fields") != expected_fields:
            return False
        if section.get("value_collection") != "not_collected":
            return False
        if section.get("authorization_effect") != "none":
            return False
    return True


def design_mappings_locked(draft_record_design: dict[str, Any]) -> bool:
    mappings = [row for row in as_list(draft_record_design.get("field_mappings")) if isinstance(row, dict)]
    if len(mappings) != len(FIELD_ORDER):
        return False
    if [row.get("draft_field_id") for row in mappings] != FIELD_ORDER:
        return False
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        row = mappings[index - 1]
        if row.get("source_scaffold_field") != field_id:
            return False
        if row.get("draft_section") != FIELD_TO_SECTION[field_id]:
            return False
        if row.get("fill_sequence") != index:
            return False
        if row.get("draft_value_status") != "not_collected":
            return False
        if row.get("value_status") != "not_collected":
            return False
        if row.get("draft_value_placeholder") is not None:
            return False
        if row.get("value") is not None:
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


def source_blockers(draft_design: dict[str, Any], draft_design_gate: dict[str, Any]) -> list[str]:
    design_summary = as_dict(draft_design.get("summary"))
    design_inputs = as_dict(draft_design.get("inputs"))
    scaffold_input = as_dict(design_inputs.get("human_rebuild_authorization_record_scaffold"))
    scaffold_gate_input = as_dict(design_inputs.get("human_rebuild_authorization_record_scaffold_gate"))
    design_guardrails = as_dict(draft_design.get("guardrails"))
    draft_record_design = as_dict(draft_design.get("draft_record_design"))
    design_handoff = as_dict(draft_design.get("handoff"))
    design_traceability = as_dict(draft_design.get("traceability"))
    gate_summary = as_dict(draft_design_gate.get("summary"))

    blockers: list[str] = []
    if draft_design.get("version") != "0.4.14.4":
        blockers.append("draft_design_version_mismatch")
    if draft_design.get("schema_kind") != "human_rebuild_authorization_record_draft_design":
        blockers.append("draft_design_schema_mismatch")
    if design_summary.get("status") != "ready_for_human_rebuild_authorization_record_draft_design_gate":
        blockers.append("draft_design_status_mismatch")
    if design_summary.get("allowed_next_step") != "human_rebuild_authorization_record_draft_design_gate":
        blockers.append("draft_design_next_step_mismatch")
    for key, expected in {
        "draft_design_only": True,
        "draft_record_created": False,
        "field_mapping_count": 10,
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
        if design_summary.get(key) != expected:
            blockers.append(f"draft_design_{key}_mismatch")
    if design_summary.get("blockers") != []:
        blockers.append("draft_design_blockers_present")
    if set(design_inputs) != {"human_rebuild_authorization_record_scaffold", "human_rebuild_authorization_record_scaffold_gate"}:
        blockers.append("draft_design_input_lineage_mismatch")
    if scaffold_input.get("version") != "0.4.14.2" or scaffold_input.get("schema_kind") != "human_rebuild_authorization_record_scaffold":
        blockers.append("draft_design_scaffold_input_mismatch")
    if scaffold_gate_input.get("version") != "0.4.14.3" or scaffold_gate_input.get("schema_kind") != "human_rebuild_authorization_record_scaffold_gate":
        blockers.append("draft_design_scaffold_gate_input_mismatch")
    if set(design_guardrails) != set(REQUIRED_DESIGN_GUARDRAILS):
        blockers.append("draft_design_guardrail_keys_mismatch")
    for key, expected in REQUIRED_DESIGN_GUARDRAILS.items():
        if design_guardrails.get(key) != expected:
            blockers.append(f"draft_design_guardrail_{key}_mismatch")
    if not design_sections_locked(draft_record_design):
        blockers.append("draft_design_section_contract_mismatch")
    if not design_mappings_locked(draft_record_design):
        blockers.append("draft_design_field_mapping_contract_mismatch")
    if as_dict(draft_record_design.get("future_validation_policy")) != FUTURE_VALIDATION_POLICY:
        blockers.append("draft_design_future_validation_policy_mismatch")
    if design_handoff.get("allowed_next_step") != "human_rebuild_authorization_record_draft_design_gate":
        blockers.append("draft_design_handoff_next_step_mismatch")
    if set(as_list(design_handoff.get("not_allowed_yet"))) != REQUIRED_NOT_ALLOWED:
        blockers.append("draft_design_handoff_boundary_mismatch")
    if design_traceability.get("source_of_truth") != "v0.4.14.2 scaffold gated by v0.4.14.3":
        blockers.append("draft_design_traceability_source_mismatch")
    if design_traceability.get("draft_field_count") != 10 or design_traceability.get("section_count") != 7:
        blockers.append("draft_design_traceability_count_mismatch")

    if draft_design_gate.get("version") != "0.4.14.5":
        blockers.append("draft_design_gate_version_mismatch")
    if draft_design_gate.get("schema_kind") != "human_rebuild_authorization_record_draft_design_gate":
        blockers.append("draft_design_gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("draft_design_gate_not_passed")
    if gate_summary.get("failed_check_count") != 0:
        blockers.append("draft_design_gate_failed_checks_present")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_record_draft_scaffold":
        blockers.append("draft_design_gate_next_step_mismatch")
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
            blockers.append(f"draft_design_gate_{key}_mismatch")
    return sorted(set(blockers))


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
    }


def design_mapping_by_field(draft_design: dict[str, Any]) -> dict[str, dict[str, Any]]:
    draft_record_design = as_dict(draft_design.get("draft_record_design"))
    mappings = [row for row in as_list(draft_record_design.get("field_mappings")) if isinstance(row, dict)]
    return {str(row.get("draft_field_id")): row for row in mappings}


def build_scaffold_rows(draft_design: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    mapping_by_field = design_mapping_by_field(draft_design)
    rows = []
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        mapping = mapping_by_field.get(field_id, {})
        rows.append({
            "row_id": f"draft_scaffold_row_{index:02d}_{field_id}",
            "source_mapping_id": mapping.get("mapping_id"),
            "section_id": FIELD_TO_SECTION[field_id],
            "field_id": field_id,
            "requirement": "required",
            "fill_sequence": index,
            "future_human_input_required": True,
            "value_status": "not_collected",
            "human_value": None,
            "normalized_value": None,
            "review_status": "pending_future_human_input" if ready else "blocked",
            "authorization_effect_now": "none",
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "captures_formal_authorization_outcome": False,
            "guidance": mapping.get("guidance"),
        })
    return rows


def build_scaffold_sections(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "section_id": section_id,
            "section_title": SECTION_TITLES[section_id],
            "field_ids": [row["field_id"] for row in rows if row["section_id"] == section_id],
            "value_collection": "not_collected",
            "authorization_effect": "none",
        }
        for section_id in SECTION_ORDER
    ]


def build_report(
    draft_design_path: Path = DEFAULT_DRAFT_DESIGN_PATH,
    draft_design_gate_path: Path = DEFAULT_DRAFT_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    draft_design = load_json(draft_design_path)
    draft_design_gate = load_json(draft_design_gate_path)
    blockers = source_blockers(draft_design, draft_design_gate)
    ready = not blockers
    rows = build_scaffold_rows(draft_design, ready)
    sections = build_scaffold_sections(rows)
    status = "pending_human_rebuild_authorization_record_draft_scaffold_gate" if ready else "blocked"
    allowed_next_step = "human_rebuild_authorization_record_draft_scaffold_gate" if ready else "blocked"

    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_draft_scaffold",
        "scope": "blank human rebuild authorization record draft scaffold only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_draft_design": source_meta(draft_design_path, draft_design),
            "human_rebuild_authorization_record_draft_design_gate": source_meta(draft_design_gate_path, draft_design_gate),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_use": "blank_draft_scaffold_only" if ready else "blocked",
            "allowed_next_step": allowed_next_step,
            "draft_scaffold_only": True,
            "draft_record_scaffold_created": ready,
            "draft_record_created": False,
            "field_count": len(rows),
            "section_count": len(sections),
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
        "draft_scaffold_gate": {
            "status": status,
            "allowed_use": "blank_draft_scaffold_only" if ready else "blocked",
            "draft_record_scaffold_created": ready,
            "draft_record_created": False,
            "formal_authorization_record_created": False,
            "authorization_granted": False,
            "live_preflight_run": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "blockers": blockers,
        },
        "draft_scaffold": {
            "scaffold_status": "blank_draft_scaffold" if ready else "blocked",
            "record_status": "not_created",
            "record_acceptance_status": "not_accepted",
            "value_collection_status": "not_collected",
            "section_order": SECTION_ORDER,
            "sections": sections,
            "rows": rows,
            "future_validation_policy": FUTURE_VALIDATION_POLICY,
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
            "source_of_truth": "v0.4.14.4 draft design gated by v0.4.14.5",
            "source_field_count": len(FIELD_ORDER),
            "scaffold_field_count": len(rows),
            "section_count": len(sections),
            "next_gate": "human_rebuild_authorization_record_draft_scaffold_gate",
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        new_blockers = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["draft_record_scaffold_created"] = False
        report["summary"]["blockers"] = new_blockers
        report["draft_scaffold_gate"]["status"] = "blocked"
        report["draft_scaffold_gate"]["allowed_use"] = "blocked"
        report["draft_scaffold_gate"]["draft_record_scaffold_created"] = False
        report["draft_scaffold_gate"]["blockers"] = new_blockers
        report["forbidden_output_key_count"] = len(forbidden)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    scaffold = as_dict(report.get("draft_scaffold"))
    lines = [
        "# v0.4.14.6 Human Rebuild Authorization Record Draft Scaffold",
        "",
        "本版本只生成未来正式授权记录的空白草案 scaffold。它不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 字段数: `{summary.get('field_count')}`",
        f"- 分区数: `{summary.get('section_count')}`",
        f"- 已收集人工值: `{summary.get('human_value_count')}`",
        f"- 是否已创建草案 scaffold: `{summary.get('draft_record_scaffold_created')}`",
        f"- 是否已创建正式授权记录: `{summary.get('formal_authorization_record_created')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 草案 scaffold 分区",
        "",
    ]
    for section in scaffold.get("sections", []):
        lines.append(f"- `{section.get('section_id')}`: fields={section.get('field_ids')}; values=`not_collected`")
    lines.extend([
        "",
        "通过本版本只允许进入 `human_rebuild_authorization_record_draft_scaffold_gate`。它仍不代表已经允许填写真实人工值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.6 human rebuild authorization record draft scaffold.")
    parser.add_argument("--draft-design", type=Path, default=DEFAULT_DRAFT_DESIGN_PATH)
    parser.add_argument("--draft-design-gate", type=Path, default=DEFAULT_DRAFT_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.draft_design, args.draft_design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization record draft scaffold: "
        f"{summary.get('status')}, fields={summary.get('field_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
