"""Metrics for evidence-only RAG retrieval experiments."""
from __future__ import annotations

import math
from statistics import mean, median
from typing import Any, Iterable


def _same_evidence(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    expected_source = expected.get("source") or expected.get("law_name")
    actual_source = actual.get("source") or actual.get("law_name")
    if expected_source and not _source_matches(actual_source, expected_source):
        return False
    if expected.get("article_no") is not None:
        try:
            return int(actual.get("article_no")) == int(expected["article_no"])
        except (TypeError, ValueError):
            return False
    if expected.get("section_no") is not None:
        return str(actual.get("section_no")) == str(expected["section_no"])
    return bool(expected_source and _source_matches(actual_source, expected_source))


def _source_matches(actual_source: Any, expected_source: Any) -> bool:
    """Match a canonical source name to an indexed versioned display name."""
    actual = " ".join(str(actual_source or "").split())
    expected = " ".join(str(expected_source or "").split())
    if not actual or not expected:
        return False
    return actual == expected or actual.startswith(expected + " ") or expected.startswith(actual + " ")


def expected_hit_ranks(
    evidence: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    k: int,
) -> list[int]:
    """Return one-to-one hit ranks for expected items found in top-k evidence."""
    ranks, _ = _match_expected_evidence(evidence, expected, k)
    return ranks


def _match_expected_evidence(
    evidence: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    k: int,
) -> tuple[list[int], list[int]]:
    """Match chunks to expected evidence once, preventing duplicate-chunk inflation."""
    unmatched = set(range(len(expected)))
    ranks: list[int] = []
    relevance: list[int] = []
    for rank, actual in enumerate(evidence[:k], start=1):
        matching_index = next(
            (index for index in sorted(unmatched) if _same_evidence(actual, expected[index])),
            None,
        )
        if matching_index is None:
            relevance.append(0)
            continue
        unmatched.remove(matching_index)
        ranks.append(rank)
        relevance.append(1)
    return ranks, relevance


def _dcg(relevances: Iterable[int]) -> float:
    return sum(relevance / math.log2(index + 2) for index, relevance in enumerate(relevances))


def calculate_case_metrics(
    evidence: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    k: int,
) -> dict[str, float | int]:
    """Calculate binary evidence metrics for one case."""
    expected = expected or []
    ranks, relevance = _match_expected_evidence(evidence, expected, k)
    hit_count = len(ranks)
    recall = hit_count / len(expected) if expected else 1.0
    mrr = 1.0 / min(ranks) if ranks else 0.0
    ideal = [1] * min(len(expected), k)
    ndcg = _dcg(relevance) / _dcg(ideal) if ideal and _dcg(ideal) else 0.0
    expected_sources = {
        item.get("source") or item.get("law_name") for item in expected
    }
    matched_sources = {
        evidence_item.get("source") or evidence_item.get("law_name")
        for evidence_item in evidence[:k]
        if any(_same_evidence(evidence_item, item) for item in expected)
    }
    source_coverage = (
        len(matched_sources & expected_sources) / len(expected_sources)
        if expected_sources
        else 1.0
    )
    return {
        "evidence_recall_at_k": round(recall, 6),
        "mrr_at_k": round(mrr, 6),
        "ndcg_at_k": round(ndcg, 6),
        "multi_source_coverage": round(source_coverage, 6),
        "matched_evidence": hit_count,
        "expected_evidence": len(expected),
    }


def summarize_case_metrics(case_metrics: list[dict[str, Any]]) -> dict[str, float | int]:
    """Aggregate case metrics without hiding per-case results."""
    if not case_metrics:
        return {
            "case_count": 0,
            "evidence_recall_at_k": 0.0,
            "mrr_at_k": 0.0,
            "ndcg_at_k": 0.0,
            "multi_source_coverage": 0.0,
            "retrieval_time_p50_ms": 0.0,
            "retrieval_time_p95_ms": 0.0,
        }
    times = sorted(float(item.get("retrieval_elapsed_ms", 0.0)) for item in case_metrics)
    p95_index = min(len(times) - 1, max(0, math.ceil(len(times) * 0.95) - 1))
    return {
        "case_count": len(case_metrics),
        "evidence_recall_at_k": round(mean(float(item["evidence_recall_at_k"]) for item in case_metrics), 6),
        "mrr_at_k": round(mean(float(item["mrr_at_k"]) for item in case_metrics), 6),
        "ndcg_at_k": round(mean(float(item["ndcg_at_k"]) for item in case_metrics), 6),
        "multi_source_coverage": round(mean(float(item["multi_source_coverage"]) for item in case_metrics), 6),
        "retrieval_time_p50_ms": round(median(times), 2),
        "retrieval_time_p95_ms": round(times[p95_index], 2),
    }
