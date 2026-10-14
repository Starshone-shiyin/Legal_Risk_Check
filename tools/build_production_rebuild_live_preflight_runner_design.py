"""Build the v0.4.14.15 production rebuild live preflight runner design.

This design reads only the v0.4.14.14 readiness cutoff report. It defines the
minimum future live preflight runner contract without running live preflight,
accessing Qdrant, creating authorization, rebuilding collections, calling
RAG/embedding/LLM, running full eval, or mutating runtime and eval artifacts.
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


VERSION = "0.4.14.15"

DEFAULT_READINESS_CUTOFF_PATH = legacy_report_path("production_rebuild_readiness_cutoff_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_live_preflight_runner_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md")

READINESS_EXPECTATION = {
    "version": "0.4.14.14",
    "schema_kind": "production_rebuild_readiness_cutoff",
    "status": "ready_for_live_preflight_runner_design_cutoff",
    "allowed_next_step": "production_rebuild_live_preflight_runner_design",
}

READINESS_BOUNDARIES = {
    "stop_scaffold_expansion": True,
    "live_preflight_run_allowed": False,
    "production_rebuild_allowed": False,
    "qdrant_write_allowed": False,
    "authorization_granted": False,
    "full_eval": "not_run",
}

GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "readiness_cutoff_only": True,
    "runner_created": False,
    "runner_executed": False,
    "human_authorization_record_created": False,
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
    "input_scaffold_expansion": "disallowed",
    "importer_scaffold_expansion": "disallowed",
}

FUTURE_INPUTS = [
    {
        "field": "authorization_record_reference",
        "required": True,
        "source": "future formal authorization record",
        "current_status": "not_collected",
    },
    {
        "field": "target_collection",
        "required": True,
        "source": "future human authorization and environment check",
        "current_status": "not_collected",
    },
    {
        "field": "backup_or_snapshot_reference",
        "required": True,
        "source": "future operator-provided backup/snapshot reference",
        "current_status": "not_verified",
    },
    {
        "field": "source_lineage_reference",
        "required": True,
        "source": "v0.4.13.8 source patch and post-patch dry-run lineage",
        "current_status": "available_as_saved_report_lineage",
    },
    {
        "field": "expected_id_drift_acknowledgement",
        "required": True,
        "source": "future human authorization record",
        "current_status": "not_collected",
    },
    {
        "field": "maintenance_window",
        "required": True,
        "source": "future operator-provided execution window",
        "current_status": "not_collected",
    },
]

PREFLIGHT_CHECKS = [
    "authorization_record_present_and_accepted",
    "target_collection_matches_authorization",
    "qdrant_endpoint_reachable_read_only",
    "backup_or_snapshot_reference_verified",
    "source_patch_lineage_matches_expected_version",
    "expected_id_drift_acknowledged",
    "maintenance_window_active",
    "post_rebuild_validation_plan_present",
]

OUTPUT_FIELDS = [
    "preflight_status",
    "checked_at",
    "target_collection",
    "authorization_record_reference",
    "backup_or_snapshot_reference",
    "check_results",
    "blocking_conditions",
    "live_preflight_readiness",
    "qdrant_write_allowed",
    "production_rebuild_allowed",
]

BLOCKING_CONDITIONS = [
    "authorization_record_missing_or_not_accepted",
    "target_collection_missing_or_mismatch",
    "qdrant_read_only_reachability_failed",
    "backup_or_snapshot_reference_unverified",
    "source_lineage_mismatch",
    "expected_id_drift_not_acknowledged",
    "maintenance_window_inactive",
    "post_rebuild_validation_plan_missing",
]

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "authorized_actions",
    "ready_to_apply",
    "commands",
    "execution_commands",
    "implementation_commands",
    "qdrant_operation_log",
    "rebuild_steps",
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


def cutoff_blockers(cutoff: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    summary = as_dict(cutoff.get("summary"))
    if not cutoff:
        blockers.append("readiness_cutoff_missing")
        return blockers
    if cutoff.get("version") != READINESS_EXPECTATION["version"]:
        blockers.append("readiness_cutoff_version_mismatch")
    if cutoff.get("schema_kind") != READINESS_EXPECTATION["schema_kind"]:
        blockers.append("readiness_cutoff_schema_mismatch")
    if summary.get("status") != READINESS_EXPECTATION["status"]:
        blockers.append("readiness_cutoff_status_mismatch")
    if summary.get("allowed_next_step") != READINESS_EXPECTATION["allowed_next_step"]:
        blockers.append("readiness_cutoff_next_step_mismatch")
    for field, expected in READINESS_BOUNDARIES.items():
        if summary.get(field) != expected:
            blockers.append(f"readiness_cutoff_{field}_mismatch")
    if forbidden_output_keys(cutoff):
        blockers.append("readiness_cutoff_forbidden_output_key_present")
    return sorted(set(blockers))


def build_report(readiness_cutoff_path: Path = DEFAULT_READINESS_CUTOFF_PATH) -> dict[str, Any]:
    cutoff = load_json(readiness_cutoff_path)
    blockers = cutoff_blockers(cutoff)
    status = "ready_for_live_preflight_runner_design_gate" if not blockers else "blocked"
    allowed_next_step = "production_rebuild_live_preflight_runner_design_gate" if status != "blocked" else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_design",
        "scope": "design a minimal future live preflight runner contract without executing it",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "readiness_cutoff": {
                "path": str(readiness_cutoff_path),
                "present": readiness_cutoff_path.exists(),
                "version": cutoff.get("version"),
                "schema_kind": cutoff.get("schema_kind"),
                "status": as_dict(cutoff.get("summary")).get("status"),
                "allowed_next_step": as_dict(cutoff.get("summary")).get("allowed_next_step"),
            }
        },
        "guardrails": GUARDRAILS,
        "future_runner_contract": {
            "runner_created": False,
            "runner_executed": False,
            "future_inputs": FUTURE_INPUTS,
            "preflight_checks": PREFLIGHT_CHECKS,
            "output_fields": OUTPUT_FIELDS,
            "blocking_conditions": BLOCKING_CONDITIONS,
            "must_run_read_only_before_any_write": True,
            "must_require_formal_authorization_before_execution": True,
            "must_fail_closed_on_unknown_status": True,
        },
        "scaffold_cutoff_policy": {
            "continue_input_or_importer_scaffold_chain": False,
            "reason": "v0.4.14.14 already cut off input/importer scaffold expansion; this design keeps the next step focused on live preflight runner quality.",
        },
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "blockers": blockers,
            "runner_created": False,
            "runner_executed": False,
            "live_preflight_run_allowed": False,
            "production_rebuild_allowed": False,
            "qdrant_write_allowed": False,
            "authorization_granted": False,
            "full_eval": "not_run",
            "future_input_count": len(FUTURE_INPUTS),
            "preflight_check_count": len(PREFLIGHT_CHECKS),
            "blocking_condition_count": len(BLOCKING_CONDITIONS),
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
    contract = as_dict(report.get("future_runner_contract"))
    lines = [
        "# v0.4.14.15 Production Rebuild Live Preflight Runner Design",
        "",
        "本版本只设计未来 live preflight runner 的最小契约，不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- future inputs: `{summary.get('future_input_count')}`",
        f"- preflight checks: `{summary.get('preflight_check_count')}`",
        f"- blocking conditions: `{summary.get('blocking_condition_count')}`",
        f"- 是否允许现在运行 live preflight: `{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许现在 production rebuild: `{summary.get('production_rebuild_allowed')}`",
        "",
        "## 未来检查项",
        "",
    ]
    for check in contract.get("preflight_checks", []):
        lines.append(f"- `{check}`")
    lines.extend([
        "",
        "## 阻断条件",
        "",
    ])
    for condition in contract.get("blocking_conditions", []):
        lines.append(f"- `{condition}`")
    lines.extend([
        "",
        "结论：本版本把下一步压缩为 live preflight runner design gate；仍不开放 input/importer scaffold 扩张，也不代表已经允许生产执行。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.15 production rebuild live preflight runner design.")
    parser.add_argument("--readiness-cutoff", type=Path, default=DEFAULT_READINESS_CUTOFF_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.readiness_cutoff)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild live preflight runner design: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
