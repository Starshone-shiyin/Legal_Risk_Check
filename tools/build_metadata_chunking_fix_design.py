"""Build the v0.4.12.1 metadata/chunking fix design report.

The report turns the v0.4.12.0 root-cause finding into an implementation
design. It does not patch ingestion, rebuild Qdrant, or change retrieval.
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


VERSION = "0.4.12.1"

DEFAULT_ROOT_CAUSE_PATH = legacy_report_path("metadata_chunking_root_cause_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_fix_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_fix_design_v0.4.12.1.md")

GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
    "source_static_read_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "knowledge_base_fulltext_scan": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "metadata_mutation": "disallowed",
    "chunk_mutation": "disallowed",
    "ingestion_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
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


def build_report(root_cause_path: Path = DEFAULT_ROOT_CAUSE_PATH) -> dict[str, Any]:
    root_cause = load_json(root_cause_path)
    root_summary = as_dict(root_cause.get("summary"))
    root_gate = as_dict(root_cause.get("root_cause_gate"))

    blockers = []
    if root_cause.get("version") != "0.4.12.0":
        blockers.append("root_cause_version_mismatch")
    if root_cause.get("schema_kind") != "metadata_chunking_root_cause_report":
        blockers.append("root_cause_schema_mismatch")
    if root_gate.get("status") != "ready_for_metadata_chunking_fix_design":
        blockers.append("root_cause_not_ready_for_fix_design")
    if root_summary.get("primary_root_cause") != "ingestion_article_chunks_missing_boundary_metadata":
        blockers.append("unexpected_primary_root_cause")

    status = "ready_for_fix_design_gate" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "metadata_chunking_fix_design",
        "scope": "metadata/chunking fix design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "root_cause": {
                "path": str(root_cause_path),
                "version": root_cause.get("version"),
                "schema_kind": root_cause.get("schema_kind"),
                "primary_root_cause": root_summary.get("primary_root_cause"),
            }
        },
        "guardrails": GUARDRAILS,
        "fix_design_gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_fix_design_gate" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "design_target": "build_article_documents_chunk_boundary_metadata",
            "primary_root_cause": root_summary.get("primary_root_cause"),
            "requires_rebuild": True,
            "stable_id_impact": "expected",
            "recommended_next_version": "v0.4.12.2 metadata/chunking fix design gate",
        },
        "proposed_patch_plan": [
            {
                "step": "add_article_boundary_metadata",
                "target": "src/rag/ingestion.py::build_article_documents",
                "design": "Assign deterministic chunk_index/chunk_count to article, paragraph, and item documents produced by the legal article ingestion path.",
                "runtime_patch_allowed_in_this_version": False,
            },
            {
                "step": "preserve_standard_section_contract",
                "target": "src/rag/ingestion.py::build_standard_section_documents",
                "design": "Leave the existing standard_section chunk_index/chunk_count behavior unchanged.",
                "runtime_patch_allowed_in_this_version": False,
            },
            {
                "step": "rebuild_instead_of_payload_patch",
                "target": "Qdrant collection rebuild plan",
                "design": "Because stable chunk IDs include chunk_index, apply the future fix through an ingestion rebuild/dry-run path rather than direct Qdrant payload mutation.",
                "runtime_patch_allowed_in_this_version": False,
            },
        ],
        "metadata_contract": {
            "affected_block_types": ["article", "paragraph", "item"],
            "required_new_fields": ["chunk_index", "chunk_count"],
            "chunk_index_base": 1,
            "chunk_count_rule": "count deterministic sibling chunks generated for the same parent article scope",
            "parent_article_document_rule": "single parent article document should receive chunk_index=1 and chunk_count=1 unless a future design explicitly splits parent article content",
            "paragraph_item_rule": "paragraph and item documents should receive deterministic sibling positions after article parsing and before stable chunk ID assignment",
        },
        "stable_id_impact": {
            "assign_stable_chunk_ids_includes_chunk_index": True,
            "chunk_id_change_expected": True,
            "qdrant_point_id_change_expected": True,
            "direct_payload_patch_allowed": False,
            "rebuild_required": True,
        },
        "required_future_validations": [
            "ingestion unit tests for article/paragraph/item chunk_index and chunk_count",
            "stable chunk ID drift test documenting expected ID changes",
            "rebuild dry-run report before writing Qdrant",
            "qdrant index integrity check after any approved rebuild",
            "targeted RAG eval after rebuild",
            "full RAG eval only after behavior-impacting rebuild is approved",
        ],
        "prohibited_actions": [
            "do not patch src/rag/ingestion.py in v0.4.12.1",
            "do not patch src/rag/retriever.py",
            "do not write Qdrant payloads",
            "do not rebuild the collection",
            "do not change anchor/risk supplement rules",
            "do not change eval cases or fixtures",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("fix_design_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.12.1 Metadata/Chunking Fix Design",
        "",
        "This report is a design handoff only. It does not patch ingestion, rebuild Qdrant, or change retrieval.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Design target: `{summary.get('design_target')}`",
        f"- Requires rebuild: `{summary.get('requires_rebuild')}`",
        f"- Stable ID impact: `{summary.get('stable_id_impact')}`",
        "",
        "## Proposed Patch Plan",
        "",
    ]
    for row in report.get("proposed_patch_plan", []):
        lines.append(f"- `{row.get('step')}`: {row.get('design')}")
    lines.extend(
        [
            "",
            "## Metadata Contract",
            "",
            f"- Required fields: `{', '.join(report.get('metadata_contract', {}).get('required_new_fields', []))}`",
            f"- Affected block types: `{', '.join(report.get('metadata_contract', {}).get('affected_block_types', []))}`",
            "",
            "## Stable ID Impact",
            "",
            "- `assign_stable_chunk_ids` already includes `chunk_index`; future implementation is expected to change chunk IDs and Qdrant point IDs.",
            "- Direct Qdrant payload patching remains disallowed. A rebuild/dry-run plan is required before any data write.",
            "",
            "## Required Future Validations",
            "",
        ]
    )
    for item in report.get("required_future_validations", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Boundary", ""])
    for item in report.get("prohibited_actions", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.12.1 metadata/chunking fix design report.")
    parser.add_argument("--root-cause", type=Path, default=DEFAULT_ROOT_CAUSE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root_cause)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    gate = as_dict(report.get("fix_design_gate"))
    print(f"Metadata/chunking fix design built: {gate.get('status')}, {report['summary']['design_target']}")
    return 1 if gate.get("status") == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
