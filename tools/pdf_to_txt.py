"""PDF 转 TXT 预处理工具。

适用于法规、标准、制度文件入库前的文本抽取质量检查。
如果 PDF 的文本层编码异常，本工具会生成报告并提示走 OCR。
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


COMMON_CHINESE_CHARS = set(
    "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过"
    "子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体"
    "制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线"
    "内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通"
    "并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将"
    "组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规"
    "热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清美再采转更单风切打白教速花"
    "带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土"
    "许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委"
    "素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲"
    "快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"
    "龙飞"
)

SUSPICIOUS_CHARS = set("犐犆犛犔犌犅犜狀狅犿犪狋犻狊犲犮狌狉犔狆")
CID_PATTERN = re.compile(r"\(cid:\d+\)")


@dataclass
class ExtractionResult:
    method: str
    text: str
    pages: int


def extract_with_pdfplumber(pdf_path: Path, max_pages: int | None = None) -> ExtractionResult:
    import pdfplumber

    page_texts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages
        for index, page in enumerate(pages, start=1):
            text = page.extract_text(x_tolerance=1.5, y_tolerance=3) or ""
            page_texts.append(f"\n\n=== Page {index} ===\n{text.strip()}")
        return ExtractionResult("pdfplumber", "\n".join(page_texts).strip(), len(pdf.pages))


def extract_with_fitz(pdf_path: Path, max_pages: int | None = None) -> ExtractionResult:
    import fitz

    page_texts = []
    with fitz.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        pages = range(min(max_pages, page_count)) if max_pages else range(page_count)
        for page_index in pages:
            text = doc[page_index].get_text("text") or ""
            page_texts.append(f"\n\n=== Page {page_index + 1} ===\n{text.strip()}")
        return ExtractionResult("fitz", "\n".join(page_texts).strip(), page_count)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = CID_PATTERN.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def quality_metrics(text: str) -> dict:
    nonspace_chars = [char for char in text if not char.isspace()]
    cjk_chars = [char for char in nonspace_chars if "\u4e00" <= char <= "\u9fff"]
    common_cjk_chars = [char for char in cjk_chars if char in COMMON_CHINESE_CHARS]
    suspicious_chars = [char for char in nonspace_chars if char in SUSPICIOUS_CHARS]
    cid_count = len(CID_PATTERN.findall(text))

    total = max(len(nonspace_chars), 1)
    cjk_count = max(len(cjk_chars), 1)
    return {
        "total_chars": len(nonspace_chars),
        "cjk_chars": len(cjk_chars),
        "common_cjk_chars": len(common_cjk_chars),
        "common_cjk_ratio": round(len(common_cjk_chars) / cjk_count, 4),
        "cjk_ratio": round(len(cjk_chars) / total, 4),
        "suspicious_ratio": round((len(suspicious_chars) + cid_count * 5) / total, 4),
        "cid_count": cid_count,
    }


def is_readable(metrics: dict, min_common_cjk_ratio: float, max_suspicious_ratio: float) -> bool:
    if metrics["total_chars"] < 200:
        return False
    if metrics["cjk_chars"] < 100:
        return False
    if metrics["common_cjk_ratio"] < min_common_cjk_ratio:
        return False
    if metrics["suspicious_ratio"] > max_suspicious_ratio:
        return False
    return True


def build_report(pdf_path: Path, result: ExtractionResult, metrics: dict, readable: bool) -> str:
    status = "PASS" if readable else "NEEDS_OCR"
    lines = [
        f"PDF: {pdf_path}",
        f"method: {result.method}",
        f"pages: {result.pages}",
        f"status: {status}",
        "",
        "metrics:",
    ]
    for key, value in metrics.items():
        lines.append(f"  {key}: {value}")
    lines.extend([
        "",
        "notes:",
        "  - PASS 表示文本层基本可读，可以继续人工清洗后入库。",
        "  - NEEDS_OCR 表示抽取文本疑似乱码或质量过低，建议改走 OCR 或寻找官方可复制文本源。",
        "  - 国标 PDF 常见特殊字体编码，pdfplumber/PyMuPDF 都可能抽出乱码。",
    ])
    return "\n".join(lines)


def choose_best_result(results: list[ExtractionResult]) -> tuple[ExtractionResult, dict]:
    scored = []
    for result in results:
        cleaned = normalize_text(result.text)
        metrics = quality_metrics(cleaned)
        score = metrics["common_cjk_ratio"] - metrics["suspicious_ratio"]
        scored.append((score, ExtractionResult(result.method, cleaned, result.pages), metrics))
    scored.sort(key=lambda item: item[0], reverse=True)
    _, best_result, best_metrics = scored[0]
    return best_result, best_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract readable TXT from PDF for RAG ingestion.")
    parser.add_argument("pdf", type=Path, help="PDF 文件路径")
    parser.add_argument("--output", "-o", type=Path, help="输出 TXT 路径")
    parser.add_argument("--report", type=Path, help="输出质量报告路径")
    parser.add_argument("--method", choices=["auto", "pdfplumber", "fitz"], default="auto")
    parser.add_argument("--max-pages", type=int, default=None, help="仅抽取前 N 页，用于快速检查")
    parser.add_argument("--min-common-cjk-ratio", type=float, default=0.35)
    parser.add_argument("--max-suspicious-ratio", type=float, default=0.08)
    parser.add_argument("--force", action="store_true", help="即使质量检测失败也输出 TXT")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf
    if not pdf_path.exists():
        print(f"文件不存在: {pdf_path}")
        return 2

    extractors = []
    if args.method in {"auto", "pdfplumber"}:
        extractors.append(extract_with_pdfplumber)
    if args.method in {"auto", "fitz"}:
        extractors.append(extract_with_fitz)

    results = [extractor(pdf_path, args.max_pages) for extractor in extractors]
    best_result, metrics = choose_best_result(results)
    readable = is_readable(metrics, args.min_common_cjk_ratio, args.max_suspicious_ratio)

    output_path = args.output or pdf_path.with_suffix(".txt")
    report_path = args.report or pdf_path.with_suffix(".pdf_extract_report.txt")
    report_text = build_report(pdf_path, best_result, metrics, readable)
    report_path.write_text(report_text, encoding="utf-8")

    if readable or args.force:
        output_path.write_text(best_result.text, encoding="utf-8")
        print(f"已输出 TXT: {output_path}")
    else:
        print("文本质量检测未通过，未输出 TXT。可使用 --force 强制输出。")

    print(report_text)
    return 0 if readable else 1


if __name__ == "__main__":
    raise SystemExit(main())
