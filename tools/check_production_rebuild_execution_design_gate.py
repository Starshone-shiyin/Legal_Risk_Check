"""Check the v0.4.14.1 production rebuild execution design gate.

The gate validates only the saved v0.4.14.0 execution design report. It does
not create or accept human authorization, run live preflight, access Qdrant,
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


VERSION = "0.4.14.1"

DEFAULT_DESIGN_PATH = legacy_report_path("production_rebuild_execution_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_execution_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/production_rebuild_execution_design_gate_v0.4.14.1.md")

REQUIRED_AUTHORIZATION_FIELDS = {
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
}

REQUIRED_PHASES = [
    "preflight_validation",
    "backup_or_rollback_verification",
    "target_collection_lock_confirmation",
    "rebuild_execution",
    "post_rebuild_metadata_validation",
    "post_rebuild_smoke_validation",
    "rollback_or_acceptance_decision",
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

REQUIRED_GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "closeout_report_only": True,
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
}

REQUIRED_CLOSEOUT_INPUT = {
    "version": "0.4.13.18",
    "schema_kind": "ingestion_metadata_rebuild_planning_series_closeout",
    "status": "closed_for_execution_design_handoff",
    "allowed_next_step": "production_rebuild_execution_design",
}

REQUIRED_HANDOFF_BLOCKS = {
    "create or accept human authorization record",
    "run live preflight",
    "write Qdrant",
    "rebuild collection",
    "switch collection",
    "call rag_query",
    "call embedding or LLM services",
    "run full eval as a substitute for authorization",
    "modify runtime, ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases",
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


def build_report(design_path: Path = DEFAULT_DESIGN_PATH) -> dict[str, Any]:
    design_report = load_json(design_path)
    summary = as_dict(design_report.get("summary"))
    guardrails = as_dict(design_report.get("guardrails"))
    execution_design = as_dict(design_report.get("execution_design"))
    records = as_dict(execution_design.get("record_contracts"))
    output_contract = as_dict(design_report.get("output_contract"))
    handoff = as_dict(design_report.get("handoff"))
    design_inputs = as_dict(design_report.get("inputs"))
    planning_closeout = as_dict(design_inputs.get("planning_closeout"))

    preflight_record = as_dict(records.get("preflight_record"))
    rebuild_record = as_dict(records.get("rebuild_execution_record"))
    decision_record = as_dict(records.get("abort_or_acceptance_decision_record"))
    decision_policy = as_dict(execution_design.get("decision_policy"))

    checks = [
        check_row("design_version", design_report.get("version") == "0.4.14.0", "Design report must be v0.4.14.0."),
        check_row("design_schema", design_report.get("schema_kind") == "production_rebuild_execution_design", "Design schema must match."),
        check_row(
            "design_status",
            summary.get("status") == "ready_for_production_rebuild_execution_design_gate",
            "Design must be ready for this gate.",
        ),
        check_row(
            "design_next_step",
            summary.get("allowed_next_step") == "production_rebuild_execution_design_gate",
            "Design must open only this gate.",
        ),
        check_row(
            "no_authorization_or_execution",
            summary.get("authorization_record_required") is True
            and summary.get("authorization_record_created") is False
            and summary.get("authorization_granted") is False
            and summary.get("live_preflight_run") is False
            and summary.get("production_rebuild_executed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("rebuild_allowed") is False
            and summary.get("full_eval") == "not_run"
            and summary.get("blockers") == [],
            "Design must require future authorization while keeping execution, Qdrant, rebuild, and full eval blocked.",
        ),
        check_row(
            "closeout_lineage",
            set(design_inputs) == {"planning_closeout"}
            and execution_design.get("source_of_truth") == "v0.4.13.18 planning closeout report"
            and all(planning_closeout.get(key) == expected for key, expected in REQUIRED_CLOSEOUT_INPUT.items()),
            "Design must keep v0.4.13.18 planning closeout as the only source-of-truth input.",
        ),
        check_row(
            "guardrails_locked",
            set(guardrails) == set(REQUIRED_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must remain design-only and block authorization acceptance, live preflight, Qdrant, rebuild, runtime, prompt/rerank/rule, eval, and fixture mutation.",
        ),
        check_row(
            "authorization_fields",
            set(as_list(execution_design.get("required_authorization_fields"))) == REQUIRED_AUTHORIZATION_FIELDS,
            "Design must inherit exactly the required human authorization fields.",
        ),
        check_row(
            "phase_order",
            execution_design.get("phase_order") == REQUIRED_PHASES,
            "Execution phase order must match the execution design contract.",
        ),
        check_row(
            "record_contracts_present",
            list(records.keys()) == REQUIRED_RECORD_ORDER,
            "Design must define exactly the required record contracts in the expected order.",
        ),
        check_row(
            "preflight_record_contract",
            set(as_list(preflight_record.get("checks"))) == REQUIRED_PREFLIGHT_CHECKS
            and preflight_record.get("must_pass_before") == "backup_or_rollback_verification",
            "Preflight record must define exactly all checks and must pass before backup/rollback verification.",
        ),
        check_row(
            "rebuild_record_not_created",
            rebuild_record.get("must_not_be_created_in_this_version") is True,
            "Rebuild execution record must not be created in this design gate series.",
        ),
        check_row(
            "abort_or_acceptance_policy",
            decision_record.get("automatic_acceptance_allowed") is False
            and decision_record.get("main_flow_change_authorized_by_this_record") is False
            and decision_policy.get("all_checks_pass") == "requires_explicit_human_acceptance_record"
            and decision_policy.get("main_flow_change") == "not_authorized_by_this_design",
            "Decision policy must require explicit human acceptance and must not authorize main-flow changes.",
        ),
        check_row(
            "abort_conditions",
            set(as_list(execution_design.get("blocking_conditions"))) == REQUIRED_ABORT_CONDITIONS,
            "Design must preserve exactly all required abort conditions.",
        ),
        check_row(
            "output_contract",
            as_list(output_contract.get("required_records")) == REQUIRED_RECORD_ORDER
            and "authorization_granted" in set(as_list(output_contract.get("summary_fields")))
            and "production_rebuild_executed" in set(as_list(output_contract.get("summary_fields"))),
            "Output contract must include exactly all records and key non-execution summary fields.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("next_allowed_step") == "gate this production rebuild execution design"
            and REQUIRED_HANDOFF_BLOCKS.issubset(set(as_list(handoff.get("not_allowed_yet")))),
            "Handoff must keep authorization acceptance, live preflight, Qdrant write, rebuild, collection switch, RAG/LLM/full eval, and runtime/eval mutation blocked.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_execution_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "production_rebuild_execution_design": {
                "path": str(design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": summary.get("status"),
            },
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "human_rebuild_authorization_record_scaffold" if status == "passed" else "blocked",
            "authorization_record_created": False,
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
        "# v0.4.14.1 Production Rebuild Execution Design Gate",
        "",
        "本 gate 只检查 v0.4.14.0 production rebuild execution design。它不创建或接受人工授权记录，不运行 live preflight，不访问或写入 Qdrant，不 rebuild collection。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已授权: `{summary.get('authorization_granted')}`",
        f"- 是否已运行 live preflight: `{summary.get('live_preflight_run')}`",
        f"- 是否已执行生产 rebuild: `{summary.get('production_rebuild_executed')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        "",
        "## 检查项",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    lines.extend([
        "",
        "通过本 gate 只允许进入 `human_rebuild_authorization_record_scaffold`，仍不代表已经允许 live preflight、Qdrant write 或生产 rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.1 production rebuild execution design gate.")
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.design)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild execution design gate: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
