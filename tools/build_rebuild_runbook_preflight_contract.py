"""Build the v0.4.13.17 rebuild runbook/preflight contract.

The contract reads the saved worksheet gate and planning reports. It defines the
future rebuild execution runbook and preflight report contract without running
live preflight, accessing Qdrant, rebuilding collections, calling RAG/LLM, or
mutating runtime/eval artifacts.
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


VERSION = "0.4.13.17"

DEFAULT_WORKSHEET_GATE_PATH = legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json")
DEFAULT_WORKSHEET_PATH = legacy_report_path("human_rebuild_authorization_worksheet_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("rebuild_runbook_preflight_contract_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/rebuild_runbook_preflight_contract_v0.4.13.17.md")

PREFLIGHT_CHECKS = [
    "authorization_record_present_and_valid",
    "target_collection_confirmed",
    "backup_or_rollback_collection_verified",
    "source_lineage_confirmed",
    "expected_id_drift_acknowledged",
    "maintenance_window_active",
    "rollback_owner_available",
    "post_rebuild_validation_owner_available",
]

RUNBOOK_PHASES = [
    "preflight_validation",
    "backup_or_rollback_verification",
    "target_collection_lock_confirmation",
    "rebuild_execution",
    "post_rebuild_metadata_validation",
    "post_rebuild_smoke_validation",
    "rollback_or_acceptance_decision",
]

ABORT_CONDITIONS = [
    "authorization_record_missing_or_invalid",
    "target_collection_mismatch",
    "backup_or_rollback_unavailable",
    "source_lineage_mismatch",
    "unexpected_preflight_failure",
    "post_rebuild_validation_failure",
    "rollback_owner_unavailable",
]

GUARDRAILS = {
    "contract_only": True,
    "saved_reports_only": True,
    "live_preflight_run": False,
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


def source_blockers(gate_report: dict[str, Any], worksheet_report: dict[str, Any]) -> list[str]:
    gate_summary = as_dict(gate_report.get("summary"))
    worksheet_gate = as_dict(worksheet_report.get("worksheet_gate"))
    blockers: list[str] = []
    if gate_report.get("version") != "0.4.13.16":
        blockers.append("worksheet_gate_version_mismatch")
    if gate_report.get("schema_kind") != "human_rebuild_authorization_worksheet_gate":
        blockers.append("worksheet_gate_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("worksheet_gate_not_passed")
    if gate_summary.get("allowed_next_step") != "rebuild_runbook_preflight_contract":
        blockers.append("worksheet_gate_next_step_mismatch")
    if gate_summary.get("authorization_granted") is not False:
        blockers.append("worksheet_gate_authorization_not_blocked")
    if gate_summary.get("rebuild_allowed") is not False:
        blockers.append("worksheet_gate_rebuild_not_blocked")
    if worksheet_report.get("version") != "0.4.13.15":
        blockers.append("worksheet_version_mismatch")
    if worksheet_report.get("schema_kind") != "human_rebuild_authorization_worksheet":
        blockers.append("worksheet_schema_mismatch")
    if worksheet_gate.get("authorization_granted") is not False:
        blockers.append("worksheet_authorization_not_blocked")
    if worksheet_gate.get("rebuild_allowed") is not False:
        blockers.append("worksheet_rebuild_not_blocked")
    return blockers


def build_report(
    worksheet_gate_path: Path = DEFAULT_WORKSHEET_GATE_PATH,
    worksheet_path: Path = DEFAULT_WORKSHEET_PATH,
) -> dict[str, Any]:
    gate_report = load_json(worksheet_gate_path)
    worksheet_report = load_json(worksheet_path)
    blockers = source_blockers(gate_report, worksheet_report)
    ready = not blockers
    status = "ready_for_series_closeout" if ready else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "rebuild_runbook_preflight_contract",
        "scope": "future rebuild execution runbook and preflight contract only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "human_rebuild_authorization_worksheet_gate": {
                "path": str(worksheet_gate_path),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
                "status": as_dict(gate_report.get("summary")).get("status"),
            },
            "human_rebuild_authorization_worksheet": {
                "path": str(worksheet_path),
                "version": worksheet_report.get("version"),
                "schema_kind": worksheet_report.get("schema_kind"),
                "status": as_dict(worksheet_report.get("worksheet_gate")).get("status"),
            },
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": "v0.4.13_series_closeout" if ready else "blocked",
            "preflight_check_count": len(PREFLIGHT_CHECKS),
            "runbook_phase_count": len(RUNBOOK_PHASES),
            "abort_condition_count": len(ABORT_CONDITIONS),
            "live_preflight_run": False,
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
            "blockers": blockers,
        },
        "future_runbook_contract": {
            "phase_order": RUNBOOK_PHASES,
            "preflight_checks": PREFLIGHT_CHECKS,
            "abort_conditions": ABORT_CONDITIONS,
            "required_future_inputs": [
                "valid_human_authorization_record",
                "target_collection",
                "backup_or_rollback_reference",
                "source_lineage_reference",
                "maintenance_window",
            ],
            "future_output_fields": [
                "preflight_status",
                "rebuild_execution_status",
                "post_rebuild_validation_status",
                "rollback_status",
                "final_acceptance_status",
            ],
        },
        "handoff": {
            "next_allowed_step": "close out v0.4.13 planning series" if ready else "resolve contract blockers",
            "not_allowed_yet": [
                "run live preflight",
                "write Qdrant",
                "rebuild collection",
                "call rag_query",
                "run full eval",
                "modify runtime or eval artifacts",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    contract = as_dict(report.get("future_runbook_contract"))
    lines = [
        "# v0.4.13.17 Rebuild Runbook / Preflight Contract",
        "",
        "本 contract 只定义未来 rebuild execution series 的 runbook 和 preflight 报告契约。它不运行 live preflight，不访问 Qdrant，不 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- live preflight: `{summary.get('live_preflight_run')}`",
        f"- 是否已经授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## Preflight Checks",
        "",
    ]
    for item in contract.get("preflight_checks", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "通过本 contract 只允许进入 v0.4.13 series closeout，仍不代表已经允许生产 Qdrant rebuild。"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.17 rebuild runbook/preflight contract.")
    parser.add_argument("--worksheet-gate", type=Path, default=DEFAULT_WORKSHEET_GATE_PATH)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.worksheet_gate, args.worksheet)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Rebuild runbook/preflight contract: "
        f"{summary.get('status')}, preflight_checks={summary.get('preflight_check_count')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
