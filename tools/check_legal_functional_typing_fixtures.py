"""Validate legal functional typing against golden fixtures.

The fixture gate protects classification quality for the offline functional
typing layer. It does not call RAG, LLM, Qdrant, rerank, or eval cases.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.legal_functional_typing import (
    classify_legal_function,
    configured_functional_type_ids,
    load_functional_type_config,
)


DEFAULT_FIXTURES_PATH = Path("tests/fixtures/legal_functional_typing_golden.json")
DEFAULT_CONFIG_PATH = Path("config/legal_functional_types.json")
DEFAULT_REPORT_PATH = Path("tests/legal_functional_typing_fixture_report.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture_structure(
    payload: dict[str, Any],
    allowed_types: set[str],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload.get("version"), str) or not payload.get("version", "").strip():
        errors.append("version must be a non-empty string")
    if not isinstance(payload.get("purpose"), str) or not payload.get("purpose", "").strip():
        errors.append("purpose must be a non-empty string")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a non-empty list"]

    seen_ids: set[str] = set()
    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{label}.id must be a non-empty string")
        elif case_id in seen_ids:
            errors.append(f"{label}.id duplicates fixture id: {case_id}")
        else:
            seen_ids.add(case_id)
        expected = case.get("expected_functional_type")
        if expected not in allowed_types:
            errors.append(f"{label}.expected_functional_type is not declared: {expected}")
        if not isinstance(case.get("text"), str) or not case.get("text", "").strip():
            errors.append(f"{label}.text must be a non-empty string")
        if not isinstance(case.get("metadata"), dict):
            errors.append(f"{label}.metadata must be an object")
    return errors


def evaluate_fixtures(
    fixtures: dict[str, Any],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = []
    expected_counts: Counter[str] = Counter()
    actual_counts: Counter[str] = Counter()
    failures_by_expected: dict[str, list[str]] = defaultdict(list)

    for case in fixtures.get("cases") or []:
        expected = case.get("expected_functional_type")
        result = classify_legal_function(
            text=case.get("text", ""),
            metadata=case.get("metadata") or {},
            config=config,
        )
        passed = result.functional_type == expected
        expected_counts[str(expected)] += 1
        actual_counts[result.functional_type] += 1
        if not passed:
            failures_by_expected[str(expected)].append(case.get("id", "unknown"))
        results.append({
            "id": case.get("id"),
            "passed": passed,
            "expected_functional_type": expected,
            "actual_functional_type": result.functional_type,
            "confidence": result.confidence,
            "matched_rule": result.matched_rule,
            "matched_terms": list(result.matched_terms),
        })

    failed = [result for result in results if not result["passed"]]
    summary = {
        "total_cases": len(results),
        "passed_cases": len(results) - len(failed),
        "failed_cases": len(failed),
        "expected_type_counts": dict(sorted(expected_counts.items())),
        "actual_type_counts": dict(sorted(actual_counts.items())),
        "failures_by_expected_type": {
            key: value
            for key, value in sorted(failures_by_expected.items())
        },
    }
    return results, summary


def build_report(
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_functional_type_config(str(config_path))
    fixtures = load_json(fixtures_path)
    structure_errors = validate_fixture_structure(fixtures, configured_functional_type_ids(config))
    results, summary = evaluate_fixtures(fixtures, config) if not structure_errors else ([], {})
    return {
        "version": config.get("version") or fixtures.get("version") or "0.4.7.2.2",
        "scope": "legal functional typing golden fixture gate",
        "inputs": {
            "fixtures": str(fixtures_path),
            "config": str(config_path),
        },
        "passed": not structure_errors and summary.get("failed_cases", 0) == 0,
        "structure_errors": structure_errors,
        "summary": summary,
        "cases": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check legal functional typing golden fixtures.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.fixtures, args.config)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report.get("summary") or {}
    status = "passed" if report["passed"] else "failed"
    print(
        "Legal functional typing fixture gate "
        f"{status}: {summary.get('passed_cases', 0)}/{summary.get('total_cases', 0)} passed"
    )
    if report["structure_errors"]:
        for error in report["structure_errors"]:
            print(f"ERROR: {error}")
    for result in report["cases"]:
        if not result["passed"]:
            print(
                "FAIL: "
                f"{result['id']} expected={result['expected_functional_type']} "
                f"actual={result['actual_functional_type']} "
                f"matched={result['matched_terms']}"
            )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
