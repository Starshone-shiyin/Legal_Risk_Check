from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_anchor_rules() -> dict:
    rules_path = Path(__file__).parent.parent.parent / "config" / "rag_anchor_rules.json"
    with open(rules_path, encoding="utf-8") as f:
        return json.load(f)


# v0.4.0.2: 查询扩展词库（扁平结构 + 领域术语扩充）
LEGAL_QUERY_EXPANSIONS = {
    "原则": ["原则", "遵循", "合法", "正当", "必要", "诚信", "明确", "合理", "最小", "公开", "透明", "质量", "安全"],
    "同意": ["同意", "单独同意", "书面同意", "撤回", "知情", "自愿", "明确", "取得授权", "用户许可"],
    "敏感个人信息": ["敏感个人信息", "单独同意", "生物识别", "医疗健康", "金融账户", "行踪轨迹"],
    "跨境": ["跨境", "境外", "安全评估", "个人信息保护认证", "标准合同", "数据出境"],
    "责任": ["法律责任", "责令改正", "警告", "罚款", "没收违法所得", "行政处罚"],
    "国家标准": ["国家标准", "标准", "GB/T", "个人信息安全规范", "信息安全技术"],
    "国标": ["国家标准", "标准", "GB/T", "个人信息安全规范", "信息安全技术"],
    "GB/T": ["国家标准", "推荐性国家标准", "个人信息安全规范", "信息安全技术"],
    "人脸识别": ["生物识别信息", "敏感个人信息", "个人信息处理", "告知义务", "单独同意", "人脸信息"],
    "定位": ["行踪轨迹", "位置信息", "敏感个人信息", "告知同意", "单独同意"],
    # v0.4.0.2: 公司治理域扩充
    "股东": ["股东", "出资", "股权", "分红", "表决权", "股东会", "知情权", "查阅权", "股东权益"],
    "董事": ["董事", "监事", "高管", "忠实义务", "勤勉义务", "关联交易", "高管责任", "董事违规"],
    "公司": ["公司", "章程", "注册资本", "法人", "法人人格否认", "连带责任", "人格混同"],
    "出资": ["出资", "认缴", "实缴", "出资义务", "出资违约责任", "按期足额", "抽逃出资"],
    "分红": ["分红", "利润分配", "弥补亏损", "违法分红", "股利", "股东分红"],
    "股权转让": ["股权转让", "优先购买权", "转让股权", "股权变更", "股东退出"],
    # v0.4.0.2: 市场秩序域扩充
    "垄断": ["垄断协议", "市场支配地位", "经营者集中", "滥用", "排除限制竞争", "固定价格", "联合涨价", "协同行为"],
    "不正当竞争": ["混淆行为", "商业贿赂", "虚假宣传", "商业秘密", "诋毁", "不正当竞争", "仿冒", "傍名牌", "山寨"],
    "滥用": ["市场支配地位", "二选一", "排他交易", "搭售", "差别待遇", "拒绝交易", "捆绑销售"],
    "经营者集中": ["经营者集中", "并购", "合并", "收购", "申报", "反垄断审查"],
    "虚假宣传": ["虚假宣传", "虚假广告", "误导消费者", "夸大宣传", "刷单", "虚假好评"],
    "商业秘密": ["商业秘密", "客户名单", "技术秘密", "经营信息", "保密信息", "跳槽带走", "前员工带走"],
    # v0.4.0.2: 知识产权域扩充
    "商标": ["商标", "注册商标", "商标专用权", "商标侵权", "近似商标", "驰名商标", "仿冒商标", "山寨商标", "撤三", "商标撤销"],
    "专利": ["专利", "发明", "实用新型", "外观设计", "专利权", "专利侵权", "职务发明", "专利无效", "强制许可"],
    "专利侵权": ["专利侵权", "未经许可实施", "假冒专利", "仿制专利", "专利纠纷", "侵犯专利权"],
    "职务发明": ["职务发明", "专利权属", "职务成果", "员工发明", "工作发明", "职务内发明"],
    # v0.4.0.2: 财税域扩充
    "增值税": ["增值税", "销项税额", "进项税额", "抵扣", "发票", "纳税人", "税率", "征收率"],
    "纳税": ["纳税", "纳税人", "税率", "税收", "申报", "缴纳", "发票", "偷税", "逃税", "漏税"],
    "发票": ["发票", "虚开", "虚开发票", "增值税发票", "发票管理", "违法发票"],
    # v0.4.0.2: 民商事域扩充
    "合同": ["合同", "格式条款", "违约责任", "履行", "解除", "无效", "撤销", "缔约过失"],
    "侵权": ["侵权", "损害赔偿", "过错", "因果关系", "停止侵害", "赔礼道歉", "侵权责任"],
    "物权": ["物权", "所有权", "共有", "抵押权", "质权", "业主", "共有部分", "建筑物区分"],
    "派遣": ["劳务派遣", "派遣用工", "外包用工", "规避劳动法", "非正式用工", "核心岗位外包"],
    # v0.4.0.2: 安全合规域扩充
    "国家秘密": ["国家秘密", "保密", "定密", "密级", "保密期限", "知悉范围", "泄密", "保密制度", "保密管理"],
}
# 跨域通用法律术语
GENERAL_LEGAL_TERMS = ["应当", "不得", "有权", "义务", "规则", "处理", "处罚", "责任", "合法", "违法"]
PRINCIPLE_QUERY_TERMS = [
    "合法",
    "正当",
    "必要",
    "诚信",
    "目的明确",
    "合理目的",
    "最小必要",
    "公开透明",
    "个人信息质量",
    "安全保障",
]
STANDARD_QUERY_HINTS = ["国家标准", "国标", "GB/T", "GB ", "GB/Z", "推荐性国家标准", "强制性国家标准", "标准规定"]
INFORMATION_SCOPE_QUERY_HINTS = ["哪些信息", "何种信息", "信息类型", "保护范围", "保护哪些", "包括哪些"]
PIPL_LAW_NAME = "中华人民共和国个人信息保护法"
DATA_EXPORT_MEASURES_NAME = "数据出境安全评估办法"
STANDARD_CONTRACT_MEASURES_NAME = "个人信息出境标准合同办法"
COMPANY_LAW_NAME = "中华人民共和国公司法"
ANTI_UNFAIR_COMPETITION_LAW_NAME = "中华人民共和国反不正当竞争法"
ANTI_MONOPOLY_LAW_NAME = "中华人民共和国反垄断法"
TRADEMARK_LAW_NAME = "中华人民共和国商标法"
PATENT_LAW_NAME = "中华人民共和国专利法"
VAT_LAW_NAME = "中华人民共和国增值税法"
CIVIL_CODE_NAME = "中华人民共和国民法典"
STATE_SECRETS_LAW_NAME = "中华人民共和国保守国家秘密法"


def add_article_anchors(
    anchors: dict[str, list[int]],
    target_law_name: str,
    article_numbers: list[int],
):
    """向确定性法条锚点追加条号，并保留规则命中的稳定顺序。"""
    bucket = anchors.setdefault(target_law_name, [])
    for article_no in article_numbers:
        if article_no not in bucket:
            bucket.append(article_no)


# ── v0.4.3: Layered Retrieval (Dense + BM25 Union) + Cross-Encoder Reranker ──


def match_scene_anchors_from_rules(question: str, category: str | None = None) -> dict[str, list[int]]:
    """根据 config/rag_anchor_rules.json 匹配场景锚点；category 非空时仅匹配对应域。"""
    rules = _load_anchor_rules()
    anchors: dict[str, list[int]] = {}
    domains_to_check = [category] if category else list(rules.get("domains", {}).keys())
    for domain in domains_to_check:
        domain_rules = rules.get("domains", {}).get(domain)
        if not domain_rules:
            continue
        matched_rules = []
        for rule_index, rule in enumerate(domain_rules.get("scene_anchors", [])):
            triggers = rule.get("triggers", [])
            context_any = rule.get("context_any", [])
            matched_triggers = [t for t in triggers if t in question]
            if not matched_triggers:
                continue
            matched_context = [c for c in context_any if c in question]
            if context_any and not matched_context:
                continue
            max_trigger_len = max(len(t) for t in matched_triggers)
            max_context_len = max((len(c) for c in matched_context), default=0)
            matched_rules.append((max(max_trigger_len, max_context_len), len(matched_triggers) + len(matched_context), -rule_index, rule))
        matched_rules.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        for _, _, _, rule in matched_rules:
            for anchor in rule.get("anchors", []):
                source = anchor["source"]
                if "articles" in anchor:
                    add_article_anchors(anchors, source, anchor["articles"])
    priority_sources = []
    if "标准合同" in question and "重新评估" in question:
        priority_sources.append(STANDARD_CONTRACT_MEASURES_NAME)
    if priority_sources:
        ordered_anchors: dict[str, list[int]] = {}
        for source in priority_sources:
            if source in anchors:
                ordered_anchors[source] = anchors[source]
        for source, article_numbers in anchors.items():
            if source not in ordered_anchors:
                ordered_anchors[source] = article_numbers
        return ordered_anchors
    return anchors


def matched_scene_rules_from_config(question: str, category: str | None = None) -> list[dict]:
    """Return matched scene rules for deterministic output taxonomy supplements."""
    rules = _load_anchor_rules()
    domains_to_check = [category] if category else list(rules.get("domains", {}).keys())
    matched_rules: list[tuple[int, int, int, dict]] = []
    for domain in domains_to_check:
        domain_rules = rules.get("domains", {}).get(domain)
        if not domain_rules:
            continue
        for rule_index, rule in enumerate(domain_rules.get("scene_anchors", [])):
            triggers = rule.get("triggers", [])
            context_any = rule.get("context_any", [])
            matched_triggers = [term for term in triggers if term in question]
            if not matched_triggers:
                continue
            matched_context = [term for term in context_any if term in question]
            if context_any and not matched_context:
                continue
            max_trigger_len = max(len(term) for term in matched_triggers)
            max_context_len = max((len(term) for term in matched_context), default=0)
            matched_rules.append((
                max(max_trigger_len, max_context_len),
                len(matched_triggers) + len(matched_context),
                -rule_index,
                rule,
            ))
    matched_rules.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [rule for _, _, _, rule in matched_rules]


LOW_RISK_QUESTION_HINTS = [
    "依法",
    "合法有效",
    "如实",
    "真实描述",
    "无夸大",
    "无虚假",
    "按期足额",
    "已明确告知",
    "取得单独同意",
    "可以关闭",
    "未与竞争对手协商",
    "独立制定",
]

HIGH_RISK_QUESTION_HINTS = [
    "未按",
    "未实际",
    "未弥补",
    "未申报",
    "未获得",
    "未取得",
    "未提示",
    "未通知",
    "未经",
    "私自",
    "出售",
    "泄露",
    "违规",
    "违法",
    "虚开",
    "虚报",
    "滥用",
    "拒绝",
    "规避",
    "侵权",
    "无效",
    "缺陷",
    "受伤",
    "自动续费",
    "算法歧视",
    "不合理差别待遇",
    "经营者集中",
]

MEDIUM_RISK_QUESTION_HINTS = [
    "股权转让",
    "未使用",
    "通用名称",
    "职务发明",
    "餐饮服务",
    "抵扣",
]


def looks_like_low_risk_question(question: str) -> bool:
    """Identify explicit compliance examples so rule supplements do not create false risks."""
    if "未与竞争对手协商" in question and any(term in question for term in ["独立", "自主", "自身成本"]):
        return True
    if "真实描述" in question and any(term in question for term in ["无夸大", "无虚假"]):
        return True
    if "按期足额" in question and "缴纳出资" in question:
        return True
    negative_markers = [
        "未按",
        "未实际",
        "未弥补",
        "未申报",
        "未取得",
        "未获得",
        "未经",
        "未提示",
        "未通知",
        "未约定",
        "私自",
        "出售",
        "泄露",
        "违法",
        "违规",
        "虚开",
        "虚报",
        "滥用",
        "拒绝",
        "规避",
        "侵权",
        "无效",
        "缺陷",
        "受伤",
    ]
    return any(term in question for term in LOW_RISK_QUESTION_HINTS) and not any(
        term in question for term in negative_markers
    )


def infer_rule_based_risk_level(question: str) -> str:
    if any(term in question for term in HIGH_RISK_QUESTION_HINTS):
        return "high"
    if any(term in question for term in MEDIUM_RISK_QUESTION_HINTS):
        return "medium"
    return "medium"


# v0.3.11: infer_scene_article_anchors 已迁移到 config/rag_anchor_rules.json
# match_scene_anchors_from_rules() 统一驱动全部 7 法域场景锚点
def infer_scene_article_anchors(question: str) -> dict[str, set[int]]:
    """[已废弃] 场景锚点已迁移到 match_scene_anchors_from_rules() + rag_anchor_rules.json。"""
    return {}


def infer_filters_from_question(
    question: str,
    document_type: str | None,
    law_level: str | None,
    standard_type: str | None,
) -> tuple[str | None, str | None, str | None]:
    """根据问题中的明确限定词补充默认过滤器；显式参数优先。"""
    inferred_document_type = document_type
    inferred_law_level = law_level
    inferred_standard_type = standard_type

    if any(hint in question for hint in STANDARD_QUERY_HINTS):
        inferred_document_type = inferred_document_type or "标准"
        if any(hint in question for hint in ["国家标准", "国标", "GB/T", "GB ", "GB/Z", "推荐性国家标准", "强制性国家标准"]):
            inferred_law_level = inferred_law_level or "国家标准"
        if "推荐性国家标准" in question or "GB/T" in question:
            inferred_standard_type = inferred_standard_type or "推荐性国家标准"
        elif "强制性国家标准" in question:
            inferred_standard_type = inferred_standard_type or "强制性国家标准"
        elif "指导性技术文件" in question or "GB/Z" in question:
            inferred_standard_type = inferred_standard_type or "国家标准化指导性技术文件"

    if any(hint in question for hint in ["指导性案例", "典型案例", "裁判文书", "判例"]):
        inferred_document_type = inferred_document_type or "案例"

    if any(hint in question for hint in ["专利", "权利要求", "发明人"]):
        inferred_document_type = inferred_document_type or "法律法规"

    return inferred_document_type, inferred_law_level, inferred_standard_type


def is_standard_scope_question(question: str, document_type: str | None) -> bool:
    """识别询问标准中保护/处理信息范围的题型。"""
    return (
        document_type == "标准"
        and any(hint in question for hint in INFORMATION_SCOPE_QUERY_HINTS)
    )


def standard_anchor_sections(question: str, document_type: str | None) -> list[str]:
    """识别国家标准类问题中可直接锚定的章节。"""
    if document_type != "标准":
        return []

    sections = []
    if "最小必要" in question or ("收集" in question and "必要" in question):
        sections.append("5.2")
    if "查询" in question and ("个人信息主体" in question or "权利" in question):
        sections.append("8.1")
    if is_standard_scope_question(question, document_type):
        sections.extend(["3.1", "3.2"])

    deduped = []
    seen = set()
    for section in sections:
        if section not in seen:
            seen.add(section)
            deduped.append(section)
    return deduped


def source_allows_named_supplement(
    law_name: str | None,
    source: str | None,
    target_name: str,
) -> bool:
    """显式限定其他 source/law_name 时，不混入命名补充候选。"""
    if law_name and law_name != target_name:
        return False
    if source and source != target_name:
        return False
    return True
