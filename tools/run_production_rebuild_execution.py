"""Run the authorized production rebuild and write an execution record."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VERSION = "0.4.14.29"
DEFAULT_AUTHORIZATION_RECORD_PATH = Path("tests/production_rebuild_authorization_record.json")
DEFAULT_PREFLIGHT_REPORT_PATH = Path("tests/production_rebuild_live_preflight_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/production_rebuild_execution_report.json")
DEFAULT_COLLECTION = "legal_knowledge"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_collection_snapshot(collection_name: str = DEFAULT_COLLECTION) -> dict[str, Any]:
    """Collect a small Qdrant snapshot without vectors."""
    from src.core.vectorstore import get_qdrant_client

    client = get_qdrant_client()
    snapshot: dict[str, Any] = {
        "collection_name": collection_name,
        "reachable": False,
        "points_count": None,
        "vectors_config_present": False,
        "sparse_vectors_config_present": False,
        "sample_payload_observed": False,
        "sample_metadata_keys": [],
    }
    info = client.get_collection(collection_name)
    snapshot["reachable"] = True
    snapshot["points_count"] = getattr(info, "points_count", None)
    params = getattr(getattr(info, "config", None), "params", None)
    snapshot["vectors_config_present"] = getattr(params, "vectors", None) is not None
    snapshot["sparse_vectors_config_present"] = getattr(params, "sparse_vectors", None) is not None
    points, _ = client.scroll(
        collection_name=collection_name,
        limit=1,
        with_payload=True,
        with_vectors=False,
    )
    if points:
        metadata = (points[0].payload or {}).get("metadata", {})
        snapshot["sample_payload_observed"] = True
        snapshot["sample_metadata_keys"] = sorted(metadata.keys())
    return snapshot


def read_manifest_summary(path: Path = Path("knowledge_manifest.json")) -> dict[str, Any]:
    manifest = load_json(path)
    documents = manifest.get("documents", [])
    if not isinstance(documents, list):
        raise ValueError("knowledge_manifest.json documents must be a list")
    sources = []
    missing_files = []
    for entry in documents:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source")
        if source:
            sources.append(source)
        file_path = Path(str(entry.get("file_path", "")))
        if not file_path.exists():
            missing_files.append(str(file_path))
    return {
        "manifest_path": str(path),
        "document_count": len(documents),
        "sources": sources,
        "missing_files": missing_files,
    }


def validate_execution_inputs(
    authorization_record: dict[str, Any],
    preflight_report: dict[str, Any],
    collection_name: str = DEFAULT_COLLECTION,
) -> list[str]:
    blockers: list[str] = []
    if authorization_record.get("schema_kind") != "production_rebuild_authorization_record":
        blockers.append("authorization_record_schema_mismatch")
    if authorization_record.get("authorization_status") != "accepted":
        blockers.append("authorization_record_not_accepted")
    if authorization_record.get("target_collection") != collection_name:
        blockers.append("authorization_target_collection_mismatch")
    if not authorization_record.get("authorization_reference"):
        blockers.append("authorization_reference_missing")
    if not authorization_record.get("backup_or_snapshot_reference"):
        blockers.append("backup_or_snapshot_reference_missing")
    if not authorization_record.get("source_lineage_reference"):
        blockers.append("source_lineage_reference_missing")

    summary = preflight_report.get("summary", {})
    if preflight_report.get("schema_kind") != "production_rebuild_live_preflight_report":
        blockers.append("preflight_schema_mismatch")
    if summary.get("preflight_status") != "passed":
        blockers.append("preflight_not_passed")
    if summary.get("blockers") not in ([], None):
        blockers.append("preflight_blockers_present")
    if summary.get("formal_authorization_accepted") is not True:
        blockers.append("preflight_formal_authorization_not_accepted")
    return blockers


def run_rebuild_command(
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    command = [sys.executable, "rag_admin.py", "--rebuild"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    completed = command_runner(
        command,
        input="y\n",
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
        timeout=timeout_seconds,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": (completed.stdout or "")[-12000:],
        "stderr_tail": (completed.stderr or "")[-12000:],
    }


def build_execution_record(
    *,
    authorization_record_path: Path = DEFAULT_AUTHORIZATION_RECORD_PATH,
    preflight_report_path: Path = DEFAULT_PREFLIGHT_REPORT_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    execute: bool = False,
    collection_snapshot: Callable[[str], dict[str, Any]] = collect_collection_snapshot,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    clock: Callable[[], str] = utc_now,
) -> dict[str, Any]:
    started_at = clock()
    authorization_record = load_json(authorization_record_path)
    preflight_report = load_json(preflight_report_path)
    manifest_summary = read_manifest_summary()
    blockers = validate_execution_inputs(authorization_record, preflight_report, collection_name)

    before_snapshot: dict[str, Any] | None = None
    after_snapshot: dict[str, Any] | None = None
    command_result: dict[str, Any] | None = None
    execution_status = "blocked"
    errors: list[str] = []

    if execute and not blockers:
        try:
            before_snapshot = collection_snapshot(collection_name)
            command_result = run_rebuild_command(command_runner=command_runner)
            if command_result["returncode"] == 0:
                after_snapshot = collection_snapshot(collection_name)
                execution_status = "succeeded"
            else:
                execution_status = "failed"
                errors.append("rebuild_command_nonzero_exit")
        except Exception as exc:  # pragma: no cover - exercised through CLI safety.
            execution_status = "failed"
            errors.append(f"rebuild_execution_exception:{type(exc).__name__}")
            command_result = command_result or {"command": [sys.executable, "rag_admin.py", "--rebuild"]}
            command_result["exception"] = str(exc)
    elif execute:
        execution_status = "blocked"
    else:
        execution_status = "dry_run_only"

    completed_at = clock()
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_execution_report",
        "generated_at": completed_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "inputs": {
            "authorization_record_path": str(authorization_record_path),
            "preflight_report_path": str(preflight_report_path),
            "target_collection": collection_name,
            "execute": execute,
            "authorization_reference": authorization_record.get("authorization_reference"),
            "backup_or_snapshot_reference": authorization_record.get("backup_or_snapshot_reference"),
            "source_lineage_reference": authorization_record.get("source_lineage_reference"),
        },
        "preconditions": {
            "status": "passed" if not blockers else "blocked",
            "blockers": blockers,
        },
        "manifest_summary": manifest_summary,
        "before_snapshot": before_snapshot,
        "command_result": command_result,
        "after_snapshot": after_snapshot,
        "summary": {
            "execution_status": execution_status,
            "errors": errors,
            "qdrant_write_executed": execution_status == "succeeded",
            "collection_rebuilt": execution_status == "succeeded",
            "full_eval": "not_run",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run authorized production rebuild and write an execution record.")
    parser.add_argument("--authorization-record", type=Path, default=DEFAULT_AUTHORIZATION_RECORD_PATH)
    parser.add_argument("--preflight-report", type=Path, default=DEFAULT_PREFLIGHT_REPORT_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--execute-production-rebuild", action="store_true")
    args = parser.parse_args()

    report = build_execution_record(
        authorization_record_path=args.authorization_record,
        preflight_report_path=args.preflight_report,
        collection_name=args.collection,
        execute=args.execute_production_rebuild,
    )
    write_json(args.output, report)
    status = report["summary"]["execution_status"]
    print(f"Production rebuild execution completed: {status}, output={args.output}")
    return 0 if status in {"succeeded", "dry_run_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
