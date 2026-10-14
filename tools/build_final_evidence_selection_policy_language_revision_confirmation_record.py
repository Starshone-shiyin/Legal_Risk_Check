"""Build the v0.4.8.10 final-evidence policy language confirmation record.

The record reads the saved v0.4.8.9 language closeout draft and records the
user confirmation for the three narrowed wording drafts. It allows the confirmed
wording to be used as input for a later offline simulation design only. It does
not authorize runtime policy, rerank, prompt, eval case, fixture, rule, schema,
importer, backend, Qdrant, LLM, or RAG main-flow changes.
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


VERSION = "0.4.8.10"
USER_CONFIRMATION_TEXT = "确认以上三条。"

DEFAULT_DRAFT_PATH = legacy_report_path(
    "final_evidence_selection_policy_language_revision_closeout_draft_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "final_evidence_selection_policy_language_revision_confirmation_record_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md"
)

EXPECTED_SOURCE_VERSION = "0.4.8.9"
EXPECTED_SOURCE_SCHEMA = "final_evidence_selection_policy_language_revision_closeout_draft"
EXPECTED_SOURCE_SCOPE = "offline final evidence selection policy language revision closeout draft only"
EXPECTED_SOURCE_STATUS = "draft_pending_user_confirmation"
EXPECTED_ROW_COUNT = 3
EXPECTED_CASE_COUNT = 4
EXPECTED_REVISION_CATEGORIES = ["liability", "scenario_core", "coverage_floor"]
EXPECTED_POST_CONFIRMATION_ROUTE = "eligible_for_future_offline_simulation_design_after_user_confirmation"

CONFIRMATION_GUARDRAILS = {
    "confirmation_record_only": True,
    "source_closeout_draft_only": True,
    "user_confirmation_recorded": True,
    "policy_language_outcome_recorded": True,
    "confirmed_wording_for_offline_design_only": True,
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
    "confirmed_policy_wording",
}

FORBIDDEN_OUTPUT_KEYS = {
    key for key in FORBIDDEN_SOURCE_KEYS if key != "confirmed_policy_wording"
}

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


def source_meta(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "schema_kind": payload.get("schema_kind"),
    }


def draft_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(source.get("language_revision_closeout_draft_rows"))


def source_contract_blockers(source: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(source.get("draft_gate"))
    summary = as_dict(source.get("summary"))
    handoff = as_dict(source.get("next_version_handoff"))
    packet = as_dict(source.get("user_confirmation_packet"))
    rows = draft_rows(source)

    if source.get("version") != EXPECTED_SOURCE_VERSION:
        blockers.append("source_version_mismatch")
    if source.get("schema_kind") != EXPECTED_SOURCE_SCHEMA:
        blockers.append("source_schema_mismatch")
    if source.get("scope") != EXPECTED_SOURCE_SCOPE:
        blockers.append("source_scope_mismatch")
    if gate.get("status") != EXPECTED_SOURCE_STATUS:
        blockers.append("source_gate_not_pending_confirmation")
    if gate.get("requires_user_confirmation") is not True:
        blockers.append("source_confirmation_not_required")
    if gate.get("final_policy_wording_recorded") is not False:
        blockers.append("source_already_records_final_wording")
    if gate.get("formal_policy_language_outcome_recorded") is not False:
        blockers.append("source_formal_language_outcome_present")
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
    if summary.get("draft_row_count") != EXPECTED_ROW_COUNT:
        blockers.append("source_draft_row_count_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("source_case_count_drift")
    if summary.get("requires_user_confirmation") is not True:
        blockers.append("source_summary_confirmation_not_required")
    if summary.get("final_policy_wording_recorded") is not False:
        blockers.append("source_summary_already_records_final_wording")
    if summary.get("implementation_allowed") is not False:
        blockers.append("source_summary_implementation_not_blocked")
    if len(rows) != EXPECTED_ROW_COUNT:
        blockers.append("source_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_REVISION_CATEGORIES:
        blockers.append("source_category_order_drift")
    if handoff.get("recommended_next_version") != "v0.4.8.10":
        blockers.append("source_next_version_mismatch")
    if handoff.get("requires_user_confirmation_first") is not True:
        blockers.append("source_handoff_confirmation_not_required")
    if handoff.get("runtime_implementation_allowed") is not False:
        blockers.append("source_handoff_runtime_not_blocked")
    if packet.get("requires_user_confirmation") is not True:
        blockers.append("source_packet_confirmation_not_required")
    if packet.get("final_policy_wording_recorded") is not False:
        blockers.append("source_packet_already_records_final_wording")
    if packet.get("importer_compatible") is not False:
        blockers.append("source_packet_importer_not_blocked")

    for row in rows:
        category = text(row.get("policy_category"))
        if row.get("draft_status") != EXPECTED_SOURCE_STATUS:
            blockers.append(f"source_row_not_pending_confirmation:{category}")
        if row.get("requires_user_confirmation") is not True:
            blockers.append(f"source_row_confirmation_not_required:{category}")
        if row.get("final_policy_wording_recorded") is not False:
            blockers.append(f"source_row_already_records_final_wording:{category}")
        if row.get("formal_policy_language_outcome_recorded") is not False:
            blockers.append(f"source_row_formal_language_outcome_present:{category}")
        if row.get("implementation_allowed") is not False:
            blockers.append(f"source_row_implementation_not_blocked:{category}")
        if row.get("code_patch_authorized") is not False:
            blockers.append(f"source_row_code_patch_not_blocked:{category}")
        if row.get("runtime_adoption_status") != "not_allowed":
            blockers.append(f"source_row_runtime_not_blocked:{category}")
        if row.get("post_confirmation_route") != EXPECTED_POST_CONFIRMATION_ROUTE:
            blockers.append(f"source_row_route_drift:{category}")
        for required in ("suggested_policy_wording", "must_not_mean", "acceptance_boundary", "confirmation_question"):
            if not text(row.get(required)):
                blockers.append(f"source_row_missing_{required}:{category}")
        if not as_list(row.get("source_case_ids")):
            blockers.append(f"source_row_missing_cases:{category}")

    for path in find_key_paths(source, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"source_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(source, ADVISORY_SOURCE_KEYS):
        blockers.append(f"source_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(source):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_confirmed_rows(source: dict[str, Any], confirmation_ready: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(draft_rows(source), start=1):
        rows.append({
            "confirmed_row_id": f"FES-LANGUAGE-CONFIRMED-{index:03d}",
            "source_draft_row_id": source_row.get("draft_row_id"),
            "source_worksheet_row_id": source_row.get("source_worksheet_row_id"),
            "source_confirmed_row_id": source_row.get("source_confirmed_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": source_row.get("policy_category"),
            "priority": source_row.get("priority"),
            "confirmation_status": "confirmed_by_user" if confirmation_ready else "blocked",
            "user_confirmation_recorded": confirmation_ready,
            "user_confirmation_text": USER_CONFIRMATION_TEXT if confirmation_ready else None,
            "confirmed_policy_wording": source_row.get("suggested_policy_wording") if confirmation_ready else None,
            "confirmed_must_not_mean": source_row.get("must_not_mean") if confirmation_ready else None,
            "confirmed_acceptance_boundary": source_row.get("acceptance_boundary") if confirmation_ready else None,
            "confirmed_post_confirmation_route": "future_offline_simulation_design_candidate" if confirmation_ready else None,
            "offline_simulation_design_input_allowed": confirmation_ready,
            "runtime_policy_implementation_allowed": False,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "source_case_ids": as_list(source_row.get("source_case_ids")),
            "case_count": int(source_row.get("case_count", 0)),
            "traceability": {
                "source_report": str(DEFAULT_DRAFT_PATH),
                "source_draft_row_id": source_row.get("draft_row_id"),
                "source_worksheet_row_id": source_row.get("source_worksheet_row_id"),
                "source_confirmed_row_id": source_row.get("source_confirmed_row_id"),
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
    confirmed = status == "confirmed_for_future_offline_simulation_design"
    return {
        "status": status,
        "allowed_use": "offline_simulation_design_input_only" if confirmed else "blocked",
        "source_draft_status": as_dict(source.get("draft_gate")).get("status"),
        "confirmed_row_count": len(rows),
        "source_draft_row_count": len(draft_rows(source)),
        "unique_case_count": len(unique_case_ids),
        "revision_categories": [row.get("policy_category") for row in rows],
        "priority_summary": counter_dict(priority_counter),
        "user_confirmation_recorded": confirmed,
        "user_confirmation_text": USER_CONFIRMATION_TEXT if confirmed else None,
        "policy_language_outcome_recorded": confirmed,
        "confirmed_wording_for_offline_design_only": confirmed,
        "may_enter_offline_simulation_design": confirmed,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "prompt_change_allowed": False,
        "rag_query_integration": "disallowed",
        "next_version_recommendation": "v0.4.8.11 offline simulation design intake, if user asks to proceed",
    }


def build_assertions(
    source_blockers: list[str],
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_row_ids = {text(row.get("draft_row_id")) for row in draft_rows(source)}
    confirmed_source_ids = {text(row.get("source_draft_row_id")) for row in rows}
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
            "name": "source_draft_is_ready_for_confirmation",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "confirmation_covers_all_draft_rows",
            "status": "passed" if source_row_ids and source_row_ids == confirmed_source_ids else "failed",
            "source_row_count": len(source_row_ids),
            "confirmed_source_row_count": len(confirmed_source_ids),
            "missing_source_row_ids": sorted(source_row_ids - confirmed_source_ids),
        },
        {
            "name": "confirmation_has_three_rows",
            "status": "passed" if len(rows) == EXPECTED_ROW_COUNT else "failed",
            "confirmed_row_count": len(rows),
            "expected": EXPECTED_ROW_COUNT,
        },
        {
            "name": "confirmation_categories_are_expected",
            "status": "passed" if [row.get("policy_category") for row in rows] == EXPECTED_REVISION_CATEGORIES else "failed",
            "categories": [row.get("policy_category") for row in rows],
            "expected": EXPECTED_REVISION_CATEGORIES,
        },
        {
            "name": "confirmation_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "source_case_ids": sorted(unique_case_ids),
        },
        {
            "name": "user_confirmation_recorded_for_all_rows",
            "status": "passed"
            if all(
                row.get("user_confirmation_recorded") is True
                and row.get("user_confirmation_text") == USER_CONFIRMATION_TEXT
                and row.get("confirmed_policy_wording")
                for row in rows
            )
            else "failed",
        },
        {
            "name": "confirmation_is_non_runtime",
            "status": "passed"
            if all(
                row.get("implementation_allowed") is False
                and row.get("code_patch_authorized") is False
                and row.get("runtime_policy_implementation_allowed") is False
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


def build_report(draft_path: Path = DEFAULT_DRAFT_PATH) -> dict[str, Any]:
    source = load_json(draft_path)
    source_blockers = source_contract_blockers(source)
    confirmation_ready = not source_blockers
    rows = build_confirmed_rows(source, confirmation_ready)
    status = "confirmed_for_future_offline_simulation_design" if confirmation_ready else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_language_revision_confirmation_record",
        "scope": "offline final evidence selection policy language revision confirmation record only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "language_revision_closeout_draft": source_meta(draft_path, source),
        },
        "guardrails": CONFIRMATION_GUARDRAILS,
        "confirmation_context": {
            "user_confirmation_text": USER_CONFIRMATION_TEXT,
            "confirmation_scope": EXPECTED_REVISION_CATEGORIES,
            "confirmation_interpretation": "the three suggested wording drafts are confirmed for future offline simulation design input only",
            "implementation_authorization": "not_granted",
        },
        "confirmation_gate": {
            "status": status,
            "allowed_use": "offline_simulation_design_input_only" if confirmation_ready else "blocked",
            "saved_report_only": True,
            "user_confirmation_recorded": confirmation_ready,
            "policy_language_outcome_recorded": confirmation_ready,
            "confirmed_wording_for_offline_design_only": confirmation_ready,
            "may_enter_offline_simulation_design": confirmation_ready,
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
        "confirmed_language_revision_rows": rows,
        "offline_simulation_design_handoff": {
            "handoff_status": "ready_for_future_offline_simulation_design" if confirmation_ready else "blocked",
            "confirmed_revision_categories": EXPECTED_REVISION_CATEGORIES if confirmation_ready else [],
            "previously_accepted_categories_waiting": [
                "primary",
                "operative",
                "procedural",
                "definition_only",
                "high_risk_manual_review",
            ],
            "runtime_implementation_allowed": False,
            "requires_new_version_before_any_simulation_or_runtime_work": True,
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
            "source_report": str(draft_path),
            "source_draft_version": source.get("version"),
            "source_draft_row_ids": [row.get("draft_row_id") for row in draft_rows(source)],
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
        source,
        forbidden_output_keys,
        readability_errors,
    )
    if forbidden_output_keys or readability_errors:
        report["confirmation_gate"]["status"] = "blocked"
        report["confirmation_gate"]["allowed_use"] = "blocked"
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
    rows = as_list(report.get("confirmed_language_revision_rows"))
    lines = [
        "# v0.4.8.10 Final Evidence Selection Policy Language Revision Confirmation Record",
        "",
        "This record captures the user's confirmation of the three narrowed policy-language drafts. The confirmed wording is only an input for future offline simulation design. It does not authorize runtime policy, rerank, prompt, eval case, fixture, rule, schema, importer, backend, Qdrant, LLM, or RAG main-flow changes.",
        "",
        "## Overview",
        "",
        f"- Confirmation status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Confirmed rows: {summary.get('confirmed_row_count')}",
        f"- Revision categories: {', '.join(as_list(summary.get('revision_categories')))}",
        f"- User confirmation recorded: {gate.get('user_confirmation_recorded')}",
        f"- User confirmation text: {summary.get('user_confirmation_text')}",
        f"- May enter offline simulation design: {gate.get('may_enter_offline_simulation_design')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        "",
        "## Confirmed Wording",
        "",
    ]
    for row in rows:
        lines.extend([
            f"### {row.get('policy_category')}",
            "",
            f"- Confirmed wording: {row.get('confirmed_policy_wording')}",
            f"- Must not mean: {row.get('confirmed_must_not_mean')}",
            f"- Acceptance boundary: {row.get('confirmed_acceptance_boundary')}",
            f"- Confirmed route: `{row.get('confirmed_post_confirmation_route')}`",
            f"- Source cases: {', '.join(as_list(row.get('source_case_ids')))}",
            "",
        ])
    lines.extend([
        "## Boundaries",
        "",
        "- Confirmed wording may be used only as future offline simulation design input.",
        "- `implementation_allowed=false` and `code_patch_authorized=false` remain unchanged.",
        "- This record does not implement runtime final evidence selection policy.",
        "- It does not modify rerank, prompt, eval cases, fixtures, anchors, hidden seeds, risk supplement, term preservation, scenario registry, schema, importer, or dry-run contracts.",
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
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.draft)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))

    summary = as_dict(report.get("summary"))
    print(
        "Final evidence selection policy language revision confirmation record built: "
        f"{summary.get('status')}, {summary.get('confirmed_row_count')} rows, "
        f"{summary.get('unique_case_count')} cases"
    )
    return 0 if as_dict(report.get("confirmation_gate")).get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
