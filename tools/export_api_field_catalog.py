"""Export a field catalog for the public API request/response models.

The catalog is offline documentation data for frontend/workbench handoff. It
imports Pydantic models only; it does not start the service, call RAG, contact
Qdrant, call an LLM, or generate a real report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic_core import PydanticUndefined

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.main import (  # noqa: E402
    AskRequest,
    AskResponse,
    RiskAnalyzeRequest,
    RiskReportExportRequest,
    RiskAnalyzeResponse,
    RiskReportResponse,
    app,
)


DEFAULT_OUTPUT_PATH = Path(f"tests/api_field_catalog_v{app.version}.json")
MODEL_GROUPS = {
    "requests": {
        "AskRequest": AskRequest,
        "RiskAnalyzeRequest": RiskAnalyzeRequest,
        "RiskReportExportRequest": RiskReportExportRequest,
    },
    "responses": {
        "AskResponse": AskResponse,
        "RiskAnalyzeResponse": RiskAnalyzeResponse,
        "RiskReportResponse": RiskReportResponse,
    },
}


def field_default(field: Any) -> Any:
    if field.default is PydanticUndefined:
        return None
    return field.default


def field_catalog(model: type) -> dict[str, Any]:
    schema = model.model_json_schema()
    required = set(schema.get("required", []))
    fields = []
    for name, field in model.model_fields.items():
        property_schema = schema.get("properties", {}).get(name, {})
        fields.append(
            {
                "name": name,
                "required": name in required,
                "annotation": str(field.annotation),
                "default": field_default(field),
                "title": property_schema.get("title"),
                "description": property_schema.get("description"),
                "json_schema": property_schema,
            }
        )
    return {
        "required_fields": sorted(required),
        "field_count": len(fields),
        "fields": fields,
    }


def build_api_field_catalog() -> dict[str, Any]:
    model_catalog = {
        group: {name: field_catalog(model) for name, model in models.items()}
        for group, models in MODEL_GROUPS.items()
    }
    return {
        "version": app.version,
        "scope": "offline api field catalog for frontend handoff",
        "guardrails": {
            "service_started": False,
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
            "report_generation": "not_called",
            "frontend_integration": "not_started",
        },
        "models": model_catalog,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the offline API field catalog.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_api_field_catalog()
    write_json(args.output, payload)
    total_fields = sum(
        model["field_count"]
        for group in payload["models"].values()
        for model in group.values()
    )
    print(f"API field catalog exported: {args.output} ({total_fields} fields)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
