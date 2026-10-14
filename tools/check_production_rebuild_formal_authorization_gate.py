"""Check formal production rebuild authorization readiness.

This gate reads the saved snapshot capture report and the saved real read-only
preflight probe report. It verifies that backup/snapshot reference is now
available and that the only remaining blocker is formal rebuild authorization.

It does not access Qdrant, create snapshots, write collection points, run live
preflight, run RAG, call an LLM, run eval, or execute production rebuild.
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

from tools._shared.layout import legacy_report_path


VERSION = "0.4.14.26"

DEFAULT_SNAPSHOT_CAPTURE_PATH = legacy_report_path(
    "production_rebuild_live_preflight_snapshot_create_reference_capture_report.json"
)
DEFAULT_REAL_READONLY_PREFLIGHT_PATH = legacy_report_path(
    "production_rebuild_live_preflight_real_readonly_probe_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path("production_rebuild_formal_authorization_gate_report.json")

ACCEPTED_AUTHORIZATION_STATUS = "accepted"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def build_report(
    *,
    snapshot_capture_path: Path = DEFAULT_SNAPSHOT_CAPTURE_PATH,
    real_readonly_preflight_path: Path = DEFAULT_REAL_READONLY_PREFLIGHT_PATH,
    authorization_status: str = "not_collected",
    authorization_reference: str | None = None,
    clock=utc_now,
) -> dict[str, Any]:
    snapshot_capture = load_json(snapshot_capture_path)
    real_preflight = load_json(real_readonly_preflight_path)

    snapshot_summary = as_dict(snapshot_capture.get("summary"))
    preflight_summary = as_dict(real_preflight.get("summary"))
    preflight_blockers = as_list(preflight_summary.get("blockers"))

    backup_or_snapshot_reference = snapshot_summary.get("backup_or_snapshot_reference")
    formal_authorization_accepted = (
        authorization_status == ACCEPTED_AUTHORIZATION_STATUS and non_empty_text(authorization_reference)
    )

    checks = []
    blockers: list[str] = []

    def add_check(check_id: str, passed: bool, details: str, blocker: str | None = None) -> None:
        checks.append({
            "check_id": check_id,
            "status": "passed" if passed else "failed",
            "details": details,
        })
        if not passed and blocker:
            blockers.append(blocker)

    add_check(
        "snapshot_capture_report_present",
        bool(snapshot_capture),
        "Snapshot capture report is present." if snapshot_capture else "Snapshot capture report is missing.",
        "snapshot_capture_report_missing",
    )
    add_check(
        "snapshot_reference_present",
        bool(snapshot_summary.get("backup_or_snapshot_reference_present")) and non_empty_text(backup_or_snapshot_reference),
        "Snapshot reference is available." if backup_or_snapshot_reference else "Snapshot reference is missing.",
        "backup_or_snapshot_reference_missing",
    )
    add_check(
        "snapshot_capture_passed",
        snapshot_summary.get("snapshot_capture_status") == "passed",
        "Snapshot capture status is passed.",
        "snapshot_capture_not_passed",
    )
    add_check(
        "real_readonly_preflight_report_present",
        bool(real_preflight),
        "Real read-only preflight report is present." if real_preflight else "Real read-only preflight report is missing.",
        "real_readonly_preflight_report_missing",
    )
    add_check(
        "real_readonly_preflight_has_snapshot_reference",
        as_dict(real_preflight.get("inputs")).get("backup_or_snapshot_reference_present") is True,
        "Real read-only preflight saw a backup/snapshot reference.",
        "real_readonly_preflight_missing_snapshot_reference",
    )
    add_check(
        "real_readonly_preflight_only_blocks_on_authorization",
        preflight_blockers == ["authorization_record_not_accepted"],
        f"Current preflight blockers: {preflight_blockers}",
        "real_readonly_preflight_unexpected_blockers",
    )
    add_check(
        "formal_authorization_accepted",
        formal_authorization_accepted,
        "Formal production rebuild authorization is accepted.",
        "authorization_record_not_accepted",
    )

    status = "passed" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_formal_authorization_gate_report",
        "scope": "formal production rebuild authorization gate based on saved preflight reports",
        "generated_at": clock(),
        "inputs": {
            "snapshot_capture_report": str(snapshot_capture_path),
            "real_readonly_preflight_report": str(real_readonly_preflight_path),
            "authorization_status": authorization_status,
            "authorization_reference_present": non_empty_text(authorization_reference),
        },
        "guardrails": {
            "saved_reports_only": True,
            "qdrant_access": "not_called",
            "qdrant_snapshot_create": "not_called",
            "qdrant_write": "disallowed",
            "collection_rebuild": "disallowed",
            "collection_switch": "disallowed",
            "live_preflight_run": "not_run",
            "production_rebuild": "disallowed",
            "rag_query_integration": "disallowed",
            "embedding_call": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "checks": checks,
        "authorization_gate": {
            "status": status,
            "formal_authorization_accepted": formal_authorization_accepted,
            "authorization_status": authorization_status,
            "authorization_reference_present": non_empty_text(authorization_reference),
            "backup_or_snapshot_reference": backup_or_snapshot_reference,
            "remaining_blockers": blockers,
            "allowed_next_step": (
                "run_fail_closed_live_preflight_with_accepted_authorization"
                if status == "passed"
                else "collect_formal_production_rebuild_authorization"
            ),
        },
        "summary": {
            "authorization_gate_status": status,
            "blockers": blockers,
            "backup_or_snapshot_reference_present": non_empty_text(backup_or_snapshot_reference),
            "formal_authorization_accepted": formal_authorization_accepted,
            "qdrant_access_allowed": False,
            "qdrant_write_allowed": False,
            "production_rebuild_allowed": False,
            "live_preflight_run": "not_run",
            "full_eval": "not_run",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check formal rebuild authorization readiness.")
    parser.add_argument("--snapshot-capture-report", type=Path, default=DEFAULT_SNAPSHOT_CAPTURE_PATH)
    parser.add_argument("--real-readonly-preflight-report", type=Path, default=DEFAULT_REAL_READONLY_PREFLIGHT_PATH)
    parser.add_argument("--authorization-status", default="not_collected")
    parser.add_argument("--authorization-reference", default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--allow-blocked-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        snapshot_capture_path=args.snapshot_capture_report,
        real_readonly_preflight_path=args.real_readonly_preflight_report,
        authorization_status=args.authorization_status,
        authorization_reference=args.authorization_reference,
    )
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Production rebuild formal authorization gate: "
        f"{summary['authorization_gate_status']}, "
        f"blockers={len(summary.get('blockers', []))}"
    )
    if summary["authorization_gate_status"] == "blocked" and not args.allow_blocked_output:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
