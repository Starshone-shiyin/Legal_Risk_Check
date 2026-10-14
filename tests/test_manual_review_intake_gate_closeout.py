import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_intake_gate_closeout import build_report, gate_status


class ManualReviewIntakeGateCloseoutTest(unittest.TestCase):
    def test_gate_status_blocks_without_imported_rows_or_promotions(self):
        status, blockers = gate_status(
            {"imported_rows": 0},
            {"blocked_cases": 0},
            {"invalid_records": 0},
            {"promotion_candidates": 0, "ready_action_candidates": 0},
        )

        self.assertEqual(status, "blocked")
        self.assertIn("no_imported_review_rows", blockers)
        self.assertIn("no_promotion_candidates", blockers)

    def test_closeout_report_opens_when_all_conditions_met(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            contract = tmp / "contract.json"
            import_report = tmp / "import.json"
            diff = tmp / "diff.json"
            validation = tmp / "validation.json"
            promotion = tmp / "promotion.json"
            contract.write_text(__import__("json").dumps({"version": "0.4.7.7.0"}), encoding="utf-8")
            import_report.write_text(__import__("json").dumps({"version": "0.4.7.7.1", "summary": {"imported_rows": 1, "rejected_rows": 0}}), encoding="utf-8")
            diff.write_text(__import__("json").dumps({"version": "0.4.7.7.2", "summary": {"changed_cases": 1, "blocked_cases": 0}}), encoding="utf-8")
            validation.write_text(__import__("json").dumps({"version": "0.4.7.7.3", "summary": {"valid_records": 1, "invalid_records": 0, "pending_records": 0}}), encoding="utf-8")
            promotion.write_text(__import__("json").dumps({"version": "0.4.7.7.4", "summary": {"promotion_candidates": 1, "ready_action_candidates": 1}}), encoding="utf-8")

            report = build_report(contract, import_report, diff, validation, promotion)

        self.assertEqual(report["version"], "0.4.7.7.5")
        self.assertEqual(report["summary"]["gate_status"], "open")
        self.assertEqual(report["summary"]["ready_action_candidates"], 1)


if __name__ == "__main__":
    unittest.main()
