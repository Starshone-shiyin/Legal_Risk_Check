"""Build the v0.4.8.7 final-evidence policy closeout confirmed record.

The record reads the saved v0.4.8.6 confirmation scaffold and records the
user's explicit confirmation of all eight suggested closeout options. It may be
used as future offline design-planning input only; it does not authorize runtime
policy, code patches, RAG, rerank, prompts, eval cases, or any main-flow change.
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


VERSION = "0.4.8.7"

DEFAULT_SCAFFOLD_REPORT_PATH = legacy_report_path(
    "final_evidence_selection_policy_closeout_confirmation_record_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "final_evidence_selection_policy_closeout_confirmed_record_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md"
)

EXPECTED_SCAFFOLD_VERSION = "0.4.8.6"
EXPECTED_SCAFFOLD_SCHEMA = "final_evidence_selection_policy_closeout_confirmation_record_scaffold"
EXPECTED_SCAFFOLD_SCOPE = (
    "offline final evidence selection policy human closeout confirmation scaffold only"
)
EXPECTED_SCAFFOLD_STATUS = "pending_user_confirmation"
EXPECTED_ROW_COUNT = 8
EXPECTED_CASE_COUNT = 5
EXPECTED_POLICY_CATEGORIES = [
    "primary",
    "operative",
    "procedural",
    "liability",
    "scenario_core",
    "definition_only",
    "coverage_floor",
    "high_risk_manual_review",
]
EXPECTED_SOURCE_POLICY_IDS = [f"FES-POLICY-DRAFT-{index:03d}" for index in range(1, 9)]
EXPECTED_SUGGESTED_OPTIONS = {
    "primary": "accept_for_future_offline_simulation_design",
    "operative": "accept_for_future_offline_simulation_design",
    "procedural": "accept_for_future_offline_simulation_design",
    "liability": "revise_policy_language_before_closeout",
    "scenario_core": "revise_policy_language_before_closeout",
    "definition_only": "accept_for_future_offline_simulation_design",
    "coverage_floor": "revise_policy_language_before_closeout",
    "high_risk_manual_review": "accept_for_future_offline_simulation_design",
}

USER_CONFIRMATION_CONTEXT = {
    "source": "chat_user_confirmation",
    "confirmation_text": "确认以上 8 条，按 suggested closeout option 生成 v0.4.8.7。",
    "confirmed_at_version": VERSION,
    "confirmed_scope": "final_evidence_selection_policy_closeout_options_only",
    "selected_confirmation_option": "confirm_suggested_closeout_option",
    "implementation_allowed": False,
}

CONFIRMED_RECORD_GUARDRAILS = {
    "confirmation_record_only": True,
    "source_scaffold_only": True,
    "user_confirmation_recorded": True,
    "formal_policy_closeout_recorded": True,
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
    "confirmed_route_to_work_items": "disallowed",
    "fixture_write_to_eval": "disallowed",
    "schema_mutation": "disallowed",
    "manual_review_schema_mutation": "disallowed",
    "manual_review_importer_mutation": "disallowed",
    "manual_review_dry_run_contract_mutation": "disallowed",
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


def scaffold_rows(scaffold: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(scaffold.get("confirmation_scaffold_rows"))


def source_contract_blockers(scaffold: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(scaffold.get("confirmation_gate"))
    summary = as_dict(scaffold.get("summary"))
    rows = scaffold_rows(scaffold)

    if scaffold.get("version") != EXPECTED_SCAFFOLD_VERSION:
        blockers.append("scaffold_version_mismatch")
    if scaffold.get("schema_kind") != EXPECTED_SCAFFOLD_SCHEMA:
        blockers.append("scaffold_schema_mismatch")
    if scaffold.get("scope") != EXPECTED_SCAFFOLD_SCOPE:
        blockers.append("scaffold_scope_mismatch")
    if gate.get("status") != EXPECTED_SCAFFOLD_STATUS:
        blockers.append("scaffold_gate_not_pending_confirmation")
    if gate.get("confirmation_scaffold_allowed") is not True:
        blockers.append("scaffold_not_allowed")
    if gate.get("requires_user_confirmation") is not True:
        blockers.append("scaffold_does_not_require_user_confirmation")
    if gate.get("user_confirmation_recorded") is not False:
        blockers.append("scaffold_already_records_user_confirmation")
    if gate.get("formal_human_outcome_recorded") is not False:
        blockers.append("scaffold_records_formal_outcome")
    if gate.get("implementation_allowed") is not False:
        blockers.append("scaffold_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("scaffold_code_patch_not_blocked")
    if gate.get("runtime_policy_implementation_allowed") is not False:
        blockers.append("scaffold_runtime_policy_not_blocked")
    if gate.get("runtime_selection_policy_patch_allowed") is not False:
        blockers.append("scaffold_runtime_selection_not_blocked")
    if gate.get("rerank_change_allowed") is not False:
        blockers.append("scaffold_rerank_not_blocked")
    if gate.get("prompt_change_allowed") is not False:
        blockers.append("scaffold_prompt_not_blocked")
    if gate.get("rag_query_integration") != "disallowed":
        blockers.append("scaffold_rag_query_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("scaffold_gate_has_blockers")
    if summary.get("confirmation_row_count") != EXPECTED_ROW_COUNT:
        blockers.append("scaffold_row_count_summary_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("scaffold_case_count_drift")
    if summary.get("pending_user_confirmation_count") != EXPECTED_ROW_COUNT:
        blockers.append("scaffold_pending_count_drift")
    if summary.get("user_confirmation_recorded") is not False:
        blockers.append("scaffold_summary_already_confirmed")
    if len(rows) != EXPECTED_ROW_COUNT:
        blockers.append("scaffold_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_POLICY_CATEGORIES:
        blockers.append("scaffold_policy_category_order_drift")
    if [row.get("source_policy_id") for row in rows] != EXPECTED_SOURCE_POLICY_IDS:
        blockers.append("scaffold_policy_id_order_drift")
    if any(row.get("confirmation_status") != EXPECTED_SCAFFOLD_STATUS for row in rows):
        blockers.append("scaffold_row_status_not_pending")
    if any(row.get("user_confirmation_required") is not True for row in rows):
        blockers.append("scaffold_row_does_not_require_confirmation")
    if any(row.get("user_confirmation_recorded") is not False for row in rows):
        blockers.append("scaffold_row_already_confirmed")
    if any(row.get("implementation_allowed") is not False for row in rows):
        blockers.append("scaffold_row_implementation_not_blocked")
    if any(row.get("code_patch_authorized") is not False for row in rows):
        blockers.append("scaffold_row_code_patch_not_blocked")
    if any(row.get("candidate_route_authorized") is not False for row in rows):
        blockers.append("scaffold_row_route_authorized")
    for row in rows:
        category = text(row.get("policy_category"))
        expected_option = EXPECTED_SUGGESTED_OPTIONS.get(category)
        if row.get("suggested_closeout_option") != expected_option:
            blockers.append(f"scaffold_suggested_option_drift:{category}")

    for path in find_key_paths(scaffold, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"scaffold_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(scaffold, ADVISORY_SOURCE_KEYS):
        blockers.append(f"scaffold_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(scaffold):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def followup_route_for(option: str) -> str:
    if option == "accept_for_future_offline_simulation_design":
        return "future_offline_simulation_design_candidate"
    if option == "revise_policy_language_before_closeout":
        return "policy_language_revision_required_before_simulation"
    return "no_followup_route"


def build_confirmed_rows(scaffold: dict[str, Any], confirmation_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(scaffold_rows(scaffold), start=1):
        option = source_row.get("suggested_closeout_option")
        rows.append({
            "confirmed_row_id": f"FES-CLOSEOUT-CONFIRMED-{index:03d}",
            "source_confirmation_row_id": source_row.get("confirmation_row_id"),
            "source_draft_row_id": source_row.get("source_draft_row_id"),
            "source_closeout_row_id": source_row.get("source_closeout_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": source_row.get("policy_category"),
            "priority": source_row.get("priority"),
            "confirmation_status": "confirmed_as_suggested_closeout_option" if confirmation_ready else "blocked",
            "selected_confirmation_option": "confirm_suggested_closeout_option" if confirmation_ready else None,
            "confirmed_closeout_option": option if confirmation_ready else None,
            "confirmed_followup_route": followup_route_for(text(option)) if confirmation_ready else "blocked",
            "user_confirmation_recorded": confirmation_ready,
            "formal_policy_closeout_recorded": confirmation_ready,
            "formal_human_outcome_recorded": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "candidate_route_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "future_offline_design_input_allowed": confirmation_ready,
            "requires_separate_design_version": True,
            "requires_future_explicit_implementation_approval": True,
            "confirmation_basis": {
                "user_confirmation_text": USER_CONFIRMATION_CONTEXT["confirmation_text"],
                "source_suggested_option": option,
                "source_confirmation_prompt": source_row.get("confirmation_prompt"),
                "source_required_basis": source_row.get("required_confirmation_basis"),
            },
            "case_count": int(source_row.get("case_count", 0)),
            "source_case_ids": as_list(source_row.get("source_case_ids")),
            "traceability": {
                "source_report": str(DEFAULT_SCAFFOLD_REPORT_PATH),
                "source_confirmation_row_id": source_row.get("confirmation_row_id"),
                "source_draft_row_id": source_row.get("source_draft_row_id"),
                "source_policy_id": source_row.get("source_policy_id"),
                "source_case_ids": as_list(source_row.get("source_case_ids")),
            },
            "constraints": [
                "This row confirms the closeout option only.",
                "This row does not authorize runtime final evidence selection policy.",
                "Any implementation must be proposed in a separate future version with explicit approval.",
            ],
        })
    return rows


def build_summary(status: str, rows: list[dict[str, Any]], scaffold: dict[str, Any]) -> dict[str, Any]:
    option_counter = Counter(text(row.get("confirmed_closeout_option")) or "blocked" for row in rows)
    route_counter = Counter(text(row.get("confirmed_followup_route")) or "blocked" for row in rows)
    priority_counter = Counter(text(row.get("priority")) or "unknown" for row in rows)
    unique_case_ids = {
        text(case_id)
        for row in rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    return {
        "status": status,
        "allowed_use": "future_offline_design_planning_input_only" if status != "blocked" else "blocked",
        "source_scaffold_status": as_dict(scaffold.get("confirmation_gate")).get("status"),
        "confirmed_row_count": len(rows),
        "source_scaffold_row_count": len(scaffold_rows(scaffold)),
        "unique_case_count": len(unique_case_ids),
        "priority_summary": counter_dict(priority_counter),
        "confirmed_closeout_option_summary": counter_dict(option_counter),
        "confirmed_followup_route_summary": counter_dict(route_counter),
        "user_confirmation_recorded": status != "blocked",
        "formal_policy_closeout_recorded": status != "blocked",
        "formal_human_outcome_recorded": False,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "prompt_change_allowed": False,
        "rag_query_integration": "disallowed",
        "required_next_action": "open_separate_offline_design_or_language_revision_version_before_any_runtime_change",
    }


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def readability_violations(report: dict[str, Any]) -> list[str]:
    return sorted_unique(find_string_paths_with_markers(report))


def build_assertions(
    source_blockers: list[str],
    rows: list[dict[str, Any]],
    scaffold: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_ids = {text(row.get("confirmation_row_id")) for row in scaffold_rows(scaffold)}
    confirmed_source_ids = {text(row.get("source_confirmation_row_id")) for row in rows}
    source_policy_ids = {text(row.get("source_policy_id")) for row in scaffold_rows(scaffold)}
    confirmed_policy_ids = {text(row.get("source_policy_id")) for row in rows}
    unique_case_ids = {
        text(case_id)
        for row in rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    return [
        {
            "name": "source_scaffold_is_ready_for_confirmed_record",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "confirmed_record_covers_all_scaffold_rows",
            "status": "passed" if source_ids and source_ids == confirmed_source_ids else "failed",
            "source_row_count": len(source_ids),
            "confirmed_source_row_count": len(confirmed_source_ids),
            "missing_source_row_ids": sorted(source_ids - confirmed_source_ids),
        },
        {
            "name": "confirmed_record_preserves_policy_traceability",
            "status": "passed" if source_policy_ids and source_policy_ids == confirmed_policy_ids else "failed",
            "source_policy_count": len(source_policy_ids),
            "confirmed_policy_count": len(confirmed_policy_ids),
            "missing_policy_ids": sorted(source_policy_ids - confirmed_policy_ids),
        },
        {
            "name": "confirmed_record_has_eight_rows",
            "status": "passed" if len(rows) == EXPECTED_ROW_COUNT else "failed",
            "confirmed_row_count": len(rows),
            "expected": EXPECTED_ROW_COUNT,
        },
        {
            "name": "confirmed_record_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "expected": EXPECTED_CASE_COUNT,
        },
        {
            "name": "all_rows_confirm_suggested_options",
            "status": "passed"
            if all(
                row.get("selected_confirmation_option") == "confirm_suggested_closeout_option"
                and row.get("confirmed_closeout_option")
                for row in rows
            )
            else "failed",
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed"
            if all(
                row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("candidate_route_authorized") is False
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
            "status": "passed" if not readability_errors else "failed",
            "mojibake_like_paths": readability_errors,
        },
    ]


def build_report(scaffold_report_path: Path = DEFAULT_SCAFFOLD_REPORT_PATH) -> dict[str, Any]:
    scaffold = load_json(scaffold_report_path)
    source_blockers = source_contract_blockers(scaffold)
    confirmation_ready = not source_blockers
    rows = build_confirmed_rows(scaffold, confirmation_ready)
    status = "confirmed_for_future_offline_design_planning" if confirmation_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_closeout_confirmed_record",
        "scope": "offline final evidence selection policy closeout confirmed record only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_closeout_confirmation_scaffold": source_meta(scaffold_report_path, scaffold),
        },
        "confirmation_context": USER_CONFIRMATION_CONTEXT,
        "guardrails": CONFIRMED_RECORD_GUARDRAILS,
        "confirmation_gate": {
            "status": status,
            "allowed_use": "future_offline_design_planning_input_only" if confirmation_ready else "blocked",
            "saved_report_only": True,
            "user_confirmation_recorded": confirmation_ready,
            "formal_policy_closeout_recorded": confirmation_ready,
            "formal_human_outcome_recorded": False,
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
        "summary": build_summary(status, rows, scaffold),
        "confirmed_rows": rows,
        "next_version_handoff": {
            "recommended_next_step": "offline_policy_language_revision_and_simulation_design_planning",
            "accepted_for_future_offline_simulation_design": [
                row.get("policy_category")
                for row in rows
                if row.get("confirmed_followup_route") == "future_offline_simulation_design_candidate"
            ],
            "requires_policy_language_revision_before_simulation": [
                row.get("policy_category")
                for row in rows
                if row.get("confirmed_followup_route") == "policy_language_revision_required_before_simulation"
            ],
            "runtime_implementation_allowed": False,
            "requires_explicit_future_implementation_approval": True,
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
            "source_report": str(scaffold_report_path),
            "source_scaffold_version": scaffold.get("version"),
            "source_confirmation_row_ids": [row.get("confirmation_row_id") for row in scaffold_rows(scaffold)],
            "confirmed_row_ids": [row.get("confirmed_row_id") for row in rows],
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
        scaffold,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["confirmation_gate"]["status"] = "blocked"
        report["confirmation_gate"]["allowed_use"] = "blocked"
        report["confirmation_gate"]["user_confirmation_recorded"] = False
        report["confirmation_gate"]["formal_policy_closeout_recorded"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        report["summary"]["user_confirmation_recorded"] = False
        report["summary"]["formal_policy_closeout_recorded"] = False
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["confirmation_gate"]["blockers"] = sorted_unique(report["confirmation_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("confirmation_gate"))
    summary = as_dict(report.get("summary"))
    handoff = as_dict(report.get("next_version_handoff"))
    lines = [
        "# v0.4.8.7 Final Evidence Selection Policy Closeout Confirmed Record",
        "",
        "This file records the user's explicit confirmation of the eight suggested closeout options from v0.4.8.6. It is future offline design-planning input only and does not authorize runtime policy, rerank, prompt, eval case, or RAG main-flow changes.",
        "",
        "## Overview",
        "",
        f"- Confirmation status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmed rows: {summary.get('confirmed_row_count')}",
        f"- Unique cases: {summary.get('unique_case_count')}",
        f"- User confirmation recorded: {gate.get('user_confirmation_recorded')}",
        f"- Formal policy closeout recorded: {gate.get('formal_policy_closeout_recorded')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        "",
        "## Confirmation Context",
        "",
        f"- Source: `{as_dict(report.get('confirmation_context')).get('source')}`",
        f"- Confirmation text: {as_dict(report.get('confirmation_context')).get('confirmation_text')}",
        f"- Selected option: `{as_dict(report.get('confirmation_context')).get('selected_confirmation_option')}`",
        "",
        "## Confirmed Rows",
        "",
        "| Row | Policy | Category | Confirmed option | Follow-up route |",
        "|---|---|---|---|---|",
    ]
    for row in as_list(report.get("confirmed_rows")):
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | `{}` |".format(
                row.get("confirmed_row_id"),
                row.get("source_policy_id"),
                row.get("policy_category"),
                row.get("confirmed_closeout_option"),
                row.get("confirmed_followup_route"),
            )
        )
    lines.extend([
        "",
        "## Handoff",
        "",
        f"- Accepted for future offline simulation design: {', '.join(as_list(handoff.get('accepted_for_future_offline_simulation_design')))}",
        f"- Requires policy-language revision before simulation: {', '.join(as_list(handoff.get('requires_policy_language_revision_before_simulation')))}",
        f"- Runtime implementation allowed: {handoff.get('runtime_implementation_allowed')}",
        "",
        "## Boundaries",
        "",
        "- This record confirms closeout options only.",
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
    parser.add_argument("--scaffold-report", type=Path, default=DEFAULT_SCAFFOLD_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.scaffold_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))

    summary = as_dict(report.get("summary"))
    print(
        "Final evidence selection policy closeout confirmed record built: "
        f"{summary.get('status')}, {summary.get('confirmed_row_count')} rows, "
        f"{summary.get('unique_case_count')} cases"
    )
    return 0 if as_dict(report.get("confirmation_gate")).get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
