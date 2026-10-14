"""Build the v0.4.12.3 metadata/chunking root-cause series closeout.

This closeout summarizes root-cause, fix design, and gate reports. It does not
authorize implementation, rebuild Qdrant, or change retrieval behavior.
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


VERSION = "0.4.12.3"

DEFAULT_ROOT_CAUSE_PATH = legacy_report_path("metadata_chunking_root_cause_report.json")
DEFAULT_FIX_DESIGN_PATH = legacy_report_path("metadata_chunking_fix_design_report.json")
DEFAULT_FIX_DESIGN_GATE_PATH = legacy_report_path("metadata_chunking_fix_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("metadata_chunking_series_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/metadata_chunking_series_closeout_v0.4.12.3.md")

GUARDRAILS = {
    "closeout_only": True,
    "saved_reports_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
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
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def build_report(
    root_cause_path: Path = DEFAULT_ROOT_CAUSE_PATH,
    fix_design_path: Path = DEFAULT_FIX_DESIGN_PATH,
    fix_design_gate_path: Path = DEFAULT_FIX_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    root_cause = load_json(root_cause_path)
    fix_design = load_json(fix_design_path)
    gate = load_json(fix_design_gate_path)
    root_summary = as_dict(root_cause.get("summary"))
    fix_summary = as_dict(fix_design.get("summary"))
    gate_summary = as_dict(gate.get("summary"))

    blockers = []
    if root_cause.get("version") != "0.4.12.0":
        blockers.append("root_cause_version_mismatch")
    if as_dict(root_cause.get("root_cause_gate")).get("status") != "ready_for_metadata_chunking_fix_design":
        blockers.append("root_cause_gate_not_ready")
    if fix_design.get("version") != "0.4.12.1":
        blockers.append("fix_design_version_mismatch")
    if as_dict(fix_design.get("fix_design_gate")).get("status") != "ready_for_fix_design_gate":
        blockers.append("fix_design_not_ready")
    if gate.get("version") != "0.4.12.2":
        blockers.append("fix_design_gate_version_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("fix_design_gate_not_passed")

    status = "completed" if not blockers else "blocked"
    completed_steps = [
        {
            "version": "0.4.12.0",
            "name": "Metadata/Chunking Root-Cause Report",
            "status": as_dict(root_cause.get("root_cause_gate")).get("status"),
            "output": str(root_cause_path),
        },
        {
            "version": "0.4.12.1",
            "name": "Metadata/Chunking Fix Design",
            "status": as_dict(fix_design.get("fix_design_gate")).get("status"),
            "output": str(fix_design_path),
        },
        {
            "version": "0.4.12.2",
            "name": "Metadata/Chunking Fix Design Gate",
            "status": gate_summary.get("status"),
            "output": str(fix_design_gate_path),
        },
    ]
    return {
        "version": VERSION,
        "schema_kind": "metadata_chunking_series_closeout",
        "scope": "metadata/chunking root-cause and fix design series closeout only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "root_cause": {"path": str(root_cause_path), "version": root_cause.get("version")},
            "fix_design": {"path": str(fix_design_path), "version": fix_design.get("version")},
            "fix_design_gate": {"path": str(fix_design_gate_path), "version": gate.get("version")},
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "completed_step_count": len(completed_steps),
            "primary_root_cause": root_summary.get("primary_root_cause"),
            "design_target": fix_summary.get("design_target"),
            "stable_id_impact": fix_summary.get("stable_id_impact"),
            "requires_rebuild": fix_summary.get("requires_rebuild"),
            "gate_failed_check_count": gate_summary.get("failed_check_count"),
            "implementation_allowed": False,
            "retrieval_logic_change_allowed": False,
            "allowed_next_series": "v0.4.13.x ingestion metadata patch and rebuild dry-run planning" if status == "completed" else "blocked",
            "blockers": blockers,
        },
        "completed_steps": completed_steps,
        "handoff": {
            "next_series_goal": "Design and gate an ingestion metadata patch plus rebuild dry-run before any Qdrant write.",
            "must_not_do_next": [
                "do not patch rag_query",
                "do not add anchor rules to mask metadata gaps",
                "do not patch Qdrant payloads directly",
                "do not rebuild collection before rebuild dry-run and rollback plan",
                "do not modify eval cases or fixtures to match current failures",
            ],
            "required_next_inputs": [
                "approved ingestion metadata patch plan",
                "affected source and point/chunk ID drift estimate",
                "rebuild dry-run report",
                "rollback plan",
                "post-rebuild qdrant integrity and targeted eval plan",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.12.3 Metadata/Chunking Series Closeout",
        "",
        "This closeout completes the root-cause and fix-design series. It does not authorize implementation.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Primary root cause: `{summary.get('primary_root_cause')}`",
        f"- Design target: `{summary.get('design_target')}`",
        f"- Requires rebuild: `{summary.get('requires_rebuild')}`",
        f"- Allowed next series: `{summary.get('allowed_next_series')}`",
        "",
        "## Completed Steps",
        "",
    ]
    for row in report.get("completed_steps", []):
        lines.append(f"- `{row.get('version')}` {row.get('name')}: `{row.get('status')}`")
    lines.extend(["", "## Handoff", ""])
    handoff = as_dict(report.get("handoff"))
    lines.append(handoff.get("next_series_goal", ""))
    lines.extend(["", "### Must Not Do Next", ""])
    for item in handoff.get("must_not_do_next", []):
        lines.append(f"- {item}")
    lines.extend(["", "### Required Next Inputs", ""])
    for item in handoff.get("required_next_inputs", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.12.3 metadata/chunking series closeout.")
    parser.add_argument("--root-cause", type=Path, default=DEFAULT_ROOT_CAUSE_PATH)
    parser.add_argument("--fix-design", type=Path, default=DEFAULT_FIX_DESIGN_PATH)
    parser.add_argument("--fix-design-gate", type=Path, default=DEFAULT_FIX_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root_cause, args.fix_design, args.fix_design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(f"Metadata/chunking series closeout: {summary.get('status')}, next={summary.get('allowed_next_series')}")
    return 0 if summary.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
