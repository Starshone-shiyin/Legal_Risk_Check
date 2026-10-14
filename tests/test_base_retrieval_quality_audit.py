import tempfile
import unittest
from pathlib import Path

from tools.audit_base_retrieval_quality import (
    ISSUE_ANCHOR_RESCUE_PATTERN,
    ISSUE_INDEX_OR_SOURCE_REVIEW,
    ISSUE_METADATA_OR_CHUNKING_REVIEW,
    ISSUE_NO_UNION_GAIN,
    ISSUE_SPARSE_ONLY_SUPPORT,
    ISSUE_UNION_RETRIEVAL_GAP,
    ISSUE_ZERO_BASE_RECALL,
    build_report,
    classify_case,
)


def layer(ratio, expected=4, missing=None):
    matched = int(ratio * expected)
    return {
        "coverage_ratio": ratio,
        "matched_count": matched,
        "expected_count": expected,
        "missing": missing or [],
    }


def coverage_case(**layers):
    default_missing = [{"source": "个人信息保护法", "article_no": 38, "functional_type": "procedural"}]
    return {
        "case_id": "generic_case",
        "risk_level": "low",
        "expected_domains": ["数据合规"],
        "layer_coverage": {
            "dense": layer(layers.get("dense", 0), missing=default_missing),
            "sparse": layer(layers.get("sparse", 0), missing=default_missing),
            "union": layer(layers.get("union", 0), missing=default_missing),
            "anchor": layer(layers.get("anchor", 0), missing=[]),
            "final": layer(layers.get("final", 0), missing=[]),
        },
    }


class BaseRetrievalQualityAuditTest(unittest.TestCase):
    def test_sparse_only_anchor_rescue_pattern(self):
        result = classify_case(
            "generic_case",
            coverage_case(dense=0.0, sparse=0.5, union=0.5, anchor=1.0, final=1.0),
            {"root_causes": ["base_retrieval_gap"], "triage_status": "review"},
        )

        self.assertIn(ISSUE_UNION_RETRIEVAL_GAP, result["detected_issues"])
        self.assertIn(ISSUE_SPARSE_ONLY_SUPPORT, result["detected_issues"])
        self.assertIn(ISSUE_ANCHOR_RESCUE_PATTERN, result["detected_issues"])
        self.assertIn(ISSUE_METADATA_OR_CHUNKING_REVIEW, result["detected_issues"])

    def test_zero_base_recall_with_no_anchor_recovery_routes_to_source_review(self):
        result = classify_case(
            "generic_case",
            coverage_case(dense=0.0, sparse=0.0, union=0.0, anchor=0.0, final=0.0),
            {"root_causes": ["base_retrieval_gap"], "triage_status": "high_priority_review"},
        )

        self.assertIn(ISSUE_ZERO_BASE_RECALL, result["detected_issues"])
        self.assertIn(ISSUE_INDEX_OR_SOURCE_REVIEW, result["detected_issues"])
        self.assertEqual(result["priority"], "high")

    def test_no_union_gain_is_reported_generically(self):
        result = classify_case(
            "generic_case",
            coverage_case(dense=0.5, sparse=0.5, union=0.5, anchor=0.5, final=0.5),
            {"root_causes": ["base_retrieval_gap"], "triage_status": "review"},
        )

        self.assertIn(ISSUE_NO_UNION_GAIN, result["detected_issues"])
        self.assertEqual(result["base_layer_coverage"]["union_gain_over_best_single"], 0.0)

    def test_file_report_builds_from_saved_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage = tmp / "coverage.json"
            triage = tmp / "triage.json"
            coverage.write_text(
                __import__("json").dumps(
                    {"version": "test", "cases": [coverage_case(dense=0.0, sparse=0.5, union=0.5, anchor=1.0)]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            triage.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "cases": [
                            {
                                "case_id": "generic_case",
                                "root_causes": ["base_retrieval_gap"],
                                "triage_status": "review",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(coverage, triage)

        self.assertEqual(report["version"], "0.4.7.4.3")
        self.assertEqual(report["summary"]["total_base_gap_cases"], 1)
        self.assertIn("sparse_only_support", report["summary"]["issue_type_summary"])


if __name__ == "__main__":
    unittest.main()
