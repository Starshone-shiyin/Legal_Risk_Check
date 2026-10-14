import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.check_product_mock_endpoint_contract import (
    MOCK_ENDPOINTS,
    build_report,
)


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
        "map_data_access": "not_called",
    },
    "product_risks": [
        {
            "risk_id": "risk-a",
            "title": "Risk A",
            "risk_level": "high",
            "domain": "data_compliance",
            "summary": "summary",
            "source_modules": ["dashboard"],
            "review_status": "required",
        }
    ],
    "view_models": {
        "dashboard_summary": {"risk_cards": [{"risk_id": "risk-a"}]},
        "legal_workspace": {
            "active_answer": {"risk_ids": ["risk-a"]},
            "evidence_chain": [{"evidence_id": "ev-a", "risk_id": "risk-a"}],
        },
        "market_signals": {"signals": [{"risk_ids": ["risk-a"]}]},
        "supply_chain_map": {
            "nodes": [{"node_id": "node-a", "risk_ids": ["risk-a"]}],
            "edges": [{"edge_id": "edge-a", "risk_ids": ["risk-a"]}],
            "region_overlays": [],
        },
        "lifecycle_risk": {
            "stages": [{"stage_id": "stage-a", "risk_ids": ["risk-a"], "evidence_refs": ["ev-a"]}]
        },
    },
}


class ProductMockEndpointContractTest(unittest.TestCase):
    def test_current_contract_passes(self):
        report = build_report()

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["issue_count"], 0)
        self.assertEqual(report["summary"]["endpoint_count"], 6)
        self.assertEqual(report["guardrails"]["fastapi_route_added"], "promoted_to_fixture_backed_api_in_v0.4.18.5")
        self.assertEqual(report["guardrails"]["rag_query"], "not_called")
        self.assertTrue(all(endpoint["mock_only"] for endpoint in report["endpoint_contract"]))

    def test_unknown_risk_reference_is_reported_generically(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = copy.deepcopy(FIXTURE)
            payload["view_models"]["dashboard_summary"]["risk_cards"][0]["risk_id"] = "missing-risk"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            report = build_report(path)

        self.assertEqual(report["status"], "failed")
        self.assertIn("unknown_risk_ref", report["issue_type_summary"])

    def test_non_get_endpoint_is_rejected(self):
        endpoint_specs = copy.deepcopy(MOCK_ENDPOINTS)
        endpoint_specs[0]["method"] = "POST"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(FIXTURE, ensure_ascii=False), encoding="utf-8")

            report = build_report(path, endpoint_specs)

        self.assertEqual(report["status"], "failed")
        self.assertIn("unsupported_method", report["issue_type_summary"])

    def test_fastapi_surface_exposure_is_recorded_after_api_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = copy.deepcopy(FIXTURE)
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            original_read_text = Path.read_text

            def read_text_side_effect(target: Path, *args, **kwargs):
                if target.as_posix().endswith("src/main.py"):
                    return 'app.get("/product/dashboard/summary")'
                return original_read_text(target, *args, **kwargs)

            with patch("pathlib.Path.read_text", read_text_side_effect):
                report = build_report(path)

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["checks"]["fastapi_surface"]["surface_state"], "promoted_to_fixture_backed_api")
        self.assertIn("/product/dashboard/summary", report["checks"]["fastapi_surface"]["exposed_paths"])


if __name__ == "__main__":
    unittest.main()
