"""Create research-style ESG figures from a judged retrieval-only report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS = (2400, 1350)
FONT = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 34)
SMALL = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 28)
TITLE = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 52)
AXIS = "#374151"
GRID = "#D1D5DB"
COLORS = ("#0072B2", "#009E73", "#E69F00", "#D55E00")


def _canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", CANVAS, "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((110, 72), title, fill="#111827", font=TITLE)
    return image, draw


def _draw_rate_bars(output: Path, summary: dict[str, float | int], case_count: int) -> None:
    image, draw = _canvas(f"Evidence Sufficiency Gate routing (n={case_count})")
    labels = ["Sufficient", "Web supplement", "Human review", "Local primary law"]
    values = [
        float(summary["sufficient_rate"]),
        float(summary["web_supplement_rate"]),
        float(summary["human_review_rate"]),
        float(summary["local_primary_law_coverage"]),
    ]
    left, top, right, bottom = 180, 230, 2250, 1080
    draw.line((left, top, left, bottom), fill=AXIS, width=4)
    draw.line((left, bottom, right, bottom), fill=AXIS, width=4)
    for tick in range(6):
        y = bottom - (bottom - top) * tick / 5
        value = tick / 5
        draw.line((left, y, right, y), fill=GRID, width=2)
        label = f"{value:.1f}"
        box = draw.textbbox((0, 0), label, font=SMALL)
        draw.text((left - 24 - (box[2] - box[0]), y - 17), label, fill=AXIS, font=SMALL)
    group_width = (right - left) / len(labels)
    bar_width = 210
    for index, (label, value, color) in enumerate(zip(labels, values, COLORS)):
        center = left + group_width * (index + 0.5)
        bar_top = bottom - (bottom - top) * value
        x0 = center - bar_width / 2
        draw.rectangle((x0, bar_top, x0 + bar_width, bottom), fill=color)
        value_label = f"{value:.3f}"
        box = draw.textbbox((0, 0), value_label, font=FONT)
        draw.text((center - (box[2] - box[0]) / 2, max(top, bar_top - 50)), value_label, fill=AXIS, font=FONT)
        label_box = draw.textbbox((0, 0), label, font=FONT)
        draw.text((center - (label_box[2] - label_box[0]) / 2, bottom + 34), label, fill=AXIS, font=FONT)
    image.save(output, dpi=(300, 300))


def _draw_score_distribution(output: Path, scores: list[float], case_count: int) -> None:
    image, draw = _canvas(f"Evidence Sufficiency Gate score distribution (n={case_count})")
    bins = [0, 0, 0, 0, 0, 0]
    for score in scores:
        bins[min(5, max(0, int(score * 5)))] += 1
    labels = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0", "1.0"]
    maximum = max(bins) or 1
    left, top, right, bottom = 180, 230, 2250, 1080
    draw.line((left, top, left, bottom), fill=AXIS, width=4)
    draw.line((left, bottom, right, bottom), fill=AXIS, width=4)
    for tick in range(6):
        y = bottom - (bottom - top) * tick / 5
        value = round(maximum * tick / 5)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((left - 68, y - 17), str(value), fill=AXIS, font=SMALL)
    group_width = (right - left) / len(labels)
    bar_width = min(220, group_width * 0.62)
    for index, (label, count) in enumerate(zip(labels, bins)):
        center = left + group_width * (index + 0.5)
        bar_top = bottom - (bottom - top) * count / maximum
        x0 = center - bar_width / 2
        color = COLORS[0] if index >= 4 else COLORS[3]
        draw.rectangle((x0, bar_top, x0 + bar_width, bottom), fill=color)
        count_label = str(count)
        box = draw.textbbox((0, 0), count_label, font=FONT)
        draw.text((center - (box[2] - box[0]) / 2, max(top, bar_top - 50)), count_label, fill=AXIS, font=FONT)
        label_box = draw.textbbox((0, 0), label, font=SMALL)
        draw.text((center - (label_box[2] - label_box[0]) / 2, bottom + 36), label, fill=AXIS, font=SMALL)
    image.save(output, dpi=(300, 300))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("tests/rag_esg_m4_report.json"))
    parser.add_argument("--profile", default="M4_full")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/core_tech_20260810"))
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    profile = report.get("profiles", {}).get(args.profile)
    if report.get("status") != "completed" or not isinstance(profile, dict):
        raise SystemExit("completed report and requested profile are required")
    summary = profile.get("evidence_sufficiency_summary")
    cases = profile.get("cases")
    if not isinstance(summary, dict) or not isinstance(cases, list):
        raise SystemExit("report does not contain ESG summary and cases")
    scores = [float(case["evidence_sufficiency"]["score"]) for case in cases]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _draw_rate_bars(args.output_dir / "esg_routing_summary.png", summary, len(cases))
    _draw_score_distribution(args.output_dir / "esg_score_distribution.png", scores, len(cases))
    (args.output_dir / "esg_summary.md").write_text(
        "\n".join([
            "# Evidence Sufficiency Gate Summary",
            "",
            f"- Source report: `{args.report}`",
            f"- Frozen case hash: `{report.get('case_file_sha256', '')}`",
            f"- Profile: `{args.profile}`",
            f"- Case count: {len(cases)}",
            f"- Mean ESG score: {float(summary['mean_score']):.6f}",
            f"- Direct answer rate: {float(summary['sufficient_rate']):.6f}",
            f"- Web supplementation rate: {float(summary['web_supplement_rate']):.6f}",
            f"- Human review rate: {float(summary['human_review_rate']):.6f}",
            f"- Local primary-law coverage: {float(summary['local_primary_law_coverage']):.6f}",
            "",
            "ESG is a routing and evidence-governance metric, not a legal-correctness metric.",
        ]) + "\n",
        encoding="utf-8",
    )
    print(f"built ESG assets in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
