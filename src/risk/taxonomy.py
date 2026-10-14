"""Deterministic risk taxonomy used by the risk engine."""

from __future__ import annotations


RISK_LEVELS = {"low": 0, "medium": 1, "high": 2}

RISK_TAXONOMY = [
    {
        "id": "notice_consent",
        "name": "告知同意不合规",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["告知", "同意", "单独同意", "明示同意", "未取得同意", "未履行告知义务"],
    },
    {
        "id": "sensitive_personal_info",
        "name": "敏感个人信息处理风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["敏感个人信息", "人脸", "生物识别", "精准定位", "行踪轨迹", "医疗健康", "病历"],
    },
    {
        "id": "children_personal_info",
        "name": "儿童个人信息保护风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["儿童", "未成年人", "不满十四", "监护人"],
    },
    {
        "id": "data_export",
        "name": "数据出境合规风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["出境", "境外", "跨境", "境外接收方", "安全评估", "标准合同"],
    },
    {
        "id": "third_party_sharing",
        "name": "第三方共享或提供风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["第三方", "共享", "提供给", "营销公司", "广告平台", "转让"],
    },
    {
        "id": "security_incident",
        "name": "安全事件处置风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["泄露", "服务器被攻击", "安全事件", "补救措施", "通知义务"],
    },
    {
        "id": "internal_misuse",
        "name": "内部人员违规与管理失职风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["员工私自", "内部人员", "导出", "出售", "权限", "日志审计", "管理失职"],
    },
    {
        "id": "automated_decision",
        "name": "自动化决策与算法歧视风险",
        "domain": "数据合规",
        "default_level": "high",
        "keywords": ["自动化决策", "算法", "算法歧视", "差异化定价", "价格歧视", "不合理差别待遇"],
    },
    {
        "id": "purpose_change",
        "name": "处理目的变更或超范围使用风险",
        "domain": "数据合规",
        "default_level": "medium",
        "keywords": ["目的变更", "超出原授权", "超范围", "二次利用", "模型训练", "训练AI"],
    },
    {
        "id": "data_minimization",
        "name": "最小必要原则风险",
        "domain": "数据合规",
        "default_level": "medium",
        "keywords": ["最小必要", "过度收集", "直接相关", "不必要", "减少收集"],
    },
    {
        "id": "anonymization",
        "name": "匿名化与再识别风险",
        "domain": "数据合规",
        "default_level": "medium",
        "keywords": ["匿名化", "去标识化", "再识别", "重新识别", "匿名化效果"],
    },
    # v0.3.8: 公司治理域
    {
        "id": "capital_contribution",
        "name": "出资违约风险",
        "domain": "公司治理",
        "default_level": "high",
        "keywords": ["出资", "认缴", "缴纳出资", "未按期"],
    },
    {
        "id": "illegal_dividend",
        "name": "违法利润分配风险",
        "domain": "公司治理",
        "default_level": "high",
        "keywords": ["分红", "利润分配", "弥补亏损", "违法分红"],
    },
    {
        "id": "director_duty_breach",
        "name": "董事义务违反风险",
        "domain": "公司治理",
        "default_level": "high",
        "keywords": ["忠实义务", "勤勉义务", "关联交易", "谋取私利"],
    },
    {
        "id": "company_personality_abuse",
        "name": "公司人格滥用风险",
        "domain": "公司治理",
        "default_level": "high",
        "keywords": ["法人人格否认", "连带责任", "滥用公司"],
    },
    {
        "id": "shareholder_rights",
        "name": "股东权利侵害风险",
        "domain": "公司治理",
        "default_level": "medium",
        "keywords": ["知情权", "优先购买权", "股权转让", "查阅权"],
    },
    # v0.3.8: 市场秩序域
    {
        "id": "monopoly_agreement",
        "name": "垄断协议风险",
        "domain": "市场秩序",
        "default_level": "high",
        "keywords": ["垄断协议", "固定价格", "横向垄断", "纵向垄断"],
    },
    {
        "id": "abuse_of_dominance",
        "name": "滥用市场支配地位风险",
        "domain": "市场秩序",
        "default_level": "high",
        "keywords": ["市场支配地位", "滥用", "二选一", "排他"],
    },
    {
        "id": "concentration_non_filing",
        "name": "经营者集中未申报风险",
        "domain": "市场秩序",
        "default_level": "high",
        "keywords": ["经营者集中", "合并", "并购", "未申报"],
    },
    {
        "id": "unfair_competition_confusion",
        "name": "市场混淆风险",
        "domain": "市场秩序",
        "default_level": "medium",
        "keywords": ["混淆行为", "误认", "擅自使用", "近似标识"],
    },
    {
        "id": "unfair_competition_false_ad",
        "name": "虚假宣传风险",
        "domain": "市场秩序",
        "default_level": "high",
        "keywords": ["虚假宣传", "虚假广告", "误导", "引人误解"],
    },
    {
        "id": "trade_secret_infringement",
        "name": "商业秘密侵权风险",
        "domain": "市场秩序",
        "default_level": "high",
        "keywords": ["商业秘密", "侵犯商业秘密", "客户名单", "不正当获取"],
    },
    # v0.3.8: 知识产权域
    {
        "id": "trademark_infringement",
        "name": "商标侵权风险",
        "domain": "知识产权",
        "default_level": "high",
        "keywords": ["商标侵权", "假冒注册商标", "近似商标", "混淆"],
    },
    {
        "id": "trademark_invalid",
        "name": "商标无效或撤销风险",
        "domain": "知识产权",
        "default_level": "medium",
        "keywords": ["商标无效", "商标撤销", "通用名称", "缺乏显著性", "三年不使用"],
    },
    {
        "id": "patent_infringement",
        "name": "专利侵权风险",
        "domain": "知识产权",
        "default_level": "high",
        "keywords": ["专利侵权", "未经许可实施", "假冒专利", "发明专利"],
    },
    {
        "id": "patent_validity",
        "name": "专利有效性风险",
        "domain": "知识产权",
        "default_level": "high",
        "keywords": ["专利无效", "新颖性", "创造性", "现有技术"],
    },
    {
        "id": "employee_invention_dispute",
        "name": "职务发明归属风险",
        "domain": "知识产权",
        "default_level": "medium",
        "keywords": ["职务发明", "职务行为", "发明归属", "专利权属"],
    },
    # v0.3.8: 财税域
    {
        "id": "vat_false_invoice",
        "name": "虚开发票风险",
        "domain": "财税",
        "default_level": "high",
        "keywords": ["虚开发票", "虚开", "发票违法"],
    },
    {
        "id": "vat_input_deduction",
        "name": "进项税额抵扣违规风险",
        "domain": "财税",
        "default_level": "medium",
        "keywords": ["进项税额", "不得抵扣", "抵扣", "销项税额"],
    },
    {
        "id": "vat_tax_rate_error",
        "name": "增值税税率适用错误风险",
        "domain": "财税",
        "default_level": "high",
        "keywords": ["税率", "征收率", "少缴税款", "混合销售"],
    },
    {
        "id": "vat_non_filing",
        "name": "未申报纳税风险",
        "domain": "财税",
        "default_level": "high",
        "keywords": ["未申报", "偷税", "隐匿收入", "逃税"],
    },
    # v0.3.8: 民商事域
    {
        "id": "standard_form_terms",
        "name": "格式条款合规风险",
        "domain": "民商事",
        "default_level": "high",
        "keywords": ["格式条款", "提示说明", "自动续费", "无效条款"],
    },
    {
        "id": "contract_breach",
        "name": "违约责任风险",
        "domain": "民商事",
        "default_level": "medium",
        "keywords": ["违约责任", "不履行", "损害赔偿", "违约金"],
    },
    {
        "id": "product_liability",
        "name": "产品责任风险",
        "domain": "民商事",
        "default_level": "high",
        "keywords": ["产品责任", "缺陷产品", "销售者责任", "产品侵权"],
    },
    {
        "id": "property_rights",
        "name": "物权侵害风险",
        "domain": "民商事",
        "default_level": "medium",
        "keywords": ["共有部分", "业主共有", "物权", "所有权"],
    },
    {
        "id": "labor_dispatch_abuse",
        "name": "用工合规风险",
        "domain": "民商事",
        "default_level": "medium",
        "keywords": ["劳务派遣", "规避", "派遣", "用工"],
    },
]


def normalize_risk_level(level: str | None, fallback: str = "medium") -> str:
    normalized = (level or "").strip().lower()
    return normalized if normalized in RISK_LEVELS else fallback


def stronger_level(left: str | None, right: str | None) -> str:
    left_level = normalize_risk_level(left)
    right_level = normalize_risk_level(right)
    return left_level if RISK_LEVELS[left_level] >= RISK_LEVELS[right_level] else right_level


def classify_risk_categories(*texts: object) -> list[dict]:
    """Map free-form scenario/result text into stable taxonomy categories."""
    haystack = " ".join(_flatten_texts(texts))
    categories = []
    for item in RISK_TAXONOMY:
        matched_keywords = [keyword for keyword in item["keywords"] if keyword in haystack]
        if item["name"] in haystack and item["name"] not in matched_keywords:
            matched_keywords.append(item["name"])
        if not matched_keywords:
            continue
        categories.append({
            "id": item["id"],
            "name": item["name"],
            "domain": item["domain"],
            "default_level": item["default_level"],
            "matched_keywords": matched_keywords,
        })
    return categories


def infer_taxonomy_risk_level(categories: list[dict], fallback: str | None = None) -> str:
    level = normalize_risk_level(fallback, fallback="low" if not categories else "medium")
    for category in categories:
        level = stronger_level(level, category.get("default_level"))
    return level


def _flatten_texts(values: tuple[object, ...]) -> list[str]:
    flattened = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip():
                flattened.append(value.strip())
            continue
        if isinstance(value, dict):
            flattened.extend(_flatten_texts(tuple(value.values())))
            continue
        if isinstance(value, (list, tuple, set)):
            flattened.extend(_flatten_texts(tuple(value)))
            continue
        flattened.append(str(value))
    return flattened
