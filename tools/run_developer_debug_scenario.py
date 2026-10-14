"""Run a named developer-debug scenario through its FastAPI endpoints.

This is deliberately local-only: it enables the protected developer endpoint
for this process and writes an auditable report below output/developer_debug_runs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["RISK_DEVELOPER_DEBUG_ENABLED"] = "true"

from src.main import app  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute an isolated developer debug scenario.")
    parser.add_argument("--scenario", default="china-semiconductor-ai-chain")
    args = parser.parse_args()

    default_files = [
        PROJECT_ROOT / "data/supply_chain.json",
        PROJECT_ROOT / "data/risk_intake.json",
        PROJECT_ROOT / "data/internal_risk_workflow.json",
    ]
    baseline_hashes = {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in default_files}
    with TestClient(app) as client:
        created = client.post(f"/developer-debug/scenarios/{args.scenario}/runs")
        created.raise_for_status()
        run = created.json()
        run_id = run["run_id"]
        suppliers_response = client.get(f"/developer-debug/runs/{run_id}/suppliers")
        suppliers_response.raise_for_status()
        suppliers = suppliers_response.json()
        executed = client.post(f"/developer-debug/runs/{run_id}/execute")
        executed.raise_for_status()
        execution = executed.json()
        reset = client.post(f"/developer-debug/runs/{run_id}/reset")
        reset.raise_for_status()
        after_reset = client.get(f"/developer-debug/runs/{run_id}/suppliers")
        after_reset.raise_for_status()

    manifest = json.loads((PROJECT_ROOT / "config/developer_debug_scenarios.json").read_text(encoding="utf-8"))
    scenario = next(item for item in manifest["scenarios"] if item["scenario_id"] == args.scenario)
    fixture_path = PROJECT_ROOT / scenario["fixture_path"]
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    nodes = fixture["nodes"]
    edges = fixture["edges"]
    node_ids = {node["node_id"] for node in nodes}
    source_ids = {source["source_id"] for source in fixture["sources"]}
    expected_codes = {item["security_code"] for item in suppliers}
    default_hashes_after = {str(path.relative_to(PROJECT_ROOT)): sha256(path) for path in default_files}
    assertions = {
        "created_isolated_run": bool(run_id),
        "supplier_count_at_least_eight": len(suppliers) >= 8,
        "all_suppliers_have_security_codes": all(item.get("security_code") for item in suppliers),
        "all_suppliers_have_public_evidence_refs": all(item.get("evidence_refs") for item in suppliers),
        "all_relationships_marked_as_simulated": all("测试模拟" in (item.get("notes") or "") for item in suppliers),
        "chain_has_seven_or_more_stages": len(scenario["chain_stages"]) >= 7,
        "network_has_connected_simulated_edges": len(edges) >= 7 and all(edge["is_simulated"] for edge in edges),
        "network_references_known_nodes_and_sources": all(
            edge["from"] in node_ids and edge["to"] in node_ids and set(edge["source_ids"]).issubset(source_ids)
            for edge in edges
        ),
        "structured_sources_are_traceable": all(
            source.get("url", "").startswith("https://") and source.get("title") and source.get("publisher")
            and source.get("published_at") and source.get("retrieved_at") for source in fixture["sources"]
        ),
        "risk_intake_loop_confirmed": execution["intake_status"] == "promoted" and execution["event_status"] == "confirmed" and bool(execution["confirmed_risk_id"]),
        "default_data_unchanged": baseline_hashes == default_hashes_after,
        "reset_is_repeatable": suppliers == after_reset.json(),
    }
    report = {
        "report_type": "developer_debug_scenario_run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run": run,
        "chain_stages": scenario["chain_stages"],
        "supplier_count": len(suppliers),
        "security_codes": sorted(expected_codes),
        "fixture_sha256": sha256(fixture_path),
        "default_data_sha256_before": baseline_hashes,
        "default_data_sha256_after": default_hashes_after,
        "network": {"nodes": nodes, "edges": edges, "sources": fixture["sources"]},
        "execution": execution,
        "assertions": assertions,
        "result": "passed" if all(assertions.values()) else "failed",
    }
    report_path = PROJECT_ROOT / "output" / "developer_debug_runs" / run_id / "scenario_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": run_id, "report_path": str(report_path), "result": report["result"]}, ensure_ascii=False))
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
