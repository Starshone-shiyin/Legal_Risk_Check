"""Build the v0.4.7.4.x evidence quality action-series baseline.

This report freezes the execution order, inputs, and boundaries for follow-up
offline audits. It does not change retrieval, anchors, rerank, prompts, risk
rules, or eval cases.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.4.0"

DEFAULT_ACTION_PLAN_PATH = legacy_report_path("evidence_root_cause_action_plan.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_action_series_baseline.json")

SERIES_STEPS = [
    {
        "version": "0.4.7.4.1",
        "name": "Evidence Report Enrichment Hardening",
        "goal": "Investigate enrichment unmatched evidence and stabilize enrichment diagnostics.",
        "inputs": ["tests/evidence_coverage_report.json"],
        "expected_output": "tests/evidence_enrichment_hardening_report.json",
        "boundary": "Do not write back ingestion metadata or change retrieval behavior.",
    },
    {
        "version": "0.4.7.4.2",
        "name": "Scenario Registry Calibration",
        "goal": "Audit scenario core gaps against manual review candidates and registry metadata.",
        "inputs": ["config/scenario_registry.json", "tests/evidence_manual_review_dataset.json"],
        "expected_output": "tests/scenario_registry_calibration_report.json",
        "boundary": "Do not edit eval cases or scenario registry entries in this version.",
    },
    {
        "version": "0.4.7.4.3",
        "name": "Base Retrieval Quality Audit",
        "goal": "Audit dense/sparse/union coverage gaps without tuning retrieval.",
        "inputs": ["tests/evidence_coverage_report.json", "tests/evidence_manual_review_dataset.json"],
        "expected_output": "tests/base_retrieval_quality_audit_report.json",
        "boundary": "Do not change dense, sparse, fusion, or rerank settings.",
    },
    {
        "version": "0.4.7.4.4",
        "name": "Anchor Dependency Audit",
        "goal": "Distinguish healthy anchor support from anchor masking weak base retrieval.",
        "inputs": ["tests/evidence_coverage_report.json", "tests/evidence_manual_review_dataset.json"],
        "expected_output": "tests/anchor_dependency_audit_report.json",
        "boundary": "Do not add or edit anchor rules.",
    },
    {
        "version": "0.4.7.4.5",
        "name": "Final Evidence Selection Audit",
        "goal": "Audit rerank_input to final evidence coverage loss patterns.",
        "inputs": ["tests/evidence_coverage_report.json", "tests/evidence_manual_review_dataset.json"],
        "expected_output": "tests/final_evidence_selection_audit_report.json",
        "boundary": "Do not change rerank, final truncation, or evidence selection logic.",
    },
    {
        "version": "0.4.7.4.6",
        "name": "Manual Review Loop",
        "goal": "Prepare reviewer decision schema and follow-up action tracking.",
        "inputs": ["tests/evidence_manual_review_dataset.json", "tests/evidence_root_cause_action_plan.json"],
        "expected_output": "tests/evidence_manual_review_loop_report.json",
        "boundary": "Do not fabricate reviewer decisions; keep all review items pending unless supplied by a human.",
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_baseline(action_plan_path: Path = DEFAULT_ACTION_PLAN_PATH) -> dict[str, Any]:
    action_plan = load_json(action_plan_path)
    planned_versions = {
        action.get("target_version")
        for action in action_plan.get("actions") or []
        if action.get("target_version")
    }
    steps = []
    for step in SERIES_STEPS:
        linked_actions = [
            action
            for action in action_plan.get("actions") or []
            if action.get("target_version") == step["version"]
        ]
        steps.append({
            **step,
            "planned_actions": linked_actions,
            "has_action_plan_link": step["version"] in planned_versions or step["version"] == "0.4.7.4.1",
            "status": "planned",
        })
    return {
        "version": VERSION,
        "scope": "offline evidence quality action series baseline",
        "inputs": {
            "action_plan": str(action_plan_path),
            "action_plan_version": action_plan.get("version"),
        },
        "summary": {
            "total_steps": len(steps),
            "planned_action_count": len(action_plan.get("actions") or []),
            "series": "0.4.7.4.x Evidence Quality Action Series",
            "execution_order": [step["version"] for step in steps],
        },
        "global_boundaries": [
            "Do not fix hidden seeds.",
            "Do not add anchors.",
            "Do not modify rerank.",
            "Do not modify prompts.",
            "Do not modify risk supplement or term preservation rules.",
            "Do not modify eval cases.",
            "Do not connect diagnostics to rag_query main flow.",
            "Do not run full eval for these offline audit versions.",
        ],
        "steps": steps,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build evidence action-series baseline.")
    parser.add_argument("--action-plan", type=Path, default=DEFAULT_ACTION_PLAN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_baseline(args.action_plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Evidence action-series baseline built: "
        f"{report['summary']['total_steps']} planned steps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
