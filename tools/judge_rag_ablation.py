"""Judge the structural and primary-metric validity of an ablation report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_PROFILES = {"M1_dense", "M2_hybrid", "M3_concept", "M4_full"}
REQUIRED_SUMMARY_KEYS = {
    "case_count",
    "evidence_recall_at_k",
    "mrr_at_k",
    "ndcg_at_k",
    "multi_source_coverage",
    "retrieval_time_p50_ms",
    "retrieval_time_p95_ms",
}


def judge(report: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    profiles = report.get("profiles") or {}
    if report.get("status") != "completed":
        findings.append("消融运行未完成，不能把阻断状态作为实验结果")
    missing_profiles = sorted(REQUIRED_PROFILES - set(profiles))
    if missing_profiles:
        findings.append(f"缺少实验配置: {', '.join(missing_profiles)}")
    if not report.get("case_file_sha256"):
        findings.append("缺少冻结测试集 SHA-256")
    if not isinstance(report.get("case_count"), int) or report["case_count"] <= 0:
        findings.append("测试集数量无效")

    for name in sorted(REQUIRED_PROFILES & set(profiles)):
        profile = profiles[name]
        summary = profile.get("summary") or {}
        missing_keys = sorted(REQUIRED_SUMMARY_KEYS - set(summary))
        if missing_keys:
            findings.append(f"{name} 缺少指标: {', '.join(missing_keys)}")
        cases = profile.get("cases")
        if not isinstance(cases, list) or len(cases) != report.get("case_count"):
            findings.append(f"{name} 的 case 数量与冻结测试集不一致")
        if not profile.get("definition"):
            findings.append(f"{name} 缺少配置定义")

    m1 = profiles.get("M1_dense", {}).get("summary", {}).get("evidence_recall_at_k")
    m4 = profiles.get("M4_full", {}).get("summary", {}).get("evidence_recall_at_k")
    if isinstance(m1, (int, float)) and isinstance(m4, (int, float)) and m4 < m1:
        findings.append(f"M4_full Recall@K ({m4}) 低于 M1_dense ({m1})")

    return {
        "schema_version": "rag-ablation-judge-v1",
        "verdict": "accepted" if not findings else "needs_revision",
        "checks": {
            "required_profiles": not missing_profiles,
            "frozen_case_set": bool(report.get("case_file_sha256")) and report.get("case_count", 0) > 0,
            "required_metrics": not any("缺少指标" in finding for finding in findings),
            "m4_primary_recall_gate": not any("Recall@K" in finding for finding in findings),
        },
        "findings": findings,
        "case_file_sha256": report.get("case_file_sha256"),
        "case_count": report.get("case_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = judge(report)
    output = args.output or args.report.with_name("judge_report.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
