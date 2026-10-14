"""Build the v0.4.15.3 selection trace readiness report.

This checker is intentionally local and synthetic. It does not call rag_query,
run eval, contact Qdrant or an LLM, or change rerank/selector behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import (
    _debug_final_evidence_selection_trace,
    _debug_rerank_full_score_order,
    _select_diverse_rerank_top,
)


VERSION = "0.4.15.3"

DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md")

GUARDRAILS = {
    "synthetic_documents_only": True,
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_score_mutation": "disallowed",
    "selector_behavior_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def doc(source: str, article_no: int, chunk_id: str, content: str | None = None) -> Document:
    return Document(
        page_content=content or f"{source} article {article_no} {chunk_id}",
        metadata={
            "source": source,
            "law_name": source,
            "article_no": article_no,
            "chunk_id": chunk_id,
            "citation": f"[{source}第{article_no}条]",
            "block_type": "article",
        },
    )


def synthetic_trace_sample() -> dict[str, Any]:
    docs = [
        doc("Law A", 24, "a24"),
        doc("Law A", 24, "a24-sibling"),
        doc("Law A", 48, "a48"),
        doc("Law B", 20, "b20"),
    ]
    reranked = [(docs[0], 0.99), (docs[1], 0.98), (docs[2], 0.97), (docs[3], 0.96)]
    selected = _select_diverse_rerank_top(reranked, top_k=3)
    return {
        "full_score_order": _debug_rerank_full_score_order(docs, reranked),
        "selection_trace": _debug_final_evidence_selection_trace(
            docs,
            reranked,
            selected,
            mode="cross_encoder",
            top_k=3,
        ),
        "selected_chunk_ids": [item.metadata["chunk_id"] for item, _ in selected],
    }


def build_report() -> dict[str, Any]:
    sample = synthetic_trace_sample()
    selected = sample["selection_trace"]["selected"]
    not_selected = sample["selection_trace"]["not_selected"]
    full_order = sample["full_score_order"]

    required_full_order_fields = {
        "rerank_rank",
        "input_rank",
        "score",
        "exact_key",
        "article_key",
        "source",
        "law_name",
        "article_no",
        "chunk_id",
        "content_preview",
    }
    required_selected_fields = required_full_order_fields | {"final_rank"}
    checks = [
        {
            "name": "full_rerank_score_order_present",
            "passed": bool(full_order) and required_full_order_fields.issubset(full_order[0]),
        },
        {
            "name": "selection_trace_present",
            "passed": sample["selection_trace"].get("mode") == "cross_encoder",
        },
        {
            "name": "selected_trace_has_final_and_rerank_rank",
            "passed": bool(selected) and required_selected_fields.issubset(selected[0]),
        },
        {
            "name": "not_selected_trace_exposes_skipped_candidate",
            "passed": [item["chunk_id"] for item in not_selected] == ["a24-sibling"],
        },
        {
            "name": "synthetic_selector_result_unchanged",
            "passed": sample["selected_chunk_ids"] == ["a24", "a48", "b20"],
        },
    ]
    blockers = [item["name"] for item in checks if not item["passed"]]

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_selection_trace_readiness",
        "scope": "debug-only full rerank score order and final evidence selection trace readiness",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "trace_fields": {
            "debug_info_fields": [
                "rerank_full_score_order",
                "final_evidence_selection_trace",
            ],
            "full_score_order_fields": sorted(required_full_order_fields),
            "selected_trace_fields": sorted(required_selected_fields),
            "selection_trace_summary_fields": [
                "mode",
                "top_k",
                "score_epsilon",
                "input_count",
                "full_rerank_count",
                "selected_count",
                "selected",
                "not_selected",
            ],
        },
        "synthetic_sample": sample,
        "checks": checks,
        "summary": {
            "status": "passed" if not blockers else "blocked",
            "blockers": blockers,
            "runtime_behavior_change": False,
            "recommended_next_step": "run_targeted_repeat_with_debug_trace_capture",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    sample = report["synthetic_sample"]
    lines = [
        "# v0.4.15.3 Selection Trace Readiness",
        "",
        "## 结论",
        "",
        f"- status: `{summary['status']}`",
        f"- blockers: `{summary['blockers']}`",
        f"- runtime behavior change: `{summary['runtime_behavior_change']}`",
        f"- recommended next step: `{summary['recommended_next_step']}`",
        "",
        "## 本版本新增的调试信号",
        "",
        "- `debug_info.rerank_full_score_order`: 记录 Cross-Encoder score 返回后的全量稳定排序、输入位次和候选标识。",
        "- `debug_info.final_evidence_selection_trace`: 记录 final evidence selector 的输入数量、选中项、未选中项、final rank、rerank rank 和 fallback 模式。",
        "- 这些字段只在 `debug=True` 时写入返回结果，不参与排序、筛选、prompt、risk supplement 或 term preservation。",
        "",
        "## Synthetic Sample",
        "",
        f"- selected chunk ids: `{sample['selected_chunk_ids']}`",
        f"- not selected chunk ids: `{[item['chunk_id'] for item in sample['selection_trace']['not_selected']]}`",
        "",
        "## 边界",
        "",
        "本版本是 RAG 主链路可观测性补丁，不是 rerank 调参，也不是 selector 行为修复。",
        "不修改 hidden seed、anchor、prompt、risk supplement、term preservation、scenario registry、fixtures、eval cases 或 Qdrant。",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build post-rebuild selection trace readiness report.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild selection trace readiness completed: "
        f"{report['summary']['status']}, blockers={report['summary']['blockers']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
