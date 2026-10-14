"""Check the v0.4.14.16 production rebuild live preflight runner design gate.

The gate validates only the saved v0.4.14.15 design report. It does not create
a runner, run live preflight, access Qdrant, create or accept authorization,
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


VERSION = "0.4.14.16"

DEFAULT_DESIGN_PATH = legacy_report_path("production_rebuild_live_preflight_runner_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_live_preflight_runner_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md")

REQUIRED_FUTURE_INPUT_FIELDS = {
    "authorization_record_reference",
    "target_collection",
    "backup_or_snapshot_reference",
    "source_lineage_reference",
    "expected_id_drift_acknowledgement",
    "maintenance_window",
}

REQUIRED_PREFLIGHT_CHECKS = {
    "authorization_record_present_and_accepted",
    "target_collection_matches_authorization",
    "qdrant_endpoint_reachable_read_only",
    "backup_or_snapshot_reference_verified",
    "source_patch_lineage_matches_expected_version",
    "expected_id_drift_acknowledged",
    "maintenance_window_active",
    "post_rebuild_validation_plan_present",
}

REQUIRED_OUTPUT_FIELDS = {
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
}

REQUIRED_BLOCKING_CONDITIONS = {
    "authorization_record_missing_or_not_accepted",
    "target_collection_missing_or_mismatch",
    "qdrant_read_only_reachability_failed",
    "backup_or_snapshot_reference_unverified",
    "source_lineage_mismatch",
    "expected_id_drift_not_acknowledged",
    "maintenance_window_inactive",
    "post_rebuild_validation_plan_missing",
}

REQUIRED_GUARDRAILS = {
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


def check_row(check_id: str, passed: bool, details: str) -> dict[str, Any]:
    return {"check_id": check_id, "passed": passed, "details": details}


def list_field_set(rows: list[Any], field: str) -> set[str]:
    values: set[str] = set()
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get(field), str):
            values.add(row[field])
    return values


def build_report(design_path: Path = DEFAULT_DESIGN_PATH) -> dict[str, Any]:
    design = load_json(design_path)
    summary = as_dict(design.get("summary"))
    guardrails = as_dict(design.get("guardrails"))
    contract = as_dict(design.get("future_runner_contract"))
    cutoff_policy = as_dict(design.get("scaffold_cutoff_policy"))
    inputs = as_dict(design.get("inputs"))
    cutoff_input = as_dict(inputs.get("readiness_cutoff"))

    future_inputs = as_list(contract.get("future_inputs"))
    preflight_checks = set(as_list(contract.get("preflight_checks")))
    output_fields = set(as_list(contract.get("output_fields")))
    blocking_conditions = set(as_list(contract.get("blocking_conditions")))

    checks = [
        check_row("design_present", bool(design), "Design report must exist and be a JSON object."),
        check_row("design_version", design.get("version") == "0.4.14.15", "Design report must be v0.4.14.15."),
        check_row(
            "design_schema",
            design.get("schema_kind") == "production_rebuild_live_preflight_runner_design",
            "Design schema must match.",
        ),
        check_row(
            "design_status",
            summary.get("status") == "ready_for_live_preflight_runner_design_gate",
            "Design must be ready for this gate.",
        ),
        check_row(
            "design_next_step",
            summary.get("allowed_next_step") == "production_rebuild_live_preflight_runner_design_gate",
            "Design must open only this gate.",
        ),
        check_row(
            "lineage_cutoff_only",
            set(inputs) == {"readiness_cutoff"}
            and cutoff_input.get("version") == "0.4.14.14"
            and cutoff_input.get("schema_kind") == "production_rebuild_readiness_cutoff"
            and cutoff_input.get("status") == "ready_for_live_preflight_runner_design_cutoff",
            "Gate must validate a design sourced only from the v0.4.14.14 cutoff.",
        ),
        check_row(
            "summary_permissions_locked",
            summary.get("runner_created") is False
            and summary.get("runner_executed") is False
            and summary.get("live_preflight_run_allowed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("production_rebuild_allowed") is False
            and summary.get("authorization_granted") is False
            and summary.get("full_eval") == "not_run",
            "Design summary must not grant runner execution, Qdrant write, production rebuild, authorization, or full eval.",
        ),
        check_row(
            "guardrails_locked",
            set(guardrails) == set(REQUIRED_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must remain design-only and block runtime, Qdrant, rebuild, RAG/LLM, eval, fixture, and scaffold expansion.",
        ),
        check_row(
            "future_inputs_contract",
            list_field_set(future_inputs, "field") == REQUIRED_FUTURE_INPUT_FIELDS
            and all(as_dict(row).get("required") is True for row in future_inputs),
            "Future inputs must exactly match the required field set and remain required.",
        ),
        check_row(
            "preflight_checks_contract",
            preflight_checks == REQUIRED_PREFLIGHT_CHECKS,
            "Preflight checks must exactly match the required design contract.",
        ),
        check_row(
            "output_fields_contract",
            output_fields == REQUIRED_OUTPUT_FIELDS,
            "Output fields must exactly match the required design contract.",
        ),
        check_row(
            "blocking_conditions_contract",
            blocking_conditions == REQUIRED_BLOCKING_CONDITIONS,
            "Blocking conditions must exactly match the required design contract.",
        ),
        check_row(
            "fail_closed_contract",
            contract.get("runner_created") is False
            and contract.get("runner_executed") is False
            and contract.get("must_run_read_only_before_any_write") is True
            and contract.get("must_require_formal_authorization_before_execution") is True
            and contract.get("must_fail_closed_on_unknown_status") is True,
            "Future runner contract must remain non-executed, read-only-before-write, authorization-gated, and fail-closed.",
        ),
        check_row(
            "scaffold_cutoff_policy",
            cutoff_policy.get("continue_input_or_importer_scaffold_chain") is False,
            "Design must not reopen input/importer scaffold expansion.",
        ),
        check_row(
            "forbidden_output_keys_absent",
            forbidden_output_keys(design) == [],
            "Design report must not contain execution-like forbidden output keys.",
        ),
    ]

    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    allowed_next_step = "production_rebuild_live_preflight_runner_minimal_implementation_design" if status == "passed" else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_design_gate",
        "scope": "gate the live preflight runner design without creating or executing a runner",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "design": {
                "path": str(design_path),
                "present": design_path.exists(),
                "version": design.get("version"),
                "schema_kind": design.get("schema_kind"),
                "status": summary.get("status"),
                "allowed_next_step": summary.get("allowed_next_step"),
            }
        },
        "checks": checks,
        "guardrails": {
            "gate_only": True,
            "saved_reports_only": True,
            **REQUIRED_GUARDRAILS,
        },
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "check_count": len(checks),
            "failure_count": len(failed),
            "failed_checks": [row["check_id"] for row in failed],
            "runner_created": False,
            "runner_executed": False,
            "live_preflight_run_allowed": False,
            "production_rebuild_allowed": False,
            "qdrant_write_allowed": False,
            "authorization_granted": False,
            "full_eval": "not_run",
        },
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.14.16 Production Rebuild Live Preflight Runner Design Gate",
        "",
        "本版本只 gate v0.4.14.15 live preflight runner design，不创建 runner，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failure_count')}`",
        f"- 是否允许现在运行 live preflight: `{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许现在 production rebuild: `{summary.get('production_rebuild_allowed')}`",
        "",
        "## 失败项",
        "",
    ]
    failed = summary.get("failed_checks") or []
    if failed:
        for check_id in failed:
            lines.append(f"- `{check_id}`")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "结论：design gate 通过后，只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design`；仍不直接创建 runner、运行 live preflight、写入 Qdrant 或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.16 live preflight runner design gate.")
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
        "Production rebuild live preflight runner design gate: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
