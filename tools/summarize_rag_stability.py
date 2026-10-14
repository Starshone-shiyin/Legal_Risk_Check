import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REPORT = Path("tests/rag_stability_report.json")
DEFAULT_OUTPUT = Path("tests/rag_stability_summary.md")


LABEL_ORDER = [
    "PURE_LLM_PASS",
    "ANCHOR_PASS",
    "RISK_SUPPLEMENT_PASS",
    "TERM_PRESERVATION_PASS",
    "DENSE_FALLBACK_PASS",
]


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_list(values: list[Any]) -> str:
    return ", ".join(str(value) for value in values)


def contribution_count(summary: dict[str, Any], label: str) -> int:
    return int(summary.get("label_counts", {}).get(label, 0))


def rule_heavy_cases(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for run in runs:
        run_no = run.get("run")
        for report in run.get("reports", []):
            labels = set(report.get("contribution_labels", []))
            if not {"ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"}.issubset(labels):
                continue
            case_id = report.get("id", "")
            item = cases.setdefault(
                case_id,
                {
                    "id": case_id,
                    "runs": [],
                    "category": report.get("category", ""),
                    "question": report.get("question", ""),
                    "labels": set(),
                },
            )
            item["runs"].append(run_no)
            item["labels"].update(labels)

    sorted_cases = sorted(cases.values(), key=lambda item: (-len(item["runs"]), item["id"]))
    for item in sorted_cases:
        item["labels"] = sorted(item["labels"])
    return sorted_cases


def render_experiment_comparison(report: dict[str, Any]) -> list[str]:
    lines = ["## 实验对象边界", ""]
    lines.extend([
        "注意：v0.4.5.13 原始 repeat 基线与 v0.4.5.14 patch 后 repeat 是两个不同代码状态下的实验对象，不能用修复后三连跑覆盖原始稳定性结论。",
        "",
    ])

    experiments = report.get("experiment_comparison", [])
    if not experiments:
        lines.extend(["未找到 `experiment_comparison`，无法区分原始基线与 patch 后实验。", ""])
        return lines

    lines.extend([
        "| 实验 | 代码状态 | pass counts | 结论 |",
        "|---|---|---:|---|",
    ])
    for experiment in experiments:
        lines.append(
            "| {experiment_id} | {code_state} | {pass_counts} | {conclusion} |".format(
                experiment_id=experiment.get("experiment_id", ""),
                code_state=experiment.get("code_state", ""),
                pass_counts=format_list(experiment.get("pass_counts", [])),
                conclusion=experiment.get("conclusion", ""),
            )
        )
    lines.append("")
    return lines


def render_patch_summary(report: dict[str, Any]) -> list[str]:
    stability = report.get("stability_summary", {})
    runs = report.get("runs", [])
    lines = [
        "## v0.4.5.14 Patch 后稳定性",
        "",
        f"- repeat：`{report.get('repeat', len(runs))}`",
        f"- pass counts：`{format_list(stability.get('pass_counts', []))}`",
        f"- all runs full pass：`{stability.get('all_runs_full_pass')}`",
        f"- unstable cases：`{len(stability.get('unstable_cases', []))}`",
        f"- label variation cases：`{len(stability.get('label_variation_cases', []))}`",
        "",
        "| run | passed | failed | PURE | ANCHOR | RISK | TERM | DENSE_FALLBACK |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in runs:
        summary = run.get("contribution_summary", {})
        lines.append(
            "| {run} | {passed}/{total} | {failed} | {pure} | {anchor} | {risk} | {term} | {fallback} |".format(
                run=run.get("run", ""),
                passed=run.get("passed", 0),
                total=run.get("total", 0),
                failed=run.get("failed", 0),
                pure=contribution_count(summary, "PURE_LLM_PASS"),
                anchor=contribution_count(summary, "ANCHOR_PASS"),
                risk=contribution_count(summary, "RISK_SUPPLEMENT_PASS"),
                term=contribution_count(summary, "TERM_PRESERVATION_PASS"),
                fallback=contribution_count(summary, "DENSE_FALLBACK_PASS"),
            )
        )
    lines.append("")
    return lines


def render_label_variations(report: dict[str, Any]) -> list[str]:
    variations = report.get("stability_summary", {}).get("label_variation_cases", [])
    lines = ["## 贡献标签波动", ""]
    if not variations:
        lines.extend(["无贡献标签波动。", ""])
        return lines

    lines.extend(["| case | labels by run |", "|---|---|"])
    for item in variations:
        labels_by_run = ["+".join(labels) if labels else "(none)" for labels in item.get("contribution_labels", [])]
        lines.append(f"| {item.get('id', '')} | {' / '.join(labels_by_run)} |")
    lines.append("")
    return lines


def render_rule_heavy_cases(report: dict[str, Any]) -> list[str]:
    cases = rule_heavy_cases(report.get("runs", []))
    lines = [
        "## 规则依赖较高 Case",
        "",
        "口径：同一 run 中同时带有 `ANCHOR_PASS` 与 `RISK_SUPPLEMENT_PASS` 的通过样本。",
        "",
    ]
    if not cases:
        lines.extend(["未发现同时依赖 anchor 与风险补全的通过样本。", ""])
        return lines

    lines.extend(["| case | runs | labels | question |", "|---|---:|---|---|"])
    for item in cases:
        lines.append(
            "| {case_id} | {runs} | {labels} | {question} |".format(
                case_id=item["id"],
                runs=format_list(item["runs"]),
                labels=", ".join(item["labels"]),
                question=item.get("question", "").replace("|", "\\|"),
            )
        )
    lines.append("")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# RAG Eval 稳定性与贡献归因摘要",
        "",
        "本报告由 `tools/summarize_rag_stability.py` 从 `tests/rag_stability_report.json` 生成。",
        "",
    ]
    lines.extend(render_experiment_comparison(report))
    lines.extend(render_patch_summary(report))
    lines.extend(render_label_variations(report))
    lines.extend(render_rule_heavy_cases(report))
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown summary for RAG stability reports.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_report(args.report)
    markdown = render_markdown(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"summary written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
