"""Build the v0.4.13.13 production rebuild authorization design.

The design reads only saved v0.4.13.11 and v0.4.13.12 reports. It defines the
human authorization envelope required before any future Qdrant collection
rebuild. It does not access Qdrant, rebuild a collection, call RAG, call
embeddings or LLMs, run full eval, or mutate runtime/eval artifacts.
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


VERSION = "0.4.13.13"

DEFAULT_RUNNER_REPORT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json")
DEFAULT_RUNNER_GATE_REPORT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("rebuild_authorization_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/rebuild_authorization_design_v0.4.13.13.md")

GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "authorization_granted": False,
    "human_authorization_record_created": False,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "ingestion_source_mutation": "disallowed",
    "retrieval_logic_change_allowed": False,
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

REQUIRED_CONFIRMATION_FIELDS = [
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

ABORT_CONDITIONS = [
    "missing_backup_or_snapshot",
    "target_collection_unclear_or_unexpected",
    "source_patch_or_dry_run_lineage_stale",
    "rebuild_scope_unclear",
    "rollback_plan_missing_or_untested",
    "operator_approval_missing",
    "expected_id_drift_not_acknowledged",
    "v0.4.13.12_gate_not_passed",
    "post_rebuild_validation_plan_missing",
]

POST_REBUILD_VALIDATION_PLAN = {
    "metadata_boundary_check": "verify chunk_index and chunk_count are present in rebuilt payloads",
    "id_drift_accounting": "confirm chunk_id and qdrant_point_id drift is expected and documented",
    "limited_smoke": "run only separately authorized smoke checks after rebuild",
    "rollback_readiness": "verify rollback collection or snapshot remains available until validation passes",
    "full_eval_policy": "not part of this design; requires separate authorization if needed",
}

OUTPUT_CONTRACT = {
    "summary_fields": [
        "status",
        "allowed_next_step",
        "human_authorization_required",
        "authorization_granted",
        "qdrant_write_allowed",
        "rebuild_allowed",
        "full_eval",
        "blockers",
    ],
    "future_authorization_record_fields": REQUIRED_CONFIRMATION_FIELDS,
    "blocking_conditions": ABORT_CONDITIONS,
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


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": as_dict(data.get("summary")).get("status"),
        "allowed_next_step": as_dict(data.get("summary")).get("allowed_next_step"),
    }


def runner_gate_blockers(gate_report: dict[str, Any]) -> list[str]:
    summary = as_dict(gate_report.get("summary"))
    blockers: list[str] = []
    if gate_report.get("version") != "0.4.13.12":
        blockers.append("runner_gate_version_mismatch")
    if gate_report.get("schema_kind") != "ingestion_metadata_patch_post_patch_rebuild_dry_run_gate":
        blockers.append("runner_gate_schema_mismatch")
    if summary.get("status") != "passed":
        blockers.append("runner_gate_not_passed")
    if summary.get("failed_check_count") != 0:
        blockers.append("runner_gate_failed_checks_present")
    if summary.get("allowed_next_step") != "rebuild_authorization_design":
        blockers.append("runner_gate_next_step_mismatch")
    if summary.get("runner_rerun_allowed") is not False:
        blockers.append("runner_gate_allows_runner_rerun")
    if summary.get("qdrant_write_allowed") is not False:
        blockers.append("runner_gate_allows_qdrant_write")
    if summary.get("rebuild_allowed") is not False:
        blockers.append("runner_gate_allows_rebuild")
    if summary.get("rag_query_allowed") is not False:
        blockers.append("runner_gate_allows_rag_query")
    if summary.get("embedding_or_llm_allowed") is not False:
        blockers.append("runner_gate_allows_embedding_or_llm")
    if summary.get("full_eval") != "not_run":
        blockers.append("runner_gate_full_eval_drift")
    return blockers


def runner_report_blockers(runner_report: dict[str, Any]) -> list[str]:
    summary = as_dict(runner_report.get("summary"))
    blockers: list[str] = []
    if runner_report.get("version") != "0.4.13.11":
        blockers.append("runner_report_version_mismatch")
    if runner_report.get("schema_kind") != "ingestion_metadata_patch_post_patch_rebuild_dry_run":
        blockers.append("runner_report_schema_mismatch")
    if summary.get("status") != "passed":
        blockers.append("runner_report_not_passed")
    if summary.get("sample_count") != 3:
        blockers.append("runner_sample_count_mismatch")
    if summary.get("row_count") != 9:
        blockers.append("runner_row_count_mismatch")
    if summary.get("metadata_presence_rows") != 9:
        blockers.append("runner_metadata_presence_mismatch")
    if summary.get("expected_id_drift_rows") != 9:
        blockers.append("runner_expected_id_drift_mismatch")
    if summary.get("forbidden_drift_count") != 0:
        blockers.append("runner_forbidden_drift_present")
    if summary.get("blocking_condition_count") != 0:
        blockers.append("runner_blocking_conditions_present")
    if summary.get("qdrant_write_allowed") is not False:
        blockers.append("runner_allows_qdrant_write")
    if summary.get("rebuild_allowed") is not False:
        blockers.append("runner_allows_rebuild")
    if summary.get("full_eval") != "not_run":
        blockers.append("runner_full_eval_drift")
    return blockers


def build_report(
    runner_report_path: Path = DEFAULT_RUNNER_REPORT_PATH,
    runner_gate_report_path: Path = DEFAULT_RUNNER_GATE_REPORT_PATH,
) -> dict[str, Any]:
    runner_report = load_json(runner_report_path)
    runner_gate_report = load_json(runner_gate_report_path)
    blockers = runner_gate_blockers(runner_gate_report) + runner_report_blockers(runner_report)
    status = "ready_for_rebuild_authorization_design_gate" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "rebuild_authorization_design",
        "scope": "production rebuild authorization design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "post_patch_rebuild_dry_run_runner": source_meta(runner_report_path, runner_report),
            "post_patch_rebuild_dry_run_runner_gate": source_meta(runner_gate_report_path, runner_gate_report),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": "rebuild_authorization_design_gate" if status != "blocked" else "blocked",
            "human_authorization_required": True,
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "rag_query_allowed": False,
            "embedding_or_llm_allowed": False,
            "full_eval": "not_run",
            "blockers": blockers,
        },
        "authorization_design": {
            "purpose": "separate production rebuild authorization from technical dry-run success",
            "future_authorization_record_status": "not_created_in_this_version",
            "required_confirmation_fields": REQUIRED_CONFIRMATION_FIELDS,
            "authorization_sections": {
                "target_collection": [
                    "collection_name",
                    "environment",
                    "endpoint_class",
                    "operator_visible_target_confirmation",
                ],
                "rebuild_scope": [
                    "full_collection_or_isolated_replacement",
                    "expected_law_corpus",
                    "excluded_data",
                    "source_manifest_or_equivalent_reference",
                ],
                "source_version": [
                    "code_version",
                    "v0.4.13.8_source_patch_report",
                    "v0.4.13.11_dry_run_report",
                    "v0.4.13.12_runner_gate_report",
                ],
                "expected_id_drift_acknowledgement": [
                    "chunk_id_drift_expected",
                    "qdrant_point_id_drift_expected",
                    "reason_chunk_index_chunk_count_changed_identity",
                ],
                "backup_plan": [
                    "snapshot_or_export_location",
                    "rollback_collection_name",
                    "verification_owner",
                ],
                "rollback_plan": [
                    "restore_or_swap_steps",
                    "stop_conditions",
                    "operator_responsibility",
                ],
                "operator_approval": [
                    "approver_name",
                    "approved_at",
                    "explicit_yes_no_authorization",
                ],
                "maintenance_window": [
                    "start_time",
                    "end_time",
                    "communication_owner",
                ],
                "post_rebuild_validation_plan": list(POST_REBUILD_VALIDATION_PLAN),
                "abort_conditions_acknowledgement": ABORT_CONDITIONS,
            },
            "post_rebuild_validation_plan": POST_REBUILD_VALIDATION_PLAN,
            "abort_conditions": ABORT_CONDITIONS,
        },
        "output_contract": OUTPUT_CONTRACT,
        "handoff": {
            "next_allowed_step": "gate this rebuild authorization design" if status != "blocked" else "resolve authorization design blockers",
            "not_allowed_yet": [
                "create or accept human authorization record",
                "write Qdrant",
                "rebuild collection",
                "run rebuild preflight against a live collection",
                "call rag_query",
                "call embedding or LLM services",
                "run full eval as a substitute for authorization",
                "modify ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("authorization_design"))
    lines = [
        "# v0.4.13.13 Rebuild Authorization Design",
        "",
        "本报告只设计未来生产 rebuild 的人工授权 envelope。它不创建授权记录，不访问 Qdrant，不写 collection，不 rebuild，不调用 RAG/embedding/LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否需要人工授权: `{summary.get('human_authorization_required')}`",
        f"- 是否已经授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        f"- full eval: `{summary.get('full_eval')}`",
        "",
        "## 必填授权字段",
        "",
    ]
    for field in design.get("required_confirmation_fields", []):
        lines.append(f"- `{field}`")
    lines.extend(["", "## 终止条件", ""])
    for condition in design.get("abort_conditions", []):
        lines.append(f"- `{condition}`")
    lines.extend(["", "## 边界", ""])
    for item in as_dict(report.get("handoff")).get("not_allowed_yet", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "通过本设计只允许进入 `rebuild_authorization_design_gate`，仍不代表已经允许生产 Qdrant rebuild。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.13 rebuild authorization design.")
    parser.add_argument("--runner-report", type=Path, default=DEFAULT_RUNNER_REPORT_PATH)
    parser.add_argument("--runner-gate-report", type=Path, default=DEFAULT_RUNNER_GATE_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.runner_report, args.runner_gate_report)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Rebuild authorization design: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
