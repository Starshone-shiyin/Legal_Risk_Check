import tempfile
import unittest
from pathlib import Path

from tools.build_evidence_root_cause_action_plan import (
    DEFAULT_COVERAGE_REPORT_PATH,
    DEFAULT_GATE_DRAFT_REPORT_PATH,
    DEFAULT_MANUAL_REVIEW_DATASET_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TRIAGE_REPORT_PATH,
    build_actions,
    build_plan,
)


class EvidenceRootCauseActionPlanTest(unittest.TestCase):
    def test_default_paths_remain_legacy_tests_reports(self):
        self.assertEqual(DEFAULT_COVERAGE_REPORT_PATH, Path("tests/evidence_coverage_report.json"))
        self.assertEqual(DEFAULT_TRIAGE_REPORT_PATH, Path("tests/evidence_coverage_triage_report.json"))
        self.assertEqual(DEFAULT_MANUAL_REVIEW_DATASET_PATH, Path("tests/evidence_manual_review_dataset.json"))
        self.assertEqual(DEFAULT_GATE_DRAFT_REPORT_PATH, Path("tests/evidence_coverage_gate_draft_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/evidence_root_cause_action_plan.json"))

    def test_actions_map_root_causes_to_versions(self):
        triage_report = {
            "summary": {
                "root_cause_summary": {
                    "scenario_core_gap": 8,
                    "base_retrieval_gap": 34,
                    "anchor_dependency": 33,
                }
            }
        }
        manual_dataset = {
            "review_items": [
                {"case_id": "case_a", "root_causes": ["scenario_core_gap"]},
                {"case_id": "case_b", "root_causes": ["base_retrieval_gap", "anchor_dependency"]},
            ]
        }

        actions = build_actions(triage_report, manual_dataset)
        by_root = {action["root_cause"]: action for action in actions}

        self.assertEqual(by_root["scenario_core_gap"]["target_version"], "0.4.7.4.2")
        self.assertEqual(by_root["base_retrieval_gap"]["target_version"], "0.4.7.4.3")
        self.assertEqual(by_root["anchor_dependency"]["target_version"], "0.4.7.4.4")
        self.assertEqual(by_root["scenario_core_gap"]["sample_case_ids"], ["case_a"])

    def test_build_plan_from_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            coverage = tmp / "coverage.json"
            triage = tmp / "triage.json"
            manual = tmp / "manual.json"
            gate = tmp / "gate.json"
            coverage.write_text('{"version":"0.4.7.3.2"}', encoding="utf-8")
            triage.write_text(
                '{"version":"0.4.7.3.2","summary":{"root_cause_summary":{"final_primary_gap":8}}}',
                encoding="utf-8",
            )
            manual.write_text(
                '{"version":"0.4.7.3.3","review_items":[{"case_id":"case_a","root_causes":["final_primary_gap"]}]}',
                encoding="utf-8",
            )
            gate.write_text(
                '{"version":"0.4.7.3.4","summary":{"failed_gates":0}}',
                encoding="utf-8",
            )

            plan = build_plan(coverage, triage, manual, gate)

        self.assertEqual(plan["version"], "0.4.7.3.5")
        self.assertEqual(plan["summary"]["total_actions"], 1)
        self.assertEqual(plan["actions"][0]["target_version"], "0.4.7.4.6")
        self.assertTrue(plan["summary"]["gate_draft_passed"])


if __name__ == "__main__":
    unittest.main()
