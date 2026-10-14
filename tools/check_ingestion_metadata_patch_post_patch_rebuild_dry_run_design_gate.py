"""Check the v0.4.13.10 post-patch rebuild dry-run design gate.

The gate validates the v0.4.13.9 post-patch rebuild dry-run design and keeps
runner creation, Qdrant writes, collection rebuilds, RAG/LLM calls, and runtime
logic changes blocked.
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


VERSION = "0.4.13.10"

DEFAULT_DESIGN_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path(
    "docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_v0.4.13.10.md"
)

REQUIRED_GUARDRAILS = {
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

REQUIRED_ALLOWED_INPUTS = {
    "saved v0.4.13.8 source patch report",
    "small deterministic local article_parts samples",
    "current build_article_documents output",
}

REQUIRED_FORBIDDEN_INPUTS = {
    "Qdrant collection writes",
    "Qdrant collection rebuild",
    "production collection point mutation",
    "rag_query output",
    "embedding or LLM calls",
    "full eval reports as a substitute for metadata dry-run rows",
}

REQUIRED_SAMPLE_SHAPES = {
    "single paragraph article",
    "paragraph plus item article",
    "multi-paragraph article",
}

REQUIRED_STABLE_FIELDS = {
    "page_content",
    "citation",
    "block_type",
    "paragraph_no",
    "item_no",
    "item_label",
    "parent_article_id",
}

REQUIRED_SUMMARY_FIELDS = {
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
}

REQUIRED_ROW_FIELDS = {
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
}

REQUIRED_BLOCKING_CONDITIONS = {
    "source_patch_report_missing_or_failed",
    "chunk_boundary_metadata_missing",
    "forbidden_content_or_citation_drift",
    "unexpected_standard_section_drift",
    "qdrant_write_requested",
    "collection_rebuild_requested",
    "rag_or_llm_call_requested",
    "eval_case_or_fixture_mutation_requested",
}

REQUIRED_HANDOFF_BLOCKS = {
    "create the rebuild dry-run runner",
    "write Qdrant",
    "rebuild collection",
    "modify ingestion or retrieval source",
    "modify anchors, risk rules, scenario registry, fixtures, or eval cases",
    "run full eval as a substitute for the rebuild dry-run contract",
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


def build_report(design_path: Path = DEFAULT_DESIGN_PATH) -> dict[str, Any]:
    design_report = load_json(design_path)
    inputs = as_dict(design_report.get("inputs"))
    source_patch_input = as_dict(inputs.get("source_patch_report"))
    guardrails = as_dict(design_report.get("guardrails"))
    summary = as_dict(design_report.get("summary"))
    dry_run_design = as_dict(design_report.get("dry_run_design"))
    sample_strategy = as_dict(dry_run_design.get("sample_strategy"))
    comparison_fields = as_dict(dry_run_design.get("comparison_fields"))
    output_contract = as_dict(design_report.get("output_contract"))
    handoff = as_dict(design_report.get("handoff"))

    allowed_inputs = set(as_list(dry_run_design.get("allowed_inputs")))
    forbidden_inputs = set(as_list(dry_run_design.get("forbidden_inputs")))
    sample_shapes = set(as_list(sample_strategy.get("required_shapes")))
    must_be_present = set(as_list(comparison_fields.get("must_be_present_after_patch")))
    expected_id_drift = set(as_list(comparison_fields.get("expected_to_change_if_rebuild_materializes")))
    stable_fields = set(as_list(comparison_fields.get("must_remain_stable")))
    expected_drift = set(as_list(dry_run_design.get("expected_drift")))
    forbidden_drift = set(as_list(dry_run_design.get("forbidden_drift")))
    summary_fields = set(as_list(output_contract.get("summary_fields")))
    row_fields = set(as_list(output_contract.get("row_fields")))
    blocking_conditions = set(as_list(output_contract.get("blocking_conditions")))
    not_allowed_yet = set(as_list(handoff.get("not_allowed_yet")))

    guardrail_checks = [
        guardrails.get(key) == expected for key, expected in REQUIRED_GUARDRAILS.items()
    ]
    checks = [
        check_row("design_version", design_report.get("version") == "0.4.13.9", "Design report must be v0.4.13.9."),
        check_row(
            "design_schema",
            design_report.get("schema_kind") == "ingestion_metadata_patch_post_patch_rebuild_dry_run_design",
            "Design schema must match the v0.4.13.9 post-patch rebuild dry-run design.",
        ),
        check_row(
            "design_status",
            summary.get("status") == "ready_for_post_patch_rebuild_dry_run_design_gate",
            "Design must explicitly open the design gate.",
        ),
        check_row(
            "allowed_next_step",
            summary.get("allowed_next_step") == "post_patch_rebuild_dry_run_design_gate",
            "Design must open only this gate.",
        ),
        check_row(
            "summary_blockers_empty",
            summary.get("blockers") == [],
            "Design must carry no source patch blockers.",
        ),
        check_row(
            "source_patch_input",
            source_patch_input.get("version") == "0.4.13.8"
            and source_patch_input.get("schema_kind") == "ingestion_metadata_source_patch_check"
            and source_patch_input.get("status") == "passed"
            and source_patch_input.get("allowed_next_step") == "post_patch_rebuild_dry_run_design",
            "Design input must be the passed v0.4.13.8 source patch report.",
        ),
        check_row(
            "summary_permissions_blocked",
            summary.get("implementation_allowed") is False
            and summary.get("runner_creation_allowed") is False
            and summary.get("qdrant_write_allowed") is False
            and summary.get("rebuild_allowed") is False
            and summary.get("retrieval_logic_change_allowed") is False
            and summary.get("full_eval") == "not_run",
            "Summary must keep implementation, runner creation, Qdrant, rebuild, retrieval, and full eval blocked.",
        ),
        check_row(
            "guardrails_locked",
            all(guardrail_checks),
            "Guardrails must keep design-only scope and block runtime, Qdrant, rebuild, rules, fixtures, eval cases, RAG, LLM, and embedding calls.",
        ),
        check_row(
            "future_runner_not_created",
            dry_run_design.get("future_runner_name") == "run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py"
            and dry_run_design.get("runner_status") == "not_created_in_this_version",
            "Future runner name may be designed, but runner must not be created in this version.",
        ),
        check_row(
            "allowed_inputs",
            REQUIRED_ALLOWED_INPUTS.issubset(allowed_inputs),
            "Allowed inputs must remain saved-report/local sample/current builder scoped.",
        ),
        check_row(
            "forbidden_inputs",
            REQUIRED_FORBIDDEN_INPUTS.issubset(forbidden_inputs),
            "Forbidden inputs must block Qdrant writes/rebuilds, production point mutation, RAG, embedding/LLM, and full-eval substitution.",
        ),
        check_row(
            "sample_strategy",
            sample_strategy.get("minimum_samples", 0) >= 3
            and REQUIRED_SAMPLE_SHAPES.issubset(sample_shapes)
            and sample_strategy.get("case_id_dependency") == "disallowed"
            and sample_strategy.get("hidden_seed_dependency") == "disallowed",
            "Sample strategy must cover the three local article shapes without case-id or hidden-seed dependency.",
        ),
        check_row(
            "boundary_metadata_fields",
            {"chunk_index", "chunk_count"}.issubset(must_be_present),
            "Comparison fields must require chunk_index and chunk_count after patch.",
        ),
        check_row(
            "expected_id_drift_fields",
            {"chunk_id", "qdrant_point_id"}.issubset(expected_id_drift),
            "Expected ID drift fields must include chunk_id and qdrant_point_id.",
        ),
        check_row(
            "stable_fields",
            REQUIRED_STABLE_FIELDS.issubset(stable_fields),
            "Stable comparison fields must cover content, citation, and block identity metadata.",
        ),
        check_row(
            "expected_drift_documented",
            any("chunk_id" in item for item in expected_drift)
            and any("qdrant_point_id" in item for item in expected_drift),
            "Expected drift narrative must document chunk_id and qdrant_point_id drift.",
        ),
        check_row(
            "forbidden_drift_documented",
            {
                "content_drift",
                "citation_drift",
                "block_type_drift",
                "paragraph_or_item_number_drift",
                "standard_section_behavior_drift",
                "retrieval_logic_drift",
                "anchor_or_risk_rule_drift",
                "eval_case_or_fixture_drift",
            }.issubset(forbidden_drift),
            "Forbidden drift must cover content, citation, standard sections, retrieval/rules, and eval/fixture drift.",
        ),
        check_row(
            "summary_output_contract",
            REQUIRED_SUMMARY_FIELDS.issubset(summary_fields),
            "Output contract summary fields must support sample, row, metadata, ID drift, blocker, and guardrail accounting.",
        ),
        check_row(
            "row_output_contract",
            REQUIRED_ROW_FIELDS.issubset(row_fields),
            "Output contract row fields must support per-document metadata, ID drift, stability, and blocker review.",
        ),
        check_row(
            "blocking_conditions",
            REQUIRED_BLOCKING_CONDITIONS.issubset(blocking_conditions),
            "Blocking conditions must catch failed source patch, missing boundary metadata, forbidden drift, Qdrant/rebuild/RAG/LLM requests, and eval/fixture mutation.",
        ),
        check_row(
            "handoff_boundaries",
            handoff.get("next_allowed_step") == "gate this post-patch rebuild dry-run design"
            and REQUIRED_HANDOFF_BLOCKS.issubset(not_allowed_yet),
            "Handoff must keep runner creation, Qdrant, rebuild, source/retrieval, rules, fixtures, eval cases, and full-eval substitution blocked.",
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    status = "passed" if not failed else "failed"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "post_patch_rebuild_dry_run_design": {
                "path": str(design_path),
                "version": design_report.get("version"),
                "schema_kind": design_report.get("schema_kind"),
                "status": summary.get("status"),
            }
        },
        "summary": {
            "status": status,
            "check_count": len(checks),
            "failed_check_count": len(failed),
            "allowed_next_step": "post_patch_rebuild_dry_run_runner" if status == "passed" else "blocked",
            "implementation_allowed": False,
            "runner_creation_allowed_in_this_version": False,
            "retrieval_logic_change_allowed": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
        },
        "checks": checks,
        "failed_checks": failed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.10 补丁后 rebuild dry-run 设计门禁",
        "",
        "本门禁只校验 v0.4.13.9 的 post-patch rebuild dry-run 设计是否稳定。它不创建 runner、不写入 Qdrant、不重建 collection、不调用 RAG/embedding/LLM，也不运行 full eval。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 检查项: {summary.get('check_count')}",
        f"- 失败项: {summary.get('failed_check_count')}",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 本版本是否允许创建 runner: `{summary.get('runner_creation_allowed_in_this_version')}`",
        f"- 是否允许写入 Qdrant: `{summary.get('qdrant_write_allowed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
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
            "- 本版本只 gate 设计，不创建 `run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py`。",
            "- 不写 Qdrant，不 rebuild collection，不接入 `rag_query`。",
            "- 不修改 ingestion、retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the v0.4.13.10 post-patch rebuild dry-run design gate.")
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.design)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Post-patch rebuild dry-run design gate: "
        f"{summary.get('status')}, failed={summary.get('failed_check_count')}"
    )
    return 0 if summary.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
