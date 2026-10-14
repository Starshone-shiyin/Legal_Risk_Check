"""Build the v0.4.11.0 evidence-level metadata snapshot contract.

The contract defines a future read-only Qdrant payload snapshot runner. It does
not connect to Qdrant, scan the knowledge base, run RAG/LLM, or mutate data.
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


VERSION = "0.4.11.0"

DEFAULT_CLOSEOUT_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_series_closeout_report.json")
DEFAULT_MANIFEST_PATH = legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json")
DEFAULT_EVAL_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_metadata_snapshot_contract_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/evidence_metadata_snapshot_contract_v0.4.11.0.md")

REQUIRED_METADATA_FIELDS = [
    "chunk_id",
    "parent_article_id",
    "source",
    "law_name",
    "citation",
    "block_type",
    "article_no_or_section_no",
    "chunk_index_or_chunk_count",
]

OUTPUT_FIELDS = [
    "case_id",
    "target_id",
    "expected_source",
    "expected_article_no",
    "expected_section_no",
    "matched_point_count",
    "metadata_completeness_status",
    "chunk_boundary_status",
    "parent_article_link_status",
    "citation_identity_status",
    "article_locator_status",
    "sample_case_mapping_status",
    "blocking_findings",
]

FAILURE_BUCKETS = [
    "target_not_found",
    "metadata_completeness_gap",
    "chunk_boundary_ambiguity",
    "parent_article_link_gap",
    "citation_identity_gap",
    "article_locator_gap",
    "sample_case_mapping_gap",
    "qdrant_unavailable",
]

GUARDRAILS = {
    "contract_only": True,
    "qdrant_access": "not_run_in_contract",
    "future_qdrant_access": "read_only_payload_scroll_allowed",
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


def case_index(eval_cases: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("id", ""): item
        for item in as_list(eval_cases.get("cases"))
        if isinstance(item, dict) and item.get("id")
    }


def manifest_case_ids(manifest: dict[str, Any]) -> list[str]:
    ids = []
    for item in as_list(manifest.get("manifest_items")):
        case_id = item.get("case_id")
        if case_id and case_id not in ids:
            ids.append(case_id)
    return ids


def target_id(case_id: str, evidence: dict[str, Any], index: int) -> str:
    source = evidence.get("source", "")
    article = evidence.get("article_no", evidence.get("section_no", ""))
    return f"{case_id}::{source}::{article or index}"


def build_snapshot_targets(case_ids: list[str], cases: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    targets = []
    blockers = []
    for case_id in case_ids:
        case = cases.get(case_id)
        if not case:
            blockers.append(f"{case_id}:missing_eval_case")
            continue
        expected_evidence = as_list(case.get("expected_evidence"))
        if not expected_evidence:
            blockers.append(f"{case_id}:missing_expected_evidence")
            continue
        for index, evidence in enumerate(expected_evidence, start=1):
            if not isinstance(evidence, dict):
                blockers.append(f"{case_id}:invalid_expected_evidence")
                continue
            targets.append({
                "case_id": case_id,
                "target_id": target_id(case_id, evidence, index),
                "expected_source": evidence.get("source", ""),
                "expected_article_no": evidence.get("article_no"),
                "expected_section_no": evidence.get("section_no"),
                "must_include": evidence.get("must_include", []),
                "matching_policy": "source_and_article_or_section_metadata",
            })
    return targets, blockers


def build_report(
    closeout_path: Path = DEFAULT_CLOSEOUT_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    eval_cases_path: Path = DEFAULT_EVAL_CASES_PATH,
) -> dict[str, Any]:
    closeout = load_json(closeout_path)
    manifest = load_json(manifest_path)
    eval_cases = load_json(eval_cases_path)
    case_ids = manifest_case_ids(manifest)
    targets, target_blockers = build_snapshot_targets(case_ids, case_index(eval_cases))

    blockers = []
    if closeout.get("version") != "0.4.10.3":
        blockers.append("closeout_version_mismatch")
    if closeout.get("schema_kind") != "metadata_chunking_diagnostic_runner_series_closeout":
        blockers.append("closeout_schema_mismatch")
    if as_dict(closeout.get("closeout_gate")).get("status") != "v0_4_10_series_closed_for_saved_report_diagnostic":
        blockers.append("closeout_not_ready")
    if manifest.get("version") != "0.4.10.0":
        blockers.append("manifest_version_mismatch")
    if manifest.get("schema_kind") != "metadata_chunking_diagnostic_runner_manifest":
        blockers.append("manifest_schema_mismatch")
    if len(case_ids) != 8:
        blockers.append("sample_case_count_not_8")
    blockers.extend(target_blockers)

    status = "ready_for_evidence_metadata_snapshot_runner" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "evidence_metadata_snapshot_contract",
        "scope": "read-only evidence-level metadata snapshot contract",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "series_closeout": {"path": str(closeout_path), "version": closeout.get("version"), "schema_kind": closeout.get("schema_kind")},
            "runner_manifest": {"path": str(manifest_path), "version": manifest.get("version"), "schema_kind": manifest.get("schema_kind")},
            "eval_cases": {"path": str(eval_cases_path), "case_count": len(as_list(eval_cases.get("cases")))},
        },
        "guardrails": GUARDRAILS,
        "contract_gate": {
            "status": status,
            "allowed_next_step": "read_only_evidence_metadata_snapshot_runner" if status != "blocked" else "blocked",
            "qdrant_access": "not_run_in_contract",
            "future_qdrant_access": "read_only_payload_scroll_allowed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": sorted(set(blockers)),
        },
        "snapshot_contract": {
            "collection": "legal_knowledge",
            "sample_case_count": len(case_ids),
            "target_count": len(targets),
            "required_metadata_fields": REQUIRED_METADATA_FIELDS,
            "output_fields": OUTPUT_FIELDS,
            "failure_buckets": FAILURE_BUCKETS,
            "read_policy": {
                "with_payload": True,
                "with_vectors": False,
                "scroll_only": True,
                "write_operations": "disallowed",
                "query_embedding": "disallowed",
            },
        },
        "snapshot_targets": targets,
        "assertions": [
            {"name": "source_reports_ready", "status": "passed" if not blockers else "failed", "blockers": sorted(set(blockers))},
            {"name": "read_only_contract", "status": "passed"},
            {"name": "runtime_changes_blocked", "status": "passed"},
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("contract_gate"))
    contract = as_dict(report.get("snapshot_contract"))
    lines = [
        "# v0.4.11.0 Evidence Metadata Snapshot Contract",
        "",
        "This contract defines a future read-only Qdrant payload snapshot runner. It does not connect to Qdrant or authorize data fixes.",
        "",
        "## Overview",
        "",
        f"- Contract status: `{gate.get('status')}`",
        f"- Sample cases: {contract.get('sample_case_count')}",
        f"- Snapshot targets: {contract.get('target_count')}",
        f"- Allowed next step: `{gate.get('allowed_next_step')}`",
        f"- Qdrant access in this version: `{gate.get('qdrant_access')}`",
        "",
        "## Boundaries",
        "",
        "- Future runner may read Qdrant payloads with vectors disabled.",
        "- No RAG query, embedding call, LLM call, full eval, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change is authorized.",
        "- The runner must report Qdrant unavailability as a blocker instead of fabricating evidence-level results.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closeout", type=Path, default=DEFAULT_CLOSEOUT_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--eval-cases", type=Path, default=DEFAULT_EVAL_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.closeout, args.manifest, args.eval_cases)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    print(
        "Evidence metadata snapshot contract built: "
        f"{report['contract_gate']['status']}, {report['snapshot_contract']['target_count']} targets"
    )
    return 0 if report["contract_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
