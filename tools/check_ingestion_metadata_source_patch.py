"""检查 v0.4.13.8 最小入库元数据源码补丁。

本检查器只导入 ingestion helper 并读取 v0.4.13.7 gate report。
它不写入 Qdrant、不重建 collection、不调用 RAG，也不运行 eval。
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

from tools._shared.layout import legacy_report_path


VERSION = "0.4.13.8"

DEFAULT_GATE_PATH = legacy_report_path("ingestion_metadata_patch_actual_design_gate_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_source_patch_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_source_patch_v0.4.13.8.md")

FORBIDDEN_FILES = [
    "src/rag/retriever.py",
    "config/rag_anchor_rules.json",
    "config/risk_payload_supplement_rules.json",
    "tests/rag_eval_cases.json",
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


def article_metadata() -> dict[str, Any]:
    return {
        "source": "v0.4.13.8 source patch sample law",
        "law_name": "v0.4.13.8 source patch sample law",
        "document_type": "法律法规",
        "law_level": "法律",
        "authority_level": "source_patch_check",
        "jurisdiction": "source_patch_check",
        "issuing_authority": "source_patch_check",
        "category": "source_patch_check",
        "version": VERSION,
        "type": "article",
        "article": "第九十一万三千四百零八条",
        "article_no": 913408,
    }


def source_patch_observations() -> dict[str, Any]:
    from src.rag.ingestion import build_article_documents, build_standard_section_documents

    article_parts = [
        "个人信息处理者应当按照约定处理个人信息。",
        "（一）明确处理目的、处理方式和保存期限；",
        "（二）建立访问控制、日志审计和删除机制。",
    ]
    article_docs = build_article_documents(article_parts, article_metadata())
    parent = article_docs[0]
    children = article_docs[1:]

    standard_docs = build_standard_section_documents(
        {
            "heading": "5.4 收集个人信息时的授权同意",
            "section_no": "5.4",
            "section_title": "收集个人信息时的授权同意",
            "section_level": 2,
            "chapter": "5 个人信息的收集",
            "heading_level": "section",
        },
        ["收集个人信息，应向个人信息主体告知收集、使用个人信息的目的、方式和范围等规则。"],
        {
            "source": "信息安全技术 source patch 示例标准",
            "law_name": "信息安全技术 source patch 示例标准",
            "document_type": "标准",
            "law_level": "国家标准",
            "type": "article",
        },
    )
    standard_section = next(doc for doc in standard_docs if doc.metadata.get("block_type") == "standard_section")
    standard_heading = next(doc for doc in standard_docs if doc.metadata.get("block_type") == "heading")

    return {
        "article_document_count": len(article_docs),
        "parent": {
            "block_type": parent.metadata.get("block_type"),
            "chunk_index": parent.metadata.get("chunk_index"),
            "chunk_count": parent.metadata.get("chunk_count"),
            "page_content": parent.page_content,
            "citation": parent.metadata.get("citation"),
        },
        "children": [
            {
                "block_type": doc.metadata.get("block_type"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "chunk_count": doc.metadata.get("chunk_count"),
                "paragraph_no": doc.metadata.get("paragraph_no"),
                "item_label": doc.metadata.get("item_label"),
                "page_content": doc.page_content,
                "citation": doc.metadata.get("citation"),
            }
            for doc in children
        ],
        "standard_section": {
            "heading_has_chunk_index": "chunk_index" in standard_heading.metadata,
            "block_type": standard_section.metadata.get("block_type"),
            "chunk_index": standard_section.metadata.get("chunk_index"),
            "chunk_count": standard_section.metadata.get("chunk_count"),
            "paragraph_no": standard_section.metadata.get("paragraph_no"),
        },
    }


def build_checks(gate_report: dict[str, Any], observations: dict[str, Any]) -> list[dict[str, Any]]:
    gate_summary = as_dict(gate_report.get("summary"))
    parent = as_dict(observations.get("parent"))
    children = observations.get("children") if isinstance(observations.get("children"), list) else []
    standard = as_dict(observations.get("standard_section"))

    expected_child_count = 3
    checks = [
        (
            "gate_version",
            gate_report.get("version") == "0.4.13.7",
            "Source patch must follow v0.4.13.7 gate.",
        ),
        (
            "gate_status",
            gate_summary.get("status") == "passed",
            "Source patch gate must have passed.",
        ),
        (
            "gate_next_step",
            gate_summary.get("allowed_next_step") == "minimal_ingestion_metadata_source_patch",
            "Gate must open only the minimal source patch.",
        ),
        (
            "parent_block_type",
            parent.get("block_type") == "article",
            "Parent document must remain article block.",
        ),
        (
            "parent_chunk_index",
            parent.get("chunk_index") == 1,
            "Parent article chunk_index must be 1.",
        ),
        (
            "parent_chunk_count",
            parent.get("chunk_count") == 1,
            "Parent article chunk_count must be 1.",
        ),
        (
            "child_document_count",
            len(children) == expected_child_count,
            "Each article_part must emit one child document.",
        ),
        (
            "child_chunk_indexes",
            [child.get("chunk_index") for child in children] == [1, 2, 3],
            "Child chunk_index must follow 1-based article_parts order.",
        ),
        (
            "child_chunk_counts",
            [child.get("chunk_count") for child in children] == [expected_child_count] * expected_child_count,
            "Child chunk_count must equal len(article_parts).",
        ),
        (
            "child_block_types",
            [child.get("block_type") for child in children] == ["paragraph", "item", "item"],
            "Patch must not change paragraph/item block typing.",
        ),
        (
            "content_stable",
            parent.get("page_content") and all(child.get("page_content") for child in children),
            "Patch must preserve emitted content.",
        ),
        (
            "citation_stable",
            parent.get("citation") and all(child.get("citation") for child in children),
            "Patch must preserve citation generation.",
        ),
        (
            "standard_heading_unchanged",
            standard.get("heading_has_chunk_index") is False,
            "Standard heading chunk metadata behavior must remain unchanged.",
        ),
        (
            "standard_section_unchanged",
            standard.get("block_type") == "standard_section"
            and standard.get("chunk_index") == 1
            and standard.get("chunk_count") == 1
            and standard.get("paragraph_no") == 1,
            "Standard section chunk metadata behavior must remain unchanged.",
        ),
        (
            "qdrant_blocked",
            gate_summary.get("qdrant_write_allowed") is False and gate_summary.get("rebuild_allowed") is False,
            "Qdrant write and rebuild remain blocked in this version.",
        ),
    ]
    return [
        {"id": check_id, "passed": bool(passed), "details": details}
        for check_id, passed, details in checks
    ]


def build_report(gate_path: Path = DEFAULT_GATE_PATH) -> dict[str, Any]:
    gate_report = load_json(gate_path)
    observations = source_patch_observations()
    checks = build_checks(gate_report, observations)
    failed = [check for check in checks if not check["passed"]]
    status = "passed" if not failed else "failed"

    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_source_patch_check",
        "scope": "minimal ingestion metadata source patch check",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "actual_design_gate": {
                "path": str(gate_path),
                "version": gate_report.get("version"),
                "schema_kind": gate_report.get("schema_kind"),
                "status": as_dict(gate_report.get("summary")).get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "post_patch_rebuild_dry_run_design" if status == "passed" else "blocked",
            "implementation_completed": status == "passed",
            "retrieval_logic_change_allowed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
        },
        "patch_boundary": {
            "modified_runtime_target": "src/rag/ingestion.py::build_article_documents",
            "added_metadata_fields": ["chunk_index", "chunk_count"],
            "forbidden_files": FORBIDDEN_FILES,
        },
        "observations": observations,
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.8 入库元数据源码补丁",
        "",
        "本报告只验证最小源码补丁。它不写入 Qdrant、不重建 collection、不运行 RAG，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败检查项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 检查项",
        "",
    ]
    for check in report.get("checks", []):
        lines.append(f"- `{check.get('id')}`: `{check.get('passed')}`")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.8 ingestion metadata source patch.")
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.gate)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Ingestion metadata source patch check: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
