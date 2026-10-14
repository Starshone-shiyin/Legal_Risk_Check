"""Summarize post-rebuild repeat full RAG eval stability from saved reports.

This tool is a saved-report-only diagnostic. It does not call rag_query,
contact Qdrant or an LLM, run eval, or mutate runtime configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.0"

DEFAULT_REPEAT_REPORT_PATH = Path("tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json")
DEFAULT_BASELINE_REPORT_PATH = Path("tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md")


GUARDRAILS = {
    "saved_reports_only": True,
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def report_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in as_list(report.get("reports")) if isinstance(row, dict)]


def row_id(row: dict[str, Any]) -> str:
    return str(row.get("id") or row.get("case_id") or "")


def failed_check_names(row: dict[str, Any]) -> list[str]:
    names = []
    for check in as_list(row.get("checks")):
        if not isinstance(check, dict):
            continue
        if check.get("passed") is False:
            names.append(str(check.get("name") or "unnamed_check"))
    return names


def evidence_key(evidence: dict[str, Any]) -> str:
    source = str(evidence.get("source") or evidence.get("law_name") or "")
    article = evidence.get("article_no", "")
    section = evidence.get("section_no", "")
    citation = str(evidence.get("citation") or "")
    chunk_id = str(evidence.get("chunk_id") or "")
    if source or article or section:
        return f"{source}|{article}|{section}".strip("|")
    if citation:
        return citation
    return chunk_id or hashlib.sha256(json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def evidence_keys(row: dict[str, Any]) -> list[str]:
    keys = []
    for item in as_list(row.get("evidence")):
        if isinstance(item, dict):
            keys.append(evidence_key(item))
    return keys


def answer_digest(row: dict[str, Any]) -> str:
    answer = str(row.get("answer") or "")
    return hashlib.sha256(answer.encode("utf-8")).hexdigest()


def answer_excerpt(row: dict[str, Any], limit: int = 180) -> str:
    answer = " ".join(str(row.get("answer") or "").split())
    return answer if len(answer) <= limit else answer[: limit - 3] + "..."


def reports_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row_id(row): row for row in report_rows(report) if row_id(row)}


def case_metadata(cases_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = as_list(cases_report.get("cases"))
    if not rows:
        rows = as_list(cases_report.get("rag_eval_cases"))
    meta = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        case_id = str(row.get("id") or row.get("case_id") or "")
        if case_id:
            meta[case_id] = {
                "category": row.get("category"),
                "scenario_id": row.get("scenario_id"),
                "question": row.get("question"),
                "expected_evidence": row.get("expected_evidence"),
                "expected_answer_keywords": row.get("expected_answer_keywords"),
            }
    return meta


def case_status_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": row.get("passed"),
        "retrieval_failure_stage": row.get("retrieval_failure_stage"),
        "failed_checks": failed_check_names(row),
        "contribution_labels": as_list(row.get("contribution_labels")),
        "evidence_keys": evidence_keys(row),
        "answer_digest": answer_digest(row),
        "answer_excerpt": answer_excerpt(row),
    }


def classify_unstable_case(snapshots: list[dict[str, Any]]) -> str:
    stages = {snapshot.get("retrieval_failure_stage") for snapshot in snapshots}
    failed_checks = {tuple(snapshot.get("failed_checks", [])) for snapshot in snapshots}
    evidence_sets = {tuple(snapshot.get("evidence_keys", [])) for snapshot in snapshots}
    passed_values = {snapshot.get("passed") for snapshot in snapshots}
    if stages != {"PASS"}:
        return "retrieval_stage_instability"
    if len(evidence_sets) > 1:
        return "final_evidence_identity_drift"
    if len(passed_values) > 1 and failed_checks:
        return "answer_or_check_instability_with_stable_retrieval"
    return "label_or_generation_variation"


def repeat_case_ids(repeat_report: dict[str, Any]) -> list[str]:
    ids: set[str] = set()
    for run in as_list(repeat_report.get("runs")):
        if isinstance(run, dict):
            ids.update(reports_by_id(run).keys())
    return sorted(ids)


def build_unstable_cases(repeat_report: dict[str, Any], metadata: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    runs = [run for run in as_list(repeat_report.get("runs")) if isinstance(run, dict)]
    stability = as_dict(repeat_report.get("stability_summary"))
    unstable_ids = [str(item.get("id")) for item in as_list(stability.get("unstable_cases")) if isinstance(item, dict)]
    output = []
    for case_id in unstable_ids:
        snapshots = []
        for run in runs:
            row = reports_by_id(run).get(case_id, {})
            snapshot = case_status_snapshot(row) if row else {"missing": True}
            snapshot["run"] = run.get("run")
            snapshots.append(snapshot)
        output.append({
            "id": case_id,
            "category": metadata.get(case_id, {}).get("category"),
            "scenario_id": metadata.get(case_id, {}).get("scenario_id"),
            "question": metadata.get(case_id, {}).get("question"),
            "classification": classify_unstable_case(snapshots),
            "pass_by_run": [snapshot.get("passed") for snapshot in snapshots],
            "retrieval_stage_by_run": [snapshot.get("retrieval_failure_stage") for snapshot in snapshots],
            "failed_checks_by_run": [snapshot.get("failed_checks", []) for snapshot in snapshots],
            "contribution_labels_by_run": [snapshot.get("contribution_labels", []) for snapshot in snapshots],
            "evidence_keys_by_run": [snapshot.get("evidence_keys", []) for snapshot in snapshots],
            "answer_digest_by_run": [snapshot.get("answer_digest") for snapshot in snapshots],
            "answer_excerpt_by_run": [snapshot.get("answer_excerpt", "") for snapshot in snapshots],
            "review_reason": "同一 case 在 repeat full RAG eval 中出现通过状态或检查项波动，需要先定位输出措辞、证据身份或检索阶段是否稳定。",
        })
    return output


def build_label_variation_cases(repeat_report: dict[str, Any], metadata: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    stability = as_dict(repeat_report.get("stability_summary"))
    output = []
    for item in as_list(stability.get("label_variation_cases")):
        if not isinstance(item, dict):
            continue
        case_id = str(item.get("id") or "")
        output.append({
            "id": case_id,
            "category": metadata.get(case_id, {}).get("category"),
            "scenario_id": metadata.get(case_id, {}).get("scenario_id"),
            "question": metadata.get(case_id, {}).get("question"),
            "contribution_labels": as_list(item.get("contribution_labels")),
            "blocking": False,
            "review_reason": "贡献标签在多轮之间变化，但若通过状态、检索阶段和失败检查未同步漂移，则作为观察信号而非阻断项。",
        })
    return output


def build_evidence_identity_drift(repeat_report: dict[str, Any]) -> dict[str, Any]:
    runs = [run for run in as_list(repeat_report.get("runs")) if isinstance(run, dict)]
    changed = []
    unchanged = 0
    for case_id in repeat_case_ids(repeat_report):
        keys_by_run = []
        for run in runs:
            row = reports_by_id(run).get(case_id, {})
            keys_by_run.append(evidence_keys(row))
        if len({tuple(keys) for keys in keys_by_run}) > 1:
            changed.append({"id": case_id, "evidence_keys_by_run": keys_by_run})
        else:
            unchanged += 1
    return {
        "changed_case_count": len(changed),
        "unchanged_case_count": unchanged,
        "changed_cases": changed,
    }


def build_answer_drift_summary(repeat_report: dict[str, Any]) -> dict[str, Any]:
    runs = [run for run in as_list(repeat_report.get("runs")) if isinstance(run, dict)]
    changed = []
    unchanged = 0
    for case_id in repeat_case_ids(repeat_report):
        digests = []
        excerpts = []
        for run in runs:
            row = reports_by_id(run).get(case_id, {})
            digests.append(answer_digest(row))
            excerpts.append(answer_excerpt(row, limit=120))
        if len(set(digests)) > 1:
            changed.append({"id": case_id, "answer_digest_by_run": digests, "answer_excerpt_by_run": excerpts})
        else:
            unchanged += 1
    return {
        "changed_case_count": len(changed),
        "unchanged_case_count": unchanged,
        "changed_cases": changed,
    }


def build_baseline_comparison(repeat_report: dict[str, Any], baseline_report: dict[str, Any]) -> dict[str, Any]:
    baseline = reports_by_id(baseline_report)
    runs = [run for run in as_list(repeat_report.get("runs")) if isinstance(run, dict)]
    baseline_ids = set(baseline)
    repeat_ids = set(repeat_case_ids(repeat_report))
    pass_status_drifts = []
    retrieval_stage_drifts = []
    failed_check_drifts = []
    evidence_identity_drifts = []

    for run in runs:
        run_id = run.get("run")
        current = reports_by_id(run)
        for case_id in sorted(baseline_ids & set(current)):
            base_row = baseline[case_id]
            run_row = current[case_id]
            if base_row.get("passed") != run_row.get("passed"):
                pass_status_drifts.append({
                    "id": case_id,
                    "run": run_id,
                    "baseline": base_row.get("passed"),
                    "current": run_row.get("passed"),
                })
            if base_row.get("retrieval_failure_stage") != run_row.get("retrieval_failure_stage"):
                retrieval_stage_drifts.append({
                    "id": case_id,
                    "run": run_id,
                    "baseline": base_row.get("retrieval_failure_stage"),
                    "current": run_row.get("retrieval_failure_stage"),
                })
            if failed_check_names(base_row) != failed_check_names(run_row):
                failed_check_drifts.append({
                    "id": case_id,
                    "run": run_id,
                    "baseline": failed_check_names(base_row),
                    "current": failed_check_names(run_row),
                })
            if evidence_keys(base_row) != evidence_keys(run_row):
                evidence_identity_drifts.append({
                    "id": case_id,
                    "run": run_id,
                    "baseline": evidence_keys(base_row),
                    "current": evidence_keys(run_row),
                })

    return {
        "baseline_total": baseline_report.get("total"),
        "baseline_passed": baseline_report.get("passed"),
        "missing_cases": sorted(baseline_ids - repeat_ids),
        "new_cases": sorted(repeat_ids - baseline_ids),
        "pass_status_drifts": pass_status_drifts,
        "retrieval_stage_drifts": retrieval_stage_drifts,
        "failed_check_drifts": failed_check_drifts,
        "evidence_identity_drifts": evidence_identity_drifts,
    }


def contribution_summary_by_run(repeat_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for run in as_list(repeat_report.get("runs")):
        if not isinstance(run, dict):
            continue
        contribution = as_dict(run.get("contribution_summary"))
        rows.append({
            "run": run.get("run"),
            "passed": run.get("passed"),
            "total": run.get("total"),
            "retrieval_failure_stage_summary": as_dict(run.get("retrieval_failure_stage_summary")),
            "label_counts": as_dict(contribution.get("label_counts")),
            "dense_fallback_passed": contribution.get("dense_fallback_passed"),
        })
    return rows


def blocker_list(
    repeat_report: dict[str, Any],
    baseline_comparison: dict[str, Any],
    evidence_drift: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    stability = as_dict(repeat_report.get("stability_summary"))
    pass_counts = as_list(stability.get("pass_counts"))
    total_counts = as_list(stability.get("total_counts"))
    if stability.get("all_runs_full_pass") is not True:
        blockers.append("repeat_not_all_runs_full_pass")
    if any(pass_count != total_count for pass_count, total_count in zip(pass_counts, total_counts)):
        blockers.append("repeat_pass_count_below_total")
    if as_list(stability.get("unstable_cases")):
        blockers.append("repeat_unstable_cases_present")
    if baseline_comparison["missing_cases"] or baseline_comparison["new_cases"]:
        blockers.append("baseline_case_set_drift")
    if baseline_comparison["pass_status_drifts"]:
        blockers.append("baseline_pass_status_drift")
    if baseline_comparison["retrieval_stage_drifts"]:
        blockers.append("baseline_retrieval_stage_drift")
    if baseline_comparison["failed_check_drifts"]:
        blockers.append("baseline_failed_check_drift")
    if evidence_drift["changed_case_count"]:
        blockers.append("repeat_evidence_identity_drift")
    for row in contribution_summary_by_run(repeat_report):
        if row.get("dense_fallback_passed") not in (0, None):
            blockers.append("dense_fallback_used_in_repeat")
            break
    return sorted(set(blockers))


def build_report(
    repeat_report_path: Path = DEFAULT_REPEAT_REPORT_PATH,
    baseline_report_path: Path = DEFAULT_BASELINE_REPORT_PATH,
    cases_path: Path = DEFAULT_CASES_PATH,
) -> dict[str, Any]:
    repeat_report = load_json(repeat_report_path)
    baseline_report = load_json(baseline_report_path)
    cases = load_json(cases_path, required=False)
    metadata = case_metadata(cases)
    stability = as_dict(repeat_report.get("stability_summary"))
    evidence_drift = build_evidence_identity_drift(repeat_report)
    answer_drift = build_answer_drift_summary(repeat_report)
    baseline = build_baseline_comparison(repeat_report, baseline_report)
    blockers = blocker_list(repeat_report, baseline, evidence_drift)

    unstable_cases = build_unstable_cases(repeat_report, metadata)
    issue_type_summary = Counter(row["classification"] for row in unstable_cases)
    issue_type_summary.update({"label_variation_observation": len(build_label_variation_cases(repeat_report, metadata))})

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_repeat_stability_summary",
        "scope": "post-rebuild repeat full RAG eval saved-report stability baseline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "repeat_report": str(repeat_report_path),
            "baseline_report": str(baseline_report_path),
            "cases": str(cases_path),
        },
        "guardrails": GUARDRAILS,
        "repeat_summary": {
            "repeat": repeat_report.get("repeat"),
            "runs": stability.get("runs"),
            "pass_counts": stability.get("pass_counts"),
            "total_counts": stability.get("total_counts"),
            "all_runs_full_pass": stability.get("all_runs_full_pass"),
            "unstable_case_count": len(as_list(stability.get("unstable_cases"))),
            "label_variation_case_count": len(as_list(stability.get("label_variation_cases"))),
        },
        "contribution_summary_by_run": contribution_summary_by_run(repeat_report),
        "unstable_cases": unstable_cases,
        "label_variation_cases": build_label_variation_cases(repeat_report, metadata),
        "issue_type_summary": dict(sorted(issue_type_summary.items())),
        "evidence_identity_drift_summary": evidence_drift,
        "answer_drift_summary": answer_drift,
        "baseline_comparison": baseline,
        "high_risk_manual_review_list": [
            {
                "id": row["id"],
                "classification": row["classification"],
                "review_reason": row["review_reason"],
            }
            for row in unstable_cases
        ],
        "summary": {
            "status": "needs_triage" if blockers else "passed",
            "blockers": blockers,
            "recommended_next_step": (
                "triage_repeat_output_instability_before_runtime_change"
                if blockers
                else "proceed_to_next_real_rag_quality_task"
            ),
            "runtime_fix_authorized": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    repeat = as_dict(report.get("repeat_summary"))
    evidence = as_dict(report.get("evidence_identity_drift_summary"))
    answer = as_dict(report.get("answer_drift_summary"))
    baseline = as_dict(report.get("baseline_comparison"))

    lines = [
        "# v0.4.15.0 Post-Rebuild Repeat Stability Summary",
        "",
        "## 结论",
        "",
        f"- 状态：`{summary.get('status')}`",
        f"- repeat：`{repeat.get('repeat')}`",
        f"- pass counts：`{repeat.get('pass_counts')}` / totals `{repeat.get('total_counts')}`",
        f"- all runs full pass：`{repeat.get('all_runs_full_pass')}`",
        f"- unstable cases：`{repeat.get('unstable_case_count')}`",
        f"- label variation cases：`{repeat.get('label_variation_case_count')}`",
        f"- final evidence identity drift cases：`{evidence.get('changed_case_count')}`",
        f"- answer drift cases：`{answer.get('changed_case_count')}`",
        f"- blockers：`{summary.get('blockers')}`",
        f"- 推荐下一步：`{summary.get('recommended_next_step')}`",
        "",
        "## 关键发现",
        "",
        "本版本读取已保存的 repeat full RAG eval 报告和 v0.4.14.34 单次 60/60 基线，未重新运行评测，也未连接 Qdrant 或 LLM。",
        "",
    ]
    unstable = as_list(report.get("unstable_cases"))
    if unstable:
        lines.append("出现波动的 case：")
        for row in unstable:
            lines.append(
                f"- `{row.get('id')}`：`{row.get('classification')}`；"
                f"pass_by_run=`{row.get('pass_by_run')}`；"
                f"failed_checks_by_run=`{row.get('failed_checks_by_run')}`。"
            )
    else:
        lines.append("未发现通过状态波动 case。")

    lines.extend([
        "",
        "## 基线对比",
        "",
        f"- missing cases：`{baseline.get('missing_cases')}`",
        f"- new cases：`{baseline.get('new_cases')}`",
        f"- pass status drifts：`{len(as_list(baseline.get('pass_status_drifts')))}`",
        f"- retrieval stage drifts：`{len(as_list(baseline.get('retrieval_stage_drifts')))}`",
        f"- failed check drifts：`{len(as_list(baseline.get('failed_check_drifts')))}`",
        f"- evidence identity drifts：`{len(as_list(baseline.get('evidence_identity_drifts')))}`",
        "",
        "## 边界",
        "",
        "这是 RAG 质量稳定性诊断，不是样本修补工具，不是新增 gate 链，也不是 runtime 调参授权。"
        "本版本不修改 anchor、prompt、rerank、risk supplement、term preservation、scenario registry、hidden seed、fixtures 或 eval cases。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a saved-report post-rebuild repeat RAG stability summary.")
    parser.add_argument("--repeat-report", type=Path, default=DEFAULT_REPEAT_REPORT_PATH)
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repeat_report, args.baseline_report, args.cases)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    status = report["summary"]["status"]
    blockers = report["summary"]["blockers"]
    print(f"Post-rebuild repeat stability summary completed: {status}, blockers={blockers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
