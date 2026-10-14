import tempfile
import unittest
from pathlib import Path

from tools.build_risk_level_overrisk_attribution import build_report, write_json


def report_case(
    case_id,
    *,
    passed=False,
    mismatch_type="over_risk",
    counts=None,
    risk_types=None,
    actions=None,
):
    return {
        "id": case_id,
        "category": "民商事",
        "passed": passed,
        "retrieval_failure_stage": "PASS",
        "risk_level": "high",
        "risk_types": risk_types or ["风险一"],
        "recommended_actions": actions or ["整改一"],
        "checks": [
            {
                "name": "expected_risk_level",
                "passed": mismatch_type == "exact_match",
                "message": f"risk_level=high, expected=medium, policy=exact, mismatch_type={mismatch_type}",
                "details": {
                    "policy": "exact",
                    "actual_level": "high",
                    "expected_level": "medium",
                    "mismatch_type": mismatch_type,
                },
            }
        ],
        "contribution_trace_summary": counts or {},
        "evidence": [
            {
                "source": "中华人民共和国民法典",
                "article_no": 271,
                "citation": "[《中华人民共和国民法典》第二百七十一条]",
            }
        ],
    }


class RiskLevelOverriskAttributionTest(unittest.TestCase):
    def test_build_report_classifies_output_rule_amplification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_json(
                path,
                {
                    "report_profile": "compact",
                    "total": 2,
                    "passed": 1,
                    "failed": 1,
                    "retrieval_failure_stage_summary": {"PASS": 2},
                    "reports": [
                        report_case(
                            "case_over",
                            counts={"risk_supplement_rules": 1, "scene_output_rules": 1},
                            risk_types=["a", "b", "c", "d"],
                            actions=["a1", "a2", "a3", "a4", "a5"],
                        ),
                        report_case("case_exact", mismatch_type="exact_match", passed=True),
                    ],
                },
            )

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "overrisk_attribution_ready")
        self.assertEqual(report["summary"]["overrisk_case_count"], 1)
        self.assertEqual(report["summary"]["confidence_counts"], {"strong_signal": 1})
        self.assertEqual(report["summary"]["high_priority_manual_review_list"], ["case_over"])
        row = report["case_rows"][0]
        self.assertEqual(row["case_id"], "case_over")
        self.assertEqual(row["primary_attribution"], "output_rule_amplification_review")
        self.assertEqual(row["confidence"], "strong_signal")
        self.assertIn("risk_supplement_rule_review", row["review_routes"])
        self.assertIn("scene_output_rule_review", row["review_routes"])
        self.assertIn("answer_wording_overstatement_review", row["review_routes"])
        self.assertIn("output contribution counts", row["review_reason"])
        self.assertEqual(row["recommended_next_step"], "inspect_full_trace_or_rule_contribution_before_risk_rule_change")
        self.assertEqual(row["risk_supplement_count"], 1)
        self.assertEqual(row["scene_output_rule_count"], 1)
        self.assertEqual(row["evidence_refs"][0]["article_no"], 271)

    def test_build_report_routes_unlabeled_risk_output_to_taxonomy_or_wording(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_json(path, {"reports": [report_case("case_plain", counts={})]})

            report = build_report(path)

        row = report["case_rows"][0]
        self.assertEqual(row["primary_attribution"], "taxonomy_or_llm_wording_review")
        self.assertEqual(row["confidence"], "medium_signal")
        self.assertIn("taxonomy_or_llm_wording_review", row["review_routes"])
        self.assertIn("without recorded supplement", row["review_reason"])

    def test_no_overrisk_cases_reports_clean_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_json(path, {"reports": [report_case("case_exact", mismatch_type="exact_match", passed=True)]})

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "no_overrisk_cases")
        self.assertEqual(report["case_rows"], [])


if __name__ == "__main__":
    unittest.main()
