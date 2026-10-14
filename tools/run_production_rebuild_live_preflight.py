"""Run or scaffold production rebuild live preflight reports.

The default CLI behavior still writes the historical scaffold status report.
The live preflight path is opt-in through ``--run-readonly-live-preflight`` and
performs only Qdrant read operations. It does not write Qdrant, switch
collections, call RAG/embedding/LLM/eval, or execute production rebuild.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VERSION = "0.4.14.29"
SCAFFOLD_VERSION = "0.4.14.21"

DEFAULT_OUTPUT_PATH = Path("tests/production_rebuild_live_preflight_report.json")
DEFAULT_SCAFFOLD_REPORT_PATH = Path(
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json"
)
DEFAULT_COLLECTION = "legal_knowledge"
DEFAULT_SOURCE_LINEAGE_REFERENCE = "ingestion-metadata-source-patch-v0.4.13.8"
READ_ONLY_EXPOSED_METHODS = ["get_collection", "count", "scroll"]

FORBIDDEN_WRITE_METHODS = {
    "upsert",
    "delete",
    "delete_collection",
    "recreate_collection",
    "update_collection",
    "create_alias",
    "update_aliases",
    "switch_collection",
}

REQUIRED_AUTHORIZATION_STATUS = "accepted"
FORBIDDEN_AUTHORIZATION_RECORD_KEYS = {
    "authorized_actions",
    "commands",
    "operation_log",
    "qdrant_write_allowed",
    "ready_to_apply",
    "rebuild_steps",
    "production_rebuild_allowed",
    "collection_switch_allowed",
}

ReadOnlyProbe = Callable[[str], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_authorization_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("authorization record must be a JSON object")
    return data


def _forbidden_authorization_record_keys(value: Any) -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_AUTHORIZATION_RECORD_KEYS:
                matches.append(key)
            matches.extend(_forbidden_authorization_record_keys(child))
    elif isinstance(value, list):
        for child in value:
            matches.extend(_forbidden_authorization_record_keys(child))
    return sorted(set(matches))


def _choose_record_or_cli_value(
    *,
    field_name: str,
    record: dict[str, Any],
    cli_value: str | None,
    default_value: str | None = None,
    errors: list[str],
) -> str | None:
    record_value = record.get(field_name)
    if non_empty_text(record_value):
        if non_empty_text(cli_value) and cli_value.strip() != record_value.strip():
            errors.append(f"authorization_record_{field_name}_mismatch")
        return record_value.strip()
    if non_empty_text(cli_value):
        return cli_value.strip()
    return default_value


def build_authorization_context(
    *,
    authorization_record: dict[str, Any] | None,
    cli_authorization_status: str | None,
    cli_authorization_reference: str | None,
    cli_target_collection: str | None,
    cli_backup_or_snapshot_reference: str | None,
    cli_source_lineage_reference: str | None,
) -> tuple[dict[str, Any], str | None, str | None, str | None]:
    record = dict(authorization_record or {})
    errors = list(record.get("_authorization_record_input_errors") or [])
    forbidden_keys = _forbidden_authorization_record_keys(record)
    if forbidden_keys:
        errors.append("authorization_record_forbidden_execution_fields")

    authorization_status = _choose_record_or_cli_value(
        field_name="authorization_status",
        record=record,
        cli_value=cli_authorization_status,
        default_value="not_collected",
        errors=errors,
    )
    authorization_reference = _choose_record_or_cli_value(
        field_name="authorization_reference",
        record=record,
        cli_value=cli_authorization_reference,
        default_value=None,
        errors=errors,
    )
    target_collection = _choose_record_or_cli_value(
        field_name="target_collection",
        record=record,
        cli_value=cli_target_collection,
        default_value=DEFAULT_COLLECTION,
        errors=errors,
    )
    backup_or_snapshot_reference = _choose_record_or_cli_value(
        field_name="backup_or_snapshot_reference",
        record=record,
        cli_value=cli_backup_or_snapshot_reference,
        default_value=None,
        errors=errors,
    )
    source_lineage_reference = _choose_record_or_cli_value(
        field_name="source_lineage_reference",
        record=record,
        cli_value=cli_source_lineage_reference,
        default_value=DEFAULT_SOURCE_LINEAGE_REFERENCE,
        errors=errors,
    )

    context_record = {
        **record,
        "authorization_status": authorization_status,
        "authorization_reference": authorization_reference,
        "_authorization_record_input_errors": sorted(set(errors)),
        "_authorization_record_forbidden_keys": forbidden_keys,
    }
    return context_record, target_collection, backup_or_snapshot_reference, source_lineage_reference


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


def build_real_qdrant_readonly_probe(client: Any | None = None) -> ReadOnlyProbe:
    """Return a probe callable that performs read-only Qdrant checks."""

    def probe(collection_name: str) -> dict[str, Any]:
        if client is None:
            from src.core.vectorstore import get_qdrant_client

            active_client = get_qdrant_client()
        else:
            active_client = client
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


def _base_checks() -> list[dict[str, Any]]:
    return [
        {"check_id": "authorization_record_accepted", "status": "not_run", "details": ""},
        {"check_id": "authorization_record_input_safe", "status": "not_run", "details": ""},
        {"check_id": "target_collection_present", "status": "not_run", "details": ""},
        {"check_id": "backup_or_snapshot_reference_present", "status": "not_run", "details": ""},
        {"check_id": "source_lineage_reference_present", "status": "not_run", "details": ""},
        {"check_id": "readonly_probe_available", "status": "not_run", "details": ""},
        {"check_id": "readonly_probe_target_matches", "status": "not_run", "details": ""},
        {"check_id": "forbidden_write_methods_absent", "status": "not_run", "details": ""},
    ]


def _set_check(checks: list[dict[str, Any]], check_id: str, status: str, details: str) -> None:
    for check in checks:
        if check["check_id"] == check_id:
            check["status"] = status
            check["details"] = details
            return


def _probe_exposed_methods(probe_result: dict[str, Any]) -> set[str]:
    methods: set[str] = set()
    for key in ("exposed_methods", "write_methods_exposed", "available_methods"):
        value = probe_result.get(key)
        if isinstance(value, list):
            methods.update(item for item in value if isinstance(item, str))
    return methods


def build_live_preflight_report(
    *,
    authorization_record: dict[str, Any] | None = None,
    target_collection: str | None = None,
    backup_or_snapshot_reference: str | None = None,
    source_lineage_reference: str | None = None,
    qdrant_readonly_probe: ReadOnlyProbe | None = None,
    clock: Callable[[], str] = utc_now,
) -> dict[str, Any]:
    checks = _base_checks()
    blockers: list[str] = []
    authorization = as_dict(authorization_record)
    authorization_errors = [item for item in authorization.get("_authorization_record_input_errors", []) if isinstance(item, str)]
    if authorization_errors:
        blockers.extend(authorization_errors)
        _set_check(
            checks,
            "authorization_record_input_safe",
            "failed",
            "Authorization record input contains unsafe fields, load errors, or CLI conflicts.",
        )
    else:
        _set_check(
            checks,
            "authorization_record_input_safe",
            "passed",
            "Authorization record input contains no unsafe fields or CLI conflicts.",
        )

    authorization_reference = authorization.get("authorization_reference")
    formal_authorization_accepted = (
        authorization.get("authorization_status") == REQUIRED_AUTHORIZATION_STATUS
        and non_empty_text(authorization_reference)
    )
    if formal_authorization_accepted:
        _set_check(checks, "authorization_record_accepted", "passed", "Authorization record is marked accepted.")
    else:
        blockers.append("authorization_record_not_accepted")
        _set_check(
            checks,
            "authorization_record_accepted",
            "failed",
            "Authorization record is missing or not accepted.",
        )

    if non_empty_text(target_collection):
        normalized_target = target_collection.strip()
        _set_check(checks, "target_collection_present", "passed", "Target collection is present.")
    else:
        normalized_target = ""
        blockers.append("target_collection_missing")
        _set_check(checks, "target_collection_present", "failed", "Target collection is missing.")

    if non_empty_text(backup_or_snapshot_reference):
        _set_check(
            checks,
            "backup_or_snapshot_reference_present",
            "passed",
            "Backup or snapshot reference is present.",
        )
    else:
        blockers.append("backup_or_snapshot_reference_missing")
        _set_check(
            checks,
            "backup_or_snapshot_reference_present",
            "failed",
            "Backup or snapshot reference is missing.",
        )

    if non_empty_text(source_lineage_reference):
        _set_check(checks, "source_lineage_reference_present", "passed", "Source lineage reference is present.")
    else:
        blockers.append("source_lineage_reference_missing")
        _set_check(
            checks,
            "source_lineage_reference_present",
            "failed",
            "Source lineage reference is missing.",
        )

    probe_result: dict[str, Any] = {}
    if qdrant_readonly_probe is None:
        blockers.append("readonly_probe_missing")
        _set_check(checks, "readonly_probe_available", "failed", "No injected read-only probe was provided.")
        _set_check(checks, "readonly_probe_target_matches", "failed", "Target match cannot be checked.")
        _set_check(checks, "forbidden_write_methods_absent", "failed", "Method exposure cannot be checked.")
    else:
        _set_check(checks, "readonly_probe_available", "passed", "Injected read-only probe is available.")
        try:
            probe_result = as_dict(qdrant_readonly_probe(normalized_target))
        except Exception as exc:  # pragma: no cover - exact exception type belongs to the injected probe.
            blockers.append("readonly_probe_error")
            probe_result = {"error": str(exc)}
            _set_check(checks, "readonly_probe_target_matches", "failed", "Injected probe raised an error.")
            _set_check(checks, "forbidden_write_methods_absent", "failed", "Method exposure cannot be checked.")
        else:
            returned_collection = probe_result.get("collection_name") or probe_result.get("target_collection")
            if returned_collection == normalized_target:
                _set_check(checks, "readonly_probe_target_matches", "passed", "Probe target matches input.")
            else:
                blockers.append("target_collection_mismatch")
                _set_check(checks, "readonly_probe_target_matches", "failed", "Probe target does not match input.")

            exposed = _probe_exposed_methods(probe_result)
            forbidden = sorted(FORBIDDEN_WRITE_METHODS & exposed)
            if forbidden:
                blockers.append("forbidden_write_methods_exposed")
                _set_check(
                    checks,
                    "forbidden_write_methods_absent",
                    "failed",
                    "Forbidden write-like methods are exposed.",
                )
            else:
                _set_check(
                    checks,
                    "forbidden_write_methods_absent",
                    "passed",
                    "No forbidden write-like methods are exposed.",
                )

    preflight_status = "passed" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_live_preflight_report",
        "scope": "minimal mockable live preflight scaffold with fail-closed defaults",
        "generated_at": clock(),
        "inputs": {
            "target_collection": normalized_target,
            "backup_or_snapshot_reference_present": non_empty_text(backup_or_snapshot_reference),
            "source_lineage_reference_present": non_empty_text(source_lineage_reference),
            "authorization_status": authorization.get("authorization_status"),
            "authorization_reference_present": non_empty_text(authorization_reference),
            "readonly_probe_injected": qdrant_readonly_probe is not None,
        },
        "probe_result": probe_result,
        "checks": checks,
        "guardrails": {
            "no_live_probe_by_default": True,
            "qdrant_client_import_deferred_to_explicit_readonly_probe": True,
            "no_write_methods_exposed_by_runner": True,
            "unknown_states_fail_closed": True,
            "readonly_live_preflight_run": qdrant_readonly_probe is not None,
            "write_or_rebuild_preflight_run": False,
            "qdrant_write": "disallowed",
            "production_rebuild": "disallowed",
            "collection_switch": "disallowed",
            "rag_query_integration": "disallowed",
            "embedding_call": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "summary": {
            "preflight_status": preflight_status,
            "blockers": blockers,
            "readonly_live_preflight_run": qdrant_readonly_probe is not None,
            "write_or_rebuild_preflight_run": False,
            "live_preflight_run_allowed": False,
            "qdrant_access_allowed": qdrant_readonly_probe is not None,
            "qdrant_write_allowed": False,
            "production_rebuild_allowed": False,
            "authorization_granted": False,
            "formal_authorization_accepted": formal_authorization_accepted,
            "full_eval": "not_run",
        },
    }


def build_scaffold_status_report(clock: Callable[[], str] = utc_now) -> dict[str, Any]:
    return {
        "version": SCAFFOLD_VERSION,
        "schema_kind": "production_rebuild_live_preflight_runner_minimal_implementation_scaffold",
        "scope": "create the minimal mockable runner scaffold without live preflight execution",
        "generated_at": clock(),
        "created_files": [
            "tools/run_production_rebuild_live_preflight.py",
            "tests/test_production_rebuild_live_preflight_runner.py",
        ],
        "not_created_files": [
            "tests/production_rebuild_live_preflight_report.json",
        ],
        "guardrails": {
            "standard_library_only": True,
            "no_live_probe_by_default": True,
            "no_qdrant_import_in_core_logic": True,
            "no_write_methods_exposed_by_runner": True,
            "mock_only_tests": True,
            "live_preflight_run": False,
            "production_rebuild_executed": False,
            "qdrant_write": "disallowed",
            "collection_switch": "disallowed",
            "rag_query_integration": "disallowed",
            "embedding_call": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "summary": {
            "status": "ready_for_minimal_scaffold_gate",
            "allowed_next_step": "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate",
            "runner_file_created": True,
            "runner_test_file_created": True,
            "runner_report_created": False,
            "live_preflight_run_allowed": False,
            "qdrant_write_allowed": False,
            "production_rebuild_allowed": False,
            "authorization_granted": False,
            "full_eval": "not_run",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run read-only production rebuild preflight or write scaffold status.")
    parser.add_argument("--scaffold-report-output", type=Path, default=DEFAULT_SCAFFOLD_REPORT_PATH)
    parser.add_argument("--run-readonly-live-preflight", action="store_true")
    parser.add_argument("--collection", default=None)
    parser.add_argument("--authorization-status", default=None)
    parser.add_argument("--authorization-reference", default=None)
    parser.add_argument("--authorization-record", type=Path, default=None)
    parser.add_argument("--backup-or-snapshot-reference", default=None)
    parser.add_argument("--source-lineage-reference", default=DEFAULT_SOURCE_LINEAGE_REFERENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--allow-blocked-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_readonly_live_preflight:
        target_collection = args.collection or DEFAULT_COLLECTION
        backup_or_snapshot_reference = args.backup_or_snapshot_reference
        source_lineage_reference = args.source_lineage_reference
        try:
            authorization_record: dict[str, Any] = {}
            if args.authorization_record is not None:
                try:
                    authorization_record = load_authorization_record(args.authorization_record)
                except Exception as exc:
                    authorization_record = {
                        "_authorization_record_input_errors": ["authorization_record_load_error"],
                        "authorization_record_load_error": str(exc),
                    }
            authorization_record, target_collection, backup_or_snapshot_reference, source_lineage_reference = (
                build_authorization_context(
                    authorization_record=authorization_record,
                    cli_authorization_status=args.authorization_status,
                    cli_authorization_reference=args.authorization_reference,
                    cli_target_collection=args.collection,
                    cli_backup_or_snapshot_reference=args.backup_or_snapshot_reference,
                    cli_source_lineage_reference=args.source_lineage_reference,
                )
            )
            report = build_live_preflight_report(
                authorization_record=authorization_record,
                target_collection=target_collection,
                backup_or_snapshot_reference=backup_or_snapshot_reference,
                source_lineage_reference=source_lineage_reference,
                qdrant_readonly_probe=build_real_qdrant_readonly_probe(),
            )
        except Exception as exc:
            report = {
                "version": VERSION,
                "schema_kind": "production_rebuild_live_preflight_report",
                "scope": "read-only live preflight failed closed before production rebuild",
                "generated_at": utc_now(),
                "inputs": {
                    "target_collection": target_collection,
                    "authorization_status": args.authorization_status,
                    "authorization_reference_present": non_empty_text(args.authorization_reference),
                    "backup_or_snapshot_reference_present": non_empty_text(args.backup_or_snapshot_reference),
                    "source_lineage_reference_present": non_empty_text(args.source_lineage_reference),
                    "readonly_probe_injected": True,
                },
                "probe_error": str(exc),
                "guardrails": {
                    "readonly_live_preflight_run": True,
                    "write_or_rebuild_preflight_run": False,
                    "qdrant_write": "disallowed",
                    "collection_switch": "disallowed",
                    "production_rebuild": "disallowed",
                    "rag_query_integration": "disallowed",
                    "embedding_call": "disallowed",
                    "llm_access": "disallowed",
                    "full_eval": "not_run",
                },
                "summary": {
                    "preflight_status": "blocked",
                    "blockers": ["readonly_live_preflight_error"],
                    "readonly_live_preflight_run": True,
                    "write_or_rebuild_preflight_run": False,
                    "qdrant_access_allowed": True,
                    "qdrant_write_allowed": False,
                    "production_rebuild_allowed": False,
                    "authorization_granted": False,
                    "formal_authorization_accepted": False,
                    "full_eval": "not_run",
                },
            }
        write_json(args.output, report)
        summary = report["summary"]
        print(
            "Production rebuild read-only live preflight: "
            f"{summary['preflight_status']}, blockers={len(summary.get('blockers', []))}"
        )
        if summary["preflight_status"] == "blocked" and not args.allow_blocked_output:
            return 1
        return 0

    report = build_scaffold_status_report()
    write_json(args.scaffold_report_output, report)
    summary = report["summary"]
    print(
        "Production rebuild live preflight runner minimal scaffold: "
        f"{summary['status']}, next={summary['allowed_next_step']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
