import json
import tempfile
import unittest
from pathlib import Path

from src.product.repository import FixtureProductViewRepository, PRODUCT_DATA_SOURCE_BOUNDARY
from src.product.service import ProductViewModelError, ProductViewModelService
from tools.export_product_data_source_boundary import build_catalog


FIXTURE_PATH = Path("tests/fixtures/product_view_models_v0.4.18.3.json")


class ProductDataSourceBoundaryTest(unittest.TestCase):
    def test_service_uses_repository_boundary(self):
        service = ProductViewModelService(FixtureProductViewRepository(FIXTURE_PATH))

        dashboard = service.dashboard_summary()

        self.assertIn("overall_risk", dashboard)
        self.assertEqual(service.repository.source_name, "fixture_sample")

    def test_service_keeps_fixture_path_constructor_compatibility(self):
        service = ProductViewModelService(FIXTURE_PATH)

        dashboard = service.dashboard_summary()

        self.assertIn("overall_risk", dashboard)
        self.assertEqual(service.repository.source_name, "fixture_sample")

    def test_repository_fails_closed_on_version_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
            payload["version"] = "0.4.18.0"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(ProductViewModelError) as ctx:
                FixtureProductViewRepository(path).load_payload()

        self.assertEqual(ctx.exception.code, "PRODUCT_VIEW_MODEL_VERSION_MISMATCH")

    def test_boundary_catalog_documents_future_provider_slots_without_connecting_them(self):
        catalog = build_catalog()

        self.assertEqual(catalog["version"], "0.4.18.8")
        self.assertEqual(catalog["guardrails"]["real_data_source_connected"], False)
        self.assertEqual(catalog["summary"]["currently_connected_provider_count"], 1)
        self.assertGreaterEqual(catalog["summary"]["future_allowed_provider_count"], 5)
        self.assertEqual(PRODUCT_DATA_SOURCE_BOUNDARY["currently_connected_providers"], ["fixture_sample"])
        self.assertEqual(PRODUCT_DATA_SOURCE_BOUNDARY["currently_disallowed_runtime_access"]["rag"], "not_called")

    def test_product_backend_does_not_import_runtime_data_clients(self):
        scanned_paths = [
            Path("src/product/repository.py"),
            Path("src/product/service.py"),
            Path("src/product/router.py"),
            Path("tools/export_product_data_source_boundary.py"),
        ]
        forbidden_markers = [
            "from src.rag",
            "import qdrant",
            "qdrant_client.",
            "rag_query(",
            "OpenAI(",
            "market_data_client.",
            "map_data_client.",
            "supply_chain_client.",
        ]

        for path in scanned_paths:
            text = path.read_text(encoding="utf-8")
            for marker in forbidden_markers:
                self.assertNotIn(marker, text, f"{marker} should not be imported or called by {path}")


if __name__ == "__main__":
    unittest.main()
