import unittest

from tools.export_product_api_field_catalog import build_catalog


class ProductApiFieldCatalogTest(unittest.TestCase):
    def test_catalog_exports_all_product_endpoints(self):
        catalog = build_catalog()

        self.assertEqual(catalog["version"], "0.4.18.6")
        self.assertEqual(catalog["summary"]["endpoint_count"], 6)
        self.assertTrue(catalog["summary"]["source_version_matches"])
        self.assertEqual(catalog["guardrails"]["data_source"], "fixture_sample")
        self.assertEqual(catalog["guardrails"]["rag_query"], "not_called")
        self.assertEqual(catalog["guardrails"]["qdrant_access"], "not_called")
        self.assertEqual(catalog["guardrails"]["llm_access"], "not_called")

    def test_catalog_records_query_params_and_response_envelope(self):
        catalog = build_catalog()
        endpoints = {endpoint["path"]: endpoint for endpoint in catalog["endpoints"]}

        risks = endpoints["/product/risks"]
        self.assertEqual(risks["response_key"], "items")
        self.assertEqual(
            [param["name"] for param in risks["query_params"]],
            ["company_id", "risk_level", "domain", "review_status"],
        )
        self.assertEqual(risks["response_envelope"]["required_fields"], ["status", "items", "meta"])

        dashboard = endpoints["/product/dashboard/summary"]
        self.assertEqual(dashboard["response_envelope"]["required_fields"], ["status", "data", "meta"])
        self.assertIn("overall_risk.score", {field["path"] for field in dashboard["field_paths"]})
        self.assertIn("risk_cards[]", {field["path"] for field in dashboard["field_paths"]})

    def test_catalog_does_not_truncate_current_fixture_fields(self):
        catalog = build_catalog()

        self.assertFalse(any(endpoint["truncated"] for endpoint in catalog["endpoints"]))
        self.assertGreater(catalog["summary"]["field_path_count"], 30)


if __name__ == "__main__":
    unittest.main()
