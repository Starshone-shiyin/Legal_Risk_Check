"""Check the v0.4.12.1 metadata/chunking fix design gate.

The gate verifies that the design acknowledges stable ID impact, requires a
rebuild/dry-run path, and keeps runtime implementation unauthorized.
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


VERSION = "0.4.12.2"

DEFAULT_FIX_DESIGN_PATH = legacy_report_path("metadata_chunking_fix_design_report.json")
DEFAULT_ROOT_CAUSE_PATH = legacy_report_path("metadata_chunking_root_cause_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_fix_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_fix_design_gate_v0.4.12.2.md")


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


def build_report(
    fix_design_path: Path = DEFAULT_FIX_DESIGN_PATH,
    root_cause_path: Path = DEFAULT_ROOT_CAUSE_PATH,
) -> dict[str, Any]:
    fix_design = load_json(fix_design_path)
    root_cause = load_json(root_cause_path)
    fix_gate = as_dict(fix_design.get("fix_design_gate"))
    fix_summary = as_dict(fix_design.get("summary"))
    stable = as_dict(fix_design.get("stable_id_impact"))
    guardrails = as_dict(fix_design.get("guardrails"))
    metadata_contract = as_dict(fix_design.get("metadata_contract"))

    checks = [
        check_row("root_cause_version", root_cause.get("version") == "0.4.12.0", "Root-cause report must be v0.4.12.0."),
        check_row("fix_design_version", fix_design.get("version") == "0.4.12.1", "Fix design report must be v0.4.12.1."),
        check_row("fix_design_schema", fix_design.get("schema_kind") == "metadata_chunking_fix_design", "Fix design schema must match."),
        check_row("fix_design_ready", fix_gate.get("status") == "ready_for_fix_design_gate", "Fix design must explicitly open the gate step."),
        check_row("design_target", fix_summary.get("design_target") == "build_article_documents_chunk_boundary_metadata", "Design target must stay on article ingestion metadata."),
        check_row("required_fields", {"chunk_index", "chunk_count"}.issubset(set(metadata_contract.get("required_new_fields", []))), "Design must require chunk_index and chunk_count."),
        check_row("affected_block_types", {"article", "paragraph", "item"}.issubset(set(metadata_contract.get("affected_block_types", []))), "Design must cover article, paragraph, and item blocks."),
        check_row("stable_id_impact", stable.get("assign_stable_chunk_ids_includes_chunk_index") is True and stable.get("chunk_id_change_expected") is True, "Stable ID impact must be acknowledged."),
        check_row("point_id_impact", stable.get("qdrant_point_id_change_expected") is True, "Qdrant point ID impact must be acknowledged."),
        check_row("rebuild_required", stable.get("rebuild_required") is True and fix_summary.get("requires_rebuild") is True, "Rebuild must be required before any data write."),
        check_row("no_payload_patch", stable.get("direct_payload_patch_allowed") is False, "Direct Qdrant payload patching must remain blocked."),
        check_row("no_runtime_implementation", guardrails.get("implementation_allowed") is False and guardrails.get("code_patch_authorized") is False, "Implementation must remain unauthorized in this gate."),
        check_row("no_retriever_change", guardrails.get("retrieval_logic_change_allowed") is False, "Retriever changes must remain unauthorized."),
        check_row("no_eval_case_change", guardrails.get("eval_case_mutation") == "disallowed", "Eval case mutation must remain disallowed."),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "metadata_chunking_fix_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "fix_design": {
                "path": str(fix_design_path),
                "version": fix_design.get("version"),
                "schema_kind": fix_design.get("schema_kind"),
            },
            "root_cause": {
                "path": str(root_cause_path),
                "version": root_cause.get("version"),
                "schema_kind": root_cause.get("schema_kind"),
            },
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "metadata_chunking_series_closeout" if status == "passed" else "blocked",
            "implementation_allowed": False,
            "retrieval_logic_change_allowed": False,
            "full_eval": "not_run",
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.12.2 Metadata/Chunking Fix Design Gate",
        "",
        "This gate validates the v0.4.12.1 fix design. It does not implement the fix.",
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
    parser = argparse.ArgumentParser(description="Check the v0.4.12.2 metadata/chunking fix design gate.")
    parser.add_argument("--fix-design", type=Path, default=DEFAULT_FIX_DESIGN_PATH)
    parser.add_argument("--root-cause", type=Path, default=DEFAULT_ROOT_CAUSE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.fix_design, args.root_cause)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Metadata/chunking fix design gate: {summary.get('status')}, failed={summary.get('failed_check_count')}")
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
