"""Check Qdrant index integrity after rebuild.

This validates the persisted collection, not just local load_txt() output.
It catches sparse-only empty payload points, missing stable chunk ids, and
source count drift against knowledge_manifest.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.vectorstore import get_qdrant_client
from src.rag.bm25_encoder import get_bm25_encoder
from src.rag.ingestion import load_txt


DEFAULT_COLLECTION = "legal_knowledge"
DEFAULT_MANIFEST = Path("knowledge_manifest.json")
DEFAULT_OUTPUT = Path("tests/qdrant_index_integrity_report.json")


def expected_counts_from_manifest(manifest_path: Path) -> dict[str, int]:
    if not manifest_path.exists():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for entry in manifest.get("documents", []):
        file_path = Path(entry.get("file_path", ""))
        if not file_path.exists():
            continue
        docs = load_txt(
            str(file_path),
            source_name=entry.get("source"),
            law_level=entry.get("law_level"),
            category=entry.get("category", "数据合规"),
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
        counts[entry.get("source", file_path.stem)] = len(docs)
    return counts


def scan_collection(collection_name: str) -> dict[str, Any]:
    client = get_qdrant_client()
    offset = None
    stats = {
        "total_scanned": 0,
        "empty_payload": 0,
        "missing_metadata": 0,
        "missing_source": 0,
        "missing_chunk_id": 0,
        "missing_qdrant_point_id": 0,
        "missing_bm25_vector": 0,
        "unindexable_bm25_chunks": 0,
        "duplicate_chunk_id_count": 0,
        "source_counts": {},
        "sample_failures": [],
        "sample_warnings": [],
    }
    bm25 = get_bm25_encoder()
    chunk_ids = []
    source_counts: Counter[str] = Counter()

    while True:
        points, offset = client.scroll(
            collection_name=collection_name,
            limit=500,
            offset=offset,
            with_payload=True,
            with_vectors=["bm25"],
        )
        for point in points:
            stats["total_scanned"] += 1
            payload = point.payload or {}
            metadata = payload.get("metadata") or {}
            vector = point.vector or {}
            failures = []

            if not payload:
                stats["empty_payload"] += 1
                failures.append("empty_payload")
            if not metadata:
                stats["missing_metadata"] += 1
                failures.append("missing_metadata")
            if not metadata.get("source"):
                stats["missing_source"] += 1
                failures.append("missing_source")
            else:
                source_counts[metadata["source"]] += 1
            if not metadata.get("chunk_id"):
                stats["missing_chunk_id"] += 1
                failures.append("missing_chunk_id")
            else:
                chunk_ids.append(metadata["chunk_id"])
            if metadata.get("qdrant_point_id") is None:
                stats["missing_qdrant_point_id"] += 1
                failures.append("missing_qdrant_point_id")
            if not (isinstance(vector, dict) and vector.get("bm25")):
                content = payload.get("page_content") or payload.get("content") or ""
                sparse_indices, _ = bm25.encode(content)
                if sparse_indices:
                    stats["missing_bm25_vector"] += 1
                    failures.append("missing_bm25_vector")
                else:
                    stats["unindexable_bm25_chunks"] += 1
                    if len(stats["sample_warnings"]) < 20:
                        stats["sample_warnings"].append({
                            "id": str(point.id),
                            "warning": "unindexable_bm25_chunk",
                            "source": metadata.get("source", ""),
                            "citation": metadata.get("citation", ""),
                            "content_preview": content[:80],
                        })

            if failures and len(stats["sample_failures"]) < 20:
                stats["sample_failures"].append({
                    "id": str(point.id),
                    "failures": failures,
                    "source": metadata.get("source", ""),
                    "citation": metadata.get("citation", ""),
                })

        if offset is None:
            break

    stats["duplicate_chunk_id_count"] = len(chunk_ids) - len(set(chunk_ids))
    stats["source_counts"] = dict(sorted(source_counts.items()))
    return stats


def build_report(collection_name: str, manifest_path: Path) -> dict[str, Any]:
    actual = scan_collection(collection_name)
    expected_counts = expected_counts_from_manifest(manifest_path)
    failures = []

    for key in [
        "empty_payload",
        "missing_metadata",
        "missing_source",
        "missing_chunk_id",
        "missing_qdrant_point_id",
        "missing_bm25_vector",
        "duplicate_chunk_id_count",
    ]:
        if actual[key]:
            failures.append(f"{key}: {actual[key]}")

    count_mismatches = {}
    for source, expected in expected_counts.items():
        actual_count = actual["source_counts"].get(source, 0)
        if actual_count != expected:
            count_mismatches[source] = {"expected": expected, "actual": actual_count}
    if count_mismatches:
        failures.append("source_count_mismatch")

    return {
        "collection": collection_name,
        "passed": not failures,
        "failures": failures,
        "actual": actual,
        "expected_source_counts": expected_counts,
        "count_mismatches": count_mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check persisted Qdrant index integrity.")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_report(args.collection, args.manifest)
    status = "PASS" if report["passed"] else "FAIL"
    actual = report["actual"]
    print(f"[{status}] {args.collection}: {actual['total_scanned']} points")
    print(
        "  empty_payload={empty_payload}, missing_chunk_id={missing_chunk_id}, "
        "missing_qdrant_point_id={missing_qdrant_point_id}, missing_bm25_vector={missing_bm25_vector}, "
        "unindexable_bm25_chunks={unindexable_bm25_chunks}, "
        "duplicate_chunk_id_count={duplicate_chunk_id_count}".format(**actual)
    )
    if report["count_mismatches"]:
        print(f"  count mismatches: {report['count_mismatches']}")
    if report["failures"]:
        print(f"  failures: {report['failures']}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"报告已保存: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
