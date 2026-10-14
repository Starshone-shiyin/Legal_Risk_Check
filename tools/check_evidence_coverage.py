"""Offline evidence coverage diagnostics for saved RAG evaluation reports.

This tool reads existing report artifacts only. It does not call rag_query,
LLMs, Qdrant, rerank, prompt construction, anchor injection, or risk rules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.legal_functional_typing import (
    classify_evidence_function,
    classify_legal_function,
    has_operative_support,
    load_functional_type_config,
)
from src.rag.ingestion import load_txt
from tools.check_evidence_alignment import (
    evidence_matches_expected,
    expected_evidence_from_report,
    infer_expected_domains,
    load_scenario_metadata,
    normalize_text,
    read_reports,
    source_domain,
)
from tools._shared.layout import legacy_report_path


DEFAULT_RAG_REPORT_PATH = legacy_report_path("rag_eval_report.json")
DEFAULT_HIDDEN_REPORT_PATH = legacy_report_path("hidden_eval_report.json")
DEFAULT_SCENARIO_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_KNOWLEDGE_MANIFEST_PATH = Path("knowledge_manifest.json")
DEFAULT_FUNCTIONAL_TYPE_CONFIG_PATH = Path("config/legal_functional_types.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("evidence_coverage_report.json")
REPORT_VERSION = "0.4.7.4.1"

COVERAGE_OK = "ok"
COVERAGE_REVIEW = "review"

ISSUE_FINAL_PRIMARY_GAP = "final_primary_gap"
ISSUE_SCENARIO_CORE_GAP = "scenario_core_gap"
ISSUE_OPERATIVE_SUPPORT_GAP = "operative_support_gap"
ISSUE_FUNCTIONAL_TYPE_GAP = "functional_type_gap"
ISSUE_ANCHOR_DEPENDENT_COVERAGE = "anchor_dependent_coverage"
ISSUE_LAYER_COVERAGE_REGRESSION = "layer_coverage_regression"
ISSUE_LOW_FINAL_COVERAGE = "low_final_coverage"

DIAGNOSTIC_LAYERS = ("dense", "sparse", "union", "anchor", "rerank_input", "final")
OPERATIVE_TYPES = {"operative_rule", "procedural", "liability", "rights_remedy", "technical_standard"}
TEXT_PREVIEW_CHARS = 260
CITATION_LOCATION_PATTERN = re.compile(r"《(?P<source>[^》]+)》(?P<location>[^\]]+)")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_preview(text: Any, limit: int = TEXT_PREVIEW_CHARS) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def article_identity(item: dict[str, Any]) -> dict[str, Any]:
    identity = {
        "source": item.get("source") or item.get("law_name"),
        "article_no": item.get("article_no"),
        "section_no": item.get("section_no") or "",
    }
    for key in (
        "citation",
        "content_preview",
        "functional_type",
        "functional_type_confidence",
        "functional_type_matched_rule",
        "enrichment_status",
        "enrichment_source",
    ):
        if item.get(key) not in (None, "", []):
            identity[key] = item.get(key)
    return identity


def article_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize_text(item.get("source") or item.get("law_name")),
        normalize_text(item.get("article_no")),
        normalize_text(item.get("section_no")),
    )


def manifest_documents(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path or not manifest_path.exists():
        return []
    payload = load_json(manifest_path)
    return [item for item in payload.get("documents") or [] if isinstance(item, dict)]


def document_load_kwargs(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": document.get("source"),
        "law_level": document.get("law_level"),
        "category": document.get("category", "数据合规"),
        "version": document.get("version", ""),
        "document_type": document.get("document_type"),
        "authority_level": document.get("authority_level"),
        "jurisdiction": document.get("jurisdiction"),
        "issuing_authority": document.get("issuing_authority"),
        "legal_effect": document.get("legal_effect"),
        "standard_type": document.get("standard_type"),
        "case_type": document.get("case_type"),
        "patent_type": document.get("patent_type"),
    }


def evidence_index_key(source: Any, article_no: Any = "", section_no: Any = "") -> tuple[str, str, str]:
    return (normalize_text(source), normalize_text(article_no), normalize_text(section_no))


def citation_location_key(citation: Any) -> tuple[str, str, str] | None:
    text = normalize_text(citation)
    match = CITATION_LOCATION_PATTERN.search(text)
    if not match:
        return None
    source = match.group("source")
    location = normalize_text(match.group("location"))
    if not source or not location:
        return None
    return evidence_index_key(source, "", location)


def evidence_index_candidate(doc: Any, config: dict[str, Any]) -> dict[str, Any] | None:
    metadata = dict(getattr(doc, "metadata", {}) or {})
    source = metadata.get("source") or metadata.get("law_name")
    article_no = metadata.get("article_no")
    section_no = metadata.get("section_no") or metadata.get("section_title") or ""
    if article_no in (None, "") and not section_no:
        return None

    content = metadata.get("parent_content") or getattr(doc, "page_content", "")
    if not normalize_text(content):
        return None

    result = classify_legal_function(content, metadata, config)
    block_type = normalize_text(metadata.get("block_type") or metadata.get("type"))
    score = min(len(str(content)), 2000) / 2000
    if block_type == "article":
        score += 3
    elif block_type in {"section", "standard_section"}:
        score += 2
    elif block_type == "paragraph":
        score += 1
    if metadata.get("paragraph_no") is None and metadata.get("item_no") is None:
        score += 0.5

    return {
        "source": source,
        "law_name": metadata.get("law_name") or source,
        "article_no": article_no,
        "section_no": section_no,
        "citation": metadata.get("citation"),
        "category": metadata.get("category"),
        "document_type": metadata.get("document_type"),
        "content_preview": compact_preview(content),
        "functional_type": result.functional_type,
        "functional_type_confidence": result.confidence,
        "functional_type_matched_rule": result.matched_rule,
        "functional_type_matched_terms": list(result.matched_terms),
        "enrichment_status": "matched",
        "enrichment_source": "knowledge_manifest",
        "_score": score,
    }


def build_evidence_enrichment_index(
    manifest_path: Path = DEFAULT_KNOWLEDGE_MANIFEST_PATH,
    config_path: Path = DEFAULT_FUNCTIONAL_TYPE_CONFIG_PATH,
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, Any]]:
    documents = manifest_documents(manifest_path)
    config = load_functional_type_config(str(config_path))
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    missing_files = []
    loaded_documents = 0
    indexed_articles = 0

    for document in documents:
        file_path = Path(document.get("file_path", ""))
        if not file_path.exists():
            missing_files.append(str(file_path))
            continue
        loaded_documents += 1
        for doc in load_txt(str(file_path), **document_load_kwargs(document)):
            candidate = evidence_index_candidate(doc, config)
            if not candidate:
                continue
            keys = [
                evidence_index_key(candidate.get("source"), candidate.get("article_no"), candidate.get("section_no")),
                evidence_index_key(candidate.get("law_name"), candidate.get("article_no"), candidate.get("section_no")),
            ]
            if candidate.get("citation"):
                citation_key = citation_location_key(candidate.get("citation"))
                if citation_key:
                    keys.append(citation_key)
            if candidate.get("article_no") not in (None, ""):
                keys.extend([
                    evidence_index_key(candidate.get("source"), candidate.get("article_no"), ""),
                    evidence_index_key(candidate.get("law_name"), candidate.get("article_no"), ""),
                ])
            for key in keys:
                if not key[0] or (not key[1] and not key[2]):
                    continue
                existing = index.get(key)
                if not existing or candidate["_score"] > existing.get("_score", 0):
                    index[key] = dict(candidate)
        indexed_articles = len(index)

    for value in index.values():
        value.pop("_score", None)

    return index, {
        "enabled": bool(documents),
        "manifest": str(manifest_path),
        "functional_type_config": str(config_path),
        "manifest_documents": len(documents),
        "loaded_documents": loaded_documents,
        "indexed_keys": indexed_articles,
        "missing_files": missing_files,
    }


def enrich_article_item(
    item: dict[str, Any],
    enrichment_index: dict[tuple[str, str, str], dict[str, Any]] | None,
) -> dict[str, Any]:
    enriched = dict(item)
    if not enrichment_index:
        enriched.setdefault("enrichment_status", "disabled")
        return enriched

    keys = [
        article_key(enriched),
        evidence_index_key(enriched.get("source") or enriched.get("law_name"), enriched.get("article_no"), ""),
        evidence_index_key(enriched.get("law_name") or enriched.get("source"), enriched.get("article_no"), ""),
    ]
    citation_key = citation_location_key(enriched.get("citation"))
    if citation_key:
        keys.append(citation_key)
    match = None
    for key in keys:
        if key in enrichment_index:
            match = enrichment_index[key]
            break
    if not match:
        enriched.setdefault("enrichment_status", "not_found")
        return enriched

    for key, value in match.items():
        if key in {"source", "law_name", "article_no", "section_no"}:
            enriched.setdefault(key, value)
        else:
            enriched[key] = value
    return enriched


def enrich_article_items(
    items: list[dict[str, Any]],
    enrichment_index: dict[tuple[str, str, str], dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [enrich_article_item(item, enrichment_index) for item in items]


def unique_articles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, Any, str]] = set()
    result = []
    for item in items:
        identity = article_identity(item)
        key = (
            normalize_text(identity["source"]),
            identity["article_no"],
            normalize_text(identity["section_no"]),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(identity)
    return result


def layer_payload(report: dict[str, Any], layer_name: str) -> dict[str, Any]:
    return (
        report.get("retrieval_diagnostics", {})
        .get("layers", {})
        .get(layer_name, {})
    )


def expected_count_from_report(report: dict[str, Any]) -> int:
    final_layer = layer_payload(report, "final")
    expected_count = final_layer.get("expected_count")
    if isinstance(expected_count, int):
        return expected_count
    return len(expected_evidence_from_report(report))


def layer_coverage(
    report: dict[str, Any],
    layer_name: str,
    enrichment_index: dict[tuple[str, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    layer = layer_payload(report, layer_name)
    matched = enrich_article_items(
        [item for item in layer.get("matched") or [] if isinstance(item, dict)],
        enrichment_index,
    )
    missing = enrich_article_items(
        [item for item in layer.get("missing") or [] if isinstance(item, dict)],
        enrichment_index,
    )
    expected_count = int(layer.get("expected_count") or (len(matched) + len(missing)))
    matched_count = int(layer.get("matched_count") or len(matched))
    coverage_ratio = matched_count / expected_count if expected_count else 1.0
    return {
        "layer": layer_name,
        "matched_count": matched_count,
        "expected_count": expected_count,
        "required_count": layer.get("required_count"),
        "coverage_ratio": round(coverage_ratio, 3),
        "satisfied": bool(layer.get("satisfied")) if "satisfied" in layer else matched_count >= expected_count,
        "missing": unique_articles(missing),
    }


def final_evidence(report: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = report.get("evidence") or report.get("evidence_chain") or []
    return [item for item in evidence if isinstance(item, dict)]


def final_expected(report: dict[str, Any]) -> list[dict[str, Any]]:
    final_layer = layer_payload(report, "final")
    expected = []
    for key in ("matched", "missing"):
        for item in final_layer.get(key) or []:
            if isinstance(item, dict):
                expected.append(item)
    return unique_articles(expected)


def evidence_coverage_against_expected(
    evidence_items: list[dict[str, Any]],
    expected_items: list[dict[str, Any]],
) -> dict[str, Any]:
    matched = []
    missing = []
    for expected in expected_items:
        if any(evidence_matches_expected(item, expected) for item in evidence_items):
            matched.append(expected)
        else:
            missing.append(expected)
    total = len(expected_items)
    ratio = len(matched) / total if total else 1.0
    return {
        "matched": len(matched),
        "expected": total,
        "coverage_ratio": round(ratio, 3),
        "missing": unique_articles(missing),
    }


def functional_type_coverage(evidence_items: list[dict[str, Any]]) -> dict[str, Any]:
    text_keys = ("content", "page_content", "text", "content_preview", "matched_content")
    metadata_keys = ("functional_type", "legal_functional_type", "functional_types")
    evaluable_items = [
        item
        for item in evidence_items
        if any(normalize_text(item.get(key)) for key in text_keys)
        or any(item.get(key) for key in metadata_keys)
    ]
    counts = Counter(classify_evidence_function(item).functional_type for item in evidence_items)
    present_types = set(counts)
    return {
        "evaluable": bool(evaluable_items),
        "evaluable_items": len(evaluable_items),
        "total_items": len(evidence_items),
        "not_evaluable_reason": "" if evaluable_items else "evidence items lack text content or functional_type metadata",
        "counts": dict(sorted(counts.items())),
        "has_operative_support": has_operative_support(present_types),
        "has_definition": bool(counts.get("definition")),
        "has_any_functional_signal": bool(present_types - {"unclassified", "unrelated_or_contextual"}),
        "operative_support_types_present": sorted(present_types & OPERATIVE_TYPES),
    }


def enrichment_coverage(items: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(normalize_text(item.get("enrichment_status") or "unknown") for item in items)
    total = len(items)
    matched = status_counts.get("matched", 0)
    return {
        "total_items": total,
        "matched_items": matched,
        "matched_ratio": round(matched / total, 3) if total else 1.0,
        "status_counts": dict(sorted(status_counts.items())),
    }


def scenario_core_articles(scenario: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not scenario:
        return []
    return [item for item in scenario.get("core_articles") or [] if isinstance(item, dict)]


def coverage_status(issues: list[str]) -> str:
    return COVERAGE_REVIEW if issues else COVERAGE_OK


def evaluate_case(
    report: dict[str, Any],
    scenario: dict[str, Any] | None = None,
    enrichment_index: dict[tuple[str, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    case_id = normalize_text(report.get("id") or report.get("case_id") or "unknown_case")
    evidence_items = enrich_article_items(final_evidence(report), enrichment_index)
    expected_domains = infer_expected_domains(report, scenario)
    final_expected_items = enrich_article_items(final_expected(report), enrichment_index)
    scenario_expected_items = enrich_article_items(scenario_core_articles(scenario), enrichment_index)
    layer_coverages = {
        layer: layer_coverage(report, layer, enrichment_index)
        for layer in DIAGNOSTIC_LAYERS
    }
    final_layer = layer_coverages["final"]

    final_evidence_coverage = evidence_coverage_against_expected(evidence_items, final_expected_items)
    scenario_core_coverage = evidence_coverage_against_expected(evidence_items, scenario_expected_items)
    function_coverage = functional_type_coverage(evidence_items)

    issues: list[str] = []
    review_reasons: list[str] = []

    if final_evidence_coverage["expected"] and final_evidence_coverage["coverage_ratio"] < 1.0:
        issues.append(ISSUE_FINAL_PRIMARY_GAP)
        review_reasons.append("Final evidence_chain does not cover all final expected statutes.")
    if scenario_core_coverage["expected"] and scenario_core_coverage["coverage_ratio"] < 1.0:
        issues.append(ISSUE_SCENARIO_CORE_GAP)
        review_reasons.append("Final evidence_chain does not cover all scenario core articles.")
    if evidence_items and function_coverage["evaluable"] and not function_coverage["has_operative_support"]:
        issues.append(ISSUE_OPERATIVE_SUPPORT_GAP)
        review_reasons.append("Final evidence_chain lacks operative, procedural, liability, rights, or technical support.")
    if evidence_items and function_coverage["evaluable"] and not function_coverage["has_any_functional_signal"]:
        issues.append(ISSUE_FUNCTIONAL_TYPE_GAP)
        review_reasons.append("Final evidence_chain has no classified legal functional signal beyond fallback/context.")
    if layer_coverages["anchor"]["coverage_ratio"] > layer_coverages["union"]["coverage_ratio"]:
        issues.append(ISSUE_ANCHOR_DEPENDENT_COVERAGE)
        review_reasons.append("Expected coverage improves only after anchor layer; review retrieval coverage dependency.")
    if layer_coverages["rerank_input"]["coverage_ratio"] > final_layer["coverage_ratio"]:
        issues.append(ISSUE_LAYER_COVERAGE_REGRESSION)
        review_reasons.append("Coverage decreases from rerank_input to final evidence.")
    if final_layer["expected_count"] and final_layer["coverage_ratio"] < 0.75:
        issues.append(ISSUE_LOW_FINAL_COVERAGE)
        review_reasons.append("Final layer covers less than 75% of expected statutes.")

    issues = list(dict.fromkeys(issues))
    review_reasons = list(dict.fromkeys(review_reasons))

    evidence_domains = sorted({
        domain
        for domain in (
            source_domain(normalize_text(item.get("source") or item.get("law_name")), item.get("category"))
            for item in evidence_items
        )
        if domain
    })

    return {
        "case_id": case_id,
        "report_source": report.get("_report_source", "unknown"),
        "coverage_status": coverage_status(issues),
        "detected_issues": issues,
        "review_reasons": review_reasons,
        "expected_domains": sorted(expected_domains),
        "evidence_domains": evidence_domains,
        "risk_level": report.get("risk_level"),
        "layer_coverage": layer_coverages,
        "final_evidence_coverage": final_evidence_coverage,
        "scenario_core_coverage": scenario_core_coverage,
        "functional_type_coverage": function_coverage,
        "enrichment_coverage": enrichment_coverage(evidence_items),
        "final_evidence": unique_articles(evidence_items),
    }


def build_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counts = Counter()
    domain_summary: dict[str, Counter] = defaultdict(Counter)
    layer_totals: dict[str, Counter] = defaultdict(Counter)
    enrichment_totals: Counter = Counter()
    high_priority_review = []

    for result in case_results:
        for issue in result["detected_issues"]:
            issue_counts[issue] += 1
        for domain in result.get("expected_domains") or ["unknown"]:
            domain_summary[domain]["total"] += 1
            if result["coverage_status"] == COVERAGE_REVIEW:
                domain_summary[domain]["review"] += 1
        for layer, coverage in result["layer_coverage"].items():
            layer_totals[layer]["matched"] += int(coverage.get("matched_count") or 0)
            layer_totals[layer]["expected"] += int(coverage.get("expected_count") or 0)
        for status, count in (result.get("enrichment_coverage", {}).get("status_counts") or {}).items():
            enrichment_totals[status] += int(count)
        if result["coverage_status"] == COVERAGE_REVIEW and (
            result.get("risk_level") == "high"
            or ISSUE_SCENARIO_CORE_GAP in result["detected_issues"]
            or ISSUE_FINAL_PRIMARY_GAP in result["detected_issues"]
        ):
            high_priority_review.append({
                "case_id": result["case_id"],
                "risk_level": result.get("risk_level"),
                "detected_issues": result["detected_issues"],
                "review_reasons": result["review_reasons"],
            })

    layer_summary = {}
    for layer, counts in sorted(layer_totals.items()):
        expected = counts["expected"]
        layer_summary[layer] = {
            "matched": counts["matched"],
            "expected": expected,
            "coverage_ratio": round(counts["matched"] / expected, 3) if expected else 1.0,
        }

    return {
        "total_cases": len(case_results),
        "ok_cases": sum(1 for result in case_results if result["coverage_status"] == COVERAGE_OK),
        "review_cases": sum(1 for result in case_results if result["coverage_status"] == COVERAGE_REVIEW),
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "per_domain_summary": {
            domain: dict(counts)
            for domain, counts in sorted(domain_summary.items())
        },
        "layer_summary": layer_summary,
        "enrichment_summary": {
            "total_items": sum(enrichment_totals.values()),
            "matched_items": enrichment_totals.get("matched", 0),
            "matched_ratio": round(enrichment_totals.get("matched", 0) / sum(enrichment_totals.values()), 3)
            if enrichment_totals else 1.0,
            "status_counts": dict(sorted(enrichment_totals.items())),
        },
        "high_priority_manual_review": high_priority_review,
    }


def build_coverage_report(
    rag_report_path: Path = DEFAULT_RAG_REPORT_PATH,
    hidden_report_path: Path = DEFAULT_HIDDEN_REPORT_PATH,
    scenario_registry_path: Path = DEFAULT_SCENARIO_REGISTRY_PATH,
    knowledge_manifest_path: Path | None = DEFAULT_KNOWLEDGE_MANIFEST_PATH,
    functional_type_config_path: Path = DEFAULT_FUNCTIONAL_TYPE_CONFIG_PATH,
) -> dict[str, Any]:
    scenario_by_case = load_scenario_metadata(scenario_registry_path)
    enrichment_index = None
    enrichment_index_summary = {"enabled": False}
    if knowledge_manifest_path is not None:
        enrichment_index, enrichment_index_summary = build_evidence_enrichment_index(
            knowledge_manifest_path,
            functional_type_config_path,
        )
    reports = read_reports(rag_report_path, "rag_eval_report")
    hidden_reports = read_reports(hidden_report_path, "hidden_eval_report")
    skipped_inputs = []
    if not hidden_report_path.exists():
        skipped_inputs.append(str(hidden_report_path))
    reports.extend(hidden_reports)
    case_results = [
        evaluate_case(
            report,
            scenario_by_case.get(normalize_text(report.get("id") or report.get("case_id"))),
            enrichment_index,
        )
        for report in reports
    ]
    return {
        "version": REPORT_VERSION,
        "scope": "offline evidence coverage diagnostics",
        "inputs": {
            "rag_report": str(rag_report_path),
            "hidden_report": str(hidden_report_path),
            "scenario_registry": str(scenario_registry_path),
            "knowledge_manifest": str(knowledge_manifest_path) if knowledge_manifest_path else "",
            "functional_type_config": str(functional_type_config_path),
            "skipped_inputs": skipped_inputs,
        },
        "enrichment_index": enrichment_index_summary,
        "summary": build_summary(case_results),
        "cases": case_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check saved RAG reports for evidence coverage diagnostics.")
    parser.add_argument("--rag-report", type=Path, default=DEFAULT_RAG_REPORT_PATH)
    parser.add_argument("--hidden-report", type=Path, default=DEFAULT_HIDDEN_REPORT_PATH)
    parser.add_argument("--scenario-registry", type=Path, default=DEFAULT_SCENARIO_REGISTRY_PATH)
    parser.add_argument("--knowledge-manifest", type=Path, default=DEFAULT_KNOWLEDGE_MANIFEST_PATH)
    parser.add_argument("--functional-type-config", type=Path, default=DEFAULT_FUNCTIONAL_TYPE_CONFIG_PATH)
    parser.add_argument("--no-enrichment", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_coverage_report(
        rag_report_path=args.rag_report,
        hidden_report_path=args.hidden_report,
        scenario_registry_path=args.scenario_registry,
        knowledge_manifest_path=None if args.no_enrichment else args.knowledge_manifest,
        functional_type_config_path=args.functional_type_config,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Evidence coverage check completed: "
        f"{summary['total_cases']} cases, {summary['review_cases']} review, "
        f"{summary['ok_cases']} ok"
    )
    if report["inputs"]["skipped_inputs"]:
        print(f"Skipped optional inputs: {', '.join(report['inputs']['skipped_inputs'])}")
    if args.fail_on_review and summary["review_cases"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
