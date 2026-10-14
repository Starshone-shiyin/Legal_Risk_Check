"""Check the v0.4.8.12 final-evidence offline simulation result gate.

The gate reads only the saved simulation report, verifies completeness and
non-runtime boundaries, and emits a release-quality gate report. It does not
run eval or authorize runtime final-evidence selection policy implementation.
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


VERSION = "0.4.8.13"

DEFAULT_SIMULATION_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md")

EXPECTED_POLICY_ORDER = [
    "primary",
    "operative",
    "procedural",
    "liability",
    "scenario_core",
    "definition_only",
    "coverage_floor",
    "high_risk_manual_review",
]

REQUIRED_ROW_FIELDS = [
    "simulation_row_id",
    "source_contract_row_id",
    "policy_category",
    "simulation_status",
    "simulated_policy_effect",
    "simulated_result",
    "manual_review_signal",
    "runtime_adoption_status",
    "implementation_allowed",
    "code_patch_authorized",
    "source_case_ids",
]

GUARDRAILS = {
    "saved_reports_only": True,
    "gate_only": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
    "runtime_selection_policy_patch_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "main_flow_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
}

MOJIBAKE_MARKERS = ["\u951b", "\u7ecb", "\u9428", "\u93c2", "\u6d93", "\u4e63", "\ufffd"]
FORBIDDEN_KEYS = {
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "work_items",
    "engineering_tasks",
    "pending_tasks",
    "implementation_queue",
    "reviewer_decision",
    "human_outcome_record",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def counter_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: str(item[0])))


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


def find_key_paths(value: Any, blocked: set[str], prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if key in blocked:
                paths.append(child_path)
            paths.extend(find_key_paths(child, blocked, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_key_paths(child, blocked, f"{prefix}[{index}]"))
    return paths


def readability_paths(value: Any, prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, str) and any(marker in value for marker in MOJIBAKE_MARKERS):
        paths.append(prefix)
    elif isinstance(value, dict):
        for key, child in value.items():
            paths.extend(readability_paths(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(readability_paths(child, f"{prefix}[{index}]"))
    return paths


def simulation_checks(simulation: dict[str, Any]) -> list[dict[str, Any]]:
    gate = as_dict(simulation.get("simulation_gate"))
    summary = as_dict(simulation.get("summary"))
    rows = as_list(simulation.get("simulation_result_rows"))
    categories = [row.get("policy_category") for row in rows]
    missing_row_fields = {
        text(row.get("simulation_row_id")) or f"row_{index}": [
            field for field in REQUIRED_ROW_FIELDS if field not in row
        ]
        for index, row in enumerate(rows, start=1)
    }
    missing_row_fields = {key: value for key, value in missing_row_fields.items() if value}
    row_runtime_violations = [
        text(row.get("simulation_row_id")) or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if row.get("implementation_allowed") is not False
        or row.get("code_patch_authorized") is not False
        or row.get("runtime_adoption_status") != "not_allowed"
    ]
    forbidden_paths = find_key_paths(simulation, FORBIDDEN_KEYS)
    readable_paths = readability_paths(simulation)
    return [
        {
            "name": "simulation_report_schema",
            "status": "passed" if simulation.get("schema_kind") == "final_evidence_selection_policy_offline_simulation" else "failed",
            "expected": "final_evidence_selection_policy_offline_simulation",
            "actual": simulation.get("schema_kind"),
        },
        {
            "name": "simulation_report_version",
            "status": "passed" if simulation.get("version") == "0.4.8.12" else "failed",
            "expected": "0.4.8.12",
            "actual": simulation.get("version"),
        },
        {
            "name": "simulation_gate_completed",
            "status": "passed" if gate.get("status") == "completed_saved_report_simulation" else "failed",
            "actual": gate.get("status"),
        },
        {
            "name": "simulation_row_count",
            "status": "passed" if len(rows) == 8 and summary.get("simulation_row_count") == 8 else "failed",
            "row_count": len(rows),
            "summary_row_count": summary.get("simulation_row_count"),
        },
        {
            "name": "policy_category_order",
            "status": "passed" if categories == EXPECTED_POLICY_ORDER else "failed",
            "expected": EXPECTED_POLICY_ORDER,
            "actual": categories,
        },
        {
            "name": "blocking_failure_count",
            "status": "passed" if summary.get("blocking_failure_count") == 0 else "failed",
            "actual": summary.get("blocking_failure_count"),
        },
        {
            "name": "manual_review_signal_present",
            "status": "passed" if summary.get("manual_review_signal_count", 0) >= 1 else "failed",
            "actual": summary.get("manual_review_signal_count"),
        },
        {
            "name": "all_rows_have_required_fields",
            "status": "passed" if not missing_row_fields else "failed",
            "missing_row_fields": missing_row_fields,
        },
        {
            "name": "row_runtime_adoption_blocked",
            "status": "passed" if not row_runtime_violations else "failed",
            "violations": row_runtime_violations,
        },
        {
            "name": "gate_runtime_adoption_blocked",
            "status": "passed" if gate.get("implementation_allowed") is False and gate.get("code_patch_authorized") is False else "failed",
            "implementation_allowed": gate.get("implementation_allowed"),
            "code_patch_authorized": gate.get("code_patch_authorized"),
        },
        {
            "name": "forbidden_keys_absent",
            "status": "passed" if not forbidden_paths else "failed",
            "forbidden_paths": forbidden_paths,
        },
        {
            "name": "text_readability_gate",
            "status": "passed" if not readable_paths else "failed",
            "mojibake_like_paths": readable_paths,
        },
    ]


def build_report(simulation_report_path: Path = DEFAULT_SIMULATION_REPORT_PATH) -> dict[str, Any]:
    simulation = load_json(simulation_report_path)
    checks = simulation_checks(simulation)
    failed = [check for check in checks if check["status"] != "passed"]
    status = "open_for_policy_adoption_decision_draft" if not failed else "blocked"
    rows = as_list(simulation.get("simulation_result_rows"))
    categories = [text(row.get("policy_category")) for row in rows]
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_offline_simulation_gate",
        "scope": "saved-report offline simulation result gate only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "simulation_report": {
                "path": str(simulation_report_path),
                "present": simulation_report_path.exists(),
                "version": simulation.get("version"),
                "schema_kind": simulation.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "gate": {
            "status": status,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "allowed_next_step": "policy_adoption_decision_draft" if status != "blocked" else "blocked",
            "blockers": [check["name"] for check in failed],
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "simulation_row_count": len(rows),
            "policy_categories": categories,
            "result_summary": counter_dict(Counter(row.get("simulated_result") for row in rows)),
            "manual_review_signal_count": len([row for row in rows if row.get("manual_review_signal") is True]),
            "blocking_failure_count": as_dict(simulation.get("summary")).get("blocking_failure_count"),
            "next_version_recommendation": "v0.4.8.14 policy adoption decision draft",
        },
        "checks": checks,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.13 Final Evidence Selection Policy Offline Simulation Gate",
        "",
        "This gate validates the saved-report offline simulation result before any adoption decision draft is written.",
        "",
        "## Overview",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Checks: {summary.get('check_count')}",
        f"- Failed checks: {summary.get('failed_check_count')}",
        f"- Simulation rows: {summary.get('simulation_row_count')}",
        f"- Blocking failures: {summary.get('blocking_failure_count')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        "",
        "## Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in as_list(report.get("checks")):
        lines.append(f"| `{check.get('name')}` | `{check.get('status')}` |")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is a saved-report gate, not a runtime policy.",
        "- It does not run eval, backend calls, RAG, Qdrant, or LLM calls.",
        "- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.",
        "- Passing this gate only allows a policy adoption decision draft.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation-report", type=Path, default=DEFAULT_SIMULATION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()
    report = build_report(args.simulation_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy offline simulation gate checked: "
        f"{summary.get('status')}, {summary.get('failed_check_count')} failed checks"
    )
    return 1 if args.fail_on_error and report["gate"]["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
