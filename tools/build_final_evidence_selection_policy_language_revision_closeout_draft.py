"""Build the v0.4.8.9 final-evidence policy language closeout draft.

The draft reads the saved v0.4.8.8 language revision worksheet and proposes
narrowed wording for the three policy-language rows that still require user
confirmation. It is not final policy wording, does not authorize implementation,
and does not call RAG, Qdrant, an LLM, or mutate retrieval, prompts, rules,
fixtures, eval cases, hidden seeds, schemas, importers, or the main flow.
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


VERSION = "0.4.8.9"

DEFAULT_WORKSHEET_PATH = legacy_report_path(
    "final_evidence_selection_policy_language_revision_worksheet_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path(
    "final_evidence_selection_policy_language_revision_closeout_draft_report.json"
)
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md"
)

EXPECTED_SOURCE_VERSION = "0.4.8.8"
EXPECTED_SOURCE_SCHEMA = "final_evidence_selection_policy_language_revision_worksheet"
EXPECTED_SOURCE_SCOPE = "offline final evidence selection policy language revision worksheet only"
EXPECTED_SOURCE_STATUS = "ready_for_policy_language_revision_review"
EXPECTED_ROW_COUNT = 3
EXPECTED_CASE_COUNT = 4
EXPECTED_REVISION_CATEGORIES = ["liability", "scenario_core", "coverage_floor"]
EXPECTED_WAITING_CATEGORIES = [
    "primary",
    "operative",
    "procedural",
    "definition_only",
    "high_risk_manual_review",
]

CLOSEOUT_DRAFT_PROFILES = {
    "liability": {
        "suggested_policy_wording": (
            "Preserve liability or consequence evidence only when the answer "
            "asserts penalties, liability exposure, enforcement consequences, "
            "damages, remedies, or compliance consequences. If the answer only "
            "identifies the applicable conduct rule, liability evidence is optional "
            "and must not displace operative-rule evidence."
        ),
        "must_not_mean": (
            "Do not force penalty, remedy, or consequence provisions into every "
            "final evidence set merely because a case is high-risk."
        ),
        "acceptance_boundary": (
            "The row must name the asserted consequence that makes liability evidence "
            "necessary, or explicitly record that no liability evidence is required."
        ),
        "confirmation_question": (
            "Confirm whether liability evidence should be required only when the "
            "answer expressly discusses penalties, liabilities, remedies, or other "
            "legal consequences."
        ),
        "post_confirmation_route": "eligible_for_future_offline_simulation_design_after_user_confirmation",
    },
    "scenario_core": {
        "suggested_policy_wording": (
            "Preserve scenario-core evidence only when a scenario fact changes the "
            "applicable legal requirement, such as cross-border transfer, automated "
            "decision, sensitive personal information, employee context, consumer "
            "context, or entrusted processing. A broad topic label is not enough."
        ),
        "must_not_mean": (
            "Do not preserve topical but non-operative materials simply because they "
            "share the same business scene or legal domain label."
        ),
        "acceptance_boundary": (
            "The row must identify the legally material scenario fact and an acceptable "
            "substitute that covers the same legal requirement."
        ),
        "confirmation_question": (
            "Confirm whether scenario-core preservation should be limited to facts "
            "that change the applicable legal duty or rights analysis."
        ),
        "post_confirmation_route": "eligible_for_future_offline_simulation_design_after_user_confirmation",
    },
    "coverage_floor": {
        "suggested_policy_wording": (
            "Apply the evidence coverage floor only to material issues actually "
            "asserted in the answer. For each asserted issue, retain at least one "
            "operative or procedural evidence item when such evidence is present in "
            "the candidate set; if no applicable evidence is present, record a "
            "coverage gap or manual-review signal instead of forcing unrelated evidence."
        ),
        "must_not_mean": (
            "Do not recreate score fusion or broad hybrid fallback by requiring every "
            "case to include every evidence class."
        ),
        "acceptance_boundary": (
            "The row must be issue-conditioned and must include a stop condition for "
            "candidate sets that lack applicable evidence."
        ),
        "confirmation_question": (
            "Confirm whether the coverage floor should be issue-conditioned and should "
            "prefer an explicit gap/manual-review signal over unrelated evidence."
        ),
        "post_confirmation_route": "eligible_for_future_offline_simulation_design_after_user_confirmation",
    },
}

DRAFT_GUARDRAILS = {
    "draft_only": True,
    "source_language_revision_worksheet_only": True,
    "requires_user_confirmation": True,
    "formal_policy_language_outcome_recorded": False,
    "final_policy_wording_recorded": False,
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
    "final_policy_wording",
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


def worksheet_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    return as_list(source.get("revision_worksheet_rows"))


def source_contract_blockers(source: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    gate = as_dict(source.get("worksheet_gate"))
    summary = as_dict(source.get("summary"))
    dependency = as_dict(source.get("simulation_design_dependency"))
    rows = worksheet_rows(source)

    if source.get("version") != EXPECTED_SOURCE_VERSION:
        blockers.append("source_version_mismatch")
    if source.get("schema_kind") != EXPECTED_SOURCE_SCHEMA:
        blockers.append("source_schema_mismatch")
    if source.get("scope") != EXPECTED_SOURCE_SCOPE:
        blockers.append("source_scope_mismatch")
    if gate.get("status") != EXPECTED_SOURCE_STATUS:
        blockers.append("source_gate_not_ready")
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
    if summary.get("revision_row_count") != EXPECTED_ROW_COUNT:
        blockers.append("source_revision_row_count_drift")
    if summary.get("unique_case_count") != EXPECTED_CASE_COUNT:
        blockers.append("source_case_count_drift")
    if summary.get("formal_policy_language_outcome_recorded") is not False:
        blockers.append("source_summary_formal_language_outcome_present")
    if summary.get("implementation_allowed") is not False:
        blockers.append("source_summary_implementation_not_blocked")
    if len(rows) != EXPECTED_ROW_COUNT:
        blockers.append("source_row_count_drift")
    if [row.get("policy_category") for row in rows] != EXPECTED_REVISION_CATEGORIES:
        blockers.append("source_revision_category_order_drift")
    if as_list(dependency.get("revision_categories_required_first")) != EXPECTED_REVISION_CATEGORIES:
        blockers.append("source_dependency_revision_categories_drift")
    if as_list(dependency.get("accepted_categories_waiting_for_simulation_design")) != EXPECTED_WAITING_CATEGORIES:
        blockers.append("source_dependency_waiting_categories_drift")
    if dependency.get("simulation_design_should_wait_for_revision_closeout") is not True:
        blockers.append("source_dependency_wait_flag_missing")

    for row in rows:
        category = text(row.get("policy_category"))
        if row.get("worksheet_status") != "ready_for_policy_language_review":
            blockers.append(f"source_row_not_ready:{category}")
        if row.get("implementation_allowed") is not False:
            blockers.append(f"source_row_implementation_not_blocked:{category}")
        if row.get("code_patch_authorized") is not False:
            blockers.append(f"source_row_code_patch_not_blocked:{category}")
        if row.get("runtime_adoption_status") != "not_allowed":
            blockers.append(f"source_row_runtime_not_blocked:{category}")
        if not as_list(row.get("source_case_ids")):
            blockers.append(f"source_row_missing_cases:{category}")
        for required in ("wording_risk", "target_boundary", "simulation_entry_condition"):
            if not text(row.get(required)):
                blockers.append(f"source_row_missing_{required}:{category}")

    for path in find_key_paths(source, FORBIDDEN_SOURCE_KEYS):
        blockers.append(f"source_forbidden_key_present:{path.split('.')[-1]}")
    for path in find_key_paths(source, ADVISORY_SOURCE_KEYS):
        blockers.append(f"source_advisory_signal_present:{path.split('.')[-1]}")
    if find_string_paths_with_markers(source):
        blockers.append("blocked_for_human_readability")
    return sorted_unique(blockers)


def build_closeout_draft_rows(source: dict[str, Any], draft_allowed: bool) -> list[dict[str, Any]]:
    rows = []
    for index, source_row in enumerate(worksheet_rows(source), start=1):
        category = text(source_row.get("policy_category"))
        profile = CLOSEOUT_DRAFT_PROFILES[category]
        rows.append({
            "draft_row_id": f"FES-LANGUAGE-CLOSEOUT-DRAFT-{index:03d}",
            "source_worksheet_row_id": source_row.get("worksheet_row_id"),
            "source_confirmed_row_id": source_row.get("source_confirmed_row_id"),
            "source_policy_id": source_row.get("source_policy_id"),
            "policy_category": category,
            "priority": source_row.get("priority"),
            "draft_status": "draft_pending_user_confirmation" if draft_allowed else "blocked",
            "requires_user_confirmation": True,
            "formal_policy_language_outcome_recorded": False,
            "final_policy_wording_recorded": False,
            "suggested_policy_wording": profile["suggested_policy_wording"],
            "must_not_mean": profile["must_not_mean"],
            "acceptance_boundary": profile["acceptance_boundary"],
            "confirmation_question": profile["confirmation_question"],
            "post_confirmation_route": profile["post_confirmation_route"],
            "source_wording_risk": source_row.get("wording_risk"),
            "source_target_boundary": source_row.get("target_boundary"),
            "source_simulation_entry_condition": source_row.get("simulation_entry_condition"),
            "source_acceptance_checks": as_list(source_row.get("acceptance_checks")),
            "source_case_ids": as_list(source_row.get("source_case_ids")),
            "case_count": int(source_row.get("case_count", 0)),
            "prohibited_now": [
                "Do not treat suggested wording as final policy wording.",
                "Do not implement runtime final evidence selection policy.",
                "Do not change rerank, prompts, anchors, hidden seeds, risk rules, or eval cases.",
                "Do not convert this draft into engineering work without explicit future approval.",
            ],
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "runtime_adoption_status": "not_allowed",
            "traceability": {
                "source_report": str(DEFAULT_WORKSHEET_PATH),
                "source_worksheet_row_id": source_row.get("worksheet_row_id"),
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
    return {
        "status": status,
        "allowed_use": "user_confirmation_draft_only" if status != "blocked" else "blocked",
        "source_worksheet_status": as_dict(source.get("worksheet_gate")).get("status"),
        "draft_row_count": len(rows),
        "source_worksheet_row_count": len(worksheet_rows(source)),
        "unique_case_count": len(unique_case_ids),
        "revision_categories": [row.get("policy_category") for row in rows],
        "priority_summary": counter_dict(priority_counter),
        "requires_user_confirmation": True,
        "formal_policy_language_outcome_recorded": False,
        "final_policy_wording_recorded": False,
        "implementation_allowed": False,
        "code_patch_authorized": False,
        "runtime_policy_implementation_allowed": False,
        "runtime_selection_policy_patch_allowed": False,
        "rerank_change_allowed": False,
        "prompt_change_allowed": False,
        "rag_query_integration": "disallowed",
        "next_version_recommendation": "v0.4.8.10 language revision confirmation record, only if user confirms this draft",
    }


def build_assertions(
    source_blockers: list[str],
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    output_forbidden_keys: list[str],
    readability_errors: list[str],
) -> list[dict[str, Any]]:
    source_row_ids = {text(row.get("worksheet_row_id")) for row in worksheet_rows(source)}
    draft_source_ids = {text(row.get("source_worksheet_row_id")) for row in rows}
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
            "name": "source_worksheet_is_ready_for_closeout_draft",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "draft_covers_all_revision_rows",
            "status": "passed" if source_row_ids and source_row_ids == draft_source_ids else "failed",
            "source_row_count": len(source_row_ids),
            "draft_source_row_count": len(draft_source_ids),
            "missing_source_row_ids": sorted(source_row_ids - draft_source_ids),
        },
        {
            "name": "draft_has_three_rows",
            "status": "passed" if len(rows) == EXPECTED_ROW_COUNT else "failed",
            "draft_row_count": len(rows),
            "expected": EXPECTED_ROW_COUNT,
        },
        {
            "name": "draft_categories_are_expected",
            "status": "passed" if [row.get("policy_category") for row in rows] == EXPECTED_REVISION_CATEGORIES else "failed",
            "categories": [row.get("policy_category") for row in rows],
            "expected": EXPECTED_REVISION_CATEGORIES,
        },
        {
            "name": "draft_preserves_case_traceability",
            "status": "passed" if len(unique_case_ids) == EXPECTED_CASE_COUNT else "failed",
            "unique_case_count": len(unique_case_ids),
            "source_case_ids": sorted(unique_case_ids),
        },
        {
            "name": "draft_is_pending_confirmation_only",
            "status": "passed"
            if all(
                row.get("requires_user_confirmation") is True
                and row.get("formal_policy_language_outcome_recorded") is False
                and row.get("final_policy_wording_recorded") is False
                for row in rows
            )
            else "failed",
        },
        {
            "name": "draft_is_non_runtime",
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


def build_report(worksheet_path: Path = DEFAULT_WORKSHEET_PATH) -> dict[str, Any]:
    source = load_json(worksheet_path)
    source_blockers = source_contract_blockers(source)
    draft_allowed = not source_blockers
    rows = build_closeout_draft_rows(source, draft_allowed)
    status = "draft_pending_user_confirmation" if draft_allowed else "blocked"
    report = {
        "version": VERSION,
        "schema_kind": "final_evidence_selection_policy_language_revision_closeout_draft",
        "scope": "offline final evidence selection policy language revision closeout draft only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "language_revision_worksheet": source_meta(worksheet_path, source),
        },
        "guardrails": DRAFT_GUARDRAILS,
        "draft_gate": {
            "status": status,
            "allowed_use": "user_confirmation_draft_only" if draft_allowed else "blocked",
            "saved_report_only": True,
            "requires_user_confirmation": True,
            "formal_policy_language_outcome_recorded": False,
            "final_policy_wording_recorded": False,
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
        "language_revision_closeout_draft_rows": rows,
        "user_confirmation_packet": {
            "requires_user_confirmation": True,
            "formal_policy_language_outcome_captured": False,
            "final_policy_wording_recorded": False,
            "importer_compatible": False,
            "recommended_review_order": [row.get("draft_row_id") for row in rows],
            "confirmation_questions": [
                {
                    "draft_row_id": row.get("draft_row_id"),
                    "policy_category": row.get("policy_category"),
                    "confirmation_question": row.get("confirmation_question"),
                }
                for row in rows
            ],
        },
        "next_version_handoff": {
            "recommended_next_version": "v0.4.8.10",
            "recommended_next_step": "record user confirmation or revision requests for the three suggested wording drafts",
            "may_enter_offline_simulation_design": False,
            "requires_user_confirmation_first": True,
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
            "source_report": str(worksheet_path),
            "source_worksheet_version": source.get("version"),
            "source_worksheet_row_ids": [row.get("worksheet_row_id") for row in worksheet_rows(source)],
            "draft_row_ids": [row.get("draft_row_id") for row in rows],
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
        report["draft_gate"]["status"] = "blocked"
        report["draft_gate"]["allowed_use"] = "blocked"
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
    rows = as_list(report.get("language_revision_closeout_draft_rows"))
    lines = [
        "# v0.4.8.9 Final Evidence Selection Policy Language Revision Closeout Draft",
        "",
        "This draft proposes narrowed wording for the three policy-language rows that still require user confirmation. It is not final policy wording, does not authorize implementation, and does not modify RAG, rerank, prompts, eval cases, fixtures, rules, or the main flow.",
        "",
        "## Overview",
        "",
        f"- Draft status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Draft rows: {summary.get('draft_row_count')}",
        f"- Revision categories: {', '.join(as_list(summary.get('revision_categories')))}",
        f"- Requires user confirmation: {gate.get('requires_user_confirmation')}",
        f"- Final policy wording recorded: {gate.get('final_policy_wording_recorded')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        "",
        "## Suggested Wording Drafts",
        "",
    ]
    for row in rows:
        lines.extend([
            f"### {row.get('policy_category')}",
            "",
            f"- Suggested wording: {row.get('suggested_policy_wording')}",
            f"- Must not mean: {row.get('must_not_mean')}",
            f"- Acceptance boundary: {row.get('acceptance_boundary')}",
            f"- Confirmation question: {row.get('confirmation_question')}",
            f"- Post-confirmation route: `{row.get('post_confirmation_route')}`",
            f"- Source cases: {', '.join(as_list(row.get('source_case_ids')))}",
            "",
        ])
    lines.extend([
        "## Confirmation Packet",
        "",
        "- The suggested wording above is pending user confirmation.",
        "- It is not importer-compatible and does not capture a formal review outcome.",
        "- A later confirmation record may only be generated after explicit user confirmation or revision instructions.",
        "- Offline simulation design remains blocked until this language closeout is confirmed.",
        "",
        "## Boundaries",
        "",
        "- This draft does not finalize policy wording.",
        "- `implementation_allowed=false` and `code_patch_authorized=false` must remain unchanged.",
        "- It does not implement runtime final evidence selection policy.",
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
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", "--markdown-output", dest="markdown_output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.worksheet)
    write_json(args.output, report)
    if args.markdown_output:
        write_text(args.markdown_output, render_markdown(report))

    summary = as_dict(report.get("summary"))
    print(
        "Final evidence selection policy language revision closeout draft built: "
        f"{summary.get('status')}, {summary.get('draft_row_count')} rows, "
        f"{summary.get('unique_case_count')} cases"
    )
    return 0 if as_dict(report.get("draft_gate")).get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
