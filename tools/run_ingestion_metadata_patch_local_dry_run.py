"""Run the v0.4.13.4 local ingestion metadata patch dry-run.

The runner uses only small in-memory article samples. It imports the current
article document builder, simulates the intended boundary metadata patch on
cloned documents, and reports expected stable ID drift without touching Qdrant.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.13.4"

DEFAULT_DRY_RUN_DESIGN_PATH = legacy_report_path("ingestion_metadata_patch_dry_run_design_report.json")
DEFAULT_DRY_RUN_DESIGN_GATE_PATH = legacy_report_path("ingestion_metadata_patch_dry_run_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_local_dry_run_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_local_dry_run_v0.4.13.4.md")

EXPECTED_METADATA_DRIFT = {"chunk_index", "chunk_count", "chunk_id", "qdrant_point_id"}
FORBIDDEN_METADATA_DRIFT = {
    "citation",
    "block_type",
    "paragraph_no",
    "item_no",
    "item_label",
    "parent_article_id",
}

GUARDRAILS = {
    "local_in_memory_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "knowledge_base_fulltext_scan": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "implementation_allowed": False,
    "code_patch_authorized": False,
    "retrieval_logic_change_allowed": False,
    "ingestion_source_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
}

SAMPLE_SCENARIOS = [
    {
        "scenario_id": "single_paragraph_article",
        "article_no": 913401,
        "article": "第九十一万三千四百零一条",
        "parts": ["经营者应当依法履行个人信息保护义务。"],
        "expected_blocks": {"article": 1, "paragraph": 1, "item": 0},
    },
    {
        "scenario_id": "multi_paragraph_article",
        "article_no": 913402,
        "article": "第九十一万三千四百零二条",
        "parts": [
            "个人信息处理者应当按照约定处理个人信息。",
            "处理目的、方式发生变化的，应当重新告知相关主体。",
        ],
        "expected_blocks": {"article": 1, "paragraph": 2, "item": 0},
    },
    {
        "scenario_id": "paragraph_with_items",
        "article_no": 913403,
        "article": "第九十一万三千四百零三条",
        "parts": [
            "（一）明确处理目的、处理方式和保存期限；",
            "（二）建立访问控制、日志审计和删除机制。",
        ],
        "expected_blocks": {"article": 1, "paragraph": 0, "item": 2},
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


def _article_metadata(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "v0.4.13.4 local dry-run sample law",
        "law_name": "v0.4.13.4 local dry-run sample law",
        "document_type": "法律法规",
        "law_level": "法律",
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

    return build_article_documents(sample["parts"], _article_metadata(sample))


def assign_ids(documents):
    from src.rag.ingestion import assign_stable_chunk_ids

    return assign_stable_chunk_ids(documents)


def simulate_boundary_metadata_patch(documents):
    patched = copy.deepcopy(documents)
    child_docs = [doc for doc in patched if doc.metadata.get("block_type") in {"paragraph", "item"}]
    child_count = len(child_docs)

    child_index = 0
    for doc in patched:
        block_type = doc.metadata.get("block_type")
        if block_type == "article":
            doc.metadata["chunk_index"] = 1
            doc.metadata["chunk_count"] = 1
        elif block_type in {"paragraph", "item"}:
            child_index += 1
            doc.metadata["chunk_index"] = child_index
            doc.metadata["chunk_count"] = child_count
    return patched


def _metadata_changed(pre: dict[str, Any], post: dict[str, Any], key: str) -> bool:
    return pre.get(key) != post.get(key)


def compare_documents(scenario_id: str, pre_docs, post_docs) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    if len(pre_docs) != len(post_docs):
        blockers.append(f"{scenario_id}:document_count_mismatch")

    for index, (pre_doc, post_doc) in enumerate(zip(pre_docs, post_docs), start=1):
        forbidden_drift = [
            key
            for key in sorted(FORBIDDEN_METADATA_DRIFT)
            if _metadata_changed(pre_doc.metadata, post_doc.metadata, key)
        ]
        content_changed = pre_doc.page_content != post_doc.page_content
        citation_changed = _metadata_changed(pre_doc.metadata, post_doc.metadata, "citation")
        missing_post_boundary = post_doc.metadata.get("chunk_index") is None or post_doc.metadata.get("chunk_count") is None

        if content_changed:
            blockers.append(f"{scenario_id}:{index}:content_changed")
        if citation_changed:
            blockers.append(f"{scenario_id}:{index}:citation_changed")
        if forbidden_drift:
            blockers.append(f"{scenario_id}:{index}:forbidden_drift")
        if missing_post_boundary:
            blockers.append(f"{scenario_id}:{index}:missing_post_boundary_metadata")

        rows.append(
            {
                "scenario_id": scenario_id,
                "doc_index": index,
                "block_type": post_doc.metadata.get("block_type"),
                "pre_chunk_index": pre_doc.metadata.get("chunk_index"),
                "post_chunk_index": post_doc.metadata.get("chunk_index"),
                "pre_chunk_count": pre_doc.metadata.get("chunk_count"),
                "post_chunk_count": post_doc.metadata.get("chunk_count"),
                "content_changed": content_changed,
                "citation_changed": citation_changed,
                "chunk_id_changed": _metadata_changed(pre_doc.metadata, post_doc.metadata, "chunk_id"),
                "qdrant_point_id_changed": _metadata_changed(pre_doc.metadata, post_doc.metadata, "qdrant_point_id"),
                "forbidden_drift": forbidden_drift,
                "missing_post_boundary_metadata": missing_post_boundary,
            }
        )
    return rows, blockers


def _block_counts(documents) -> dict[str, int]:
    counts = Counter(doc.metadata.get("block_type") for doc in documents)
    return {"article": counts.get("article", 0), "paragraph": counts.get("paragraph", 0), "item": counts.get("item", 0)}


def run_sample(sample: dict[str, Any]) -> dict[str, Any]:
    scenario_id = sample["scenario_id"]
    pre_base_docs = build_current_documents(sample)
    post_base_docs = simulate_boundary_metadata_patch(build_current_documents(sample))
    pre_docs = assign_ids(copy.deepcopy(pre_base_docs))
    post_docs = assign_ids(post_base_docs)
    rows, blockers = compare_documents(scenario_id, pre_docs, post_docs)

    pre_counts = _block_counts(pre_docs)
    post_counts = _block_counts(post_docs)
    if post_counts != sample["expected_blocks"]:
        blockers.append(f"{scenario_id}:unexpected_post_block_counts")

    return {
        "scenario_id": scenario_id,
        "article_parts_shape": ["item" if part.startswith("（") else "paragraph" for part in sample["parts"]],
        "expected_blocks": sample["expected_blocks"],
        "pre_block_counts": pre_counts,
        "post_block_counts": post_counts,
        "pre_document_count": len(pre_docs),
        "post_document_count": len(post_docs),
        "rows": rows,
        "blockers": blockers,
    }


def build_report(
    dry_run_design_path: Path = DEFAULT_DRY_RUN_DESIGN_PATH,
    dry_run_design_gate_path: Path = DEFAULT_DRY_RUN_DESIGN_GATE_PATH,
) -> dict[str, Any]:
    design_report = load_json(dry_run_design_path)
    gate_report = load_json(dry_run_design_gate_path)
    gate_summary = as_dict(gate_report.get("summary"))
    prerequisite_blockers = []
    if design_report.get("version") != "0.4.13.2":
        prerequisite_blockers.append("dry_run_design_version_mismatch")
    if design_report.get("schema_kind") != "ingestion_metadata_patch_dry_run_design":
        prerequisite_blockers.append("dry_run_design_schema_mismatch")
    if gate_report.get("version") != "0.4.13.3":
        prerequisite_blockers.append("dry_run_design_gate_version_mismatch")
    if gate_summary.get("status") != "passed":
        prerequisite_blockers.append("dry_run_design_gate_not_passed")
    if gate_summary.get("allowed_next_step") != "ingestion_metadata_patch_local_dry_run_runner":
        prerequisite_blockers.append("unexpected_gate_next_step")

    sample_results = [run_sample(sample) for sample in SAMPLE_SCENARIOS]
    rows = [row for sample in sample_results for row in sample["rows"]]
    sample_blockers = [blocker for sample in sample_results for blocker in sample["blockers"]]
    blockers = prerequisite_blockers + sample_blockers

    metadata_drift_count = sum(
        1
        for row in rows
        if row["pre_chunk_index"] != row["post_chunk_index"] or row["pre_chunk_count"] != row["post_chunk_count"]
    )
    chunk_id_drift_count = sum(1 for row in rows if row["chunk_id_changed"])
    qdrant_point_id_drift_count = sum(1 for row in rows if row["qdrant_point_id_changed"])
    forbidden_drift_count = sum(1 for row in rows if row["forbidden_drift"])
    status = "passed" if not blockers else "failed"

    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_local_dry_run",
        "scope": "local in-memory ingestion metadata patch simulation only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "dry_run_design": {
                "path": str(dry_run_design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
            },
            "dry_run_design_gate": {
                "path": str(dry_run_design_gate_path),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
                "status": gate_summary.get("status"),
                "allowed_next_step": gate_summary.get("allowed_next_step"),
            },
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "sample_count": len(sample_results),
            "pre_document_count": sum(sample["pre_document_count"] for sample in sample_results),
            "post_document_count": sum(sample["post_document_count"] for sample in sample_results),
            "metadata_drift_count": metadata_drift_count,
            "chunk_id_drift_count": chunk_id_drift_count,
            "qdrant_point_id_drift_count": qdrant_point_id_drift_count,
            "forbidden_drift_count": forbidden_drift_count,
            "blocking_condition_count": len(blockers),
            "allowed_next_step": "ingestion_metadata_patch_local_dry_run_gate" if status == "passed" else "blocked",
            "implementation_allowed": False,
            "qdrant_write_allowed": False,
            "retrieval_logic_change_allowed": False,
            "full_eval": "not_run",
        },
        "expected_metadata_drift": sorted(EXPECTED_METADATA_DRIFT),
        "forbidden_metadata_drift": sorted(FORBIDDEN_METADATA_DRIFT),
        "sample_results": sample_results,
        "rows": rows,
        "blockers": blockers,
        "handoff": {
            "next_allowed_step": "gate this local dry-run report" if status == "passed" else "resolve local dry-run blockers",
            "not_allowed_yet": [
                "patch src/rag/ingestion.py",
                "write Qdrant",
                "rebuild collection",
                "modify rag_query or rules",
                "run full eval as a substitute for local dry-run gate",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.4 Ingestion Metadata Patch Local Dry-Run",
        "",
        "This report runs a local in-memory simulation only. It does not patch ingestion, write Qdrant, or run RAG.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Samples: `{summary.get('sample_count')}`",
        f"- Documents: `{summary.get('pre_document_count')}` pre / `{summary.get('post_document_count')}` post",
        f"- Boundary metadata drift rows: `{summary.get('metadata_drift_count')}`",
        f"- Chunk ID drift rows: `{summary.get('chunk_id_drift_count')}`",
        f"- Qdrant point ID drift rows: `{summary.get('qdrant_point_id_drift_count')}`",
        f"- Forbidden drift rows: `{summary.get('forbidden_drift_count')}`",
        f"- Allowed next step: `{summary.get('allowed_next_step')}`",
        "",
        "## Samples",
        "",
    ]
    for sample in report.get("sample_results", []):
        lines.extend(
            [
                f"### {sample.get('scenario_id')}",
                "",
                f"- Pre block counts: `{sample.get('pre_block_counts')}`",
                f"- Post block counts: `{sample.get('post_block_counts')}`",
                f"- Blockers: `{sample.get('blockers')}`",
                "",
            ]
        )
    lines.extend(["## Guardrails", ""])
    for key, value in as_dict(report.get("guardrails")).items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the v0.4.13.4 ingestion metadata patch local dry-run.")
    parser.add_argument("--dry-run-design", type=Path, default=DEFAULT_DRY_RUN_DESIGN_PATH)
    parser.add_argument("--dry-run-design-gate", type=Path, default=DEFAULT_DRY_RUN_DESIGN_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.dry_run_design, args.dry_run_design_gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Ingestion metadata patch local dry-run: "
        f"{summary.get('status')}, drift={summary.get('metadata_drift_count')}, "
        f"forbidden={summary.get('forbidden_drift_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
