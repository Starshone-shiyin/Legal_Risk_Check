"""Summarize post-rebuild smoke and metadata validation results."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.14.30"
DEFAULT_POST_REBUILD_SMOKE_PATH = Path("tests/post_rebuild_smoke_eval_report.json")
DEFAULT_BASELINE_SMOKE_PATH = Path("tests/smoke_eval_report.json")
DEFAULT_POST_VALIDATION_PATH = Path("tests/production_rebuild_post_validation_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_quality_summary_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_quality_summary_v0.4.14.30.md")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def report_case_statuses(report: dict[str, Any]) -> dict[str, bool]:
    statuses = {}
    for item in report.get("reports") or []:
        case_id = item.get("id")
        if case_id:
            statuses[case_id] = bool(item.get("passed"))
    return statuses


def summarize_contribution_labels(post_smoke: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in post_smoke.get("reports") or []:
        for layer_report in (item.get("layers") or {}).values():
            for label in layer_report.get("contribution_labels") or []:
                counts[label] = counts.get(label, 0) + 1
    return counts


def build_summary_report(
    post_rebuild_smoke_path: Path = DEFAULT_POST_REBUILD_SMOKE_PATH,
    baseline_smoke_path: Path = DEFAULT_BASELINE_SMOKE_PATH,
    post_validation_path: Path = DEFAULT_POST_VALIDATION_PATH,
) -> dict[str, Any]:
    post_smoke = load_json(post_rebuild_smoke_path)
    baseline_smoke = load_json(baseline_smoke_path)
    post_validation = load_json(post_validation_path)

    post_statuses = report_case_statuses(post_smoke)
    baseline_statuses = report_case_statuses(baseline_smoke)
    regressed_cases = sorted(
        case_id for case_id, passed in baseline_statuses.items()
        if passed and post_statuses.get(case_id) is False
    )
    newly_passing_cases = sorted(
        case_id for case_id, passed in post_statuses.items()
        if passed and baseline_statuses.get(case_id) is False
    )
    missing_from_post = sorted(set(baseline_statuses) - set(post_statuses))

    blockers = []
    if post_smoke.get("passed") != post_smoke.get("total"):
        blockers.append("post_rebuild_smoke_not_full_pass")
    if regressed_cases:
        blockers.append("baseline_smoke_regressions")
    if missing_from_post:
        blockers.append("post_rebuild_smoke_missing_baseline_cases")
    if post_validation.get("summary", {}).get("status") != "passed":
        blockers.append("post_validation_not_passed")

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_quality_summary_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "post_rebuild_smoke_report": str(post_rebuild_smoke_path),
            "baseline_smoke_report": str(baseline_smoke_path),
            "post_validation_report": str(post_validation_path),
        },
        "smoke_summary": {
            "baseline_total": baseline_smoke.get("total"),
            "baseline_passed": baseline_smoke.get("passed"),
            "post_rebuild_total": post_smoke.get("total"),
            "post_rebuild_passed": post_smoke.get("passed"),
            "post_rebuild_failed": post_smoke.get("failed"),
            "regressed_cases": regressed_cases,
            "newly_passing_cases": newly_passing_cases,
            "missing_from_post_rebuild": missing_from_post,
            "contribution_label_counts": summarize_contribution_labels(post_smoke),
        },
        "post_validation_summary": {
            "status": post_validation.get("summary", {}).get("status"),
            "blockers": post_validation.get("summary", {}).get("blockers", []),
            "points_count": post_validation.get("validation", {}).get("points_count"),
            "scanned_points": post_validation.get("validation", {}).get("scanned_points"),
            "observed_chunk_fields": post_validation.get("validation", {}).get("observed_chunk_fields", {}),
            "missing_chunk_fields": post_validation.get("validation", {}).get("missing_chunk_fields", {}),
        },
        "summary": {
            "status": "passed" if not blockers else "failed",
            "blockers": blockers,
            "full_eval": "not_run",
            "recommended_next_step": "run_post_rebuild_targeted_or_full_rag_eval" if not blockers else "triage_post_rebuild_smoke_failure",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    smoke = report["smoke_summary"]
    validation = report["post_validation_summary"]
    lines = [
        "# v0.4.14.30 Post-Rebuild Quality Summary",
        "",
        "## 结论",
        "",
        f"- 状态：`{report['summary']['status']}`",
        f"- post-rebuild smoke：`{smoke['post_rebuild_passed']}/{smoke['post_rebuild_total']}`",
        f"- baseline smoke：`{smoke['baseline_passed']}/{smoke['baseline_total']}`",
        f"- 回归 case：`{len(smoke['regressed_cases'])}`",
        f"- post-validation：`{validation['status']}`",
        f"- Qdrant points：`{validation['points_count']}`",
        f"- 扫描 points：`{validation['scanned_points']}`",
        "",
        "## Metadata 观测",
        "",
        f"- observed_chunk_fields：`{validation['observed_chunk_fields']}`",
        f"- missing_chunk_fields：`{validation['missing_chunk_fields']}`",
        "",
        "## 下一步",
        "",
        f"- `{report['summary']['recommended_next_step']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize post-rebuild quality checks.")
    parser.add_argument("--post-rebuild-smoke", type=Path, default=DEFAULT_POST_REBUILD_SMOKE_PATH)
    parser.add_argument("--baseline-smoke", type=Path, default=DEFAULT_BASELINE_SMOKE_PATH)
    parser.add_argument("--post-validation", type=Path, default=DEFAULT_POST_VALIDATION_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()

    report = build_summary_report(
        post_rebuild_smoke_path=args.post_rebuild_smoke,
        baseline_smoke_path=args.baseline_smoke,
        post_validation_path=args.post_validation,
    )
    write_json(args.output, report)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(render_markdown(report), encoding="utf-8")
    print(f"Post-rebuild quality summary completed: {report['summary']['status']}, output={args.output}")
    return 0 if report["summary"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
