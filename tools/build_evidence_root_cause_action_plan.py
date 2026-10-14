"""Build an offline action plan from evidence coverage root causes.

This is a planning/reporting tool only. It maps diagnostics to future audit
versions and does not change retrieval, rerank, prompts, anchors, or eval cases.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.3.5"

DEFAULT_COVERAGE_REPORT_PATH = legacy_report_path("evidence_coverage_report.json")
DEFAULT_TRIAGE_REPORT_PATH = legacy_report_path("evidence_coverage_triage_report.json")
DEFAULT_MANUAL_REVIEW_DATASET_PATH = legacy_report_path("evidence_manual_review_dataset.json")
DEFAULT_GATE_DRAFT_REPORT_PATH = legacy_report_path("evidence_coverage_gate_draft_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_root_cause_action_plan.json")


ACTION_CATALOG = {
    "scenario_core_gap": {
        "action_id": "scenario_registry_calibration",
        "target_version": "0.4.7.4.2",
        "title": "Scenario Registry Calibration",
        "goal": "Check whether scenario core articles are too broad, missing, or correctly absent from final evidence.",
        "boundary": "Do not edit eval cases or patch hidden seeds; produce calibration findings first.",
    },
    "base_retrieval_gap": {
        "action_id": "base_retrieval_quality_audit",
        "target_version": "0.4.7.4.3",
        "title": "Base Retrieval Quality Audit",
        "goal": "Audit dense/sparse/union coverage gaps using existing diagnostics and enriched evidence context.",
        "boundary": "Do not tune retrieval or rerank; identify metadata/chunking/source issues first.",
    },
    "anchor_dependency": {
        "action_id": "anchor_dependency_audit",
        "target_version": "0.4.7.4.4",
        "title": "Anchor Dependency Audit",
        "goal": "Separate healthy anchor support from anchor masking weak base retrieval.",
        "boundary": "Do not add anchors; audit dependency patterns first.",
    },
    "final_selection_loss": {
        "action_id": "final_evidence_selection_audit",
        "target_version": "0.4.7.4.5",
        "title": "Final Evidence Selection Audit",
        "goal": "Inspect cases where rerank_input coverage is higher than final evidence coverage.",
        "boundary": "Do not change rerank or final truncation logic; report loss patterns first.",
    },
    "final_primary_gap": {
        "action_id": "primary_evidence_review_loop",
        "target_version": "0.4.7.4.6",
        "title": "Primary Evidence Manual Review Loop",
        "goal": "Use manual review samples to confirm whether primary expected evidence is truly missing.",
        "boundary": "Do not rewrite expected evidence; capture reviewer decisions and follow-up actions.",
    },
    "low_final_coverage": {
        "action_id": "high_risk_manual_review_queue",
        "target_version": "0.4.7.4.6",
        "title": "High-Risk Manual Review Queue",
        "goal": "Prioritize low final coverage cases for manual grounding review.",
        "boundary": "Do not force pass; route to review dataset and action tracking.",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def count_review_items_by_root(manual_review_dataset: dict[str, Any]) -> Counter:
    counts = Counter()
    for item in manual_review_dataset.get("review_items") or []:
        for cause in item.get("root_causes") or []:
            counts[cause] += 1
    return counts


def sample_case_ids(manual_review_dataset: dict[str, Any], root_cause: str, limit: int = 5) -> list[str]:
    case_ids = []
    for item in manual_review_dataset.get("review_items") or []:
        if root_cause in (item.get("root_causes") or []):
            case_ids.append(str(item.get("case_id")))
    return case_ids[:limit]


def build_actions(
    triage_report: dict[str, Any],
    manual_review_dataset: dict[str, Any],
) -> list[dict[str, Any]]:
    root_summary = (triage_report.get("summary") or {}).get("root_cause_summary") or {}
    review_counts = count_review_items_by_root(manual_review_dataset)
    actions = []
    for root_cause, catalog in ACTION_CATALOG.items():
        observed_cases = int(root_summary.get(root_cause, 0))
        review_items = int(review_counts.get(root_cause, 0))
        if not observed_cases and not review_items:
            continue
        priority = "P1" if root_cause in {"scenario_core_gap", "final_primary_gap"} else "P2"
        if root_cause == "low_final_coverage":
            priority = "P0"
        actions.append({
            **catalog,
            "root_cause": root_cause,
            "priority": priority,
            "observed_cases": observed_cases,
            "manual_review_items": review_items,
            "sample_case_ids": sample_case_ids(manual_review_dataset, root_cause),
            "status": "planned",
        })

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(
        actions,
        key=lambda item: (
            priority_order.get(item["priority"], 9),
            item["target_version"],
            item["action_id"],
        ),
    )


def build_summary(actions: list[dict[str, Any]], gate_draft_report: dict[str, Any]) -> dict[str, Any]:
    by_priority = Counter(action["priority"] for action in actions)
    by_version = Counter(action["target_version"] for action in actions)
    return {
        "total_actions": len(actions),
        "by_priority": dict(sorted(by_priority.items())),
        "by_target_version": dict(sorted(by_version.items())),
        "gate_draft_passed": (gate_draft_report.get("summary") or {}).get("failed_gates", 0) == 0,
        "next_series": "0.4.7.4.x Evidence Quality Action Series",
    }


def build_plan(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    triage_report_path: Path = DEFAULT_TRIAGE_REPORT_PATH,
    manual_review_dataset_path: Path = DEFAULT_MANUAL_REVIEW_DATASET_PATH,
    gate_draft_report_path: Path = DEFAULT_GATE_DRAFT_REPORT_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    triage_report = load_json(triage_report_path)
    manual_review_dataset = load_json(manual_review_dataset_path)
    gate_draft_report = load_json(gate_draft_report_path)
    actions = build_actions(triage_report, manual_review_dataset)
    return {
        "version": VERSION,
        "scope": "offline evidence root cause action plan",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "triage_report": str(triage_report_path),
            "triage_report_version": triage_report.get("version"),
            "manual_review_dataset": str(manual_review_dataset_path),
            "manual_review_dataset_version": manual_review_dataset.get("version"),
            "gate_draft_report": str(gate_draft_report_path),
            "gate_draft_report_version": gate_draft_report.get("version"),
        },
        "summary": build_summary(actions, gate_draft_report),
        "actions": actions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an evidence root cause action plan.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT_PATH)
    parser.add_argument("--manual-review-dataset", type=Path, default=DEFAULT_MANUAL_REVIEW_DATASET_PATH)
    parser.add_argument("--gate-draft-report", type=Path, default=DEFAULT_GATE_DRAFT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_plan(
        args.coverage_report,
        args.triage_report,
        args.manual_review_dataset,
        args.gate_draft_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Evidence root cause action plan built: "
        f"{report['summary']['total_actions']} planned actions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
