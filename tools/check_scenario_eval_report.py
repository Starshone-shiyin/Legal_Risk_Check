"""Validate scenario eval report as a lightweight release gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REPORT_PATH = Path("tests/scenario_eval_report.json")


def load_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scenario eval report must be a JSON object")
    return payload


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return bool(value)


def _int_field(payload: dict[str, Any], field: str, label: str, errors: list[str]) -> int | None:
    value = payload.get(field)
    if not isinstance(value, int):
        errors.append(f"{label}.{field} must be an integer")
        return None
    return value


def validate_scenario_eval_report(
    report: dict[str, Any],
    min_scenarios: int = 10,
    min_cases: int = 15,
    allow_partial_pass: bool = True,
) -> list[str]:
    errors: list[str] = []

    missing_case_ids = report.get("missing_case_ids")
    if not isinstance(missing_case_ids, dict):
        errors.append("missing_case_ids must be an object")
    elif missing_case_ids:
        errors.append(f"missing_case_groups must be 0, got {len(missing_case_ids)}")

    scenarios_without_eval_case_ids = report.get("scenarios_without_eval_case_ids")
    if not isinstance(scenarios_without_eval_case_ids, list):
        errors.append("scenarios_without_eval_case_ids must be a list")
    elif scenarios_without_eval_case_ids:
        errors.append("scenarios_without_eval_case_ids must be empty")

    scenarios_all_failed = report.get("scenarios_all_failed")
    if not isinstance(scenarios_all_failed, list):
        errors.append("scenarios_all_failed must be a list")
    elif scenarios_all_failed:
        errors.append("scenarios_all_failed must be empty")

    total_scenarios = _int_field(report, "total_scenarios", "report", errors)
    if total_scenarios is not None and total_scenarios < min_scenarios:
        errors.append(f"total_scenarios must be >= {min_scenarios}, got {total_scenarios}")

    total_unique_eval_cases = _int_field(report, "total_unique_eval_cases", "report", errors)
    if total_unique_eval_cases is not None and total_unique_eval_cases < min_cases:
        errors.append(f"total_unique_eval_cases must be >= {min_cases}, got {total_unique_eval_cases}")

    scenario_summaries = report.get("scenario_summaries")
    if not isinstance(scenario_summaries, list):
        errors.append("scenario_summaries must be a list")
        return errors

    if total_scenarios is not None and len(scenario_summaries) != total_scenarios:
        errors.append(
            f"scenario_summaries length must equal total_scenarios, got {len(scenario_summaries)} vs {total_scenarios}"
        )

    for index, summary in enumerate(scenario_summaries):
        if not isinstance(summary, dict):
            errors.append(f"scenario_summaries[{index}] must be an object")
            continue
        scenario_id = summary.get("scenario_id") or f"scenario_summaries[{index}]"

        passed = _int_field(summary, "passed", scenario_id, errors)
        total = _int_field(summary, "total", scenario_id, errors)
        if not isinstance(summary.get("retrieval_failure_stage_summary"), dict):
            errors.append(f"{scenario_id}.retrieval_failure_stage_summary must be an object")

        if total is not None and total <= 0:
            errors.append(f"{scenario_id}.total must be > 0")
        if passed is not None and passed <= 0:
            errors.append(f"{scenario_id}.passed must be > 0")
        if passed is not None and total is not None:
            if passed > total:
                errors.append(f"{scenario_id}.passed must be <= total")
            if not allow_partial_pass and passed != total:
                errors.append(f"{scenario_id}.passed must equal total when partial pass is disabled")

        if _is_non_empty(summary.get("missing_case_ids")):
            errors.append(f"{scenario_id}.missing_case_ids must be empty")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate tests/scenario_eval_report.json as a release gate.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--min-scenarios", type=int, default=10)
    parser.add_argument("--min-cases", type=int, default=15)
    parser.add_argument("--allow-partial-pass", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = load_report(args.report)
    except Exception as exc:
        print(f"Scenario eval gate failed: could not load report: {exc}")
        return 1

    errors = validate_scenario_eval_report(
        report,
        min_scenarios=args.min_scenarios,
        min_cases=args.min_cases,
        allow_partial_pass=args.allow_partial_pass,
    )
    if errors:
        print("Scenario eval gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Scenario eval gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
