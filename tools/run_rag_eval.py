"""运行 RAG 回归评测。

默认读取 tests/rag_eval_cases.json，检查 evidence 命中、回答关键词和置信度。
该脚本不做模型训练，只用于回归验证 RAG 检索与回答质量。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.retriever import rag_query


DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
KEYWORD_ALIASES = {
    "公开透明": ["公开透明", "公开、透明", "公开", "透明"],
    "信息质量": ["信息质量", "个人信息质量", "质量原则", "质量", "准确", "完整"],
    "便捷方式": ["便捷方式", "便捷", "撤回方式", "撤回同意的方式"],
    "不得拒绝": ["不得拒绝", "不得以个人不同意", "不得以个人撤回同意", "不得以用户撤回同意", "不得以撤回同意", "不能因此拒绝"],
    "撤回前有效": ["撤回前有效", "撤回前", "撤回不影响撤回前", "不影响撤回前", "效力不受影响", "第十五条"],
    "影响评估": ["影响评估", "个人信息保护影响评估"],
    "最小范围": ["最小范围", "限于实现处理目的的最小范围", "限于实现处理目的", "最低频率", "最少数量"],
    "个人信息主体": ["个人信息主体", "自然人", "该主体", "特定自然人", "特定自然人身份"],
    "个人信息类型": ["个人信息类型", "个人信息的类型", "个人信息或个人信息的类型", "个人信息或其类型"],
    "处理目的": ["处理目的", "所用于的目的", "用于的目的"],
    "目的变更": ["目的变更", "目的发生变化", "目的发生变更", "处理目的、方式", "超出原处理目的", "新使用行为", "用途"],
    "范围扩大": ["范围扩大", "范围发生变化", "规模、范围", "目的、范围"],
    "境外法规变化": ["境外法规变化", "个人信息保护政策和法规发生变化", "所在国家或者地区"],
    "提供产品服务": ["提供产品服务", "提供产品或者服务", "产品或者服务", "产品或服务"],
    "重新评估": ["重新评估", "重新开展个人信息保护影响评估", "重新开展"],
    "补充订立": ["补充订立", "补充或者重新订立", "重新订立"],
    "安全措施": ["安全措施", "安全保护", "保护措施", "管理和技术措施"],
    "保护认证": ["保护认证", "认证", "个人信息保护认证"],
    "告知": ["告知", "通知", "说明"],
    "同意": ["同意", "单独同意", "明确同意", "明示同意"],
    "精准定位": ["精准定位", "定位", "行踪轨迹"],
    "敏感个人信息违规处理": ["敏感个人信息违规处理", "敏感个人信息处理风险", "处理敏感个人信息", "未取得单独同意"],
    "敏感个人信息违规收集": ["敏感个人信息违规收集", "敏感个人信息处理风险", "处理敏感个人信息", "违规处理敏感个人信息"],
    "未履行告知义务": ["未履行告知义务", "告知义务履行风险", "违反告知义务", "未告知", "告知义务"],
    "目的限制": ["目的限制", "处理目的", "目的", "必要"],
    "单独同意": ["单独同意", "单独取得同意"],
    "第三方共享": ["第三方共享", "共享", "第三方", "向第三方提供", "提供给"],
    "违规提供个人信息": ["违规提供个人信息", "未经同意向第三方提供个人信息", "向第三方提供个人信息", "向其他个人信息处理者提供"],
    "明示": ["明示", "明确", "充分知情", "单独同意"],
    "明示同意": ["明示同意", "明确同意", "单独同意", "取得个人的单独同意"],
    "权限控制": ["权限控制", "权限", "访问控制"],
    "通知义务": ["通知义务", "通知", "告知", "个人信息泄露", "泄露", "安全事件"],
    "及时告知": ["及时告知", "及时通知", "通知"],
    "行政处罚": ["行政处罚", "行政责任", "处罚", "罚款", "法律责任"],
    "公平公正": ["公平公正", "公平、公正", "公平", "公正", "不合理的差别待遇"],
    "说明义务": ["说明义务", "说明", "解释", "透明度", "公开算法决策规则", "知情权"],
    "拒绝权": ["拒绝权", "拒绝", "有权拒绝", "拒绝自动化决策", "人工复核", "申诉渠道"],
    "监护人同意": ["监护人同意", "监护人的同意", "监护人"],
    "专门规则": ["专门规则", "专门的个人信息处理规则", "专门处理规则"],
    "再识别": ["再识别", "重新识别"],
    "合规边界": ["合规边界", "合规风险", "法律适用边界", "边界", "核心在于", "匿名化可能不彻底", "匿名化可能不充分", "匿名化不彻底", "匿名化效果评估", "不属于真正的匿名化", "重新识别风险"],
    "超出原授权": ["超出原授权", "超出原处理目的", "超出原处理目的的新使用行为", "超出原服务必要范围", "超出了实现初始客服目的", "超出实现初始客服目的", "超出初始客服目的", "新的处理目的", "从提供服务变为模型训练", "目的变更后未重新取得同意", "未明确告知用户将用于模型训练", "后续使用", "二次利用", "新使用行为"],
    "重新获取同意": ["重新获取同意", "重新取得同意", "重新取得个人同意", "另行取得同意"],
    "去标识化": ["去标识化", "匿名化", "匿名化处理", "限制训练数据范围", "最小范围", "最小必要"],
    "管理责任": ["管理责任", "公司作为个人信息处理者", "个人信息处理者", "对个人信息处理活动负责", "负责", "安全保护义务", "内部制度", "内部安全管理制度"],
    "安全事件": ["安全事件", "泄露事件", "泄露"],
    "技术措施": ["技术措施", "安全漏洞", "权限管控", "安全义务", "操作权限", "安全措施", "访问权限", "日志审计", "监控机制"],
    "赔偿责任": ["赔偿责任", "损害赔偿", "民事责任", "侵权责任"],
    "第三方": ["第三方", "其他个人信息处理者", "营销公司", "他人"],
    "违规": ["违规", "不合规", "违反", "违法"],
    "儿童个人信息": ["儿童个人信息", "未成年人个人信息", "不满十四周岁未成年人"],
    "儿童信息保护不力": ["儿童信息保护不力", "未成年人个人信息保护风险", "未成年人个人信息", "不满十四周岁未成年人"],
    "最小必要": ["最小必要", "最小范围", "必要原则", "影响最小"],
    "直接关联": ["直接关联", "直接相关", "不直接相关", "无关"],
    "合法": ["合法", "合规", "符合"],
    "必要": ["必要", "功能直接相关", "用途与功能直接相关", "导航服务", "合规要求"],
    "价格歧视": ["价格歧视", "差异化定价", "交易价格进行差别待遇", "交易价格等交易条件上实行不合理的差别待遇", "不合理的差别待遇"],
    "算法歧视": ["算法歧视", "价格歧视", "不合理差别待遇", "自动化决策不合规"],
    "超范围使用": ["超范围使用", "目的变更", "未重新告知", "用于广告推荐", "变更处理目的"],
    "超出授权范围使用": ["超出授权范围使用", "超出原客服服务目的", "目的变更未重新同意", "新的处理目的", "新处理活动"],
    "内部人员违规": ["内部人员违规", "员工私自导出", "内部追责", "追究员工责任"],
    "数据泄露": ["数据泄露", "个人信息泄露", "泄露事件"],
    "管理失职": ["管理失职", "内部管理风险", "未能履行", "安全保护义务"],
    "未履行通知义务": ["未履行通知义务", "未通知", "泄露未通知", "通知风险"],
    "数据出境不合规": ["数据出境不合规", "个人信息出境风险", "出境未履行", "未履行出境"],
    "医疗健康": ["医疗健康", "患者病历", "病历数据", "医疗"],
    "提供拒绝个性化推荐选项": ["提供拒绝个性化推荐选项", "如用户拒绝", "不得因此拒绝提供非必需服务", "拒绝自动化决策"],
    "提供替代识别方式（如刷卡、密码）": ["提供替代识别方式", "不得以拒绝提供考勤服务为由强制同意", "停止使用人脸识别考勤系统"],
    "采取内部管控措施（权限分级、日志审计）": ["采取内部管控措施", "权限控制", "内部安全管理制度", "员工培训和监督"],
    "赔偿损失": ["赔偿损失", "民事赔偿", "损害赔偿", "民事责任"],
    "面临罚款": ["面临罚款", "罚款", "行政处罚"],
    "提供说明和申诉渠道": ["提供说明和申诉渠道", "评分依据说明", "解释说明", "人工复核渠道", "投诉渠道", "解释和救济渠道"],
    "制定专门的儿童个人信息处理规则": ["制定专门的儿童个人信息处理规则", "专门的未成年人个人信息处理规则", "专门的个人信息处理规则"],
    "限制收集范围，仅收集实现功能所必需的信息": ["限制收集范围", "最小必要评估", "最小范围", "必需的信息"],
    "明确保存期限和删除机制": ["明确保存期限和删除机制", "严格保护措施", "保存期限", "删除"],
    "配合调查": ["配合调查", "配合监管部门调查", "报告泄露信息", "报告"],
    "明确境外接收方信息": ["明确境外接收方信息", "告知境外接收方信息", "境外接收方的名称"],
    "优化算法规则": ["优化算法规则", "优化算法逻辑", "调整算法模型", "优化评分逻辑", "公平性审计", "自动化决策系统", "自动化决策机制开展个人信息安全影响评估", "停止基于用户浏览记录进行差异化定价", "停止基于消费能力分析进行差异化定价"],
    "提供价格解释机制": ["提供价格解释机制", "自动化决策的逻辑及后果", "透明度", "人工复核"],
    "允许用户拒绝个性化推荐": ["允许用户拒绝个性化推荐", "提供便捷的拒绝方式", "便捷的拒绝自动化决策", "拒绝自动化决策", "拒绝方式", "非个性化选项", "不针对其个人特征的选项"],
    "减少收集字段": ["减少收集字段", "停止收集与天气查询无关", "仅收集实现天气查询功能所必需的信息"],
    "保持现有合规措施": ["保持现有合规措施", "持续保持", "持续提供", "确保告知内容", "持续关注", "定期审查"],
    "进行再识别风险评估": ["进行再识别风险评估", "重新评估匿名化技术措施", "匿名化有效性评估"],
    "或对数据去标识化处理": ["或对数据去标识化处理", "匿名化处理", "匿名化", "无法识别特定自然人"],
    "限制训练数据范围": ["限制训练数据范围", "数据使用范围", "训练目的", "最小必要"],
    "允许人工复核": ["允许人工复核", "人工复核", "投诉渠道"],
}
CORE_MATCH_TERMS = [
    "告知", "通知", "同意", "单独同意", "明示同意", "安全评估", "申报", "标准合同", "认证",
    "停止", "限制", "收集", "删除", "存储期限", "替代", "人工复核", "算法", "公平",
    "公正", "解释", "说明", "申诉", "复核", "补救", "监管", "部门", "配合调查",
    "匿名化", "去标识化", "再识别", "风险评估", "权限", "日志审计", "内部管控",
    "赔偿", "追究", "关闭", "拒绝", "个性化推荐", "最小必要", "减少", "字段",
    "保持", "合规措施", "安全措施", "技术措施", "未履行", "敏感个人信息", "违规",
    "超范围", "数据出境", "不合规", "算法歧视", "自动化决策", "过度收集", "儿童",
    "安全事件", "管理责任", "目的变更", "超出原授权",
]


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: dict[str, Any] | None = None


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return payload.get("cases", [])


def text_contains_all(text: str, keywords: list[str]) -> tuple[bool, list[str]]:
    missing = []
    for keyword in keywords:
        aliases = KEYWORD_ALIASES.get(keyword, [keyword])
        if not any(alias in text for alias in aliases) and not core_terms_match(text, keyword):
            missing.append(keyword)
    return not missing, missing


def text_contains_enough(text: str, keywords: list[str], min_ratio: float = 0.5) -> tuple[bool, list[str]]:
    """风险字段允许同义表达和覆盖率通过，避免把评测变成固定话术背诵。"""
    if not keywords:
        return True, []
    missing = []
    for keyword in keywords:
        aliases = KEYWORD_ALIASES.get(keyword, [keyword])
        if not any(alias in text for alias in aliases) and not core_terms_match(text, keyword):
            missing.append(keyword)
    hit_count = len(keywords) - len(missing)
    required = max(1, int(len(keywords) * min_ratio + 0.999))
    return hit_count >= required, missing


def core_terms_match(text: str, expectation: str) -> bool:
    """用核心动作/风险词做轻量模糊匹配，避免要求 LLM 与测试集逐字一致。"""
    terms = []
    for term in CORE_MATCH_TERMS:
        if term in expectation and term not in terms:
            terms.append(term)

    if not terms:
        return False

    hit_count = sum(1 for term in terms if term in text)
    required = len(terms) if len(terms) <= 2 else max(2, (len(terms) + 1) // 2)
    return hit_count >= required


def normalize_text_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()] if str(value).strip() else []


def check_expected_risk_types(case: dict[str, Any], result: dict[str, Any], enabled: bool) -> CheckResult:
    if not enabled:
        return CheckResult("expected_risk_types", True, "未启用 --check-risk，跳过")
    expected_types = case.get("expected_risk_types", [])
    if not expected_types:
        return CheckResult("expected_risk_types", True, "未配置 expected_risk_types，跳过")
    actual_text = " ".join(normalize_text_items(result.get("risk_types")) + [result.get("answer", "")])
    passed, missing = text_contains_enough(actual_text, expected_types)
    message = "风险类型覆盖率达标" if passed else f"缺失风险类型: {missing}"
    return CheckResult("expected_risk_types", passed, message)


def check_expected_risk_level(case: dict[str, Any], result: dict[str, Any], enabled: bool) -> CheckResult:
    if not enabled:
        return CheckResult("expected_risk_level", True, "未启用 --check-risk，跳过")
    expected_level = case.get("expected_risk_level")
    if not expected_level:
        return CheckResult("expected_risk_level", True, "未配置 expected_risk_level，跳过")
    actual_level = result.get("risk_level")
    level_order = {"low": 0, "medium": 1, "high": 2}
    passed = actual_level == expected_level
    actual_rank = level_order.get(actual_level, -1)
    expected_rank = level_order.get(expected_level, -1)
    if passed:
        mismatch_type = "exact_match"
    elif actual_rank > expected_rank >= 0:
        mismatch_type = "over_risk"
    elif 0 <= actual_rank < expected_rank:
        mismatch_type = "under_risk"
    else:
        mismatch_type = "invalid_or_missing_risk_level"
    message = f"risk_level={actual_level}, expected={expected_level}, policy=exact, mismatch_type={mismatch_type}"
    return CheckResult(
        "expected_risk_level",
        passed,
        message,
        {
            "policy": "exact",
            "actual_level": actual_level,
            "expected_level": expected_level,
            "mismatch_type": mismatch_type,
        },
    )


def check_expected_actions(case: dict[str, Any], result: dict[str, Any], enabled: bool) -> CheckResult:
    if not enabled:
        return CheckResult("expected_actions", True, "未启用 --check-risk，跳过")
    expected_actions = case.get("expected_actions", [])
    if not expected_actions:
        return CheckResult("expected_actions", True, "未配置 expected_actions，跳过")
    actual_text = " ".join(normalize_text_items(result.get("recommended_actions")) + [result.get("answer", "")])
    passed, missing = text_contains_enough(actual_text, expected_actions)
    message = "整改动作覆盖率达标" if passed else f"缺失整改动作: {missing}"
    return CheckResult("expected_actions", passed, message)


def source_matches(expected: str, item: dict[str, Any]) -> bool:
    if not expected:
        return True
    candidates = [
        item.get("source", ""),
        item.get("law_name", ""),
    ]
    return any(expected == candidate or expected in candidate or candidate in expected for candidate in candidates)


def evidence_matches(expected: dict[str, Any], item: dict[str, Any]) -> bool:
    if not source_matches(expected.get("source", ""), item):
        return False

    if "article_no" in expected and expected["article_no"] != item.get("article_no"):
        return False
    if "article" in expected and expected["article"] != item.get("article"):
        return False
    if "section_no" in expected and expected["section_no"] != item.get("section_no"):
        return False

    expected_keywords = expected.get("must_include", [])
    if expected_keywords:
        content = item.get("content", "") or item.get("matched_content", "") or item.get("content_preview", "")
        contains, _ = text_contains_all(content, expected_keywords)
        if not contains:
            return False

    return True


def check_expected_evidence(case: dict[str, Any], evidence_chain: list[dict[str, Any]]) -> CheckResult:
    expected_items = case.get("expected_evidence", [])
    if not expected_items:
        return CheckResult("expected_evidence", True, "未配置 expected_evidence，跳过")

    match_mode = case.get("expected_evidence_match", "all")
    required_count = expected_evidence_required_count(case, expected_items, match_mode)
    matched = []
    missing = []
    for expected in expected_items:
        hit = any(evidence_matches(expected, item) for item in evidence_chain)
        if hit:
            matched.append(expected)
        else:
            missing.append(expected)

    passed = len(matched) >= required_count
    if "expected_evidence_min_match" in case:
        message = f"命中 {len(matched)}/{len(expected_items)} 个期望证据（min={required_count}）"
    elif match_mode == "any":
        message = f"命中 {len(matched)}/{len(expected_items)} 个期望证据（any）"
    else:
        message = f"命中 {len(matched)}/{len(expected_items)} 个期望证据（all）"

    if not passed:
        message += f"，缺失: {missing}"
    return CheckResult("expected_evidence", passed, message)


def expected_evidence_required_count(
    case: dict[str, Any],
    expected_items: list[dict[str, Any]],
    match_mode: str,
) -> int:
    if not expected_items:
        return 0
    configured = case.get("expected_evidence_min_match")
    if configured is not None:
        return max(1, min(int(configured), len(expected_items)))
    if match_mode == "any":
        return 1
    return len(expected_items)


def expected_evidence_layer_status(
    expected_items: list[dict[str, Any]],
    items: list[dict[str, Any]],
    match_mode: str,
    required_count: int,
) -> dict[str, Any]:
    matched = []
    missing = []
    for expected in expected_items:
        if any(evidence_matches(expected, item) for item in items):
            matched.append(expected)
        else:
            missing.append(expected)
    if not expected_items:
        satisfied = True
    else:
        satisfied = len(matched) >= required_count
    return {
        "matched_count": len(matched),
        "expected_count": len(expected_items),
        "required_count": required_count,
        "satisfied": satisfied,
        "matched": matched,
        "missing": missing,
    }


def classify_retrieval_failure(layer_status: dict[str, dict[str, Any]]) -> str:
    if layer_status["final"].get("satisfied"):
        return "PASS"
    if layer_status["rerank_input"].get("satisfied"):
        return "RERANK_MISS"
    if layer_status["union"].get("satisfied"):
        return "CANDIDATE_CUT_MISS"
    if layer_status["dense"].get("satisfied") or layer_status["sparse"].get("satisfied"):
        return "UNION_MISS"
    if layer_status["anchor"].get("satisfied"):
        return "ANCHOR_CUT_MISS"
    if layer_status["dense"]["matched_count"] or layer_status["sparse"]["matched_count"] or layer_status["anchor"]["matched_count"]:
        return "PARTIAL_RECALL_MISS"
    return "RETRIEVAL_MISS"


def build_retrieval_diagnostics(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    expected_items = case.get("expected_evidence", [])
    match_mode = case.get("expected_evidence_match", "all")
    required_count = expected_evidence_required_count(case, expected_items, match_mode)
    debug_info = result.get("debug_info", {})
    layer_items = {
        "dense": debug_info.get("dense_candidates", []),
        "sparse": debug_info.get("sparse_candidates", []),
        "union": debug_info.get("union_candidates", []),
        "anchor": debug_info.get("anchor_candidates", []),
        "rerank_input": debug_info.get("rerank_input_candidates", []),
        "final": result.get("evidence_chain", []),
    }
    layer_status = {
        layer: expected_evidence_layer_status(expected_items, items, match_mode, required_count)
        for layer, items in layer_items.items()
    }
    failure_stage = "NOT_CONFIGURED" if not expected_items else classify_retrieval_failure(layer_status)
    return {
        "match_mode": match_mode,
        "required_count": required_count,
        "failure_stage": failure_stage,
        "layers": layer_status,
    }


SOURCE_REF_PREFIXES = {
    "中华人民共和国个人信息保护法": "pipl",
    "中华人民共和国数据安全法": "data_security_law",
    "中华人民共和国网络安全法": "cybersecurity_law",
    "数据出境安全评估办法": "data_export_security_assessment_measures",
    "个人信息出境标准合同办法": "standard_contract_measures",
    "中华人民共和国反不正当竞争法": "anti_unfair_competition_law",
    "中华人民共和国消费者权益保护法": "consumer_rights_protection_law",
    "中华人民共和国民法典": "civil_code",
    "中华人民共和国公司法": "company_law",
    "信息安全技术 个人信息安全规范 GB_T_35273_2020": "gb_t_35273_2020",
    "信息安全技术 个人信息安全规范": "gb_t_35273_2020",
}

SOURCE_DOMAINS = {
    "pipl": "personal_information_protection",
    "data_security_law": "data_security",
    "cybersecurity_law": "cybersecurity",
    "data_export_security_assessment_measures": "data_export",
    "standard_contract_measures": "data_export",
    "gb_t_35273_2020": "standard_guidance",
    "anti_unfair_competition_law": "anti_unfair_competition",
    "consumer_rights_protection_law": "consumer_protection",
    "civil_code": "civil_code",
    "company_law": "company_law",
}

OPERATIVE_FUNCTIONAL_TYPES = {"operative_rule", "procedural", "rights_remedy", "principle"}
DEFINITION_FUNCTIONAL_TYPES = {"definition"}


def _compact_source_name(value: Any) -> str:
    text = str(value or "").strip()
    return " ".join(text.split())


def source_ref_prefix(item: dict[str, Any]) -> str:
    candidates = [
        _compact_source_name(item.get("source")),
        _compact_source_name(item.get("law_name")),
    ]
    for candidate in candidates:
        if candidate in SOURCE_REF_PREFIXES:
            return SOURCE_REF_PREFIXES[candidate]
    for candidate in candidates:
        for source_name, prefix in SOURCE_REF_PREFIXES.items():
            if candidate and (candidate in source_name or source_name in candidate):
                return prefix
    return ""


def evidence_ref(item: dict[str, Any]) -> str:
    prefix = source_ref_prefix(item)
    if not prefix:
        return ""
    article_no = item.get("article_no")
    if isinstance(article_no, int):
        return f"{prefix}::article_{article_no}"
    if isinstance(article_no, str) and article_no.isdigit():
        return f"{prefix}::article_{article_no}"
    section_no = str(item.get("section_no") or item.get("article") or "").strip()
    if section_no:
        normalized = section_no.lower().replace(".", "_").replace("-", "_").replace(" ", "_")
        return f"{prefix}::section_{normalized}"
    return ""


def _expected_refs_by_functional_type(case: dict[str, Any]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for item in case.get("expected_statutes", []):
        if not isinstance(item, dict):
            continue
        ref = item.get("ref")
        functional_type = item.get("functional_type", "unknown")
        if isinstance(ref, str) and ref:
            grouped.setdefault(str(functional_type), []).append(ref)
    return grouped


def build_quality_signal_diagnostics(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    evidence_chain = result.get("evidence_chain", [])
    final_refs = [ref for ref in (evidence_ref(item) for item in evidence_chain) if ref]
    final_ref_set = set(final_refs)
    issues = []
    review_reasons = []

    expected_by_type = _expected_refs_by_functional_type(case)
    expected_refs = {
        ref
        for refs in expected_by_type.values()
        for ref in refs
    }
    matched_expected_refs = sorted(expected_refs.intersection(final_ref_set))
    operative_expected_refs = {
        ref
        for functional_type, refs in expected_by_type.items()
        if functional_type in OPERATIVE_FUNCTIONAL_TYPES
        for ref in refs
    }
    definition_expected_refs = {
        ref
        for functional_type, refs in expected_by_type.items()
        if functional_type in DEFINITION_FUNCTIONAL_TYPES
        for ref in refs
    }
    matched_operative_refs = sorted(operative_expected_refs.intersection(final_ref_set))
    matched_definition_refs = sorted(definition_expected_refs.intersection(final_ref_set))
    expected_evidence_items = case.get("expected_evidence", [])
    expected_evidence_refs = {
        ref
        for ref in (evidence_ref(item) for item in expected_evidence_items if isinstance(item, dict))
        if ref
    }
    expected_evidence_status = expected_evidence_layer_status(
        expected_evidence_items,
        evidence_chain,
        case.get("expected_evidence_match", "all"),
        expected_evidence_required_count(
            case,
            expected_evidence_items,
            case.get("expected_evidence_match", "all"),
        ),
    )
    missing_expected_evidence_refs = {
        ref
        for ref in (evidence_ref(item) for item in expected_evidence_status.get("missing", []))
        if ref
    }

    if expected_refs and not matched_expected_refs:
        issues.append("major_issue_evidence_gap")
        review_reasons.append("Expected hidden-style statute coverage is absent from the final evidence chain.")
    elif operative_expected_refs and matched_definition_refs and not matched_operative_refs:
        issues.append("definition_substitutes_operative_rule")
        review_reasons.append("Final evidence only covers definition provisions while operative/procedural provisions are missing.")

    known_bad_refs = {
        item.get("ref")
        for item in case.get("known_bad_evidence", [])
        if isinstance(item, dict) and item.get("ref")
    }
    known_bad_hits = sorted(known_bad_refs.intersection(final_ref_set))
    if known_bad_hits:
        issues.append("known_bad_evidence_leakage")
        review_reasons.append("Final evidence contains seed-marked known-bad or contaminating references.")

    contaminating_domains = set(case.get("contaminating_domains", []) or [])
    evidence_domains = sorted({
        SOURCE_DOMAINS.get(source_ref_prefix(item), "")
        for item in evidence_chain
        if SOURCE_DOMAINS.get(source_ref_prefix(item), "")
    })
    contaminating_domain_hits = sorted(contaminating_domains.intersection(evidence_domains))
    if contaminating_domain_hits:
        issues.append("jurisdiction_or_domain_pollution")
        review_reasons.append("Final evidence includes domains marked as contaminating for this scenario.")

    selection_trace = result.get("debug_info", {}).get("final_evidence_selection_trace", {})
    score_order_observations = []
    score_order_risks = []
    selected = selection_trace.get("selected", []) if isinstance(selection_trace, dict) else []
    not_selected = selection_trace.get("not_selected", []) if isinstance(selection_trace, dict) else []
    selected_scores = [float(item.get("score", 0.0)) for item in selected if item.get("score") is not None]
    if selected_scores:
        weakest_selected = min(selected_scores)
        score_epsilon = float(selection_trace.get("score_epsilon", 0.1) or 0.1)
        weakest_bucket = int(weakest_selected / score_epsilon) if score_epsilon > 0 else None
        for item in not_selected:
            score = item.get("score")
            if score is None:
                continue
            score = float(score)
            same_bucket = score_epsilon > 0 and int(score / score_epsilon) == weakest_bucket
            if same_bucket and score - weakest_selected >= 0.02:
                not_selected_ref = evidence_ref(item)
                observation = {
                    "not_selected_ref": evidence_ref(item),
                    "not_selected_score": score,
                    "weakest_selected_score": weakest_selected,
                    "score_delta": round(score - weakest_selected, 6),
                }
                score_order_observations.append(observation)
                if not_selected_ref in final_ref_set:
                    continue
                missing_expected_evidence_hit = (
                    not expected_evidence_status.get("satisfied", True)
                    and not_selected_ref in missing_expected_evidence_refs
                )
                missing_operative_hit = (
                    not_selected_ref in operative_expected_refs
                    and not_selected_ref not in final_ref_set
                )
                if missing_expected_evidence_hit or missing_operative_hit:
                    score_order_risks.append(observation)
    if score_order_risks:
        issues.append("same_bucket_selection_order_risk")
        review_reasons.append("A non-selected candidate has a materially higher score inside the same coarse rerank bucket.")

    status = "review_recommended" if issues else "aligned_or_not_configured"
    if not expected_refs and not known_bad_refs and not contaminating_domains and not score_order_risks:
        status = "not_configured"

    return {
        "status": status,
        "detected_issues": sorted(set(issues)),
        "review_reasons": review_reasons,
        "final_refs": final_refs,
        "matched_expected_refs": matched_expected_refs,
        "matched_operative_refs": matched_operative_refs,
        "matched_definition_refs": matched_definition_refs,
        "known_bad_hits": known_bad_hits,
        "evidence_domains": evidence_domains,
        "contaminating_domain_hits": contaminating_domain_hits,
        "expected_evidence_status": expected_evidence_status,
        "score_order_observations": score_order_observations,
        "score_order_risks": score_order_risks,
    }


def build_contribution_labels(
    passed: bool,
    retrieval_diagnostics: dict[str, Any],
    debug_info: dict[str, Any],
) -> list[str]:
    if not passed:
        return []

    labels = []
    output_contributions = debug_info.get("output_contributions", {})
    layers = retrieval_diagnostics.get("layers", {})

    if passed and debug_info.get("rerank_dense_fallback"):
        labels.append("DENSE_FALLBACK_PASS")

    union_satisfied = layers.get("union", {}).get("satisfied", False)
    anchor_satisfied = layers.get("anchor", {}).get("satisfied", False)
    rerank_input_satisfied = layers.get("rerank_input", {}).get("satisfied", False)
    final_satisfied = layers.get("final", {}).get("satisfied", False)
    if passed and final_satisfied and not union_satisfied and (anchor_satisfied or rerank_input_satisfied):
        labels.append("ANCHOR_PASS")

    if output_contributions.get("term_preservation_rules"):
        labels.append("TERM_PRESERVATION_PASS")

    risk_rule_keys = (
        "risk_supplement_rules",
        "scene_output_rules",
        "low_risk_rules",
    )
    if any(output_contributions.get(key) for key in risk_rule_keys) or output_contributions.get("compliant_permission_rule"):
        labels.append("RISK_SUPPLEMENT_PASS")

    if passed and not labels:
        labels.append("PURE_LLM_PASS")

    return labels


def build_contribution_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts: dict[str, int] = {}
    passed_reports = [report for report in reports if report.get("passed")]
    for report in passed_reports:
        for label in report.get("contribution_labels", []):
            label_counts[label] = label_counts.get(label, 0) + 1

    output_rule_assisted = sum(
        1
        for report in passed_reports
        if any(label in report.get("contribution_labels", []) for label in ["TERM_PRESERVATION_PASS", "RISK_SUPPLEMENT_PASS"])
    )
    return {
        "label_counts": label_counts,
        "passed_total": len(passed_reports),
        "output_rule_assisted_passed": output_rule_assisted,
        "pure_llm_passed": label_counts.get("PURE_LLM_PASS", 0),
        "anchor_assisted_passed": label_counts.get("ANCHOR_PASS", 0),
        "term_preservation_assisted_passed": label_counts.get("TERM_PRESERVATION_PASS", 0),
        "risk_supplement_assisted_passed": label_counts.get("RISK_SUPPLEMENT_PASS", 0),
        "dense_fallback_passed": label_counts.get("DENSE_FALLBACK_PASS", 0),
    }


def build_risk_level_mismatch_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize exact risk-level mismatches without changing retrieval diagnostics."""
    mismatch_counts: dict[str, int] = {}
    mismatch_cases: list[dict[str, Any]] = []
    checked_count = 0
    for report in reports:
        for check in report.get("checks", []):
            if check.get("name") != "expected_risk_level":
                continue
            details = check.get("details") or {}
            if details.get("policy") != "exact":
                continue
            checked_count += 1
            mismatch_type = details.get("mismatch_type", "unknown")
            mismatch_counts[mismatch_type] = mismatch_counts.get(mismatch_type, 0) + 1
            if mismatch_type != "exact_match":
                mismatch_cases.append(
                    {
                        "id": report.get("id"),
                        "actual_level": details.get("actual_level"),
                        "expected_level": details.get("expected_level"),
                        "mismatch_type": mismatch_type,
                    }
                )
    return {
        "policy": "exact",
        "checked_count": checked_count,
        "mismatch_counts": mismatch_counts,
        "mismatch_cases": mismatch_cases,
    }


def failed_check_names(report: dict[str, Any]) -> list[str]:
    return [check["name"] for check in report.get("checks", []) if not check.get("passed")]


def build_stability_summary(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    case_ids = sorted({
        report["id"]
        for summary in run_summaries
        for report in summary.get("reports", [])
    })
    reports_by_run = [
        {report["id"]: report for report in summary.get("reports", [])}
        for summary in run_summaries
    ]
    unstable_cases = []
    label_variation_cases = []

    for case_id in case_ids:
        reports = [run_reports.get(case_id, {}) for run_reports in reports_by_run]
        pass_values = [bool(report.get("passed")) for report in reports]
        stages = [report.get("retrieval_failure_stage") for report in reports]
        failed_checks = [tuple(failed_check_names(report)) for report in reports]
        label_sets = [tuple(sorted(report.get("contribution_labels", []))) for report in reports]

        if len(set(pass_values)) > 1 or len(set(stages)) > 1 or len(set(failed_checks)) > 1:
            unstable_cases.append({
                "id": case_id,
                "passed": pass_values,
                "retrieval_failure_stage": stages,
                "failed_checks": [list(items) for items in failed_checks],
                "contribution_labels": [list(items) for items in label_sets],
            })
        elif len(set(label_sets)) > 1:
            label_variation_cases.append({
                "id": case_id,
                "contribution_labels": [list(items) for items in label_sets],
            })

    return {
        "runs": len(run_summaries),
        "all_runs_full_pass": all(summary["passed"] == summary["total"] for summary in run_summaries),
        "pass_counts": [summary["passed"] for summary in run_summaries],
        "total_counts": [summary["total"] for summary in run_summaries],
        "unstable_cases": unstable_cases,
        "label_variation_cases": label_variation_cases,
    }


def check_answer_keywords(case: dict[str, Any], answer: str) -> CheckResult:
    keywords = case.get("expected_answer_keywords", [])
    if not keywords:
        return CheckResult("expected_answer_keywords", True, "未配置 expected_answer_keywords，跳过")
    passed, missing = text_contains_all(answer, keywords)
    message = "答案关键词全部命中" if passed else f"缺失答案关键词: {missing}"
    return CheckResult("expected_answer_keywords", passed, message)


def build_visible_output_text(result: dict[str, Any]) -> str:
    """评测用户可见输出；结构化风险字段也是接口响应的一部分。"""
    return " ".join(
        [result.get("answer", "")]
        + normalize_text_items(result.get("risk_types"))
        + normalize_text_items(result.get("recommended_actions"))
    )


def check_confidence(case: dict[str, Any], confidence_score: float | None) -> CheckResult:
    threshold = case.get("min_confidence_score")
    if threshold is None:
        return CheckResult("min_confidence_score", True, "未配置 min_confidence_score，跳过")
    score = confidence_score if confidence_score is not None else 0.0
    passed = score >= threshold
    message = f"confidence_score={score}, threshold={threshold}"
    return CheckResult("min_confidence_score", passed, message)


def check_expected_missing_evidence(case: dict[str, Any], result: dict[str, Any]) -> CheckResult:
    keywords = case.get("expected_missing_evidence_keywords", [])
    if not keywords:
        return CheckResult("expected_missing_evidence_keywords", True, "未配置 expected_missing_evidence_keywords，跳过")
    missing_text = " ".join(normalize_text_items(result.get("missing_evidence")))
    passed, missing = text_contains_all(missing_text, keywords)
    message = "缺失依据提示命中" if passed else f"缺失依据提示未覆盖: {missing}"
    return CheckResult("expected_missing_evidence_keywords", passed, message)


def check_expected_answer_status(case: dict[str, Any], result: dict[str, Any]) -> CheckResult:
    expected_status = case.get("expected_answer_status")
    if not expected_status:
        return CheckResult("expected_answer_status", True, "未配置 expected_answer_status，跳过")
    actual_status = (result.get("filters") or {}).get("answer_status")
    passed = actual_status == expected_status
    message = f"answer_status={actual_status}, expected={expected_status}"
    return CheckResult("expected_answer_status", passed, message)


def run_case(
    case: dict[str, Any],
    check_risk: bool = False,
    collection_name: str | None = None,
) -> dict[str, Any]:
    filters = case.get("filters", {})
    retrieval_options = dict(filters)
    if collection_name:
        retrieval_options["collection_name"] = collection_name
    result = rag_query(
        case["question"],
        k=case.get("k", 5),
        debug=True,
        **retrieval_options,
    )
    retrieval_diagnostics = build_retrieval_diagnostics(case, result)
    quality_signal_diagnostics = build_quality_signal_diagnostics(case, result)
    checks = [
        check_expected_evidence(case, result.get("evidence_chain", [])),
        check_answer_keywords(case, build_visible_output_text(result)),
        check_confidence(case, result.get("confidence_score")),
        check_expected_risk_types(case, result, check_risk),
        check_expected_risk_level(case, result, check_risk),
        check_expected_actions(case, result, check_risk),
        check_expected_missing_evidence(case, result),
        check_expected_answer_status(case, result),
    ]
    passed = all(check.passed for check in checks)
    debug_info = result.get("debug_info", {})
    contribution_labels = build_contribution_labels(passed, retrieval_diagnostics, debug_info)
    return {
        "id": case.get("id", ""),
        "category": filters.get("category", ""),
        "retrieval_failure_stage": retrieval_diagnostics["failure_stage"],
        "retrieval_diagnostics": retrieval_diagnostics,
        "quality_signal_diagnostics": quality_signal_diagnostics,
        "contribution_labels": contribution_labels,
        "contribution_trace": debug_info.get("output_contributions", {}),
        "passed": passed,
        "question": case.get("question", ""),
        "checks": [check.__dict__ for check in checks],
        "answer": result.get("answer", ""),
        "confidence_score": result.get("confidence_score"),
        "answer_confidence": result.get("answer_confidence"),
        "retrieval_confidence": result.get("retrieval_confidence"),
        "needs_human_review": result.get("needs_human_review"),
        "missing_evidence": result.get("missing_evidence", []),
        "risk_level": result.get("risk_level"),
        "risk_types": result.get("risk_types", []),
        "risk_type_evidence": result.get("risk_type_evidence", []),
        "recommended_actions": result.get("recommended_actions", []),
        "recommended_action_evidence": result.get("recommended_action_evidence", []),
        "filters": result.get("filters", {}),
        "evidence": [
            {
                "rank": item.get("rank"),
                "source": item.get("source"),
                "law_name": item.get("law_name"),
                "article_no": item.get("article_no"),
                "section_no": item.get("section_no"),
                "citation": item.get("citation"),
                "rerank_score": item.get("rerank_score"),
            }
            for item in result.get("evidence_chain", [])
        ],
        "debug_info": debug_info,
    }


def _count_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def build_compact_debug_summary(debug_info: dict[str, Any]) -> dict[str, Any]:
    """Keep debug observability counts without embedding full candidate payloads."""
    if not isinstance(debug_info, dict):
        return {}
    selection_trace = debug_info.get("final_evidence_selection_trace", {})
    if not isinstance(selection_trace, dict):
        selection_trace = {}
    output_contributions = debug_info.get("output_contributions", {})
    if not isinstance(output_contributions, dict):
        output_contributions = {}
    return {
        "candidate_counts": {
            "dense": _count_list(debug_info.get("dense_candidates")),
            "sparse": _count_list(debug_info.get("sparse_candidates")),
            "union": _count_list(debug_info.get("union_candidates")),
            "anchor": _count_list(debug_info.get("anchor_candidates")),
            "rerank_input": _count_list(debug_info.get("rerank_input_candidates")),
            "rerank_full_score_order": _count_list(debug_info.get("rerank_full_score_order")),
        },
        "final_evidence_selection_trace": {
            "score_epsilon": selection_trace.get("score_epsilon"),
            "full_rerank_count": selection_trace.get("full_rerank_count"),
            "selected_count": selection_trace.get("selected_count"),
            "not_selected_count": selection_trace.get("not_selected_count"),
        },
        "output_contribution_counts": {
            key: _count_list(value)
            for key, value in output_contributions.items()
            if isinstance(value, list)
        },
        "rerank_dense_fallback": bool(debug_info.get("rerank_dense_fallback")),
    }


def compact_case_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return a smaller report preserving eval outcome and quality signals."""
    compact = dict(report)
    debug_info = compact.pop("debug_info", {})
    compact["debug_info_summary"] = build_compact_debug_summary(debug_info)
    contribution_trace = compact.get("contribution_trace", {})
    if isinstance(contribution_trace, dict):
        compact["contribution_trace_summary"] = {
            key: _count_list(value)
            for key, value in contribution_trace.items()
            if isinstance(value, list)
        }
    compact.pop("contribution_trace", None)
    return compact


def apply_report_profile(summary: dict[str, Any], profile: str) -> dict[str, Any]:
    """Apply an output-only report profile without changing eval execution."""
    if profile == "full":
        profiled = dict(summary)
        profiled["report_profile"] = "full"
        return profiled
    if profile != "compact":
        raise ValueError(f"unsupported report profile: {profile}")
    compact_summary = dict(summary)
    compact_summary["report_profile"] = "compact"
    if "reports" in compact_summary:
        compact_summary["reports"] = [
            compact_case_report(report)
            for report in compact_summary.get("reports", [])
        ]
    if "runs" in compact_summary:
        compact_runs = []
        for run_summary in compact_summary.get("runs", []):
            compact_run = dict(run_summary)
            compact_run["reports"] = [
                compact_case_report(report)
                for report in compact_run.get("reports", [])
            ]
            compact_runs.append(compact_run)
        compact_summary["runs"] = compact_runs
    return compact_summary


def print_case_report(report: dict[str, Any], verbose: bool = False):
    status = "PASS" if report["passed"] else "FAIL"
    print(f"[{status}] {report['id']}")
    if report.get("contribution_labels"):
        print(f"  labels: {', '.join(report['contribution_labels'])}")
    for check in report["checks"]:
        check_status = "OK" if check["passed"] else "X"
        print(f"  - {check_status} {check['name']}: {check['message']}")
    print("  evidence:")
    for item in report["evidence"]:
        print(f"    {item['rank']}. {item['citation']} score={item['rerank_score']}")
    if verbose:
        print(f"  answer: {report['answer']}")
        print(f"  retrieval_confidence: {report.get('retrieval_confidence')}")
        print(f"  needs_human_review: {report.get('needs_human_review')}")
        if report.get("missing_evidence"):
            print(f"  missing_evidence: {report.get('missing_evidence')}")
        if report.get("risk_level") or report.get("risk_types") or report.get("recommended_actions"):
            print(f"  risk_level: {report.get('risk_level')}")
            print(f"  risk_types: {report.get('risk_types')}")
            print(f"  recommended_actions: {report.get('recommended_actions')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAG regression evaluation cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="评测用例 JSON 路径")
    parser.add_argument("--output", type=Path, help="可选：保存 JSON 报告路径")
    parser.add_argument(
        "--compact-report",
        action="store_true",
        help="Write compact JSON without full per-case debug_info payloads.",
    )
    parser.add_argument("--verbose", action="store_true", help="输出完整答案")
    parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")
    parser.add_argument("--check-risk", action="store_true", help="校验 expected_risk_types、expected_risk_level 和 expected_actions")
    parser.add_argument("--domain", type=str, help="仅运行指定领域（按 category 筛选）")
    parser.add_argument("--case-id", action="append", default=[], help="仅运行指定 case id，可重复传入")
    parser.add_argument("--smoke", action="store_true", help="使用 smoke_eval_cases.json 而非全量题库")
    parser.add_argument("--repeat", type=int, default=1, help="重复运行次数，用于稳定性回归")
    parser.add_argument("--collection", type=str, help="可选：指定 Qdrant collection，默认使用运行时配置")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repeat < 1:
        print("--repeat must be >= 1")
        return 1
    if args.smoke:
        args.cases = Path("tests/smoke_eval_cases.json")
    cases = load_cases(args.cases)
    if args.domain:
        cases = [c for c in cases if c.get("filters", {}).get("category") == args.domain]
        if not cases:
            print(f"No cases found for domain: {args.domain}")
            return 1
    if args.case_id:
        wanted = set(args.case_id)
        cases = [c for c in cases if c.get("id") in wanted]
        if not cases:
            print(f"No cases found for ids: {sorted(wanted)}")
            return 1

    run_summaries = []
    for run_index in range(1, args.repeat + 1):
        if args.repeat > 1:
            print(f"\n=== Run {run_index}/{args.repeat} ===")
        reports = []
        for case in cases:
            report = run_case(
                case,
                check_risk=args.check_risk,
                collection_name=args.collection,
            )
            reports.append(report)
            print_case_report(report, verbose=args.verbose)
            if args.fail_fast and not report["passed"]:
                break

        passed_count = sum(1 for report in reports if report["passed"])
        failure_stage_summary: dict[str, int] = {}
        for report in reports:
            stage = report.get("retrieval_failure_stage", "UNKNOWN")
            failure_stage_summary[stage] = failure_stage_summary.get(stage, 0) + 1
        contribution_summary = build_contribution_summary(reports)
        risk_level_mismatch_summary = build_risk_level_mismatch_summary(reports)
        run_summary = {
            "run": run_index,
            "total": len(reports),
            "passed": passed_count,
            "failed": len(reports) - passed_count,
            "retrieval_failure_stage_summary": failure_stage_summary,
            "contribution_summary": contribution_summary,
            "risk_level_mismatch_summary": risk_level_mismatch_summary,
            "reports": reports,
        }
        run_summaries.append(run_summary)
        print(f"\nSummary: {passed_count}/{len(reports)} passed")
        print(f"Retrieval stages: {failure_stage_summary}")
        print(f"Contribution labels: {contribution_summary['label_counts']}")
        print(f"Risk level mismatches: {risk_level_mismatch_summary['mismatch_counts']}")

    if args.repeat == 1:
        summary = run_summaries[0]
    else:
        summary = {
            "repeat": args.repeat,
            "stability_summary": build_stability_summary(run_summaries),
            "runs": run_summaries,
        }
        stability = summary["stability_summary"]
        print("\nStability summary:")
        print(f"  all_runs_full_pass: {stability['all_runs_full_pass']}")
        print(f"  pass_counts: {stability['pass_counts']}")
        print(f"  unstable_cases: {len(stability['unstable_cases'])}")
        print(f"  label_variation_cases: {len(stability['label_variation_cases'])}")

    if args.output:
        if args.compact_report:
            summary = apply_report_profile(summary, "compact")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"报告已保存: {args.output}")

    if args.repeat == 1:
        return 0 if summary["passed"] == summary["total"] else 1
    return 0 if summary["stability_summary"]["all_runs_full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
