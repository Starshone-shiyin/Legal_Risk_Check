"""Judge Evidence Sufficiency Gate experiment reports.

The judge deliberately distinguishes a smoke run from a formal benchmark.  A
smoke run may retain diagnostic Recall@K fields produced by the experiment
runner, but those fields are explicitly *not* eligible for formal reporting
when its cases have no expected evidence.  A formal benchmark must provide an
expected-evidence count for every case before retrieval metrics are accepted.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


ESG_SUMMARY_FIELDS = {
    "case_count",
    "mean_score",
    "sufficient_rate",
    "web_supplement_rate",
    "human_review_rate",
    "local_primary_law_coverage",
}
ESG_CASE_FIELDS = {
    "status",
    "score",
    "recommended_route",
    "local_legal_evidence_count",
}
RETRIEVAL_METRIC_FIELDS = {
    "evidence_recall_at_k",
    "mrr_at_k",
    "ndcg_at_k",
    "multi_source_coverage",
}
VALID_STATUSES = {"sufficient", "review", "insufficient"}
VALID_ROUTES = {"answer_with_evidence", "web_supplement", "human_review"}
FORMAL_LABELS = {"formal", "full", "full_benchmark", "benchmark"}
SMOKE_LABELS = {"smoke", "diagnostic", "runtime_smoke"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _between_zero_and_one(value: Any) -> bool:
    return _is_number(value) and 0.0 <= float(value) <= 1.0


def _check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": passed, "detail": detail})


def _classify_benchmark(report: dict[str, Any]) -> tuple[str, str]:
    """Classify legacy reports without requiring a format migration."""
    declared = str(report.get("benchmark_kind") or report.get("benchmark_type") or "").strip().lower()
    if declared in SMOKE_LABELS:
        return "smoke", "declared"
    if declared in FORMAL_LABELS:
        return "formal", "declared"

    case_file = str(report.get("case_file") or "").lower()
    if "smoke" in Path(case_file).name:
        return "smoke", "case_file_name"

    profiles = report.get("profiles") or {}
    case_rows = [case for profile in profiles.values() if isinstance(profile, dict) for case in profile.get("cases") or []]
    if case_rows and any(
        isinstance(case.get("metrics"), dict) and _is_number(case["metrics"].get("expected_evidence"))
        and int(case["metrics"]["expected_evidence"]) > 0
        for case in case_rows
        if isinstance(case, dict)
    ):
        return "formal", "expected_evidence_present"
    return "unclassified", "insufficient_metadata"


def _expected_esg_summary(cases: list[dict[str, Any]]) -> dict[str, float | int]:
    reports = [case["evidence_sufficiency"] for case in cases]
    count = len(reports)
    return {
        "case_count": count,
        "mean_score": round(mean(float(item["score"]) for item in reports), 6),
        "sufficient_rate": round(sum(item["status"] == "sufficient" for item in reports) / count, 6),
        "web_supplement_rate": round(
            sum(item["recommended_route"] == "web_supplement" for item in reports) / count,
            6,
        ),
        "human_review_rate": round(
            sum(item["recommended_route"] == "human_review" for item in reports) / count,
            6,
        ),
        "local_primary_law_coverage": round(
            sum(int(item["local_legal_evidence_count"]) > 0 for item in reports) / count,
            6,
        ),
    }


def _same_value(actual: Any, expected: Any) -> bool:
    if isinstance(expected, int):
        return actual == expected
    return _is_number(actual) and abs(float(actual) - float(expected)) <= 0.000001


def _validate_esg_cases(cases: list[Any]) -> list[str]:
    errors: list[str] = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] is not an object")
            continue
        esg = case.get("evidence_sufficiency")
        if not isinstance(esg, dict):
            errors.append(f"case[{index}] missing evidence_sufficiency")
            continue
        missing = sorted(ESG_CASE_FIELDS - set(esg))
        if missing:
            errors.append(f"case[{index}] missing ESG fields: {', '.join(missing)}")
            continue
        if esg["status"] not in VALID_STATUSES:
            errors.append(f"case[{index}] has invalid ESG status")
        if esg["recommended_route"] not in VALID_ROUTES:
            errors.append(f"case[{index}] has invalid ESG route")
        if not _between_zero_and_one(esg["score"]):
            errors.append(f"case[{index}] ESG score is outside [0, 1]")
        count = esg["local_legal_evidence_count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append(f"case[{index}] local_legal_evidence_count is invalid")
    return errors


def _validate_formal_metrics(cases: list[Any]) -> list[str]:
    errors: list[str] = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict) or not isinstance(case.get("metrics"), dict):
            errors.append(f"case[{index}] missing metrics for formal benchmark")
            continue
        metrics = case["metrics"]
        expected = metrics.get("expected_evidence")
        if not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0:
            errors.append(f"case[{index}] formal Recall@K has no expected_evidence")
            continue
        matched = metrics.get("matched_evidence")
        if not isinstance(matched, int) or isinstance(matched, bool) or not 0 <= matched <= expected:
            errors.append(f"case[{index}] matched_evidence is inconsistent with expected_evidence")
        for field in RETRIEVAL_METRIC_FIELDS:
            if not _between_zero_and_one(metrics.get(field)):
                errors.append(f"case[{index}] {field} is outside [0, 1]")
    return errors


def judge(report: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, structured verdict without running RAG or an LLM."""
    checks: list[dict[str, Any]] = []
    notices: list[str] = []
    profile_results: dict[str, Any] = {}
    benchmark_kind, classification_basis = _classify_benchmark(report)
    profiles = report.get("profiles")

    _check(checks, "completed_run", report.get("status") == "completed", "status must be completed")
    _check(
        checks,
        "benchmark_classified",
        benchmark_kind in {"smoke", "formal"},
        f"classification={benchmark_kind}; basis={classification_basis}",
    )
    _check(
        checks,
        "frozen_case_set",
        isinstance(report.get("case_count"), int) and report["case_count"] > 0 and bool(report.get("case_file_sha256")),
        "case_count must be positive and case_file_sha256 must be present",
    )
    _check(checks, "profiles_present", isinstance(profiles, dict) and bool(profiles), "at least one profile is required")

    if isinstance(profiles, dict):
        for name, profile in profiles.items():
            profile_checks: list[dict[str, Any]] = []
            if not isinstance(profile, dict):
                _check(profile_checks, "profile_object", False, "profile must be an object")
                profile_results[str(name)] = {"checks": profile_checks}
                continue
            cases = profile.get("cases")
            case_list = cases if isinstance(cases, list) else []
            _check(
                profile_checks,
                "case_count_matches_report",
                isinstance(cases, list) and len(case_list) == report.get("case_count"),
                f"profile_cases={len(case_list)}; report_case_count={report.get('case_count')}",
            )

            esg_errors = _validate_esg_cases(case_list)
            _check(profile_checks, "esg_case_fields_valid", not esg_errors, "; ".join(esg_errors) or "all case ESG fields valid")
            esg_summary = profile.get("evidence_sufficiency_summary")
            missing_esg_fields = sorted(ESG_SUMMARY_FIELDS - set(esg_summary or {})) if isinstance(esg_summary, dict) else sorted(ESG_SUMMARY_FIELDS)
            _check(
                profile_checks,
                "esg_summary_complete",
                not missing_esg_fields,
                ", ".join(missing_esg_fields) if missing_esg_fields else "all required fields present",
            )
            if not esg_errors and not missing_esg_fields:
                expected_summary = _expected_esg_summary(case_list)
                mismatches = [
                    field for field, expected in expected_summary.items() if not _same_value(esg_summary.get(field), expected)
                ]
                _check(
                    profile_checks,
                    "esg_summary_consistent",
                    not mismatches,
                    ", ".join(mismatches) if mismatches else "summary recomputes from case ESG records",
                )
            else:
                _check(profile_checks, "esg_summary_consistent", False, "cannot recompute from incomplete ESG data")

            if benchmark_kind == "formal":
                metric_errors = _validate_formal_metrics(case_list)
                _check(
                    profile_checks,
                    "formal_recall_has_expected_evidence",
                    not metric_errors,
                    "; ".join(metric_errors) or "all formal cases include expected_evidence",
                )
            elif benchmark_kind == "smoke":
                zero_expected = sum(
                    1
                    for case in case_list
                    if isinstance(case, dict)
                    and isinstance(case.get("metrics"), dict)
                    and (
                        not isinstance(case["metrics"].get("expected_evidence"), int)
                        or isinstance(case["metrics"].get("expected_evidence"), bool)
                        or case["metrics"].get("expected_evidence") == 0
                    )
                )
                notices.append(
                    f"{name}: smoke report has {zero_expected}/{len(case_list)} cases without expected_evidence; "
                    "Recall@K/MRR/nDCG/multi-source coverage are diagnostic only and must not be reported as formal metrics."
                )
            profile_results[str(name)] = {"checks": profile_checks}

    all_checks = [*checks, *(check for profile in profile_results.values() for check in profile.get("checks", []))]
    accepted = bool(all_checks) and all(check["passed"] for check in all_checks)
    return {
        "schema_version": "evidence-sufficiency-judge-v1",
        "report_type": "evidence_sufficiency_experiment_judgment",
        "verdict": "accepted" if accepted else "needs_revision",
        "benchmark": {
            "kind": benchmark_kind,
            "classification_basis": classification_basis,
            "formal_retrieval_metrics_eligible": benchmark_kind == "formal" and accepted,
            "smoke_metrics_policy": "diagnostic_only" if benchmark_kind == "smoke" else "not_applicable",
        },
        "checks": checks,
        "profiles": profile_results,
        "notices": notices,
        "case_file": report.get("case_file"),
        "case_file_sha256": report.get("case_file_sha256"),
        "case_count": report.get("case_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to a RAG ESG experiment JSON report")
    parser.add_argument("--output", type=Path, help="Path for the structured judgment JSON")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = judge(report)
    output = args.output or args.report.with_name("judge_evidence_sufficiency_report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
