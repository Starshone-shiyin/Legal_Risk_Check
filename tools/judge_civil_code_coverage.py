"""Judge the Civil Code source, coverage map, and direct-anchor configuration."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.ingestion import clean_legal_line, extract_article_metadata


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_article_numbers(path: Path) -> set[int]:
    articles: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        _, article_no = extract_article_metadata(clean_legal_line(line))
        if article_no is not None:
            articles.add(article_no)
    return articles


def build_judgment(root: Path = PROJECT_ROOT) -> dict:
    coverage = load_json(root / "config" / "civil_code_coverage.json")
    concepts = load_json(root / "config" / "legal_concepts.json").get("concepts", [])
    manifest = load_json(root / "knowledge_manifest.json").get("documents", [])
    source_path = root / coverage["source_file"]
    source_articles = source_article_numbers(source_path)
    expected_start, expected_end = coverage["article_range"]
    expected_articles = set(range(expected_start, expected_end + 1))
    concept_by_id = {item.get("id"): item for item in concepts if isinstance(item, dict)}
    manifest_entry = next((item for item in manifest if item.get("source") == coverage["source"]), None)

    findings: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        findings.append({"criterion": name, "passed": condition, "detail": detail})

    missing_source_articles = sorted(expected_articles - source_articles)
    unexpected_source_articles = sorted(source_articles - expected_articles)
    check(
        "全文条号连续",
        not missing_source_articles and not unexpected_source_articles,
        f"expected={expected_start}-{expected_end}; missing={missing_source_articles}; unexpected={unexpected_source_articles}",
    )
    check("民法典清单登记", manifest_entry is not None, "knowledge_manifest.json 包含中华人民共和国民法典")

    all_anchors: set[int] = set()
    missing_concepts: list[str] = []
    invalid_concept_anchors: list[dict] = []
    range_errors: list[dict] = []
    for book in coverage["books"]:
        start, end = book["range"]
        anchors = set(book.get("anchors", []))
        all_anchors.update(anchors)
        out_of_range = sorted(article for article in anchors if article < start or article > end)
        if out_of_range:
            range_errors.append({"book": book["book"], "anchors": out_of_range})
        for concept_id in book.get("concept_ids", []):
            concept = concept_by_id.get(concept_id)
            if not concept:
                missing_concepts.append(concept_id)
                continue
            civil_anchors = [
                article
                for anchor in concept.get("anchors", [])
                if anchor.get("source") == coverage["source"]
                for article in anchor.get("articles", [])
            ]
            if not civil_anchors or any(article not in source_articles for article in civil_anchors):
                invalid_concept_anchors.append({"concept_id": concept_id, "articles": civil_anchors})

    check("七编范围连续", all(book["range"][0] <= book["range"][1] for book in coverage["books"]), "每编均配置有效起止条号")
    check("七编代表性锚点", not range_errors and all_anchors.issubset(source_articles), f"out_of_range={range_errors}")
    check("概念直连法源", not missing_concepts and not invalid_concept_anchors, f"missing={missing_concepts}; invalid={invalid_concept_anchors}")
    check("七编均有概念覆盖", all(book.get("concept_ids") for book in coverage["books"]), "每编至少有一个常见概念直连法条")

    passed_count = sum(1 for finding in findings if finding["passed"])
    return {
        "report_type": "civil_code_coverage_judgment",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": coverage["source"],
        "article_range": coverage["article_range"],
        "books": [book["book"] for book in coverage["books"]],
        "summary": {"passed": passed_count, "total": len(findings), "source_article_count": len(source_articles), "anchor_count": len(all_anchors)},
        "findings": findings,
        "verdict": "accepted" if passed_count == len(findings) else "needs_revision",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Judge Civil Code source coverage and configured direct anchors.")
    parser.add_argument("--output", type=Path, default=Path("tests/civil_code_coverage_judge_report.json"))
    args = parser.parse_args()
    judgment = build_judgment()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(judgment, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": judgment["verdict"], "output": str(args.output), "summary": judgment["summary"]}, ensure_ascii=False))
    return 0 if judgment["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
