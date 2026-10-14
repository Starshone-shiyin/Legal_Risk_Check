"""Build the v0.4.8.14 final-evidence policy adoption decision draft.

The draft consumes the v0.4.8.13 gate and v0.4.8.12 simulation reports. It
records suggested adoption routes for future human confirmation only; it does
not implement or authorize runtime final-evidence selection policy changes.
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


VERSION = "0.4.8.14"

DEFAULT_GATE_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_gate_report.json")
DEFAULT_SIMULATION_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_adoption_decision_draft_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md")

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

SUGGESTED_ADOPTION_OPTIONS = {
    "primary": "accept_for_future_runtime_design_after_separate_approval",
    "operative": "accept_for_future_runtime_design_after_separate_approval",
    "procedural": "accept_for_future_runtime_design_after_separate_approval",
    "liability": "accept_as_context_only_for_future_runtime_design_after_separate_approval",
    "scenario_core": "accept_as_grounding_floor_candidate_after_separate_approval",
    "definition_only": "accept_as_demotion_rule_candidate_after_separate_approval",
    "coverage_floor": "accept_as_manual_review_gate_candidate_after_separate_approval",
    "high_risk_manual_review": "accept_as_manual_review_routing_candidate_after_separate_approval",
}

DECISION_BOUNDARIES = {
    "primary": "Future runtime design may preserve primary authority if already present in candidate evidence.",
    "operative": "Future runtime design may preserve operative rules over definitions or background material.",
    "procedural": "Future runtime design may preserve procedural route evidence where the issue depends on process compliance.",
    "liability": "Liability provisions remain context and should not replace operative rules.",
    "scenario_core": "Scenario-core provisions can act as floor candidates but should not auto-win final selection.",
    "definition_only": "Definition-only provisions can support terminology and should be demoted when merits rules are available.",
    "coverage_floor": "Coverage gaps should trigger manual review, not synthetic evidence.",
    "high_risk_manual_review": "High-risk thin-evidence cases should route to manual review before runtime confidence is raised.",
}

GUARDRAILS = {
    "saved_reports_only": True,
    "decision_draft_only": True,
    "requires_user_confirmation": True,
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


def source_blockers(gate_report: dict[str, Any], simulation_report: dict[str, Any]) -> list[str]:
    gate = as_dict(gate_report.get("gate"))
    sim_gate = as_dict(simulation_report.get("simulation_gate"))
    sim_summary = as_dict(simulation_report.get("summary"))
    sim_rows = as_list(simulation_report.get("simulation_result_rows"))
    blockers: list[str] = []
    if gate_report.get("version") != "0.4.8.13":
        blockers.append("gate_version_mismatch")
    if gate_report.get("schema_kind") != "final_evidence_selection_policy_offline_simulation_gate":
        blockers.append("gate_schema_mismatch")
    if gate.get("status") != "open_for_policy_adoption_decision_draft":
        blockers.append("gate_not_open_for_decision_draft")
    if gate.get("implementation_allowed") is not False:
        blockers.append("gate_implementation_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("gate_has_blockers")
    if simulation_report.get("version") != "0.4.8.12":
        blockers.append("simulation_version_mismatch")
    if simulation_report.get("schema_kind") != "final_evidence_selection_policy_offline_simulation":
        blockers.append("simulation_schema_mismatch")
    if sim_gate.get("status") != "completed_saved_report_simulation":
        blockers.append("simulation_not_completed")
    if sim_summary.get("blocking_failure_count") != 0:
        blockers.append("simulation_has_blocking_failures")
    if [row.get("policy_category") for row in sim_rows] != EXPECTED_POLICY_ORDER:
        blockers.append("simulation_category_order_drift")
    if len(sim_rows) != 8:
        blockers.append("simulation_row_count_drift")
    for name, payload in [("gate", gate_report), ("simulation", simulation_report)]:
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{name}_forbidden_key_present:{path.split('.')[-1]}")
        if readability_paths(payload):
            blockers.append(f"{name}_blocked_for_human_readability")
    return sorted_unique(blockers)


def decision_rows(simulation_report: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source in enumerate(as_list(simulation_report.get("simulation_result_rows")), start=1):
        category = text(source.get("policy_category"))
        rows.append({
            "draft_row_id": f"FES-ADOPTION-DRAFT-{index:03d}",
            "source_simulation_row_id": source.get("simulation_row_id"),
            "policy_category": category,
            "draft_status": "pending_user_confirmation" if ready else "blocked",
            "suggested_adoption_option": SUGGESTED_ADOPTION_OPTIONS.get(category, "blocked_unknown_policy_category"),
            "decision_boundary": DECISION_BOUNDARIES.get(category, "Unknown category cannot be adopted."),
            "requires_user_confirmation": True,
            "runtime_adoption_status": "not_allowed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "source_case_ids": as_list(source.get("source_case_ids")),
            "source_simulated_result": source.get("simulated_result"),
            "source_manual_review_signal": source.get("manual_review_signal"),
        })
    return rows


def build_report(
    gate_report_path: Path = DEFAULT_GATE_REPORT_PATH,
    simulation_report_path: Path = DEFAULT_SIMULATION_REPORT_PATH,
) -> dict[str, Any]:
    gate_report = load_json(gate_report_path)
    simulation_report = load_json(simulation_report_path)
    blockers = source_blockers(gate_report, simulation_report)
    ready = not blockers
    rows = decision_rows(simulation_report, ready)
    categories = [row["policy_category"] for row in rows]
    status = "pending_user_confirmation" if ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_adoption_decision_draft",
        "scope": "adoption decision draft only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "simulation_gate_report": {
                "path": str(gate_report_path),
                "present": gate_report_path.exists(),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
            },
            "simulation_report": {
                "path": str(simulation_report_path),
                "present": simulation_report_path.exists(),
                "version": simulation_report.get("version"),
                "schema_kind": simulation_report.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "draft_gate": {
            "status": status,
            "requires_user_confirmation": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "allowed_next_step": "series_closeout" if ready else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "draft_row_count": len(rows),
            "policy_categories": categories,
            "suggested_adoption_option_summary": counter_dict(Counter(row.get("suggested_adoption_option") for row in rows)),
            "requires_user_confirmation_count": len([row for row in rows if row.get("requires_user_confirmation") is True]),
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.8.15 v0.4.8.x closeout",
        },
        "adoption_decision_draft_rows": rows,
    }
    forbidden = sorted_unique(find_key_paths(report, FORBIDDEN_KEYS))
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "draft_has_eight_rows", "status": "passed" if len(rows) == 8 else "failed", "row_count": len(rows)},
        {"name": "draft_categories_are_expected", "status": "passed" if categories == EXPECTED_POLICY_ORDER else "failed", "categories": categories},
        {"name": "draft_requires_user_confirmation", "status": "passed" if all(row.get("requires_user_confirmation") is True for row in rows) else "failed"},
        {"name": "draft_is_non_runtime", "status": "passed" if all(row.get("implementation_allowed") is False and row.get("code_patch_authorized") is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["draft_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["draft_gate"]["blockers"] = sorted_unique(blockers + ["output_draft_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("draft_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.14 Final Evidence Selection Policy Adoption Decision Draft",
        "",
        "This draft records suggested adoption routes for human confirmation. It is not a final decision and does not authorize runtime implementation.",
        "",
        "## Overview",
        "",
        f"- Draft status: `{gate.get('status')}`",
        f"- Rows: {summary.get('draft_row_count')}",
        f"- Requires user confirmation: {gate.get('requires_user_confirmation')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Draft Rows",
        "",
        "| Row | Category | Suggested option |",
        "|---|---|---|",
    ]
    for row in as_list(report.get("adoption_decision_draft_rows")):
        lines.append(
            f"| `{row.get('draft_row_id')}` | `{row.get('policy_category')}` | `{row.get('suggested_adoption_option')}` |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This draft requires explicit user confirmation before any later step treats it as a decision.",
        "- It does not run eval, backend calls, RAG, Qdrant, or LLM calls.",
        "- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.",
        "- Any future runtime design still needs a separate approved implementation version.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-report", type=Path, default=DEFAULT_GATE_REPORT_PATH)
    parser.add_argument("--simulation-report", type=Path, default=DEFAULT_SIMULATION_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.gate_report, args.simulation_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy adoption decision draft built: "
        f"{summary.get('status')}, {summary.get('draft_row_count')} rows"
    )
    return 0 if report["draft_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
