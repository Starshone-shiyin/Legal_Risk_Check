import tempfile
import unittest
from pathlib import Path

from tools.export_manual_review_workbench import build_report, csv_row, write_csv


def decision_record(case_id="case_a", priority=9):
    return {
        "case_id": case_id,
        "decision_status": "pending",
        "priority_score": priority,
        "risk_level": "high",
        "expected_domains": ["数据合规"],
        "queue_tags": ["base_retrieval_quality_review"],
        "issue_types": ["metadata_or_chunking_review_candidate"],
        "suggested_root_causes": ["metadata_chunking_or_query_coverage"],
        "suggested_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
        "suggested_review_questions": ["Review metadata?"],
        "diagnostic_summary": {"base_retrieval_quality": {"detected_issues": ["x"]}},
        "evidence_context": {
            "missing_final_expected": [{"source": "个人信息保护法", "article_no": 66}],
            "missing_scenario_core": [],
            "lost_evidence": [],
            "final_evidence": [{"source": "个人信息保护法", "article_no": 13}],
        },
        "reviewer_decision": {
            "reviewer": "",
            "reviewed_at": "",
            "decision": "",
            "confirmed_root_causes": [],
            "rejected_root_causes": [],
            "confirmed_follow_up_actions": [],
            "proposed_change_targets": [],
            "fixture_candidate": False,
            "rationale": "",
            "notes": "",
        },
    }


class ManualReviewWorkbenchExportTest(unittest.TestCase):
    def test_report_exports_pending_decisions_as_workbench_items(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.json"
            schema_path.write_text(
                __import__("json").dumps(
                    {"version": "0.4.7.5.0", "decision_records": [decision_record()]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(schema_path)

        self.assertEqual(report["version"], "0.4.7.6.0")
        self.assertEqual(report["summary"]["total_workbench_items"], 1)
        item = report["workbench_items"][0]
        self.assertEqual(item["evidence_context_counts"]["missing_final_expected"], 1)
        self.assertEqual(item["reviewer_input_template"]["decision"], "")

    def test_csv_row_keeps_reviewer_fields_blank(self):
        report = {
            "workbench_items": [
                {
                    "case_id": "case_a",
                    "priority_score": 9,
                    "risk_level": "high",
                    "expected_domains": ["数据合规"],
                    "queue_tags": ["base_retrieval_quality_review"],
                    "issue_types": ["metadata_or_chunking_review_candidate"],
                    "suggested_root_causes": ["metadata_chunking_or_query_coverage"],
                    "suggested_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                    "suggested_review_questions": ["Review?"],
                    "evidence_context_counts": {"missing_final_expected": 1, "missing_scenario_core": 0, "lost_evidence": 0},
                    "reviewer_input_template": {"decision": "", "fixture_candidate": False},
                }
            ]
        }

        row = csv_row(report["workbench_items"][0])

        self.assertEqual(row["decision"], "")
        self.assertEqual(row["fixture_candidate"], "false")
        self.assertIn("metadata_chunking_or_query_coverage", row["suggested_root_causes"])

    def test_write_csv_outputs_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "workbench.csv"
            report = {
                "workbench_items": [
                    {
                        "case_id": "case_a",
                        "priority_score": 1,
                        "risk_level": "normal",
                        "expected_domains": [],
                        "queue_tags": [],
                        "issue_types": [],
                        "suggested_root_causes": [],
                        "suggested_follow_up_actions": [],
                        "suggested_review_questions": [],
                        "evidence_context_counts": {},
                        "reviewer_input_template": {},
                    }
                ]
            }
            write_csv(report, output)

            text = output.read_text(encoding="utf-8-sig")

        self.assertIn("case_id", text)
        self.assertIn("case_a", text)


if __name__ == "__main__":
    unittest.main()
