"""Build the v0.4.8.5 final-evidence policy closeout decision draft.

The draft reads the saved v0.4.8.4 closeout envelope and prepares eight
suggested policy closeout decisions for user confirmation. It is not a formal
human outcome, does not authorize implementation, and does not call RAG,
Qdrant, an LLM, or mutate retrieval, prompts, rules, fixtures, scenario
registry entries, eval cases, hidden seeds, anchors, schema/importer contracts,
dry-run contracts, or the main flow.
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


VERSION = "0.4.8.5"

DEFAULT_CLOSEOUT_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_closeout_envelope_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_closeout_decision_draft_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md")

EXPECTED_CLOSEOUT_VERSION = "0.4.8.4"
EXPECTED_CLOSEOUT_SCHEMA = "final_evidence_selection_policy_closeout_envelope"
EXPECTED_CLOSEOUT_SCOPE = "offline final evidence selection policy closeout envelope only"
EXPECTED_CLOSEOUT_STATUS = "pending_policy_table_human_closeout"
EXPECTED_CLOSEOUT_ROW_COUNT = 8
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

DRAFT_DECISION_PROFILES = {
    "accept_for_future_offline_simulation_design": {
        "draft_decision_label": "accept for future offline simulation design",
        "draft_confirmation_question": "Confirm whether this policy row may advance to a later offline simulation design artifact.",
        "required_confirmation_basis": "Confirm the row expresses a real evidence-selection concern and does not authorize runtime adoption.",
        "draft_next_step": "eligible_for_future_offline_simulation_design_after_user_confirmation",
    },
    "revise_policy_language_before_closeout": {
        "draft_decision_label": "revise policy language before closeout",
        "draft_confirmation_question": "Confirm whether this policy row needs wording or acceptance-criteria revision before closeout.",
        "required_confirmation_basis": "Confirm the row is directionally useful but the current wording is too broad, narrow, or ambiguous.",
        "draft_next_step": "revise_policy_language_then_rebuild_closeout_materials",
    },
    "split_or_merge_policy_row_after_manual_review": {
        "draft_decision_label": "split or merge after manual review",
        "draft_confirmation_question": "Confirm whether this policy row should be split, merged, or reordered before later design work.",
        "required_confirmation_basis": "Confirm the row overlaps materially with another row or combines multiple legal-evidence functions.",
        "draft_next_step": "create_revised_policy_table_draft_before_any_runtime_work",
    },
    "defer_until_more_manual_cases_exist": {
        "draft_decision_label": "defer until more manual cases exist",
        "draft_confirmation_question": "Confirm whether current source cases are insufficient for this policy row.",
        "required_confirmation_basis": "Confirm more completed manual review cases are needed before forming a durable policy direction.",
        "draft_next_step": "wait_for_more_manual_review_materials",
    },
    "close_without_followup": {
        "draft_decision_label": "close without follow-up",
        "draft_confirmation_question": "Confirm whether this policy direction should be closed for now without follow-up work.",
        "required_confirmation_basis": "Confirm the row is not useful enough to continue and should not become implementation work.",
        "draft_next_step": "no_followup_task_generated",
    },
}

DRAFT_GUARDRAILS = {
    "draft_only": True,
    "source_closeout_envelope_only": True,
    "requires_user_confirmation": True,
    "captures_formal_review_outcome": False,
    "formal_human_outcome_recorded": False,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "runtime_policy_implementation_allowed": False,
    "runtime_selection_policy_patch_allowed": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "draft_route_to_work_items": "disallowed",
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
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
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

NON_GOALS = [
    "Do not capture a formal human review outcome.",
    "Do not authorize final evidence selection runtime policy.",
    "Do not convert draft suggestions into engineering tasks, patch plans, or backlog items.",
    "Do not modify rerank, prompts, anchors, hidden seeds, risk supplement, or term preservation rules.",
    "Do not modify scenario registry, fixtures, eval cases, schema, importer, or dry-run contracts.",
    "Do not call backend services, Qdrant, LLMs, RAG, or full eval.",
]

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
    "completed_outcomes",
    "formal_review_outcomes",
    "reviewer_decision",
    "completed_decisions",
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


def closeout_rows(closeout: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(closeout.get("closeout_rows"))


def source_contract_blockers(closeout: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(closeout.get("closeout_gate"))
    summary = as_dict(closeout.get("summary"))
    rows = closeout_rows(closeout)

    if closeout.get("version") != EXPECTED_CLOSEOUT_VERSION:
        blockers.append("closeout_version_mismatch")
    if closeout.get("schema_kind") != EXPECTED_CLOSEOUT_SCHEMA:
        blockers.append("closeout_schema_mismatch")
    if closeout.get("scope") != EXPECTED_CLOSEOUT_SCOPE:
        blockers.append("closeout_scope_mismatch")
    if gate.get("status") != EXPECTED_CLOSEOUT_STATUS:
        blockers.append("closeout_gate_not_pending")
    if gate.get("closeout_envelope_allowed") is not True:
        blockers.append("closeout_envelope_not_allowed")
    if gate.get("implementation_allowed") is not False:
        blockers.append("closeout_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("closeout_code_patch_not_blocked")
    if gate.get("runtime_policy_implementation_allowed") is not False:
        blockers.append("closeout_runtime_policy_not_blocked")
    if gate.get("runtime_selection_policy_patch_allowed") is not False:
        blockers.append("closeout_runtime_selection_not_blocked")
    if gate.get("rerank_change_allowed") is not False:
        blockers.append("closeout_rerank_not_blocked")
    if gate.get("captures_formal_review_outcome") is not False:
        blockers.append("closeout_captures_formal_outcome")
    if gate.get("formal_human_outcome_recorded") is not False:
        blockers.append("closeout_records_formal_outcome")
    if gate.get("rag_query_integration") != "disallowed":
        blockers.append("closeout_rag_query_integration_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("closeout_gate_has_blockers")
    if summary.get("next_version_recommendation") != "v0.4.8.5 policy table human closeout decision draft":
        blockers.append("closeout_next_version_mismatch")
    if summary.get("closeout_row_count") != EXPECTED_CLOSEOUT_ROW_COUNT:
        blockers.append("closeout_row_count_summary_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("closeout_case_count_drift")
    if len(rows) != EXPECTED_CLOSEOUT_ROW_COUNT:
        blockers.append("closeout_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_POLICY_CATEGORIES:
        blockers.append("closeout_policy_category_order_drift")
    if [row.get("source_policy_id") for row in rows] != EXPECTED_SOURCE_POLICY_IDS:
        blockers.append("closeout_policy_id_order_drift")
    if any(row.get("closeout_status") != "pending_human_closeout" for row in rows):
        blockers.append("closeout_row_status_not_pending")
    if any(row.get("implementation_allowed") is not False for row in rows):
        blockers.append("closeout_row_implementation_not_blocked")
    if any(row.get("code_patch_authorized") is not False for row in rows):
        blockers.append("closeout_row_code_patch_not_blocked")
    if any(row.get("candidate_route_authorized") is not False for row in rows):
        blockers.append("closeout_row_route_authorized")
    if any(row.get("formal_human_outcome_recorded") is not False for row in rows):
        blockers.append("closeout_row_formal_outcome_not_blocked")
    if any(row.get("captures_formal_review_outcome") is not False for row in rows):
        blockers.append("closeout_row_captures_formal_outcome")

    for path in find_key_paths(closeout, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"closeout_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(closeout, ADVISORY_SOURCE_KEYS):
        blockers.append(f"closeout_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(closeout):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_input_contract() -> dict[str, Any]:
    return {
        "contract_type": "saved_report_only_policy_closeout_decision_draft_input_contract",
        "required_reports": [
            {
                "role": "policy_closeout_envelope",
                "path": str(DEFAULT_CLOSEOUT_REPORT_PATH),
                "expected_version": EXPECTED_CLOSEOUT_VERSION,
                "expected_schema_kind": EXPECTED_CLOSEOUT_SCHEMA,
                "expected_scope": EXPECTED_CLOSEOUT_SCOPE,
                "required_sections": [
                    "closeout_gate",
                    "summary",
                    "closeout_rows",
                    "closeout_packet",
                    "assertions",
                ],
            }
        ],
        "forbidden_inputs": [
            "live RAG output",
            "backend response",
            "Qdrant query result",
            "LLM-generated answer",
            "modified eval case",
            "modified scenario registry",
            "runtime policy state",
            "formal manual review outcome",
            "implementation authorization",
        ],
    }


def build_draft_rows(closeout: dict[str, Any], draft_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(closeout_rows(closeout), start=1):
        suggested_option = text(source_row.get("recommended_closeout_option"))
        profile = DRAFT_DECISION_PROFILES.get(
            suggested_option,
            DRAFT_DECISION_PROFILES["revise_policy_language_before_closeout"],
        )
        rows.append({
            "draft_row_id": f"FES-CLOSEOUT-DRAFT-{index:03d}",
            "source_closeout_row_id": source_row.get("closeout_row_id"),
            "source_review_row_id": source_row.get("source_review_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": source_row.get("policy_category"),
            "priority": source_row.get("priority"),
            "draft_status": "draft_pending_user_confirmation" if draft_ready else "blocked",
            "requires_user_confirmation": True,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "draft_is_importable_decision": False,
            "candidate_route_authorized": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "suggested_closeout_option": suggested_option,
            "draft_decision_label": profile["draft_decision_label"],
            "draft_confirmation_question": profile["draft_confirmation_question"],
            "required_confirmation_basis": profile["required_confirmation_basis"],
            "draft_next_step": profile["draft_next_step"],
            "source_candidate_route": source_row.get("candidate_route"),
            "source_closeout_question": source_row.get("closeout_question"),
            "source_minimum_human_basis": source_row.get("minimum_human_basis"),
            "case_count": int(source_row.get("case_count", 0)),
            "source_case_ids": as_list(source_row.get("source_case_ids")),
            "prohibited_now": [
                "Do not treat this draft as a formal human outcome.",
                "Do not modify rerank, prompt, anchor, risk supplement, scenario registry, or eval cases from this draft.",
                "Do not create implementation work from this draft.",
                "Do not connect this draft to runtime final evidence selection policy.",
            ],
            "traceability": {
                "source_closeout_row_id": source_row.get("closeout_row_id"),
                "source_review_row_id": source_row.get("source_review_row_id"),
                "source_policy_id": source_row.get("source_policy_id"),
                "source_report": str(DEFAULT_CLOSEOUT_REPORT_PATH),
                "source_case_ids": as_list(source_row.get("source_case_ids")),
            },
        })
    return rows


def build_summary(status: str, draft_rows: list[dict[str, Any]], closeout: dict[str, Any]) -> dict[str, Any]:
    priority_counter = Counter(text(row.get("priority")) or "unknown" for row in draft_rows)
    option_counter = Counter(text(row.get("suggested_closeout_option")) or "unknown" for row in draft_rows)
    unique_case_ids = {
        text(case_id)
        for row in draft_rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    return {
        "status": status,
        "allowed_use": "user_confirmation_draft_only" if status != "blocked" else "blocked",
        "source_closeout_status": as_dict(closeout.get("closeout_gate")).get("status"),
        "draft_row_count": len(draft_rows),
        "source_closeout_row_count": len(closeout_rows(closeout)),
        "unique_case_count": len(unique_case_ids),
        "priority_summary": counter_dict(priority_counter),
        "suggested_closeout_option_summary": counter_dict(option_counter),
        "requires_user_confirmation": True,
        "formal_human_outcome_recorded": False,
        "captures_formal_review_outcome": False,
        "draft_is_importable_decision": False,
        "next_version_recommendation": "v0.4.8.6 policy table human closeout confirmation record",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "rag_query_integration": "disallowed",
    }


def build_user_confirmation_packet(draft_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "policy_table_human_closeout_user_confirmation_draft_packet",
        "formal_review_outcome_captured": False,
        "importer_compatible": False,
        "recommended_review_order": [row.get("draft_row_id") for row in draft_rows],
        "allowed_draft_options": sorted(DRAFT_DECISION_PROFILES),
        "reviewer_instructions": [
            "Use this draft to confirm, revise, defer, or close each policy row in a later confirmation artifact.",
            "Do not write final reviewer outcomes into this draft report.",
            "Do not use this draft as implementation approval.",
        ],
        "minimum_materials_to_review": [
            str(DEFAULT_CLOSEOUT_REPORT_PATH),
            "tests/final_evidence_selection_policy_human_review_worksheet_report.json",
            "tests/final_evidence_selection_policy_table_draft_report.json",
            "tests/final_evidence_selection_policy_simulator_spec_report.json",
            "tests/final_evidence_selection_audit_report.json",
        ],
    }


def output_key_violations(report: dict[str, Any]) -> list[str]:
    violations = []
    for node in walk_dicts(report):
        for key in FORBIDDEN_OUTPUT_KEYS & set(node.keys()):
            violations.append(key)
    return sorted_unique(violations)


def readability_violations(report: dict[str, Any]) -> list[str]:
    return sorted_unique(find_string_paths_with_markers(report))


def build_assertions(
    source_blockers: list[str],
    draft_rows: list[dict[str, Any]],
    closeout: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_closeout_ids = {text(row.get("closeout_row_id")) for row in closeout_rows(closeout)}
    draft_closeout_ids = {text(row.get("source_closeout_row_id")) for row in draft_rows}
    source_policy_ids = {text(row.get("source_policy_id")) for row in closeout_rows(closeout)}
    draft_policy_ids = {text(row.get("source_policy_id")) for row in draft_rows}
    unique_case_ids = {
        text(case_id)
        for row in draft_rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    readability_blockers = [
        blocker for blocker in source_blockers if blocker == "blocked_for_human_readability"
    ]
    return [
        {
            "name": "source_closeout_is_ready_for_decision_draft",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "draft_covers_all_closeout_rows",
            "status": "passed"
            if source_closeout_ids and source_closeout_ids == draft_closeout_ids
            else "failed",
            "source_closeout_row_count": len(source_closeout_ids),
            "draft_closeout_row_count": len(draft_closeout_ids),
            "missing_closeout_row_ids": sorted(source_closeout_ids - draft_closeout_ids),
        },
        {
            "name": "draft_preserves_policy_traceability",
            "status": "passed"
            if source_policy_ids and source_policy_ids == draft_policy_ids
            else "failed",
            "source_policy_count": len(source_policy_ids),
            "draft_policy_count": len(draft_policy_ids),
            "missing_policy_ids": sorted(source_policy_ids - draft_policy_ids),
        },
        {
            "name": "draft_has_eight_rows",
            "status": "passed" if len(draft_rows) == EXPECTED_CLOSEOUT_ROW_COUNT else "failed",
            "draft_row_count": len(draft_rows),
            "expected": EXPECTED_CLOSEOUT_ROW_COUNT,
        },
        {
            "name": "draft_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "expected": EXPECTED_CASE_COUNT,
        },
        {
            "name": "draft_is_not_formal_outcome_or_implementation",
            "status": "passed"
            if all(
                row.get("formal_human_outcome_recorded") is False
                and row.get("candidate_route_authorized") is False
                and row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("captures_formal_review_outcome") is False
                and row.get("draft_is_importable_decision") is False
                for row in draft_rows
            )
            else "failed",
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
        },
        {
            "name": "forbidden_output_keys_absent",
            "status": "passed" if not output_forbidden_keys else "failed",
            "forbidden_keys": output_forbidden_keys,
        },
        {
            "name": "text_readability_gate",
            "status": "passed" if not readability_errors and not readability_blockers else "failed",
            "source_readability_blockers": readability_blockers,
            "mojibake_like_paths": readability_errors,
        },
    ]


def build_report(
    closeout_report_path: Path = DEFAULT_CLOSEOUT_REPORT_PATH,
) -> dict[str, Any]:
    closeout = load_json(closeout_report_path)
    source_blockers = source_contract_blockers(closeout)
    draft_ready = not source_blockers
    draft_rows = build_draft_rows(closeout, draft_ready)
    status = "draft_pending_user_confirmation" if draft_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_closeout_decision_draft",
        "scope": "offline final evidence selection policy human closeout decision draft only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_closeout_envelope": source_meta(closeout_report_path, closeout),
        },
        "guardrails": DRAFT_GUARDRAILS,
        "non_goals": NON_GOALS,
        "draft_gate": {
            "status": status,
            "allowed_use": "user_confirmation_draft_only" if draft_ready else "blocked",
            "saved_report_only": True,
            "decision_draft_allowed": draft_ready,
            "requires_user_confirmation": True,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "draft_is_importable_decision": False,
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "runtime_policy_implementation_allowed": False,
            "runtime_selection_policy_patch_allowed": False,
            "rerank_change_allowed": False,
            "prompt_change_allowed": False,
            "rag_query_integration": "disallowed",
            "blockers": source_blockers,
        },
        "summary": build_summary(status, draft_rows, closeout),
        "input_contract": build_input_contract(),
        "decision_draft_rows": draft_rows,
        "user_confirmation_packet": build_user_confirmation_packet(draft_rows),
        "next_version_handoff": {
            "recommended_next_version": "v0.4.8.6",
            "recommended_artifact": "policy table human closeout confirmation record",
            "handoff_status": "decision_draft_ready_for_user_confirmation" if draft_ready else "blocked",
            "allowed_next_step": "record_user_confirmed_policy_closeout_choices" if draft_ready else "resolve_source_contract_blockers",
            "runtime_implementation_allowed": False,
            "requires_explicit_future_implementation_approval": True,
        },
        "excluded_scope": {
            "formal_manual_review_outcome": "not_captured",
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
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "traceability": {
            "source_report": str(closeout_report_path),
            "source_closeout_version": closeout.get("version"),
            "source_closeout_row_ids": [row.get("closeout_row_id") for row in closeout_rows(closeout)],
            "decision_draft_row_ids": [row.get("draft_row_id") for row in draft_rows],
            "source_policy_ids": [row.get("source_policy_id") for row in draft_rows],
            "source_case_ids": sorted_unique([
                text(case_id)
                for row in draft_rows
                for case_id in as_list(row.get("source_case_ids"))
            ]),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        draft_rows,
        closeout,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["draft_gate"]["status"] = "blocked"
        report["draft_gate"]["allowed_use"] = "blocked"
        report["draft_gate"]["decision_draft_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
        extra = []
        if forbidden_output_keys:
            extra.append("forbidden_output_key_present")
        if readability_errors:
            extra.append("blocked_for_human_readability")
        report["draft_gate"]["blockers"] = sorted_unique(report["draft_gate"]["blockers"] + extra)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("draft_gate"))
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.8.5 Final Evidence Selection Policy Closeout Decision Draft",
        "",
        "This file is a user-confirmation draft for final evidence selection policy closeout. It converts the v0.4.8.4 closeout envelope into suggested choices for each policy row. It does not record formal human outcomes and does not authorize runtime policy, rerank, prompt, eval case, or RAG main-flow changes.",
        "",
        "## Overview",
        "",
        f"- Draft status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Draft rows: {summary.get('draft_row_count')}",
        f"- Unique cases: {summary.get('unique_case_count')}",
        f"- Requires user confirmation: {gate.get('requires_user_confirmation')}",
        f"- Next version recommendation: `{summary.get('next_version_recommendation')}`",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Formal human outcome recorded: {gate.get('formal_human_outcome_recorded')}",
        f"- Draft is importable decision: {gate.get('draft_is_importable_decision')}",
        "",
        "## Input Contract",
        "",
    ]
    for item in as_list(as_dict(report.get("input_contract")).get("required_reports")):
        lines.append(f"- `{item.get('role')}`: `{item.get('path')}` (version `{item.get('expected_version')}`)")
    lines.extend(["", "## Decision Draft Rows", ""])
    lines.append("| Row | Policy | Category | Status | Suggested option | Next step |")
    lines.append("|---|---|---|---|---|---|")
    for row in as_list(report.get("decision_draft_rows")):
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | `{}` | `{}` |".format(
                row.get("draft_row_id"),
                row.get("source_policy_id"),
                row.get("policy_category"),
                row.get("draft_status"),
                row.get("suggested_closeout_option"),
                row.get("draft_next_step"),
            )
        )
    lines.extend(["", "## Confirmation Questions", ""])
    for row in as_list(report.get("decision_draft_rows")):
        lines.extend([
            f"### {row.get('source_policy_id')} - {row.get('policy_category')}",
            f"- Suggested option: `{row.get('suggested_closeout_option')}`",
            f"- Confirmation question: {row.get('draft_confirmation_question')}",
            f"- Required basis: {row.get('required_confirmation_basis')}",
            "",
        ])
    lines.extend([
        "## Boundaries",
        "",
        "- This draft does not capture a formal review outcome.",
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
    parser.add_argument("--closeout-report", type=Path, default=DEFAULT_CLOSEOUT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.closeout_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))

    summary = as_dict(report.get("summary"))
    print(
        "Final evidence selection policy closeout decision draft built: "
        f"{summary.get('status')}, {summary.get('draft_row_count')} rows, "
        f"{summary.get('unique_case_count')} cases"
    )
    return 0 if as_dict(report.get("draft_gate")).get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
