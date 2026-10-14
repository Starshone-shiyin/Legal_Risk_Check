"""Build a closeout report for the fixture-backed product backend.

The report summarizes existing product backend contracts and handoff artifacts.
It does not start a server, run eval, call RAG, contact Qdrant, call an LLM, or
connect market/map/supply-chain data sources.
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


VERSION = "0.4.18.9"
DEFAULT_OUTPUT_PATH = Path("tests/product_backend_closeout_v0.4.18.9_report.json")

REQUIRED_ARTIFACTS = [
    Path("tests/fixtures/product_view_models_v0.4.18.3.json"),
    Path("tests/product_view_model_contract_v0.4.18.3_report.json"),
    Path("tests/product_mock_endpoint_contract_v0.4.18.4_report.json"),
    Path("tests/product_api_contract_v0.4.18.5_report.json"),
    Path("tests/product_api_field_catalog_v0.4.18.6.json"),
    Path("tests/product_api_status_catalog_v0.4.18.7.json"),
    Path("tests/product_data_source_boundary_v0.4.18.8.json"),
    Path("docs/product_api_backend_integration_v0.4.18.5.md"),
    Path("docs/product_api_field_catalog_v0.4.18.6.md"),
    Path("docs/product_api_status_catalog_v0.4.18.7.md"),
    Path("docs/product_data_source_boundary_v0.4.18.8.md"),
]

READ_ORDER = [
    "docs/product_design_brief_v0.4.18.2.md",
    "docs/product_view_model_contract_v0.4.18.3.md",
    "docs/product_mock_endpoint_contract_v0.4.18.4.md",
    "docs/product_api_backend_integration_v0.4.18.5.md",
    "docs/product_api_field_catalog_v0.4.18.6.md",
    "docs/product_api_status_catalog_v0.4.18.7.md",
    "docs/product_data_source_boundary_v0.4.18.8.md",
    "docs/product_backend_closeout_v0.4.18.9.md",
]

ACCEPTANCE_COMMANDS = [
    ".\\venv\\Scripts\\python.exe -m unittest tests.test_product_api_contract tests.test_product_api_field_catalog tests.test_product_api_status_catalog tests.test_product_data_source_boundary tests.test_product_backend_closeout",
    ".\\venv\\Scripts\\python.exe tools\\build_product_backend_closeout.py --output tests\\product_backend_closeout_v0.4.18.9_report.json",
    ".\\venv\\Scripts\\python.exe tools\\run_project_health_check.py --output tests\\project_health_check_report.json --fail-on-error",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def artifact_rows(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in REQUIRED_ARTIFACTS:
        full_path = root / path
        data = read_json(full_path) if path.suffix == ".json" else {}
        rows.append(
            {
                "path": path.as_posix(),
                "present": full_path.exists(),
                "version": data.get("version"),
                "status": data.get("status"),
            }
        )
    return rows


def build_report(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    artifacts = artifact_rows(root)
    missing = [row["path"] for row in artifacts if not row["present"]]
    api_contract = read_json(root / "tests/product_api_contract_v0.4.18.5_report.json")
    field_catalog = read_json(root / "tests/product_api_field_catalog_v0.4.18.6.json")
    status_catalog = read_json(root / "tests/product_api_status_catalog_v0.4.18.7.json")
    data_boundary = read_json(root / "tests/product_data_source_boundary_v0.4.18.8.json")

    api_summary = api_contract.get("summary", {})
    field_summary = field_catalog.get("summary", {})
    status_summary = status_catalog.get("summary", {})
    boundary_summary = data_boundary.get("summary", {})
    guardrails = data_boundary.get("guardrails", {})

    blockers: list[str] = []
    if missing:
        blockers.append("required_artifacts_missing")
    if api_contract.get("status") != "passed":
        blockers.append("product_api_contract_not_passed")
    if api_summary.get("endpoint_count") != len(PRODUCT_ENDPOINTS):
        blockers.append("product_endpoint_count_mismatch")
    if api_summary.get("openapi_passed") != len(PRODUCT_ENDPOINTS):
        blockers.append("product_openapi_not_fully_passed")
    if api_summary.get("response_passed") != len(PRODUCT_ENDPOINTS):
        blockers.append("product_response_contract_not_fully_passed")
    if not field_summary.get("source_version_matches"):
        blockers.append("product_field_catalog_source_version_mismatch")
    if status_summary.get("error_code_count", 0) < 6:
        blockers.append("product_status_catalog_too_small")
    if boundary_summary.get("currently_connected_provider_count") != 1:
        blockers.append("product_boundary_connected_provider_count_drift")
    if guardrails.get("real_data_source_connected") is not False:
        blockers.append("product_boundary_real_data_source_connected")

    status = "passed" if not blockers else "blocked"
    return {
        "version": VERSION,
        "scope": "product backend closeout and handoff runbook",
        "status": status,
        "guardrails": {
            "saved_report_only": True,
            "server_started": False,
            "full_eval": "not_run",
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
            "market_data_access": "not_called",
            "map_data_access": "not_called",
            "supply_chain_data_access": "not_called",
            "real_data_source_connected": False,
        },
        "summary": {
            "backend_design_status": "basically_complete" if status == "passed" else "attention_required",
            "endpoint_count": len(PRODUCT_ENDPOINTS),
            "openapi_passed": api_summary.get("openapi_passed"),
            "response_passed": api_summary.get("response_passed"),
            "field_catalog_endpoint_count": field_summary.get("endpoint_count"),
            "status_catalog_error_code_count": status_summary.get("error_code_count"),
            "currently_connected_provider_count": boundary_summary.get("currently_connected_provider_count"),
            "future_provider_slot_count": boundary_summary.get("future_allowed_provider_count"),
            "blocker_count": len(blockers),
        },
        "blockers": blockers,
        "artifacts": artifacts,
        "read_order": READ_ORDER,
        "stable_endpoints": [
            {
                "method": endpoint["method"],
                "path": endpoint["path"],
                "response_key": endpoint["response_key"],
                "query_params": endpoint["query_params"],
            }
            for endpoint in PRODUCT_ENDPOINTS
        ],
        "frontend_handoff": {
            "allowed_now": [
                "Use fixture-backed GET /product/* endpoints for UI prototype wiring.",
                "Use field catalog for labels, nested paths, and optional query params.",
                "Use status/error catalog for empty state and public error handling.",
                "Use data source boundary to keep future providers behind repository implementations.",
            ],
            "not_allowed_yet": [
                "Do not treat /product/legal/workspace as live RAG answer generation.",
                "Do not connect real RAG, market, map, supply-chain, or permission providers in this closeout.",
                "Do not change anchors, prompts, rerank, risk supplement, taxonomy, scenario registry, or eval cases.",
            ],
        },
        "future_provider_sequence": [
            "Pick one provider first, preferably legal_rag_summary_provider or market_signal_provider.",
            "Implement provider behind ProductViewRepository or a versioned provider adapter.",
            "Add targeted smoke tests and degraded/unavailable status handling before replacing fixture payloads.",
            "Only then allow UI to opt into non-fixture data for that provider.",
        ],
        "acceptance_commands": ACCEPTANCE_COMMANDS,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build product backend closeout report.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Product backend closeout completed: "
        f"{report['status']}, "
        f"{summary['endpoint_count']} endpoints, "
        f"{summary['blocker_count']} blockers"
    )
    print(f"Report saved: {args.output}")
    return 1 if args.fail_on_error and report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
