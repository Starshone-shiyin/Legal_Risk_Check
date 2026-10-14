"""Export the FastAPI OpenAPI schema without starting the service.

This is an offline API-contract helper for frontend handoff. It imports the
FastAPI app and writes app.openapi() to JSON. It does not call RAG, Qdrant, LLM,
or report generation.
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

from src.main import app


DEFAULT_OUTPUT_PATH = Path(f"tests/openapi_schema_v{app.version}.json")


def build_openapi_schema() -> dict[str, Any]:
    schema = app.openapi()
    return {
        "version": app.version,
        "scope": "offline openapi schema snapshot for api contract handoff",
        "guardrails": {
            "service_started": False,
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
            "report_generation": "not_called",
        },
        "openapi": schema,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the FastAPI OpenAPI schema.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_openapi_schema()
    write_json(args.output, payload)
    paths = payload.get("openapi", {}).get("paths", {})
    print(f"OpenAPI schema exported: {args.output} ({len(paths)} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
