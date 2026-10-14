import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_decision_examples import build_report


class ManualReviewDecisionExamplesTest(unittest.TestCase):
    def test_examples_include_valid_and_invalid_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.json"
            schema_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.0",
                        "decision_records": [
                            {
                                "case_id": "case_a",
                                "decision_status": "pending",
                                "priority_score": 3,
                                "risk_level": "normal",
                                "expected_domains": ["数据合规"],
                                "queue_tags": [],
                                "issue_types": [],
                                "suggested_root_causes": [],
                                "suggested_follow_up_actions": [],
                                "reviewer_decision": {},
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(schema_path)

        self.assertEqual(report["version"], "0.4.7.6.1")
        self.assertEqual(report["summary"]["total_examples"], 4)
        self.assertEqual(report["summary"]["valid_examples"], 3)
        self.assertEqual(report["summary"]["invalid_examples"], 1)
        self.assertEqual(report["summary"]["expectation_mismatches"], 0)
        invalid = [item for item in report["examples"] if item["expected_validation_status"] == "invalid"][0]
        self.assertIn("prohibited_change_target", invalid["validation"]["errors"])


if __name__ == "__main__":
    unittest.main()
