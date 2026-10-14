"""Build a non-production Qdrant collection from verified manifest entries."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.vectorstore import ensure_collection_with_sparse, get_qdrant_client
from src.rag.ingestion import ingest, load_txt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_COLLECTION = "legal_knowledge"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_entries(manifest_path: Path, include_pending_effective: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for entry in manifest.get("documents", []):
        if entry.get("legal_effect") == "待生效" and not include_pending_effective:
            excluded.append(entry)
        else:
            included.append(entry)
    return included, excluded


def check_target_collection(client: Any, collection: str) -> None:
    if collection == PRODUCTION_COLLECTION:
        raise ValueError("staging collection must not reuse legal_knowledge")
    try:
        count = client.count(collection_name=collection, exact=False).count
    except Exception:
        return
    if count:
        raise ValueError(f"target collection {collection!r} already contains {count} points")


def entry_options(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": entry["source"],
        "law_level": entry["law_level"],
        "category": entry["category"],
        "version": entry["version"],
        "document_type": entry["document_type"],
        "authority_level": entry["authority_level"],
        "jurisdiction": entry["jurisdiction"],
        "issuing_authority": entry["issuing_authority"],
        "legal_effect": entry.get("legal_effect"),
        "standard_type": entry.get("standard_type"),
        "case_type": entry.get("case_type"),
        "patent_type": entry.get("patent_type"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True, help="new non-production Qdrant collection name")
    parser.add_argument("--manifest", type=Path, default=Path("knowledge_manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("tests/legal_staging_collection_report.json"))
    parser.add_argument("--include-pending-effective", action="store_true")
    parser.add_argument("--execute", action="store_true", help="perform Qdrant writes; omit for a local dry run")
    args = parser.parse_args()

    manifest_path = (PROJECT_ROOT / args.manifest).resolve()
    entries, excluded = load_entries(manifest_path, args.include_pending_effective)
    report: dict[str, Any] = {
        "schema_version": "legal-staging-collection-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "dry_run",
        "target_collection": args.collection,
        "production_collection_untouched": PRODUCTION_COLLECTION,
        "manifest_sha256": sha256_file(manifest_path),
        "included_sources": [entry["source"] for entry in entries],
        "excluded_pending_effective": [
            {"source": entry["source"], "effective_date": entry.get("effective_date")}
            for entry in excluded
        ],
        "sources": [],
    }

    for entry in entries:
        source_path = (PROJECT_ROOT / entry["file_path"]).resolve()
        docs = load_txt(str(source_path), **entry_options(entry))
        report["sources"].append({
            "source": entry["source"],
            "file_path": entry["file_path"],
            "file_sha256": sha256_file(source_path),
            "local_chunk_count": len(docs),
            "legal_effect": entry.get("legal_effect", ""),
        })

    report["local_chunk_count"] = sum(row["local_chunk_count"] for row in report["sources"])
    if args.execute:
        client = get_qdrant_client()
        check_target_collection(client, args.collection)
        source_snapshot = client.create_snapshot(collection_name=PRODUCTION_COLLECTION)
        report["production_snapshot"] = {
            "collection": PRODUCTION_COLLECTION,
            "name": source_snapshot.name,
        }
        ensure_collection_with_sparse(args.collection)
        for index, entry in enumerate(entries, start=1):
            print(f"[{index}/{len(entries)}] ingesting {entry['source']}", flush=True)
            ingest(
                str((PROJECT_ROOT / entry["file_path"]).resolve()),
                collection_name=args.collection,
                **entry_options(entry),
            )
        report["status"] = "completed"
        report["target_point_count"] = client.count(collection_name=args.collection, exact=False).count

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "target_collection": args.collection,
        "local_chunk_count": report["local_chunk_count"],
        "excluded_pending_effective": report["excluded_pending_effective"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
