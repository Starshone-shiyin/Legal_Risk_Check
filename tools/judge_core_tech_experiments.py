"""Validate the complete 2026-08-15 core-technology experiment packet offline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROFILES = (
    "C0_dense",
    "C1_hybrid",
    "C2_query_expansion",
    "C3_concept_anchors",
    "C4_scene_anchors",
    "C5_complex_planner",
    "C6_cross_encoder",
)
FIGURES = (
    "controlled_ablation_quality.png",
    "controlled_ablation_latency.png",
    "rewritten_question_robustness.png",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_figures(directory: Path) -> tuple[bool, list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    for name in FIGURES:
        path = directory / name
        item: dict[str, Any] = {"file": str(path), "passed": False}
        if path.is_file() and path.stat().st_size > 0:
            with Image.open(path) as image:
                dpi = image.info.get("dpi", (0, 0))
                item.update({
                    "dimensions": list(image.size),
                    "mode": image.mode,
                    "dpi": list(dpi),
                    "passed": (
                        image.size == (2400, 1350)
                        and image.mode in {"RGB", "RGBA"}
                        and all(round(float(value)) == 300 for value in dpi)
                    ),
                })
        details.append(item)
    return all(item["passed"] for item in details), details


def build_report(root: Path = ROOT) -> dict[str, Any]:
    """Return a deterministic, JSON-serializable judgment for the experiment packet."""
    controlled = _load(root / "tests/rag_controlled_ablation_20260815_recomputed.json")
    controlled_judge = _load(root / "tests/rag_controlled_ablation_20260815_judge.json")
    esg_judge = _load(root / "tests/rag_controlled_ablation_20260815_esg_judge.json")
    robustness = _load(root / "tests/rag_robustness_perturbation_20260815_summary.json")
    end_to_end = _load(root / "tests/rag_end_to_end_sample_20260815.json")

    profiles = controlled.get("profiles", {})
    profile_set_ok = all(name in profiles for name in EXPECTED_PROFILES)
    summaries_ok = profile_set_ok and all(
        all(key in profiles[name].get("summary", {}) for key in (
            "evidence_recall_at_k", "mrr_at_k", "ndcg_at_k", "retrieval_time_p50_ms", "retrieval_time_p95_ms",
        ))
        for name in EXPECTED_PROFILES
    )
    robustness_profiles = robustness.get("profiles", {})
    robustness_ok = (
        robustness.get("verdict") == "accepted"
        and robustness.get("case_count") == 24
        and all(name in robustness_profiles for name in ("C0_dense", "C3_concept_anchors", "C4_scene_anchors", "C6_cross_encoder"))
    )
    end_to_end_ok = end_to_end.get("passed") == end_to_end.get("total") == 6
    figures_ok, figure_details = _check_figures(root / "reports/core_tech_20260815")

    checks = {
        "controlled_ablation_judge_accepted": controlled_judge.get("verdict") == "accepted",
        "esg_judge_accepted": esg_judge.get("verdict") == "accepted",
        "controlled_case_count_60": controlled.get("case_count") == 60,
        "controlled_profiles_complete": profile_set_ok,
        "controlled_summaries_complete": summaries_ok,
        "paired_perturbation_robustness_complete": robustness_ok,
        "end_to_end_sample_6_of_6": end_to_end_ok,
        "research_figures_pass": figures_ok,
    }
    verdict = "accepted" if all(checks.values()) else "rejected"
    return {
        "schema_version": "core-tech-experiment-packet-judge-v1",
        "verdict": verdict,
        "checks": checks,
        "controlled_collection": controlled.get("collection_name"),
        "controlled_case_file_sha256": controlled.get("case_file_sha256"),
        "figure_details": figure_details,
        "scope": (
            "Validates experiment artifact completeness and internal consistency. "
            "It does not measure legal conclusion correctness or production performance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tests/core_tech_experiment_final_judge_20260815.json")
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
