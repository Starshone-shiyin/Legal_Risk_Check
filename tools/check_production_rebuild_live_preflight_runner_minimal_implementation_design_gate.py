"""Check the v0.4.14.18 live preflight runner minimal implementation design gate.

The gate validates only the saved v0.4.14.17 implementation design report. It
does not create a runner, run live preflight, access Qdrant, create or accept
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


VERSION = "0.4.14.18"

DEFAULT_DESIGN_PATH = legacy_report_path("production_rebuild_live_preflight_runner_minimal_implementation_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md"
)

EXPECTED_FUTURE_FILES = {
    "tools/run_production_rebuild_live_preflight.py",
    "tests/test_production_rebuild_live_preflight_runner.py",
    "tests/production_rebuild_live_preflight_report.json",
}

EXPECTED_REQUIRED_ARGS = {
    "--authorization-record",
    "--target-collection",
    "--backup-or-snapshot-reference",
    "--source-lineage-reference",
    "--output",
}

EXPECTED_OPTIONAL_ARGS = {
    "--read-timeout-seconds",
    "--maintenance-window",
    "--strict-read-only",
}

EXPECTED_FORBIDDEN_ARGS = {
    "--write",
    "--rebuild",
    "--switch-collection",
    "--force",
}

EXPECTED_FUNCTION_INPUTS = {
    "authorization_record",
    "target_collection",
    "backup_or_snapshot_reference",
    "source_lineage_reference",
    "qdrant_readonly_probe",
    "clock",
}

EXPECTED_READ_ONLY_STRATEGY = {
    "require an injected qdrant_readonly_probe abstraction instead of importing qdrant_client in core logic",
    "perform only collection existence and metadata reachability checks in the future runner",
    "never call upsert, delete, recreate_collection, update_collection, or alias/switch APIs",
    "mark qdrant_write_allowed=false and production_rebuild_allowed=false in every preflight output",
}

EXPECTED_MOCK_TEST_STRATEGY = {
    "test accepted authorization plus successful read-only probe yields preflight_status=passed without write permission",
    "test missing authorization fails closed",
    "test target collection mismatch fails closed",
    "test read-only probe error fails closed",
    "test backup or snapshot reference missing fails closed",
    "test forbidden write-like method exposure fails closed",
}

EXPECTED_FAIL_CLOSED_RULES = {
    "unknown authorization status blocks",
    "missing or mismatched target collection blocks",
    "missing backup or snapshot reference blocks",
    "read-only probe exception blocks",
    "maintenance window mismatch blocks",
    "any unexpected field or permission drift blocks",
}

REQUIRED_GUARDRAILS = {
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
    impl = as_dict(design.get("implementation_design"))
    inputs = as_dict(design.get("inputs"))
    design_gate = as_dict(inputs.get("design_gate"))
    cli = as_dict(impl.get("cli_contract"))
    function = as_dict(impl.get("function_contract"))
    future_files = as_list(impl.get("future_files"))

    checks = [
        check_row("design_present", bool(design), "Design report must exist and be a JSON object."),
        check_row("design_version", design.get("version") == "0.4.14.17", "Design report must be v0.4.14.17."),
        check_row(
            "design_schema",
            design.get("schema_kind") == "production_rebuild_live_preflight_runner_minimal_implementation_design",
            "Design schema must match.",
        ),
        check_row(
            "design_status",
            summary.get("status") == "ready_for_minimal_implementation_design_gate",
            "Design must be ready for this gate.",
        ),
        check_row(
            "design_next_step",
            summary.get("allowed_next_step")
            == "production_rebuild_live_preflight_runner_minimal_implementation_design_gate",
            "Design must open only this gate.",
        ),
        check_row(
            "lineage_gate_only",
            set(inputs) == {"design_gate"}
            and design_gate.get("version") == "0.4.14.16"
            and design_gate.get("schema_kind") == "production_rebuild_live_preflight_runner_design_gate"
            and design_gate.get("status") == "passed",
            "Design must be sourced only from the v0.4.14.16 design gate.",
        ),
        check_row(
            "summary_permissions_locked",
            summary.get("runner_file_created") is False
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
            "Guardrails must remain implementation-design-only and block execution and runtime mutation.",
        ),
        check_row(
            "future_files_contract",
            field_set(future_files, "path") == EXPECTED_FUTURE_FILES
            and all(as_dict(row).get("created_now") is False for row in future_files),
            "Future files must match the expected set and stay marked not-created in the design report.",
        ),
        check_row(
            "cli_contract",
            cli.get("entrypoint") == "tools/run_production_rebuild_live_preflight.py"
            and set(as_list(cli.get("required_args"))) == EXPECTED_REQUIRED_ARGS
            and set(as_list(cli.get("optional_args"))) == EXPECTED_OPTIONAL_ARGS
            and set(as_list(cli.get("forbidden_args"))) == EXPECTED_FORBIDDEN_ARGS
            and cli.get("created_now") is False
            and "--qdrant-url-env" not in as_list(cli.get("optional_args")),
            "CLI contract must match the expected non-executable argument design and avoid Qdrant connection parameters.",
        ),
        check_row(
            "function_contract",
            function.get("entry_function") == "build_live_preflight_report"
            and set(as_list(function.get("inputs"))) == EXPECTED_FUNCTION_INPUTS
            and function.get("created_now") is False
            and "no writes" in str(function.get("side_effect_policy")),
            "Function contract must remain injected, non-created, and no-write.",
        ),
        check_row(
            "read_only_strategy",
            set(as_list(impl.get("read_only_strategy"))) == EXPECTED_READ_ONLY_STRATEGY,
            "Read-only strategy must exactly match the expected design.",
        ),
        check_row(
            "mock_test_strategy",
            set(as_list(impl.get("mock_test_strategy"))) == EXPECTED_MOCK_TEST_STRATEGY,
            "Mock test strategy must exactly match the expected design.",
        ),
        check_row(
            "fail_closed_rules",
            set(as_list(impl.get("fail_closed_rules"))) == EXPECTED_FAIL_CLOSED_RULES,
            "Fail-closed rules must exactly match the expected design.",
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
        "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design"
        if status == "passed"
        else "blocked"
    )
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_design_gate",
        "scope": "gate the minimal implementation design without creating or running a runner",
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


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.14.18 Production Rebuild Live Preflight Runner Minimal Implementation Design Gate",
        "",
        "本版本只 gate v0.4.14.17 minimal implementation design，不创建 runner 文件，不运行 live preflight，不访问或写入 Qdrant，不执行 rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failure_count')}`",
        f"- 是否创建 runner 文件: `{summary.get('runner_file_created')}`",
        f"- 是否允许现在运行 live preflight: `{summary.get('live_preflight_run_allowed')}`",
        f"- 是否允许现在写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
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
        "结论：gate 通过后只开放 `production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design`；仍不运行 live preflight、不访问或写入 Qdrant、不执行 production rebuild。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.18 minimal implementation design gate.")
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
        "Production rebuild live preflight runner minimal implementation design gate: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
