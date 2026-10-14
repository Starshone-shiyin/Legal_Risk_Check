import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_loop import (
    QUEUE_ANCHOR_DEPENDENCY,
    QUEUE_BASE_RETRIEVAL,
    QUEUE_FINAL_SELECTION,
    QUEUE_PRIMARY_EVIDENCE,
    QUEUE_SCENARIO_REGISTRY,
    build_report,
    build_review_package,
)


class ManualReviewLoopTest(unittest.TestCase):
    def test_review_package_combines_diagnostics_and_reviewer_fields(self):
        package = build_review_package(
            "case_a",
            {
                "case_id": "case_a",
                "priority_score": 8,
                "risk_level": "high",
                "expected_domains": ["数据合规"],
                "root_causes": ["final_primary_gap"],
                "detected_issues": ["final_primary_gap"],
                "review_questions": ["Manual question"],
            },
            {"detected_issues": ["registry_core_review_needed"]},
            {"detected_issues": ["base_retrieval_review_needed"]},
            {"detected_issues": ["anchor_masking_base_retrieval_gap"]},
            {"detected_issues": ["primary_evidence_lost", "liability_evidence_lost"]},
        )

        self.assertIn(QUEUE_SCENARIO_REGISTRY, package["queue_tags"])
        self.assertIn(QUEUE_BASE_RETRIEVAL, package["queue_tags"])
        self.assertIn(QUEUE_ANCHOR_DEPENDENCY, package["queue_tags"])
        self.assertIn(QUEUE_FINAL_SELECTION, package["queue_tags"])
        self.assertIn(QUEUE_PRIMARY_EVIDENCE, package["queue_tags"])
        self.assertEqual(package["review_status"], "pending")
        self.assertEqual(package["reviewer_fields"]["decision"], "")
        self.assertIn("primary_evidence_fixture_candidate_review", package["follow_up_candidates"])

    def test_file_report_builds_from_all_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manual = tmp / "manual.json"
            scenario = tmp / "scenario.json"
            base = tmp / "base.json"
            anchor = tmp / "anchor.json"
            final = tmp / "final.json"

            manual.write_text(
                __import__("json").dumps(
                    {
                        "version": "manual",
                        "review_items": [
                            {
                                "case_id": "case_a",
                                "priority_score": 5,
                                "risk_level": "high",
                                "expected_domains": ["数据合规"],
                                "root_causes": ["final_primary_gap"],
                                "detected_issues": ["final_primary_gap"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            for path, issue in (
                (scenario, "registry_core_review_needed"),
                (base, "base_retrieval_review_needed"),
                (anchor, "anchor_masking_base_retrieval_gap"),
                (final, "primary_evidence_lost"),
            ):
                path.write_text(
                    __import__("json").dumps(
                        {"version": "test", "cases": [{"case_id": "case_a", "detected_issues": [issue]}]},
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            report = build_report(manual, scenario, base, anchor, final)

        self.assertEqual(report["version"], "0.4.7.4.6")
        self.assertEqual(report["summary"]["total_review_packages"], 1)
        self.assertEqual(report["summary"]["pending_review_packages"], 1)
        self.assertIn(QUEUE_FINAL_SELECTION, report["summary"]["queue_summary"])


if __name__ == "__main__":
    unittest.main()
