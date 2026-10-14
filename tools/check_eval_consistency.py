"""自检工具：扫描测试用例中的 expected_evidence，验证法条号是否与知识库实际内容一致。

用于每次新增/修改法规或测试用例后，自动发现条款号错位、内容不匹配等问题。
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from qdrant_client.http import models

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.vectorstore import get_qdrant_client


def check_all(
    eval_path: Path = ROOT / "tests" / "rag_eval_cases.json",
    smoke_path: Path = ROOT / "tests" / "smoke_eval_cases.json",
) -> dict:
    """检查所有评测用例的 expected_evidence 是否与 Qdrant 数据一致。"""
    client = get_qdrant_client()
    issues: dict[str, list[str]] = defaultdict(list)
    checked = 0

    for label, path in [("rag_eval", eval_path), ("smoke_eval", smoke_path)]:
        if not path.exists():
            issues["_missing_file"].append(str(path))
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for case in data.get("cases", []):
            cid = case.get("id", "?")
            checked += 1
            for ev in case.get("expected_evidence", []):
                src = ev.get("source", "")
                an = ev.get("article_no")
                sn = ev.get("section_no")
                if an is not None:
                    # 检查 article_no 是否存在
                    points, _ = client.scroll(
                        collection_name="legal_knowledge",
                        scroll_filter=models.Filter(must=[
                            models.FieldCondition(key="metadata.source", match=models.MatchValue(value=src)),
                            models.FieldCondition(key="metadata.article_no", match=models.MatchValue(value=an)),
                        ]),
                        limit=1,
                        with_payload=True,
                    )
                    if not points:
                        issues[cid].append(
                            f"MISSING: [{src}] 第{an}条 在知识库中不存在"
                        )
                    else:
                        # 可选：检查内容是否与 case 主题相关（轻量关键词匹配）
                        _check_content_relevance(cid, case, ev, points[0], issues)

                if sn is not None:
                    points, _ = client.scroll(
                        collection_name="legal_knowledge",
                        scroll_filter=models.Filter(must=[
                            models.FieldCondition(key="metadata.source", match=models.MatchValue(value=src)),
                            models.FieldCondition(key="metadata.section_no", match=models.MatchValue(value=sn)),
                        ]),
                        limit=1,
                        with_payload=True,
                    )
                    if not points:
                        issues[cid].append(
                            f"MISSING: [{src}] 第{sn}节 在知识库中不存在"
                        )

    return {"checked": checked, "issues": dict(issues)}


def _check_content_relevance(case_id: str, case: dict, ev: dict, point, issues: dict):
    """启发式检查：法条存在但内容是否与题目主题相关。"""
    question = case.get("question", "")
    content = point.payload.get("page_content", "")
    metadata = point.payload.get("metadata", {})
    article_label = metadata.get("article", "")

    # 仅对有明显主题词的问题做检查
    topic_keywords = _extract_topic_keywords(question)
    if not topic_keywords:
        return

    # 如果法条内容中至少命中一个主题词，认为相关
    if any(kw in content for kw in topic_keywords):
        return

    issues[case_id].append(
        f"SUSPICIOUS: [{ev.get('source')}] {article_label} 存在但与题目主题词 {topic_keywords} 可能不相关"
    )


def _extract_topic_keywords(question: str) -> list[str]:
    """从题目中提取最可能的主题关键词。"""
    topic_map = {
        "出资": ["出资", "缴纳", "认缴"],
        "分红": ["分红", "利润分配", "税后利润"],
        "董事": ["忠实", "勤勉", "董事"],
        "股权转让": ["股权转让", "优先购买"],
        "法人人格": ["法人", "连带", "独立地位"],
        "知情": ["查阅", "知情"],
        "混淆": ["混淆", "误认"],
        "商业秘密": ["商业秘密", "保密"],
        "垄断协议": ["垄断协议", "固定价格"],
        "滥用市场支配": ["市场支配", "滥用"],
        "经营者集中": ["经营者集中", "申报"],
        "商标侵权": ["商标侵权", "注册商标"],
        "专利侵权": ["专利侵权", "未经许可"],
        "职务发明": ["职务发明", "职务行为"],
        "专利条件": ["新颖性", "创造性"],
        "增值税": ["增值税", "进项", "销项", "发票"],
        "格式条款": ["格式条款", "自动续费"],
        "违约责任": ["违约", "不履行"],
        "产品责任": ["产品责任", "缺陷"],
        "业主": ["共有", "业主", "物业"],
    }
    for topic, keywords in topic_map.items():
        if any(kw in question for kw in keywords):
            return keywords
    return []


def print_report(result: dict):
    checked = result["checked"]
    issues = result["issues"]
    issues.pop("_missing_file", None)
    if not issues:
        print(f"All {checked} test cases consistent with knowledge base.")
        return
    count = sum(len(v) for v in issues.values())
    print(f"{len(issues)} test cases have {count} issues (out of {checked} checked):\n")
    for cid in sorted(issues):
        for msg in issues[cid]:
            print(f"  [{cid}] {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check eval cases for article number consistency.")
    parser.add_argument("--rag-eval", type=Path, default=ROOT / "tests" / "rag_eval_cases.json")
    parser.add_argument("--smoke-eval", type=Path, default=ROOT / "tests" / "smoke_eval_cases.json")
    parser.add_argument("--output", type=Path, help="Save JSON report")
    args = parser.parse_args()

    result = check_all(eval_path=args.rag_eval, smoke_path=args.smoke_eval)
    print_report(result)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved: {args.output}")
    return 0 if not result.get("issues") else 1


if __name__ == "__main__":
    raise SystemExit(main())
