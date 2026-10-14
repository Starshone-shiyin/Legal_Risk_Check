"""Build an offline evidence fixture candidate pool.

The pool records which manual-review items could become future fixtures after
human confirmation. It does not edit eval cases, hidden seeds, prompts, anchors,
rerank, risk rules, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_manual_review_action_candidates import (
    ACTION_CATEGORIES,
    ACTION_FUNCTIONAL_FIXTURE,
    ACTION_PRIMARY_FIXTURE,
    READINESS_BLOCKED,
    READINESS_READY,
)
from tools.check_evidence_alignment import normalize_text


VERSION = "0.4.7.5.3"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_ACTION_CANDIDATES_PATH = Path("tests/evidence_manual_review_action_candidates.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_fixture_candidate_pool.json")

POOL_STATUS_READY = "ready_from_valid_decision"
POOL_STATUS_BLOCKED = "blocked_pending_manual_review"

FIXTURE_TYPE_PRIMARY_EVIDENCE = "primary_evidence_grounding_fixture"
FIXTURE_TYPE_FUNCTIONAL_TYPING = "functional_typing_fixture"
FIXTURE_TYPE_FINAL_SELECTION = "final_selection_grounding_fixture"
FIXTURE_TYPE_SCENARIO_CORE = "scenario_core_scope_fixture"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def unique_list(values: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for value in values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def decision_map(decision_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        normalize_text(record.get("case_id")): record
        for record in decision_schema.get("decision_records") or []
        if isinstance(record, dict) and normalize_text(record.get("case_id"))
    }


def fixture_types(record: dict[str, Any], action_type: str) -> list[str]:
    issues = set(record.get("issue_types") or [])
    roots = set(record.get("suggested_root_causes") or [])
    reviewer_decision = record.get("reviewer_decision") if isinstance(record.get("reviewer_decision"), dict) else {}
    roots.update(reviewer_decision.get("confirmed_root_causes") or [])
    types = []

    if action_type == ACTION_PRIMARY_FIXTURE or "primary_evidence_gap" in roots or "primary_evidence_lost" in issues:
        types.append(FIXTURE_TYPE_PRIMARY_EVIDENCE)
    if action_type == ACTION_FUNCTIONAL_FIXTURE or "functional_typing_metadata" in roots or "definition_core_candidate" in issues:
        types.append(FIXTURE_TYPE_FUNCTIONAL_TYPING)
    if "final_evidence_selection_policy" in roots or "rerank_input_to_final_loss" in issues:
        types.append(FIXTURE_TYPE_FINAL_SELECTION)
    if "scenario_core_scope" in roots or "scenario_core_gap" in issues:
        types.append(FIXTURE_TYPE_SCENARIO_CORE)
    return unique_list(types)


def fixture_references(record: dict[str, Any]) -> dict[str, Any]:
    evidence_context = record.get("evidence_context") if isinstance(record.get("evidence_context"), dict) else {}
    return {
        "missing_final_expected": evidence_context.get("missing_final_expected") or [],
        "missing_scenario_core": evidence_context.get("missing_scenario_core") or [],
        "lost_evidence": evidence_context.get("lost_evidence") or [],
        "final_evidence": evidence_context.get("final_evidence") or [],
    }


def fixture_candidate(action_candidate: dict[str, Any], record: dict[str, Any]) -> dict[str, Any] | None:
    action_type = normalize_text(action_candidate.get("action_type"))
    types = fixture_types(record, action_type)
    if not types:
        return None

    readiness = normalize_text(action_candidate.get("readiness"))
    status = POOL_STATUS_READY if readiness == READINESS_READY else POOL_STATUS_BLOCKED
    return {
        "case_id": normalize_text(action_candidate.get("case_id")),
        "fixture_status": status,
        "source_action_type": action_type,
        "source_action_category": ACTION_CATEGORIES.get(action_type, "unknown"),
        "fixture_types": types,
        "priority_score": action_candidate.get("priority_score"),
        "risk_level": action_candidate.get("risk_level"),
        "expected_domains": action_candidate.get("expected_domains") or [],
        "issue_types": record.get("issue_types") or [],
        "suggested_root_causes": record.get("suggested_root_causes") or [],
        "confirmed_root_causes": action_candidate.get("confirmed_root_causes") or [],
        "fixture_references": fixture_references(record),
        "blocked_reason": (
            "Manual decision is pending; fixture candidate must not be written into eval cases."
            if status == POOL_STATUS_BLOCKED
            else ""
        ),
        "allowed_next_step": (
            "draft_fixture_after_manual_confirmation"
            if status == POOL_STATUS_READY
            else "await_manual_review_decision"
        ),
    }


def build_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter()
    fixture_type_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    ready_cases = set()
    blocked_cases = set()

    for candidate in candidates:
        status = candidate.get("fixture_status")
        status_counts[status] += 1
        if status == POOL_STATUS_READY:
            ready_cases.add(candidate.get("case_id"))
        if status == POOL_STATUS_BLOCKED:
            blocked_cases.add(candidate.get("case_id"))
        for fixture_type in candidate.get("fixture_types") or []:
            fixture_type_counts[fixture_type] += 1
        for domain in candidate.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["fixture_candidates"] += 1
            if status == POOL_STATUS_READY:
                domain_summary[domain]["ready_candidates"] += 1
            if status == POOL_STATUS_BLOCKED:
                domain_summary[domain]["blocked_candidates"] += 1

    return {
        "total_fixture_candidates": len(candidates),
        "ready_fixture_candidates": status_counts.get(POOL_STATUS_READY, 0),
        "blocked_fixture_candidates": status_counts.get(POOL_STATUS_BLOCKED, 0),
        "ready_case_count": len(ready_cases),
        "blocked_case_count": len(blocked_cases),
        "fixture_status_summary": dict(sorted(status_counts.items())),
        "fixture_type_summary": dict(sorted(fixture_type_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
    }


def build_report(
    decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH,
    action_candidates_path: Path = DEFAULT_ACTION_CANDIDATES_PATH,
) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    action_report = load_json(action_candidates_path)
    records = decision_map(decision_schema)
    candidates = []
    for action_candidate in action_report.get("action_candidates") or []:
        if not isinstance(action_candidate, dict):
            continue
        record = records.get(normalize_text(action_candidate.get("case_id"))) or {}
        candidate = fixture_candidate(action_candidate, record)
        if candidate:
            candidates.append(candidate)
    candidates = sorted(
        candidates,
        key=lambda item: (
            item.get("fixture_status") != POOL_STATUS_READY,
            -int(item.get("priority_score") or 0),
            item.get("case_id") or "",
            item.get("source_action_type") or "",
        ),
    )
    return {
        "version": VERSION,
        "scope": "offline evidence fixture candidate pool",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
            "action_candidates": str(action_candidates_path),
            "action_candidates_version": action_report.get("version"),
        },
        "policy": {
            "ready_fixture_candidates": "May be drafted only after valid completed manual decisions.",
            "blocked_fixture_candidates": "Must not be written into eval cases; wait for manual confirmation.",
            "eval_case_mutation": "disallowed",
            "hidden_seed_mutation": "disallowed",
        },
        "summary": build_summary(candidates),
        "fixture_candidates": candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an offline evidence fixture candidate pool.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--action-candidates", type=Path, default=DEFAULT_ACTION_CANDIDATES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema, args.action_candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Evidence fixture candidate pool built: "
        f"{summary['total_fixture_candidates']} candidates, "
        f"{summary['ready_fixture_candidates']} ready, "
        f"{summary['blocked_fixture_candidates']} blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
