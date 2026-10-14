"""Recompute retrieval metrics from a completed ablation report without re-querying RAG."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.eval_metrics import calculate_case_metrics, summarize_case_metrics


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload if isinstance(payload, list) else payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("case file must contain a list of cases")
    return cases


def recompute(report: dict[str, Any], cases: list[dict[str, Any]], case_file: Path) -> dict[str, Any]:
    if report.get("status") != "completed":
        raise ValueError("only completed ablation reports can be recomputed")
    case_by_id = {str(case.get("id", "")): case for case in cases}
    if len(case_by_id) != len(cases):
        raise ValueError("frozen case identifiers must be unique")
    if report.get("case_file_sha256") and report["case_file_sha256"] != _sha256(case_file):
        raise ValueError("frozen case file hash does not match the report")

    output = json.loads(json.dumps(report))
    for profile in output.get("profiles", {}).values():
        rows = profile.get("cases")
        if not isinstance(rows, list):
            raise ValueError("profile cases must be a list")
        for row in rows:
            case = case_by_id.get(str(row.get("id", "")))
            if case is None:
                raise ValueError(f"report case is absent from frozen set: {row.get('id')!r}")
            metric = calculate_case_metrics(
                row.get("evidence") or [],
                case.get("expected_evidence") or [],
                int(case.get("k", 5)),
            )
            metric["retrieval_elapsed_ms"] = row.get("metrics", {}).get("retrieval_elapsed_ms", 0.0)
            row["metrics"] = metric
        profile["summary"] = summarize_case_metrics([row["metrics"] for row in rows])

    output["metric_recalculation"] = {
        "method": "offline_from_saved_evidence_chain",
        "reason": "apply one-to-one expected-evidence matching for bounded nDCG@K",
        "input_report_sha256": report.get("_input_sha256", ""),
        "frozen_case_sha256": _sha256(case_file),
        "reran_rag": False,
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    report["_input_sha256"] = _sha256(args.report)
    case_file = args.cases or Path(report.get("case_file", ""))
    if not case_file.exists():
        raise SystemExit(f"case file does not exist: {case_file}")
    output = recompute(report, _load_cases(case_file), case_file)
    output.pop("_input_sha256", None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"recomputed metrics written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
