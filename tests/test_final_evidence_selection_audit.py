import tempfile
import unittest
from pathlib import Path

from tools.audit_final_evidence_selection import (
    ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST,
    ISSUE_LIABILITY_EVIDENCE_LOST,
    ISSUE_LOW_FINAL_COVERAGE_AFTER_SELECTION,
    ISSUE_OPERATIVE_EVIDENCE_LOST,
    ISSUE_PRIMARY_EVIDENCE_LOST,
    ISSUE_SCENARIO_CORE_LOST,
    build_report,
    classify_case,
)


def evidence(article_no, functional_type="operative_rule"):
    return {
        "source": "个人信息保护法",
        "article_no": article_no,
        "functional_type": functional_type,
        "enrichment_status": "matched",
    }


def layer(ratio, missing=None):
    return {
        "coverage_ratio": ratio,
        "matched_count": int(ratio * 4),
        "expected_count": 4,
        "missing": missing or [],
    }


def coverage_case(final_ratio=0.5, missing=None, scenario_missing=None):
    missing = missing or [evidence(66, "liability")]
    return {
        "case_id": "generic_case",
        "risk_level": "high",
        "expected_domains": ["数据合规"],
        "layer_coverage": {
            "anchor": layer(1.0),
            "rerank_input": layer(1.0),
            "final": layer(final_ratio, missing=missing),
        },
        "final_evidence_coverage": {
            "matched": 2,
            "expected": 4,
            "coverage_ratio": final_ratio,
            "missing": missing,
        },
        "scenario_core_coverage": {
            "matched": 1,
            "expected": 2,
            "coverage_ratio": 0.5,
            "missing": scenario_missing or [],
        },
    }


class FinalEvidenceSelectionAuditTest(unittest.TestCase):
    def test_primary_and_liability_loss_are_reported(self):
        result = classify_case(
            "generic_case",
            coverage_case(final_ratio=0.5, missing=[evidence(66, "liability")]),
            {"root_causes": ["final_selection_loss"]},
            {},
        )

        self.assertIn(ISSUE_PRIMARY_EVIDENCE_LOST, result["detected_issues"])
        self.assertIn(ISSUE_LIABILITY_EVIDENCE_LOST, result["detected_issues"])
        self.assertIn(ISSUE_LOW_FINAL_COVERAGE_AFTER_SELECTION, result["detected_issues"])

    def test_anchor_supported_but_final_lost_and_scenario_core(self):
        result = classify_case(
            "generic_case",
            coverage_case(
                final_ratio=0.75,
                missing=[evidence(38, "procedural")],
                scenario_missing=[evidence(38, "procedural")],
            ),
            {"root_causes": ["final_selection_loss"]},
            {"detected_issues": ["anchor_rescue_success", "anchor_supported_but_final_lost"]},
        )

        self.assertIn(ISSUE_ANCHOR_SUPPORTED_BUT_FINAL_LOST, result["detected_issues"])
        self.assertIn(ISSUE_SCENARIO_CORE_LOST, result["detected_issues"])
        self.assertIn(ISSUE_OPERATIVE_EVIDENCE_LOST, result["detected_issues"])

    def test_file_report_builds_from_saved_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage = tmp / "coverage.json"
            triage = tmp / "triage.json"
            anchor = tmp / "anchor.json"
            coverage.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "cases": [
                            {
                                **coverage_case(),
                                "detected_issues": ["layer_coverage_regression"],
                            }
                        ],
                    },
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
                                "root_causes": ["final_selection_loss"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            anchor.write_text(
                __import__("json").dumps(
                    {"version": "test", "cases": []},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(coverage, triage, anchor)

        self.assertEqual(report["version"], "0.4.7.4.5")
        self.assertEqual(report["summary"]["total_final_selection_loss_cases"], 1)
        self.assertIn("primary_evidence_lost", report["summary"]["issue_type_summary"])


if __name__ == "__main__":
    unittest.main()
