"""Validate offline product view model fixtures for UI handoff.

This checker validates the product-facing data shapes that future frontend
pages can consume. It does not start the API, call RAG, contact Qdrant, fetch
market/map data, or call an LLM.
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


VERSION = "0.4.18.3"
DEFAULT_FIXTURE_PATH = Path("tests/fixtures/product_view_models_v0.4.18.3.json")
DEFAULT_OUTPUT_PATH = Path("tests/product_view_model_contract_v0.4.18.3_report.json")

REQUIRED_VIEW_MODELS = [
    "dashboard_summary",
    "legal_workspace",
    "market_signals",
    "supply_chain_map",
    "lifecycle_risk",
]

EXPECTED_GUARDRAILS = {
    "ui_implementation": "not_started",
    "api_integration": "not_started",
    "rag_query": "not_called",
    "qdrant_access": "not_called",
    "llm_access": "not_called",
    "market_data_access": "not_called",
    "map_data_access": "not_called",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_issue(issues: list[dict[str, Any]], issue_type: str, message: str, **details: Any) -> None:
    issues.append({"issue_type": issue_type, "message": message, "details": details})


def require_fields(
    obj: dict[str, Any],
    fields: list[str],
    issues: list[dict[str, Any]],
    issue_type: str,
    location: str,
) -> None:
    for field in fields:
        if field not in obj or obj[field] in (None, ""):
            add_issue(issues, issue_type, f"{location} is missing required field: {field}", location=location, field=field)


def list_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    return value if isinstance(value, list) else []


def collect_ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item.get(key)) for item in items if item.get(key)}


def check_guardrails(payload: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    guardrails = payload.get("guardrails", {})
    status = "passed"
    for key, expected in EXPECTED_GUARDRAILS.items():
        if guardrails.get(key) != expected:
            status = "failed"
            add_issue(
                issues,
                "guardrail_mismatch",
                f"guardrail {key} must remain {expected}",
                key=key,
                expected=expected,
                actual=guardrails.get(key),
            )
    return {"status": status, "expected": EXPECTED_GUARDRAILS, "actual": guardrails}


def check_top_level(payload: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    require_fields(payload, ["version", "scope", "guardrails", "shared_enums", "product_risks", "view_models"], issues, "missing_top_level_field", "root")
    status = "passed"
    if payload.get("version") != VERSION:
        status = "failed"
        add_issue(issues, "version_mismatch", "fixture version differs from checker version", expected=VERSION, actual=payload.get("version"))
    view_models = payload.get("view_models", {})
    for model_name in REQUIRED_VIEW_MODELS:
        if not isinstance(view_models.get(model_name), dict):
            status = "failed"
            add_issue(issues, "missing_view_model", f"missing view model: {model_name}", view_model=model_name)
    return {"status": "passed" if not any(issue["issue_type"] in {"missing_top_level_field", "version_mismatch", "missing_view_model"} for issue in issues) else "failed"}


def check_product_risks(payload: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    risks = list_items(payload, "product_risks")
    risk_levels = set(payload.get("shared_enums", {}).get("risk_levels", []))
    source_modules = set(payload.get("shared_enums", {}).get("source_modules", []))
    risk_ids = []
    for index, risk in enumerate(risks, start=1):
        location = f"product_risks[{index}]"
        require_fields(risk, ["risk_id", "title", "risk_level", "domain", "summary", "source_modules", "review_status"], issues, "missing_product_risk_field", location)
        risk_ids.append(risk.get("risk_id"))
        if risk.get("risk_level") not in risk_levels:
            add_issue(issues, "invalid_risk_level", "product risk uses an unknown risk level", location=location, risk_level=risk.get("risk_level"))
        for module in risk.get("source_modules", []):
            if module not in source_modules:
                add_issue(issues, "invalid_source_module", "product risk references an unknown source module", location=location, source_module=module)
    duplicates = [risk_id for risk_id, count in Counter(risk_ids).items() if risk_id and count > 1]
    if duplicates:
        add_issue(issues, "duplicate_risk_id", "product_risks contains duplicate risk_id values", duplicates=duplicates)
    return {"status": "passed" if not duplicates else "failed", "risk_count": len(risks)}


def check_dashboard(view_models: dict[str, Any], risk_ids: set[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    dashboard = view_models.get("dashboard_summary", {})
    require_fields(dashboard, ["company_id", "as_of", "overall_risk", "key_metrics", "risk_cards", "alerts", "tasks", "recent_reports", "data_sources"], issues, "missing_dashboard_field", "dashboard_summary")
    for card in list_items(dashboard, "risk_cards"):
        if card.get("risk_id") not in risk_ids:
            add_issue(issues, "unknown_risk_ref", "dashboard risk card references unknown risk_id", location="dashboard_summary.risk_cards", risk_id=card.get("risk_id"))
    for alert in list_items(dashboard, "alerts"):
        if alert.get("risk_id") not in risk_ids:
            add_issue(issues, "unknown_risk_ref", "dashboard alert references unknown risk_id", location="dashboard_summary.alerts", risk_id=alert.get("risk_id"))
    for task in list_items(dashboard, "tasks"):
        if task.get("risk_id") not in risk_ids:
            add_issue(issues, "unknown_risk_ref", "dashboard task references unknown risk_id", location="dashboard_summary.tasks", risk_id=task.get("risk_id"))
    return {"status": "passed", "risk_cards": len(list_items(dashboard, "risk_cards"))}


def check_legal_workspace(view_models: dict[str, Any], risk_ids: set[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    workspace = view_models.get("legal_workspace", {})
    require_fields(workspace, ["workspace_id", "active_thread_id", "supported_upload_types", "threads", "active_answer", "evidence_chain", "report_actions"], issues, "missing_legal_workspace_field", "legal_workspace")
    evidence_ids = collect_ids(list_items(workspace, "evidence_chain"), "evidence_id")
    for evidence in list_items(workspace, "evidence_chain"):
        require_fields(evidence, ["evidence_id", "risk_id", "law_name", "article", "jurisdiction", "legal_functional_type", "excerpt"], issues, "missing_evidence_field", "legal_workspace.evidence_chain")
        if evidence.get("risk_id") not in risk_ids:
            add_issue(issues, "unknown_risk_ref", "evidence references unknown risk_id", location="legal_workspace.evidence_chain", risk_id=evidence.get("risk_id"))
    for risk_id in workspace.get("active_answer", {}).get("risk_ids", []):
        if risk_id not in risk_ids:
            add_issue(issues, "unknown_risk_ref", "active answer references unknown risk_id", location="legal_workspace.active_answer", risk_id=risk_id)
    return {"status": "passed", "evidence_count": len(evidence_ids), "evidence_ids": sorted(evidence_ids)}


def check_market_signals(view_models: dict[str, Any], risk_ids: set[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    market = view_models.get("market_signals", {})
    require_fields(market, ["as_of", "signals"], issues, "missing_market_signals_field", "market_signals")
    for signal in list_items(market, "signals"):
        require_fields(signal, ["signal_id", "title", "source_type", "severity", "affected_domains", "risk_ids", "direction", "summary"], issues, "missing_market_signal_field", "market_signals.signals")
        for risk_id in signal.get("risk_ids", []):
            if risk_id not in risk_ids:
                add_issue(issues, "unknown_risk_ref", "market signal references unknown risk_id", location="market_signals.signals", risk_id=risk_id)
    return {"status": "passed", "signal_count": len(list_items(market, "signals"))}


def check_supply_chain_map(view_models: dict[str, Any], risk_ids: set[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    supply = view_models.get("supply_chain_map", {})
    require_fields(supply, ["map_mode", "nodes", "edges", "region_overlays"], issues, "missing_supply_chain_field", "supply_chain_map")
    node_ids = collect_ids(list_items(supply, "nodes"), "node_id")
    for node in list_items(supply, "nodes"):
        require_fields(node, ["node_id", "label", "node_type", "location", "risk_level", "risk_ids"], issues, "missing_supply_node_field", "supply_chain_map.nodes")
        for risk_id in node.get("risk_ids", []):
            if risk_id not in risk_ids:
                add_issue(issues, "unknown_risk_ref", "supply-chain node references unknown risk_id", location="supply_chain_map.nodes", risk_id=risk_id)
    for edge in list_items(supply, "edges"):
        require_fields(edge, ["edge_id", "source_node_id", "target_node_id", "relationship", "risk_ids"], issues, "missing_supply_edge_field", "supply_chain_map.edges")
        if edge.get("source_node_id") not in node_ids or edge.get("target_node_id") not in node_ids:
            add_issue(issues, "unknown_node_ref", "supply-chain edge references unknown node", edge_id=edge.get("edge_id"), source=edge.get("source_node_id"), target=edge.get("target_node_id"))
        for risk_id in edge.get("risk_ids", []):
            if risk_id not in risk_ids:
                add_issue(issues, "unknown_risk_ref", "supply-chain edge references unknown risk_id", location="supply_chain_map.edges", risk_id=risk_id)
    return {"status": "passed", "node_count": len(node_ids), "edge_count": len(list_items(supply, "edges"))}


def check_lifecycle(view_models: dict[str, Any], risk_ids: set[str], evidence_ids: set[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    lifecycle = view_models.get("lifecycle_risk", {})
    require_fields(lifecycle, ["company_id", "stages"], issues, "missing_lifecycle_field", "lifecycle_risk")
    phase_orders = []
    for stage in list_items(lifecycle, "stages"):
        require_fields(stage, ["stage_id", "label", "phase_order", "risk_level", "risk_ids", "evidence_refs", "recommended_actions"], issues, "missing_lifecycle_stage_field", "lifecycle_risk.stages")
        if isinstance(stage.get("phase_order"), int):
            phase_orders.append(stage["phase_order"])
        for risk_id in stage.get("risk_ids", []):
            if risk_id not in risk_ids:
                add_issue(issues, "unknown_risk_ref", "lifecycle stage references unknown risk_id", location="lifecycle_risk.stages", risk_id=risk_id)
        for evidence_ref in stage.get("evidence_refs", []):
            if evidence_ref not in evidence_ids:
                add_issue(issues, "unknown_evidence_ref", "lifecycle stage references unknown evidence_id", location="lifecycle_risk.stages", evidence_ref=evidence_ref)
    if phase_orders != sorted(phase_orders):
        add_issue(issues, "lifecycle_order_drift", "lifecycle stage phase_order must be ascending", phase_orders=phase_orders)
    return {"status": "passed", "stage_count": len(list_items(lifecycle, "stages"))}


def build_report(fixture_path: Path = DEFAULT_FIXTURE_PATH) -> dict[str, Any]:
    payload = read_json(fixture_path)
    issues: list[dict[str, Any]] = []
    checks = {
        "top_level": check_top_level(payload, issues),
        "guardrails": check_guardrails(payload, issues),
        "product_risks": check_product_risks(payload, issues),
    }
    risk_ids = collect_ids(list_items(payload, "product_risks"), "risk_id")
    view_models = payload.get("view_models", {})
    checks["dashboard_summary"] = check_dashboard(view_models, risk_ids, issues)
    checks["legal_workspace"] = check_legal_workspace(view_models, risk_ids, issues)
    evidence_ids = set(checks["legal_workspace"].get("evidence_ids", []))
    checks["market_signals"] = check_market_signals(view_models, risk_ids, issues)
    checks["supply_chain_map"] = check_supply_chain_map(view_models, risk_ids, issues)
    checks["lifecycle_risk"] = check_lifecycle(view_models, risk_ids, evidence_ids, issues)

    issue_counts = Counter(issue["issue_type"] for issue in issues)
    return {
        "version": VERSION,
        "status": "passed" if not issues else "failed",
        "fixture_path": str(fixture_path),
        "guardrails": EXPECTED_GUARDRAILS,
        "summary": {
            "issue_count": len(issues),
            "product_risk_count": len(risk_ids),
            "view_model_count": len(REQUIRED_VIEW_MODELS),
            "dashboard_risk_cards": checks["dashboard_summary"].get("risk_cards", 0),
            "market_signal_count": checks["market_signals"].get("signal_count", 0),
            "supply_chain_node_count": checks["supply_chain_map"].get("node_count", 0),
            "lifecycle_stage_count": checks["lifecycle_risk"].get("stage_count", 0),
        },
        "issue_type_summary": dict(sorted(issue_counts.items())),
        "issues": issues,
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate offline product view model contract fixture.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[{report['status'].upper()}] "
        f"view_models={report['summary']['view_model_count']}, "
        f"product_risks={report['summary']['product_risk_count']}, "
        f"issues={report['summary']['issue_count']}"
    )
    print(f"Report saved: {args.output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
