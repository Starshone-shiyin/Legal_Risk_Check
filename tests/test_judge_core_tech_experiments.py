import unittest

from tools.judge_core_tech_experiments import EXPECTED_PROFILES, build_report


class CoreTechnologyExperimentPacketJudgeTest(unittest.TestCase):
    def test_current_experiment_packet_is_accepted(self):
        report = build_report()

        self.assertEqual(report["verdict"], "accepted")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(len(EXPECTED_PROFILES), 7)
        self.assertEqual(len(report["figure_details"]), 3)


if __name__ == "__main__":
    unittest.main()
