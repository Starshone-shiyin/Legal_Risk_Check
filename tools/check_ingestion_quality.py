"""Check ingestion quality before or after adding knowledge files.

The checker calls src.rag.ingestion.load_txt directly, so it validates the same
Document objects that would be written into Qdrant.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.ingestion import load_txt


DEFAULT_MANIFEST_PATH = Path("knowledge_manifest.json")
DEFAULT_OUTPUT_PATH = Path("tests/ingestion_quality_report.json")
MIN_CHINESE_RATIO = 0.45


def load_manifest(path: Path) -> dict[str, Any]:
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


def chinese_ratio(text: str) -> float:
    visible = re.sub(r"\s+", "", text)
    if not visible:
        return 0.0
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", visible))
    return chinese_count / len(visible)


def suspicious_noise(text: str) -> list[str]:
    issues = []
    if "�" in text:
        issues.append("contains_replacement_char")
    # Common mojibake markers from UTF-8/GBK mis-decoding; these are intentional
    # detection tokens, not source-code corruption.
    if re.search(r"鍥|鎴|绗|涓|瀹|鏁|鐨", text) and chinese_ratio(text) < 0.65:
        issues.append("possible_mojibake")
    if len(re.findall(r"<[^>]+>", text)) >= 5:
        issues.append("html_tags")
    if len(re.findall(r"^\s*\d+\s*$", text, flags=re.MULTILINE)) >= 5:
        issues.append("many_page_number_lines")
    if re.search(r"\.{5,}\s*\d+", text):
        issues.append("toc_leader_dots")
    return issues


def anchor_exists(anchor: dict[str, Any], docs: list) -> bool:
    for doc in docs:
        metadata = doc.metadata
        if "article_no" in anchor and metadata.get("article_no") == anchor["article_no"]:
            return True
        if "article" in anchor and metadata.get("article") == anchor["article"]:
            return True
        if "section_no" in anchor and metadata.get("section_no") == anchor["section_no"]:
            return True
    return False


def summarize_docs(docs: list) -> dict[str, Any]:
    type_counts: dict[str, int] = {}
    block_counts: dict[str, int] = {}
    article_numbers = []
    section_numbers = []
    chunk_ids = []
    qdrant_point_ids = []
    citations = 0

    for doc in docs:
        metadata = doc.metadata
        doc_type = metadata.get("type", "")
        block_type = metadata.get("block_type", "")
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        block_counts[block_type] = block_counts.get(block_type, 0) + 1
        if metadata.get("article_no") is not None:
            article_numbers.append(metadata["article_no"])
        if metadata.get("section_no"):
            section_numbers.append(metadata["section_no"])
        if metadata.get("chunk_id"):
            chunk_ids.append(metadata["chunk_id"])
        if metadata.get("qdrant_point_id") is not None:
            qdrant_point_ids.append(metadata["qdrant_point_id"])
        if metadata.get("citation"):
            citations += 1

    return {
        "document_count": len(docs),
        "type_counts": type_counts,
        "block_type_counts": block_counts,
        "article_count": len(set(article_numbers)),
        "article_no_min": min(article_numbers) if article_numbers else None,
        "article_no_max": max(article_numbers) if article_numbers else None,
        "standard_section_count": len(set(section_numbers)),
        "chunk_id_count": len(chunk_ids),
        "duplicate_chunk_id_count": len(chunk_ids) - len(set(chunk_ids)),
        "qdrant_point_id_count": len(qdrant_point_ids),
        "duplicate_qdrant_point_id_count": len(qdrant_point_ids) - len(set(qdrant_point_ids)),
        "citation_count": citations,
        "sample_citations": [
            doc.metadata.get("citation")
            for doc in docs
            if doc.metadata.get("citation")
        ][:5],
    }


def check_document(document: dict[str, Any]) -> dict[str, Any]:
    failures = []
    warnings = []
    file_path = Path(document.get("file_path", ""))

    if not file_path.exists():
        return {
            "source": document.get("source", ""),
            "passed": False,
            "failures": [f"file_not_found: {file_path}"],
            "warnings": [],
            "summary": {},
        }

    raw_text = file_path.read_text(encoding="utf-8")
    ratio = chinese_ratio(raw_text)
    if ratio < MIN_CHINESE_RATIO:
        failures.append(f"low_chinese_ratio: {ratio:.2f}")

    warnings.extend(suspicious_noise(raw_text))

    docs = load_txt(
        str(file_path),
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
    summary = summarize_docs(docs)

    if not docs:
        failures.append("no_documents_generated")
    if summary["chunk_id_count"] != summary["document_count"]:
        failures.append("missing_chunk_id")
    if summary["qdrant_point_id_count"] != summary["document_count"]:
        failures.append("missing_qdrant_point_id")
    if summary["duplicate_chunk_id_count"] > 0:
        failures.append(f"duplicate_chunk_id: {summary['duplicate_chunk_id_count']}")
    if summary["duplicate_qdrant_point_id_count"] > 0:
        failures.append(f"duplicate_qdrant_point_id: {summary['duplicate_qdrant_point_id_count']}")
    if summary["citation_count"] == 0:
        failures.append("no_citations_generated")

    document_type = document.get("document_type")
    if document_type == "标准":
        if summary["standard_section_count"] == 0:
            failures.append("no_standard_sections_detected")
    else:
        if summary["article_count"] == 0:
            failures.append("no_articles_detected")

    missing_anchors = [
        anchor
        for anchor in document.get("expected_anchors", [])
        if not anchor_exists(anchor, docs)
    ]
    if missing_anchors:
        failures.append(f"missing_expected_anchors: {missing_anchors}")

    return {
        "source": document.get("source", ""),
        "file_path": str(file_path),
        "passed": not failures,
        "failures": failures,
        "warnings": sorted(set(warnings)),
        "chinese_ratio": round(ratio, 4),
        "summary": summary,
    }


def print_document_report(report: dict[str, Any]):
    status = "PASS" if report["passed"] else "FAIL"
    print(f"[{status}] {report['source']}")
    if report.get("failures"):
        print(f"  failures: {report['failures']}")
    if report.get("warnings"):
        print(f"  warnings: {report['warnings']}")
    summary = report.get("summary", {})
    if summary:
        print(
            "  docs/articles/sections/citations: "
            f"{summary.get('document_count')}/"
            f"{summary.get('article_count')}/"
            f"{summary.get('standard_section_count')}/"
            f"{summary.get('citation_count')}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check ingestion quality for manifest documents.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH, help="知识库清单路径")
    parser.add_argument("--source", action="append", help="按 source 筛选，可重复或逗号分隔")
    parser.add_argument("--domain", action="append", help="按 domain 筛选，可重复或逗号分隔")
    parser.add_argument("--category", action="append", help="按 category 筛选，可重复或逗号分隔")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="保存 JSON 报告路径")
    parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    documents = select_documents(
        manifest,
        sources=parse_csv(args.source),
        domains=parse_csv(args.domain),
        categories=parse_csv(args.category),
    )

    reports = []
    for document in documents:
        report = check_document(document)
        reports.append(report)
        print_document_report(report)
        if args.fail_fast and not report["passed"]:
            break

    passed_count = sum(1 for report in reports if report["passed"])
    summary = {
        "manifest": str(args.manifest),
        "total": len(reports),
        "passed": passed_count,
        "failed": len(reports) - passed_count,
        "reports": reports,
    }
    print(f"\nSummary: {passed_count}/{len(reports)} passed")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"报告已保存: {args.output}")

    return 0 if passed_count == len(reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
