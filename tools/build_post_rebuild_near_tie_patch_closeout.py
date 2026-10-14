"""Build the v0.4.15.7 near-tie runtime patch closeout report.

This helper reads saved v0.4.15.6 validation artifacts and the latest project
health report. It does not run eval, call rag_query, contact Qdrant or an LLM,
or mutate runtime retrieval behavior, anchors, prompts, risk rules, eval cases,
hidden seeds, fixtures, rerank scores, score_epsilon, or top_k.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


VERSION = "0.4.15.7"

DEFAULT_TARGETED_REPEAT_PATH = Path(
    "tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json"
)
DEFAULT_PATCH_VALIDATION_PATH = Path(
    "tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json"
)
DEFAULT_PROJECT_HEALTH_PATH = Path("tests/project_health_check_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md")

EXPECTED_RUNTIME_PATCH_SCOPE = "same_bucket_deterministic_ordering_only"

GUARDRAILS = {
    "saved_reports_only": True,
    "closeout_only": True,
    "runtime_patch": "disallowed",
    "runs_eval": "disallowed_by_builder",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_score_mutation": "disallowed",
    "score_epsilon_mutation": "disallowed",
    "top_k_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "fixture_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_optional_json(path: Path) -> tuple[dict[str, Any], bool]:
    if not path.exists():
        return {}, False
    return load_json(path), True


def summarize_targeted_repeat(report: dict[str, Any]) -> dict[str, Any]:
    stability = as_dict(report.get("stability_summary"))
    runs = as_list(report.get("runs"))
    case_ids: set[str] = set()
    for run in runs:
        for case_report in as_list(as_dict(run).get("reports")):
            case_id = as_dict(case_report).get("id")
            if case_id:
                case_ids.add(str(case_id))
    return {
        "repeat_runs": len(runs),
        "all_runs_full_pass": stability.get("all_runs_full_pass") is True,
        "pass_counts": as_list(stability.get("pass_counts")),
        "total_counts": as_list(stability.get("total_counts")),
        "unstable_cases": as_list(stability.get("unstable_cases")),
        "case_ids": sorted(case_ids),
    }


def summarize_validation(report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "status": summary.get("status"),
        "blockers": as_list(summary.get("blockers")),
        "runtime_patch_authorized": summary.get("runtime_patch_authorized") is True,
        "runtime_patch_scope": summary.get("runtime_patch_scope"),
        "repeat_runs": summary.get("repeat_runs"),
        "case_run_count": summary.get("case_run_count"),
        "case_ids": as_list(summary.get("case_ids")),
        "unique_selected_evidence_chains": summary.get("unique_selected_evidence_chains"),
        "selected_evidence_identity_counts": as_dict(report.get("selected_evidence_identity_counts")),
    }


def summarize_health(report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "version": report.get("version"),
        "status": summary.get("status"),
        "total_checks": summary.get("total_checks"),
        "failed_checks": summary.get("failed_checks"),
        "failed": as_list(summary.get("failed")),
    }


def readable_evidence_chain(chain: str) -> str:
    articles: list[str] = []
    for item in chain.split(" -> "):
        if "|article:" in item:
            articles.append(item.rsplit("|article:", 1)[1])
    if articles == ["24", "48", "56"]:
        return "Personal Information Protection Law article 24 -> article 48 -> article 56"
    return chain


def build_checks(
    *,
    targeted_repeat_exists: bool,
    validation_exists: bool,
    health_exists: bool,
    targeted_repeat_summary: dict[str, Any],
    validation_summary: dict[str, Any],
    health_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = [
        {
            "name": "targeted_repeat_available",
            "passed": targeted_repeat_exists,
        },
        {
            "name": "targeted_repeat_all_runs_passed",
            "passed": targeted_repeat_summary.get("all_runs_full_pass") is True,
        },
        {
            "name": "patch_validation_available",
            "passed": validation_exists,
        },
        {
            "name": "patch_validation_passed",
            "passed": validation_summary.get("status") == "passed"
            and not validation_summary.get("blockers"),
        },
        {
            "name": "final_evidence_identity_stable",
            "passed": validation_summary.get("unique_selected_evidence_chains") == 1,
        },
        {
            "name": "runtime_patch_scope_is_same_bucket_only",
            "passed": validation_summary.get("runtime_patch_scope") == EXPECTED_RUNTIME_PATCH_SCOPE,
        },
        {
            "name": "project_health_available",
            "passed": health_exists,
        },
        {
            "name": "project_health_passed",
            "passed": health_summary.get("status") == "passed"
            and health_summary.get("failed_checks") == 0,
        },
    ]
    return checks


def build_report(
    targeted_repeat_path: Path = DEFAULT_TARGETED_REPEAT_PATH,
    patch_validation_path: Path = DEFAULT_PATCH_VALIDATION_PATH,
    project_health_path: Path = DEFAULT_PROJECT_HEALTH_PATH,
) -> dict[str, Any]:
    targeted_repeat, targeted_repeat_exists = read_optional_json(targeted_repeat_path)
    patch_validation, validation_exists = read_optional_json(patch_validation_path)
    project_health, health_exists = read_optional_json(project_health_path)

    targeted_repeat_summary = summarize_targeted_repeat(targeted_repeat)
    validation_summary = summarize_validation(patch_validation)
    health_summary = summarize_health(project_health)
    checks = build_checks(
        targeted_repeat_exists=targeted_repeat_exists,
        validation_exists=validation_exists,
        health_exists=health_exists,
        targeted_repeat_summary=targeted_repeat_summary,
        validation_summary=validation_summary,
        health_summary=health_summary,
    )
    blockers = [item["name"] for item in checks if not item["passed"]]
    status = "closed_for_next_real_rag_quality_task" if not blockers else "blocked"
    next_action = (
        "move_to_post_patch_regression_or_broader_rag_quality_work"
        if not blockers
        else "fix_or_regenerate_missing_saved_validation_inputs_before_any_runtime_work"
    )
    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_near_tie_patch_closeout",
        "scope": "saved-report closeout for the v0.4.15.6 same-bucket near-tie runtime patch",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "targeted_repeat_report": str(targeted_repeat_path),
            "targeted_repeat_report_exists": targeted_repeat_exists,
            "patch_validation_report": str(patch_validation_path),
            "patch_validation_report_exists": validation_exists,
            "project_health_report": str(project_health_path),
            "project_health_report_exists": health_exists,
        },
        "guardrails": GUARDRAILS,
        "targeted_repeat_summary": targeted_repeat_summary,
        "patch_validation_summary": validation_summary,
        "project_health_summary": health_summary,
        "checks": checks,
        "summary": {
            "status": status,
            "blockers": blockers,
            "runtime_patch_closed": not blockers,
            "runtime_patch_scope": EXPECTED_RUNTIME_PATCH_SCOPE,
            "next_action": next_action,
            "no_new_gate_chain": True,
            "full_eval_run_by_builder": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    repeat = as_dict(report.get("targeted_repeat_summary"))
    validation = as_dict(report.get("patch_validation_summary"))
    health = as_dict(report.get("project_health_summary"))
    chain_counts = as_dict(validation.get("selected_evidence_identity_counts"))
    chain_lines = [
        f"- `{readable_evidence_chain(chain)}`: {count}" for chain, count in chain_counts.items()
    ] or ["- none"]
    lines = [
        "# v0.4.15.7 Near-Tie Patch Closeout",
        "",
        "## Conclusion",
        "",
        f"- status: `{summary.get('status')}`",
        f"- blockers: `{summary.get('blockers')}`",
        f"- runtime patch closed: `{summary.get('runtime_patch_closed')}`",
        f"- next action: `{summary.get('next_action')}`",
        "",
        "## Evidence Read",
        "",
        f"- targeted repeat runs: `{repeat.get('repeat_runs')}`",
        f"- targeted repeat all passed: `{repeat.get('all_runs_full_pass')}`",
        f"- validation status: `{validation.get('status')}`",
        f"- unique final evidence chains: `{validation.get('unique_selected_evidence_chains')}`",
        f"- project health status: `{health.get('status')}`",
        f"- project health failed checks: `{health.get('failed_checks')}`",
        "",
        "## Stable Final Evidence Identity",
        "",
        *chain_lines,
        "",
        "## Boundary",
        "",
        "This closeout only reads saved reports. It does not run eval, call `rag_query`, access Qdrant, call an LLM, or change runtime behavior.",
        "The closed patch scope remains same-bucket deterministic ordering inside existing Cross-Encoder stable-score buckets.",
        "No hidden seed, anchor, prompt, rerank score, `score_epsilon`, top_k, risk supplement, term preservation rule, scenario registry, fixture, or eval case change is authorized here.",
        "",
        "## Engineering Meaning",
        "",
        "v0.4.15.7 closes the near-tie patch validation loop. The next useful engineering move should be regression monitoring or a broader RAG quality task, not another design-only gate chain.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build near-tie patch closeout report.")
    parser.add_argument("--targeted-repeat", type=Path, default=DEFAULT_TARGETED_REPEAT_PATH)
    parser.add_argument("--patch-validation", type=Path, default=DEFAULT_PATCH_VALIDATION_PATH)
    parser.add_argument("--project-health", type=Path, default=DEFAULT_PROJECT_HEALTH_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.targeted_repeat, args.patch_validation, args.project_health)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild near-tie patch closeout completed: "
        f"{report['summary']['status']}, blockers={report['summary']['blockers']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
