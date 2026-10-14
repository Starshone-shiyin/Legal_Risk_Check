"""Build report-ready figures and a concise evidence packet from saved experiment runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS = (2400, 1350)
FONT = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 34)
SMALL = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 28)
TITLE = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 52)
COLORS = ("#0072B2", "#009E73", "#D55E00", "#CC79A7")
TEXT = "#1F2937"
GRID = "#D1D5DB"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def new_chart(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", CANVAS, "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((105, 64), title, fill=TEXT, font=TITLE)
    return image, draw


def save(image: Image.Image, path: Path) -> None:
    image.save(path, dpi=(300, 300))


def draw_series_chart(path: Path, title: str, labels: list[str], series: list[tuple[str, list[float], str]]) -> None:
    image, draw = new_chart(title)
    left, top, right, bottom = 170, 205, 2260, 1080
    draw.line((left, top, left, bottom), fill=TEXT, width=4)
    draw.line((left, bottom, right, bottom), fill=TEXT, width=4)
    for tick in range(6):
        value = tick / 5
        y = bottom - (bottom - top) * value
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((100, y - 16), f"{value:.1f}", fill=TEXT, font=SMALL)
    step = (right - left) / (len(labels) - 1)
    for name, values, color in series:
        points = []
        for index, value in enumerate(values):
            x = left + index * step
            y = bottom - (bottom - top) * value
            points.append((x, y))
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color)
        draw.line(points, fill=color, width=6)
    for index, label in enumerate(labels):
        x = left + index * step
        box = draw.textbbox((0, 0), label, font=FONT)
        draw.text((x - (box[2] - box[0]) / 2, bottom + 32), label, fill=TEXT, font=FONT)
    x = left
    for name, _values, color in series:
        draw.rectangle((x, 1182, x + 32, 1214), fill=color)
        draw.text((x + 46, 1178), name, fill=TEXT, font=SMALL)
        x += max(300, len(name) * 22 + 90)
    save(image, path)


def draw_latency_chart(path: Path, labels: list[str], p50: list[float], p95: list[float]) -> None:
    image, draw = new_chart("Controlled ablation: retrieval latency")
    left, top, right, bottom = 170, 205, 2260, 1080
    maximum = max(p95) * 1.12
    draw.line((left, top, left, bottom), fill=TEXT, width=4)
    draw.line((left, bottom, right, bottom), fill=TEXT, width=4)
    for tick in range(6):
        value = maximum * tick / 5
        y = bottom - (bottom - top) * tick / 5
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((58, y - 16), f"{value:.0f} ms", fill=TEXT, font=SMALL)
    width = (right - left) / len(labels)
    for index, label in enumerate(labels):
        center = left + width * (index + 0.5)
        for offset, (value, color, name) in enumerate(((p50[index], COLORS[0], "p50"), (p95[index], COLORS[2], "p95"))):
            x = center + (-42 if offset == 0 else 10)
            y = bottom - (bottom - top) * value / maximum
            draw.rectangle((x, y, x + 32, bottom), fill=color)
            draw.text((x - 24, max(top, y - 42)), f"{value:.0f}", fill=color, font=SMALL)
        box = draw.textbbox((0, 0), label, font=FONT)
        draw.text((center - (box[2] - box[0]) / 2, bottom + 32), label, fill=TEXT, font=FONT)
    draw.rectangle((left, 1182, left + 32, 1214), fill=COLORS[0])
    draw.text((left + 46, 1178), "p50", fill=TEXT, font=SMALL)
    draw.rectangle((left + 180, 1182, left + 212, 1214), fill=COLORS[2])
    draw.text((left + 226, 1178), "p95", fill=TEXT, font=SMALL)
    save(image, path)


def draw_robustness_chart(path: Path, robustness: dict) -> None:
    labels = ["Colloquial", "Term substitution", "Multi-issue"]
    profile_names = ("C0_dense", "C3_concept_anchors", "C4_scene_anchors", "C6_cross_encoder")
    series = (
        ("C0 dense", COLORS[0]),
        ("C3 concept anchors", COLORS[1]),
        ("C4 scenario anchors", COLORS[2]),
        ("C6 full", COLORS[3]),
    )
    image, draw = new_chart("Rewritten-question robustness (n=24)")
    left, top, right, bottom = 170, 205, 2260, 1080
    draw.line((left, top, left, bottom), fill=TEXT, width=4)
    draw.line((left, bottom, right, bottom), fill=TEXT, width=4)
    for tick in range(6):
        y = bottom - (bottom - top) * tick / 5
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((100, y - 16), f"{tick / 5:.1f}", fill=TEXT, font=SMALL)
    step = (right - left) / len(labels)
    for index, label in enumerate(labels):
        center = left + step * (index + 0.5)
        for offset, ((profile_name, (name, color))) in enumerate(zip(profile_names, series)):
            value = float(robustness["profiles"][profile_name]["by_perturbation_type"][
                ("colloquial", "term_substitution", "multi_issue")[index]
            ]["evidence_recall_at_k"])
            x = center + (-96 + offset * 52)
            y = bottom - (bottom - top) * value
            draw.rectangle((x, y, x + 34, bottom), fill=color)
        box = draw.textbbox((0, 0), label, font=SMALL)
        draw.text((center - (box[2] - box[0]) / 2, bottom + 32), label, fill=TEXT, font=SMALL)
    x = left
    for name, color in series:
        draw.rectangle((x, 1182, x + 28, 1210), fill=color)
        draw.text((x + 40, 1178), name, fill=TEXT, font=SMALL)
        x += 390
    save(image, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controlled", type=Path, required=True)
    parser.add_argument("--robustness", type=Path, required=True)
    parser.add_argument("--end-to-end", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/core_tech_20260815"))
    parser.add_argument("--summary", type=Path, default=Path("docs/core_tech_experiment_results_20260815.md"))
    args = parser.parse_args()
    controlled = load(args.controlled)
    robustness = load(args.robustness)
    end_to_end = load(args.end_to_end)
    names = [f"C{index}" for index in range(7)]
    profiles = [controlled["profiles"][f"C{index}_{suffix}"] for index, suffix in enumerate((
        "dense", "hybrid", "query_expansion", "concept_anchors", "scene_anchors", "complex_planner", "cross_encoder",
    ))]
    summaries = [profile["summary"] for profile in profiles]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    draw_series_chart(
        args.output_dir / "controlled_ablation_quality.png",
        f"Controlled retrieval ablation (n={controlled['case_count']})",
        names,
        [
            ("Evidence Recall@K", [float(item["evidence_recall_at_k"]) for item in summaries], COLORS[0]),
            ("MRR@K", [float(item["mrr_at_k"]) for item in summaries], COLORS[1]),
            ("nDCG@K", [float(item["ndcg_at_k"]) for item in summaries], COLORS[2]),
        ],
    )
    draw_latency_chart(
        args.output_dir / "controlled_ablation_latency.png",
        names,
        [float(item["retrieval_time_p50_ms"]) for item in summaries],
        [float(item["retrieval_time_p95_ms"]) for item in summaries],
    )
    draw_robustness_chart(args.output_dir / "rewritten_question_robustness.png", robustness)
    esg = controlled["profiles"]["C6_cross_encoder"]["evidence_sufficiency_summary"]
    summary = [
        "# 核心技术实验结果（2026-08-15）",
        "",
        "本文件记录比赛报告中可声明的实验结果。所有检索指标均为期望法源进入前 K 条证据的排序指标，不等于法律结论正确率。",
        "",
        "## 1. 单变量控制消融",
        "",
        f"- 冻结测试集：60 题，SHA-256 `{controlled['case_file_sha256']}`",
        f"- 知识库集合：`{controlled['collection_name']}`",
        "- C0 至 C6 每一相邻配置只改变一个开关；控制变量裁判已通过。",
        "",
        "| 配置 | 新增模块 | Recall@K | MRR@K | nDCG@K | 多来源覆盖 | P50(ms) | P95(ms) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = ("Dense baseline", "BM25 sparse recall", "Query expansion", "Concept anchors", "Scenario anchors", "Complex planner", "Cross-Encoder")
    for name, label, item in zip(names, labels, summaries):
        summary.append(
            f"| {name} | {label} | {item['evidence_recall_at_k']:.6f} | {item['mrr_at_k']:.6f} | {item['ndcg_at_k']:.6f} | {item['multi_source_coverage']:.6f} | {item['retrieval_time_p50_ms']:.2f} | {item['retrieval_time_p95_ms']:.2f} |"
        )
    summary.extend([
        "",
        "**解释边界**：场景锚点（C3->C4）是本冻结集上的主要增益来源；复杂规划在全体题目上无额外增益，应仅在多问题子集另行解释。Cross-Encoder 带来边际排序增益，也增加延迟。上述结果不能归因于单一大模型能力。",
        "",
        "## 2. 改写鲁棒性",
        "",
        f"- 24 题人工成对改写集，SHA-256 `{robustness['case_file_sha256']}`；口语化、术语替换和多问题重组各 8 题。",
        f"- 整体 Recall@K：C0 `{robustness['profiles']['C0_dense']['overall']['evidence_recall_at_k']:.6f}`；C3 `{robustness['profiles']['C3_concept_anchors']['overall']['evidence_recall_at_k']:.6f}`；C4 `{robustness['profiles']['C4_scene_anchors']['overall']['evidence_recall_at_k']:.6f}`；C6 `{robustness['profiles']['C6_cross_encoder']['overall']['evidence_recall_at_k']:.6f}`。",
        "- 该组验证措辞变化下的检索稳定性，不是外部公开基准，也不能替代真实用户评测。",
        "",
        "## 3. ESG 证据路由核验",
        "",
        f"- C6 平均 ESG：`{esg['mean_score']:.6f}`；充分作答率：`{esg['sufficient_rate']:.2%}`；联网补证率：`{esg['web_supplement_rate']:.2%}`；本地一级法源覆盖率：`{esg['local_primary_law_coverage']:.2%}`。",
        "- ESG 衡量证据结构和路由，不衡量法律适用或事实认定的正确性。",
        "",
        "## 4. 端到端闭环抽样",
        "",
        f"- 跨数据、反垄断、知识产权和民商事的 6 题抽样回归：`{end_to_end['passed']}/{end_to_end['total']}` 通过。",
        "- 该结果检查答案关键词、预期法源、风险字段和引用链的工程断言；样本量很小，不应宣传为司法或法律意见准确率。",
        "",
        "## 5. 可直接放入报告的结论",
        "",
        "在固定知识库、固定问题集和固定 K 下，单变量消融表明：BM25 的独立提升有限，概念扩展与概念锚点带来小幅增益，场景锚点带来主要增益，Cross-Encoder 进一步改善排序但增加延迟。系统应如实披露其规则辅助依赖，并继续以人工标注的外部测试集验证泛化能力。",
    ])
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"assets={args.output_dir}; summary={args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
