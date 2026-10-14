"""Domain router: classify a legal question into one of seven domains.

Deterministic keyword-based classification. Fast, auditable, and maintainable
by non-engineers via config/rag_anchor_rules.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.rag.legal_concepts import get_concept_domain


DOMAIN_LABELS = {
    "数据合规": "数据合规",
    "公司治理": "公司治理",
    "市场秩序": "市场秩序",
    "知识产权": "知识产权",
    "财税": "财税",
    "民商事": "民商事",
    "安全合规": "安全合规",
}

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "数据合规": [
        "个人信息", "数据", "隐私", "同意", "告知", "敏感信息", "跨境", "出境",
        "数据安全", "网络安全", "标准合同", "安全评估", "网信办", "个人信息保护法",
        "数据安全法", "网络安全法", "个保法", "APP", "定位", "人脸", "生物识别",
        "行踪轨迹", "算法", "自动化决策", "儿童信息", "用户画像", "去标识化",
    ],
    "公司治理": [
        "公司", "股东", "董事", "监事", "高管", "出资", "股权", "章程",
        "注册资本", "分红", "利润分配", "关联交易", "法人人格", "有限责任",
        "股份有限", "公司法", "认缴", "知情权", "减资", "股权转让",
    ],
    "市场秩序": [
        "垄断", "反垄断", "经营者集中", "市场支配", "不正当竞争", "虚假宣传",
        "商业秘密", "混淆", "商业贿赂", "诋毁", "固定价格", "二选一",
        "排他", "并购", "统一定价", "垄断协议", "统一提高", "统一价格",
        "联合涨价", "价格联盟", "串通投标", "滥用行政权力", "限制竞争",
    ],
    "知识产权": [
        "商标", "专利", "知识产权", "著作权", "版权", "注册商标", "侵权产品",
        "专利法", "商标法", "发明", "实用新型", "外观设计", "职务发明",
        "专利申请", "商标注册", "驰名商标", "假冒", "字样",
    ],
    "财税": [
        "税", "增值税", "纳税", "发票", "抵扣", "进项", "销项", "税率",
        "征收率", "出口退税", "所得税", "消费税", "个税", "虚开",
        "税务", "申报纳税", "缴税", "税款", "征税",
    ],
    "民商事": [
        "合同", "侵权", "赔偿", "违约", "格式条款", "民事", "物权",
        "业主", "物业", "婚姻", "继承", "人格权", "债权", "担保",
        "自动续费", "产品责任", "消费者", "退款", "退货", "派遣",
    ],
    "安全合规": [
        "国家秘密", "保密", "定密", "密级", "涉密", "保密法",
        "泄露国家秘密", "保密工作", "保密制度",
    ],
}

DOMAIN_FALLBACK_CHAIN = [
    "数据合规",
    "民商事",
    "公司治理",
    "市场秩序",
    "知识产权",
    "财税",
    "安全合规",
]


@dataclass
class RoutingResult:
    domain: str
    category: str
    confidence: float


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    rules_path = Path(__file__).parent.parent.parent / "config" / "rag_anchor_rules.json"
    with open(rules_path, encoding="utf-8") as f:
        return json.load(f)


def route_question(question: str) -> RoutingResult:
    """Classify a legal question into a domain.

    Returns RoutingResult with domain, category (same value), and confidence.
    Confidence is a heuristic score based on keyword match density.
    """
    concept_domain = get_concept_domain(question)
    if concept_domain in DOMAIN_LABELS:
        return RoutingResult(
            domain=concept_domain,
            category=concept_domain,
            confidence=0.95,
        )

    scores: dict[str, float] = {}
    question_lower = question

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in question_lower:
                # Longer keyword matches get higher weight
                score += len(kw) * 0.5
        if score > 0:
            scores[domain] = score

    if not scores:
        return RoutingResult(
            domain="数据合规",
            category="数据合规",
            confidence=0.0,
        )

    # Normalize to [0, 1]
    max_possible = max(scores.values()) if scores else 1.0
    best_domain = max(scores, key=scores.get)
    confidence = min(1.0, scores[best_domain] / max(8.0, max_possible))

    return RoutingResult(
        domain=best_domain,
        category=best_domain,
        confidence=round(confidence, 2),
    )


def get_domain_laws(domain: str) -> list[str]:
    """Return the list of law names for a given domain."""
    rules = _load_rules()
    domain_rules = rules.get("domains", {}).get(domain, {})
    return domain_rules.get("laws", [])


def get_category_supplements(domain: str) -> dict[str, list[int]]:
    """Return category supplement articles for a domain.

    Returns a dict mapping law_name -> list of article numbers.
    """
    rules = _load_rules()
    domain_rules = rules.get("domains", {}).get(domain, {})
    return domain_rules.get("category_supplements", {})


def get_scene_anchors(domain: str) -> list[dict]:
    """Return scene anchor rules for a domain."""
    rules = _load_rules()
    domain_rules = rules.get("domains", {}).get(domain, {})
    return domain_rules.get("scene_anchors", [])
