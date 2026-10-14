"""Build v0.4.15.19 base candidate live read-only probe report.

The default probe performs Qdrant read-only payload and sparse retrieval checks.
It does not call rag_query, run eval, call an LLM, rerank, mutate runtime
configuration, or write to Qdrant. Dense probing is explicit opt-in because it
may call the embedding service to build a query vector.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client.http import models

from src.core.vectorstore import get_qdrant_client, get_vectorstore
from src.rag.retriever import (
    RetrievalFilters,
    _candidate_exact_key,
    _limit_candidates_by_article_budget,
    point_to_document,
    retrieve_with_sparse,
    summarize_debug_results,
)


VERSION = "0.4.15.19"

DEFAULT_MISMATCH_PATH = Path("tests/base_candidate_mismatch_summary_v0.4.15.18_report.json")
DEFAULT_TRACE_PATH = Path("tests/targeted_dependency_trace_v0.4.15.16_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json")
DEFAULT_COLLECTION = "legal_knowledge"

READ_ONLY_METHODS_USED = [
    "get_collection",
    "count",
    "scroll",
    "sparse_query_http_post",
]

GUARDRAILS = {
    "qdrant_read_only": True,
    "qdrant_write": "disallowed",
    "rag_query_call": "disallowed",
    "eval_run": "disallowed",
    "llm_access": "disallowed",
    "rerank_call": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "dense_probe_default": "disabled_to_avoid_embedding_service_call",
}

FILTER_KEYS = [
    "doc_type",
    "block_type",
    "document_type",
    "law_name",
    "source",
    "law_level",
    "authority_level",
    "jurisdiction",
    "issuing_authority",
    "legal_effect",
    "standard_type",
    "case_type",
    "patent_type",
    "category",
    "version",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref_key(item: dict[str, Any]) -> tuple[str, Any, str]:
    return (
        str(item.get("source") or item.get("law_name") or ""),
        item.get("article_no"),
        str(item.get("section_no") or ""),
    )


def ref_label(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": item.get("source") or item.get("law_name"),
        "article_no": item.get("article_no"),
        "section_no": item.get("section_no") or "",
        "citation": item.get("citation"),
    }


def load_trace_cases(trace_path: Path) -> dict[str, dict[str, Any]]:
    trace = load_json(trace_path)
    return {
        str(item.get("id")): item
        for item in as_list(trace.get("reports"))
        if isinstance(item, dict) and item.get("id")
    }


def retrieval_filters_from_trace(case: dict[str, Any]) -> RetrievalFilters:
    filters = as_dict(as_dict(case.get("debug_info")).get("filters"))
    return RetrievalFilters(**{key: filters.get(key) for key in FILTER_KEYS})


def field_match_condition(field: str, value: Any) -> models.FieldCondition:
    return models.FieldCondition(
        key=f"metadata.{field}",
        match=models.MatchValue(value=value),
    )


def ref_conditions(ref: dict[str, Any], *, include_type: bool = False) -> list[models.FieldCondition]:
    source = ref.get("source") or ref.get("law_name")
    conditions: list[models.FieldCondition] = []
    if source:
        conditions.append(field_match_condition("source", source))
    article_no = ref.get("article_no")
    section_no = ref.get("section_no")
    if article_no is not None:
        conditions.append(field_match_condition("article_no", article_no))
    elif section_no:
        conditions.append(field_match_condition("section_no", section_no))
    if include_type:
        conditions.append(field_match_condition("type", "article"))
    return conditions


def scroll_ref_points(
    client: Any,
    collection_name: str,
    ref: dict[str, Any],
    *,
    filters: RetrievalFilters | None = None,
    limit: int = 20,
) -> list[Any]:
    conditions: list[Any] = []
    qdrant_filter = filters.to_qdrant_filter() if filters else None
    if qdrant_filter:
        conditions.extend(list(qdrant_filter.must or []))
    conditions.extend(ref_conditions(ref))
    points, _offset = client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(must=conditions),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return list(points)


def point_summary(point: Any) -> dict[str, Any]:
    payload = point.payload or {}
    metadata = payload.get("metadata") if isinstance(payload, dict) else {}
    metadata = metadata if isinstance(metadata, dict) else {}
    content = payload.get("page_content") or payload.get("content") or ""
    return {
        "id": str(getattr(point, "id", "")),
        "source": metadata.get("source") or metadata.get("law_name"),
        "article_no": metadata.get("article_no"),
        "section_no": metadata.get("section_no") or "",
        "type": metadata.get("type"),
        "block_type": metadata.get("block_type"),
        "document_type": metadata.get("document_type"),
        "category": metadata.get("category"),
        "chunk_id": metadata.get("chunk_id"),
        "citation": metadata.get("citation"),
        "content_preview": str(content)[:220],
    }


def doc_ref_matches(doc: Any, ref: dict[str, Any]) -> bool:
    metadata = getattr(doc, "metadata", {}) or {}
    doc_source = metadata.get("source") or metadata.get("law_name")
    ref_source = ref.get("source") or ref.get("law_name")
    if doc_source != ref_source:
        return False
    if ref.get("article_no") is not None:
        return metadata.get("article_no") == ref.get("article_no")
    if ref.get("section_no"):
        return str(metadata.get("section_no") or "") == str(ref.get("section_no") or "")
    return False


def find_ref_rank(results: list[tuple[Any, float]], ref: dict[str, Any]) -> dict[str, Any]:
    for index, (doc, score) in enumerate(results, start=1):
        if doc_ref_matches(doc, ref):
            return {
                "present": True,
                "rank": index,
                "score": float(score),
                "candidate": summarize_debug_results([(doc, score)], limit=1)[0],
            }
    return {"present": False, "rank": None, "score": None, "candidate": None}


def live_union(
    dense_results: list[tuple[Any, float]],
    sparse_results: list[tuple[Any, float]],
    *,
    max_total: int = 15,
) -> list[tuple[Any, float]]:
    seen = set()
    merged_docs = []
    score_by_key: dict[Any, float] = {}
    for doc, score in dense_results + sparse_results:
        key = _candidate_exact_key(doc)
        if key in seen:
            continue
        seen.add(key)
        merged_docs.append(doc)
        score_by_key[key] = float(score)
    limited_docs = _limit_candidates_by_article_budget(merged_docs, max_total=max_total)
    return [(doc, score_by_key.get(_candidate_exact_key(doc), 0.0)) for doc in limited_docs]


def run_sparse_probe(question: str, collection_name: str, filters: RetrievalFilters, *, k: int) -> dict[str, Any]:
    try:
        results = retrieve_with_sparse(question, collection_name=collection_name, k=k, filters=filters)
        return {"status": "completed", "results": results, "error": None}
    except Exception as exc:  # pragma: no cover - defensive only; retrieve_with_sparse usually logs and returns [].
        return {"status": "error", "results": [], "error": str(exc)}


def run_dense_probe(
    question: str,
    collection_name: str,
    filters: RetrievalFilters,
    *,
    k: int,
    score_threshold: float | None,
) -> dict[str, Any]:
    try:
        vectorstore = get_vectorstore(collection_name)
        results = vectorstore.similarity_search_with_score(
            question,
            k=k,
            filter=filters.to_qdrant_filter(),
            score_threshold=score_threshold,
        )
        return {"status": "completed", "results": results, "error": None}
    except Exception as exc:  # pragma: no cover - external service/client dependent.
        return {"status": "error", "results": [], "error": str(exc)}


def classify_ref(row: dict[str, Any], *, dense_enabled: bool) -> str:
    if row["qdrant_payload"]["found_count"] == 0:
        return "absent_from_qdrant_payload"
    if row["runtime_filter_probe"]["found_count"] == 0:
        return "metadata_filter_exclusion"
    if row["union_probe"]["in_runtime_union_15"]:
        return "saved_live_union_drift"
    if row["sparse_probe"]["high_k"]["present"] and not row["sparse_probe"]["runtime_k"]["present"]:
        return "sparse_rank_cutoff_loss"
    if row["union_probe"]["in_raw_sparse_high_k"] and not row["union_probe"]["in_runtime_union_15"]:
        return "candidate_budget_loss"
    if dense_enabled:
        if row["dense_probe"]["high_k"]["present"] and not row["dense_probe"]["runtime_k"]["present"]:
            return "dense_rank_cutoff_loss"
        if row["union_probe"]["in_raw_dense_high_k"] and not row["union_probe"]["in_runtime_union_15"]:
            return "candidate_budget_loss"
        return "base_retrieval_gap_confirmed_with_dense_probe"
    return "base_retrieval_gap_requires_dense_probe"


def build_ref_row(
    *,
    client: Any,
    collection_name: str,
    case_id: str,
    question: str,
    filters: RetrievalFilters,
    ref: dict[str, Any],
    sparse_runtime: list[tuple[Any, float]],
    sparse_high: list[tuple[Any, float]],
    dense_runtime: list[tuple[Any, float]],
    dense_high: list[tuple[Any, float]],
    max_ref_points: int,
    dense_enabled: bool,
) -> dict[str, Any]:
    payload_points = scroll_ref_points(client, collection_name, ref, limit=max_ref_points)
    filtered_points = scroll_ref_points(client, collection_name, ref, filters=filters, limit=max_ref_points)
    union_runtime = live_union(dense_runtime, sparse_runtime, max_total=15)
    union_high = live_union(dense_high, sparse_high, max_total=15)
    row = {
        "case_id": case_id,
        "question": question,
        "missing_ref": ref_label(ref),
        "qdrant_payload": {
            "found_count": len(payload_points),
            "sample_points": [point_summary(point) for point in payload_points[:3]],
        },
        "runtime_filter_probe": {
            "found_count": len(filtered_points),
            "passes_filter": bool(filtered_points),
            "sample_points": [point_summary(point) for point in filtered_points[:3]],
        },
        "dense_probe": {
            "enabled": dense_enabled,
            "runtime_k": find_ref_rank(dense_runtime, ref) if dense_enabled else {"present": False, "rank": None},
            "high_k": find_ref_rank(dense_high, ref) if dense_enabled else {"present": False, "rank": None},
        },
        "sparse_probe": {
            "runtime_k": find_ref_rank(sparse_runtime, ref),
            "high_k": find_ref_rank(sparse_high, ref),
        },
        "union_probe": {
            "in_raw_dense_high_k": find_ref_rank(dense_high, ref)["present"] if dense_enabled else False,
            "in_raw_sparse_high_k": find_ref_rank(sparse_high, ref)["present"],
            "in_runtime_union_15": find_ref_rank(union_runtime, ref)["present"],
            "in_high_k_union_15": find_ref_rank(union_high, ref)["present"],
            "runtime_union_top_refs": summarize_debug_results(union_runtime, limit=15),
        },
        "read_only_methods_used": list(READ_ONLY_METHODS_USED),
    }
    if dense_enabled:
        row["read_only_methods_used"].append("dense_similarity_search_with_score")
    row["attribution"] = classify_ref(row, dense_enabled=dense_enabled)
    return row


def build_report(
    *,
    mismatch_path: Path = DEFAULT_MISMATCH_PATH,
    trace_path: Path = DEFAULT_TRACE_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    sparse_runtime_k: int = 10,
    sparse_high_k: int = 100,
    dense_runtime_k: int = 5,
    dense_high_k: int = 100,
    max_ref_points: int = 20,
    enable_dense_probe: bool = False,
) -> dict[str, Any]:
    mismatch = load_json(mismatch_path)
    trace_cases = load_trace_cases(trace_path)
    client = get_qdrant_client()

    collection_error = None
    collection_count = None
    try:
        client.get_collection(collection_name)
        collection_count = getattr(client.count(collection_name=collection_name, exact=False), "count", None)
    except Exception as exc:
        collection_error = str(exc)

    case_rows = []
    ref_rows = []
    if collection_error is None:
        for case_row in as_list(mismatch.get("case_rows")):
            if not isinstance(case_row, dict):
                continue
            case_id = str(case_row.get("id") or "")
            trace_case = trace_cases.get(case_id, {})
            question = str(trace_case.get("question") or "")
            filters = retrieval_filters_from_trace(trace_case)
            score_threshold = as_dict(as_dict(trace_case.get("debug_info")).get("filters")).get("score_threshold")

            sparse_runtime_result = run_sparse_probe(
                question, collection_name, filters, k=sparse_runtime_k
            )
            sparse_high_result = run_sparse_probe(
                question, collection_name, filters, k=sparse_high_k
            )
            dense_runtime_result = {"status": "disabled", "results": [], "error": None}
            dense_high_result = {"status": "disabled", "results": [], "error": None}
            if enable_dense_probe:
                dense_runtime_result = run_dense_probe(
                    question, collection_name, filters, k=dense_runtime_k, score_threshold=score_threshold
                )
                dense_high_result = run_dense_probe(
                    question, collection_name, filters, k=dense_high_k, score_threshold=score_threshold
                )

            case_ref_rows = []
            for ref in as_list(case_row.get("missing_final_refs_from_union")):
                if not isinstance(ref, dict):
                    continue
                row = build_ref_row(
                    client=client,
                    collection_name=collection_name,
                    case_id=case_id,
                    question=question,
                    filters=filters,
                    ref=ref,
                    sparse_runtime=as_list(sparse_runtime_result.get("results")),
                    sparse_high=as_list(sparse_high_result.get("results")),
                    dense_runtime=as_list(dense_runtime_result.get("results")),
                    dense_high=as_list(dense_high_result.get("results")),
                    max_ref_points=max_ref_points,
                    dense_enabled=enable_dense_probe,
                )
                ref_rows.append(row)
                case_ref_rows.append(row)

            case_rows.append({
                "case_id": case_id,
                "question": question,
                "filters": filters.to_payload(candidate_k=15, score_threshold=score_threshold),
                "missing_ref_count": len(case_ref_rows),
                "attribution_counts": dict(sorted(Counter(row["attribution"] for row in case_ref_rows).items())),
                "sparse_runtime_status": sparse_runtime_result.get("status"),
                "sparse_high_status": sparse_high_result.get("status"),
                "dense_probe_enabled": enable_dense_probe,
                "dense_runtime_status": dense_runtime_result.get("status"),
                "dense_high_status": dense_high_result.get("status"),
                "errors": [
                    err for err in [
                        sparse_runtime_result.get("error"),
                        sparse_high_result.get("error"),
                        dense_runtime_result.get("error"),
                        dense_high_result.get("error"),
                    ] if err
                ],
            })

    attribution_counts = Counter(row["attribution"] for row in ref_rows)
    payload_present = sum(1 for row in ref_rows if row["qdrant_payload"]["found_count"] > 0)
    filter_present = sum(1 for row in ref_rows if row["runtime_filter_probe"]["found_count"] > 0)
    sparse_high_present = sum(1 for row in ref_rows if row["sparse_probe"]["high_k"]["present"])
    status = "qdrant_unavailable" if collection_error else "completed_requires_dense_probe"
    if enable_dense_probe and collection_error is None:
        status = "completed_with_dense_probe"
    return {
        "version": VERSION,
        "schema_kind": "base_candidate_live_readonly_probe",
        "scope": "targeted Qdrant live read-only probe for missing base union final refs",
        "generated_at": utc_now(),
        "inputs": {
            "mismatch_report": str(mismatch_path),
            "trace_report": str(trace_path),
            "collection_name": collection_name,
            "sparse_runtime_k": sparse_runtime_k,
            "sparse_high_k": sparse_high_k,
            "dense_probe_enabled": enable_dense_probe,
            "dense_runtime_k": dense_runtime_k if enable_dense_probe else None,
            "dense_high_k": dense_high_k if enable_dense_probe else None,
            "max_ref_points": max_ref_points,
        },
        "guardrails": GUARDRAILS,
        "collection_probe": {
            "collection_name": collection_name,
            "reachable": collection_error is None,
            "points_count": collection_count,
            "error": collection_error,
            "read_only_methods_used": ["get_collection", "count"],
        },
        "summary": {
            "status": status,
            "case_count": len(case_rows),
            "missing_ref_count": len(ref_rows),
            "qdrant_payload_present_count": payload_present,
            "runtime_filter_present_count": filter_present,
            "sparse_high_k_present_count": sparse_high_present,
            "dense_probe_enabled": enable_dense_probe,
            "attribution_counts": dict(sorted(attribution_counts.items())),
            "qdrant_write_performed": False,
            "rag_query_run": False,
            "eval_run": False,
            "next_step": (
                "enable_dense_probe_or_inspect_embedding_rank"
                if not enable_dense_probe and collection_error is None
                else "review_live_probe_attribution"
            ),
        },
        "case_rows": case_rows,
        "ref_rows": ref_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build base candidate live read-only Qdrant probe report.")
    parser.add_argument("--mismatch", type=Path, default=DEFAULT_MISMATCH_PATH)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--sparse-runtime-k", type=int, default=10)
    parser.add_argument("--sparse-high-k", type=int, default=100)
    parser.add_argument("--dense-runtime-k", type=int, default=5)
    parser.add_argument("--dense-high-k", type=int, default=100)
    parser.add_argument("--max-ref-points", type=int, default=20)
    parser.add_argument("--enable-dense-probe", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        mismatch_path=args.mismatch,
        trace_path=args.trace,
        collection_name=args.collection,
        sparse_runtime_k=args.sparse_runtime_k,
        sparse_high_k=args.sparse_high_k,
        dense_runtime_k=args.dense_runtime_k,
        dense_high_k=args.dense_high_k,
        max_ref_points=args.max_ref_points,
        enable_dense_probe=args.enable_dense_probe,
    )
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Base candidate live read-only probe completed: "
        f"{summary['status']}, refs={summary['missing_ref_count']}, "
        f"payload_present={summary['qdrant_payload_present_count']}, "
        f"sparse_high_present={summary['sparse_high_k_present_count']}"
    )
    return 0 if report["collection_probe"]["reachable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
