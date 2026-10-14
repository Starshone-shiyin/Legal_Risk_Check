"""Check the v0.4.13.16 human rebuild authorization worksheet gate."""

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


VERSION = "0.4.13.16"

DEFAULT_WORKSHEET_PATH = legacy_report_path("human_rebuild_authorization_worksheet_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/human_rebuild_authorization_worksheet_gate_v0.4.13.16.md")

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

REQUIRED_GUARDRAILS = {
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


def row_contract_ok(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != len(FIELD_ORDER):
        return False
    if [row.get("source_required_field") for row in rows] != FIELD_ORDER:
        return False
    for row in rows:
        labels = as_list(row.get("field_labels"))
        if not any(as_dict(label).get("requirement") == "required" for label in labels):
            return False
        if not any(as_dict(label).get("requirement") == "optional" for label in labels):
            return False
        if row.get("human_value_status") != "not_collected":
            return False
        if row.get("authorization_granted") is not False:
            return False
        if row.get("rebuild_allowed") is not False:
            return False
        if row.get("qdrant_write_allowed") is not False:
            return False
        if row.get("captures_formal_authorization_outcome") is not False:
            return False
    return True


def build_report(worksheet_path: Path = DEFAULT_WORKSHEET_PATH) -> dict[str, Any]:
    worksheet = load_json(worksheet_path)
    gate = as_dict(worksheet.get("worksheet_gate"))
    summary = as_dict(worksheet.get("summary"))
    guardrails = as_dict(worksheet.get("guardrails"))
    rows = [row for row in as_list(worksheet.get("authorization_worksheet_rows")) if isinstance(row, dict)]
    handoff = as_dict(worksheet.get("handoff"))

    checks = [
        check_row("worksheet_version", worksheet.get("version") == "0.4.13.15", "Worksheet report must be v0.4.13.15."),
        check_row("worksheet_schema", worksheet.get("schema_kind") == "human_rebuild_authorization_worksheet", "Worksheet schema must match."),
        check_row(
            "worksheet_status",
            gate.get("status") == "ready_for_human_rebuild_authorization_review"
            and gate.get("allowed_use") == "human_authorization_discussion_only"
            and summary.get("allowed_next_step") == "human_rebuild_authorization_worksheet_gate",
            "Worksheet must be ready for this gate only.",
        ),
        check_row(
            "no_values_or_authorization",
            summary.get("collected_value_count") == 0
            and summary.get("human_values_collected") is False
            and gate.get("human_authorization_record_created") is False
            and gate.get("authorization_granted") is False
            and gate.get("qdrant_write_allowed") is False
            and gate.get("rebuild_allowed") is False
            and gate.get("captures_formal_authorization_outcome") is False,
            "Worksheet must not collect values, create authorization, allow Qdrant write, or allow rebuild.",
        ),
        check_row("guardrails_locked", all(guardrails.get(k) == v for k, v in REQUIRED_GUARDRAILS.items()), "Guardrails must remain locked."),
        check_row("row_contract", row_contract_ok(rows), "Worksheet rows must preserve required order, labels, not_collected values, and blocked permissions."),
        check_row(
            "handoff_boundaries",
            handoff.get("next_allowed_step") == "gate this blank human authorization worksheet"
            and {"accept this worksheet as authorization", "write Qdrant", "rebuild collection"}.issubset(set(as_list(handoff.get("not_allowed_yet")))),
            "Handoff must keep authorization acceptance, Qdrant write, and rebuild blocked.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "human_rebuild_authorization_worksheet_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_worksheet": {
                "path": str(worksheet_path),
                "version": worksheet.get("version"),
                "schema_kind": worksheet.get("schema_kind"),
                "status": gate.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "rebuild_runbook_preflight_contract" if status == "passed" else "blocked",
            "human_values_collected": False,
            "authorization_granted": False,
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
        "# v0.4.13.16 Human Rebuild Authorization Worksheet Gate",
        "",
        "本 gate 只验证 v0.4.13.15 空白 worksheet 的结构和未授权边界。它不收集人工值，不创建授权记录，不访问 Qdrant，不 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已经授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 检查项",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    lines.extend(["", "通过本 gate 只允许进入 runbook/preflight contract design，仍不代表已经允许生产 Qdrant rebuild。"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.16 human rebuild authorization worksheet gate.")
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.worksheet)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Human rebuild authorization worksheet gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
