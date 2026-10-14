"""Build the v0.4.11.3 evidence metadata snapshot series closeout."""

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


VERSION = "0.4.11.3"

DEFAULT_CONTRACT_PATH = legacy_report_path("evidence_metadata_snapshot_contract_report.json")
DEFAULT_SNAPSHOT_PATH = legacy_report_path("evidence_metadata_snapshot_report.json")
DEFAULT_GATE_PATH = legacy_report_path("evidence_metadata_snapshot_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_metadata_snapshot_series_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/evidence_metadata_snapshot_series_closeout_v0.4.11.3.md")

EXPECTED_STEPS = [
    ("0.4.11.0", "snapshot_contract", DEFAULT_CONTRACT_PATH, "evidence_metadata_snapshot_contract"),
    ("0.4.11.1", "read_only_snapshot_runner", DEFAULT_SNAPSHOT_PATH, "evidence_metadata_snapshot"),
    ("0.4.11.2", "snapshot_gate", DEFAULT_GATE_PATH, "evidence_metadata_snapshot_gate"),
]

GUARDRAILS = {
    "series_closeout_only": True,
    "saved_reports_only": True,
    "qdrant_access": "not_run_by_closeout",
    "knowledge_base_fulltext_scan": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "metadata_mutation": "disallowed",
    "chunk_mutation": "disallowed",
    "ingestion_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
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


def status_signal(payload: dict[str, Any]) -> str:
    for key in ("contract_gate", "snapshot_gate", "gate", "closeout_gate"):
        status = as_dict(payload.get(key)).get("status")
        if isinstance(status, str):
            return status
    return as_dict(payload.get("summary")).get("status", "")


def build_step_rows(steps: list[tuple[str, str, Path, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows = []
    blockers = []
    for version, step, path, schema in steps:
        payload = load_json(path)
        row_blockers = []
        if not path.exists():
            row_blockers.append("missing_report")
        if payload.get("version") != version:
            row_blockers.append("version_mismatch")
        if payload.get("schema_kind") != schema:
            row_blockers.append("schema_mismatch")
        rows.append({
            "version": version,
            "step": step,
            "path": str(path),
            "schema_kind": payload.get("schema_kind"),
            "status_signal": status_signal(payload),
            "present": path.exists(),
            "closeout_status": "passed" if not row_blockers else "failed",
            "blockers": row_blockers,
        })
        blockers.extend([f"{step}:{blocker}" for blocker in row_blockers])
    return rows, sorted(set(blockers))


def build_report(
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    gate_path: Path = DEFAULT_GATE_PATH,
) -> dict[str, Any]:
    steps = [
        ("0.4.11.0", "snapshot_contract", contract_path, "evidence_metadata_snapshot_contract"),
        ("0.4.11.1", "read_only_snapshot_runner", snapshot_path, "evidence_metadata_snapshot"),
        ("0.4.11.2", "snapshot_gate", gate_path, "evidence_metadata_snapshot_gate"),
    ]
    rows, blockers = build_step_rows(steps)
    contract = load_json(contract_path)
    snapshot = load_json(snapshot_path)
    gate = load_json(gate_path)
    contract_targets = as_list(contract.get("snapshot_targets"))
    diagnostic_rows = as_list(snapshot.get("diagnostic_rows"))
    snapshot_summary = as_dict(snapshot.get("summary"))
    gate_summary = as_dict(gate.get("summary"))
    finding_counts = Counter(finding for row in diagnostic_rows for finding in as_list(row.get("blocking_findings")))

    if as_dict(gate.get("gate")).get("status") != "open_for_v0_4_11_series_closeout":
        blockers.append("snapshot_gate_not_open")
    if len(contract_targets) != len(diagnostic_rows):
        blockers.append("target_row_count_mismatch")
    if snapshot_summary.get("qdrant_payload_read") is not True:
        blockers.append("qdrant_payload_not_read")
    if gate_summary.get("primary_finding") != "chunk_boundary_ambiguity":
        blockers.append("primary_finding_unexpected")

    status = "v0_4_11_series_closed_for_evidence_metadata_snapshot" if not blockers else "blocked"
    completed_versions = [row["version"] for row in rows if row["closeout_status"] == "passed"]
    return {
        "version": VERSION,
        "schema_kind": "evidence_metadata_snapshot_series_closeout",
        "scope": "v0.4.11.x evidence metadata snapshot read-only diagnostic closeout",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "closeout_gate": {
            "status": status,
            "series": "v0.4.11.x",
            "allowed_next_step": "v0.4.12.x metadata_chunking_root_cause_fix_design" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "retrieval_logic_change_allowed": False,
            "blockers": sorted(set(blockers)),
        },
        "summary": {
            "status": status,
            "completed_step_count": len(completed_versions),
            "expected_step_count": len(steps),
            "completed_versions": completed_versions,
            "target_count": len(contract_targets),
            "diagnostic_row_count": len(diagnostic_rows),
            "blocked_target_count": snapshot_summary.get("blocked_target_count"),
            "scanned_point_count": snapshot_summary.get("scanned_point_count"),
            "finding_counts": dict(sorted(finding_counts.items())),
            "primary_finding": gate_summary.get("primary_finding"),
            "recommended_next_series": "v0.4.12.x metadata/chunking root-cause and fix design",
        },
        "series_rows": rows,
        "closeout_findings": [
            {
                "finding": "real_qdrant_payload_snapshot_completed",
                "status": "closed" if snapshot_summary.get("qdrant_payload_read") is True else "blocked",
                "basis": f"Snapshot scanned {snapshot_summary.get('scanned_point_count')} Qdrant points with vectors disabled.",
            },
            {
                "finding": "chunk_boundary_ambiguity_is_primary_signal",
                "status": "closed" if gate_summary.get("primary_finding") == "chunk_boundary_ambiguity" else "blocked",
                "basis": "All 19 evidence targets are affected by missing chunk boundary metadata.",
            },
            {
                "finding": "runtime_not_authorized",
                "status": "closed",
                "basis": "No metadata/chunk, ingestion, retrieval, rerank, prompt, rule, fixture, or eval-case mutation is authorized.",
            },
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("closeout_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.11.3 Evidence Metadata Snapshot Series Closeout",
        "",
        "This closeout marks v0.4.11.x complete as a read-only evidence metadata snapshot diagnostic series. It does not authorize fixes.",
        "",
        "## Overview",
        "",
        f"- Closeout status: `{gate.get('status')}`",
        f"- Completed steps: {summary.get('completed_step_count')} / {summary.get('expected_step_count')}",
        f"- Targets: {summary.get('target_count')}",
        f"- Diagnostic rows: {summary.get('diagnostic_row_count')}",
        f"- Scanned points: {summary.get('scanned_point_count')}",
        f"- Primary finding: `{summary.get('primary_finding')}`",
        f"- Recommended next series: `{summary.get('recommended_next_series')}`",
        "",
        "## Boundaries",
        "",
        "- v0.4.11.x identified a real metadata/chunking signal; it did not fix it.",
        "- No RAG query, embedding call, LLM call, full eval, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change is authorized.",
        "- v0.4.12.x should design root-cause confirmation and fix strategy before any data repair.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.contract, args.snapshot, args.gate)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    print(
        "Evidence metadata snapshot series closeout built: "
        f"{report['closeout_gate']['status']}, {report['summary']['completed_step_count']} steps"
    )
    return 0 if report["closeout_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
