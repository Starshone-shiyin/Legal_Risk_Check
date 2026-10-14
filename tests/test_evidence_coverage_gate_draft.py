import tempfile
import unittest
from pathlib import Path

from tools.draft_evidence_coverage_gates import (
    DEFAULT_COVERAGE_REPORT_PATH,
    DEFAULT_MANUAL_REVIEW_DATASET_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TRIAGE_REPORT_PATH,
    SEVERITY_BLOCKING_DRAFT,
    build_gates,
    build_report,
)


def coverage_report(review_cases=36, total_cases=60, final=0.913, enrichment=0.994, scenario_core_gap=8):
    return {
        "version": "0.4.7.3.2",
        "summary": {
            "total_cases": total_cases,
            "review_cases": review_cases,
            "issue_type_summary": {"scenario_core_gap": scenario_core_gap},
            "layer_summary": {"final": {"coverage_ratio": final}},
            "enrichment_summary": {"matched_ratio": enrichment},
        },
    }


def triage_report(high_priority=12, final_selection_loss=7):
    return {
        "version": "0.4.7.3.2",
        "summary": {
            "triage_status_summary": {"high_priority_review": high_priority},
            "root_cause_summary": {"final_selection_loss": final_selection_loss},
        },
    }


def manual_dataset(pending=12):
    return {
        "version": "0.4.7.3.3",
        "summary": {"pending_review_items": pending},
    }


class EvidenceCoverageGateDraftTest(unittest.TestCase):
    def test_default_paths_remain_legacy_tests_reports(self):
        self.assertEqual(DEFAULT_COVERAGE_REPORT_PATH, Path("tests/evidence_coverage_report.json"))
        self.assertEqual(DEFAULT_TRIAGE_REPORT_PATH, Path("tests/evidence_coverage_triage_report.json"))
        self.assertEqual(DEFAULT_MANUAL_REVIEW_DATASET_PATH, Path("tests/evidence_manual_review_dataset.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/evidence_coverage_gate_draft_report.json"))

    def test_current_baseline_passes_draft_gates(self):
        gates = build_gates(coverage_report(), triage_report(), manual_dataset())

        self.assertTrue(all(gate["passed"] for gate in gates))
        self.assertEqual(len(gates), 7)

    def test_high_priority_regression_is_blocking_draft(self):
        gates = build_gates(coverage_report(), triage_report(high_priority=13), manual_dataset())
        failed = [gate for gate in gates if not gate["passed"]]

        self.assertEqual(failed[0]["gate_id"], "draft.high_priority_review.max")
        self.assertEqual(failed[0]["severity"], SEVERITY_BLOCKING_DRAFT)

    def test_build_report_from_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage = tmp / "coverage.json"
            triage = tmp / "triage.json"
            manual = tmp / "manual.json"
            coverage.write_text(__import__("json").dumps(coverage_report()), encoding="utf-8")
            triage.write_text(__import__("json").dumps(triage_report()), encoding="utf-8")
            manual.write_text(__import__("json").dumps(manual_dataset()), encoding="utf-8")

            report = build_report(coverage, triage, manual)

        self.assertEqual(report["version"], "0.4.7.3.4")
        self.assertTrue(report["summary"]["non_enforcing"])
        self.assertEqual(report["summary"]["failed_gates"], 0)


if __name__ == "__main__":
    unittest.main()
