"""Check the v0.4.14.22 live preflight runner minimal scaffold gate.

The gate reads the v0.4.14.21 scaffold report and source files. It does not run
live preflight, access Qdrant, write the default preflight report, accept
authorization, rebuild collections, call RAG/embedding/LLM, run full eval, or
mutate runtime and eval artifacts.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.14.22"

DEFAULT_SCAFFOLD_REPORT_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json"
)
DEFAULT_RUNNER_PATH = Path("tools/run_production_rebuild_live_preflight.py")
DEFAULT_TEST_PATH = Path("tests/test_production_rebuild_live_preflight_runner.py")
DEFAULT_FORBIDDEN_REPORT_PATH = Path("tests/production_rebuild_live_preflight_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md"
)

EXPECTED_CREATED_FILES = {
    "tools/run_production_rebuild_live_preflight.py",
    "tests/test_production_rebuild_live_preflight_runner.py",
}

REQUIRED_SCAFFOLD_GUARDRAILS = {
    "standard_library_only": True,
    "no_live_probe_by_default": True,
    "no_qdrant_import_in_core_logic": True,
    "no_write_methods_exposed_by_runner": True,
    "mock_only_tests": True,
    "live_preflight_run": False,
    "production_rebuild_executed": False,
    "qdrant_write": "disallowed",
    "collection_switch": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
}

FORBIDDEN_IMPORTS = {
    "qdrant_client",
    "openai",
    "src.rag.retriever",
    "src.rag.ingestion",
    "src.risk.analyzer",
    "src.risk.report",
    "run_rag_eval",
}

FORBIDDEN_TEXT_PATTERNS = {
    "rag" + "_query(",
    "Qdrant" + "Client(",
    "Open" + "AI(",
    "run" + "_eval(",
    "--write",
    "--rebuild",
    "--force",
    "--switch-collection",
    "recreate_collection(",
    "update_collection(",
    "delete_collection(",
    "update_aliases(",
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


def check_row(check_id: str, passed: bool, details: str) -> dict[str, Any]:
    return {"check_id": check_id, "passed": passed, "details": details}


def source_imports(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_report(
    scaffold_report_path: Path = DEFAULT_SCAFFOLD_REPORT_PATH,
    runner_path: Path = DEFAULT_RUNNER_PATH,
    test_path: Path = DEFAULT_TEST_PATH,
    forbidden_report_path: Path = DEFAULT_FORBIDDEN_REPORT_PATH,
) -> dict[str, Any]:
    scaffold = load_json(scaffold_report_path)
    summary = as_dict(scaffold.get("summary"))
    guardrails = as_dict(scaffold.get("guardrails"))
    runner_source = source_text(runner_path)
    test_source = source_text(test_path)
    imports = source_imports(runner_path)
    forbidden_import_matches = sorted(FORBIDDEN_IMPORTS & imports)
    forbidden_text_matches = sorted(pattern for pattern in FORBIDDEN_TEXT_PATTERNS if pattern in runner_source)

    checks = [
        check_row("scaffold_report_present", bool(scaffold), "Scaffold report must exist and be a JSON object."),
        check_row("scaffold_version", scaffold.get("version") == "0.4.14.21", "Scaffold report must be v0.4.14.21."),
        check_row(
            "scaffold_schema",
            scaffold.get("schema_kind") == "production_rebuild_live_preflight_runner_minimal_implementation_scaffold",
            "Scaffold schema must match.",
        ),
        check_row(
            "scaffold_status",
            summary.get("status") == "ready_for_minimal_scaffold_gate",
            "Scaffold must be ready for this gate.",
        ),
        check_row(
            "scaffold_next_step",
            summary.get("allowed_next_step")
            == "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate",
            "Scaffold must open only this gate.",
        ),
        check_row(
            "created_files_present",
            set(scaffold.get("created_files") or []) == EXPECTED_CREATED_FILES
            and runner_path.exists()
            and test_path.exists(),
            "Runner scaffold and mock-only test must exist.",
        ),
        check_row(
            "historical_scaffold_report_declared_no_live_output",
            (scaffold.get("not_created_files") or []) == [str(forbidden_report_path).replace("\\", "/")]
            and summary.get("runner_report_created") is False,
            "Historical scaffold report must document that v0.4.14.21 itself did not create live output.",
        ),
        check_row(
            "scaffold_permissions_locked",
            summary.get("runner_file_created") is True
            and summary.get("runner_test_file_created") is True
            and summary.get("live_preflight_run_allowed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("production_rebuild_allowed") is False
            and summary.get("authorization_granted") is False
            and summary.get("full_eval") == "not_run",
            "Scaffold summary must not grant live preflight, Qdrant write, rebuild, authorization, or full eval.",
        ),
        check_row(
            "scaffold_guardrails_locked",
            set(guardrails) == set(REQUIRED_SCAFFOLD_GUARDRAILS)
            and all(guardrails.get(key) == expected for key, expected in REQUIRED_SCAFFOLD_GUARDRAILS.items()),
            "Scaffold guardrails must stay standard-library-only, mock-only, and non-executing.",
        ),
        check_row(
            "runner_imports_locked",
            not forbidden_import_matches,
            "Runner source must not import Qdrant, OpenAI, RAG, risk, or eval services.",
        ),
        check_row(
            "runner_forbidden_text_absent",
            not forbidden_text_matches,
            "Runner source must not include live service calls, write/rebuild flags, or collection mutation calls.",
        ),
        check_row(
            "runner_core_contract_present",
            "def build_live_preflight_report(" in runner_source
            and "qdrant_readonly_probe" in runner_source
            and "qdrant_write_allowed" in runner_source
            and "production_rebuild_allowed" in runner_source
            and "authorization_granted" in runner_source,
            "Runner must expose the injected-probe fail-closed report contract.",
        ),
        check_row(
            "mock_only_tests_present",
            "fake_probe" in test_source
            and "test_successful_fake_readonly_probe_does_not_grant_write_or_rebuild" in test_source
            and "test_forbidden_write_method_exposure_fails_closed" in test_source
            and "test_default_paths_and_no_live_probe" in test_source,
            "Mock-only tests must cover fake probe success, no-live default, and write exposure fail-closed.",
        ),
    ]

    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate",
        "scope": "gate the minimal runner scaffold without live preflight execution",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "scaffold_report": {
                "path": str(scaffold_report_path),
                "present": scaffold_report_path.exists(),
                "version": scaffold.get("version"),
                "schema_kind": scaffold.get("schema_kind"),
                "status": summary.get("status"),
                "allowed_next_step": summary.get("allowed_next_step"),
            },
            "runner_path": str(runner_path),
            "test_path": str(test_path),
            "forbidden_default_report_path": str(forbidden_report_path),
        },
        "source_scan": {
            "runner_imports": sorted(imports),
            "forbidden_import_matches": forbidden_import_matches,
            "forbidden_text_matches": forbidden_text_matches,
        },
        "checks": checks,
        "guardrails": {
            "gate_only": True,
            "saved_reports_and_source_scan_only": True,
            "live_preflight_run": False,
            "qdrant_access": "disallowed",
            "qdrant_write": "disallowed",
            "production_rebuild_executed": False,
            "authorization_granted": False,
            "rag_query_integration": "disallowed",
            "embedding_call": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "summary": {
            "status": status,
            "allowed_next_step": "historical_scaffold_gate_retained_for_traceability" if status == "passed" else "blocked",
            "check_count": len(checks),
            "failure_count": len(failed),
            "failed_checks": [row["check_id"] for row in failed],
            "runner_file_created": runner_path.exists(),
            "runner_test_file_created": test_path.exists(),
            "runner_report_created": forbidden_report_path.exists(),
            "live_preflight_run_allowed": False,
            "qdrant_write_allowed": False,
            "production_rebuild_allowed": False,
            "authorization_granted": False,
            "full_eval": "not_run",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    failed = summary.get("failed_checks") or []
    lines = [
        "# v0.4.14.22 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate",
        "",
        "本版本只 gate v0.4.14.21 最小 runner scaffold，不运行 live preflight，不访问或写入 Qdrant，不执行 production rebuild。",
        "",
        "## 摘要",
        "",
        f"- 状态：`{summary.get('status')}`",
        f"- 允许的下一步：`{summary.get('allowed_next_step')}`",
        f"- 检查项：`{summary.get('check_count')}`",
        f"- 失败项：`{summary.get('failure_count')}`",
        f"- 是否创建正式 live preflight 输出：`{summary.get('runner_report_created')}`",
        f"- 是否允许现在写入 Qdrant：`{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许现在 production rebuild：`{summary.get('production_rebuild_allowed')}`",
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
        "结论：gate 通过后仍不能直接运行 live preflight 或 production rebuild；下一步只允许继续收紧 mock preflight contract / dry-run boundary。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.14.22 minimal runner scaffold gate.")
    parser.add_argument("--scaffold-report", type=Path, default=DEFAULT_SCAFFOLD_REPORT_PATH)
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER_PATH)
    parser.add_argument("--test", type=Path, default=DEFAULT_TEST_PATH)
    parser.add_argument("--forbidden-report", type=Path, default=DEFAULT_FORBIDDEN_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.scaffold_report, args.runner, args.test, args.forbidden_report)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Production rebuild live preflight runner minimal scaffold gate: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
