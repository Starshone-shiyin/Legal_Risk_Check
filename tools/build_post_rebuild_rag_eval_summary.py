"""Summarize post-rebuild full RAG eval regressions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.14.31"
DEFAULT_POST_REBUILD_RAG_PATH = Path("tests/post_rebuild_rag_eval_report.json")
DEFAULT_BASELINE_RAG_PATH = Path("tests/rag_eval_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_rag_eval_summary_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_rag_eval_summary_v0.4.14.31.md")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reports_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in report.get("reports") or []
        if isinstance(item, dict) and item.get("id")
    }


def failed_checks(case_report: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    for check in case_report.get("checks") or []:
        if not check.get("passed"):
            failures.append({
                "name": check.get("name"),
                "message": check.get("message"),
            })
    return failures


def layer_status(case_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers = (case_report.get("retrieval_diagnostics") or {}).get("layers") or {}
    status: dict[str, dict[str, Any]] = {}
    for name, layer in layers.items():
        if not isinstance(layer, dict):
            continue
        status[name] = {
            "satisfied": bool(layer.get("satisfied")),
            "matched_count": layer.get("matched_count"),
            "expected_count": layer.get("expected_count"),
            "required_count": layer.get("required_count"),
        }
    return status


def classify_failure(case_report: dict[str, Any], failures: list[dict[str, Any]]) -> str:
    names = {failure.get("name") for failure in failures}
    layers = layer_status(case_report)
    final_satisfied = layers.get("final", {}).get("satisfied")
    rerank_input_satisfied = layers.get("rerank_input", {}).get("satisfied")
    sparse_satisfied = layers.get("sparse", {}).get("satisfied")
    dense_satisfied = layers.get("dense", {}).get("satisfied")

    if "expected_evidence" in names:
        if rerank_input_satisfied and not final_satisfied:
            return "final_evidence_selection_drop"
        if sparse_satisfied and not dense_satisfied:
            return "dense_gap_with_sparse_recovery"
        return "expected_evidence_gap"
    if "expected_answer_keywords" in names:
        if final_satisfied:
            return "answer_keyword_coverage_gap"
        return "answer_quality_gap_with_evidence_gap"
    if "expected_risk_types" in names or "expected_actions" in names or "expected_risk_level" in names:
        return "risk_payload_quality_gap"
    return "unclassified_eval_failure"


def summarize_contribution_labels(report: dict[str, Any]) -> dict[str, int]:
    summary_counts = ((report.get("contribution_summary") or {}).get("label_counts") or {})
    if summary_counts:
        return {str(key): int(value) for key, value in summary_counts.items()}

    counts: Counter[str] = Counter()
    for item in report.get("reports") or []:
        counts.update(item.get("contribution_labels") or [])
    return dict(counts)


def build_summary_report(
    post_rebuild_rag_path: Path = DEFAULT_POST_REBUILD_RAG_PATH,
    baseline_rag_path: Path = DEFAULT_BASELINE_RAG_PATH,
) -> dict[str, Any]:
    post_report = load_json(post_rebuild_rag_path)
    baseline_report = load_json(baseline_rag_path)

    post_cases = reports_by_id(post_report)
    baseline_cases = reports_by_id(baseline_report)
    missing_from_post = sorted(set(baseline_cases) - set(post_cases))
    new_cases = sorted(set(post_cases) - set(baseline_cases))

    failed_case_rows = []
    issue_counts: Counter[str] = Counter()
    check_counts: Counter[str] = Counter()
    regression_count = 0

    for case_id, case_report in sorted(post_cases.items()):
        if case_report.get("passed"):
            continue
        failures = failed_checks(case_report)
        classification = classify_failure(case_report, failures)
        baseline_case = baseline_cases.get(case_id)
        baseline_passed = bool(baseline_case.get("passed")) if baseline_case else None
        is_regression = baseline_passed is True
        if is_regression:
            regression_count += 1
        issue_counts[classification] += 1
        check_counts.update(failure.get("name") or "unknown" for failure in failures)
        failed_case_rows.append({
            "case_id": case_id,
            "category": case_report.get("category", ""),
            "baseline_passed": baseline_passed,
            "is_regression": is_regression,
            "retrieval_failure_stage": case_report.get("retrieval_failure_stage"),
            "failed_checks": failures,
            "classification": classification,
            "layer_status": layer_status(case_report),
            "evidence": case_report.get("evidence") or [],
            "question": case_report.get("question", ""),
            "answer_excerpt": (case_report.get("answer") or "")[:500],
            "recommended_triage": triage_recommendation(classification),
        })

    blockers = []
    if post_report.get("passed") != post_report.get("total"):
        blockers.append("post_rebuild_full_rag_not_full_pass")
    if regression_count:
        blockers.append("baseline_full_rag_regressions")
    if missing_from_post:
        blockers.append("post_rebuild_full_rag_missing_baseline_cases")

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_rag_eval_summary_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "post_rebuild_rag_report": str(post_rebuild_rag_path),
            "baseline_rag_report": str(baseline_rag_path),
        },
        "rag_eval_summary": {
            "baseline_total": baseline_report.get("total"),
            "baseline_passed": baseline_report.get("passed"),
            "baseline_failed": baseline_report.get("failed"),
            "post_rebuild_total": post_report.get("total"),
            "post_rebuild_passed": post_report.get("passed"),
            "post_rebuild_failed": post_report.get("failed"),
            "regression_count": regression_count,
            "failed_case_count": len(failed_case_rows),
            "missing_from_post_rebuild": missing_from_post,
            "new_post_rebuild_cases": new_cases,
            "retrieval_failure_stage_summary": post_report.get("retrieval_failure_stage_summary", {}),
            "failed_check_summary": dict(check_counts),
            "issue_type_summary": dict(issue_counts),
            "contribution_label_counts": summarize_contribution_labels(post_report),
        },
        "failed_cases": failed_case_rows,
        "summary": {
            "status": "passed" if not blockers else "needs_triage",
            "blockers": blockers,
            "full_eval": "run_from_saved_post_rebuild_report",
            "runtime_changes": "not_performed",
            "qdrant_access": "not_called_by_summary",
            "llm_access": "not_called_by_summary",
            "recommended_next_step": (
                "triage_post_rebuild_full_rag_regressions"
                if blockers
                else "post_rebuild_full_rag_baseline_accepted"
            ),
        },
    }


def triage_recommendation(classification: str) -> str:
    recommendations = {
        "final_evidence_selection_drop": "inspect_final_evidence_selection_without_changing_eval_cases",
        "dense_gap_with_sparse_recovery": "inspect_retrieval_input_and_final_selection_before_anchor_changes",
        "expected_evidence_gap": "inspect_retrieval_layers_and_ingestion_metadata",
        "answer_keyword_coverage_gap": "inspect_answer_grounding_and_eval_keyword_contract",
        "answer_quality_gap_with_evidence_gap": "inspect_evidence_then_answer_generation",
        "risk_payload_quality_gap": "inspect_risk_payload_grounding",
    }
    return recommendations.get(classification, "manual_triage_required")


def render_markdown(report: dict[str, Any]) -> str:
    rag = report["rag_eval_summary"]
    lines = [
        "# v0.4.14.31 Post-Rebuild Full RAG Eval Summary",
        "",
        "## 结论",
        "",
        f"- 状态：`{report['summary']['status']}`",
        f"- baseline full RAG eval：`{rag['baseline_passed']}/{rag['baseline_total']}`",
        f"- post-rebuild full RAG eval：`{rag['post_rebuild_passed']}/{rag['post_rebuild_total']}`",
        f"- 回归 case：`{rag['regression_count']}`",
        f"- failed check summary：`{rag['failed_check_summary']}`",
        f"- issue type summary：`{rag['issue_type_summary']}`",
        "",
        "## 失败样例",
        "",
    ]
    if not report["failed_cases"]:
        lines.append("- 无。")
    for item in report["failed_cases"]:
        failed_names = [check.get("name") for check in item["failed_checks"]]
        lines.extend([
            f"- `{item['case_id']}`",
            f"  - 是否 baseline 回归：`{item['is_regression']}`",
            f"  - retrieval stage：`{item['retrieval_failure_stage']}`",
            f"  - failed checks：`{failed_names}`",
            f"  - 分类：`{item['classification']}`",
            f"  - 建议：`{item['recommended_triage']}`",
        ])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 本摘要只读取已保存的 full RAG eval 报告和 baseline 报告。",
        "- 本摘要不调用 RAG、Qdrant 或 LLM，不修改 retrieval、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。",
        "- 结论不是 runtime 修复；下一步应围绕两个真实回归做最小主链路排查。",
        "",
        "## 下一步",
        "",
        f"- `{report['summary']['recommended_next_step']}`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize post-rebuild full RAG eval regressions.")
    parser.add_argument("--post-rebuild-rag", type=Path, default=DEFAULT_POST_REBUILD_RAG_PATH)
    parser.add_argument("--baseline-rag", type=Path, default=DEFAULT_BASELINE_RAG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()

    report = build_summary_report(
        post_rebuild_rag_path=args.post_rebuild_rag,
        baseline_rag_path=args.baseline_rag,
    )
    write_json(args.output, report)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(render_markdown(report), encoding="utf-8")
    print(
        "Post-rebuild full RAG eval summary completed: "
        f"{report['summary']['status']}, "
        f"{report['rag_eval_summary']['post_rebuild_passed']}/"
        f"{report['rag_eval_summary']['post_rebuild_total']} passed, "
        f"regressions={report['rag_eval_summary']['regression_count']}, "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
