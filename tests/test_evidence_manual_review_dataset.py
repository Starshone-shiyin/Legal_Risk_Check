import tempfile
import unittest
from pathlib import Path

from tools.build_evidence_manual_review_dataset import (
    DEFAULT_COVERAGE_REPORT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TRIAGE_REPORT_PATH,
    REVIEW_PENDING,
    build_dataset,
    build_review_item,
    review_questions,
)


class EvidenceManualReviewDatasetTest(unittest.TestCase):
    def test_default_paths_remain_legacy_tests_reports(self):
        self.assertEqual(DEFAULT_COVERAGE_REPORT_PATH, Path("tests/evidence_coverage_report.json"))
        self.assertEqual(DEFAULT_TRIAGE_REPORT_PATH, Path("tests/evidence_coverage_triage_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/evidence_manual_review_dataset.json"))

    def test_review_questions_are_root_cause_driven(self):
        questions = review_questions(["base_retrieval_gap", "scenario_core_gap"])

        self.assertEqual(len(questions), 2)
        self.assertIn("dense/sparse/union", questions[0])
        self.assertIn("scenario core", questions[1])

    def test_build_review_item_preserves_evidence_context_and_placeholders(self):
        triage_case = {
            "case_id": "case_a",
            "priority_score": 9,
            "risk_level": "high",
            "root_causes": ["final_primary_gap"],
            "recommended_actions": ["Review missing primary statute."],
            "coverage_flow": {"final": 0.5},
        }
        coverage_case = {
            "expected_domains": ["示例领域"],
            "final_evidence_coverage": {"missing": [{"source": "示例法", "article_no": 2}]},
            "scenario_core_coverage": {"missing": []},
            "final_evidence": [{"source": "示例法", "article_no": 1, "content_preview": "第一条..."}],
        }

        item = build_review_item(triage_case, coverage_case)

        self.assertEqual(item["review_status"], REVIEW_PENDING)
        self.assertEqual(item["missing_final_expected"][0]["article_no"], 2)
        self.assertEqual(item["final_evidence"][0]["content_preview"], "第一条...")
        self.assertEqual(item["reviewer_fields"]["confirmed_root_causes"], [])

    def test_build_dataset_selects_high_priority_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage = tmp / "coverage.json"
            triage = tmp / "triage.json"
            coverage.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.3.2",
                        "cases": [
                            {
                                "case_id": "case_high",
                                "expected_domains": ["示例领域"],
                                "final_evidence": [{"source": "示例法", "article_no": 1}],
                            },
                            {"case_id": "case_review"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            triage.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.3.2",
                        "summary": {"triage_status_summary": {"high_priority_review": 1}},
                        "cases": [
                            {
                                "case_id": "case_high",
                                "triage_status": "high_priority_review",
                                "priority_score": 8,
                                "root_causes": ["anchor_dependency"],
                            },
                            {
                                "case_id": "case_review",
                                "triage_status": "review",
                                "priority_score": 2,
                                "root_causes": ["anchor_dependency"],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_dataset(coverage, triage)

        self.assertEqual(report["version"], "0.4.7.3.3")
        self.assertEqual(report["summary"]["total_review_items"], 1)
        self.assertEqual(report["review_items"][0]["case_id"], "case_high")
        self.assertEqual(report["summary"]["root_cause_summary"]["anchor_dependency"], 1)


if __name__ == "__main__":
    unittest.main()
