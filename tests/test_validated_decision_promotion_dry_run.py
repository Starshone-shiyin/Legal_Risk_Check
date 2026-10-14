import tempfile
import unittest
from pathlib import Path

from tools.build_validated_decision_promotion_dry_run import build_report


class ValidatedDecisionPromotionDryRunTest(unittest.TestCase):
    def test_only_completed_valid_records_are_promoted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            proposed = tmp / "proposed.json"
            validation = tmp / "validation.json"
            proposed.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.7.1",
                        "decision_records": [
                            {
                                "case_id": "case_ready",
                                "decision_status": "completed",
                                "priority_score": 9,
                                "reviewer_decision": {
                                    "reviewer": "reviewer",
                                    "reviewed_at": "2026-05-11",
                                    "decision": "confirm_diagnostic_issue",
                                    "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                    "rejected_root_causes": [],
                                    "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                    "proposed_change_targets": ["knowledge_manifest_metadata"],
                                    "fixture_candidate": False,
                                    "rationale": "Confirmed.",
                                    "notes": "",
                                },
                            },
                            {
                                "case_id": "case_pending",
                                "decision_status": "pending",
                                "reviewer_decision": {},
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            validation.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.7.3",
                        "summary": {"valid_records": 1, "invalid_records": 0, "pending_records": 1},
                        "cases": [
                            {
                                "case_id": "case_ready",
                                "decision_status": "completed",
                                "validation_status": "valid",
                            },
                            {
                                "case_id": "case_pending",
                                "decision_status": "pending",
                                "validation_status": "pending",
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(proposed, validation)

        self.assertEqual(report["version"], "0.4.7.7.4")
        self.assertEqual(report["summary"]["promotion_candidates"], 1)
        self.assertEqual(report["summary"]["ready_action_candidates"], 1)
        self.assertEqual(report["promotion_candidates"][0]["case_id"], "case_ready")


if __name__ == "__main__":
    unittest.main()
