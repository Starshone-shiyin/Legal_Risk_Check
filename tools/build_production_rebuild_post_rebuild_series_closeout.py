"""Close out the v0.4.14 production rebuild and post-rebuild RAG chain."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.14.35"

DEFAULT_EXECUTION_PATH = Path("tests/production_rebuild_execution_report.json")
DEFAULT_POST_VALIDATION_PATH = Path("tests/production_rebuild_post_validation_report.json")
DEFAULT_SMOKE_PATH = Path("tests/post_rebuild_smoke_eval_report.json")
DEFAULT_QUALITY_SUMMARY_PATH = Path("tests/post_rebuild_quality_summary_report.json")
DEFAULT_INITIAL_FULL_RAG_PATH = Path("tests/post_rebuild_rag_eval_report.json")
DEFAULT_INITIAL_FULL_RAG_SUMMARY_PATH = Path("tests/post_rebuild_rag_eval_summary_report.json")
DEFAULT_RETENTION_FULL_RAG_PATH = Path("tests/post_rebuild_rag_eval_after_alignment_retention_report.json")
DEFAULT_RETENTION_DELTA_PATH = Path("tests/post_rebuild_alignment_retention_delta_report.json")
DEFAULT_TIGHTENED_FULL_RAG_PATH = Path("tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json")
DEFAULT_TIGHTENING_DOC_PATH = Path("docs/post_rebuild_alignment_retention_tightening_v0.4.14.34.md")
DEFAULT_OUTPUT_PATH = Path("tests/production_rebuild_post_rebuild_series_closeout_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md")


GUARDRAILS = {
    "closeout_only": True,
    "saved_reports_only": True,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "rag_query_call": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval_execution": "not_run_by_closeout",
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


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
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


def eval_status(report: dict[str, Any]) -> str | None:
    total = report.get("total")
    passed = report.get("passed")
    if isinstance(total, int) and isinstance(passed, int):
        return "passed" if total == passed else "failed"
    return None


def source_meta(path: Path, data: dict[str, Any], *, kind: str) -> dict[str, Any]:
    summary = as_dict(data.get("summary"))
    status = summary.get("status") or summary.get("execution_status") or eval_status(data)
    return {
        "kind": kind,
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": status,
        "total": data.get("total"),
        "passed": data.get("passed"),
        "failed": data.get("failed"),
    }


def closed_loop_blockers(reports: dict[str, dict[str, Any]], tightening_doc_path: Path) -> list[str]:
    blockers: list[str] = []

    execution_summary = as_dict(reports["execution"].get("summary"))
    if execution_summary.get("execution_status") != "succeeded":
        blockers.append("production_rebuild_execution_not_succeeded")
    if execution_summary.get("qdrant_write_executed") is not True:
        blockers.append("production_rebuild_write_not_recorded")
    if execution_summary.get("collection_rebuilt") is not True:
        blockers.append("collection_rebuild_not_recorded")

    post_validation_summary = as_dict(reports["post_validation"].get("summary"))
    if post_validation_summary.get("status") != "passed":
        blockers.append("post_validation_not_passed")

    if reports["smoke"].get("total") != 25 or reports["smoke"].get("passed") != 25:
        blockers.append("post_rebuild_smoke_not_25_of_25")

    quality_summary = as_dict(reports["quality_summary"].get("summary"))
    if quality_summary.get("status") != "passed":
        blockers.append("quality_summary_not_passed")

    if reports["initial_full_rag"].get("total") != 60 or reports["initial_full_rag"].get("passed") != 58:
        blockers.append("initial_post_rebuild_full_rag_expected_58_of_60_missing")

    initial_summary = as_dict(reports["initial_full_rag_summary"].get("rag_eval_summary"))
    if initial_summary.get("regression_count") != 2:
        blockers.append("initial_post_rebuild_regression_count_not_2")

    if reports["retention_full_rag"].get("total") != 60 or reports["retention_full_rag"].get("passed") != 60:
        blockers.append("alignment_retention_full_rag_not_60_of_60")

    delta_summary = as_dict(reports["retention_delta"].get("summary"))
    evidence_delta_summary = as_dict(reports["retention_delta"].get("evidence_delta_summary"))
    if delta_summary.get("status") != "passed":
        blockers.append("alignment_retention_delta_not_passed")
    if evidence_delta_summary.get("removed_expected_evidence_count") != 0:
        blockers.append("alignment_retention_delta_removed_expected_evidence")

    if reports["tightened_full_rag"].get("total") != 60 or reports["tightened_full_rag"].get("passed") != 60:
        blockers.append("tightened_full_rag_not_60_of_60")
    if as_dict(reports["tightened_full_rag"].get("retrieval_failure_stage_summary")) != {"PASS": 60}:
        blockers.append("tightened_full_rag_stage_summary_not_all_pass")

    if not tightening_doc_path.exists():
        blockers.append("tightening_doc_missing")

    return blockers


def build_report(
    execution_path: Path = DEFAULT_EXECUTION_PATH,
    post_validation_path: Path = DEFAULT_POST_VALIDATION_PATH,
    smoke_path: Path = DEFAULT_SMOKE_PATH,
    quality_summary_path: Path = DEFAULT_QUALITY_SUMMARY_PATH,
    initial_full_rag_path: Path = DEFAULT_INITIAL_FULL_RAG_PATH,
    initial_full_rag_summary_path: Path = DEFAULT_INITIAL_FULL_RAG_SUMMARY_PATH,
    retention_full_rag_path: Path = DEFAULT_RETENTION_FULL_RAG_PATH,
    retention_delta_path: Path = DEFAULT_RETENTION_DELTA_PATH,
    tightened_full_rag_path: Path = DEFAULT_TIGHTENED_FULL_RAG_PATH,
    tightening_doc_path: Path = DEFAULT_TIGHTENING_DOC_PATH,
) -> dict[str, Any]:
    reports = {
        "execution": load_json(execution_path),
        "post_validation": load_json(post_validation_path),
        "smoke": load_json(smoke_path),
        "quality_summary": load_json(quality_summary_path),
        "initial_full_rag": load_json(initial_full_rag_path),
        "initial_full_rag_summary": load_json(initial_full_rag_summary_path),
        "retention_full_rag": load_json(retention_full_rag_path),
        "retention_delta": load_json(retention_delta_path),
        "tightened_full_rag": load_json(tightened_full_rag_path),
    }
    blockers = closed_loop_blockers(reports, tightening_doc_path)
    status = "closed_for_next_real_rag_quality_task" if not blockers else "blocked"

    execution_summary = as_dict(reports["execution"].get("summary"))
    post_validation_summary = as_dict(reports["post_validation"].get("summary"))
    post_validation_detail = as_dict(reports["quality_summary"].get("post_validation_summary"))
    initial_rag_summary = as_dict(reports["initial_full_rag_summary"].get("rag_eval_summary"))
    delta_summary = as_dict(reports["retention_delta"].get("summary"))
    evidence_delta_summary = as_dict(reports["retention_delta"].get("evidence_delta_summary"))

    return {
        "version": VERSION,
        "schema_kind": "production_rebuild_post_rebuild_series_closeout",
        "scope": "v0.4.14 production rebuild and post-rebuild RAG quality closeout",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "execution": source_meta(execution_path, reports["execution"], kind="production_rebuild_execution"),
            "post_validation": source_meta(post_validation_path, reports["post_validation"], kind="post_rebuild_payload_validation"),
            "smoke": source_meta(smoke_path, reports["smoke"], kind="post_rebuild_smoke_eval"),
            "quality_summary": source_meta(quality_summary_path, reports["quality_summary"], kind="post_rebuild_quality_summary"),
            "initial_full_rag": source_meta(initial_full_rag_path, reports["initial_full_rag"], kind="post_rebuild_full_rag_eval"),
            "initial_full_rag_summary": source_meta(initial_full_rag_summary_path, reports["initial_full_rag_summary"], kind="post_rebuild_full_rag_summary"),
            "retention_full_rag": source_meta(retention_full_rag_path, reports["retention_full_rag"], kind="post_fix_full_rag_eval"),
            "retention_delta": source_meta(retention_delta_path, reports["retention_delta"], kind="post_fix_evidence_delta"),
            "tightened_full_rag": source_meta(tightened_full_rag_path, reports["tightened_full_rag"], kind="tightened_post_fix_full_rag_eval"),
            "tightening_doc": {
                "kind": "post_rebuild_alignment_retention_tightening_doc",
                "path": str(tightening_doc_path),
                "present": tightening_doc_path.exists(),
            },
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "blockers": blockers,
            "production_rebuild_succeeded": execution_summary.get("execution_status") == "succeeded",
            "qdrant_write_was_previously_executed_by_rebuild": execution_summary.get("qdrant_write_executed") is True,
            "post_validation_passed": post_validation_summary.get("status") == "passed",
            "points_count": post_validation_detail.get("points_count"),
            "post_rebuild_smoke": {
                "passed": reports["smoke"].get("passed"),
                "total": reports["smoke"].get("total"),
            },
            "initial_post_rebuild_full_rag": {
                "passed": reports["initial_full_rag"].get("passed"),
                "total": reports["initial_full_rag"].get("total"),
                "retrieval_failure_stage_summary": reports["initial_full_rag"].get("retrieval_failure_stage_summary", {}),
                "regression_count": initial_rag_summary.get("regression_count"),
                "issue_type_summary": initial_rag_summary.get("issue_type_summary", {}),
            },
            "alignment_retention_full_rag": {
                "passed": reports["retention_full_rag"].get("passed"),
                "total": reports["retention_full_rag"].get("total"),
            },
            "alignment_retention_delta": {
                "status": delta_summary.get("status"),
                "manual_review_case_count": delta_summary.get("manual_review_case_count"),
                "removed_expected_evidence_count": evidence_delta_summary.get("removed_expected_evidence_count"),
                "risky_unexplained_replacement_count": evidence_delta_summary.get("risky_unexplained_replacement_count"),
            },
            "tightened_full_rag": {
                "passed": reports["tightened_full_rag"].get("passed"),
                "total": reports["tightened_full_rag"].get("total"),
                "retrieval_failure_stage_summary": reports["tightened_full_rag"].get("retrieval_failure_stage_summary", {}),
            },
            "allowed_next_step": "next_real_rag_quality_task_planning" if not blockers else "resolve_closeout_blockers",
        },
        "closed_loop_findings": [
            "v0.4.14.29 已执行授权后的生产重建，并记录 legal_knowledge rebuild 成功。",
            "重建后 post-validation 只读扫描 payload metadata 并通过，未观测到 chunk_index/chunk_count 缺失。",
            "重建后 smoke 保持稳定，结果为 25/25 passed。",
            "初次 post-rebuild full RAG eval 暴露了真实的 58/60 回归信号，而不是被新的设计步骤遮住。",
            "alignment retention selector patch 将 full eval 恢复为 60/60，delta report 确认没有 removed expected evidence。",
            "tightening pass 增加 protected evidence 硬保护，最终 full RAG eval 为 60/60，retrieval_failure_stage_summary 为 {'PASS': 60}。",
        ],
        "residual_risks": [
            "单次 60/60 证明本轮 saved regression loop 已闭环，但不代表未来法规扩容后一定稳定。",
            "contribution summary 中仍能看到 anchor assistance；后续质量工作应提升 retrieval input quality，而不是把新增 anchor 当成捷径。",
            "答案生成仍可能有措辞波动；后续审计应区分证据失败与答案表达波动。",
        ],
        "not_allowed_next_steps": [
            "不要为了重复说明本收口而新增 gate 链",
            "不要通过新增 anchor 掩盖基础召回弱点",
            "不要把修改 prompt、rerank、eval cases、hidden seeds、risk supplement、term preservation rules、scenario registry 或 fixtures 当成捷径",
            "不要从本 closeout 工具触发 Qdrant 写入",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    initial = as_dict(summary.get("initial_post_rebuild_full_rag"))
    tightened = as_dict(summary.get("tightened_full_rag"))
    delta = as_dict(summary.get("alignment_retention_delta"))

    lines = [
        "# v0.4.14.35 Production Rebuild / Post-Rebuild Series Closeout",
        "",
        "## 结论",
        "",
        f"- 状态：`{summary.get('status')}`",
        f"- 生产重建：`{'passed' if summary.get('production_rebuild_succeeded') else 'blocked'}`",
        f"- 重建后验证：`{'passed' if summary.get('post_validation_passed') else 'blocked'}`",
        f"- smoke：`{as_dict(summary.get('post_rebuild_smoke')).get('passed')}/{as_dict(summary.get('post_rebuild_smoke')).get('total')}`",
        f"- 初次 full RAG eval：`{initial.get('passed')}/{initial.get('total')}`，回归数 `{initial.get('regression_count')}`",
        f"- 收紧后 full RAG eval：`{tightened.get('passed')}/{tightened.get('total')}`，stage `{tightened.get('retrieval_failure_stage_summary')}`",
        f"- delta 复核：`{delta.get('status')}`，removed expected evidence `{delta.get('removed_expected_evidence_count')}`",
        f"- 允许的下一步：`{summary.get('allowed_next_step')}`",
        "",
        "## 闭环事实",
        "",
    ]
    for item in report.get("closed_loop_findings") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 边界",
        "",
        "本文件只是 RAG 主链路生产重建后的收口归档。它只读取既有报告，不连接 Qdrant，不调用 `rag_query`，不调用 LLM，不运行 full eval，也不修改运行时代码。",
        "",
        "本版本不是样本修补、不是新增 gate，也不是 anchor/prompt/rerank/eval case 调参。v0.4.14.34 的 selector tightening 已经用正式 full RAG eval 60/60 覆盖，本 closeout 只把这条证据链归档。",
        "",
        "## 剩余风险",
        "",
    ])
    for item in report.get("residual_risks") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 不建议的下一步",
        "",
    ])
    for item in report.get("not_allowed_next_steps") or []:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 输入报告",
        "",
    ])
    for key, item in as_dict(report.get("inputs")).items():
        lines.append(f"- `{key}`: `{item.get('path')}`，present=`{item.get('present')}`，status=`{item.get('status')}`")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Close out the v0.4.14 production rebuild/post-rebuild RAG chain.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()

    report = build_report()
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Production rebuild post-rebuild series closeout completed: "
        f"{report['summary']['status']}, blockers={len(report['summary']['blockers'])}"
    )
    return 0 if report["summary"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
