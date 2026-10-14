"""Validate the rebuilt production collection with read-only Qdrant checks."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VERSION = "0.4.14.29"
DEFAULT_COLLECTION = "legal_knowledge"
DEFAULT_EXECUTION_REPORT_PATH = Path("tests/production_rebuild_execution_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/production_rebuild_post_validation_report.json")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_payload_metadata(collection_name: str = DEFAULT_COLLECTION, scan_limit: int = 500) -> dict[str, Any]:
    from src.core.vectorstore import get_qdrant_client

    client = get_qdrant_client()
    info = client.get_collection(collection_name)
    offset = None
    scanned = 0
    block_type_counts: Counter[str] = Counter()
    missing_chunk_fields: Counter[str] = Counter()
    observed_chunk_fields: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()

    while scanned < scan_limit:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            limit=min(100, scan_limit - scanned),
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break
        for point in points:
            metadata = (point.payload or {}).get("metadata", {})
            block_type = metadata.get("block_type") or "(missing)"
            block_type_counts[block_type] += 1
            source_counts[metadata.get("source") or "(missing)"] += 1
            if block_type in {"article", "paragraph", "item", "standard_section"}:
                if "chunk_index" in metadata and "chunk_count" in metadata:
                    observed_chunk_fields[block_type] += 1
                else:
                    missing_chunk_fields[block_type] += 1
            scanned += 1
        if next_offset is None:
            break
        offset = next_offset

    return {
        "collection_name": collection_name,
        "points_count": getattr(info, "points_count", None),
        "scanned_points": scanned,
        "block_type_counts": dict(block_type_counts),
        "source_count": len(source_counts),
        "observed_chunk_fields": dict(observed_chunk_fields),
        "missing_chunk_fields": dict(missing_chunk_fields),
    }


def build_post_validation_report(
    execution_report_path: Path = DEFAULT_EXECUTION_REPORT_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    scan_limit: int = 500,
) -> dict[str, Any]:
    execution_report = load_json(execution_report_path)
    validation = validate_payload_metadata(collection_name=collection_name, scan_limit=scan_limit)
    blockers = []
    if execution_report.get("summary", {}).get("execution_status") != "succeeded":
        blockers.append("execution_report_not_succeeded")
    if validation.get("points_count") != execution_report.get("after_snapshot", {}).get("points_count"):
        blockers.append("points_count_mismatch")
    if validation.get("missing_chunk_fields"):
        blockers.append("chunk_fields_missing_in_scanned_structured_blocks")
    if not validation.get("observed_chunk_fields"):
        blockers.append("chunk_fields_not_observed")

    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_post_validation_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "execution_report_path": str(execution_report_path),
            "target_collection": collection_name,
            "scan_limit": scan_limit,
        },
        "validation": validation,
        "summary": {
            "status": "passed" if not blockers else "failed",
            "blockers": blockers,
            "full_eval": "not_run",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate rebuilt production collection with read-only checks.")
    parser.add_argument("--execution-report", type=Path, default=DEFAULT_EXECUTION_REPORT_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--scan-limit", type=int, default=500)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_post_validation_report(
        execution_report_path=args.execution_report,
        collection_name=args.collection,
        scan_limit=args.scan_limit,
    )
    write_json(args.output, report)
    print(f"Production rebuild post-validation completed: {report['summary']['status']}, output={args.output}")
    return 0 if report["summary"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
