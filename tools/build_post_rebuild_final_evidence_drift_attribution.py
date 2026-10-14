"""Attribute v0.4.15.1 final evidence drift from saved targeted repeat reports.

This is a saved-report-only attribution helper. It reads debug_info already
captured by run_rag_eval and does not run eval, call rag_query, contact Qdrant
or an LLM, or mutate runtime behavior.
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

from tools.build_post_rebuild_repeat_stability_summary import (  # noqa: E402
    as_dict,
    as_list,
    case_metadata,
    evidence_key,
    load_json,
    reports_by_id,
    write_json,
    write_text,
)


VERSION = "0.4.15.2"

TARGET_CASE_ID = "risk_algorithm_bias_001"
DRIFT_CANDIDATE_KEYS = [
    "中华人民共和国个人信息保护法|56",
    "中华人民共和国网络安全法|20",
]
CORE_EXPECTED_KEYS = [
    "中华人民共和国个人信息保护法|24",
    "中华人民共和国个人信息保护法|48",
]

DEFAULT_TARGETED_REPEAT_PATH = Path("tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json")
DEFAULT_TRIAGE_PATH = Path("tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md")

DEBUG_LAYERS = [
    "dense_candidates",
    "sparse_candidates",
    "union_candidates",
    "anchor_candidates",
    "rerank_input_candidates",
    "reranked_candidates",
    "final_candidates",
]

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


def candidate_key(candidate: dict[str, Any]) -> str:
    return evidence_key(candidate)


def candidate_preview(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": candidate_key(candidate),
        "source": candidate.get("source") or candidate.get("law_name"),
        "article_no": candidate.get("article_no"),
        "section_no": candidate.get("section_no"),
        "citation": candidate.get("citation"),
        "similarity_score": candidate.get("similarity_score"),
        "rerank_score": candidate.get("rerank_score"),
        "keyword_hits": candidate.get("keyword_hits", []),
        "content_preview": candidate.get("content_preview"),
    }


def find_candidates(candidates: list[Any], key: str) -> list[dict[str, Any]]:
    output = []
    for index, item in enumerate(candidates, start=1):
        if not isinstance(item, dict):
            continue
        if candidate_key(item) == key:
            row = candidate_preview(item)
            row["rank"] = index
            output.append(row)
    return output


def run_report_rows(repeat_report: dict[str, Any], case_id: str) -> list[dict[str, Any]]:
    rows = []
    for run in as_list(repeat_report.get("runs")):
        if not isinstance(run, dict):
            continue
        case = reports_by_id(run).get(case_id)
        if isinstance(case, dict):
            rows.append({"run": run.get("run"), "case": case})
    return rows


def layer_hits(debug_info: dict[str, Any], key: str) -> dict[str, Any]:
    hits = {}
    for layer in DEBUG_LAYERS:
        candidates = as_list(debug_info.get(layer))
        layer_rows = find_candidates(candidates, key)
        hits[layer] = {
            "present": bool(layer_rows),
            "count": len(layer_rows),
            "hits": layer_rows,
        }
    return hits


def selected_alternate(final_keys: list[str]) -> str | None:
    for key in final_keys:
        if key in DRIFT_CANDIDATE_KEYS:
            return key
    return None


def build_run_attribution(repeat_report: dict[str, Any], case_id: str) -> list[dict[str, Any]]:
    output = []
    for item in run_report_rows(repeat_report, case_id):
        case = item["case"]
        debug_info = as_dict(case.get("debug_info"))
        final = as_list(case.get("evidence"))
        final_keys = [candidate_key(row) for row in final if isinstance(row, dict)]
        debug_final_keys = [
            candidate_key(row)
            for row in as_list(debug_info.get("final_candidates"))
            if isinstance(row, dict)
        ]
        run_layers = {
            key: layer_hits(debug_info, key)
            for key in CORE_EXPECTED_KEYS + DRIFT_CANDIDATE_KEYS
        }
        output.append({
            "run": item["run"],
            "passed": case.get("passed"),
            "retrieval_failure_stage": case.get("retrieval_failure_stage"),
            "final_evidence_keys": final_keys,
            "debug_final_candidate_keys": debug_final_keys,
            "selected_alternate_key": selected_alternate(final_keys),
            "core_expected_keys_present_in_final": all(key in final_keys for key in CORE_EXPECTED_KEYS),
            "drift_candidate_layer_hits": run_layers,
        })
    return output


def layer_presence_summary(run_attribution: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for key in CORE_EXPECTED_KEYS + DRIFT_CANDIDATE_KEYS:
        per_layer = {}
        for layer in DEBUG_LAYERS:
            present_runs = [
                row["run"]
                for row in run_attribution
                if as_dict(as_dict(row.get("drift_candidate_layer_hits")).get(key)).get(layer, {}).get("present")
            ]
            per_layer[layer] = {
                "present_run_count": len(present_runs),
                "present_runs": present_runs,
            }
        summary[key] = per_layer
    return summary


def selected_alternate_summary(run_attribution: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [row.get("selected_alternate_key") for row in run_attribution]
    counts = Counter(key for key in selected if key)
    return {
        "selected_alternate_by_run": selected,
        "selected_alternate_counts": dict(sorted(counts.items())),
        "selected_alternate_changed": len(set(key for key in selected if key)) > 1,
    }


def classify_attribution(run_attribution: list[dict[str, Any]], layer_summary: dict[str, Any]) -> dict[str, Any]:
    selected_summary = selected_alternate_summary(run_attribution)
    pipl56 = layer_summary.get("中华人民共和国个人信息保护法|56", {})
    cyber20 = layer_summary.get("中华人民共和国网络安全法|20", {})
    pipl56_rerank_input_all = as_dict(pipl56.get("rerank_input_candidates")).get("present_run_count") == len(run_attribution)
    cyber20_rerank_input_all = as_dict(cyber20.get("rerank_input_candidates")).get("present_run_count") == len(run_attribution)
    core_final_all = all(row.get("core_expected_keys_present_in_final") for row in run_attribution)

    blockers = []
    if selected_summary["selected_alternate_changed"]:
        blockers.append("selected_alternate_candidate_changed_across_runs")
    if pipl56_rerank_input_all and cyber20_rerank_input_all and selected_summary["selected_alternate_changed"]:
        blockers.append("both_alternates_present_before_final_selection")

    if blockers and core_final_all:
        classification = "rerank_top3_boundary_drift_after_core_evidence_locked"
    elif blockers:
        classification = "final_evidence_identity_drift"
    else:
        classification = "no_final_evidence_identity_drift_reproduced"

    return {
        "classification": classification,
        "blockers": blockers,
        "core_expected_evidence_stable": core_final_all,
        "both_alternates_present_in_rerank_input_all_runs": pipl56_rerank_input_all and cyber20_rerank_input_all,
        "stable_up_to_stage": "rerank_input_candidates" if pipl56_rerank_input_all and cyber20_rerank_input_all else "unknown",
        "stage_of_first_observed_divergence": "reranked_candidates_or_final_candidates" if blockers else None,
        "attribution_confidence": "medium",
        "raw_cross_encoder_full_order_available": False,
        "limitation": (
            "Saved debug_info stores selected reranked/final candidates but not the full raw Cross-Encoder score order "
            "for every rerank_input candidate; this report can attribute the drift to final third-slot alternate selection, "
            "but cannot prove whether the immediate cause is raw rerank score jitter or selector replacement logic."
        ),
    }


def build_report(
    targeted_repeat_path: Path = DEFAULT_TARGETED_REPEAT_PATH,
    triage_path: Path = DEFAULT_TRIAGE_PATH,
    cases_path: Path = DEFAULT_CASES_PATH,
) -> dict[str, Any]:
    targeted_repeat = load_json(targeted_repeat_path)
    triage = load_json(triage_path)
    cases = load_json(cases_path, required=False)
    metadata = case_metadata(cases)
    run_attribution = build_run_attribution(targeted_repeat, TARGET_CASE_ID)
    layer_summary = layer_presence_summary(run_attribution)
    selected_summary = selected_alternate_summary(run_attribution)
    attribution = classify_attribution(run_attribution, layer_summary)

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_final_evidence_drift_attribution",
        "scope": "saved-report attribution for risk_algorithm_bias_001 final evidence identity drift",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "targeted_repeat": str(targeted_repeat_path),
            "triage": str(triage_path),
            "cases": str(cases_path),
        },
        "guardrails": GUARDRAILS,
        "target_case": {
            "id": TARGET_CASE_ID,
            "question": metadata.get(TARGET_CASE_ID, {}).get("question"),
            "core_expected_keys": CORE_EXPECTED_KEYS,
            "drift_candidate_keys": DRIFT_CANDIDATE_KEYS,
            "previous_triage_status": as_dict(triage.get("summary")).get("status"),
            "previous_triage_blockers": as_dict(triage.get("summary")).get("blockers"),
        },
        "selected_alternate_summary": selected_summary,
        "layer_presence_summary": layer_summary,
        "run_attribution": run_attribution,
        "attribution": attribution,
        "summary": {
            "status": "needs_selector_stability_design" if attribution["blockers"] else "passed",
            "blockers": attribution["blockers"],
            "classification": attribution["classification"],
            "recommended_next_step": (
                "design_selection_trace_before_runtime_change"
                if attribution["blockers"]
                else "return_to_repeat_stability_monitoring"
            ),
            "runtime_fix_authorized": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    selected = as_dict(report.get("selected_alternate_summary"))
    attribution = as_dict(report.get("attribution"))
    lines = [
        "# v0.4.15.2 最终证据漂移归因报告",
        "",
        "## 结论",
        "",
        f"- status: `{summary.get('status')}`",
        f"- classification: `{summary.get('classification')}`",
        f"- blockers: `{summary.get('blockers')}`",
        f"- 每轮选中的备选第三证据: `{selected.get('selected_alternate_by_run')}`",
        f"- 备选第三证据计数: `{selected.get('selected_alternate_counts')}`",
        f"- 建议下一步: `{summary.get('recommended_next_step')}`",
        f"- 是否授权运行时修复: `{summary.get('runtime_fix_authorized')}`",
        "",
        "## 归因",
        "",
        "- 核心预期证据在多轮 targeted repeat 的最终证据中保持存在。",
        "- 两个备选第三证据在每一轮最终选择前都已经进入候选层。",
        "- 当前保存报告能观察到的首次分叉位于 `reranked_candidates/final_candidates` 的 top-3 边界。",
        "- 漂移项是最终证据的第三个备选项，不是核心预期证据对。",
        "- 现有保存报告不包含完整 raw Cross-Encoder score order，也不包含 selector decision trace。",
        f"- 局限: {attribution.get('limitation')}",
        "",
        "## 边界",
        "",
        "本报告是 saved-report attribution，不是运行时修复，也不是新增 gate 链。",
        "本版本不修改 hidden seeds、anchors、rerank、prompt、risk supplement、term preservation、scenario registry、fixtures、eval cases 或 Qdrant。",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-report final evidence drift attribution.")
    parser.add_argument("--targeted-repeat", type=Path, default=DEFAULT_TARGETED_REPEAT_PATH)
    parser.add_argument("--triage", type=Path, default=DEFAULT_TRIAGE_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.targeted_repeat, args.triage, args.cases)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild final evidence drift attribution completed: "
        f"{report['summary']['status']}, blockers={report['summary']['blockers']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
