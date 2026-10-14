"""Draft non-enforcing evidence coverage quality gates.

This tool proposes release-gate signals from offline coverage artifacts. By
default it never fails the build; use --fail-on-blocking only for experiments.
It does not call rag_query, Qdrant, rerank, prompts, or risk rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.3.4"

DEFAULT_COVERAGE_REPORT_PATH = legacy_report_path("evidence_coverage_report.json")
DEFAULT_TRIAGE_REPORT_PATH = legacy_report_path("evidence_coverage_triage_report.json")
DEFAULT_MANUAL_REVIEW_DATASET_PATH = legacy_report_path("evidence_manual_review_dataset.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_coverage_gate_draft_report.json")

SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_BLOCKING_DRAFT = "blocking_draft"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def nested(mapping: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def gate_result(
    gate_id: str,
    description: str,
    observed: int | float,
    threshold: int | float,
    operator: str,
    severity: str,
    rationale: str,
) -> dict[str, Any]:
    if operator == "<=":
        passed = observed <= threshold
    elif operator == ">=":
        passed = observed >= threshold
    else:
        raise ValueError(f"unsupported operator: {operator}")
    return {
        "gate_id": gate_id,
        "description": description,
        "observed": observed,
        "threshold": threshold,
        "operator": operator,
        "passed": passed,
        "severity": severity,
        "rationale": rationale,
    }


def build_gates(
    coverage_report: dict[str, Any],
    triage_report: dict[str, Any],
    manual_review_dataset: dict[str, Any],
) -> list[dict[str, Any]]:
    coverage_summary = coverage_report.get("summary") or {}
    triage_summary = triage_report.get("summary") or {}
    manual_summary = manual_review_dataset.get("summary") or {}
    issue_summary = coverage_summary.get("issue_type_summary") or {}
    root_summary = triage_summary.get("root_cause_summary") or {}

    high_priority = nested(
        triage_summary,
        "triage_status_summary",
        "high_priority_review",
        default=0,
    )
    review_cases = coverage_summary.get("review_cases", 0)
    total_cases = coverage_summary.get("total_cases", 0)
    final_coverage = nested(coverage_summary, "layer_summary", "final", "coverage_ratio", default=0.0)
    enrichment_ratio = nested(coverage_summary, "enrichment_summary", "matched_ratio", default=0.0)
    final_selection_loss = root_summary.get("final_selection_loss", 0)
    scenario_core_gap = issue_summary.get("scenario_core_gap", 0)
    manual_pending = manual_summary.get("pending_review_items", 0)

    return [
        gate_result(
            "draft.high_priority_review.max",
            "High-priority manual review cases should not exceed the current draft ceiling.",
            int(high_priority),
            12,
            "<=",
            SEVERITY_BLOCKING_DRAFT,
            "Current baseline has 12 high-priority review cases; future releases should not increase this before root-cause fixes.",
        ),
        gate_result(
            "draft.review_ratio.max",
            "Coverage review ratio should stay below the draft ceiling.",
            round(review_cases / total_cases, 3) if total_cases else 0.0,
            0.6,
            "<=",
            SEVERITY_WARN,
            "Review ratio is a trend signal, not a release blocker in this draft.",
        ),
        gate_result(
            "draft.final_coverage.min",
            "Final expected evidence coverage should stay above the draft floor.",
            float(final_coverage),
            0.9,
            ">=",
            SEVERITY_WARN,
            "Final coverage is already high; the draft gate catches regressions.",
        ),
        gate_result(
            "draft.enrichment_ratio.min",
            "Evidence enrichment match ratio should stay above the draft floor.",
            float(enrichment_ratio),
            0.99,
            ">=",
            SEVERITY_WARN,
            "Functional coverage depends on evidence text/function metadata enrichment.",
        ),
        gate_result(
            "draft.final_selection_loss.max",
            "Final selection loss cases should not exceed the current draft ceiling.",
            int(final_selection_loss),
            7,
            "<=",
            SEVERITY_WARN,
            "This catches regressions from rerank_input coverage to final evidence coverage.",
        ),
        gate_result(
            "draft.scenario_core_gap.max",
            "Scenario core gap cases should not exceed the current draft ceiling.",
            int(scenario_core_gap),
            8,
            "<=",
            SEVERITY_WARN,
            "Scenario core gaps require manual validation before registry or retrieval changes.",
        ),
        gate_result(
            "draft.manual_review_dataset.pending.max",
            "Pending manual review dataset should not exceed the current draft ceiling.",
            int(manual_pending),
            12,
            "<=",
            SEVERITY_INFO,
            "The dataset is intentionally pending; this is a workload tracking signal.",
        ),
    ]


def build_summary(gates: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [gate for gate in gates if not gate["passed"]]
    blocking = [
        gate for gate in failed if gate.get("severity") == SEVERITY_BLOCKING_DRAFT
    ]
    return {
        "total_gates": len(gates),
        "passed_gates": sum(1 for gate in gates if gate["passed"]),
        "failed_gates": len(failed),
        "blocking_draft_failures": len(blocking),
        "non_enforcing": True,
        "default_exit_behavior": "always_zero_unless_fail_on_blocking_is_set",
    }


def build_report(
    coverage_report_path: Path = DEFAULT_COVERAGE_REPORT_PATH,
    triage_report_path: Path = DEFAULT_TRIAGE_REPORT_PATH,
    manual_review_dataset_path: Path = DEFAULT_MANUAL_REVIEW_DATASET_PATH,
) -> dict[str, Any]:
    coverage_report = load_json(coverage_report_path)
    triage_report = load_json(triage_report_path)
    manual_review_dataset = load_json(manual_review_dataset_path)
    gates = build_gates(coverage_report, triage_report, manual_review_dataset)
    return {
        "version": VERSION,
        "scope": "draft non-enforcing evidence coverage quality gates",
        "inputs": {
            "coverage_report": str(coverage_report_path),
            "coverage_report_version": coverage_report.get("version"),
            "triage_report": str(triage_report_path),
            "triage_report_version": triage_report.get("version"),
            "manual_review_dataset": str(manual_review_dataset_path),
            "manual_review_dataset_version": manual_review_dataset.get("version"),
        },
        "summary": build_summary(gates),
        "gates": gates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft evidence coverage quality gates.")
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT_PATH)
    parser.add_argument("--triage-report", type=Path, default=DEFAULT_TRIAGE_REPORT_PATH)
    parser.add_argument("--manual-review-dataset", type=Path, default=DEFAULT_MANUAL_REVIEW_DATASET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-blocking", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.coverage_report, args.triage_report, args.manual_review_dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Evidence coverage gate draft completed: "
        f"{summary['passed_gates']}/{summary['total_gates']} gates passed, "
        f"{summary['blocking_draft_failures']} blocking draft failures"
    )
    if args.fail_on_blocking and summary["blocking_draft_failures"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
