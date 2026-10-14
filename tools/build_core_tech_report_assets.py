"""Build report-ready charts from a completed RAG ablation report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS_SIZE = (2400, 1350)
FONT = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 34)
SMALL_FONT = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 28)
TITLE_FONT = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 52)
AXIS_COLOR = "#374151"
GRID_COLOR = "#D1D5DB"
COLORBLIND_SAFE = ("#0072B2", "#009E73", "#E69F00", "#D55E00")


def _new_chart(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", CANVAS_SIZE, "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((110, 72), title, fill="#111827", font=TITLE_FONT)
    return image, draw


def _save_figure(image: Image.Image, output: Path) -> None:
    """Save a 300 dpi raster suitable for report placement and print export."""
    image.save(output, dpi=(300, 300))


def _draw_grouped_bars(
    output: Path,
    title: str,
    labels: list[str],
    series: list[tuple[str, list[float], str]],
    maximum: float,
    unit: str,
) -> None:
    image, draw = _new_chart(title)
    left, top, right, bottom = 180, 220, 2250, 1080
    draw.line((left, top, left, bottom), fill=AXIS_COLOR, width=4)
    draw.line((left, bottom, right, bottom), fill=AXIS_COLOR, width=4)
    for tick in range(6):
        value = maximum * tick / 5
        y = bottom - (bottom - top) * tick / 5
        draw.line((left, y, right, y), fill=GRID_COLOR, width=2)
        label = f"{value:.2f}{unit}"
        bbox = draw.textbbox((0, 0), label, font=SMALL_FONT)
        draw.text((left - 24 - (bbox[2] - bbox[0]), y - 17), label, fill=AXIS_COLOR, font=SMALL_FONT)
    group_width = (right - left) / len(labels)
    bar_width = min(100, group_width / (len(series) + 2.5))
    for index, label in enumerate(labels):
        center = left + group_width * (index + 0.5)
        for offset, (_name, values, color) in enumerate(series):
            bar_left = center + (offset - (len(series) - 1) / 2) * (bar_width + 18) - bar_width / 2
            bar_top = bottom - (bottom - top) * values[index] / maximum
            draw.rectangle((bar_left, bar_top, bar_left + bar_width, bottom), fill=color)
            value_label = f"{values[index]:.3f}" if maximum <= 1.1 else f"{values[index]:.0f}"
            label_box = draw.textbbox((0, 0), value_label, font=SMALL_FONT)
            draw.text(
                (bar_left + (bar_width - (label_box[2] - label_box[0])) / 2, max(top, bar_top - 40)),
                value_label,
                fill=AXIS_COLOR,
                font=SMALL_FONT,
            )
        text_box = draw.textbbox((0, 0), label, font=FONT)
        draw.text((center - (text_box[2] - text_box[0]) / 2, bottom + 34), label, fill=AXIS_COLOR, font=FONT)
    legend_x = left
    for name, _values, color in series:
        draw.rectangle((legend_x, 1190, legend_x + 32, 1222), fill=color)
        draw.text((legend_x + 46, 1186), name, fill=AXIS_COLOR, font=SMALL_FONT)
        legend_x += max(285, len(name) * 20 + 84)
    _save_figure(image, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("tests/rag_ablation_report.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/core_tech"))
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("status") != "completed":
        raise SystemExit("ablation report is not completed")
    names = ["M1_dense", "M2_hybrid", "M3_concept", "M4_full"]
    labels = ["M1 Dense", "M2 Hybrid", "M3 Concept", "M4 Full"]
    summaries = [report["profiles"][name]["summary"] for name in names]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metric_names = ["Evidence Recall@K", "MRR@K", "nDCG@K", "Multi-source coverage"]
    metric_keys = ["evidence_recall_at_k", "mrr_at_k", "ndcg_at_k", "multi_source_coverage"]
    metric_colors = list(COLORBLIND_SAFE)
    metric_series = [
        (name, [float(summary[key]) for summary in summaries], color)
        for name, key, color in zip(metric_names, metric_keys, metric_colors)
    ]
    _draw_grouped_bars(
        args.output_dir / "ablation_evidence_metrics.png",
        f"Retrieval ablation: evidence quality (n={report['case_count']})",
        labels,
        metric_series,
        maximum=1.0,
        unit="",
    )

    p50 = [float(summary["retrieval_time_p50_ms"]) for summary in summaries]
    p95 = [float(summary["retrieval_time_p95_ms"]) for summary in summaries]
    _draw_grouped_bars(
        args.output_dir / "ablation_latency.png",
        f"Retrieval ablation: latency (n={report['case_count']})",
        labels,
        [("p50", p50, COLORBLIND_SAFE[0]), ("p95", p95, COLORBLIND_SAFE[3])],
        maximum=max(p95) * 1.1,
        unit="ms",
    )

    summary_lines = [
        "# RAG 消融实验摘要",
        "",
        f"- 测试集数量：{report['case_count']}",
        f"- 测试集 SHA-256：`{report['case_file_sha256']}`",
        "- 指标含义：Evidence Recall@K 是期望法源进入前 K 条证据的比例，不等于回答准确率。",
        "",
        "| 配置 | Recall@K | MRR@K | nDCG@K | 多来源覆盖 | p50(ms) | p95(ms) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, summary in zip(labels, summaries):
        summary_lines.append(
            f"| {label} | {summary['evidence_recall_at_k']:.4f} | {summary['mrr_at_k']:.4f} | "
            f"{summary['ndcg_at_k']:.4f} | {summary['multi_source_coverage']:.4f} | "
            f"{summary['retrieval_time_p50_ms']:.2f} | {summary['retrieval_time_p95_ms']:.2f} |"
        )
    (args.output_dir / "ablation_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"built report assets in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
