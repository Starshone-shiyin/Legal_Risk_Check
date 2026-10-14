"""Risk report generation built on top of risk analysis."""

from __future__ import annotations

import copy
import json
from typing import Any

from src.core.citations import (
    assess_citation_coverage,
    citation_coverage_messages,
    citation_failure_messages,
    verify_citation_integrity,
)
from src.risk.analyzer import analyze_risk


def generate_risk_report(
    scenario: str,
    **kwargs,
) -> dict[str, Any]:
    """Run risk analysis and convert it into a business-facing report."""
    analysis = analyze_risk(scenario, **kwargs)
    return build_risk_report(analysis)


def generate_risk_report_export(
    scenario: str,
    export_format: str = "markdown",
    include_evidence_chain: bool = True,
    include_source_analysis: bool = False,
    **kwargs,
) -> str | dict[str, Any]:
    """Run risk analysis and export the report in a presentation-friendly format."""
    report = generate_risk_report(scenario, **kwargs)
    return export_risk_report(
        report,
        export_format=export_format,
        include_evidence_chain=include_evidence_chain,
        include_source_analysis=include_source_analysis,
    )


def build_risk_report(analysis: dict[str, Any]) -> dict[str, Any]:
    """Build a stable report structure from an analyze_risk result."""
    risk_findings = build_risk_findings(analysis)
    action_plan = build_action_plan(analysis)
    confidence = analysis.get("confidence", {})
    base_report = {
        "title": "企业合规风险分析报告",
        "scenario": analysis.get("scenario", ""),
        "executive_summary": build_executive_summary(analysis),
        "risk_level": analysis.get("risk_level", "medium"),
        "risk_findings": risk_findings,
        "action_plan": action_plan,
        "legal_basis": analysis.get("legal_basis", []),
        "confidence": confidence,
        "evidence_chain": analysis.get("evidence_chain", []),
        "material_sources": analysis.get("material_sources", []),
        "decision_state": analysis.get("decision_state", "assessable"),
        "evidence_guardrail": analysis.get("evidence_guardrail", {}),
        "source_analysis": analysis,
    }
    citation_integrity = build_report_citation_integrity(base_report)
    review_reasons = build_review_reasons(analysis)
    for message in citation_failure_messages(citation_integrity):
        if message not in review_reasons:
            review_reasons.append(message)

    for message in citation_coverage_messages(citation_integrity.get("coverage") or {}):
        if message not in review_reasons:
            review_reasons.append(message)
    base_report["human_review_required"] = (
        bool(analysis.get("needs_human_review"))
        or not citation_integrity.get("passed", True)
        or bool((citation_integrity.get("coverage") or {}).get("requires_review"))
    )
    base_report["review_reasons"] = review_reasons
    base_report["citation_integrity"] = citation_integrity
    return base_report


def build_report_citation_integrity(report: dict[str, Any]) -> dict[str, Any]:
    """Verify that report text citations are backed by legal_basis/evidence_chain."""
    texts = [report.get("executive_summary", "")]
    for finding in report.get("risk_findings", []) or []:
        texts.append(finding.get("analysis", ""))
        texts.extend(finding.get("recommended_actions", []) or [])
    for action in report.get("action_plan", []) or []:
        texts.append(action.get("action", ""))

    supported_items = list(report.get("legal_basis", []) or []) + list(report.get("evidence_chain", []) or [])
    integrity = verify_citation_integrity(texts, supported_items)
    integrity["coverage"] = assess_citation_coverage(texts, supported_items)
    return integrity


def export_risk_report(
    report: dict[str, Any],
    export_format: str = "markdown",
    include_evidence_chain: bool = True,
    include_source_analysis: bool = False,
) -> str | dict[str, Any]:
    """Export a built risk report as markdown text or a trimmed JSON-ready dict."""
    export_format = export_format.lower().strip()
    exportable = build_exportable_report(
        report,
        include_evidence_chain=include_evidence_chain,
        include_source_analysis=include_source_analysis,
    )
    if export_format in {"md", "markdown"}:
        return render_risk_report_markdown(exportable)
    if export_format == "json":
        return exportable
    raise ValueError("export_format must be 'markdown' or 'json'")


def build_exportable_report(
    report: dict[str, Any],
    include_evidence_chain: bool = True,
    include_source_analysis: bool = False,
) -> dict[str, Any]:
    """Return a report copy suitable for export without always exposing heavy internals."""
    exportable = copy.deepcopy(report)
    if not include_evidence_chain:
        exportable.pop("evidence_chain", None)
    if not include_source_analysis:
        exportable.pop("source_analysis", None)
    return exportable


def render_risk_report_markdown(report: dict[str, Any]) -> str:
    """Render a risk report as deterministic Markdown for demos and review artifacts."""
    lines = [
        f"# {report.get('title') or '企业合规风险分析报告'}",
        "",
        "## 一、场景描述",
        safe_text(report.get("scenario")),
        "",
        "## 二、执行摘要",
        safe_text(report.get("executive_summary")),
        "",
        "## 三、风险等级",
        f"`{report.get('risk_level', 'medium')}`",
        "",
        "## 四、风险发现",
    ]

    findings = report.get("risk_findings") or []
    if findings:
        for index, finding in enumerate(findings, start=1):
            lines.extend(render_finding_markdown(index, finding))
    else:
        lines.append("- 未识别出结构化风险发现。")

    lines.extend([
        "",
        "## 五、整改行动计划",
    ])
    action_plan = report.get("action_plan") or []
    if action_plan:
        lines.extend(render_action_plan_markdown(action_plan))
    else:
        lines.append("- 暂无整改动作。")

    lines.extend([
        "",
        "## 六、法律与标准依据",
    ])
    lines.extend(render_legal_basis_markdown(report.get("legal_basis") or []))

    lines.extend([
        "",
        "## 七、置信度与复核",
    ])
    lines.extend(render_confidence_markdown(report))

    evidence_chain = report.get("evidence_chain") or []
    if evidence_chain:
        lines.extend([
            "",
            "## 八、证据链摘要",
        ])
        lines.extend(render_evidence_markdown(evidence_chain))

    return "\n".join(lines).strip() + "\n"


def render_finding_markdown(index: int, finding: dict[str, Any]) -> list[str]:
    lines = [
        f"### {index}. {safe_text(finding.get('risk_type'))}",
        f"- 风险等级：`{finding.get('risk_level', 'medium')}`",
        f"- 分析：{safe_text(finding.get('analysis'))}",
    ]
    basis = finding.get("legal_basis") or []
    if basis:
        lines.append("- 相关依据：")
        lines.extend(f"  - {format_basis_item(item)}" for item in basis)
    actions = finding.get("recommended_actions") or []
    if actions:
        lines.append("- 建议动作：")
        lines.extend(f"  - {safe_text(action)}" for action in actions)
    return lines


def render_action_plan_markdown(action_plan: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| 优先级 | 建议动作 | 负责方提示 | 依据 |",
        "| --- | --- | --- | --- |",
    ]
    for item in action_plan:
        basis = "；".join(format_basis_item(basis_item) for basis_item in item.get("basis", [])) or "-"
        lines.append(
            "| "
            f"{escape_table_cell(item.get('priority', 'P1'))} | "
            f"{escape_table_cell(item.get('action', ''))} | "
            f"{escape_table_cell(item.get('owner_hint', ''))} | "
            f"{escape_table_cell(basis)} |"
        )
    return lines


def render_legal_basis_markdown(legal_basis: list[dict[str, Any]]) -> list[str]:
    if not legal_basis:
        return ["- 暂无可展示依据。"]
    return [f"- {format_basis_item(item)}" for item in legal_basis]


def render_confidence_markdown(report: dict[str, Any]) -> list[str]:
    confidence = report.get("confidence") or {}
    review_required = "是" if report.get("human_review_required") else "否"
    lines = [
        f"- 回答置信度：{format_score(confidence.get('answer'))}",
        f"- 检索置信度：{format_score(confidence.get('retrieval'))}",
        f"- 整体置信度：{format_score(confidence.get('overall'))}",
        f"- 是否建议人工复核：{review_required}",
    ]
    reasons = report.get("review_reasons") or []
    if reasons:
        lines.append("- 复核原因：")
        lines.extend(f"  - {safe_text(reason)}" for reason in reasons)
    return lines


def render_evidence_markdown(evidence_chain: list[dict[str, Any]], limit: int = 8) -> list[str]:
    lines = []
    for index, item in enumerate(evidence_chain[:limit], start=1):
        score = item.get("rerank_score", item.get("similarity_score"))
        score_text = f"，score={score:.4f}" if isinstance(score, (int, float)) else ""
        lines.append(f"- {index}. {format_basis_item(item)}{score_text}")
    if len(evidence_chain) > limit:
        lines.append(f"- 其余 {len(evidence_chain) - limit} 条证据已省略。")
    return lines


def format_basis_item(item: dict[str, Any]) -> str:
    citation = item.get("citation")
    if citation:
        return safe_text(citation)
    source = item.get("law_name") or item.get("source") or "未知来源"
    article = item.get("article") or item.get("section_no") or item.get("article_no") or ""
    return safe_text(f"{source} {article}".strip())


def format_score(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "未知"


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).replace("\r\n", "\n").strip()


def escape_table_cell(value: Any) -> str:
    return safe_text(value).replace("|", "\\|").replace("\n", "<br>")


def build_executive_summary(analysis: dict[str, Any]) -> str:
    risk_level = analysis.get("risk_level", "medium")
    risk_types = analysis.get("risk_types", [])
    confidence = analysis.get("confidence", {})
    overall = confidence.get("overall")

    if analysis.get("decision_state") == "pending_evidence":
        return "现有证据与风险领域不匹配或引用校验未通过，暂不形成风险等级或具体领域标签，需补充法源后人工复核。"
    if risk_types:
        risk_phrase = "、".join(risk_types[:3])
    else:
        risk_phrase = "未识别出明确重大风险"

    confidence_text = f"，整体置信度为 {overall}" if overall is not None else ""
    return f"经初步分析，该场景风险等级为 {risk_level}，主要涉及{risk_phrase}{confidence_text}。"


def build_risk_findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    risk_types = analysis.get("risk_types", [])
    categories = analysis.get("risk_categories", [])
    legal_basis = analysis.get("legal_basis", [])
    actions = analysis.get("recommended_actions", [])
    risk_evidence = {item.get("text"): item.get("citations", []) for item in analysis.get("risk_type_evidence", [])}

    if not risk_types and analysis.get("risk_level") == "low":
        return [{
            "risk_type": "未识别出明确重大风险",
            "risk_level": "low",
            "analysis": analysis.get("summary", ""),
            "legal_basis": legal_basis,
            "recommended_actions": actions,
        }]

    findings = []
    for risk_type in risk_types:
        matched_category = find_matching_category(risk_type, categories)
        findings.append({
            "risk_type": risk_type,
            "risk_level": matched_category.get("default_level", analysis.get("risk_level", "medium")) if matched_category else analysis.get("risk_level", "medium"),
            "analysis": build_finding_analysis(risk_type, analysis, matched_category),
            "legal_basis": select_legal_basis_for_citations(
                legal_basis,
                risk_evidence.get(risk_type, []),
            ),
            "recommended_actions": select_recommended_actions(risk_type, analysis),
        })
    return findings


def build_action_plan(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    actions = analysis.get("recommended_actions", [])
    action_evidence = {
        item.get("text"): item.get("citations", [])
        for item in analysis.get("recommended_action_evidence", [])
    }
    legal_basis = analysis.get("legal_basis", [])
    risk_level = analysis.get("risk_level", "medium")

    plan = []
    for index, action in enumerate(actions, start=1):
        plan.append({
            "priority": priority_for_action(index, risk_level),
            "action": action,
            "owner_hint": infer_owner_hint(action),
            "basis": select_legal_basis_for_citations(legal_basis, action_evidence.get(action, [])),
        })
    return plan


def build_review_reasons(analysis: dict[str, Any]) -> list[str]:
    reasons = list(analysis.get("missing_evidence", []))
    confidence = analysis.get("confidence", {})
    overall = confidence.get("overall")
    if overall is not None and overall < 0.7:
        reasons.append("整体置信度低于 0.7")
    if analysis.get("risk_level") == "high" and overall is not None and overall < 0.8:
        reasons.append("高风险场景置信度不足 0.8")
    return dedupe_texts(reasons)


def build_finding_analysis(
    risk_type: str,
    analysis: dict[str, Any],
    category: dict[str, Any] | None,
) -> str:
    if category:
        keywords = category.get("matched_keywords", [])
        keyword_text = f"，命中关键词：{'、'.join(keywords[:5])}" if keywords else ""
        return f"该场景涉及{category.get('name', risk_type)}{keyword_text}。{analysis.get('summary', '')}"
    return analysis.get("summary", "")


def find_matching_category(risk_type: str, categories: list[dict[str, Any]]) -> dict[str, Any] | None:
    for category in categories:
        name = category.get("name", "")
        if name and (name in risk_type or risk_type in name):
            return category
    for category in categories:
        if any(keyword in risk_type for keyword in category.get("matched_keywords", [])):
            return category
    return None


def select_legal_basis_for_citations(
    legal_basis: list[dict[str, Any]],
    citations: list[str],
    fallback_limit: int = 3,
) -> list[dict[str, Any]]:
    if citations:
        selected = [basis for basis in legal_basis if basis.get("citation") in citations]
        if selected:
            return selected
    return legal_basis[:fallback_limit]


def select_recommended_actions(risk_type: str, analysis: dict[str, Any], limit: int = 3) -> list[str]:
    actions = analysis.get("recommended_actions", [])
    matched = []
    for action in actions:
        if any(term in action for term in extract_terms(risk_type)):
            matched.append(action)
    return (matched or actions)[:limit]


def extract_terms(text: str) -> list[str]:
    return [term for term in ["同意", "告知", "出境", "安全", "算法", "儿童", "匿名化", "最小必要", "第三方", "泄露"] if term in text]


def priority_for_action(index: int, risk_level: str) -> str:
    if risk_level == "high" and index <= 2:
        return "P0"
    if risk_level in {"high", "medium"}:
        return "P1"
    return "P2"


def infer_owner_hint(action: str) -> str:
    if any(term in action for term in ["告知", "同意", "隐私政策", "用户"]):
        return "产品/法务/合规"
    if any(term in action for term in ["安全", "权限", "日志", "匿名化", "评估"]):
        return "安全/数据治理"
    if any(term in action for term in ["算法", "自动化决策", "人工复核"]):
        return "算法/产品/合规"
    if any(term in action for term in ["监管", "申报", "出境", "标准合同"]):
        return "法务/合规"
    return "业务负责人/合规"


def dedupe_texts(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
