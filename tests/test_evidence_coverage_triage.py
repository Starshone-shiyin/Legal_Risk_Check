import tempfile
import unittest
from pathlib import Path

from tools.triage_evidence_coverage_loss import (
    ROOT_ANCHOR_DEPENDENCY,
    ROOT_BASE_RETRIEVAL_GAP,
    ROOT_FINAL_PRIMARY_GAP,
    ROOT_FINAL_SELECTION_LOSS,
    ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE,
    ROOT_SCENARIO_CORE_GAP,
    TRIAGE_HIGH_PRIORITY,
    TRIAGE_OK,
    build_triage_report,
    triage_case,
)


def case_with_layers(case_id, union=1.0, anchor=1.0, rerank=1.0, final=1.0, issues=None, risk_level="low"):
    return {
        "case_id": case_id,
        "coverage_status": "review" if issues else "ok",
        "risk_level": risk_level,
        "expected_domains": ["示例领域"],
        "detected_issues": issues or [],
        "layer_coverage": {
            "dense": {"coverage_ratio": union, "expected_count": 2},
            "sparse": {"coverage_ratio": union, "expected_count": 2},
            "union": {"coverage_ratio": union, "expected_count": 2},
            "anchor": {"coverage_ratio": anchor, "expected_count": 2},
            "rerank_input": {"coverage_ratio": rerank, "expected_count": 2},
            "final": {"coverage_ratio": final, "expected_count": 2},
        },
        "functional_type_coverage": {"total_items": 2, "evaluable": False},
    }


class EvidenceCoverageTriageTest(unittest.TestCase):
    def test_anchor_dependency_and_base_gap_are_triaged(self):
        result = triage_case(case_with_layers("case_anchor", union=0.25, anchor=1.0))

        self.assertIn(ROOT_BASE_RETRIEVAL_GAP, result["root_causes"])
        self.assertIn(ROOT_ANCHOR_DEPENDENCY, result["root_causes"])
        self.assertIn(ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE, result["root_causes"])
        self.assertEqual(result["coverage_flow"]["union_to_anchor_delta"], 0.75)

    def test_final_selection_loss_and_primary_gap_are_high_priority(self):
        result = triage_case(
            case_with_layers(
                "case_final_loss",
                union=1.0,
                anchor=1.0,
                rerank=1.0,
                final=0.5,
                issues=["final_primary_gap"],
                risk_level="high",
            )
        )

        self.assertEqual(result["triage_status"], TRIAGE_HIGH_PRIORITY)
        self.assertIn(ROOT_FINAL_SELECTION_LOSS, result["root_causes"])
        self.assertIn(ROOT_FINAL_PRIMARY_GAP, result["root_causes"])

    def test_scenario_core_gap_is_not_case_specific(self):
        result = triage_case(
            case_with_layers(
                "any_case_id",
                union=1.0,
                anchor=1.0,
                rerank=1.0,
                final=1.0,
                issues=["scenario_core_gap"],
            )
        )

        self.assertIn(ROOT_SCENARIO_CORE_GAP, result["root_causes"])

    def test_no_root_cause_is_ok(self):
        case = case_with_layers("case_ok", issues=None)
        case["functional_type_coverage"] = {"total_items": 2, "evaluable": True}

        result = triage_case(case)

        self.assertEqual(result["triage_status"], TRIAGE_OK)
        self.assertEqual(result["root_causes"], [])

    def test_metadata_limitation_alone_does_not_force_review(self):
        result = triage_case(case_with_layers("metadata_only", issues=None))

        self.assertEqual(result["triage_status"], TRIAGE_OK)
        self.assertEqual(result["root_causes"], [ROOT_FUNCTIONAL_METADATA_NOT_EVALUABLE])

    def test_build_report_from_coverage_report_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_path = Path(tmpdir) / "coverage.json"
            coverage_path.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.3.2",
                        "cases": [
                            case_with_layers("case_a", union=0.25, anchor=1.0),
                            case_with_layers(
                                "case_b",
                                union=1.0,
                                anchor=1.0,
                                rerank=1.0,
                                final=0.5,
                                issues=["final_primary_gap"],
                                risk_level="high",
                            ),
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_triage_report(coverage_path)

        self.assertEqual(report["version"], "0.4.7.3.2")
        self.assertEqual(report["summary"]["total_cases"], 2)
        self.assertEqual(report["summary"]["root_cause_summary"][ROOT_ANCHOR_DEPENDENCY], 1)
        self.assertEqual(len(report["summary"]["high_priority_manual_review"]), 1)


if __name__ == "__main__":
    unittest.main()
