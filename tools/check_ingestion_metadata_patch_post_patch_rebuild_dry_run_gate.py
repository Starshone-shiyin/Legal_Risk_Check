"""Check the v0.4.13.12 post-patch rebuild dry-run runner gate.

The gate validates only the saved v0.4.13.11 runner report. It does not rerun
the runner, access Qdrant, rebuild collections, call RAG, call embeddings or
LLMs, run full eval, or mutate ingestion/retrieval/rules/eval artifacts.
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


VERSION = "0.4.13.12"

DEFAULT_RUNNER_REPORT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md")

REQUIRED_GUARDRAILS = {
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

REQUIRED_SAMPLE_SHAPES = {
    "single paragraph article",
    "paragraph plus item article",
    "multi-paragraph article",
}

REQUIRED_SAMPLE_DOCUMENT_COUNTS = {
    "single_paragraph_article": 2,
    "paragraph_plus_item_article": 4,
    "multi_paragraph_article": 3,
}

REQUIRED_DETECTED_DRIFTS = {
    "expected_chunk_id_drift",
    "expected_qdrant_point_id_drift",
    "expected_chunk_index_added",
    "expected_chunk_count_added",
}

REQUIRED_COMPARISON_FIELDS = {
    "expected_drifts": {"chunk_index_added", "chunk_count_added", "chunk_id", "qdrant_point_id"},
    "forbidden_drifts": {
        "page_content",
        "citation",
        "block_type",
        "paragraph_no",
        "item_no",
        "item_label",
        "parent_article_id",
    },
}

REQUIRED_HANDOFF_BLOCKS = {
    "write Qdrant",
    "rebuild collection",
    "call rag_query",
    "call embedding or LLM services",
    "run full eval as a substitute for this dry-run",
    "modify ingestion, retriever, rerank, prompt, anchors, risk rules, scenario registry, fixtures, or eval cases",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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


def check_row(check_id: str, passed: bool, details: str) -> dict[str, Any]:
    return {"check_id": check_id, "passed": passed, "details": details}


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in as_list(report.get("rows")) if isinstance(row, dict)]


def _sample_results(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [sample for sample in as_list(report.get("sample_results")) if isinstance(sample, dict)]


def _has_required_lineage(inputs: dict[str, Any]) -> bool:
    source_patch = as_dict(inputs.get("source_patch_report"))
    design = as_dict(inputs.get("post_patch_rebuild_dry_run_design"))
    design_gate = as_dict(inputs.get("post_patch_rebuild_dry_run_design_gate"))
    return (
        source_patch.get("version") == "0.4.13.8"
        and source_patch.get("schema_kind") == "ingestion_metadata_source_patch_check"
        and source_patch.get("status") == "passed"
        and design.get("version") == "0.4.13.9"
        and design.get("schema_kind") == "ingestion_metadata_patch_post_patch_rebuild_dry_run_design"
        and design.get("status") == "ready_for_post_patch_rebuild_dry_run_design_gate"
        and design_gate.get("version") == "0.4.13.10"
        and design_gate.get("schema_kind") == "ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate"
        and design_gate.get("status") == "passed"
    )


def _has_expected_summary(summary: dict[str, Any], row_count: int) -> bool:
    return (
        summary.get("status") == "passed"
        and summary.get("sample_count") == 3
        and summary.get("row_count") == row_count == 9
        and summary.get("metadata_presence_rows") == row_count
        and summary.get("expected_id_drift_rows") == row_count
        and summary.get("forbidden_drift_count") == 0
        and summary.get("blocking_condition_count") == 0
        and summary.get("allowed_next_step") == "post_patch_rebuild_dry_run_runner_gate"
        and summary.get("qdrant_write_allowed") is False
        and summary.get("rebuild_allowed") is False
        and summary.get("full_eval") == "not_run"
    )


def _has_expected_samples(report: dict[str, Any]) -> bool:
    sample_strategy = as_dict(report.get("sample_strategy"))
    sample_results = _sample_results(report)
    shapes = set(as_list(sample_strategy.get("required_shapes")))
    sample_counts = {sample.get("sample_id"): sample.get("document_count") for sample in sample_results}
    return (
        sample_strategy.get("sample_count") == 3
        and REQUIRED_SAMPLE_SHAPES.issubset(shapes)
        and sample_strategy.get("case_id_dependency") == "disallowed"
        and sample_strategy.get("hidden_seed_dependency") == "disallowed"
        and all(sample_counts.get(sample_id) == count for sample_id, count in REQUIRED_SAMPLE_DOCUMENT_COUNTS.items())
        and all(sample.get("blockers") == [] for sample in sample_results)
    )


def _rows_are_stable(rows: list[dict[str, Any]]) -> bool:
    return all(
        row.get("chunk_index") is not None
        and row.get("chunk_count") is not None
        and as_dict(row.get("after_metadata")).get("chunk_index") is not None
        and as_dict(row.get("after_metadata")).get("chunk_count") is not None
        and row.get("chunk_id_drift") is True
        and row.get("qdrant_point_id_drift") is True
        and row.get("content_stable") is True
        and row.get("citation_stable") is True
        and row.get("block_metadata_stable") is True
        and row.get("blocking_conditions") == []
        and REQUIRED_DETECTED_DRIFTS.issubset(set(as_list(row.get("detected_drifts"))))
        for row in rows
    )


def _comparison_contract_ok(report: dict[str, Any]) -> bool:
    contract = as_dict(report.get("comparison_contract"))
    return (
        contract.get("before_state") == "simulated_pre_patch_metadata_without_chunk_index_or_chunk_count"
        and contract.get("after_state") == "current_build_article_documents_output"
        and REQUIRED_COMPARISON_FIELDS["expected_drifts"].issubset(set(as_list(contract.get("expected_drifts"))))
        and REQUIRED_COMPARISON_FIELDS["forbidden_drifts"].issubset(set(as_list(contract.get("forbidden_drifts"))))
    )


def build_report(runner_report_path: Path = DEFAULT_RUNNER_REPORT_PATH) -> dict[str, Any]:
    runner_report = load_json(runner_report_path)
    summary = as_dict(runner_report.get("summary"))
    inputs = as_dict(runner_report.get("inputs"))
    guardrails = as_dict(runner_report.get("guardrails"))
    handoff = as_dict(runner_report.get("handoff"))
    rows = _rows(runner_report)

    guardrail_checks = [guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()]
    handoff_blocks = set(as_list(handoff.get("not_allowed_yet")))
    checks = [
        check_row(
            "runner_report_version",
            runner_report.get("version") == "0.4.13.11",
            "Runner report must be v0.4.13.11.",
        ),
        check_row(
            "runner_report_schema",
            runner_report.get("schema_kind") == "ingestion_metadata_patch_post_patch_rebuild_dry_run",
            "Runner report schema must match the post-patch rebuild dry-run runner.",
        ),
        check_row(
            "runner_scope",
            runner_report.get("scope") == "local saved-report post-patch rebuild dry-run only",
            "Runner report must remain local saved-report dry-run scoped.",
        ),
        check_row(
            "lineage",
            _has_required_lineage(inputs),
            "Runner lineage must reference the passed v0.4.13.8 source patch, v0.4.13.9 design, and v0.4.13.10 design gate reports.",
        ),
        check_row(
            "summary_contract",
            _has_expected_summary(summary, len(rows)),
            "Summary must show 3 samples, 9 rows, full metadata presence, expected ID drift, zero forbidden drift, zero blockers, and no runtime permissions.",
        ),
        check_row(
            "guardrails_locked",
            all(guardrail_checks),
            "Guardrails must keep saved-report/local scope and block Qdrant, rebuild, RAG, embedding, LLM, full eval, ingestion/retrieval/rules/eval mutation.",
        ),
        check_row(
            "sample_contract",
            _has_expected_samples(runner_report),
            "Samples must cover the three required shapes without case-id or hidden-seed dependency, with expected document counts and no blockers.",
        ),
        check_row(
            "row_contract",
            len(rows) == 9 and _rows_are_stable(rows),
            "Each row must have chunk_index/chunk_count, expected chunk_id/qdrant_point_id drift, stable content/citation/block metadata, required drift tags, and no blockers.",
        ),
        check_row(
            "comparison_contract",
            _comparison_contract_ok(runner_report),
            "Comparison contract must describe simulated pre-patch metadata, current build_article_documents output, expected boundary/ID drift, and forbidden content/citation/block drift.",
        ),
        check_row(
            "blockers_empty",
            runner_report.get("blockers") == [],
            "Runner report must have no top-level blockers.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("next_allowed_step") == "gate this post-patch rebuild dry-run runner"
            and REQUIRED_HANDOFF_BLOCKS.issubset(handoff_blocks),
            "Handoff must keep Qdrant write, rebuild, rag_query, embedding/LLM, full eval substitution, and runtime/eval mutation blocked.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_post_patch_rebuild_dry_run_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "post_patch_rebuild_dry_run_runner": {
                "path": str(runner_report_path),
                "version": runner_report.get("version"),
                "schema_kind": runner_report.get("schema_kind"),
                "status": summary.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "rebuild_authorization_design" if status == "passed" else "blocked",
            "runner_rerun_allowed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "rag_query_allowed": False,
            "embedding_or_llm_allowed": False,
            "full_eval": "not_run",
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.12 Post-Patch Rebuild Dry-Run Runner Gate",
        "",
        "本门禁只读取 v0.4.13.11 saved report，验证 post-patch rebuild dry-run runner 的输出是否稳定。它不重跑 runner，不访问 Qdrant，不写 collection，不 rebuild，不调用 RAG/embedding/LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: `{summary.get('check_count')}`",
        f"- 失败项: `{summary.get('failed_check_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否允许重跑 runner: `{summary.get('runner_rerun_allowed')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        f"- full eval: `{summary.get('full_eval')}`",
        "",
        "## 检查项",
        "",
    ]
    for row in report.get("checks", []):
        state = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"- `{state}` `{row.get('check_id')}`: {row.get('details')}")
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 只读取 `tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json`。",
            "- 不重新生成样本，不重跑 runner，不访问或写入 Qdrant，不 rebuild collection。",
            "- 不调用 `rag_query`、embedding、LLM 或 full eval。",
            "- 不修改 ingestion、retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。",
            "- 通过后只开放 rebuild authorization design，不代表已经允许生产 rebuild。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.12 post-patch rebuild dry-run runner gate.")
    parser.add_argument("--runner-report", type=Path, default=DEFAULT_RUNNER_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.runner_report)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Post-patch rebuild dry-run runner gate: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
