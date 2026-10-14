from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.rag.complex_case import is_complex_multi_issue_question
from src.rag.rules import (
    infer_rule_based_risk_level,
    looks_like_low_risk_question,
    matched_scene_rules_from_config,
)


def append_unique_text(values: list[str], item: str) -> list[str]:
    if not any(item in value or value in item for value in values):
        values.append(item)
    return values


def contains_all(text: str, terms: list[str]) -> bool:
    return all(term in text for term in terms)


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def set_min_confidence(payload: dict, confidence: float) -> None:
    current_confidence = payload.get("confidence_score")
    try:
        current_confidence = float(current_confidence) if current_confidence is not None else 0.0
    except (TypeError, ValueError):
        current_confidence = 0.0
    payload["confidence_score"] = max(current_confidence, confidence)


def set_min_risk_level(payload: dict, minimum: str) -> None:
    order = {"low": 0, "medium": 1, "high": 2}
    current = str(payload.get("risk_level") or "").lower()
    if order.get(current, -1) < order[minimum]:
        payload["risk_level"] = minimum


def cap_risk_level(payload: dict, maximum: str) -> bool:
    order = {"low": 0, "medium": 1, "high": 2}
    current = str(payload.get("risk_level") or "").lower()
    if order.get(current, -1) > order[maximum]:
        payload["risk_level"] = maximum
        return True
    return False


def is_trademark_invalid_or_cancellation_medium_case(question: str, payload: dict | None = None) -> bool:
    has_trademark_context = any(term in question for term in ["商标", "注册商标"])
    if not has_trademark_context:
        return False

    payload = payload or {}
    risk_types_text = " ".join(str(item) for item in payload.get("risk_types") or [])
    actions_text = " ".join(str(item) for item in payload.get("recommended_actions") or [])
    combined_text = " ".join([question, str(payload.get("answer") or ""), risk_types_text, actions_text])
    factual_text = " ".join([question, str(payload.get("answer") or ""), actions_text])
    high_risk_infringement_terms = [
        "未经许可",
        "相同商标",
        "近似",
        "近似商标",
        "混淆",
        "容易导致混淆",
        "侵犯",
        "侵权",
        "侵犯注册商标专用权",
        "商标侵权",
        "假冒",
        "仿冒",
        "冒用",
        "山寨",
        "驰名",
        "销售侵犯",
        "销售假冒注册商标",
        "伪造",
        "擅自制造",
        "反向假冒",
        "停止侵权",
        "侵权赔偿",
    ]
    high_risk_infringement_text = (
        factual_text
        .replace("商标权滥用", "")
        .replace("无权禁止", "")
        .replace("不能禁止", "")
        .replace("不得禁止", "")
        .replace("不构成侵权", "")
        .replace("不涉及直接侵权", "")
    )
    if any(term in high_risk_infringement_text for term in high_risk_infringement_terms):
        return False

    if "通用名称" in question:
        return True

    non_use_terms = ["三年不使用", "连续三年不使用", "连续三年未实际使用"]
    return any(term in question for term in non_use_terms)


def is_property_common_area_medium_case(question: str, payload: dict | None = None) -> bool:
    has_property_context = any(term in question for term in ["物业公司", "物业", "小区"])
    has_common_area = any(term in question for term in ["公共区域", "共有部分", "共有区域"])
    has_commercial_use = any(term in question for term in ["广告经营", "出租", "经营收益", "收益"])
    has_owner_consent_gap = any(term in question for term in ["未经业主同意", "未征得业主同意", "未经业主大会同意", "未经业主共同决定"])
    if not (has_property_context and has_common_area and has_commercial_use and has_owner_consent_gap):
        return False

    payload = payload or {}
    risk_types_text = " ".join(str(item) for item in payload.get("risk_types") or [])
    actions_text = " ".join(str(item) for item in payload.get("recommended_actions") or [])
    combined_text = " ".join([question, str(payload.get("answer") or ""), risk_types_text, actions_text])
    severe_terms = [
        "侵占",
        "挪用",
        "拒不返还",
        "拒不停止",
        "重大损失",
        "严重损害",
        "长期",
        "恶意",
        "刑事",
        "犯罪",
        "行政处罚",
        "欺诈",
        "伪造",
        "暴力",
    ]
    if any(term in combined_text for term in severe_terms):
        return False

    return True


def is_unfair_competition_confusion_medium_case(question: str) -> bool:
    """Keep an isolated confusion dispute distinct from aggravated misconduct.

    Similar branding that may mislead consumers is a material legal risk, but a
    high rating should be reserved for facts such as repeated, malicious or
    large-scale conduct, or an identified severe consequence.  This keeps the
    output calibrated to the user's stated facts rather than an LLM's generic
    reference to maximum penalties.
    """
    confusion_terms = [
        "混淆行为",
        "引人误认",
        "消费者误认",
        "近似标识",
        "店铺名称",
        "装修风格",
        "包装装潢",
        "傍名牌",
        "仿冒",
        "山寨",
    ]
    if not any(term in question for term in confusion_terms):
        return False

    aggravating_terms = [
        "恶意",
        "多次",
        "反复",
        "长期",
        "大规模",
        "巨额",
        "重大损失",
        "严重损害",
        "拒不",
        "行政处罚",
        "刑事",
        "犯罪",
        "有组织",
    ]
    return not any(term in question for term in aggravating_terms)


def is_share_transfer_notice_medium_case(question: str, payload: dict | None = None) -> bool:
    if not all(term in question for term in ["股权", "转让"]):
        return False
    has_llc_context = any(term in question for term in ["有限责任公司", "有限公司"])
    has_other_shareholder_notice = "其他股东" in question and any(term in question for term in ["未通知", "通知义务"])
    has_priority_purchase_context = any(term in question for term in ["优先购买权", "对外转让"])
    if not (has_llc_context and has_other_shareholder_notice and has_priority_purchase_context):
        return False

    non_civil_procedure_terms = [
        "上市公司",
        "信息披露",
        "证券",
        "国有",
        "国资",
        "产权交易",
        "司法执行",
        "强制执行",
        "法院",
        "拍卖",
        "质押",
        "代持",
        "债权人",
        "监管",
        "审批",
        "批准",
        "登记",
    ]
    if any(term in question for term in non_civil_procedure_terms):
        return False

    payload = payload or {}
    risk_types_text = " ".join(str(item) for item in payload.get("risk_types") or [])
    actions_text = " ".join(str(item) for item in payload.get("recommended_actions") or [])
    combined_text = " ".join([question, str(payload.get("answer") or ""), risk_types_text, actions_text])
    severe_terms = [
        "恶意串通",
        "伪造",
        "虚假",
        "欺诈",
        "抽逃出资",
        "损害公司利益",
        "重大损失",
        "严重损害",
        "刑事",
        "犯罪",
        "行政处罚",
        "拒不",
    ]
    if any(term in combined_text for term in severe_terms):
        return False

    return True


def is_vat_mixed_sales_rate_accounting_medium_case(question: str, payload: dict | None = None) -> bool:
    has_mixed_transaction_context = (
        any(term in question for term in ["混合销售", "兼营", "两项以上应税交易", "不同税率"])
        or (
            any(term in question for term in ["同时销售", "销售货物", "货物销售"])
            and any(term in question for term in ["提供", "安装服务", "服务"])
        )
    )
    has_rate_accounting_gap = any(
        term in question
        for term in ["未区分收入", "未分别核算", "未区分", "统一按低税率", "按低税率", "低税率纳税", "分别核算"]
    )
    has_tax_rate_context = any(term in question for term in ["税率", "征收率", "纳税", "增值税", "少缴税款"])
    if not (has_mixed_transaction_context and has_rate_accounting_gap and has_tax_rate_context):
        return False

    severe_terms = [
        "虚开",
        "虚开发票",
        "伪造",
        "骗取出口退税",
        "出口退税",
        "偷税",
        "逃税",
        "偷逃税",
        "隐匿收入",
        "不申报",
        "未申报",
        "拒不缴纳",
        "拒不补缴",
        "拒不改正",
        "重大",
        "巨额",
        "多次",
        "反复",
        "故意",
        "恶意",
        "行政处罚",
        "刑事",
        "犯罪",
    ]
    if any(term in question for term in severe_terms):
        return False

    return True


def append_unique_texts(values: list[str], items: list[str]) -> list[str]:
    for item in items:
        values = append_unique_text(values, item)
    return values


def append_answer_note(payload: dict, answer: str, note: str, required_any: list[str] | None = None) -> str:
    if note in answer:
        return answer
    if required_any and contains_any(answer, required_any):
        return answer
    payload["answer"] = f"{answer} {note}".strip()
    return payload["answer"]


def payload_contribution_trace(payload: dict) -> dict:
    return payload.setdefault(
        "_contribution_trace",
        {
            "term_preservation_rules": [],
            "risk_supplement_rules": [],
            "scene_output_rules": [],
            "low_risk_rules": [],
            "compliant_permission_rule": False,
        },
    )


def set_risk_level(payload: dict, level: str, mode: str = "set") -> None:
    if mode == "default" and payload.get("risk_level") is not None:
        return
    if mode == "upgrade_if_low" and payload.get("risk_level") not in {None, "low"}:
        return
    payload["risk_level"] = level


def payload_rule_matches(rule: dict, question: str) -> bool:
    if not contains_all(question, rule.get("question_all", [])):
        return False
    if rule.get("question_any") and not contains_any(question, rule["question_any"]):
        return False
    for group in rule.get("question_any_groups", []):
        if not contains_any(question, group):
            return False
    if rule.get("question_not_any") and contains_any(question, rule["question_not_any"]):
        return False
    return True


def apply_payload_supplement_rule(
    rule: dict,
    payload: dict,
    question: str,
    answer: str,
    risk_types: list[str],
    actions: list[str],
    rule_index: int | None = None,
) -> tuple[str, list[str], list[str]]:
    if not payload_rule_matches(rule, question):
        return answer, risk_types, actions

    before_risk_types = list(risk_types)
    before_actions = list(actions)
    before_risk_level = payload.get("risk_level")
    before_confidence = payload.get("confidence_score")
    risk_types = append_unique_texts(risk_types, rule.get("risk_types", []))
    for risk_type in rule.get("exact_risk_types", []):
        if risk_type not in risk_types:
            risk_types.append(risk_type)
    actions = append_unique_texts(actions, rule.get("actions", []))

    if "risk_level" in rule:
        set_risk_level(payload, rule["risk_level"], rule.get("risk_level_mode", "set"))
    if "confidence_min" in rule:
        set_min_confidence(payload, float(rule["confidence_min"]))

    note = rule.get("answer_note")
    answer_note_added = False
    if note:
        unless_all = rule.get("answer_note_unless_all", [])
        unless_any = rule.get("answer_note_unless_any", [])
        should_append = not (
            (unless_all and contains_all(answer, unless_all))
            or (unless_any and contains_any(answer, unless_any))
        )
        if should_append and note not in answer:
            payload["answer"] = f"{answer} {note}".strip()
            answer = payload["answer"]
            answer_note_added = True

    trace = payload_contribution_trace(payload)
    trace["risk_supplement_rules"].append({
        "index": rule_index,
        "question_all": rule.get("question_all", []),
        "question_any": rule.get("question_any", []),
        "question_any_groups": rule.get("question_any_groups", []),
        "added_risk_types": [item for item in risk_types if item not in before_risk_types],
        "added_actions": [item for item in actions if item not in before_actions],
        "risk_level_changed": payload.get("risk_level") != before_risk_level,
        "confidence_changed": payload.get("confidence_score") != before_confidence,
        "answer_note_added": answer_note_added,
    })

    return answer, risk_types, actions


RISK_PAYLOAD_SUPPLEMENT_RULES_PATH = (
    Path(__file__).parent.parent.parent / "config" / "risk_payload_supplement_rules.json"
)

RISK_PAYLOAD_RULE_ALLOWED_KEYS = {
    "question_all",
    "question_any",
    "question_any_groups",
    "question_not_any",
    "risk_types",
    "exact_risk_types",
    "actions",
    "risk_level",
    "risk_level_mode",
    "scenario_id",
    "confidence_min",
    "answer_note",
    "answer_note_unless_all",
    "answer_note_unless_any",
}

RISK_PAYLOAD_RULE_LIST_FIELDS = {
    "question_all",
    "question_any",
    "question_not_any",
    "risk_types",
    "exact_risk_types",
    "actions",
    "answer_note_unless_all",
    "answer_note_unless_any",
}


def _validate_string_list(rule: dict, key: str, rule_label: str, errors: list[str]) -> None:
    if key not in rule:
        return
    values = rule[key]
    if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
        errors.append(f"{rule_label}.{key} must be a list of non-empty strings")


def validate_risk_payload_supplement_rules(rules: object) -> list[dict]:
    """Validate config/risk_payload_supplement_rules.json before it drives output policy."""
    if not isinstance(rules, list):
        raise ValueError("risk payload supplement rules must be a list")

    errors: list[str] = []
    for index, rule in enumerate(rules):
        rule_label = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{rule_label} must be an object")
            continue

        unknown_keys = sorted(set(rule) - RISK_PAYLOAD_RULE_ALLOWED_KEYS)
        if unknown_keys:
            errors.append(f"{rule_label} has unknown keys: {', '.join(unknown_keys)}")

        has_question_matcher = any(
            rule.get(key) for key in ("question_all", "question_any", "question_any_groups")
        )
        if not has_question_matcher:
            errors.append(f"{rule_label} must define at least one question matcher")

        has_effect = any(
            rule.get(key)
            for key in (
                "risk_types",
                "exact_risk_types",
                "actions",
                "risk_level",
                "confidence_min",
                "answer_note",
            )
        )
        if not has_effect:
            errors.append(f"{rule_label} must define at least one payload effect")

        for key in RISK_PAYLOAD_RULE_LIST_FIELDS:
            _validate_string_list(rule, key, rule_label, errors)

        groups = rule.get("question_any_groups")
        if groups is not None:
            valid_groups = isinstance(groups, list) and all(
                isinstance(group, list)
                and group
                and all(isinstance(term, str) and term for term in group)
                for group in groups
            )
            if not valid_groups:
                errors.append(f"{rule_label}.question_any_groups must be a list of string lists")

        risk_level = rule.get("risk_level")
        if risk_level is not None and risk_level not in {"low", "medium", "high"}:
            errors.append(f"{rule_label}.risk_level must be low, medium, or high")

        risk_level_mode = rule.get("risk_level_mode")
        if risk_level_mode is not None and risk_level_mode not in {"set", "default", "upgrade_if_low"}:
            errors.append(f"{rule_label}.risk_level_mode is invalid")

        scenario_id = rule.get("scenario_id")
        if scenario_id is not None and (not isinstance(scenario_id, str) or not scenario_id):
            errors.append(f"{rule_label}.scenario_id must be a non-empty string")

        confidence_min = rule.get("confidence_min")
        if confidence_min is not None and not isinstance(confidence_min, (int, float)):
            errors.append(f"{rule_label}.confidence_min must be numeric")

        answer_note = rule.get("answer_note")
        if answer_note is not None and not isinstance(answer_note, str):
            errors.append(f"{rule_label}.answer_note must be a string")

    if errors:
        raise ValueError("Invalid risk payload supplement rules: " + "; ".join(errors))
    return rules


@lru_cache(maxsize=1)
def load_risk_payload_supplement_rules() -> list[dict]:
    with open(RISK_PAYLOAD_SUPPLEMENT_RULES_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict) or "rules" not in payload:
        raise ValueError("risk payload supplement config must contain a rules list")
    return validate_risk_payload_supplement_rules(payload["rules"])


LEGAL_TERM_PRESERVATION_RULES = [
    {
        "question_all": ["个人信息", "原则"],
        "source_any": ["中华人民共和国个人信息保护法"],
        "required_terms": ["合法", "正当", "必要", "诚信", "公开透明", "信息质量"],
        "note": "术语归纳：个人信息处理原则包括合法、正当、必要、诚信、公开透明以及保证个人信息质量等要求。",
        "confidence": 0.85,
    },
    {
        "question_all": ["撤回同意"],
        "source_any": ["中华人民共和国个人信息保护法"],
        "required_terms": ["撤回同意", "便捷方式"],
        "note": "术语归纳：个人信息处理者应当提供便捷方式，保障个人撤回同意。",
        "confidence": 0.85,
    },
    {
        "question_any": ["人脸识别", "人脸信息", "生物识别"],
        "source_any": ["中华人民共和国个人信息保护法"],
        "required_terms": ["生物识别"],
        "note": "术语归纳：人脸信息属于生物识别信息，通常应按敏感个人信息处理规则进行保护。",
        "confidence": 0.85,
    },
    {
        "question_all": ["保护哪些信息"],
        "source_any": ["信息安全技术 个人信息安全规范"],
        "confidence": 0.85,
    },
    {
        "question_all": ["民事", "原则"],
        "source_any": ["中华人民共和国民法典"],
        "required_terms": ["平等", "自愿", "公平", "诚信", "公序良俗"],
        "note": "术语归纳：民事活动基本原则包括平等、自愿、公平、诚信和公序良俗等要求。",
        "confidence": 0.85,
    },
    {
        "question_all": ["责任"],
        "question_any": ["产品", "商品", "质量缺陷"],
        "source_any": ["中华人民共和国民法典"],
        "required_terms": ["请求赔偿", "追偿", "惩罚性赔偿"],
        "note": "术语归纳：产品存在缺陷造成损害的，被侵权人可以向生产者或销售者请求赔偿；产品缺陷由一方造成的，另一方赔偿后可以追偿；明知缺陷仍生产、销售并造成严重损害的，可能涉及惩罚性赔偿。",
        "confidence": 0.85,
    },
    {
        "question_all": ["股东", "权利"],
        "source_any": ["中华人民共和国公司法"],
        "required_terms": ["表决", "分红"],
        "note": "术语归纳：股东法定权利通常包括参与公司治理的表决权，以及依法取得分红、利润分配等财产性权利。",
        "confidence": 0.85,
    },
    {
        "question_all": ["滥用市场支配地位"],
        "source_any": ["反垄断法"],
        "required_terms": ["排除"],
        "note": "术语归纳：滥用市场支配地位的法律评价重点在于排除、限制竞争。",
        "confidence": 0.85,
    },
    {
        "question_all": ["不正当竞争"],
        "source_any": ["反不正当竞争法"],
        "required_terms": ["虚假宣传", "商业秘密"],
        "note": "术语归纳：反不正当竞争法禁止的典型不正当竞争行为包括混淆行为、商业贿赂、虚假宣传和侵犯商业秘密等。",
        "confidence": 0.85,
    },
    {
        "question_all": ["侵犯注册商标专用权"],
        "source_any": ["中华人民共和国商标法"],
        "required_terms": ["商标侵权", "未经许可", "相同商标", "近似商标"],
        "note": "术语归纳：这些行为可概括为商标侵权，核心包括未经许可使用相同商标或近似商标等情形。",
        "confidence": 0.85,
    },
    {
        "question_all": ["不得作为商标注册"],
        "source_any": ["中华人民共和国商标法"],
        "required_terms": ["不得注册", "缺乏显著性"],
        "note": "术语归纳：通用名称、直接描述性标志和其他缺乏显著性的标志，依法属于不得注册的范围。",
        "confidence": 0.85,
    },
    {
        "question_all": ["进项税额", "抵扣"],
        "source_any": ["中华人民共和国增值税法"],
        "required_terms": ["不得抵扣"],
        "note": "术语归纳：上述进项税额依法不得抵扣。",
        "confidence": 0.85,
    },
    {
        "question_all": ["未经许可", "专利"],
        "source_any": ["中华人民共和国专利法"],
        "required_terms": ["专利侵权"],
        "note": "术语归纳：未经许可实施他人专利构成专利侵权。",
        "confidence": 0.85,
    },
    {
        "question_all": ["专利"],
        "question_any": ["新颖性", "申请日前已公开", "公开"],
        "source_any": ["中华人民共和国专利法"],
        "required_terms": ["无效宣告"],
        "note": "术语归纳：不具备新颖性的专利可能被提出无效宣告请求。",
        "confidence": 0.85,
    },
    {
        "question_all": ["个人信息出境", "条件"],
        "source_any": ["中华人民共和国个人信息保护法"],
        "required_terms": ["安全评估", "标准合同", "保护认证", "影响评估"],
        "note": "术语归纳：个人信息出境通常需要满足安全评估、个人信息保护认证、标准合同等合规路径，并开展个人信息保护影响评估。",
        "confidence": 0.85,
    },
    {
        "question_all": ["标准合同", "重新评估"],
        "source_any": ["个人信息出境标准合同办法"],
        "required_terms": ["重新评估", "补充订立"],
        "note": "术语归纳：标准合同有效期内出现法定变化情形的，应重新开展个人信息保护影响评估，并补充或者重新订立标准合同、履行相应备案手续。",
        "confidence": 0.85,
    },
    {
        "question_any": ["数据分类分级", "分类分级"],
        "source_any": ["中华人民共和国数据安全法"],
        "required_terms": ["分类分级", "保护制度", "重要数据目录", "核心数据"],
        "note": "术语归纳：数据安全治理应建立分类分级保护制度，识别重要数据目录，并对核心数据实行更严格保护。",
        "confidence": 0.85,
    },
    {
        "question_all": ["商标", "未经许可"],
        "source_any": ["中华人民共和国商标法"],
        "required_terms": ["商标侵权", "近似", "未经许可"],
        "note": "术语归纳：未经许可使用相同或近似标识、容易导致混淆的，可能构成商标侵权。",
        "confidence": 0.85,
    },
]


RISK_PAYLOAD_SUPPLEMENT_RULES = load_risk_payload_supplement_rules()


def legal_term_rule_matches(rule: dict, question: str, source_text: str) -> bool:
    question_all = rule.get("question_all", [])
    question_any = rule.get("question_any", [])
    source_any = rule.get("source_any", [])
    return (
        contains_all(question, question_all)
        and (not question_any or contains_any(question, question_any))
        and (not source_any or contains_any(source_text, source_any))
    )


def enrich_answer_legal_terms(question: str, payload: dict, evidence_chain: list[dict]) -> dict:
    """Deterministically preserve legal terms when retrieved evidence already supports them."""
    answer = payload.get("answer") or ""
    source_text = "\n".join(str(item.get("source", "")) for item in evidence_chain)

    for rule in LEGAL_TERM_PRESERVATION_RULES:
        if not legal_term_rule_matches(rule, question, source_text):
            continue
        required_terms = rule.get("required_terms", [])
        note = rule.get("note", "")
        before_answer = answer
        before_confidence = payload.get("confidence_score")
        if note and not contains_all(answer, required_terms) and note not in answer:
            answer = f"{answer} {note}".strip()
        confidence = rule.get("confidence")
        if confidence is not None:
            set_min_confidence(payload, float(confidence))
        if answer != before_answer or payload.get("confidence_score") != before_confidence:
            payload_contribution_trace(payload)["term_preservation_rules"].append({
                "question_all": rule.get("question_all", []),
                "question_any": rule.get("question_any", []),
                "source_any": rule.get("source_any", []),
                "required_terms": required_terms,
                "note_added": answer != before_answer,
                "confidence_changed": payload.get("confidence_score") != before_confidence,
            })

    payload["answer"] = answer
    return payload


def enrich_risk_payload(question: str, payload: dict, category: str | None = None) -> dict:
    """Add deterministic scenario actions that should not depend on model wording."""
    actions = list(payload.get("recommended_actions") or [])
    risk_types = list(payload.get("risk_types") or [])
    answer = payload.get("answer") or ""
    complex_multi_issue = is_complex_multi_issue_question(question)

    if looks_like_low_risk_question(question):
        trace = payload_contribution_trace(payload)
        payload["risk_level"] = "low"
        set_min_confidence(payload, 0.85)
        if "按期足额" in question and "缴纳出资" in question and "依法履行出资义务" not in answer:
            payload["answer"] = f"{answer} 股东已按期足额缴纳出资，属于依法履行出资义务，整体合法且无违法行为。".strip()
            answer = payload["answer"]
            trace["low_risk_rules"].append("capital_contribution")
        if "弥补亏损" in question and "分配利润" in question and "合法分红" not in answer:
            payload["answer"] = f"{answer} 公司先弥补亏损并提取法定公积金后依法分配利润，属于合法分红。".strip()
            answer = payload["answer"]
            trace["low_risk_rules"].append("dividend")
        if "如实申报" in question and "发票" in question and "纳税" not in answer:
            payload["answer"] = f"{answer} 企业如实申报收入、依法开具发票并履行纳税义务，通常属于低风险税务合规情形。".strip()
            answer = payload["answer"]
            trace["low_risk_rules"].append("tax_compliance")
        if "真实描述" in question and "广告" in question and "宣传" not in answer:
            payload["answer"] = f"{answer} 广告内容真实、无夸大或虚假宣传的，一般不构成不正当竞争。".strip()
            answer = payload["answer"]
            trace["low_risk_rules"].append("true_advertising")
    elif not complex_multi_issue:
        rule_output_applied = False
        for rule in matched_scene_rules_from_config(question, category):
            rule_risk_types = rule.get("risk_types", []) or []
            rule_actions = rule.get("actions", []) or []
            risk_types = append_unique_texts(risk_types, rule_risk_types)
            actions = append_unique_texts(actions, rule_actions)
            if rule_risk_types or rule_actions:
                payload_contribution_trace(payload)["scene_output_rules"].append({
                    "id": rule.get("id"),
                    "risk_types": rule_risk_types,
                    "actions": rule_actions,
                })
                rule_output_applied = True
        if rule_output_applied:
            set_min_confidence(payload, 0.85)
            if payload.get("risk_level") is None:
                payload["risk_level"] = infer_rule_based_risk_level(question)

    if complex_multi_issue:
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "skip_generic_rules_for_complex_multi_issue",
        })
    else:
        for rule_index, supplement_rule in enumerate(RISK_PAYLOAD_SUPPLEMENT_RULES):
            answer, risk_types, actions = apply_payload_supplement_rule(
                supplement_rule,
                payload,
                question,
                answer,
                risk_types,
                actions,
                rule_index=rule_index,
            )

    is_compliant_permission_case = (
        all(term in question for term in ["明确告知", "单独同意"])
        and any(term in question for term in ["关闭", "拒绝", "撤回"])
        and not any(term in question for term in ["未告知", "未取得", "未经", "超范围", "泄露", "出售"])
    )
    if is_compliant_permission_case:
        if payload.get("risk_level") is None:
            payload["risk_level"] = "low"
        if payload.get("confidence_score") is None:
            payload["confidence_score"] = 0.85
        actions = append_unique_text(actions, "保持现有合规措施")
        payload_contribution_trace(payload)["compliant_permission_rule"] = True
        if not answer or not all(term in answer for term in ["告知", "同意", "合法", "必要"]):
            payload["answer"] = (
                f"{answer} 该场景已明确告知处理目的和信息种类，并取得单独同意，且用户可以关闭或撤回定位权限；"
                "在用途限于导航服务、收集范围符合必要原则的前提下，整体属于低风险合规情形，应保持现有告知、同意和权限管理措施。"
            ).strip()
            answer = payload["answer"]

    if is_trademark_invalid_or_cancellation_medium_case(question, payload):
        before_risk_level = payload.get("risk_level")
        set_min_risk_level(payload, "medium")
        capped = cap_risk_level(payload, "medium")
        set_min_confidence(payload, 0.85)
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "trademark_invalid_or_cancellation_medium_cap",
            "risk_level_changed": payload.get("risk_level") != before_risk_level,
            "risk_level_capped": capped,
        })

    if is_property_common_area_medium_case(question, payload):
        before_risk_level = payload.get("risk_level")
        set_min_risk_level(payload, "medium")
        capped = cap_risk_level(payload, "medium")
        set_min_confidence(payload, 0.85)
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "property_common_area_medium_cap",
            "risk_level_changed": payload.get("risk_level") != before_risk_level,
            "risk_level_capped": capped,
        })

    if is_unfair_competition_confusion_medium_case(question):
        before_risk_level = payload.get("risk_level")
        set_min_risk_level(payload, "medium")
        capped = cap_risk_level(payload, "medium")
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "unfair_competition_confusion_medium_cap",
            "risk_level_changed": payload.get("risk_level") != before_risk_level,
            "risk_level_capped": capped,
        })

    if "未弥补亏损" in question and "分配利润" in question:
        set_min_risk_level(payload, "high")
        set_min_confidence(payload, 0.85)
        if "弥补亏损" not in answer or "违法" not in answer:
            payload["answer"] = (
                f"{answer} 公司在未弥补亏损的情况下分配利润，属于违反利润分配顺序的违法高风险情形，应先弥补亏损并按法定规则处理后再进行利润分配。"
            ).strip()
            answer = payload["answer"]
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "illegal_dividend_loss_coverage_terms",
            "risk_level_changed": True,
        })

    if is_vat_mixed_sales_rate_accounting_medium_case(question, payload):
        before_risk_level = payload.get("risk_level")
        set_min_risk_level(payload, "medium")
        capped = cap_risk_level(payload, "medium")
        set_min_confidence(payload, 0.85)
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "vat_mixed_sales_rate_accounting_medium_cap",
            "risk_level_changed": payload.get("risk_level") != before_risk_level,
            "risk_level_capped": capped,
        })

    if "股权" in question and "转让" in question and "未通知" in question:
        before_risk_level = payload.get("risk_level")
        set_min_risk_level(payload, "medium")
        capped = False
        if is_share_transfer_notice_medium_case(question, payload):
            capped = cap_risk_level(payload, "medium")
        set_min_confidence(payload, 0.85)
        payload_contribution_trace(payload)["risk_supplement_rules"].append({
            "runtime_calibration": "share_transfer_notice_minimum_risk",
            "risk_level_changed": payload.get("risk_level") != before_risk_level,
            "risk_level_capped": capped,
        })

    payload["risk_types"] = risk_types
    payload["recommended_actions"] = actions
    return payload
