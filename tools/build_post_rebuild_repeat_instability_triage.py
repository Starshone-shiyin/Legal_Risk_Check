"""Build v0.4.15.1 targeted repeat instability triage from saved reports.

The targeted repeat reports are produced by run_rag_eval, but this builder is
saved-report-only. It does not run eval, call rag_query, contact Qdrant or an
LLM, or mutate runtime configuration.
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

from tools.build_post_rebuild_repeat_stability_summary import (
    answer_digest,
    answer_excerpt,
    as_dict,
    as_list,
    case_metadata,
    evidence_keys,
    failed_check_names,
    load_json,
    reports_by_id,
    write_json,
    write_text,
)


VERSION = "0.4.15.1"

DEFAULT_PRODUCT_REPEAT_PATH = Path("tests/targeted_repeat_product_liability_v0.4.15.1_report.json")
DEFAULT_ALGORITHM_REPEAT_PATH = Path("tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json")
DEFAULT_PREVIOUS_REPEAT_PATH = Path("tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json")
DEFAULT_PREVIOUS_SUMMARY_PATH = Path("tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json")
DEFAULT_BASELINE_PATH = Path("tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md")

TARGETED_CASES = {
    "risk_tort_product_liability_001": {
        "input_key": "product_liability_targeted_repeat",
        "reason": "v0.4.15.0 repeat showed answer keyword pass/fail instability with stable final evidence.",
        "previous_signal": "answer_or_check_instability_with_stable_retrieval",
    },
    "risk_algorithm_bias_001": {
        "input_key": "algorithm_bias_targeted_repeat",
        "reason": "v0.4.15.0 repeat showed final evidence identity drift while the case still passed.",
        "previous_signal": "final_evidence_identity_drift",
    },
}

GUARDRAILS = {
    "saved_reports_only": True,
    "targeted_repeat_was_previously_run": True,
    "runs_eval": "disallowed_by_builder",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def run_rows(repeat_report: dict[str, Any], case_id: str) -> list[dict[str, Any]]:
    rows = []
    for run in as_list(repeat_report.get("runs")):
        if not isinstance(run, dict):
            continue
        row = reports_by_id(run).get(case_id)
        if isinstance(row, dict):
            rows.append({"run": run.get("run"), "row": row})
    return rows


def stable(values: list[Any]) -> bool:
    normalized = [json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values]
    return len(set(normalized)) <= 1


def case_repeat_summary(repeat_report: dict[str, Any], case_id: str, metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = run_rows(repeat_report, case_id)
    pass_by_run = [item["row"].get("passed") for item in rows]
    stage_by_run = [item["row"].get("retrieval_failure_stage") for item in rows]
    failed_checks_by_run = [failed_check_names(item["row"]) for item in rows]
    labels_by_run = [as_list(item["row"].get("contribution_labels")) for item in rows]
    evidence_by_run = [evidence_keys(item["row"]) for item in rows]
    answer_digest_by_run = [answer_digest(item["row"]) for item in rows]
    answer_excerpt_by_run = [answer_excerpt(item["row"], limit=160) for item in rows]

    pass_stable = stable(pass_by_run)
    stage_stable = stable(stage_by_run)
    failed_checks_stable = stable(failed_checks_by_run)
    labels_stable = stable(labels_by_run)
    evidence_stable = stable(evidence_by_run)
    answer_stable = stable(answer_digest_by_run)
    all_passed = bool(pass_by_run) and all(value is True for value in pass_by_run)

    if not evidence_stable:
        classification = "final_evidence_identity_drift_reproduced"
        blocking = True
        triage_reason = "Final evidence identity changed across targeted repeat runs; this remains a grounding stability issue even though all targeted runs passed."
    elif not all_passed or not failed_checks_stable:
        classification = "answer_or_check_instability_reproduced"
        blocking = True
        triage_reason = "Targeted repeat reproduced pass/fail or failed-check instability."
    elif not answer_stable:
        classification = "output_wording_variation_without_current_check_failure"
        blocking = False
        triage_reason = "Answer wording varied across targeted repeat runs, but checks, retrieval stage and final evidence stayed stable."
    elif not labels_stable:
        classification = "label_variation_only"
        blocking = False
        triage_reason = "Contribution labels varied without pass, check, stage or evidence drift."
    else:
        classification = "targeted_repeat_stable"
        blocking = False
        triage_reason = "Targeted repeat did not reproduce instability."

    return {
        "id": case_id,
        "question": metadata.get(case_id, {}).get("question"),
        "previous_signal": TARGETED_CASES.get(case_id, {}).get("previous_signal"),
        "targeted_repeat_runs": len(rows),
        "all_targeted_runs_passed": all_passed,
        "pass_by_run": pass_by_run,
        "retrieval_stage_by_run": stage_by_run,
        "failed_checks_by_run": failed_checks_by_run,
        "contribution_labels_by_run": labels_by_run,
        "evidence_keys_by_run": evidence_by_run,
        "answer_digest_by_run": answer_digest_by_run,
        "answer_excerpt_by_run": answer_excerpt_by_run,
        "stability_flags": {
            "pass_stable": pass_stable,
            "retrieval_stage_stable": stage_stable,
            "failed_checks_stable": failed_checks_stable,
            "contribution_labels_stable": labels_stable,
            "final_evidence_identity_stable": evidence_stable,
            "answer_text_stable": answer_stable,
        },
        "classification": classification,
        "blocking": blocking,
        "triage_reason": triage_reason,
    }


def targeted_repeat_summary(name: str, path: Path, report: dict[str, Any]) -> dict[str, Any]:
    stability_summary = as_dict(report.get("stability_summary"))
    return {
        "name": name,
        "path": str(path),
        "repeat": report.get("repeat"),
        "pass_counts": stability_summary.get("pass_counts"),
        "total_counts": stability_summary.get("total_counts"),
        "all_runs_full_pass": stability_summary.get("all_runs_full_pass"),
        "unstable_case_count": len(as_list(stability_summary.get("unstable_cases"))),
        "label_variation_case_count": len(as_list(stability_summary.get("label_variation_cases"))),
    }


def build_report(
    product_repeat_path: Path = DEFAULT_PRODUCT_REPEAT_PATH,
    algorithm_repeat_path: Path = DEFAULT_ALGORITHM_REPEAT_PATH,
    previous_repeat_path: Path = DEFAULT_PREVIOUS_REPEAT_PATH,
    previous_summary_path: Path = DEFAULT_PREVIOUS_SUMMARY_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    cases_path: Path = DEFAULT_CASES_PATH,
) -> dict[str, Any]:
    product_repeat = load_json(product_repeat_path)
    algorithm_repeat = load_json(algorithm_repeat_path)
    previous_repeat = load_json(previous_repeat_path)
    previous_summary = load_json(previous_summary_path)
    baseline = load_json(baseline_path)
    cases = load_json(cases_path, required=False)
    metadata = case_metadata(cases)

    reports_by_input = {
        "product_liability_targeted_repeat": product_repeat,
        "algorithm_bias_targeted_repeat": algorithm_repeat,
    }
    case_triage = []
    for case_id, target in TARGETED_CASES.items():
        case_triage.append(case_repeat_summary(reports_by_input[target["input_key"]], case_id, metadata))

    blockers = []
    if any(item["blocking"] for item in case_triage):
        blockers.append("targeted_blocking_instability_present")
    if any(item["classification"] == "final_evidence_identity_drift_reproduced" for item in case_triage):
        blockers.append("targeted_final_evidence_identity_drift_reproduced")
    if any(item["classification"] == "answer_or_check_instability_reproduced" for item in case_triage):
        blockers.append("targeted_answer_or_check_instability_reproduced")

    issue_type_summary = Counter(item["classification"] for item in case_triage)
    status = "needs_evidence_stability_triage" if blockers else "targeted_instability_not_blocking"

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_repeat_instability_triage",
        "scope": "targeted triage for v0.4.15.0 repeat instability signals",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "product_liability_targeted_repeat": str(product_repeat_path),
            "algorithm_bias_targeted_repeat": str(algorithm_repeat_path),
            "previous_repeat_report": str(previous_repeat_path),
            "previous_stability_summary": str(previous_summary_path),
            "baseline_report": str(baseline_path),
            "cases": str(cases_path),
        },
        "guardrails": GUARDRAILS,
        "targeted_scope": [
            {"id": case_id, **details}
            for case_id, details in TARGETED_CASES.items()
        ],
        "source_context": {
            "previous_repeat_pass_counts": as_dict(previous_repeat.get("stability_summary")).get("pass_counts"),
            "previous_summary_status": as_dict(previous_summary.get("summary")).get("status"),
            "previous_summary_blockers": as_dict(previous_summary.get("summary")).get("blockers"),
            "baseline_passed": baseline.get("passed"),
            "baseline_total": baseline.get("total"),
        },
        "targeted_repeat_summaries": [
            targeted_repeat_summary("product_liability", product_repeat_path, product_repeat),
            targeted_repeat_summary("algorithm_bias", algorithm_repeat_path, algorithm_repeat),
        ],
        "case_triage": case_triage,
        "issue_type_summary": dict(sorted(issue_type_summary.items())),
        "summary": {
            "status": status,
            "blockers": sorted(set(blockers)),
            "recommended_next_step": (
                "triage_final_evidence_identity_drift_before_runtime_change"
                if blockers
                else "keep_observing_repeat_output_variation"
            ),
            "runtime_fix_authorized": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.15.1 Post-Rebuild Repeat Instability Triage",
        "",
        "## Conclusion",
        "",
        f"- status: `{summary.get('status')}`",
        f"- blockers: `{summary.get('blockers')}`",
        f"- recommended next step: `{summary.get('recommended_next_step')}`",
        f"- runtime fix authorized: `{summary.get('runtime_fix_authorized')}`",
        "",
        "## Targeted Results",
        "",
    ]
    for item in as_list(report.get("case_triage")):
        lines.extend([
            f"- `{item.get('id')}`",
            f"  - previous signal: `{item.get('previous_signal')}`",
            f"  - classification: `{item.get('classification')}`",
            f"  - all targeted runs passed: `{item.get('all_targeted_runs_passed')}`",
            f"  - pass by run: `{item.get('pass_by_run')}`",
            f"  - final evidence stable: `{as_dict(item.get('stability_flags')).get('final_evidence_identity_stable')}`",
            f"  - answer text stable: `{as_dict(item.get('stability_flags')).get('answer_text_stable')}`",
            f"  - triage reason: {item.get('triage_reason')}",
        ])
    lines.extend([
        "",
        "## Boundary",
        "",
        "This is saved-report triage. It is not a new gate chain, not a sample patch, and not a runtime fix authorization.",
        "It does not modify hidden seeds, anchors, rerank, prompt, risk supplement, term preservation, scenario registry, fixtures, eval cases, or Qdrant.",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v0.4.15.1 targeted repeat instability triage.")
    parser.add_argument("--product-repeat", type=Path, default=DEFAULT_PRODUCT_REPEAT_PATH)
    parser.add_argument("--algorithm-repeat", type=Path, default=DEFAULT_ALGORITHM_REPEAT_PATH)
    parser.add_argument("--previous-repeat", type=Path, default=DEFAULT_PREVIOUS_REPEAT_PATH)
    parser.add_argument("--previous-summary", type=Path, default=DEFAULT_PREVIOUS_SUMMARY_PATH)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        product_repeat_path=args.product_repeat,
        algorithm_repeat_path=args.algorithm_repeat,
        previous_repeat_path=args.previous_repeat,
        previous_summary_path=args.previous_summary,
        baseline_path=args.baseline,
        cases_path=args.cases,
    )
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild repeat instability triage completed: "
        f"{report['summary']['status']}, blockers={report['summary']['blockers']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
