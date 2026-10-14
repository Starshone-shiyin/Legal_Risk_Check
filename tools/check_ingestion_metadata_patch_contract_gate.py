"""Check the v0.4.13.1 ingestion metadata patch contract gate.

The gate verifies that v0.4.13.0 remains a narrow contract: only
build_article_documents may be patched in a future version, and no runtime
implementation or Qdrant mutation is authorized.
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


VERSION = "0.4.13.1"

DEFAULT_CONTRACT_PATH = legacy_report_path("ingestion_metadata_patch_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_contract_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_contract_gate_v0.4.13.1.md")


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


def build_report(contract_path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    contract_report = load_json(contract_path)
    guardrails = as_dict(contract_report.get("guardrails"))
    gate = as_dict(contract_report.get("contract_gate"))
    summary = as_dict(contract_report.get("summary"))
    contract = as_dict(contract_report.get("patch_contract"))
    parent_rule = as_dict(contract.get("parent_article_rule"))
    child_rule = as_dict(contract.get("child_chunk_rule"))

    checks = [
        check_row("contract_version", contract_report.get("version") == "0.4.13.0", "Contract report must be v0.4.13.0."),
        check_row("contract_schema", contract_report.get("schema_kind") == "ingestion_metadata_patch_contract", "Contract schema must match."),
        check_row("contract_ready", gate.get("status") == "ready_for_ingestion_metadata_patch_contract_gate", "Contract must explicitly open this gate."),
        check_row("allowed_file_scope", contract.get("allowed_files") == ["src/rag/ingestion.py"], "Only src/rag/ingestion.py may be patched in a future version."),
        check_row("allowed_function_scope", contract.get("allowed_function") == "build_article_documents", "Only build_article_documents may be patched in a future version."),
        check_row("forbidden_runtime_files", {"src/rag/retriever.py", "config/rag_anchor_rules.json", "config/risk_payload_supplement_rules.json", "tests/rag_eval_cases.json"}.issubset(set(contract.get("forbidden_files", []))), "Runtime, rule, and eval case files must remain forbidden."),
        check_row("forbidden_functions", {"rag_query", "build_standard_section_documents", "assign_stable_chunk_ids"}.issubset(set(contract.get("forbidden_functions", []))), "Main retrieval, standard section, and stable ID functions must remain forbidden."),
        check_row("required_metadata_fields", {"chunk_index", "chunk_count"}.issubset(set(contract.get("required_metadata_fields", []))), "chunk_index and chunk_count must be required."),
        check_row("parent_article_rule", parent_rule.get("block_type") == "article" and parent_rule.get("chunk_index") == 1 and parent_rule.get("chunk_count") == 1 and parent_rule.get("content_change_allowed") is False, "Parent article rule must be deterministic and content preserving."),
        check_row("child_chunk_rule", set(child_rule.get("block_types", [])) == {"paragraph", "item"} and child_rule.get("chunk_index") == "1-based emission order within article_parts" and child_rule.get("chunk_count") == "len(article_parts)" and child_rule.get("content_change_allowed") is False, "Paragraph/item rule must be deterministic and content preserving."),
        check_row("requires_rebuild", summary.get("requires_rebuild") is True and summary.get("stable_id_impact") == "expected", "Rebuild and stable ID impact must remain explicit."),
        check_row("implementation_blocked", guardrails.get("implementation_allowed") is False and guardrails.get("code_patch_authorized") is False, "Implementation must remain unauthorized."),
        check_row("qdrant_blocked", guardrails.get("qdrant_write") == "disallowed" and guardrails.get("qdrant_access") == "disallowed", "Qdrant access/write must remain disallowed."),
        check_row("retrieval_blocked", guardrails.get("retrieval_logic_change_allowed") is False and guardrails.get("rag_query_integration") == "disallowed", "Retrieval changes must remain disallowed."),
        check_row("eval_case_blocked", guardrails.get("eval_case_mutation") == "disallowed" and guardrails.get("fixture_mutation") == "disallowed", "Eval case and fixture mutation must remain disallowed."),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_contract_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "contract": {
                "path": str(contract_path),
                "version": contract_report.get("version"),
                "schema_kind": contract_report.get("schema_kind"),
            },
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "ingestion_metadata_patch_dry_run_design" if status == "passed" else "blocked",
            "implementation_allowed": False,
            "retrieval_logic_change_allowed": False,
            "qdrant_write_allowed": False,
            "full_eval": "not_run",
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.1 Ingestion Metadata Patch Contract Gate",
        "",
        "This gate validates the v0.4.13.0 contract. It does not implement the patch.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Allowed next step: `{summary.get('allowed_next_step')}`",
        "",
        "## Checks",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.1 ingestion metadata patch contract gate.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.contract)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Ingestion metadata patch contract gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
