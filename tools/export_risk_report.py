"""Export a single risk report to Markdown or JSON.

Examples:
  python tools/export_risk_report.py --scenario "某APP未告知收集精准定位用于广告推荐" --format markdown
  python tools/export_risk_report.py --case-id risk_app_location_ads_002 --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.risk.report import generate_risk_report_export
from tools.run_rag_eval import load_cases


DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_DIR = Path("reports")


def find_case(case_id: str, cases_path: Path) -> dict[str, Any]:
    for case in load_cases(cases_path):
        if case.get("id") == case_id:
            return case
    raise ValueError(f"未找到 case_id: {case_id}")


def slugify(value: str, fallback: str = "risk_report") -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", value.strip(), flags=re.UNICODE)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:80] or fallback


def build_output_path(args: argparse.Namespace, scenario: str) -> Path:
    output_format = "md" if args.format == "markdown" else "json"
    if args.output:
        return args.output

    stem = args.case_id or slugify(scenario)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return args.output_dir / f"{stem}_{timestamp}.{output_format}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export one risk report to Markdown or JSON.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--scenario", type=str, help="直接输入业务场景")
    source.add_argument("--case-id", type=str, help="从测试题库按 id 读取业务场景")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="题库 JSON 路径")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="导出格式")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="默认输出目录")
    parser.add_argument("--output", type=Path, default=None, help="显式输出文件路径")
    parser.add_argument("--k", type=int, default=None, help="检索证据数量；未指定时使用 case 中的 k 或默认 5")
    parser.add_argument("--category", type=str, default=None, help="可选：覆盖 category 过滤条件")
    parser.add_argument("--include-evidence-chain", action=argparse.BooleanOptionalAction, default=True, help="是否包含 evidence_chain")
    parser.add_argument("--include-source-analysis", action=argparse.BooleanOptionalAction, default=False, help="是否包含完整 source_analysis")
    parser.add_argument("--debug", action="store_true", help="是否开启底层 RAG debug")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case = find_case(args.case_id, args.cases) if args.case_id else {}
    scenario = args.scenario or case["question"]
    filters = dict(case.get("filters", {}))
    if args.category is not None:
        filters["category"] = args.category

    result = generate_risk_report_export(
        scenario,
        export_format=args.format,
        include_evidence_chain=args.include_evidence_chain,
        include_source_analysis=args.include_source_analysis,
        k=args.k or case.get("k", 5),
        debug=args.debug,
        **filters,
    )

    output_path = build_output_path(args, scenario)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output_path.write_text(str(result), encoding="utf-8")

    print(f"报告已导出: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
