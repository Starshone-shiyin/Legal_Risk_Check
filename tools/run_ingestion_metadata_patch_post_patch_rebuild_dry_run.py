"""Run the v0.4.13.11 post-patch rebuild dry-run.

This runner uses only saved governance reports and small deterministic local
article samples. It compares simulated pre-patch metadata with the current
post-patch ``build_article_documents`` output in memory. It does not write
Qdrant, rebuild a collection, call RAG, call embeddings or LLMs, or run full
eval.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.13.11"

DEFAULT_SOURCE_PATCH_REPORT_PATH = legacy_report_path("ingestion_metadata_source_patch_report.json")
DEFAULT_DESIGN_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json")
DEFAULT_DESIGN_GATE_PATH = legacy_report_path(
    "ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json"
)
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md")

BOUNDARY_METADATA_KEYS = {"chunk_index", "chunk_count"}
STABLE_METADATA_KEYS = {
    "citation",
    "block_type",
    "paragraph_no",
    "item_no",
    "item_label",
    "parent_article_id",
}

GUARDRAILS = {
    "local_in_memory_only": True,
    "saved_reports_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "ingestion_source_mutation": "disallowed",
    "retrieval_logic_change_allowed": False,
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

SAMPLE_SCENARIOS = [
    {
        "sample_id": "single_paragraph_article",
        "shape": "single paragraph article",
        "article": "Article 913411",
        "article_no": 913411,
        "parts": [
            "Controllers shall keep processing records and retain compliance evidence.",
        ],
    },
    {
        "sample_id": "paragraph_plus_item_article",
        "shape": "paragraph plus item article",
        "article": "Article 913412",
        "article_no": 913412,
        "parts": [
            "Controllers shall maintain a lawful basis before processing personal data.",
            "\uff08\u4e00\uff09define processing purposes, methods, and retention periods.",
            "\uff08\u4e8c\uff09establish access control, audit log, and deletion procedures.",
        ],
    },
    {
        "sample_id": "multi_paragraph_article",
        "shape": "multi-paragraph article",
        "article": "Article 913413",
        "article_no": 913413,
        "parts": [
            "Operators shall notify affected parties when processing rules materially change.",
            "Operators shall keep complaint handling and correction channels available.",
        ],
    },
]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sample_metadata(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "v0.4.13.11 post-patch rebuild dry-run sample law",
        "law_name": "v0.4.13.11 post-patch rebuild dry-run sample law",
        "document_type": "local_dry_run_law",
        "law_level": "local_dry_run",
        "authority_level": "local_dry_run",
        "jurisdiction": "local_dry_run",
        "issuing_authority": "local_dry_run",
        "category": "local_dry_run",
        "version": VERSION,
        "type": "article",
        "article": sample["article"],
        "article_no": sample["article_no"],
    }


def build_current_documents(sample: dict[str, Any]):
    from src.rag.ingestion import build_article_documents

    return build_article_documents(sample["parts"], _sample_metadata(sample))


def assign_ids(documents):
    from src.rag.ingestion import assign_stable_chunk_ids

    return assign_stable_chunk_ids(documents)


def simulate_pre_patch_documents(post_patch_documents):
    pre_patch_documents = copy.deepcopy(post_patch_documents)
    for document in pre_patch_documents:
        document.metadata.pop("chunk_index", None)
        document.metadata.pop("chunk_count", None)
        document.metadata.pop("chunk_id", None)
        document.metadata.pop("qdrant_point_id", None)
    return pre_patch_documents


def document_role(document) -> str:
    block_type = document.metadata.get("block_type")
    if block_type == "article":
        return "parent_article"
    if block_type in {"paragraph", "item"}:
        return "article_child"
    return str(block_type or "unknown")


def _stable_metadata_equal(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return all(before.get(key) == after.get(key) for key in STABLE_METADATA_KEYS)


def _metadata_snapshot(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(STABLE_METADATA_KEYS | BOUNDARY_METADATA_KEYS | {"chunk_id", "qdrant_point_id", "article_no"})
    return {key: metadata.get(key) for key in keys if key in metadata}


def compare_documents(sample_id: str, before_docs, after_docs) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    if len(before_docs) != len(after_docs):
        blockers.append(f"{sample_id}:document_count_mismatch")

    for index, (before_doc, after_doc) in enumerate(zip(before_docs, after_docs), start=1):
        chunk_index = after_doc.metadata.get("chunk_index")
        chunk_count = after_doc.metadata.get("chunk_count")
        content_stable = before_doc.page_content == after_doc.page_content
        citation_stable = before_doc.metadata.get("citation") == after_doc.metadata.get("citation")
        block_metadata_stable = _stable_metadata_equal(before_doc.metadata, after_doc.metadata)
        chunk_id_drift = before_doc.metadata.get("chunk_id") != after_doc.metadata.get("chunk_id")
        qdrant_point_id_drift = before_doc.metadata.get("qdrant_point_id") != after_doc.metadata.get("qdrant_point_id")

        detected_drifts: list[str] = []
        blocking_conditions: list[str] = []
        if chunk_id_drift:
            detected_drifts.append("expected_chunk_id_drift")
        if qdrant_point_id_drift:
            detected_drifts.append("expected_qdrant_point_id_drift")
        if before_doc.metadata.get("chunk_index") != chunk_index:
            detected_drifts.append("expected_chunk_index_added")
        if before_doc.metadata.get("chunk_count") != chunk_count:
            detected_drifts.append("expected_chunk_count_added")
        if chunk_index is None or chunk_count is None:
            blocking_conditions.append("chunk_boundary_metadata_missing")
        if not content_stable or not citation_stable:
            blocking_conditions.append("forbidden_content_or_citation_drift")
        if not block_metadata_stable:
            blocking_conditions.append("forbidden_block_metadata_drift")
        if not chunk_id_drift:
            blocking_conditions.append("expected_chunk_id_drift_missing")
        if not qdrant_point_id_drift:
            blocking_conditions.append("expected_qdrant_point_id_drift_missing")

        for condition in blocking_conditions:
            blockers.append(f"{sample_id}:{index}:{condition}")

        rows.append(
            {
                "sample_id": sample_id,
                "document_index": index,
                "document_role": document_role(after_doc),
                "block_type": after_doc.metadata.get("block_type"),
                "before_metadata": _metadata_snapshot(before_doc.metadata),
                "after_metadata": _metadata_snapshot(after_doc.metadata),
                "chunk_index": chunk_index,
                "chunk_count": chunk_count,
                "chunk_id_drift": chunk_id_drift,
                "qdrant_point_id_drift": qdrant_point_id_drift,
                "content_stable": content_stable,
                "citation_stable": citation_stable,
                "block_metadata_stable": block_metadata_stable,
                "detected_drifts": detected_drifts,
                "blocking_conditions": blocking_conditions,
            }
        )
    return rows, blockers


def prerequisite_blockers(
    source_patch_report: dict[str, Any],
    design_report: dict[str, Any],
    design_gate_report: dict[str, Any],
) -> list[str]:
    blockers = []
    source_summary = as_dict(source_patch_report.get("summary"))
    design_summary = as_dict(design_report.get("summary"))
    gate_summary = as_dict(design_gate_report.get("summary"))

    if source_patch_report.get("version") != "0.4.13.8":
        blockers.append("source_patch_report_version_mismatch")
    if source_patch_report.get("schema_kind") != "ingestion_metadata_source_patch_check":
        blockers.append("source_patch_report_schema_mismatch")
    if source_summary.get("status") != "passed":
        blockers.append("source_patch_report_missing_or_failed")
    if source_summary.get("allowed_next_step") != "post_patch_rebuild_dry_run_design":
        blockers.append("source_patch_report_next_step_mismatch")

    if design_report.get("version") != "0.4.13.9":
        blockers.append("design_report_version_mismatch")
    if design_report.get("schema_kind") != "ingestion_metadata_patch_post_patch_rebuild_dry_run_design":
        blockers.append("design_report_schema_mismatch")
    if design_summary.get("status") != "ready_for_post_patch_rebuild_dry_run_design_gate":
        blockers.append("design_report_not_ready")
    if design_summary.get("allowed_next_step") != "post_patch_rebuild_dry_run_design_gate":
        blockers.append("design_report_next_step_mismatch")

    if design_gate_report.get("version") != "0.4.13.10":
        blockers.append("design_gate_report_version_mismatch")
    if design_gate_report.get("schema_kind") != "ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate":
        blockers.append("design_gate_report_schema_mismatch")
    if gate_summary.get("status") != "passed":
        blockers.append("design_gate_report_not_passed")
    if gate_summary.get("allowed_next_step") != "post_patch_rebuild_dry_run_runner":
        blockers.append("design_gate_next_step_mismatch")

    for report_name, summary in [
        ("source_patch", source_summary),
        ("design", design_summary),
        ("design_gate", gate_summary),
    ]:
        if summary.get("qdrant_write_allowed") is not False:
            blockers.append(f"{report_name}:qdrant_write_requested")
        if summary.get("rebuild_allowed") is not False:
            blockers.append(f"{report_name}:collection_rebuild_requested")
        if summary.get("full_eval") != "not_run":
            blockers.append(f"{report_name}:rag_or_llm_call_requested")

    return blockers


def run_sample(sample: dict[str, Any]) -> dict[str, Any]:
    post_patch_base_docs = build_current_documents(sample)
    before_docs = assign_ids(simulate_pre_patch_documents(post_patch_base_docs))
    after_docs = assign_ids(copy.deepcopy(post_patch_base_docs))
    rows, blockers = compare_documents(sample["sample_id"], before_docs, after_docs)

    return {
        "sample_id": sample["sample_id"],
        "shape": sample["shape"],
        "article_part_count": len(sample["parts"]),
        "document_count": len(after_docs),
        "rows": rows,
        "blockers": blockers,
    }


def build_report(
    source_patch_path: Path = DEFAULT_SOURCE_PATCH_REPORT_PATH,
    design_path: Path = DEFAULT_DESIGN_PATH,
    design_gate_path: Path = DEFAULT_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    source_patch_report = load_json(source_patch_path)
    design_report = load_json(design_path)
    design_gate_report = load_json(design_gate_path)
    blockers = prerequisite_blockers(source_patch_report, design_report, design_gate_report)

    sample_results = [run_sample(sample) for sample in SAMPLE_SCENARIOS]
    rows = [row for sample in sample_results for row in sample["rows"]]
    sample_blockers = [blocker for sample in sample_results for blocker in sample["blockers"]]
    blockers.extend(sample_blockers)

    metadata_presence_rows = sum(1 for row in rows if row["chunk_index"] is not None and row["chunk_count"] is not None)
    expected_id_drift_rows = sum(1 for row in rows if row["chunk_id_drift"] and row["qdrant_point_id_drift"])
    forbidden_drift_count = sum(
        1
        for row in rows
        if not row["content_stable"] or not row["citation_stable"] or not row["block_metadata_stable"]
    )
    status = "passed" if not blockers else "blocked"

    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_post_patch_rebuild_dry_run",
        "scope": "local saved-report post-patch rebuild dry-run only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "source_patch_report": {
                "path": str(source_patch_path),
                "version": source_patch_report.get("version"),
                "schema_kind": source_patch_report.get("schema_kind"),
                "status": as_dict(source_patch_report.get("summary")).get("status"),
            },
            "post_patch_rebuild_dry_run_design": {
                "path": str(design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": as_dict(design_report.get("summary")).get("status"),
            },
            "post_patch_rebuild_dry_run_design_gate": {
                "path": str(design_gate_path),
                "version": design_gate_report.get("version"),
                "schema_kind": design_gate_report.get("schema_kind"),
                "status": as_dict(design_gate_report.get("summary")).get("status"),
            },
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "sample_count": len(sample_results),
            "row_count": len(rows),
            "metadata_presence_rows": metadata_presence_rows,
            "expected_id_drift_rows": expected_id_drift_rows,
            "forbidden_drift_count": forbidden_drift_count,
            "blocking_condition_count": len(blockers),
            "allowed_next_step": "post_patch_rebuild_dry_run_runner_gate" if status == "passed" else "blocked",
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
        },
        "sample_strategy": {
            "sample_count": len(SAMPLE_SCENARIOS),
            "required_shapes": [sample["shape"] for sample in SAMPLE_SCENARIOS],
            "case_id_dependency": "disallowed",
            "hidden_seed_dependency": "disallowed",
        },
        "comparison_contract": {
            "before_state": "simulated_pre_patch_metadata_without_chunk_index_or_chunk_count",
            "after_state": "current_build_article_documents_output",
            "expected_drifts": ["chunk_index_added", "chunk_count_added", "chunk_id", "qdrant_point_id"],
            "forbidden_drifts": ["page_content", "citation", "block_type", "paragraph_no", "item_no", "item_label", "parent_article_id"],
        },
        "sample_results": sample_results,
        "rows": rows,
        "blockers": blockers,
        "handoff": {
            "next_allowed_step": "gate this post-patch rebuild dry-run runner" if status == "passed" else "resolve runner blockers",
            "not_allowed_yet": [
                "write Qdrant",
                "rebuild collection",
                "call rag_query",
                "call embedding or LLM services",
                "run full eval as a substitute for this dry-run",
                "modify ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.11 Post-Patch Rebuild Dry-Run Runner",
        "",
        "本报告只执行本地、只读、确定性样本 dry-run。它读取已保存的 v0.4.13.8/0.4.13.9/v0.4.13.10 报告，并调用当前 `build_article_documents` 生成 post-patch 文档；不写 Qdrant、不 rebuild collection、不调用 RAG/embedding/LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 样本数: `{summary.get('sample_count')}`",
        f"- 对比行数: `{summary.get('row_count')}`",
        f"- 边界元数据存在行数: `{summary.get('metadata_presence_rows')}`",
        f"- 预期 ID 漂移行数: `{summary.get('expected_id_drift_rows')}`",
        f"- 禁止漂移行数: `{summary.get('forbidden_drift_count')}`",
        f"- 阻断条件数: `{summary.get('blocking_condition_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        "",
        "## 样本",
        "",
    ]
    for sample in report.get("sample_results", []):
        lines.extend(
            [
                f"### {sample.get('sample_id')}",
                "",
                f"- 形态: `{sample.get('shape')}`",
                f"- 文档数: `{sample.get('document_count')}`",
                f"- 阻断条件: `{sample.get('blockers')}`",
                "",
            ]
        )
    lines.extend(["## 边界", ""])
    for key, value in as_dict(report.get("guardrails")).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## 仍不允许", ""])
    for item in as_dict(report.get("handoff")).get("not_allowed_yet", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the v0.4.13.11 post-patch rebuild dry-run runner.")
    parser.add_argument("--source-patch", type=Path, default=DEFAULT_SOURCE_PATCH_REPORT_PATH)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN_PATH)
    parser.add_argument("--design-gate", type=Path, default=DEFAULT_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.source_patch, args.design, args.design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Post-patch rebuild dry-run runner: "
        f"{summary.get('status')}, rows={summary.get('row_count')}, "
        f"blockers={summary.get('blocking_condition_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
