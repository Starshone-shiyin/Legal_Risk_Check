"""Build v0.4.15.20 explicit dense live probe report.

This is a thin wrapper around the v0.4.15.19 live read-only probe. Dense probing
is explicit here because it may call the external embedding service to generate
query vectors. Qdrant access remains read-only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.build_base_candidate_live_readonly_probe import (
    DEFAULT_COLLECTION,
    DEFAULT_MISMATCH_PATH,
    DEFAULT_TRACE_PATH,
    build_report as build_live_readonly_report,
    write_json,
)


VERSION = "0.4.15.20"

DEFAULT_OUTPUT_PATH = Path("tests/base_candidate_dense_live_probe_v0.4.15.20_report.json")


def build_dense_report(
    *,
    mismatch_path: Path = DEFAULT_MISMATCH_PATH,
    trace_path: Path = DEFAULT_TRACE_PATH,
    collection_name: str = DEFAULT_COLLECTION,
    sparse_runtime_k: int = 10,
    sparse_high_k: int = 100,
    dense_runtime_k: int = 5,
    dense_high_k: int = 100,
    max_ref_points: int = 20,
) -> dict[str, Any]:
    report = build_live_readonly_report(
        mismatch_path=mismatch_path,
        trace_path=trace_path,
        collection_name=collection_name,
        sparse_runtime_k=sparse_runtime_k,
        sparse_high_k=sparse_high_k,
        dense_runtime_k=dense_runtime_k,
        dense_high_k=dense_high_k,
        max_ref_points=max_ref_points,
        enable_dense_probe=True,
    )
    report["version"] = VERSION
    report["schema_kind"] = "base_candidate_dense_live_probe"
    report["scope"] = "explicit dense-enabled live read-only probe for missing base union final refs"
    report.setdefault("guardrails", {})["dense_probe"] = "explicit_opt_in_embedding_service_call"
    report.setdefault("summary", {})["dense_probe_enabled"] = True
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build explicit dense live read-only probe report.")
    parser.add_argument("--mismatch", type=Path, default=DEFAULT_MISMATCH_PATH)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--sparse-runtime-k", type=int, default=10)
    parser.add_argument("--sparse-high-k", type=int, default=100)
    parser.add_argument("--dense-runtime-k", type=int, default=5)
    parser.add_argument("--dense-high-k", type=int, default=100)
    parser.add_argument("--max-ref-points", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_dense_report(
        mismatch_path=args.mismatch,
        trace_path=args.trace,
        collection_name=args.collection,
        sparse_runtime_k=args.sparse_runtime_k,
        sparse_high_k=args.sparse_high_k,
        dense_runtime_k=args.dense_runtime_k,
        dense_high_k=args.dense_high_k,
        max_ref_points=args.max_ref_points,
    )
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Base candidate dense live probe completed: "
        f"{summary['status']}, refs={summary['missing_ref_count']}, "
        f"attribution_counts={summary['attribution_counts']}"
    )
    return 0 if report["collection_probe"]["reachable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
