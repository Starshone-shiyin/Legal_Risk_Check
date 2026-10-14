import tempfile
import unittest
from pathlib import Path

from tools.build_rag_quality_triage import build_report, write_json


def case(
    case_id,
    labels,
    *,
    category="数据合规",
    needs_review=False,
    union=False,
    anchor=True,
    score_order_risks=0,
    observations=0,
    confidence=0.83,
):
    return {
        "id": case_id,
        "category": category,
        "passed": True,
        "retrieval_failure_stage": "PASS",
        "retrieval_confidence": confidence,
        "needs_human_review": needs_review,
        "contribution_labels": labels,
        "retrieval_diagnostics": {
            "layers": {
                "dense": {"satisfied": False},
                "sparse": {"satisfied": False},
                "union": {"satisfied": union},
                "anchor": {"satisfied": anchor},
                "final": {"satisfied": True},
            }
        },
        "quality_signal_diagnostics": {
            "final_refs": [{"source": "A", "article_no": 1}],
            "score_order_observations": [{} for _ in range(observations)],
            "score_order_risks": [{} for _ in range(score_order_risks)],
            "review_reasons": [],
        },
    }


class RagQualityTriageTest(unittest.TestCase):
    def test_build_report_classifies_dependency_and_review_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval.json"
            write_json(
                path,
                {
                    "report_profile": "compact",
                    "total": 4,
                    "passed": 4,
                    "retrieval_failure_stage_summary": {"PASS": 4},
                    "reports": [
                        case("anchor_case", ["ANCHOR_PASS"]),
                        case("both_case", ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"]),
                        case("review_case", ["RISK_SUPPLEMENT_PASS"], needs_review=True, union=True, anchor=False),
                        case("pure_case", ["PURE_LLM_PASS"], union=True, anchor=False),
                    ],
                },
            )

            report = build_report(path)

        summary = report["summary"]
        self.assertEqual(summary["status"], "passed_with_high_dependency")
        self.assertEqual(summary["passed_cases"], 4)
        self.assertEqual(summary["label_counts"]["ANCHOR_PASS"], 2)
        self.assertEqual(summary["dependency_classification_counts"]["anchor_and_risk_supplement_assisted"], 1)
        self.assertEqual(summary["needs_human_review_cases"], ["review_case"])
        self.assertEqual(report["priority_lists"]["manual_review_marker_present"], ["review_case"])
        self.assertIn("anchor_case", report["priority_lists"]["base_retrieval_or_query_lexical_triage"])
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertGreater(rows["review_case"]["triage_priority_score"], rows["pure_case"]["triage_priority_score"])

    def test_score_order_risk_takes_priority_over_dependency_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval.json"
            write_json(
                path,
                {
                    "reports": [
                        case("risk_case", ["ANCHOR_PASS"], score_order_risks=1),
                        case("pure_case", ["PURE_LLM_PASS"], union=True, anchor=False),
                    ]
                },
            )

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "passed_with_quality_risks")
        self.assertEqual(report["summary"]["quality_signal_summary"]["score_order_risks"], 1)
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertEqual(rows["risk_case"]["recommendation"], "inspect_score_order_risk_before_runtime_change")

    def test_priority_list_orders_manual_review_observations_and_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval.json"
            write_json(
                path,
                {
                    "reports": [
                        case("ordinary_anchor", ["ANCHOR_PASS"], observations=1, confidence=0.83),
                        case("high_observation", ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"], observations=9, confidence=0.82),
                        case("manual_low_confidence", ["RISK_SUPPLEMENT_PASS"], needs_review=True, union=True, anchor=False, confidence=0.79),
                    ]
                },
            )

            report = build_report(path)

        self.assertEqual(report["priority_lists"]["top_dependency_triage_candidates"][0], "manual_low_confidence")
        self.assertIn("high_observation", report["priority_lists"]["top_dependency_triage_candidates"])


if __name__ == "__main__":
    unittest.main()
