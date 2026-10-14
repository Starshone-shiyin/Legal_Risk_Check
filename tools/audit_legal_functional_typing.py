"""Audit legal functional typing coverage for ingested knowledge files.

This is an offline diagnostics tool. It reads knowledge files through the same
loader used by ingestion, classifies chunks with deterministic functional-type
cues, and writes a report. It does not write Qdrant data or affect rag_query.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.ingestion import load_txt
from src.rag.legal_functional_typing import (
    FUNCTION_DEFINITION,
    FUNCTION_UNCLASSIFIED,
    classify_legal_function,
    load_functional_type_config,
    operative_support_types,
)


DEFAULT_MANIFEST_PATH = Path("knowledge_manifest.json")
DEFAULT_CONFIG_PATH = Path("config/legal_functional_types.json")
DEFAULT_OUTPUT_PATH = Path("tests/legal_functional_typing_report.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_matches(expected: str, actual: str) -> bool:
    expected = str(expected or "").strip()
    actual = str(actual or "").strip()
    return bool(expected and actual and (expected == actual or expected in actual or actual in expected))


def parse_csv(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def select_documents(
    manifest: dict[str, Any],
    sources: set[str],
    domains: set[str],
    categories: set[str],
) -> list[dict[str, Any]]:
    selected = []
    for document in manifest.get("documents", []):
        if sources and not any(source_matches(source, document.get("source", "")) for source in sources):
            continue
        if domains and document.get("domain") not in domains:
            continue
        if categories and document.get("category") not in categories:
            continue
        selected.append(document)
    return selected


def document_chunks(document: dict[str, Any]) -> list:
    return load_txt(
        str(document.get("file_path", "")),
        source_name=document.get("source"),
        law_level=document.get("law_level"),
        category=document.get("category", "数据合规"),
        version=document.get("version", ""),
        document_type=document.get("document_type"),
        authority_level=document.get("authority_level"),
        jurisdiction=document.get("jurisdiction"),
        issuing_authority=document.get("issuing_authority"),
        legal_effect=document.get("legal_effect"),
        standard_type=document.get("standard_type"),
        case_type=document.get("case_type"),
        patent_type=document.get("patent_type"),
    )


def audit_document(
    document: dict[str, Any],
    config: dict[str, Any],
    max_samples: int = 5,
) -> dict[str, Any]:
    path = Path(document.get("file_path", ""))
    if not path.exists():
        return {
            "source": document.get("source", ""),
            "file_path": str(path),
            "passed": False,
            "failures": [f"file_not_found: {path}"],
            "warnings": [],
            "total_chunks": 0,
            "functional_type_counts": {},
            "review_reasons": ["Knowledge file is missing."],
            "review_required": True,
            "sample_unclassified": [],
        }

    docs = document_chunks(document)
    counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    samples_unclassified = []
    samples_by_type: dict[str, list[dict[str, Any]]] = {}
    support_types = operative_support_types(config)

    for doc in docs:
        result = classify_legal_function(doc.page_content, doc.metadata, config)
        counts[result.functional_type] += 1
        confidence_counts[result.confidence] += 1
        sample = {
            "citation": doc.metadata.get("citation"),
            "article_no": doc.metadata.get("article_no"),
            "section_no": doc.metadata.get("section_no"),
            "matched_rule": result.matched_rule,
            "matched_terms": list(result.matched_terms),
            "text_preview": doc.page_content[:160],
        }
        samples_by_type.setdefault(result.functional_type, [])
        if len(samples_by_type[result.functional_type]) < max_samples:
            samples_by_type[result.functional_type].append(sample)
        if result.functional_type == FUNCTION_UNCLASSIFIED and len(samples_unclassified) < max_samples:
            samples_unclassified.append(sample)

    total = len(docs)
    unclassified_count = counts.get(FUNCTION_UNCLASSIFIED, 0)
    operative_count = sum(counts.get(function_type, 0) for function_type in support_types)
    definition_count = counts.get(FUNCTION_DEFINITION, 0)
    unclassified_ratio = unclassified_count / total if total else 1.0
    operative_ratio = operative_count / total if total else 0.0
    review_reasons = []

    if total == 0:
        review_reasons.append("No chunks were generated from this document.")
    if unclassified_ratio > 0.35:
        review_reasons.append("More than 35% of chunks are unclassified.")
    if definition_count and not operative_count:
        review_reasons.append("Document has definition chunks but no operative support chunks.")
    if document.get("document_type") != "标准" and operative_count == 0:
        review_reasons.append("Legal/regulatory document has no operative support chunks.")

    return {
        "source": document.get("source", ""),
        "file_path": str(path),
        "domain": document.get("domain"),
        "category": document.get("category"),
        "document_type": document.get("document_type"),
        "passed": not review_reasons,
        "failures": [],
        "warnings": [],
        "total_chunks": total,
        "functional_type_counts": dict(sorted(counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "operative_support_chunks": operative_count,
        "unclassified_chunks": unclassified_count,
        "unclassified_ratio": round(unclassified_ratio, 3),
        "operative_support_ratio": round(operative_ratio, 3),
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "sample_unclassified": samples_unclassified,
        "sample_by_functional_type": {
            key: value
            for key, value in sorted(samples_by_type.items())
        },
    }


def build_summary(document_reports: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts: Counter[str] = Counter()
    domain_summary: dict[str, Counter] = {}
    review_documents = []
    total_chunks = 0
    unclassified_chunks = 0
    operative_chunks = 0

    for report in document_reports:
        total_chunks += int(report.get("total_chunks") or 0)
        unclassified_chunks += int(report.get("unclassified_chunks") or 0)
        operative_chunks += int(report.get("operative_support_chunks") or 0)
        for function_type, count in (report.get("functional_type_counts") or {}).items():
            type_counts[function_type] += int(count)
        domain = report.get("domain") or "unknown"
        domain_counter = domain_summary.setdefault(domain, Counter())
        domain_counter["documents"] += 1
        domain_counter["chunks"] += int(report.get("total_chunks") or 0)
        if report.get("review_required"):
            domain_counter["review_documents"] += 1
            review_documents.append({
                "source": report.get("source"),
                "domain": domain,
                "review_reasons": report.get("review_reasons") or [],
                "unclassified_ratio": report.get("unclassified_ratio"),
                "operative_support_ratio": report.get("operative_support_ratio"),
            })

    return {
        "total_documents": len(document_reports),
        "review_documents": len(review_documents),
        "total_chunks": total_chunks,
        "unclassified_chunks": unclassified_chunks,
        "operative_support_chunks": operative_chunks,
        "unclassified_ratio": round(unclassified_chunks / total_chunks, 3) if total_chunks else 1.0,
        "operative_support_ratio": round(operative_chunks / total_chunks, 3) if total_chunks else 0.0,
        "functional_type_summary": dict(sorted(type_counts.items())),
        "per_domain_summary": {
            domain: dict(counter)
            for domain, counter in sorted(domain_summary.items())
        },
        "manual_review_documents": review_documents,
    }


def build_report(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    sources: set[str] | None = None,
    domains: set[str] | None = None,
    categories: set[str] | None = None,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    config = load_functional_type_config(str(config_path))
    selected = select_documents(manifest, sources or set(), domains or set(), categories or set())
    document_reports = [audit_document(document, config) for document in selected]
    return {
        "version": config.get("version") or "0.4.7.2",
        "scope": "offline legal functional typing audit",
        "inputs": {
            "manifest": str(manifest_path),
            "functional_type_config": str(config_path),
            "sources": sorted(sources or []),
            "domains": sorted(domains or []),
            "categories": sorted(categories or []),
        },
        "summary": build_summary(document_reports),
        "documents": document_reports,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit legal functional typing coverage for knowledge files.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--source", action="append", help="Filter by source; repeat or comma-separate values.")
    parser.add_argument("--domain", action="append", help="Filter by manifest domain; repeat or comma-separate values.")
    parser.add_argument("--category", action="append", help="Filter by manifest category; repeat or comma-separate values.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        manifest_path=args.manifest,
        config_path=args.config,
        sources=parse_csv(args.source),
        domains=parse_csv(args.domain),
        categories=parse_csv(args.category),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Legal functional typing audit completed: "
        f"{summary['total_documents']} documents, {summary['total_chunks']} chunks, "
        f"{summary['review_documents']} review documents"
    )
    print(
        "Functional typing coverage: "
        f"unclassified_ratio={summary['unclassified_ratio']}, "
        f"operative_support_ratio={summary['operative_support_ratio']}"
    )
    if args.fail_on_review and summary["review_documents"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
