"""Export product API status and error catalog.

The catalog documents success states, empty-result semantics, and product API
error codes. It does not start a server, call RAG, contact Qdrant, call an LLM,
or fetch market/map/supply-chain data.
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
from src.product.status import PRODUCT_ERROR_CATALOG, PRODUCT_STATUS_CATALOG_VERSION, PRODUCT_SUCCESS_STATES  # noqa: E402


DEFAULT_OUTPUT_PATH = Path("tests/product_api_status_catalog_v0.4.18.7.json")


def build_catalog() -> dict[str, Any]:
    return {
        "version": PRODUCT_STATUS_CATALOG_VERSION,
        "scope": "product API status and error catalog for frontend/backend handoff",
        "guardrails": {
            "server_started": False,
            "data_source": "fixture_sample",
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
            "success_state_count": len(PRODUCT_SUCCESS_STATES),
            "error_code_count": len(PRODUCT_ERROR_CATALOG),
            "blocking_error_count": sum(1 for item in PRODUCT_ERROR_CATALOG if item["frontend_severity"] == "blocking"),
            "degraded_error_count": sum(1 for item in PRODUCT_ERROR_CATALOG if item["frontend_severity"] == "degraded"),
        },
        "success_states": PRODUCT_SUCCESS_STATES,
        "error_codes": PRODUCT_ERROR_CATALOG,
        "empty_result_semantics": {
            "path": "/product/risks",
            "http_status": 200,
            "response_key": "items",
            "empty_value": [],
            "frontend_action": "展示空态，不作为系统错误处理。",
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export product API status and error catalog.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_catalog()
    write_json(args.output, payload)
    summary = payload["summary"]
    print(
        "Product API status catalog exported: "
        f"{args.output} "
        f"({summary['success_state_count']} success states, {summary['error_code_count']} error codes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
