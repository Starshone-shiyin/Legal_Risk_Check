"""Build v0.4.15.18 base candidate source / lexical mismatch summary.

Saved-report-only. Does not run eval, call rag_query, access Qdrant/LLM, or
mutate runtime/config/test data.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.15.18"

DEFAULT_TRACE_PATH = Path("tests/targeted_dependency_trace_v0.4.15.16_report.json")
DEFAULT_INSPECTION_PATH = Path("tests/base_retrieval_query_inspection_v0.4.15.17_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/base_candidate_mismatch_summary_v0.4.15.18_report.json")

GUARDRAILS = {
    "saved_reports_only": True,
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
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9_\u4e00-\u9fff]+")
STOP_TOKENS = {
    "第",
    "条",
    "款",
    "项",
    "是否",
    "什么",
    "公司",
    "风险",
    "相关",
    "检索",
    "概念",
    "场景",
    "锚点",
    "法条",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ref_key(item: dict[str, Any]) -> str:
    return f"{item.get('source') or item.get('law_name')}::{item.get('article_no')}::{item.get('section_no') or ''}"


def ref_label(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": item.get("source") or item.get("law_name"),
        "article_no": item.get("article_no"),
        "section_no": item.get("section_no") or "",
        "citation": item.get("citation"),
    }


def debug(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(report.get("debug_info"))


def candidates(report: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [item for item in as_list(debug(report).get(key)) if isinstance(item, dict)]


def final_refs(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in as_list(report.get("evidence")) if isinstance(item, dict)]


def tokenize(text: str) -> set[str]:
    tokens = set()
    for token in TOKEN_RE.findall(text):
        token = token.strip()
        if len(token) < 2 or token in STOP_TOKENS:
            continue
        tokens.add(token)
    return tokens


def ref_text(item: dict[str, Any]) -> str:
    return " ".join(
        str(item.get(key) or "")
        for key in ["source", "law_name", "citation", "content_preview"]
    )


def query_tokens(report: dict[str, Any]) -> set[str]:
    return tokenize(str(debug(report).get("used_rerank_query") or debug(report).get("used_query") or ""))


def overlap_ratio(query: set[str], item: dict[str, Any]) -> float:
    ref_tokens = tokenize(ref_text(item))
    if not ref_tokens:
        return 0.0
    return round(len(query & ref_tokens) / len(ref_tokens), 4)


def source_distribution(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(item.get("source") or item.get("law_name") or "unknown") for item in items)
    return dict(sorted(counts.items()))


def classify_mismatch(report: dict[str, Any]) -> str:
    final = final_refs(report)
    union = candidates(report, "union_candidates")
    union_keys = {ref_key(item) for item in union}
    missing_final = [item for item in final if ref_key(item) not in union_keys]
    if not missing_final:
        return "final_refs_present_in_union"
    missing_sources = {str(item.get("source") or item.get("law_name")) for item in missing_final}
    union_sources = {str(item.get("source") or item.get("law_name")) for item in union[:5]}
    if missing_sources.isdisjoint(union_sources):
        return "union_top_source_drift"
    missing_articles = {
        (str(item.get("source") or item.get("law_name")), item.get("article_no"))
        for item in missing_final
    }
    union_articles = {(str(item.get("source") or item.get("law_name")), item.get("article_no")) for item in union[:10]}
    if missing_articles.isdisjoint(union_articles):
        return "same_source_article_drift"
    return "partial_final_ref_missing_from_union"


def build_case_row(report: dict[str, Any], inspected_ids: set[str]) -> dict[str, Any] | None:
    case_id = str(report.get("id") or "")
    if inspected_ids and case_id not in inspected_ids:
        return None
    query = query_tokens(report)
    final = final_refs(report)
    union = candidates(report, "union_candidates")
    anchor = candidates(report, "anchor_candidates")
    union_keys = {ref_key(item) for item in union}
    missing_final = [item for item in final if ref_key(item) not in union_keys]
    return {
        "id": case_id,
        "classification": classify_mismatch(report),
        "query_token_count": len(query),
        "union_candidate_count": len(union),
        "anchor_candidate_count": len(anchor),
        "final_refs": [ref_label(item) for item in final],
        "union_top_refs": [ref_label(item) for item in union[:5]],
        "missing_final_refs_from_union": [ref_label(item) for item in missing_final],
        "union_source_distribution_top15": source_distribution(union[:15]),
        "anchor_source_distribution": source_distribution(anchor),
        "final_ref_query_overlap": [
            {**ref_label(item), "query_overlap_ratio": overlap_ratio(query, item)}
            for item in final
        ],
        "union_top_query_overlap": [
            {**ref_label(item), "query_overlap_ratio": overlap_ratio(query, item)}
            for item in union[:5]
        ],
    }


def inspected_case_ids(inspection: dict[str, Any]) -> set[str]:
    summary = as_dict(inspection.get("summary"))
    return set(str(item) for item in as_list(summary.get("anchor_filled_final_ref_cases")))


def build_report(
    trace_path: Path = DEFAULT_TRACE_PATH,
    inspection_path: Path = DEFAULT_INSPECTION_PATH,
) -> dict[str, Any]:
    trace = load_json(trace_path)
    inspection = load_json(inspection_path)
    ids = inspected_case_ids(inspection)
    rows = []
    if not ids:
        status = "no_inspected_cases"
        return {
            "version": VERSION,
            "schema_kind": "base_candidate_mismatch_summary",
            "scope": "saved-report source/article drift and lexical mismatch summary before Qdrant inspection",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "targeted_trace_report": str(trace_path),
                "base_retrieval_query_inspection": str(inspection_path),
                "inspected_case_count": 0,
            },
            "guardrails": GUARDRAILS,
            "summary": {
                "status": status,
                "total_cases": 0,
                "classification_counts": {},
                "missing_final_ref_from_union_total": 0,
                "qdrant_stop_required": False,
                "stopping_condition": "No anchor-filled final-ref cases were supplied by the inspection report.",
            },
            "case_rows": rows,
        }
    for report in as_list(trace.get("reports")):
        if not isinstance(report, dict):
            continue
        row = build_case_row(report, ids)
        if row:
            rows.append(row)

    classification_counts = Counter(str(row.get("classification")) for row in rows)
    missing_ref_total = sum(len(as_list(row.get("missing_final_refs_from_union"))) for row in rows)
    status = "qdrant_or_live_retrieval_needed" if missing_ref_total else "no_qdrant_needed"
    stopping_condition = (
        "Saved reports can identify source/article drift and query overlap, but cannot prove whether missing final refs "
        "were absent from Qdrant payloads, filtered before candidate collection, or scored below candidate cutoffs. "
        "Resolving that requires Qdrant/live retrieval inspection."
    )
    return {
        "version": VERSION,
        "schema_kind": "base_candidate_mismatch_summary",
        "scope": "saved-report source/article drift and lexical mismatch summary before Qdrant inspection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "targeted_trace_report": str(trace_path),
            "base_retrieval_query_inspection": str(inspection_path),
            "inspected_case_count": len(ids),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "total_cases": len(rows),
            "classification_counts": dict(sorted(classification_counts.items())),
            "missing_final_ref_from_union_total": missing_ref_total,
            "qdrant_stop_required": status == "qdrant_or_live_retrieval_needed",
            "stopping_condition": stopping_condition,
        },
        "case_rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build base candidate mismatch summary from saved reports.")
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--inspection", type=Path, default=DEFAULT_INSPECTION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.trace, args.inspection)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Base candidate mismatch summary completed: "
        f"{summary['status']}, total={summary['total_cases']}, "
        f"missing_final_refs={summary['missing_final_ref_from_union_total']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
