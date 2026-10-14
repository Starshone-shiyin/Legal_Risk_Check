"""Build a dry-run routing report for ready manual-review actions.

Only ready_from_valid_decision candidates are routed. Pending/blocked
candidates remain blocked and are never treated as authorized engineering work.
The report does not modify retrieval, rerank, prompts, anchors, risk rules,
eval cases, hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "0.4.7.6.3"

DEFAULT_ACTION_CANDIDATES_PATH = Path("tests/evidence_manual_review_action_candidates.json")
DEFAULT_PROGRESS_REPORT_PATH = Path("tests/evidence_manual_review_progress_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/ready_action_routing_dry_run_report.json")

READINESS_READY = "ready_from_valid_decision"
READINESS_BLOCKED = "blocked_pending_manual_review"

ROUTE_RETRIEVAL_INPUT = "v0.4.9.x_retrieval_input_quality_governance"
ROUTE_SCENARIO_CORE = "scenario_registry_core_review"
ROUTE_FINAL_SELECTION = "v0.4.8.x_final_evidence_selection_policy_design"
ROUTE_FIXTURE = "fixture_draft_governance"
ROUTE_ANCHOR = "anchor_dependency_governance"
ROUTE_MANUAL_GROUNDING = "manual_grounding_review_queue"
ROUTE_ADDITIONAL_CAPTURE = "offline_diagnostic_capture"
ROUTE_NO_ACTION = "no_action_archive"

ACTION_ROUTE_MAP = {
    "metadata_chunking_or_query_coverage_review": ROUTE_RETRIEVAL_INPUT,
    "source_index_coverage_review": ROUTE_RETRIEVAL_INPUT,
    "anchor_dependency_governance_review": ROUTE_ANCHOR,
    "scenario_registry_core_article_review": ROUTE_SCENARIO_CORE,
    "final_evidence_selection_policy_review": ROUTE_FINAL_SELECTION,
    "primary_evidence_fixture_candidate_review": ROUTE_FIXTURE,
    "functional_typing_fixture_review": ROUTE_FIXTURE,
    "high_risk_manual_grounding_review": ROUTE_MANUAL_GROUNDING,
    "needs_additional_evidence_capture": ROUTE_ADDITIONAL_CAPTURE,
    "no_action": ROUTE_NO_ACTION,
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def route_for_action(action_type: str) -> str:
    return ACTION_ROUTE_MAP.get(action_type, "unmapped_action")


def route_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    action_type = candidate.get("action_type") or ""
    return {
        "case_id": candidate.get("case_id"),
        "action_type": action_type,
        "route": route_for_action(action_type),
        "priority_score": candidate.get("priority_score"),
        "risk_level": candidate.get("risk_level"),
        "expected_domains": candidate.get("expected_domains") or [],
        "confirmed_root_causes": candidate.get("confirmed_root_causes") or [],
        "target_areas": candidate.get("target_areas") or [],
        "rationale": candidate.get("rationale") or "",
    }


def build_summary(ready_routes: list[dict[str, Any]], blocked_candidates: list[dict[str, Any]], progress_summary: dict[str, Any]) -> dict[str, Any]:
    route_counts = Counter()
    action_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    for item in ready_routes:
        route_counts[item.get("route")] += 1
        action_counts[item.get("action_type")] += 1
        for domain in item.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["ready_routes"] += 1

    readiness_state = "ready_actions_available" if ready_routes else "manual_review_required"
    return {
        "ready_routes": len(ready_routes),
        "blocked_candidates": len(blocked_candidates),
        "readiness_state": readiness_state,
        "manual_review_completed_cases": progress_summary.get("completed_cases", 0),
        "manual_review_pending_cases": progress_summary.get("pending_cases", 0),
        "route_summary": dict(sorted(route_counts.items())),
        "action_type_summary": dict(sorted(action_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
    }


def build_report(
    action_candidates_path: Path = DEFAULT_ACTION_CANDIDATES_PATH,
    progress_report_path: Path = DEFAULT_PROGRESS_REPORT_PATH,
) -> dict[str, Any]:
    action_report = load_json(action_candidates_path)
    progress_report = load_json(progress_report_path)
    candidates = [
        item
        for item in action_report.get("action_candidates") or []
        if isinstance(item, dict)
    ]
    ready = [item for item in candidates if item.get("readiness") == READINESS_READY]
    blocked = [item for item in candidates if item.get("readiness") == READINESS_BLOCKED]
    routed = [route_candidate(item) for item in ready]
    routed = sorted(routed, key=lambda item: (item.get("route") or "", -int(item.get("priority_score") or 0), item.get("case_id") or ""))
    return {
        "version": VERSION,
        "scope": "offline ready action routing dry run",
        "inputs": {
            "action_candidates": str(action_candidates_path),
            "action_candidates_version": action_report.get("version"),
            "progress_report": str(progress_report_path),
            "progress_report_version": progress_report.get("version"),
        },
        "routing_policy": {
            "only_ready_from_valid_decision": True,
            "blocked_candidates_are_not_routed": True,
            "main_flow_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
        },
        "summary": build_summary(routed, blocked, progress_report.get("summary") or {}),
        "ready_routes": routed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ready action routing dry-run report.")
    parser.add_argument("--action-candidates", type=Path, default=DEFAULT_ACTION_CANDIDATES_PATH)
    parser.add_argument("--progress-report", type=Path, default=DEFAULT_PROGRESS_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.action_candidates, args.progress_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Ready action routing dry run built: "
        f"{summary['ready_routes']} ready routes, "
        f"{summary['blocked_candidates']} blocked candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
