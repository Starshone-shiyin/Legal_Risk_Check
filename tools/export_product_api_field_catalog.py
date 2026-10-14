"""Export a field catalog for fixture-backed product API endpoints.

The catalog is backend handoff data for UI and frontend planning. It reads the
product fixture and endpoint constants only; it does not start a server, call
RAG, contact Qdrant, call an LLM, or fetch market/map/supply-chain data.
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

from src.product.contracts import PRODUCT_ENDPOINTS, SOURCE_VIEW_MODEL_VERSION  # noqa: E402
from src.product.service import DEFAULT_VIEW_MODEL_PATH  # noqa: E402


VERSION = "0.4.18.6"
DEFAULT_OUTPUT_PATH = Path("tests/product_api_field_catalog_v0.4.18.6.json")
MAX_FIELD_PATHS_PER_ENDPOINT = 80


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def type_name(value: Any) -> str:
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return "string"


def field_paths(value: Any, prefix: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}" if prefix else key
            rows.append({"path": child_path, "type": type_name(child), "required": True})
            rows.extend(field_paths(child, child_path))
    elif isinstance(value, list) and value:
        item_prefix = f"{prefix}[]"
        rows.append({"path": item_prefix, "type": type_name(value[0]), "required": True})
        rows.extend(field_paths(value[0], item_prefix))
    return rows


def payload_for_endpoint(source: dict[str, Any], endpoint: dict[str, Any]) -> Any:
    if endpoint["view_model"] == "product_risks":
        return source.get("product_risks", [])
    return source.get("view_models", {}).get(endpoint["view_model"], {})


def endpoint_catalog(source: dict[str, Any], endpoint: dict[str, Any]) -> dict[str, Any]:
    payload = payload_for_endpoint(source, endpoint)
    rows = field_paths(payload)
    return {
        "endpoint_id": endpoint["endpoint_id"],
        "method": endpoint["method"],
        "path": endpoint["path"],
        "view_model": endpoint["view_model"],
        "response_key": endpoint["response_key"],
        "query_params": [
            {
                "name": name,
                "required": False,
                "type": "string",
                "source": "query",
            }
            for name in endpoint["query_params"]
        ],
        "response_envelope": {
            "required_fields": ["status", endpoint["response_key"], "meta"],
            "meta_fields": ["contract_version", "source_view_model_version", "data_source", "runtime_data_access"],
        },
        "field_count": len(rows),
        "field_paths": rows[:MAX_FIELD_PATHS_PER_ENDPOINT],
        "truncated": len(rows) > MAX_FIELD_PATHS_PER_ENDPOINT,
    }


def build_catalog(view_model_path: Path = DEFAULT_VIEW_MODEL_PATH) -> dict[str, Any]:
    source = read_json(view_model_path)
    endpoints = [endpoint_catalog(source, endpoint) for endpoint in PRODUCT_ENDPOINTS]
    return {
        "version": VERSION,
        "scope": "product API field catalog for backend/UI handoff",
        "source_view_model_path": str(view_model_path),
        "source_view_model_version": source.get("version"),
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
            "endpoint_count": len(endpoints),
            "query_param_count": sum(len(endpoint["query_params"]) for endpoint in endpoints),
            "field_path_count": sum(endpoint["field_count"] for endpoint in endpoints),
            "source_version_matches": source.get("version") == SOURCE_VIEW_MODEL_VERSION,
        },
        "endpoints": endpoints,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export product API field catalog.")
    parser.add_argument("--view-models", type=Path, default=DEFAULT_VIEW_MODEL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_catalog(args.view_models)
    write_json(args.output, payload)
    summary = payload["summary"]
    print(
        "Product API field catalog exported: "
        f"{args.output} "
        f"({summary['endpoint_count']} endpoints, {summary['field_path_count']} field paths)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
