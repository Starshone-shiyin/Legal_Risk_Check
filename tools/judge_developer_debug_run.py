"""Independent rubric-based judge for a completed developer-debug run artifact."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(condition: bool, points: int, label: str, findings: list[dict]) -> int:
    findings.append({"criterion": label, "points": points if condition else 0, "max_points": points, "passed": condition})
    return points if condition else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Judge a developer-debug scenario run artifact.")
    parser.add_argument("report", type=Path, help="Path to scenario_report.json")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    run_path = args.report.parent
    run_metadata = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
    fixture_path = PROJECT_ROOT / run_metadata["fixture_path"]
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    nodes = report["network"]["nodes"]
    edges = report["network"]["edges"]
    sources = report["network"]["sources"]
    node_ids = {item["node_id"] for item in nodes}
    source_ids = {item["source_id"] for item in sources}
    run_files = [run_path / "supply_chain.json", run_path / "risk_intake.json", run_path / "internal_risk_workflow.json"]

    infrastructure_findings: list[dict] = []
    infrastructure_score = 0
    infrastructure_score += score(all(path.exists() for path in run_files), 20, "three isolated module stores exist", infrastructure_findings)
    infrastructure_score += score(report["default_data_sha256_before"] == report["default_data_sha256_after"], 20, "default data hashes unchanged", infrastructure_findings)
    infrastructure_score += score(report["assertions"].get("reset_is_repeatable") is True, 15, "run reset is repeatable", infrastructure_findings)
    infrastructure_score += score(report["assertions"].get("risk_intake_loop_confirmed") is True, 20, "signal-to-confirmed-risk loop executed", infrastructure_findings)
    infrastructure_score += score(report["fixture_sha256"] == sha256(fixture_path), 10, "fixture integrity matches run record", infrastructure_findings)
    infrastructure_score += score(report["result"] == "passed" and all(report["assertions"].values()), 15, "all recorded run assertions passed", infrastructure_findings)

    test_findings: list[dict] = []
    test_score = 0
    test_score += score(report["supplier_count"] >= 8 and len(report["security_codes"]) >= 8, 15, "real-company identifier coverage", test_findings)
    test_score += score(len({node["stage"] for node in nodes}) >= 7, 15, "long-chain stage coverage", test_findings)
    test_score += score(len(edges) >= 7 and all(edge["from"] in node_ids and edge["to"] in node_ids for edge in edges), 15, "topology is explicit and connected", test_findings)
    test_score += score(all(edge.get("is_simulated") is True for edge in edges), 10, "relations explicitly marked as simulated", test_findings)
    test_score += score(all(set(item.get("source_ids", [])).issubset(source_ids) and item.get("source_ids") for item in [*nodes, *edges]), 10, "nodes and edges cite source objects", test_findings)
    test_score += score(all(item.get("url", "").startswith("https://") and item.get("publisher") and item.get("title") and item.get("published_at") and item.get("retrieved_at") for item in sources), 15, "structured public-source traceability", test_findings)
    test_score += score(report["execution"]["risk_count"] >= 1 and report["execution"]["event_status"] == "confirmed", 10, "risk workflow conclusion recorded", test_findings)
    test_score += score(any("出口管制" in supplier["external_tags"] for supplier in fixture["suppliers"]), 10, "cross-border risk coverage", test_findings)

    judgment = {
        "report_type": "developer_debug_judgment",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_run_report": str(args.report),
        "infrastructure": {"score": infrastructure_score, "out_of": 100, "findings": infrastructure_findings},
        "initial_test": {"score": test_score, "out_of": 100, "findings": test_findings},
        "verdict": "accepted" if infrastructure_score >= 80 and test_score >= 80 else "needs_revision",
    }
    output = args.report.with_name("judge_report.json")
    output.write_text(json.dumps(judgment, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"judge_report": str(output), "verdict": judgment["verdict"], "infrastructure_score": infrastructure_score, "test_score": test_score}, ensure_ascii=False))
    return 0 if judgment["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
