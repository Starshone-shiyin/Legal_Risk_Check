import tempfile
import unittest
from pathlib import Path

from tools.build_base_retrieval_query_inspection import build_report, write_json


def candidate(source, article):
    return {
        "source": source,
        "law_name": source,
        "article_no": article,
        "section_no": "",
        "citation": f"{source}::{article}",
    }


def trace_case(case_id, *, union=False, needs_review=False):
    final = [candidate("A", 1), candidate("A", 2)]
    union_candidates = [candidate("B", 9)] if not union else final
    return {
        "id": case_id,
        "passed": True,
        "retrieval_confidence": 0.8,
        "needs_human_review": needs_review,
        "contribution_labels": ["ANCHOR_PASS"],
        "evidence": final,
        "retrieval_diagnostics": {
            "layers": {
                "dense": {"satisfied": False, "matched_count": 0},
                "sparse": {"satisfied": union, "matched_count": 2 if union else 0},
                "union": {"satisfied": union, "matched_count": 2 if union else 0},
                "anchor": {"satisfied": True, "matched_count": 2},
                "final": {"satisfied": True, "matched_count": 2},
            }
        },
        "debug_info": {
            "used_query": "question",
            "used_rerank_query": "question\n相关检索概念：x\n场景锚点法条：A第1条、第2条",
            "union_candidates": union_candidates,
            "anchor_candidates": final,
        },
    }


class BaseRetrievalQueryInspectionTest(unittest.TestCase):
    def test_build_report_detects_anchor_filled_final_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace_path = Path(tmp) / "trace.json"
            summary_path = Path(tmp) / "summary.json"
            write_json(summary_path, {"summary": {"status": "needs_dependency_reduction_trace_review"}})
            write_json(
                trace_path,
                {
                    "reports": [
                        trace_case("anchor_gap", union=False),
                        trace_case("manual_case", union=True, needs_review=True),
                    ]
                },
            )

            report = build_report(trace_path, summary_path)

        self.assertEqual(report["summary"]["status"], "base_retrieval_query_inspection_needed")
        self.assertEqual(report["summary"]["anchor_filled_final_ref_cases"], ["anchor_gap"])
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertEqual(rows["anchor_gap"]["classification"], "base_union_gap_with_anchor_filled_final_refs")
        self.assertEqual(rows["manual_case"]["classification"], "union_satisfied_manual_review_or_output_dependency")
        self.assertTrue(rows["anchor_gap"]["query_features"]["has_scenario_anchor_statutes"])


if __name__ == "__main__":
    unittest.main()
