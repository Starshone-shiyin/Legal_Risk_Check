from __future__ import annotations

import re
from typing import Any

from src.core.citations import verify_citation_integrity
from src.rag.evidence import build_supported_items

PIPL_LAW_NAME = "中华人民共和国个人信息保护法"
DATA_EXPORT_MEASURES_NAME = "数据出境安全评估办法"


def append_unique_texts(values: list[str], items: list[str]) -> list[str]:
    for item in items:
        if item and not any(item in value or value in item for value in values):
            values.append(item)
    return values


def is_complex_multi_issue_question(question: str) -> bool:
    markers = ["公司背景", "事件经过", "问题清单", "融资尽调", "IPO", "序号", "事件1", "事件2"]
    if any(marker in question for marker in markers):
        return True
    numbered_questions = len(re.findall(r"(?:^|\n)\s*(?:\d+|[一二三四五六七八九十]+)[\.、\s]", question))
    if numbered_questions >= 3:
        return True
    return len(question) >= 900 and question.count("？") + question.count("?") >= 3


def extract_complex_case_issues(question: str, limit: int = 12) -> list[str]:
    """Extract user-numbered legal issues from a long case prompt."""
    issue_lines: list[str] = []
    lines = [line.strip() for line in question.splitlines() if line.strip()]
    pattern = re.compile(r"^(?:问题\s*)?(?:\d+|[一二三四五六七八九十]+)[\.、\s]+(.+)")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        text = match.group(1).strip()
        if len(text) < 8:
            continue
        issue_lines.append(text)
    if issue_lines:
        return issue_lines[:limit]

    fallback_markers = ["是否", "能否", "如何", "应如何", "哪几个", "哪些", "怎么办", "优先"]
    clauses = re.split(r"[？?]\s*", question)
    for clause in clauses:
        clause = clause.strip(" ；;。")
        if len(clause) < 12 or not any(marker in clause for marker in fallback_markers):
            continue
        issue_lines.append(clause[-260:])
    return issue_lines[:limit]


def _issue_contains(issue: str, terms: list[str]) -> bool:
    return any(term in issue for term in terms)


def plan_complex_case_issues(question: str) -> list[dict[str, Any]]:
    issues = extract_complex_case_issues(question)
    if not issues:
        issues = [question[:500]]

    case_context_missing: list[str] = []
    case_context_domains: list[str] = []
    if _issue_contains(question, ["医疗影像", "AI诊断", "三甲医院", "辅助诊断", "肺结节", "乳腺癌", "眼底"]):
        case_context_domains.append("医疗监管")
        case_context_missing.extend(["医疗器械监督管理条例", "医疗 AI/辅助诊断软件注册审评规则"])
    if _issue_contains(question, ["信贷", "信用评分", "消费金融", "银行", "征信"]):
        case_context_domains.append("金融合规")
        case_context_missing.extend(["征信业管理条例", "金融消费者权益保护相关监管规则"])

    plans: list[dict[str, Any]] = []
    for index, issue in enumerate(issues, start=1):
        anchors: dict[str, list[int]] = {}
        missing: list[str] = list(case_context_missing)
        retrieval_terms: list[str] = []
        domains: list[str] = list(case_context_domains)

        if _issue_contains(issue, ["患者", "影像", "医疗", "病历", "个人信息", "身份证", "姓名", "用户画像", "车辆位置", "行驶轨迹", "驾驶习惯", "消费行为", "设备指纹", "手机号", "收入"]):
            domains.append("数据合规")
            anchors.setdefault(PIPL_LAW_NAME, []).extend([6, 13, 14, 17, 23, 28, 29, 51, 55, 56])
            retrieval_terms.extend(["个人信息处理", "告知同意", "敏感个人信息", "目的限制", "最小必要", "第三方提供"])
        if _issue_contains(issue, ["出境", "境外", "新加坡", "AWS", "跨境"]):
            domains.append("数据出境")
            anchors.setdefault(PIPL_LAW_NAME, []).extend([38, 39, 55])
            anchors.setdefault(DATA_EXPORT_MEASURES_NAME, []).extend([4, 5])
            retrieval_terms.extend(["个人信息出境", "安全评估", "境外接收方", "单独同意"])
        if _issue_contains(issue, ["自动化决策", "算法歧视", "差异化定价", "漏检率", "低评分", "农村户籍", "系统性偏低", "公平", "偏见"]):
            domains.append("算法治理")
            anchors.setdefault(PIPL_LAW_NAME, []).extend([24, 48])
            retrieval_terms.extend(["自动化决策", "公平公正", "解释说明", "人工复核", "算法歧视"])
        if _issue_contains(issue, ["模型权重", "权重文件", "设计文档", "RTL", "综合脚本", "核心算法", "核心模型", "技术秘密", "商业秘密", "离职", "竞对", "个人网盘", "移动硬盘", "带走"]):
            domains.append("商业秘密")
            anchors.setdefault("中华人民共和国反不正当竞争法", []).extend([10, 22, 26, 39])
            retrieval_terms.extend(["商业秘密", "技术信息", "经营信息", "保密措施", "违反保密义务", "实质上相同"])
            if _issue_contains(issue, ["竞业", "竞业限制", "补偿金", "月工资", "期限"]):
                missing.append("劳动合同法及竞业限制司法解释/地方裁判规则")
        if _issue_contains(issue, ["市场支配", "拒绝交易", "排他", "排他性", "二选一", "反垄断", "数据垄断", "差别待遇"]):
            domains.append("反垄断")
            anchors.setdefault("中华人民共和国反垄断法", []).extend([3, 7, 9, 22, 23, 24, 50, 57, 60, 62])
            retrieval_terms.extend(["滥用市场支配地位", "拒绝交易", "限定交易", "排他性协议", "数据和算法"])
        if _issue_contains(issue, ["合同", "合作方", "后续使用权", "成果归属", "客户", "赔偿", "道歉", "推广"]):
            domains.append("合同责任")
            anchors.setdefault("中华人民共和国民法典", []).extend([509, 577, 584, 1165])
            retrieval_terms.extend(["合同义务", "违约责任", "赔偿损失", "诚实信用"])
        if _issue_contains(issue, ["开源", "RISC-V", "BSD", "Apache", "闭源", "许可证", "版权声明", "署名"]):
            domains.append("开源合规")
            missing.extend(["中华人民共和国著作权法", "计算机软件保护条例", "BSD 3-Clause 许可证文本", "Apache 2.0 许可证文本"])
            retrieval_terms.extend(["开源许可证", "版权声明", "署名", "NOTICE", "软件著作权"])
        if _issue_contains(issue, ["出口管制", "技术出口", "管制清单", "商务", "NovaSemi", "以色列", "境外服务器", "先进制程"]):
            domains.append("出口管制")
            missing.extend(["中华人民共和国出口管制法", "技术进出口管理条例", "两用物项出口管制清单/技术出口许可规则"])
            retrieval_terms.extend(["出口管制", "技术出口", "管制清单", "最终用户", "最终用途"])
        if _issue_contains(issue, ["融资", "尽调", "上市", "IPO", "科创板", "投资人", "券商", "估值"]):
            domains.append("融资上市")
            missing.extend(["证券法", "科创板股票发行上市审核规则", "IPO 信息披露与重大违法风险规则"])
            retrieval_terms.extend(["融资尽调", "重大风险", "信息披露", "整改时间表"])
        if _issue_contains(issue, ["信贷", "信用评分", "消费金融", "银行", "征信"]):
            domains.append("金融合规")
            missing.extend(["征信业管理条例", "金融消费者权益保护相关监管规则"])
        if _issue_contains(issue, ["医疗影像", "AI诊断", "三甲医院", "辅助诊断", "肺结节", "乳腺癌", "眼底"]):
            domains.append("医疗监管")
            missing.extend(["医疗器械监督管理条例", "医疗 AI/辅助诊断软件注册审评规则"])

        deduped_anchors = {source: sorted(set(numbers)) for source, numbers in anchors.items()}
        plans.append({
            "id": index,
            "issue": issue,
            "domains": list(dict.fromkeys(domains)) or ["综合合规"],
            "anchors": deduped_anchors,
            "missing_laws": list(dict.fromkeys(missing)),
            "query": " ".join([issue] + retrieval_terms),
        })
    return plans


def format_complex_case_plan(plans: list[dict[str, Any]]) -> str:
    lines = ["复杂案例拆解与法规覆盖："]
    for plan in plans:
        lines.append(f"{plan['id']}. {plan['issue']}")
        lines.append(f"   - 识别法域：{'、'.join(plan['domains'])}")
        if plan["anchors"]:
            anchor_text = "；".join(
                f"{source}第{'、'.join(str(num) for num in nums)}条"
                for source, nums in plan["anchors"].items()
            )
            lines.append(f"   - 已入库可检索依据：{anchor_text}")
        if plan["missing_laws"]:
            lines.append(f"   - 当前知识库缺口：{'、'.join(plan['missing_laws'])}")
    return "\n".join(lines)


def _evidence_citations_for_plan(plan: dict[str, Any], evidence_chain: list[dict[str, Any]], limit: int = 5) -> list[str]:
    citations: list[str] = []
    anchors = plan.get("anchors", {})
    for item in evidence_chain:
        source = item.get("source") or item.get("law_name")
        article_no = item.get("article_no")
        if source not in anchors or article_no not in anchors[source]:
            continue
        citation = item.get("citation") or _citation_from_evidence_item(item)
        if citation and citation not in citations:
            citations.append(citation)
        if len(citations) >= limit:
            break
    return citations


def _citation_from_evidence_item(item: dict[str, Any]) -> str:
    source = item.get("law_name") or item.get("source") or "已入库依据"
    article = item.get("article") or item.get("section_no") or item.get("article_no") or ""
    return f"[《{source}》{article}]" if article else f"[《{source}》]"


def _complex_issue_judgment(plan: dict[str, Any]) -> str:
    issue = plan.get("issue", "")
    domains = set(plan.get("domains", []))
    missing = plan.get("missing_laws", [])
    if "出口管制" in domains:
        return "当前知识库缺少出口管制直接依据，不能直接判定是否违规；但技术资料跨境提供应先按技术出口/两用物项路径做许可和最终用途审查。"
    if "开源合规" in domains:
        return "当前知识库缺少著作权、软件保护和具体开源许可证文本，不能直接判断是否违反许可证；应先按许可证原文做组件级审查。"
    if "融资上市" in domains:
        return "当前知识库缺少证券发行和交易所审核规则，不能给出完整上市法定判断；但已识别的未决合规事项应作为融资尽调整改优先项。"
    if "金融合规" in domains or "医疗监管" in domains:
        return "当前知识库缺少该行业专项监管规则，只能给出通用个人信息、算法或商业秘密风险提示。"
    if "商业秘密" in domains:
        return "如相关材料具备秘密性、商业价值且公司已采取保密措施，未经授权备份、带出、披露或在竞对使用，通常具备追究商业秘密责任的基础。"
    if "反垄断" in domains:
        return "需先界定相关市场并判断市场支配地位；若具有支配地位且无正当理由拒绝交易、限定交易或实行差别待遇，存在滥用市场支配地位风险。"
    if "算法治理" in domains:
        return "存在自动化决策公平性和透明度高风险，应进行偏差审计、解释说明和人工复核安排。"
    if "数据合规" in domains or "数据出境" in domains:
        if any(term in issue for term in ["未经", "未取得", "出售", "提供", "推广", "出境", "差异化"]):
            return "该处理活动存在较高不合规风险，需核查合法性基础、告知同意、目的限制、最小必要、敏感个人信息和第三方提供规则。"
        return "该问题涉及个人信息处理合规，应结合处理目的、数据类型、授权范围和第三方流转进行审查。"
    if "合同责任" in domains:
        return "如超出合同授权目的使用客户资料或成果，可能构成违约或侵权，应结合合同条款、保密义务和损害后果判断。"
    return "当前入库依据不足以形成稳定结论，应补充相关法规、合同和事实证据后复核。"


def _complex_issue_actions(plan: dict[str, Any]) -> list[str]:
    domains = set(plan.get("domains", []))
    actions: list[str] = []
    if "出口管制" in domains:
        actions.extend(["暂停相关技术资料跨境传输", "开展出口管制物项分类、最终用户和最终用途审查", "必要时补办许可或向主管部门咨询"])
    if "商业秘密" in domains:
        actions.extend(["固定下载、备份、访问和相似性证据", "核查秘密点、商业价值和保密措施", "申请行为保全或提起商业秘密维权"])
    if "开源合规" in domains:
        actions.extend(["建立开源组件清单/SBOM", "逐项核查许可证义务", "补充版权声明、NOTICE 或替换违规组件"])
    if "数据合规" in domains or "数据出境" in domains:
        actions.extend(["停止超范围处理或第三方提供", "补充告知并取得必要同意/单独同意", "开展个人信息保护影响评估并删除或匿名化违规数据"])
    if "算法治理" in domains:
        actions.extend(["开展模型公平性审计", "补齐代表性样本和标注质量", "提供解释说明和人工复核渠道"])
    if "反垄断" in domains:
        actions.extend(["停止排他性或拒绝交易安排", "准备相关市场、市场份额和正当理由材料", "配合执法调查并提交整改承诺"])
    if "融资上市" in domains:
        actions.extend(["形成专项整改台账", "补充法律意见和尽调底稿", "完成重大风险披露口径"])
    if "合同责任" in domains:
        actions.extend(["核查合同授权边界", "通知客户并协商补救", "补充保密、数据使用和违约责任条款"])
    return list(dict.fromkeys(actions))[:5]


def _complex_issue_risk_types(plan: dict[str, Any]) -> list[str]:
    mapping = {
        "出口管制": "技术出口管制风险",
        "商业秘密": "商业秘密侵权风险",
        "开源合规": "开源许可证合规风险",
        "数据合规": "个人信息处理合规风险",
        "数据出境": "数据出境合规风险",
        "算法治理": "自动化决策与算法歧视风险",
        "反垄断": "滥用市场支配地位风险",
        "融资上市": "融资尽调/IPO合规风险",
        "合同责任": "合同违约与客户资料滥用风险",
        "金融合规": "金融数据/征信合规风险",
        "医疗监管": "医疗AI监管合规风险",
    }
    return [mapping[domain] for domain in plan.get("domains", []) if domain in mapping]


def build_complex_case_fast_payload(
    question: str,
    plans: list[dict[str, Any]],
    evidence_chain: list[dict[str, Any]],
    retrieval_confidence: float,
    missing_evidence: list[str],
    filters: dict,
    debug_info: dict | None = None,
) -> dict[str, Any]:
    lines = ["以下为复杂案例快速审查结果，按问题逐项列示；缺少直接入库法规的部分已降级为风险方向。"]
    all_actions: list[str] = []
    all_risk_types: list[str] = []
    for plan in plans:
        citations = _evidence_citations_for_plan(plan, evidence_chain)
        basis = "、".join(citations) if citations else "当前知识库缺少直接依据或未检索到可引用条文"
        if plan.get("missing_laws"):
            basis = f"{basis}；缺口：{'、'.join(plan['missing_laws'])}"
        actions = _complex_issue_actions(plan)
        risk_types = _complex_issue_risk_types(plan)
        all_actions = append_unique_texts(all_actions, actions)
        all_risk_types = append_unique_texts(all_risk_types, risk_types)
        lines.extend([
            "",
            f"{plan['id']}. {plan['issue']}",
            f"初步判断：{_complex_issue_judgment(plan)}",
            f"依据：{basis}",
            f"补救/应对动作：{'；'.join(actions) if actions else '补充法规、合同和事实证据后人工复核'}。",
        ])

    missing_laws = []
    for plan in plans:
        missing_laws.extend(plan.get("missing_laws", []))
    missing_laws = list(dict.fromkeys(missing_laws))
    if missing_laws:
        missing_note = "当前知识库未入库或未覆盖：" + "、".join(missing_laws)
        if missing_note not in missing_evidence:
            missing_evidence.append(missing_note)

    citation_integrity = verify_citation_integrity(lines, evidence_chain)
    response = {
        "answer": "\n".join(lines).strip(),
        "confidence_score": 0.72 if missing_laws else 0.84,
        "answer_confidence": 0.72 if missing_laws else 0.84,
        "retrieval_confidence": retrieval_confidence,
        "needs_human_review": True,
        "missing_evidence": missing_evidence,
        "risk_level": "high" if all_risk_types else "medium",
        "risk_types": all_risk_types,
        "risk_type_evidence": build_supported_items(all_risk_types, evidence_chain),
        "recommended_actions": all_actions,
        "recommended_action_evidence": build_supported_items(all_actions, evidence_chain),
        "citation_integrity": citation_integrity,
        "evidence_chain": evidence_chain,
        "filters": {
            **filters,
            "answer_status": "complex_case_fast_workflow",
        },
        "sources": [
            {
                "source": item["source"],
                "law_name": item["law_name"],
                "document_type": item["document_type"],
                "type": item["type"],
                "block_type": item["block_type"],
                "law_level": item["law_level"],
                "authority_level": item["authority_level"],
                "jurisdiction": item["jurisdiction"],
            }
            for item in evidence_chain
        ],
    }
    if debug_info is not None:
        response["debug_info"] = debug_info
    return response
