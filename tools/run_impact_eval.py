"""Run scoped evaluation for changed or selected knowledge areas.

This script is the lightweight companion to full RAG/Risk/Report regression.
Use it after adding or changing one law/standard so you only run related smoke
cases instead of the entire evaluation suite.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.run_rag_eval import load_cases, run_case as run_rag_case
from tools.run_report_eval import run_case as run_report_case
from tools.run_risk_eval import run_case as run_risk_case


DEFAULT_MANIFEST_PATH = Path("knowledge_manifest.json")
DEFAULT_CASES_PATH = Path("tests/smoke_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/impact_eval_report.json")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def source_matches(expected: str, actual: str) -> bool:
    expected = normalize_text(expected)
    actual = normalize_text(actual)
    if not expected or not actual:
        return False
    return expected == actual or expected in actual or actual in expected


def document_matches_filters(
    document: dict[str, Any],
    sources: set[str],
    categories: set[str],
    domains: set[str],
    document_types: set[str],
) -> bool:
    if sources and not any(source_matches(source, document.get("source", "")) for source in sources):
        return False
    if categories and document.get("category") not in categories:
        return False
    if domains and document.get("domain") not in domains:
        return False
    if document_types and document.get("document_type") not in document_types:
        return False
    return True


def get_changed_files() -> set[str]:
    files: set[str] = set()
    commands = [
        ["git", "diff", "--name-only", "HEAD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        if result.returncode == 0:
            files.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return files


def select_documents(
    manifest: dict[str, Any],
    sources: set[str],
    categories: set[str],
    domains: set[str],
    document_types: set[str],
    changed_only: bool = False,
) -> list[dict[str, Any]]:
    documents = manifest.get("documents", [])
    selected = [
        document
        for document in documents
        if document_matches_filters(document, sources, categories, domains, document_types)
    ]
    if changed_only:
        changed_files = get_changed_files()
        selected = [
            document
            for document in selected
            if normalize_text(document.get("file_path")).replace("\\", "/") in changed_files
            or normalize_text(document.get("source")) in changed_files
        ]
    return selected


def case_matches_documents(
    case: dict[str, Any],
    documents: list[dict[str, Any]],
    allow_domain_match: bool = True,
) -> bool:
    if not documents:
        return True

    document_sources = {document.get("source", "") for document in documents}
    document_domains = {document.get("domain", "") for document in documents}
    for source in case.get("impact_sources", []):
        if any(source_matches(source, document_source) for document_source in document_sources):
            return True

    if allow_domain_match:
        for domain in case.get("impact_domains", []):
            if domain in document_domains:
                return True

    for expected in case.get("expected_evidence", []):
        expected_source = expected.get("source", "")
        if any(source_matches(expected_source, document_source) for document_source in document_sources):
            return True

    return False


def select_cases_for_impact(
    cases: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    allow_domain_match: bool = True,
) -> list[dict[str, Any]]:
    return [
        case
        for case in cases
        if case_matches_documents(case, documents, allow_domain_match=allow_domain_match)
    ]


def has_risk_expectation(case: dict[str, Any]) -> bool:
    return any(key in case for key in ("expected_risk_types", "expected_risk_level", "expected_actions"))


def run_layers_for_case(case: dict[str, Any], layers: list[str]) -> dict[str, Any]:
    reports = {}
    if "rag" in layers:
        reports["rag"] = run_rag_case(case, check_risk=has_risk_expectation(case))
    if "risk" in layers and has_risk_expectation(case):
        reports["risk"] = run_risk_case(case)
    if "report" in layers and has_risk_expectation(case):
        reports["report"] = run_report_case(case)

    passed = all(report.get("passed", False) for report in reports.values())
    return {
        "id": case.get("id", ""),
        "passed": passed,
        "question": case.get("question", ""),
        "layers": reports,
    }


def print_case_report(report: dict[str, Any]):
    status = "PASS" if report["passed"] else "FAIL"
    layer_status = ", ".join(
        f"{name}={'PASS' if layer.get('passed') else 'FAIL'}"
        for name, layer in report.get("layers", {}).items()
    )
    print(f"[{status}] {report['id']} ({layer_status})")


def parse_csv(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def parse_layers(value: str) -> list[str]:
    if value == "all":
        return ["rag", "risk", "report"]
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scoped impact evaluation cases.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH, help="知识库清单路径")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="评测用例 JSON 路径")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="保存 JSON 报告路径")
    parser.add_argument("--source", action="append", help="按 source 筛选，可重复或逗号分隔")
    parser.add_argument("--category", action="append", help="按 category 筛选，可重复或逗号分隔")
    parser.add_argument("--domain", action="append", help="按 domain 筛选，可重复或逗号分隔")
    parser.add_argument("--document-type", action="append", help="按 document_type 筛选，可重复或逗号分隔")
    parser.add_argument("--changed-only", action="store_true", help="只选择 Git 变更涉及的 manifest 文档")
    parser.add_argument("--layers", default="rag", help="评测层：rag、risk、report、rag,risk 或 all；默认 rag")
    parser.add_argument("--list-only", action="store_true", help="只列出将要运行的文档和用例，不实际调用模型")
    parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    cases = load_cases(args.cases)
    layers = parse_layers(args.layers)

    sources = parse_csv(args.source)
    categories = parse_csv(args.category)
    domains = parse_csv(args.domain)
    document_types = parse_csv(args.document_type)
    source_only = bool(sources) and not categories and not domains and not document_types

    documents = select_documents(
        manifest,
        sources=sources,
        categories=categories,
        domains=domains,
        document_types=document_types,
        changed_only=args.changed_only,
    )
    selected_cases = select_cases_for_impact(cases, documents, allow_domain_match=not source_only)

    print(f"Selected documents: {len(documents)}")
    for document in documents:
        print(f"  - {document.get('source')} ({document.get('domain')}, {document.get('category')})")
    print(f"Selected cases: {len(selected_cases)}")
    for case in selected_cases:
        print(f"  - {case.get('id')}")

    if args.list_only:
        return 0

    reports = []
    for case in selected_cases:
        report = run_layers_for_case(case, layers)
        reports.append(report)
        print_case_report(report)
        if args.fail_fast and not report["passed"]:
            break

    passed_count = sum(1 for report in reports if report["passed"])
    summary = {
        "manifest": str(args.manifest),
        "cases": str(args.cases),
        "layers": layers,
        "selected_documents": [document.get("source") for document in documents],
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
