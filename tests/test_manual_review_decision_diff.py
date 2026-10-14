import tempfile
import unittest
from pathlib import Path

from tools.audit_manual_review_decision_diff import build_report


def schema(record):
    return {"version": "test", "decision_records": [record]}


def record(decision_status="pending", target=None):
    return {
        "case_id": "case_a",
        "decision_status": decision_status,
        "reviewer_decision": {
            "reviewer": "reviewer" if decision_status == "completed" else "",
            "reviewed_at": "2026-05-11" if decision_status == "completed" else "",
            "decision": "confirm_diagnostic_issue" if decision_status == "completed" else "",
            "confirmed_root_causes": ["metadata_chunking_or_query_coverage"] if decision_status == "completed" else [],
            "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"] if decision_status == "completed" else [],
            "proposed_change_targets": [target] if target else [],
            "fixture_candidate": False,
            "rationale": "Confirmed" if decision_status == "completed" else "",
            "notes": "",
        },
    }


class ManualReviewDecisionDiffTest(unittest.TestCase):
    def test_diff_report_detects_changed_decision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            original = tmp / "original.json"
            proposed = tmp / "proposed.json"
            original.write_text(__import__("json").dumps(schema(record()), ensure_ascii=False), encoding="utf-8")
            proposed.write_text(__import__("json").dumps(schema(record("completed")), ensure_ascii=False), encoding="utf-8")

            report = build_report(original, proposed)

        self.assertEqual(report["version"], "0.4.7.7.2")
        self.assertEqual(report["summary"]["changed_cases"], 1)
        self.assertIn("decision_status", report["summary"]["changed_field_summary"])

    def test_diff_report_blocks_prohibited_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            original = tmp / "original.json"
            proposed = tmp / "proposed.json"
            original.write_text(__import__("json").dumps(schema(record()), ensure_ascii=False), encoding="utf-8")
            proposed.write_text(__import__("json").dumps(schema(record("completed", "rag_anchor_rules")), ensure_ascii=False), encoding="utf-8")

            report = build_report(original, proposed)

        self.assertEqual(report["summary"]["blocked_cases"], 1)
        self.assertEqual(report["diff_cases"][0]["audit_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
