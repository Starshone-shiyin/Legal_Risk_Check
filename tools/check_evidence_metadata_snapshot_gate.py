"""Check the v0.4.11.1 evidence metadata snapshot report.

The gate confirms the read-only snapshot really read Qdrant payloads, kept
vectors disabled, produced the expected target rows, and preserved runtime
guardrails. Findings are allowed; fabricated or unavailable snapshots are not.
"""

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

from tools._shared.layout import legacy_report_path


VERSION = "0.4.11.2"

DEFAULT_SNAPSHOT_PATH = legacy_report_path("evidence_metadata_snapshot_report.json")
DEFAULT_CONTRACT_PATH = legacy_report_path("evidence_metadata_snapshot_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_metadata_snapshot_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/evidence_metadata_snapshot_gate_v0.4.11.2.md")

ALLOWED_SNAPSHOT_STATUSES = {
    "completed_read_only_evidence_metadata_snapshot",
    "completed_with_metadata_findings",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check(name: str, passed: bool, **details: Any) -> dict[str, Any]:
    return {"name": name, "status": "passed" if passed else "failed", **details}


def build_report(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    snapshot = load_json(snapshot_path)
    contract = load_json(contract_path)
    summary = as_dict(snapshot.get("summary"))
    gate = as_dict(snapshot.get("snapshot_gate"))
    rows = as_list(snapshot.get("diagnostic_rows"))
    targets = as_list(contract.get("snapshot_targets"))
    finding_counts = Counter(finding for row in rows for finding in as_list(row.get("blocking_findings")))

    checks = [
        check("snapshot_schema", snapshot.get("schema_kind") == "evidence_metadata_snapshot", actual=snapshot.get("schema_kind")),
        check("snapshot_version", snapshot.get("version") == "0.4.11.1", actual=snapshot.get("version")),
        check("contract_schema", contract.get("schema_kind") == "evidence_metadata_snapshot_contract", actual=contract.get("schema_kind")),
        check("contract_version", contract.get("version") == "0.4.11.0", actual=contract.get("version")),
        check("snapshot_status_allowed", gate.get("status") in ALLOWED_SNAPSHOT_STATUSES, actual=gate.get("status")),
        check("qdrant_payload_read", summary.get("qdrant_payload_read") is True and gate.get("qdrant_payload_read") is True),
        check("vectors_disabled", gate.get("with_vectors") is False),
        check("row_count_matches_contract", len(rows) == len(targets) and summary.get("diagnostic_row_count") == len(targets), row_count=len(rows), target_count=len(targets)),
        check("non_empty_qdrant_scan", summary.get("scanned_point_count", 0) > 0, scanned_point_count=summary.get("scanned_point_count")),
        check("runtime_changes_blocked", gate.get("implementation_allowed") is False and gate.get("retrieval_logic_change_allowed") is False),
    ]
    failed = [item for item in checks if item["status"] != "passed"]
    status = "open_for_v0_4_11_series_closeout" if not failed else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "evidence_metadata_snapshot_gate",
        "scope": "read-only evidence metadata snapshot gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "snapshot": {"path": str(snapshot_path), "version": snapshot.get("version"), "schema_kind": snapshot.get("schema_kind")},
            "contract": {"path": str(contract_path), "version": contract.get("version"), "schema_kind": contract.get("schema_kind")},
        },
        "gate": {
            "status": status,
            "allowed_next_step": "v0_4_11_series_closeout" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": [item["name"] for item in failed],
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "target_count": len(targets),
            "diagnostic_row_count": len(rows),
            "blocked_target_count": summary.get("blocked_target_count"),
            "scanned_point_count": summary.get("scanned_point_count"),
            "finding_counts": dict(sorted(finding_counts.items())),
            "primary_finding": finding_counts.most_common(1)[0][0] if finding_counts else "",
            "next_version_recommendation": "v0.4.11.3 evidence metadata snapshot series closeout",
        },
        "checks": checks,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.11.2 Evidence Metadata Snapshot Gate",
        "",
        "This gate validates the read-only Qdrant payload snapshot report. Metadata findings are preserved as evidence for the next series; they are not fixed here.",
        "",
        "## Overview",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Diagnostic rows: {summary.get('diagnostic_row_count')}",
        f"- Blocked targets: {summary.get('blocked_target_count')}",
        f"- Scanned points: {summary.get('scanned_point_count')}",
        f"- Primary finding: `{summary.get('primary_finding')}`",
        f"- Recommended next: `{summary.get('next_version_recommendation')}`",
        "",
        "## Boundaries",
        "",
        "- This gate does not repair metadata or chunks.",
        "- It does not change retrieval, rerank, prompt, anchors, rules, fixtures, or eval cases.",
        "- The current findings should feed a later root-cause/fix design series.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.snapshot, args.contract)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    print(
        "Evidence metadata snapshot gate checked: "
        f"{report['gate']['status']}, {report['summary']['failed_check_count']} failed"
    )
    return 0 if report["gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
