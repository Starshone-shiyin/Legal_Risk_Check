"""Build the v0.4.13.9 post-patch rebuild dry-run design.

This design reads only the v0.4.13.8 source patch report. It defines the
future rebuild dry-run contract without writing Qdrant, rebuilding collections,
calling RAG, embedding models, LLMs, or full eval.
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


VERSION = "0.4.13.9"

DEFAULT_SOURCE_PATCH_REPORT_PATH = legacy_report_path("ingestion_metadata_source_patch_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_v0.4.13.9.md")

GUARDRAILS = {
    "design_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "implementation_allowed": False,
    "runner_creation_allowed": False,
    "rebuild_allowed": False,
    "retrieval_logic_change_allowed": False,
    "ingestion_source_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

DRY_RUN_DESIGN = {
    "future_runner_name": "run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py",
    "runner_status": "not_created_in_this_version",
    "allowed_inputs": [
        "saved v0.4.13.8 source patch report",
        "small deterministic local article_parts samples",
        "current build_article_documents output",
    ],
    "forbidden_inputs": [
        "Qdrant collection writes",
        "Qdrant collection rebuild",
        "production collection point mutation",
        "rag_query output",
        "embedding or LLM calls",
        "full eval reports as a substitute for metadata dry-run rows",
    ],
    "sample_strategy": {
        "minimum_samples": 3,
        "required_shapes": [
            "single paragraph article",
            "paragraph plus item article",
            "multi-paragraph article",
        ],
        "case_id_dependency": "disallowed",
        "hidden_seed_dependency": "disallowed",
    },
    "comparison_fields": {
        "must_be_present_after_patch": ["chunk_index", "chunk_count"],
        "expected_to_change_if_rebuild_materializes": ["chunk_id", "qdrant_point_id"],
        "must_remain_stable": [
            "page_content",
            "citation",
            "block_type",
            "paragraph_no",
            "item_no",
            "item_label",
            "parent_article_id",
        ],
    },
    "expected_drift": [
        "chunk_id drift may occur because stable identity includes chunk_index",
        "qdrant_point_id drift may occur because it is derived from stable identity",
    ],
    "forbidden_drift": [
        "content_drift",
        "citation_drift",
        "block_type_drift",
        "paragraph_or_item_number_drift",
        "standard_section_behavior_drift",
        "retrieval_logic_drift",
        "anchor_or_risk_rule_drift",
        "eval_case_or_fixture_drift",
    ],
}

OUTPUT_CONTRACT = {
    "summary_fields": [
        "status",
        "sample_count",
        "row_count",
        "metadata_presence_rows",
        "expected_id_drift_rows",
        "forbidden_drift_count",
        "blocking_condition_count",
        "allowed_next_step",
        "qdrant_write_allowed",
        "rebuild_allowed",
        "full_eval",
    ],
    "row_fields": [
        "sample_id",
        "document_role",
        "block_type",
        "before_metadata",
        "after_metadata",
        "chunk_index",
        "chunk_count",
        "chunk_id_drift",
        "qdrant_point_id_drift",
        "content_stable",
        "citation_stable",
        "block_metadata_stable",
        "detected_drifts",
        "blocking_conditions",
    ],
    "blocking_conditions": [
        "source_patch_report_missing_or_failed",
        "chunk_boundary_metadata_missing",
        "forbidden_content_or_citation_drift",
        "unexpected_standard_section_drift",
        "qdrant_write_requested",
        "collection_rebuild_requested",
        "rag_or_llm_call_requested",
        "eval_case_or_fixture_mutation_requested",
    ],
}


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


def source_patch_blockers(source_patch_report: dict[str, Any]) -> list[str]:
    summary = as_dict(source_patch_report.get("summary"))
    blockers = []
    if source_patch_report.get("version") != "0.4.13.8":
        blockers.append("source_patch_report_version_mismatch")
    if source_patch_report.get("schema_kind") != "ingestion_metadata_source_patch_check":
        blockers.append("source_patch_report_schema_mismatch")
    if summary.get("status") != "passed":
        blockers.append("source_patch_report_not_passed")
    if summary.get("failed_check_count") != 0:
        blockers.append("source_patch_failed_checks_present")
    if summary.get("allowed_next_step") != "post_patch_rebuild_dry_run_design":
        blockers.append("unexpected_source_patch_next_step")
    if summary.get("qdrant_write_allowed") is not False:
        blockers.append("source_patch_qdrant_write_not_blocked")
    if summary.get("rebuild_allowed") is not False:
        blockers.append("source_patch_rebuild_not_blocked")
    if summary.get("full_eval") != "not_run":
        blockers.append("source_patch_full_eval_drift")
    return blockers


def build_report(source_patch_path: Path = DEFAULT_SOURCE_PATCH_REPORT_PATH) -> dict[str, Any]:
    source_patch_report = load_json(source_patch_path)
    blockers = source_patch_blockers(source_patch_report)
    status = "ready_for_post_patch_rebuild_dry_run_design_gate" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_post_patch_rebuild_dry_run_design",
        "scope": "post-patch rebuild dry-run design only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "source_patch_report": {
                "path": str(source_patch_path),
                "version": source_patch_report.get("version"),
                "schema_kind": source_patch_report.get("schema_kind"),
                "status": as_dict(source_patch_report.get("summary")).get("status"),
                "allowed_next_step": as_dict(source_patch_report.get("summary")).get("allowed_next_step"),
            }
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "allowed_next_step": "post_patch_rebuild_dry_run_design_gate" if status != "blocked" else "blocked",
            "implementation_allowed": False,
            "runner_creation_allowed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "retrieval_logic_change_allowed": False,
            "full_eval": "not_run",
            "source_patch_status": as_dict(source_patch_report.get("summary")).get("status"),
            "blockers": blockers,
        },
        "dry_run_design": DRY_RUN_DESIGN,
        "output_contract": OUTPUT_CONTRACT,
        "handoff": {
            "next_allowed_step": "gate this post-patch rebuild dry-run design" if status != "blocked" else "resolve design blockers",
            "not_allowed_yet": [
                "create the rebuild dry-run runner",
                "write Qdrant",
                "rebuild collection",
                "modify ingestion or retrieval source",
                "modify anchors, risk rules, scenario registry, fixtures, or eval cases",
                "run full eval as a substitute for the rebuild dry-run contract",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    design = as_dict(report.get("dry_run_design"))
    output_contract = as_dict(report.get("output_contract"))
    lines = [
        "# v0.4.13.9 补丁后 rebuild dry-run 设计",
        "",
        "本报告只设计未来的补丁后 rebuild dry-run。它不写入 Qdrant、不重建 collection、不调用 RAG、不调用 embedding 模型、不调用 LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否允许实现: `{summary.get('implementation_allowed')}`",
        f"- 是否允许创建 runner: `{summary.get('runner_creation_allowed')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 未来 Runner 设计",
        "",
        f"- 未来 runner: `{design.get('future_runner_name')}`",
        f"- runner 状态: `{design.get('runner_status')}`",
        f"- 样本策略: `{design.get('sample_strategy')}`",
        "",
        "## 对比字段",
        "",
    ]
    comparison_fields = as_dict(design.get("comparison_fields"))
    for key, values in comparison_fields.items():
        lines.append(f"- `{key}`: `{values}`")
    lines.extend(["", "## 输出契约", ""])
    lines.append(f"- Summary fields: `{output_contract.get('summary_fields')}`")
    lines.append(f"- Row fields: `{output_contract.get('row_fields')}`")
    lines.append(f"- Blocking conditions: `{output_contract.get('blocking_conditions')}`")
    lines.extend(["", "## 仍不允许", ""])
    for item in as_dict(report.get("handoff")).get("not_allowed_yet", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.9 post-patch rebuild dry-run design.")
    parser.add_argument("--source-patch", type=Path, default=DEFAULT_SOURCE_PATCH_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.source_patch)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Post-patch rebuild dry-run design: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
