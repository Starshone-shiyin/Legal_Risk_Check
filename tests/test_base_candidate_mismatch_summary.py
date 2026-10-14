import tempfile
import unittest
from pathlib import Path

from tools.build_base_candidate_mismatch_summary import build_report, write_json


def candidate(source, article, content=""):
    return {
        "source": source,
        "law_name": source,
        "article_no": article,
        "section_no": "",
        "citation": f"{source}::{article}",
        "content_preview": content,
    }


class BaseCandidateMismatchSummaryTest(unittest.TestCase):
    def test_build_report_classifies_source_and_article_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            inspection = Path(tmp) / "inspection.json"
            write_json(
                inspection,
                {"summary": {"anchor_filled_final_ref_cases": ["source_drift", "article_drift"]}},
            )
            write_json(
                trace,
                {
                    "reports": [
                        {
                            "id": "source_drift",
                            "evidence": [candidate("A", 1, "alpha duty")],
                            "debug_info": {
                                "used_rerank_query": "alpha duty A",
                                "union_candidates": [candidate("B", 9, "other")],
                                "anchor_candidates": [candidate("A", 1, "alpha duty")],
                            },
                        },
                        {
                            "id": "article_drift",
                            "evidence": [candidate("A", 2, "beta duty")],
                            "debug_info": {
                                "used_rerank_query": "beta duty A",
                                "union_candidates": [candidate("A", 9, "different")],
                                "anchor_candidates": [candidate("A", 2, "beta duty")],
                            },
                        },
                    ]
                },
            )

            report = build_report(trace, inspection)

        self.assertEqual(report["summary"]["status"], "qdrant_or_live_retrieval_needed")
        self.assertEqual(report["summary"]["missing_final_ref_from_union_total"], 2)
        rows = {row["id"]: row for row in report["case_rows"]}
        self.assertEqual(rows["source_drift"]["classification"], "union_top_source_drift")
        self.assertEqual(rows["article_drift"]["classification"], "same_source_article_drift")

    def test_build_report_handles_final_refs_present_without_qdrant_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            inspection = Path(tmp) / "inspection.json"
            write_json(inspection, {"summary": {"anchor_filled_final_ref_cases": ["covered"]}})
            write_json(
                trace,
                {
                    "reports": [
                        {
                            "id": "covered",
                            "evidence": [candidate("A", 1, "covered duty")],
                            "debug_info": {
                                "used_rerank_query": "covered duty A",
                                "union_candidates": [candidate("A", 1, "covered duty")],
                                "anchor_candidates": [],
                            },
                        },
                    ]
                },
            )

            report = build_report(trace, inspection)

        self.assertEqual(report["summary"]["status"], "no_qdrant_needed")
        self.assertEqual(report["summary"]["missing_final_ref_from_union_total"], 0)
        self.assertFalse(report["summary"]["qdrant_stop_required"])
        self.assertEqual(report["case_rows"][0]["classification"], "final_refs_present_in_union")

    def test_build_report_does_not_process_all_cases_when_inspection_has_no_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            inspection = Path(tmp) / "inspection.json"
            write_json(inspection, {"summary": {"anchor_filled_final_ref_cases": []}})
            write_json(
                trace,
                {
                    "reports": [
                        {
                            "id": "not_requested",
                            "evidence": [candidate("A", 1)],
                            "debug_info": {"union_candidates": [candidate("B", 1)]},
                        }
                    ]
                },
            )

            report = build_report(trace, inspection)

        self.assertEqual(report["summary"]["status"], "no_inspected_cases")
        self.assertEqual(report["summary"]["total_cases"], 0)
        self.assertEqual(report["case_rows"], [])

    def test_classification_uses_missing_final_refs_for_article_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            inspection = Path(tmp) / "inspection.json"
            write_json(inspection, {"summary": {"anchor_filled_final_ref_cases": ["mixed"]}})
            write_json(
                trace,
                {
                    "reports": [
                        {
                            "id": "mixed",
                            "evidence": [
                                candidate("A", 1, "covered duty"),
                                candidate("A", 2, "missing duty"),
                            ],
                            "debug_info": {
                                "used_rerank_query": "covered missing duty A",
                                "union_candidates": [
                                    candidate("A", 1, "covered duty"),
                                    candidate("A", 9, "different duty"),
                                ],
                                "anchor_candidates": [candidate("A", 2, "missing duty")],
                            },
                        },
                    ]
                },
            )

            report = build_report(trace, inspection)

        row = report["case_rows"][0]
        self.assertEqual(row["classification"], "same_source_article_drift")
        self.assertEqual(len(row["missing_final_refs_from_union"]), 1)


if __name__ == "__main__":
    unittest.main()
