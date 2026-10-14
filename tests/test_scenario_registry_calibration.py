import tempfile
import unittest
from pathlib import Path

from tools.calibrate_scenario_registry_coverage import (
    ISSUE_CORE_MISSING_FROM_FINAL,
    ISSUE_CROSS_DOMAIN_CORE_GAP,
    ISSUE_EVIDENCE_CHAIN_GAP,
    ISSUE_FINAL_PRIMARY_OVERLAP,
    ISSUE_REGISTRY_SCOPE_REVIEW,
    build_report,
    classify_case,
)


def evidence(source, article_no, functional_type="operative_rule"):
    return {
        "source": source,
        "article_no": article_no,
        "functional_type": functional_type,
        "enrichment_status": "matched",
    }


class ScenarioRegistryCalibrationTest(unittest.TestCase):
    def test_registry_scope_candidate_when_final_expected_is_covered(self):
        pipl_38 = evidence("个人信息保护法", 38, "procedural")
        pipl_39 = evidence("个人信息保护法", 39, "procedural")
        coverage_case = {
            "case_id": "generic_case",
            "risk_level": "low",
            "detected_issues": ["scenario_core_gap"],
            "expected_domains": ["数据合规"],
            "scenario_core_coverage": {"matched": 1, "expected": 2, "coverage_ratio": 0.5, "missing": [pipl_39]},
            "final_evidence_coverage": {"matched": 1, "expected": 1, "coverage_ratio": 1.0, "missing": []},
            "final_evidence": [pipl_38],
        }
        scenario = {
            "scenario_id": "generic_scenario",
            "domain": "数据合规",
            "core_articles": [pipl_38, pipl_39],
        }

        result = classify_case("generic_case", coverage_case, None, scenario)

        self.assertIn(ISSUE_CORE_MISSING_FROM_FINAL, result["detected_issues"])
        self.assertIn(ISSUE_REGISTRY_SCOPE_REVIEW, result["detected_issues"])
        self.assertNotIn(ISSUE_EVIDENCE_CHAIN_GAP, result["detected_issues"])

    def test_evidence_chain_gap_overlap_is_reported(self):
        pipl_38 = evidence("个人信息保护法", 38, "procedural")
        pipl_39 = evidence("个人信息保护法", 39, "procedural")
        coverage_case = {
            "case_id": "generic_case",
            "risk_level": "high",
            "detected_issues": ["scenario_core_gap", "final_primary_gap"],
            "expected_domains": ["数据合规"],
            "scenario_core_coverage": {"matched": 1, "expected": 2, "coverage_ratio": 0.5, "missing": [pipl_39]},
            "final_evidence_coverage": {"matched": 1, "expected": 2, "coverage_ratio": 0.5, "missing": [pipl_39]},
            "final_evidence": [pipl_38],
        }
        review_item = {
            "root_causes": ["scenario_core_gap", "final_primary_gap"],
            "missing_scenario_core": [pipl_39],
            "missing_final_expected": [pipl_39],
            "final_evidence": [pipl_38],
        }

        result = classify_case("generic_case", coverage_case, review_item, {"domain": "数据合规", "core_articles": [pipl_38, pipl_39]})

        self.assertIn(ISSUE_EVIDENCE_CHAIN_GAP, result["detected_issues"])
        self.assertIn(ISSUE_FINAL_PRIMARY_OVERLAP, result["detected_issues"])
        self.assertEqual(result["priority"], "high")

    def test_cross_domain_gap_is_generic(self):
        pipl = evidence("个人信息保护法", 51)
        anti = evidence("反不正当竞争法", 10, "definition")
        coverage_case = {
            "case_id": "generic_cross_domain",
            "risk_level": "low",
            "detected_issues": ["scenario_core_gap"],
            "expected_domains": ["数据合规", "市场秩序"],
            "scenario_core_coverage": {"matched": 1, "expected": 2, "coverage_ratio": 0.5, "missing": [anti]},
            "final_evidence_coverage": {"matched": 1, "expected": 1, "coverage_ratio": 1.0, "missing": []},
            "final_evidence": [pipl],
        }

        result = classify_case("generic_cross_domain", coverage_case, None, {"domain": "市场秩序", "core_articles": [pipl, anti]})

        self.assertIn(ISSUE_CROSS_DOMAIN_CORE_GAP, result["detected_issues"])

    def test_file_report_builds_from_generic_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage_report = tmp / "coverage.json"
            review_dataset = tmp / "manual.json"
            scenario_registry = tmp / "scenario.json"

            core_a = evidence("个人信息保护法", 38)
            core_b = evidence("个人信息保护法", 39)
            coverage_report.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "cases": [
                            {
                                "case_id": "case_a",
                                "risk_level": "high",
                                "detected_issues": ["scenario_core_gap"],
                                "expected_domains": ["数据合规"],
                                "scenario_core_coverage": {
                                    "matched": 1,
                                    "expected": 2,
                                    "coverage_ratio": 0.5,
                                    "missing": [core_b],
                                },
                                "final_evidence_coverage": {
                                    "matched": 1,
                                    "expected": 1,
                                    "coverage_ratio": 1.0,
                                    "missing": [],
                                },
                                "final_evidence": [core_a],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            review_dataset.write_text(
                '{"version":"test","review_items":[]}',
                encoding="utf-8",
            )
            scenario_registry.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "scenarios": [
                            {
                                "scenario_id": "scenario_a",
                                "domain": "数据合规",
                                "core_articles": [core_a, core_b],
                                "eval_case_ids": ["case_a"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(coverage_report, review_dataset, scenario_registry)

        self.assertEqual(report["version"], "0.4.7.4.2")
        self.assertEqual(report["summary"]["total_scenario_gap_cases"], 1)
        self.assertEqual(report["cases"][0]["scenario_id"], "scenario_a")


if __name__ == "__main__":
    unittest.main()
