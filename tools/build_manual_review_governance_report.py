"""Build the v0.4.7.5.x manual-review governance report.

This report consolidates decision schema, validation, action candidates, and
fixture candidate pool outputs. It is a governance summary only and does not
modify retrieval, rerank, prompts, anchors, risk rules, eval cases, or hidden
seeds.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "0.4.7.5.4"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_VALIDATION_REPORT_PATH = Path("tests/evidence_manual_review_decision_validation_report.json")
DEFAULT_ACTION_CANDIDATES_PATH = Path("tests/evidence_manual_review_action_candidates.json")
DEFAULT_FIXTURE_POOL_PATH = Path("tests/evidence_fixture_candidate_pool.json")
DEFAULT_OUTPUT_PATH = Path("tests/evidence_manual_review_governance_report.json")

RECOMMENDATION_MANUAL_REVIEW = "complete_manual_review_decisions_first"
RECOMMENDATION_RETRIEVAL_INPUT = "plan_metadata_chunking_query_coverage_governance"
RECOMMENDATION_ANCHOR = "plan_anchor_dependency_governance_after_manual_confirmation"
RECOMMENDATION_SCENARIO = "plan_scenario_core_article_review_after_manual_confirmation"
RECOMMENDATION_FINAL_SELECTION = "plan_final_evidence_policy_design_after_manual_confirmation"
RECOMMENDATION_FIXTURE = "keep_fixture_candidates_blocked_until_valid_decisions"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def counter_from(summary: dict[str, Any], key: str) -> Counter:
    return Counter(summary.get(key) or {})


def merge_counters(*counters: Counter) -> dict[str, int]:
    merged = Counter()
    for counter in counters:
        merged.update(counter)
    return dict(sorted(merged.items()))


def readiness_state(action_summary: dict[str, Any], fixture_summary: dict[str, Any]) -> str:
    if action_summary.get("ready_action_candidates", 0) or fixture_summary.get("ready_fixture_candidates", 0):
        return "has_ready_candidates"
    if action_summary.get("blocked_pending_candidates", 0) or fixture_summary.get("blocked_fixture_candidates", 0):
        return "manual_review_required"
    return "no_candidates"


def next_recommendations(action_summary: dict[str, Any], fixture_summary: dict[str, Any]) -> list[dict[str, Any]]:
    action_types = action_summary.get("action_type_summary") or {}
    recommendations = [
        {
            "recommendation": RECOMMENDATION_MANUAL_REVIEW,
            "priority": "P0",
            "reason": "All current candidates are blocked until manual decisions are completed and validated.",
        }
    ]
    if action_types.get("metadata_chunking_or_query_coverage_review"):
        recommendations.append({
            "recommendation": RECOMMENDATION_RETRIEVAL_INPUT,
            "priority": "P1",
            "reason": "Base retrieval quality and anchor rescue signals point to metadata, chunking, or lexical coverage review.",
        })
    if action_types.get("anchor_dependency_governance_review"):
        recommendations.append({
            "recommendation": RECOMMENDATION_ANCHOR,
            "priority": "P1",
            "reason": "Anchor dependency appears frequently and should be governed after reviewer confirmation.",
        })
    if action_types.get("scenario_registry_core_article_review"):
        recommendations.append({
            "recommendation": RECOMMENDATION_SCENARIO,
            "priority": "P2",
            "reason": "Scenario core gaps require human scope calibration before registry edits.",
        })
    if action_types.get("final_evidence_selection_policy_review"):
        recommendations.append({
            "recommendation": RECOMMENDATION_FINAL_SELECTION,
            "priority": "P2",
            "reason": "Final evidence selection loss should be reviewed before any policy design.",
        })
    if fixture_summary.get("blocked_fixture_candidates", 0):
        recommendations.append({
            "recommendation": RECOMMENDATION_FIXTURE,
            "priority": "P2",
            "reason": "Fixture candidates exist but cannot become eval cases without valid manual decisions.",
        })
    return recommendations


def build_domain_summary(
    decision_summary: dict[str, Any],
    action_summary: dict[str, Any],
    fixture_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    domains = set()
    for summary in (decision_summary, action_summary, fixture_summary):
        domains.update((summary.get("per_domain_summary") or {}).keys())
    result: dict[str, dict[str, Any]] = {}
    for domain in sorted(domains):
        result[domain] = {
            "decision_records": ((decision_summary.get("per_domain_summary") or {}).get(domain) or {}).get("decision_records", 0),
            "action_candidates": ((action_summary.get("per_domain_summary") or {}).get(domain) or {}).get("action_candidates", 0),
            "ready_action_candidates": ((action_summary.get("per_domain_summary") or {}).get(domain) or {}).get("ready_candidates", 0),
            "blocked_action_candidates": ((action_summary.get("per_domain_summary") or {}).get(domain) or {}).get("blocked_candidates", 0),
            "fixture_candidates": ((fixture_summary.get("per_domain_summary") or {}).get(domain) or {}).get("fixture_candidates", 0),
            "ready_fixture_candidates": ((fixture_summary.get("per_domain_summary") or {}).get(domain) or {}).get("ready_candidates", 0),
            "blocked_fixture_candidates": ((fixture_summary.get("per_domain_summary") or {}).get(domain) or {}).get("blocked_candidates", 0),
        }
    return result


def build_report(
    decision_schema_path: Path = DEFAULT_DECISION_SCHEMA_PATH,
    validation_report_path: Path = DEFAULT_VALIDATION_REPORT_PATH,
    action_candidates_path: Path = DEFAULT_ACTION_CANDIDATES_PATH,
    fixture_pool_path: Path = DEFAULT_FIXTURE_POOL_PATH,
) -> dict[str, Any]:
    decision_schema = load_json(decision_schema_path)
    validation_report = load_json(validation_report_path)
    action_report = load_json(action_candidates_path)
    fixture_pool = load_json(fixture_pool_path)

    decision_summary = decision_schema.get("summary") or {}
    validation_summary = validation_report.get("summary") or {}
    action_summary = action_report.get("summary") or {}
    fixture_summary = fixture_pool.get("summary") or {}

    state = readiness_state(action_summary, fixture_summary)
    recommendations = next_recommendations(action_summary, fixture_summary)

    summary = {
        "decision_records": decision_summary.get("total_decision_records", 0),
        "pending_decisions": decision_summary.get("pending_decisions", 0),
        "invalid_decisions": validation_summary.get("invalid_records", 0),
        "ready_action_candidates": action_summary.get("ready_action_candidates", 0),
        "blocked_action_candidates": action_summary.get("blocked_pending_candidates", 0),
        "ready_fixture_candidates": fixture_summary.get("ready_fixture_candidates", 0),
        "blocked_fixture_candidates": fixture_summary.get("blocked_fixture_candidates", 0),
        "readiness_state": state,
        "recommendation_count": len(recommendations),
    }

    return {
        "version": VERSION,
        "scope": "manual review decision governance summary",
        "inputs": {
            "decision_schema": str(decision_schema_path),
            "decision_schema_version": decision_schema.get("version"),
            "decision_validation_report": str(validation_report_path),
            "decision_validation_report_version": validation_report.get("version"),
            "action_candidates": str(action_candidates_path),
            "action_candidates_version": action_report.get("version"),
            "fixture_pool": str(fixture_pool_path),
            "fixture_pool_version": fixture_pool.get("version"),
        },
        "guardrails": {
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
            "risk_supplement_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "rag_query_integration": "disallowed",
        },
        "summary": summary,
        "issue_type_summary": merge_counters(counter_from(decision_summary, "issue_type_summary")),
        "action_type_summary": action_summary.get("action_type_summary") or {},
        "fixture_type_summary": fixture_summary.get("fixture_type_summary") or {},
        "per_domain_summary": build_domain_summary(decision_summary, action_summary, fixture_summary),
        "recommendations": recommendations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manual-review governance summary.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument("--action-candidates", type=Path, default=DEFAULT_ACTION_CANDIDATES_PATH)
    parser.add_argument("--fixture-pool", type=Path, default=DEFAULT_FIXTURE_POOL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.decision_schema, args.validation_report, args.action_candidates, args.fixture_pool)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review governance report built: "
        f"{summary['decision_records']} decisions, "
        f"{summary['ready_action_candidates']} ready actions, "
        f"{summary['blocked_action_candidates']} blocked actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
