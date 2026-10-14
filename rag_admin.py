#!/usr/bin/env python
"""
RAG 知识库管理工具
用法：
    python rag_admin.py --stats                        查看集合统计
    python rag_admin.py --add <file.txt> [--source <name>] [--document-type <type>] [--law-level <level>] [--category <category>] [--version <version>]     增加文档
    python rag_admin.py --delete <source>              删除指定 source 的所有文档
    python rag_admin.py --replace <file.txt> <old_source> [--new-source <name>] [--law-level <level>] [--category <category>] [--version <version>]  替换文档
    python rag_admin.py --rebuild [--document-type <type>] [--law-level <level>] [--category <category>] [--version <version>]  全量重建（清空后重新入库所有 .txt/.md）
    python rag_admin.py --list-sources                 列出所有不同的 source
    python rag_admin.py --inspect [source]             检查知识库入库结构；可指定单个 source
"""

import os
import sys
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent))

from src.core.vectorstore import ensure_collection_with_sparse, get_qdrant_client
from src.rag.ingestion import ingest
import qdrant_client.http.models as models


def get_collection_name():
    return "legal_knowledge"


def print_stats():
    client = get_qdrant_client()
    try:
        info = client.get_collection(get_collection_name())
        print(f"集合名称: {get_collection_name()}")
        print(f"向量点数: {info.points_count}")
        print(f"状态: {info.status}")
    except Exception as e:
        print(f"获取集合信息失败: {e}")


def list_sources():
    """列出所有不同的 source（需要扫描所有点，可能较慢）"""
    client = get_qdrant_client()
    sources = set()
    offset = None
    while True:
        result = client.scroll(
            collection_name=get_collection_name(),
            limit=100,
            offset=offset,
            with_payload=True,
        )
        points, next_offset = result
        for point in points:
            src = point.payload.get("metadata", {}).get("source")
            if src:
                sources.add(src)
        if next_offset is None:
            break
        offset = next_offset
    print("当前知识库包含的文档来源：")
    for s in sorted(sources):
        print(f"  - {s}")


def iter_points(source: str = None, limit: int = 100):
    """扫描 Qdrant 点；source 不为空时只扫描指定来源。"""
    client = get_qdrant_client()
    offset = None
    scroll_filter = None
    if source:
        scroll_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.source",
                    match=models.MatchValue(value=source),
                )
            ]
        )

    while True:
        points, next_offset = client.scroll(
            collection_name=get_collection_name(),
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            yield point
        if next_offset is None:
            break
        offset = next_offset


def natural_key(value):
    """用于章节号/条号的人类友好排序。"""
    if value is None:
        return ()
    text = str(value)
    section_match = re.match(r"^(\d+(?:\.\d+)*)", text)
    sortable = section_match.group(1) if section_match else text
    parts = []
    for part in sortable.split("."):
        if part.isdigit():
            parts.append((0, int(part)))
        else:
            parts.append((1, part))
    if section_match:
        parts.append((2, text))
    return tuple(parts)


def new_source_summary():
    return {
        "total": 0,
        "law_name": "",
        "document_type": "",
        "law_level": "",
        "authority_level": "",
        "jurisdiction": "",
        "issuing_authority": "",
        "standard_type": "",
        "case_type": "",
        "patent_type": "",
        "category": "",
        "version": "",
        "type_counts": Counter(),
        "block_type_counts": Counter(),
        "article_labels": set(),
        "article_label_numbers": {},
        "article_numbers": set(),
        "standard_sections": set(),
        "chapters": set(),
        "citations": [],
    }


def summarize_points(points) -> tuple[dict, Counter, Counter]:
    """汇总 Qdrant payload，返回按 source 的摘要和全局计数。"""
    summaries = defaultdict(new_source_summary)
    document_type_counts = Counter()
    law_level_counts = Counter()

    for point in points:
        metadata = (point.payload or {}).get("metadata", {})
        source = metadata.get("source") or "(missing source)"
        summary = summaries[source]
        summary["total"] += 1

        for key in [
            "law_name",
            "document_type",
            "law_level",
            "authority_level",
            "jurisdiction",
            "issuing_authority",
            "standard_type",
            "case_type",
            "patent_type",
            "category",
            "version",
        ]:
            if not summary[key] and metadata.get(key):
                summary[key] = metadata.get(key)

        document_type_counts[metadata.get("document_type") or "(missing)"] += 1
        law_level_counts[metadata.get("law_level") or "(missing)"] += 1
        summary["type_counts"][metadata.get("type") or "(missing)"] += 1
        summary["block_type_counts"][metadata.get("block_type") or "(missing)"] += 1

        if metadata.get("block_type") == "article":
            if metadata.get("article"):
                summary["article_labels"].add(metadata.get("article"))
            if metadata.get("article_no") is not None:
                summary["article_numbers"].add(metadata.get("article_no"))
                if metadata.get("article"):
                    summary["article_label_numbers"][metadata.get("article")] = metadata.get("article_no")

        if metadata.get("block_type") == "standard_section":
            section_no = metadata.get("section_no") or ""
            section_title = metadata.get("section_title") or metadata.get("section") or ""
            label = " ".join(part for part in [section_no, section_title] if part).strip()
            if label:
                summary["standard_sections"].add(label)

        if metadata.get("type") == "chapter":
            heading = metadata.get("section") or metadata.get("chapter") or metadata.get("heading_level")
            if heading:
                summary["chapters"].add(heading)

        citation = metadata.get("citation")
        if citation and citation not in summary["citations"]:
            summary["citations"].append(citation)

    return summaries, document_type_counts, law_level_counts


def format_counter(counter: Counter) -> str:
    if not counter:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in counter.most_common())


def print_sample(title: str, values, sample_limit: int):
    values = list(values)
    if not values:
        return
    print(f"  {title}（{len(values)} 个）:")
    for value in values[:sample_limit]:
        print(f"    - {value}")
    if len(values) > sample_limit:
        print(f"    ... 还有 {len(values) - sample_limit} 个")


def print_source_summary(source: str, summary: dict, sample_limit: int):
    print(f"\n[{source}]")
    print(f"  law_name: {summary['law_name'] or '-'}")
    print(
        "  分类: "
        f"document_type={summary['document_type'] or '-'}, "
        f"law_level={summary['law_level'] or '-'}, "
        f"authority_level={summary['authority_level'] or '-'}, "
        f"jurisdiction={summary['jurisdiction'] or '-'}"
    )
    details = []
    for label, key in [
        ("issuing_authority", "issuing_authority"),
        ("standard_type", "standard_type"),
        ("case_type", "case_type"),
        ("patent_type", "patent_type"),
        ("category", "category"),
        ("version", "version"),
    ]:
        if summary[key]:
            details.append(f"{label}={summary[key]}")
    if details:
        print(f"  细节: {', '.join(details)}")
    print(f"  chunk 总数: {summary['total']}")
    print(f"  type 分布: {format_counter(summary['type_counts'])}")
    print(f"  block_type 分布: {format_counter(summary['block_type_counts'])}")

    article_numbers = sorted(summary["article_numbers"])
    if article_numbers:
        print(f"  条文数: {len(article_numbers)}（{article_numbers[0]} - {article_numbers[-1]}）")
        article_label_numbers = summary["article_label_numbers"]
        print_sample(
            "条文样例",
            sorted(
                summary["article_labels"],
                key=lambda label: (article_label_numbers.get(label, 999999), label),
            ),
            sample_limit,
        )

    print_sample("标准章节样例", sorted(summary["standard_sections"], key=natural_key), sample_limit)
    print_sample("标题/章节样例", sorted(summary["chapters"], key=natural_key), sample_limit)
    print_sample("引用样例", summary["citations"], sample_limit)


def inspect_knowledge_base(source: str = None, sample_limit: int = 8):
    """检查知识库入库结构，辅助判断文档是否按预期切片。"""
    points = list(iter_points(source=source))
    if not points:
        if source:
            print(f"未找到 source='{source}' 的文档。")
            print("可用 source：")
            list_sources()
        else:
            print("知识库为空。")
        return

    summaries, document_type_counts, law_level_counts = summarize_points(points)
    print(f"集合名称: {get_collection_name()}")
    print(f"扫描点数: {len(points)}")
    print(f"source 数量: {len(summaries)}")
    print(f"document_type 分布: {format_counter(document_type_counts)}")
    print(f"law_level 分布: {format_counter(law_level_counts)}")

    for source_name in sorted(summaries):
        print_source_summary(source_name, summaries[source_name], sample_limit)


def delete_by_source(source: str):
    """删除 metadata.source == source 的所有点"""
    client = get_qdrant_client()
    client.delete(
        collection_name=get_collection_name(),
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source",
                        match=models.MatchValue(value=source),
                    )
                ]
            )
        ),
    )
    print(f"已删除 source 为 '{source}' 的所有文档切片")


def add_document(
    file_path: str,
    source_name: str = None,
    law_level: str = None,
    category: str = "数据合规",
    version: str = "",
    document_type: str = None,
    authority_level: str = None,
    jurisdiction: str = None,
    issuing_authority: str = None,
    legal_effect: str = None,
    standard_type: str = None,
    case_type: str = None,
    patent_type: str = None,
):
    """追加一个文档（不删除已有）"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    # 调用 ingest，传递 source_name（若为 None 则自动从文件名提取）
    ingest(
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
    print(
        "已追加文档: "
        f"{file_path} "
        f"(source={source_name or Path(file_path).stem}, "
        f"document_type={document_type or 'auto'}, law_level={law_level or 'auto'}, "
        f"authority_level={authority_level or 'auto'}, jurisdiction={jurisdiction or 'auto'}, "
        f"category={category}, version={version})"
    )


def replace_document(
    file_path: str,
    old_source: str,
    new_source: str = None,
    law_level: str = None,
    category: str = "数据合规",
    version: str = "",
    document_type: str = None,
    authority_level: str = None,
    jurisdiction: str = None,
    issuing_authority: str = None,
    legal_effect: str = None,
    standard_type: str = None,
    case_type: str = None,
    patent_type: str = None,
):
    """先删除旧 source，再入库新文件，可指定新 source（默认取自文件名）"""
    print(f"准备替换 source='{old_source}' 的文档")
    delete_by_source(old_source)
    add_document(
        file_path,
        source_name=new_source,
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


def rebuild_all(
    docs_dir: str = "src/knowledge/data_compliance",
    law_level: str = None,
    category: str = "数据合规",
    version: str = "",
    document_type: str = None,
    authority_level: str = None,
    jurisdiction: str = None,
    issuing_authority: str = None,
    legal_effect: str = None,
    standard_type: str = None,
    case_type: str = None,
    patent_type: str = None,
):
    """全量重建：优先按 knowledge_manifest.json 重建全部文档，缺失时回退到目录扫描。"""
    print("⚠️  全量重建将删除现有所有数据")
    confirm = input("确定继续？(y/N): ")
    if confirm.lower() != "y":
        print("取消")
        return

    client = get_qdrant_client()
    try:
        client.delete_collection(get_collection_name())
    except Exception:
        pass
    ensure_collection_with_sparse(get_collection_name())
    print("已重建空集合（dense + bm25 sparse）")

    manifest_path = Path("knowledge_manifest.json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        documents = manifest.get("documents", [])
        if not documents:
            print("knowledge_manifest.json 中没有 documents")
            return
        for entry in documents:
            file_path = Path(entry.get("file_path", ""))
            if not file_path.exists():
                print(f"跳过不存在文件: {file_path}")
                continue
            print(
                f"入库: {file_path.name} "
                f"(source={entry.get('source')}, document_type={entry.get('document_type') or document_type or 'auto'}, "
                f"law_level={entry.get('law_level') or law_level or 'auto'}, category={entry.get('category') or category})"
            )
            ingest(
                str(file_path),
                source_name=entry.get("source"),
                law_level=entry.get("law_level") or law_level,
                category=entry.get("category") or category,
                version=entry.get("version", version),
                document_type=entry.get("document_type") or document_type,
                authority_level=entry.get("authority_level") or authority_level,
                jurisdiction=entry.get("jurisdiction") or jurisdiction,
                issuing_authority=entry.get("issuing_authority") or issuing_authority,
                legal_effect=entry.get("legal_effect") or legal_effect,
                standard_type=entry.get("standard_type") or standard_type,
                case_type=entry.get("case_type") or case_type,
                patent_type=entry.get("patent_type") or patent_type,
            )
    else:
        doc_dir = Path(docs_dir)
        if not doc_dir.exists():
            print(f"文档目录不存在: {doc_dir}")
            return
        input_files = sorted([*doc_dir.glob("*.txt"), *doc_dir.glob("*.md")])
        if not input_files:
            print("没有找到 .txt 或 .md 文件")
            return
        for txt_file in input_files:
            print(
                f"入库: {txt_file.name} "
                f"(source={txt_file.stem}, document_type={document_type or 'auto'}, "
                f"law_level={law_level or 'auto'}, category={category}, version={version})"
            )
            ingest(
                str(txt_file),
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
    print("全量重建完成")


def main():
    parser = argparse.ArgumentParser(description="RAG 知识库管理工具")
    parser.add_argument("--stats", action="store_true", help="查看集合统计")
    parser.add_argument("--add", type=str, help="增加文档（文件路径）")
    parser.add_argument("--delete", type=str, help="删除指定 source 的所有文档")
    parser.add_argument("--replace", nargs=2, metavar=("FILE", "OLD_SOURCE"), help="替换文档（文件路径 旧source）")
    parser.add_argument("--rebuild", action="store_true", help="全量重建（清空后重新入库所有文档）")
    parser.add_argument("--list-sources", action="store_true", help="列出所有不同的 source")
    parser.add_argument("--inspect", nargs="?", const="", metavar="SOURCE", help="检查知识库入库结构；可选指定 source")
    parser.add_argument("--inspect-limit", type=int, default=8, help="--inspect 输出样例数量（默认：8）")

    # 新增可选参数
    parser.add_argument("--source", type=str, help="用于 --add 时指定 source 名称（默认取自文件名）")
    parser.add_argument("--new-source", type=str, help="用于 --replace 时指定新 source 名称（默认取自文件名）")
    parser.add_argument("--document-type", type=str, help="指定粗类：法律法规、标准、专利、案例、政策文件、合同、报告、其他")
    parser.add_argument("--law-level", type=str, help="指定细分效力/类型：法律、行政法规、国家标准、指导性案例等；默认自动推断")
    parser.add_argument("--authority-level", type=str, help="指定发布/效力层级：国家级、地方级、行业级、团体级、企业级、国际")
    parser.add_argument("--jurisdiction", type=str, help="指定适用地域：全国、地方、国际等")
    parser.add_argument("--issuing-authority", type=str, help="指定发布机关")
    parser.add_argument("--legal-effect", type=str, help="指定效力状态：现行有效、已废止、尚未生效等")
    parser.add_argument("--standard-type", type=str, help="指定标准细类：强制性国家标准、推荐性国家标准、国家标准化指导性技术文件等")
    parser.add_argument("--case-type", type=str, help="指定案例细类：指导性案例、典型案例、裁判文书、行政处罚决定等")
    parser.add_argument("--patent-type", type=str, help="指定专利细类：发明专利、实用新型专利、外观设计专利等")
    parser.add_argument("--category", type=str, default="数据合规", help="指定知识分类（默认：数据合规）")
    parser.add_argument("--version", type=str, default="", help="指定法规版本或年份（默认：空）")

    args = parser.parse_args()

    if args.stats:
        print_stats()
    elif args.add:
        add_document(
            args.add,
            source_name=args.source,
            law_level=args.law_level,
            category=args.category,
            version=args.version,
            document_type=args.document_type,
            authority_level=args.authority_level,
            jurisdiction=args.jurisdiction,
            issuing_authority=args.issuing_authority,
            legal_effect=args.legal_effect,
            standard_type=args.standard_type,
            case_type=args.case_type,
            patent_type=args.patent_type,
        )
    elif args.delete:
        delete_by_source(args.delete)
    elif args.replace:
        file_path, old_source = args.replace
        replace_document(
            file_path,
            old_source,
            new_source=args.new_source,
            law_level=args.law_level,
            category=args.category,
            version=args.version,
            document_type=args.document_type,
            authority_level=args.authority_level,
            jurisdiction=args.jurisdiction,
            issuing_authority=args.issuing_authority,
            legal_effect=args.legal_effect,
            standard_type=args.standard_type,
            case_type=args.case_type,
            patent_type=args.patent_type,
        )
    elif args.rebuild:
        rebuild_all(
            law_level=args.law_level,
            category=args.category,
            version=args.version,
            document_type=args.document_type,
            authority_level=args.authority_level,
            jurisdiction=args.jurisdiction,
            issuing_authority=args.issuing_authority,
            legal_effect=args.legal_effect,
            standard_type=args.standard_type,
            case_type=args.case_type,
            patent_type=args.patent_type,
        )
    elif args.list_sources:
        list_sources()
    elif args.inspect is not None:
        inspect_knowledge_base(
            source=args.inspect or None,
            sample_limit=max(1, args.inspect_limit),
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
