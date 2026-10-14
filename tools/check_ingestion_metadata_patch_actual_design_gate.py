"""Check the v0.4.13.7 ingestion metadata patch actual design gate.

The gate validates the v0.4.13.6 actual patch design and keeps source patching,
Qdrant writes, rebuilds, retrieval changes, rules, and eval cases blocked until
the design itself is stable.
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


VERSION = "0.4.13.7"

DEFAULT_ACTUAL_DESIGN_PATH = legacy_report_path("ingestion_metadata_patch_actual_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_actual_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_actual_design_gate_v0.4.13.7.md")

EXPECTED_FORBIDDEN_FILES = {
    "src/rag/retriever.py",
    "config/rag_anchor_rules.json",
    "config/risk_payload_supplement_rules.json",
    "tests/rag_eval_cases.json",
}

EXPECTED_FORBIDDEN_FUNCTIONS = {
    "rag_query",
    "build_standard_section_documents",
    "assign_stable_chunk_ids",
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


def build_report(actual_design_path: Path = DEFAULT_ACTUAL_DESIGN_PATH) -> dict[str, Any]:
    design_report = load_json(actual_design_path)
    summary = as_dict(design_report.get("summary"))
    guardrails = as_dict(design_report.get("guardrails"))
    patch_design = as_dict(design_report.get("patch_design"))
    parent_rule = as_dict(patch_design.get("parent_article_rule"))
    child_rule = as_dict(patch_design.get("child_chunk_rule"))
    implementation_sketch = " ".join(patch_design.get("implementation_sketch", []))
    validation_plan = " ".join(design_report.get("post_patch_validation_plan", []))
    handoff = as_dict(design_report.get("handoff"))
    not_allowed_yet = set(handoff.get("not_allowed_yet", []))

    forbidden_files = set(patch_design.get("forbidden_files", []))
    forbidden_functions = set(patch_design.get("forbidden_functions", []))
    child_block_types = set(child_rule.get("block_types", []))

    checks = [
        check_row("design_version", design_report.get("version") == "0.4.13.6", "Actual patch design report must be v0.4.13.6."),
        check_row("design_schema", design_report.get("schema_kind") == "ingestion_metadata_patch_actual_design", "Actual patch design schema must match."),
        check_row("design_status", summary.get("status") == "ready_for_actual_ingestion_metadata_patch_design_gate", "Design must explicitly open this gate."),
        check_row("allowed_next_step", summary.get("allowed_next_step") == "actual_ingestion_metadata_patch_design_gate", "Design must open only this gate."),
        check_row("single_patch_target", summary.get("patch_target") == "src/rag/ingestion.py::build_article_documents", "Patch target must remain build_article_documents only."),
        check_row("single_file_scope", patch_design.get("allowed_file") == "src/rag/ingestion.py", "Allowed file must remain src/rag/ingestion.py."),
        check_row("single_function_scope", patch_design.get("allowed_function") == "build_article_documents", "Allowed function must remain build_article_documents."),
        check_row("forbidden_files", EXPECTED_FORBIDDEN_FILES.issubset(forbidden_files), "Retriever, rules, and eval cases must remain forbidden files."),
        check_row("forbidden_functions", EXPECTED_FORBIDDEN_FUNCTIONS.issubset(forbidden_functions), "rag_query, standard sections, and stable ID function must remain forbidden."),
        check_row("parent_article_rule", parent_rule.get("block_type") == "article" and parent_rule.get("chunk_index") == 1 and parent_rule.get("chunk_count") == 1, "Parent article chunk rule must be deterministic 1/1."),
        check_row("parent_content_citation_stable", parent_rule.get("content_change_allowed") is False and parent_rule.get("citation_change_allowed") is False, "Parent content and citation must remain unchanged."),
        check_row("child_block_types", {"paragraph", "item"}.issubset(child_block_types), "Child rule must cover paragraph and item blocks."),
        check_row("child_index_rule", child_rule.get("chunk_index") == "1-based emission order across article_parts", "Child chunk_index rule must remain 1-based emission order."),
        check_row("child_count_rule", child_rule.get("chunk_count") == "len(article_parts)", "Child chunk_count rule must remain len(article_parts)."),
        check_row("child_content_citation_stable", child_rule.get("content_change_allowed") is False and child_rule.get("citation_change_allowed") is False, "Child content and citation must remain unchanged."),
        check_row("implementation_sketch_parent", "chunk_index=1" in implementation_sketch and "chunk_count=1" in implementation_sketch, "Implementation sketch must include parent boundary metadata."),
        check_row("implementation_sketch_child", "child_chunk_count = len(article_parts)" in implementation_sketch and "child_chunk_index" in implementation_sketch, "Implementation sketch must include child counter and count rules."),
        check_row("implementation_sketch_no_other_changes", "Do not alter page_content" in implementation_sketch and "assign_stable_chunk_ids" in implementation_sketch, "Implementation sketch must block content/citation/stable-ID-function changes."),
        check_row("validation_parent_test", "parent article chunk_index=1 and chunk_count=1" in validation_plan, "Validation plan must test parent boundary metadata."),
        check_row("validation_child_tests", "1-based emission order" in validation_plan and "len(article_parts)" in validation_plan, "Validation plan must test child index/count metadata."),
        check_row("validation_content_citation", "page_content, citation, block_type" in validation_plan, "Validation plan must test content, citation, and block identity stability."),
        check_row("validation_standard_sections", "build_standard_section_documents behavior remains unchanged" in validation_plan, "Validation plan must preserve standard section behavior."),
        check_row("validation_restricted_diff", "restricted diff check" in validation_plan and "only src/rag/ingestion.py changes" in validation_plan, "Validation plan must require restricted runtime diff check."),
        check_row("validation_pre_patch_drift_note", "pre-patch drift runner" in validation_plan and "direct metadata assertions" in validation_plan, "Validation plan must not reuse pre-patch drift runner as post-patch expectation."),
        check_row("implementation_blocked", summary.get("implementation_allowed") is False and summary.get("code_patch_authorized") is False and guardrails.get("implementation_allowed") is False and guardrails.get("code_patch_authorized") is False, "Implementation must remain unauthorized in this gate."),
        check_row("ingestion_mutation_blocked", guardrails.get("ingestion_source_mutation") == "disallowed", "Ingestion source mutation must remain blocked by this gate."),
        check_row("qdrant_rebuild_blocked", summary.get("qdrant_write_allowed") is False and summary.get("rebuild_allowed") is False and guardrails.get("qdrant_write") == "disallowed" and guardrails.get("collection_rebuild") == "disallowed", "Qdrant write and rebuild must remain blocked."),
        check_row("retrieval_blocked", summary.get("retrieval_logic_change_allowed") is False and guardrails.get("retrieval_logic_change_allowed") is False and guardrails.get("rag_query_integration") == "disallowed", "Retrieval changes and rag_query integration must remain blocked."),
        check_row("rules_eval_blocked", guardrails.get("anchor_mutation") == "disallowed" and guardrails.get("risk_rule_mutation") == "disallowed" and guardrails.get("eval_case_mutation") == "disallowed" and guardrails.get("fixture_mutation") == "disallowed", "Rules, eval cases, and fixtures must remain blocked."),
        check_row("full_eval_not_run", summary.get("full_eval") == "not_run" and guardrails.get("full_eval") == "not_run", "Full eval must not run for this design gate."),
        check_row("handoff_boundaries", {"patch src/rag/ingestion.py", "write Qdrant", "rebuild collection", "modify rag_query or retriever", "modify anchor or risk rules", "modify eval cases or fixtures", "run full eval as a substitute for post-patch metadata tests"}.issubset(not_allowed_yet), "Handoff must keep implementation, Qdrant, rebuild, retrieval, rules, eval, fixtures, and full-eval-substitution blocked."),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_actual_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "actual_design": {
                "path": str(actual_design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": summary.get("status"),
            },
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "minimal_ingestion_metadata_source_patch" if status == "passed" else "blocked",
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
        "# v0.4.13.7 Ingestion Metadata Patch Actual Design Gate",
        "",
        "This gate validates the v0.4.13.6 actual patch design. It does not patch ingestion, write Qdrant, rebuild the collection, or change retrieval.",
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
    parser = argparse.ArgumentParser(description="Check the v0.4.13.7 ingestion metadata patch actual design gate.")
    parser.add_argument("--actual-design", type=Path, default=DEFAULT_ACTUAL_DESIGN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.actual_design)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Ingestion metadata patch actual design gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
