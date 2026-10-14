"""Check the v0.4.13.3 ingestion metadata patch dry-run design gate.

The gate validates the v0.4.13.2 dry-run design and keeps implementation,
Qdrant writes, and retrieval changes blocked.
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


VERSION = "0.4.13.3"

DEFAULT_DRY_RUN_DESIGN_PATH = legacy_report_path("ingestion_metadata_patch_dry_run_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_dry_run_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md")


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


def build_report(dry_run_design_path: Path = DEFAULT_DRY_RUN_DESIGN_PATH) -> dict[str, Any]:
    design_report = load_json(dry_run_design_path)
    guardrails = as_dict(design_report.get("guardrails"))
    design_gate = as_dict(design_report.get("design_gate"))
    summary = as_dict(design_report.get("summary"))
    design = as_dict(design_report.get("dry_run_design"))
    output = as_dict(design_report.get("output_contract"))
    handoff = as_dict(design_report.get("handoff"))

    expected_drift = set(design.get("expected_metadata_drift", []))
    forbidden_drift = set(design.get("forbidden_metadata_drift", []))
    allowed_inputs = set(design.get("allowed_inputs", []))
    forbidden_inputs = set(design.get("forbidden_inputs", []))
    comparison_strategy = " ".join(design.get("comparison_strategy", []))
    summary_fields = set(output.get("required_summary_fields", []))
    row_fields = set(output.get("required_row_fields", []))
    blocking_conditions = set(output.get("blocking_conditions", []))
    not_allowed_yet = set(handoff.get("not_allowed_yet", []))

    checks = [
        check_row("design_version", design_report.get("version") == "0.4.13.2", "Dry-run design report must be v0.4.13.2."),
        check_row("design_schema", design_report.get("schema_kind") == "ingestion_metadata_patch_dry_run_design", "Dry-run design schema must match."),
        check_row("design_ready", design_gate.get("status") == "ready_for_ingestion_metadata_patch_dry_run_design_gate", "Design must explicitly open this gate."),
        check_row("local_scope", summary.get("allowed_future_runner_scope") == "local in-memory comparison only", "Future runner scope must stay local and in-memory."),
        check_row("expected_drift", {"chunk_index", "chunk_count", "chunk_id", "qdrant_point_id"}.issubset(expected_drift), "Expected drift must cover boundary metadata and stable IDs."),
        check_row("forbidden_drift", {"page_content", "citation", "block_type", "paragraph_no", "item_no", "item_label", "parent_article_id"}.issubset(forbidden_drift), "Forbidden drift must cover content, citation, and block identity metadata."),
        check_row("allowed_inputs", {"src/rag/ingestion.py source text", "small in-memory article_parts fixtures", "v0.4.13.0 contract report", "v0.4.13.1 contract gate report"}.issubset(allowed_inputs), "Allowed inputs must stay local/saved-report scoped."),
        check_row("forbidden_inputs", {"Qdrant collection scroll", "knowledge base fulltext scan", "rag_query output", "LLM output", "embedding calls"}.issubset(forbidden_inputs), "Qdrant, knowledge scan, RAG, LLM, and embedding inputs must remain forbidden."),
        check_row("comparison_strategy", "isolated simulation helper" in comparison_strategy and "assign_stable_chunk_ids" in comparison_strategy, "Comparison strategy must include isolated simulation and stable ID drift estimate."),
        check_row("sample_scenarios", len(design.get("sample_scenarios", [])) >= 3, "Design must include at least three local article_parts sample scenarios."),
        check_row("summary_output_fields", {"status", "sample_count", "pre_document_count", "post_document_count", "metadata_drift_count", "chunk_id_drift_count", "qdrant_point_id_drift_count", "forbidden_drift_count"}.issubset(summary_fields), "Output summary fields must support drift and blocker accounting."),
        check_row("row_output_fields", {"scenario_id", "doc_index", "block_type", "pre_chunk_index", "post_chunk_index", "pre_chunk_count", "post_chunk_count", "content_changed", "citation_changed", "chunk_id_changed", "qdrant_point_id_changed", "forbidden_drift"}.issubset(row_fields), "Output row fields must support per-document drift review."),
        check_row("blocking_conditions", {"any content_changed row", "any citation_changed row", "any block_type/paragraph_no/item_no/item_label drift", "pre/post document count mismatch for a sample", "missing chunk_index or chunk_count after simulation"}.issubset(blocking_conditions), "Blocking conditions must catch content/citation/identity drift and missing boundary metadata."),
        check_row("implementation_blocked", guardrails.get("implementation_allowed") is False and guardrails.get("code_patch_authorized") is False and design_gate.get("implementation_allowed") is False, "Implementation must remain unauthorized."),
        check_row("qdrant_blocked", guardrails.get("qdrant_access") == "disallowed" and guardrails.get("qdrant_write") == "disallowed" and design_gate.get("qdrant_write_allowed") is False, "Qdrant access/write must remain blocked."),
        check_row("retrieval_blocked", guardrails.get("retrieval_logic_change_allowed") is False and guardrails.get("rag_query_integration") == "disallowed", "Retrieval changes must remain blocked."),
        check_row("mutation_blocked", guardrails.get("ingestion_mutation") == "disallowed" and guardrails.get("metadata_mutation") == "disallowed" and guardrails.get("chunk_mutation") == "disallowed", "Ingestion, metadata, and chunk mutations must remain blocked."),
        check_row("full_eval_not_substitute", "run full eval as a substitute for dry-run" in not_allowed_yet, "Full eval must not be used as a substitute for the dry-run."),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_dry_run_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "dry_run_design": {
                "path": str(dry_run_design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
            },
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "ingestion_metadata_patch_local_dry_run_runner" if status == "passed" else "blocked",
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
        "# v0.4.13.3 Ingestion Metadata Patch Dry-Run Design Gate",
        "",
        "This gate validates the v0.4.13.2 dry-run design. It does not implement the runner.",
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
    parser = argparse.ArgumentParser(description="Check the v0.4.13.3 ingestion metadata patch dry-run design gate.")
    parser.add_argument("--dry-run-design", type=Path, default=DEFAULT_DRY_RUN_DESIGN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.dry_run_design)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Ingestion metadata patch dry-run design gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
