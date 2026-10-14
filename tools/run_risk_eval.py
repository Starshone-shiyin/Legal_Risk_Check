"""运行风险引擎回归评测。

默认复用 tests/rag_eval_cases.json 中带有 expected_risk_* 字段的风控场景题。
该脚本不做模型训练，只用于验证 /risk/analyze 底层 analyze_risk 的稳定性。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.risk.analyzer import analyze_risk
from tools.run_rag_eval import (
    CheckResult,
    check_expected_evidence,
    check_expected_risk_level,
    load_cases,
    normalize_text_items,
    text_contains_enough,
)


DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/risk_eval_report.json")


def select_risk_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick scenario cases that contain risk expectations."""
    selected = []
    for case in cases:
        if any(
            key in case
            for key in ("expected_risk_types", "expected_risk_level", "expected_actions")
        ):
            selected.append(case)
    return selected


def check_expected_risk_types(case: dict[str, Any], result: dict[str, Any]) -> CheckResult:
    expected = case.get("expected_risk_types", [])
    if not expected:
        return CheckResult("expected_risk_types", True, "未配置 expected_risk_types，跳过")
    actual_text = " ".join(
        normalize_text_items(result.get("risk_types"))
        + normalize_text_items([item.get("name", "") for item in result.get("risk_categories", [])])
        + [result.get("summary", "")]
    )
    passed, missing = text_contains_enough(actual_text, expected)
    message = "风险类型覆盖率达标" if passed else f"缺失风险类型: {missing}"
    return CheckResult("expected_risk_types", passed, message)


def check_expected_actions(case: dict[str, Any], result: dict[str, Any]) -> CheckResult:
    expected = case.get("expected_actions", [])
    if not expected:
        return CheckResult("expected_actions", True, "未配置 expected_actions，跳过")
    actual_text = " ".join(normalize_text_items(result.get("recommended_actions")) + [result.get("summary", "")])
    passed, missing = text_contains_enough(actual_text, expected)
    message = "整改动作覆盖率达标" if passed else f"缺失整改动作: {missing}"
    return CheckResult("expected_actions", passed, message)


def check_legal_basis(result: dict[str, Any]) -> CheckResult:
    legal_basis = result.get("legal_basis", [])
    passed = bool(legal_basis)
    message = f"legal_basis={len(legal_basis)}" if passed else "legal_basis 为空"
    return CheckResult("legal_basis_non_empty", passed, message)


def check_overall_confidence(result: dict[str, Any], min_confidence: float | None) -> CheckResult:
    confidence = result.get("confidence", {})
    overall = confidence.get("overall")
    if overall is None:
        return CheckResult("overall_confidence", False, "confidence.overall 缺失")
    if min_confidence is None:
        return CheckResult("overall_confidence", True, f"overall={overall}")
    passed = float(overall) >= min_confidence
    message = f"overall={overall}, threshold={min_confidence}"
    return CheckResult("overall_confidence", passed, message)


def check_high_risk_has_basis(case: dict[str, Any], result: dict[str, Any]) -> CheckResult:
    expected_level = case.get("expected_risk_level")
    actual_level = result.get("risk_level")
    if expected_level != "high" and actual_level != "high":
        return CheckResult("high_risk_has_basis", True, "非高风险场景，跳过")
    has_basis = bool(result.get("legal_basis"))
    has_cited_risk = any(item.get("citations") for item in result.get("risk_type_evidence", []))
    passed = has_basis and has_cited_risk
    message = "高风险场景已绑定依据" if passed else "高风险场景缺少 legal_basis 或 risk_type_evidence"
    return CheckResult("high_risk_has_basis", passed, message)


def run_case(case: dict[str, Any], min_confidence: float | None = None) -> dict[str, Any]:
    filters = case.get("filters", {})
    result = analyze_risk(
        case["question"],
        k=case.get("k", 5),
        debug=True,
        **filters,
    )
    checks = [
        check_expected_risk_level(case, result, enabled=True),
        check_expected_risk_types(case, result),
        check_expected_actions(case, result),
        check_legal_basis(result),
        check_expected_evidence(case, result.get("legal_basis", [])),
        check_overall_confidence(result, min_confidence),
        check_high_risk_has_basis(case, result),
    ]
    passed = all(check.passed for check in checks)
    return {
        "id": case.get("id", ""),
        "passed": passed,
        "scenario": case.get("question", ""),
        "checks": [check.__dict__ for check in checks],
        "risk_level": result.get("risk_level"),
        "risk_types": result.get("risk_types", []),
        "risk_categories": result.get("risk_categories", []),
        "recommended_actions": result.get("recommended_actions", []),
        "confidence": result.get("confidence", {}),
        "needs_human_review": result.get("needs_human_review"),
        "missing_evidence": result.get("missing_evidence", []),
        "legal_basis": result.get("legal_basis", []),
        "risk_type_evidence": result.get("risk_type_evidence", []),
        "recommended_action_evidence": result.get("recommended_action_evidence", []),
        "summary": result.get("summary", ""),
        "filters": result.get("filters", {}),
        "debug_info": result.get("debug_info", {}),
    }


def print_case_report(report: dict[str, Any], verbose: bool = False):
    status = "PASS" if report["passed"] else "FAIL"
    print(f"[{status}] {report['id']}")
    for check in report["checks"]:
        check_status = "OK" if check["passed"] else "X"
        print(f"  - {check_status} {check['name']}: {check['message']}")
    print(f"  risk_level: {report.get('risk_level')}")
    print(f"  legal_basis: {len(report.get('legal_basis', []))}")
    print(f"  confidence: {report.get('confidence')}")
    if verbose:
        print(f"  risk_types: {report.get('risk_types')}")
        print(f"  recommended_actions: {report.get('recommended_actions')}")
        print(f"  summary: {report.get('summary')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run risk engine regression evaluation cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="评测用例 JSON 路径")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="保存 JSON 报告路径")
    parser.add_argument("--verbose", action="store_true", help="输出完整风险结果摘要")
    parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")
    parser.add_argument("--min-overall-confidence", type=float, default=None, help="可选：要求 confidence.overall 达到指定阈值")
    parser.add_argument("--domain", type=str, help="仅运行指定领域（按 category 筛选）")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    all_cases = load_cases(args.cases)
    if args.domain:
        all_cases = [c for c in all_cases if c.get("filters", {}).get("category") == args.domain]
    cases = select_risk_cases(all_cases)
    reports = []

    for case in cases:
        report = run_case(case, min_confidence=args.min_overall_confidence)
        reports.append(report)
        print_case_report(report, verbose=args.verbose)
        if args.fail_fast and not report["passed"]:
            break

    passed_count = sum(1 for report in reports if report["passed"])
    summary = {
        "source_cases": str(args.cases),
        "total": len(reports),
        "passed": passed_count,
        "failed": len(reports) - passed_count,
        "reports": reports,
    }
    print(f"\nSummary: {passed_count}/{len(reports)} passed")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"报告已保存: {args.output}")

    return 0 if passed_count == len(reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
