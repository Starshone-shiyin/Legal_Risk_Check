"""文档分类与效力层级推断。

该模块只做轻量、可解释的规则推断。正式入库时仍建议通过 CLI/API 显式传入元数据，
规则推断作为兜底，避免不同类型文档被统一标成“法律”。
"""

from __future__ import annotations

import re
from dataclasses import dataclass


BROAD_DOCUMENT_TYPES = {
    "法律法规",
    "标准",
    "专利",
    "案例",
    "政策文件",
    "合同",
    "报告",
    "其他",
}

LEGAL_LEVELS = {
    "法律",
    "行政法规",
    "地方性法规",
    "自治条例和单行条例",
    "部门规章",
    "地方政府规章",
    "司法解释",
    "规范性文件",
}

STANDARD_LEVELS = {
    "国家标准",
    "行业标准",
    "地方标准",
    "团体标准",
    "企业标准",
    "国际标准",
}

STANDARD_TYPES = {
    "强制性国家标准",
    "推荐性国家标准",
    "国家标准化指导性技术文件",
    "推荐性行业标准",
    "强制性行业标准",
    "地方标准",
    "团体标准",
    "企业标准",
    "国际标准",
}

CASE_TYPES = {
    "指导性案例",
    "典型案例",
    "公报案例",
    "裁判文书",
    "判例",
    "行政处罚决定",
}

PATENT_TYPES = {
    "发明专利",
    "实用新型专利",
    "外观设计专利",
    "专利申请",
}

AUTHORITY_LEVELS = {
    "国家级",
    "地方级",
    "行业级",
    "团体级",
    "企业级",
    "国际",
    "未知",
}

NATIONAL_LEGAL_AUTHORITIES = [
    "全国人民代表大会",
    "全国人民代表大会常务委员会",
    "国家互联网信息办公室",
    "最高人民法院",
    "最高人民检察院",
    "国务院",
]

LOCAL_HINTS = [
    "省",
    "自治区",
    "直辖市",
    "设区的市",
    "自治州",
    "人民政府令",
    "人大常委会公告",
]

INDUSTRY_STANDARD_PREFIXES = (
    "JR/T",
    "YD/T",
    "GA/T",
    "SJ/T",
    "NB/T",
    "RB/T",
    "YY/T",
    "HJ/T",
    "DL/T",
)


@dataclass
class Classification:
    document_type: str = "法律法规"
    law_level: str = "法律"
    authority_level: str = "国家级"
    jurisdiction: str = "全国"
    issuing_authority: str = ""
    legal_effect: str = ""
    standard_type: str = ""
    case_type: str = ""
    patent_type: str = ""


def first_present(text: str, candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in text:
            return candidate
    return ""


def detect_standard_type(text: str) -> tuple[str, str, str, str]:
    """返回 law_level, standard_type, authority_level, jurisdiction。"""
    compact = re.sub(r"\s+", "", text.upper())
    if re.search(r"\bGB/Z\s*\d+", text, flags=re.IGNORECASE) or "GB/Z" in compact:
        return "国家标准", "国家标准化指导性技术文件", "国家级", "全国"
    if re.search(r"\bGB/T\s*\d+", text, flags=re.IGNORECASE) or "GB/T" in compact:
        return "国家标准", "推荐性国家标准", "国家级", "全国"
    if re.search(r"\bGB\s*\d+", text, flags=re.IGNORECASE) or re.search(r"(^|[^A-Z])GB\d+", compact):
        return "国家标准", "强制性国家标准", "国家级", "全国"
    if any(prefix.replace("/", "") in compact or prefix in text.upper() for prefix in INDUSTRY_STANDARD_PREFIXES):
        return "行业标准", "推荐性行业标准", "行业级", "全国"
    if re.search(r"\bDB\d{2}/T\s*\d+", text, flags=re.IGNORECASE):
        return "地方标准", "地方标准", "地方级", "地方"
    if re.search(r"\bT/[A-Z0-9]+\s*\d+", text, flags=re.IGNORECASE):
        return "团体标准", "团体标准", "团体级", "全国"
    if re.search(r"\bQ/[A-Z0-9]+\s*\d+", text, flags=re.IGNORECASE):
        return "企业标准", "企业标准", "企业级", "企业"
    return "标准", "", "未知", ""


def has_standard_identifier(text: str) -> bool:
    compact = re.sub(r"\s+", "", text.upper())
    return bool(
        re.search(r"\b(?:GB/T|GB/Z|GB|JR/T|YD/T|GA/T|SJ/T|NB/T|RB/T|YY/T|HJ/T|DL/T)\s*\d+", text, flags=re.IGNORECASE)
        or re.search(r"\bDB\d{2}/T\s*\d+", text, flags=re.IGNORECASE)
        or re.search(r"\bT/[A-Z0-9]+\s*\d+", text, flags=re.IGNORECASE)
        or re.search(r"\bQ/[A-Z0-9]+\s*\d+", text, flags=re.IGNORECASE)
        or any(prefix.replace("/", "") in compact for prefix in INDUSTRY_STANDARD_PREFIXES)
    )


def looks_like_legal_norm(source_name: str, text: str) -> bool:
    return (
        source_name.startswith("中华人民共和国")
        or source_name.endswith(("法", "条例", "办法", "规定", "规则", "决定", "解释"))
        or "主席令" in text
        or "国务院令" in text
        or "国家互联网信息办公室令" in text
        or any(authority in text for authority in NATIONAL_LEGAL_AUTHORITIES)
    )


def infer_document_classification(
    source_name: str,
    text: str = "",
    *,
    law_level: str | None = None,
    document_type: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
) -> Classification:
    """根据文件名和正文推断分类；显式参数优先。"""
    haystack = f"{source_name}\n{text[:5000]}"
    compact = re.sub(r"\s+", "", haystack)
    inferred = Classification()

    if any(token in haystack for token in ["专利号", "申请号", "发明人", "权利要求书", "说明书摘要"]):
        inferred.document_type = "专利"
        inferred.law_level = "专利"
        inferred.authority_level = "国家级"
        inferred.jurisdiction = "全国"
        if "实用新型" in haystack:
            inferred.patent_type = "实用新型专利"
        elif "外观设计" in haystack:
            inferred.patent_type = "外观设计专利"
        elif "发明" in haystack:
            inferred.patent_type = "发明专利"
        else:
            inferred.patent_type = "专利申请" if "申请" in haystack else ""

    elif any(token in haystack for token in ["指导性案例", "典型案例", "公报案例", "判决书", "裁定书", "行政处罚决定书"]):
        inferred.document_type = "案例"
        inferred.authority_level = "国家级" if any(token in haystack for token in ["最高人民法院", "最高人民检察院"]) else "未知"
        inferred.jurisdiction = "全国" if inferred.authority_level == "国家级" else ""
        if "指导性案例" in haystack:
            inferred.case_type = "指导性案例"
        elif "典型案例" in haystack:
            inferred.case_type = "典型案例"
        elif "公报案例" in haystack:
            inferred.case_type = "公报案例"
        elif "行政处罚决定书" in haystack:
            inferred.case_type = "行政处罚决定"
        elif any(token in haystack for token in ["判决书", "裁定书"]):
            inferred.case_type = "裁判文书"
        else:
            inferred.case_type = "判例"
        inferred.law_level = inferred.case_type

    elif looks_like_legal_norm(source_name, haystack) and not has_standard_identifier(source_name):
        inferred.document_type = "法律法规"
        inferred.issuing_authority = first_present(haystack, NATIONAL_LEGAL_AUTHORITIES)
        if "全国人民代表大会" in haystack or source_name.startswith("中华人民共和国"):
            inferred.law_level = "法律"
            inferred.authority_level = "国家级"
            inferred.jurisdiction = "全国"
        elif source_name.endswith(("办法", "规定", "规则")) and "国务院令" not in haystack:
            inferred.law_level = "部门规章"
            inferred.authority_level = "国家级"
            inferred.jurisdiction = "全国"
        elif "国务院令" in haystack or ("条例" in source_name and "国务院" in haystack):
            inferred.law_level = "行政法规"
            inferred.authority_level = "国家级"
            inferred.jurisdiction = "全国"
        elif "司法解释" in haystack or any(authority in haystack for authority in ["最高人民法院", "最高人民检察院"]):
            inferred.law_level = "司法解释"
            inferred.authority_level = "国家级"
            inferred.jurisdiction = "全国"
        elif any(hint in haystack for hint in LOCAL_HINTS):
            inferred.law_level = "地方性法规" if "人大" in compact else "地方政府规章"
            inferred.authority_level = "地方级"
            inferred.jurisdiction = "地方"
        elif "部门规章" in haystack:
            inferred.law_level = "部门规章"
            inferred.authority_level = "国家级"
            inferred.jurisdiction = "全国"

    elif has_standard_identifier(haystack) or source_name.endswith("标准"):
        inferred.document_type = "标准"
        (
            inferred.law_level,
            inferred.standard_type,
            inferred.authority_level,
            inferred.jurisdiction,
        ) = detect_standard_type(haystack)

    else:
        inferred.document_type = "其他"
        inferred.law_level = "其他"
        inferred.authority_level = "未知"
        inferred.jurisdiction = ""

    if issuing_authority:
        inferred.issuing_authority = issuing_authority
    elif not inferred.issuing_authority:
        inferred.issuing_authority = first_present(haystack, NATIONAL_LEGAL_AUTHORITIES)

    inferred.document_type = document_type or inferred.document_type
    inferred.law_level = law_level or inferred.law_level
    inferred.authority_level = authority_level or inferred.authority_level
    inferred.jurisdiction = jurisdiction or inferred.jurisdiction
    inferred.legal_effect = legal_effect or inferred.legal_effect
    inferred.standard_type = standard_type or inferred.standard_type
    inferred.case_type = case_type or inferred.case_type
    inferred.patent_type = patent_type or inferred.patent_type
    return inferred
