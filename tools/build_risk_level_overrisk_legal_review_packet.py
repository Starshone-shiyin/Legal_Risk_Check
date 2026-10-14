"""Build a saved-report-only legal review packet for over-risk cases.

This tool reads existing RAG eval and attribution reports. It does not run
eval, call rag_query, contact Qdrant or an LLM, or mutate retrieval, rerank,
prompts, anchors, risk rules, eval cases, scenario registry, or hidden seeds.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.24"

DEFAULT_EVAL_REPORT_PATH = Path("tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json")
DEFAULT_ATTRIBUTION_REPORT_PATH = Path("tests/risk_level_overrisk_attribution_v0.4.15.23_report.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_SCENARIO_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_OUTPUT_PATH = Path("tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json")

GUARDRAILS = {
    "saved_reports_only": True,
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "taxonomy_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, *, optional: bool = False) -> dict[str, Any]:
    if optional and not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def expected_risk_level_check(report: dict[str, Any]) -> dict[str, Any]:
    for check in as_list(report.get("checks")):
        if isinstance(check, dict) and check.get("name") == "expected_risk_level":
            return check
    return {}


def risk_level_details(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(expected_risk_level_check(report).get("details"))


def is_over_risk(report: dict[str, Any]) -> bool:
    details = risk_level_details(report)
    return details.get("policy") == "exact" and details.get("mismatch_type") == "over_risk"


def norm_text(*parts: Any) -> str:
    chunks: list[str] = []
    for part in parts:
        if isinstance(part, str):
            chunks.append(part)
        elif isinstance(part, list):
            chunks.extend(str(item) for item in part if item is not None)
        elif isinstance(part, dict):
            chunks.extend(str(item) for item in part.values() if item is not None)
        elif part is not None:
            chunks.append(str(part))
    return " ".join(chunks)


def any_term(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def evidence_refs(report: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for item in as_list(report.get("evidence")):
        if not isinstance(item, dict):
            continue
        refs.append({
            "source": item.get("source") or item.get("law_name"),
            "article_no": item.get("article_no"),
            "section_no": item.get("section_no"),
            "citation": item.get("citation"),
        })
    return refs


def expected_refs(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"source": item.get("source"), "article_no": item.get("article_no")}
        for item in as_list(case.get("expected_evidence"))
        if isinstance(item, dict)
    ]


def build_case_maps(cases_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("id")): case
        for case in as_list(cases_payload.get("cases"))
        if isinstance(case, dict) and case.get("id")
    }


def build_attribution_map(attribution_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("case_id") or row.get("id")): row
        for row in as_list(attribution_payload.get("case_rows"))
        if isinstance(row, dict) and (row.get("case_id") or row.get("id"))
    }


def scenario_rows_for_case(scenario_payload: dict[str, Any], case_id: str) -> list[dict[str, Any]]:
    rows = []
    for scenario in as_list(scenario_payload.get("scenarios")):
        if not isinstance(scenario, dict):
            continue
        if case_id in [str(item) for item in as_list(scenario.get("eval_case_ids"))]:
            rows.append({
                "scenario_id": scenario.get("scenario_id"),
                "domain": scenario.get("domain"),
                "risk_level": scenario.get("risk_level"),
                "risk_types": as_list(scenario.get("risk_types")),
                "required_actions": as_list(scenario.get("required_actions")),
            })
    return rows


def classify_legal_review(
    report: dict[str, Any],
    case: dict[str, Any],
    attribution: dict[str, Any],
) -> dict[str, Any]:
    text = norm_text(
        report.get("question"),
        report.get("answer"),
        report.get("risk_types"),
        report.get("recommended_actions"),
        case.get("expected_answer_keywords"),
        case.get("expected_risk_types"),
        case.get("expected_actions"),
        case.get("legal_reasoning"),
        case.get("risk_level_reason"),
    )
    actual_level = risk_level_details(report).get("actual_level") or report.get("risk_level")
    expected_level = risk_level_details(report).get("expected_level") or case.get("expected_risk_level")
    broad_output = len(as_list(report.get("risk_types"))) >= 4 or len(as_list(report.get("recommended_actions"))) >= 5
    attribution_routes = as_list(attribution.get("review_routes") or attribution.get("suspected_root_causes"))

    signals: list[str] = []
    if actual_level == "high" and expected_level == "medium":
        signals.append("exact_policy_high_vs_expected_medium")
    if broad_output:
        signals.append("broad_risk_or_action_output")
    if attribution_routes:
        signals.append("attribution_routes_available")

    if any_term(text, ["连续三年", "三年不使用", "未实际使用", "撤销"]) and any_term(text, ["商标"]):
        return {
            "legal_reasonableness": "actual_high_likely_overstated",
            "legal_review_confidence": "high",
            "manual_review_priority": 1,
            "legal_signals": signals + ["trademark_non_use_is_procedural_cancellation_risk"],
            "legal_reasoning_summary": (
                "现有事实更像连续三年不使用触发的商标撤销风险。该风险成立，但通常是条件触发型、程序型风险；"
                "在缺少核心资产、重大损失或恶意规避等事实时，直接定为 high 偏重。"
            ),
            "recommended_next_step": "review_output_rule_or_wording_to_prevent_high_escalation",
        }

    if any_term(text, ["通用名称", "显著性"]) and any_term(text, ["商标", "独占"]):
        return {
            "legal_reasonableness": "actual_high_likely_overstated",
            "legal_review_confidence": "high",
            "manual_review_priority": 1,
            "legal_signals": signals + ["generic_name_distinctiveness_invalidity_risk"],
            "legal_reasoning_summary": (
                "行业通用名称缺乏显著性并被独占使用，核心法律后果更接近注册受阻、无效或正当使用抗辩。"
                "除非事实显示恶意维权、重大市场混淆或实质损害，high 定级通常偏重。"
            ),
            "recommended_next_step": "review_output_rule_or_taxonomy_escalation_for_ip_invalidity_cases",
        }

    if any_term(text, ["低税率", "少缴税款", "补缴", "滞纳金", "税率适用"]) and any_term(text, ["增值税", "混合销售", "分别核算"]):
        return {
            "legal_reasonableness": "actual_high_potentially_defensible",
            "legal_review_confidence": "medium",
            "manual_review_priority": 3,
            "legal_signals": signals + ["tax_underpayment_or_rate_misapplication_signal"],
            "legal_reasoning_summary": (
                "未区分收入并统一按低税率纳税，可能直接指向少缴税款、补税和滞纳金。high 有一定法律语义基础；"
                "但若缺少金额、持续性、主观故意或处罚事实，expected medium 也可成立。"
            ),
            "recommended_next_step": "manual_review_expected_level_before_rule_change",
        }

    if any_term(text, ["知名品牌", "误认", "混淆"]) and any_term(text, ["不正当竞争", "赔偿", "行政处罚", "装修风格", "店铺名称"]):
        return {
            "legal_reasonableness": "actual_high_potentially_defensible",
            "legal_review_confidence": "medium",
            "manual_review_priority": 3,
            "legal_signals": signals + ["confusion_with_known_brand_and_liability_signal"],
            "legal_reasoning_summary": (
                "事实已经包含知名品牌近似和消费者误认，接近混淆行为核心要件；若混淆影响明确，high 可能成立。"
                "若只是外观接近而损害或影响较弱，则 expected medium 更稳妥。"
            ),
            "recommended_next_step": "manual_review_fact_strength_before_rule_change",
        }

    if any_term(text, ["物业", "业主", "公共区域", "共有部分", "共有财产"]):
        return {
            "legal_reasonableness": "expected_medium_likely_reasonable",
            "legal_review_confidence": "medium",
            "manual_review_priority": 2,
            "legal_signals": signals + ["owner_common_property_consent_risk"],
            "legal_reasoning_summary": (
                "未经业主同意使用共有部分确有违法和返还收益等后果，但主轴偏民事合规、共有权和物业管理纠纷。"
                "在缺少严重侵占、重大损害或持续恶意事实时，medium 更合理；high 属偏高但不一定完全错误。"
            ),
            "recommended_next_step": "review_answer_wording_and_action_scope_before_rule_change",
        }

    return {
        "legal_reasonableness": "manual_review_required",
        "legal_review_confidence": "low",
        "manual_review_priority": 4,
        "legal_signals": signals or ["insufficient_saved_report_legal_signal"],
        "legal_reasoning_summary": "saved report 和 eval metadata 不足以形成稳定法律初判，需要人工复核事实强度和预期等级。",
        "recommended_next_step": "manual_review_required_before_rule_change",
    }


def build_case_row(
    report: dict[str, Any],
    case: dict[str, Any],
    attribution: dict[str, Any],
    scenario_payload: dict[str, Any],
) -> dict[str, Any]:
    details = risk_level_details(report)
    case_id = str(report.get("id"))
    legal = classify_legal_review(report, case, attribution)
    review_reasons = [
        "严格风险等级口径下 actual=high、expected=medium，需要确认是答案过度放大还是 expected level 本身偏保守。",
        legal["legal_reasoning_summary"],
    ]
    if attribution:
        review_reasons.append(str(attribution.get("review_reason") or "v0.4.15.23 attribution signal is available."))

    return {
        "case_id": case_id,
        "category": report.get("category") or case.get("category") or "uncategorized",
        "question": report.get("question") or case.get("question"),
        "passed": bool(report.get("passed")),
        "retrieval_failure_stage": report.get("retrieval_failure_stage"),
        "expected_level": details.get("expected_level") or case.get("expected_risk_level"),
        "actual_level": details.get("actual_level") or report.get("risk_level"),
        "mismatch_type": details.get("mismatch_type"),
        "expected_risk_types": as_list(case.get("expected_risk_types")),
        "actual_risk_types": as_list(report.get("risk_types")),
        "expected_actions": as_list(case.get("expected_actions")),
        "actual_actions": as_list(report.get("recommended_actions")),
        "expected_evidence_refs": expected_refs(case),
        "final_evidence_refs": evidence_refs(report),
        "attribution": {
            "primary_attribution": attribution.get("primary_attribution"),
            "review_routes": as_list(attribution.get("review_routes")),
            "confidence": attribution.get("confidence"),
            "output_contribution_counts": as_dict(attribution.get("output_contribution_counts")),
        },
        "scenario_registry_matches": scenario_rows_for_case(scenario_payload, case_id),
        "legal_reasonableness": legal["legal_reasonableness"],
        "legal_review_confidence": legal["legal_review_confidence"],
        "manual_review_priority": legal["manual_review_priority"],
        "legal_signals": legal["legal_signals"],
        "legal_reasoning_summary": legal["legal_reasoning_summary"],
        "review_reasons": review_reasons,
        "recommended_next_step": legal["recommended_next_step"],
        "rule_change_allowed": False,
    }


def build_report(
    eval_report_path: Path = DEFAULT_EVAL_REPORT_PATH,
    attribution_report_path: Path = DEFAULT_ATTRIBUTION_REPORT_PATH,
    cases_path: Path = DEFAULT_CASES_PATH,
    scenario_registry_path: Path | None = DEFAULT_SCENARIO_REGISTRY_PATH,
) -> dict[str, Any]:
    eval_report = load_json(eval_report_path)
    attribution_report = load_json(attribution_report_path, optional=True)
    cases_payload = load_json(cases_path)
    scenario_payload = load_json(scenario_registry_path, optional=True) if scenario_registry_path else {}

    case_map = build_case_maps(cases_payload)
    attribution_map = build_attribution_map(attribution_report)
    rows = [
        build_case_row(report, case_map.get(str(report.get("id")), {}), attribution_map.get(str(report.get("id")), {}), scenario_payload)
        for report in as_list(eval_report.get("reports"))
        if isinstance(report, dict) and is_over_risk(report)
    ]
    rows.sort(key=lambda row: (int(row["manual_review_priority"]), str(row["case_id"])))

    legal_counts = Counter(str(row["legal_reasonableness"]) for row in rows)
    priority_counts = Counter(str(row["manual_review_priority"]) for row in rows)
    domain_counts = Counter(str(row["category"]) for row in rows)

    return {
        "version": VERSION,
        "schema_kind": "risk_level_overrisk_legal_review_packet",
        "scope": "saved-report-only preliminary legal review packet for exact-policy over-risk cases",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "eval_report": str(eval_report_path),
            "attribution_report": str(attribution_report_path),
            "cases": str(cases_path),
            "scenario_registry": str(scenario_registry_path) if scenario_registry_path else None,
            "eval_report_profile": eval_report.get("report_profile"),
            "source_total": eval_report.get("total"),
            "source_passed": eval_report.get("passed"),
            "source_failed": eval_report.get("failed"),
            "source_retrieval_failure_stage_summary": eval_report.get("retrieval_failure_stage_summary", {}),
            "source_risk_level_mismatch_summary": eval_report.get("risk_level_mismatch_summary", {}),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": "legal_review_packet_ready" if rows else "no_overrisk_cases",
            "overrisk_case_count": len(rows),
            "legal_reasonableness_counts": dict(legal_counts),
            "manual_review_priority_counts": dict(priority_counts),
            "domain_counts": dict(domain_counts),
            "high_risk_manual_review_list": [row["case_id"] for row in rows if int(row["manual_review_priority"]) <= 2],
            "all_manual_review_list": [row["case_id"] for row in rows],
            "rule_change_allowed": False,
            "expected_next_step": "manual_review_or_targeted_full_trace_before_risk_rule_change",
        },
        "case_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build saved-report-only over-risk legal review packet.")
    parser.add_argument("--eval-report", type=Path, default=DEFAULT_EVAL_REPORT_PATH)
    parser.add_argument("--attribution-report", type=Path, default=DEFAULT_ATTRIBUTION_REPORT_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--scenario-registry", type=Path, default=DEFAULT_SCENARIO_REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.eval_report, args.attribution_report, args.cases, args.scenario_registry)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Risk-level over-risk legal review packet completed: "
        f"{summary['status']}, "
        f"{summary['overrisk_case_count']} cases, "
        f"rule_change_allowed={summary['rule_change_allowed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
