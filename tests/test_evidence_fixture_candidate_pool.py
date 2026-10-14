import tempfile
import unittest
from pathlib import Path

from tools.build_evidence_fixture_candidate_pool import (
    FIXTURE_TYPE_FINAL_SELECTION,
    FIXTURE_TYPE_PRIMARY_EVIDENCE,
    POOL_STATUS_BLOCKED,
    POOL_STATUS_READY,
    build_report,
    fixture_candidate,
)
from tools.build_manual_review_action_candidates import READINESS_BLOCKED, READINESS_READY
from tools.build_manual_review_decision_schema import ACTION_PRIMARY_FIXTURE


def decision_record():
    return {
        "case_id": "case_a",
        "priority_score": 10,
        "risk_level": "high",
        "expected_domains": ["数据合规"],
        "issue_types": ["primary_evidence_lost", "rerank_input_to_final_loss"],
        "suggested_root_causes": ["primary_evidence_gap", "final_evidence_selection_policy"],
        "evidence_context": {
            "missing_final_expected": [{"source": "个人信息保护法", "article_no": 66}],
            "lost_evidence": [{"source": "个人信息保护法", "article_no": 66}],
        },
    }


def action_candidate(readiness):
    return {
        "case_id": "case_a",
        "action_type": ACTION_PRIMARY_FIXTURE,
        "readiness": readiness,
        "priority_score": 10,
        "risk_level": "high",
        "expected_domains": ["数据合规"],
        "confirmed_root_causes": ["primary_evidence_gap"] if readiness == READINESS_READY else [],
    }


class EvidenceFixtureCandidatePoolTest(unittest.TestCase):
    def test_ready_action_creates_ready_fixture_candidate(self):
        candidate = fixture_candidate(action_candidate(READINESS_READY), decision_record())

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["fixture_status"], POOL_STATUS_READY)
        self.assertIn(FIXTURE_TYPE_PRIMARY_EVIDENCE, candidate["fixture_types"])
        self.assertIn(FIXTURE_TYPE_FINAL_SELECTION, candidate["fixture_types"])

    def test_blocked_action_stays_blocked(self):
        candidate = fixture_candidate(action_candidate(READINESS_BLOCKED), decision_record())

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["fixture_status"], POOL_STATUS_BLOCKED)
        self.assertEqual(candidate["allowed_next_step"], "await_manual_review_decision")

    def test_file_report_builds_pool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema_path = tmp / "schema.json"
            actions_path = tmp / "actions.json"
            schema_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.0",
                        "decision_records": [decision_record()],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            actions_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.2",
                        "action_candidates": [
                            action_candidate(READINESS_READY),
                            action_candidate(READINESS_BLOCKED),
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(schema_path, actions_path)

        self.assertEqual(report["version"], "0.4.7.5.3")
        self.assertEqual(report["summary"]["total_fixture_candidates"], 2)
        self.assertEqual(report["summary"]["ready_fixture_candidates"], 1)
        self.assertEqual(report["summary"]["blocked_fixture_candidates"], 1)


if __name__ == "__main__":
    unittest.main()
