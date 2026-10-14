"""Build a saved-report-only expected-level review packet for RAG repeat failures.

The tool reads a repeat eval report and existing eval-case metadata. It
classifies persistent failures without running eval, calling rag_query, touching
Qdrant/LLM, or mutating runtime rules, anchors, prompts, or eval cases.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.17.4"

DEFAULT_REPEAT_REPORT_PATH = Path("tests/targeted_rag_evidence_independence_v0.4.17.3_report.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/rag_expected_level_review_packet_v0.4.17.4_report.json")

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
    "taxonomy_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

NON_GROUNDING_CHECKS = {"expected_risk_level"}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def case_map(cases_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("id")): case
        for case in as_list(cases_payload.get("cases"))
        if isinstance(case, dict) and case.get("id")
    }


def check_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(check.get("name")): check
        for check in as_list(report.get("checks"))
        if isinstance(check, dict) and check.get("name")
    }


def failed_checks(report: dict[str, Any]) -> list[str]:
    return [
        str(check.get("name"))
        for check in as_list(report.get("checks"))
        if isinstance(check, dict) and check.get("passed") is False
    ]


def risk_level_details(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(as_dict(check_map(report).get("expected_risk_level")).get("details"))


def expected_refs(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"source": item.get("source"), "article_no": item.get("article_no")}
        for item in as_list(case.get("expected_evidence"))
        if isinstance(item, dict)
    ]


def final_refs(report: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for item in as_list(report.get("evidence")):
        if not isinstance(item, dict):
            continue
        refs.append({
            "source": item.get("source") or item.get("law_name"),
            "article_no": item.get("article_no"),
            "citation": item.get("citation"),
            "rerank_score": item.get("rerank_score"),
        })
    return refs


def layer_status(report: dict[str, Any]) -> dict[str, Any]:
    layers = as_dict(as_dict(report.get("retrieval_diagnostics")).get("layers"))
    return {
        name: {
            "satisfied": as_dict(payload).get("satisfied"),
            "matched_count": as_dict(payload).get("matched_count"),
            "expected_count": as_dict(payload).get("expected_count"),
        }
        for name, payload in layers.items()
        if isinstance(payload, dict)
    }


def grounding_checks_all_pass(report: dict[str, Any]) -> bool:
    for check in as_list(report.get("checks")):
        if not isinstance(check, dict):
            continue
        name = str(check.get("name"))
        if name in NON_GROUNDING_CHECKS:
            continue
        if check.get("passed") is False:
            return False
    return True


def article_numbers_from_reasoning(text: str) -> list[int]:
    numbers: list[int] = []
    for match in re.finditer(r"第\s*(\d+)\s*条", text or ""):
        numbers.append(int(match.group(1)))
    return numbers


def metadata_warnings(case: dict[str, Any]) -> list[str]:
    expected_numbers = {
        int(ref["article_no"])
        for ref in expected_refs(case)
        if isinstance(ref.get("article_no"), int)
    }
    reasoning_numbers = set(article_numbers_from_reasoning(str(case.get("legal_reasoning") or "")))
    warnings = []
    if reasoning_numbers and expected_numbers and not reasoning_numbers.issubset(expected_numbers):
        warnings.append("legal_reasoning_article_ref_not_subset_of_expected_evidence")
    return warnings


def classify_case(case_id: str, reports: list[dict[str, Any]], case: dict[str, Any]) -> dict[str, Any]:
    pass_by_run = [bool(report.get("passed")) for report in reports]
    retrieval_stages = [str(report.get("retrieval_failure_stage") or "") for report in reports]
    failed_by_run = [failed_checks(report) for report in reports]
    risk_details_by_run = [risk_level_details(report) for report in reports]
    all_retrieval_pass = all(stage == "PASS" for stage in retrieval_stages)
    only_risk_level_failed = all(set(failed) == {"expected_risk_level"} for failed in failed_by_run)
    all_grounding_pass = all(grounding_checks_all_pass(report) for report in reports)
    mismatch_types = {str(details.get("mismatch_type") or "") for details in risk_details_by_run if details}

    if not all_retrieval_pass:
        review_classification = "retrieval_or_evidence_chain_review"
        recommended_next_step = "inspect_retrieval_or_evidence_before_any_level_change"
    elif only_risk_level_failed and all_grounding_pass:
        review_classification = "expected_level_fact_strength_review"
        recommended_next_step = "manual_review_expected_level_or_fact_strength_before_runtime_patch"
    else:
        review_classification = "output_or_eval_contract_review"
        recommended_next_step = "inspect_failed_checks_before_runtime_patch"

    first = reports[0] if reports else {}
    return {
        "case_id": case_id,
        "review_classification": review_classification,
        "recommended_next_step": recommended_next_step,
        "runtime_patch_allowed": False,
        "eval_case_change_allowed": False,
        "anchor_change_allowed": False,
        "pass_by_run": pass_by_run,
        "retrieval_failure_stages": retrieval_stages,
        "failed_checks_by_run": failed_by_run,
        "risk_level_details_by_run": risk_details_by_run,
        "risk_level_mismatch_types": sorted(mismatch_types),
        "all_retrieval_pass": all_retrieval_pass,
        "all_non_level_checks_pass": all_grounding_pass,
        "question": first.get("question") or case.get("question"),
        "answer_samples": [str(report.get("answer") or "") for report in reports[:3]],
        "expected_case_metadata": {
            "expected_risk_level": case.get("expected_risk_level"),
            "risk_level_reason": case.get("risk_level_reason"),
            "legal_reasoning": case.get("legal_reasoning"),
            "expected_evidence": expected_refs(case),
            "expected_risk_types": as_list(case.get("expected_risk_types")),
            "expected_actions": as_list(case.get("expected_actions")),
        },
        "final_evidence_refs_by_run": [final_refs(report) for report in reports],
        "retrieval_layers_by_run": [layer_status(report) for report in reports],
        "metadata_warnings": metadata_warnings(case),
        "review_reasons": [
            "All retrieval layers and expected evidence checks passed in the saved repeat report."
            if all_retrieval_pass and all_grounding_pass
            else "At least one retrieval or non-level check needs inspection before classification.",
            "The persistent failure is expected_risk_level only." if only_risk_level_failed else "Failures include checks beyond expected_risk_level.",
            "This packet does not authorize runtime, anchor, prompt, rule, or eval-case changes.",
        ],
    }


def collect_reports_by_case(repeat_report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    reports_by_case: dict[str, list[dict[str, Any]]] = {}
    for run in as_list(repeat_report.get("runs")):
        if not isinstance(run, dict):
            continue
        for report in as_list(run.get("reports")):
            if not isinstance(report, dict):
                continue
            case_id = str(report.get("id") or "")
            if case_id:
                reports_by_case.setdefault(case_id, []).append(report)
    return reports_by_case


def build_report(
    repeat_report_path: Path = DEFAULT_REPEAT_REPORT_PATH,
    cases_path: Path = DEFAULT_CASES_PATH,
) -> dict[str, Any]:
    repeat_report = load_json(repeat_report_path)
    cases_payload = load_json(cases_path)
    cases_by_id = case_map(cases_payload)
    reports_by_case = collect_reports_by_case(repeat_report)

    failed_case_ids = sorted(
        case_id
        for case_id, reports in reports_by_case.items()
        if any(report.get("passed") is False for report in reports)
    )
    rows = [
        classify_case(case_id, reports_by_case[case_id], cases_by_id.get(case_id, {}))
        for case_id in failed_case_ids
    ]

    classification_counts = Counter(str(row["review_classification"]) for row in rows)
    metadata_warning_counts = Counter(
        warning
        for row in rows
        for warning in as_list(row.get("metadata_warnings"))
    )
    status = "expected_level_review_packet_ready" if rows else "no_persistent_failures"
    if any(row["review_classification"] == "retrieval_or_evidence_chain_review" for row in rows):
        status = "retrieval_review_required"

    return {
        "version": VERSION,
        "schema_kind": "rag_expected_level_review_packet",
        "scope": "saved-report-only classification for persistent targeted-repeat failures",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "repeat_report": str(repeat_report_path),
            "cases": str(cases_path),
            "repeat": repeat_report.get("repeat"),
            "stability_summary": as_dict(repeat_report.get("stability_summary")),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "persistent_failed_case_count": len(rows),
            "persistent_failed_case_ids": failed_case_ids,
            "review_classification_counts": dict(sorted(classification_counts.items())),
            "metadata_warning_counts": dict(sorted(metadata_warning_counts.items())),
            "runtime_patch_recommendation": "not_recommended_by_this_packet",
            "eval_case_change_recommendation": "not_recommended_by_this_packet",
            "anchor_change_recommendation": "not_recommended_by_this_packet",
        },
        "case_rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-report-only expected-level review packet.")
    parser.add_argument("--repeat-report", type=Path, default=DEFAULT_REPEAT_REPORT_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repeat_report, args.cases)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "RAG expected-level review packet completed: "
        f"{summary['status']}, persistent_failed_case_count={summary['persistent_failed_case_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
