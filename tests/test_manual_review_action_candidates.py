import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_action_candidates import (
    READINESS_BLOCKED,
    READINESS_READY,
    build_report,
    candidates_for_record,
)
from tools.build_manual_review_decision_schema import (
    ACTION_METADATA_QUERY,
    DECISION_CONFIRM_ISSUE,
    DECISION_STATUS_COMPLETED,
    ROOT_METADATA_QUERY,
)


def pending_record():
    return {
        "case_id": "case_pending",
        "decision_status": "pending",
        "priority_score": 9,
        "expected_domains": ["数据合规"],
        "suggested_root_causes": [ROOT_METADATA_QUERY],
        "suggested_follow_up_actions": [ACTION_METADATA_QUERY],
        "reviewer_decision": {},
    }


def completed_record():
    return {
        "case_id": "case_ready",
        "decision_status": DECISION_STATUS_COMPLETED,
        "priority_score": 11,
        "expected_domains": ["数据合规"],
        "suggested_root_causes": [],
        "suggested_follow_up_actions": [],
        "reviewer_decision": {
            "reviewer": "reviewer",
            "reviewed_at": "2026-05-11",
            "decision": DECISION_CONFIRM_ISSUE,
            "confirmed_root_causes": [ROOT_METADATA_QUERY],
            "rejected_root_causes": [],
            "confirmed_follow_up_actions": [],
            "proposed_change_targets": ["knowledge_manifest_metadata"],
            "fixture_candidate": False,
            "rationale": "Metadata issue confirmed.",
            "notes": "",
        },
    }


class ManualReviewActionCandidatesTest(unittest.TestCase):
    def test_pending_record_creates_blocked_candidate(self):
        candidates = candidates_for_record(pending_record())

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["readiness"], READINESS_BLOCKED)
        self.assertEqual(candidates[0]["action_type"], ACTION_METADATA_QUERY)

    def test_valid_completed_record_creates_ready_candidate(self):
        candidates = candidates_for_record(completed_record())

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["readiness"], READINESS_READY)
        self.assertEqual(candidates[0]["action_type"], ACTION_METADATA_QUERY)

    def test_file_report_uses_validation_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema_path = tmp / "schema.json"
            validation_path = tmp / "validation.json"
            schema_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.0",
                        "decision_records": [pending_record(), completed_record()],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            validation_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.1",
                        "cases": [
                            {
                                "case_id": "case_pending",
                                "validation_status": "pending",
                                "errors": [],
                            },
                            {
                                "case_id": "case_ready",
                                "validation_status": "valid",
                                "errors": [],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(schema_path, validation_path)

        self.assertEqual(report["version"], "0.4.7.5.2")
        self.assertEqual(report["summary"]["total_action_candidates"], 2)
        self.assertEqual(report["summary"]["ready_action_candidates"], 1)
        self.assertEqual(report["summary"]["blocked_pending_candidates"], 1)


if __name__ == "__main__":
    unittest.main()
