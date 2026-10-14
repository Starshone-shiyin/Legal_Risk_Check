import json
import tempfile
import unittest
from pathlib import Path

from tools.check_product_view_model_contract import build_report


FIXTURE = {
    "version": "0.4.18.3",
    "scope": "test",
    "guardrails": {
        "ui_implementation": "not_started",
        "api_integration": "not_started",
        "rag_query": "not_called",
        "qdrant_access": "not_called",
        "llm_access": "not_called",
        "market_data_access": "not_called",
        "map_data_access": "not_called"
    },
    "shared_enums": {
        "risk_levels": ["low", "medium", "high", "critical"],
        "source_modules": ["dashboard", "legal_workspace", "market_signals", "supply_chain_map", "lifecycle_risk"]
    },
    "product_risks": [
        {
            "risk_id": "risk-a",
            "title": "Risk A",
            "risk_level": "high",
            "domain": "data_compliance",
            "summary": "summary",
            "source_modules": ["dashboard", "legal_workspace"],
            "review_status": "required"
        }
    ],
    "view_models": {
        "dashboard_summary": {
            "company_id": "demo",
            "as_of": "2026-06-15T09:00:00+08:00",
            "overall_risk": {"score": 80, "level": "high", "trend": "up", "summary": "summary"},
            "key_metrics": [],
            "risk_cards": [{"risk_id": "risk-a"}],
            "alerts": [],
            "tasks": [],
            "recent_reports": [],
            "data_sources": []
        },
        "legal_workspace": {
            "workspace_id": "workspace",
            "active_thread_id": "thread",
            "supported_upload_types": ["pdf"],
            "threads": [],
            "active_answer": {"risk_ids": ["risk-a"]},
            "evidence_chain": [
                {
                    "evidence_id": "ev-a",
                    "risk_id": "risk-a",
                    "law_name": "Law",
                    "article": "Article 1",
                    "jurisdiction": "CN",
                    "legal_functional_type": "义务条款",
                    "excerpt": "excerpt"
                }
            ],
            "report_actions": []
        },
        "market_signals": {
            "as_of": "2026-06-15T09:00:00+08:00",
            "signals": [
                {
                    "signal_id": "signal-a",
                    "title": "Signal",
                    "source_type": "market",
                    "severity": "high",
                    "affected_domains": ["data_compliance"],
                    "risk_ids": ["risk-a"],
                    "direction": "negative",
                    "summary": "summary"
                }
            ]
        },
        "supply_chain_map": {
            "map_mode": "world",
            "nodes": [
                {
                    "node_id": "node-a",
                    "label": "Node",
                    "node_type": "supplier",
                    "location": {"country": "China"},
                    "risk_level": "high",
                    "risk_ids": ["risk-a"]
                }
            ],
            "edges": [
                {
                    "edge_id": "edge-a",
                    "source_node_id": "node-a",
                    "target_node_id": "node-a",
                    "relationship": "rel",
                    "risk_ids": ["risk-a"]
                }
            ],
            "region_overlays": []
        },
        "lifecycle_risk": {
            "company_id": "demo",
            "stages": [
                {
                    "stage_id": "stage-a",
                    "label": "Stage",
                    "phase_order": 1,
                    "risk_level": "high",
                    "risk_ids": ["risk-a"],
                    "evidence_refs": ["ev-a"],
                    "recommended_actions": ["action"]
                }
            ]
        }
    }
}


def write_fixture(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class ProductViewModelContractTest(unittest.TestCase):
    def test_current_fixture_passes_contract(self):
        report = build_report()

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["issue_count"], 0)
        self.assertEqual(report["summary"]["view_model_count"], 5)

    def test_unknown_risk_reference_is_reported_generically(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = json.loads(json.dumps(FIXTURE))
            payload["view_models"]["dashboard_summary"]["risk_cards"][0]["risk_id"] = "missing-risk"
            write_fixture(path, payload)

            report = build_report(path)

        self.assertEqual(report["status"], "failed")
        self.assertIn("unknown_risk_ref", report["issue_type_summary"])

    def test_guardrail_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = json.loads(json.dumps(FIXTURE))
            payload["guardrails"]["rag_query"] = "called"
            write_fixture(path, payload)

            report = build_report(path)

        self.assertEqual(report["status"], "failed")
        self.assertIn("guardrail_mismatch", report["issue_type_summary"])

    def test_unknown_supply_chain_node_reference_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = json.loads(json.dumps(FIXTURE))
            payload["view_models"]["supply_chain_map"]["edges"][0]["target_node_id"] = "missing-node"
            write_fixture(path, payload)

            report = build_report(path)

        self.assertEqual(report["status"], "failed")
        self.assertIn("unknown_node_ref", report["issue_type_summary"])


if __name__ == "__main__":
    unittest.main()
