"""Export product data source/repository boundary catalog.

The catalog documents how fixture-backed product APIs can later swap data
providers without changing routers. It does not connect real data sources,
call RAG, contact Qdrant, call an LLM, or fetch market/map/supply-chain data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.product.contracts import PRODUCT_ENDPOINTS  # noqa: E402
from src.product.repository import PRODUCT_DATA_SOURCE_BOUNDARY  # noqa: E402


DEFAULT_OUTPUT_PATH = Path("tests/product_data_source_boundary_v0.4.18.8.json")


def build_catalog() -> dict[str, Any]:
    return {
        "version": "0.4.18.8",
        "scope": "product API data source and repository boundary",
        "guardrails": {
            "real_data_source_connected": False,
            "server_started": False,
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
            "market_data_access": "not_called",
            "map_data_access": "not_called",
            "supply_chain_data_access": "not_called",
            "report_generation": "not_called",
        },
        "summary": {
            "endpoint_count": len(PRODUCT_ENDPOINTS),
            "currently_connected_provider_count": len(PRODUCT_DATA_SOURCE_BOUNDARY["currently_connected_providers"]),
            "future_allowed_provider_count": len(PRODUCT_DATA_SOURCE_BOUNDARY["future_allowed_providers"]),
            "default_repository": PRODUCT_DATA_SOURCE_BOUNDARY["default_repository"],
        },
        "boundary": PRODUCT_DATA_SOURCE_BOUNDARY,
        "handoff_rules": [
            "Future providers should implement ProductViewRepository instead of changing router functions.",
            "RAG, market, map, supply-chain, and permission providers must be introduced in separate versions with dedicated tests.",
            "Response envelope and status/error catalog must remain stable unless a versioned contract update says otherwise.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export product data source boundary catalog.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_catalog()
    write_json(args.output, payload)
    summary = payload["summary"]
    print(
        "Product data source boundary exported: "
        f"{args.output} "
        f"({summary['currently_connected_provider_count']} connected provider, "
        f"{summary['future_allowed_provider_count']} future provider slots)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
