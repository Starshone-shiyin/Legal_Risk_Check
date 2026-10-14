"""Check the v0.4.14.20 live preflight runner scaffold design gate.

The gate reads only the saved v0.4.14.19 scaffold design report. It does not
create the future runner, run live preflight, access Qdrant, create or accept
authorization, rebuild collections, call RAG/embedding/LLM, run full eval, or
mutate runtime and eval artifacts.
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


VERSION = "0.4.14.20"

DEFAULT_DESIGN_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md"
)

EXPECTED_FUTURE_FILES = {
    "tools/run_production_rebuild_live_preflight.py",
    "tests/test_production_rebuild_live_preflight_runner.py",
    "tests/production_rebuild_live_preflight_report.json",
}

EXPECTED_CONTRACT = {
    "entrypoint": "tools/run_production_rebuild_live_preflight.py",
    "entry_function": "build_live_preflight_report",
    "probe_injection_name": "qdrant_readonly_probe",
    "default_output": "tests/production_rebuild_live_preflight_report.json",
    "no_live_probe_by_default": True,
    "no_qdrant_import_in_core_logic": True,
    "no_write_methods_exposed": True,
    "all_unknown_states_fail_closed": True,
}

EXPECTED_PLACEHOLDER_TESTS = {
    "test_default_paths_and_no_live_probe",
    "test_successful_fake_readonly_probe_does_not_grant_write_or_rebuild",
    "test_missing_authorization_fails_closed",
    "test_target_collection_mismatch_fails_closed",
    "test_fake_probe_error_fails_closed",
    "test_forbidden_write_method_exposure_fails_closed",
}

EXPECTED_FORBIDDEN_SCAFFOLD_CONTENT = {
    "qdrant_client import",
    "OpenAI import",
    "rag_query call",
    "upsert/delete/recreate_collection/update_collection call",
    "collection switch or alias mutation",
    "real endpoint default",
    "execution command examples",
}

REQUIRED_GUARDRAILS = {
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


def field_set(rows: list[Any], key: str) -> set[str]:
    values: set[str] = set()
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get(key), str):
            values.add(row[key])
    return values


def build_report(design_path: Path = DEFAULT_DESIGN_PATH) -> dict[str, Any]:
    design = load_json(design_path)
    summary = as_dict(design.get("summary"))
    guardrails = as_dict(design.get("guardrails"))
    scaffold_design = as_dict(design.get("scaffold_design"))
    inputs = as_dict(design.get("inputs"))
    implementation_gate = as_dict(inputs.get("implementation_design_gate"))
    files = as_list(scaffold_design.get("files"))
    contract = as_dict(scaffold_design.get("contract"))

    checks = [
        check_row("design_present", bool(design), "Scaffold design report must exist and be a JSON object."),
        check_row("design_version", design.get("version") == "0.4.14.19", "Design report must be v0.4.14.19."),
        check_row(
            "design_schema",
            design.get("schema_kind")
            == "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design",
            "Design schema must match.",
        ),
        check_row(
            "design_status",
            summary.get("status") == "ready_for_minimal_implementation_scaffold_design_gate",
            "Design must be ready for this gate.",
        ),
        check_row(
            "design_next_step",
            summary.get("allowed_next_step")
            == "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate",
            "Design must open only this gate.",
        ),
        check_row("design_blockers_empty", summary.get("blockers") == [], "Design blockers must be empty."),
        check_row(
            "lineage_implementation_design_gate_only",
            set(inputs) == {"implementation_design_gate"}
            and implementation_gate.get("version") == "0.4.14.18"
            and implementation_gate.get("schema_kind")
            == "production_rebuild_live_preflight_runner_minimal_implementation_design_gate"
            and implementation_gate.get("status") == "passed"
            and implementation_gate.get("allowed_next_step")
            == "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design",
            "Design must be sourced only from the v0.4.14.18 implementation design gate.",
        ),
        check_row(
            "summary_permissions_locked",
            summary.get("runner_file_created") is False
            and summary.get("runner_test_file_created") is False
            and summary.get("runner_report_created") is False
            and summary.get("runner_created") is False
            and summary.get("runner_executed") is False
            and summary.get("live_preflight_run_allowed") is False
            and summary.get("production_rebuild_allowed") is False
            and summary.get("qdrant_access_allowed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("authorization_granted") is False
            and summary.get("full_eval") == "not_run",
            "Summary must not grant runner creation/execution, Qdrant, rebuild, authorization, or full eval.",
        ),
        check_row(
            "guardrails_locked",
            set(guardrails) == set(REQUIRED_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()),
            "Guardrails must stay scaffold-design-only and block execution and runtime mutation.",
        ),
        check_row(
            "scaffold_files_contract",
            summary.get("scaffold_file_count") == 3
            and field_set(files, "path") == EXPECTED_FUTURE_FILES
            and all(as_dict(row).get("created_now") is False for row in files),
            "Future scaffold files must match the expected set and stay marked not-created in the design report.",
        ),
        check_row(
            "scaffold_contract_locked",
            set(contract) == set(EXPECTED_CONTRACT)
            and all(contract.get(key) == expected for key, expected in EXPECTED_CONTRACT.items()),
            "Scaffold contract must stay injected, read-only, no-write, and fail-closed.",
        ),
        check_row(
            "placeholder_tests_locked",
            summary.get("placeholder_test_count") == 6
            and set(as_list(scaffold_design.get("placeholder_tests"))) == EXPECTED_PLACEHOLDER_TESTS,
            "Placeholder test names must match the expected mock-only coverage.",
        ),
        check_row(
            "forbidden_scaffold_content_locked",
            set(as_list(scaffold_design.get("forbidden_scaffold_content"))) == EXPECTED_FORBIDDEN_SCAFFOLD_CONTENT,
            "Forbidden scaffold content list must block live services, writes, rebuilds, and command examples.",
        ),
        check_row(
            "forbidden_output_keys_absent",
            forbidden_output_keys(design) == [],
            "Design report must not contain execution-like forbidden output keys.",
        ),
    ]

    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    allowed_next_step = (
        "production_rebuild_live_preflight_runner_minimal_implementation_scaffold"
        if status == "passed"
        else "blocked"
    )
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate",
        "scope": "gate the minimal scaffold design without creating or running a live preflight runner",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "scaffold_design": {
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
            "runner_file_created": False,
            "runner_test_file_created": False,
            "runner_report_created": False,
            "runner_created": False,
            "runner_executed": False,
            "live_preflight_run": False,
            "production_rebuild_executed": False,
            "qdrant_access": "disallowed",
            "qdrant_write": "disallowed",
            "authorization_granted": False,
            "rag_query_integration": "disallowed",
            "embedding_call": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
            "runtime_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "fixture_mutation": "disallowed",
        },
        "summary": {
            "status": status,
            "allowed_next_step": allowed_next_step,
            "check_count": len(checks),
            "failure_count": len(failed),
            "failed_checks": [row["check_id"] for row in failed],
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


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    failed = summary.get("failed_checks") or []
    lines = [
        "# v0.4.14.20 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate",
        "",
        "本版本只 gate v0.4.14.19 scaffold design，不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不执行 production rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态：`{summary.get('status')}`",
        f"- 允许的下一步：`{summary.get('allowed_next_step')}`",
        f"- 检查项：`{summary.get('check_count')}`",
        f"- 失败项：`{summary.get('failure_count')}`",
        f"- 是否创建 runner 文件：`{summary.get('runner_file_created')}`",
        f"- 是否允许现在运行 live preflight：`{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant：`{summary.get('qdrant_write_allowed')}`",
        "",
        "## 失败项",
        "",
    ]
    if failed:
        lines.extend(f"- `{check_id}`" for check_id in failed)
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "结论：gate 通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold`；这只表示可以创建最小、默认不连接真实服务的 scaffold，仍不代表允许运行 live preflight、访问或写入 Qdrant、接受正式授权或执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.20 minimal scaffold design gate.")
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
        "Production rebuild live preflight runner minimal implementation scaffold design gate: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
