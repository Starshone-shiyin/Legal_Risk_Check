import tempfile
import unittest
from pathlib import Path

from tools.build_dependency_trace_summary import build_report, write_json


def report_case(case_id, labels, *, union=False, anchor=True, needs_review=False):
    return {
        "id": case_id,
        "passed": True,
        "retrieval_confidence": 0.8,
        "needs_human_review": needs_review,
        "contribution_labels": labels,
        "retrieval_diagnostics": {
            "layers": {
                "dense": {"satisfied": False, "matched_count": 0},
                "sparse": {"satisfied": union, "matched_count": 1 if union else 0},
                "union": {"satisfied": union, "matched_count": 1 if union else 0},
                "anchor": {"satisfied": anchor, "matched_count": 2 if anchor else 0},
                "final": {"satisfied": True, "matched_count": 2},
            }
        },
        "quality_signal_diagnostics": {
            "score_order_observations": [{}],
            "score_order_risks": [],
        },
        "debug_info": {
            "dense_candidates": [],
            "sparse_candidates": [{}],
            "union_candidates": [{}],
            "anchor_candidates": [{}, {}],
            "rerank_input_candidates": [{}, {}],
            "rerank_full_score_order": [{}, {}],
            "final_evidence_selection_trace": {
                "full_rerank_count": 2,
                "selected_count": 2,
                "score_epsilon": 0.1,
            },
        },
    }


class DependencyTraceSummaryTest(unittest.TestCase):
    def test_build_report_identifies_base_union_gap_anchor_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace_path = Path(tmp) / "trace.json"
            triage_path = Path(tmp) / "triage.json"
            write_json(triage_path, {"summary": {"status": "passed_with_high_dependency"}})
            write_json(
                trace_path,
                {
                    "retrieval_failure_stage_summary": {"PASS": 2},
                    "reports": [
                        report_case("anchor_gap", ["ANCHOR_PASS"], union=False, anchor=True),
                        report_case("review_case", ["RISK_SUPPLEMENT_PASS"], union=True, anchor=True, needs_review=True),
                    ],
                },
            )

            report = build_report(trace_path, triage_path)

        self.assertEqual(report["summary"]["status"], "needs_dependency_reduction_trace_review")
        self.assertEqual(report["summary"]["base_union_gap_anchor_filled_cases"], ["anchor_gap"])
        self.assertEqual(report["summary"]["human_review_cases"], ["review_case"])
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertEqual(rows["anchor_gap"]["dependency_reason"], "base_union_gap_anchor_filled")
        self.assertEqual(
            rows["review_case"]["dependency_reason"],
            "union_satisfied_but_manual_review_or_output_rule_dependency",
        )


if __name__ == "__main__":
    unittest.main()
