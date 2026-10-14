"""Check the v0.4.14.5 human rebuild authorization record draft design gate.

The gate validates only the saved v0.4.14.4 draft design report. It does not
collect human values, create or accept formal authorization, run live preflight,
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


VERSION = "0.4.14.5"

DEFAULT_DRAFT_DESIGN_PATH = legacy_report_path("human_rebuild_authorization_record_draft_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_draft_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md")

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

REQUIRED_GUARDRAILS = {
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

REQUIRED_FUTURE_VALIDATION_POLICY = {
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


def section_contract_is_locked(draft_record_design: dict[str, Any]) -> bool:
    sections = [row for row in as_list(draft_record_design.get("section_contract")) if isinstance(row, dict)]
    if draft_record_design.get("record_status") != "not_created":
        return False
    if draft_record_design.get("record_acceptance_status") != "not_accepted":
        return False
    if draft_record_design.get("value_collection_status") != "not_collected":
        return False
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


def field_mapping_contract_is_locked(draft_record_design: dict[str, Any]) -> bool:
    mappings = [row for row in as_list(draft_record_design.get("field_mappings")) if isinstance(row, dict)]
    if len(mappings) != len(FIELD_ORDER):
        return False
    if [row.get("draft_field_id") for row in mappings] != FIELD_ORDER:
        return False
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        row = mappings[index - 1]
        if row.get("mapping_id") != f"draft_field_{index:02d}_{field_id}":
            return False
        if row.get("source_scaffold_field") != field_id:
            return False
        if row.get("draft_section") != FIELD_TO_SECTION[field_id]:
            return False
        if row.get("requirement") != "required":
            return False
        if row.get("fill_sequence") != index:
            return False
        if row.get("future_human_input_required") is not True:
            return False
        if row.get("draft_value_status") != "not_collected":
            return False
        if row.get("value_status") != "not_collected":
            return False
        if row.get("draft_value_placeholder") is not None:
            return False
        if row.get("value") is not None:
            return False
        if row.get("design_status") != "ready_for_future_draft":
            return False
        if row.get("authorization_granted") is not False:
            return False
        if row.get("authorization_effect_now") != "none":
            return False
        if row.get("qdrant_write_allowed") is not False:
            return False
        if row.get("rebuild_allowed") is not False:
            return False
        if row.get("captures_formal_authorization_outcome") is not False:
            return False
        if not isinstance(row.get("guidance"), str) or not row.get("guidance"):
            return False
    return True


def build_report(draft_design_path: Path = DEFAULT_DRAFT_DESIGN_PATH) -> dict[str, Any]:
    draft_design = load_json(draft_design_path)
    inputs = as_dict(draft_design.get("inputs"))
    scaffold_input = as_dict(inputs.get("human_rebuild_authorization_record_scaffold"))
    scaffold_gate_input = as_dict(inputs.get("human_rebuild_authorization_record_scaffold_gate"))
    summary = as_dict(draft_design.get("summary"))
    guardrails = as_dict(draft_design.get("guardrails"))
    internal_gate = as_dict(draft_design.get("draft_design_gate"))
    draft_record_design = as_dict(draft_design.get("draft_record_design"))
    future_policy = as_dict(draft_record_design.get("future_validation_policy"))
    handoff = as_dict(draft_design.get("handoff"))
    traceability = as_dict(draft_design.get("traceability"))
    forbidden_count = forbidden_output_key_count(draft_design)

    checks = [
        check_row(
            "draft_design_version",
            draft_design.get("version") == "0.4.14.4",
            "Draft design report must be v0.4.14.4.",
        ),
        check_row(
            "draft_design_schema",
            draft_design.get("schema_kind") == "human_rebuild_authorization_record_draft_design",
            "Draft design schema must match.",
        ),
        check_row(
            "draft_design_status",
            summary.get("status") == "ready_for_human_rebuild_authorization_record_draft_design_gate"
            and summary.get("allowed_next_step") == "human_rebuild_authorization_record_draft_design_gate"
            and summary.get("blockers") == [],
            "Draft design must open only this gate and have no blockers.",
        ),
        check_row(
            "source_lineage",
            set(inputs) == {"human_rebuild_authorization_record_scaffold", "human_rebuild_authorization_record_scaffold_gate"}
            and scaffold_input.get("present") is True
            and scaffold_input.get("version") == "0.4.14.2"
            and scaffold_input.get("schema_kind") == "human_rebuild_authorization_record_scaffold"
            and scaffold_input.get("status") == "pending_human_authorization_record"
            and scaffold_gate_input.get("present") is True
            and scaffold_gate_input.get("version") == "0.4.14.3"
            and scaffold_gate_input.get("schema_kind") == "human_rebuild_authorization_record_scaffold_gate"
            and scaffold_gate_input.get("status") == "passed",
            "Draft design must retain only v0.4.14.2 scaffold and v0.4.14.3 gate saved-report lineage.",
        ),
        check_row(
            "no_values_or_authorization",
            summary.get("human_value_count") == 0
            and summary.get("human_values_collected") is False
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
            "Draft design must remain blank, uncreated, unauthorized, and non-executing.",
        ),
        check_row(
            "internal_design_gate_locked",
            internal_gate.get("status") == "ready_for_human_rebuild_authorization_record_draft_design_gate"
            and internal_gate.get("allowed_use") == "design_review_only"
            and internal_gate.get("draft_record_created") is False
            and internal_gate.get("formal_authorization_record_created") is False
            and internal_gate.get("authorization_granted") is False
            and internal_gate.get("live_preflight_run") is False
            and internal_gate.get("qdrant_write_allowed") is False
            and internal_gate.get("rebuild_allowed") is False
            and internal_gate.get("blockers") == [],
            "Internal draft design gate fields must preserve design-only non-authorization boundary.",
        ),
        check_row(
            "guardrails_locked",
            set(guardrails) == set(REQUIRED_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must remain design-only and block authorization, live preflight, Qdrant, rebuild, runtime, and eval mutation.",
        ),
        check_row(
            "section_contract_locked",
            section_contract_is_locked(draft_record_design),
            "Section contract must preserve order, fields, not_collected values, and no current authorization effect.",
        ),
        check_row(
            "field_mapping_contract_locked",
            field_mapping_contract_is_locked(draft_record_design),
            "Field mappings must preserve order, required status, empty values, future-only guidance, and blocked permissions.",
        ),
        check_row(
            "future_validation_policy_locked",
            future_policy == REQUIRED_FUTURE_VALIDATION_POLICY,
            "Future validation policy must require future record completeness while granting no current execution effect.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("allowed_next_step") == "human_rebuild_authorization_record_draft_design_gate"
            and set(as_list(handoff.get("not_allowed_yet"))) == REQUIRED_NOT_ALLOWED,
            "Handoff must block value collection, authorization acceptance, live preflight, Qdrant write, rebuild, runtime/eval mutation, and full eval substitution.",
        ),
        check_row(
            "traceability_counts",
            traceability.get("source_of_truth") == "v0.4.14.2 scaffold gated by v0.4.14.3"
            and traceability.get("source_field_count") == 10
            and traceability.get("draft_field_count") == 10
            and traceability.get("section_count") == 7
            and traceability.get("next_gate") == "human_rebuild_authorization_record_draft_design_gate",
            "Traceability counts and next gate must match the draft design contract.",
        ),
        check_row(
            "forbidden_output_keys_absent",
            forbidden_count == 0,
            "Draft design report must not expose execution-style output keys.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_draft_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_draft_design": {
                "path": str(draft_design_path),
                "version": draft_design.get("version"),
                "schema_kind": draft_design.get("schema_kind"),
                "status": summary.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "human_rebuild_authorization_record_draft_scaffold" if status == "passed" else "blocked",
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
            "forbidden_output_key_count": forbidden_count,
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.14.5 Human Rebuild Authorization Record Draft Design Gate",
        "",
        "本 gate 只检查 v0.4.14.4 正式授权记录草案设计。它不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已收集人工值: `{summary.get('human_values_collected')}`",
        f"- 是否已创建草案记录: `{summary.get('draft_record_created')}`",
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
        "通过本 gate 只允许进入 `human_rebuild_authorization_record_draft_scaffold`，仍不代表已经允许填写真实人工值、创建或接受正式授权、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.5 human rebuild authorization record draft design gate.")
    parser.add_argument("--draft-design", type=Path, default=DEFAULT_DRAFT_DESIGN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.draft_design)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization record draft design gate: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
