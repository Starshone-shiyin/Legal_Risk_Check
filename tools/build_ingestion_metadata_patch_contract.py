"""Build the v0.4.13.0 ingestion metadata patch contract.

This contract defines the allowed future patch scope for article chunk boundary
metadata. It does not patch ingestion, rebuild Qdrant, or change retrieval.
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


VERSION = "0.4.13.0"

DEFAULT_SERIES_CLOSEOUT_PATH = legacy_report_path("metadata_chunking_series_closeout_report.json")
DEFAULT_FIX_DESIGN_PATH = legacy_report_path("metadata_chunking_fix_design_report.json")
DEFAULT_INGESTION_PATH = Path("src/rag/ingestion.py")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_contract_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_contract_v0.4.13.0.md")

GUARDRAILS = {
    "contract_only": True,
    "saved_reports_only": True,
    "source_static_read_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
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


def extract_function(source: str, name: str) -> str:
    marker = f"def {name}("
    start = source.find(marker)
    if start < 0:
        return ""
    next_def = source.find("\ndef ", start + len(marker))
    return source[start:] if next_def < 0 else source[start:next_def]


def build_report(
    closeout_path: Path = DEFAULT_SERIES_CLOSEOUT_PATH,
    fix_design_path: Path = DEFAULT_FIX_DESIGN_PATH,
    ingestion_path: Path = DEFAULT_INGESTION_PATH,
) -> dict[str, Any]:
    closeout = load_json(closeout_path)
    fix_design = load_json(fix_design_path)
    closeout_summary = as_dict(closeout.get("summary"))
    fix_summary = as_dict(fix_design.get("summary"))
    ingestion_source = ingestion_path.read_text(encoding="utf-8-sig") if ingestion_path.exists() else ""
    article_fn = extract_function(ingestion_source, "build_article_documents")
    stable_id_fn = extract_function(ingestion_source, "assign_stable_chunk_ids")

    blockers = []
    if closeout.get("version") != "0.4.12.3":
        blockers.append("series_closeout_version_mismatch")
    if closeout_summary.get("status") != "completed":
        blockers.append("series_closeout_not_completed")
    if fix_design.get("version") != "0.4.12.1":
        blockers.append("fix_design_version_mismatch")
    if fix_summary.get("design_target") != "build_article_documents_chunk_boundary_metadata":
        blockers.append("unexpected_fix_design_target")
    if not article_fn:
        blockers.append("build_article_documents_missing")
    if '"chunk_index"' in article_fn or '"chunk_count"' in article_fn:
        blockers.append("article_boundary_metadata_already_present")
    if 'metadata.get("chunk_index", "")' not in stable_id_fn:
        blockers.append("stable_id_chunk_index_dependency_missing")

    status = "ready_for_ingestion_metadata_patch_contract_gate" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_contract",
        "scope": "ingestion metadata patch contract only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "series_closeout": {
                "path": str(closeout_path),
                "version": closeout.get("version"),
                "schema_kind": closeout.get("schema_kind"),
            },
            "fix_design": {
                "path": str(fix_design_path),
                "version": fix_design.get("version"),
                "schema_kind": fix_design.get("schema_kind"),
            },
            "ingestion_source": {
                "path": str(ingestion_path),
                "present": bool(ingestion_source),
            },
        },
        "guardrails": GUARDRAILS,
        "contract_gate": {
            "status": status,
            "allowed_next_step": "ingestion_metadata_patch_contract_gate" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "patch_target": "src/rag/ingestion.py::build_article_documents",
            "allowed_future_patch_scope": "add deterministic chunk_index/chunk_count metadata only",
            "requires_rebuild": True,
            "stable_id_impact": "expected",
            "recommended_next_version": "v0.4.13.1 ingestion metadata patch contract gate",
        },
        "patch_contract": {
            "allowed_files": ["src/rag/ingestion.py"],
            "allowed_function": "build_article_documents",
            "forbidden_files": [
                "src/rag/retriever.py",
                "config/rag_anchor_rules.json",
                "config/risk_payload_supplement_rules.json",
                "tests/rag_eval_cases.json",
            ],
            "forbidden_functions": [
                "rag_query",
                "build_standard_section_documents",
                "assign_stable_chunk_ids",
            ],
            "required_metadata_fields": ["chunk_index", "chunk_count"],
            "parent_article_rule": {
                "block_type": "article",
                "chunk_index": 1,
                "chunk_count": 1,
                "content_change_allowed": False,
            },
            "child_chunk_rule": {
                "block_types": ["paragraph", "item"],
                "chunk_index": "1-based emission order within article_parts",
                "chunk_count": "len(article_parts)",
                "content_change_allowed": False,
            },
            "standard_section_rule": "preserve existing standard_section chunk_index/chunk_count behavior unchanged",
        },
        "required_future_tests": [
            "build_article_documents parent article has chunk_index=1 and chunk_count=1",
            "paragraph and item documents have deterministic 1-based chunk_index",
            "paragraph and item documents have chunk_count equal to len(article_parts)",
            "page_content and citation output remain unchanged",
            "build_standard_section_documents contract remains unchanged",
            "future stable ID drift is explicit and expected before rebuild",
        ],
        "rebuild_dry_run_requirements": [
            "estimate affected sources and block types before writing Qdrant",
            "estimate chunk_id and qdrant_point_id drift before writing Qdrant",
            "provide rollback path before rebuild",
            "run qdrant integrity after any approved rebuild",
            "run targeted RAG eval after any approved rebuild",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("contract_gate"))
    summary = as_dict(report.get("summary"))
    contract = as_dict(report.get("patch_contract"))
    lines = [
        "# v0.4.13.0 Ingestion Metadata Patch Contract",
        "",
        "This contract defines the future patch boundary. It does not patch ingestion or rebuild Qdrant.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Patch target: `{summary.get('patch_target')}`",
        f"- Allowed future scope: `{summary.get('allowed_future_patch_scope')}`",
        f"- Requires rebuild: `{summary.get('requires_rebuild')}`",
        "",
        "## Patch Contract",
        "",
        f"- Allowed file: `{', '.join(contract.get('allowed_files', []))}`",
        f"- Allowed function: `{contract.get('allowed_function')}`",
        f"- Required metadata fields: `{', '.join(contract.get('required_metadata_fields', []))}`",
        "- Parent article rule: `chunk_index=1`, `chunk_count=1`, no content change.",
        "- Paragraph/item rule: 1-based emission order, `chunk_count=len(article_parts)`, no content change.",
        "- Standard section behavior must remain unchanged.",
        "",
        "## Future Tests Required",
        "",
    ]
    for item in report.get("required_future_tests", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Rebuild Dry-Run Requirements", ""])
    for item in report.get("rebuild_dry_run_requirements", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.0 ingestion metadata patch contract.")
    parser.add_argument("--closeout", type=Path, default=DEFAULT_SERIES_CLOSEOUT_PATH)
    parser.add_argument("--fix-design", type=Path, default=DEFAULT_FIX_DESIGN_PATH)
    parser.add_argument("--ingestion", type=Path, default=DEFAULT_INGESTION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.closeout, args.fix_design, args.ingestion)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    gate = as_dict(report.get("contract_gate"))
    print(f"Ingestion metadata patch contract: {gate.get('status')}, target={report['summary']['patch_target']}")
    return 0 if gate.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
