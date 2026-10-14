import tempfile
import unittest
from pathlib import Path

from tools.build_rag_evidence_independence_baseline import build_report, write_json


def case(
    case_id,
    labels,
    *,
    passed=True,
    category="data_compliance",
    union=False,
    anchor=True,
    needs_review=False,
):
    return {
        "id": case_id,
        "category": category,
        "passed": passed,
        "retrieval_failure_stage": "PASS",
        "needs_human_review": needs_review,
        "contribution_labels": labels,
        "retrieval_diagnostics": {
            "layers": {
                "dense": {"satisfied": False, "matched_count": 0},
                "sparse": {"satisfied": union, "matched_count": 2 if union else 0},
                "union": {"satisfied": union, "matched_count": 2 if union else 0},
                "anchor": {"satisfied": anchor, "matched_count": 3 if anchor else 0},
                "final": {"satisfied": True, "matched_count": 3},
            }
        },
        "quality_signal_diagnostics": {
            "final_refs": [{"source": "A", "article_no": 1}],
            "score_order_observations": [],
        },
    }


class RagEvidenceIndependenceBaselineTest(unittest.TestCase):
    def test_build_report_summarizes_dependency_hotspots(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval.json"
            write_json(
                path,
                {
                    "total": 4,
                    "passed": 4,
                    "retrieval_failure_stage_summary": {"PASS": 4},
                    "reports": [
                        case("anchor_gap", ["ANCHOR_PASS"]),
                        case("both_rules", ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"]),
                        case("risk_only", ["RISK_SUPPLEMENT_PASS"], union=True, anchor=False),
                        case("pure", ["PURE_LLM_PASS"], union=True, anchor=False),
                    ],
                },
            )

            report = build_report(path)

        summary = report["summary"]
        self.assertEqual(summary["status"], "needs_dependency_reduction_baseline")
        self.assertEqual(summary["total_cases"], 4)
        self.assertEqual(summary["label_counts"]["ANCHOR_PASS"], 2)
        self.assertEqual(summary["dependency_bucket_counts"]["anchor_and_risk_supplement"], 1)
        self.assertEqual(summary["high_dependency_case_count"], 3)
        self.assertIn("anchor_gap", report["priority_lists"]["base_retrieval_query_lexical_triage"])
        self.assertIn("both_rules", report["priority_lists"]["base_retrieval_query_lexical_triage"])
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertLess(rows["both_rules"]["independence_score"], rows["pure"]["independence_score"])

    def test_failed_case_is_kept_separate_from_runtime_patch_recommendations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval.json"
            write_json(
                path,
                {
                    "risk_level_mismatch_summary": {
                        "mismatch_cases": [
                            {
                                "id": "expected_review",
                                "mismatch_type": "over_risk",
                            }
                        ]
                    },
                    "reports": [
                        case("expected_review", ["RISK_SUPPLEMENT_PASS"], passed=False, union=True, anchor=False),
                        case("pure", ["PURE_LLM_PASS"], union=True, anchor=False),
                    ],
                },
            )

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "has_failed_cases_and_dependency_hotspots")
        self.assertEqual(report["priority_lists"]["failed_or_expected_level_review"], ["expected_review"])
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertEqual(rows["expected_review"]["risk_level_mismatch_type"], "over_risk")
        self.assertEqual(rows["expected_review"]["next_action"], "failed_case_fact_or_expected_level_review")


if __name__ == "__main__":
    unittest.main()
