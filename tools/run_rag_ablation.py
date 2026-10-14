"""Run reproducible retrieval-only ablation experiments over frozen cases."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.eval_metrics import calculate_case_metrics, summarize_case_metrics
from src.rag.evidence_sufficiency import summarize_evidence_sufficiency
from src.rag.experiment_profiles import list_experiment_profiles, resolve_experiment_profile
from src.rag.retriever import rag_query


DEFAULT_CASES = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT = Path("tests/rag_ablation_report.json")


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("cases", [])


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(
    case: dict[str, Any],
    profile_name: str,
    repeats: int,
    collection_name: str | None,
) -> dict[str, Any]:
    filters = case.get("filters") or {}
    timings: list[float] = []
    result: dict[str, Any] = {}
    for _ in range(repeats):
        started = perf_counter()
        result = rag_query(
            case["question"],
            k=int(case.get("k", 5)),
            debug=True,
            experiment_profile=profile_name,
            retrieval_only=True,
            collection_name=collection_name or "legal_knowledge",
            **filters,
        )
        timings.append((perf_counter() - started) * 1000)
    evidence = result.get("evidence_chain", [])
    metrics = calculate_case_metrics(
        evidence,
        case.get("expected_evidence", []),
        int(case.get("k", 5)),
    )
    metrics["retrieval_elapsed_ms"] = round(sum(timings) / len(timings), 2)
    return {
        "id": case.get("id", ""),
        "question": case["question"],
        "metadata": case.get("metadata", {}),
        "metrics": metrics,
        "evidence_sufficiency": result.get("evidence_sufficiency", {}),
        "evidence": [
            {
                "rank": item.get("rank"),
                "source": item.get("source") or item.get("law_name"),
                "article_no": item.get("article_no"),
                "section_no": item.get("section_no"),
                "section_title": item.get("section_title", ""),
                "block_type": item.get("block_type", ""),
                "citation": item.get("citation", ""),
            }
            for item in evidence
        ],
        "debug": {
            "merged_candidate_count": result.get("debug_info", {}).get("merged_candidate_count", 0),
            "retrieval_elapsed_ms": result.get("retrieval_elapsed_ms"),
            "rerank_mode": result.get("debug_info", {}).get("final_evidence_selection_trace", {}).get("mode"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=["M1_dense", "M2_hybrid", "M3_concept", "M4_full"],
        help="Legacy M1-M4 by default; pass C0-C6 explicitly for controlled ablation.",
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--collection", help="Qdrant collection snapshot used by this experiment")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be >= 1")
    for profile_name in args.profiles:
        resolve_experiment_profile(profile_name)

    cases = load_cases(args.cases)
    report: dict[str, Any] = {
        "schema_version": "rag-ablation-v1",
        "status": "completed",
        "case_file": str(args.cases),
        "case_file_sha256": file_sha256(args.cases),
        "case_count": len(cases),
        "repeats": args.repeats,
        "collection_name": args.collection or "legal_knowledge",
        "profiles": {},
    }
    for profile_name in args.profiles:
        try:
            case_results = [run_case(case, profile_name, args.repeats, args.collection) for case in cases]
        except Exception as exc:
            report["status"] = "blocked"
            report["execution_error"] = {
                "profile": profile_name,
                "type": type(exc).__name__,
                "message": str(exc),
            }
            break
        metric_rows = [row["metrics"] for row in case_results]
        report["profiles"][profile_name] = {
            "definition": resolve_experiment_profile(profile_name).to_dict(),
            "cases": case_results,
            "summary": summarize_case_metrics(metric_rows),
            "evidence_sufficiency_summary": summarize_evidence_sufficiency(
                [row["evidence_sufficiency"] for row in case_results]
            ),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
