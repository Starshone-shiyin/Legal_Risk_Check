"""Create an authorized Qdrant collection snapshot and capture its reference.

This tool is a narrow production-preflight helper. It may create one Qdrant
collection snapshot only when explicit user authorization is supplied. After
creation, it lists snapshots to capture the resulting backup_or_snapshot_reference
for later fail-closed preflight checks.

It does not write collection points, switch collections, recover snapshots,
delete snapshots, run RAG, call an LLM, run eval, or execute production rebuild.
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
from tools.run_production_rebuild_live_preflight_snapshot_reference_probe import (
    build_snapshot_reference,
)


VERSION = "0.4.14.25"

DEFAULT_COLLECTION = "legal_knowledge"
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_live_preflight_snapshot_create_reference_capture_report.json")
AUTHORIZED_STATUS = "user_explicitly_authorized_snapshot_creation"
EXPOSED_METHODS = ["list_snapshots", "create_snapshot", "list_snapshots"]


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


def normalize_snapshot(snapshot: Any) -> dict[str, Any]:
    data = _safe_model_dump(snapshot)
    if not data:
        data = {
            "name": _safe_get(snapshot, "name"),
            "creation_time": _safe_get(snapshot, "creation_time"),
            "size": _safe_get(snapshot, "size"),
            "checksum": _safe_get(snapshot, "checksum"),
        }
    return {
        "name": str(data.get("name")) if data.get("name") is not None else None,
        "creation_time": str(data.get("creation_time")) if data.get("creation_time") is not None else None,
        "size": data.get("size"),
        "checksum": str(data.get("checksum")) if data.get("checksum") is not None else None,
    }


def snapshot_sort_key(snapshot: dict[str, Any]) -> tuple[str, str]:
    return (
        str(snapshot.get("creation_time") or ""),
        str(snapshot.get("name") or ""),
    )


def build_authorized_snapshot_capture(
    *,
    collection_name: str,
    authorization_status: str,
    authorization_reference: str,
    client: Any | None = None,
) -> dict[str, Any]:
    if collection_name != DEFAULT_COLLECTION:
        return {
            "collection_name": collection_name,
            "status": "blocked",
            "blockers": ["target_collection_not_locked_to_legal_knowledge"],
            "before_snapshots": [],
            "created_snapshot": None,
            "after_snapshots": [],
            "backup_or_snapshot_reference": None,
            "exposed_methods": [],
        }

    if authorization_status != AUTHORIZED_STATUS:
        return {
            "collection_name": collection_name,
            "status": "blocked",
            "blockers": ["snapshot_creation_not_explicitly_authorized"],
            "before_snapshots": [],
            "created_snapshot": None,
            "after_snapshots": [],
            "backup_or_snapshot_reference": None,
            "exposed_methods": [],
        }

    active_client = client or get_qdrant_client()
    before_snapshots = [
        normalize_snapshot(item) for item in active_client.list_snapshots(collection_name=collection_name)
    ]
    before_snapshots = sorted(before_snapshots, key=snapshot_sort_key, reverse=True)
    created = normalize_snapshot(active_client.create_snapshot(collection_name=collection_name, wait=True))
    after_snapshots = [
        normalize_snapshot(item) for item in active_client.list_snapshots(collection_name=collection_name)
    ]
    after_snapshots = sorted(after_snapshots, key=snapshot_sort_key, reverse=True)
    created_name = created.get("name")
    selected = next((item for item in after_snapshots if item.get("name") == created_name), None)
    if selected is None and created_name:
        selected = created
    reference = build_snapshot_reference(collection_name, selected["name"]) if selected and selected.get("name") else None
    blockers = [] if reference else ["created_snapshot_reference_missing"]
    return {
        "collection_name": collection_name,
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "authorization_reference": authorization_reference,
        "before_snapshots": before_snapshots,
        "created_snapshot": created,
        "after_snapshots": after_snapshots,
        "snapshot_count_before_create": len(before_snapshots),
        "snapshot_count_after_create": len(after_snapshots),
        "selected_snapshot": selected,
        "backup_or_snapshot_reference": reference,
        "exposed_methods": EXPOSED_METHODS,
    }


def build_report(
    *,
    collection_name: str,
    authorization_status: str,
    authorization_reference: str,
    client: Any | None = None,
    clock=utc_now,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        capture = build_authorized_snapshot_capture(
            collection_name=collection_name,
            authorization_status=authorization_status,
            authorization_reference=authorization_reference,
            client=client,
        )
    except Exception as exc:
        capture = {
            "collection_name": collection_name,
            "status": "blocked",
            "blockers": ["snapshot_creation_or_capture_error"],
            "capture_error": str(exc),
            "created_snapshot": None,
            "before_snapshots": [],
            "after_snapshots": [],
            "backup_or_snapshot_reference": None,
            "exposed_methods": EXPOSED_METHODS,
        }

    errors.extend(capture.get("blockers", []))
    status = "passed" if not errors else "blocked"
    created_snapshot = capture.get("created_snapshot")
    created_snapshot_name = created_snapshot.get("name") if isinstance(created_snapshot, dict) else None
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_snapshot_create_reference_capture_report",
        "scope": "authorized Qdrant collection snapshot creation and reference capture",
        "generated_at": clock(),
        "inputs": {
            "target_collection": collection_name,
            "authorization_status": authorization_status,
            "authorization_reference": authorization_reference,
            "snapshot_creation_wait": True,
        },
        "guardrails": {
            "explicit_user_authorization_required": True,
            "qdrant_snapshot_create": "authorized_for_collection_snapshot_only",
            "qdrant_methods_sequence": EXPOSED_METHODS,
            "qdrant_write_to_points": "disallowed",
            "qdrant_snapshot_delete": "disallowed",
            "qdrant_snapshot_recover": "disallowed",
            "collection_switch": "disallowed",
            "production_rebuild": "disallowed",
            "rag_query_integration": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "snapshot_capture": capture,
        "summary": {
            "snapshot_capture_status": status,
            "blockers": errors,
            "backup_or_snapshot_reference": capture.get("backup_or_snapshot_reference"),
            "backup_or_snapshot_reference_present": bool(capture.get("backup_or_snapshot_reference")),
            "snapshot_created": bool(created_snapshot_name),
            "qdrant_snapshot_create_allowed": authorization_status == AUTHORIZED_STATUS,
            "qdrant_point_write_allowed": False,
            "production_rebuild_allowed": False,
            "authorization_granted_for_rebuild": False,
            "full_eval": "not_run",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an authorized Qdrant snapshot and capture its reference.")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--authorization-status", required=True)
    parser.add_argument("--authorization-reference", required=True)
    parser.add_argument("--authorized-snapshot-create", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--allow-blocked-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        collection_name=args.collection,
        authorization_status=args.authorization_status if args.authorized_snapshot_create else "missing_cli_ack",
        authorization_reference=args.authorization_reference,
    )
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Production rebuild authorized snapshot capture: "
        f"{summary['snapshot_capture_status']}, "
        f"snapshot_created={summary['snapshot_created']}, "
        f"reference_present={summary['backup_or_snapshot_reference_present']}"
    )
    if summary["snapshot_capture_status"] == "blocked" and not args.allow_blocked_output:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
