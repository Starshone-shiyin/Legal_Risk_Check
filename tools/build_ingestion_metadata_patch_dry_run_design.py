"""Build the v0.4.13.2 ingestion metadata patch dry-run design.

This design defines how a future dry-run should compare pre/post article
metadata and ID drift without patching ingestion or writing Qdrant.
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


VERSION = "0.4.13.2"

DEFAULT_CONTRACT_PATH = legacy_report_path("ingestion_metadata_patch_contract_report.json")
DEFAULT_CONTRACT_GATE_PATH = legacy_report_path("ingestion_metadata_patch_contract_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_dry_run_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_dry_run_design_v0.4.13.2.md")

GUARDRAILS = {
    "design_only": True,
    "saved_reports_only": True,
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
    "ingestion_mutation": "disallowed",
    "metadata_mutation": "disallowed",
    "chunk_mutation": "disallowed",
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


def build_report(
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    contract_gate_path: Path = DEFAULT_CONTRACT_GATE_PATH,
) -> dict[str, Any]:
    contract_report = load_json(contract_path)
    gate_report = load_json(contract_gate_path)
    contract = as_dict(contract_report.get("patch_contract"))
    gate_summary = as_dict(gate_report.get("summary"))

    blockers = []
    if contract_report.get("version") != "0.4.13.0":
        blockers.append("contract_version_mismatch")
    if contract_report.get("schema_kind") != "ingestion_metadata_patch_contract":
        blockers.append("contract_schema_mismatch")
    if gate_report.get("version") != "0.4.13.1":
        blockers.append("contract_gate_version_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("contract_gate_not_passed")
    if contract.get("allowed_function") != "build_article_documents":
        blockers.append("unexpected_allowed_function")

    status = "ready_for_ingestion_metadata_patch_dry_run_design_gate" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_dry_run_design",
        "scope": "ingestion metadata patch dry-run design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "contract": {
                "path": str(contract_path),
                "version": contract_report.get("version"),
                "schema_kind": contract_report.get("schema_kind"),
            },
            "contract_gate": {
                "path": str(contract_gate_path),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
                "status": gate_summary.get("status"),
            },
        },
        "guardrails": GUARDRAILS,
        "design_gate": {
            "status": status,
            "allowed_next_step": "ingestion_metadata_patch_dry_run_design_gate" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "qdrant_write_allowed": False,
            "retrieval_logic_change_allowed": False,
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "dry_run_target": "simulate_build_article_documents_boundary_metadata_patch",
            "allowed_future_runner_scope": "local in-memory comparison only",
            "requires_rebuild": True,
            "stable_id_impact": "expected",
            "recommended_next_version": "v0.4.13.3 ingestion metadata patch dry-run design gate",
        },
        "dry_run_design": {
            "allowed_inputs": [
                "src/rag/ingestion.py source text",
                "small in-memory article_parts fixtures",
                "v0.4.13.0 contract report",
                "v0.4.13.1 contract gate report",
            ],
            "forbidden_inputs": [
                "Qdrant collection scroll",
                "knowledge base fulltext scan",
                "rag_query output",
                "LLM output",
                "embedding calls",
            ],
            "comparison_strategy": [
                "build pre-patch documents with current build_article_documents behavior",
                "build post-patch documents with an isolated simulation helper that only adds chunk_index/chunk_count",
                "run assign_stable_chunk_ids on cloned pre/post documents to estimate chunk_id and qdrant_point_id drift",
                "compare page_content, citation, block_type, paragraph_no, item_no, item_label, chunk_index, chunk_count, chunk_id, qdrant_point_id",
            ],
            "expected_metadata_drift": ["chunk_index", "chunk_count", "chunk_id", "qdrant_point_id"],
            "forbidden_metadata_drift": [
                "page_content",
                "citation",
                "block_type",
                "paragraph_no",
                "item_no",
                "item_label",
                "parent_article_id",
            ],
            "sample_scenarios": [
                {
                    "scenario_id": "single_paragraph_article",
                    "article_parts_shape": ["paragraph"],
                    "expected_post_patch_blocks": {"article": 1, "paragraph": 1, "item": 0},
                },
                {
                    "scenario_id": "multi_paragraph_article",
                    "article_parts_shape": ["paragraph", "paragraph"],
                    "expected_post_patch_blocks": {"article": 1, "paragraph": 2, "item": 0},
                },
                {
                    "scenario_id": "paragraph_with_items",
                    "article_parts_shape": ["item", "item"],
                    "expected_post_patch_blocks": {"article": 1, "paragraph": 0, "item": 2},
                },
            ],
        },
        "output_contract": {
            "required_summary_fields": [
                "status",
                "sample_count",
                "pre_document_count",
                "post_document_count",
                "metadata_drift_count",
                "chunk_id_drift_count",
                "qdrant_point_id_drift_count",
                "forbidden_drift_count",
            ],
            "required_row_fields": [
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
            ],
            "blocking_conditions": [
                "any content_changed row",
                "any citation_changed row",
                "any block_type/paragraph_no/item_no/item_label drift",
                "pre/post document count mismatch for a sample",
                "missing chunk_index or chunk_count after simulation",
            ],
        },
        "handoff": {
            "next_allowed_step": "gate this dry-run design",
            "not_allowed_yet": [
                "patch src/rag/ingestion.py",
                "write Qdrant",
                "rebuild collection",
                "run full eval as a substitute for dry-run",
                "modify rag_query or rules",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("design_gate"))
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("dry_run_design"))
    output = as_dict(report.get("output_contract"))
    lines = [
        "# v0.4.13.2 Ingestion Metadata Patch Dry-Run Design",
        "",
        "This report designs a future local dry-run. It does not patch ingestion, write Qdrant, or run RAG.",
        "",
        "## Overview",
        "",
        f"- Status: `{gate.get('status')}`",
        f"- Dry-run target: `{summary.get('dry_run_target')}`",
        f"- Future runner scope: `{summary.get('allowed_future_runner_scope')}`",
        f"- Stable ID impact: `{summary.get('stable_id_impact')}`",
        "",
        "## Comparison Strategy",
        "",
    ]
    for item in design.get("comparison_strategy", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Expected Drift", ""])
    for item in design.get("expected_metadata_drift", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Forbidden Drift", ""])
    for item in design.get("forbidden_metadata_drift", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocking Conditions", ""])
    for item in output.get("blocking_conditions", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.2 ingestion metadata patch dry-run design.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--contract-gate", type=Path, default=DEFAULT_CONTRACT_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.contract, args.contract_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    gate = as_dict(report.get("design_gate"))
    print(f"Ingestion metadata patch dry-run design: {gate.get('status')}, target={report['summary']['dry_run_target']}")
    return 0 if gate.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
