"""Build the v0.4.14.17 live preflight runner minimal implementation design.

This design reads only the v0.4.14.16 design gate report. It specifies the
future runner file boundary, CLI/function contract, read-only strategy, mock
test strategy, and fail-closed behavior without creating a runner, running live
preflight, accessing Qdrant, creating or accepting authorization, rebuilding
collections, calling RAG/embedding/LLM, running full eval, or mutating runtime
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


VERSION = "0.4.14.17"

DEFAULT_DESIGN_GATE_PATH = legacy_report_path("production_rebuild_live_preflight_runner_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_live_preflight_runner_minimal_implementation_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md"
)

DESIGN_GATE_EXPECTATION = {
    "version": "0.4.14.16",
    "schema_kind": "production_rebuild_live_preflight_runner_design_gate",
    "status": "passed",
    "allowed_next_step": "production_rebuild_live_preflight_runner_minimal_implementation_design",
}

DESIGN_GATE_BOUNDARIES = {
    "runner_created": False,
    "runner_executed": False,
    "live_preflight_run_allowed": False,
    "production_rebuild_allowed": False,
    "qdrant_write_allowed": False,
    "authorization_granted": False,
    "full_eval": "not_run",
}

GUARDRAILS = {
    "implementation_design_only": True,
    "saved_reports_only": True,
    "design_gate_only": True,
    "runner_file_created": False,
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

FUTURE_FILES = [
    {
        "path": "tools/run_production_rebuild_live_preflight.py",
        "purpose": "future read-only live preflight runner entrypoint",
        "created_now": False,
    },
    {
        "path": "tests/test_production_rebuild_live_preflight_runner.py",
        "purpose": "future mock-only tests for fail-closed runner behavior",
        "created_now": False,
    },
    {
        "path": "tests/production_rebuild_live_preflight_report.json",
        "purpose": "future runner output report, generated only after explicit implementation and run authorization",
        "created_now": False,
    },
]

CLI_CONTRACT = {
    "entrypoint": "tools/run_production_rebuild_live_preflight.py",
    "required_args": [
        "--authorization-record",
        "--target-collection",
        "--backup-or-snapshot-reference",
        "--source-lineage-reference",
        "--output",
    ],
    "optional_args": [
        "--read-timeout-seconds",
        "--maintenance-window",
        "--strict-read-only",
    ],
    "forbidden_args": [
        "--write",
        "--rebuild",
        "--switch-collection",
        "--force",
    ],
    "created_now": False,
}

FUNCTION_CONTRACT = {
    "entry_function": "build_live_preflight_report",
    "inputs": [
        "authorization_record",
        "target_collection",
        "backup_or_snapshot_reference",
        "source_lineage_reference",
        "qdrant_readonly_probe",
        "clock",
    ],
    "returns": "dict[str, Any] shaped like the future preflight output contract",
    "side_effect_policy": "no writes, no collection mutation, no rebuild, no RAG/LLM calls",
    "created_now": False,
}

READ_ONLY_STRATEGY = [
    "require an injected qdrant_readonly_probe abstraction instead of importing qdrant_client in core logic",
    "perform only collection existence and metadata reachability checks in the future runner",
    "never call upsert, delete, recreate_collection, update_collection, or alias/switch APIs",
    "mark qdrant_write_allowed=false and production_rebuild_allowed=false in every preflight output",
]

MOCK_TEST_STRATEGY = [
    "test accepted authorization plus successful read-only probe yields preflight_status=passed without write permission",
    "test missing authorization fails closed",
    "test target collection mismatch fails closed",
    "test read-only probe error fails closed",
    "test backup or snapshot reference missing fails closed",
    "test forbidden write-like method exposure fails closed",
]

FAIL_CLOSED_RULES = [
    "unknown authorization status blocks",
    "missing or mismatched target collection blocks",
    "missing backup or snapshot reference blocks",
    "read-only probe exception blocks",
    "maintenance window mismatch blocks",
    "any unexpected field or permission drift blocks",
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


def design_gate_blockers(gate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    summary = as_dict(gate.get("summary"))
    if not gate:
        blockers.append("design_gate_missing")
        return blockers
    if gate.get("version") != DESIGN_GATE_EXPECTATION["version"]:
        blockers.append("design_gate_version_mismatch")
    if gate.get("schema_kind") != DESIGN_GATE_EXPECTATION["schema_kind"]:
        blockers.append("design_gate_schema_mismatch")
    if summary.get("status") != DESIGN_GATE_EXPECTATION["status"]:
        blockers.append("design_gate_status_mismatch")
    if summary.get("allowed_next_step") != DESIGN_GATE_EXPECTATION["allowed_next_step"]:
        blockers.append("design_gate_next_step_mismatch")
    if summary.get("failure_count") != 0 or summary.get("failed_checks") != []:
        blockers.append("design_gate_failure_drift")
    for field, expected in DESIGN_GATE_BOUNDARIES.items():
        if summary.get(field) != expected:
            blockers.append(f"design_gate_{field}_mismatch")
    if forbidden_output_keys(gate):
        blockers.append("design_gate_forbidden_output_key_present")
    return sorted(set(blockers))


def build_report(design_gate_path: Path = DEFAULT_DESIGN_GATE_PATH) -> dict[str, Any]:
    gate = load_json(design_gate_path)
    blockers = design_gate_blockers(gate)
    status = "ready_for_minimal_implementation_design_gate" if not blockers else "blocked"
    allowed_next_step = "production_rebuild_live_preflight_runner_minimal_implementation_design_gate" if status != "blocked" else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_design",
        "scope": "design the future live preflight runner implementation boundary without creating or running it",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "design_gate": {
                "path": str(design_gate_path),
                "present": design_gate_path.exists(),
                "version": gate.get("version"),
                "schema_kind": gate.get("schema_kind"),
                "status": as_dict(gate.get("summary")).get("status"),
                "allowed_next_step": as_dict(gate.get("summary")).get("allowed_next_step"),
            }
        },
        "guardrails": GUARDRAILS,
        "implementation_design": {
            "future_files": FUTURE_FILES,
            "cli_contract": CLI_CONTRACT,
            "function_contract": FUNCTION_CONTRACT,
            "read_only_strategy": READ_ONLY_STRATEGY,
            "mock_test_strategy": MOCK_TEST_STRATEGY,
            "fail_closed_rules": FAIL_CLOSED_RULES,
        },
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "blockers": blockers,
            "future_file_count": len(FUTURE_FILES),
            "mock_test_count": len(MOCK_TEST_STRATEGY),
            "fail_closed_rule_count": len(FAIL_CLOSED_RULES),
            "runner_file_created": False,
            "runner_created": False,
            "runner_executed": False,
            "live_preflight_run_allowed": False,
            "production_rebuild_allowed": False,
            "qdrant_access_allowed": False,
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
    design = as_dict(report.get("implementation_design"))
    lines = [
        "# v0.4.14.17 Production Rebuild Live Preflight Runner Minimal Implementation Design",
        "",
        "本版本只设计未来 live preflight runner 的最小实现边界，不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- future files: `{summary.get('future_file_count')}`",
        f"- mock tests: `{summary.get('mock_test_count')}`",
        f"- fail-closed rules: `{summary.get('fail_closed_rule_count')}`",
        f"- 是否创建 runner 文件: `{summary.get('runner_file_created')}`",
        f"- 是否允许现在运行 live preflight: `{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        "",
        "## 未来文件边界",
        "",
    ]
    for item in design.get("future_files", []):
        row = as_dict(item)
        lines.append(f"- `{row.get('path')}`: {row.get('purpose')}；created_now=`{row.get('created_now')}`")
    lines.extend([
        "",
        "结论：本版本只开放 `production_rebuild_live_preflight_runner_minimal_implementation_design_gate`；仍不创建 runner、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.17 live preflight runner minimal implementation design.")
    parser.add_argument("--design-gate", type=Path, default=DEFAULT_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild live preflight runner minimal implementation design: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
