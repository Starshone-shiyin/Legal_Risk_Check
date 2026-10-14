"""Check the v0.4.13.5 ingestion metadata patch local dry-run gate.

The gate validates the v0.4.13.4 local dry-run report and keeps actual
ingestion patching, Qdrant writes, rebuilds, and retrieval changes blocked.
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


VERSION = "0.4.13.5"

DEFAULT_LOCAL_DRY_RUN_PATH = legacy_report_path("ingestion_metadata_patch_local_dry_run_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_local_dry_run_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_local_dry_run_gate_v0.4.13.5.md")

REQUIRED_ROW_FIELDS = {
    "scenario_id",
    "doc_index",
    "block_type",
    "pre_chunk_index",
    "post_chunk_index",
    "pre_chunk_count",
    "post_chunk_count",
    "content_changed",
    "citation_changed",
    "chunk_id_changed",
    "qdrant_point_id_changed",
    "forbidden_drift",
    "missing_post_boundary_metadata",
}

REQUIRED_SCENARIOS = {
    "single_paragraph_article",
    "multi_paragraph_article",
    "paragraph_with_items",
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


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("rows", [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _samples(report: dict[str, Any]) -> list[dict[str, Any]]:
    samples = report.get("sample_results", [])
    return [sample for sample in samples if isinstance(sample, dict)] if isinstance(samples, list) else []


def build_report(local_dry_run_path: Path = DEFAULT_LOCAL_DRY_RUN_PATH) -> dict[str, Any]:
    dry_run_report = load_json(local_dry_run_path)
    summary = as_dict(dry_run_report.get("summary"))
    guardrails = as_dict(dry_run_report.get("guardrails"))
    handoff = as_dict(dry_run_report.get("handoff"))
    rows = _rows(dry_run_report)
    samples = _samples(dry_run_report)
    sample_ids = {sample.get("scenario_id") for sample in samples}
    expected_drift = set(dry_run_report.get("expected_metadata_drift", []))
    forbidden_drift = set(dry_run_report.get("forbidden_metadata_drift", []))
    not_allowed_yet = set(handoff.get("not_allowed_yet", []))

    row_count_matches = len(rows) == summary.get("post_document_count")
    all_rows_have_required_fields = all(REQUIRED_ROW_FIELDS.issubset(row.keys()) for row in rows)
    all_rows_keep_content = all(row.get("content_changed") is False for row in rows)
    all_rows_keep_citation = all(row.get("citation_changed") is False for row in rows)
    all_rows_have_no_forbidden_drift = all(row.get("forbidden_drift") == [] for row in rows)
    all_rows_have_boundary_metadata = all(
        row.get("missing_post_boundary_metadata") is False
        and row.get("post_chunk_index") is not None
        and row.get("post_chunk_count") is not None
        for row in rows
    )
    all_rows_have_expected_id_drift = all(
        row.get("chunk_id_changed") is True and row.get("qdrant_point_id_changed") is True
        for row in rows
    )
    samples_have_no_blockers = all(sample.get("blockers") == [] for sample in samples)
    samples_have_equal_counts = all(sample.get("pre_document_count") == sample.get("post_document_count") for sample in samples)
    samples_match_expected_blocks = all(sample.get("expected_blocks") == sample.get("post_block_counts") for sample in samples)

    checks = [
        check_row("report_version", dry_run_report.get("version") == "0.4.13.4", "Local dry-run report must be v0.4.13.4."),
        check_row("report_schema", dry_run_report.get("schema_kind") == "ingestion_metadata_patch_local_dry_run", "Local dry-run schema must match."),
        check_row("report_status", summary.get("status") == "passed", "Local dry-run must have passed before this gate."),
        check_row("sample_count", summary.get("sample_count") == 3 and REQUIRED_SCENARIOS.issubset(sample_ids), "Gate requires the three approved in-memory scenarios."),
        check_row("document_counts", summary.get("pre_document_count") == summary.get("post_document_count") and summary.get("post_document_count", 0) > 0, "Pre/post document counts must match and be nonzero."),
        check_row("row_count", row_count_matches and len(rows) > 0, "Row count must match post_document_count."),
        check_row("row_fields", all_rows_have_required_fields, "Every row must contain required drift review fields."),
        check_row("expected_metadata_drift", {"chunk_index", "chunk_count", "chunk_id", "qdrant_point_id"}.issubset(expected_drift), "Expected drift must cover boundary metadata and stable IDs."),
        check_row("drift_counts", summary.get("metadata_drift_count", 0) > 0 and summary.get("chunk_id_drift_count", 0) > 0 and summary.get("qdrant_point_id_drift_count", 0) > 0, "Boundary metadata, chunk_id, and qdrant_point_id drift must be observed."),
        check_row("id_drift_rows", all_rows_have_expected_id_drift, "Every row should show expected stable ID and point ID drift."),
        check_row("forbidden_drift_config", {"block_type", "citation", "paragraph_no", "item_no", "item_label", "parent_article_id"}.issubset(forbidden_drift), "Forbidden drift config must cover citation and block identity metadata."),
        check_row("forbidden_drift_zero", summary.get("forbidden_drift_count") == 0 and all_rows_have_no_forbidden_drift, "Forbidden drift must remain zero at summary and row level."),
        check_row("content_stable", all_rows_keep_content, "No row may change page content."),
        check_row("citation_stable", all_rows_keep_citation, "No row may change citation."),
        check_row("boundary_metadata_present", all_rows_have_boundary_metadata, "Every post row must have chunk_index and chunk_count."),
        check_row("sample_block_counts", samples_have_no_blockers and samples_have_equal_counts and samples_match_expected_blocks, "Sample block counts must match expected shapes with no blockers."),
        check_row("blocking_conditions_zero", summary.get("blocking_condition_count") == 0, "Local dry-run must have zero blocking conditions."),
        check_row("next_step", summary.get("allowed_next_step") == "ingestion_metadata_patch_local_dry_run_gate", "Local dry-run must open only this gate."),
        check_row("local_only_guardrail", guardrails.get("local_in_memory_only") is True, "Dry-run must remain local and in-memory."),
        check_row("qdrant_blocked", guardrails.get("qdrant_access") == "disallowed" and guardrails.get("qdrant_write") == "disallowed" and summary.get("qdrant_write_allowed") is False, "Qdrant access/write must remain blocked."),
        check_row("rag_llm_embedding_blocked", guardrails.get("rag_query_integration") == "disallowed" and guardrails.get("embedding_call") == "disallowed" and guardrails.get("llm_access") == "disallowed", "RAG, embedding, and LLM calls must remain blocked."),
        check_row("implementation_blocked", summary.get("implementation_allowed") is False and guardrails.get("code_patch_authorized") is False and guardrails.get("ingestion_source_mutation") == "disallowed", "Actual ingestion patching must remain unauthorized."),
        check_row("retrieval_blocked", summary.get("retrieval_logic_change_allowed") is False and guardrails.get("retrieval_logic_change_allowed") is False, "Retrieval changes must remain blocked."),
        check_row("full_eval_not_run", summary.get("full_eval") == "not_run" and guardrails.get("full_eval") == "not_run", "Full eval must not run for this gate."),
        check_row("handoff_boundaries", {"patch src/rag/ingestion.py", "write Qdrant", "rebuild collection", "modify rag_query or rules", "run full eval as a substitute for local dry-run gate"}.issubset(not_allowed_yet), "Handoff must keep patch, Qdrant, rebuild, RAG/rules, and full-eval-substitution blocked."),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_local_dry_run_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "local_dry_run": {
                "path": str(local_dry_run_path),
                "version": dry_run_report.get("version"),
                "schema_kind": dry_run_report.get("schema_kind"),
                "status": summary.get("status"),
            },
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "actual_ingestion_metadata_patch_design" if status == "passed" else "blocked",
            "implementation_allowed": False,
            "retrieval_logic_change_allowed": False,
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
        "# v0.4.13.5 Ingestion Metadata Patch Local Dry-Run Gate",
        "",
        "This gate validates the v0.4.13.4 local dry-run report. It does not patch ingestion, write Qdrant, or rebuild the collection.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Allowed next step: `{summary.get('allowed_next_step')}`",
        f"- Implementation allowed: `{summary.get('implementation_allowed')}`",
        f"- Rebuild allowed: `{summary.get('rebuild_allowed')}`",
        "",
        "## Checks",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.5 ingestion metadata patch local dry-run gate.")
    parser.add_argument("--local-dry-run", type=Path, default=DEFAULT_LOCAL_DRY_RUN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.local_dry_run)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Ingestion metadata patch local dry-run gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
