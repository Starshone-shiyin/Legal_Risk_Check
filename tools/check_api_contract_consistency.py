"""Check offline API contract artifacts for cross-file consistency.

This checker compares the current in-memory OpenAPI schema, API contract
bundle, field catalog, and example payload fixture. It does not start the
service, call RAG, contact Qdrant, call an LLM, or generate a real report.
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

from src.main import app  # noqa: E402
from tools.export_api_contract_bundle import (  # noqa: E402
    CORE_PATHS,
    DEFAULT_EXAMPLES_PATH,
    ERROR_EXAMPLES,
    build_api_contract_bundle,
)
from tools.export_api_field_catalog import build_api_field_catalog  # noqa: E402
from tools.export_openapi_schema import build_openapi_schema  # noqa: E402


VERSION = "0.4.16.11"
DEFAULT_OUTPUT_PATH = Path("tests/api_contract_consistency_v0.4.16.11_report.json")

MODEL_GROUPS = {
    "requests": ["AskRequest", "RiskAnalyzeRequest", "RiskReportExportRequest"],
    "responses": ["AskResponse", "RiskAnalyzeResponse", "RiskReportResponse"],
}

EXAMPLE_MODEL_MAP = {
    "ask_request": "AskRequest",
    "ask_response": "AskResponse",
    "risk_analyze_request": "RiskAnalyzeRequest",
    "risk_analyze_response": "RiskAnalyzeResponse",
    "risk_report_request": "RiskAnalyzeRequest",
    "risk_report_response": "RiskReportResponse",
    "risk_report_export_json": "RiskReportResponse",
}

ENDPOINT_REF_MAP = {
    "/ask": {"request": "AskRequest", "response": "AskResponse"},
    "/risk/analyze": {"request": "RiskAnalyzeRequest", "response": "RiskAnalyzeResponse"},
    "/risk/report": {"request": "RiskAnalyzeRequest", "response": "RiskReportResponse"},
    "/risk/report/export": {"request": "RiskReportExportRequest", "response": None},
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_ref_name(ref: str | None) -> str | None:
    if not ref:
        return None
    return ref.rsplit("/", 1)[-1]


def model_schemas(openapi: dict[str, Any]) -> dict[str, Any]:
    return openapi.get("components", {}).get("schemas", {})


def schema_fields(schema: dict[str, Any]) -> set[str]:
    return set(schema.get("properties", {}).keys())


def catalog_fields(catalog_model: dict[str, Any]) -> set[str]:
    return {field["name"] for field in catalog_model.get("fields", [])}


def add_issue(issues: list[dict[str, Any]], issue_type: str, message: str, **details: Any) -> None:
    issues.append({"issue_type": issue_type, "message": message, "details": details})


def check_model_catalog_alignment(
    openapi_payload: dict[str, Any],
    field_catalog: dict[str, Any],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    schemas = model_schemas(openapi_payload["openapi"])
    checks = []
    for group, names in MODEL_GROUPS.items():
        for name in names:
            schema = schemas.get(name, {})
            catalog_model = field_catalog.get("models", {}).get(group, {}).get(name, {})
            openapi_fields = schema_fields(schema)
            field_catalog_fields = catalog_fields(catalog_model)
            openapi_required = sorted(schema.get("required", []))
            catalog_required = sorted(catalog_model.get("required_fields", []))
            missing_in_catalog = sorted(openapi_fields - field_catalog_fields)
            extra_in_catalog = sorted(field_catalog_fields - openapi_fields)
            required_mismatch = openapi_required != catalog_required
            field_count_mismatch = len(field_catalog_fields) != catalog_model.get("field_count")
            check = {
                "model": name,
                "group": group,
                "status": "passed",
                "openapi_field_count": len(openapi_fields),
                "catalog_field_count": len(field_catalog_fields),
                "required_fields": openapi_required,
                "missing_in_catalog": missing_in_catalog,
                "extra_in_catalog": extra_in_catalog,
                "required_mismatch": required_mismatch,
                "field_count_mismatch": field_count_mismatch,
            }
            if missing_in_catalog or extra_in_catalog or required_mismatch or field_count_mismatch:
                check["status"] = "failed"
                add_issue(
                    issues,
                    "model_catalog_mismatch",
                    f"{name} differs between OpenAPI schema and field catalog.",
                    model=name,
                    missing_in_catalog=missing_in_catalog,
                    extra_in_catalog=extra_in_catalog,
                    openapi_required=openapi_required,
                    catalog_required=catalog_required,
                    field_count=catalog_model.get("field_count"),
                )
            checks.append(check)
    return checks


def check_example_payloads(
    openapi_payload: dict[str, Any],
    examples: dict[str, Any],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    schemas = model_schemas(openapi_payload["openapi"])
    checks = []
    for example_key, model_name in EXAMPLE_MODEL_MAP.items():
        example = examples.get(example_key)
        schema = schemas.get(model_name, {})
        allowed_fields = schema_fields(schema)
        required_fields = set(schema.get("required", []))
        if not isinstance(example, dict):
            checks.append({"example": example_key, "model": model_name, "status": "failed"})
            add_issue(
                issues,
                "example_payload_missing_or_not_object",
                f"{example_key} is missing or is not a JSON object.",
                example=example_key,
                model=model_name,
            )
            continue
        example_fields = set(example)
        missing_required = sorted(required_fields - example_fields)
        extra_fields = sorted(example_fields - allowed_fields)
        status = "passed" if not missing_required and not extra_fields else "failed"
        checks.append(
            {
                "example": example_key,
                "model": model_name,
                "status": status,
                "field_count": len(example_fields),
                "missing_required": missing_required,
                "extra_fields": extra_fields,
            }
        )
        if status == "failed":
            add_issue(
                issues,
                "example_payload_schema_mismatch",
                f"{example_key} does not match {model_name}.",
                example=example_key,
                model=model_name,
                missing_required=missing_required,
                extra_fields=extra_fields,
            )
    markdown = examples.get("risk_report_export_markdown")
    checks.append(
        {
            "example": "risk_report_export_markdown",
            "model": "text/markdown",
            "status": "passed" if isinstance(markdown, str) and markdown.startswith("# ") else "failed",
        }
    )
    if not isinstance(markdown, str) or not markdown.startswith("# "):
        add_issue(
            issues,
            "example_payload_markdown_mismatch",
            "risk_report_export_markdown must remain a Markdown string starting with a title.",
        )
    return checks


def request_ref_for(openapi: dict[str, Any], path: str) -> str | None:
    post = openapi.get("paths", {}).get(path, {}).get("post", {})
    schema = post.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    return schema_ref_name(schema.get("$ref"))


def response_ref_for(openapi: dict[str, Any], path: str) -> str | None:
    post = openapi.get("paths", {}).get(path, {}).get("post", {})
    schema = post.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})
    return schema_ref_name(schema.get("$ref"))


def check_endpoint_refs(openapi_payload: dict[str, Any], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    openapi = openapi_payload["openapi"]
    checks = []
    for path, expected in ENDPOINT_REF_MAP.items():
        actual_request = request_ref_for(openapi, path)
        actual_response = response_ref_for(openapi, path)
        status = "passed"
        if actual_request != expected["request"] or actual_response != expected["response"]:
            status = "failed"
            add_issue(
                issues,
                "endpoint_ref_mismatch",
                f"{path} request/response schema refs differ from the contract matrix.",
                path=path,
                expected=expected,
                actual={"request": actual_request, "response": actual_response},
            )
        checks.append(
            {
                "path": path,
                "status": status,
                "request_model": actual_request,
                "response_model": actual_response,
            }
        )
    return checks


def check_bundle_alignment(
    openapi_payload: dict[str, Any],
    examples_payload: dict[str, Any],
    bundle: dict[str, Any],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    examples = examples_payload.get("examples", {})
    missing_core_paths = [path for path in CORE_PATHS if path not in bundle.get("openapi", {}).get("paths", {})]
    example_keys = sorted(examples)
    bundle_example_keys = sorted(bundle.get("examples", {}))
    error_keys = sorted(ERROR_EXAMPLES)
    bundle_error_keys = sorted(bundle.get("error_examples", {}))
    checks = {
        "status": "passed",
        "openapi_matches_current": bundle.get("openapi") == openapi_payload.get("openapi"),
        "examples_match_fixture": bundle.get("examples") == examples,
        "missing_core_paths": missing_core_paths,
        "example_keys_match": bundle_example_keys == example_keys,
        "error_example_keys_match": bundle_error_keys == error_keys,
    }
    if not all(
        [
            checks["openapi_matches_current"],
            checks["examples_match_fixture"],
            not missing_core_paths,
            checks["example_keys_match"],
            checks["error_example_keys_match"],
        ]
    ):
        checks["status"] = "failed"
        add_issue(
            issues,
            "bundle_source_mismatch",
            "API contract bundle differs from current generated schema, fixture examples, or error examples.",
            checks=checks,
            bundle_example_keys=bundle_example_keys,
            expected_example_keys=example_keys,
            bundle_error_keys=bundle_error_keys,
            expected_error_keys=error_keys,
        )
    return checks


def check_versions_and_guardrails(
    artifacts: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    guardrail_expectations = {
        "service_started": False,
        "rag_query": "not_called",
        "qdrant_access": "not_called",
        "llm_access": "not_called",
        "report_generation": "not_called",
    }
    checks: dict[str, Any] = {"status": "passed", "artifacts": {}}
    for name, payload in artifacts.items():
        guardrails = payload.get("guardrails", {})
        mismatches = {
            key: {"expected": value, "actual": guardrails.get(key)}
            for key, value in guardrail_expectations.items()
            if key in guardrails and guardrails.get(key) != value
        }
        version = payload.get("version")
        checks["artifacts"][name] = {
            "version": version,
            "version_matches_app": version == app.version,
            "guardrail_mismatches": mismatches,
        }
        if version != app.version or mismatches:
            checks["status"] = "failed"
            add_issue(
                issues,
                "version_or_guardrail_mismatch",
                f"{name} version or guardrails differ from the current offline contract expectation.",
                artifact=name,
                version=version,
                app_version=app.version,
                guardrail_mismatches=mismatches,
            )
    return checks


def build_report(examples_path: Path = DEFAULT_EXAMPLES_PATH) -> dict[str, Any]:
    openapi_payload = build_openapi_schema()
    field_catalog = build_api_field_catalog()
    bundle = build_api_contract_bundle(examples_path)
    examples_payload = read_json(examples_path)
    issues: list[dict[str, Any]] = []

    model_checks = check_model_catalog_alignment(openapi_payload, field_catalog, issues)
    example_checks = check_example_payloads(openapi_payload, examples_payload.get("examples", {}), issues)
    endpoint_checks = check_endpoint_refs(openapi_payload, issues)
    bundle_checks = check_bundle_alignment(openapi_payload, examples_payload, bundle, issues)
    version_checks = check_versions_and_guardrails(
        {
            "openapi_schema": openapi_payload,
            "api_contract_bundle": bundle,
            "api_field_catalog": field_catalog,
        },
        issues,
    )

    return {
        "version": VERSION,
        "app_version": app.version,
        "status": "passed" if not issues else "failed",
        "scope": "offline api contract consistency diagnostics",
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
            "api_contract_bundle": "generated_from_current_fastapi_app_and_examples",
            "api_field_catalog": "generated_from_current_pydantic_models",
            "example_payloads": examples_path.as_posix(),
        },
        "summary": {
            "issue_count": len(issues),
            "model_count": len(model_checks),
            "example_count": len(example_checks),
            "endpoint_count": len(endpoint_checks),
            "checked_core_paths": CORE_PATHS,
        },
        "detected_issues": issues,
        "checks": {
            "model_catalog_alignment": model_checks,
            "example_payload_alignment": example_checks,
            "endpoint_ref_alignment": endpoint_checks,
            "bundle_alignment": bundle_checks,
            "version_and_guardrails": version_checks,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check offline API contract artifact consistency.")
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.examples)
    write_json(args.output, report)
    print(
        "API contract consistency checked: "
        f"{args.output} status={report['status']} issues={report['summary']['issue_count']}"
    )
    return 1 if args.fail_on_error and report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
