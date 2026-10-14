import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REPORT = Path("tests/rag_stability_report.json")
PRE_PATCH_ID = "v0.4.5.13-pre-patch-repeat"
POST_PATCH_ID = "v0.4.5.14-post-patch-repeat"


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dense_fallback_counts(report: dict[str, Any]) -> list[int]:
    counts = []
    for run in report.get("runs", []):
        summary = run.get("contribution_summary", {})
        count = summary.get("dense_fallback_passed")
        if count is None:
            count = summary.get("label_counts", {}).get("DENSE_FALLBACK_PASS", 0)
        counts.append(int(count))
    return counts


def experiments_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        experiment.get("experiment_id", ""): experiment
        for experiment in report.get("experiment_comparison", [])
        if isinstance(experiment, dict)
    }


def validate_report(
    report: dict[str, Any],
    max_unstable_cases: int = 0,
    max_dense_fallback_pass: int = 0,
    require_experiment_comparison: bool = True,
) -> list[str]:
    errors: list[str] = []
    stability = report.get("stability_summary", {})
    runs = report.get("runs", [])

    unstable_count = len(stability.get("unstable_cases", []))
    if unstable_count > max_unstable_cases:
        errors.append(f"unstable_cases={unstable_count} exceeds max_unstable_cases={max_unstable_cases}")

    fallback_counts = dense_fallback_counts(report)
    fallback_total = sum(fallback_counts)
    if fallback_total > max_dense_fallback_pass:
        errors.append(
            f"DENSE_FALLBACK_PASS total={fallback_total} exceeds max_dense_fallback_pass={max_dense_fallback_pass}"
        )

    if report.get("repeat") != len(runs):
        errors.append(f"repeat={report.get('repeat')} does not match runs length={len(runs)}")

    pass_counts = [run.get("passed") for run in runs]
    total_counts = [run.get("total") for run in runs]
    if stability.get("pass_counts") != pass_counts:
        errors.append("stability_summary.pass_counts does not match top-level runs")
    if stability.get("total_counts") != total_counts:
        errors.append("stability_summary.total_counts does not match top-level runs")

    if require_experiment_comparison:
        experiments = experiments_by_id(report)
        pre_patch = experiments.get(PRE_PATCH_ID)
        post_patch = experiments.get(POST_PATCH_ID)
        if pre_patch is None:
            errors.append(f"missing experiment_comparison entry: {PRE_PATCH_ID}")
        if post_patch is None:
            errors.append(f"missing experiment_comparison entry: {POST_PATCH_ID}")
        if pre_patch and "historical" not in pre_patch.get("relationship_to_current_runs", "").lower():
            errors.append(f"{PRE_PATCH_ID} must be marked as historical baseline")
        if post_patch and post_patch.get("pass_counts") != pass_counts:
            errors.append(f"{POST_PATCH_ID}.pass_counts must match top-level post-patch runs")
        if post_patch and post_patch.get("total_counts") != total_counts:
            errors.append(f"{POST_PATCH_ID}.total_counts must match top-level post-patch runs")
        if post_patch and post_patch.get("dense_fallback_pass_counts") != fallback_counts:
            errors.append(f"{POST_PATCH_ID}.dense_fallback_pass_counts must match top-level runs")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check RAG stability report release gates.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-unstable-cases", type=int, default=0)
    parser.add_argument("--max-dense-fallback-pass", type=int, default=0)
    parser.add_argument("--no-experiment-comparison", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_report(args.report)
    errors = validate_report(
        report,
        max_unstable_cases=args.max_unstable_cases,
        max_dense_fallback_pass=args.max_dense_fallback_pass,
        require_experiment_comparison=not args.no_experiment_comparison,
    )
    if errors:
        print("RAG stability gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RAG stability gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
