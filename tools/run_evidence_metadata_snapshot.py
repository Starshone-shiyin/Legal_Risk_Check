"""Run the v0.4.11.1 read-only evidence metadata snapshot.

The runner reads Qdrant payload metadata only, with vectors disabled. It does
not call rag_query, embeddings, an LLM, full eval, or any write/mutation API.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client import QdrantClient

from tools._shared.layout import legacy_report_path


VERSION = "0.4.11.1"

DEFAULT_CONTRACT_PATH = legacy_report_path("evidence_metadata_snapshot_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_metadata_snapshot_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/evidence_metadata_snapshot_v0.4.11.1.md")
DEFAULT_COLLECTION = "legal_knowledge"

GUARDRAILS = {
    "read_only_qdrant_payload_snapshot": True,
    "with_vectors": False,
    "scroll_only": True,
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


def env_value(name: str, default: str) -> str:
    if name in os.environ:
        return os.environ[name]
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip().upper() == name:
                return value.strip().strip('"').strip("'")
    return default


def connect_client(host: str, port: int, timeout: float) -> QdrantClient:
    return QdrantClient(host=host, port=port, timeout=timeout)


def article_locator(metadata: dict[str, Any]) -> Any:
    return metadata.get("article_no") if metadata.get("article_no") is not None else metadata.get("section_no")


def target_matches(target: dict[str, Any], metadata: dict[str, Any]) -> bool:
    expected_source = target.get("expected_source")
    source_candidates = {metadata.get("source"), metadata.get("law_name")}
    if expected_source not in source_candidates:
        return False
    expected_article = target.get("expected_article_no")
    expected_section = target.get("expected_section_no")
    if expected_article is not None:
        return metadata.get("article_no") == expected_article
    if expected_section is not None:
        return metadata.get("section_no") == expected_section
    return False


def summarize_match(point_id: Any, payload: dict[str, Any]) -> dict[str, Any]:
    metadata = as_dict(payload.get("metadata"))
    return {
        "point_id": str(point_id),
        "chunk_id": metadata.get("chunk_id"),
        "parent_article_id": metadata.get("parent_article_id"),
        "source": metadata.get("source"),
        "law_name": metadata.get("law_name"),
        "citation": metadata.get("citation"),
        "block_type": metadata.get("block_type"),
        "article_no": metadata.get("article_no"),
        "section_no": metadata.get("section_no"),
        "chunk_index": metadata.get("chunk_index"),
        "chunk_count": metadata.get("chunk_count"),
        "content_preview": (payload.get("page_content") or payload.get("content") or "")[:160],
    }


def status_for_required_fields(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "target_not_found"
    required = ["chunk_id", "parent_article_id", "source", "law_name", "citation", "block_type"]
    missing = [field for field in required if not any(item.get(field) not in (None, "") for item in matches)]
    has_locator = any(item.get("article_no") is not None or item.get("section_no") for item in matches)
    if not has_locator:
        missing.append("article_no_or_section_no")
    return "passed" if not missing else "metadata_completeness_gap"


def diagnostic_row(target: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    findings = []
    if not matches:
        findings.append("target_not_found")
    completeness = status_for_required_fields(matches)
    if completeness != "passed" and completeness not in findings:
        findings.append(completeness)
    chunk_boundary = "passed" if matches and any(item.get("chunk_index") is not None or item.get("chunk_count") is not None for item in matches) else "chunk_boundary_ambiguity"
    if chunk_boundary != "passed" and chunk_boundary not in findings:
        findings.append(chunk_boundary)
    parent_link = "passed" if matches and any(item.get("parent_article_id") for item in matches) else "parent_article_link_gap"
    if parent_link != "passed" and parent_link not in findings:
        findings.append(parent_link)
    citation = "passed" if matches and any(item.get("citation") for item in matches) else "citation_identity_gap"
    if citation != "passed" and citation not in findings:
        findings.append(citation)
    locator = "passed" if matches and any(item.get("article_no") is not None or item.get("section_no") for item in matches) else "article_locator_gap"
    if locator != "passed" and locator not in findings:
        findings.append(locator)
    sample_mapping = "passed" if matches else "sample_case_mapping_gap"
    if sample_mapping != "passed" and sample_mapping not in findings:
        findings.append(sample_mapping)
    return {
        "case_id": target.get("case_id"),
        "target_id": target.get("target_id"),
        "expected_source": target.get("expected_source"),
        "expected_article_no": target.get("expected_article_no"),
        "expected_section_no": target.get("expected_section_no"),
        "matched_point_count": len(matches),
        "metadata_completeness_status": completeness,
        "chunk_boundary_status": chunk_boundary,
        "parent_article_link_status": parent_link,
        "citation_identity_status": citation,
        "article_locator_status": locator,
        "sample_case_mapping_status": sample_mapping,
        "sample_matches": matches[:5],
        "blocking_findings": findings,
    }


def collect_payloads(client: QdrantClient, collection: str) -> list[tuple[Any, dict[str, Any]]]:
    payloads: list[tuple[Any, dict[str, Any]]] = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=512,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payloads.append((point.id, point.payload or {}))
        if offset is None:
            break
    return payloads


def build_blocked_report(contract: dict[str, Any], reason: str, detail: str, collection: str) -> dict[str, Any]:
    targets = as_list(contract.get("snapshot_targets"))
    return {
        "version": VERSION,
        "schema_kind": "evidence_metadata_snapshot",
        "scope": "read-only evidence-level metadata snapshot",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "snapshot_gate": {
            "status": "blocked",
            "allowed_next_step": "blocked",
            "collection": collection,
            "qdrant_read_attempted": True,
            "qdrant_payload_read": False,
            "with_vectors": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": [reason],
            "error_detail": detail[:500],
        },
        "summary": {
            "status": "blocked",
            "target_count": len(targets),
            "diagnostic_row_count": 0,
            "blocked_target_count": len(targets),
            "qdrant_payload_read": False,
            "next_version_recommendation": "rerun_v0.4.11.1_after_qdrant_available",
        },
        "diagnostic_rows": [],
    }


def build_report(contract_path: Path, collection: str, host: str, port: int, timeout: float) -> dict[str, Any]:
    contract = load_json(contract_path)
    targets = as_list(contract.get("snapshot_targets"))
    contract_gate = as_dict(contract.get("contract_gate"))
    if contract.get("version") != "0.4.11.0" or contract.get("schema_kind") != "evidence_metadata_snapshot_contract":
        return build_blocked_report(contract, "contract_version_or_schema_mismatch", "Contract report is not v0.4.11.0 evidence_metadata_snapshot_contract.", collection)
    if contract_gate.get("status") != "ready_for_evidence_metadata_snapshot_runner":
        return build_blocked_report(contract, "contract_not_ready", str(contract_gate.get("blockers", [])), collection)

    try:
        client = connect_client(host, port, timeout)
        payloads = collect_payloads(client, collection)
    except Exception as exc:  # pragma: no cover - exercised through tests with fake clients
        return build_blocked_report(contract, "qdrant_unavailable", f"{type(exc).__name__}: {exc}", collection)

    rows = []
    for target in targets:
        matches = []
        for point_id, payload in payloads:
            metadata = as_dict(payload.get("metadata"))
            if target_matches(target, metadata):
                matches.append(summarize_match(point_id, payload))
        rows.append(diagnostic_row(target, matches))

    blocked_rows = [row for row in rows if row["blocking_findings"]]
    status = "completed_read_only_evidence_metadata_snapshot" if not blocked_rows else "completed_with_metadata_findings"
    return {
        "version": VERSION,
        "schema_kind": "evidence_metadata_snapshot",
        "scope": "read-only evidence-level metadata snapshot",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "snapshot_gate": {
            "status": status,
            "allowed_next_step": "evidence_metadata_snapshot_gate",
            "collection": collection,
            "qdrant_read_attempted": True,
            "qdrant_payload_read": True,
            "with_vectors": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": [],
        },
        "summary": {
            "status": status,
            "target_count": len(targets),
            "diagnostic_row_count": len(rows),
            "blocked_target_count": len(blocked_rows),
            "qdrant_payload_read": True,
            "scanned_point_count": len(payloads),
            "next_version_recommendation": "v0.4.11.2 evidence metadata snapshot gate",
        },
        "diagnostic_rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("snapshot_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.11.1 Evidence Metadata Snapshot",
        "",
        "This report is generated by a read-only Qdrant payload snapshot runner. It does not read vectors or authorize data fixes.",
        "",
        "## Overview",
        "",
        f"- Snapshot status: `{gate.get('status')}`",
        f"- Collection: `{gate.get('collection')}`",
        f"- Qdrant payload read: {summary.get('qdrant_payload_read')}",
        f"- Diagnostic rows: {summary.get('diagnostic_row_count')}",
        f"- Blocked targets: {summary.get('blocked_target_count')}",
        f"- Recommended next: `{summary.get('next_version_recommendation')}`",
        "",
        "## Boundaries",
        "",
        "- Payload-only Qdrant scroll; vectors are disabled.",
        "- No RAG query, embedding call, LLM call, full eval, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change.",
        "- If Qdrant is unavailable, this report is intentionally blocked.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--host", default=env_value("QDRANT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(env_value("QDRANT_PORT", "6333")))
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    parser.add_argument("--allow-blocked-output", action="store_true", help="Return 0 after writing a blocked diagnostic report.")
    args = parser.parse_args()
    report = build_report(args.contract, args.collection, args.host, args.port, args.timeout)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    status = report["summary"]["status"]
    print(
        "Evidence metadata snapshot built: "
        f"{status}, {report['summary'].get('diagnostic_row_count')} rows"
    )
    if status == "blocked" and not args.allow_blocked_output:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
