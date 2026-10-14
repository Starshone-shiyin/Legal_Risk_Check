"""Build the v0.4.8.6 final-evidence policy closeout confirmation scaffold.

The scaffold reads the saved v0.4.8.5 decision draft and prepares eight
confirmation rows for user review. It does not record actual user confirmation,
does not capture a formal human outcome, does not authorize implementation,
and does not call RAG, Qdrant, an LLM, or mutate retrieval, prompts, rules,
fixtures, scenario registry entries, eval cases, hidden seeds, anchors,
schema/importer contracts, dry-run contracts, or the main flow.
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


VERSION = "0.4.8.6"

DEFAULT_DRAFT_REPORT_PATH = legacy_report_path("final_evidence_selection_policy_closeout_decision_draft_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("final_evidence_selection_policy_closeout_confirmation_record_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md")

EXPECTED_DRAFT_VERSION = "0.4.8.5"
EXPECTED_DRAFT_SCHEMA = "final_evidence_selection_policy_closeout_decision_draft"
EXPECTED_DRAFT_SCOPE = "offline final evidence selection policy human closeout decision draft only"
EXPECTED_DRAFT_STATUS = "draft_pending_user_confirmation"
EXPECTED_DRAFT_ROW_COUNT = 8
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

CONFIRMATION_OPTIONS = [
    "confirm_suggested_closeout_option",
    "revise_closeout_option_before_confirmation",
    "defer_confirmation",
    "close_without_followup",
]

CONFIRMATION_GUARDRAILS = {
    "confirmation_record_scaffold_only": True,
    "source_decision_draft_only": True,
    "requires_user_confirmation": True,
    "user_confirmation_recorded": False,
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
    "Do not record the user's actual confirmation in this scaffold.",
    "Do not capture a formal human review outcome.",
    "Do not authorize final evidence selection runtime policy.",
    "Do not convert suggested closeout choices into engineering tasks, patch plans, or backlog items.",
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
    "confirmed_closeout_option",
    "confirmed_next_step",
    "user_confirmed_option",
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


def draft_rows(draft: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(draft.get("decision_draft_rows"))


def source_contract_blockers(draft: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(draft.get("draft_gate"))
    summary = as_dict(draft.get("summary"))
    rows = draft_rows(draft)

    if draft.get("version") != EXPECTED_DRAFT_VERSION:
        blockers.append("draft_version_mismatch")
    if draft.get("schema_kind") != EXPECTED_DRAFT_SCHEMA:
        blockers.append("draft_schema_mismatch")
    if draft.get("scope") != EXPECTED_DRAFT_SCOPE:
        blockers.append("draft_scope_mismatch")
    if gate.get("status") != EXPECTED_DRAFT_STATUS:
        blockers.append("draft_gate_not_pending")
    if gate.get("decision_draft_allowed") is not True:
        blockers.append("draft_not_allowed")
    if gate.get("requires_user_confirmation") is not True:
        blockers.append("draft_does_not_require_user_confirmation")
    if gate.get("implementation_allowed") is not False:
        blockers.append("draft_implementation_not_blocked")
    if gate.get("code_patch_authorized") is not False:
        blockers.append("draft_code_patch_not_blocked")
    if gate.get("runtime_policy_implementation_allowed") is not False:
        blockers.append("draft_runtime_policy_not_blocked")
    if gate.get("runtime_selection_policy_patch_allowed") is not False:
        blockers.append("draft_runtime_selection_not_blocked")
    if gate.get("rerank_change_allowed") is not False:
        blockers.append("draft_rerank_not_blocked")
    if gate.get("captures_formal_review_outcome") is not False:
        blockers.append("draft_captures_formal_outcome")
    if gate.get("formal_human_outcome_recorded") is not False:
        blockers.append("draft_records_formal_outcome")
    if gate.get("draft_is_importable_decision") is not False:
        blockers.append("draft_importable_decision_not_blocked")
    if gate.get("rag_query_integration") != "disallowed":
        blockers.append("draft_rag_query_integration_not_blocked")
    if as_list(gate.get("blockers")):
        blockers.append("draft_gate_has_blockers")
    if summary.get("next_version_recommendation") != "v0.4.8.6 policy table human closeout confirmation record":
        blockers.append("draft_next_version_mismatch")
    if summary.get("draft_row_count") != EXPECTED_DRAFT_ROW_COUNT:
        blockers.append("draft_row_count_summary_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("draft_case_count_drift")
    if len(rows) != EXPECTED_DRAFT_ROW_COUNT:
        blockers.append("draft_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_POLICY_CATEGORIES:
        blockers.append("draft_policy_category_order_drift")
    if [row.get("source_policy_id") for row in rows] != EXPECTED_SOURCE_POLICY_IDS:
        blockers.append("draft_policy_id_order_drift")
    if any(row.get("draft_status") != "draft_pending_user_confirmation" for row in rows):
        blockers.append("draft_row_status_not_pending")
    if any(row.get("requires_user_confirmation") is not True for row in rows):
        blockers.append("draft_row_does_not_require_user_confirmation")
    if any(row.get("implementation_allowed") is not False for row in rows):
        blockers.append("draft_row_implementation_not_blocked")
    if any(row.get("code_patch_authorized") is not False for row in rows):
        blockers.append("draft_row_code_patch_not_blocked")
    if any(row.get("candidate_route_authorized") is not False for row in rows):
        blockers.append("draft_row_route_authorized")
    if any(row.get("formal_human_outcome_recorded") is not False for row in rows):
        blockers.append("draft_row_formal_outcome_not_blocked")
    if any(row.get("captures_formal_review_outcome") is not False for row in rows):
        blockers.append("draft_row_captures_formal_outcome")
    if any(row.get("draft_is_importable_decision") is not False for row in rows):
        blockers.append("draft_row_importable_decision_not_blocked")

    for path in find_key_paths(draft, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"draft_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(draft, ADVISORY_SOURCE_KEYS):
        blockers.append(f"draft_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(draft):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_input_contract() -> dict[str, Any]:
    return {
        "contract_type": "saved_report_only_policy_closeout_confirmation_scaffold_input_contract",
        "required_reports": [
            {
                "role": "policy_closeout_decision_draft",
                "path": str(DEFAULT_DRAFT_REPORT_PATH),
                "expected_version": EXPECTED_DRAFT_VERSION,
                "expected_schema_kind": EXPECTED_DRAFT_SCHEMA,
                "expected_scope": EXPECTED_DRAFT_SCOPE,
                "required_sections": [
                    "draft_gate",
                    "summary",
                    "decision_draft_rows",
                    "user_confirmation_packet",
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


def build_confirmation_rows(draft: dict[str, Any], scaffold_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(draft_rows(draft), start=1):
        rows.append({
            "confirmation_row_id": f"FES-CLOSEOUT-CONFIRMATION-SCAFFOLD-{index:03d}",
            "source_draft_row_id": source_row.get("draft_row_id"),
            "source_closeout_row_id": source_row.get("source_closeout_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": source_row.get("policy_category"),
            "priority": source_row.get("priority"),
            "confirmation_status": "pending_user_confirmation" if scaffold_ready else "blocked",
            "user_confirmation_required": True,
            "user_confirmation_recorded": False,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "candidate_route_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "suggested_closeout_option": source_row.get("suggested_closeout_option"),
            "allowed_confirmation_options": CONFIRMATION_OPTIONS,
            "confirmation_prompt": source_row.get("draft_confirmation_question"),
            "required_confirmation_basis": source_row.get("required_confirmation_basis"),
            "draft_next_step_if_confirmed_later": source_row.get("draft_next_step"),
            "case_count": int(source_row.get("case_count", 0)),
            "source_case_ids": as_list(source_row.get("source_case_ids")),
            "empty_confirmation_fields": {
                "selected_option": None,
                "confirmation_notes": None,
                "confirmed_by_user": None,
            },
            "prohibited_now": [
                "Do not treat this scaffold as the user's confirmation.",
                "Do not modify rerank, prompt, anchor, risk supplement, scenario registry, or eval cases from this scaffold.",
                "Do not create implementation work from this scaffold.",
                "Do not connect this scaffold to runtime final evidence selection policy.",
            ],
            "traceability": {
                "source_draft_row_id": source_row.get("draft_row_id"),
                "source_closeout_row_id": source_row.get("source_closeout_row_id"),
                "source_policy_id": source_row.get("source_policy_id"),
                "source_report": str(DEFAULT_DRAFT_REPORT_PATH),
                "source_case_ids": as_list(source_row.get("source_case_ids")),
            },
        })
    return rows


def build_summary(status: str, confirmation_rows: list[dict[str, Any]], draft: dict[str, Any]) -> dict[str, Any]:
    priority_counter = Counter(text(row.get("priority")) or "unknown" for row in confirmation_rows)
    option_counter = Counter(text(row.get("suggested_closeout_option")) or "unknown" for row in confirmation_rows)
    unique_case_ids = {
        text(case_id)
        for row in confirmation_rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    return {
        "status": status,
        "allowed_use": "user_confirmation_record_scaffold_only" if status != "blocked" else "blocked",
        "source_draft_status": as_dict(draft.get("draft_gate")).get("status"),
        "confirmation_row_count": len(confirmation_rows),
        "source_draft_row_count": len(draft_rows(draft)),
        "unique_case_count": len(unique_case_ids),
        "priority_summary": counter_dict(priority_counter),
        "suggested_closeout_option_summary": counter_dict(option_counter),
        "pending_user_confirmation_count": sum(
            1 for row in confirmation_rows if row.get("confirmation_status") == "pending_user_confirmation"
        ),
        "requires_user_confirmation": True,
        "user_confirmation_recorded": False,
        "formal_human_outcome_recorded": False,
        "captures_formal_review_outcome": False,
        "next_version_recommendation": "wait for explicit user confirmation before any implementation design",
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "rag_query_integration": "disallowed",
    }


def build_confirmation_packet(confirmation_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "policy_table_human_closeout_confirmation_record_scaffold",
        "formal_review_outcome_captured": False,
        "user_confirmation_recorded": False,
        "importer_compatible": False,
        "recommended_confirmation_order": [row.get("confirmation_row_id") for row in confirmation_rows],
        "allowed_confirmation_options": CONFIRMATION_OPTIONS,
        "reviewer_instructions": [
            "Use this scaffold to collect explicit user confirmation outside this generated report.",
            "Do not treat prefilled suggested options as confirmed choices.",
            "Do not use this scaffold as implementation approval.",
        ],
        "minimum_materials_to_review": [
            str(DEFAULT_DRAFT_REPORT_PATH),
            "tests/final_evidence_selection_policy_closeout_envelope_report.json",
            "tests/final_evidence_selection_policy_human_review_worksheet_report.json",
            "tests/final_evidence_selection_policy_table_draft_report.json",
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
    confirmation_rows: list[dict[str, Any]],
    draft: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_draft_ids = {text(row.get("draft_row_id")) for row in draft_rows(draft)}
    confirmation_draft_ids = {text(row.get("source_draft_row_id")) for row in confirmation_rows}
    source_policy_ids = {text(row.get("source_policy_id")) for row in draft_rows(draft)}
    confirmation_policy_ids = {text(row.get("source_policy_id")) for row in confirmation_rows}
    unique_case_ids = {
        text(case_id)
        for row in confirmation_rows
        for case_id in as_list(row.get("source_case_ids"))
    }
    readability_blockers = [
        blocker for blocker in source_blockers if blocker == "blocked_for_human_readability"
    ]
    return [
        {
            "name": "source_draft_is_ready_for_confirmation_scaffold",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "confirmation_scaffold_covers_all_draft_rows",
            "status": "passed"
            if source_draft_ids and source_draft_ids == confirmation_draft_ids
            else "failed",
            "source_draft_row_count": len(source_draft_ids),
            "confirmation_draft_row_count": len(confirmation_draft_ids),
            "missing_draft_row_ids": sorted(source_draft_ids - confirmation_draft_ids),
        },
        {
            "name": "confirmation_scaffold_preserves_policy_traceability",
            "status": "passed"
            if source_policy_ids and source_policy_ids == confirmation_policy_ids
            else "failed",
            "source_policy_count": len(source_policy_ids),
            "confirmation_policy_count": len(confirmation_policy_ids),
            "missing_policy_ids": sorted(source_policy_ids - confirmation_policy_ids),
        },
        {
            "name": "confirmation_scaffold_has_eight_rows",
            "status": "passed" if len(confirmation_rows) == EXPECTED_DRAFT_ROW_COUNT else "failed",
            "confirmation_row_count": len(confirmation_rows),
            "expected": EXPECTED_DRAFT_ROW_COUNT,
        },
        {
            "name": "confirmation_scaffold_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "expected": EXPECTED_CASE_COUNT,
        },
        {
            "name": "confirmation_scaffold_has_no_user_outcome_or_implementation",
            "status": "passed"
            if all(
                row.get("user_confirmation_recorded") is False
                and row.get("formal_human_outcome_recorded") is False
                and row.get("candidate_route_authorized") is False
                and row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("captures_formal_review_outcome") is False
                for row in confirmation_rows
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
    draft_report_path: Path = DEFAULT_DRAFT_REPORT_PATH,
) -> dict[str, Any]:
    draft = load_json(draft_report_path)
    source_blockers = source_contract_blockers(draft)
    scaffold_ready = not source_blockers
    confirmation_rows = build_confirmation_rows(draft, scaffold_ready)
    status = "pending_user_confirmation" if scaffold_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_closeout_confirmation_record_scaffold",
        "scope": "offline final evidence selection policy human closeout confirmation scaffold only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_closeout_decision_draft": source_meta(draft_report_path, draft),
        },
        "guardrails": CONFIRMATION_GUARDRAILS,
        "non_goals": NON_GOALS,
        "confirmation_gate": {
            "status": status,
            "allowed_use": "user_confirmation_record_scaffold_only" if scaffold_ready else "blocked",
            "saved_report_only": True,
            "confirmation_scaffold_allowed": scaffold_ready,
            "requires_user_confirmation": True,
            "user_confirmation_recorded": False,
            "formal_human_outcome_recorded": False,
            "captures_formal_review_outcome": False,
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
        "summary": build_summary(status, confirmation_rows, draft),
        "input_contract": build_input_contract(),
        "confirmation_scaffold_rows": confirmation_rows,
        "confirmation_packet": build_confirmation_packet(confirmation_rows),
        "next_version_handoff": {
            "recommended_next_step": "wait_for_explicit_user_confirmation",
            "recommended_artifact_after_confirmation": "policy table human closeout confirmation record with user choices",
            "handoff_status": "confirmation_scaffold_ready_for_user_review" if scaffold_ready else "blocked",
            "runtime_implementation_allowed": False,
            "requires_explicit_future_implementation_approval": True,
        },
        "excluded_scope": {
            "actual_user_confirmation": "not_captured",
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
            "source_report": str(draft_report_path),
            "source_draft_version": draft.get("version"),
            "source_draft_row_ids": [row.get("draft_row_id") for row in draft_rows(draft)],
            "confirmation_row_ids": [row.get("confirmation_row_id") for row in confirmation_rows],
            "source_policy_ids": [row.get("source_policy_id") for row in confirmation_rows],
            "source_case_ids": sorted_unique([
                text(case_id)
                for row in confirmation_rows
                for case_id in as_list(row.get("source_case_ids"))
            ]),
        },
    }
    forbidden_output_keys = output_key_violations(report)
    readability_errors = readability_violations(report)
    report["assertions"] = build_assertions(
        source_blockers,
        confirmation_rows,
        draft,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["confirmation_gate"]["status"] = "blocked"
        report["confirmation_gate"]["allowed_use"] = "blocked"
        report["confirmation_gate"]["confirmation_scaffold_allowed"] = False
        report["summary"]["status"] = "blocked"
        report["summary"]["allowed_use"] = "blocked"
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
    lines = [
        "# v0.4.8.6 Final Evidence Selection Policy Closeout Confirmation Record Scaffold",
        "",
        "This file is a confirmation record scaffold for final evidence selection policy closeout. It prepares rows for user confirmation but does not record the user's actual confirmation, does not capture formal human outcomes, and does not authorize runtime policy, rerank, prompt, eval case, or RAG main-flow changes.",
        "",
        "## Overview",
        "",
        f"- Confirmation status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmation rows: {summary.get('confirmation_row_count')}",
        f"- Unique cases: {summary.get('unique_case_count')}",
        f"- Pending user confirmation rows: {summary.get('pending_user_confirmation_count')}",
        f"- User confirmation recorded: {gate.get('user_confirmation_recorded')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Formal human outcome recorded: {gate.get('formal_human_outcome_recorded')}",
        "",
        "## Input Contract",
        "",
    ]
    for item in as_list(as_dict(report.get("input_contract")).get("required_reports")):
        lines.append(f"- `{item.get('role')}`: `{item.get('path')}` (version `{item.get('expected_version')}`)")
    lines.extend(["", "## Confirmation Scaffold Rows", ""])
    lines.append("| Row | Policy | Category | Status | Suggested option |")
    lines.append("|---|---|---|---|---|")
    for row in as_list(report.get("confirmation_scaffold_rows")):
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | `{}` |".format(
                row.get("confirmation_row_id"),
                row.get("source_policy_id"),
                row.get("policy_category"),
                row.get("confirmation_status"),
                row.get("suggested_closeout_option"),
            )
        )
    lines.extend(["", "## Confirmation Prompts", ""])
    for row in as_list(report.get("confirmation_scaffold_rows")):
        lines.extend([
            f"### {row.get('source_policy_id')} - {row.get('policy_category')}",
            f"- Suggested option: `{row.get('suggested_closeout_option')}`",
            f"- Confirmation prompt: {row.get('confirmation_prompt')}",
            f"- Required basis: {row.get('required_confirmation_basis')}",
            f"- Confirmation recorded: {row.get('user_confirmation_recorded')}",
            "",
        ])
    lines.extend([
        "## Boundaries",
        "",
        "- This scaffold does not record the user's actual confirmation.",
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
    parser.add_argument("--draft-report", type=Path, default=DEFAULT_DRAFT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.draft_report)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))

    summary = as_dict(report.get("summary"))
    print(
        "Final evidence selection policy closeout confirmation scaffold built: "
        f"{summary.get('status')}, {summary.get('confirmation_row_count')} rows, "
        f"{summary.get('unique_case_count')} cases"
    )
    return 0 if as_dict(report.get("confirmation_gate")).get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
