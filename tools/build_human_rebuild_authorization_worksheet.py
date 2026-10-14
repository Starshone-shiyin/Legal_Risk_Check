"""Build the v0.4.13.15 human rebuild authorization worksheet.

The worksheet prepares human-review fields from the v0.4.13.13 authorization
design after the v0.4.13.14 design gate. It does not collect human values,
grant authorization, access Qdrant, rebuild collections, call RAG/embedding/LLM,
run full eval, or mutate runtime/eval artifacts.
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


VERSION = "0.4.13.15"

DEFAULT_DESIGN_PATH = legacy_report_path("rebuild_authorization_design_report.json")
DEFAULT_DESIGN_GATE_PATH = legacy_report_path("rebuild_authorization_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_worksheet_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_worksheet_v0.4.13.15.md")

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

OPTIONAL_FIELDS = {
    "target_collection": ["notes"],
    "rebuild_scope": ["scope_notes"],
    "source_version": ["repository_state_note"],
    "expected_id_drift_acknowledgement": ["drift_review_note"],
    "backup_plan": ["backup_verification_note"],
    "rollback_plan": ["rollback_test_reference"],
    "operator_approval": ["approval_channel_reference"],
    "maintenance_window": ["stakeholder_notice_reference"],
    "post_rebuild_validation_plan": ["validation_owner"],
    "abort_conditions_acknowledgement": ["additional_abort_condition"],
}

FIELD_GUIDANCE = {
    "target_collection": "Confirm the exact Qdrant collection target before any later rebuild authorization.",
    "rebuild_scope": "Confirm whether the future rebuild is full collection or isolated replacement, including included and excluded data.",
    "source_version": "Confirm code and report lineage before any future rebuild authorization.",
    "expected_id_drift_acknowledgement": "Confirm expected chunk_id and qdrant_point_id drift caused by chunk_index/chunk_count metadata.",
    "backup_plan": "Confirm snapshot/export or rollback collection details before any future rebuild authorization.",
    "rollback_plan": "Confirm restore/swap strategy, stop conditions, and operator responsibility.",
    "operator_approval": "Worksheet field only; this row must not be treated as current approval.",
    "maintenance_window": "Confirm when a separately authorized rebuild may occur and who owns communication.",
    "post_rebuild_validation_plan": "Confirm metadata, ID drift, limited smoke, rollback readiness, and full eval policy.",
    "abort_conditions_acknowledgement": "Confirm all abort conditions are visible and can stop a later rebuild.",
}

GUARDRAILS = {
    "worksheet_only": True,
    "saved_reports_only": True,
    "human_values_collected": False,
    "human_authorization_record_created": False,
    "captures_formal_authorization_outcome": False,
    "authorization_granted": False,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "runtime_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "authorized_actions",
    "ready_to_apply",
    "commands",
    "rebuild_steps",
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


def source_blockers(design_report: dict[str, Any], gate_report: dict[str, Any]) -> list[str]:
    design_summary = as_dict(design_report.get("summary"))
    gate_summary = as_dict(gate_report.get("summary"))
    design = as_dict(design_report.get("authorization_design"))
    blockers: list[str] = []
    if design_report.get("version") != "0.4.13.13":
        blockers.append("design_version_mismatch")
    if design_report.get("schema_kind") != "rebuild_authorization_design":
        blockers.append("design_schema_mismatch")
    if design_summary.get("status") != "ready_for_rebuild_authorization_design_gate":
        blockers.append("design_not_ready")
    if set(as_list(design.get("required_confirmation_fields"))) != set(FIELD_ORDER):
        blockers.append("design_required_field_drift")
    if not set(as_list(design.get("abort_conditions"))):
        blockers.append("design_abort_conditions_missing")
    if design_summary.get("authorization_granted") is not False:
        blockers.append("design_authorization_not_blocked")
    if design_summary.get("rebuild_allowed") is not False:
        blockers.append("design_rebuild_not_blocked")
    if gate_report.get("version") != "0.4.13.14":
        blockers.append("gate_version_mismatch")
    if gate_report.get("schema_kind") != "rebuild_authorization_design_gate":
        blockers.append("gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("gate_not_passed")
    if gate_summary.get("allowed_next_step") != "human_rebuild_authorization_worksheet":
        blockers.append("gate_next_step_mismatch")
    if gate_summary.get("human_authorization_record_created") is not False:
        blockers.append("gate_authorization_record_created")
    if gate_summary.get("authorization_granted") is not False:
        blockers.append("gate_authorization_not_blocked")
    if gate_summary.get("qdrant_write_allowed") is not False:
        blockers.append("gate_qdrant_write_not_blocked")
    if gate_summary.get("rebuild_allowed") is not False:
        blockers.append("gate_rebuild_not_blocked")
    if gate_summary.get("full_eval") != "not_run":
        blockers.append("gate_full_eval_drift")
    return blockers


def field_labels(field_id: str, design_report: dict[str, Any]) -> list[dict[str, str]]:
    sections = as_dict(as_dict(design_report.get("authorization_design")).get("authorization_sections"))
    required = [{"field": field, "requirement": "required"} for field in as_list(sections.get(field_id))]
    optional = [{"field": field, "requirement": "optional"} for field in OPTIONAL_FIELDS[field_id]]
    return required + optional


def build_rows(design_report: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, field_id in enumerate(FIELD_ORDER, start=1):
        rows.append(
            {
                "row_id": f"authorization_field_{index:02d}_{field_id}",
                "source_required_field": field_id,
                "worksheet_status": "ready_for_human_review" if ready else "blocked",
                "required": True,
                "field_labels": field_labels(field_id, design_report),
                "human_review_required": True,
                "human_value_status": "not_collected",
                "authorization_granted": False,
                "rebuild_allowed": False,
                "qdrant_write_allowed": False,
                "captures_formal_authorization_outcome": False,
                "guidance": FIELD_GUIDANCE[field_id],
            }
        )
    return rows


def forbidden_output_keys(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted(set(matches))


def build_report(
    design_path: Path = DEFAULT_DESIGN_PATH,
    design_gate_path: Path = DEFAULT_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    design_report = load_json(design_path)
    gate_report = load_json(design_gate_path)
    blockers = source_blockers(design_report, gate_report)
    ready = not blockers
    rows = build_rows(design_report, ready)
    status = "ready_for_human_rebuild_authorization_review" if ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_worksheet",
        "scope": "human rebuild authorization worksheet only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "rebuild_authorization_design": {
                "path": str(design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": as_dict(design_report.get("summary")).get("status"),
            },
            "rebuild_authorization_design_gate": {
                "path": str(design_gate_path),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
                "status": as_dict(gate_report.get("summary")).get("status"),
            },
        },
        "guardrails": GUARDRAILS,
        "worksheet_gate": {
            "status": status,
            "allowed_use": "human_authorization_discussion_only" if ready else "blocked",
            "human_authorization_record_created": False,
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "captures_formal_authorization_outcome": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "worksheet_row_count": len(rows),
            "required_field_count": len(rows),
            "collected_value_count": 0,
            "human_values_collected": False,
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
            "allowed_next_step": "human_rebuild_authorization_worksheet_gate" if ready else "blocked",
            "blockers": blockers,
        },
        "authorization_worksheet_rows": rows,
        "operator_instructions": [
            "This worksheet is not an approval record.",
            "All required fields remain not_collected in this version.",
            "Any unclear backup, rollback, target collection, or approval value blocks future authorization.",
        ],
        "handoff": {
            "next_allowed_step": "gate this blank human authorization worksheet" if ready else "resolve worksheet blockers",
            "not_allowed_yet": [
                "accept this worksheet as authorization",
                "write Qdrant",
                "rebuild collection",
                "run rebuild preflight against a live collection",
                "call rag_query",
                "run full eval",
            ],
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        report["worksheet_gate"]["status"] = "blocked"
        report["worksheet_gate"]["blockers"] = sorted(set(blockers + ["forbidden_output_key_present"]))
        report["summary"]["status"] = "blocked"
        report["summary"]["blockers"] = report["worksheet_gate"]["blockers"]
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    gate = as_dict(report.get("worksheet_gate"))
    lines = [
        "# v0.4.13.15 Human Rebuild Authorization Worksheet",
        "",
        "本 worksheet 只列出未来人工授权需要填写的字段。当前没有收集任何人工值，没有创建授权记录，也没有授予生产 rebuild 权限。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{gate.get('status')}`",
        f"- 字段数: `{summary.get('worksheet_row_count')}`",
        f"- 已收集字段数: `{summary.get('collected_value_count')}`",
        f"- 是否已经授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        "",
        "## Worksheet 字段",
        "",
    ]
    for row in report.get("authorization_worksheet_rows", []):
        required = [item["field"] for item in row.get("field_labels", []) if item.get("requirement") == "required"]
        optional = [item["field"] for item in row.get("field_labels", []) if item.get("requirement") == "optional"]
        lines.append(f"- `{row.get('source_required_field')}`: required={required}; optional={optional}; status=`not_collected`")
    lines.extend(["", "通过本 worksheet 只允许进入 worksheet gate，仍不代表已经允许生产 Qdrant rebuild。"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.15 human rebuild authorization worksheet.")
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
        "Human rebuild authorization worksheet: "
        f"{summary.get('status')}, rows={summary.get('worksheet_row_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
