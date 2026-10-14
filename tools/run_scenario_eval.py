"""Run RAG eval cases grouped by scenario_registry.json scenarios."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.run_rag_eval import build_contribution_summary, load_cases, run_case
from tools.check_scenario_registry import load_json


DEFAULT_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/scenario_eval_report.json")
DEFAULT_SUMMARY_PATH = Path("tests/scenario_eval_summary.md")


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    registry = load_json(path)
    scenarios = registry.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("registry.scenarios must be a list")
    return [scenario for scenario in scenarios if isinstance(scenario, dict)]


def case_map(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_id = case.get("id")
        if case_id:
            mapped[case_id] = case
    return mapped


def scenario_eval_case_ids(scenarios: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for scenario in scenarios:
        for case_id in scenario.get("eval_case_ids") or []:
            if case_id not in seen:
                ids.append(case_id)
                seen.add(case_id)
    return ids


def missing_case_ids(scenarios: list[dict[str, Any]], cases_by_id: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for scenario in scenarios:
        scenario_id = scenario.get("scenario_id", "")
        missing_ids = [
            case_id
            for case_id in scenario.get("eval_case_ids") or []
            if case_id not in cases_by_id
        ]
        if missing_ids:
            missing[scenario_id] = missing_ids
    return missing


def stage_summary(reports: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for report in reports:
        stage = report.get("retrieval_diagnostics", {}).get("failure_stage", "UNKNOWN")
        summary[stage] = summary.get(stage, 0) + 1
    return summary


def summarize_scenarios(
    scenarios: list[dict[str, Any]],
    reports_by_case_id: dict[str, dict[str, Any]],
    missing_by_scenario: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    summaries = []
    missing_by_scenario = missing_by_scenario or {}
    for scenario in scenarios:
        scenario_id = scenario.get("scenario_id", "")
        eval_case_ids = list(scenario.get("eval_case_ids") or [])
        reports = [
            reports_by_case_id[case_id]
            for case_id in eval_case_ids
            if case_id in reports_by_case_id
        ]
        passed = sum(1 for report in reports if report.get("passed"))
        total = len(reports)
        summaries.append(
            {
                "scenario_id": scenario_id,
                "domain": scenario.get("domain", ""),
                "risk_level": scenario.get("risk_level", ""),
                "eval_case_ids": eval_case_ids,
                "missing_case_ids": missing_by_scenario.get(scenario_id, []),
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "all_failed": total > 0 and passed == 0,
                "retrieval_failure_stage_summary": stage_summary(reports),
                "contribution_summary": build_contribution_summary(reports),
                "reports": reports,
            }
        )
    return summaries


def build_report(
    registry_path: Path,
    cases_path: Path,
    check_risk: bool = True,
    runner: Callable[[dict[str, Any], bool], dict[str, Any]] = run_case,
) -> dict[str, Any]:
    registry = load_json(registry_path)
    scenarios = load_scenarios(registry_path)
    cases_by_id = case_map(load_cases(cases_path))
    missing_by_scenario = missing_case_ids(scenarios, cases_by_id)
    unique_case_ids = scenario_eval_case_ids(scenarios)

    reports_by_case_id: dict[str, dict[str, Any]] = {}
    for case_id in unique_case_ids:
        if case_id in cases_by_id:
            reports_by_case_id[case_id] = runner(cases_by_id[case_id], check_risk)

    scenario_summaries = summarize_scenarios(scenarios, reports_by_case_id, missing_by_scenario)
    scenarios_without_eval = [
        scenario.get("scenario_id", "")
        for scenario in scenarios
        if not scenario.get("eval_case_ids")
    ]
    all_failed = [
        summary["scenario_id"]
        for summary in scenario_summaries
        if summary["all_failed"]
    ]

    return {
        "version": "0.4.6.4",
        "registry_version": registry.get("version", ""),
        "registry_path": str(registry_path),
        "cases_path": str(cases_path),
        "check_risk": check_risk,
        "total_scenarios": len(scenarios),
        "total_unique_eval_cases": len(unique_case_ids),
        "missing_case_ids": missing_by_scenario,
        "scenarios_without_eval_case_ids": scenarios_without_eval,
        "scenarios_all_failed": all_failed,
        "scenario_summaries": scenario_summaries,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Scenario Eval Summary",
        "",
        f"- Version: `{report.get('version')}`",
        f"- Registry version: `{report.get('registry_version')}`",
        f"- Total scenarios: `{report.get('total_scenarios')}`",
        f"- Total unique eval cases: `{report.get('total_unique_eval_cases')}`",
        f"- Missing case groups: `{len(report.get('missing_case_ids') or {})}`",
        f"- Scenarios without eval case ids: `{len(report.get('scenarios_without_eval_case_ids') or [])}`",
        f"- Scenarios all failed: `{len(report.get('scenarios_all_failed') or [])}`",
        "",
        "| scenario_id | domain | pass/total | retrieval stages | contribution labels |",
        "|---|---|---:|---|---|",
    ]
    for summary in report.get("scenario_summaries") or []:
        stages = ", ".join(
            f"{key}:{value}"
            for key, value in (summary.get("retrieval_failure_stage_summary") or {}).items()
        ) or "-"
        labels = ", ".join(
            f"{key}:{value}"
            for key, value in (summary.get("contribution_summary", {}).get("label_counts") or {}).items()
        ) or "-"
        lines.append(
            "| {scenario_id} | {domain} | {passed}/{total} | {stages} | {labels} |".format(
                scenario_id=summary.get("scenario_id", ""),
                domain=summary.get("domain", ""),
                passed=summary.get("passed", 0),
                total=summary.get("total", 0),
                stages=stages,
                labels=labels,
            )
        )

    if report.get("missing_case_ids"):
        lines.extend(["", "## Missing Case IDs", ""])
        for scenario_id, case_ids in report["missing_case_ids"].items():
            lines.append(f"- `{scenario_id}`: {', '.join(f'`{case_id}`' for case_id in case_ids)}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAG eval grouped by scenario registry scenarios.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--no-check-risk", action="store_true", help="Do not validate risk fields.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.registry, args.cases, check_risk=not args.no_check_risk)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scenario eval report saved: {args.output}")

    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(render_markdown(report), encoding="utf-8")
        print(f"Scenario eval summary saved: {args.summary}")

    for summary in report["scenario_summaries"]:
        print(
            "[{passed}/{total}] {scenario_id} stages={stages} labels={labels}".format(
                passed=summary["passed"],
                total=summary["total"],
                scenario_id=summary["scenario_id"],
                stages=summary["retrieval_failure_stage_summary"],
                labels=summary["contribution_summary"]["label_counts"],
            )
        )

    if report["missing_case_ids"]:
        print(f"Missing case ids: {report['missing_case_ids']}")
        return 1
    if report["scenarios_without_eval_case_ids"]:
        print(f"Scenarios without eval_case_ids: {report['scenarios_without_eval_case_ids']}")
        return 1
    if report["scenarios_all_failed"]:
        print(f"Scenarios all failed: {report['scenarios_all_failed']}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
