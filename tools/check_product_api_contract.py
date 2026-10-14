"""Validate fixture-backed product API endpoints.

This checker exercises the in-memory FastAPI app with TestClient. It does not
start a server, call RAG, contact Qdrant, fetch market/map data, call an LLM,
or generate a real risk report.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.main import app  # noqa: E402
from src.product.contracts import PRODUCT_API_VERSION, PRODUCT_ENDPOINTS, SOURCE_VIEW_MODEL_VERSION  # noqa: E402


VERSION = "0.4.18.5"
DEFAULT_OUTPUT_PATH = Path("tests/product_api_contract_v0.4.18.5_report.json")
EXPECTED_RUNTIME_ACCESS = {
    "rag": "not_called",
    "qdrant": "not_called",
    "llm": "not_called",
    "market_data": "not_called",
    "map_data": "not_called",
    "supply_chain_data": "not_called",
}


def add_issue(issues: list[dict[str, Any]], issue_type: str, message: str, **details: Any) -> None:
    issues.append({"issue_type": issue_type, "message": message, "details": details})


def check_openapi_paths(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = app.openapi().get("paths", {})
    checks = []
    for endpoint in PRODUCT_ENDPOINTS:
        path = endpoint["path"]
        method = endpoint["method"].lower()
        has_path = path in paths
        has_method = has_path and method in paths[path]
        status = "passed" if has_method else "failed"
        if status == "failed":
            add_issue(
                issues,
                "openapi_product_path_missing",
                "product endpoint is missing from OpenAPI",
                path=path,
                method=method,
            )
        checks.append({"path": path, "method": method, "status": status})
    return checks


def check_runtime_responses(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    client = TestClient(app)
    checks = []
    for endpoint in PRODUCT_ENDPOINTS:
        response = client.get(endpoint["path"])
        errors = []
        if response.status_code != 200:
            errors.append("non_200_status")
            add_issue(
                issues,
                "product_endpoint_non_200",
                "product endpoint must return 200 for fixture-backed sample data",
                path=endpoint["path"],
                status_code=response.status_code,
            )
            payload: dict[str, Any] = {}
        else:
            payload = response.json()

        response_key = endpoint["response_key"]
        if payload.get("status") != "ok":
            errors.append("status_not_ok")
            add_issue(issues, "product_response_status_not_ok", "product response status must be ok", path=endpoint["path"])
        if response_key not in payload:
            errors.append("missing_response_key")
            add_issue(
                issues,
                "product_response_key_missing",
                "product response is missing the contracted data/items key",
                path=endpoint["path"],
                response_key=response_key,
            )
        elif response_key == "data" and not isinstance(payload[response_key], dict):
            errors.append("data_not_object")
            add_issue(issues, "product_response_data_not_object", "product data response must be an object", path=endpoint["path"])
        elif response_key == "items" and not isinstance(payload[response_key], list):
            errors.append("items_not_list")
            add_issue(issues, "product_response_items_not_list", "product items response must be a list", path=endpoint["path"])

        meta = payload.get("meta", {})
        if meta.get("contract_version") != PRODUCT_API_VERSION:
            errors.append("contract_version_mismatch")
            add_issue(
                issues,
                "product_contract_version_mismatch",
                "product response contract_version mismatch",
                path=endpoint["path"],
                expected=PRODUCT_API_VERSION,
                actual=meta.get("contract_version"),
            )
        if meta.get("source_view_model_version") != SOURCE_VIEW_MODEL_VERSION:
            errors.append("source_view_model_version_mismatch")
            add_issue(
                issues,
                "product_source_version_mismatch",
                "product response source_view_model_version mismatch",
                path=endpoint["path"],
                expected=SOURCE_VIEW_MODEL_VERSION,
                actual=meta.get("source_view_model_version"),
            )
        if meta.get("data_source") != "fixture_sample":
            errors.append("data_source_not_fixture_sample")
            add_issue(
                issues,
                "product_data_source_mismatch",
                "product response must disclose fixture_sample data source",
                path=endpoint["path"],
                actual=meta.get("data_source"),
            )
        runtime_access = meta.get("runtime_data_access", {})
        for key, expected in EXPECTED_RUNTIME_ACCESS.items():
            if runtime_access.get(key) != expected:
                errors.append(f"{key}_access_mismatch")
                add_issue(
                    issues,
                    "product_runtime_access_mismatch",
                    "product response runtime_data_access must remain not_called",
                    path=endpoint["path"],
                    key=key,
                    expected=expected,
                    actual=runtime_access.get(key),
                )

        checks.append(
            {
                "path": endpoint["path"],
                "response_key": response_key,
                "status": "passed" if not errors else "failed",
                "errors": errors,
            }
        )
    return checks


def build_report() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    openapi_checks = check_openapi_paths(issues)
    response_checks = check_runtime_responses(issues)
    issue_counts = Counter(issue["issue_type"] for issue in issues)
    return {
        "version": VERSION,
        "scope": "fixture-backed product API contract check",
        "status": "passed" if not issues else "failed",
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
            "issue_count": len(issues),
            "endpoint_count": len(PRODUCT_ENDPOINTS),
            "openapi_passed": sum(1 for check in openapi_checks if check["status"] == "passed"),
            "response_passed": sum(1 for check in response_checks if check["status"] == "passed"),
        },
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "issues": issues,
        "checks": {
            "openapi_paths": openapi_checks,
            "runtime_responses": response_checks,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate fixture-backed product API contract.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Product API contract check completed: "
        f"{report['status']}, "
        f"{summary['endpoint_count']} endpoints, "
        f"{summary['issue_count']} issues"
    )
    print(f"Report saved: {args.output}")
    return 1 if args.fail_on_error and report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
