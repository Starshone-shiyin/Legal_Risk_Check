"""清洗 MinerU 输出的 OCR Markdown。

目标：把 PDF OCR 结果清洗成适合 RAG 入库的结构化 Markdown。
默认优化国标/行标等章节编号型文件，也可通过参数处理其他 OCR 文档。
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass, field
from pathlib import Path


SECTION_NO_PATTERN = re.compile(r"^#?\s*(\d+(?:\.\d+)*)\s*$")
HEADING_PATTERN = re.compile(r"^#\s+(.+?)\s*$")
MAIN_SECTION_PATTERN = re.compile(r"^#\s+(\d+(?:\.\d+)*)\s+(.+?)\s*$")
APPENDIX_PATTERN = re.compile(r"^#?\s*(附录[A-Z])（(.+?)附录）\s*(.+?)(?:[·\s]+\d+)?\s*$")
TOC_START_PATTERN = re.compile(r"^#\s*目次\s*$")
BODY_START_PATTERN = re.compile(r"^#\s*前言\s*$")
REFERENCE_HEADING_PATTERN = re.compile(r"^#\s*参考文献(?:\s+\d+)?\s*$")
STANDARD_NO_PATTERN = re.compile(
    r"\b((?:GB/T|GB/Z|GB|JR/T|YD/T|T/[A-Z0-9]+)\s*\d+(?:[—-]\d+)?)\b",
    re.IGNORECASE,
)


@dataclass
class HeaderMetadata:
    title: str
    standard_no: str = ""
    publish_date: str = ""
    implement_date: str = ""
    doc_type: str = "标准类文件"
    source_note: str = "MinerU OCR 清洗稿，入库前建议抽样校对。"
    expected_anchors: list[str] = field(default_factory=list)


def normalize_html_fragments(text: str) -> str:
    """把 MinerU 偶发输出的 HTML 表格展开成可检索的普通文本。"""
    text = html.unescape(text)
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*(?:p|div|tr|table)\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*(?:td|th)\s*>", "；", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("□", "")
    text = text.replace("■", "")
    return text


def normalize_line(line: str) -> str:
    line = line.replace("\u3000", " ").strip()
    line = re.sub(r"\s+", " ", line)
    line = line.replace("$8.1\\sim 8.6$", "8.1~8.6")
    line = line.replace("$48\\mathrm{h}$", "48h")
    line = line.replace("userprofiling", "user profiling")
    line = line.replace("businessfunction", "business function")
    line = re.sub(r"GB/T(?=\d)", "GB/T ", line)
    line = re.sub(r"GB/T\s+", "GB/T ", line)
    line = re.sub(r"[；;]\s*[；;]+", "；", line)
    line = re.sub(r"\s+；", "；", line)
    return line


def strip_cover_and_toc(lines: list[str], title: str) -> list[str]:
    """删除封面和目录，从前言开始保留。"""
    for index, line in enumerate(lines):
        if BODY_START_PATTERN.match(line):
            return lines[index:]

    # 兜底：如果没有前言，从正文标题第二次出现处开始。
    title_seen = 0
    for index, line in enumerate(lines):
        if line == f"# {title}":
            title_seen += 1
            if title_seen >= 2:
                return lines[index:]

    return lines


def merge_split_term_headings(lines: list[str]) -> list[str]:
    """合并 MinerU 常见的 '3.1' + '# 术语名' 分离标题。"""
    merged = []
    index = 0
    while index < len(lines):
        line = lines[index]
        section_match = SECTION_NO_PATTERN.match(line)
        if section_match and index + 2 < len(lines):
            maybe_blank = lines[index + 1]
            next_line = lines[index + 2]
            heading_match = HEADING_PATTERN.match(next_line)
            if maybe_blank == "" and heading_match:
                merged.append(f"# {section_match.group(1)} {heading_match.group(1)}")
                index += 3
                continue
        if section_match and index + 1 < len(lines):
            heading_match = HEADING_PATTERN.match(lines[index + 1])
            if heading_match:
                merged.append(f"# {section_match.group(1)} {heading_match.group(1)}")
                index += 2
                continue
        merged.append(line)
        index += 1
    return merged


def normalize_headings(lines: list[str]) -> list[str]:
    normalized = []
    for line in lines:
        appendix_match = APPENDIX_PATTERN.match(line)
        if appendix_match:
            appendix_no, appendix_type, title = appendix_match.groups()
            normalized.append(f"# {appendix_no}（{appendix_type}附录）{title.strip()}")
            continue

        if REFERENCE_HEADING_PATTERN.match(line):
            normalized.append("# 参考文献")
            continue

        section_match = MAIN_SECTION_PATTERN.match(line)
        if section_match:
            section_no, title = section_match.groups()
            normalized.append(f"# {section_no} {title.strip()}")
            continue

        normalized.append(line)
    return normalized


def remove_noise(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        if TOC_START_PATTERN.match(line):
            continue
        if re.fullmatch(r"[.·…\s]{4,}", line):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if "书书书" in line:
            continue
        cleaned.append(line)
    return cleaned


def collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank
    return collapsed


def infer_header_metadata(text: str, input_path: Path | None = None) -> HeaderMetadata:
    """尽量从 MinerU Markdown 中推断标题和标准号；推断不到时使用文件名。"""
    normalized_lines = [normalize_line(line) for line in text.splitlines()]
    title = ""
    for line in normalized_lines:
        heading_match = HEADING_PATTERN.match(line)
        if not heading_match:
            continue
        candidate = heading_match.group(1).strip()
        if candidate in {"目次", "前言", "引言", "参考文献"}:
            continue
        if MAIN_SECTION_PATTERN.match(line) or candidate.startswith("附录"):
            continue
        if STANDARD_NO_PATTERN.fullmatch(candidate):
            continue
        if re.search(r"[\u4e00-\u9fff]", candidate):
            title = candidate
            break

    if not title and input_path:
        title = input_path.stem
    if not title:
        title = "未命名标准文件"

    standard_match = STANDARD_NO_PATTERN.search(text)
    standard_no = standard_match.group(1).replace("—", "-") if standard_match else ""
    standard_no = re.sub(r"\s+", " ", standard_no).strip()
    return HeaderMetadata(title=title, standard_no=standard_no)


def build_header(metadata: HeaderMetadata) -> list[str]:
    header = [f"# {metadata.title}", ""]
    if metadata.standard_no:
        header.append(f"标准号：{metadata.standard_no}")
    if metadata.publish_date:
        header.append(f"发布日期：{metadata.publish_date}")
    if metadata.implement_date:
        header.append(f"实施日期：{metadata.implement_date}")
    if metadata.doc_type:
        header.append(f"文档类型：{metadata.doc_type}")
    if metadata.source_note:
        header.append(f"来源：{metadata.source_note}")
    header.append("")
    return header


def clean_markdown(text: str, metadata: HeaderMetadata) -> str:
    text = normalize_html_fragments(text)
    lines = [normalize_line(line) for line in text.splitlines()]
    lines = strip_cover_and_toc(lines, metadata.title)
    lines = remove_noise(lines)
    lines = merge_split_term_headings(lines)
    lines = normalize_headings(lines)
    lines = collapse_blank_lines(lines)

    # 如果正文仍以标题开头，避免重复标题。
    if lines and lines[0] == f"# {metadata.title}":
        lines = lines[1:]
        if lines and lines[0] == "":
            lines = lines[1:]

    return "\n".join(build_header(metadata) + lines).strip() + "\n"


def quality_report(text: str, expected_anchors: list[str] | None = None) -> dict:
    nonspace = [char for char in text if not char.isspace()]
    cjk = [char for char in nonspace if "\u4e00" <= char <= "\u9fff"]
    headings = re.findall(r"(?m)^#\s+", text)
    section_headings = re.findall(r"(?m)^#\s+\d+(?:\.\d+)*\s+", text)
    report = {
        "total_chars": len(nonspace),
        "cjk_chars": len(cjk),
        "cjk_ratio": round(len(cjk) / max(len(nonspace), 1), 4),
        "heading_count": len(headings),
        "section_heading_count": len(section_headings),
        "has_toc": "# 目次" in text,
        "html_tag_count": len(re.findall(r"<[^>]+>", text)),
        "checkbox_count": text.count("□") + text.count("■"),
    }
    for anchor in expected_anchors or []:
        report[f"has_anchor:{anchor}"] = anchor in text
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean MinerU Markdown for standard-document RAG ingestion.")
    parser.add_argument("input", type=Path, help="MinerU Markdown 文件")
    parser.add_argument("--output", "-o", type=Path, required=True, help="清洗后 Markdown 输出路径")
    parser.add_argument("--report", type=Path, help="质量报告输出路径")
    parser.add_argument("--title", help="文档标题；不传则从 Markdown 标题或文件名推断")
    parser.add_argument("--standard-no", help="标准号，如 GB/T 35273-2020；不传则尝试从文本推断")
    parser.add_argument("--publish-date", default="", help="发布日期，如 2020-03-06")
    parser.add_argument("--implement-date", default="", help="实施日期，如 2020-10-01")
    parser.add_argument("--doc-type", default="标准类文件", help="文档类型，如 推荐性国家标准、强制性国家标准、行业标准")
    parser.add_argument(
        "--source-note",
        default="MinerU OCR 清洗稿，入库前建议抽样校对。",
        help="来源说明",
    )
    parser.add_argument(
        "--expect-anchor",
        action="append",
        default=[],
        help="期望保留的关键锚点，可重复传入；质量报告会输出 has_anchor:<锚点>",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_text = args.input.read_text(encoding="utf-8")
    inferred = infer_header_metadata(raw_text, args.input)
    metadata = HeaderMetadata(
        title=args.title or inferred.title,
        standard_no=args.standard_no or inferred.standard_no,
        publish_date=args.publish_date,
        implement_date=args.implement_date,
        doc_type=args.doc_type,
        source_note=args.source_note,
        expected_anchors=args.expect_anchor,
    )
    cleaned = clean_markdown(raw_text, metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(cleaned, encoding="utf-8")

    report = quality_report(cleaned, metadata.expected_anchors)
    report_lines = [f"{key}: {value}" for key, value in report.items()]
    report_text = "\n".join(report_lines) + "\n"
    if args.report:
        args.report.write_text(report_text, encoding="utf-8")
    print(report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
