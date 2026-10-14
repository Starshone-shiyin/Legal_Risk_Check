"""Judge a single-variable retrieval-ablation report without rerunning RAG."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CONTROLLED_PROFILES = (
    "C0_dense",
    "C1_hybrid",
    "C2_query_expansion",
    "C3_concept_anchors",
    "C4_scene_anchors",
    "C5_complex_planner",
    "C6_cross_encoder",
)
SWITCHES = (
    "enable_sparse_recall",
    "enable_concept_expansion",
    "enable_concept_anchors",
    "enable_deterministic_anchors",
    "enable_complex_planner",
    "enable_reranker",
)
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
        findings.append("实验运行未完成")
    if not report.get("case_file_sha256"):
        findings.append("缺少冻结测试集 SHA-256")
    if not report.get("collection_name"):
        findings.append("缺少知识库集合标识")

    missing = [name for name in CONTROLLED_PROFILES if name not in profiles]
    if missing:
        findings.append(f"缺少控制变量配置: {', '.join(missing)}")

    transition_checks: list[dict[str, Any]] = []
    for previous_name, current_name in zip(CONTROLLED_PROFILES, CONTROLLED_PROFILES[1:]):
        previous = (profiles.get(previous_name) or {}).get("definition") or {}
        current = (profiles.get(current_name) or {}).get("definition") or {}
        changed = [key for key in SWITCHES if previous.get(key) != current.get(key)]
        passed = len(changed) == 1
        transition_checks.append({
            "transition": f"{previous_name}->{current_name}",
            "changed_switches": changed,
            "passed": passed,
        })
        if not passed:
            findings.append(f"{previous_name}->{current_name} 不是单变量变化: {changed}")

    for name in CONTROLLED_PROFILES:
        profile = profiles.get(name) or {}
        summary = profile.get("summary") or {}
        missing_metrics = sorted(REQUIRED_SUMMARY_KEYS - set(summary))
        if missing_metrics:
            findings.append(f"{name} 缺少指标: {', '.join(missing_metrics)}")
        if len(profile.get("cases") or []) != report.get("case_count"):
            findings.append(f"{name} 的案例数与冻结集不一致")

    return {
        "schema_version": "controlled-rag-ablation-judge-v1",
        "verdict": "accepted" if not findings else "needs_revision",
        "checks": {
            "frozen_case_set": bool(report.get("case_file_sha256")) and report.get("case_count", 0) > 0,
            "collection_identified": bool(report.get("collection_name")),
            "required_profiles": not missing,
            "single_variable_transitions": all(item["passed"] for item in transition_checks),
            "required_metrics": not any("缺少指标" in item for item in findings),
        },
        "transitions": transition_checks,
        "findings": findings,
        "case_file_sha256": report.get("case_file_sha256"),
        "collection_name": report.get("collection_name"),
        "case_count": report.get("case_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = judge(report)
    output = args.output or args.report.with_name("controlled_ablation_judge_report.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
