"""文档切片 + 入库（支持多文件，source 自动取自文件名）"""
import hashlib
import logging
import re
from pathlib import Path

from langchain_core.documents import Document

logger = logging.getLogger(__name__)
from src.core.vectorstore import get_vectorstore
from src.rag.taxonomy import infer_document_classification


ARTICLE_PATTERN = re.compile(r"^第([一二三四五六七八九十百千万零〇\d]+)条")
HEADING_PATTERN = re.compile(r"^第([一二三四五六七八九十百千万零〇\d]+)(章|节)\s*(.*)$")
LEGAL_APPENDIX_PATTERN = re.compile(r"^(附表[一二三四五六七八九十\d]+)[：:]?\s*(.*)$")
ITEM_PATTERN = re.compile(r"^（([一二三四五六七八九十百千万零〇\d]+)）")
LEADER_PAGE_PATTERN = re.compile(r"\s*[.．。·…\-—_]{2,}\s*\d+\s*$")
PAGE_NUMBER_PATTERN = re.compile(r"^\d+$")
MARKDOWN_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STANDARD_SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+?)\s*$")
STANDARD_APPENDIX_PATTERN = re.compile(r"^(附录[A-Z])(?:（(.+?)附录）)?\s*(.*)$")
STANDARD_ITEM_PATTERN = re.compile(r"^([a-zA-Z]|[0-9]+)[）)]")
STANDARD_METADATA_LINE_PATTERN = re.compile(r"^(标准号|发布日期|实施日期|文档类型|来源)[:：]")
STANDARD_MAX_CHUNK_CHARS = 1600
STANDARD_CHUNK_OVERLAP_CHARS = 180
CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
CHINESE_UNITS = {
    "十": 10,
    "百": 100,
    "千": 1000,
    "万": 10000,
}


def chinese_number_to_int(text: str) -> int | None:
    """将中文条号数字转换为整数，支持常见法律条文编号。"""
    if text.isdigit():
        return int(text)

    total = 0
    section = 0
    number = 0
    for char in text:
        if char in CHINESE_DIGITS:
            number = CHINESE_DIGITS[char]
        elif char in CHINESE_UNITS:
            unit = CHINESE_UNITS[char]
            if unit == 10000:
                section = (section + number) * unit
                total += section
                section = 0
            else:
                section += (number or 1) * unit
            number = 0
        else:
            return None

    return total + section + number


def int_to_chinese_number(value: int) -> str:
    """将 1-9999 的整数转为常见中文编号。"""
    if value <= 0:
        return str(value)
    if value < 10:
        digits = "零一二三四五六七八九"
        return digits[value]
    if value < 20:
        return "十" + (int_to_chinese_number(value % 10) if value % 10 else "")
    if value < 100:
        tens, ones = divmod(value, 10)
        return int_to_chinese_number(tens) + "十" + (int_to_chinese_number(ones) if ones else "")
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        return int_to_chinese_number(hundreds) + "百" + (int_to_chinese_number(rest) if rest else "")

    thousands, rest = divmod(value, 1000)
    return int_to_chinese_number(thousands) + "千" + (int_to_chinese_number(rest) if rest else "")


def extract_article_metadata(text: str) -> tuple[str, int | None]:
    """提取条文显示编号和整数编号。"""
    match = ARTICLE_PATTERN.match(text)
    if not match:
        return "", None

    article = f"第{match.group(1)}条"
    article_no = chinese_number_to_int(match.group(1))
    return article, article_no


def extract_item_metadata(text: str) -> tuple[str, int | None]:
    """提取（一）（二）等项编号。"""
    match = ITEM_PATTERN.match(text)
    if not match:
        return "", None

    item_label = f"（{match.group(1)}）"
    item_no = chinese_number_to_int(match.group(1))
    return item_label, item_no


def build_citation(
    law_name: str,
    article: str,
    paragraph_no: int | None = None,
    item_label: str = "",
) -> str:
    """构造标准法律来源标签。"""
    citation = f"[《{law_name}》{article}]"
    if paragraph_no:
        citation = citation[:-1] + f"第{int_to_chinese_number(paragraph_no)}款]"
    if item_label:
        citation = citation[:-1] + f"{item_label}项]"
    return citation


def build_standard_citation(source_name: str, section_no: str = "", section_title: str = "") -> str:
    """构造标准/指南类文件的来源标签。"""
    location = section_no
    if section_title:
        location = f"{location} {section_title}".strip()
    if location:
        return f"[《{source_name}》{location}]"
    return f"[《{source_name}》]"


def build_appendix_citation(law_name: str, appendix: str, title: str = "") -> str:
    """构造法律附表来源标签，避免将表格误归入末条条文。"""
    location = f"{appendix} {title}".strip()
    return f"[《{law_name}》{location}]"


def clean_legal_line(line: str) -> str:
    """清洗法律文本行，去除目录点线页码和多余空白。"""
    cleaned = line.strip().replace("\u3000", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = LEADER_PAGE_PATTERN.sub("", cleaned).strip()
    return cleaned


def strip_table_of_contents(text: str) -> str:
    """跳过常见法律文本中的目录区。"""
    lines = text.splitlines()
    output = []
    in_toc = False
    saw_toc_entry = False
    blank_count = 0

    for line in lines:
        cleaned = clean_legal_line(line)
        compact = re.sub(r"\s+", "", cleaned)

        if not in_toc and compact == "目录":
            in_toc = True
            saw_toc_entry = False
            blank_count = 0
            continue

        if in_toc:
            if cleaned:
                saw_toc_entry = True
                blank_count = 0
                continue

            if saw_toc_entry:
                blank_count += 1
                if blank_count >= 2:
                    in_toc = False
                    saw_toc_entry = False
                    blank_count = 0
                continue

        output.append(line)

    return text if in_toc else "\n".join(output)


def split_legal_blocks(text: str) -> list[str]:
    """Split legal text by blank lines and structural headings.

    Official texts are not consistent about blank lines between adjacent
    articles.  A new article, chapter/section, or attached table must start a
    fresh block even in compact source files.
    """
    blocks = []
    current = []

    for raw_line in text.splitlines():
        line = clean_legal_line(raw_line)
        if PAGE_NUMBER_PATTERN.match(line):
            continue

        if not line:
            if current:
                blocks.append("".join(current).strip())
                current = []
            continue

        is_structural_boundary = bool(
            ARTICLE_PATTERN.match(line)
            or HEADING_PATTERN.match(line)
            or LEGAL_APPENDIX_PATTERN.match(line)
        )
        if current and is_structural_boundary:
            blocks.append("".join(current).strip())
            current = []

        current.append(line)

    if current:
        blocks.append("".join(current).strip())

    return [block for block in blocks if block]


def clean_standard_line(line: str) -> str:
    """清洗标准类文档行，保留 Markdown 标题结构。"""
    cleaned = line.strip().replace("\u3000", " ")
    cleaned = LEADER_PAGE_PATTERN.sub("", cleaned).strip()
    if PAGE_NUMBER_PATTERN.match(cleaned):
        return ""
    return cleaned


def parse_standard_heading(line: str) -> dict | None:
    """识别标准/指南类文档的 Markdown 或编号标题。"""
    stripped = line.strip()
    if not stripped:
        return None

    markdown_match = MARKDOWN_HEADING_PATTERN.match(stripped)
    if markdown_match:
        markdown_level = len(markdown_match.group(1))
        title = markdown_match.group(2).strip()
    else:
        markdown_level = 1
        title = stripped

    if STANDARD_METADATA_LINE_PATTERN.match(title):
        return None

    appendix_match = STANDARD_APPENDIX_PATTERN.match(title)
    if appendix_match:
        appendix_no, appendix_type, appendix_title = appendix_match.groups()
        appendix_title = appendix_title.strip()
        heading = appendix_no
        if appendix_type:
            heading += f"（{appendix_type}附录）"
        if appendix_title:
            heading += f" {appendix_title}"
        return {
            "heading": heading,
            "heading_level": "appendix",
            "section_no": appendix_no,
            "section_title": appendix_title,
            "section_level": 1,
            "appendix": appendix_no,
        }

    section_match = STANDARD_SECTION_PATTERN.match(title)
    if section_match:
        section_no, section_title = section_match.groups()
        section_level = section_no.count(".") + 1
        return {
            "heading": f"{section_no} {section_title.strip()}",
            "heading_level": "section",
            "section_no": section_no,
            "section_title": section_title.strip(),
            "section_level": section_level,
            "appendix": "",
        }

    if title in {"前言", "引言", "参考文献"}:
        return {
            "heading": title,
            "heading_level": "front_matter" if title in {"前言", "引言"} else "reference",
            "section_no": "",
            "section_title": title,
            "section_level": 0,
            "appendix": "",
        }

    if markdown_match:
        return {
            "heading": title,
            "heading_level": "heading",
            "section_no": "",
            "section_title": title,
            "section_level": markdown_level,
            "appendix": "",
        }

    return None


def extract_standard_title(text: str, fallback: str) -> str:
    """从标准类清洗稿中提取展示标题，失败时回退到文件名。"""
    for raw_line in text.splitlines():
        line = clean_standard_line(raw_line)
        markdown_match = MARKDOWN_HEADING_PATTERN.match(line)
        if not markdown_match:
            continue
        title = markdown_match.group(2).strip()
        if title in {"前言", "引言", "参考文献"}:
            continue
        if STANDARD_SECTION_PATTERN.match(title) or STANDARD_APPENDIX_PATTERN.match(title):
            continue
        if STANDARD_METADATA_LINE_PATTERN.match(title):
            continue
        return title
    return fallback


def build_standard_chunks(parts: list[str], max_chars: int = STANDARD_MAX_CHUNK_CHARS) -> list[str]:
    """按段落组合标准正文块；超长章节使用轻量滑动窗口。"""
    chunks = []
    current = []
    current_len = 0

    for part in parts:
        part = part.strip()
        if not part:
            continue
        part_len = len(part)
        if current and current_len + part_len > max_chars:
            chunk = "\n\n".join(current).strip()
            chunks.append(chunk)
            overlap = chunk[-STANDARD_CHUNK_OVERLAP_CHARS:] if len(chunk) > STANDARD_CHUNK_OVERLAP_CHARS else chunk
            current = [overlap, part] if overlap else [part]
            current_len = sum(len(item) for item in current)
        else:
            current.append(part)
            current_len += part_len

    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks


def build_standard_section_documents(
    section_metadata: dict,
    section_parts: list[str],
    base_metadata: dict,
) -> list[Document]:
    """构造标准/指南类章节标题块和正文块。"""
    if not section_metadata:
        return []

    docs = []
    source_name = base_metadata.get("source", "")
    display_name = base_metadata.get("law_name") or source_name
    heading = section_metadata["heading"]
    section_no = section_metadata.get("section_no", "")
    section_title = section_metadata.get("section_title", "")
    section_level = section_metadata.get("section_level")
    appendix = section_metadata.get("appendix", "")
    citation = build_standard_citation(display_name, section_no, section_title)
    parent_section_id = f"{source_name}::{section_no or heading}"
    section_text = "\n\n".join(part for part in section_parts if part).strip()
    full_section_content = f"{heading}\n\n{section_text}".strip()

    common_metadata = {
        **base_metadata,
        "chapter": section_metadata.get("chapter", ""),
        "section": heading,
        "heading_level": section_metadata.get("heading_level", ""),
        "article": section_no,
        "article_no": None,
        "section_no": section_no,
        "section_title": section_title,
        "section_level": section_level,
        "appendix": appendix,
        "parent_article_id": parent_section_id,
        "paragraph_no": None,
        "item_no": None,
        "item_label": "",
        "citation": citation,
    }

    docs.append(Document(
        page_content=heading,
        metadata={
            **common_metadata,
            "type": "chapter",
            "block_type": "heading",
            "parent_content": full_section_content[:STANDARD_MAX_CHUNK_CHARS],
        },
    ))

    if not section_text:
        return docs

    chunks = build_standard_chunks(section_parts)
    for index, chunk in enumerate(chunks, start=1):
        chunk_content = f"{heading}\n\n{chunk}".strip()
        docs.append(Document(
            page_content=chunk_content,
            metadata={
                **common_metadata,
                "type": "article",
                "block_type": "standard_section",
                "paragraph_no": index,
                "chunk_index": index,
                "chunk_count": len(chunks),
                "parent_content": chunk_content,
            },
        ))

    return docs


def build_standard_documents(text: str, base_metadata: dict) -> list[Document]:
    """解析国标/行标/指南等编号章节型文件。"""
    docs = []
    current_heading = None
    current_parts = []
    current_paragraph = []
    current_main_chapter = ""

    def flush_paragraph():
        nonlocal current_paragraph
        if current_paragraph:
            current_parts.append("\n".join(current_paragraph).strip())
            current_paragraph = []

    def flush_section():
        nonlocal current_heading, current_parts
        flush_paragraph()
        if current_heading:
            docs.extend(build_standard_section_documents(current_heading, current_parts, base_metadata))
        current_heading = None
        current_parts = []

    for raw_line in text.splitlines():
        line = clean_standard_line(raw_line)
        heading = parse_standard_heading(line)
        if heading:
            flush_section()
            if heading["heading_level"] == "heading" and not docs:
                # 清洗稿首行通常是文档标题，基础元数据已保存 source/law_name，避免重复入库。
                current_heading = None
                continue
            if heading.get("section_level") == 1 and heading.get("section_no"):
                current_main_chapter = heading["heading"]
            heading["chapter"] = current_main_chapter if heading.get("section_level", 0) > 1 else heading["heading"]
            current_heading = heading
            continue

        if not line:
            flush_paragraph()
            continue

        if current_heading is None:
            if STANDARD_METADATA_LINE_PATTERN.match(line):
                continue
            current_heading = {
                "heading": "正文说明",
                "heading_level": "text",
                "section_no": "",
                "section_title": "正文说明",
                "section_level": 0,
                "appendix": "",
                "chapter": "",
            }

        if STANDARD_ITEM_PATTERN.match(line) and current_paragraph:
            flush_paragraph()

        current_paragraph.append(line)

    flush_section()
    return docs


def extract_heading_metadata(text: str) -> tuple[str, str] | None:
    """识别章、节标题，返回标题层级和规范标题。"""
    match = HEADING_PATTERN.match(text)
    if not match:
        return None

    number, unit, title = match.groups()
    heading = f"第{number}{unit}"
    if title:
        heading = f"{heading} {title.strip()}"

    heading_level = "chapter" if unit == "章" else "section"
    return heading_level, heading


def build_base_metadata(
    path: Path,
    source_name: str,
    category: str,
    version: str,
    text: str = "",
    law_level: str | None = None,
    document_type: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
) -> dict:
    """构造所有法律文本切片共享的基础元数据。"""
    classification = infer_document_classification(
        source_name,
        text,
        law_level=law_level,
        document_type=document_type,
        authority_level=authority_level,
        jurisdiction=jurisdiction,
        issuing_authority=issuing_authority,
        legal_effect=legal_effect,
        standard_type=standard_type,
        case_type=case_type,
        patent_type=patent_type,
    )
    return {
        "source": source_name,
        "law_name": source_name,
        "file_path": str(path),
        "document_type": classification.document_type,
        "law_level": classification.law_level,
        "authority_level": classification.authority_level,
        "jurisdiction": classification.jurisdiction,
        "issuing_authority": classification.issuing_authority,
        "legal_effect": classification.legal_effect,
        "standard_type": classification.standard_type,
        "case_type": classification.case_type,
        "patent_type": classification.patent_type,
        "category": category,
        "version": version,
    }


def assign_stable_chunk_ids(docs: list[Document]) -> list[Document]:
    """Attach deterministic chunk_id and qdrant_point_id for dense/sparse alignment."""
    for index, doc in enumerate(docs, start=1):
        metadata = doc.metadata
        identity_parts = [
            metadata.get("source", ""),
            metadata.get("citation", ""),
            metadata.get("block_type", ""),
            metadata.get("article_no", ""),
            metadata.get("section_no", ""),
            metadata.get("paragraph_no", ""),
            metadata.get("item_no", ""),
            metadata.get("chunk_index", ""),
            index,
            doc.page_content,
        ]
        raw_identity = "\u241f".join(str(part) for part in identity_parts)
        digest = hashlib.sha256(raw_identity.encode("utf-8")).hexdigest()
        metadata["chunk_id"] = metadata.get("chunk_id") or digest[:24]
        metadata["qdrant_point_id"] = int(digest[:15], 16)
    return docs


def build_article_documents(
    article_parts: list[str],
    article_metadata: dict,
) -> list[Document]:
    """构造父条文块和款/项子块。"""
    if not article_parts:
        return []

    article = article_metadata.get("article", "")
    article_no = article_metadata.get("article_no")
    law_name = article_metadata.get("law_name", article_metadata.get("source", ""))
    parent_article_id = f"{law_name}::{article_no or article}"
    parent_content = "\n\n".join(article_parts)

    common_metadata = {
        **article_metadata,
        "parent_article_id": parent_article_id,
        "paragraph_no": None,
        "item_no": None,
        "item_label": "",
        "parent_content": parent_content,
        "citation": build_citation(law_name, article),
    }

    docs = [
        Document(
            page_content=parent_content,
            metadata={
                **common_metadata,
                "block_type": "article",
                "chunk_index": 1,
                "chunk_count": 1,
            },
        )
    ]

    paragraph_no = 0
    child_chunk_count = len(article_parts)
    child_chunk_index = 0
    for part in article_parts:
        child_chunk_index += 1
        item_label, item_no = extract_item_metadata(part)
        if item_label:
            if paragraph_no == 0:
                paragraph_no = 1
            docs.append(Document(
                page_content=part,
                metadata={
                    **common_metadata,
                    "block_type": "item",
                    "paragraph_no": paragraph_no,
                    "item_no": item_no,
                    "item_label": item_label,
                    "chunk_index": child_chunk_index,
                    "chunk_count": child_chunk_count,
                    "citation": build_citation(law_name, article, paragraph_no, item_label),
                },
            ))
            continue

        paragraph_no += 1
        docs.append(Document(
            page_content=part,
            metadata={
                **common_metadata,
                "block_type": "paragraph",
                "paragraph_no": paragraph_no,
                "chunk_index": child_chunk_index,
                "chunk_count": child_chunk_count,
                "citation": build_citation(law_name, article, paragraph_no),
            },
        ))

    return docs


def build_legal_appendix_documents(
    appendix_parts: list[str],
    appendix_metadata: dict,
) -> list[Document]:
    """Build independent, citable evidence blocks for a law's attached tables."""
    if not appendix_parts and not appendix_metadata.get("section_title"):
        return []

    law_name = appendix_metadata.get("law_name", appendix_metadata.get("source", ""))
    appendix = appendix_metadata.get("appendix", "")
    title = appendix_metadata.get("section_title", "")
    if not appendix_parts:
        appendix_parts = [title]
    citation = build_appendix_citation(law_name, appendix, title)
    parent_appendix_id = f"{law_name}::{appendix}"
    chunk_count = len(appendix_parts)
    docs: list[Document] = []

    for chunk_index, part in enumerate(appendix_parts, start=1):
        content = f"{appendix} {title}".strip()
        if part != title:
            content = f"{content}\n{part}".strip()
        docs.append(Document(
            page_content=content,
            metadata={
                **appendix_metadata,
                "type": "appendix",
                "block_type": "appendix_table",
                "heading_level": "appendix",
                "article": "",
                "article_no": None,
                "parent_article_id": parent_appendix_id,
                "parent_content": content,
                "paragraph_no": None,
                "item_no": None,
                "item_label": "",
                "citation": citation,
                "chunk_index": chunk_index,
                "chunk_count": chunk_count,
            },
        ))
    return docs


def load_txt(
    file_path: str,
    source_name: str = None,
    law_level: str | None = None,
    category: str = "数据合规",
    version: str = "",
    document_type: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
) -> list[Document]:
    """
    加载纯文本文件，按段落切分。
    
    Args:
        file_path: 文件路径
        source_name: 文档来源名称，若为 None 则从文件名提取（不含扩展名）
        law_level: 细分效力/类型，如法律、行政法规、国家标准、指导性案例；不传则自动推断
        category: 风控分类，如数据合规、供应链、知识产权
        version: 版本年份或生效版本说明，可暂空
        document_type: 粗类，如法律法规、标准、专利、案例；不传则自动推断
        authority_level: 发布/效力层级，如国家级、地方级、行业级
        jurisdiction: 适用地域，如全国、地方、国际
        issuing_authority: 发布机关
        legal_effect: 生效/废止/现行有效等效力状态
        standard_type: 标准细类，如强制性国家标准、推荐性国家标准、国家标准化指导性技术文件
        case_type: 案例细类，如指导性案例、典型案例、裁判文书
        patent_type: 专利细类，如发明专利、实用新型专利、外观设计专利
    
    Returns:
        Document 列表
    """
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")

    # 确定 source 名称
    if source_name is None:
        source_name = path.stem  # 不含扩展名的文件名

    base_metadata = build_base_metadata(
        path,
        source_name,
        category,
        version,
        text=text,
        law_level=law_level,
        document_type=document_type,
        authority_level=authority_level,
        jurisdiction=jurisdiction,
        issuing_authority=issuing_authority,
        legal_effect=legal_effect,
        standard_type=standard_type,
        case_type=case_type,
        patent_type=patent_type,
    )

    if base_metadata.get("document_type") == "标准":
        base_metadata["law_name"] = extract_standard_title(text, source_name)
        return assign_stable_chunk_ids(build_standard_documents(text, base_metadata))

    text = strip_table_of_contents(text)
    blocks = split_legal_blocks(text)
    docs = []
    current_chapter = ""
    current_section = ""
    current_article_parts = []
    current_article_metadata = None
    current_appendix_parts = []
    current_appendix_metadata = None

    def flush_article():
        nonlocal current_article_parts, current_article_metadata
        if not current_article_parts or current_article_metadata is None:
            return
        docs.extend(build_article_documents(current_article_parts, current_article_metadata))
        current_article_parts = []
        current_article_metadata = None

    def flush_appendix():
        nonlocal current_appendix_parts, current_appendix_metadata
        if current_appendix_metadata is None or (
            not current_appendix_parts
            and not current_appendix_metadata.get("section_title")
        ):
            return
        docs.extend(build_legal_appendix_documents(current_appendix_parts, current_appendix_metadata))
        current_appendix_parts = []
        current_appendix_metadata = None

    for block in blocks:
        appendix_match = LEGAL_APPENDIX_PATTERN.match(block)
        if appendix_match:
            flush_article()
            flush_appendix()
            appendix, inline_title = appendix_match.groups()
            current_appendix_parts = []
            current_appendix_metadata = {
                **base_metadata,
                "chapter": current_chapter,
                "section": current_section,
                "section_no": appendix,
                "section_title": inline_title,
                "section_level": 1,
                "appendix": appendix,
            }
            continue

        heading_metadata = extract_heading_metadata(block)
        if heading_metadata:
            flush_article()
            flush_appendix()
            heading_level, heading = heading_metadata
            if heading_level == "chapter":
                current_chapter = heading
                current_section = ""
            else:
                current_section = heading

            docs.append(Document(
                page_content=heading,
                metadata={
                    **base_metadata,
                    "type": "chapter",
                    "heading_level": heading_level,
                    "chapter": current_chapter,
                    "section": current_section,
                    "article": "",
                    "article_no": None,
                },
            ))
            continue

        article, article_no = extract_article_metadata(block)
        if article:
            flush_appendix()
            flush_article()
            current_article_parts = [block]
            current_article_metadata = {
                **base_metadata,
                "type": "article",
                "block_type": "article",
                "chapter": current_chapter,
                "section": current_section,
                "article": article,
                "article_no": article_no,
            }
            continue

        if current_appendix_metadata is not None:
            if not current_appendix_metadata.get("section_title"):
                current_appendix_metadata["section_title"] = block
                current_appendix_parts.append(block)
                continue
            current_appendix_parts.append(block)
            continue

        if current_article_parts:
            current_article_parts.append(block)
        else:
            docs.append(Document(
                page_content=block,
                metadata={
                    **base_metadata,
                    "type": "text",
                    "chapter": current_chapter,
                    "section": current_section,
                    "article": "",
                    "article_no": None,
                },
            ))

    flush_article()
    flush_appendix()

    return assign_stable_chunk_ids(docs)


def ingest(
    file_path: str,
    collection_name: str = "legal_knowledge",
    source_name: str = None,
    law_level: str | None = None,
    category: str = "数据合规",
    version: str = "",
    document_type: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
):
    """
    将文档入库（追加模式）
    
    Args:
        file_path: 文件路径
        collection_name: Qdrant 集合名称
        source_name: 可覆盖的 source 名称，默认从文件名提取
        law_level: 细分效力/类型，如法律、行政法规、国家标准、指导性案例；不传则自动推断
        category: 风控分类，如数据合规、供应链、知识产权
        version: 版本年份或生效版本说明，可暂空
    """
    docs = load_txt(
        file_path,
        source_name=source_name,
        law_level=law_level,
        category=category,
        version=version,
        document_type=document_type,
        authority_level=authority_level,
        jurisdiction=jurisdiction,
        issuing_authority=issuing_authority,
        legal_effect=legal_effect,
        standard_type=standard_type,
        case_type=case_type,
        patent_type=patent_type,
    )
    logger.info(f"加载了 {len(docs)} 个文档片段，来源: {docs[0].metadata['source'] if docs else '未知'}")
    if docs:
        metadata = docs[0].metadata
        logger.info("文档分类: %s", {
            "document_type": metadata.get("document_type"),
            "law_level": metadata.get("law_level"),
            "authority_level": metadata.get("authority_level"),
            "jurisdiction": metadata.get("jurisdiction"),
            "standard_type": metadata.get("standard_type"),
            "case_type": metadata.get("case_type"),
            "patent_type": metadata.get("patent_type"),
        })
    article_docs = [
        doc.metadata.get("article")
        for doc in docs
        if doc.metadata.get("block_type") == "article"
    ]
    if article_docs:
        logger.info("入库条文号: %s", article_docs)

    standard_section_labels = [
        " ".join(
            part for part in [
                doc.metadata.get("section_no", ""),
                doc.metadata.get("section_title", ""),
            ]
            if part
        )
        for doc in docs
        if doc.metadata.get("block_type") == "standard_section"
        and doc.metadata.get("chunk_index") == 1
    ]
    if standard_section_labels:
        logger.info(f"入库标准章节号（{len(standard_section_labels)} 个）: %s", standard_section_labels)
    if not article_docs and not standard_section_labels:
        text_blocks = [
            doc.metadata.get("section") or doc.metadata.get("chapter") or doc.page_content[:30]
            for doc in docs
            if doc.metadata.get("type") == "text"
        ]
        logger.info("入库文本块: %s", text_blocks[:50])

    # v0.4.4: Dense and BM25 sparse share stable point ids; sparse updates the same points.
    from src.rag.bm25_encoder import get_bm25_encoder
    from src.core.vectorstore import get_qdrant_client, ensure_collection_with_sparse
    import qdrant_client.http.models as models

    ensure_collection_with_sparse(collection_name)

    point_ids = [doc.metadata["qdrant_point_id"] for doc in docs]

    vectorstore = get_vectorstore(collection_name)
    vectorstore.add_documents(docs, ids=point_ids)

    bm25 = get_bm25_encoder()
    client = get_qdrant_client()
    sparse_vectors = []
    for doc in docs:
        sparse_indices, sparse_values = bm25.encode(doc.page_content)
        if not sparse_indices:
            continue
        sparse_vectors.append(models.PointVectors(
            id=doc.metadata["qdrant_point_id"],
            vector={"bm25": models.SparseVector(indices=sparse_indices, values=sparse_values)},
        ))

    BATCH = 100
    for start in range(0, len(sparse_vectors), BATCH):
        batch = sparse_vectors[start:start + BATCH]
        if batch:
            client.update_vectors(collection_name=collection_name, points=batch)
    logger.info("已写入 %s (%d dense + %d BM25 sparse)", collection_name, len(docs), len(sparse_vectors))


if __name__ == "__main__":
    # 示例：入库一个文件
    import sys
    if len(sys.argv) > 1:
        ingest(sys.argv[1])
    else:
        # 默认入库原有的个保法文件（保持兼容）
        ingest("src/knowledge/data_compliance/pipl.txt")
