import tempfile
import unittest
from pathlib import Path

from tools.build_product_backend_closeout import build_report, write_json


class ProductBackendCloseoutTest(unittest.TestCase):
    def test_current_backend_closeout_is_passed(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.18.9")
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["backend_design_status"], "basically_complete")
        self.assertEqual(report["summary"]["endpoint_count"], 6)
        self.assertEqual(report["summary"]["openapi_passed"], 6)
        self.assertEqual(report["summary"]["response_passed"], 6)
        self.assertEqual(report["summary"]["currently_connected_provider_count"], 1)
        self.assertEqual(report["guardrails"]["rag_query"], "not_called")
        self.assertFalse(report["guardrails"]["real_data_source_connected"])

    def test_closeout_lists_frontend_handoff_and_future_provider_sequence(self):
        report = build_report()

        self.assertIn("docs/product_backend_closeout_v0.4.18.9.md", report["read_order"])
        self.assertEqual(len(report["stable_endpoints"]), 6)
        self.assertTrue(report["frontend_handoff"]["allowed_now"])
        self.assertTrue(report["frontend_handoff"]["not_allowed_yet"])
        self.assertGreaterEqual(len(report["future_provider_sequence"]), 4)
        self.assertGreaterEqual(len(report["acceptance_commands"]), 3)

    def test_missing_artifacts_block_closeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_report(Path(tmp))

        self.assertEqual(report["status"], "blocked")
        self.assertIn("required_artifacts_missing", report["blockers"])
        self.assertGreater(report["summary"]["blocker_count"], 0)

    def test_write_json_outputs_report_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "closeout.json"
            report = build_report()
            write_json(path, report)

            self.assertTrue(path.exists())
            self.assertIn('"version": "0.4.18.9"', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
