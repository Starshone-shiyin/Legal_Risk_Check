"""Build the v0.4.8.11 final-evidence offline simulation input contract.

The contract merges the five categories accepted in v0.4.8.7 with the three
confirmed wording rows from v0.4.8.10. It is saved-report input for a future
offline simulation only; it does not run simulation, call RAG/Qdrant/LLM, or
modify retrieval, rerank, prompts, eval cases, fixtures, rules, or main flow.
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


VERSION = "0.4.8.11"

DEFAULT_CONFIRMED_RECORD_PATH = legacy_report_path("final_evidence_selection_policy_closeout_confirmed_record_report.json")
DEFAULT_LANGUAGE_CONFIRMATION_PATH = legacy_report_path("final_evidence_selection_policy_language_revision_confirmation_record_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_offline_simulation_input_contract_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md")

EXPECTED_ACCEPTED_CATEGORIES = ["primary", "operative", "procedural", "definition_only", "high_risk_manual_review"]
EXPECTED_CONFIRMED_LANGUAGE_CATEGORIES = ["liability", "scenario_core", "coverage_floor"]
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

GUARDRAILS = {
    "contract_only": True,
    "saved_reports_only": True,
    "simulation_not_run": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
    "runtime_selection_policy_patch_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "rag_query_integration": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "main_flow_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
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


def source_meta(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": payload.get("version"),
        "schema_kind": payload.get("schema_kind"),
        "scope": payload.get("scope"),
    }


def closeout_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(source.get("confirmed_rows"))


def language_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(source.get("confirmed_language_revision_rows"))


def source_blockers(closeout: dict[str, Any], language: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    closeout_gate = as_dict(closeout.get("confirmation_gate"))
    language_gate = as_dict(language.get("confirmation_gate"))
    accepted = [
        row for row in closeout_rows(closeout)
        if row.get("confirmed_followup_route") == "future_offline_simulation_design_candidate"
    ]
    if closeout.get("version") != "0.4.8.7":
        blockers.append("closeout_version_mismatch")
    if closeout.get("schema_kind") != "final_evidence_selection_policy_closeout_confirmed_record":
        blockers.append("closeout_schema_mismatch")
    if closeout_gate.get("status") != "confirmed_for_future_offline_design_planning":
        blockers.append("closeout_gate_not_confirmed")
    if closeout_gate.get("implementation_allowed") is not False:
        blockers.append("closeout_implementation_not_blocked")
    if closeout_gate.get("code_patch_authorized") is not False:
        blockers.append("closeout_code_patch_not_blocked")
    if as_list(closeout_gate.get("blockers")):
        blockers.append("closeout_gate_has_blockers")
    if [row.get("policy_category") for row in accepted] != EXPECTED_ACCEPTED_CATEGORIES:
        blockers.append("accepted_category_order_drift")
    if language.get("version") != "0.4.8.10":
        blockers.append("language_version_mismatch")
    if language.get("schema_kind") != "final_evidence_selection_policy_language_revision_confirmation_record":
        blockers.append("language_schema_mismatch")
    if language_gate.get("status") != "confirmed_for_future_offline_simulation_design":
        blockers.append("language_gate_not_confirmed")
    if language_gate.get("may_enter_offline_simulation_design") is not True:
        blockers.append("language_not_ready_for_offline_simulation")
    if language_gate.get("implementation_allowed") is not False:
        blockers.append("language_implementation_not_blocked")
    if language_gate.get("code_patch_authorized") is not False:
        blockers.append("language_code_patch_not_blocked")
    if as_list(language_gate.get("blockers")):
        blockers.append("language_gate_has_blockers")
    if [row.get("policy_category") for row in language_rows(language)] != EXPECTED_CONFIRMED_LANGUAGE_CATEGORIES:
        blockers.append("language_category_order_drift")
    if len(closeout_rows(closeout)) != 8:
        blockers.append("closeout_row_count_drift")
    if len(language_rows(language)) != 3:
        blockers.append("language_row_count_drift")
    for payload_name, payload in [("closeout", closeout), ("language", language)]:
        for path in find_key_paths(payload, FORBIDDEN_KEYS):
            blockers.append(f"{payload_name}_forbidden_key_present:{path.split('.')[-1]}")
        if readability_paths(payload):
            blockers.append(f"{payload_name}_blocked_for_human_readability")
    return sorted_unique(blockers)


def build_policy_rows(closeout: dict[str, Any], language: dict[str, Any], ready: bool) -> list[dict[str, Any]]:
    accepted_by_category = {
        row.get("policy_category"): row
        for row in closeout_rows(closeout)
        if row.get("policy_category") in EXPECTED_ACCEPTED_CATEGORIES
    }
    language_by_category = {row.get("policy_category"): row for row in language_rows(language)}
    rows = []
    for index, category in enumerate(EXPECTED_POLICY_ORDER, start=1):
        if category in accepted_by_category:
            source = accepted_by_category[category]
            rows.append({
                "contract_row_id": f"FES-OFFLINE-SIM-INPUT-{index:03d}",
                "policy_category": category,
                "priority": source.get("priority"),
                "contract_status": "ready_for_saved_report_simulation" if ready else "blocked",
                "source_kind": "v0.4.8.7_confirmed_closeout_category",
                "source_row_id": source.get("confirmed_row_id"),
                "source_policy_id": source.get("source_policy_id"),
                "policy_basis": source.get("confirmed_closeout_option"),
                "policy_wording_status": "accepted_without_language_revision",
                "confirmed_policy_wording": None,
                "simulation_input_allowed": ready,
                "runtime_adoption_status": "not_allowed",
                "implementation_allowed": False,
                "code_patch_authorized": False,
                "source_case_ids": as_list(source.get("source_case_ids")),
            })
        else:
            source = language_by_category[category]
            rows.append({
                "contract_row_id": f"FES-OFFLINE-SIM-INPUT-{index:03d}",
                "policy_category": category,
                "priority": source.get("priority"),
                "contract_status": "ready_for_saved_report_simulation" if ready else "blocked",
                "source_kind": "v0.4.8.10_confirmed_language_revision",
                "source_row_id": source.get("confirmed_row_id"),
                "source_policy_id": source.get("source_policy_id"),
                "policy_basis": source.get("confirmed_post_confirmation_route"),
                "policy_wording_status": "confirmed_language_revision",
                "confirmed_policy_wording": source.get("confirmed_policy_wording"),
                "confirmed_must_not_mean": source.get("confirmed_must_not_mean"),
                "confirmed_acceptance_boundary": source.get("confirmed_acceptance_boundary"),
                "simulation_input_allowed": ready,
                "runtime_adoption_status": "not_allowed",
                "implementation_allowed": False,
                "code_patch_authorized": False,
                "source_case_ids": as_list(source.get("source_case_ids")),
            })
    return rows


def build_report(
    confirmed_record_path: Path = DEFAULT_CONFIRMED_RECORD_PATH,
    language_confirmation_path: Path = DEFAULT_LANGUAGE_CONFIRMATION_PATH,
) -> dict[str, Any]:
    closeout = load_json(confirmed_record_path)
    language = load_json(language_confirmation_path)
    blockers = source_blockers(closeout, language)
    ready = not blockers
    rows = build_policy_rows(closeout, language, ready)
    categories = [row["policy_category"] for row in rows]
    unique_cases = sorted_unique([
        text(case_id)
        for row in rows
        for case_id in as_list(row.get("source_case_ids"))
    ])
    status = "ready_for_saved_report_offline_simulation" if ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_offline_simulation_input_contract",
        "scope": "offline final evidence selection policy simulation input contract only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "closeout_confirmed_record": source_meta(confirmed_record_path, closeout),
            "language_revision_confirmation_record": source_meta(language_confirmation_path, language),
        },
        "guardrails": GUARDRAILS,
        "contract_gate": {
            "status": status,
            "allowed_use": "saved_report_offline_simulation_input_only" if ready else "blocked",
            "simulation_not_run": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "rag_query_integration": "disallowed",
            "blockers": blockers,
        },
        "summary": {
            "status": status,
            "contract_row_count": len(rows),
            "policy_categories": categories,
            "accepted_category_count": len(EXPECTED_ACCEPTED_CATEGORIES),
            "confirmed_language_category_count": len(EXPECTED_CONFIRMED_LANGUAGE_CATEGORIES),
            "unique_case_count": len(unique_cases),
            "priority_summary": counter_dict(Counter(row.get("priority") for row in rows)),
            "simulation_not_run": True,
            "implementation_allowed": False,
            "next_version_recommendation": "v0.4.8.12 saved-report offline simulation runner",
        },
        "simulation_input_contract_rows": rows,
        "traceability": {
            "source_reports": [str(confirmed_record_path), str(language_confirmation_path)],
            "source_case_ids": unique_cases,
            "policy_categories": categories,
        },
    }
    forbidden = sorted_unique([
        key for node in walk(report) if isinstance(node, dict) for key in (FORBIDDEN_KEYS & set(node))
    ])
    readable = readability_paths(report)
    report["assertions"] = [
        {"name": "sources_ready", "status": "passed" if not blockers else "failed", "blockers": blockers},
        {"name": "contract_has_eight_rows", "status": "passed" if len(rows) == 8 else "failed", "row_count": len(rows)},
        {"name": "contract_categories_are_expected", "status": "passed" if categories == EXPECTED_POLICY_ORDER else "failed", "categories": categories},
        {"name": "contract_is_non_runtime", "status": "passed" if all(row["implementation_allowed"] is False and row["code_patch_authorized"] is False for row in rows) else "failed"},
        {"name": "forbidden_output_keys_absent", "status": "passed" if not forbidden else "failed", "forbidden_keys": forbidden},
        {"name": "text_readability_gate", "status": "passed" if not readable else "failed", "mojibake_like_paths": readable},
    ]
    if forbidden or readable:
        report["contract_gate"]["status"] = "blocked"
        report["contract_gate"]["allowed_use"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["contract_gate"]["blockers"] = sorted_unique(blockers + ["output_contract_violation"])
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("contract_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.11 Final Evidence Selection Policy Offline Simulation Input Contract",
        "",
        "This contract merges the five accepted policy categories and three confirmed language revisions into saved-report-only input for a future offline simulation. It does not run simulation and does not authorize runtime changes.",
        "",
        "## Overview",
        "",
        f"- Contract status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Contract rows: {summary.get('contract_row_count')}",
        f"- Policy categories: {', '.join(as_list(summary.get('policy_categories')))}",
        f"- Simulation not run: {summary.get('simulation_not_run')}",
        f"- Implementation allowed: {summary.get('implementation_allowed')}",
        "",
        "## Contract Rows",
        "",
        "| Row | Category | Source | Wording status | Simulation input |",
        "|---|---|---|---|---|",
    ]
    for row in as_list(report.get("simulation_input_contract_rows")):
        lines.append(
            f"| `{row.get('contract_row_id')}` | `{row.get('policy_category')}` | `{row.get('source_kind')}` | `{row.get('policy_wording_status')}` | {row.get('simulation_input_allowed')} |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This contract is input only for later saved-report offline simulation.",
        "- It does not run simulation, full eval, RAG, Qdrant, or LLM calls.",
        "- It does not modify `rag_query`, rerank, prompts, eval cases, fixtures, rules, schemas, or imports.",
        "- `implementation_allowed=false` and `code_patch_authorized=false` remain fixed.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirmed-record", type=Path, default=DEFAULT_CONFIRMED_RECORD_PATH)
    parser.add_argument("--language-confirmation", type=Path, default=DEFAULT_LANGUAGE_CONFIRMATION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()
    report = build_report(args.confirmed_record, args.language_confirmation)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Final evidence selection policy offline simulation input contract built: "
        f"{summary.get('status')}, {summary.get('contract_row_count')} rows"
    )
    return 0 if report["contract_gate"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
