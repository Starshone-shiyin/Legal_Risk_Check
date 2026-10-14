"""Summarize the paired 24-question robustness evaluation by perturbation type."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.eval_metrics import summarize_case_metrics


REQUIRED_PROFILES = ("C0_dense", "C3_concept_anchors", "C4_scene_anchors", "C6_cross_encoder")
REQUIRED_TYPES = ("colloquial", "term_substitution", "multi_issue")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(case_path: Path, run_path: Path) -> dict[str, Any]:
    cases = _load(case_path).get("cases", [])
    run = _load(run_path)
    case_types = {str(case["id"]): str(case.get("metadata", {}).get("perturbation_type", "")) for case in cases}
    counts = Counter(case_types.values())
    profiles = run.get("profiles", {})
    result: dict[str, Any] = {
        "schema_version": "rag-robustness-perturbation-summary-v1",
        "case_file": str(case_path),
        "case_file_sha256": run.get("case_file_sha256"),
        "case_count": len(cases),
        "collection_name": run.get("collection_name"),
        "profiles": {},
        "checks": {
            "case_count_24": len(cases) == 24,
            "three_balanced_perturbation_types": all(counts[item] == 8 for item in REQUIRED_TYPES),
            "required_profiles_present": all(item in profiles for item in REQUIRED_PROFILES),
            "run_completed": run.get("status") == "completed",
        },
    }
    for profile_name in REQUIRED_PROFILES:
        profile = profiles.get(profile_name, {})
        rows = profile.get("cases", [])
        by_type: dict[str, dict[str, float]] = {}
        for perturbation_type in REQUIRED_TYPES:
            metrics = [row.get("metrics", {}) for row in rows if case_types.get(str(row.get("id"))) == perturbation_type]
            by_type[perturbation_type] = summarize_case_metrics(metrics) if metrics else {}
        result["profiles"][profile_name] = {
            "definition": profile.get("definition", {}),
            "overall": profile.get("summary", {}),
            "by_perturbation_type": by_type,
        }
    result["verdict"] = "accepted" if all(result["checks"].values()) else "rejected"
    result["scope"] = (
        "Internal paired-rewrite retrieval robustness evaluation. Metrics measure expected evidence ranking, "
        "not legal-answer accuracy or external generalization."
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.cases, args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
