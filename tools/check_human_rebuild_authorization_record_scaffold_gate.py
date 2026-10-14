"""Check the v0.4.14.3 human rebuild authorization record scaffold gate.

The gate validates only the saved v0.4.14.2 blank scaffold report. It does not
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


VERSION = "0.4.14.3"

DEFAULT_SCAFFOLD_PATH = legacy_report_path("human_rebuild_authorization_record_scaffold_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_record_scaffold_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md")

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

REQUIRED_PREFLIGHT_ORDER = sorted(REQUIRED_PREFLIGHT_CHECKS)

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

REQUIRED_ABORT_ORDER = sorted(REQUIRED_ABORT_CONDITIONS)

REQUIRED_GUARDRAILS = {
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

REQUIRED_ASSERTIONS = {
    "scaffold_only",
    "no_human_values",
    "no_authorization",
    "no_runtime_action",
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


def rows_preserve_blank_contract(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != len(FIELD_ORDER):
        return False
    if [row.get("field_id") for row in rows] != FIELD_ORDER:
        return False
    for row in rows:
        if row.get("requirement") != "required":
            return False
        if row.get("source") != "v0.4.14.0 execution_design.required_authorization_fields":
            return False
        if row.get("scaffold_status") != "pending_human_input":
            return False
        if row.get("human_input_required") is not True:
            return False
        if row.get("human_value_status") != "not_collected":
            return False
        if row.get("empty_authorization_value") is not None:
            return False
        if row.get("authorization_granted") is not False:
            return False
        if row.get("live_preflight_allowed") is not False:
            return False
        if row.get("qdrant_write_allowed") is not False:
            return False
        if row.get("rebuild_allowed") is not False:
            return False
        if row.get("captures_formal_authorization_outcome") is not False:
            return False
    return True


def build_report(scaffold_path: Path = DEFAULT_SCAFFOLD_PATH) -> dict[str, Any]:
    scaffold = load_json(scaffold_path)
    inputs = as_dict(scaffold.get("inputs"))
    design_input = as_dict(inputs.get("production_rebuild_execution_design"))
    design_gate_input = as_dict(inputs.get("production_rebuild_execution_design_gate"))
    summary = as_dict(scaffold.get("summary"))
    guardrails = as_dict(scaffold.get("guardrails"))
    gate = as_dict(scaffold.get("authorization_record_scaffold_gate"))
    input_contract = as_dict(scaffold.get("input_contract"))
    packet = as_dict(scaffold.get("authorization_record_packet"))
    handoff = as_dict(scaffold.get("next_version_handoff"))
    traceability = as_dict(scaffold.get("traceability"))
    assertions = [row for row in as_list(scaffold.get("assertions")) if isinstance(row, dict)]
    rows = [row for row in as_list(scaffold.get("authorization_record_scaffold_rows")) if isinstance(row, dict)]

    checks = [
        check_row("scaffold_version", scaffold.get("version") == "0.4.14.2", "Scaffold report must be v0.4.14.2."),
        check_row(
            "scaffold_schema",
            scaffold.get("schema_kind") == "human_rebuild_authorization_record_scaffold",
            "Scaffold schema must match.",
        ),
        check_row(
            "scaffold_status",
            summary.get("status") == "pending_human_authorization_record"
            and summary.get("allowed_use") == "human_authorization_record_scaffold_only"
            and summary.get("allowed_next_step") == "human_rebuild_authorization_record_scaffold_gate"
            and summary.get("blockers") == [],
            "Scaffold must be pending human authorization record review and open only this gate.",
        ),
        check_row(
            "source_lineage",
            set(inputs) == {"production_rebuild_execution_design", "production_rebuild_execution_design_gate"}
            and design_input.get("present") is True
            and design_input.get("version") == "0.4.14.0"
            and design_input.get("schema_kind") == "production_rebuild_execution_design"
            and design_input.get("status") == "ready_for_production_rebuild_execution_design_gate"
            and design_gate_input.get("present") is True
            and design_gate_input.get("version") == "0.4.14.1"
            and design_gate_input.get("schema_kind") == "production_rebuild_execution_design_gate"
            and design_gate_input.get("status") == "passed",
            "Scaffold must retain only v0.4.14.0 design and v0.4.14.1 gate saved-report lineage.",
        ),
        check_row(
            "no_values_or_authorization",
            summary.get("human_value_count") == 0
            and summary.get("human_values_collected") is False
            and summary.get("formal_authorization_record_created") is False
            and summary.get("human_authorization_record_created") is False
            and summary.get("human_authorization_record_accepted") is False
            and summary.get("authorization_granted") is False
            and summary.get("live_preflight_run") is False
            and summary.get("production_rebuild_executed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("rebuild_allowed") is False
            and summary.get("full_eval") == "not_run",
            "Scaffold must remain blank, unaccepted, unauthorized, and non-executing.",
        ),
        check_row(
            "internal_gate_locked",
            gate.get("status") == "ready_for_human_authorization_record_review"
            and gate.get("allowed_use") == "human_authorization_record_scaffold_only"
            and gate.get("formal_authorization_record_created") is False
            and gate.get("human_authorization_record_created") is False
            and gate.get("human_authorization_record_accepted") is False
            and gate.get("authorization_granted") is False
            and gate.get("live_preflight_run") is False
            and gate.get("production_rebuild_executed") is False
            and gate.get("qdrant_write_allowed") is False
            and gate.get("rebuild_allowed") is False
            and gate.get("captures_formal_authorization_outcome") is False
            and gate.get("blockers") == [],
            "Internal scaffold gate fields must preserve blank non-authorization boundary.",
        ),
        check_row(
            "guardrails_locked",
            set(guardrails) == set(REQUIRED_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must remain scaffold-only and block authorization, live preflight, Qdrant, rebuild, runtime, and eval mutation.",
        ),
        check_row(
            "input_contract",
            input_contract.get("required_authorization_fields") == FIELD_ORDER
            and input_contract.get("required_record_contracts") == REQUIRED_RECORD_ORDER
            and as_list(input_contract.get("required_preflight_checks")) == REQUIRED_PREFLIGHT_ORDER
            and as_list(input_contract.get("required_abort_conditions")) == REQUIRED_ABORT_ORDER,
            "Input contract must preserve authorization fields, execution records, preflight checks, and abort conditions.",
        ),
        check_row(
            "row_blank_contract",
            rows_preserve_blank_contract(rows),
            "Rows must preserve order, required status, not_collected values, and blocked permissions.",
        ),
        check_row(
            "authorization_packet_blank",
            packet.get("packet_status") == "scaffold_only"
            and packet.get("formal_authorization_record_created") is False
            and packet.get("record_creation_status") == "not_created"
            and packet.get("record_acceptance_status") == "not_accepted"
            and packet.get("formal_authorization_value_status") == "not_collected"
            and packet.get("manual_completion_required") is True,
            "Authorization packet must remain a blank scaffold packet.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("allowed_next_step") == "human_rebuild_authorization_record_scaffold_gate"
            and set(as_list(handoff.get("not_allowed_yet"))) == REQUIRED_NOT_ALLOWED,
            "Handoff must block authorization acceptance, live preflight, Qdrant write, rebuild, runtime/eval mutation, and full eval substitution.",
        ),
        check_row(
            "traceability_counts",
            traceability.get("source_of_truth") == "v0.4.14.0 production rebuild execution design gated by v0.4.14.1"
            and traceability.get("authorization_field_count") == 10
            and traceability.get("record_contract_count") == 5
            and traceability.get("preflight_check_count") == 8
            and traceability.get("abort_condition_count") == 9,
            "Traceability counts must match the scaffold source contract.",
        ),
        check_row(
            "assertions_present",
            {row.get("assertion_id") for row in assertions} == REQUIRED_ASSERTIONS
            and all(row.get("passed") is True for row in assertions),
            "All scaffold-only/no-values/no-authorization/no-runtime assertions must pass.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_record_scaffold_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_record_scaffold": {
                "path": str(scaffold_path),
                "version": scaffold.get("version"),
                "schema_kind": scaffold.get("schema_kind"),
                "status": summary.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "human_rebuild_authorization_record_draft_design" if status == "passed" else "blocked",
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
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.14.3 Human Rebuild Authorization Record Scaffold Gate",
        "",
        "本 gate 只检查 v0.4.14.2 空白授权记录 scaffold。它不收集人工值，不创建或接受正式授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已收集人工值: `{summary.get('human_values_collected')}`",
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
        "通过本 gate 只允许进入 `human_rebuild_authorization_record_draft_design`，仍不代表已经允许填写正式授权、live preflight、Qdrant write 或生产 rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.3 human rebuild authorization record scaffold gate.")
    parser.add_argument("--scaffold", type=Path, default=DEFAULT_SCAFFOLD_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.scaffold)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Human rebuild authorization record scaffold gate: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
