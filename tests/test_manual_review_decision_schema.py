import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_decision_schema import (
    ACTION_ANCHOR_GOVERNANCE,
    ACTION_FINAL_SELECTION,
    ACTION_METADATA_QUERY,
    ACTION_PRIMARY_FIXTURE,
    DECISION_STATUS_PENDING,
    ROOT_ANCHOR_GOVERNANCE,
    ROOT_FINAL_SELECTION,
    ROOT_METADATA_QUERY,
    ROOT_PRIMARY_EVIDENCE,
    build_report,
    decision_record,
)


class ManualReviewDecisionSchemaTest(unittest.TestCase):
    def test_decision_record_suggests_root_causes_from_generic_signals(self):
        record = decision_record(
            {
                "case_id": "case_a",
                "review_status": "pending",
                "priority_score": 12,
                "risk_level": "high",
                "expected_domains": ["数据合规"],
                "queue_tags": [
                    "base_retrieval_quality_review",
                    "anchor_dependency_review",
                    "final_evidence_selection_review",
                    "primary_evidence_review",
                ],
                "issue_types": [
                    "metadata_or_chunking_review_candidate",
                    "anchor_masking_base_retrieval_gap",
                    "rerank_input_to_final_loss",
                    "primary_evidence_lost",
                ],
                "follow_up_candidates": ["metadata_chunking_or_query_coverage_review"],
                "diagnostics": {
                    "base_retrieval_quality": {
                        "present": True,
                        "detected_issues": ["metadata_or_chunking_review_candidate"],
                        "review_reasons": ["review metadata"],
                    }
                },
            }
        )

        self.assertEqual(record["decision_status"], DECISION_STATUS_PENDING)
        self.assertIn(ROOT_METADATA_QUERY, record["suggested_root_causes"])
        self.assertIn(ROOT_ANCHOR_GOVERNANCE, record["suggested_root_causes"])
        self.assertIn(ROOT_FINAL_SELECTION, record["suggested_root_causes"])
        self.assertIn(ROOT_PRIMARY_EVIDENCE, record["suggested_root_causes"])
        self.assertIn(ACTION_METADATA_QUERY, record["suggested_follow_up_actions"])
        self.assertIn(ACTION_ANCHOR_GOVERNANCE, record["suggested_follow_up_actions"])
        self.assertIn(ACTION_FINAL_SELECTION, record["suggested_follow_up_actions"])
        self.assertIn(ACTION_PRIMARY_FIXTURE, record["suggested_follow_up_actions"])
        self.assertEqual(record["reviewer_decision"]["decision"], "")

    def test_file_report_builds_schema_and_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "manual_loop.json"
            report_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.4.6",
                        "review_packages": [
                            {
                                "case_id": "case_a",
                                "review_status": "pending",
                                "priority_score": 8,
                                "expected_domains": ["市场秩序"],
                                "queue_tags": ["scenario_registry_calibration"],
                                "issue_types": ["registry_core_review_needed"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(report_path)

        self.assertEqual(report["version"], "0.4.7.5.0")
        self.assertEqual(report["summary"]["total_decision_records"], 1)
        self.assertEqual(report["summary"]["pending_decisions"], 1)
        self.assertIn("prohibited_change_targets", report["schema"])
        self.assertIn("hidden_seed", report["schema"]["prohibited_change_targets"])


if __name__ == "__main__":
    unittest.main()
