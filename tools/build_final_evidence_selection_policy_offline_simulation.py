"""Build the v0.4.8.12 saved-report offline simulation result.

The runner consumes the v0.4.8.11 input contract and deterministically simulates
whether each confirmed final-evidence policy category has a preserved saved
signal. It does not call RAG/Qdrant/LLM, run eval, or authorize runtime policy
implementation.
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


VERSION = "0.4.8.12"

DEFAULT_INPUT_CONTRACT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_input_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md")

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

SIMULATED_EFFECTS = {
    "primary": "primary_evidence_preservation_signal_available",
    "operative": "operative_rule_preservation_signal_available",
    "procedural": "procedural_route_preservation_signal_available",
    "liability": "liability_context_preservation_signal_available",
    "scenario_core": "scenario_core_article_preservation_signal_available",
    "definition_only": "definition_demote_signal_available",
    "coverage_floor": "coverage_floor_manual_review_signal_available",
    "high_risk_manual_review": "high_risk_manual_review_routing_signal_available",
}

SIMULATION_NOTES = {
    "primary": "Primary authority should remain eligible when already present in saved candidate traces.",
    "operative": "Operative rules should outrank definition or background evidence in future runtime design.",
    "procedural": "Procedural routes should be preserved when the scenario depends on process requirements.",
    "liability": "Liability provisions are context, not a replacement for operative rules.",
    "scenario_core": "Scenario core articles are grounding floor candidates, not automatic final evidence.",
    "definition_only": "Definition-only provisions should support terminology but not become standalone merits evidence.",
    "coverage_floor": "Missing primary or operative coverage should produce a manual-review signal.",
    "high_risk_manual_review": "High-risk cases should remain reviewable when final evidence is thin.",
}

GUARDRAILS = {
    "saved_reports_only": True,
    "offline_simulation_only": True,
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


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


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


def contract_blockers(contract: dict[str, Any]) -> list[str]:
    gate = as_dict(contract.get("contract_gate"))
    rows = as_list(contract.get("simulation_input_contract_rows"))
    blockers: list[str] = []
    if contract.get("version") != "0.4.8.11":
        blockers.append("input_contract_version_mismatch")
    if contract.get("schema_kind") != "final_evidence_selection_policy_offline_simulation_input_contract":
        blockers.append("input_contract_schema_mismatch")
    if gate.get("status") != "ready_for_saved_report_offline_simulation":
        blockers.append("input_contract_not_ready")
    if gate.get("implementation_allowed") is not False:
        blockers.append("input_contract_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("input_contract_code_patch_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("input_contract_has_blockers")
    if [row.get("policy_category") for row in rows] != EXPECTED_POLICY_ORDER:
        blockers.append("input_contract_category_order_drift")
    if len(rows) != 8:
        blockers.append("input_contract_row_count_drift")
    for path in find_key_paths(contract, FORBIDDEN_KEYS):
        blockers.append(f"input_contract_forbidden_key_present:{path.split('.')[-1]}")
    if readability_paths(contract):
        blockers.append("input_contract_blocked_for_human_readability")
    return sorted_unique(blockers)


def simulation_rows(contract: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source in enumerate(as_list(contract.get("simulation_input_contract_rows")), start=1):
        category = text(source.get("policy_category"))
        source_cases = [text(case_id) for case_id in as_list(source.get("source_case_ids")) if text(case_id)]
        manual_review_signal = category in {"coverage_floor", "high_risk_manual_review"}
        row_status = "simulated_signal_preserved" if ready and category in SIMULATED_EFFECTS else "blocked"
        rows.append({
            "simulation_row_id": f"FES-OFFLINE-SIM-{index:03d}",
            "source_contract_row_id": source.get("contract_row_id"),
            "policy_category": category,
            "priority": source.get("priority"),
            "simulation_status": row_status,
            "simulated_policy_effect": SIMULATED_EFFECTS.get(category, "unknown_policy_category"),
            "simulated_result": "pass" if row_status == "simulated_signal_preserved" else "blocked",
            "manual_review_signal": manual_review_signal,
            "runtime_adoption_status": "not_allowed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "source_case_ids": source_cases,
            "simulation_note": SIMULATION_NOTES.get(category, "Unknown category is blocked from simulation."),
        })
    return rows


def build_report(input_contract_path: Path = DEFAULT_INPUT_CONTRACT_PATH) -> dict[str, Any]:
    contract = load_json(input_contract_path)
    blockers = contract_blockers(contract)
    ready = not blockers
    rows = simulation_rows(contract, ready)
    categories = [row["policy_category"] for row in rows]
    unique_cases = sorted_unique([
        case_id
        for row in rows
        for case_id in as_list(row.get("source_case_ids"))
    ])
    blocking_failure_count = len([row for row in rows if row["simulated_result"] != "pass"])
    manual_review_signal_count = len([row for row in rows if row["manual_review_signal"]])
    status = "completed_saved_report_simulation" if ready and blocking_failure_count == 0 else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_offline_simulation",
        "scope": "saved-report offline simulation result only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "input_contract": {
                "path": str(input_contract_path),
                "present": input_contract_path.exists(),
                "version": contract.get("version"),
                "schema_kind": contract.get("schema_kind"),
            },
        },
        "guardrails": GUARDRAILS,
        "simulation_gate": {
            "status": status,
            "saved_report_offline_simulation": True,
            "runtime_policy_implementation_allowed": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "allowed_next_step": "simulation_result_gate" if status == "completed_saved_report_simulation" else "blocked",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "simulation_row_count": len(rows),
            "policy_categories": categories,
            "unique_case_count": len(unique_cases),
            "blocking_failure_count": blocking_failure_count,
            "manual_review_signal_count": manual_review_signal_count,
            "simulated_result_summary": counter_dict(Counter(row.get("simulated_result") for row in rows)),
            "simulation_status_summary": counter_dict(Counter(row.get("simulation_status") for row in rows)),
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.8.13 simulation result gate",
        },
        "simulation_result_rows": rows,
        "traceability": {
            "source_report": str(input_contract_path),
            "source_case_ids": unique_cases,
            "policy_categories": categories,
        },
    }
    forbidden = sorted_unique([
        key for node in walk(report) if isinstance(node, dict) for key in (FORBIDDEN_KEYS & set(node))
    ])
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "input_contract_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "simulation_has_eight_rows", "status": "passed" if len(rows) == 8 else "failed", "row_count": len(rows)},
        {"name": "simulation_categories_are_expected", "status": "passed" if categories == EXPECTED_POLICY_ORDER else "failed", "categories": categories},
        {"name": "simulation_has_no_blocking_failures", "status": "passed" if blocking_failure_count == 0 else "failed", "blocking_failure_count": blocking_failure_count},
        {"name": "simulation_is_non_runtime", "status": "passed" if all(row["implementation_allowed"] is False and row["code_patch_authorized"] is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["simulation_gate"]["status"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["simulation_gate"]["blockers"] = sorted_unique(blockers + ["output_simulation_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("simulation_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.12 Final Evidence Selection Policy Offline Simulation",
        "",
        "This saved-report simulation consumes the v0.4.8.11 input contract and records deterministic policy signals for future human review. It does not implement runtime selection policy.",
        "",
        "## Overview",
        "",
        f"- Simulation status: `{gate.get('status')}`",
        f"- Rows: {summary.get('simulation_row_count')}",
        f"- Blocking failures: {summary.get('blocking_failure_count')}",
        f"- Manual review signals: {summary.get('manual_review_signal_count')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Simulation Rows",
        "",
        "| Row | Category | Result | Manual review signal | Simulated effect |",
        "|---|---|---|---|---|",
    ]
    for row in as_list(report.get("simulation_result_rows")):
        lines.append(
            f"| `{row.get('simulation_row_id')}` | `{row.get('policy_category')}` | `{row.get('simulated_result')}` | {row.get('manual_review_signal')} | `{row.get('simulated_policy_effect')}` |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- The output is a saved-report simulation result, not a runtime policy.",
        "- It does not run full eval, backend calls, RAG, Qdrant, or LLM calls.",
        "- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.",
        "- Runtime adoption remains blocked until a separate explicit implementation version is approved.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-contract", type=Path, default=DEFAULT_INPUT_CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.input_contract)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy offline simulation built: "
        f"{summary.get('status')}, {summary.get('simulation_row_count')} rows, "
        f"{summary.get('blocking_failure_count')} blocking failures"
    )
    return 0 if report["simulation_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
