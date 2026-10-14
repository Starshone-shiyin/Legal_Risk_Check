"""Build the v0.4.14.19 live preflight runner minimal scaffold design.

This design reads only the v0.4.14.18 implementation design gate report. It
specifies the future placeholder scaffold boundaries without creating runner
files, running live preflight, accessing Qdrant, creating or accepting
authorization, rebuilding collections, calling RAG/embedding/LLM, running full
eval, or mutating runtime and eval artifacts.
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


VERSION = "0.4.14.19"

DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md"
)

GATE_EXPECTATION = {
    "version": "0.4.14.18",
    "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_design_gate",
    "status": "passed",
    "allowed_next_step": "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design",
}

GATE_BOUNDARIES = {
    "runner_file_created": False,
    "runner_created": False,
    "runner_executed": False,
    "live_preflight_run_allowed": False,
    "production_rebuild_allowed": False,
    "qdrant_access_allowed": False,
    "qdrant_write_allowed": False,
    "authorization_granted": False,
    "full_eval": "not_run",
}

GUARDRAILS = {
    "scaffold_design_only": True,
    "saved_reports_only": True,
    "implementation_design_gate_only": True,
    "runner_file_created": False,
    "runner_test_file_created": False,
    "runner_report_created": False,
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
}

SCAFFOLD_FILES = [
    {
        "path": "tools/run_production_rebuild_live_preflight.py",
        "file_role": "future runner placeholder",
        "created_now": False,
        "initial_contents_policy": "imports standard library only; defines dataclass-like typed dictionaries or plain dict helpers; no qdrant_client import",
    },
    {
        "path": "tests/test_production_rebuild_live_preflight_runner.py",
        "file_role": "future mock-only test placeholder",
        "created_now": False,
        "initial_contents_policy": "uses fake read-only probe and local dict inputs only; no live services",
    },
    {
        "path": "tests/production_rebuild_live_preflight_report.json",
        "file_role": "future generated report path placeholder",
        "created_now": False,
        "initial_contents_policy": "not created until explicit future runner execution is authorized",
    },
]

SCAFFOLD_CONTRACT = {
    "entrypoint": "tools/run_production_rebuild_live_preflight.py",
    "entry_function": "build_live_preflight_report",
    "probe_injection_name": "qdrant_readonly_probe",
    "default_output": "tests/production_rebuild_live_preflight_report.json",
    "no_live_probe_by_default": True,
    "no_qdrant_import_in_core_logic": True,
    "no_write_methods_exposed": True,
    "all_unknown_states_fail_closed": True,
}

PLACEHOLDER_TESTS = [
    "test_default_paths_and_no_live_probe",
    "test_successful_fake_readonly_probe_does_not_grant_write_or_rebuild",
    "test_missing_authorization_fails_closed",
    "test_target_collection_mismatch_fails_closed",
    "test_fake_probe_error_fails_closed",
    "test_forbidden_write_method_exposure_fails_closed",
]

FORBIDDEN_SCAFFOLD_CONTENT = [
    "qdrant_client import",
    "OpenAI import",
    "rag_query call",
    "upsert/delete/recreate_collection/update_collection call",
    "collection switch or alias mutation",
    "real endpoint default",
    "execution command examples",
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


def gate_blockers(gate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    summary = as_dict(gate.get("summary"))
    if not gate:
        blockers.append("implementation_design_gate_missing")
        return blockers
    if gate.get("version") != GATE_EXPECTATION["version"]:
        blockers.append("implementation_design_gate_version_mismatch")
    if gate.get("schema_kind") != GATE_EXPECTATION["schema_kind"]:
        blockers.append("implementation_design_gate_schema_mismatch")
    if summary.get("status") != GATE_EXPECTATION["status"]:
        blockers.append("implementation_design_gate_status_mismatch")
    if summary.get("allowed_next_step") != GATE_EXPECTATION["allowed_next_step"]:
        blockers.append("implementation_design_gate_next_step_mismatch")
    if summary.get("failure_count") != 0 or summary.get("failed_checks") != []:
        blockers.append("implementation_design_gate_failure_drift")
    for field, expected in GATE_BOUNDARIES.items():
        if summary.get(field) != expected:
            blockers.append(f"implementation_design_gate_{field}_mismatch")
    if forbidden_output_keys(gate):
        blockers.append("implementation_design_gate_forbidden_output_key_present")
    return sorted(set(blockers))


def build_report(implementation_design_gate_path: Path = DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH) -> dict[str, Any]:
    gate = load_json(implementation_design_gate_path)
    blockers = gate_blockers(gate)
    status = "ready_for_minimal_implementation_scaffold_design_gate" if not blockers else "blocked"
    allowed_next_step = (
        "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate"
        if status != "blocked"
        else "blocked"
    )
    report = {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design",
        "scope": "design the future minimal runner scaffold without creating files or running live preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "implementation_design_gate": {
                "path": str(implementation_design_gate_path),
                "present": implementation_design_gate_path.exists(),
                "version": gate.get("version"),
                "schema_kind": gate.get("schema_kind"),
                "status": as_dict(gate.get("summary")).get("status"),
                "allowed_next_step": as_dict(gate.get("summary")).get("allowed_next_step"),
            }
        },
        "guardrails": GUARDRAILS,
        "scaffold_design": {
            "files": SCAFFOLD_FILES,
            "contract": SCAFFOLD_CONTRACT,
            "placeholder_tests": PLACEHOLDER_TESTS,
            "forbidden_scaffold_content": FORBIDDEN_SCAFFOLD_CONTENT,
        },
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "blockers": blockers,
            "scaffold_file_count": len(SCAFFOLD_FILES),
            "placeholder_test_count": len(PLACEHOLDER_TESTS),
            "runner_file_created": False,
            "runner_test_file_created": False,
            "runner_report_created": False,
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
    design = as_dict(report.get("scaffold_design"))
    lines = [
        "# v0.4.14.19 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design",
        "",
        "本版本只设计未来 runner scaffold，不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- scaffold files: `{summary.get('scaffold_file_count')}`",
        f"- placeholder tests: `{summary.get('placeholder_test_count')}`",
        f"- 是否创建 runner 文件: `{summary.get('runner_file_created')}`",
        f"- 是否允许现在运行 live preflight: `{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        "",
        "## 未来 scaffold 文件",
        "",
    ]
    for item in design.get("files", []):
        row = as_dict(item)
        lines.append(f"- `{row.get('path')}`: {row.get('file_role')}；created_now=`{row.get('created_now')}`")
    lines.extend([
        "",
        "结论：本版本只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate`；仍不创建 runner、不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.14.19 minimal implementation scaffold design.")
    parser.add_argument("--implementation-design-gate", type=Path, default=DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.implementation_design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild live preflight runner minimal implementation scaffold design: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
