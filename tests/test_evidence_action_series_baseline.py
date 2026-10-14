import tempfile
import unittest
from pathlib import Path

from tools.build_evidence_action_series_baseline import (
    DEFAULT_ACTION_PLAN_PATH,
    DEFAULT_OUTPUT_PATH,
    build_baseline,
)


class EvidenceActionSeriesBaselineTest(unittest.TestCase):
    def test_default_paths_remain_legacy_tests_reports(self):
        self.assertEqual(DEFAULT_ACTION_PLAN_PATH, Path("tests/evidence_root_cause_action_plan.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/evidence_action_series_baseline.json"))

    def test_baseline_contains_order_and_boundaries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "action_plan.json"
            path.write_text(
                '{"version":"0.4.7.3.5","actions":[{"target_version":"0.4.7.4.2","action_id":"scenario"}]}',
                encoding="utf-8",
            )

            report = build_baseline(path)

        self.assertEqual(report["version"], "0.4.7.4.0")
        self.assertEqual(report["summary"]["total_steps"], 6)
        self.assertEqual(report["summary"]["execution_order"][0], "0.4.7.4.1")
        self.assertTrue(any("Do not add anchors" in item for item in report["global_boundaries"]))
        scenario_step = [step for step in report["steps"] if step["version"] == "0.4.7.4.2"][0]
        self.assertTrue(scenario_step["has_action_plan_link"])
        self.assertEqual(scenario_step["planned_actions"][0]["action_id"], "scenario")


if __name__ == "__main__":
    unittest.main()
