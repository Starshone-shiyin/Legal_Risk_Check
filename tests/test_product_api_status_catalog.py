import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app
from src.product.service import ProductViewModelError, ProductViewModelService
from src.product.status import PRODUCT_ERROR_BY_CODE
from tools.export_product_api_status_catalog import build_catalog


class ProductApiStatusCatalogTest(unittest.TestCase):
    def test_status_catalog_exports_success_and_error_states(self):
        catalog = build_catalog()

        self.assertEqual(catalog["version"], "0.4.18.7")
        self.assertEqual(catalog["summary"]["success_state_count"], 2)
        self.assertEqual(catalog["summary"]["error_code_count"], 6)
        self.assertEqual(catalog["guardrails"]["rag_query"], "not_called")
        self.assertEqual(catalog["empty_result_semantics"]["empty_value"], [])

    def test_error_catalog_contains_runtime_fixture_errors(self):
        self.assertEqual(PRODUCT_ERROR_BY_CODE["PRODUCT_VIEW_MODEL_UNAVAILABLE"]["http_status"], 500)
        self.assertEqual(PRODUCT_ERROR_BY_CODE["PRODUCT_VIEW_MODEL_INVALID_JSON"]["http_status"], 500)
        self.assertEqual(PRODUCT_ERROR_BY_CODE["PRODUCT_VIEW_MODEL_VERSION_MISMATCH"]["http_status"], 500)
        self.assertEqual(PRODUCT_ERROR_BY_CODE["PRODUCT_DATA_SOURCE_DEGRADED"]["http_status"], 503)

    def test_product_view_model_error_exposes_public_message(self):
        error = ProductViewModelError("PRODUCT_VIEW_MODEL_VERSION_MISMATCH", "internal detail")

        self.assertEqual(error.code, "PRODUCT_VIEW_MODEL_VERSION_MISMATCH")
        self.assertEqual(error.http_status, 500)
        self.assertNotEqual(error.public_message, "internal detail")

    def test_invalid_fixture_json_fails_closed_with_specific_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text("{not-json", encoding="utf-8")
            service = ProductViewModelService(path)

            with self.assertRaises(ProductViewModelError) as ctx:
                service.dashboard_summary()

        self.assertEqual(ctx.exception.code, "PRODUCT_VIEW_MODEL_INVALID_JSON")

    def test_product_risks_empty_result_is_success_state(self):
        client = TestClient(app)
        response = client.get("/product/risks", params={"risk_level": "critical"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])


if __name__ == "__main__":
    unittest.main()
