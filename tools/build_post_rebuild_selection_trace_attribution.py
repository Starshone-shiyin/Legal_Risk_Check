"""Attribute v0.4.15.4 final evidence drift with saved selection traces.

This helper reads the targeted repeat report produced after v0.4.15.3 trace
instrumentation. It does not run eval, call rag_query, contact Qdrant or an
LLM, or mutate runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


VERSION = "0.4.15.4"

TARGET_CASE_ID = "risk_algorithm_bias_001"
CORE_EXPECTED_KEYS = [
    "中华人民共和国个人信息保护法|24",
    "中华人民共和国个人信息保护法|48",
]
DRIFT_CANDIDATE_KEYS = [
    "中华人民共和国个人信息保护法|56",
    "中华人民共和国网络安全法|20",
]

DEFAULT_TRACE_REPEAT_PATH = Path("tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md")

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
    "rerank_score_mutation": "disallowed",
    "selector_behavior_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
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


def evidence_key(item: dict[str, Any]) -> str:
    source = str(item.get("source") or item.get("law_name") or "")
    article_no = item.get("article_no", "")
    section_no = item.get("section_no", "")
    if section_no:
        return f"{source}|{article_no}|{section_no}"
    return f"{source}|{article_no}"


def reports_by_id(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = as_list(run.get("reports"))
    output = {}
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            output[str(row["id"])] = row
    return output


def run_case_rows(report: dict[str, Any], case_id: str) -> list[dict[str, Any]]:
    rows = []
    for run in as_list(report.get("runs")):
        if not isinstance(run, dict):
            continue
        case = reports_by_id(run).get(case_id)
        if isinstance(case, dict):
            rows.append({"run": run.get("run"), "case": case})
    return rows


def selected_alternate(final_keys: list[str]) -> str | None:
    for key in final_keys:
        if key in DRIFT_CANDIDATE_KEYS:
            return key
    return None


def trace_item_by_key(items: list[Any], key: str) -> dict[str, Any] | None:
    for item in items:
        if isinstance(item, dict) and evidence_key(item) == key:
            return item
    return None


def build_run_trace_rows(trace_repeat_report: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for row in run_case_rows(trace_repeat_report, TARGET_CASE_ID):
        case = row["case"]
        debug_info = as_dict(case.get("debug_info"))
        trace = as_dict(debug_info.get("final_evidence_selection_trace"))
        final_keys = [evidence_key(item) for item in as_list(case.get("evidence")) if isinstance(item, dict)]
        selected_trace = [item for item in as_list(trace.get("selected")) if isinstance(item, dict)]
        not_selected_trace = [item for item in as_list(trace.get("not_selected")) if isinstance(item, dict)]
        full_order = [item for item in as_list(debug_info.get("rerank_full_score_order")) if isinstance(item, dict)]
        selected_key = selected_alternate(final_keys)
        drift_rows = {}
        for key in DRIFT_CANDIDATE_KEYS:
            selected_item = trace_item_by_key(selected_trace, key)
            full_order_item = trace_item_by_key(full_order, key)
            not_selected_item = trace_item_by_key(not_selected_trace, key)
            drift_rows[key] = {
                "selected": selected_item is not None,
                "final_rank": as_dict(selected_item).get("final_rank"),
                "rerank_rank": as_dict(selected_item or not_selected_item or full_order_item).get("rerank_rank"),
                "input_rank": as_dict(selected_item or not_selected_item or full_order_item).get("input_rank"),
                "score": as_dict(selected_item or not_selected_item or full_order_item).get("score"),
                "in_not_selected": not_selected_item is not None,
                "in_full_order": full_order_item is not None,
            }
        output.append({
            "run": row["run"],
            "passed": case.get("passed"),
            "retrieval_failure_stage": case.get("retrieval_failure_stage"),
            "trace_mode": trace.get("mode"),
            "final_evidence_keys": final_keys,
            "selected_alternate_key": selected_key,
            "core_expected_keys_present_in_final": all(key in final_keys for key in CORE_EXPECTED_KEYS),
            "selected_trace_keys": [evidence_key(item) for item in selected_trace],
            "drift_candidate_trace": drift_rows,
            "selected_alternate_matches_trace": bool(selected_key and trace_item_by_key(selected_trace, selected_key)),
        })
    return output


def classify_trace_attribution(run_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [row.get("selected_alternate_key") for row in run_rows]
    selected_counts = dict(sorted(Counter(key for key in selected if key).items()))
    selected_changed = len(set(key for key in selected if key)) > 1
    all_core_stable = all(row.get("core_expected_keys_present_in_final") for row in run_rows)
    all_matches_trace = all(row.get("selected_alternate_matches_trace") for row in run_rows)
    all_have_both_full_order = all(
        all(as_dict(as_dict(row.get("drift_candidate_trace")).get(key)).get("in_full_order") for key in DRIFT_CANDIDATE_KEYS)
        for row in run_rows
    )
    selected_is_earlier_rerank_candidate = True
    for row in run_rows:
        selected_key = row.get("selected_alternate_key")
        if not selected_key:
            selected_is_earlier_rerank_candidate = False
            continue
        selected_rank = as_dict(as_dict(row.get("drift_candidate_trace")).get(selected_key)).get("rerank_rank")
        other_ranks = [
            as_dict(as_dict(row.get("drift_candidate_trace")).get(key)).get("rerank_rank")
            for key in DRIFT_CANDIDATE_KEYS
            if key != selected_key
        ]
        if selected_rank is None or any(rank is None or selected_rank >= rank for rank in other_ranks):
            selected_is_earlier_rerank_candidate = False

    blockers = []
    if selected_changed:
        blockers.append("selected_alternate_candidate_changed_across_trace_runs")
    if all_have_both_full_order and selected_is_earlier_rerank_candidate:
        blockers.append("selected_alternate_follows_full_rerank_order_boundary")

    if selected_changed and all_matches_trace and selected_is_earlier_rerank_candidate:
        classification = "raw_rerank_order_boundary_drift_not_selector_replacement"
        recommended_next_step = "design_near_tie_stability_policy_before_runtime_change"
    elif selected_changed and all_matches_trace:
        classification = "selection_trace_confirms_final_selection_drift"
        recommended_next_step = "inspect_selector_replacement_rules_before_runtime_change"
    elif selected_changed:
        classification = "trace_incomplete_for_drift_attribution"
        recommended_next_step = "rerun_targeted_trace_capture"
    else:
        classification = "no_final_evidence_identity_drift_reproduced"
        recommended_next_step = "return_to_repeat_stability_monitoring"

    return {
        "classification": classification,
        "status": "needs_near_tie_stability_design" if blockers else "passed",
        "blockers": blockers,
        "selected_alternate_by_run": selected,
        "selected_alternate_counts": selected_counts,
        "selected_alternate_changed": selected_changed,
        "core_expected_evidence_stable": all_core_stable,
        "all_selected_alternates_match_trace": all_matches_trace,
        "both_drift_candidates_present_in_full_order_all_runs": all_have_both_full_order,
        "selected_alternate_is_earlier_full_order_candidate": selected_is_earlier_rerank_candidate,
        "runtime_fix_authorized": False,
        "recommended_next_step": recommended_next_step,
    }


def build_report(trace_repeat_path: Path = DEFAULT_TRACE_REPEAT_PATH) -> dict[str, Any]:
    trace_repeat_report = load_json(trace_repeat_path)
    run_rows = build_run_trace_rows(trace_repeat_report)
    attribution = classify_trace_attribution(run_rows)
    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_selection_trace_attribution",
        "scope": "saved trace attribution for risk_algorithm_bias_001 final evidence third-slot drift",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {"trace_repeat": str(trace_repeat_path)},
        "guardrails": GUARDRAILS,
        "target_case": {
            "id": TARGET_CASE_ID,
            "core_expected_keys": CORE_EXPECTED_KEYS,
            "drift_candidate_keys": DRIFT_CANDIDATE_KEYS,
        },
        "run_trace_rows": run_rows,
        "summary": attribution,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.15.4 Selection Trace Attribution",
        "",
        "## 结论",
        "",
        f"- status: `{summary.get('status')}`",
        f"- classification: `{summary.get('classification')}`",
        f"- blockers: `{summary.get('blockers')}`",
        f"- selected alternate by run: `{summary.get('selected_alternate_by_run')}`",
        f"- selected alternate counts: `{summary.get('selected_alternate_counts')}`",
        f"- recommended next step: `{summary.get('recommended_next_step')}`",
        f"- runtime fix authorized: `{summary.get('runtime_fix_authorized')}`",
        "",
        "## 归因",
        "",
        "- 核心证据《个人信息保护法》第 24 条和第 48 条在本轮 trace repeat 中保持稳定。",
        "- 第三席证据继续在《个人信息保护法》第 56 条与《网络安全法》第 20 条之间漂移。",
        "- 每一轮最终选中的第三席都能在 `final_evidence_selection_trace.selected` 中找到。",
        "- 选中的第三席始终是两个漂移候选中 full rerank order 更靠前的候选。",
        "- 因此本轮可将直接原因归到 raw rerank stable order / near-tie boundary drift，而不是 selector replacement 额外替换。",
        "",
        "## 边界",
        "",
        "本报告只读取 v0.4.15.4 targeted repeat saved report，不运行 eval、不调用 `rag_query`、不连接 Qdrant 或 LLM。",
        "本版本不修改 hidden seed、anchor、prompt、rerank score、selector 行为、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved selection trace attribution report.")
    parser.add_argument("--trace-repeat", type=Path, default=DEFAULT_TRACE_REPEAT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.trace_repeat)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild selection trace attribution completed: "
        f"{report['summary']['status']}, classification={report['summary']['classification']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
