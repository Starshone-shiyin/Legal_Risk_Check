import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_progress_report import build_report


class ManualReviewProgressReportTest(unittest.TestCase):
    def test_progress_report_counts_pending_and_blocked_candidates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            decision = tmp / "decision.json"
            validation = tmp / "validation.json"
            workbench = tmp / "workbench.json"
            actions = tmp / "actions.json"
            fixtures = tmp / "fixtures.json"

            decision.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.0",
                        "decision_records": [
                            {
                                "case_id": "case_a",
                                "decision_status": "pending",
                                "priority_score": 5,
                                "expected_domains": ["数据合规"],
                                "queue_tags": ["base_retrieval_quality_review"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            validation.write_text(
                __import__("json").dumps(
                    {"version": "0.4.7.5.1", "cases": [{"case_id": "case_a", "validation_status": "pending"}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            workbench.write_text(
                __import__("json").dumps(
                    {"version": "0.4.7.6.0", "workbench_items": [{"case_id": "case_a", "rank": 1}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            actions.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.2",
                        "action_candidates": [
                            {"case_id": "case_a", "readiness": "blocked_pending_manual_review"}
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            fixtures.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.3",
                        "fixture_candidates": [
                            {"case_id": "case_a", "fixture_status": "blocked_pending_manual_review"}
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(decision, validation, workbench, actions, fixtures)

        self.assertEqual(report["version"], "0.4.7.6.2")
        self.assertEqual(report["summary"]["total_cases"], 1)
        self.assertEqual(report["summary"]["pending_cases"], 1)
        self.assertEqual(report["summary"]["blocked_action_candidates"], 1)
        self.assertEqual(report["summary"]["blocked_fixture_candidates"], 1)
        self.assertIn("awaiting_manual_decision", report["cases"][0]["blockers"])


if __name__ == "__main__":
    unittest.main()
