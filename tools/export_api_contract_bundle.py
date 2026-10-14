"""Export an offline API contract bundle for frontend handoff.

The bundle combines the current OpenAPI schema with the saved example payload
fixture. It does not start the service, call RAG, contact Qdrant, call an LLM,
or generate a real report.
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
from tools.export_openapi_schema import build_openapi_schema


DEFAULT_EXAMPLES_PATH = Path("tests/fixtures/api_contract_example_payloads_v0.4.16.4.json")
DEFAULT_OUTPUT_PATH = Path(f"tests/api_contract_bundle_v{app.version}.json")
CORE_PATHS = ["/health", "/ask", "/risk/analyze", "/risk/report", "/risk/report/export"]
ERROR_EXAMPLES = {
    "validation_error_422": {
        "status_code": 422,
        "description": "FastAPI request validation error for invalid or missing fields.",
        "content_type": "application/json",
        "body_shape": {
            "detail": [
                {
                    "loc": ["body", "field_name"],
                    "msg": "Field required or value is invalid.",
                    "type": "validation_error",
                }
            ]
        },
    },
    "llm_timeout_504": {
        "status_code": 504,
        "description": "Unified timeout envelope returned when /ask catches TimeoutError.",
        "content_type": "application/json",
        "body": {
            "error": {
                "code": "LLM_TIMEOUT",
                "message": "AI 模型响应超时，请简化问题后重试。",
            }
        },
    },
    "internal_error_500": {
        "status_code": 500,
        "description": "Unified internal error envelope returned when runtime processing fails.",
        "content_type": "application/json",
        "body": {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "内部服务错误，请稍后重试。",
            }
        },
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_api_contract_bundle(examples_path: Path = DEFAULT_EXAMPLES_PATH) -> dict[str, Any]:
    openapi_payload = build_openapi_schema()
    examples_payload = read_json(examples_path)
    paths = openapi_payload["openapi"].get("paths", {})
    missing_paths = [path for path in CORE_PATHS if path not in paths]

    return {
        "version": app.version,
        "scope": "offline api contract bundle for frontend handoff",
        "guardrails": {
            "service_started": False,
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
            "report_generation": "not_called",
            "frontend_integration": "not_started",
        },
        "sources": {
            "openapi_schema": "generated_from_current_fastapi_app",
            "example_payloads": examples_path.as_posix(),
        },
        "summary": {
            "core_path_count": len(CORE_PATHS),
            "missing_core_paths": missing_paths,
            "example_version": examples_payload.get("version"),
            "example_keys": sorted(examples_payload.get("examples", {}).keys()),
            "error_example_keys": sorted(ERROR_EXAMPLES),
        },
        "openapi": openapi_payload["openapi"],
        "examples": examples_payload.get("examples", {}),
        "error_examples": ERROR_EXAMPLES,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the offline API contract bundle.")
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_api_contract_bundle(args.examples)
    write_json(args.output, payload)
    summary = payload["summary"]
    print(
        "API contract bundle exported: "
        f"{args.output} ({summary['core_path_count']} core paths, "
        f"{len(summary['example_keys'])} example payloads)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
