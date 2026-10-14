"""Validate offline product mock endpoint contracts for UI handoff.

This checker turns the v0.4.18.3 product view model fixture into a thin
mock-endpoint contract for future frontend discussion. It does not add FastAPI
routes, start a service, call RAG, contact Qdrant, fetch market/map data, or
call an LLM.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


VERSION = "0.4.18.4"
SOURCE_VIEW_MODEL_VERSION = "0.4.18.3"
DEFAULT_VIEW_MODEL_PATH = Path("tests/fixtures/product_view_models_v0.4.18.3.json")
DEFAULT_OUTPUT_PATH = Path("tests/product_mock_endpoint_contract_v0.4.18.4_report.json")

MOCK_ENDPOINTS = [
    {
        "endpoint_id": "product_dashboard_summary",
        "method": "GET",
        "path": "/product/dashboard/summary",
        "view_model": "dashboard_summary",
        "response_key": "data",
        "query_params": ["company_id", "as_of"],
        "ui_module": "dashboard",
        "description": "Homepage executive risk dashboard summary.",
    },
    {
        "endpoint_id": "product_legal_workspace",
        "method": "GET",
        "path": "/product/legal/workspace",
        "view_model": "legal_workspace",
        "response_key": "data",
        "query_params": ["workspace_id", "thread_id"],
        "ui_module": "legal_workspace",
        "description": "Legal RAG workspace state for a selected company or thread.",
    },
    {
        "endpoint_id": "product_market_signals",
        "method": "GET",
        "path": "/product/market/signals",
        "view_model": "market_signals",
        "response_key": "data",
        "query_params": ["company_id", "domain", "as_of"],
        "ui_module": "market_signals",
        "description": "External market, regulatory, and event signals linked to product risks.",
    },
    {
        "endpoint_id": "product_supply_chain_map",
        "method": "GET",
        "path": "/product/supply-chain/map",
        "view_model": "supply_chain_map",
        "response_key": "data",
        "query_params": ["company_id", "map_mode"],
        "ui_module": "supply_chain_map",
        "description": "Supply-chain map nodes, edges, overlays, and linked risk identifiers.",
    },
    {
        "endpoint_id": "product_lifecycle_risk",
        "method": "GET",
        "path": "/product/lifecycle/risk",
        "view_model": "lifecycle_risk",
        "response_key": "data",
        "query_params": ["company_id"],
        "ui_module": "lifecycle_risk",
        "description": "Enterprise lifecycle risk stages with evidence and action references.",
    },
    {
        "endpoint_id": "product_risks",
        "method": "GET",
        "path": "/product/risks",
        "view_model": "product_risks",
        "response_key": "items",
        "query_params": ["company_id", "risk_level", "domain", "review_status"],
        "ui_module": "shared",
        "description": "Shared cross-module product risk list referenced by every product view.",
    },
]

EXPECTED_GUARDRAILS = {
    "service_started": False,
    "fastapi_route_added": "promoted_to_fixture_backed_api_in_v0.4.18.5",
    "api_integration": "fixture_backed_product_api_only",
    "frontend_integration": "not_started",
    "rag_query": "not_called",
    "qdrant_access": "not_called",
    "llm_access": "not_called",
    "market_data_access": "not_called",
    "map_data_access": "not_called",
    "supply_chain_data_access": "not_called",
    "report_generation": "not_called",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_issue(issues: list[dict[str, Any]], issue_type: str, message: str, **details: Any) -> None:
    issues.append({"issue_type": issue_type, "message": message, "details": details})


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def collect_risk_ids(payload: dict[str, Any]) -> set[str]:
    return {str(item.get("risk_id")) for item in as_list(payload.get("product_risks")) if item.get("risk_id")}


def response_payload_for(view_model_payload: dict[str, Any], view_model_name: str) -> Any:
    if view_model_name == "product_risks":
        return view_model_payload.get("product_risks", [])
    return view_model_payload.get("view_models", {}).get(view_model_name)


def referenced_risk_ids(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "risk_id" and child:
                refs.add(str(child))
            elif key == "risk_ids" and isinstance(child, list):
                refs.update(str(item) for item in child if item)
            else:
                refs.update(referenced_risk_ids(child))
    elif isinstance(value, list):
        for item in value:
            refs.update(referenced_risk_ids(item))
    return refs


def check_endpoint_specs(
    endpoint_specs: list[dict[str, Any]],
    view_model_payload: dict[str, Any],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    view_models = view_model_payload.get("view_models", {})
    risk_ids = collect_risk_ids(view_model_payload)
    seen_route_keys = Counter((spec.get("method"), spec.get("path")) for spec in endpoint_specs)
    checks = []

    for spec in endpoint_specs:
        endpoint_id = spec.get("endpoint_id")
        method = spec.get("method")
        path = spec.get("path")
        view_model = spec.get("view_model")
        response_key = spec.get("response_key")
        response_payload = response_payload_for(view_model_payload, str(view_model))
        errors = []

        if not endpoint_id:
            errors.append("missing_endpoint_id")
            add_issue(issues, "missing_endpoint_field", "mock endpoint is missing endpoint_id", path=path)
        if method != "GET":
            errors.append("unsupported_method")
            add_issue(issues, "unsupported_method", "product mock endpoints must remain read-only GET contracts", endpoint_id=endpoint_id, method=method)
        if not isinstance(path, str) or not path.startswith("/product/"):
            errors.append("invalid_product_path")
            add_issue(issues, "invalid_product_path", "mock endpoint path must remain under /product/", endpoint_id=endpoint_id, path=path)
        if seen_route_keys[(method, path)] > 1:
            errors.append("duplicate_endpoint_route")
            add_issue(issues, "duplicate_endpoint_route", "mock endpoint route is duplicated", endpoint_id=endpoint_id, method=method, path=path)
        if view_model != "product_risks" and view_model not in view_models:
            errors.append("missing_view_model")
            add_issue(issues, "missing_view_model", "mock endpoint references a missing view model", endpoint_id=endpoint_id, view_model=view_model)
        if response_key not in {"data", "items"}:
            errors.append("invalid_response_key")
            add_issue(issues, "invalid_response_key", "mock endpoint response_key must be data or items", endpoint_id=endpoint_id, response_key=response_key)
        if response_key == "data" and not isinstance(response_payload, dict):
            errors.append("response_payload_not_object")
            add_issue(issues, "response_payload_not_object", "data response payload must be a JSON object", endpoint_id=endpoint_id, view_model=view_model)
        if response_key == "items" and not isinstance(response_payload, list):
            errors.append("response_payload_not_list")
            add_issue(issues, "response_payload_not_list", "items response payload must be a JSON array", endpoint_id=endpoint_id, view_model=view_model)

        unknown_risk_refs = sorted(referenced_risk_ids(response_payload) - risk_ids)
        if unknown_risk_refs:
            errors.append("unknown_risk_ref")
            add_issue(
                issues,
                "unknown_risk_ref",
                "mock endpoint response references unknown risk_id values",
                endpoint_id=endpoint_id,
                risk_ids=unknown_risk_refs,
            )

        checks.append(
            {
                "endpoint_id": endpoint_id,
                "method": method,
                "path": path,
                "view_model": view_model,
                "response_key": response_key,
                "status": "passed" if not errors else "failed",
                "errors": errors,
                "query_params": spec.get("query_params", []),
            }
        )
    return checks


def check_source_fixture(payload: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    errors = []
    if payload.get("version") != SOURCE_VIEW_MODEL_VERSION:
        errors.append("source_version_mismatch")
        add_issue(
            issues,
            "source_version_mismatch",
            "product mock endpoint contract must be derived from the expected view model version",
            expected=SOURCE_VIEW_MODEL_VERSION,
            actual=payload.get("version"),
        )
    if not isinstance(payload.get("product_risks"), list):
        errors.append("missing_product_risks")
        add_issue(issues, "missing_product_risks", "source fixture must include product_risks")
    if not isinstance(payload.get("view_models"), dict):
        errors.append("missing_view_models")
        add_issue(issues, "missing_view_models", "source fixture must include view_models")
    return {"status": "passed" if not errors else "failed", "errors": errors}


def fastapi_surface_check(endpoint_specs: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    main_path = Path("src/main.py")
    content = main_path.read_text(encoding="utf-8") if main_path.exists() else ""
    exposed = sorted(spec["path"] for spec in endpoint_specs if isinstance(spec.get("path"), str) and spec["path"] in content)
    return {
        "status": "passed",
        "checked_file": str(main_path),
        "exposed_paths": exposed,
        "surface_state": "promoted_to_fixture_backed_api" if exposed else "contract_only",
    }


def build_report(
    view_model_path: Path = DEFAULT_VIEW_MODEL_PATH,
    endpoint_specs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    endpoint_specs = endpoint_specs or MOCK_ENDPOINTS
    view_model_payload = read_json(view_model_path)
    issues: list[dict[str, Any]] = []

    source_check = check_source_fixture(view_model_payload, issues)
    endpoint_checks = check_endpoint_specs(endpoint_specs, view_model_payload, issues)
    api_surface = fastapi_surface_check(endpoint_specs, issues)
    issue_counts = Counter(issue["issue_type"] for issue in issues)

    endpoint_contract = []
    for spec in endpoint_specs:
        response_payload = response_payload_for(view_model_payload, str(spec.get("view_model")))
        endpoint_contract.append(
            {
                **spec,
                "mock_only": True,
                "exposed_by_fastapi": False,
                "response_envelope": {
                    "status": "ok",
                    spec["response_key"]: response_payload,
                    "meta": {
                        "contract_version": VERSION,
                        "source_view_model_version": SOURCE_VIEW_MODEL_VERSION,
                        "mock_only": True,
                    },
                },
            }
        )

    return {
        "version": VERSION,
        "scope": "offline product mock endpoint contract for UI handoff",
        "source_view_model_path": str(view_model_path),
        "source_view_model_version": view_model_payload.get("version"),
        "guardrails": EXPECTED_GUARDRAILS,
        "status": "passed" if not issues else "failed",
        "summary": {
            "issue_count": len(issues),
            "endpoint_count": len(endpoint_specs),
            "view_endpoint_count": sum(1 for spec in endpoint_specs if spec.get("view_model") != "product_risks"),
            "shared_endpoint_count": sum(1 for spec in endpoint_specs if spec.get("view_model") == "product_risks"),
            "product_risk_count": len(collect_risk_ids(view_model_payload)),
        },
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "issues": issues,
        "checks": {
            "source_fixture": source_check,
            "endpoint_contract": endpoint_checks,
            "fastapi_surface": api_surface,
        },
        "endpoint_contract": endpoint_contract,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate offline product mock endpoint contract.")
    parser.add_argument("--view-models", type=Path, default=DEFAULT_VIEW_MODEL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.view_models)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Product mock endpoint contract check completed: "
        f"{report['status']}, "
        f"{summary['endpoint_count']} endpoints, "
        f"{summary['issue_count']} issues"
    )
    print(f"Report saved: {args.output}")
    return 1 if args.fail_on_error and report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
