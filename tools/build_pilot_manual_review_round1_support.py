"""Build a read-only Round 1 support packet for pilot manual review.

This report helps a human reviewer decide the first five pilot cases. It does
not write reviewer decisions, does not create importable workbench rows, and
does not mutate retrieval, rerank, prompts, anchors, risk rules, eval cases,
hidden seeds, or the RAG main flow.
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

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.8.19"

DEFAULT_PILOT_BATCH_PATH = legacy_report_path("manual_review_pilot_batch_report.json")
DEFAULT_PILOT_REVIEW_ASSIST_PATH = legacy_report_path("manual_review_pilot_case_review_assist_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("pilot_manual_review_round1_support_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/pilot_manual_review_round1_support_v0.4.7.8.19.md")

GUARDRAILS = {
    "advisory_only": True,
    "writes_reviewer_decisions": "disallowed",
    "completed_manual_decision_generation": "disallowed",
    "reviewer_input_template_written": "disallowed",
    "workbench_import": "disallowed",
    "promotion_candidate_generation": "disallowed",
    "ready_action_candidate_generation": "disallowed",
    "rag_query_integration": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
}

DANGEROUS_OUTPUT_KEYS = {
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
    "decision_status",
}


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


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [value]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def text(value: Any) -> str:
    return str(value or "").strip()


def compact(value: Any, limit: int = 360) -> str:
    value_text = " ".join(text(value).split())
    if len(value_text) <= limit:
        return value_text
    return value_text[: limit - 1].rstrip() + "..."


def by_case(items: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in as_list(items):
        if not isinstance(item, dict):
            continue
        case_id = text(item.get("case_id") or item.get("id"))
        if case_id:
            result[case_id] = item
    return result


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
        "schema_kind": data.get("schema_kind"),
    }


def recursive_key_scan(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(recursive_key_scan(child))
    elif isinstance(value, list):
        for item in value:
            keys.extend(recursive_key_scan(item))
    return keys


def evidence_line(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "citation": item.get("citation") or "",
        "source": item.get("source") or item.get("law_name") or "",
        "article_no": item.get("article_no") or item.get("article") or "",
        "functional_type": item.get("functional_type") or item.get("legal_functional_type") or "",
        "content_preview": compact(
            item.get("content_preview")
            or item.get("content")
            or item.get("matched_content")
            or item.get("citation")
            or "",
            260,
        ),
    }


def evidence_examples(assessment: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        "final_evidence": [evidence_line(item) for item in as_list(assessment.get("final_evidence_examples"))[:3] if isinstance(item, dict)],
        "missing_expected_evidence": [
            evidence_line(item) for item in as_list(assessment.get("missing_expected_evidence_examples"))[:3] if isinstance(item, dict)
        ],
        "missing_scenario_core_evidence": [
            evidence_line(item) for item in as_list(assessment.get("missing_scenario_core_evidence_examples"))[:3] if isinstance(item, dict)
        ],
        "lost_before_final_evidence": [
            evidence_line(item) for item in as_list(assessment.get("lost_before_final_evidence_examples"))[:3] if isinstance(item, dict)
        ],
    }


def option_explanations() -> list[dict[str, str]]:
    return [
        {
            "option_code": "confirm_diagnostic_issue",
            "plain_label": "确认诊断成立",
            "when_to_use": "你认为当前答案确实存在证据支撑、主争点覆盖或证据选择问题。",
        },
        {
            "option_code": "confirm_scope_adjustment_needed",
            "plain_label": "确认需要范围校准",
            "when_to_use": "你认为问题存在，但主要原因是案由、场景登记或预期证据范围需要校准。",
        },
        {
            "option_code": "reject_diagnostic_issue",
            "plain_label": "驳回诊断",
            "when_to_use": "你认为现有 evidence chain 已足以支撑答案，诊断信号不成立。",
        },
        {
            "option_code": "insufficient_information",
            "plain_label": "信息不足",
            "when_to_use": "你无法根据当前离线证据判断，需要补充材料或进一步检索。",
        },
        {
            "option_code": "defer",
            "plain_label": "暂缓",
            "when_to_use": "你暂时不想在本轮对该案作出结论。",
        },
    ]


def likely_attention_level(counts: dict[str, Any], signals: list[dict[str, Any]]) -> str:
    signal_codes = {text(signal.get("code")) for signal in signals if isinstance(signal, dict)}
    if counts.get("missing_expected_evidence") or "primary_issue_missing_evidence" in signal_codes:
        return "high"
    if counts.get("missing_scenario_core_evidence") or counts.get("lost_before_final_evidence"):
        return "medium"
    return "review"


def user_decision_prompts(case: dict[str, Any]) -> list[str]:
    assist = as_dict(case.get("advisory_review_assist"))
    assessment = as_dict(case.get("evidence_support_assessment"))
    prompts = [text(item) for item in as_list(assist.get("focus_questions_for_user")) if text(item)]
    if assessment.get("missing_expected_evidence_examples"):
        prompts.append("缺失的预期条文是否属于本案主争点必须证据？")
    if assessment.get("missing_scenario_core_evidence_examples"):
        prompts.append("场景核心条文缺口是 registry 范围偏宽，还是 final evidence 漏选？")
    if assessment.get("lost_before_final_evidence_examples"):
        prompts.append("候选阶段出现但最终流失的条文是否应进入 evidence_chain？")
    prompts.append("如果你要确认诊断成立，请写明具体证据缺口，而不是只复述辅助信号。")
    return list(dict.fromkeys(prompts))


def build_case_support(pilot_case: dict[str, Any], assist_case: dict[str, Any]) -> dict[str, Any]:
    assessment = as_dict(assist_case.get("evidence_support_assessment"))
    assist = as_dict(assist_case.get("advisory_review_assist"))
    claims = as_dict(assist_case.get("original_llm_claims"))
    counts = as_dict(assessment.get("counts"))
    signals = [signal for signal in as_list(assessment.get("detected_assist_signals")) if isinstance(signal, dict)]
    return {
        "case_id": text(assist_case.get("case_id") or pilot_case.get("case_id")),
        "rank": assist_case.get("rank") or pilot_case.get("rank"),
        "risk_level": assist_case.get("risk_level") or pilot_case.get("risk_level"),
        "expected_domains": as_list(assist_case.get("expected_domains") or pilot_case.get("expected_domains")),
        "case_under_review": {
            "case_topic": text(assist_case.get("case_topic") or pilot_case.get("case_topic")),
            "question": text(assist_case.get("question") or pilot_case.get("question")),
            "plain_case_brief": text(assist_case.get("plain_case_brief")),
        },
        "original_llm_output_for_comparison": {
            "excerpt": compact(claims.get("excerpt") or pilot_case.get("original_llm_output_excerpt"), 900),
            "risk_types": as_list(claims.get("risk_types") or pilot_case.get("risk_types_from_original_output")),
            "recommended_actions": as_list(claims.get("recommended_actions") or pilot_case.get("recommended_actions_from_original_output")),
            "source": claims.get("source") or "pilot_batch_report/pilot_review_assist_report",
            "not_a_current_generation": True,
        },
        "evidence_snapshot": {
            "support_status": assessment.get("support_status"),
            "support_status_label": assessment.get("support_status_label"),
            "counts": counts,
            "signals": signals,
            "plain_assessment": assessment.get("plain_assessment"),
            "examples": evidence_examples(assessment),
        },
        "round1_review_prompts": user_decision_prompts(assist_case),
        "non_binding_assist_view": {
            "advisory_tendency": assist.get("advisory_tendency"),
            "advisory_tendency_label": assist.get("advisory_tendency_label"),
            "advisory_rationale": as_list(assist.get("advisory_rationale")),
            "why_selected": as_list(as_dict(assist_case.get("source_signals")).get("why_selected") or pilot_case.get("why_selected")),
            "must_be_confirmed_by_user": True,
            "not_a_reviewer_decision": True,
        },
        "decision_options_explained": option_explanations(),
        "round1_attention_level": likely_attention_level(counts, signals),
        "safe_output_boundary": {
            "manual_import_payload_written": False,
            "completed_decision_written": False,
            "promotion_or_ready_action_written": False,
            "user_must_fill_visual_workbench": True,
        },
    }


def build_report(
    pilot_batch_path: Path = DEFAULT_PILOT_BATCH_PATH,
    pilot_review_assist_path: Path = DEFAULT_PILOT_REVIEW_ASSIST_PATH,
) -> dict[str, Any]:
    pilot_batch = load_json(pilot_batch_path)
    pilot_review_assist = load_json(pilot_review_assist_path)
    pilot_cases = by_case(pilot_batch.get("pilot_cases"))
    assist_cases = by_case(pilot_review_assist.get("assisted_cases"))
    case_ids = [text(case.get("case_id")) for case in as_list(pilot_batch.get("pilot_cases")) if isinstance(case, dict)]
    cases = [
        build_case_support(pilot_cases.get(case_id, {}), assist_cases.get(case_id, {"case_id": case_id}))
        for case_id in case_ids
        if case_id
    ]
    attention_counter = Counter(case["round1_attention_level"] for case in cases)
    signal_counter: Counter[str] = Counter()
    for case in cases:
        signal_counter.update(
            text(signal.get("code"))
            for signal in case["evidence_snapshot"]["signals"]
            if isinstance(signal, dict) and text(signal.get("code"))
        )
    report = {
        "version": VERSION,
        "schema_kind": "advisory_pilot_manual_review_round1_support",
        "contains_completed_manual_decisions": False,
        "advisory_packet_only": True,
        "scope": "pilot manual review round 1 support",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "pilot_batch_report": source_meta(pilot_batch_path, pilot_batch),
            "pilot_review_assist_report": source_meta(pilot_review_assist_path, pilot_review_assist),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "pilot_cases": len(cases),
            "round1_support_cases": len(cases),
            "needs_user_confirmation_cases": len(cases),
            "completed_manual_decisions": 0,
            "promotion_candidates": 0,
            "ready_action_candidates": 0,
            "attention_level_summary": dict(sorted(attention_counter.items())),
            "signal_summary": dict(sorted(signal_counter.items())),
            "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
        },
        "round1_cases": cases,
        "next_user_action": {
            "open_visual_workbench": "tools/manual_review_visual_workbench/index.html",
            "queue": "pilot_batch",
            "instruction": "Use this packet to understand each case, then fill the visual workbench manually if you decide.",
            "not_importable_as_manual_review": True,
        },
    }
    dangerous_keys = sorted(DANGEROUS_OUTPUT_KEYS & set(recursive_key_scan(report)))
    if dangerous_keys:
        raise ValueError(f"round1 support report contains dangerous import keys: {dangerous_keys}")
    return report


def render_evidence(items: list[dict[str, Any]]) -> str:
    if not items:
        return "- 暂无可展示条文摘录。"
    return "\n".join(
        f"- {item.get('citation') or item.get('source') or '未标注条文'}：{item.get('content_preview') or '无摘录'}"
        for item in items
    )


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# v0.4.7.8.19 Pilot Manual Review Round 1 Support",
        "",
        "## 定位",
        "",
        "本报告是 5 个 pilot case 的人工复核第一轮支持材料。它只帮助 reviewer 看懂案由、原 LLM 输出、证据链缺口和需要拍板的问题。",
        "它不是人工复核结论，不会写入可导入的人工复核字段，也不能作为 importer 或 dry-run 的 completed decision 输入。",
        "",
        "## 摘要",
        "",
        f"- 支持 case：{summary['round1_support_cases']}",
        f"- 需要人工确认：{summary['needs_user_confirmation_cases']}",
        f"- Completed manual decisions：{summary['completed_manual_decisions']}",
        f"- Promotion candidates：{summary['promotion_candidates']}",
        f"- Ready action candidates：{summary['ready_action_candidates']}",
        f"- Gate status：`{summary['gate_status']}`",
        "",
        "## 每案复核支持",
        "",
    ]
    for case in report["round1_cases"]:
        review = case["case_under_review"]
        original = case["original_llm_output_for_comparison"]
        evidence = case["evidence_snapshot"]
        assist = case["non_binding_assist_view"]
        examples = evidence["examples"]
        signals = "、".join(signal.get("label") or signal.get("code") for signal in evidence["signals"]) or "暂无明显信号"
        lines.extend(
            [
                f"### {case['rank']}. `{case['case_id']}`",
                "",
                f"- 关注级别：{case['round1_attention_level']}",
                f"- 案由/问题：{review.get('plain_case_brief') or review.get('question')}",
                f"- 原 LLM 风险类型：{'、'.join(map(str, original.get('risk_types') or [])) or '未提取'}",
                f"- 原 LLM 整改动作：{'、'.join(map(str, original.get('recommended_actions') or [])) or '未提取'}",
                f"- 证据状态：{evidence.get('support_status_label') or evidence.get('support_status')}",
                f"- 辅助信号：{signals}",
                f"- 非绑定辅助倾向：{assist.get('advisory_tendency_label') or assist.get('advisory_tendency')}（只作参考，仍需人工确认）",
                "",
                "重点核对问题：",
            ]
        )
        lines.extend(f"- {prompt}" for prompt in case["round1_review_prompts"])
        lines.extend(["", "缺失/流失证据示例："])
        missing_and_lost = (
            examples["missing_expected_evidence"]
            + examples["missing_scenario_core_evidence"]
            + examples["lost_before_final_evidence"]
        )
        lines.append(render_evidence(missing_and_lost))
        lines.extend(["", "可选人工结论含义："])
        lines.extend(
            f"- `{option['option_code']}`：{option['plain_label']}。{option['when_to_use']}"
            for option in case["decision_options_explained"]
        )
        lines.append("")
    lines.extend(
        [
            "## 边界",
            "",
            "- 本报告不写 `reviewer_input_template`。",
            "- 本报告不生成 `reviewer_decision` 或 completed manual decision。",
            "- 本报告不生成 promotion candidate 或 ready action candidate。",
            "- 本报告不接入 `rag_query`、后端 API、Qdrant 或 LLM。",
            "- 本报告不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。",
            "- 真正治理动作必须等待人工在 visual workbench 填写并通过 export pipeline dry run。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build read-only Round 1 support for pilot manual review.")
    parser.add_argument("--pilot-batch-report", type=Path, default=DEFAULT_PILOT_BATCH_PATH)
    parser.add_argument("--pilot-review-assist-report", type=Path, default=DEFAULT_PILOT_REVIEW_ASSIST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.pilot_batch_report, args.pilot_review_assist_report)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Pilot manual review round1 support built: "
        f"{summary['round1_support_cases']} cases, "
        f"{summary['needs_user_confirmation_cases']} need user confirmation, "
        f"gate={summary['gate_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
