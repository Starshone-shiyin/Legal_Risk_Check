"""Build the v0.4.8.8 final-evidence policy language revision worksheet.

The worksheet reads the saved v0.4.8.7 confirmed record and prepares the three
confirmed rows that require policy-language revision before offline simulation.
It is a saved-report worksheet only: no runtime policy, RAG, rerank, prompts,
eval cases, fixtures, rules, Qdrant, LLM, or main-flow behavior is changed.
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


VERSION = "0.4.8.8"

DEFAULT_CONFIRMED_RECORD_PATH = legacy_report_path(
    "final_evidence_selection_policy_closeout_confirmed_record_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "final_evidence_selection_policy_language_revision_worksheet_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md"
)

EXPECTED_SOURCE_VERSION = "0.4.8.7"
EXPECTED_SOURCE_SCHEMA = "final_evidence_selection_policy_closeout_confirmed_record"
EXPECTED_SOURCE_SCOPE = "offline final evidence selection policy closeout confirmed record only"
EXPECTED_SOURCE_STATUS = "confirmed_for_future_offline_design_planning"
EXPECTED_ROW_COUNT = 8
EXPECTED_CASE_COUNT = 5
EXPECTED_REVISION_CATEGORIES = ["liability", "scenario_core", "coverage_floor"]
EXPECTED_SIMULATION_CATEGORIES = [
    "primary",
    "operative",
    "procedural",
    "definition_only",
    "high_risk_manual_review",
]
EXPECTED_REVISION_OPTION = "revise_policy_language_before_closeout"
EXPECTED_REVISION_ROUTE = "policy_language_revision_required_before_simulation"
EXPECTED_SIMULATION_ROUTE = "future_offline_simulation_design_candidate"

REVISION_GUIDANCE = {
    "liability": {
        "revision_focus": "Separate liability or consequence evidence from operative-rule evidence.",
        "wording_risk": "Language that forces liability evidence into every final set can over-select penalty or consequence provisions even when the legal question only needs an operative rule.",
        "target_boundary": "Require liability evidence only when the answer asserts penalties, liability exposure, enforcement consequence, or remedy consequence.",
        "simulation_entry_condition": "A later simulator may test liability preservation only after the row states when liability evidence is required and when it is optional.",
    },
    "scenario_core": {
        "revision_focus": "Narrow scenario-core preservation to legally essential scenario facts rather than broad scenario labels.",
        "wording_risk": "Broad scenario-core wording can preserve topical but non-operative materials and mask weak base retrieval.",
        "target_boundary": "Tie scenario-core preservation to case facts that change the applicable legal requirement, such as cross-border transfer, automated decision, sensitive personal information, or employee/consumer context.",
        "simulation_entry_condition": "A later simulator may test scenario-core preservation only after the row defines legally material scenario facts and acceptable substitutes.",
    },
    "coverage_floor": {
        "revision_focus": "Define a minimum evidence floor without making every case require every evidence class.",
        "wording_risk": "An overbroad coverage floor can re-create score fusion behavior by forcing unrelated evidence into the final set.",
        "target_boundary": "Require coverage only for issue types that are actually present in the case and allow explicit no-applicable-evidence outcomes.",
        "simulation_entry_condition": "A later simulator may test coverage floor behavior only after the row defines issue-conditioned minimums and stop conditions.",
    },
}

WORKSHEET_GUARDRAILS = {
    "worksheet_only": True,
    "source_confirmed_record_only": True,
    "policy_language_revision_only": True,
    "formal_policy_language_outcome_recorded": False,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
    "runtime_selection_policy_patch_allowed": False,
    "rerank_change_allowed": False,
    "prompt_change_allowed": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "fixture_write_to_eval": "disallowed",
    "schema_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "rag_query_integration": "disallowed",
    "main_flow_mutation": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
}

FORBIDDEN_SOURCE_KEYS = {
    "approved",
    "approved_actions",
    "authorized_actions",
    "ready_to_apply",
    "ready_to_implement",
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "migration_steps",
    "work_items",
    "engineering_tasks",
    "pending_tasks",
    "implementation_queue",
    "completed_decisions",
    "formal_review_outcomes",
    "reviewer_decision",
    "human_outcome_record",
}

FORBIDDEN_OUTPUT_KEYS = set(FORBIDDEN_SOURCE_KEYS)

ADVISORY_SOURCE_KEYS = {
    "ai_suggestion",
    "safe_ai_suggestion_input",
    "advisory_packet_only",
    "prescreen_advisory",
    "pilot_assist",
    "mobile_aid",
    "contains_completed_manual_decisions",
}

MOJIBAKE_MARKERS = [
    "\u951b",
    "\u7ecb",
    "\u9428",
    "\u93c2",
    "\u6d93",
    "\u4e63",
    "\ufffd",
]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def counter_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: item[0]))


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


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def source_meta(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "schema_kind": payload.get("schema_kind"),
    }


def find_key_paths(value: Any, blocked_keys: set[str], prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if key in blocked_keys:
                paths.append(child_path)
            paths.extend(find_key_paths(child, blocked_keys, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_key_paths(child, blocked_keys, f"{prefix}[{index}]"))
    return paths


def find_string_paths_with_markers(value: Any, prefix: str = "$") -> list[str]:
    paths = []
    if isinstance(value, str):
        if any(marker in value for marker in MOJIBAKE_MARKERS):
            paths.append(prefix)
    elif isinstance(value, dict):
        for key, child in value.items():
            paths.extend(find_string_paths_with_markers(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(find_string_paths_with_markers(child, f"{prefix}[{index}]"))
    return paths


def confirmed_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(source.get("confirmed_rows"))


def revision_source_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in confirmed_rows(source)
        if row.get("confirmed_followup_route") == EXPECTED_REVISION_ROUTE
    ]


def source_contract_blockers(source: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(source.get("confirmation_gate"))
    summary = as_dict(source.get("summary"))
    handoff = as_dict(source.get("next_version_handoff"))
    rows = confirmed_rows(source)
    revision_rows = revision_source_rows(source)

    if source.get("version") != EXPECTED_SOURCE_VERSION:
        blockers.append("source_version_mismatch")
    if source.get("schema_kind") != EXPECTED_SOURCE_SCHEMA:
        blockers.append("source_schema_mismatch")
    if source.get("scope") != EXPECTED_SOURCE_SCOPE:
        blockers.append("source_scope_mismatch")
    if gate.get("status") != EXPECTED_SOURCE_STATUS:
        blockers.append("source_gate_not_confirmed")
    if gate.get("user_confirmation_recorded") is not True:
        blockers.append("source_user_confirmation_missing")
    if gate.get("formal_policy_closeout_recorded") is not True:
        blockers.append("source_policy_closeout_missing")
    if gate.get("implementation_allowed") is not False:
        blockers.append("source_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("source_code_patch_not_blocked")
    if gate.get("runtime_policy_implementation_allowed") is not False:
        blockers.append("source_runtime_policy_not_blocked")
    if gate.get("runtime_selection_policy_patch_allowed") is not False:
        blockers.append("source_runtime_selection_not_blocked")
    if gate.get("rerank_change_allowed") is not False:
        blockers.append("source_rerank_not_blocked")
    if gate.get("prompt_change_allowed") is not False:
        blockers.append("source_prompt_not_blocked")
    if gate.get("rag_query_integration") != "disallowed":
        blockers.append("source_rag_query_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("source_gate_has_blockers")
    if summary.get("confirmed_row_count") != EXPECTED_ROW_COUNT:
        blockers.append("source_row_count_summary_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("source_case_count_drift")
    if summary.get("implementation_allowed") is not False:
        blockers.append("source_summary_implementation_not_blocked")
    if summary.get("confirmed_followup_route_summary", {}).get(EXPECTED_REVISION_ROUTE) != len(EXPECTED_REVISION_CATEGORIES):
        blockers.append("source_revision_route_count_drift")
    if summary.get("confirmed_followup_route_summary", {}).get(EXPECTED_SIMULATION_ROUTE) != len(EXPECTED_SIMULATION_CATEGORIES):
        blockers.append("source_simulation_route_count_drift")
    if len(rows) != EXPECTED_ROW_COUNT:
        blockers.append("source_row_count_drift")
    if len(revision_rows) != len(EXPECTED_REVISION_CATEGORIES):
        blockers.append("source_revision_row_count_drift")
    if [row.get("policy_category") for row in revision_rows] != EXPECTED_REVISION_CATEGORIES:
        blockers.append("source_revision_category_order_drift")
    if as_list(handoff.get("requires_policy_language_revision_before_simulation")) != EXPECTED_REVISION_CATEGORIES:
        blockers.append("source_handoff_revision_categories_drift")
    if as_list(handoff.get("accepted_for_future_offline_simulation_design")) != EXPECTED_SIMULATION_CATEGORIES:
        blockers.append("source_handoff_simulation_categories_drift")

    for row in revision_rows:
        category = text(row.get("policy_category"))
        if row.get("confirmed_closeout_option") != EXPECTED_REVISION_OPTION:
            blockers.append(f"source_revision_option_drift:{category}")
        if row.get("user_confirmation_recorded") is not True:
            blockers.append(f"source_revision_row_unconfirmed:{category}")
        if row.get("implementation_allowed") is not False:
            blockers.append(f"source_revision_row_implementation_not_blocked:{category}")
        if row.get("code_patch_authorized") is not False:
            blockers.append(f"source_revision_row_code_patch_not_blocked:{category}")
        if row.get("candidate_route_authorized") is not False:
            blockers.append(f"source_revision_row_route_authorized:{category}")
        if not as_list(row.get("source_case_ids")):
            blockers.append(f"source_revision_row_missing_cases:{category}")

    for path in find_key_paths(source, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"source_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(source, ADVISORY_SOURCE_KEYS):
        blockers.append(f"source_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(source):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_revision_rows(source: dict[str, Any], worksheet_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(revision_source_rows(source), start=1):
        category = text(source_row.get("policy_category"))
        guidance = REVISION_GUIDANCE[category]
        rows.append({
            "worksheet_row_id": f"FES-POLICY-LANGUAGE-REVISION-{index:03d}",
            "source_confirmed_row_id": source_row.get("confirmed_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": category,
            "priority": source_row.get("priority"),
            "worksheet_status": "ready_for_policy_language_review" if worksheet_ready else "blocked",
            "confirmed_closeout_option": source_row.get("confirmed_closeout_option"),
            "confirmed_followup_route": source_row.get("confirmed_followup_route"),
            "revision_focus": guidance["revision_focus"],
            "wording_risk": guidance["wording_risk"],
            "target_boundary": guidance["target_boundary"],
            "simulation_entry_condition": guidance["simulation_entry_condition"],
            "acceptance_checks": [
                "The row names when the policy applies and when it does not apply.",
                "The row does not force unrelated evidence into the final evidence set.",
                "The row preserves traceability to source cases without creating case-specific patches.",
                "The row remains suitable for a later offline simulator without authorizing runtime adoption.",
            ],
            "review_questions": [
                "Is the policy category legally necessary for the source cases?",
                "Which words would over-preserve non-operative or unrelated evidence?",
                "What explicit stop condition prevents broad fallback behavior?",
                "What minimal source-case evidence is needed before a later simulator can test this row?",
            ],
            "case_count": int(source_row.get("case_count", 0)),
            "source_case_ids": as_list(source_row.get("source_case_ids")),
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "traceability": {
                "source_report": str(DEFAULT_CONFIRMED_RECORD_PATH),
                "source_confirmed_row_id": source_row.get("confirmed_row_id"),
                "source_policy_id": source_row.get("source_policy_id"),
                "source_case_ids": as_list(source_row.get("source_case_ids")),
            },
        })
    return rows


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def readability_violations(report: dict[str, Any]) -> list[str]:
    return sorted_unique(find_string_paths_with_markers(report))


def build_summary(status: str, rows: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]:
    priority_counter = Counter(text(row.get("priority")) or "unknown" for row in rows)
    unique_case_ids = {
        text(case_id)
        for row in rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    return {
        "status": status,
        "allowed_use": "policy_language_revision_worksheet_only" if status != "blocked" else "blocked",
        "source_confirmed_record_status": as_dict(source.get("confirmation_gate")).get("status"),
        "revision_row_count": len(rows),
        "source_confirmed_row_count": len(confirmed_rows(source)),
        "source_revision_row_count": len(revision_source_rows(source)),
        "unique_case_count": len(unique_case_ids),
        "revision_categories": [row.get("policy_category") for row in rows],
        "priority_summary": counter_dict(priority_counter),
        "formal_policy_language_outcome_recorded": False,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "prompt_change_allowed": False,
        "rag_query_integration": "disallowed",
        "recommended_next_step": "use this worksheet to revise policy language before building offline simulation design spec",
    }


def build_assertions(
    source_blockers: list[str],
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_revision_ids = {text(row.get("confirmed_row_id")) for row in revision_source_rows(source)}
    worksheet_source_ids = {text(row.get("source_confirmed_row_id")) for row in rows}
    unique_case_ids = {
        text(case_id)
        for row in rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    source_readability_blockers = [
        blocker for blocker in source_blockers if blocker == "blocked_for_human_readability"
    ]
    return [
        {
            "name": "source_confirmed_record_is_ready_for_language_revision",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "worksheet_covers_all_revision_rows",
            "status": "passed" if source_revision_ids and source_revision_ids == worksheet_source_ids else "failed",
            "source_revision_row_count": len(source_revision_ids),
            "worksheet_source_row_count": len(worksheet_source_ids),
            "missing_source_row_ids": sorted(source_revision_ids - worksheet_source_ids),
        },
        {
            "name": "worksheet_has_three_revision_rows",
            "status": "passed" if len(rows) == len(EXPECTED_REVISION_CATEGORIES) else "failed",
            "revision_row_count": len(rows),
            "expected": len(EXPECTED_REVISION_CATEGORIES),
        },
        {
            "name": "worksheet_categories_are_expected",
            "status": "passed" if [row.get("policy_category") for row in rows] == EXPECTED_REVISION_CATEGORIES else "failed",
            "categories": [row.get("policy_category") for row in rows],
            "expected": EXPECTED_REVISION_CATEGORIES,
        },
        {
            "name": "worksheet_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) >= 4 else "failed",
            "unique_case_count": len(unique_case_ids),
            "source_case_ids": sorted(unique_case_ids),
        },
        {
            "name": "worksheet_is_non_runtime",
            "status": "passed"
            if all(
                row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("runtime_adoption_status") == "not_allowed"
                for row in rows
            )
            else "failed",
        },
        {
            "name": "forbidden_output_keys_absent",
            "status": "passed" if not output_forbidden_keys else "failed",
            "forbidden_keys": output_forbidden_keys,
        },
        {
            "name": "text_readability_gate",
            "status": "passed" if not readability_errors and not source_readability_blockers else "failed",
            "source_readability_blockers": source_readability_blockers,
            "mojibake_like_paths": readability_errors,
        },
    ]


def build_report(confirmed_record_path: Path = DEFAULT_CONFIRMED_RECORD_PATH) -> dict[str, Any]:
    source = load_json(confirmed_record_path)
    source_blockers = source_contract_blockers(source)
    worksheet_ready = not source_blockers
    rows = build_revision_rows(source, worksheet_ready)
    status = "ready_for_policy_language_revision_review" if worksheet_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_language_revision_worksheet",
        "scope": "offline final evidence selection policy language revision worksheet only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_closeout_confirmed_record": source_meta(confirmed_record_path, source),
        },
        "guardrails": WORKSHEET_GUARDRAILS,
        "worksheet_gate": {
            "status": status,
            "allowed_use": "policy_language_revision_worksheet_only" if worksheet_ready else "blocked",
            "saved_report_only": True,
            "formal_policy_language_outcome_recorded": False,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "rag_query_integration": "disallowed",
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
            "blockers": source_blockers,
        },
        "summary": build_summary(status, rows, source),
        "revision_worksheet_rows": rows,
        "simulation_design_dependency": {
            "accepted_categories_waiting_for_simulation_design": EXPECTED_SIMULATION_CATEGORIES,
            "revision_categories_required_first": EXPECTED_REVISION_CATEGORIES,
            "simulation_design_should_wait_for_revision_closeout": True,
            "runtime_implementation_allowed": False,
        },
        "excluded_scope": {
            "runtime_policy_patch": "disallowed",
            "rerank_or_prompt_change": "disallowed",
            "hidden_seed_anchor_eval_fixture_mutation": "disallowed",
            "backend_qdrant_llm_access": "disallowed",
            "full_eval": "not_run",
        },
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_report": str(confirmed_record_path),
            "source_confirmed_record_version": source.get("version"),
            "source_confirmed_row_ids": [row.get("confirmed_row_id") for row in revision_source_rows(source)],
            "worksheet_row_ids": [row.get("worksheet_row_id") for row in rows],
            "source_policy_ids": [row.get("source_policy_id") for row in rows],
            "source_case_ids": sorted_unique([
                text(case_id)
                for row in rows
                for case_id in as_list(row.get("source_case_ids"))
            ]),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        rows,
        source,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["worksheet_gate"]["status"] = "blocked"
        report["worksheet_gate"]["allowed_use"] = "blocked"
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["worksheet_gate"]["blockers"] = sorted_unique(report["worksheet_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("worksheet_gate"))
    summary = as_dict(report.get("summary"))
    dependency = as_dict(report.get("simulation_design_dependency"))
    lines = [
        "# v0.4.8.8 Final Evidence Selection Policy Language Revision Worksheet",
        "",
        "This worksheet prepares policy-language revision for the three confirmed rows that must be narrowed before offline simulation design. It does not record final wording, does not authorize runtime policy, and does not modify RAG, rerank, prompts, eval cases, fixtures, or rules.",
        "",
        "## Overview",
        "",
        f"- Worksheet status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Revision rows: {summary.get('revision_row_count')}",
        f"- Revision categories: {', '.join(as_list(summary.get('revision_categories')))}",
        f"- Unique cases: {summary.get('unique_case_count')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        "",
        "## Revision Rows",
        "",
        "| Row | Policy | Priority | Revision focus | Simulation entry condition |",
        "|---|---|---|---|---|",
    ]
    for row in as_list(report.get("revision_worksheet_rows")):
        lines.append(
            "| `{}` | `{}` | `{}` | {} | {} |".format(
                row.get("worksheet_row_id"),
                row.get("policy_category"),
                row.get("priority"),
                row.get("revision_focus"),
                row.get("simulation_entry_condition"),
            )
        )
    lines.extend(["", "## Review Questions", ""])
    for row in as_list(report.get("revision_worksheet_rows")):
        lines.extend([
            f"### {row.get('policy_category')}",
            f"- Wording risk: {row.get('wording_risk')}",
            f"- Target boundary: {row.get('target_boundary')}",
            "- Questions:",
        ])
        for question in as_list(row.get("review_questions")):
            lines.append(f"  - {question}")
        lines.append("")
    lines.extend([
        "## Simulation Dependency",
        "",
        f"- Accepted categories waiting for simulation design: {', '.join(as_list(dependency.get('accepted_categories_waiting_for_simulation_design')))}",
        f"- Revision categories required first: {', '.join(as_list(dependency.get('revision_categories_required_first')))}",
        f"- Simulation design should wait for revision closeout: {dependency.get('simulation_design_should_wait_for_revision_closeout')}",
        "",
        "## Boundaries",
        "",
        "- This worksheet is for language review only.",
        "- It does not finalize policy wording.",
        "- `implementation_allowed=false` and `code_patch_authorized=false` must remain unchanged.",
        "- It does not implement runtime policy, final evidence selection runtime, rerank, prompt, or eval case changes.",
        "- It does not modify anchors, hidden seeds, risk supplement, term preservation, scenario registry, fixtures, schema, importer, or dry-run contracts.",
        "- It does not call backend services, Qdrant, LLMs, RAG, or full eval.",
        "",
        "## Sources",
        "",
    ])
    for role, meta in as_dict(report.get("inputs")).items():
        lines.append(f"- {role}: `{meta.get('path')}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirmed-record", type=Path, default=DEFAULT_CONFIRMED_RECORD_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.confirmed_record)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))

    summary = as_dict(report.get("summary"))
    print(
        "Final evidence selection policy language revision worksheet built: "
        f"{summary.get('status')}, {summary.get('revision_row_count')} rows, "
        f"{summary.get('unique_case_count')} cases"
    )
    return 0 if as_dict(report.get("worksheet_gate")).get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
