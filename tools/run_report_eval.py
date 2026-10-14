"""Run regression checks for risk report generation.

This script reuses risk cases from tests/rag_eval_cases.json. It does not train
models; it verifies that generate_risk_report keeps producing a complete,
business-facing report with findings, actions, legal basis and exportable
Markdown.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.risk.report import export_risk_report, generate_risk_report
from tools.run_risk_eval import (
    check_expected_actions,
    check_expected_risk_types,
    select_risk_cases,
)
from tools.run_rag_eval import (
    CheckResult,
    check_expected_evidence,
    check_expected_risk_level,
    load_cases,
)


DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/report_eval_report.json")

REQUIRED_REPORT_FIELDS = [
    "title",
    "scenario",
    "executive_summary",
    "risk_level",
    "risk_findings",
    "action_plan",
    "legal_basis",
    "confidence",
    "human_review_required",
    "evidence_chain",
]

REQUIRED_MARKDOWN_SECTIONS = [
    "# 企业合规风险分析报告",
    "## 一、场景描述",
    "## 二、执行摘要",
    "## 三、风险等级",
    "## 四、风险发现",
    "## 五、整改行动计划",
    "## 六、法律与标准依据",
    "## 七、置信度与复核",
]


def check_report_fields(report: dict[str, Any]) -> CheckResult:
    missing = []
    empty = []
    for field in REQUIRED_REPORT_FIELDS:
        if field not in report:
            missing.append(field)
        elif report[field] in (None, "", [], {}):
            empty.append(field)

    passed = not missing and not empty
    message = "报告核心字段完整" if passed else f"missing={missing}, empty={empty}"
    return CheckResult("report_fields", passed, message)


def check_report_findings(report: dict[str, Any]) -> CheckResult:
    findings = report.get("risk_findings", [])
    if not findings:
        return CheckResult("risk_findings", False, "risk_findings 为空")
    invalid = [
        index
        for index, finding in enumerate(findings, start=1)
        if not finding.get("risk_type") or not finding.get("risk_level") or not finding.get("analysis")
    ]
    passed = not invalid
    message = "风险发现结构完整" if passed else f"风险发现字段不完整: {invalid}"
    return CheckResult("risk_findings", passed, message)


def check_action_plan(report: dict[str, Any]) -> CheckResult:
    actions = report.get("action_plan", [])
    if not actions:
        return CheckResult("action_plan", False, "action_plan 为空")
    invalid = [
        index
        for index, action in enumerate(actions, start=1)
        if not action.get("priority") or not action.get("action") or not action.get("owner_hint")
    ]
    passed = not invalid
    message = "行动计划结构完整" if passed else f"行动计划字段不完整: {invalid}"
    return CheckResult("action_plan", passed, message)


def check_confidence(report: dict[str, Any], min_overall_confidence: float | None) -> CheckResult:
    confidence = report.get("confidence", {})
    overall = confidence.get("overall")
    if overall is None:
        return CheckResult("report_confidence", False, "confidence.overall 缺失")
    if min_overall_confidence is None:
        return CheckResult("report_confidence", True, f"overall={overall}")
    passed = float(overall) >= min_overall_confidence
    return CheckResult("report_confidence", passed, f"overall={overall}, threshold={min_overall_confidence}")


def check_markdown_export(report: dict[str, Any]) -> CheckResult:
    markdown = export_risk_report(
        report,
        export_format="markdown",
        include_evidence_chain=True,
        include_source_analysis=False,
    )
    missing_sections = [section for section in REQUIRED_MARKDOWN_SECTIONS if section not in markdown]
    passed = not missing_sections
    message = "Markdown 导出章节完整" if passed else f"缺少 Markdown 章节: {missing_sections}"
    return CheckResult("markdown_export", passed, message)


def check_json_export(report: dict[str, Any]) -> CheckResult:
    payload = export_risk_report(
        report,
        export_format="json",
        include_evidence_chain=False,
        include_source_analysis=False,
    )
    passed = "evidence_chain" not in payload and "source_analysis" not in payload
    message = "JSON 瘦身导出正常" if passed else "JSON 瘦身导出仍包含 evidence_chain 或 source_analysis"
    return CheckResult("json_export", passed, message)


def run_case(case: dict[str, Any], min_overall_confidence: float | None = None) -> dict[str, Any]:
    filters = case.get("filters", {})
    report = generate_risk_report(
        case["question"],
        k=case.get("k", 5),
        debug=True,
        **filters,
    )
    source_analysis = report.get("source_analysis", {})
    checks = [
        check_report_fields(report),
        check_report_findings(report),
        check_action_plan(report),
        check_expected_risk_level(case, report, enabled=True),
        check_expected_risk_types(case, source_analysis),
        check_expected_actions(case, source_analysis),
        check_expected_evidence(case, report.get("legal_basis", [])),
        check_confidence(report, min_overall_confidence),
        check_markdown_export(report),
        check_json_export(report),
    ]
    passed = all(check.passed for check in checks)
    return {
        "id": case.get("id", ""),
        "passed": passed,
        "scenario": case.get("question", ""),
        "checks": [check.__dict__ for check in checks],
        "risk_level": report.get("risk_level"),
        "risk_findings_count": len(report.get("risk_findings", [])),
        "action_plan_count": len(report.get("action_plan", [])),
        "legal_basis_count": len(report.get("legal_basis", [])),
        "confidence": report.get("confidence", {}),
        "human_review_required": report.get("human_review_required"),
        "review_reasons": report.get("review_reasons", []),
        "executive_summary": report.get("executive_summary", ""),
    }


def print_case_report(report: dict[str, Any], verbose: bool = False):
    status = "PASS" if report["passed"] else "FAIL"
    print(f"[{status}] {report['id']}")
    for check in report["checks"]:
        check_status = "OK" if check["passed"] else "X"
        print(f"  - {check_status} {check['name']}: {check['message']}")
    print(f"  risk_level: {report.get('risk_level')}")
    print(f"  findings/actions/basis: {report.get('risk_findings_count')}/{report.get('action_plan_count')}/{report.get('legal_basis_count')}")
    print(f"  confidence: {report.get('confidence')}")
    if verbose:
        print(f"  summary: {report.get('executive_summary')}")
        if report.get("review_reasons"):
            print(f"  review_reasons: {report.get('review_reasons')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run risk report regression evaluation cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="评测用例 JSON 路径")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="保存 JSON 报告路径")
    parser.add_argument("--verbose", action="store_true", help="输出报告摘要")
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
        report = run_case(case, min_overall_confidence=args.min_overall_confidence)
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
