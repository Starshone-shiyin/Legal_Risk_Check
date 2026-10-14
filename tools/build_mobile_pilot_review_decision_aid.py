"""Build a mobile-friendly advisory aid for pilot manual review.

The output is a compact confirmation aid for a user reviewing on a phone. It
does not write reviewer decisions, does not create importable workbench rows,
and does not mutate retrieval, rerank, prompts, anchors, risk rules, eval
cases, hidden seeds, or the RAG main flow.
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


VERSION = "0.4.7.8.20"

DEFAULT_ROUND1_SUPPORT_PATH = legacy_report_path("pilot_manual_review_round1_support_report.json")
DEFAULT_CONTRACT_PATH = legacy_report_path("manual_review_visual_workbench_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("mobile_pilot_review_decision_aid_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/mobile_pilot_review_decision_aid_v0.4.7.8.20.md")

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
    "decision",
    "confirmed_root_causes",
    "rejected_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
    "fixture_candidate",
    "rationale",
    "notes",
}

ROOT_CAUSE_BY_SIGNAL = {
    "primary_issue_missing_evidence": "primary_evidence_gap",
    "scenario_core_gap": "scenario_core_scope",
    "final_selection_loss": "final_evidence_selection_policy",
    "definition_substitution_review": "functional_typing_metadata",
    "retrieval_stability_review": "metadata_chunking_or_query_coverage",
}

ACTION_BY_ROOT_CAUSE = {
    "primary_evidence_gap": "primary_evidence_fixture_candidate_review",
    "scenario_core_scope": "scenario_registry_core_article_review",
    "final_evidence_selection_policy": "final_evidence_selection_policy_review",
    "functional_typing_metadata": "functional_typing_fixture_review",
    "metadata_chunking_or_query_coverage": "metadata_chunking_or_query_coverage_review",
}

TENDENCY_LABELS = {
    "confirm_diagnostic_issue": "建议优先考虑：确认诊断成立",
    "confirm_scope_adjustment_needed": "建议优先考虑：确认需要范围校准",
    "reject_diagnostic_issue": "建议优先考虑：驳回诊断",
    "insufficient_information": "建议优先考虑：信息不足",
    "defer": "建议优先考虑：暂缓",
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


def compact(value: Any, limit: int = 180) -> str:
    value_text = " ".join(text(value).split())
    if len(value_text) <= limit:
        return value_text
    return value_text[: limit - 1].rstrip() + "..."


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


def allowed_values(contract: dict[str, Any], key: str) -> set[str]:
    return set(as_list(as_dict(as_dict(contract.get("field_contract")).get("allowed_values")).get(key)))


def signal_codes(case: dict[str, Any]) -> list[str]:
    signals = as_list(as_dict(case.get("evidence_snapshot")).get("signals"))
    return [text(signal.get("code")) for signal in signals if isinstance(signal, dict) and text(signal.get("code"))]


def suggest_tendency(case: dict[str, Any]) -> str:
    evidence = as_dict(case.get("evidence_snapshot"))
    counts = as_dict(evidence.get("counts"))
    codes = set(signal_codes(case))
    if counts.get("missing_expected_evidence") or "primary_issue_missing_evidence" in codes:
        return "confirm_diagnostic_issue"
    if counts.get("missing_scenario_core_evidence") or "scenario_core_gap" in codes:
        return "confirm_scope_adjustment_needed"
    if not codes:
        return "insufficient_information"
    return "confirm_diagnostic_issue"


def suggest_root_causes(codes: list[str], allowed: set[str]) -> list[str]:
    roots = []
    for code in codes:
        root = ROOT_CAUSE_BY_SIGNAL.get(code)
        if root and root in allowed:
            roots.append(root)
    return list(dict.fromkeys(roots))[:3]


def suggest_actions(roots: list[str], allowed: set[str]) -> list[str]:
    actions = []
    for root in roots:
        action = ACTION_BY_ROOT_CAUSE.get(root)
        if action and action in allowed:
            actions.append(action)
    if "primary_evidence_gap" in roots and "needs_additional_evidence_capture" in allowed:
        actions.append("needs_additional_evidence_capture")
    return list(dict.fromkeys(actions))[:3]


def top_evidence_gap(case: dict[str, Any]) -> str:
    examples = as_dict(as_dict(case.get("evidence_snapshot")).get("examples"))
    for key in ("missing_expected_evidence", "missing_scenario_core_evidence", "lost_before_final_evidence"):
        rows = [row for row in as_list(examples.get(key)) if isinstance(row, dict)]
        if rows:
            row = rows[0]
            return compact(row.get("citation") or row.get("source") or row.get("content_preview"), 160)
    return "当前支持包未列出具体缺失证据示例。"


def mobile_lines(case: dict[str, Any], tendency: str, roots: list[str], actions: list[str]) -> list[str]:
    review = as_dict(case.get("case_under_review"))
    original = as_dict(case.get("original_llm_output_for_comparison"))
    evidence = as_dict(case.get("evidence_snapshot"))
    prompts = as_list(case.get("round1_review_prompts"))
    return [
        f"案由：{compact(review.get('plain_case_brief') or review.get('question'), 140)}",
        f"原回答：风险包括 {compact('、'.join(map(str, as_list(original.get('risk_types')))) or original.get('excerpt'), 120)}",
        f"证据状态：{compact(evidence.get('support_status_label') or evidence.get('support_status'), 100)}",
        f"关键缺口：{top_evidence_gap(case)}",
        f"建议倾向：{TENDENCY_LABELS.get(tendency, tendency)}",
        f"建议根因：{', '.join(roots) if roots else '暂不建议直接确认根因'}",
        f"建议动作：{', '.join(actions) if actions else '先人工判断，不直接进入治理动作'}",
        f"你只需确认：{compact(prompts[0] if prompts else '该辅助建议是否符合你的人工判断', 120)}",
    ]


def build_case_aid(case: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    roots_allowed = allowed_values(contract, "confirmed_root_causes")
    actions_allowed = allowed_values(contract, "confirmed_follow_up_actions")
    tendency = suggest_tendency(case)
    roots = suggest_root_causes(signal_codes(case), roots_allowed)
    actions = suggest_actions(roots, actions_allowed)
    return {
        "case_id": case.get("case_id"),
        "rank": case.get("rank"),
        "mobile_card_title": f"{case.get('rank')}. {case.get('case_id')}",
        "mobile_case_brief": compact(as_dict(case.get("case_under_review")).get("plain_case_brief"), 180),
        "mobile_attention_level": case.get("round1_attention_level"),
        "mobile_review_lines": mobile_lines(case, tendency, roots, actions),
        "mobile_advisory_tendency": tendency,
        "mobile_advisory_tendency_label": TENDENCY_LABELS.get(tendency, tendency),
        "mobile_advisory_root_cause_codes": roots,
        "mobile_advisory_follow_up_action_codes": actions,
        "mobile_advisory_rationale": (
            "当前支持包显示主争点或关键证据存在缺口。该建议仅用于减少手机端阅读负担，"
            "不能替代你的人工确认；如你不同意，应在网页工作台中选择其他结论。"
        ),
        "mobile_evidence_gap_summary": top_evidence_gap(case),
        "mobile_review_focus_points": as_list(case.get("round1_review_prompts"))[:3],
        "mobile_suggested_questions": as_list(case.get("round1_review_prompts"))[:2],
        "mobile_user_confirmation_required": True,
        "mobile_not_reviewer_decision": True,
        "mobile_source_packet": "pilot_manual_review_round1_support_report",
    }


def build_report(
    round1_support_path: Path = DEFAULT_ROUND1_SUPPORT_PATH,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    round1 = load_json(round1_support_path)
    contract = load_json(contract_path)
    cards = [
        build_case_aid(case, contract)
        for case in as_list(round1.get("round1_cases"))
        if isinstance(case, dict)
    ]
    tendency_counter = Counter(card["mobile_advisory_tendency"] for card in cards)
    report = {
        "version": VERSION,
        "schema_kind": "advisory_mobile_pilot_review_decision_aid",
        "contains_completed_manual_decisions": False,
        "advisory_packet_only": True,
        "scope": "mobile pilot review decision aid",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "round1_support_report": source_meta(round1_support_path, round1),
            "visual_workbench_contract": source_meta(contract_path, contract),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "mobile_cards": len(cards),
            "user_confirmation_needed_cases": len(cards),
            "completed_manual_decisions": 0,
            "promotion_candidates": 0,
            "ready_action_candidates": 0,
            "mobile_advisory_tendency_summary": dict(sorted(tendency_counter.items())),
            "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
        },
        "mobile_cards": cards,
        "next_user_action": {
            "open_visual_workbench": "tools/manual_review_visual_workbench/index.html",
            "queue": "pilot_batch",
            "instruction": "Use each mobile card as a pre-read checklist, then manually confirm or change the decision in the visual workbench.",
            "not_importable_as_manual_review": True,
        },
    }
    dangerous_keys = sorted(DANGEROUS_OUTPUT_KEYS & set(recursive_key_scan(report)))
    if dangerous_keys:
        raise ValueError(f"mobile decision aid contains dangerous import keys: {dangerous_keys}")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# v0.4.7.8.20 Mobile Pilot Review Decision Aid",
        "",
        "## 定位",
        "",
        "这是手机端确认前草稿，用来减少远程操作时的阅读负担。它不是人工复核结论，不会写入可导入字段，也不能直接进入 dry-run。",
        "",
        "## 摘要",
        "",
        f"- 手机卡片：{summary['mobile_cards']}",
        f"- 需要用户确认：{summary['user_confirmation_needed_cases']}",
        f"- Completed manual decisions：{summary['completed_manual_decisions']}",
        f"- Promotion candidates：{summary['promotion_candidates']}",
        f"- Ready action candidates：{summary['ready_action_candidates']}",
        f"- Gate status：`{summary['gate_status']}`",
        "",
        "## 手机复核卡片",
        "",
    ]
    for card in report["mobile_cards"]:
        lines.extend([f"### {card['mobile_card_title']}", ""])
        lines.extend(f"- {line}" for line in card["mobile_review_lines"])
        lines.extend(
            [
                f"- 确认前草稿：`{card['mobile_advisory_tendency']}`",
                f"- 建议理由：{card['mobile_advisory_rationale']}",
                "- 边界：这不是人工复核结论；你可以同意、修改或驳回。",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 本报告不写 `reviewer_input_template`。",
            "- 本报告不生成 `reviewer_decision` 或 completed manual decision。",
            "- 本报告不生成 promotion candidate 或 ready action candidate。",
            "- 本报告不接入 `rag_query`、后端 API、Qdrant 或 LLM。",
            "- 本报告不修改 hidden seed、anchor、rerank、prompt、risk supplement、term preservation、scenario registry 或 eval case。",
            "- 真正结论必须由用户在 visual workbench 中确认或修改。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a mobile-friendly advisory decision aid for pilot review.")
    parser.add_argument("--round1-support", type=Path, default=DEFAULT_ROUND1_SUPPORT_PATH)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.round1_support, args.contract)
    write_json(args.output, report)
    write_text(args.markdown_output, render_markdown(report))
    summary = report["summary"]
    print(
        "Mobile pilot review decision aid built: "
        f"{summary['mobile_cards']} cards, "
        f"{summary['user_confirmation_needed_cases']} need confirmation, "
        f"gate={summary['gate_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
