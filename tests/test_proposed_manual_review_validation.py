import tempfile
import unittest
from pathlib import Path

from tools.validate_proposed_manual_review_decisions import build_report


class ProposedManualReviewValidationTest(unittest.TestCase):
    def test_wrapper_reports_proposed_schema_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            proposed = Path(tmpdir) / "proposed.json"
            proposed.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.7.1",
                        "decision_records": [
                            {
                                "case_id": "case_a",
                                "decision_status": "pending",
                                "reviewer_decision": {},
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(proposed)

        self.assertEqual(report["version"], "0.4.7.7.3")
        self.assertEqual(report["inputs"]["proposed_decision_schema_version"], "0.4.7.7.1")
        self.assertEqual(report["summary"]["pending_records"], 1)


if __name__ == "__main__":
    unittest.main()
