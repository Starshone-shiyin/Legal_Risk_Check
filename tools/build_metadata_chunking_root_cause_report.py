"""Build the v0.4.12.0 metadata/chunking root-cause report.

This report reads only saved diagnostics and source text. It does not patch
ingestion, rebuild Qdrant, run RAG/LLM, or authorize runtime changes.
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


VERSION = "0.4.12.0"

DEFAULT_CLOSEOUT_PATH = legacy_report_path("evidence_metadata_snapshot_series_closeout_report.json")
DEFAULT_SNAPSHOT_PATH = legacy_report_path("evidence_metadata_snapshot_report.json")
DEFAULT_QDRANT_INTEGRITY_PATH = legacy_report_path("qdrant_index_integrity_report.json")
DEFAULT_INGESTION_PATH = Path("src/rag/ingestion.py")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_root_cause_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_root_cause_v0.4.12.0.md")

GUARDRAILS = {
    "saved_reports_only": True,
    "source_static_read_only": True,
    "qdrant_access": "disallowed",
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


def extract_function(source: str, name: str) -> str:
    marker = f"def {name}("
    start = source.find(marker)
    if start < 0:
        return ""
    next_def = source.find("\ndef ", start + len(marker))
    return source[start:] if next_def < 0 else source[start:next_def]


def static_ingestion_signals(source: str) -> dict[str, Any]:
    standard_fn = extract_function(source, "build_standard_section_documents")
    article_fn = extract_function(source, "build_article_documents")
    return {
        "standard_section_assigns_chunk_index": '"chunk_index": index' in standard_fn,
        "standard_section_assigns_chunk_count": '"chunk_count": len(chunks)' in standard_fn,
        "article_function_present": bool(article_fn),
        "article_function_assigns_chunk_index": '"chunk_index"' in article_fn,
        "article_function_assigns_chunk_count": '"chunk_count"' in article_fn,
        "article_block_types": [
            name
            for name in ["article", "paragraph", "item"]
            if f'"block_type": "{name}"' in article_fn
        ],
    }


def build_report(
    closeout_path: Path = DEFAULT_CLOSEOUT_PATH,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    qdrant_integrity_path: Path = DEFAULT_QDRANT_INTEGRITY_PATH,
    ingestion_path: Path = DEFAULT_INGESTION_PATH,
) -> dict[str, Any]:
    closeout = load_json(closeout_path)
    snapshot = load_json(snapshot_path)
    integrity = load_json(qdrant_integrity_path)
    ingestion_source = ingestion_path.read_text(encoding="utf-8-sig") if ingestion_path.exists() else ""
    signals = static_ingestion_signals(ingestion_source)
    finding_counts = as_dict(as_dict(closeout.get("summary")).get("finding_counts"))
    snapshot_summary = as_dict(snapshot.get("summary"))
    integrity_actual = as_dict(integrity.get("actual"))

    blockers = []
    if closeout.get("version") != "0.4.11.3":
        blockers.append("closeout_version_mismatch")
    if closeout.get("schema_kind") != "evidence_metadata_snapshot_series_closeout":
        blockers.append("closeout_schema_mismatch")
    if snapshot.get("version") != "0.4.11.1":
        blockers.append("snapshot_version_mismatch")
    if not ingestion_source:
        blockers.append("ingestion_source_missing")

    source_count_mismatch = bool(integrity.get("count_mismatches"))
    current_primary = as_dict(closeout.get("summary")).get("primary_finding")
    root_cause = "ingestion_article_chunks_missing_boundary_metadata"
    confidence = "high" if (
        current_primary == "chunk_boundary_ambiguity"
        and finding_counts.get("chunk_boundary_ambiguity") == snapshot_summary.get("diagnostic_row_count")
        and signals["standard_section_assigns_chunk_index"]
        and not signals["article_function_assigns_chunk_index"]
        and integrity.get("passed") is True
        and not source_count_mismatch
    ) else "medium"

    status = "ready_for_metadata_chunking_fix_design" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "metadata_chunking_root_cause_report",
        "scope": "metadata/chunking root-cause report only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "series_closeout": {"path": str(closeout_path), "version": closeout.get("version"), "schema_kind": closeout.get("schema_kind")},
            "snapshot": {"path": str(snapshot_path), "version": snapshot.get("version"), "schema_kind": snapshot.get("schema_kind")},
            "qdrant_integrity": {"path": str(qdrant_integrity_path), "passed": integrity.get("passed")},
            "ingestion_source": {"path": str(ingestion_path), "present": bool(ingestion_source)},
        },
        "guardrails": GUARDRAILS,
        "root_cause_gate": {
            "status": status,
            "allowed_next_step": "metadata_chunking_fix_design" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "primary_root_cause": root_cause,
            "confidence": confidence,
            "snapshot_target_count": snapshot_summary.get("target_count"),
            "snapshot_diagnostic_row_count": snapshot_summary.get("diagnostic_row_count"),
            "chunk_boundary_ambiguity_count": finding_counts.get("chunk_boundary_ambiguity", 0),
            "qdrant_total_scanned": integrity_actual.get("total_scanned"),
            "qdrant_integrity_passed": integrity.get("passed"),
            "source_count_mismatch": source_count_mismatch,
            "next_version_recommendation": "v0.4.12.1 metadata/chunking fix design",
        },
        "static_ingestion_signals": signals,
        "root_cause_candidates": [
            {
                "candidate": "ingestion_article_chunks_missing_boundary_metadata",
                "likelihood": confidence,
                "evidence": [
                    "Snapshot reports chunk_boundary_ambiguity for all evidence targets.",
                    "Standard section ingestion assigns chunk_index/chunk_count.",
                    "Article/paragraph/item ingestion path does not assign chunk_index/chunk_count.",
                    "Qdrant integrity source counts match manifest, reducing likelihood of simple stale-count drift.",
                ],
            },
            {
                "candidate": "old_collection_not_rebuilt_after_ingestion_change",
                "likelihood": "low" if integrity.get("passed") is True and not source_count_mismatch else "medium",
                "evidence": [
                    "Qdrant integrity report passes and source counts match expected manifest counts.",
                ],
            },
            {
                "candidate": "retrieval_main_flow_policy_issue",
                "likelihood": "low",
                "evidence": [
                    "The finding is present in stored payload metadata before retrieval policy is applied.",
                ],
            },
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("root_cause_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.12.0 Metadata/Chunking Root-Cause Report",
        "",
        "This report converts the v0.4.11.x evidence snapshot findings into a root-cause hypothesis. It does not authorize a fix.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Primary root cause: `{summary.get('primary_root_cause')}`",
        f"- Confidence: `{summary.get('confidence')}`",
        f"- Chunk boundary ambiguity count: {summary.get('chunk_boundary_ambiguity_count')}",
        f"- Qdrant integrity passed: {summary.get('qdrant_integrity_passed')}",
        "",
        "## Boundary",
        "",
        "- No ingestion patch, Qdrant rebuild, retrieval change, anchor change, prompt change, or eval-case edit is authorized.",
        "- Next step is fix design, not implementation.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closeout", type=Path, default=DEFAULT_CLOSEOUT_PATH)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--qdrant-integrity", type=Path, default=DEFAULT_QDRANT_INTEGRITY_PATH)
    parser.add_argument("--ingestion", type=Path, default=DEFAULT_INGESTION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.closeout, args.snapshot, args.qdrant_integrity, args.ingestion)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    print(
        "Metadata/chunking root-cause report built: "
        f"{report['summary']['status']}, {report['summary']['primary_root_cause']}"
    )
    return 0 if report["root_cause_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
