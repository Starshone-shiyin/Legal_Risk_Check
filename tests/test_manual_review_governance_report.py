import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_governance_report import (
    RECOMMENDATION_MANUAL_REVIEW,
    build_report,
    readiness_state,
)


class ManualReviewGovernanceReportTest(unittest.TestCase):
    def test_readiness_state_requires_manual_review_when_only_blocked(self):
        state = readiness_state(
            {"ready_action_candidates": 0, "blocked_pending_candidates": 3},
            {"ready_fixture_candidates": 0, "blocked_fixture_candidates": 2},
        )

        self.assertEqual(state, "manual_review_required")

    def test_file_report_summarizes_governance_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            decision_path = tmp / "decision.json"
            validation_path = tmp / "validation.json"
            actions_path = tmp / "actions.json"
            fixture_path = tmp / "fixtures.json"

            decision_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.0",
                        "summary": {
                            "total_decision_records": 2,
                            "pending_decisions": 2,
                            "issue_type_summary": {"primary_evidence_lost": 1},
                            "per_domain_summary": {"数据合规": {"decision_records": 2}},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            validation_path.write_text(
                __import__("json").dumps(
                    {"version": "0.4.7.5.1", "summary": {"invalid_records": 0}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            actions_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.2",
                        "summary": {
                            "ready_action_candidates": 0,
                            "blocked_pending_candidates": 3,
                            "action_type_summary": {"metadata_chunking_or_query_coverage_review": 3},
                            "per_domain_summary": {"数据合规": {"action_candidates": 3, "blocked_candidates": 3}},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            fixture_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.3",
                        "summary": {
                            "ready_fixture_candidates": 0,
                            "blocked_fixture_candidates": 1,
                            "fixture_type_summary": {"primary_evidence_grounding_fixture": 1},
                            "per_domain_summary": {"数据合规": {"fixture_candidates": 1, "blocked_candidates": 1}},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(decision_path, validation_path, actions_path, fixture_path)

        self.assertEqual(report["version"], "0.4.7.5.4")
        self.assertEqual(report["summary"]["readiness_state"], "manual_review_required")
        self.assertEqual(report["summary"]["blocked_action_candidates"], 3)
        self.assertEqual(report["guardrails"]["eval_case_mutation"], "disallowed")
        self.assertIn(RECOMMENDATION_MANUAL_REVIEW, [item["recommendation"] for item in report["recommendations"]])


if __name__ == "__main__":
    unittest.main()
