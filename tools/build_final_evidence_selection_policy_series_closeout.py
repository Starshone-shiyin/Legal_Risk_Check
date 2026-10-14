"""Build the v0.4.8.15 final-evidence policy series closeout report.

The closeout records that v0.4.8.x completed the offline design, simulation,
gate, and adoption-draft chain. It does not record final user adoption and does
not authorize runtime final-evidence selection policy implementation.
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


VERSION = "0.4.8.15"

DEFAULT_ADOPTION_DRAFT_PATH = legacy_report_path("final_evidence_selection_policy_adoption_decision_draft_report.json")
DEFAULT_GATE_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_gate_report.json")
DEFAULT_SIMULATION_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json")
DEFAULT_INPUT_CONTRACT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_input_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_series_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md")

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

COMPLETED_SERIES_STEPS = [
    ("0.4.8.0", "design_intake"),
    ("0.4.8.1", "simulator_spec"),
    ("0.4.8.2", "policy_table_draft"),
    ("0.4.8.3", "human_review_worksheet"),
    ("0.4.8.4", "closeout_envelope"),
    ("0.4.8.5", "closeout_decision_draft"),
    ("0.4.8.6", "closeout_confirmation_record_scaffold"),
    ("0.4.8.7", "closeout_confirmed_record"),
    ("0.4.8.8", "language_revision_worksheet"),
    ("0.4.8.9", "language_revision_closeout_draft"),
    ("0.4.8.10", "language_revision_confirmation_record"),
    ("0.4.8.11", "offline_simulation_input_contract"),
    ("0.4.8.12", "offline_simulation"),
    ("0.4.8.13", "offline_simulation_gate"),
    ("0.4.8.14", "adoption_decision_draft"),
    ("0.4.8.15", "series_closeout"),
]

GUARDRAILS = {
    "saved_reports_only": True,
    "series_closeout_only": True,
    "formal_user_adoption_recorded": False,
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


def source_blockers(
    adoption: dict[str, Any],
    gate: dict[str, Any],
    simulation: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    adoption_gate = as_dict(adoption.get("draft_gate"))
    gate_status = as_dict(gate.get("gate"))
    simulation_gate = as_dict(simulation.get("simulation_gate"))
    contract_gate = as_dict(contract.get("contract_gate"))
    adoption_rows = as_list(adoption.get("adoption_decision_draft_rows"))
    blockers: list[str] = []
    if adoption.get("version") != "0.4.8.14":
        blockers.append("adoption_draft_version_mismatch")
    if adoption.get("schema_kind") != "final_evidence_selection_policy_adoption_decision_draft":
        blockers.append("adoption_draft_schema_mismatch")
    if adoption_gate.get("status") != "pending_user_confirmation":
        blockers.append("adoption_draft_not_pending_user_confirmation")
    if adoption_gate.get("implementation_allowed") is not False:
        blockers.append("adoption_draft_implementation_not_blocked")
    if [row.get("policy_category") for row in adoption_rows] != EXPECTED_POLICY_ORDER:
        blockers.append("adoption_draft_category_order_drift")
    if len(adoption_rows) != 8:
        blockers.append("adoption_draft_row_count_drift")
    if gate.get("version") != "0.4.8.13":
        blockers.append("gate_version_mismatch")
    if gate_status.get("status") != "open_for_policy_adoption_decision_draft":
        blockers.append("gate_not_open")
    if simulation.get("version") != "0.4.8.12":
        blockers.append("simulation_version_mismatch")
    if simulation_gate.get("status") != "completed_saved_report_simulation":
        blockers.append("simulation_not_completed")
    if contract.get("version") != "0.4.8.11":
        blockers.append("input_contract_version_mismatch")
    if contract_gate.get("status") != "ready_for_saved_report_offline_simulation":
        blockers.append("input_contract_not_ready")
    for name, payload in [
        ("adoption", adoption),
        ("gate", gate),
        ("simulation", simulation),
        ("contract", contract),
    ]:
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{name}_forbidden_key_present:{path.split('.')[-1]}")
        if readability_paths(payload):
            blockers.append(f"{name}_blocked_for_human_readability")
    return sorted_unique(blockers)


def build_report(
    adoption_draft_path: Path = DEFAULT_ADOPTION_DRAFT_PATH,
    gate_report_path: Path = DEFAULT_GATE_REPORT_PATH,
    simulation_report_path: Path = DEFAULT_SIMULATION_REPORT_PATH,
    input_contract_path: Path = DEFAULT_INPUT_CONTRACT_PATH,
) -> dict[str, Any]:
    adoption = load_json(adoption_draft_path)
    gate = load_json(gate_report_path)
    simulation = load_json(simulation_report_path)
    contract = load_json(input_contract_path)
    blockers = source_blockers(adoption, gate, simulation, contract)
    ready = not blockers
    rows = as_list(adoption.get("adoption_decision_draft_rows"))
    categories = [text(row.get("policy_category")) for row in rows]
    closeout_status = "v0_4_8_series_closed_for_offline_design" if ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_series_closeout",
        "scope": "v0.4.8.x offline final evidence selection policy series closeout",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "adoption_decision_draft": {
                "path": str(adoption_draft_path),
                "present": adoption_draft_path.exists(),
                "version": adoption.get("version"),
                "schema_kind": adoption.get("schema_kind"),
            },
            "offline_simulation_gate": {
                "path": str(gate_report_path),
                "present": gate_report_path.exists(),
                "version": gate.get("version"),
                "schema_kind": gate.get("schema_kind"),
            },
            "offline_simulation": {
                "path": str(simulation_report_path),
                "present": simulation_report_path.exists(),
                "version": simulation.get("version"),
                "schema_kind": simulation.get("schema_kind"),
            },
            "offline_simulation_input_contract": {
                "path": str(input_contract_path),
                "present": input_contract_path.exists(),
                "version": contract.get("version"),
                "schema_kind": contract.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "closeout_gate": {
            "status": closeout_status,
            "series": "v0.4.8.x",
            "formal_user_adoption_recorded": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "allowed_next_step": "v0.4.9.x retrieval input quality governance or separately approved runtime design" if ready else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": closeout_status,
            "completed_step_count": len(COMPLETED_SERIES_STEPS),
            "completed_steps": [
                {"version": version, "step": step}
                for version, step in COMPLETED_SERIES_STEPS
            ],
            "policy_categories": categories,
            "adoption_draft_row_count": len(rows),
            "pending_user_confirmation_count": len([row for row in rows if row.get("draft_status") == "pending_user_confirmation"]),
            "formal_user_adoption_recorded": False,
            "implementation_allowed": False,
            "next_recommended_series": "v0.4.9.x retrieval input quality governance",
        },
        "series_closeout_findings": [
            {
                "finding": "offline_design_chain_completed",
                "status": "closed" if ready else "blocked",
                "basis": "intake, policy table, human review worksheet, closeout, language confirmation, input contract, simulation, gate, and adoption draft are present.",
            },
            {
                "finding": "runtime_implementation_not_authorized",
                "status": "closed",
                "basis": "The latest adoption draft still requires user confirmation and every closeout guardrail keeps implementation disabled.",
            },
            {
                "finding": "next_quality_track",
                "status": "ready_for_planning" if ready else "blocked",
                "basis": "Move to retrieval input quality governance unless the user separately approves a runtime final-evidence policy implementation version.",
            },
        ],
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "series_steps_complete", "status": "passed" if len(COMPLETED_SERIES_STEPS) == 16 else "failed", "step_count": len(COMPLETED_SERIES_STEPS)},
        {"name": "policy_categories_are_expected", "status": "passed" if categories == EXPECTED_POLICY_ORDER else "failed", "categories": categories},
        {"name": "formal_user_adoption_not_recorded", "status": "passed" if report["closeout_gate"]["formal_user_adoption_recorded"] is False else "failed"},
        {"name": "series_is_non_runtime", "status": "passed" if report["closeout_gate"]["implementation_allowed"] is False and report["closeout_gate"]["code_patch_authorized"] is False else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["closeout_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["closeout_gate"]["blockers"] = sorted_unique(blockers + ["output_closeout_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("closeout_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.15 Final Evidence Selection Policy Series Closeout",
        "",
        "This closeout marks v0.4.8.x complete as an offline design and governance series. It does not record formal user adoption and does not authorize runtime implementation.",
        "",
        "## Overview",
        "",
        f"- Closeout status: `{gate.get('status')}`",
        f"- Completed steps: {summary.get('completed_step_count')}",
        f"- Adoption draft rows: {summary.get('adoption_draft_row_count')}",
        f"- Pending user confirmation rows: {summary.get('pending_user_confirmation_count')}",
        f"- Formal user adoption recorded: {summary.get('formal_user_adoption_recorded')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        f"- Next recommended series: `{summary.get('next_recommended_series')}`",
        "",
        "## Completed Steps",
        "",
        "| Version | Step |",
        "|---|---|",
    ]
    for row in as_list(summary.get("completed_steps")):
        lines.append(f"| `{row.get('version')}` | `{row.get('step')}` |")
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- v0.4.8.x is closed for offline design, not runtime implementation.",
        "- The adoption draft remains pending user confirmation.",
        "- It does not run eval, backend calls, RAG, Qdrant, or LLM calls.",
        "- Future runtime policy work needs a separately approved version.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adoption-draft", type=Path, default=DEFAULT_ADOPTION_DRAFT_PATH)
    parser.add_argument("--gate-report", type=Path, default=DEFAULT_GATE_REPORT_PATH)
    parser.add_argument("--simulation-report", type=Path, default=DEFAULT_SIMULATION_REPORT_PATH)
    parser.add_argument("--input-contract", type=Path, default=DEFAULT_INPUT_CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.adoption_draft, args.gate_report, args.simulation_report, args.input_contract)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy series closeout built: "
        f"{summary.get('status')}, {summary.get('completed_step_count')} steps"
    )
    return 0 if report["closeout_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
