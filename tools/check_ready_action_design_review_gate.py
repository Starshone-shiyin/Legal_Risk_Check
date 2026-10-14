"""Check the ready-action design review brief before any later design handoff.

This gate is intentionally conservative. It only reads the saved v0.4.7.9.1
brief report, verifies that the brief is suitable for human design review, and
keeps implementation blocked. It does not call RAG, contact a backend, read
Qdrant, use an LLM, or mutate retrieval, prompts, rules, fixtures, scenario
registry entries, eval cases, hidden seeds, anchors, or the main flow.
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


VERSION = "0.4.7.9.2"

DEFAULT_BRIEF_REPORT_PATH = legacy_report_path("ready_action_design_review_brief_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ready_action_design_review_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ready_action_design_review_gate_v0.4.7.9.2.md")

EXPECTED_SOURCE_BRIEF_VERSION = "0.4.7.9.1"
EXPECTED_SOURCE_BRIEF_SCHEMA = "ready_action_design_review_brief"
EXPECTED_SOURCE_PACK_VERSION = "0.4.7.9.0"
EXPECTED_SOURCE_PACK_SCHEMA = "governed_ready_action_design_pack"
EXPECTED_SOURCE_PACK_SUMMARY_STATUS = "ready_for_design_review"
EXPECTED_READY_ACTION_COUNT = 18
EXPECTED_SOURCE_CASE_COUNT = 5
EXPECTED_TRACK_COUNT = 5
EXPECTED_PENDING_EXCLUDED = 31

EXPECTED_REVIEW_ORDER = [
    "final_evidence_selection_policy_review",
    "primary_evidence_fixture_candidate_review",
    "high_risk_manual_grounding_review",
    "scenario_registry_core_article_review",
    "functional_typing_fixture_review",
]

TRACK_DISPLAY_NAMES = {
    "final_evidence_selection_policy_review": "最终证据选择策略评审",
    "primary_evidence_fixture_candidate_review": "主证据测试样例候选评审",
    "high_risk_manual_grounding_review": "高风险结论证据支撑评审",
    "scenario_registry_core_article_review": "场景核心条文范围评审",
    "functional_typing_fixture_review": "法律功能类型样例评审",
}

BRIEF_REQUIRED_GUARDRAILS = {
    "brief_only": True,
    "source_design_pack_only": True,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "pending_records_to_tasks": "disallowed",
    "fixture_write_to_eval": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "rag_query_integration": "disallowed",
    "main_flow_mutation": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
}

GATE_GUARDRAILS = {
    "gate_only": True,
    "source_brief_only": True,
    "review_material_only": True,
    "not_action_approval": True,
    "not_implementation_authorization": True,
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "handoff_to_implementation": "not_allowed",
    "future_explicit_implementation_approval_required": True,
    "pending_records_to_work_items": "disallowed",
    "ai_suggestion_to_decision": "disallowed",
    "brief_to_implementation_authorization": "disallowed",
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

FORBIDDEN_SOURCE_KEYS = {
    "approved",
    "approved_actions",
    "authorized_actions",
    "ready_to_apply",
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "migration_steps",
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
    "implementation_queue",
    "pending_candidates",
    "pending_backlog",
}

FORBIDDEN_OUTPUT_KEYS = {
    "approved",
    "approved_actions",
    "authorized_actions",
    "ready_to_apply",
    "implementation_plan",
    "patch_plan",
    "files_to_change",
    "commands",
    "migration_steps",
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
    "implementation_queue",
    "pending_candidates",
    "pending_backlog",
}

ADVISORY_SOURCE_KEYS = {
    "ai_suggestion",
    "safe_ai_suggestion_input",
    "advisory_packet_only",
    "prescreen_advisory",
    "pilot_assist",
    "mobile_aid",
    "human_confirmation_required",
    "contains_completed_manual_decisions",
}


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


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any) -> str:
    return str(value or "").strip()


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
        "schema_kind": data.get("schema_kind"),
    }


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def key_violations(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    forbidden: list[str] = []
    advisory: list[str] = []
    for node in walk_dicts(data):
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            if key in FORBIDDEN_SOURCE_KEYS:
                forbidden.append(key)
            if key in ADVISORY_SOURCE_KEYS and value:
                advisory.append(key)
            if key.startswith("advisory_") and value:
                advisory.append(key)
            if key.startswith("prescreen_") and value:
                advisory.append(key)
    return sorted_unique(forbidden), sorted_unique(advisory)


def source_contract_blockers(brief: dict[str, Any]) -> list[str]:
    if not brief:
        return ["missing_or_invalid_brief_report"]

    blockers: list[str] = []
    source_design_pack = as_dict(brief.get("source_design_pack"))
    brief_gate = as_dict(brief.get("brief_gate"))
    summary = as_dict(brief.get("summary"))
    guardrails = as_dict(brief.get("guardrails"))
    assertions = as_list(brief.get("assertions"))

    if brief.get("version") != EXPECTED_SOURCE_BRIEF_VERSION:
        blockers.append("source_brief_version_mismatch")
    if brief.get("schema_kind") != EXPECTED_SOURCE_BRIEF_SCHEMA:
        blockers.append("source_brief_schema_mismatch")
    if source_design_pack.get("version") != EXPECTED_SOURCE_PACK_VERSION:
        blockers.append("source_design_pack_version_mismatch")
    if source_design_pack.get("schema_kind") != EXPECTED_SOURCE_PACK_SCHEMA:
        blockers.append("source_design_pack_schema_mismatch")
    if source_design_pack.get("summary_status") != EXPECTED_SOURCE_PACK_SUMMARY_STATUS:
        blockers.append("source_design_pack_summary_not_ready")
    if source_design_pack.get("planning_gate_status") != "open_for_design_review":
        blockers.append("source_design_pack_planning_gate_not_open")

    if brief_gate.get("status") != "open_for_design_review_brief":
        blockers.append("source_brief_gate_not_open")
    if brief_gate.get("human_design_review_allowed") is not True:
        blockers.append("source_human_design_review_not_allowed")
    if brief_gate.get("implementation_allowed") is not False:
        blockers.append("source_brief_gate_implementation_not_blocked")
    if brief_gate.get("implementation_status") != "not_started":
        blockers.append("source_brief_implementation_status_not_not_started")
    if brief_gate.get("implementation_requires_future_explicit_approval") is not True:
        blockers.append("source_brief_missing_future_implementation_approval")

    if summary.get("status") != "ready_for_human_design_review":
        blockers.append("source_summary_not_ready_for_human_design_review")
    if summary.get("ready_for_design_review_candidates") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("source_ready_action_count_drift")
    if summary.get("source_ready_action_candidates") != EXPECTED_READY_ACTION_COUNT:
        blockers.append("source_ready_action_baseline_drift")
    if summary.get("ready_case_count") != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("source_case_count_drift")
    if summary.get("design_track_count") != EXPECTED_TRACK_COUNT:
        blockers.append("source_track_count_drift")
    if summary.get("pending_records_excluded") != EXPECTED_PENDING_EXCLUDED:
        blockers.append("pending_records_excluded_count_drift")
    if summary.get("pending_records_are_not_tasks") is not True:
        blockers.append("pending_records_not_marked_as_background")
    if summary.get("implementation_allowed") is not False:
        blockers.append("source_summary_implementation_not_blocked")
    if summary.get("code_patch_authorized") is not False:
        blockers.append("source_summary_code_patch_not_blocked")
    if summary.get("requires_future_explicit_approval") is not True:
        blockers.append("source_summary_missing_future_explicit_approval")
    if as_list(summary.get("review_order")) != EXPECTED_REVIEW_ORDER:
        blockers.append("source_review_order_drift")

    for key, expected in BRIEF_REQUIRED_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            blockers.append(f"source_brief_guardrail_mismatch:{key}")

    if not assertions:
        blockers.append("source_assertions_missing")
    elif any(as_dict(item).get("status") != "passed" for item in assertions):
        blockers.append("source_assertions_not_all_passed")

    forbidden_keys, advisory_keys = key_violations(brief)
    for key in forbidden_keys:
        blockers.append(f"source_forbidden_key_present:{key}")
    for key in advisory_keys:
        blockers.append(f"source_advisory_signal_present:{key}")

    return blockers


def traceability_blockers(brief: dict[str, Any]) -> list[str]:
    traceability = as_dict(brief.get("traceability"))
    track_briefs = as_list(brief.get("track_briefs"))
    top_case_ids = set(text(item) for item in as_list(traceability.get("source_case_ids")) if text(item))
    top_action_ids = set(text(item) for item in as_list(traceability.get("design_action_ids")) if text(item))
    blockers: list[str] = []

    if len(top_case_ids) != EXPECTED_SOURCE_CASE_COUNT:
        blockers.append("traceability_source_case_count_drift")
    if len(top_action_ids) != EXPECTED_READY_ACTION_COUNT:
        blockers.append("traceability_design_action_count_drift")
    if len(track_briefs) != EXPECTED_TRACK_COUNT:
        blockers.append("track_briefs_count_drift")

    track_action_ids: set[str] = set()
    track_case_ids: set[str] = set()
    track_order = []
    for index, item in enumerate(track_briefs):
        track = as_dict(item)
        action_type = text(track.get("action_type"))
        track_order.append(action_type)
        if action_type not in EXPECTED_REVIEW_ORDER:
            blockers.append(f"unknown_track_action_type:{action_type or index}")
        track_traceability = as_dict(track.get("traceability"))
        action_ids = set(text(value) for value in as_list(track_traceability.get("design_action_ids")) if text(value))
        case_ids = set(text(value) for value in as_list(track_traceability.get("source_case_ids")) if text(value))
        if not action_ids:
            blockers.append(f"track_missing_design_action_ids:{action_type or index}")
        if not case_ids:
            blockers.append(f"track_missing_source_case_ids:{action_type or index}")
        if not action_ids <= top_action_ids:
            blockers.append(f"track_action_ids_not_subset_of_top_traceability:{action_type or index}")
        if not case_ids <= top_case_ids:
            blockers.append(f"track_case_ids_not_subset_of_top_traceability:{action_type or index}")
        track_action_ids.update(action_ids)
        track_case_ids.update(case_ids)

    if track_order != EXPECTED_REVIEW_ORDER:
        blockers.append("track_briefs_order_drift")
    if track_action_ids != top_action_ids:
        blockers.append("track_action_ids_do_not_match_top_traceability")
    if track_case_ids != top_case_ids:
        blockers.append("track_case_ids_do_not_match_top_traceability")
    return blockers


def build_source_integrity(brief: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    summary = as_dict(brief.get("summary"))
    traceability = as_dict(brief.get("traceability"))
    source_design_pack = as_dict(brief.get("source_design_pack"))
    actual = {
        "source_brief_version": brief.get("version"),
        "source_brief_schema_kind": brief.get("schema_kind"),
        "source_design_pack_version": source_design_pack.get("version"),
        "source_design_pack_schema_kind": source_design_pack.get("schema_kind"),
        "source_design_pack_summary_status": source_design_pack.get("summary_status"),
        "ready_action_candidates": summary.get("ready_for_design_review_candidates", 0),
        "source_case_count": len(as_list(traceability.get("source_case_ids"))),
        "design_track_count": summary.get("design_track_count", 0),
        "design_action_id_count": len(as_list(traceability.get("design_action_ids"))),
        "pending_records_excluded": summary.get("pending_records_excluded", 0),
    }
    expected = {
        "source_brief_version": EXPECTED_SOURCE_BRIEF_VERSION,
        "source_brief_schema_kind": EXPECTED_SOURCE_BRIEF_SCHEMA,
        "source_design_pack_version": EXPECTED_SOURCE_PACK_VERSION,
        "source_design_pack_schema_kind": EXPECTED_SOURCE_PACK_SCHEMA,
        "source_design_pack_summary_status": EXPECTED_SOURCE_PACK_SUMMARY_STATUS,
        "ready_action_candidates": EXPECTED_READY_ACTION_COUNT,
        "source_case_count": EXPECTED_SOURCE_CASE_COUNT,
        "design_track_count": EXPECTED_TRACK_COUNT,
        "design_action_id_count": EXPECTED_READY_ACTION_COUNT,
        "pending_records_excluded": EXPECTED_PENDING_EXCLUDED,
    }
    return {
        "status": "passed" if not blockers else "failed",
        "expected": expected,
        "actual": actual,
        "blockers": blockers,
    }


def build_track_gates(brief: dict[str, Any], gate_open: bool) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(as_list(brief.get("track_briefs")), start=1):
        track = as_dict(item)
        action_type = text(track.get("action_type"))
        scope = as_dict(track.get("current_scope"))
        traceability = as_dict(track.get("traceability"))
        trace_action_ids = as_list(traceability.get("design_action_ids"))
        trace_case_ids = as_list(traceability.get("source_case_ids"))
        blockers = []
        if action_type not in EXPECTED_REVIEW_ORDER:
            blockers.append("unknown_track")
        if not trace_action_ids:
            blockers.append("missing_design_action_ids")
        if not trace_case_ids:
            blockers.append("missing_source_case_ids")
        if not as_list(track.get("review_questions")):
            blockers.append("missing_review_questions")
        if not as_list(track.get("entry_criteria")):
            blockers.append("missing_entry_criteria")
        if not as_list(track.get("exit_criteria")):
            blockers.append("missing_exit_criteria")
        if not as_list(track.get("prohibited_now")):
            blockers.append("missing_prohibited_now")
        status = "open_for_human_design_review_only" if gate_open and not blockers else "blocked_for_human_design_review"
        rows.append({
            "review_order": EXPECTED_REVIEW_ORDER.index(action_type) + 1 if action_type in EXPECTED_REVIEW_ORDER else index,
            "design_track_id": track.get("design_track_id") or action_type,
            "action_type": action_type,
            "display_name": TRACK_DISPLAY_NAMES.get(action_type, action_type),
            "priority_band": track.get("priority_band") or "",
            "status": status,
            "allowed_use": "human_design_review_discussion_only" if status == "open_for_human_design_review_only" else "blocked",
            "design_spec_draft_status": "draft_material_available_only" if status == "open_for_human_design_review_only" else "blocked",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "ready_for_design_review_candidates": scope.get("ready_for_design_review_candidates", len(trace_action_ids)),
            "source_case_count": scope.get("source_case_count", len(trace_case_ids)),
            "traceability": {
                "source_case_ids": trace_case_ids,
                "design_action_ids": trace_action_ids,
            },
            "blockers": blockers,
        })
    return sorted(rows, key=lambda row: (int(row.get("review_order") or 999), row.get("action_type") or ""))


def build_review_scope(brief: dict[str, Any], track_gates: list[dict[str, Any]]) -> dict[str, Any]:
    summary = as_dict(brief.get("summary"))
    traceability = as_dict(brief.get("traceability"))
    priority_counts = Counter(text(track.get("priority_band")) for track in track_gates if text(track.get("priority_band")))
    return {
        "design_track_count": len(track_gates),
        "design_action_count": len(as_list(traceability.get("design_action_ids"))),
        "source_case_count": len(as_list(traceability.get("source_case_ids"))),
        "pending_records_excluded": summary.get("pending_records_excluded", 0),
        "priority_band_summary": {key: priority_counts[key] for key in sorted(priority_counts)},
        "review_order": [track.get("action_type") for track in track_gates],
    }


def build_assertions(
    gate_open: bool,
    source_blockers: list[str],
    traceability_errors: list[str],
    track_gates: list[dict[str, Any]],
    output_forbidden_keys: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "source_brief_contract_is_valid",
            "status": "passed" if not source_blockers else "failed",
            "blockers": source_blockers,
        },
        {
            "name": "traceability_is_closed_under_source_brief",
            "status": "passed" if not traceability_errors else "failed",
            "blockers": traceability_errors,
        },
        {
            "name": "pending_records_remain_background_only",
            "status": "passed" if gate_open else "failed",
            "pending_records_policy": "background_count_only_not_work_items",
        },
        {
            "name": "implementation_is_not_authorized",
            "status": "passed",
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
        },
        {
            "name": "track_gates_are_review_only",
            "status": "passed"
            if all(track.get("implementation_allowed") is False and track.get("code_patch_authorized") is False for track in track_gates)
            else "failed",
        },
        {
            "name": "forbidden_output_keys_absent",
            "status": "passed" if not output_forbidden_keys else "failed",
            "forbidden_keys": output_forbidden_keys,
        },
    ]


def output_key_violations(report: dict[str, Any]) -> list[str]:
    matches = []
    for node in walk_dicts(report):
        if isinstance(node, dict):
            matches.extend(sorted(FORBIDDEN_OUTPUT_KEYS & set(node)))
    return sorted_unique(matches)


def build_report(brief_report_path: Path = DEFAULT_BRIEF_REPORT_PATH) -> dict[str, Any]:
    brief = load_json(brief_report_path)
    source_errors = source_contract_blockers(brief)
    traceability_errors = traceability_blockers(brief) if brief else []
    gate_blockers = sorted_unique(source_errors + traceability_errors)
    gate_open = not gate_blockers
    track_gates = build_track_gates(brief, gate_open)
    source_integrity = build_source_integrity(brief, source_errors + traceability_errors)
    review_scope = build_review_scope(brief, track_gates)
    gate = {
        "status": "open_for_human_design_review_only" if gate_open else "blocked",
        "allowed_use": "human_design_review_discussion_only" if gate_open else "blocked",
        "human_design_review_allowed": gate_open,
        "design_spec_draft_status": "draft_material_available_only" if gate_open else "blocked",
        "implementation_allowed": False,
        "implementation_status": "not_started",
        "code_patch_authorized": False,
        "handoff_to_implementation": "not_allowed",
        "future_explicit_implementation_approval_required": True,
        "blockers": gate_blockers,
    }
    excluded_scope = {
        "pending_records_excluded": as_dict(brief.get("summary")).get("pending_records_excluded", 0),
        "pending_records_policy": "background_count_only_not_work_items",
        "ai_suggestion_policy": "advisory_only_not_decision_not_authorization",
        "brief_policy": "review_material_only_not_implementation_authorization",
    }
    report = {
        "version": VERSION,
        "schema_kind": "ready_action_design_review_gate",
        "scope": "offline human design review gate only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ready_action_design_review_brief_report": source_meta(brief_report_path, brief),
        },
        "source_brief": {
            "version": brief.get("version"),
            "schema_kind": brief.get("schema_kind"),
            "scope": brief.get("scope"),
            "summary_status": as_dict(brief.get("summary")).get("status"),
            "brief_gate_status": as_dict(brief.get("brief_gate")).get("status"),
            "source_design_pack_version": as_dict(brief.get("source_design_pack")).get("version"),
            "source_design_pack_schema_kind": as_dict(brief.get("source_design_pack")).get("schema_kind"),
            "source_design_pack_summary_status": as_dict(brief.get("source_design_pack")).get("summary_status"),
        },
        "guardrails": GATE_GUARDRAILS,
        "gate": gate,
        "implementation_gate": {
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "code_patch_authorized": False,
            "handoff_to_implementation": "not_allowed",
            "future_explicit_implementation_approval_required": True,
        },
        "boundary_gate": {
            "status": "passed" if gate_open else "blocked",
            "blocked_by_boundary_violation": bool(source_errors),
            "blockers": gate_blockers,
        },
        "source_integrity": source_integrity,
        "review_scope": review_scope,
        "track_gates": track_gates,
        "excluded_scope": excluded_scope,
        "traceability": {
            "source_case_ids": as_list(as_dict(brief.get("traceability")).get("source_case_ids")),
            "design_action_ids": as_list(as_dict(brief.get("traceability")).get("design_action_ids")) if gate_open else [],
            "source_reports": [str(brief_report_path), *as_list(as_dict(brief.get("traceability")).get("source_reports"))],
        },
    }
    forbidden_output_keys = output_key_violations(report)
    report["assertions"] = build_assertions(
        gate_open,
        source_errors,
        traceability_errors,
        track_gates,
        forbidden_output_keys,
    )
    if forbidden_output_keys:
        report["gate"]["status"] = "blocked"
        report["gate"]["human_design_review_allowed"] = False
        report["gate"]["blockers"] = sorted_unique(report["gate"]["blockers"] + ["forbidden_output_key_present"])
        report["boundary_gate"]["status"] = "blocked"
        report["boundary_gate"]["blockers"] = report["gate"]["blockers"]
    return report


def render_markdown(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate"))
    review_scope = as_dict(report.get("review_scope"))
    lines = [
        "# v0.4.7.9.2 Ready Action Design Review Gate",
        "",
        "本文件是人工设计评审入口门禁。它只说明上一版 brief 是否可以作为评审材料使用，不批准任何代码、配置或样例修改。",
        "",
        "## 总览",
        "",
        f"- Gate status: `{gate.get('status')}`",
        f"- Allowed use: `{gate.get('allowed_use')}`",
        f"- Design tracks: {review_scope.get('design_track_count')}",
        f"- Design actions: {review_scope.get('design_action_count')}",
        f"- Source cases: {review_scope.get('source_case_count')}",
        f"- Pending records excluded: {review_scope.get('pending_records_excluded')}",
        f"- Implementation allowed: {gate.get('implementation_allowed')}",
        f"- Code patch authorized: {gate.get('code_patch_authorized')}",
        "",
        "## Track Gates",
        "",
        "| Order | Priority | Track | Status | Candidates | Cases |",
        "|---:|---|---|---|---:|---:|",
    ]
    for track in as_list(report.get("track_gates")):
        lines.append(
            f"| {track.get('review_order')} | {track.get('priority_band')} | {track.get('display_name')} | "
            f"`{track.get('status')}` | {track.get('ready_for_design_review_candidates')} | {track.get('source_case_count')} |"
        )

    lines.extend([
        "",
        "## Boundaries",
        "",
        "- `human_design_review_allowed=true` 只表示可以开会讨论设计问题。",
        "- `design_spec_draft_status=draft_material_available_only` 只表示可以写设计说明草案，不表示可以实现。",
        "- `implementation_allowed=false` 和 `code_patch_authorized=false` 必须保持不变。",
        "- 31 个 pending records 只作为背景统计，不进入任务清单或工程 backlog。",
        "- AI suggestion、pilot assist、mobile aid 或 prescreen 材料不能成为正式授权来源。",
        "",
        "## Source",
        "",
        f"- Source brief: `{report['inputs']['ready_action_design_review_brief_report']['path']}`",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check ready-action design review gate.")
    parser.add_argument("--brief-report", type=Path, default=DEFAULT_BRIEF_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.brief_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    gate = report["gate"]
    review_scope = report["review_scope"]
    print(
        "Ready action design review gate checked: "
        f"{gate['status']}, "
        f"{review_scope['design_action_count']} design actions, "
        f"{review_scope['design_track_count']} tracks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
