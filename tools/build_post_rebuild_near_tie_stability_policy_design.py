"""Build the v0.4.15.5 near-tie stability policy design report.

This is a design-only helper. It reads v0.4.15.4 saved trace attribution and
does not run eval, call rag_query, contact Qdrant or an LLM, or mutate runtime
behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


VERSION = "0.4.15.5"

DEFAULT_TRACE_ATTRIBUTION_PATH = Path("tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md")

GUARDRAILS = {
    "saved_reports_only": True,
    "design_only": True,
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_score_mutation": "disallowed",
    "cross_encoder_model_change": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
}

PROPOSED_POLICY = {
    "name": "deterministic_same_bucket_order_stabilization",
    "status": "design_only_not_implemented",
    "problem_target": "Cross-Encoder scores within the existing score_epsilon bucket can yield unstable full rerank order near the final evidence boundary.",
    "allowed_runtime_scope_if_later_authorized": [
        "Add deterministic ordering only inside existing stable-score buckets before final selection.",
        "Keep Cross-Encoder scores, model, query, score_epsilon and top_k unchanged.",
        "Use existing candidate metadata and selector-only evidence text; do not call LLM, Qdrant or reranker again.",
        "Preserve the current _select_diverse_rerank_top and _retain_high_alignment_evidence semantics unless a later patch explicitly proves no broader behavior drift.",
    ],
    "candidate_tie_break_keys_in_priority_order": [
        "legal_alignment_profile_score",
        "source_and_article_exactness",
        "input_rank",
        "candidate_exact_key",
    ],
    "explicitly_disallowed": [
        "Changing Cross-Encoder score values or score_epsilon.",
        "Adding or editing anchors for this case.",
        "Adding prompt instructions or risk supplement rules.",
        "Editing hidden seeds, eval cases, fixtures or scenario registry.",
        "Using case id specific branches.",
        "Using legal source names as hard-coded winners.",
    ],
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


def validate_trace_attribution(trace_attribution: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(trace_attribution.get("summary"))
    checks = [
        {
            "name": "trace_attribution_available",
            "passed": trace_attribution.get("schema_kind") == "post_rebuild_selection_trace_attribution",
        },
        {
            "name": "classification_supports_near_tie_design",
            "passed": summary.get("classification") == "raw_rerank_order_boundary_drift_not_selector_replacement",
        },
        {
            "name": "runtime_fix_not_authorized",
            "passed": summary.get("runtime_fix_authorized") is False,
        },
        {
            "name": "selected_alternates_match_trace",
            "passed": summary.get("all_selected_alternates_match_trace") is True,
        },
        {
            "name": "both_drift_candidates_present_in_full_order",
            "passed": summary.get("both_drift_candidates_present_in_full_order_all_runs") is True,
        },
        {
            "name": "selected_candidate_follows_full_order",
            "passed": summary.get("selected_alternate_is_earlier_full_order_candidate") is True,
        },
    ]
    blockers = [item["name"] for item in checks if not item["passed"]]
    return {"checks": checks, "blockers": blockers}


def build_report(trace_attribution_path: Path = DEFAULT_TRACE_ATTRIBUTION_PATH) -> dict[str, Any]:
    trace_attribution = load_json(trace_attribution_path)
    validation = validate_trace_attribution(trace_attribution)
    trace_summary = as_dict(trace_attribution.get("summary"))
    ready_for_design = not validation["blockers"]
    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_near_tie_stability_policy_design",
        "scope": "design-only near-tie stability policy after traced evidence drift attribution",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {"trace_attribution": str(trace_attribution_path)},
        "guardrails": GUARDRAILS,
        "trace_attribution_summary": {
            "classification": trace_summary.get("classification"),
            "status": trace_summary.get("status"),
            "selected_alternate_counts": trace_summary.get("selected_alternate_counts"),
            "recommended_next_step": trace_summary.get("recommended_next_step"),
        },
        "validation": validation,
        "proposed_policy": PROPOSED_POLICY,
        "implementation_gate_if_later_authorized": {
            "allowed_file": "src/rag/retriever.py",
            "preferred_function_scope": "_sort_rerank_scores_stable caller-side same-bucket stabilization before _select_diverse_rerank_top",
            "must_not_change": [
                "_call_siliconflow_rerank",
                "build_search_query",
                "_format_anchor_rerank_hint",
                "_select_diverse_rerank_top semantics",
                "_retain_high_alignment_evidence semantics",
                "risk supplement",
                "term preservation",
                "eval cases",
            ],
            "required_targeted_validation": [
                "risk_algorithm_bias_001 targeted repeat with debug trace",
                "tests.test_candidate_budget",
                "full project health check",
                "restricted diff over config/eval/fixture files",
            ],
            "full_eval_required_before_series_closeout": True,
        },
        "summary": {
            "status": "ready_for_near_tie_policy_review" if ready_for_design else "blocked",
            "blockers": validation["blockers"],
            "runtime_patch_authorized": False,
            "recommended_next_step": (
                "implement_minimal_same_bucket_stabilization_only_after_authorization"
                if ready_for_design
                else "repair_trace_attribution_before_policy_design"
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    policy = as_dict(report.get("proposed_policy"))
    trace = as_dict(report.get("trace_attribution_summary"))
    lines = [
        "# v0.4.15.5 Near-Tie Stability Policy Design",
        "",
        "## 结论",
        "",
        f"- status: `{summary.get('status')}`",
        f"- blockers: `{summary.get('blockers')}`",
        f"- runtime patch authorized: `{summary.get('runtime_patch_authorized')}`",
        f"- recommended next step: `{summary.get('recommended_next_step')}`",
        "",
        "## 输入依据",
        "",
        f"- v0.4.15.4 classification: `{trace.get('classification')}`",
        f"- v0.4.15.4 selected alternate counts: `{trace.get('selected_alternate_counts')}`",
        "",
        "## 设计口径",
        "",
        f"- policy: `{policy.get('name')}`",
        "- 只允许未来在既有 Cross-Encoder stable-score bucket 内做 deterministic ordering。",
        "- 不改变 Cross-Encoder 分数、模型、query、`score_epsilon`、top_k、anchor、prompt 或 eval case。",
        "- 不写 case id 分支，不硬编码某部法律或某个条文为赢家。",
        "- 任何 runtime patch 都必须另开版本、重新授权，并跑 targeted repeat trace 与完整健康检查。",
        "",
        "## 边界",
        "",
        "本报告是 design-only，不是 runtime patch。",
        "本版本不修改 hidden seed、anchor、prompt、rerank score、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build near-tie stability policy design report.")
    parser.add_argument("--trace-attribution", type=Path, default=DEFAULT_TRACE_ATTRIBUTION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.trace_attribution)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild near-tie stability policy design completed: "
        f"{report['summary']['status']}, blockers={report['summary']['blockers']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
