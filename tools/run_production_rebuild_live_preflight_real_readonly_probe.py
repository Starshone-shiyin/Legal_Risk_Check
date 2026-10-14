"""Run a real read-only Qdrant probe through the live preflight scaffold.

This is the first production-chain-facing probe for the rebuild preflight path.
It reuses the project Qdrant client factory, performs only read operations, and
injects the result into the fail-closed preflight scaffold. It does not write
Qdrant, switch collections, accept authorization, run RAG, call an LLM, run full
eval, or execute production rebuild.
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

from src.core.vectorstore import get_qdrant_client
from tools._shared.layout import legacy_report_path
from tools.run_production_rebuild_live_preflight import build_live_preflight_report


VERSION = "0.4.14.23"

DEFAULT_COLLECTION = "legal_knowledge"
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_live_preflight_real_readonly_probe_report.json")
READ_ONLY_EXPOSED_METHODS = ["get_collection", "count", "scroll"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _get_nested_attr(value: Any, path: tuple[str, ...]) -> Any:
    current = value
    for name in path:
        current = getattr(current, name, None)
        if current is None:
            return None
    return current


def _safe_model_dump(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "dict"):
        dumped = value.dict()
        return dumped if isinstance(dumped, dict) else {}
    return {}


def build_real_qdrant_readonly_probe(client: Any | None = None):
    """Return a probe callable that performs read-only Qdrant checks."""

    def probe(collection_name: str) -> dict[str, Any]:
        active_client = client or get_qdrant_client()
        collection_info = active_client.get_collection(collection_name)
        count_result = active_client.count(collection_name=collection_name, exact=False)
        points, _offset = active_client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        params = _get_nested_attr(collection_info, ("config", "params"))
        payload_keys: list[str] = []
        metadata_keys: list[str] = []
        if points:
            payload = points[0].payload or {}
            payload_keys = sorted(str(key) for key in payload.keys())
            metadata = payload.get("metadata")
            if isinstance(metadata, dict):
                metadata_keys = sorted(str(key) for key in metadata.keys())

        return {
            "collection_name": collection_name,
            "reachable": True,
            "points_count": getattr(count_result, "count", None),
            "vectors_config_present": bool(_safe_model_dump(getattr(params, "vectors", None))),
            "sparse_vectors_config_present": bool(_safe_model_dump(getattr(params, "sparse_vectors", None))),
            "sample_payload_observed": bool(points),
            "sample_payload_keys": payload_keys,
            "sample_metadata_keys": metadata_keys,
            "exposed_methods": READ_ONLY_EXPOSED_METHODS,
        }

    return probe


def build_report(
    *,
    collection_name: str,
    authorization_status: str,
    authorization_reference: str | None = None,
    backup_or_snapshot_reference: str | None,
    source_lineage_reference: str | None,
    client: Any | None = None,
    clock=utc_now,
) -> dict[str, Any]:
    probe = build_real_qdrant_readonly_probe(client)
    report = build_live_preflight_report(
        authorization_record={
            "authorization_status": authorization_status,
            "authorization_reference": authorization_reference,
        },
        target_collection=collection_name,
        backup_or_snapshot_reference=backup_or_snapshot_reference,
        source_lineage_reference=source_lineage_reference,
        qdrant_readonly_probe=probe,
        clock=clock,
    )
    report["version"] = VERSION
    report["schema_kind"] = "production_rebuild_live_preflight_real_readonly_probe_report"
    report["scope"] = "real Qdrant read-only probe injected into the fail-closed preflight scaffold"
    report["runner_version"] = "0.4.14.21"
    report["guardrails"].update({
        "real_qdrant_readonly_probe": True,
        "qdrant_read_methods_only": READ_ONLY_EXPOSED_METHODS,
        "qdrant_write": "disallowed",
        "collection_switch": "disallowed",
        "production_rebuild": "disallowed",
        "rag_query_integration": "disallowed",
        "llm_access": "disallowed",
        "full_eval": "not_run",
    })
    report["summary"]["real_qdrant_readonly_probe"] = True
    report["summary"]["qdrant_write_allowed"] = False
    report["summary"]["production_rebuild_allowed"] = False
    report["summary"]["authorization_granted"] = False
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a real read-only Qdrant probe through the preflight scaffold.")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--authorization-status", default="not_collected")
    parser.add_argument("--authorization-reference", default=None)
    parser.add_argument("--backup-or-snapshot-reference", default=None)
    parser.add_argument("--source-lineage-reference", default="ingestion-metadata-source-patch-v0.4.13.8")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--allow-blocked-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(
            collection_name=args.collection,
            authorization_status=args.authorization_status,
            authorization_reference=args.authorization_reference,
            backup_or_snapshot_reference=args.backup_or_snapshot_reference,
            source_lineage_reference=args.source_lineage_reference,
        )
    except Exception as exc:
        report = {
            "version": VERSION,
            "schema_kind": "production_rebuild_live_preflight_real_readonly_probe_report",
            "scope": "real Qdrant read-only probe injected into the fail-closed preflight scaffold",
            "generated_at": utc_now(),
            "inputs": {
                "target_collection": args.collection,
                "authorization_status": args.authorization_status,
                "backup_or_snapshot_reference_present": bool(args.backup_or_snapshot_reference),
                "source_lineage_reference_present": bool(args.source_lineage_reference),
            },
            "probe_error": str(exc),
            "guardrails": {
                "real_qdrant_readonly_probe": True,
                "qdrant_write": "disallowed",
                "collection_switch": "disallowed",
                "production_rebuild": "disallowed",
                "rag_query_integration": "disallowed",
                "llm_access": "disallowed",
                "full_eval": "not_run",
            },
            "summary": {
                "preflight_status": "blocked",
                "blockers": ["real_qdrant_readonly_probe_error"],
                "real_qdrant_readonly_probe": True,
                "qdrant_access_allowed": True,
                "qdrant_write_allowed": False,
                "production_rebuild_allowed": False,
                "authorization_granted": False,
                "full_eval": "not_run",
            },
        }
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Production rebuild live preflight real read-only probe: "
        f"{summary['preflight_status']}, blockers={len(summary.get('blockers', []))}"
    )
    if summary["preflight_status"] == "blocked" and not args.allow_blocked_output:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
