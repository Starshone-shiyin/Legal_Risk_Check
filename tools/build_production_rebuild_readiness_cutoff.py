"""Build the v0.4.14.14 production rebuild readiness cutoff.

This cutoff reads only saved reports and decides whether the v0.4.14 input
scaffold chain should stop. It does not create an importer, collect or import
human values, create or accept authorization, run live preflight, access
Qdrant, rebuild collections, call RAG/embedding/LLM, run full eval, or mutate
runtime and eval artifacts.
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


VERSION = "0.4.14.14"

DEFAULT_SOURCE_PATCH_PATH = legacy_report_path("ingestion_metadata_source_patch_report.json")
DEFAULT_DRY_RUN_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json")
DEFAULT_DRY_RUN_GATE_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json")
DEFAULT_AUTH_DESIGN_PATH = legacy_report_path("rebuild_authorization_design_report.json")
DEFAULT_AUTH_GATE_PATH = legacy_report_path("rebuild_authorization_design_gate_report.json")
DEFAULT_WORKSHEET_PATH = legacy_report_path("human_rebuild_authorization_worksheet_report.json")
DEFAULT_WORKSHEET_GATE_PATH = legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json")
DEFAULT_RUNBOOK_PATH = legacy_report_path("rebuild_runbook_preflight_contract_report.json")
DEFAULT_PLANNING_CLOSEOUT_PATH = legacy_report_path("ingestion_metadata_rebuild_planning_series_closeout_report.json")
DEFAULT_EXECUTION_DESIGN_PATH = legacy_report_path("production_rebuild_execution_design_report.json")
DEFAULT_EXECUTION_DESIGN_GATE_PATH = legacy_report_path("production_rebuild_execution_design_gate_report.json")
DEFAULT_FORM_SCAFFOLD_GATE_PATH = legacy_report_path(
    "human_rebuild_authorization_record_input_form_scaffold_gate_report.json"
)
DEFAULT_PROJECT_HEALTH_PATH = legacy_report_path("project_health_check_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_readiness_cutoff_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/production_rebuild_readiness_cutoff_v0.4.14.14.md")

GUARDRAILS = {
    "cutoff_only": True,
    "saved_reports_only": True,
    "stops_input_scaffold_expansion": True,
    "input_importer_created": False,
    "human_values_collected": False,
    "input_values_imported": False,
    "input_values_validated": False,
    "formal_authorization_record_created": False,
    "human_authorization_record_accepted": False,
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

SOURCE_EXPECTATIONS = {
    "source_patch": {
        "version": "0.4.13.8",
        "schema_kind": "ingestion_metadata_source_patch_check",
        "status": "passed",
    },
    "post_patch_dry_run": {
        "version": "0.4.13.11",
        "schema_kind": "ingestion_metadata_patch_post_patch_rebuild_dry_run",
        "status": "passed",
    },
    "post_patch_dry_run_gate": {
        "version": "0.4.13.12",
        "schema_kind": "ingestion_metadata_patch_post_patch_rebuild_dry_run_gate",
        "status": "passed",
    },
    "authorization_design": {
        "version": "0.4.13.13",
        "schema_kind": "rebuild_authorization_design",
        "status": "ready_for_rebuild_authorization_design_gate",
    },
    "authorization_gate": {
        "version": "0.4.13.14",
        "schema_kind": "rebuild_authorization_design_gate",
        "status": "passed",
    },
    "worksheet": {
        "version": "0.4.13.15",
        "schema_kind": "human_rebuild_authorization_worksheet",
        "status": "ready_for_human_rebuild_authorization_review",
    },
    "worksheet_gate": {
        "version": "0.4.13.16",
        "schema_kind": "human_rebuild_authorization_worksheet_gate",
        "status": "passed",
    },
    "runbook_contract": {
        "version": "0.4.13.17",
        "schema_kind": "rebuild_runbook_preflight_contract",
        "status": "ready_for_series_closeout",
    },
    "planning_closeout": {
        "version": "0.4.13.18",
        "schema_kind": "ingestion_metadata_rebuild_planning_series_closeout",
        "status": "closed_for_execution_design_handoff",
    },
    "execution_design": {
        "version": "0.4.14.0",
        "schema_kind": "production_rebuild_execution_design",
        "status": "ready_for_production_rebuild_execution_design_gate",
    },
    "execution_design_gate": {
        "version": "0.4.14.1",
        "schema_kind": "production_rebuild_execution_design_gate",
        "status": "passed",
    },
    "input_form_scaffold_gate": {
        "version": "0.4.14.13",
        "schema_kind": "human_rebuild_authorization_record_input_form_scaffold_gate",
        "status": "passed",
    },
    "project_health": {
        "version": None,
        "min_version": VERSION,
        "schema_kind": None,
        "status": "passed",
    },
}

REQUIRED_ENGINEERING_READY_FLAGS = {
    "source_patch_completed": True,
    "post_patch_dry_run_passed": True,
    "expected_id_drift_accounted": True,
    "forbidden_drift_absent": True,
    "authorization_chain_gated": True,
    "execution_design_gated": True,
    "input_scaffold_chain_gated": True,
    "project_health_passed": True,
}

EXECUTION_BLOCKERS = [
    "formal_human_authorization_record_not_created_or_accepted",
    "live_preflight_not_run",
    "backup_or_snapshot_not_live_verified",
    "qdrant_target_collection_not_locked",
    "production_rebuild_not_executed",
    "post_rebuild_rag_quality_not_validated",
]

MINIMAL_ENGINEERING_PATH = [
    "production_rebuild_live_preflight_runner_design",
    "production_rebuild_live_preflight_runner_gate",
    "human_authorization_record_minimal_intake_or_import_design",
    "live_preflight_runner",
    "preflight_gate_with_backup_and_authorization_checks",
    "production_rebuild_execution_runner_or_manual_runbook",
    "post_rebuild_metadata_and_rag_quality_validation",
]

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "authorized_actions",
    "ready_to_apply",
    "commands",
    "rebuild_steps",
    "qdrant_operation_log",
    "implementation_commands",
    "execution_commands",
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


def source_status(report: dict[str, Any]) -> str | None:
    summary = as_dict(report.get("summary"))
    return summary.get("status")


def version_tuple(value: str | None) -> tuple[int, ...]:
    if not isinstance(value, str):
        return ()
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return ()


def source_meta(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "path": str(path),
        "present": path.exists(),
        "version": report.get("version"),
        "schema_kind": report.get("schema_kind"),
        "status": summary.get("status"),
        "allowed_next_step": summary.get("allowed_next_step"),
    }


def source_blockers(reports: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for key, expected in SOURCE_EXPECTATIONS.items():
        report = reports[key]
        if not report:
            blockers.append(f"{key}_missing")
        if expected["version"] is not None and report.get("version") != expected["version"]:
            blockers.append(f"{key}_version_mismatch")
        if expected.get("min_version") is not None:
            actual_version = version_tuple(report.get("version"))
            minimum_version = version_tuple(expected.get("min_version"))
            if not actual_version or actual_version < minimum_version:
                blockers.append(f"{key}_version_mismatch")
        if expected["schema_kind"] is not None and report.get("schema_kind") != expected["schema_kind"]:
            blockers.append(f"{key}_schema_mismatch")
        if source_status(report) != expected["status"]:
            blockers.append(f"{key}_status_mismatch")
        summary = as_dict(report.get("summary"))
        for field in [
            "authorization_granted",
            "qdrant_write_allowed",
            "rebuild_allowed",
        ]:
            if field in summary and summary.get(field) is not False:
                blockers.append(f"{key}_{field}_mismatch")
        if "live_preflight_run" in summary and summary.get("live_preflight_run") is not False:
            blockers.append(f"{key}_live_preflight_run_mismatch")
        if "production_rebuild_executed" in summary and summary.get("production_rebuild_executed") is not False:
            blockers.append(f"{key}_production_rebuild_executed_mismatch")
        if "full_eval" in summary and summary.get("full_eval") != "not_run":
            blockers.append(f"{key}_full_eval_mismatch")
        if forbidden_output_keys(report):
            blockers.append(f"{key}_forbidden_output_key_present")
    return sorted(set(blockers))


def derive_readiness_flags(reports: dict[str, dict[str, Any]]) -> dict[str, bool]:
    source_patch = as_dict(reports["source_patch"].get("summary"))
    dry_run = as_dict(reports["post_patch_dry_run"].get("summary"))
    dry_run_gate = as_dict(reports["post_patch_dry_run_gate"].get("summary"))
    auth_gate = as_dict(reports["authorization_gate"].get("summary"))
    worksheet_gate = as_dict(reports["worksheet_gate"].get("summary"))
    runbook = as_dict(reports["runbook_contract"].get("summary"))
    execution_gate = as_dict(reports["execution_design_gate"].get("summary"))
    input_gate = as_dict(reports["input_form_scaffold_gate"].get("summary"))
    project_health = as_dict(reports["project_health"].get("summary"))
    return {
        "source_patch_completed": source_patch.get("implementation_completed") is True,
        "post_patch_dry_run_passed": dry_run.get("status") == "passed" and dry_run_gate.get("status") == "passed",
        "expected_id_drift_accounted": dry_run.get("expected_id_drift_rows") == dry_run.get("row_count") == 9,
        "forbidden_drift_absent": dry_run.get("forbidden_drift_count") == 0
        and dry_run.get("blocking_condition_count") == 0,
        "authorization_chain_gated": auth_gate.get("status") == "passed"
        and worksheet_gate.get("status") == "passed"
        and runbook.get("status") == "ready_for_series_closeout",
        "execution_design_gated": execution_gate.get("status") == "passed",
        "input_scaffold_chain_gated": input_gate.get("status") == "passed",
        "project_health_passed": project_health.get("status") == "passed"
        and project_health.get("failed_checks") == 0,
    }


def build_report(
    source_patch_path: Path = DEFAULT_SOURCE_PATCH_PATH,
    dry_run_path: Path = DEFAULT_DRY_RUN_PATH,
    dry_run_gate_path: Path = DEFAULT_DRY_RUN_GATE_PATH,
    auth_design_path: Path = DEFAULT_AUTH_DESIGN_PATH,
    auth_gate_path: Path = DEFAULT_AUTH_GATE_PATH,
    worksheet_path: Path = DEFAULT_WORKSHEET_PATH,
    worksheet_gate_path: Path = DEFAULT_WORKSHEET_GATE_PATH,
    runbook_path: Path = DEFAULT_RUNBOOK_PATH,
    planning_closeout_path: Path = DEFAULT_PLANNING_CLOSEOUT_PATH,
    execution_design_path: Path = DEFAULT_EXECUTION_DESIGN_PATH,
    execution_design_gate_path: Path = DEFAULT_EXECUTION_DESIGN_GATE_PATH,
    form_scaffold_gate_path: Path = DEFAULT_FORM_SCAFFOLD_GATE_PATH,
    project_health_path: Path = DEFAULT_PROJECT_HEALTH_PATH,
) -> dict[str, Any]:
    reports = {
        "source_patch": load_json(source_patch_path),
        "post_patch_dry_run": load_json(dry_run_path),
        "post_patch_dry_run_gate": load_json(dry_run_gate_path),
        "authorization_design": load_json(auth_design_path),
        "authorization_gate": load_json(auth_gate_path),
        "worksheet": load_json(worksheet_path),
        "worksheet_gate": load_json(worksheet_gate_path),
        "runbook_contract": load_json(runbook_path),
        "planning_closeout": load_json(planning_closeout_path),
        "execution_design": load_json(execution_design_path),
        "execution_design_gate": load_json(execution_design_gate_path),
        "input_form_scaffold_gate": load_json(form_scaffold_gate_path),
        "project_health": load_json(project_health_path),
    }
    blockers = source_blockers(reports)
    flags = derive_readiness_flags(reports)
    missing_ready_flags = sorted(key for key, expected in REQUIRED_ENGINEERING_READY_FLAGS.items() if flags.get(key) != expected)
    status = "ready_for_live_preflight_runner_design_cutoff" if not blockers and not missing_ready_flags else "blocked"
    allowed_next_step = "production_rebuild_live_preflight_runner_design" if status != "blocked" else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "production_rebuild_readiness_cutoff",
        "scope": "cut off input scaffold expansion and decide live preflight design readiness",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "source_patch": source_meta(source_patch_path, reports["source_patch"]),
            "post_patch_dry_run": source_meta(dry_run_path, reports["post_patch_dry_run"]),
            "post_patch_dry_run_gate": source_meta(dry_run_gate_path, reports["post_patch_dry_run_gate"]),
            "authorization_design": source_meta(auth_design_path, reports["authorization_design"]),
            "authorization_gate": source_meta(auth_gate_path, reports["authorization_gate"]),
            "worksheet": source_meta(worksheet_path, reports["worksheet"]),
            "worksheet_gate": source_meta(worksheet_gate_path, reports["worksheet_gate"]),
            "runbook_contract": source_meta(runbook_path, reports["runbook_contract"]),
            "planning_closeout": source_meta(planning_closeout_path, reports["planning_closeout"]),
            "execution_design": source_meta(execution_design_path, reports["execution_design"]),
            "execution_design_gate": source_meta(execution_design_gate_path, reports["execution_design_gate"]),
            "input_form_scaffold_gate": source_meta(form_scaffold_gate_path, reports["input_form_scaffold_gate"]),
            "project_health": source_meta(project_health_path, reports["project_health"]),
        },
        "guardrails": GUARDRAILS,
        "engineering_cutoff_decision": {
            "status": "stop_input_scaffold_expansion" if status != "blocked" else "blocked",
            "further_input_or_importer_scaffold_versions_recommended": False if status != "blocked" else None,
            "reason": (
                "The source patch, dry-run, execution design, input form scaffold gate, and project health are sufficient to stop adding scaffold-only input reports and move to live preflight runner design."
                if status != "blocked"
                else "Required saved-report readiness inputs are missing or drifted."
            ),
        },
        "execution_readiness": {
            "live_preflight_runner_design_ready": status != "blocked",
            "live_preflight_run_allowed_now": False,
            "production_rebuild_allowed_now": False,
            "qdrant_write_allowed_now": False,
            "formal_authorization_required_before_execution": True,
            "execution_blockers": EXECUTION_BLOCKERS,
        },
        "readiness_flags": flags,
        "minimal_engineering_path": MINIMAL_ENGINEERING_PATH,
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "source_report_count": len(reports),
            "missing_ready_flags": missing_ready_flags,
            "blockers": blockers,
            "stop_scaffold_expansion": status != "blocked",
            "live_preflight_run_allowed": False,
            "production_rebuild_allowed": False,
            "qdrant_write_allowed": False,
            "authorization_granted": False,
            "full_eval": "not_run",
        },
    }
    forbidden = forbidden_output_keys(report)
    if forbidden:
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_next_step"] = "blocked"
        report["summary"]["blockers"] = sorted(set(report["summary"]["blockers"] + ["forbidden_output_key_present"]))
        report["forbidden_output_keys_detected"] = forbidden
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    execution = as_dict(report.get("execution_readiness"))
    lines = [
        "# v0.4.14.14 Production Rebuild Readiness Cutoff",
        "",
        "本版本是生产 rebuild 前的收口判断，不再继续扩 input/importer scaffold。它只读取 saved reports，判断是否可以从治理链切入 live preflight runner design；不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 停止继续 scaffold 扩张: `{summary.get('stop_scaffold_expansion')}`",
        f"- 是否允许现在运行 live preflight: `{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许现在 production rebuild: `{summary.get('production_rebuild_allowed')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        "",
        "## 执行前仍缺",
        "",
    ]
    for blocker in execution.get("execution_blockers", []):
        lines.append(f"- `{blocker}`")
    lines.extend([
        "",
        "## 最短工程路径",
        "",
    ])
    for step in report.get("minimal_engineering_path", []):
        lines.append(f"- `{step}`")
    lines.extend([
        "",
        "结论：可以停止继续堆 input/importer scaffold 报告，下一步转入 `production_rebuild_live_preflight_runner_design`。这仍不代表已经允许 live preflight、Qdrant write 或 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.14 production rebuild readiness cutoff.")
    parser.add_argument("--source-patch", type=Path, default=DEFAULT_SOURCE_PATCH_PATH)
    parser.add_argument("--dry-run", type=Path, default=DEFAULT_DRY_RUN_PATH)
    parser.add_argument("--dry-run-gate", type=Path, default=DEFAULT_DRY_RUN_GATE_PATH)
    parser.add_argument("--auth-design", type=Path, default=DEFAULT_AUTH_DESIGN_PATH)
    parser.add_argument("--auth-gate", type=Path, default=DEFAULT_AUTH_GATE_PATH)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET_PATH)
    parser.add_argument("--worksheet-gate", type=Path, default=DEFAULT_WORKSHEET_GATE_PATH)
    parser.add_argument("--runbook", type=Path, default=DEFAULT_RUNBOOK_PATH)
    parser.add_argument("--planning-closeout", type=Path, default=DEFAULT_PLANNING_CLOSEOUT_PATH)
    parser.add_argument("--execution-design", type=Path, default=DEFAULT_EXECUTION_DESIGN_PATH)
    parser.add_argument("--execution-design-gate", type=Path, default=DEFAULT_EXECUTION_DESIGN_GATE_PATH)
    parser.add_argument("--form-scaffold-gate", type=Path, default=DEFAULT_FORM_SCAFFOLD_GATE_PATH)
    parser.add_argument("--project-health", type=Path, default=DEFAULT_PROJECT_HEALTH_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.source_patch,
        args.dry_run,
        args.dry_run_gate,
        args.auth_design,
        args.auth_gate,
        args.worksheet,
        args.worksheet_gate,
        args.runbook,
        args.planning_closeout,
        args.execution_design,
        args.execution_design_gate,
        args.form_scaffold_gate,
        args.project_health,
    )
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild readiness cutoff: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
