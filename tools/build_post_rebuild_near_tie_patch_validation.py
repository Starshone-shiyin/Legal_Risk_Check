"""Build the v0.4.15.6 near-tie runtime patch validation report.

This helper reads a saved targeted repeat report produced after the minimal
same-bucket rerank stabilization patch. It does not run eval, call rag_query,
contact Qdrant or an LLM, or mutate anchors, prompts, risk rules, eval cases,
hidden seeds, fixtures, rerank scores, score_epsilon, or top_k.
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


VERSION = "0.4.15.6"

DEFAULT_REPEAT_REPORT_PATH = Path("tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md")

GUARDRAILS = {
    "saved_reports_only": True,
    "runtime_patch_validation": True,
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


def evidence_key(item: dict[str, Any]) -> str:
    source = item.get("source") or item.get("law_name") or ""
    article_no = item.get("article_no")
    section_no = item.get("section_no")
    if article_no is not None:
        return f"{source}|article:{article_no}"
    if section_no:
        return f"{source}|section:{section_no}"
    return str(item.get("exact_key") or item.get("chunk_id") or source)


def selected_evidence(report: dict[str, Any]) -> list[str]:
    trace = as_dict(as_dict(report.get("debug_info")).get("final_evidence_selection_trace"))
    selected = as_list(trace.get("selected"))
    if selected:
        return [evidence_key(as_dict(item)) for item in selected]
    return [evidence_key(as_dict(item)) for item in as_list(report.get("evidence_chain"))]


def collect_case_runs(repeat_report: dict[str, Any]) -> list[dict[str, Any]]:
    case_runs: list[dict[str, Any]] = []
    for run in as_list(repeat_report.get("runs")):
        reports = as_list(as_dict(run).get("reports"))
        for report in reports:
            case_report = as_dict(report)
            if case_report:
                case_runs.append(
                    {
                        "run": as_dict(run).get("run"),
                        "case_id": case_report.get("id"),
                        "passed": case_report.get("passed") is True,
                        "retrieval_failure_stage": case_report.get("retrieval_failure_stage"),
                        "selected_evidence": selected_evidence(case_report),
                    }
                )
    return case_runs


def build_report(repeat_report_path: Path = DEFAULT_REPEAT_REPORT_PATH) -> dict[str, Any]:
    if not repeat_report_path.exists():
        return {
            "version": VERSION,
            "schema_kind": "post_rebuild_near_tie_patch_validation",
            "scope": "saved targeted repeat validation for deterministic same-bucket rerank ordering",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "repeat_report": str(repeat_report_path),
                "repeat_report_exists": False,
            },
            "guardrails": GUARDRAILS,
            "case_runs": [],
            "selected_evidence_identity_counts": {},
            "checks": [
                {
                    "name": "repeat_report_available",
                    "passed": False,
                }
            ],
            "summary": {
                "status": "blocked",
                "blockers": ["repeat_report_missing_or_unavailable"],
                "runtime_patch_authorized": True,
                "runtime_patch_scope": "same_bucket_deterministic_ordering_only",
                "repeat_runs": 0,
                "case_run_count": 0,
                "case_ids": [],
                "unique_selected_evidence_chains": 0,
            },
        }
    repeat_report = load_json(repeat_report_path)
    case_runs = collect_case_runs(repeat_report)
    selected_chains = [tuple(item["selected_evidence"]) for item in case_runs]
    chain_counts = Counter(selected_chains)
    unique_case_ids = sorted({str(item["case_id"]) for item in case_runs if item.get("case_id")})
    stability_summary = as_dict(repeat_report.get("stability_summary"))
    checks = [
        {
            "name": "repeat_report_available",
            "passed": bool(case_runs),
        },
        {
            "name": "all_runs_full_pass",
            "passed": stability_summary.get("all_runs_full_pass") is True
            or all(item["passed"] for item in case_runs),
        },
        {
            "name": "single_case_targeted_repeat",
            "passed": len(unique_case_ids) == 1,
        },
        {
            "name": "selected_evidence_identity_stable",
            "passed": len(chain_counts) == 1 and bool(chain_counts),
        },
        {
            "name": "final_selection_trace_available",
            "passed": all(len(item["selected_evidence"]) > 0 for item in case_runs),
        },
    ]
    blockers = [item["name"] for item in checks if not item["passed"]]
    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_near_tie_patch_validation",
        "scope": "saved targeted repeat validation for deterministic same-bucket rerank ordering",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {"repeat_report": str(repeat_report_path)},
        "guardrails": GUARDRAILS,
        "case_runs": case_runs,
        "selected_evidence_identity_counts": {
            " -> ".join(chain): count for chain, count in sorted(chain_counts.items())
        },
        "checks": checks,
        "summary": {
            "status": "passed" if not blockers else "blocked",
            "blockers": blockers,
            "runtime_patch_authorized": True,
            "runtime_patch_scope": "same_bucket_deterministic_ordering_only",
            "repeat_runs": len(as_list(repeat_report.get("runs"))),
            "case_run_count": len(case_runs),
            "case_ids": unique_case_ids,
            "unique_selected_evidence_chains": len(chain_counts),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.15.6 Near-Tie Patch Validation",
        "",
        "## Conclusion",
        "",
        f"- status: `{summary.get('status')}`",
        f"- blockers: `{summary.get('blockers')}`",
        f"- runtime patch scope: `{summary.get('runtime_patch_scope')}`",
        f"- repeat runs: `{summary.get('repeat_runs')}`",
        f"- unique selected evidence chains: `{summary.get('unique_selected_evidence_chains')}`",
        "",
        "## Validation Scope",
        "",
        "- Reads the post-patch targeted repeat saved report.",
        "- Checks whether each run passed, whether final selection trace is available, and whether final evidence identity is stable.",
        "- This validation only proves the runtime effect of same-bucket deterministic ordering; it does not repair samples, add anchors, or change prompt/risk supplement/eval cases.",
        "",
        "## Boundary",
        "",
        "This tool does not run eval, call `rag_query`, connect to Qdrant, call an LLM, or mutate runtime state.",
        "If the targeted repeat saved report is missing, this tool fails closed with a blocked validation report.",
        "The runtime patch itself may only stabilize candidate order inside existing Cross-Encoder stable-score buckets; it must not change scores, model, query, `score_epsilon`, top_k, anchor, prompt, risk supplement, term preservation, scenario registry, fixtures, eval cases, or hidden seed.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build near-tie runtime patch validation report.")
    parser.add_argument("--repeat-report", type=Path, default=DEFAULT_REPEAT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repeat_report)
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    print(
        "Post-rebuild near-tie patch validation completed: "
        f"{report['summary']['status']}, blockers={report['summary']['blockers']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
