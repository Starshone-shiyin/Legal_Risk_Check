import unittest

from tools.check_api_contract_consistency import build_report


class ApiContractConsistencyTest(unittest.TestCase):
    def test_current_contract_artifacts_are_consistent(self):
        report = build_report()

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["issue_count"], 0)
        self.assertEqual(report["guardrails"]["service_started"], False)
        self.assertEqual(report["guardrails"]["rag_query"], "not_called")
        self.assertEqual(report["guardrails"]["qdrant_access"], "not_called")
        self.assertEqual(report["guardrails"]["llm_access"], "not_called")
        self.assertEqual(report["guardrails"]["frontend_integration"], "not_started")

        checks = report["checks"]
        self.assertEqual(len(checks["model_catalog_alignment"]), 6)
        self.assertTrue(
            all(check["status"] == "passed" for check in checks["model_catalog_alignment"])
        )
        self.assertTrue(
            all(check["status"] == "passed" for check in checks["example_payload_alignment"])
        )
        self.assertTrue(
            all(check["status"] == "passed" for check in checks["endpoint_ref_alignment"])
        )
        self.assertEqual(checks["bundle_alignment"]["status"], "passed")
        self.assertEqual(checks["version_and_guardrails"]["status"], "passed")

    def test_missing_required_example_field_is_reported_generically(self):
        report = build_report()
        examples = {
            "ask_request": {"k": 5},
        }
        issues = []

        from tools.check_api_contract_consistency import (
            check_example_payloads,
            build_openapi_schema,
        )

        checks = check_example_payloads(build_openapi_schema(), examples, issues)
        ask_check = next(check for check in checks if check["example"] == "ask_request")

        self.assertEqual(ask_check["status"], "failed")
        self.assertEqual(ask_check["missing_required"], ["question"])
        self.assertEqual(issues[0]["issue_type"], "example_payload_schema_mismatch")


if __name__ == "__main__":
    unittest.main()
