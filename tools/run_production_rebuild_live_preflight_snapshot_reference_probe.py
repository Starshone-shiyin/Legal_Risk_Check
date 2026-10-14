"""Probe existing Qdrant snapshot references for production rebuild preflight.

This tool is intentionally read-only. It lists existing collection snapshots
through the project Qdrant client and reports whether a usable
backup_or_snapshot_reference is already available for the live preflight path.
It does not create, delete, recover, write, rebuild, run RAG, call an LLM, or
run eval.
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


VERSION = "0.4.14.24"

DEFAULT_COLLECTION = "legal_knowledge"
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_live_preflight_snapshot_reference_probe_report.json")
READ_ONLY_EXPOSED_METHODS = ["list_snapshots"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def _safe_get(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _normalize_snapshot(snapshot: Any) -> dict[str, Any]:
    data = _safe_model_dump(snapshot)
    if not data:
        data = {
            "name": _safe_get(snapshot, "name"),
            "creation_time": _safe_get(snapshot, "creation_time"),
            "size": _safe_get(snapshot, "size"),
            "checksum": _safe_get(snapshot, "checksum"),
        }
    name = data.get("name")
    creation_time = data.get("creation_time")
    size = data.get("size")
    checksum = data.get("checksum")
    return {
        "name": str(name) if name is not None else None,
        "creation_time": str(creation_time) if creation_time is not None else None,
        "size": size,
        "checksum": str(checksum) if checksum is not None else None,
    }


def _snapshot_sort_key(snapshot: dict[str, Any]) -> tuple[str, str]:
    return (
        str(snapshot.get("creation_time") or ""),
        str(snapshot.get("name") or ""),
    )


def build_snapshot_reference(collection_name: str, snapshot_name: str) -> str:
    return f"qdrant-snapshot://collection/{collection_name}/{snapshot_name}"


def build_snapshot_reference_probe(client: Any | None = None):
    """Return a probe callable that lists existing collection snapshots only."""

    def probe(collection_name: str) -> dict[str, Any]:
        active_client = client or get_qdrant_client()
        snapshots = [_normalize_snapshot(item) for item in active_client.list_snapshots(collection_name)]
        snapshots = sorted(snapshots, key=_snapshot_sort_key, reverse=True)
        selected = snapshots[0] if snapshots and snapshots[0].get("name") else None
        reference = (
            build_snapshot_reference(collection_name, selected["name"])
            if selected and selected.get("name")
            else None
        )
        return {
            "collection_name": collection_name,
            "reachable": True,
            "snapshot_count": len(snapshots),
            "snapshots": snapshots,
            "selected_snapshot": selected,
            "backup_or_snapshot_reference": reference,
            "exposed_methods": READ_ONLY_EXPOSED_METHODS,
        }

    return probe


def build_report(
    *,
    collection_name: str,
    client: Any | None = None,
    clock=utc_now,
) -> dict[str, Any]:
    probe = build_snapshot_reference_probe(client)
    errors: list[str] = []
    try:
        probe_result = probe(collection_name)
    except Exception as exc:
        probe_result = {
            "collection_name": collection_name,
            "reachable": False,
            "snapshot_count": 0,
            "snapshots": [],
            "selected_snapshot": None,
            "backup_or_snapshot_reference": None,
            "probe_error": str(exc),
            "exposed_methods": READ_ONLY_EXPOSED_METHODS,
        }
        errors.append("snapshot_reference_probe_error")

    if not probe_result.get("backup_or_snapshot_reference"):
        errors.append("backup_or_snapshot_reference_missing")

    status = "passed" if not errors else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_snapshot_reference_probe_report",
        "scope": "real Qdrant collection snapshot reference read-only probe",
        "generated_at": clock(),
        "inputs": {
            "target_collection": collection_name,
        },
        "guardrails": {
            "real_qdrant_readonly_probe": True,
            "qdrant_read_methods_only": READ_ONLY_EXPOSED_METHODS,
            "qdrant_snapshot_create": "disallowed",
            "qdrant_snapshot_delete": "disallowed",
            "qdrant_snapshot_recover": "disallowed",
            "qdrant_write": "disallowed",
            "collection_switch": "disallowed",
            "production_rebuild": "disallowed",
            "rag_query_integration": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "snapshot_probe": probe_result,
        "summary": {
            "snapshot_reference_status": status,
            "blockers": errors,
            "snapshot_count": probe_result.get("snapshot_count", 0),
            "backup_or_snapshot_reference": probe_result.get("backup_or_snapshot_reference"),
            "backup_or_snapshot_reference_present": bool(probe_result.get("backup_or_snapshot_reference")),
            "qdrant_access_allowed": True,
            "qdrant_write_allowed": False,
            "production_rebuild_allowed": False,
            "authorization_granted": False,
            "full_eval": "not_run",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List existing Qdrant snapshots for rebuild preflight.")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--allow-blocked-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(collection_name=args.collection)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Production rebuild snapshot reference probe: "
        f"{summary['snapshot_reference_status']}, "
        f"snapshots={summary['snapshot_count']}, "
        f"blockers={len(summary.get('blockers', []))}"
    )
    if summary["snapshot_reference_status"] == "blocked" and not args.allow_blocked_output:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
