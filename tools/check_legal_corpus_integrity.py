"""Check local legal corpus integrity before corpus expansion.

The checker is intentionally offline: it reads knowledge_manifest.json and
local text files, then reuses src.rag.ingestion.load_txt to validate generated
Document metadata. It does not access Qdrant, RAG, rerankers, or LLMs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.ingestion import load_txt


DEFAULT_MANIFEST = Path("knowledge_manifest.json")
DEFAULT_KNOWLEDGE_ROOT = Path("src/knowledge")
DEFAULT_OUTPUT = Path("tests/legal_corpus_integrity_v0.4.18.1_report.json")

REQUIRED_MANIFEST_FIELDS = [
    "source",
    "file_path",
    "document_type",
    "law_level",
    "authority_level",
    "jurisdiction",
    "issuing_authority",
    "category",
    "domain",
    "version",
    "effective_date",
]

REQUIRED_GENERATED_METADATA = [
    "source",
    "document_type",
    "law_level",
    "authority_level",
    "jurisdiction",
    "issuing_authority",
    "category",
    "version",
    "chunk_id",
    "qdrant_point_id",
]

CHUNKED_BLOCK_TYPES = {"article", "paragraph", "item", "standard_section"}
VERSION_PATTERN = re.compile(r"^\d{4}(?:[-/].+)?$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def normalize_path(path: Path) -> str:
    return path.as_posix()


def anchor_exists(anchor: dict[str, Any], docs: list[Any]) -> bool:
    for doc in docs:
        metadata = doc.metadata
        if "article_no" in anchor and metadata.get("article_no") == anchor["article_no"]:
            return True
        if "article" in anchor and metadata.get("article") == anchor["article"]:
            return True
        if "section_no" in anchor and metadata.get("section_no") == anchor["section_no"]:
            return True
    return False


def issue(issue_type: str, severity: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": issue_type,
        "severity": severity,
        "message": message,
        "details": details or {},
    }


def load_entry_documents(entry: dict[str, Any], file_path: Path) -> list[Any]:
    return load_txt(
        str(file_path),
        source_name=entry.get("source"),
        law_level=entry.get("law_level"),
        category=entry.get("category", ""),
        version=entry.get("version", ""),
        document_type=entry.get("document_type"),
        authority_level=entry.get("authority_level"),
        jurisdiction=entry.get("jurisdiction"),
        issuing_authority=entry.get("issuing_authority"),
        legal_effect=entry.get("legal_effect"),
        standard_type=entry.get("standard_type"),
        case_type=entry.get("case_type"),
        patent_type=entry.get("patent_type"),
    )


def summarize_generated_docs(docs: list[Any]) -> dict[str, Any]:
    block_counts: Counter[str] = Counter()
    article_numbers: set[int] = set()
    section_numbers: set[str] = set()
    chunk_ids = []
    qdrant_point_ids = []
    citations = 0

    for doc in docs:
        metadata = doc.metadata
        block_counts[str(metadata.get("block_type", ""))] += 1
        if metadata.get("article_no") is not None:
            article_numbers.add(metadata["article_no"])
        if metadata.get("section_no"):
            section_numbers.add(str(metadata["section_no"]))
        if metadata.get("chunk_id"):
            chunk_ids.append(metadata["chunk_id"])
        if metadata.get("qdrant_point_id") is not None:
            qdrant_point_ids.append(metadata["qdrant_point_id"])
        if metadata.get("citation"):
            citations += 1

    return {
        "document_count": len(docs),
        "block_type_counts": dict(sorted(block_counts.items())),
        "article_count": len(article_numbers),
        "standard_section_count": len(section_numbers),
        "citation_count": citations,
        "chunk_id_count": len(chunk_ids),
        "duplicate_chunk_id_count": len(chunk_ids) - len(set(chunk_ids)),
        "qdrant_point_id_count": len(qdrant_point_ids),
        "duplicate_qdrant_point_id_count": len(qdrant_point_ids) - len(set(qdrant_point_ids)),
    }


def check_manifest_entry_shape(entry: dict[str, Any], index: int, knowledge_root: Path) -> list[dict[str, Any]]:
    issues = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if is_blank(entry.get(field)):
            issues.append(issue("missing_manifest_field", "error", f"missing required manifest field: {field}", {"field": field}))

    file_path_text = entry.get("file_path", "")
    file_path = Path(file_path_text)
    if file_path_text:
        if file_path.suffix.lower() != ".txt":
            issues.append(issue("non_txt_knowledge_file", "error", "manifest file_path must point to a .txt file", {"file_path": file_path_text}))
        try:
            file_path.relative_to(knowledge_root)
        except ValueError:
            issues.append(issue("file_outside_knowledge_root", "error", "manifest file_path is outside knowledge root", {"file_path": file_path_text}))

    expected_anchors = entry.get("expected_anchors", [])
    if not isinstance(expected_anchors, list):
        issues.append(issue("invalid_expected_anchors", "error", "expected_anchors must be a list"))
    elif not expected_anchors:
        issues.append(issue("empty_expected_anchors", "warning", "document has no expected anchors"))

    smoke_cases = entry.get("smoke_cases", [])
    if not isinstance(smoke_cases, list):
        issues.append(issue("invalid_smoke_cases", "error", "smoke_cases must be a list"))

    version = entry.get("version")
    if isinstance(version, str) and version and not VERSION_PATTERN.match(version):
        issues.append(issue("unusual_version_format", "warning", "version is not a simple year-like string", {"version": version}))

    effective_date = entry.get("effective_date")
    if isinstance(effective_date, str) and effective_date and not DATE_PATTERN.match(effective_date):
        issues.append(issue("invalid_effective_date_format", "error", "effective_date must use YYYY-MM-DD", {"effective_date": effective_date}))

    if is_blank(entry.get("source")):
        issues.append(issue("missing_source_identity", "error", "manifest entry source is blank", {"index": index}))

    return issues


def check_generated_docs(entry: dict[str, Any], docs: list[Any]) -> list[dict[str, Any]]:
    issues = []
    source = entry.get("source", "")

    if not docs:
        return [issue("no_generated_documents", "error", "load_txt generated no documents")]

    chunk_ids = []
    qdrant_point_ids = []
    for doc_index, doc in enumerate(docs, start=1):
        metadata = doc.metadata
        for field in REQUIRED_GENERATED_METADATA:
            if is_blank(metadata.get(field)):
                issues.append(issue(
                    "missing_generated_metadata",
                    "error",
                    f"generated document is missing metadata: {field}",
                    {"doc_index": doc_index, "field": field},
                ))
        if metadata.get("source") != source:
            issues.append(issue(
                "source_metadata_mismatch",
                "error",
                "generated document source differs from manifest source",
                {"doc_index": doc_index, "expected": source, "actual": metadata.get("source")},
            ))

        block_type = metadata.get("block_type")
        if block_type in CHUNKED_BLOCK_TYPES:
            chunk_index = metadata.get("chunk_index")
            chunk_count = metadata.get("chunk_count")
            if not isinstance(chunk_index, int) or not isinstance(chunk_count, int):
                issues.append(issue(
                    "missing_chunk_boundary",
                    "error",
                    "chunked generated document is missing integer chunk_index/chunk_count",
                    {"doc_index": doc_index, "block_type": block_type},
                ))
            elif chunk_index < 1 or chunk_count < 1 or chunk_index > chunk_count:
                issues.append(issue(
                    "invalid_chunk_boundary",
                    "error",
                    "chunk_index/chunk_count boundary is invalid",
                    {"doc_index": doc_index, "block_type": block_type, "chunk_index": chunk_index, "chunk_count": chunk_count},
                ))

            if is_blank(metadata.get("citation")):
                issues.append(issue(
                    "missing_citation",
                    "error",
                    "chunked generated document is missing citation",
                    {"doc_index": doc_index, "block_type": block_type},
                ))

        if metadata.get("chunk_id"):
            chunk_ids.append(metadata["chunk_id"])
        if metadata.get("qdrant_point_id") is not None:
            qdrant_point_ids.append(metadata["qdrant_point_id"])

    duplicate_chunk_ids = len(chunk_ids) - len(set(chunk_ids))
    if duplicate_chunk_ids:
        issues.append(issue("duplicate_chunk_id", "error", "duplicate chunk_id values within one source", {"count": duplicate_chunk_ids}))

    duplicate_point_ids = len(qdrant_point_ids) - len(set(qdrant_point_ids))
    if duplicate_point_ids:
        issues.append(issue("duplicate_qdrant_point_id", "error", "duplicate qdrant_point_id values within one source", {"count": duplicate_point_ids}))

    missing_anchors = [
        anchor for anchor in entry.get("expected_anchors", [])
        if isinstance(anchor, dict) and not anchor_exists(anchor, docs)
    ]
    if missing_anchors:
        issues.append(issue("missing_expected_anchor", "error", "one or more expected anchors were not generated", {"anchors": missing_anchors}))

    document_type = entry.get("document_type")
    summary = summarize_generated_docs(docs)
    if document_type == "标准":
        if summary["standard_section_count"] == 0:
            issues.append(issue("no_standard_sections_detected", "error", "standard document generated no standard sections"))
    else:
        if summary["article_count"] == 0:
            issues.append(issue("no_articles_detected", "error", "legal document generated no article numbers"))

    return issues


def check_entry(entry: dict[str, Any], index: int, knowledge_root: Path) -> dict[str, Any]:
    entry_issues = check_manifest_entry_shape(entry, index, knowledge_root)
    file_path = Path(entry.get("file_path", ""))
    docs = []

    if not file_path.exists():
        entry_issues.append(issue("manifest_file_not_found", "error", "manifest file_path does not exist", {"file_path": str(file_path)}))
    else:
        try:
            docs = load_entry_documents(entry, file_path)
            entry_issues.extend(check_generated_docs(entry, docs))
        except Exception as exc:  # pragma: no cover - defensive CLI surface
            entry_issues.append(issue("load_txt_exception", "error", "load_txt raised an exception", {"error": repr(exc)}))

    summary = summarize_generated_docs(docs)
    severities = Counter(item["severity"] for item in entry_issues)
    return {
        "source": entry.get("source", ""),
        "file_path": str(file_path),
        "domain": entry.get("domain", ""),
        "document_type": entry.get("document_type", ""),
        "passed": severities.get("error", 0) == 0,
        "issue_count": len(entry_issues),
        "error_count": severities.get("error", 0),
        "warning_count": severities.get("warning", 0),
        "issues": entry_issues,
        "summary": summary,
    }


def find_orphan_knowledge_files(manifest: dict[str, Any], knowledge_root: Path) -> list[str]:
    manifest_paths = {
        normalize_path(Path(entry.get("file_path", "")))
        for entry in manifest.get("documents", [])
        if entry.get("file_path")
    }
    orphan_files = []
    if not knowledge_root.exists():
        return orphan_files
    for file_path in sorted(knowledge_root.rglob("*.txt")):
        normalized = normalize_path(file_path)
        if normalized not in manifest_paths:
            orphan_files.append(normalized)
    return orphan_files


def build_report(manifest_path: Path = DEFAULT_MANIFEST, knowledge_root: Path = DEFAULT_KNOWLEDGE_ROOT) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    documents = manifest.get("documents", [])
    entries = []
    global_issues = []

    if not isinstance(documents, list):
        documents = []
        global_issues.append(issue("invalid_manifest_documents", "error", "manifest documents must be a list"))

    source_counts = Counter(str(entry.get("source", "")) for entry in documents)
    path_counts = Counter(str(entry.get("file_path", "")) for entry in documents)
    for source, count in source_counts.items():
        if source and count > 1:
            global_issues.append(issue("duplicate_manifest_source", "error", "duplicate manifest source", {"source": source, "count": count}))
    for file_path, count in path_counts.items():
        if file_path and count > 1:
            global_issues.append(issue("duplicate_manifest_file_path", "error", "duplicate manifest file_path", {"file_path": file_path, "count": count}))

    orphan_files = find_orphan_knowledge_files(manifest, knowledge_root)
    for file_path in orphan_files:
        global_issues.append(issue("orphan_knowledge_file", "error", "knowledge text file is not listed in manifest", {"file_path": file_path}))

    for index, entry in enumerate(documents, start=1):
        entries.append(check_entry(entry, index, knowledge_root))

    issue_summary: Counter[str] = Counter(item["type"] for item in global_issues)
    severity_summary: Counter[str] = Counter(item["severity"] for item in global_issues)
    per_domain: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "documents": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "warnings": 0,
        "generated_chunks": 0,
    })

    for entry in entries:
        domain = entry["domain"] or "unknown"
        per_domain[domain]["documents"] += 1
        per_domain[domain]["passed" if entry["passed"] else "failed"] += 1
        per_domain[domain]["errors"] += entry["error_count"]
        per_domain[domain]["warnings"] += entry["warning_count"]
        per_domain[domain]["generated_chunks"] += entry["summary"]["document_count"]
        for item in entry["issues"]:
            issue_summary[item["type"]] += 1
            severity_summary[item["severity"]] += 1

    high_risk_manual_review = [
        {
            "source": entry["source"],
            "domain": entry["domain"],
            "errors": entry["error_count"],
            "issues": [item["type"] for item in entry["issues"] if item["severity"] == "error"],
        }
        for entry in entries
        if entry["error_count"] > 0
    ]
    for item in global_issues:
        if item["severity"] == "error":
            high_risk_manual_review.append({
                "source": "__manifest__",
                "domain": "__global__",
                "errors": 1,
                "issues": [item["type"]],
                "details": item.get("details", {}),
            })

    total_generated = sum(entry["summary"]["document_count"] for entry in entries)
    total_errors = severity_summary.get("error", 0)
    return {
        "version": "0.4.18.1",
        "status": "passed" if total_errors == 0 else "failed",
        "scope": {
            "manifest_path": str(manifest_path),
            "knowledge_root": str(knowledge_root),
            "offline_only": True,
            "uses_load_txt": True,
            "qdrant_access": False,
            "rag_or_llm_access": False,
        },
        "summary": {
            "manifest_documents": len(documents),
            "generated_documents": total_generated,
            "passed_documents": sum(1 for entry in entries if entry["passed"]),
            "failed_documents": sum(1 for entry in entries if not entry["passed"]),
            "global_issue_count": len(global_issues),
            "error_count": total_errors,
            "warning_count": severity_summary.get("warning", 0),
            "orphan_knowledge_file_count": len(orphan_files),
        },
        "issue_type_summary": dict(sorted(issue_summary.items())),
        "severity_summary": dict(sorted(severity_summary.items())),
        "per_domain_summary": dict(sorted(per_domain.items())),
        "high_risk_manual_review": high_risk_manual_review,
        "global_issues": global_issues,
        "documents": entries,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local legal corpus integrity before corpus expansion.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--knowledge-root", type=Path, default=DEFAULT_KNOWLEDGE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.manifest, args.knowledge_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report["summary"]
    print(
        f"[{report['status'].upper()}] manifest_documents={summary['manifest_documents']}, "
        f"generated_documents={summary['generated_documents']}, "
        f"errors={summary['error_count']}, warnings={summary['warning_count']}"
    )
    if report["high_risk_manual_review"]:
        print(f"high_risk_manual_review={len(report['high_risk_manual_review'])}")
    print(f"Report saved: {args.output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
