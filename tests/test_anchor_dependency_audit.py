import tempfile
import unittest
from pathlib import Path

from tools.audit_anchor_dependency import (
    ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP,
    ISSUE_ANCHOR_RESCUE_SUCCESS,
    ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST,
    ISSUE_HEALTHY_ANCHOR_SUPPORT_CANDIDATE,
    ISSUE_METADATA_OR_CHUNKING_REVIEW,
    ISSUE_ZERO_BASE_TO_ANCHOR_RECOVERY,
    build_report,
    classify_case,
)


def layer(ratio, expected=4, missing=None):
    return {
        "coverage_ratio": ratio,
        "matched_count": int(ratio * expected),
        "expected_count": expected,
        "missing": missing or [],
    }


def coverage_case(union, anchor, final=1.0, risk_level="low"):
    missing = [{"source": "个人信息保护法", "article_no": 38, "functional_type": "procedural"}]
    return {
        "case_id": "generic_case",
        "risk_level": risk_level,
        "expected_domains": ["数据合规"],
        "layer_coverage": {
            "dense": layer(0.0, missing=missing),
            "sparse": layer(union, missing=missing),
            "union": layer(union, missing=missing),
            "anchor": layer(anchor, missing=[] if anchor == 1.0 else missing),
            "rerank_input": layer(anchor),
            "final": layer(final),
        },
    }


class AnchorDependencyAuditTest(unittest.TestCase):
    def test_healthy_anchor_support_when_base_is_already_adequate(self):
        result = classify_case(
            "generic_case",
            coverage_case(union=0.8, anchor=1.0, final=1.0),
            {"root_causes": ["anchor_dependency"]},
            {},
        )

        self.assertIn(ISSUE_HEALTHY_ANCHOR_SUPPORT_CANDIDATE, result["detected_issues"])
        self.assertNotIn(ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP, result["detected_issues"])

    def test_zero_base_to_anchor_recovery_is_masking_pattern(self):
        result = classify_case(
            "generic_case",
            coverage_case(union=0.0, anchor=1.0, final=1.0, risk_level="high"),
            {"root_causes": ["anchor_dependency", "base_retrieval_gap"]},
            {"detected_issues": ["metadata_or_chunking_review_candidate", "anchor_rescue_pattern"]},
        )

        self.assertIn(ISSUE_ANCHOR_MASKING_BASE_RETRIEVAL_GAP, result["detected_issues"])
        self.assertIn(ISSUE_ANCHOR_RESCUE_SUCCESS, result["detected_issues"])
        self.assertIn(ISSUE_ZERO_BASE_TO_ANCHOR_RECOVERY, result["detected_issues"])
        self.assertIn(ISSUE_METADATA_OR_CHUNKING_REVIEW, result["detected_issues"])
        self.assertEqual(result["priority"], "high")

    def test_anchor_supported_but_final_lost_is_reported(self):
        result = classify_case(
            "generic_case",
            coverage_case(union=0.25, anchor=1.0, final=0.5),
            {"root_causes": ["anchor_dependency"]},
            {},
        )

        self.assertIn(ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST, result["detected_issues"])
        self.assertEqual(result["anchor_flow"]["final_loss_after_anchor"], 0.5)

    def test_file_report_builds_from_saved_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage = tmp / "coverage.json"
            triage = tmp / "triage.json"
            base = tmp / "base.json"
            coverage.write_text(
                __import__("json").dumps(
                    {"version": "test", "cases": [coverage_case(union=0.0, anchor=1.0)]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            triage.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "cases": [{"case_id": "generic_case", "root_causes": ["anchor_dependency"]}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            base.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "cases": [
                            {
                                "case_id": "generic_case",
                                "detected_issues": ["metadata_or_chunking_review_candidate"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(coverage, triage, base)

        self.assertEqual(report["version"], "0.4.7.4.4")
        self.assertEqual(report["summary"]["total_anchor_dependency_cases"], 1)
        self.assertIn("anchor_masking_base_retrieval_gap", report["summary"]["issue_type_summary"])


if __name__ == "__main__":
    unittest.main()
