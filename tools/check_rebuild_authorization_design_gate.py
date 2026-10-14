"""Check the v0.4.13.14 rebuild authorization design gate.

The gate validates only the saved v0.4.13.13 design report. It does not create
authorization records, access Qdrant, rebuild collections, call RAG, call
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


VERSION = "0.4.13.14"

DEFAULT_DESIGN_PATH = legacy_report_path("rebuild_authorization_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("rebuild_authorization_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/rebuild_authorization_design_gate_v0.4.13.14.md")

REQUIRED_GUARDRAILS = {
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

REQUIRED_FIELDS = {
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

REQUIRED_ABORT_CONDITIONS = {
    "missing_backup_or_snapshot",
    "target_collection_unclear_or_unexpected",
    "source_patch_or_dry_run_lineage_stale",
    "rebuild_scope_unclear",
    "rollback_plan_missing_or_untested",
    "operator_approval_missing",
    "expected_id_drift_not_acknowledged",
    "v0.4.13.12_gate_not_passed",
    "post_rebuild_validation_plan_missing",
}

REQUIRED_HANDOFF_BLOCKS = {
    "create or accept human authorization record",
    "write Qdrant",
    "rebuild collection",
    "run rebuild preflight against a live collection",
    "call rag_query",
    "call embedding or LLM services",
    "run full eval as a substitute for authorization",
    "modify ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases",
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
    inputs = as_dict(design_report.get("inputs"))
    runner_input = as_dict(inputs.get("post_patch_rebuild_dry_run_runner"))
    runner_gate_input = as_dict(inputs.get("post_patch_rebuild_dry_run_runner_gate"))
    summary = as_dict(design_report.get("summary"))
    guardrails = as_dict(design_report.get("guardrails"))
    design = as_dict(design_report.get("authorization_design"))
    sections = as_dict(design.get("authorization_sections"))
    output_contract = as_dict(design_report.get("output_contract"))
    handoff = as_dict(design_report.get("handoff"))

    checks = [
        check_row("design_version", design_report.get("version") == "0.4.13.13", "Design report must be v0.4.13.13."),
        check_row("design_schema", design_report.get("schema_kind") == "rebuild_authorization_design", "Design schema must match."),
        check_row(
            "lineage",
            runner_input.get("version") == "0.4.13.11"
            and runner_input.get("schema_kind") == "ingestion_metadata_patch_post_patch_rebuild_dry_run"
            and runner_input.get("status") == "passed"
            and runner_gate_input.get("version") == "0.4.13.12"
            and runner_gate_input.get("schema_kind") == "ingestion_metadata_patch_post_patch_rebuild_dry_run_gate"
            and runner_gate_input.get("status") == "passed"
            and runner_gate_input.get("allowed_next_step") == "rebuild_authorization_design",
            "Design lineage must preserve the passed v0.4.13.11 runner and v0.4.13.12 runner gate reports.",
        ),
        check_row(
            "design_status",
            summary.get("status") == "ready_for_rebuild_authorization_design_gate",
            "Design must be ready for this gate.",
        ),
        check_row(
            "design_next_step",
            summary.get("allowed_next_step") == "rebuild_authorization_design_gate",
            "Design must open only this gate.",
        ),
        check_row(
            "no_authorization_or_rebuild",
            summary.get("human_authorization_required") is True
            and summary.get("authorization_granted") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("rebuild_allowed") is False
            and summary.get("rag_query_allowed") is False
            and summary.get("embedding_or_llm_allowed") is False
            and summary.get("full_eval") == "not_run"
            and summary.get("blockers") == [],
            "Design must require future human authorization while keeping authorization, Qdrant, rebuild, RAG, LLM, and full eval blocked.",
        ),
        check_row(
            "guardrails_locked",
            all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must remain design-only and block all runtime/rebuild/eval mutations.",
        ),
        check_row(
            "required_fields",
            design.get("future_authorization_record_status") == "not_created_in_this_version"
            and REQUIRED_FIELDS.issubset(set(as_list(design.get("required_confirmation_fields")))),
            "Future authorization record must not be created in this version and must define all required confirmation fields.",
        ),
        check_row(
            "authorization_sections",
            REQUIRED_FIELDS.issubset(set(sections.keys()))
            and all(as_list(sections.get(field)) for field in REQUIRED_FIELDS),
            "Every required field must have a non-empty section definition.",
        ),
        check_row(
            "abort_conditions",
            REQUIRED_ABORT_CONDITIONS.issubset(set(as_list(design.get("abort_conditions")))),
            "Design must require the core abort conditions.",
        ),
        check_row(
            "output_contract",
            REQUIRED_FIELDS.issubset(set(as_list(output_contract.get("future_authorization_record_fields"))))
            and REQUIRED_ABORT_CONDITIONS.issubset(set(as_list(output_contract.get("blocking_conditions")))),
            "Output contract must preserve required future fields and blocking conditions.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("next_allowed_step") == "gate this rebuild authorization design"
            and REQUIRED_HANDOFF_BLOCKS.issubset(set(as_list(handoff.get("not_allowed_yet")))),
            "Handoff must keep authorization record creation, Qdrant write, rebuild, live preflight, RAG/LLM/full eval, and runtime/eval mutation blocked.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "rebuild_authorization_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "rebuild_authorization_design": {
                "path": str(design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": summary.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "human_rebuild_authorization_worksheet" if status == "passed" else "blocked",
            "human_authorization_record_created": False,
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
        "# v0.4.13.14 Rebuild Authorization Design Gate",
        "",
        "本门禁只检查 v0.4.13.13 授权设计报告。它不创建人工授权记录，不访问 Qdrant，不 rebuild，不调用 RAG/embedding/LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已经创建人工授权记录: `{summary.get('human_authorization_record_created')}`",
        f"- 是否已经授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 检查项",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    lines.extend(
        [
            "",
            "通过本 gate 只允许进入 `human_rebuild_authorization_worksheet`，仍不代表已经允许生产 Qdrant rebuild。",
        ]
    )
    return "\n".join(lines) + "\n"

    lines = [
        "# v0.4.13.14 Rebuild Authorization Design Gate",
        "",
        "本门禁只检查 v0.4.13.13 授权设计报告。它不创建人工授权记录，不访问 Qdrant，不 rebuild，不调用 RAG/embedding/LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已经创建人工授权记录: `{summary.get('human_authorization_record_created')}`",
        f"- 是否已经授权: `{summary.get('authorization_granted')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 检查项",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    lines.extend(
        [
            "",
            "通过本 gate 只允许进入 `human_rebuild_authorization_worksheet`，仍不代表已经允许生产 Qdrant rebuild。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.14 rebuild authorization design gate.")
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
    print(f"Rebuild authorization design gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
