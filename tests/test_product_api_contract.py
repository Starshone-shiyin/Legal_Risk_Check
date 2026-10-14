import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app
from src.product.contracts import PRODUCT_API_VERSION, PRODUCT_ENDPOINTS, SOURCE_VIEW_MODEL_VERSION
from src.product.repository import FixtureProductViewRepository
from src.product.service import ProductViewModelError, ProductViewModelService
from tools.check_product_api_contract import build_report


FIXTURE_PATH = Path("tests/fixtures/product_view_models_v0.4.18.3.json")


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class ProductApiContractTest(unittest.TestCase):
    def test_openapi_exposes_product_paths(self):
        paths = app.openapi().get("paths", {})

        for endpoint in PRODUCT_ENDPOINTS:
            self.assertIn(endpoint["path"], paths)
            self.assertIn(endpoint["method"].lower(), paths[endpoint["path"]])

    def test_product_endpoints_return_fixture_backed_envelopes(self):
        client = TestClient(app)
        fixture = load_fixture()

        for endpoint in PRODUCT_ENDPOINTS:
            response = client.get(endpoint["path"])
            self.assertEqual(response.status_code, 200, endpoint["path"])
            payload = response.json()
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["meta"]["contract_version"], PRODUCT_API_VERSION)
            self.assertEqual(payload["meta"]["source_view_model_version"], SOURCE_VIEW_MODEL_VERSION)
            self.assertEqual(payload["meta"]["data_source"], "fixture_sample")
            self.assertTrue(all(value == "not_called" for value in payload["meta"]["runtime_data_access"].values()))

            if endpoint["response_key"] == "items":
                self.assertEqual(payload["items"], fixture["product_risks"])
            else:
                self.assertEqual(payload["data"], fixture["view_models"][endpoint["view_model"]])

    def test_product_risks_filters_are_applied_without_404(self):
        client = TestClient(app)

        high = client.get("/product/risks", params={"risk_level": "high"}).json()["items"]
        self.assertTrue(high)
        self.assertTrue(all(item["risk_level"] == "high" for item in high))

        data_compliance = client.get("/product/risks", params={"domain": "data_compliance"}).json()["items"]
        self.assertTrue(data_compliance)
        self.assertTrue(all(item["domain"] == "data_compliance" for item in data_compliance))

        required = client.get("/product/risks", params={"review_status": "required"}).json()["items"]
        self.assertTrue(required)
        self.assertTrue(all(item["review_status"] == "required" for item in required))

        empty = client.get("/product/risks", params={"risk_level": "critical"}).json()["items"]
        self.assertEqual(empty, [])

    def test_product_endpoints_do_not_call_main_rag_or_report_chains(self):
        client = TestClient(app)
        with (
            patch("src.main.rag_query") as rag_query,
            patch("src.main.analyze_risk") as analyze_risk,
            patch("src.main.generate_risk_report") as generate_risk_report,
            patch("src.main.generate_risk_report_export") as generate_risk_report_export,
        ):
            for endpoint in PRODUCT_ENDPOINTS:
                response = client.get(endpoint["path"])
                self.assertEqual(response.status_code, 200)

        rag_query.assert_not_called()
        analyze_risk.assert_not_called()
        generate_risk_report.assert_not_called()
        generate_risk_report_export.assert_not_called()

    def test_service_fails_closed_on_source_version_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = load_fixture()
            payload["version"] = "0.4.18.2"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            service = ProductViewModelService(FixtureProductViewRepository(path))

            with self.assertRaises(ProductViewModelError):
                service.dashboard_summary()

    def test_product_api_checker_passes(self):
        report = build_report()

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["issue_count"], 0)
        self.assertEqual(report["summary"]["endpoint_count"], 6)


if __name__ == "__main__":
    unittest.main()
