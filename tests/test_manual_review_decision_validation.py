import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_decision_schema import (
    ACTION_METADATA_QUERY,
    DECISION_CONFIRM_ISSUE,
    DECISION_STATUS_COMPLETED,
    ROOT_METADATA_QUERY,
)
from tools.validate_manual_review_decisions import (
    ERROR_ACTION_WITHOUT_ROOT_CAUSE,
    ERROR_INVALID_ROOT_CAUSE,
    ERROR_PROHIBITED_CHANGE_TARGET,
    build_report,
    validate_record,
)


def completed_record(**overrides):
    record = {
        "case_id": "case_a",
        "decision_status": DECISION_STATUS_COMPLETED,
        "reviewer_decision": {
            "reviewer": "reviewer",
            "reviewed_at": "2026-05-11",
            "decision": DECISION_CONFIRM_ISSUE,
            "confirmed_root_causes": [ROOT_METADATA_QUERY],
            "rejected_root_causes": [],
            "confirmed_follow_up_actions": [ACTION_METADATA_QUERY],
            "proposed_change_targets": ["knowledge_manifest_metadata"],
            "fixture_candidate": False,
            "rationale": "Generic metadata issue confirmed.",
            "notes": "",
        },
    }
    for key, value in overrides.items():
        if key == "reviewer_decision":
            record["reviewer_decision"].update(value)
        else:
            record[key] = value
    return record


class ManualReviewDecisionValidationTest(unittest.TestCase):
    def test_valid_completed_decision_passes(self):
        result = validate_record(completed_record())

        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(result["errors"], [])

    def test_invalid_root_cause_is_rejected(self):
        result = validate_record(
            completed_record(
                reviewer_decision={
                    "confirmed_root_causes": ["case_specific_patch"],
                    "confirmed_follow_up_actions": [ACTION_METADATA_QUERY],
                }
            )
        )

        self.assertIn(ERROR_INVALID_ROOT_CAUSE, result["errors"])
        self.assertIn(ERROR_ACTION_WITHOUT_ROOT_CAUSE, result["errors"])

    def test_prohibited_change_target_is_rejected(self):
        result = validate_record(
            completed_record(
                reviewer_decision={
                    "proposed_change_targets": ["rag_anchor_rules new fallback"],
                }
            )
        )

        self.assertIn(ERROR_PROHIBITED_CHANGE_TARGET, result["errors"])

    def test_file_report_counts_pending_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.json"
            schema_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.0",
                        "decision_records": [
                            {"case_id": "pending_case", "decision_status": "pending", "reviewer_decision": {}},
                            completed_record(),
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(schema_path)

        self.assertEqual(report["version"], "0.4.7.5.1")
        self.assertEqual(report["summary"]["total_records"], 2)
        self.assertEqual(report["summary"]["valid_records"], 1)
        self.assertEqual(report["summary"]["pending_records"], 1)


if __name__ == "__main__":
    unittest.main()
