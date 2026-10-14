"""Build the v0.4.13.6 actual ingestion metadata patch design.

This report converts the approved contract and local dry-run gate into a
design-only implementation plan. It still does not patch ingestion, rebuild
Qdrant, or change retrieval behavior.
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


VERSION = "0.4.13.6"

DEFAULT_CONTRACT_PATH = legacy_report_path("ingestion_metadata_patch_contract_report.json")
DEFAULT_LOCAL_DRY_RUN_PATH = legacy_report_path("ingestion_metadata_patch_local_dry_run_report.json")
DEFAULT_LOCAL_DRY_RUN_GATE_PATH = legacy_report_path("ingestion_metadata_patch_local_dry_run_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_actual_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_actual_design_v0.4.13.6.md")

GUARDRAILS = {
    "design_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "knowledge_base_fulltext_scan": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "ingestion_source_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

PATCH_PLAN = {
    "allowed_file": "src/rag/ingestion.py",
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
    "parent_article_rule": {
        "block_type": "article",
        "chunk_index": 1,
        "chunk_count": 1,
        "content_change_allowed": False,
        "citation_change_allowed": False,
    },
    "child_chunk_rule": {
        "block_types": ["paragraph", "item"],
        "chunk_index": "1-based emission order across article_parts",
        "chunk_count": "len(article_parts)",
        "content_change_allowed": False,
        "citation_change_allowed": False,
    },
    "implementation_sketch": [
        "Set article metadata chunk_index=1 and chunk_count=1 when creating the parent article Document.",
        "Before iterating article_parts, compute child_chunk_count = len(article_parts) and child_chunk_index = 0.",
        "For each emitted paragraph or item child, increment child_chunk_index once and attach chunk_index=child_chunk_index and chunk_count=child_chunk_count.",
        "Do not alter page_content, citation, block_type, paragraph_no, item_no, item_label, parent_article_id, build_standard_section_documents, or assign_stable_chunk_ids.",
    ],
}

POST_PATCH_VALIDATION_PLAN = [
    "Add or update direct unit tests for build_article_documents parent article chunk_index=1 and chunk_count=1.",
    "Assert paragraph and item child chunks use deterministic 1-based emission order.",
    "Assert paragraph and item child chunks use chunk_count equal to len(article_parts).",
    "Assert page_content, citation, block_type, paragraph_no, item_no, item_label, and parent_article_id remain unchanged.",
    "Assert build_standard_section_documents behavior remains unchanged.",
    "Run a restricted diff check confirming only src/rag/ingestion.py changes among runtime sources.",
    "Do not rerun the v0.4.13.4 pre-patch drift runner as a post-patch drift expectation; after patch, direct metadata assertions become authoritative.",
]


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
    local_dry_run_path: Path = DEFAULT_LOCAL_DRY_RUN_PATH,
    local_dry_run_gate_path: Path = DEFAULT_LOCAL_DRY_RUN_GATE_PATH,
) -> dict[str, Any]:
    contract_report = load_json(contract_path)
    local_dry_run_report = load_json(local_dry_run_path)
    local_gate_report = load_json(local_dry_run_gate_path)
    contract = as_dict(contract_report.get("patch_contract"))
    dry_run_summary = as_dict(local_dry_run_report.get("summary"))
    gate_summary = as_dict(local_gate_report.get("summary"))

    blockers = []
    if contract_report.get("version") != "0.4.13.0":
        blockers.append("contract_version_mismatch")
    if contract_report.get("schema_kind") != "ingestion_metadata_patch_contract":
        blockers.append("contract_schema_mismatch")
    if local_dry_run_report.get("version") != "0.4.13.4":
        blockers.append("local_dry_run_version_mismatch")
    if dry_run_summary.get("status") != "passed":
        blockers.append("local_dry_run_not_passed")
    if local_gate_report.get("version") != "0.4.13.5":
        blockers.append("local_dry_run_gate_version_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("local_dry_run_gate_not_passed")
    if gate_summary.get("allowed_next_step") != "actual_ingestion_metadata_patch_design":
        blockers.append("unexpected_gate_next_step")
    if contract.get("allowed_function") != PATCH_PLAN["allowed_function"]:
        blockers.append("contract_allowed_function_mismatch")

    status = "ready_for_actual_ingestion_metadata_patch_design_gate" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_actual_design",
        "scope": "actual ingestion metadata patch design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "contract": {
                "path": str(contract_path),
                "version": contract_report.get("version"),
                "schema_kind": contract_report.get("schema_kind"),
            },
            "local_dry_run": {
                "path": str(local_dry_run_path),
                "version": local_dry_run_report.get("version"),
                "schema_kind": local_dry_run_report.get("schema_kind"),
                "status": dry_run_summary.get("status"),
            },
            "local_dry_run_gate": {
                "path": str(local_dry_run_gate_path),
                "version": local_gate_report.get("version"),
                "schema_kind": local_gate_report.get("schema_kind"),
                "status": gate_summary.get("status"),
                "allowed_next_step": gate_summary.get("allowed_next_step"),
            },
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "patch_target": "src/rag/ingestion.py::build_article_documents",
            "allowed_next_step": "actual_ingestion_metadata_patch_design_gate" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "retrieval_logic_change_allowed": False,
            "full_eval": "not_run",
            "stable_id_impact": "expected",
            "pre_patch_dry_run_status": dry_run_summary.get("status"),
            "pre_patch_drift_rows": dry_run_summary.get("metadata_drift_count"),
            "forbidden_drift_count": dry_run_summary.get("forbidden_drift_count"),
            "blockers": blockers,
        },
        "patch_design": PATCH_PLAN,
        "post_patch_validation_plan": POST_PATCH_VALIDATION_PLAN,
        "handoff": {
            "next_allowed_step": "gate this actual patch design" if status != "blocked" else "resolve design blockers",
            "not_allowed_yet": [
                "patch src/rag/ingestion.py",
                "write Qdrant",
                "rebuild collection",
                "modify rag_query or retriever",
                "modify anchor or risk rules",
                "modify eval cases or fixtures",
                "run full eval as a substitute for post-patch metadata tests",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("patch_design"))
    lines = [
        "# v0.4.13.6 Ingestion Metadata Patch Actual Design",
        "",
        "This report designs the actual ingestion metadata patch. It does not modify ingestion, write Qdrant, rebuild the collection, or change retrieval.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Patch target: `{summary.get('patch_target')}`",
        f"- Allowed next step: `{summary.get('allowed_next_step')}`",
        f"- Implementation allowed: `{summary.get('implementation_allowed')}`",
        f"- Rebuild allowed: `{summary.get('rebuild_allowed')}`",
        f"- Stable ID impact: `{summary.get('stable_id_impact')}`",
        "",
        "## Patch Rules",
        "",
        f"- Allowed file: `{design.get('allowed_file')}`",
        f"- Allowed function: `{design.get('allowed_function')}`",
        f"- Parent rule: `{design.get('parent_article_rule')}`",
        f"- Child rule: `{design.get('child_chunk_rule')}`",
        "",
        "## Implementation Sketch",
        "",
    ]
    for item in design.get("implementation_sketch", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Post-Patch Validation Plan", ""])
    for item in report.get("post_patch_validation_plan", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Still Not Allowed", ""])
    for item in as_dict(report.get("handoff")).get("not_allowed_yet", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.6 actual ingestion metadata patch design.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--local-dry-run", type=Path, default=DEFAULT_LOCAL_DRY_RUN_PATH)
    parser.add_argument("--local-dry-run-gate", type=Path, default=DEFAULT_LOCAL_DRY_RUN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.contract, args.local_dry_run, args.local_dry_run_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Ingestion metadata patch actual design: {summary.get('status')}, target={summary.get('patch_target')}")
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
