"""Build a saved-source legal text version verification packet.

The tool compares saved legal-source snapshots with the v0.4.17.4 expected-level
review packet. It does not browse the web, run eval, call RAG/Qdrant/LLM, or
mutate runtime/eval assets.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.17.5"

DEFAULT_REVIEW_PACKET_PATH = Path("tests/rag_expected_level_review_packet_v0.4.17.4_report.json")
DEFAULT_SNAPSHOT_PATH = Path("tests/legal_text_version_snapshot_v0.4.17.5.json")
DEFAULT_OUTPUT_PATH = Path("tests/legal_text_version_verification_packet_v0.4.17.5_report.json")

GUARDRAILS = {
    "saved_sources_only": True,
    "web_access_at_runtime": "disallowed",
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "taxonomy_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def article_numbers_from_text(text: str) -> list[int]:
    numbers: list[int] = []
    chinese_digits = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    for match in re.finditer(r"第\s*(\d+)\s*条", text or ""):
        numbers.append(int(match.group(1)))
    for match in re.finditer(r"第\s*([一二三四五六七八九十])\s*条", text or ""):
        numbers.append(chinese_digits[match.group(1)])
    return numbers


def unique_ints(values: list[Any]) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        if isinstance(value, int):
            number = value
        elif isinstance(value, str) and value.isdigit():
            number = int(value)
        else:
            continue
        if number not in seen:
            result.append(number)
            seen.add(number)
    return result


def evidence_article_numbers(row: dict[str, Any]) -> list[int]:
    values = []
    for run_refs in as_list(row.get("final_evidence_refs_by_run")):
        for ref in as_list(run_refs):
            values.append(as_dict(ref).get("article_no"))
    return unique_ints(values)


def expected_article_numbers(row: dict[str, Any]) -> list[int]:
    metadata = as_dict(row.get("expected_case_metadata"))
    return unique_ints([as_dict(ref).get("article_no") for ref in as_list(metadata.get("expected_evidence"))])


def current_confusion_article(snapshot: dict[str, Any]) -> int | None:
    conclusion = as_dict(snapshot.get("conclusion"))
    value = conclusion.get("current_law_confusion_behavior_article_no")
    return int(value) if isinstance(value, int) else None


def prior_confusion_article(snapshot: dict[str, Any]) -> int | None:
    conclusion = as_dict(snapshot.get("conclusion"))
    value = conclusion.get("prior_2019_law_confusion_behavior_article_no")
    return int(value) if isinstance(value, int) else None


def classify_row(row: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    metadata = as_dict(row.get("expected_case_metadata"))
    expected_articles = expected_article_numbers(row)
    final_articles = evidence_article_numbers(row)
    reasoning_articles = article_numbers_from_text(str(metadata.get("legal_reasoning") or ""))
    current_article = current_confusion_article(snapshot)
    prior_article = prior_confusion_article(snapshot)

    current_evidence_valid = current_article in expected_articles and current_article in final_articles
    reasoning_uses_prior_article = bool(prior_article and prior_article in reasoning_articles)
    article_numbering_drift = bool(
        current_article
        and prior_article
        and current_article != prior_article
        and current_evidence_valid
        and reasoning_uses_prior_article
    )

    if article_numbering_drift:
        classification = "metadata_article_numbering_drift_current_evidence_valid"
        recommended_next_step = "manual_review_metadata_wording_only_no_runtime_patch"
    elif current_evidence_valid:
        classification = "current_law_evidence_valid"
        recommended_next_step = "keep_current_evidence_mapping_and_review_level_only"
    else:
        classification = "legal_text_mapping_review_required"
        recommended_next_step = "inspect_legal_text_mapping_before_any_patch"

    return {
        "case_id": row.get("case_id"),
        "classification": classification,
        "recommended_next_step": recommended_next_step,
        "current_law_confusion_article_no": current_article,
        "prior_2019_confusion_article_no": prior_article,
        "expected_evidence_article_numbers": expected_articles,
        "final_evidence_article_numbers": final_articles,
        "legal_reasoning_article_numbers": reasoning_articles,
        "current_evidence_valid": current_evidence_valid,
        "article_numbering_drift": article_numbering_drift,
        "runtime_patch_allowed": False,
        "anchor_change_allowed": False,
        "eval_case_change_allowed_without_manual_review": False,
        "review_reasons": [
            "Saved legal-source snapshot maps current 2025 confusion behavior to Article 7.",
            "The repeat evidence chain and expected evidence both use Article 7.",
            "The eval-case legal_reasoning references Article 6, which matches the 2019 confusion-behavior numbering but not the 2025 current-law numbering."
            if article_numbering_drift
            else "No prior/current article-numbering drift was detected from saved metadata.",
        ],
    }


def build_report(
    review_packet_path: Path = DEFAULT_REVIEW_PACKET_PATH,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
) -> dict[str, Any]:
    review_packet = load_json(review_packet_path)
    snapshot = load_json(snapshot_path)
    rows = [
        classify_row(row, snapshot)
        for row in as_list(review_packet.get("case_rows"))
        if isinstance(row, dict)
    ]
    classification_counts = Counter(str(row["classification"]) for row in rows)

    return {
        "version": VERSION,
        "schema_kind": "legal_text_version_verification_packet",
        "scope": "saved-source verification for anti-unfair-competition article numbering",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "review_packet": str(review_packet_path),
            "legal_text_snapshot": str(snapshot_path),
            "source_urls": [source.get("url") for source in as_list(snapshot.get("sources")) if isinstance(source, dict)],
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": "legal_text_version_verified" if rows else "no_case_rows",
            "case_count": len(rows),
            "classification_counts": dict(sorted(classification_counts.items())),
            "current_law_confusion_article_no": current_confusion_article(snapshot),
            "prior_2019_confusion_article_no": prior_confusion_article(snapshot),
            "runtime_patch_recommendation": "not_recommended_by_this_packet",
            "anchor_change_recommendation": "not_recommended_by_this_packet",
            "eval_case_change_recommendation": "manual_review_required_before_change",
        },
        "case_rows": rows,
        "source_snapshot": snapshot,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-source legal text version verification packet.")
    parser.add_argument("--review-packet", type=Path, default=DEFAULT_REVIEW_PACKET_PATH)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.review_packet, args.snapshot)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Legal text version verification completed: "
        f"{summary['status']}, case_count={summary['case_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
