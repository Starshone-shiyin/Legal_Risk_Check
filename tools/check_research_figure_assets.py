"""Offline quality checks for the four core-technology research figures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


EXPECTED_SIZE = (2400, 1350)
EXPECTED_DPI = 300
EXPECTED_MODES = {"RGB", "RGBA"}
FIGURE_NAMES = (
    "ablation_evidence_metrics.png",
    "ablation_latency.png",
    "esg_routing_summary.png",
    "esg_score_distribution.png",
)
DEFAULT_FIGURE_DIR = Path("reports/core_tech_20260810")


def _is_300_dpi(dpi: object) -> bool:
    """Accept Pillow's normal PNG DPI rounding representation, e.g. 299.9994."""
    if not isinstance(dpi, tuple) or len(dpi) != 2:
        return False
    try:
        return all(round(float(value)) == EXPECTED_DPI for value in dpi)
    except (TypeError, ValueError):
        return False


def _inspect_figure(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file": path.name,
        "path": str(path),
        "exists": path.is_file(),
        "checks": {},
        "errors": [],
    }
    if not result["exists"]:
        result["errors"].append("missing_file")
        result["status"] = "failed"
        return result

    size_bytes = path.stat().st_size
    result["size_bytes"] = size_bytes
    result["checks"]["non_empty"] = size_bytes > 0
    if not result["checks"]["non_empty"]:
        result["errors"].append("empty_file")
        result["status"] = "failed"
        return result

    try:
        with Image.open(path) as image:
            image.load()
            dpi = image.info.get("dpi")
            result.update({"dimensions": list(image.size), "mode": image.mode, "dpi": list(dpi) if dpi else None})
    except (OSError, ValueError) as error:
        result["errors"].append(f"unreadable_png: {error}")
        result["status"] = "failed"
        return result

    result["checks"]["dimensions_2400x1350"] = tuple(result["dimensions"]) == EXPECTED_SIZE
    result["checks"]["dpi_rounds_to_300"] = _is_300_dpi(dpi)
    result["checks"]["rgb_or_rgba"] = result["mode"] in EXPECTED_MODES
    for check_name, passed in result["checks"].items():
        if not passed:
            result["errors"].append(check_name)
    result["status"] = "passed" if not result["errors"] else "failed"
    return result


def build_report(figure_dir: Path = DEFAULT_FIGURE_DIR) -> dict[str, Any]:
    """Build a JSON-serializable report without invoking any runtime services."""
    figures = [_inspect_figure(figure_dir / name) for name in FIGURE_NAMES]
    failed = [figure["file"] for figure in figures if figure["status"] != "passed"]
    return {
        "schema_version": "research-figure-assets-v1",
        "figure_dir": str(figure_dir),
        "expected_figure_count": len(FIGURE_NAMES),
        "expected_dimensions": list(EXPECTED_SIZE),
        "expected_dpi": EXPECTED_DPI,
        "accepted_modes": sorted(EXPECTED_MODES),
        "figures": figures,
        "summary": {
            "status": "passed" if not failed else "failed",
            "checked_figure_count": len(figures),
            "failed_figure_count": len(failed),
            "failed_figures": failed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON report.")
    args = parser.parse_args()

    report = build_report(args.figure_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["summary"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
